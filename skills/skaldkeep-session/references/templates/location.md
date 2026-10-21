# Location template

Maps to a Skaldkeep **`location`** document.

- `upsert_document(type="location", title="Location Name", slug="location-name", visibility="player", frontmatter={...}, body="...")`.

## Frontmatter facets (`location`)

| key | value |
|-----|-------|
| `region` | parent region / city |
| `location_type` | `city` \| `village` \| `dungeon` \| `building` \| `landmark` \| `plane` |
| `status` | `active` \| `destroyed` \| `abandoned` \| `unknown` |
| `parent_location` | location slug of the direct parent (e.g. the building a room is in) |
| `first_visited` | session number |
| `last_visited` | session number |

## Body skeleton

```markdown
# Location Name

## Quick reference
**Region:** [[parent-location-slug]]
**Type:** ...
**Status:** ...

## Description
Physical description, atmosphere, notable features.

## Notable areas
### Area
- What is here, what happened.

## NPCs found here
- [[npc-slug]] - role at this location

## Items found here
- [[loot-slug]] - where / how found

## Events at this location
- Session X: what happened

## Connections
- [[other-location-slug]] - how connected (road, portal, ...)
- [[quest-slug]] - related quest
```
