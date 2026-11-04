# Skaldkeep built-in MCP tools

The Skaldkeep skills drive these tools - they never re-implement them. They are served by
Skaldkeep's built-in MCP, mounted at `<SKALDKEEP_BASE_URL>/mcp` and authenticated with a
bearer personal access token (`Authorization: Bearer skp_...`). Every tool goes through the
same service layer as the REST API, so writes get identical link-graph maintenance,
revision history, and visibility enforcement.

A token acts **as its user**: own-scope rules (personal documents, own-PC editing) apply
exactly as they do in the web app. Denied calls name the missing capability. A token can be
scoped to one campaign or left unscoped (all campaigns); an out-of-scope `campaign_slug`
resolves as not-found.

> Snapshot of the Skaldkeep server's tool definitions (41 tools, checked 2026-11-04 against server 0.2.9). Treat the
> live server's instructions and each tool's own description as authoritative if they differ,
> and use only the tools the connected server actually lists - a self-hosted instance may be older.

## Start here

| Tool | Kind | Purpose |
|------|------|---------|
| `get_my_access(campaign_slug)` | read | Role, capability flags, and whether DM content is in scope (`sees_dm_content`). **Call first.** |
| `get_type_schema(type)` | read | Frontmatter facet keys and value conventions for a document type. Call before the first write of a type. |
| `list_campaigns()` | read | Campaigns this token can access, with role + capabilities. The `ref` field is the `owner/slug` to pass as `campaign_slug`. |

## Reading

