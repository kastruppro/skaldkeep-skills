# Skaldkeep MCP - per-client configuration

All examples use the hosted instance. Self-hosters replace `https://app.skaldkeep.gg` with their
own base URL (the MCP is always mounted at `/mcp`). The token is read from the environment
variable `SKALDKEEP_TOKEN` wherever the client supports it.

```bash
# once, in the shell profile or a secret manager (a leading space keeps it out of
# history in shells with HISTCONTROL=ignorespace)
 export SKALDKEEP_TOKEN='skp_...'
```

## Claude Code

### Plugin (recommended)

```text
/plugin marketplace add kastruppro/skaldkeep-skills
/plugin install skaldkeep@skaldkeep-skills
```

Claude Code prompts for:

| Option | Value |
|--------|-------|
| `server_url` | Base URL without trailing slash, e.g. `https://app.skaldkeep.gg` |
| `access_token` | The `skp_...` token. Marked sensitive: kept in secure storage, not `settings.json`. |

Change them later in `/config`. The plugin also installs all Skaldkeep skills.

### `claude mcp add`

```bash
claude mcp add --transport http skaldkeep https://app.skaldkeep.gg/mcp \
  --header "Authorization: Bearer $SKALDKEEP_TOKEN"
# --scope user  -> every project, still private to this user
claude mcp list   # skaldkeep should show as connected
```

Scopes: `local` (default, this project, private), `user` (all projects, private), `project`
(a committed `.mcp.json` - shared, so it must reference the variable, see below).

### Project `.mcp.json` (shared repos)

```json
{
  "mcpServers": {
    "skaldkeep": {
      "type": "http",
      "url": "${SKALDKEEP_URL:-https://app.skaldkeep.gg}/mcp",
      "headers": { "Authorization": "Bearer ${SKALDKEEP_TOKEN}" }
    }
  }
}
```

`${...}` is read from the environment Claude Code was started in, not from a `.env` file.

## Codex

```bash
codex mcp add skaldkeep --url https://app.skaldkeep.gg/mcp --bearer-token-env-var SKALDKEEP_TOKEN
```

or in `~/.codex/config.toml` (or a project `.codex/config.toml`):

```toml
[mcp_servers.skaldkeep]
url = "https://app.skaldkeep.gg/mcp"
bearer_token_env_var = "SKALDKEEP_TOKEN"   # the variable NAME; Codex reads the value at runtime
```

Check with `codex mcp list`.

## Cursor

`~/.cursor/mcp.json` (all projects) or `.cursor/mcp.json` (one project):

```json
{
  "mcpServers": {
    "skaldkeep": {
      "url": "https://app.skaldkeep.gg/mcp",
      "headers": { "Authorization": "Bearer ${env:SKALDKEEP_TOKEN}" }
    }
  }
}
```

## Gemini CLI

`~/.gemini/settings.json` (or `.gemini/settings.json` in a project). Gemini CLI expands
`$VAR` in settings:

```json
{
  "mcpServers": {
    "skaldkeep": {
      "httpUrl": "https://app.skaldkeep.gg/mcp",
      "headers": { "Authorization": "Bearer $SKALDKEEP_TOKEN" }
    }
  }
}
```

## VS Code (GitHub Copilot agent mode)

`.vscode/mcp.json` - VS Code prompts for the token once and stores it securely:

```json
{
  "inputs": [
    { "type": "promptString", "id": "skaldkeep-token", "description": "Skaldkeep access token (skp_...)", "password": true }
  ],
  "servers": {
    "skaldkeep": {
      "type": "http",
      "url": "https://app.skaldkeep.gg/mcp",
      "headers": { "Authorization": "Bearer ${input:skaldkeep-token}" }
    }
  }
}
```

## Antigravity

Open **Manage MCP Servers > View raw config** to find the active `mcp_config.json`. Remote
servers use `serverUrl` (not `url`):

```json
{
  "mcpServers": {
    "skaldkeep": {
      "serverUrl": "https://app.skaldkeep.gg/mcp",
      "headers": { "Authorization": "Bearer skp_..." }
    }
  }
}
```

Antigravity has no documented environment-variable interpolation here, so the token sits in
this user-level file: keep that file private and never copy it into a repository.

## Any other client

Configure a remote MCP server with transport **Streamable HTTP**, URL
`https://app.skaldkeep.gg/mcp`, and header `Authorization: Bearer <token>`. Use the client's
secret or environment-variable mechanism if it has one.

A client that only speaks stdio can use a vetted, version-pinned `mcp-remote` bridge:

```json
{
  "mcpServers": {
    "skaldkeep": {
      "command": "npx",
      "args": ["-y", "mcp-remote@<pinned-version>", "https://app.skaldkeep.gg/mcp",
               "--header", "Authorization:Bearer ${SKALDKEEP_TOKEN}"],
      "env": { "SKALDKEEP_TOKEN": "<from your secret store>" }
    }
  }
}
```

## Creating a token without the web app

The web app (Settings > Access tokens) is simplest. Scripted alternative - the password is
read without echo and never enters shell history:

```bash
BASE=https://app.skaldkeep.gg
read -rs -p "Password: " SK_PW && echo
JWT=$(curl -s -X POST "$BASE/auth/jwt/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=you@example.com" --data-urlencode "password=$SK_PW" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
unset SK_PW
curl -s -X POST "$BASE/users/me/tokens" \
  -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" \
  -d '{"name":"my-agent","campaign_slugs":["owner/your-campaign"],"expires_in_days":90}'
# -> the "token" field (skp_...) is shown once
```
