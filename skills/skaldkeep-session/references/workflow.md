# Session workflow - details

The step list lives in `SKILL.md`. This file holds the rules that are too long for it.

## At a glance

```
recording uploaded in the web app (Transcripts page)
      |  server transcribes it          list_transcripts / get_transcript
      |  or: local fallback             skaldkeep-transcribe-local -> upload_transcript
      v
   transcript ---> skip the pre-game recap song and banter
      |
      v
   session note + entity pages ---> upsert_documents (staged, one batch_label)
   narration recap              ---> upsert_recap (direct, hidden until session is published)
      |                              mark_transcript_processed
      v
   DM reviews + publishes the batch in the web app's Review tab
      |
      v
   create_campaign_snapshot("After Session NN") ---> players see what changed
      |
      v
   "Should we make songs?" hand-off (skaldkeep-songs)
```

## Entity rules

### NPCs

- Keep the session document's `npcs` list complete and set each appearing NPC's `last_seen` to
  this session.
- On creation also set `first_met`, `role` and a deliberate `prominence`:
  - `central` - a primary plot driver (antagonist, patron, ruler, companion).
  - `recurring` - expected to matter again, or the evidence is uncertain. Safe default.
  - `cameo` - incidental, usually one scene.
- Preserve an existing `first_met` and normally an existing `prominence`. Do not downgrade an
  NPC because they have not appeared recently or because `get_npc_overview` flags
  `suggested_one_off`; report the suggestion instead.
- Set `portrait` only to a filename returned by `upload_media`.
- `update_npcs` patches only `prominence`, `location`, `faction`, `status` on up to 50 NPCs
  atomically. Use it for an explicitly requested directory cleanup, not as a side effect.

### Quests

- `update_quests` changes board metadata on up to 50 existing quests: each item is `slug` plus
  only the changed `quest_type`, `status`, `priority`, `character`, `quest_giver`, `location`,
  `next_step`, `deadline`, `progress_current`, `progress_total`, `started`, `completed`.
  `null` removes an optional field. One invalid item rolls back the whole call. Create new
  quests with `upsert_document(s)` first.
- A personal quest always has both `quest_type: personal` and a non-empty `character` (PC
  slug); change them together. It stays a campaign document (`visibility: player` or
  deliberately `dm_only`), never `visibility: personal`.
- Subquests carry `parent_quest: <top-level-quest-slug>`, one level deep.
- Lifecycle: set `started` when activation is first known and preserve it; set `completed` on
  completion; clear it only on an explicitly requested reopen. Do not move a terminal quest
  (`completed`, `failed`, `abandoned`) back to open unless asked.
- `publish=true` refuses unpublished quests and pending drafts; resolve those in Review.

### Loot

Keep these as separate facts, all slug-valued where they reference a document:
physical `item_type`, narrative `item_role`, `importance`, `owner`, `holder` (who carries it
now), `location` and `container` (where it is stored), `attuned_to`, `related_quest`.
Personally owned gear is `item_role: personal` + `owner: <pc-slug>`, still `visibility:
player`. Use `importance: minor` for incidental items. `get_loot_history` shows past custody
changes when you need to check them.

### PCs

- A player may edit their own PC page only if the DM allows it; do not rewrite other players'
  characters beyond facts from the session.
- `conditions`, `curses`, `abilities` are short chip strings; details go in the body.
- Inventory lives on loot documents (`holder`), not on the PC page.
- PC leaves, dies, goes on hiatus or returns: propose `archive_pc(status=paused|retired|dead)`
  or `revive_pc`, staged. The cascade only pauses or resumes the PC's open personal quests.
  Never archive autonomously.

### Bodies and replacements

- Append-only narrative changes: `append_to_document`.
- True body replacement: check for a pending draft with `get_document(draft=true)` (the error
  "document has no pending draft" means there is none). Without one, read the document and
  send a complete merge that preserves untargeted frontmatter, title, type, visibility and
  private fields, with `base_revision_id`. With one in this run's batch, merge into the draft
  content and also pass its `draft_revision_id` as `expected_draft_revision_id`. A draft in
  another batch, or a `stale` one, goes to the DM.
- Resolve `[[links]]` by writing the linked documents too. Unresolved links appear as wanted
  pages (`get_link_graph`).

## Session desks

When the connected server exposes `list_session_desks` / `get_session_desk` /
`list_session_wishes`:

- Read the desk the user selects; do not guess which desk matches a transcript. Planned scenes
  and player wishes are intentions, never proof of what happened.
- A finished desk already created one hidden (`dm_only`) session draft. Its `result_document`
  and `batch_id` point at it: reuse that document and its batch label, preserve its text when
  adding transcript material, and leave the visibility choice to the human reviewer.
- Call `finish_session_desk` only on an explicit request. It never publishes.
- A co-DM token does not see DM-only wishes; never look for them with another token. A wish
  belongs to its author - never copy a private wish into group-visible text, and do not mark
  wishes addressed on the author's behalf.

## Where do the context files go?

The context summary (200-400 words) and the detailed reconstruction are AI context, not canon.

- **Local only (default):** keep them in the user's working folder; do not push them.
- **In Skaldkeep:** a `note` with `visibility="personal"` and `frontmatter={"session":
  "session-12"}`, private to the token's user but available from any machine through MCP.

Pick one per group and stay consistent.

## Baseline snapshot

The players' digest always compares a snapshot with now. A campaign that was never
snapshotted shows an empty digest no matter what changed. If `list_snapshots` returns nothing
(on older servers without it: `list_documents` shows no session documents), seed
`create_campaign_snapshot(name="Before Session NN")` before the first publish. After that, the
"After Session NN" snapshot each time keeps the chain going.
