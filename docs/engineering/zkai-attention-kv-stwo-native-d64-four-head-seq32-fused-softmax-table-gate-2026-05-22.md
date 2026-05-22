# d64 Four-Head Seq32 Fused Softmax-Table Gate

Date: 2026-05-22

Issue: #715

## Result

This slice extends the checked `d64` two-head `seq32` fused Softmax-table route
to four heads.

The local native Stwo route verifies one fused proof object for bounded
attention arithmetic plus LogUp Softmax-table membership:

- source arithmetic proof: `254,145` JSON proof bytes
- LogUp sidecar proof: `34,147` JSON proof bytes
- matched split frontier: `288,292` JSON proof bytes
- fused proof: `255,889` JSON proof bytes
- fused saving: `32,403` JSON proof bytes
- fused ratio: `0.887604x`
- lookup claims: `2,368`
- trace rows: `4,096`

The fused proof is `1,744` bytes larger than the source arithmetic proof alone,
so this is not a source-only compression result. It is a matched split-frontier
result: one fused proof replaces the source arithmetic proof plus LogUp sidecar
and saves `32,403` proof bytes against that honest comparator.

## d64 Head-Axis Read

Holding `d64` and `seq32` fixed:

| profile | heads | lookup claims | trace rows | source proof bytes | sidecar proof bytes | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `d64_two_head_seq32` | `2` | `1,184` | `2,048` | `248,702` | `36,400` | `285,102` | `253,257` | `0.888303x` |
| `d64_four_head_seq32` | `4` | `2,368` | `4,096` | `254,145` | `34,147` | `288,292` | `255,889` | `0.887604x` |

From two heads to four heads:

- lookup claims grow `2.000000x`
- trace rows grow `2.000000x`
- source arithmetic proof bytes grow `1.021886x`
- LogUp sidecar proof bytes shrink to `0.938104x`
- matched split proof bytes grow `1.011189x`
- fused proof bytes grow `1.010393x`
- fused savings grow `1.017522x`

This is a useful scaling signal: the work being checked doubles, but the fused
proof object grows by about one percent. That supports the amortization thesis.
It does not yet prove a full transformer block or establish a NANOZK comparison.

## Matrix Impact

The controlled route matrix now has:

- `20` matched route rows
- `13,412` total lookup claims
- `21,824` total trace rows
- `2,732,779` matched split proof bytes
- `2,282,190` fused proof bytes
- `450,589` aggregate fused proof-byte savings

The fuller crossing grid is now `20 / 60` proved and `40 / 60` missing.

## Correctness Discipline

The d64 four-head route keeps the local-only validation discipline:

- source, sidecar, and fused proof envelopes verify with the native Stwo CLI
- source input invariant tests reject stale width/head/sequence drift
- sidecar gate rejects `28 / 28` mutation cases
- fused gate rejects `30 / 30` mutation cases
- route matrix rejects `51 / 51` drift and overclaim mutations
- fuller grid rejects `18 / 18` drift and overclaim mutations
- evidence is bound by source commitments, proof-envelope commitments, table
  multiplicities, verifier domains, statement versions, and non-claim text

## Non-Claims

This is not exact real-valued Softmax. It is not full autoregressive inference.
It is not a full transformer block. It is not recursion, PCD, private-witness
privacy, on-chain verification, timing evidence, or a NANOZK comparison.

The `d64` source row is deterministically widened from the checked `d64`
two-head `seq32` source fixture and extends the head axis. It is not a
model-faithful d64 four-head transformer trace.

## Issue #715 Remaining Gates

This PR is one checked row inside issue #715, not completion of the full issue.
The following issue-level gates remain open:

- `d64_four_head_seq16` to test whether the d64 head-axis signal also holds at
  the shorter sequence midpoint.
- `d64_two_head_seq64` to test whether the d64 sequence-axis signal continues
  past `seq32`.
- `d128` and `d256` attention rows: not produced here.
- typed and binary/raw proof-size accounting for the widened attention rows.
- external same-surface baseline: no EZKL, zkVM, NANOZK, Jolt, or DeepProve row
  is included here.

## Reproduction

```bash
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_native_d64_four_head_seq32_bounded_softmax_table_proof_input
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d64_four_head_seq32_air_private_softmax_table_lookup_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d64_four_head_seq32_fused_softmax_table_native_gate
cargo +nightly-2025-07-14 test --locked attention_kv_native_d64_four_head_seq32_bounded_softmax_table_proof --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked attention_kv_d64_four_head_seq32_softmax_table_lookup --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked attention_kv_d64_four_head_seq32_fused_softmax_table --lib --features stwo-backend
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq32_bounded_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq32-bounded-softmax-table-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq32_softmax_table_lookup_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq32-softmax-table-logup-sidecar-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq32_fused_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq32-fused-softmax-table-proof-2026-05.envelope.json
python3.10 scripts/zkai_attention_kv_fused_softmax_table_route_matrix_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.tsv
python3.10 scripts/zkai_attention_kv_fuller_crossing_grid_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.tsv
python3.10 scripts/zkai_proof_pressure_wide_grid_selector_gate.py --write-json docs/engineering/evidence/zkai-proof-pressure-wide-grid-selector-2026-05.json --write-tsv docs/engineering/evidence/zkai-proof-pressure-wide-grid-selector-2026-05.tsv
```
