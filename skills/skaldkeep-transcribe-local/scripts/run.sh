#!/usr/bin/env bash
# Run transcribe.py through uv (dependencies come from its inline script metadata).
# ASSEMBLYAI_API_KEY is taken from the environment; if unset, it is read from ./.env in the
# current directory. The .env file is parsed, never sourced, and only that one key is used.
#
# Usage:
#   run.sh <audio> --campaign <name-or-file.yaml> [options]
#   run.sh --list-campaigns
#   run.sh --help
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required: https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
fi

KEY_NAME=ASSEMBLYAI_API_KEY
if [ -z "${ASSEMBLYAI_API_KEY:-}" ] && [ -f .env ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            "$KEY_NAME"=*) ;;
            *) continue ;;
        esac
        val=${line#"$KEY_NAME"=}
        case "$val" in
            \"*\") val=${val#\"}; val=${val%\"} ;;
            \'*\') val=${val#\'}; val=${val%\'} ;;
        esac
        export "$KEY_NAME"="$val"
    done < .env
fi

if [ "$#" -eq 0 ]; then
    set -- --help
fi

exec uv run --quiet --script "$SCRIPT_DIR/transcribe.py" "$@"
