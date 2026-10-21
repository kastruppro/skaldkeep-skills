# Local transcription - full reference

**Server first.** When the Skaldkeep instance has transcription configured, upload the
recording on the web app's Transcripts page instead: it accepts several files per session
(joined in order), stores who was present, speaker names, context and keyterms, deletes
the audio after success, and the AI reads the result with `get_transcript`. This local
script is the fallback for instances without it; store its output with `upload_transcript`
so the campaign keeps the transcript.

`scripts/run.sh` is the entry point; it runs `scripts/transcribe.py` with `uv`, which
installs `requests` and `PyYAML` from the script's inline metadata. `jobs.py` and
`audio_tools.py` provide durable API jobs and local audio preparation. Runs on macOS or
Linux (job locking uses `flock`).

## Methods

- `--method legacy` reproduces the previous request recipe: the full campaign
  prompt, post-recognition custom spelling and historical `known_values` speaker
  identification. This is a comparison baseline, not a newly recommended API
  contract. If the server rejects that old field, record the rejection instead
  of silently changing the experiment; `--no-identify` permits a comparison of
  the transcription recipes alone.
- `--method updated` (default) uses a short `context_prompt`, `keyterms_prompt`
  for recognition, and generic Speaker A/B labels. It does not infer participant
  names unless `--identify` is supplied. This is useful when people never say
  their names or use fictional character voices. Optional identification uses
  the current `speakers` objects, with low effort; treat the inferred names as
  hypotheses. Raw API JSON remains saved.

Both methods explicitly use `universal-3-5-pro`, `temperature=0` and the same
session speaker count. This isolates the request recipe from model selection.
It is not a benchmark of the retired `universal-3-pro` model.

Existing `prompt`, `custom_spelling`, `speaker_names` and `speakers_expected`
campaign fields still work. Add `context_prompt` and `keyterms_prompt` for the
updated recipe. If no keyterm list is supplied, custom spelling targets are used
as recognition hints. The updated method only applies replacement rules when
explicitly set in `updated_custom_spelling`. Avoid broad replacements of normal
words with fantasy names. An absent character can still be mentioned in dialogue;
excluding a participant does not remove the character from the vocabulary.

## Attendance and language

```bash
scripts/run.sh session.m4a --campaign your-campaign --absent Player1 --dry-run
```

`--absent` is repeatable and subtracts each matching participant once. Unknown
labels fail before an API call. Optional YAML `speaker_aliases` maps player names
to existing participant labels. `--speakers N` overrides the resulting count.
Use the actual number of human speakers including the DM, not the number of
fictional characters. Attendance applies to this invocation; it never edits the
campaign roster.

The campaign's `language_code` defaults to `en_us`. Use `--language da` for Danish
or `--language auto` for mixed-language audio. U3.5 supports native language
switching; no Universal-2-specific switching options are added.

## Quiet recordings

```bash
scripts/run.sh session.m4a --analyze
scripts/run.sh session.m4a --campaign your-campaign \
  --start 900 --duration 180 --gain-db 12 --compare-methods --dry-run
```

`--analyze` runs FFprobe and FFmpeg locally. It reports duration, channels,
mean/peak volume in dBFS, and a conservative gain suggestion. Fixed gain raises
speech and noise equally; it does not recover missing detail or remove noise.
The suggestion targets a mean of -22 dBFS while retaining 3 dB peak headroom,
capped at +24 dB. This is a starting point for a controlled comparison, not a
universal speech-recognition optimum.

Cropping or gain creates a separate FLAC file, preserving the source sample rate
and channels. Positive gain is refused if it would leave less than 1 dB peak
headroom. Source and resulting measurements plus hashes are saved beside the
derived audio. The input file is never overwritten. Use the same excerpt with
`--gain-db 0` and the measured gain to test normalization separately from the
request recipe. Do not join discontinuous clips into a pretend continuous session.

