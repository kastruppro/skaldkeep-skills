# Player Character template

Maps to a Skaldkeep **`pc`** document.

- `upsert_document(type="pc", title="Character Name", slug="character-name", visibility="player", frontmatter={...}, body="...")`.
- A player editing their own PC is allowed under the `write_own_notes` capability; respect ownership and avoid rewriting another player's character.

## Frontmatter facets (`pc`)

| key | value |
|-----|-------|
| `race` | free text |
| `class` | class / subclass |
| `player` | the player's name |
| `status` | `active` \| `paused` \| `retired` \| `dead` |
| `conditions` | list of short condition strings (kept brief - they render as chips) |
| `curses` | list of short strings |
| `abilities` | list of short strings |

## Body skeleton

```markdown
# Character Name

## Quick reference
**Player:** ...
**Race:** ...
**Class / Subclass:** ...
**Background:** ...

## Character concept
Brief description of who this character is.

## Backstory summary
Key points relevant to the campaign.

## Personal goals
- Goal

## Character development
### Session-by-session growth
- Session X: what happened, how they grew

### Key relationships
- [[npc-slug]] - relationship
- [[pc-slug]] - party dynamic

## Quotes
> "Memorable quote" - Session X
```
