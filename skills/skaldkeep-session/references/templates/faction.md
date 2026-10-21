# Faction template

Maps to a Skaldkeep **`faction`** document.

- `upsert_document(type="faction", title="Faction Name", slug="faction-name", visibility="player", frontmatter={...}, body="...")`.

## Frontmatter facets (`faction`)

| key | value |
|-----|-------|
| `type` | `guild` \| `cult` \| `noble house` \| `order` \| `gang` \| `pantheon` |
| `alignment` | free text |
| `relationship` | `ally` \| `enemy` \| `neutral` |
| `status` | `active` \| `disbanded` \| `destroyed` \| `unknown` |
| `location` | location slug of their seat / base |

## Body skeleton

```markdown
# Faction Name

## Quick reference
**Type:** ...
**Relationship:** ...
**Status:** ...
**Base:** [[location-slug]]

## Overview
Goals, reputation, how they operate.

## Notable members
- [[npc-slug]] - role in the faction

## History with the party
- Session X: what happened.

## Connections
- [[faction-slug]] (rival / ally) / [[location-slug]] / [[quest-slug]]
```
