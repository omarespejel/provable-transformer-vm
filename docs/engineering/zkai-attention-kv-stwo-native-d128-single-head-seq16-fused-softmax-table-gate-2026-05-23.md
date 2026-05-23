# d128 Single-Head Seq16 Fused Softmax-Table Gate

Date: 2026-05-23

Issue: #715

## Result

This slice adds the `d128_single_head_seq16` anchor row to the proof-pressure
route matrix. It is the low-pressure d128 width anchor: one head, `seq16`, and
the same `168` lookup claims as the earlier `d64_single_head_seq16` row.

The local native Stwo route verifies one fused proof object for bounded
attention arithmetic plus LogUp Softmax-table membership:

- source arithmetic proof: `374,261` raw proof bytes
- LogUp sidecar proof: `23,052` raw proof bytes
- matched split frontier: `397,313` raw proof bytes
- fused proof: `380,342` raw proof bytes
- fused saving: `16,971` raw proof bytes
- fused ratio: `0.957286x`
- lookup claims: `168`
- trace rows: `256`

The fused proof is `6,081` bytes larger than the source arithmetic proof alone,
so this is not source-only compression. The honest comparator is source plus
LogUp sidecar. Against that comparator, one fused proof still saves `16,971`
bytes.

## Width-Anchor Read

Holding one head and `seq16` fixed from `d64` to `d128`:

| profile | d | lookup claims | trace rows | source proof bytes | sidecar proof bytes | split proof bytes | fused proof bytes | saving |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `d64_single_head_seq16` | `64` | `168` | `256` | `231,415` | `22,960` | `254,375` | `237,725` | `16,650` |
| `d128_single_head_seq16` | `128` | `168` | `256` | `374,261` | `23,052` | `397,313` | `380,342` | `16,971` |

The width jump keeps lookup and trace rows fixed, while fused proof bytes grow
`1.599924x`. The saving is still positive, but the effect is modest. That is
useful information: this row supports the boundary-selection story rather than
claiming every axis behaves like lookup-heavy sequence scaling.

## Matrix Impact

The controlled route matrix now has:

- `29` matched route rows
- `44,468` total lookup claims
- `78,656` total trace rows
- `6,312,974` matched split proof bytes
- `5,576,234` fused proof bytes
- `736,740` aggregate fused proof-byte savings

The fuller crossing grid is now `29 / 100` proved and `71 / 100` missing.

The wide-grid selector now promotes `d256_h2_seq32` as the next width stress
test before scoped block work.

## Correctness Discipline

The d128 single-head seq16 route keeps the local-only validation discipline:

- source, sidecar, and fused proof envelopes verify with the native Stwo CLI
- source input invariant tests reject stale width, sequence, and commitment drift
- sidecar gate rejects `17 / 17` mutation cases
- fused gate rejects `24 / 24` mutation cases
- route matrix rejects drift and overclaim mutations
- fuller grid rejects drift and overclaim mutations
- scaling claim pack rejects drift and overclaim mutations
- wide-grid selector rejects drift and overclaim mutations

## Non-Claims

This is not exact real-valued Softmax. It is not full transformer inference or
full autoregressive inference. It is not a full transformer block. It is not
recursion, PCD, production zkML readiness, private-witness privacy, on-chain
verification, timing evidence, or a NANOZK comparison.

The d128 source row is deterministically widened from checked bounded fixtures.
It is not a model-faithful d128 single-head transformer trace.

## Reproduction

```bash
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_native_d128_single_head_seq16_bounded_softmax_table_proof_input
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d128_single_head_seq16_air_private_softmax_table_lookup_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d128_single_head_seq16_fused_softmax_table_native_gate
cargo +nightly-2025-07-14 test --locked attention_kv_native_d128_single_head_seq16_bounded_softmax_table_proof --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked attention_kv_native_d128_single_head_seq16_softmax_table_lookup_proof --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked attention_kv_native_d128_single_head_seq16_fused_softmax_table_proof --lib --features stwo-backend
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_single_head_seq16_bounded_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-single-head-seq16-bounded-softmax-table-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_single_head_seq16_softmax_table_lookup_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-single-head-seq16-softmax-table-logup-sidecar-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_single_head_seq16_fused_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-single-head-seq16-fused-softmax-table-proof-2026-05.envelope.json
python3.10 scripts/zkai_attention_kv_fused_softmax_table_route_matrix_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.tsv
python3.10 scripts/zkai_attention_kv_fuller_crossing_grid_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.tsv
python3.10 scripts/zkai_proof_pressure_scaling_claim_pack_gate.py --write-json docs/engineering/evidence/zkai-proof-pressure-scaling-claim-pack-2026-05.json --write-tsv docs/engineering/evidence/zkai-proof-pressure-scaling-claim-pack-2026-05.tsv
python3.10 scripts/zkai_proof_pressure_wide_grid_selector_gate.py --write-json docs/engineering/evidence/zkai-proof-pressure-wide-grid-selector-2026-05.json --write-tsv docs/engineering/evidence/zkai-proof-pressure-wide-grid-selector-2026-05.tsv
git diff --check
```
