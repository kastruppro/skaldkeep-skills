# Session desks and player wishes

Available on app.skaldkeep.gg since release 0.1.0.300 (2026-09-06). Verify the connected
server's tool list before use, especially on self-hosted instances; installing these skills
does not change the server.

## Before the session

1. Call get_my_access for the selected campaign. Desk readers need read_dm_content;
   writers also need write_dm_content and write_player_content.
2. list_session_desks and get_session_desk locate a saved plan. Create one only when
   requested, using save_session_desk with title, markdown body, scenes and reference_ids.
   Reference IDs come from visible documents, not guessed UUIDs. Up to 40 scenes and
   50 references; title max 200, notes max 100,000 characters.
3. list_session_wishes returns only what the token user may read. Wishes for the DM
   role do not become available to a co-DM scribe. Wishes are suggestions, not canon.

Example desk input (the campaign and referenced IDs must be supplied by the user/server):

```json
{
  "title": "Next session",
  "body": "## Notes\n\nPreparations and observations.",
  "scenes": [{"title": "Meet the messenger", "done": false}],
  "reference_ids": [],
  "state": "planned"
}
```

## During the session

The web app's Session desk page saves a scene checklist, document references and markdown
notes. References open separately so the desk stays available. The reveal action requires
hidden-content write authority and refuses unpublished documents or pending drafts.
Use save_session_desk with document_id and desk.base_revision_id to update a desk;
include the complete intended scene/reference lists. Notes remain hidden but co-DM
readable. Use the ordinary private dm_notes field for material restricted to the DM role.

## Finish and review

finish_session_desk(document_id, base_revision_id) makes one hidden session draft and
closes the desk atomically. Repeating finish returns the same result. It does not publish,
copy wishes, copy prepared scenes/references or include private dm_notes.
The response's result_document and batch_id point to the existing review workflow.
Review the notes and choose visibility before publishing. Reuse this session document
when processing the transcript, rather than writing a second one. Generic document
editing/history/export remains available, but the finished desk's typed editor is read-only.

## Player wishes

The web form asks about the character's next goal, the lead to follow and the previous
session's highlight. It saves portable markdown; optional quest links use document UUIDs.
The author can update the text or mark a wish addressed. Only their own token may act
for them through save_session_wish. Maximum title 200 and body 20,000 characters.

- audience=dm: personal document shared with the true DM role and its author.
- audience=group: personal document also shared with the current campaign members at
  save time. New members are not added automatically. Anonymous visitors never qualify.
- Creation honors player_notes_enabled; group sharing honors player_audience_sharing.
- Updating requires base_revision_id. A 409/conflict means read, merge and retry;
  never discard concurrent content or remove the revision token.
- Wishes remain personal notes in regular document views/exports. Changing the audience
  there is respected by the dedicated list too. No alternate privacy boundary is introduced.

## Media uploads

Always use upload_media's returned filename in embeds and portrait metadata. A filename
collision allocates a distinct name instead of replacing another upload. Exact bytes and
MIME deduplicate only the same uploader's files. Ordinary uploads are not image replacement.
