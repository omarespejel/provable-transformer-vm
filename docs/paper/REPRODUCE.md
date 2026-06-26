# Reproducing the Proof-Pressure Paper Package

This note is the short path for reviewers of:

`docs/paper/proof-pressure-boundaries-for-stark-native-transformers-2026.md`

The paper studies scoped bounded-attention proof-boundary placement over an
unmodified Stwo backend. It does not claim full transformer inference, exact
real-valued Softmax, production-security parameters, proving-speed improvement,
or a system-level comparison against other zkML systems.

## Primary Files

- Main paper:
  `docs/paper/proof-pressure-boundaries-for-stark-native-transformers-2026.md`
- Statement-validity companion appendix:
  `docs/paper/appendix-zkml-statement-validity-2026.md`
- Paper claim pack:
  `docs/paper/stark-native-transformer-proof-claim-pack-2026-05.md`
- Machine-readable claim pack:
  `docs/paper/evidence/stark-native-transformer-claim-pack-2026-05.json`
- Release manifest:
  `docs/paper/evidence/stark-native-transformer-paper-release-manifest-2026-06.json`
- Release audit packet:
  `docs/paper/PAPER_RELEASE_AUDIT_PACKET_2026_06_04.md`

## Evidence Files

The paper-facing claim pack points to the checked engineering evidence used by
the paper:

- `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-controlled-component-grid-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-section-delta-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-typed-size-estimate-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-binary-typed-proof-accounting-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-softmax-table-median-timing-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-fused-softmax-table-gate-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-model-faithful-quantized-attention-bridge-2026-05.json`
- `docs/engineering/evidence/zkai-stwo-ai-d64-four-head-seq64-chunk4-policy-gate-2026-06.json`
- `docs/engineering/evidence/zkai-attention-kv-d8-high-query-sensitivity-2026-06.json`
- `docs/engineering/evidence/zkai-attention-kv-d64-high-query-sensitivity-2026-06.json`

The d64 high-query sensitivity gate also checks six proof envelopes under
`docs/engineering/evidence/high-query/`. Together with the q3 default
envelopes, those artifacts form the `d64_four_head_seq64` q3/q6/q12 table in
the paper. They are engineering evidence, not production-security parameters or
d128 high-query rows.

## Fixed Experimental Configuration

The paper rows use the fixed experimental Stwo configuration recorded in the
release manifest:

| parameter | value |
|---|---:|
| proof-of-work bits | `10` |
| FRI log blowup | `1` |
| FRI blowup factor | `2` |
| FRI query count | `3` |
| FRI fold step | `1` |

These are measurement settings for boundary-placement experiments, not
production-security parameter recommendations.

Profile naming note: the repository still contains a legacy helper named
`publication_v1_pcs_config()` for this `q=3` Stwo PCS measurement profile. That
helper is not the `publication_v1_stark_options()` Vanilla STARK profile in
`src/proof.rs` and should not be read as a production-security or `96`-bit
security setting for the bounded-attention paper.

## Canonical Release Gate

Run the paper release gate from the repository root:

```bash
scripts/run_proof_pressure_release_gate.sh
```

The gate regenerates the machine-readable claim pack and figures, runs the
paper preflight, checks Python syntax and unit tests for the claim-pack gate,
and fails if committed paper artifacts drift.

If the default `python3.10` binary is not available, point the gate at an
equivalent Python 3.10+ interpreter:

```bash
PYTHON_BIN=.venv/bin/python scripts/run_proof_pressure_release_gate.sh
```

For launch or external audit, run this command on the exact release commit and
record that regeneration produced no diff against the committed paper artifacts.

## Individual Commands

The release gate expands to the commands pinned in
`docs/paper/PAPER_RELEASE_AUDIT_PACKET_2026_06_04.md`, including:

```bash
PYTHON_BIN="${PYTHON_BIN:-python3.10}"

"$PYTHON_BIN" scripts/zkai_paper_claim_pack_gate.py \
  --write-json docs/paper/evidence/stark-native-transformer-claim-pack-2026-05.json

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
```

The public release statement should include:

```text
Regeneration produced no diff against the committed paper artifacts.
```
