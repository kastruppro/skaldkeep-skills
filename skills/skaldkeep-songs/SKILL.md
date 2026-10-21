---
name: skaldkeep-songs
description: >-
  Write recap songs for a tabletop RPG session and store the lyrics in Skaldkeep: song event
  list, several song concepts, full lyrics, a Suno v6 prompt package (styles, exclusions,
  settings), then a song recap via upsert_recap. Use when the user says "make a song", "lav en
  sang", "lav sange til sessionen", "write the recap song", "song concepts for session 12",
  "Suno prompt", "revise the lyrics", "mashup of our two songs", or answers yes to "Should we
  make songs for this session?". Covers lyric review so an absent player can follow the story,
  model comparison and revisions. Audio is generated in Suno and uploaded by a human in the
  Skaldkeep web app; this skill only stores the text.
license: MIT
---

# Recap songs for a session

A session song is a recap for a player who missed the session: the sung words alone must
explain who did what, why, and what changed. Musical quality matters, but comprehension comes
first. The full method - narrative techniques, lyric review, Suno models, settings and
mashups - is in [references/suno-guide.md](references/suno-guide.md). Read it before writing
lyrics.

## Step 1 - Gather the session

- Campaign `ref` and session slug. Use `get_document(campaign_slug, slug="session-12")` and
  the linked NPC/location/quest pages; if the user has a transcript, the session note is still
  the canonical account.
- `list_recaps(campaign_slug)` - read a few earlier song lyrics for this campaign: recurring
  hooks, voice conventions, what worked. Never reuse their verses for a new concept.
- Ask for standing preferences if unknown: styles to avoid, preferred Variety, voices, how
  many concepts to review.

## Step 2 - Event list first (no lyrics yet)

Fill the [song event list](references/song-event-list.md): the event table (actor, goal,
action, reason and consequence, tone), a literal recap for an absent player, key quotes,
memorable moments and the concept proposals. Keep unknowns unknown. It is a working document:
keep it local, or store it as a `personal` `note` if the user wants it in Skaldkeep.

## Step 3 - Concepts

Propose the number of concepts the user asked for. Each concept covers the whole session and
differs in genre, rhythm, instrumentation and vocal delivery - not just the label. Let the user
pick before writing full lyrics.

## Step 4 - Lyrics and package

For each chosen concept write new lyrics from the event table (not from another concept), then
run the **required lyric review** from the guide: read it as plain speech and check that the
starting situation, people, choices with reasons, and the ending are all in the sung words.
Then check fidelity against the session. Deliver in this order: title, lyrics, styles,
exclusions, model + settings, title again - each in its own fenced block. Use `[End]` or
`[Fade Out]` at the end.

If several concepts are written in parallel, you may dispatch one subagent per concept with
the event table and the guide; review every result yourself before presenting it.

## Step 5 - Generation (only if asked)

The user normally pastes the package into Suno. Submit through the user's account only on an
explicit request, following the guide's generation checklist (read back every field, one
Create per song/model pair, record outputs).

## Step 6 - Store the chosen lyrics in Skaldkeep

Check access (`get_my_access` - needs `manage_recaps`) and existing recaps, then:

```
upsert_recap(campaign_slug=<ref>, session_slug="session-12", kind="song",
             title="The Drowned Bell", text="<final lyrics>")
```

Pass `recap_id` to update an existing song instead of creating a duplicate. The recap stays
hidden while its session document is unpublished. Tell the user to upload the audio on the
session page in the web app.

## Rules

- Comprehension and fidelity before style. No invented events, causes or certainties.
- New lyrics per concept; deliberate reuse only for model comparisons, revisions and mashups.
- Respect the group's standing style exclusions in every concept, including revisions.
- Never present text review as a listening judgement; say what was actually checked.
- Plain hyphens, no em/en dashes.
