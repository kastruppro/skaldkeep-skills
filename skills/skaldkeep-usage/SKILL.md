---
name: skaldkeep-usage
description: >-
  How to read and write a Skaldkeep campaign correctly through its MCP tools. Use whenever you
  work with Skaldkeep documents, NPCs, locations, quests, loot, PCs, companions, recaps,
  snapshots, staging or the play schedule, e.g. "add this NPC to Skaldkeep", "update the quest", "what changed since last
  session", "publish the batch", "hide this from the players", "opdater kampagnen", "find X in
  Skaldkeep", or before any upsert_document, upsert_documents, append_to_document,
  publish_staging_batch or create_campaign_snapshot call. Explains owner/slug addressing,
  staging and review batches, append_to_document versus get + upsert, visibility (player,
  dm_only, personal), the DM-only dm_notes field, optimistic concurrency, snapshots and
  diff_since. Full tool list and per-type frontmatter schemas are in references.
license: MIT
---

# Using Skaldkeep's MCP tools

Skaldkeep stores a campaign as markdown documents with frontmatter and `[[slug]]` wiki-links.
Every write goes through the same service layer as the web app: it creates a revision, updates
the link graph and enforces visibility.

**First, check the MCP connection.** This skill needs Skaldkeep's MCP tools (`list_campaigns`,
`get_my_access`, ...). If they are not available, the MCP server is not set up yet: stop and
tell the user, then set it up with the **skaldkeep-connect** skill. If that skill is not
installed: the server is `https://app.skaldkeep.gg/mcp` (or the user's own instance + `/mcp`),
Streamable HTTP, header `Authorization: Bearer <token>`, with a token created under
Settings > Access tokens and kept in the `SKALDKEEP_TOKEN` environment variable.

## Start of every task

1. **Pick the campaign.** Campaigns are addressed as `owner/slug` - the `ref` field from
   `list_campaigns`. Pass it as `campaign_slug` to every tool. A bare slug works only while it
   is unique among the token's campaigns. If the user did not name one and `list_campaigns`
   returns several, ask.
2. **`get_my_access(campaign_slug)` first.** It returns the role, capability flags,
   `sees_dm_content` (hidden documents in scope) and `sees_dm_notes` (the private field in
   scope). This decides which writes will succeed and what you must never send.
3. **`get_type_schema(type)` before the first write of a type.** Consistent frontmatter keys
   power filters, badges, cards and the quest board. The live server wins over
   [references/type-schemas.md](references/type-schemas.md).
4. **`list_documents` / `search_documents`** to learn which slugs already exist, so you update
   rather than duplicate, and so your `[[links]]` resolve.

## Writing: stage, don't publish

- Every document write tool (`upsert_document`, `upsert_documents`, `append_to_document`,
  `update_npcs`, `update_quests`, `normalize_facet_values`, `archive_pc`, `revive_pc`)
  defaults to `publish=false`: the change lands in a **review batch** and players keep seeing
  the last published version.
- Pass one stable `batch_label` for a whole run (e.g. `"Session 12"`) so everything groups into
  one batch the DM approves in the web app's **Review** tab.
- Report what is waiting with `list_staging`. Call `publish_staging_batch(campaign_slug,
  batch_label)` or pass `publish=true` **only when the user explicitly asks to go live.**
- A document with a pending draft in another batch cannot be moved into yours by the metadata
  tools; reuse that batch's label or ask the DM to publish or discard it first.
- Recaps (`upsert_recap`) are written directly, not staged; they stay hidden while their
  session document is unpublished or hidden.

## Choosing the write tool

| Goal | Tool |
|------|------|
| Add text and/or set a few frontmatter keys on an existing doc | `append_to_document` - server-side read-modify-write; keeps type, title, visibility and `dm_notes`; no read-back needed |
| Create several docs, or a session's whole set | `upsert_documents` - up to 50, atomic, one batch, all-or-nothing |
| Create one doc, or fully replace a body | `upsert_document` - for an update, `get_document` first and pass its `current_revision_id` as `base_revision_id`, and send a complete merge that keeps untouched frontmatter, title, type and visibility |
| NPC directory fields (`prominence`, `location`, `faction`, `status`) | `update_npcs` |
| Quest-board metadata (status, priority, next step, progress, ...) | `update_quests` |
| One frontmatter field across many docs | `normalize_facet_values` (see **skaldkeep-facet-cleanup**) |
| Change a slug | `rename_document` - rewrites every `[[link]]`, keeps the old slug as an alias |
| Two pages are the same thing | copy unique facts into the survivor, then `merge_documents` - old name and slug become aliases, links rewritten, duplicate trashed. Not staged: only when the user asks |
| Delete a page | `delete_document` (trash, 30 days). Not staged: only when the user asks |
| Set a page's picture (any type) | `set_document_image` - it is also the page backdrop and the overview thumbnail |
| Give a PC a familiar, mount, steed or pet | `add_companion` - SRD template (`list_companion_templates`) or blank; `owner` = the PC slug; staged |
| PC leaves, dies, returns | `archive_pc` / `revive_pc` - staged proposal; never on your own initiative |

A conflict error on `base_revision_id` means the document changed since you read it: read it
again, merge, retry. Never drop the revision check to force a write.

If the document has a pending draft, `upsert_document` replaces the draft, not the live page:
read it with `get_document(draft=true)`, merge into that content, and pass its
`draft_revision_id` as `expected_draft_revision_id` (plus `base_revision_id`). A draft in
another batch, or a `stale` one, must be reviewed in the web app first.

## Visibility and privacy

| `visibility` | Who sees it | Writing it needs |
|--------------|-------------|------------------|
| `player` (default) | Every member (and link/public viewers) once published | `write_player_content` |
| `dm_only` | DM and co-DM scribes only | `write_dm_content` |
| `personal` | Only its author, the DM if `shared_with_dm`, and named readers | `write_own_notes`; cannot be changed to/from campaign visibility later |

- **`dm_notes`** is a separate field on a document, never in the body or frontmatter. Only the
  true DM role (`access_dm_notes`, `sees_dm_notes=true`) can read or write it. Without it,
  never send `dm_notes`; existing notes are preserved automatically on your edits.
- Without `sees_dm_content`, never send `visibility="dm_only"` - hidden documents simply do
  not exist for this token.
- Secrets players must not see go in `dm_notes` or a `dm_only` document, never in a
  player-visible body.
- Treat `personal` documents as confidential to their author: never copy their content into
  campaign-visible documents. Revealing a hidden doc = flip it to `player` through a normal
  write, so the reveal shows in the players' "since last time" digest.
- Personal quests and personally owned loot stay campaign documents (`quest_type: personal` +
  `character`, `item_role: personal` + `owner`); `visibility: personal` is access control,
  not ownership.

## Snapshots and "what changed"

- `create_campaign_snapshot(campaign_slug, name="After Session 12")` pins every document's
  current revision. Take it **after** the DM publishes a session batch, so it reflects what
  players actually got. Needs `manage_snapshots`.
- `list_snapshots` shows existing ones; `diff_since(campaign_slug, snapshot_name)` lists
  documents added, changed and removed since a snapshot. A campaign with no snapshot has no
  baseline - seed one ("Before Session 12") before publishing the first processed session.

## Conventions

- Slugs are lowercase and hyphenated (`brannoc-ashvale`, `session-12`). Link with `[[slug]]` or
  `[[slug|label]]`. Links to pages that do not exist yet become "wanted pages"
  (`get_link_graph`).
- Slug-reference frontmatter (`location`, `faction`, `holder`, `owner`, `party`, `npcs`, ...)
  holds slugs, not titles.
- Media (images, audio, PDF, MP4/WebM video, max 50 MB): `upload_media` (base64) for small
  files; `create_media_upload` + `curl -T` with a shell, or `import_media_from_url` without one,
  for anything larger. Embed `![[<returned filename>]]` - a name collision returns a different
  filename. Attach recap audio with `upsert_recap(audio_media_id=...)`; a recap's cover is the
  session page's `portrait` unless `upsert_recap(cover=<image filename>)` sets its own. Read media with
  `list_media` / `get_media` (signed download links).
- "When do we play next / who is away?": `get_play_schedule` (read-only; the schedule itself
  is edited in the web app).
- Bodies use H2 sections (`## Summary`, `## Events`); the app builds navigation from them.
- Use plain hyphens rather than em/en dashes in text you write.
- Use only tools the connected server lists. A missing tool means an older server: do the
  task with what exists, or tell the user - never emulate it with broader writes.

## References

- [references/mcp-tools.md](references/mcp-tools.md) - every tool with parameters and the
  capability it needs.
- [references/type-schemas.md](references/type-schemas.md) - per-type frontmatter keys, allowed
  values, facets and badges.
- [references/session-desks.md](references/session-desks.md) - session desks and player
  wishes (`list_session_desks`, `save_session_desk`, `finish_session_desk`, `save_session_wish`).