| Tool | Kind | Purpose |
|------|------|---------|
| `list_documents(campaign_slug, type=None)` | read | Document summaries, optionally filtered by type. Includes schema-driven `facets` and rich-card `card_fields` without sending complete frontmatter. |
| `get_npc_overview(campaign_slug)` | read | Visibility-safe NPC activity: appearance and incoming-link counts, whether each NPC appeared in the five latest visible sessions, last visible session, and a conservative `suggested_one_off` signal. |
| `get_document(campaign_slug, slug, draft=False)` | read | Full document: frontmatter, body, `current_revision_id` (needed for updates), and `dm_notes` only when the token holds `access_dm_notes` (the DM's alone; a co-DM scribe reads hidden documents but never the `dm_notes` field). `draft=True` reads the pending staged content (needs `write_player_content`) and adds `has_pending_draft`, `draft_revision_id` (null when there is no draft), `base_revision_id` and `stale` (the live page moved on since the draft was made); on a published page without a draft it errors with "document has no pending draft". |
| `get_loot_history(campaign_slug, slug)` | read | Revision-derived public inventory changes for one loot document, newest first. Covers custody, ownership, storage, container, attunement, quantity/charges, related quest and status; never returns bodies, `dm_notes`, arbitrary frontmatter or authors. Pending drafts are visible only with `write_dm_content`. |
| `search_documents(campaign_slug, query, type=None, visibility=None, facets=None, limit=10)` | read | Hybrid **semantic + keyword** match when the instance has an embedding provider; keyword-only otherwise. `visibility` only ever narrows what the token may already see; `facets` are exact-match frontmatter key/value pairs and **require `type`**. Each hit carries a `match` kind (`semantic`/`keyword`). Limit capped at 50. |
| `list_recaps(campaign_slug, session_slug=None)` | read | Session recaps (song lyrics / narration scripts). |
| `get_link_graph(campaign_slug, slug)` | read | Outgoing + incoming `[[wiki-links]]`; unresolved outgoing targets are "wanted pages". |
| `get_timeline(campaign_slug)` | read | Sessions in chronological order (by frontmatter `session` number, then date). Each event carries `slug`/`title`/`session_number`/`date`/`status` and `entity_counts` - how many resolved, visible entities it introduced, per document type. |
| `diff_since(campaign_slug, snapshot_name)` | read | Documents added/changed/removed since a named snapshot. |
| `list_staging(campaign_slug)` | read | Documents staged for review (not yet published), grouped by batch (commit). Requires `write_player_content` (the DM or a scribe); without `read_dm_content` hidden (`dm_only`) staged documents are omitted. Use it to report what is waiting for a human to publish, or to confirm a batch label before `publish_staging_batch`. |
| `list_snapshots(campaign_slug)` | read | Campaign snapshots (`name`, `created_at`), newest first. Use before creating a baseline and as the source for `diff_since`. |

## Writing

| Tool | Kind | Capability required | Notes |
|------|------|---------------------|-------|
| `upsert_document(campaign_slug, slug, type, title, body="", frontmatter=None, dm_notes=None, visibility="player", base_revision_id=None, expected_draft_revision_id=None, publish=False, batch_label=None)` | write | `write_player_content`; `visibility="dm_only"` also needs `write_dm_content`; writing `dm_notes` needs `access_dm_notes` (without it existing notes are preserved); `visibility="personal"` needs `write_own_notes` | Creates a revision and syncs the wiki-link graph. Omitted `dm_notes=None` preserves existing private notes; an explicit empty string clears them when authorized. **STAGING is the default** (`publish=False`): a new doc stays hidden from players and an edit to a published doc is parked as a draft (players keep seeing the live version), grouped into a batch named by `batch_label` - pass a stable label for a whole run (e.g. the session title). Pass `publish=True` to go live immediately. On updates pass `base_revision_id` (from `get_document`); a conflict error means it changed since you read it. Not required when staging, but a staged write that passes a base still conflicts if the live revision moved on, and an existing never-published page always requires it. Replacing a pending draft requires `expected_draft_revision_id` (the `draft_revision_id` from `get_document(draft=True)`); a draft in another batch is refused until it is reviewed. `publish=True` on a published page with a pending draft this token cannot review (e.g. a player editing their own PC while the DM has staged changes) writes the live page and keeps the draft; the result then reports `draft_revision_id` null and `staged` false. Returns `slug`, `current_revision_id`, `draft_revision_id`, `incoming_links_resolved`, `staged`, `published`. |
| `append_to_document(campaign_slug, slug, body_append=None, frontmatter_set=None, publish=False, batch_label=None)` | write | Existing document write authority | Server-side read-modify-write: append markdown and/or shallow-merge frontmatter without resending the full document. Preserves type, title, visibility, and `dm_notes`; stages by default. When a draft is pending it appends to the draft; a stale draft (the live page moved on) is refused until it is reviewed. |
| `upsert_documents(campaign_slug, documents, publish=False, batch_label=None)` | write | Per-item document write authority | Atomic bulk twin of `upsert_document`, up to 50 documents in one staging batch. Items take the same fields, including `base_revision_id` and `expected_draft_revision_id`. Any invalid or unauthorized item, or one with a stale `base_revision_id`, rolls back the entire call. |
| `update_npcs(campaign_slug, slugs, prominence=None, location=None, faction=None, status=None, publish=False, batch_label=None)` | write | `write_player_content`; hidden NPCs additionally require their normal document authority | Atomically patches only the four safe NPC-directory fields on up to 50 existing campaign NPCs. Stages by default and refuses to cross an existing review-batch boundary. |
| `update_quests(campaign_slug, updates, publish=False, batch_label=None)` | write | `write_player_content`; hidden quests additionally require their normal document authority | Atomically patches up to 50 existing campaign quests. Each update needs `slug` plus one or more of `quest_type`, `status`, `priority`, `character`, `parent_quest`, `quest_giver`, `location`, `next_step`, `deadline`, `progress_current`, `progress_total`, `started`, `completed`; `null` removes an optional field. A resulting `quest_type: personal` requires a non-empty `character`; `parent_quest` must name an existing top-level quest (one level deep). Different quests may receive different changes. Bodies, visibility, and `dm_notes` are preserved; staging is the default and any invalid item rolls back the whole call. A live update refuses unpublished quests and pending drafts, which must be handled in the review queue first. |
| `upsert_recap(campaign_slug, session_slug, kind, title, text="", visible_to_players=None, sort_order=None, recap_id=None)` | write | `manage_recaps`; hiding a recap needs `read_dm_content` | `kind="song"` holds lyrics, `kind="narration"` the "Previously On" script - both in `text`. Pass `recap_id` to update. Audio is uploaded by a human in the web app. |
| `rename_document(campaign_slug, slug, new_slug)` | write | `write_player_content` | Rename a document's slug and rewrite every `[[wiki-link]]` pointing at it across other bodies/`dm_notes` and recap texts in one call. The OLD slug is kept as a redirect alias so existing links and exports still resolve. Campaign documents only (not personal); `new_slug` is slugified server-side (a title or a slug both work). Returns counts: `documents_rewritten`, `links_rewritten`, `recaps_rewritten`. A non-DM caller cannot rewrite hidden/personal docs' links (they are skipped). |
| `archive_pc(campaign_slug, slug, status, quest_slugs=None, publish=False, batch_label=None)` | write | `write_player_content` to stage; `write_dm_content` to `publish=True` | Archive a player character (`status` = `paused`/`retired`/`dead`) and move its **open** personal quests (active/available) to `paused`; terminal quests (completed/failed/abandoned, on the live page or in a pending draft) are never touched. `quest_slugs` picks which open quests to cascade - omit for all, `[]` to archive the PC alone. **STAGES by default** for the DM to approve in the Review tab. **Never archive autonomously while processing a session** - stage a proposal and let the human confirm. |
| `revive_pc(campaign_slug, slug, quest_slugs=None, publish=False, batch_label=None)` | write | `write_player_content` to stage; `write_dm_content` to `publish=True` | Revive an archived PC (status `active`) and resume its `paused` personal quests (`paused` -> `active`). `quest_slugs` picks which to resume - omit for all, `[]` to revive the PC alone. Same staging rules as `archive_pc`. |
| `publish_staging_batch(campaign_slug, batch_label)` | write | `write_player_content`; a batch containing hidden (`dm_only`) documents needs `write_dm_content` | Publish every staged change in a batch (commit), making it live for players. Normally a human reviews and publishes in the web app - use this only when explicitly asked to publish. |
| `create_campaign_snapshot(campaign_slug, name)` | write | `manage_snapshots` | Tags the current state of every document (e.g. "After Session 24"); powers the what-changed diff. |
| `delete_snapshot(campaign_slug, name)` | write | `manage_snapshots` | Permanently deletes a named snapshot and its pinned revision rows. |
| `rebaseline_snapshot(campaign_slug, name)` | write | `manage_snapshots` | Re-pins an existing snapshot to the campaign's current revisions while preserving its original creation time. |
| `reindex_embeddings(campaign_slug)` | write | `write_player_content` | (Re)build semantic-search embeddings so search reflects the current content. No-op (`enabled=false`) when the instance has no embedding provider configured. |
| `upload_media(campaign_slug, filename, content_base64, mime)` | write | `upload_media`, or `write_own_notes` for images on the member's own notes/PC page | Document images (embedded with `![[filename]]`) or recap audio. Always embed the returned filename: collisions allocate a new name. Identical content+MIME deduplicates only the same uploader's uploads, including names allocated after a collision. Allowed: `image/png`, `image/jpeg`, `image/webp`, `image/gif`, `audio/mpeg` (mp3), `audio/mp4`/`m4a`, `audio/wav`, `audio/ogg`. Size is capped by the instance (50 MB decoded by default; larger MCP requests are refused with 413). |
| `list_session_desks(campaign_slug)` | read | `read_dm_content` | Saved desks, states and revision IDs; includes finished sessions. |
| `get_session_desk(campaign_slug, document_id)` | read | `read_dm_content` | Markdown notes, scene checklist and currently visible referenced documents. |
| `save_session_desk(campaign_slug, desk, document_id?)` | write | `read_dm_content` + `write_dm_content` + `write_player_content` | Create/update a hidden desk. `desk`: title, body, scenes (id/title/done), reference_ids, state planned/live, base_revision_id on updates. Lists replace. |
| `finish_session_desk(campaign_slug, document_id, base_revision_id)` | write | same as save | Atomically finish and create one hidden session draft in a review batch. Idempotent retry; never publishes. |
| `list_session_wishes(campaign_slug)` | read | campaign membership + personal visibility | Own/group-shared wishes; DM-only wishes are visible to the true DM role, never automatically to a co-DM scribe. |
| `save_session_wish(campaign_slug, wish, document_id?)` | write | `write_own_notes` + author ownership | Markdown body, title, optional quest_id, audience dm/group, state open/addressed, base_revision_id on update. Only acts as the token user. |
| `list_facet_values(campaign_slug, type, fields=None)` | read | `read_player_content` | Every value a filterable frontmatter field holds for one type, with counts, the documents holding each value, `allowed_values`, a `suggested_mapping` (case/spacing variants folded; slug-reference fields resolved to existing slugs) and `unresolved_slug_values`. `fields` defaults to the type's facet/badge fields. Pending-draft values are included (`in_pending_draft`). |
| `normalize_facet_values(campaign_slug, type, field, mapping, dry_run=False, publish=False, batch_label=None)` | write | `write_player_content` | Atomically rewrite one field across every visible document of a type: `mapping` is `{current: new}`, exact match after trimming, `null` removes the value; list fields are rewritten per element and de-duplicated. Bodies, titles, visibility and `dm_notes` untouched. `dry_run=true` returns `{slug, before, after}` changes without writing. Stages by default; max 200 documents per call; any error rolls back. |
| `list_transcripts(campaign_slug, unprocessed_only=False)` | read | `read_dm_content` | Session transcripts, newest play date first: `id`, `title`, `status`, `source` (`assemblyai` = transcribed by the server, `upload` = made elsewhere), `played_on`, `participants` (`name`, `character_slug?`), `session_slug`, `speaker_map`, `processed_at`. `unprocessed_only=true` returns completed transcripts nobody has written up yet. |
| `get_transcript(campaign_slug, transcript_id, offset=0, max_chars=60000)` | read | `read_dm_content` | One completed transcript's text, paged (max 200,000 characters per call); call again with `next_offset` until it is null. Server jobs render as `[HH:MM:SS] Speaker: text` with the DM's speaker names applied; `speaker_labels` lists the raw diarization labels. |
| `upload_transcript(campaign_slug, title, text, session_slug=None, played_on=None, participants=None, language=None)` | write | `read_dm_content` + `write_dm_content` | Store a transcript made outside Skaldkeep (max 4,000,000 characters). `played_on` is `YYYY-MM-DD`; when `session_slug` names an existing session page its `date` is set too (staged with that page's pending draft, if any). |
| `mark_transcript_processed(campaign_slug, transcript_id, processed=True, session_slug=None)` | write | `read_dm_content` + `write_dm_content` | Record that the session documentation was written from the transcript (or undo with `processed=false`). `session_slug` links the page and copies `played_on` into its `date`. |

`update_quests` requires unique 1-200 character slugs and at least one changed field per item.
Progress values are non-negative integers and `progress_current` cannot exceed
`progress_total`; `started`/`completed` are non-negative session numbers or canonical
`YYYY-MM-DD` dates. Reuse the pending draft's `batch_label`, or resolve that draft before
staging the quest under another batch.

## Staging model (important for AI session processing)

Writes that come from AI session processing should **stage, not publish**. `upsert_document`,
`append_to_document`, `upsert_documents`, `update_npcs`, `update_quests`, `archive_pc` and
`revive_pc` all default to `publish=False`:
each change lands in an open
**batch** (a reviewable "commit") that the DM approves in the web app's Review tab. Players
keep seeing the last published version until then - security by construction, and the human
stays in control of what becomes canon. Pass a stable `batch_label` across a whole run so all
of a session's edits group into one batch. Only publish (`publish=True` or
`publish_staging_batch`) when a human explicitly asks.

## Enums

- `DocumentType`: `session`, `npc`, `location`, `quest`, `loot`, `faction`, `pc`, `note`.
- `DocumentVisibility`: `player` (default), `dm_only`, `personal`.
- `RecapKind`: `song`, `narration`.
- Quest `quest_type`: `main`, `side`, `personal`; `status`: `available`, `active`, `paused`, `completed`, `failed`, `abandoned`; `priority`: `critical`, `high`, `medium`, `low`.
- PC archive `status`: `paused`, `retired`, `dead`. Quest cascade statuses: open = `active`/`available` -> `paused`.

See `type-schemas.md` for the per-type frontmatter facets.

## Session desks and player wishes

See [session-desks.md](session-desks.md) for examples and privacy rules.
Discover tools on the connected instance first: these additions are not deployed by
installing these skills. Do not fall back to publishing ordinary documents if a tool is missing.

Both features use revisioned markdown documents. Desk rows are `note`/`dm_only`;
wishes are `note`/`personal`. Typed writes reject stale or absent base_revision_id
on updates; resolve conflicts by reading and merging, never by blindly retrying.
`finish_session_desk` stages notes as a new **dm_only session**. The reviewer explicitly
chooses player visibility if appropriate. Scene preparation, reference lists, wishes and
private dm_notes are not copied. The desk becomes read-only in this workflow.

Wishes honor player_notes_enabled on creation and player_audience_sharing for group
sharing. The group is the current membership snapshot at save time, not anonymous
viewers or future members. `shared_with_dm` and audience describe the actual personal
sharing state; generic document audience edits may make a wish fully private.

## Session transcripts

Recordings uploaded in the web app (Transcripts page) are transcribed server-side when the
instance has an AssemblyAI key configured; the audio is deleted locally and at the provider
once the transcript is stored. Transcripts are DM/co-DM only. Typical AI flow:
`list_transcripts(unprocessed_only=true)` -> `get_transcript` (follow `next_offset`) -> write
the session documents with `played_on` as the session `date` -> `mark_transcript_processed`.
A transcript made elsewhere enters the same flow through `upload_transcript`.

## Facet cleanup

`list_facet_values` -> agree the mapping with the user -> `normalize_facet_values(dry_run=true)`
-> `normalize_facet_values`. One field per call; reuse one `batch_label` for a multi-field
cleanup. The **skaldkeep-facet-cleanup** skill walks through it.
