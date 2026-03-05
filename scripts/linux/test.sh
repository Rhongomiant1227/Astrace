#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Virtual env not found. Run ./scripts/linux/setup.sh first." >&2
  exit 1
fi

.venv/bin/python -m astrace.server --self-test
.venv/bin/python -m pytest -q

echo "Linux tests passed."
