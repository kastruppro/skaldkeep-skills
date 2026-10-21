# NPC template

Maps to a Skaldkeep **`npc`** document.

- `upsert_document(type="npc", title="NPC Name", slug="npc-name", visibility="player", frontmatter={...}, body="...")`.
- Secrets the players should not see go in `dm_notes` (requires the `write_dm_content` capability), never in the body.

## Frontmatter facets (`npc`)

| key | value |
|-----|-------|
| `race` | free text |
| `gender` | free text |
| `role` | occupation / role |
| `prominence` | `central` \| `recurring` \| `cameo` |
| `status` | `alive` \| `dead` \| `missing` \| `unknown` |
| `relationship` | `ally` \| `enemy` \| `neutral` |
| `location` | location slug (current whereabouts) |
| `faction` | faction slug (if affiliated) |
| `family` | family / house slug (if part of one) |
| `first_met` | session number |
| `last_seen` | session number |
| `portrait` | uploaded image filename; omit until the image exists in Skaldkeep |

`prominence` controls the NPC directory's focus view:

- `central`: a primary antagonist, patron, ruler, companion, or plot driver.
- `recurring`: expected to matter or appear again. This is the safe default when uncertain.
- `cameo`: an incidental, usually single-scene character whose details should remain searchable
  without filling the default NPC list.

Set `first_met` when the NPC is created and preserve it thereafter. Update `last_seen` whenever
the NPC appears in a processed session. Do not downgrade an existing NPC to `cameo` merely
because they have been absent recently; use campaign evidence and human review.

## Body skeleton

```markdown
# NPC Name

## Quick reference
**Race / Gender:** ...
**Role:** ...
**Status:** ...
**Current location:** [[location-slug]]

## Description
Physical description and key characteristics.

## Personality
How they behave, what they want.

## Key quotes
> "Quote" - Session X context

## History with the party
- Session X: what happened

## Connections
- [[other-npc-slug]] - relationship
- [[location-slug]] - connection
- [[quest-slug]] - involvement
```
