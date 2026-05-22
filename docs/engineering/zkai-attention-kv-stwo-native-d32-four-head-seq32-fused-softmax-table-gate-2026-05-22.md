# d32 Four-Head Seq32 Fused Softmax-Table Gate

Date: 2026-05-22

Issue: #728

## Result

This slice fills the `d32_four_head_seq32` crossing row. It tests the most
useful next pressure point from issue #715: keep width `d32` and sequence
length `seq32`, then increase head count from two heads to four heads.

The local native Stwo route verifies one fused proof object for bounded
attention arithmetic plus LogUp Softmax-table membership:

- source arithmetic proof: `151,309` JSON proof bytes
- LogUp sidecar proof: `41,628` JSON proof bytes
- matched split frontier: `192,937` JSON proof bytes
- fused proof: `154,670` JSON proof bytes
- fused saving: `38,267` JSON proof bytes
- fused ratio: `0.801661x`
- lookup claims: `2,368`
- trace rows: `4,096`

The fused proof is `3,361` bytes larger than the source arithmetic proof alone,
so this is not a source-only compression result. It is a matched split-frontier
result: one fused proof replaces the source arithmetic proof plus LogUp sidecar
and saves `38,267` proof bytes against that honest comparator.

## d32 Seq32 Head-Count Read

Holding width `d32` and `seq32` fixed:

| profile | heads | lookup claims | trace rows | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|
| `d32_two_head_seq32` | `2` | `1,184` | `2,048` | `176,473` | `150,147` | `0.850821x` |
| `d32_four_head_seq32` | `4` | `2,368` | `4,096` | `192,937` | `154,670` | `0.801661x` |

From two heads to four heads at d32 seq32:

- head count grows `2.000000x`
- lookup claims grow `2.000000x`
- trace rows grow `2.000000x`
- source proof bytes grow `1.039946x`
- matched split proof bytes grow `1.093295x`
- fused proof bytes grow `1.030124x`
- fused savings grow `1.453582x`

This is the strongest head-count signal in the current grid. The lookup surface
and trace rows double, but the fused proof object grows only `1.030124x`. The
matched split frontier grows more than the fused proof, so the saving improves
from `26,326` bytes to `38,267` bytes.

The honest interpretation is structural amortization, not a final zkML
benchmark: proof plumbing is still being shared while attention lookup pressure
is scaled on the head axis.

## Matrix Impact

The controlled route matrix now has:

- `19` matched route rows
- `11,044` total lookup claims
- `17,728` total trace rows
- `2,444,487` matched split proof bytes
- `2,026,301` fused proof bytes
- `418,186` aggregate fused proof-byte savings

The fuller crossing grid is now `19 / 60` proved and `41 / 60` missing. The
next low-risk rows are `d64_four_head_seq32` and `d32_four_head_seq64`, which
would test whether this head-plus-sequence amortization survives larger width
or a longer sequence surface.

## Correctness Discipline

The d32 four-head seq32 route keeps the local-only validation discipline:

- source, sidecar, and fused proof envelopes verify with the native Stwo CLI
- source input invariant tests pass `22 / 22`
- source, sidecar, and fused Rust proof tests pass `33 / 33`
- sidecar gate rejects `28 / 28` mutation cases
- fused gate rejects `30 / 30` mutation cases
- route matrix rejects `49 / 49` drift and overclaim mutations
- fuller grid rejects `18 / 18` drift and overclaim mutations
- evidence is bound by source commitments, proof-envelope commitments, table
  multiplicities, verifier domains, statement versions, target identifiers, and
  non-claim text

## Non-Claims

This is not exact real-valued Softmax. It is not full autoregressive inference.
It is not a full transformer block. It is not recursion, PCD, private-witness
privacy, on-chain verification, timing evidence, or a NANOZK comparison.

The `d32_four_head_seq32` source row is a bounded integer Softmax-table fixture,
not a model-faithful d32 four-head transformer trace.

The current claim is narrower: in this native Stwo bounded Softmax-table
attention family, the fused proof object beats the matched source-plus-sidecar
comparator at d32 four-head seq32, and the d32 seq32 head-count slope shows
proof plumbing is still being shared while lookup work and trace rows double.

## Issue #715 Remaining Gates

This PR is one checked row inside the larger scaling agenda, not completion of
the full issue. The following gates remain open and must not be inferred from
this artifact:

- `d64_four_head_seq32` and `d32_four_head_seq64` scaling rows;
- `d128` and `d256` attention rows;
- typed and binary/raw proof-size accounting for the full route matrix;
- median-of-5 timing after proof shapes stabilize;
- same-surface external baseline;
- full transformer block surface.

## Reproducibility Metadata

- fused backend binary:
  `zkai_attention_kv_native_d32_four_head_seq32_fused_softmax_table_proof`
- fused backend version:
  `stwo-attention-kv-d32-four-head-seq32-fused-bounded-softmax-table-logup-v1`
- fused proof version:
  `stwo-attention-kv-d32-four-head-seq32-fused-bounded-softmax-table-logup-proof-v1`
- fused statement version:
  `zkai-attention-kv-stwo-native-d32-four-head-seq32-fused-softmax-table-logup-statement-v1`
- toolchain and features:
  `cargo +nightly-2025-07-14 --locked --features stwo-backend`
- timing mode:
  `proof_existence_and_byte_accounting_only_not_public_benchmark`

Evidence paths:

- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-seq32-bounded-softmax-table-proof-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-seq32-bounded-softmax-table-proof-2026-05.envelope.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-seq32-softmax-table-logup-sidecar-proof-2026-05.envelope.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-seq32-fused-softmax-table-proof-2026-05.envelope.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-seq32-softmax-table-logup-sidecar-gate-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-seq32-fused-softmax-table-gate-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json`

## Reproduction

```bash
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_native_d32_four_head_seq32_bounded_softmax_table_proof_input
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d32_four_head_seq32_air_private_softmax_table_lookup_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d32_four_head_seq32_fused_softmax_table_native_gate
cargo +nightly-2025-07-14 test --locked attention_kv_native_d32_four_head_seq32_bounded_softmax_table_proof --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked attention_kv_d32_four_head_seq32_softmax_table_lookup --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked attention_kv_d32_four_head_seq32_fused_softmax_table --lib --features stwo-backend
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d32_four_head_seq32_bounded_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-seq32-bounded-softmax-table-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d32_four_head_seq32_softmax_table_lookup_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-seq32-softmax-table-logup-sidecar-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d32_four_head_seq32_fused_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-seq32-fused-softmax-table-proof-2026-05.envelope.json
python3.10 scripts/zkai_attention_kv_d32_four_head_seq32_air_private_softmax_table_lookup_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-seq32-softmax-table-logup-sidecar-gate-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-seq32-softmax-table-logup-sidecar-gate-2026-05.tsv
python3.10 scripts/zkai_attention_kv_d32_four_head_seq32_fused_softmax_table_native_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-seq32-fused-softmax-table-gate-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-seq32-fused-softmax-table-gate-2026-05.tsv
python3.10 scripts/zkai_attention_kv_fused_softmax_table_route_matrix_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.tsv
python3.10 scripts/zkai_attention_kv_fuller_crossing_grid_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.tsv
```
