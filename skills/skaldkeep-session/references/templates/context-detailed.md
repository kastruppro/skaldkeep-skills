# Context Detailed template

A comprehensive session reconstruction for deep AI analysis: full timeline, quotes, lore, mechanics.

Where it goes (your choice - see "Where do the context files go?" in `references/workflow.md`):

- **Local-only (default):** keep it in your working folder.
- **In Skaldkeep:** write as a `note` document with `visibility="personal"` (private to you): `upsert_document(type="note", slug="session-xx-detailed", title="Session XX Detailed", visibility="personal", frontmatter={"session": "session-xx"})`.

## Skeleton

```text
# Session XX Detailed Context

SESSION: XX - Title
DATE: YYYY-MM-DD
PARTY: <names> (note who was present)

## TIMELINE
Chronological narrative in past tense. Include:
- Where the session started and ended
- Every significant location (room-by-room for dungeons)
- All NPC interactions with key dialogue
- Combat encounters (who fought what, who nearly died)
- Discoveries, revelations, plot developments
- Party decisions and their reasoning
- Any party splits and what each group did
- Mechanical details that matter (funny failed rolls, crits, near-deaths)

## IMPORTANT QUOTES
- "[Quote]" - [Speaker], [context]

## LORE LEARNED
- [What was learned and from whom/where]

## NEW NPCS
[Name] - [Race/Gender] - [Role] - [Key details] - [Current status/location]

## RETURNING NPCS
[Name] - [What they did this session] - [Status update]

## LOCATIONS DETAILED
[Location]: [What it looks like, what was found, what happened]

## ITEMS ACQUIRED
[Item]: [Who has it] - [What it does/is worth]

## QUEST/PLOT UPDATES
[Quest]: [What progressed, what was learned]

## PARTY STATUS AT SESSION END
- Location / Condition / Immediate goals

## UNRESOLVED THREADS
- [Thread]: [Current status]

## MEMORABLE MOMENTS (for songs/recaps)
- [Funny/dramatic/cool moment]: [What happened and who was involved]

## SESSION CLIFFHANGER
[How the session ended - what tension hangs over the next one]
```

Format: plain prose, minimal markdown, easy to parse. Include everything that might matter later.
