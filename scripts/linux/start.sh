#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Virtual env not found. Run ./scripts/linux/setup.sh first." >&2
  exit 1
fi

export MCP_HOST="${MCP_HOST:-0.0.0.0}"
export MCP_PORT="${MCP_PORT:-8788}"
export SEARCH_MAX_RESULTS="${SEARCH_MAX_RESULTS:-8}"
export REQUEST_TIMEOUT="${REQUEST_TIMEOUT:-15}"
export MAX_TEXT_CHARS="${MAX_TEXT_CHARS:-12000}"
export ASTRACE_TASK_WORKERS="${ASTRACE_TASK_WORKERS:-2}"

exec .venv/bin/python -m astrace.server
