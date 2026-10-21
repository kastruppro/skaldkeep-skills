"""Durable AssemblyAI jobs. An uncertain POST is never retried automatically."""

import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import tempfile
import time
import uuid

BASE_URL = "https://api.assemblyai.com"
HTTP_TIMEOUT = (10, 120)
PIPELINE_VERSION = 2
# No job exists after these: auth/rate-limit problems are fixed outside the
# request, so the same command must be able to submit again without manual cleanup.
RETRYABLE_SUBMIT = frozenset({401, 403, 429})
# The request itself was refused; repeating it unchanged would fail the same way.
REJECTED_SUBMIT = frozenset({400, 404, 422})


def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_json(path, value):
    atomic_write(path, json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False))


def fingerprint(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cache_key(source_id, config):
    data = [PIPELINE_VERSION, BASE_URL, source_id, config]
    return hashlib.sha256(json.dumps(data, sort_keys=True, allow_nan=False).encode()).hexdigest()


@contextlib.contextmanager
def locked(path, *, wait=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(fd, "w") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX if wait else fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("This job is already running in another process.") from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def valid_id(value):
    try:
        return str(uuid.UUID(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise RuntimeError("API returned an invalid transcript ID.") from exc


def get_client():
    import requests
    key = os.environ.get("ASSEMBLYAI_API_KEY", "").strip()
    if not key or key == "replace_me":
        raise RuntimeError("Set ASSEMBLYAI_API_KEY in the environment (run.sh also reads it from ./.env).")
    client = requests.Session()
    # requests has no automatic POST retries by default; do not add a retry adapter.
    client.headers.update({"authorization": key})
    return client


def _upload_cache(output, source_id):
    return Path(output) / "uploads" / f"{source_id}.json"


def uploaded_url(source, source_id, output, client):
    if source.startswith("https://"):
        return source
    path = _upload_cache(output, source_id)
    with locked(path.with_suffix(".lock")):
        if path.exists():
            return read_json(path)["upload_url"]
        with open(source, "rb") as stream:
            response = client.post(f"{BASE_URL}/v2/upload", data=stream, timeout=HTTP_TIMEOUT)
        if response.status_code != 200:
            raise RuntimeError(f"Upload failed (HTTP {response.status_code}); no transcription submitted.")
        url = response.json().get("upload_url", "")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise RuntimeError("Upload did not return an HTTPS resource URL.")
        # The file is reopened after it was hashed; caching an upload of
        # different bytes under the old hash would silently reuse the wrong
        # recording for every later job with this source_id.
        if fingerprint(source) != source_id:
            raise RuntimeError("Source file changed during upload; nothing was cached or submitted.")
        save_json(path, {"upload_url": url, "source_id": source_id})
        return url


def forget_upload(source, source_id, output):
    """Drop a cached upload URL after a failed job: AssemblyAI may have deleted
    the file (for example with its transcript), and a dead URL would otherwise
    fail every later job for this audio."""
    if source.startswith("https://"):
        return
    path = _upload_cache(output, source_id)
    # Wait instead of failing fast: a concurrent upload of the same audio holds
    # this lock briefly, and a lock error here would hide the job's real error.
    with locked(path.with_suffix(".lock"), wait=True):
        path.unlink(missing_ok=True)


def delay(attempt, response=None):
    if response is not None:
        try:
            return max(1, min(60, float(response.headers.get("Retry-After", ""))))
        except (ValueError, TypeError):
            pass
    return min(60, 3 * 2 ** min(attempt, 5)) * random.uniform(0.8, 1.0)


def run_job(source, source_id, config, output, *, client=None, poll_timeout=7200):
    """Return (raw transcript, job directory); replay requires identical source/config."""
    import requests
    directory = Path(output) / "jobs" / cache_key(source_id, config)
    state_path = directory / "state.json"
    result_path = directory / "result.json"
    with locked(directory / "run.lock"):
        state = read_json(state_path) if state_path.exists() else {
            "state": "new", "source_id": source_id, "config": config,
            "created_at": time.time(), "pipeline_version": PIPELINE_VERSION,
        }
        if state.get("config") != config or state.get("source_id") != source_id:
            raise RuntimeError("Saved job does not match this source and configuration.")
        if state["state"] == "completed":
            result = read_json(result_path)
            if result.get("status") != "completed" or result.get("id") != state["transcript_id"]:
                raise RuntimeError("Cached result is invalid; refusing to create a replacement paid job.")
            print(f"Reusing completed job {state['transcript_id']}")
            return result, directory
        if state["state"] in {"submitting", "submission_uncertain"}:
            raise RuntimeError(f"Submission outcome uncertain. Inspect {state_path}; do not resubmit blindly.")
        if state["state"] in {"rejected", "error"}:
            raise RuntimeError(
                f"Saved job ended as {state['state']}. Inspect {state_path}; "
                "delete it to deliberately retry this source and configuration."
            )
        owns_client = client is None
        client = client or get_client()
        try:
            if not state.get("transcript_id"):
                state["upload_url"] = uploaded_url(source, source_id, output, client)
                state["state"] = "submitting"
                save_json(state_path, state)
                try:
                    response = client.post(f"{BASE_URL}/v2/transcript", json={
                        **config, "audio_url": state["upload_url"],
                    }, timeout=HTTP_TIMEOUT)
                except requests.exceptions.RequestException as exc:
                    state["state"] = "submission_uncertain"
                    save_json(state_path, state)
                    # Network exceptions may contain private signed resource URLs.
                    raise RuntimeError(f"Submit did not complete safely; see {state_path}.") from exc
                if response.status_code != 200:
                    code = response.status_code
                    if code in RETRYABLE_SUBMIT:
                        state["state"] = "new"
                    elif code in REJECTED_SUBMIT:
                        state["state"] = "rejected"
                    else:
                        # A server error may occur after the paid job was accepted.
                        state["state"] = "submission_uncertain"
                    state["http_status"] = code
                    try:
                        state["submit_error"] = response.json()
                    except ValueError:
                        state["submit_error"] = "Response was not JSON."
                    save_json(state_path, state)
                    if code == 400:
                        # 400 is how a dead audio_url is refused; 404/422 are
                        # endpoint/config errors where the upload is still good.
                        forget_upload(source, source_id, output)
                    hint = " No job was created; rerun the same command once fixed." \
                        if state["state"] == "new" else f" See {state_path}."
                    raise RuntimeError(f"Submit HTTP {code}; state={state['state']}.{hint}")
                try:
                    state["transcript_id"] = valid_id(response.json().get("id"))
                except (ValueError, RuntimeError) as exc:
                    state["state"] = "submission_uncertain"
                    save_json(state_path, state)
                    raise RuntimeError(f"Submit did not complete safely; see {state_path}.") from exc
                state["state"] = "queued"
                save_json(state_path, state)
            transcript_id = valid_id(state["transcript_id"])
            print(f"Polling job {transcript_id}")
            deadline, attempt = time.monotonic() + poll_timeout, 0
            while time.monotonic() < deadline:
                response = None
                remaining = deadline - time.monotonic()
                try:
                    response = client.get(f"{BASE_URL}/v2/transcript/{transcript_id}",
                                          timeout=(10, max(0.1, min(120, remaining))))
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("id") != transcript_id:
                            raise RuntimeError("Polling response has the wrong transcript ID.")
                        status = result.get("status")
                        if status not in {"queued", "processing", "completed", "error"}:
                            raise RuntimeError("Polling response has an unknown status.")
                        state["state"] = status
                        if status in {"completed", "error"}:
                            save_json(result_path, result)
                        save_json(state_path, state)
                        if status == "completed":
                            return result, directory
                        if status == "error":
                            forget_upload(source, source_id, output)
                            raise RuntimeError(f"Transcription failed; details saved in {result_path}.")
                    elif response.status_code != 429 and response.status_code < 500:
                        raise RuntimeError(f"Polling HTTP {response.status_code}; job ID retained for resume.")
                except (requests.exceptions.RequestException, ValueError):
                    pass
                remaining = deadline - time.monotonic()
                if remaining > 0:
                    time.sleep(min(delay(attempt, response), remaining))
                attempt += 1
            raise RuntimeError("Polling deadline reached. Run the same command to resume this job.")
        finally:
            if owns_client:
                client.close()


def timestamp(milliseconds):
    value = round(milliseconds)
    hours, value = divmod(value, 3600000)
    minutes, value = divmod(value, 60000)
    seconds, millis = divmod(value, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:03}"


def write_outputs(result, directory, *, offset_seconds=0):
    """Keep the historical utterance format and add a timestamped evidence view."""
    lines, timed = [], []
    for utterance in result.get("utterances") or []:
        text = f"[Speaker:{utterance.get('speaker', '?')}] {utterance.get('text', '')}"
        lines.append(text)
        start = utterance.get("start", 0) + offset_seconds * 1000
        end = utterance.get("end", 0) + offset_seconds * 1000
        timed.append(f"[{timestamp(start)} - {timestamp(end)}] {text}")
    atomic_write(Path(directory) / "transcript_utterances.txt", "\n".join(lines))
    atomic_write(Path(directory) / "transcript_timed.txt", "\n".join(timed))
    atomic_write(Path(directory) / "transcript_raw.txt", result.get("text") or "")
