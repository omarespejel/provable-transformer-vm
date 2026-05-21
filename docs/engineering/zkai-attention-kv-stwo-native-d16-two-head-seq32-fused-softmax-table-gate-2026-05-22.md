# d16 Two-Head Seq32 Fused Softmax-Table Gate

Date: 2026-05-22

Issue: #715

## Result

This slice fills the lower-width `d16_two_head_seq32` row between the earlier
`d8_two_head_seq32` and `d32_two_head_seq32` routes.

The local native Stwo route verifies one fused proof object for bounded
attention arithmetic plus LogUp Softmax-table membership:

- source arithmetic proof: `90,754` JSON proof bytes
- LogUp sidecar proof: `36,453` JSON proof bytes
- matched split frontier: `127,207` JSON proof bytes
- fused proof: `92,363` JSON proof bytes
- fused saving: `34,844` JSON proof bytes
- fused ratio: `0.726084x`
- lookup claims: `1,184`
- trace rows: `2,048`

The fused proof is `1,609` bytes larger than the source arithmetic proof alone,
so this is not a source-only compression claim. It is a matched split-frontier
claim: one fused proof replaces the source arithmetic proof plus LogUp sidecar
and saves `34,844` proof bytes against that honest comparator.

## d16 Sequence Read

Holding d16 and two heads fixed:

| profile | sequence | lookup claims | trace rows | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|
| `d16_two_head_seq8` | `8` | `104` | `128` | `91,596` | `78,211` | `0.853869x` |
| `d16_two_head_seq16` | `16` | `336` | `512` | `108,158` | `84,868` | `0.784667x` |
| `d16_two_head_seq32` | `32` | `1,184` | `2,048` | `127,207` | `92,363` | `0.726084x` |

From `seq16` to `seq32` at d16:

- sequence length grows `2.000000x`
- lookup claims grow `3.523810x`
- trace rows grow `4.000000x`
- matched split proof bytes grow `1.176122x`
- fused proof bytes grow `1.088314x`
- fused savings grow `1.496093x`

This is a good pressure signal. Lookup work and trace rows grow several times,
but the fused proof object grows much more slowly.

## Seq32 Width Read

Holding two heads and `seq32` fixed:

| profile | width | lookup claims | trace rows | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|
| `d8_two_head_seq32` | `8` | `1,184` | `2,048` | `98,012` | `66,327` | `0.676723x` |
| `d16_two_head_seq32` | `16` | `1,184` | `2,048` | `127,207` | `92,363` | `0.726084x` |
| `d32_two_head_seq32` | `32` | `1,184` | `2,048` | `176,473` | `150,147` | `0.850821x` |
| `d64_two_head_seq32` | `64` | `1,184` | `2,048` | `285,102` | `253,257` | `0.888303x` |

The row confirms two things at once:

- the seq32 fused route still beats the matched split frontier at d16;
- width pressure is real, because the fused ratio weakens as width increases.

## Matrix Impact

The controlled route matrix now has:

- `17` matched route rows
- `8,004` total lookup claims
- `12,608` total trace rows
- `2,081,532` matched split proof bytes
- `1,729,297` fused proof bytes
- `352,235` aggregate fused proof-byte savings

The fuller crossing grid is now `17 / 60` proved and `43 / 60` missing.

## Correctness Discipline

The d16 seq32 route keeps the local-only validation discipline:

- source, sidecar, and fused proof envelopes verify with the native Stwo CLI
- source input invariant tests pass `21 / 21`
- sidecar and fused gate tests pass `41 / 41`
- route matrix tests pass `10 / 10`
- fuller grid tests pass `9 / 9`
- stale d32 constants were searched for and rejected before doc publication
- evidence is bound by source commitments, proof-envelope commitments, table
  multiplicities, verifier domains, statement versions, and non-claim text

## Non-Claims

This is not exact real-valued Softmax. It is not full autoregressive inference.
It is not a full transformer block. It is not recursion, PCD, private-witness
privacy, on-chain verification, timing evidence, or a NANOZK comparison.

The current claim is narrower: in this native Stwo bounded Softmax-table
attention family, the d16 two-head seq32 fused proof beats the matched
source-plus-sidecar comparator, and the d16 sequence slope supports the
proof-pressure amortization hypothesis.

## Issue #715 Remaining Gates

This PR is one checked row inside issue #715, not completion of the full issue.
The following gates remain open and must not be inferred from this artifact:

- `d128` and `d256` attention rows;
- typed and binary/raw proof-size accounting;
- median-of-5 timing after proof shapes stabilize;
- same-surface external baseline;
- full transformer block surface.

## Reproducibility Metadata

- fused backend binary:
  `zkai_attention_kv_native_d16_two_head_seq32_fused_softmax_table_proof`
- fused backend version:
  `stwo-attention-kv-d16-two-head-seq32-fused-bounded-softmax-table-logup-v1`
- fused proof version:
  `stwo-attention-kv-d16-two-head-seq32-fused-bounded-softmax-table-logup-proof-v1`
- fused statement version:
  `zkai-attention-kv-stwo-native-d16-two-head-seq32-fused-softmax-table-logup-statement-v1`
- toolchain and features:
  `cargo +nightly-2025-07-14 --locked --features stwo-backend`
- timing mode:
  `proof_existence_and_byte_accounting_only_not_public_benchmark`

Evidence paths:

- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-two-head-seq32-bounded-softmax-table-proof-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-two-head-seq32-bounded-softmax-table-proof-2026-05.envelope.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-two-head-seq32-softmax-table-logup-sidecar-proof-2026-05.envelope.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-two-head-seq32-softmax-table-logup-sidecar-gate-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-two-head-seq32-fused-softmax-table-gate-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json`

## Reproduction

```bash
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_native_d16_two_head_seq32_bounded_softmax_table_proof_input
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d16_two_head_seq32_air_private_softmax_table_lookup_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d16_two_head_seq32_fused_softmax_table_native_gate
cargo +nightly-2025-07-14 test --locked attention_kv_native_d16_two_head_seq32_bounded_softmax_table_proof --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked attention_kv_d16_two_head_seq32_softmax_table_lookup --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked attention_kv_d16_two_head_seq32_fused_softmax_table --lib --features stwo-backend
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d16_two_head_seq32_bounded_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-two-head-seq32-bounded-softmax-table-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d16_two_head_seq32_softmax_table_lookup_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-two-head-seq32-softmax-table-logup-sidecar-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d16_two_head_seq32_fused_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json
python3.10 scripts/zkai_attention_kv_d16_two_head_seq32_air_private_softmax_table_lookup_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-two-head-seq32-softmax-table-logup-sidecar-gate-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-two-head-seq32-softmax-table-logup-sidecar-gate-2026-05.tsv
python3.10 scripts/zkai_attention_kv_d16_two_head_seq32_fused_softmax_table_native_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-two-head-seq32-fused-softmax-table-gate-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-two-head-seq32-fused-softmax-table-gate-2026-05.tsv
python3.10 scripts/zkai_attention_kv_fused_softmax_table_route_matrix_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.tsv
python3.10 scripts/zkai_attention_kv_fuller_crossing_grid_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.tsv
```
