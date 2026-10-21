---
name: skaldkeep-session
description: >-
  Turn a tabletop RPG session transcript or recording into Skaldkeep campaign documentation:
  the session note, new and updated NPC, location, loot, quest, PC and faction pages, a
  "Previously On" narration recap and AI context summaries, all staged for the DM to review,
  then a snapshot. Use when the user says "process session 12", "behandl session", "skriv
  sessionen op", "write up last night's session", "a transcript is ready", "import the session
  into Skaldkeep", "update the campaign from the transcript" or hands over a transcript or
  session audio. Prefers server-side transcripts (list_transcripts, get_transcript,
  mark_transcript_processed) and falls back to a local transcript file. Never publishes or
  archives a PC on its own. Not for writing recap songs (skaldkeep-songs) or general edits.
license: MIT
---

# Process a session into Skaldkeep

One run turns one game session into staged campaign documents through Skaldkeep's MCP tools.
The rules in the **skaldkeep-usage** skill apply throughout (staging, visibility, `dm_notes`,
revisions). If Skaldkeep tools are missing, use **skaldkeep-connect** first.

Create a todo per step below and work through them in order.

## Step 1 - Find the transcript (server first)

**Server transcript (preferred).** The DM uploads the recording on the web app's Transcripts
page and Skaldkeep transcribes it.

```
list_transcripts(campaign_slug=<ref>, unprocessed_only=true)
```

Each entry has `id`, `title`, `played_on` (real play date), `participants` (`name` +
optional `character_slug` - who was at the table), `session_slug` and `status`. Only
`completed` transcripts have text. Several waiting: ask which one; never guess.
`queued`/`submitting`/`processing`: not ready yet - tell the user. `error`, `rejected`,
`submission_uncertain`: the DM retries or deletes it in the web app; do not fix it over MCP.

**The user gave you a transcript file.** Store it first so the campaign keeps it and it gets
the processed marker:

```
upload_transcript(campaign_slug=<ref>, title="Session 12", text="<full text>",
                  played_on="YYYY-MM-DD", session_slug="session-12",
                  participants=[{"name": "Riley", "character_slug": "brannoc-ashvale"}],
                  language="en")
```

**Only raw audio, and the instance has no server transcription.** Use the
**skaldkeep-transcribe-local** skill; run it in the background and continue with Step 2.

## Step 2 - Prepare (one parallel fan-out)

Issue these together in a single turn - they do not depend on the transcript:

1. `get_my_access(campaign_slug)` - decides what you may write (`sees_dm_content`,
   `sees_dm_notes`).
2. `list_documents(campaign_slug)` - the existing slugs (update vs. create, links that resolve).
3. `get_npc_overview(campaign_slug)` if available - NPC activity; `suggested_one_off` is
   evidence, never permission to downgrade an NPC.
4. `get_type_schema(type)` for every type you may write (`session`, `npc`, `location`, `loot`,
   `quest`, `pc`, `faction`, `note`).
5. `list_snapshots(campaign_slug)` - if there is no snapshot at all (and no session documents),
   this is the first processed session: seed `create_campaign_snapshot(name="Before Session 12")`
   before anything is published.
