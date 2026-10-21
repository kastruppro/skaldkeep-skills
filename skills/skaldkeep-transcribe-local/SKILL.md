---
name: skaldkeep-transcribe-local
description: >-
  Transcribe a tabletop RPG session recording locally with AssemblyAI (Universal-3.5 Pro,
  speaker labels, campaign keyterms, resumable paid jobs with a cost cap) and store the result
  in Skaldkeep with upload_transcript. Use when the user says "transcribe the session",
  "transskribér optagelsen", "lav et transskript", "transcribe this audio", hands over an audio
  file (m4a, mp3, wav, ...) and the Skaldkeep instance has no server-side transcription, or
  wants to compare transcription settings or fix a quiet recording. Requires uv, ffmpeg and an
  ASSEMBLYAI_API_KEY in the environment. Not needed when the DM can upload the audio on
  Skaldkeep's Transcripts page - prefer that.
license: MIT
compatibility: Requires uv, ffmpeg/ffprobe, network access to api.assemblyai.com, and macOS or Linux.
---

# Local session transcription

A fallback for Skaldkeep instances without server-side transcription. It sends audio to
AssemblyAI, which is paid per audio hour, so always dry-run first.

**Check first:** if the instance has transcription configured, the DM should upload the audio
on the web app's Transcripts page instead (several files per session, speaker names, audio
deleted afterwards). Then the **skaldkeep-session** skill reads it with `get_transcript`.

## Requirements

| Need | Check |
|------|-------|
| `uv` | `uv --version` (installs Python deps from the script's inline metadata) |
| `ffmpeg` + `ffprobe` | `ffprobe -version` - needed for local files (duration, cost guard, gain, excerpts) |
| AssemblyAI key | `ASSEMBLYAI_API_KEY` in the environment, or a line in `./.env` of the current directory. Never pass it on the command line, never print it, never write it into a committed file. |

All commands below run the bundled `scripts/run.sh` from this skill's directory.

## Step 1 - Campaign profile

A profile names the human speakers and the vocabulary. Ask whether the user has one; if not,
copy `scripts/campaigns/example.yaml` to
`~/.config/skaldkeep/transcribe/campaigns/<campaign>.yaml` and fill in with the user:
`speakers_expected` (humans including the GM, not characters), `speaker_names`,
`language_code` (`en_us`, `da`, or `auto` for mixed), `context_prompt` and `keyterms_prompt`
(character, place and faction names; max six words per phrase). Keep profiles out of the skill
folder. `scripts/run.sh --list-campaigns` shows what is found.

## Step 2 - Dry run (no upload, no cost)

```bash
scripts/run.sh "<audio>" --campaign <campaign> --dry-run
# someone absent this session:
scripts/run.sh "<audio>" --campaign <campaign> --absent Player2 --dry-run
```

Show the user the planned speaker count and `estimated_max_usd`. The default cap is $2 per run
(`--max-cost-usd`). Several files for one session: transcribe each, or join them first only
if they are one continuous recording.

## Step 3 - Transcribe (in the background)

Run the same command without `--dry-run` as a background job; sessions take minutes. Keep
working on session preparation meanwhile (`get_my_access`, `list_documents`, ...). It prints
the path of `transcript_timed.txt` when done. The output directory defaults to
`~/.local/share/skaldkeep/transcribe/`, outside any repository.

- Interrupted or timed out: rerun the exact same command - it resumes the saved job and never
  pays twice.
- `submission_uncertain`: stop. The paid request may have been accepted; check the AssemblyAI
  dashboard before anything else.
- 401/403: key wrong or missing; 429: rate limit - fix and rerun the same command.

Quiet audio, excerpts, method comparisons and the cache rules are in
[references/transcription.md](references/transcription.md).

## Step 4 - Store it in Skaldkeep

The transcription itself needs no MCP; storing it needs Skaldkeep's MCP tools (`list_campaigns`,
`get_my_access`, ...). If they are not available, the MCP server is not set up yet: stop and
tell the user, then set it up with the **skaldkeep-connect** skill. If that skill is not
installed: the server is `https://app.skaldkeep.gg/mcp` (or the user's own instance + `/mcp`),
Streamable HTTP, header `Authorization: Bearer <token>`, with a token created under
Settings > Access tokens and kept in the `SKALDKEEP_TOKEN` environment variable.

1. Read `transcript_timed.txt`. Lines look like `[00:01:02.300 - 00:01:05.900] [Speaker:A] text`.
   Labels are anonymous (A, B, ...). If the user confirms who is who, replace the labels with
   names; never guess a mapping.
2. Upload it (needs `read_dm_content` + `write_dm_content`; max 4,000,000 characters):

```
upload_transcript(campaign_slug=<ref>, title="Session 12", text="<transcript text>",
                  played_on="YYYY-MM-DD", session_slug="session-12",
                  participants=[{"name": "Riley", "character_slug": "brannoc-ashvale"}],
                  language="en")
```

3. Report the transcript `id`. Continue with the **skaldkeep-session** skill if the user wants
   the session written up.

## Rules

- Dry-run before every paid run and respect the cost cap; ask before raising it.
- The transcript and audio are private campaign content: never commit them or copy them into
  a repository, and do not paste long transcript passages into chat.
- Speaker identification (`--identify`) only produces hypotheses; label mapping needs the
  user's confirmation.
