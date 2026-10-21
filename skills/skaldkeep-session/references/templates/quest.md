# Quest template

Maps to a Skaldkeep **`quest`** document.

- For a **new player-visible quest**, call `upsert_document(type="quest", title="Quest Name", slug="quest-name", visibility="player", frontmatter={...}, body="...", publish=false, batch_label="Session X")`.
- For an existing quest, use `update_quests` for board metadata and `append_to_document` for narrative appends. Replace the full document only after `get_document`, with its `base_revision_id`, complete merged content, preserved visibility, and no unresolved pending draft.

## Frontmatter fields (`quest`)

| key | value |
|-----|-------|
| `quest_type` | `main` \| `side` \| `personal`; `personal` requires `character` |
| `character` | non-empty PC slug required for a personal quest |
| `status` | `available` \| `active` \| `paused` \| `completed` \| `failed` \| `abandoned` |
| `priority` | `critical` \| `high` \| `medium` \| `low` |
| `quest_giver` | npc slug |
| `location` | location slug where the quest currently leads |
| `next_step` | short, actionable next step |
| `deadline` | in-world or real-world deadline, preferably YYYY-MM-DD |
| `progress_current` | completed objective count (integer) |
| `progress_total` | total objective count (integer) |
| `started` | session number or YYYY-MM-DD |
| `completed` | session number or YYYY-MM-DD |
| `parent_quest` | slug of the top-level quest this is a subquest of (one level deep) |

The quest board renders `quest_giver`, `location`, `next_step`, `deadline`, and progress
directly on its cards. Keep `next_step` concise and only set numeric progress when the quest
has a meaningful countable objective.

Filter facets are `quest_type`, `status`, `priority`, and `character`. Card-only fields are
`quest_giver`, `location`, `next_step`, `deadline`, `progress_current`, and `progress_total`.
Personal quests remain campaign documents with `visibility: player` or deliberately `dm_only`;
document `visibility: personal` is for private notes and does not belong on the quest board.

## Body skeleton

```markdown
# Quest Name

## Objective
What the party is trying to do.

## Progress
- Session X: what advanced, what was learned.

## Leads & open questions
- Unresolved threads.

## Connections
- [[npc-slug]] / [[location-slug]] / [[loot-slug]]
```
