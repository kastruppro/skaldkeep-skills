---
name: skaldkeep-connect
description: >-
  Connect an AI agent to a Skaldkeep campaign chronicle over MCP and verify the connection.
  Use when the user wants to set up, add, configure or fix the Skaldkeep MCP server or token,
  e.g. "connect to Skaldkeep", "set up the Skaldkeep MCP", "add my Skaldkeep token", "forbind
  til Skaldkeep", "Skaldkeep tools are missing", "I get 401 from Skaldkeep", or when another
  Skaldkeep skill finds no Skaldkeep tools available. Covers Claude Code (plugin or claude mcp
  add), Codex (config.toml with bearer_token_env_var), Cursor, Gemini CLI, Antigravity, VS Code
  and any generic HTTP MCP client, with a personal access token (skp_...) kept in an
  environment variable. Verifies with get_my_access and list_campaigns.
license: MIT
---

# Connect to Skaldkeep

Skaldkeep ships its own MCP server. Connecting is configuration only - nothing to install or
host. Once connected, the agent sees tools such as `list_campaigns`, `get_document` and
`upsert_document` as native tool calls.

## What the user needs

| Item | Value |
|------|-------|
| MCP URL | `https://app.skaldkeep.gg/mcp` (self-hosted: `<their instance>/mcp`) |
| Transport | Streamable HTTP |
| Auth header | `Authorization: Bearer skp_...` |
| Token | Created in Skaldkeep under **Settings > Access tokens**. Shown once. Can be limited to specific campaigns and given an expiry date. |

Recommend a token scoped to the campaign(s) the agent should touch, with an expiry.

## Step 1 - Keep the token out of files you share

Ask the user to put the token in an environment variable named `SKALDKEEP_TOKEN` (shell
profile, a secret manager, or a gitignored `.env` they export themselves). Never ask them to
paste the token into the chat, never print it back, and never write it into a file that is
committed or shared. If they paste it anyway, use it only for the config step and tell them
it can be revoked and recreated under Settings > Access tokens.

## Step 2 - Configure the agent

Detect which agent you are running in and use its section. Exact snippets for every client are
in [references/clients.md](references/clients.md).

- **Claude Code, easiest:** the Skaldkeep plugin wires the server and prompts for URL and token
  (stored in secure storage):
  `/plugin marketplace add kastruppro/skaldkeep-skills` then
  `/plugin install skaldkeep@skaldkeep-skills`.
- **Claude Code, by hand** (the command Skaldkeep shows when a token is created):
  `claude mcp add --transport http skaldkeep https://app.skaldkeep.gg/mcp --header "Authorization: Bearer $SKALDKEEP_TOKEN"`
  Add `--scope user` to make it available in every project. The shell expands the variable,
  so the token lands only in the user's private Claude config, not in the project.
- **Codex:** `codex mcp add skaldkeep --url https://app.skaldkeep.gg/mcp --bearer-token-env-var SKALDKEEP_TOKEN`
  or the `config.toml` block in the reference. `bearer_token_env_var` holds the variable
  NAME, never the token itself.
- **Cursor, Gemini CLI, VS Code, Antigravity, other HTTP MCP clients:** see the reference.
  Prefer the client's environment-variable interpolation; where a client has none, the token
  goes only in the user's private, uncommitted config.

Most clients load MCP servers at startup: after changing config, tell the user to restart the
agent (or reload its MCP servers) before verifying.

## Step 3 - Verify

1. Confirm the Skaldkeep tools are available (for Claude Code `claude mcp list` should show
   `skaldkeep` as connected).
2. Call `list_campaigns`. Each entry has a `ref` (`owner/slug`), the role and capabilities.
   That `ref` is what every other tool takes as `campaign_slug`.
3. Call `get_my_access(campaign_slug=<ref>)` for the campaign the user cares about and report
   the role and whether DM content is in scope (`sees_dm_content`, `sees_dm_notes`).

Report success as: instance, number of campaigns, the chosen campaign's `ref` and role.

## Troubleshooting

| Symptom | Likely cause and fix |
|---------|----------------------|
| 401 Unauthorized | Token missing, mistyped, revoked or expired; or the env var was not set in the shell that started the agent. Recreate the token or export `SKALDKEEP_TOKEN` and restart. |
| Connected but `list_campaigns` is empty | The token's user is not a member of a campaign, or the token is scoped to other campaigns. Check membership and token scope in the web app. |
| A campaign is "not found" | It is outside the token's scope, or a bare slug is ambiguous - use the full `owner/slug` from `list_campaigns`. |
| No Skaldkeep tools at all | Config in the wrong file or the agent was not restarted. For Claude Code, `mcpServers` in `settings.json` is ignored; use `claude mcp add`, `.mcp.json` or the plugin. |
| A tool is missing that a skill mentions | The instance runs an older Skaldkeep. Use what the server exposes; do not emulate a missing tool with broader writes. |

For what to do once connected, use the **skaldkeep-usage** skill.
