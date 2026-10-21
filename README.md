# Skaldkeep skills

Agent skills for [Skaldkeep](https://app.skaldkeep.gg), the campaign chronicle for tabletop RPG
groups. They teach an AI agent to work with a campaign through Skaldkeep's built-in MCP server:
turn a session transcript into staged campaign documents, transcribe recordings, write recap
songs and keep the campaign's filters tidy - with the DM reviewing everything before players
see it.

Works with Claude Code, Codex, Cursor, Gemini CLI, Antigravity, GitHub Copilot, OpenCode and
any other agent that reads [Agent Skills](https://agentskills.io).

## Skills

| Skill | What it does |
|-------|--------------|
| `skaldkeep-connect` | Connects the agent to the Skaldkeep MCP server with a personal access token, per agent, and verifies it with `get_my_access` / `list_campaigns`. |
| `skaldkeep-usage` | How to use the MCP tools correctly: `owner/slug` addressing, staging and review batches, `append_to_document`, visibility, the DM-only `dm_notes` field, snapshots and `diff_since`. Includes the full tool list and type schemas. |
| `skaldkeep-session` | "Process session 12": server-side transcript (or a file) to session note, entity pages and a "Previously On" recap, staged in one batch, then a snapshot after the DM publishes. |
| `skaldkeep-transcribe-local` | Local AssemblyAI transcription with speaker labels, campaign keyterms, cost cap and resumable jobs, then `upload_transcript`. For instances without server-side transcription. |
| `skaldkeep-songs` | Recap songs: event list, concepts, lyrics that an absent player can follow, a Suno v6 package, and the lyrics stored as a song recap. |
| `skaldkeep-facet-cleanup` | Merges drifting filter values (one spelling per location, faction, holder, ...) with a dry run first and staged changes. |

## Install

### Any agent: the `skills` CLI

```bash
npx skills add kastruppro/skaldkeep-skills
```

The CLI asks which skills and which agents to install for. Non-interactive examples:

```bash
npx skills add kastruppro/skaldkeep-skills -a claude-code -a codex -y      # this project
npx skills add kastruppro/skaldkeep-skills --skill skaldkeep-session -g    # one skill, globally
npx skills add kastruppro/skaldkeep-skills --list                          # just list them
```

The skills do not configure the MCP connection themselves: afterwards, ask the agent to
"connect to Skaldkeep" and the `skaldkeep-connect` skill walks through it.

### Claude Code: the plugin (skills + MCP connection)

```text
/plugin marketplace add kastruppro/skaldkeep-skills
/plugin install skaldkeep@skaldkeep-skills
```

Claude Code asks for your Skaldkeep URL (default `https://app.skaldkeep.gg`) and a personal
access token. The token is stored in secure storage, not in `settings.json`. Change both later
in `/config`. Use either the plugin or the `skills` CLI for Claude Code, not both, or the skills
appear twice.

### Codex: the plugin manifest

`.codex-plugin/plugin.json` lets Codex load this repo as a plugin, but it ships the skills only.
Set up the MCP server separately (see below, or ask Codex to "connect to Skaldkeep").

### Manually

Copy the folders you want from `skills/` into your agent's skills directory, for example
`.claude/skills/` (Claude Code) or `.agents/skills/` (Codex, Cursor, Gemini CLI, Antigravity,
OpenCode, Copilot), or the global equivalent in your home directory.

## Connect to Skaldkeep

1. In Skaldkeep, open **Settings > Access tokens** and create a token (`skp_...`). Limit it to
   the campaigns the agent should touch and give it an expiry. It is shown once.
2. Put it in an environment variable, never in a committed file:
   `export SKALDKEEP_TOKEN='skp_...'`
3. Point your agent at `https://app.skaldkeep.gg/mcp` (Streamable HTTP, header
   `Authorization: Bearer <token>`):

```bash
# Claude Code (the command Skaldkeep shows when you create a token)
claude mcp add --transport http skaldkeep https://app.skaldkeep.gg/mcp \
  --header "Authorization: Bearer $SKALDKEEP_TOKEN"

# Codex - stores the variable NAME, reads the token at runtime
codex mcp add skaldkeep --url https://app.skaldkeep.gg/mcp --bearer-token-env-var SKALDKEEP_TOKEN
```

Cursor, Gemini CLI, VS Code, Antigravity and generic clients are covered in
[`skills/skaldkeep-connect/references/clients.md`](skills/skaldkeep-connect/references/clients.md).
Self-hosted instance? Use your own base URL plus `/mcp`.

## Requirements

- A Skaldkeep account and a campaign (DM or co-DM for transcripts and staging review).
- `skaldkeep-transcribe-local` only: [uv](https://docs.astral.sh/uv/), ffmpeg/ffprobe, an
  [AssemblyAI](https://www.assemblyai.com/) key in `ASSEMBLYAI_API_KEY`, macOS or Linux.

## Privacy

The skills send campaign content only to the Skaldkeep instance you connect, and - for local
transcription - audio to AssemblyAI. Transcripts are written outside any repository by
default. Never commit tokens, transcripts or campaign files.

See the [Skaldkeep privacy policy](https://skaldkeep.gg/privacy).

## Repository layout

```
skills/<name>/SKILL.md (+ references/, scripts/)   the skills
.claude-plugin/plugin.json, marketplace.json       Claude Code plugin "skaldkeep" + marketplace
.codex-plugin/plugin.json                          Codex plugin manifest (skills)
.mcp.json, .codex/config.toml                      MCP config for working on this repo (token from env)
AGENTS.md                                          contributor and agent instructions
```

## License

MIT - see [LICENSE](LICENSE).
