# AGENTS.md - skaldkeep-skills

Agent Skills for [Skaldkeep](https://app.skaldkeep.gg), a campaign chronicle for tabletop RPG
groups with a built-in MCP server at `<instance>/mcp`. This repo is two things at once:

1. An [Agent Skills](https://agentskills.io/specification) collection installable into any agent
   with `npx skills add kastruppro/skaldkeep-skills` (Vercel's `skills` CLI).
2. A Claude Code plugin + marketplace (`/plugin marketplace add kastruppro/skaldkeep-skills`,
   then `/plugin install skaldkeep@skaldkeep-skills`) that also wires the MCP connection.

The skills drive Skaldkeep's MCP tools; they never re-implement the API.

## Layout

```
skills/<name>/SKILL.md          one folder per skill; `name` in frontmatter == folder name
skills/<name>/references/       long guides, tool lists, schemas, templates (loaded on demand)
skills/<name>/scripts/          executable code (only skaldkeep-transcribe-local)
.claude-plugin/plugin.json      Claude Code plugin "skaldkeep": MCP server via userConfig
.claude-plugin/marketplace.json marketplace "skaldkeep-skills", one plugin, source "./"
.codex-plugin/plugin.json       Codex plugin manifest, skills -> ./skills/
.mcp.json / .codex/config.toml  the same MCP server for working on this repo (token from env)
```

## Rules for editing skills

- Follow the Agent Skills spec: frontmatter `name` (lowercase kebab, equal to the folder name,
  max 64 chars) and `description` (max 1024 chars). The description decides whether an agent
  uses the skill: say what it does AND when, with the words a user would actually say.
- Keep `SKILL.md` short (well under 500 lines). Long material goes in `references/`, referenced
  by a relative path one level from `SKILL.md`.
- Write tool-neutral instructions ("dispatch a subagent", "create a todo", "run in the
  background"). Only MCP tool names (`upsert_document`, ...) may be named directly.
- Each skill must work on its own: users install a subset. Mention a sibling skill by name,
  never by a `../` path.
- Skills are written in English. User-facing examples may be Danish or English.
- No absolute paths to anyone's machine, no secrets, no real campaign content. Examples use
  invented names, slugs and owners (`owner/your-campaign`, `session-12`, `brannoc-ashvale`).
- Use plain hyphens, not em/en dashes.
- The live server is authoritative. `skaldkeep-usage/references/type-schemas.md` and
  `mcp-tools.md` are snapshots of the Skaldkeep server source; refresh them when the server
  gains tools or fields, and keep telling agents to call `get_type_schema` live.

## Secrets

- MCP auth is a Skaldkeep personal access token (`skp_...`). It only ever reaches config via the
  plugin's sensitive `userConfig` option, the `SKALDKEEP_TOKEN` environment variable
  (`${SKALDKEEP_TOKEN}` in `.mcp.json`), or Codex's `bearer_token_env_var = "SKALDKEEP_TOKEN"`
  (the variable NAME, never the value).
- `ASSEMBLYAI_API_KEY` is read from the environment (or a local `.env`) by the transcriber.
- `.env` is gitignored; `.env.example` holds empty placeholders only.

## Checks before committing

```bash
# skills discovered by the skills CLI (needs Node.js)
npx skills add ./ --list

# plugin + marketplace manifests
claude plugin validate .

# transcriber tests (needs uv; ffmpeg/ffprobe for the audio tests, which skip otherwise)
uv run --no-project --with 'requests>=2.31,<3' --with 'PyYAML>=6.0.1,<7' \
  python -m unittest discover -s skills/skaldkeep-transcribe-local/scripts/tests -v

# no secrets or real campaign content
git grep -nE "skp_[A-Za-z0-9_]{20,}|ASSEMBLYAI_API_KEY[=].+" && echo "FOUND - fix before commit"
```

## Git

Conventional Commits, one line. Never commit `.env`, transcripts, audio or campaign files.
Do not push without an explicit instruction.
