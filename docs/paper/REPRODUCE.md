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

The high-query sensitivity gate also checks six proof envelopes under
`docs/engineering/evidence/high-query/`. Those envelopes are explicit
query-count reruns for the d8 single-head surface at FRI query counts `6` and
`12`; they are engineering evidence, not headline d64/d128 rows.

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

## Canonical Release Gate

Run the paper release gate from the repository root:

```bash
scripts/run_proof_pressure_release_gate.sh
```

The gate regenerates the machine-readable claim pack and figures, runs the
paper preflight, checks Python syntax and unit tests for the claim-pack gate,
and fails if committed paper artifacts drift.

## Individual Commands

The release gate expands to the commands pinned in
`docs/paper/PAPER_RELEASE_AUDIT_PACKET_2026_06_04.md`, including:

```bash
python3.10 scripts/zkai_paper_claim_pack_gate.py \
  --write-json docs/paper/evidence/stark-native-transformer-claim-pack-2026-05.json

python3.10 scripts/paper/generate_proof_pressure_boundaries_figures.py

python3.10 scripts/zkai_attention_kv_high_query_sensitivity_gate.py \
  --write-json docs/engineering/evidence/zkai-attention-kv-d8-high-query-sensitivity-2026-06.json \
  --write-tsv docs/engineering/evidence/zkai-attention-kv-d8-high-query-sensitivity-2026-06.tsv \
  --write-md docs/engineering/zkai-attention-kv-d8-high-query-sensitivity-2026-06-26.md

python3.10 scripts/paper/paper_preflight.py --repo-root .

scripts/run_paper_preflight_suite.sh

git diff --check
```

The public release statement should include:

```text
Regeneration produced no diff against the committed paper artifacts.
```
