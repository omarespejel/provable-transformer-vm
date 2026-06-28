#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3.10}"
export PYTHON_BIN

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Requires Python >= 3.10; set PYTHON_BIN to a compatible interpreter" >&2
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
import sys

if sys.version_info < (3, 10):
    raise SystemExit("Requires Python >= 3.10")
PY

"$PYTHON_BIN" scripts/zkai_paper_claim_pack_gate.py \
  --write-json docs/paper/evidence/stark-native-transformer-claim-pack-2026-05.json

"$PYTHON_BIN" -m py_compile \
  scripts/zkai_paper_claim_pack_gate.py \
  scripts/zkai_attention_kv_high_query_sensitivity_gate.py \
  scripts/zkai_attention_kv_d64_high_query_sensitivity_gate.py \
  scripts/tests/test_zkai_paper_claim_pack_gate.py \
  scripts/tests/test_zkai_attention_kv_high_query_sensitivity_gate.py \
  scripts/tests/test_zkai_attention_kv_d64_high_query_sensitivity_gate.py \
  scripts/paper/generate_proof_pressure_boundaries_figures.py \
  scripts/paper/paper_preflight.py

"$PYTHON_BIN" -m unittest scripts.tests.test_zkai_paper_claim_pack_gate
"$PYTHON_BIN" -m unittest scripts.tests.test_zkai_attention_kv_high_query_sensitivity_gate
"$PYTHON_BIN" -m unittest scripts.tests.test_zkai_attention_kv_d64_high_query_sensitivity_gate

"$PYTHON_BIN" scripts/zkai_attention_kv_high_query_sensitivity_gate.py \
  --write-json docs/engineering/evidence/zkai-attention-kv-d8-high-query-sensitivity-2026-06.json \
  --write-tsv docs/engineering/evidence/zkai-attention-kv-d8-high-query-sensitivity-2026-06.tsv \
  --write-md docs/engineering/zkai-attention-kv-d8-high-query-sensitivity-2026-06-26.md

"$PYTHON_BIN" scripts/zkai_attention_kv_d64_high_query_sensitivity_gate.py \
  --write-json docs/engineering/evidence/zkai-attention-kv-d64-high-query-sensitivity-2026-06.json \
  --write-tsv docs/engineering/evidence/zkai-attention-kv-d64-high-query-sensitivity-2026-06.tsv \
  --write-md docs/engineering/zkai-attention-kv-d64-high-query-sensitivity-2026-06.md

"$PYTHON_BIN" scripts/paper/generate_proof_pressure_boundaries_figures.py

"$PYTHON_BIN" scripts/paper/paper_preflight.py --repo-root .

scripts/run_paper_preflight_suite.sh

git diff --check

git diff --exit-code \
  docs/paper/evidence/stark-native-transformer-claim-pack-2026-05.json \
  docs/paper/evidence/stark-native-transformer-paper-release-manifest-2026-06.json \
  docs/paper/stark-native-transformer-proof-claim-pack-2026-05.md \
  docs/paper/proof-pressure-boundaries-for-stark-native-transformers-2026.md \
  docs/paper/appendix-zkml-statement-validity-2026.md \
  docs/paper/PAPER_NEXT_REVIEW_PACKET_2026_06_27.md \
  docs/paper/PAPER_D64_HIGH_QUERY_AUDIT_PACKET_2026_06_27.md \
  docs/paper/PAPER_RELEASE_AUDIT_PACKET_2026_06_04.md \
  docs/paper/README.md \
  docs/paper/REPRODUCE.md \
  docs/engineering/evidence/zkai-attention-kv-d8-high-query-sensitivity-2026-06.json \
  docs/engineering/evidence/zkai-attention-kv-d8-high-query-sensitivity-2026-06.tsv \
  docs/engineering/zkai-attention-kv-d8-high-query-sensitivity-2026-06-26.md \
  docs/engineering/evidence/zkai-attention-kv-d64-high-query-sensitivity-2026-06.json \
  docs/engineering/evidence/zkai-attention-kv-d64-high-query-sensitivity-2026-06.tsv \
  docs/engineering/zkai-attention-kv-d64-high-query-sensitivity-2026-06.md \
  docs/paper/figures/proof-pressure-growth-factors-2026-05.pdf \
  docs/paper/figures/proof-pressure-growth-factors-2026-05.png \
  docs/paper/figures/proof-pressure-growth-factors-2026-05.svg \
  docs/paper/figures/proof-pressure-growth-factors-2026-05.tsv \
  docs/paper/figures/proof-pressure-boundary-selection-2026-05.pdf \
  docs/paper/figures/proof-pressure-boundary-selection-2026-05.png \
  docs/paper/figures/proof-pressure-boundary-selection-2026-05.svg \
  docs/paper/figures/proof-pressure-boundary-selection-2026-05.tsv \
  docs/paper/figures/proof-pressure-opening-mechanism-2026-05.pdf \
  docs/paper/figures/proof-pressure-opening-mechanism-2026-05.png \
  docs/paper/figures/proof-pressure-opening-mechanism-2026-05.svg \
  docs/paper/figures/proof-pressure-opening-mechanism-2026-05.tsv \
  docs/paper/figures/proof-pressure-d64-high-query-sensitivity-2026-06.pdf \
  docs/paper/figures/proof-pressure-d64-high-query-sensitivity-2026-06.png \
  docs/paper/figures/proof-pressure-d64-high-query-sensitivity-2026-06.svg \
  docs/paper/figures/proof-pressure-d64-high-query-sensitivity-2026-06.tsv
