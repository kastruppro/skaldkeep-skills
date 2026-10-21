# Session Note template

Maps to a Skaldkeep **`session`** document.

- Write with `upsert_document(type="session", title="Session XX: Title", slug="session-xx", visibility="player", frontmatter={...}, body="...")`.
- The `frontmatter` dict carries the facets below; `body` is the markdown.
- Bodies use `[[slug]]` wiki-links - the server resolves them and maintains the link graph. Run `get_type_schema("session")` for the live facet hints before the first write.

## Frontmatter facets (`session`)

| key | value |
|-----|-------|
| `session` | integer session number |
| `date` | `YYYY-MM-DD` |
| `party` | list of PC slugs present |
| `npcs` | list of npc slugs that appear |
| `locations` | list of location slugs visited |
| `items_acquired` | list of loot slugs gained |
| `status` | `completed` \| `upcoming` |

## Body skeleton

```markdown
# Session XX: Title

**Date:** YYYY-MM-DD
**Party present:** [[pc-one]], [[pc-two]], [[pc-three]]

## Quick summary
> One paragraph for quick reference.

## Characters met
### New NPCs
- **[[npc-slug]]** - Race Gender - Role. "Memorable quote"
### Returning NPCs
- **[[npc-slug]]** - Updated status / interaction

## Places visited
### [[location-slug]]
- Description, what happened, what was found.

## Loot acquired
| Item | Description | Holder |
|------|-------------|--------|
| [[loot-slug]] | Description | [[pc-slug]] |

## Key events timeline
1. **Event** - brief description

## Important quotes
> "Quote" - Speaker, context

## Revelations & lore
- New information learned

## Unresolved threads
- [ ] Thread

## Party status at end
**Location:** where the session ended
**Condition:** health / resources
**Next steps:** what the party plans
```
