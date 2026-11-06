# Song Event List template

The input for recap-song generation. **Complete this BEFORE writing any lyrics.**

First priority: an absent player must learn what happened from the song alone.
Respect the group's standing style preferences and exclusions (see `references/suno-guide.md`).

It is a working document (keep local, or store as a `personal` `note`). The finished
lyrics become a Skaldkeep **`song`** recap:
`upsert_recap(campaign_slug=<ref>, session_slug="session-xx", kind="song", title="<song title>", text="<lyrics>")`.
Attach the audio afterwards with `upsert_recap(recap_id=..., audio_media_id=...)` once it is uploaded (see the skill's Step 6).

## Skeleton

```text
# Session XX: Song Event Extraction

## Event table
| # | Who and where | Goal or problem | Action or decision | Reason and consequence | Tone |
|---|---------------|-----------------|--------------------|------------------------|------|
| 1 | Name the actors and place | What they needed | What they did | Why, and what changed; unknowns stay unknown | Funny/Dramatic/Tense/Epic/Sad |

## Literal recap for a player who missed the session
- Starting situation and objective:
- Main events, connected by their established reasons and results:
- Important relationships, promises and costs:
- Ending location, changed situation and unresolved question:

## Narrative references
- Older lyric(s) read:
- Specific storytelling technique to reuse:
- Weaknesses to avoid; source facts that require checking:

## Key quotes for lyrics
- "Quote" - Speaker (usable as a chorus or hook)

## Memorable moments (prioritise for the song)
1. Moment - why it is song-worthy

## Suggested song concepts
### Concept 1: <Genre> - "Title idea"
- Focus: which events to emphasise
- Full recap: how the whole session remains understandable in this concept
- Tone: overall mood
- Why it fits: how the genre matches the session
- Voice: solo / duet / group
- Musical contrast: how rhythm, instruments and delivery differ from the other concepts

## Session tone analysis
- Dominant mood: Serious / Comedic / Epic / Mysterious / Chaotic
- Combat intensity: None / Light / Moderate / Heavy
- Emotional beats: key emotional moments
- Recommended genre: based on the above
```

When you move to lyrics, follow `references/suno-guide.md`. Reminders:

- Explain the full session chronologically: who did what, why, and what changed.
- Attribute speakers and relationships in the sung words. A campaign's existing
  voice tags may guide the arrangement but do not guarantee speaker routing.
- Always include an `[End]` or `[Fade Out]` tag.
- Choose the length needed for a clear recap within the input limits; do not
  force it below 300 words. Cut empty repetition before necessary explanation.
- Read the lyrics as plain speech before generation: can an absent player
  retell the story without the event table or style instructions?
