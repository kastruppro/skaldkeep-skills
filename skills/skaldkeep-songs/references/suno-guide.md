# Suno session-song guide (v6 and v6-wild)

Interface and pricing observations were checked against Suno's official help pages and the
signed-in web interface at https://suno.com/create on 2026-09-15. Suno changes often: recheck
the model picker, limits and costs before relying on them.

## First priority: the listener learns what happened

Every session song is a recap for a player who missed the session. The listener may know the
campaign but must not need this session's notes. This comes before rhyme, atmosphere, genre
or a short runtime - though musical quality still matters.

Mentioning every event is not enough. The lyrics must say who did what, where, why it
mattered and what changed. Before polishing, read the lyrics as plain speech: can an absent
player retell the main sequence, decisions and consequences from those words alone? If not,
rewrite. A different model or a clearer vocal mix cannot supply missing explanation.

## Standing preferences

Ask the group (or read their notes) for standing preferences and record them in the package:
styles they never want, preferred Variety level, voice types, typical length. Apply an
exclusion even when an older song used that style - learn from its storytelling, not its
arrangement - and do not reintroduce the same sound under a renamed genre label.

For several concepts, vary rhythm, instrumentation, vocal delivery and arrangement, not just
the genre name. Changing the emotional focus over the same backing is not useful variety.

## Each concept needs newly written lyrics

Write every concept from the session's event table, not from another concept's verses. Give
each its own hook, imagery, line lengths, scene grouping and emotional arc. A new title, style
prompt or synonyms around the same verses is not a new song. Facts, names and an occasional
real session quote may recur; invented events must never be used to create variety.

Intentional reuse is right for:

- **A model comparison:** identical lyrics and inputs for v6 and v6-wild, same Variety.
- **A revision of a favourite:** keep the hook and strong lines, make the agreed fixes.
- **A requested mashup of existing songs:** reuse selected verses and hooks and record which
  versions supplied them (see Mashups).

## Models and cost

| Model picker | Purpose | Access |
|---|---|---|
| v6 Pro | Controlled, polished interpretation of a brief | Pro or Premier |
| v6-wild Pro | More exploratory arrangements | Pro or Premier |
| v6-mini | Lightweight quick exploration | All plans |

