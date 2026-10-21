# Loot template

Maps to a Skaldkeep **`loot`** document.

- `upsert_document(type="loot", title="Item Name", slug="item-name", visibility="player", frontmatter={...}, body="...")`.
- Use `importance: minor` for incidental items that should render as compact inventory rows.
- Keep ownership, current holder, storage location/container and attunement separate.

## Frontmatter facets (`loot`)

| key | value |
|-----|-------|
| `rarity` | `common` \| `uncommon` \| `rare` \| `very rare` \| `legendary` \| `artifact` |
| `item_type` | `weapon` \| `armor` \| `wondrous_item` \| `potion` \| `scroll` \| `book` \| `treasure` \| `currency` \| `material` \| `consumable` \| `container` \| `mundane` \| `other` |
| `item_role` | `quest` \| `personal` \| `party` \| `lore` \| `ordinary` |
| `importance` | `featured` \| `standard` \| `minor` |
| `attunement` | `true`/`false`, or the attunement requirement text |
| `attuned_to` | PC slug currently attuned to the item |
| `owner` | PC/NPC/faction slug the item belongs to |
| `holder` | PC/NPC/faction slug currently carrying the item |
| `location` | location slug where it is stored or left |
| `container` | loot slug for the container holding it |
| `status` | `carried` \| `stored` \| `lent` \| `missing` \| `consumed` \| `sold` \| `destroyed` \| `returned` |
| `quantity` | non-negative stack count; 0 when consumed |
| `charges` / `charges_max` | remaining and maximum uses |
| `related_quest` | quest slug this item advances or unlocks |
| `acquired` | session number or YYYY-MM-DD |
| `origin` | where it came from |

All reference-valued fields contain slugs, not titles. Personally owned equipment remains
`visibility="player"` and uses `item_role: personal` plus `owner: <pc-slug>`.

## Body skeleton

```markdown
# Item Name

## Quick reference
**Rarity:** ...
**Type:** ...
**Attunement:** ...
**Owner:** [[owner-slug]]
**Held by / stored at:** [[holder-or-location-slug]]

## Description
What it looks like and what it does.

## History
- Session X: how it was acquired, notable uses.

## Connections
- [[npc-slug]] / [[location-slug]] / [[related-quest-slug]]
```