6. `list_session_desks` if available - if the DM finished a desk for this session, reuse its
   `result_document` and batch instead of creating a second session page. Details in
   [references/workflow.md](references/workflow.md#session-desks).

Ask for what is still missing: campaign (if several), session number, and - only when the
transcript has no `participants` - who was present.

## Step 3 - Read the transcript

Page with `get_transcript(campaign_slug, transcript_id, offset=<next_offset>)` until
`next_offset` is null. Lines read `[HH:MM:SS] Speaker: text`. Use `participants` for who was
present and `played_on` as the session `date`.

Recordings usually open with last session's recap song and table banter. Start at the first
in-fiction beat (a DM scene-set, "so last time...", an in-character question); ignore
everything before it. For a very long transcript you may dispatch subagents to extract events
per chunk, then merge their notes in chronological order yourself.

## Step 4 - Plan the touched documents

List every document the session touches: the session note plus each NPC, location, item,
quest, PC and faction that is new or changed. For existing documents you will fully rewrite,
fan out the `get_document` reads in parallel to get each `current_revision_id`. For appends and
small frontmatter changes use `append_to_document` and skip the read. Entity rules (NPC
`prominence`/`first_met`/`last_seen`, quests, loot custody, PC lifecycle) are in
[references/workflow.md](references/workflow.md#entity-rules).

## Step 5 - Write everything, staged, in one batch

Generate all content first, then write it together. Prefer one `upsert_documents` call (up to
50 docs, atomic) with `batch_label="Session 12"`; otherwise parallel `upsert_document` calls
with the same label. Keep `publish=false`.

| Artifact | Target | Template |
|----------|--------|----------|
| Session note | `session` document | [session-note](references/templates/session-note.md) |
| Entity pages | `npc`, `location`, `loot`, `quest`, `pc`, `faction` | [npc](references/templates/npc.md), [location](references/templates/location.md), [loot](references/templates/loot.md), [quest](references/templates/quest.md), [pc](references/templates/pc.md), [faction](references/templates/faction.md) |
| "Previously On" | `narration` recap via `upsert_recap` | [previously-on](references/templates/previously-on.md) |
| Context summary / detailed | local file, or a `personal` `note` | [context-summary](references/templates/context-summary.md), [context-detailed](references/templates/context-detailed.md) |

Session document example:

```
upsert_documents(campaign_slug=<ref>, batch_label="Session 12", documents=[
  {"slug": "session-12", "type": "session", "title": "Session 12: The Drowned Bell",
   "visibility": "player",
   "frontmatter": {"session": 12, "date": "<played_on>", "party": ["brannoc-ashvale", ...],
                   "npcs": [...], "locations": [...], "items_acquired": [...],
                   "status": "completed"},
   "body": "<markdown with [[slug]] links>"},
  ...entity documents...
])
```

## Step 6 - Narration recap

```
upsert_recap(campaign_slug=<ref>, session_slug="session-12", kind="narration",
             title="Previously On - Session 12", text="<100-150 word script>")
```

Recaps are not staged but stay hidden until the session document is published. Audio is
uploaded by a human in the web app.

## Step 7 - Close the loop and report

1. `mark_transcript_processed(campaign_slug, transcript_id, session_slug="session-12")` - links
   the transcript and copies `played_on` into the page's `date`. Skip only if you stopped
   before writing the session document.
2. `list_staging(campaign_slug)` - tell the user exactly which documents wait in the batch and
   that the DM publishes it in the web app's **Review** tab. Publish yourself
   (`publish_staging_batch`) only on an explicit request.
3. If a PC left, died or returned, you may stage `archive_pc` / `revive_pc` as a proposal and
   say so. Never archive a PC on your own initiative.

## Step 8 - Snapshot after publishing

Once the DM has published the batch: `create_campaign_snapshot(campaign_slug,
name="After Session 12")`. This is what the players' "since last session" view compares
against. Needs `manage_snapshots`; without it, ask the DM to take it in the web app.

## Step 9 - Offer songs, never start them

End by asking:

> "Should we make songs for this session? How many concepts would you like to review?"

Only on a yes, continue with the **skaldkeep-songs** skill.

## Rules that always apply

- Stage every document write under one `batch_label`; never publish unasked.
- Without `sees_dm_content` never send `visibility="dm_only"`; without `sees_dm_notes` never
  send `dm_notes`. Secrets go in `dm_notes` or hidden docs, never a player-visible body.
- Never copy `personal` documents or private wishes into campaign-visible text.
- Pass `base_revision_id` on full rewrites of existing documents.
- Slugs lowercase-hyphenated; link with `[[slug]]`; fix wrong slugs with `rename_document`.
- Facts only from the transcript and existing canon; keep uncertainty uncertain.
- Plain hyphens, no em/en dashes.