Wild is a separate model, not a high-Weirdness preset. These are Suno's descriptions, not a
guarantee that one sounds better. One standard Create submission produces **two tracks for 10
credits**; Max Mode costs extra. Count submissions separately from tracks and record the
actual balance change. v6 supports up to eight minutes per generation - a capability, not a
target. Sources: [model descriptions](https://help.suno.com/en/articles/13924737),
[v6 FAQ](https://help.suno.com/en/articles/13924481),
[what's new in v6](https://help.suno.com/en/articles/13924801).

## The Advanced form

The own-lyrics form is **Advanced** in the web interface (some help pages say Custom).
Observed 2026-09-15:

- Lyrics editor: 5,000 characters. Styles: 1,000 characters. Optional title.
- More Options: Exclude styles, Vocal Gender, Duration (Custom/Auto), Max Mode, Weirdness,
  Style Influence, Variety, Personalize.
- Switching model can reset Variety and Personalize - read the settings back after switching.
- A separate Cowriter prompt sits near the lyrics: paste prepared text into the Lyrics
  editor, then use **Create song**.

These are UI observations, not API contracts. Verify each visible value after adjusting it.

## 1. Establish the story

Extract a chronological event table from the processed session (see the event-list template):
actions, characters, decisions, gifts, consequences, quotes, the cliffhanger. Separate the
opening recap from new events.

- Write a short literal recap first: actor, action, established reason, result per beat. Do
  not invent a reason the source leaves unknown.
- Every concept covers the full session chronologically. Spreading necessary facts across
  several songs fails.
- Introduce important relationships and goals explicitly; concrete names, places and actions
  before poetic substitutes. "The roads are closing" must say which gates closed and why it
  matters.
- Keep cause, decision and consequence together. A hard choice is not a list of magic words.
- Keep uncertain identities, curses and suspected betrayals uncertain.
- Distinguish an absent player's character from one controlled by the GM.
- Let humour come from actual events, not from mocking a character's loss.
- Read relevant older lyrics in the campaign (`list_recaps`) before choosing references, and
  judge them on explanation and coverage.

### Narrative techniques that work

- **Set the scene immediately:** the first sung lines locate the party and state the problem.
- **One small scene per verse:** name the actor, show the attempt, give the result.
- **Explain the turning point:** a failed tactic, changed bargain or revelation gets its own
  words. Spell names and damage rolls do not replace cause and effect.
- **Make the hook specific:** anchor it in a mission, a real quote, a lesson or a decision;
  change the final refrain when the situation has changed.
- **Explain first, joke second:** set up the action that makes the joke land.
- **Earn the emotional ending:** the listener must know the relationship, choice and cost first.
- **Stable narrator:** attribute dialogue in the words; pronouns must not hide whose fate it is.
- **End where the next session starts:** location, changed objective, open question.

### Lessons from revising a favourite

An invented example: a song where a knight, Sir Edda, stays behind in a collapsing mirror-realm.

1. **Explain the mechanism behind a sacrifice.** "To keep the mirror from the Hollow King" is
   vague; "the mirror could free the Hollow King" makes the danger clear in one line.
2. **Use a short, attributed quote at the turning point.** "Edda said, 'Someone has to hold
   the door'" makes the loss personal right before the chorus. Attribution belongs in the sung
   words; a voice change alone does not identify the speaker.
3. **Keep intention separate from proven result.** "The realm is sealed for good" overstates
   it if the session only showed the attempt; "to keep the Hollow King inside" states the plan.
4. **Keep the specific feeling.** A short paraphrase of what a character actually said beats a
   generic farewell - but never present a condensed lyric as a verbatim quote.

Save a revision separately from the original, keep its hook, groove and arc unless asked
otherwise, and treat proposed arrangement changes as proposals until someone has listened.

Let the final scene change the meaning of the hook: if the session ends with a twist (a
stranger found dead, an ally missing), a final refrain or a stripped-back coda can carry it -
without implying causes the session did not establish.

## 2. Write a complete package

Choose length after establishing the necessary explanation; 3-4.5 minutes is a preference,
not a reason to cut context. Use singable sentences and clear breath points. Rhyme is optional
when it would obscure a fact. Cut empty repetition and long instrumentals before explanation.

### Required lyric review before generation

Read the lyrics without the event table, Styles or notes:

- Can the listener state the starting situation and the party's goal?
- Are the important people, relationships and places identifiable?
- Does each major choice carry its reason and consequence?
- Are events connected, not merely listed?
- Is the final situation clear - who stayed, who left, what is unresolved?
- Is every essential fact in the sung words, not only in a title, tag or style instruction?

Then compare against the source for omissions, invented links and drift. Call a package ready
only when both comprehension and fidelity pass.

Use simple sections (`[Verse]`, `[Chorus]`, `[Bridge]`, `[Outro]`) and finish with `[End]` or
`[Fade Out]` - an arrangement cue, not a guaranteed stop. Production directions go in Styles.

For duets, describe the contrasting voices and turn-taking in Styles and attribute dialogue
in the lyrics. Name tags such as `[Narrator]` are a convention, **not verified voice routing
in v6**. Do not claim tags guarantee a voice.

Deliver each song in this order:

1. Title.
2. Lyrics (fenced block).
3. Styles (fenced block).
4. Exclude styles (fenced block).
5. Model and More Options settings (fenced block).
6. Title again (fenced block, for copying).

Keep a manifest per song: exact lyrics, styles, settings, submission count and track URLs.

## 3. Write a plain-language musical brief

Give genre, tempo feel, instruments, vocal delivery, arrangement arc and ending. Ask for
intelligible narrative verses, space between facts and vocals above the accompaniment. Example:

```text
Storytelling funk-pop, relaxed 4/4 at about 104 BPM. One clear male narrator over an electric
bass groove, electric piano and a tight drum kit. Short brass responses between sentences,
keeping the lead words unobstructed. Verses deliver the events in complete singable
sentences; the chorus repeats the central decision. Strip back for the final consequence and
resolve after the last line. No overlapping lead vocals or long instrumental break.
```

BPM and key for an original arrangement are creative targets, not measured facts. If the user
names an existing song as inspiration, research its musical properties first, cite sources,
and describe traits - never copy its lyrics. v6 accepts natural-language direction; old rules
such as "max two genre tags" were heuristics. [Release notes](https://suno.com/release-notes).

## Mashups: two source songs, one complete recap

When the user asks to combine two of their songs (for example alternating `[Singer A]`,
`[Transition]`, `[Singer B]` blocks), you are writing a new duet arrangement that reuses lyrics
and hooks - not mixing recordings.

1. Give each voice a musical role tied to its source song: delivery, groove, instruments.
2. Read both sources and the event table; prefer the approved revisions.
3. Decide which voice carries each scene. The combined lyric must explain the full session
   without knowing either original.
4. Keep both recognisable hooks and make room for the events between them.
5. Use short transitions at handovers (a drum change, a fill) - requests, not timing controls.
6. Keep narrative vocals sequential; harmonies only on finished hooks.
7. End at the actual cliffhanger and let the voices divide the final scene.

Pick one shared tempo (or a deliberate tempo change) that suits both deliveries. Describe both
voices in Styles and leave Vocal Gender unset when it would conflict with one role.

A lyric mashup requests a new performance; it does not preserve either recording's melody or
voice. If the user wants the actual recordings combined, use Suno's currently supported
audio-input workflow and record the sources used.

## 4. Choose settings deliberately

Weirdness = conventional vs. adventurous; Style Influence = adherence to the brief
([slider help](https://help.suno.com/en/articles/6141377)). Starting points for a first
comparison:

| Setting | Starting value | Reason |
|---|---|---|
| Lyrics, Styles, exclusions | Identical within a model pair | Isolate the model |
| Weirdness | 40 | Conservative, favours clarity |
| Style Influence | 75 | Keep the brief prominent |
| Variety | Normal (High as the alternative) | Off tends to flatten; use the group's preference |
| Personalize | Off | Avoid account-taste steering |
| Duration | Auto | Avoid a forced cut at the last event |
| Max Mode | Off for a standard-cost comparison | Comparable cost |
| Vocal Gender | Match the intended singer(s) | Support the brief |

These are editorial starting points, not proven optima. Change one thing at a time. Useful
exclusions: crowd cheering, crowd clapping, unintelligible vocals, abrupt ending. Do not
exclude something the genre depends on.

## 5. Generate through the user's own account

Only when the user asks you to submit, and with their account:

1. Inspect any existing draft before replacing fields.
2. Select Advanced and the intended model.
3. Fill Lyrics, Styles, exclusions and title; set More Options.
4. Read everything back, including after a model switch. Never press Create after a
   mismatched read-back.
5. Submit Create **once** per song/model pair.
6. Record time, model, inputs, credit balance and both output IDs/URLs.
7. If the outcome is unclear, check the library before retrying - a slow render is not a
   failure.
8. Verify completion, title, model and playback before reporting a finished generation.

When driving a browser: focus a field before setting it and read the whole value back - rapid
pastes can land in the wrong field. A human-verification challenge is the user's to solve.
Titles like `<Title> - Session 12 - v6` keep pairs recognisable. Creating in the workspace and
publishing publicly are separate actions.

## 6. Verify and hand back

Judge comprehension first: can a listener retell what happened after one listen? Then
musical appeal. Report each generated track with its model. Listen for omitted endings,
altered names, repeated verses, pronunciation and clarity. If you cannot hear audio in your
environment, say so - text review, completion metadata and listening are different checks.

For Skaldkeep, store approved lyrics as a `kind="song"` recap (`upsert_recap`), reusing the
`recap_id` on updates. To attach audio (e.g. a Suno or ElevenLabs file the user provides), upload it with `create_media_upload` (shell) or `import_media_from_url` (public https link), then pass the returned `id` as `audio_media_id`. On older servers without these tools, a human uploads the audio in the web app.

This guide concerns suno.com and help.suno.com; look-alike domains are unrelated products.