If quiet dialogue coexists with peaks already near 0 dBFS, fixed gain cannot safely
raise the whole recording. `--normalize` instead makes an experimental two-pass
FFmpeg `loudnorm` copy targeting -20 LUFS, -2 dB true peak and 11 LU loudness range.
It uses dynamic gain, preserves sample rate/channels and records first-pass
measurements. This changes dynamics and can raise background noise; compare it
against the original before selecting it. It cannot be combined with `--gain-db`.
See [FFmpeg loudnorm](https://ffmpeg.org/ffmpeg-filters.html#loudnorm).

## Compare and control cost

```bash
scripts/run.sh session.m4a --campaign your-campaign \
  --start 900 --duration 180 --compare-methods --max-cost-usd 0.10
```

This submits the same excerpt once per recipe, reusing its uploaded audio. A
comparison Markdown/JSON report links the transcripts and records each exact
configuration. `--compare` retains the historical prompt/no-prompt test.
`--dry-run` never uploads or submits; it validates and shows the planned payloads
and estimated upper cost. The default cost cap is $2 for the whole invocation.
The cap is checked against the full planned workload, even when some results are
cached. It is an estimate, not an account billing limit.

Rates checked 2026-09-15: U3.5 $0.21/audio-hour; diarization $0.02; contextual
prompt $0.05; keyterms $0.05; low-effort speaker identification $0.02. Thus the
default legacy recipe estimates $0.30/hour and the updated recipe $0.33/hour.
Recheck [AssemblyAI pricing](https://www.assemblyai.com/pricing) before relying
on these rates in the future. No AssemblyAI dashboard chat is used.

Word counts and recognition confidence are diagnostic metrics, not accuracy
scores. A winner needs a reference transcript or listening to the same passages.
Check proper names, omitted dialogue, invented text, overlap and actual human
speaker attribution. The generated report deliberately leaves `winner` unset.

## Outputs, retries and cache

All results live in the output directory - `~/.local/share/skaldkeep/transcribe/` by
default (`$XDG_DATA_HOME`, `$SKALDKEEP_TRANSCRIBE_OUTPUT` or `--output-dir` override it), outside
the skill and outside any project, because transcripts are private campaign content. Each job
directory includes `result.json` and `state.json`. Its `views/` directories hold `transcript_raw.txt`,
`transcript_utterances.txt` (the historical `[Speaker:X] text` format),
`transcript_timed.txt` and a run summary. Timed text uses the original recording's
offset, including when only an excerpt was sent. Separate recordings have
independent speaker labels; do not equate Speaker A across separate jobs. Views
retain the source path, hash and offset so identical audio clips at different
positions can reuse one paid job without overwriting each other's timestamps.

Cache identity includes the source SHA-256, complete request configuration,
endpoint and pipeline version. Files from the old audio-only cache are not
silently reused. A completed empty transcript is also cached. Job files are
written atomically with mode 0600 and guarded against simultaneous submissions.

Once a job ID is returned it is saved before polling. Run the exact same command
to resume after a polling timeout or network failure. A timeout, malformed success
response or server failure during submission may mean the paid request was
accepted: these become `submission_uncertain`, and rerunning will stop instead
of paying twice. Investigate the stored job and the AssemblyAI transcript list.
No undocumented idempotency header or automatic POST retries are used. HTTP 401,
403 and 429 mean no job was created, so the job returns to `new` and the same
command can be rerun once the key or rate limit is fixed. Rejected (400/404/422)
and terminal error jobs remain recorded and are not automatically repeated. A 400
or a failed transcription also discards the cached upload URL, so deleting the
job's `state.json` to retry uploads the audio again. An upload is only cached if the file still matches its
hash afterwards.

HTTPS sources additionally need `--url-version` (an immutable content version or
checksum) and `--source-duration` in seconds. Local measurement, gain and excerpts
require a local file. Existing US endpoint usage is preserved.

## Verified API references

- [Model selection](https://www.assemblyai.com/docs/pre-recorded-audio/select-the-speech-model)
- [Prompting and keyterms](https://www.assemblyai.com/docs/pre-recorded-audio/universal-3-5-pro/prompting)
- [Code switching](https://www.assemblyai.com/docs/pre-recorded-audio/code-switching)
- [Speaker identification](https://www.assemblyai.com/docs/speech-understanding/speaker-identification)
- [Submit schema](https://www.assemblyai.com/docs/pre-recorded-audio/api-reference/transcripts/submit)

The dashboard chat's claim that `temperature` is unsupported contradicts the
submit schema. Keep 0, without promising bit-for-bit deterministic recognition.
No undocumented `include_speaker_confidence` parameter is sent. Word confidence
must not be interpreted as certainty about a speaker's identity.

## Campaign profiles

A profile (YAML or JSON) holds the table's speakers, language, context prompt and keyterms.
Start from `scripts/campaigns/example.yaml`. `--campaign` takes either a path to a profile file
or a profile name, looked up in:

1. `--campaign-dir`, if given; otherwise
2. `$SKALDKEEP_TRANSCRIBE_CAMPAIGNS`, or `~/.config/skaldkeep/transcribe/campaigns/`
   (`$XDG_CONFIG_HOME` respected); then
3. the bundled `scripts/campaigns/` (only `example`).

Keep real profiles out of the skill folder: a skill update replaces it, and profile names and
keyterms are campaign content. `--list-campaigns` shows what is found where.
