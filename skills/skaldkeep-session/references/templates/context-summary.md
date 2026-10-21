# Context Summary template

A quick-reference session summary for fast AI context loading. **Target: 200-400 words.**

Where it goes (your choice - see "Where do the context files go?" in `references/workflow.md`):

- **Local-only (default):** keep it in your working folder; do not push it to the instance.
- **In Skaldkeep:** write as a `note` document with `visibility="personal"` so it stays private to you: `upsert_document(type="note", slug="session-xx-summary", title="Session XX Summary", visibility="personal", frontmatter={"session": "session-xx"})`.

## Skeleton

```text
# Session XX Summary

SESSION: XX - Title
DATE: YYYY-MM-DD
PARTY: <who was present>

## What happened
<2-3 sentence overview of the main events.>

## Key plot points
- Point

## New information learned
- Lore / revelation

## NPCs involved
- Name: role and what they did

## Items acquired
- Item: who has it

## Current status
- Location: where the party is
- Next goal: what they plan to do

## Open threads
- Thread
```

Keep it factual and chronological - no narrative flourishes. Pair with the detailed context file for deep dives.
