# Scoped D128 Seq32 Block Boundary Preflight

Issue: #715

## Decision

`GO_SCOPED_D128_SEQ32_BLOCK_BOUNDARY_PREFLIGHT`

Result:

`ATTACK_SCOPED_D128_SEQ32_BOUNDARY_BEFORE_D256_SEQ64_STRESS`

This is a preflight gate, not a new proof object. It binds the current checked
evidence into the next execution decision: attack the scoped `d128 seq32`
boundary before promoting `d256 seq64` into the primary path.

## Human Meaning

The next paper-grade experiment should be a scoped boundary, not a bigger
stress test for its own sake. We already have one checked `seq32 + d128` native
boundary that saves `5,120`
typed bytes against its matched frontier. We also have a `d128` two-head
`seq32` attention route that saves `32,388`
raw proof bytes against matched source plus sidecar, and a seq32-derived `d128`
MLP surface that saves `30,064` typed bytes
against its separate-component frontier.

The slope table says why this is the right next gate. On the d128 sequence
axis, lookup work grows `3.72973x` and trace
rows grow `4.0x`, while fused proof bytes
grow only `1.080697x`. The width axis is
different: d128 to d256 fused proof bytes grow
`1.842162x`, so d256 stays a stress test
after this scoped gate, not the main paper path.

## Checked Rows

| row | status | scope | bytes | reference | saving | ratio | action |
|---|---|---|---:|---:|---:|---:|---|
| existing seq32 d128 single proof champion | `REGRESSION_BASELINE_GO` | typed_and_json_local_proof_bytes | `42,068` | `47,188` | `5,120` | `0.891498` | preserve as regression baseline not as full block claim |
| d128 two head seq32 attention route | `GO_ATTENTION_SOURCE_FOR_SCOPED_GATE` | raw_proof_bytes | `445,888` | `478,276` | `32,388` | `0.932282` | use as d128 attention source for scoped boundary |
| seq32 derived d128 mlp surface | `GO_MLP_SOURCE_FOR_SCOPED_GATE` | typed_bytes | `24,272` | `54,336` | `30,064` | `0.446702` | use as d128 mlp surface if source value adapter stays pinned |
| d128 two head seq32 sequence slope | `GO_SEQUENCE_AXIS_SUPPORTS_SCOPED_D128_FIRST` | raw_proof_bytes_growth | `481,870` | `522,187` | `40,317` | `0.922792` | treat seq64 as followup after scoped seq32 boundary |
| width axis caution | `CAUTION_DO_NOT_JUMP_TO_D256_SEQ64_AS_PRIMARY_GATE` | raw_proof_bytes_growth | `821,398` | `851,541` | `30,143` | `0.964602` | keep d256 seq64 as stress or falsification after scoped d128 gate |
| next scoped boundary gate | `ATTACK_NEXT` | decision_gate |  |  |  |  | IMPLEMENT SCOPED D128 SEQ32 BOUNDARY BEFORE D256 SEQ64 |

## GO Gate

- source artifacts and exact sizes remain pinned;
- d128 attention source output can be value-bound into the d128 MLP surface;
- the new scoped boundary beats its matched split local frontier before any external comparison;
- mutation gates reject source drift, envelope mismatch, VK mismatch, model-surface mismatch, and overclaim wording.

## NO-GO Gate

- source-to-MLP value adapter cannot be pinned without relabeling;
- the scoped proof is equal or heavier than the matched split frontier;
- the only positive story requires treating d256 seq64 as the primary path;
- the result needs a full-block, speed, NANOZK, or production-throughput claim to sound interesting.

## Evidence

- JSON: `docs/engineering/evidence/zkai-scoped-d128-seq32-block-boundary-preflight-2026-05.json`
- TSV: `docs/engineering/evidence/zkai-scoped-d128-seq32-block-boundary-preflight-2026-05.tsv`
- Slope table: `docs/engineering/evidence/zkai-proof-pressure-slope-table-2026-05.json`
- Route matrix: `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`
- Seq32 one-proof champion: `docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.json`

The gate rejects `17 / 17` mutation cases
covering source drift, issue drift, next-gate drift, d256 overclaim, external
comparison overclaim, full-block overclaim, row metric drift, non-claim drift,
validation-command drift, and payload-commitment drift.

## Non-Claims

- not a full transformer block proof.
- not a public proving-speed benchmark.
- not an external zkML comparison.
- not a NANOZK proof-size win.
- not exact real-valued Softmax.
- not full autoregressive inference.
- not production throughput evidence.

## Reproduce

```bash
python3.10 scripts/zkai_scoped_d128_seq32_block_boundary_preflight_gate.py --write-json docs/engineering/evidence/zkai-scoped-d128-seq32-block-boundary-preflight-2026-05.json --write-tsv docs/engineering/evidence/zkai-scoped-d128-seq32-block-boundary-preflight-2026-05.tsv --write-md docs/engineering/zkai-scoped-d128-seq32-block-boundary-preflight-2026-05-24.md
python3.10 -m py_compile scripts/zkai_scoped_d128_seq32_block_boundary_preflight_gate.py scripts/tests/test_zkai_scoped_d128_seq32_block_boundary_preflight_gate.py
python3.10 -m unittest scripts.tests.test_zkai_scoped_d128_seq32_block_boundary_preflight_gate
git diff --check
just gate-fast
just gate
```
