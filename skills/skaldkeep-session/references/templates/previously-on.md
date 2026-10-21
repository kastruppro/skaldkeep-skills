# "Previously On" recap template

Maps to a Skaldkeep **`narration`** recap attached to the session document.

- `upsert_recap(campaign_slug=<ref>, session_slug="session-xx", kind="narration", title="Previously On - Session XX", text="<script>")`.
- This is the short spoken-recap script. The audio is generated separately (e.g. a text-to-speech tool) and uploaded by a human in the web app.

## Guidelines

- 100-150 words max (under a minute read aloud); 3-5 bullets.
- Include: the setting (one sentence), the plot-deciding events, the cliffhanger, and the hook into this session.
- Leave out: detailed combat, every NPC met, non-plot loot, side chatter.
- Tone: neutral and informative. The recap song carries the drama; this carries the clarity.

## Script skeleton

```text
# Previously on... <Campaign Name>

**Session XX: "Title"**

<One sentence that sets the scene.>

What happened:
- <Key plot point 1>
- <Key plot point 2>
- <Key plot point 3>
- <Cliffhanger / unresolved thread>

<Closing hook - what do they face now?>
```
