# d64 Two-Head Seq32 Fused Softmax-Table Gate

Date: 2026-05-21

Issue: #715

## Result

This slice extends the checked two-head `seq32` fused Softmax-table route from
`d32` to a synthetic widened `d64` source row.

The local native Stwo route verifies one fused proof object for bounded
attention arithmetic plus LogUp Softmax-table membership:

- source arithmetic proof: `248,702` JSON proof bytes
- LogUp sidecar proof: `36,400` JSON proof bytes
- matched split frontier: `285,102` JSON proof bytes
- fused proof: `253,257` JSON proof bytes
- fused saving: `31,845` JSON proof bytes
- fused ratio: `0.888303x`
- lookup claims: `1,184`
- trace rows: `2,048`

The fused proof is `4,555` bytes larger than the source arithmetic proof alone,
so this is not a source-only compression result. It is a matched split-frontier
result: one fused proof replaces the source arithmetic proof plus LogUp sidecar
and saves `31,845` proof bytes against that honest comparator.

## d32 To d64 Read

Holding two heads and `seq32` fixed:

| profile | width | lookup claims | trace rows | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|
| `d32_two_head_seq32` | `32` | `1,184` | `2,048` | `176,473` | `150,147` | `0.850821x` |
| `d64_two_head_seq32` | `64` | `1,184` | `2,048` | `285,102` | `253,257` | `0.888303x` |

From `d32` to `d64`:

- width grows `2.000000x`
- lookup claims stay fixed at `1.000000x`
- trace rows stay fixed at `1.000000x`
- source arithmetic proof bytes grow `1.709327x`
- matched split proof bytes grow `1.615556x`
- fused proof bytes grow `1.686727x`
- fused savings grow `1.209641x`

This is a GO for the first d64 falsification row: fusion still beats the
matched source-plus-sidecar frontier. It is also a useful warning: the relative
ratio weakens from `0.850821x` to `0.888303x`, so width pressure is real and
must be measured instead of assumed away.

## Matrix Impact

The controlled route matrix now has:

- `15` matched route rows
- `6,484` total lookup claims
- `10,048` total trace rows
- `1,696,600` matched split proof bytes
- `1,398,430` fused proof bytes
- `298,170` aggregate fused proof-byte savings

The fuller crossing grid is now `15 / 60` proved and `45 / 60` missing.

## Correctness Discipline

The d64 route keeps the local-only validation discipline:

- source, sidecar, and fused proof envelopes verify with the native Stwo CLI
- source input invariant tests pass `21 / 21`
- sidecar gate rejects `28 / 28` mutation cases
- fused gate rejects `30 / 30` mutation cases
- route matrix rejects `38 / 38` drift and overclaim mutations
- fuller grid rejects `18 / 18` drift and overclaim mutations
- evidence is bound by source commitments, proof-envelope commitments, table
  multiplicities, verifier domains, statement versions, and non-claim text

## Non-Claims

This is not exact real-valued Softmax. It is not full autoregressive inference.
It is not a full transformer block. It is not recursion, PCD, private-witness
privacy, on-chain verification, timing evidence, or a NANOZK comparison.

The `d64` source row is deterministically widened from the checked `d32`
two-head `seq32` source fixture and recomputes every score, output, and
commitment. It is not a model-faithful d64 transformer trace.

The current claim is narrower: in this native Stwo bounded Softmax-table
attention family, the fused proof object continues to beat the matched
source-plus-sidecar comparator at `d64` two-head `seq32`, while the route matrix
records that width pressure weakens the relative saving.

## Issue #715 Remaining Gates

This PR is one checked row inside issue #715, not completion of the full issue.
The following issue-level gates remain open and must not be inferred from this
artifact:

- `d128` and `d256` attention rows: not produced here. They remain gated behind
  the checked `d64` result and either generated backend support or dedicated
  native rows.
- `seq16`/`seq32` d64 slope: only `d64_two_head_seq32` exists here. The adjacent
  `d64_two_head_seq16` row is the next recommended falsification point.
- typed and binary/raw proof-size accounting: this artifact reports JSON proof
  bytes only. Typed and raw/binary accounting remain a separate hardening gate
  before paper-facing proof-size claims.
- external baseline: no EZKL, zkVM, NANOZK, Jolt, or DeepProve row is included
  here. External comparisons require a same-surface baseline with explicit
  reproducibility labeling.

## Reproducibility Metadata

- fused backend binary:
  `zkai_attention_kv_native_d64_two_head_seq32_fused_softmax_table_proof`
- fused backend version:
  `stwo-attention-kv-d64-two-head-seq32-fused-bounded-softmax-table-logup-v1`
- fused proof version:
  `stwo-attention-kv-d64-two-head-seq32-fused-bounded-softmax-table-logup-proof-v1`
- fused statement version:
  `zkai-attention-kv-stwo-native-d64-two-head-seq32-fused-softmax-table-logup-statement-v1`
- toolchain and features:
  `cargo +nightly-2025-07-14 --locked --features stwo-backend`
- timing mode:
  `proof_existence_and_byte_accounting_only_not_public_benchmark`

Evidence paths:

- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-seq32-bounded-softmax-table-proof-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-seq32-bounded-softmax-table-proof-2026-05.envelope.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-seq32-softmax-table-logup-sidecar-proof-2026-05.envelope.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-seq32-softmax-table-logup-sidecar-gate-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-seq32-fused-softmax-table-gate-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json`

## Reproduction

```bash
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_native_d64_two_head_seq32_bounded_softmax_table_proof_input
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d64_two_head_seq32_air_private_softmax_table_lookup_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d64_two_head_seq32_fused_softmax_table_native_gate
cargo +nightly-2025-07-14 test --locked attention_kv_native_d64_two_head_seq32_bounded_softmax_table_proof --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked attention_kv_d64_two_head_seq32_softmax_table_lookup --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked attention_kv_d64_two_head_seq32_fused_softmax_table --lib --features stwo-backend
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_two_head_seq32_bounded_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-seq32-bounded-softmax-table-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_two_head_seq32_softmax_table_lookup_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-seq32-softmax-table-logup-sidecar-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_two_head_seq32_fused_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json
python3.10 scripts/zkai_attention_kv_fused_softmax_table_route_matrix_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.tsv
python3.10 scripts/zkai_attention_kv_fuller_crossing_grid_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.tsv
```
