#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3.10}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Requires Python >= 3.10; set PYTHON_BIN to a compatible interpreter" >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
import sys

if sys.version_info < (3, 10):
    raise SystemExit("Requires Python >= 3.10")
PY

"$PYTHON_BIN" -B -m unittest scripts/paper/tests/test_paper_preflight.py -q
"$PYTHON_BIN" scripts/paper/paper_preflight.py --repo-root .
