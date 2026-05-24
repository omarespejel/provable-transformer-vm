#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if command -v python3.10 >/dev/null 2>&1; then
  PYTHON_BIN="${PYTHON_BIN:-python3.10}"
else
  PYTHON_BIN="${PYTHON_BIN:-python3}"
fi

"$PYTHON_BIN" -B -m unittest scripts/paper/tests/test_paper_preflight.py -q
"$PYTHON_BIN" scripts/paper/paper_preflight.py --repo-root .
