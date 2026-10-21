"""Read-only audio measurement and explicit, lossless derived files via FFmpeg."""

import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile

from jobs import fingerprint, save_json


def probe(source):
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(source),
    ], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    if stream is None:
        raise ValueError("The file has no audio stream.")
    duration = float(data["format"]["duration"])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("The recording duration is invalid.")
    return {"duration_seconds": duration, "channels": stream["channels"],
            "sample_rate": int(stream["sample_rate"]), "codec": stream["codec_name"]}


def input_args(source, start=0, duration=None):
    args = ["ffmpeg", "-hide_banner", "-nostdin", "-ss", str(start), "-i", str(source)]
    if duration is not None:
        args += ["-t", str(duration)]
    return args + ["-map", "0:a:0", "-vn"]


def measure(source, start=0, duration=None):
    result = subprocess.run(input_args(source, start, duration) + [
        "-af", "volumedetect", "-f", "null", "-",
    ], capture_output=True, text=True, check=True)
    values = {}
    for key in ("mean_volume", "max_volume"):
        match = re.search(rf"{key}:\s*(-?[\d.]+|-[Ii]nf) dB", result.stderr)
        if not match:
            raise ValueError(f"FFmpeg did not report {key}.")
        values[f"{key}_dbfs"] = float(match[1])
    if not all(math.isfinite(v) for v in values.values()):
        raise ValueError("Audio measurement found silence or invalid levels.")
    # Fixed gain preserves dynamics. It cannot improve the signal-to-noise ratio.
    values["suggested_gain_db"] = round(max(0, min(
        24, -3 - values["max_volume_dbfs"], -22 - values["mean_volume_dbfs"],
    )), 1)
    return values


def normalization_filter(source, start=0, duration=None):
    target = "loudnorm=I=-20:TP=-2:LRA=11"
    result = subprocess.run(input_args(source, start, duration) + [
        "-af", target + ":print_format=json", "-f", "null", "-",
    ], capture_output=True, text=True, check=True)
    match = re.search(r'\{\s*"input_i".*?\}', result.stderr, flags=re.S)
    if not match:
        raise ValueError("FFmpeg did not return loudness measurements.")
    measured = json.loads(match[0])
    pairs = {"measured_I": "input_i", "measured_TP": "input_tp", "measured_LRA": "input_lra",
             "measured_thresh": "input_thresh", "offset": "target_offset"}
    values = {key: float(measured[value]) for key, value in pairs.items()}
    if not all(math.isfinite(v) for v in values.values()):
        raise ValueError("Cannot normalize silence or invalid loudness measurements.")
    options = ":".join(f"{key}={value}" for key, value in values.items())
    # The peak constraint may require dynamic gain; preserve the untouched source for A/B review.
    return f"{target}:{options}:linear=false", measured


def prepare(source, output, *, start=0, duration=None, gain_db=0, normalize=False):
    metadata = probe(source)
    if start < 0 or start >= metadata["duration_seconds"]:
        raise ValueError("Excerpt start is outside the recording.")
    if duration is not None and (duration <= 0 or start + duration > metadata["duration_seconds"] + 0.1):
        raise ValueError("Excerpt duration is outside the recording.")
    if not math.isfinite(gain_db) or abs(gain_db) > 30:
        raise ValueError("Gain must be finite and between -30 and 30 dB.")
    if normalize and gain_db:
        raise ValueError("Choose fixed gain or loudness normalization, not both.")
    levels = measure(source, start, duration)
    if gain_db > 0 and levels["max_volume_dbfs"] + gain_db > -1:
        raise ValueError("Requested gain leaves less than 1 dB peak headroom; lower --gain-db.")
    source_hash = fingerprint(source)
    recipe = {"source_sha256": source_hash, "start_seconds": start,
              "duration_seconds": duration, "gain_db": gain_db,
              "normalization": {"I": -20, "TP": -2, "LRA": 11, "linear": False} if normalize else None,
              "codec": "flac", "sample_format": "s32", "version": 1}
    import hashlib
    key = hashlib.sha256(json.dumps(recipe, sort_keys=True).encode()).hexdigest()
    directory = Path(output) / "audio"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = directory / f"{key}.flac"
    sidecar = target.with_suffix(".json")
    if target.exists() and sidecar.exists():
        saved = json.loads(sidecar.read_text(encoding="utf-8"))
        if saved.get("recipe") == recipe and saved.get("derived_sha256") == fingerprint(target):
            if normalize and saved["derived_levels"]["max_volume_dbfs"] > -1:
                raise ValueError("Normalized output failed the peak-headroom check.")
            return target, saved
    filter_value, loudness = (normalization_filter(source, start, duration) if normalize
                             else (f"volume={gain_db}dB", None))
    with tempfile.NamedTemporaryFile(dir=directory, suffix=".flac") as temporary:
        subprocess.run(input_args(source, start, duration) + [
            "-af", filter_value, "-ar", str(metadata["sample_rate"]),
            "-c:a", "flac", "-sample_fmt", "s32",
            "-y", temporary.name,
        ], capture_output=True, check=True)
        Path(temporary.name).chmod(0o600)
        # Copy into a new atomic output; the NamedTemporaryFile retains its cleanup path.
        retained = Path(temporary.name).with_suffix(".ready")
        os.link(temporary.name, retained)
        os.replace(retained, target)
    saved = {"recipe": recipe, "source_audio": metadata, "source_levels": levels,
             "normalization_measurements": loudness,
             "derived_audio": probe(target), "derived_levels": measure(target),
             "derived_sha256": fingerprint(target)}
    if normalize and saved["derived_levels"]["max_volume_dbfs"] > -1:
        raise ValueError("Normalized output failed the peak-headroom check.")
    save_json(sidecar, saved)
    return target, saved
