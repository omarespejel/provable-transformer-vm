# d32 Four-Head Seq16 Fused Softmax-Table Gate

Date: 2026-05-22

Issue: #715

## Result

This slice fills the `d32_four_head_seq16` crossing row. It tests whether the
existing d32 two-head seq16 saving survives a head-count increase without also
changing sequence length.

The local native Stwo route verifies one fused proof object for bounded
attention arithmetic plus LogUp Softmax-table membership:

- source arithmetic proof: `139,755` JSON proof bytes
- LogUp sidecar proof: `30,263` JSON proof bytes
- matched split frontier: `170,018` JSON proof bytes
- fused proof: `142,334` JSON proof bytes
- fused saving: `27,684` JSON proof bytes
- fused ratio: `0.837170x`
- lookup claims: `672`
- trace rows: `1,024`

The fused proof is `2,579` bytes larger than the source arithmetic proof alone,
so this is not a source-only compression result. It is a matched split-frontier
result: one fused proof replaces the source arithmetic proof plus LogUp sidecar
and saves `27,684` proof bytes against that honest comparator.

## d32 Head-Count Read

Holding width `d32` and `seq16` fixed:

| profile | heads | lookup claims | trace rows | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|
| `d32_two_head_seq16` | `2` | `336` | `512` | `162,138` | `132,543` | `0.817470x` |
| `d32_four_head_seq16` | `4` | `672` | `1,024` | `170,018` | `142,334` | `0.837170x` |

From two heads to four heads at d32 seq16:

- head count grows `2.000000x`
- lookup claims grow `2.000000x`
- trace rows grow `2.000000x`
- matched split proof bytes grow `1.048601x`
- fused proof bytes grow `1.073870x`
- fused savings shrink to `0.935428x`

This is a positive but smaller signal than the best seq32 sequence rows. The
work surface doubles and the fused proof remains smaller than the matched split
frontier, but the ratio weakens from `0.817470x` to `0.837170x`. The honest
interpretation is structural sharing persists on this head-count crossing, but
head pressure is not the strongest lever by itself.

## Matrix Impact

The controlled route matrix now has:

- `18` matched route rows
- `8,676` total lookup claims
- `13,632` total trace rows
- `2,251,550` matched split proof bytes
- `1,871,631` fused proof bytes
- `379,919` aggregate fused proof-byte savings

The fuller crossing grid is now `18 / 60` proved and `42 / 60` missing. The
next low-risk crossing is `d32_four_head_seq32`, which tests whether the new
four-head d32 row keeps saving when sequence pressure is also extended to
`seq32`.

## Correctness Discipline

The d32 four-head seq16 route keeps the local-only validation discipline:

- source, sidecar, and fused proof envelopes verify with the native Stwo CLI
- source input invariant tests pass `22 / 22`
- source, sidecar, and fused Rust proof tests pass `32 / 32`
- sidecar gate rejects `28 / 28` mutation cases
- fused gate rejects `30 / 30` mutation cases
- route matrix rejects `47 / 47` drift and overclaim mutations
- fuller grid rejects `18 / 18` drift and overclaim mutations
- evidence is bound by source commitments, proof-envelope commitments, table
  multiplicities, verifier domains, statement versions, and non-claim text

## Non-Claims

This is not exact real-valued Softmax. It is not full autoregressive inference.
It is not a full transformer block. It is not recursion, PCD, private-witness
privacy, on-chain verification, timing evidence, or a NANOZK comparison.

The `d32_four_head_seq16` source row is a bounded integer Softmax-table fixture,
not a model-faithful d32 transformer trace.

The current claim is narrower: in this native Stwo bounded Softmax-table
attention family, the fused proof object still beats the matched
source-plus-sidecar comparator at d32 four-head seq16, and the d32 head-count
slope shows proof plumbing is still being shared while the lookup surface
doubles.

## Issue #715 Remaining Gates

This PR is one checked row inside issue #715, not completion of the full issue.
The following issue-level gates remain open and must not be inferred from this
artifact:

- `d32_four_head_seq32`: the next low-risk row for combining the new head
  pressure with the seq32 sequence pressure.
- `d128` and `d256` attention rows: not produced here.
- typed and binary/raw proof-size accounting: this artifact reports JSON proof
  bytes only.
- median-of-5 timing: not recorded until proof shapes stabilize.
- external baseline: no EZKL, zkVM, NANOZK, Jolt, or DeepProve row is included
  here.

## Reproducibility Metadata

- fused backend binary:
  `zkai_attention_kv_native_d32_four_head_longseq_fused_softmax_table_proof`
- fused backend version:
  `stwo-attention-kv-d32-four-head-longseq-fused-bounded-softmax-table-logup-v1`
- fused proof version:
  `stwo-attention-kv-d32-four-head-longseq-fused-bounded-softmax-table-logup-proof-v1`
- fused statement version:
  `zkai-attention-kv-stwo-native-d32-four-head-longseq-fused-softmax-table-logup-statement-v1`
- toolchain and features:
  `cargo +nightly-2025-07-14 --locked --features stwo-backend`
- timing mode:
  `proof_existence_and_byte_accounting_only_not_public_benchmark`

Evidence paths:

- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-longseq-bounded-softmax-table-proof-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-longseq-bounded-softmax-table-proof-2026-05.envelope.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-longseq-softmax-table-logup-sidecar-proof-2026-05.envelope.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-longseq-fused-softmax-table-proof-2026-05.envelope.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-longseq-softmax-table-logup-sidecar-gate-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-longseq-fused-softmax-table-gate-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json`

## Reproduction

```bash
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_native_d32_four_head_longseq_bounded_softmax_table_proof_input
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d32_four_head_longseq_air_private_softmax_table_lookup_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d32_four_head_longseq_fused_softmax_table_native_gate
cargo +nightly-2025-07-14 test --locked attention_kv_native_d32_four_head_longseq_bounded_softmax_table_proof --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked attention_kv_d32_four_head_longseq_softmax_table_lookup --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked attention_kv_d32_four_head_longseq_fused_softmax_table --lib --features stwo-backend
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d32_four_head_longseq_bounded_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-longseq-bounded-softmax-table-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d32_four_head_longseq_softmax_table_lookup_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-longseq-softmax-table-logup-sidecar-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d32_four_head_longseq_fused_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-longseq-fused-softmax-table-proof-2026-05.envelope.json
python3.10 scripts/zkai_attention_kv_d32_four_head_longseq_air_private_softmax_table_lookup_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-longseq-softmax-table-logup-sidecar-gate-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-longseq-softmax-table-logup-sidecar-gate-2026-05.tsv
python3.10 scripts/zkai_attention_kv_d32_four_head_longseq_fused_softmax_table_native_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-longseq-fused-softmax-table-gate-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-four-head-longseq-fused-softmax-table-gate-2026-05.tsv
python3.10 scripts/zkai_attention_kv_fused_softmax_table_route_matrix_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.tsv
python3.10 scripts/zkai_attention_kv_fuller_crossing_grid_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.tsv
```
