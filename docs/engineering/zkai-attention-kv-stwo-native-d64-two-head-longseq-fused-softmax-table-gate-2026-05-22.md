# d64 Two-Head Seq16 Fused Softmax-Table Gate

Date: 2026-05-22

Issue: #715

## Result

This slice fills the adjacent `d64_two_head_seq16` row below the already checked
`d64_two_head_seq32` route. It exists to test whether the d64 seq32 result was a
one-off sequence artifact or part of a measurable sequence slope.

The local native Stwo route verifies one fused proof object for bounded
attention arithmetic plus LogUp Softmax-table membership:

- source arithmetic proof: `230,688` JSON proof bytes
- LogUp sidecar proof: `27,037` JSON proof bytes
- matched split frontier: `257,725` JSON proof bytes
- fused proof: `238,504` JSON proof bytes
- fused saving: `19,221` JSON proof bytes
- fused ratio: `0.925421x`
- lookup claims: `336`
- trace rows: `512`

The fused proof is `7,816` bytes larger than the source arithmetic proof alone,
so this is not a source-only compression result. It is a matched split-frontier
result: one fused proof replaces the source arithmetic proof plus LogUp sidecar
and saves `19,221` proof bytes against that honest comparator.

## d32 To d64 Seq16 Read

Holding two heads and `seq16` fixed:

| profile | width | lookup claims | trace rows | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|
| `d32_two_head_seq16` | `32` | `336` | `512` | `162,138` | `132,543` | `0.817470x` |
| `d64_two_head_seq16` | `64` | `336` | `512` | `257,725` | `238,504` | `0.925421x` |

From `d32` to `d64` at `seq16`:

- width grows `2.000000x`
- lookup claims stay fixed at `1.000000x`
- trace rows stay fixed at `1.000000x`
- source arithmetic proof bytes grow `1.708003x`
- matched split proof bytes grow `1.589541x`
- fused proof bytes grow `1.799446x`
- fused savings shrink to `0.649468x`

This is a useful negative pressure check. Fusion still beats the matched
source-plus-sidecar frontier at d64 seq16, but the relative saving is weaker
than at d32 seq16. Width pressure is real.

## d64 Seq16 To Seq32 Read

Holding d64 and two heads fixed:

| profile | sequence | lookup claims | trace rows | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|
| `d64_two_head_seq16` | `16` | `336` | `512` | `257,725` | `238,504` | `0.925421x` |
| `d64_two_head_seq32` | `32` | `1,184` | `2,048` | `285,102` | `253,257` | `0.888303x` |

From `seq16` to `seq32` at d64:

- sequence length grows `2.000000x`
- lookup claims grow `3.523810x`
- trace rows grow `4.000000x`
- source arithmetic proof bytes grow `1.078088x`
- matched split proof bytes grow `1.106226x`
- fused proof bytes grow `1.061856x`
- fused savings grow `1.656782x`

This is the sharper signal from the row. At fixed d64 width, the checked lookup
work and trace rows grow much faster than fused proof bytes. That supports the
proof-pressure hypothesis, but only inside this bounded Softmax-table fixture.

## Matrix Impact

At this row's capture time, the controlled route matrix had:

- `16` matched route rows
- `6,820` total lookup claims
- `10,560` total trace rows
- `1,954,325` matched split proof bytes
- `1,636,934` fused proof bytes
- `317,391` aggregate fused proof-byte savings

The fuller crossing grid was `16 / 60` proved and `44 / 60` missing at this
row's capture time. The live route matrix is superseded by the latest checked
matrix evidence.

## Correctness Discipline

The d64 seq16 route keeps the local-only validation discipline:

- source, sidecar, and fused proof envelopes verify with the native Stwo CLI
- source input invariant tests pass `22 / 22`
- sidecar gate rejects `28 / 28` mutation cases
- fused gate rejects `30 / 30` mutation cases
- route matrix rejects `41 / 41` drift and overclaim mutations
- fuller grid rejects `18 / 18` drift and overclaim mutations
- evidence is bound by source commitments, proof-envelope commitments, table
  multiplicities, verifier domains, statement versions, and non-claim text

## Non-Claims

This is not exact real-valued Softmax. It is not full autoregressive inference.
It is not a full transformer block. It is not recursion, PCD, private-witness
privacy, on-chain verification, timing evidence, or a NANOZK comparison.

The `d64` source row is deterministically widened from the checked `d32`
two-head `seq16` source fixture and recomputes every score, output, and
commitment. It is not a model-faithful d64 transformer trace.

The current claim is narrower: in this native Stwo bounded Softmax-table
attention family, the fused proof object still beats the matched
source-plus-sidecar comparator at `d64` two-head `seq16`, and the adjacent d64
sequence slope shows lookup pressure growing much faster than fused proof bytes.

## Issue #715 Remaining Gates

This PR is one checked row inside issue #715, not completion of the full issue.
The following issue-level gates remain open and must not be inferred from this
artifact:

- `d128` and `d256` attention rows: not produced here. They remain gated behind
  checked `d64` rows and either generated backend support or dedicated native
  rows.
- `d16_two_head_seq32`: since filled by the 2026-05-22 lower-width seq32 route.
- typed and binary/raw proof-size accounting: this artifact reports JSON proof
  bytes only. Typed and raw/binary accounting remain a separate hardening gate
  before paper-facing proof-size claims.
- external baseline: no EZKL, zkVM, NANOZK, Jolt, or DeepProve row is included
  here. External comparisons require a same-surface baseline with explicit
  reproducibility labeling.

## Reproducibility Metadata

- fused backend binary:
  `zkai_attention_kv_native_d64_two_head_longseq_fused_softmax_table_proof`
- fused backend version:
  `stwo-attention-kv-d64-two-head-longseq-fused-bounded-softmax-table-logup-v1`
- fused proof version:
  `stwo-attention-kv-d64-two-head-longseq-fused-bounded-softmax-table-logup-proof-v1`
- fused statement version:
  `zkai-attention-kv-stwo-native-d64-two-head-longseq-fused-softmax-table-logup-statement-v1`
- toolchain and features:
  `cargo +nightly-2025-07-14 --locked --features stwo-backend`
- timing mode:
  `proof_existence_and_byte_accounting_only_not_public_benchmark`

Evidence paths:

- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-longseq-bounded-softmax-table-proof-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-longseq-bounded-softmax-table-proof-2026-05.envelope.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-longseq-softmax-table-logup-sidecar-proof-2026-05.envelope.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-longseq-fused-softmax-table-proof-2026-05.envelope.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-longseq-softmax-table-logup-sidecar-gate-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-longseq-fused-softmax-table-gate-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json`

## Reproduction

```bash
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_native_d64_two_head_longseq_bounded_softmax_table_proof_input
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d64_two_head_longseq_air_private_softmax_table_lookup_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d64_two_head_longseq_fused_softmax_table_native_gate
cargo +nightly-2025-07-14 test --locked attention_kv_native_d64_two_head_longseq_bounded_softmax_table_proof --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked attention_kv_d64_two_head_longseq_softmax_table_lookup --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked attention_kv_d64_two_head_longseq_fused_softmax_table --lib --features stwo-backend
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_two_head_longseq_bounded_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-longseq-bounded-softmax-table-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_two_head_longseq_softmax_table_lookup_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-longseq-softmax-table-logup-sidecar-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_two_head_longseq_fused_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-longseq-fused-softmax-table-proof-2026-05.envelope.json
python3.10 scripts/zkai_attention_kv_d64_two_head_longseq_air_private_softmax_table_lookup_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-longseq-softmax-table-logup-sidecar-gate-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-longseq-softmax-table-logup-sidecar-gate-2026-05.tsv
python3.10 scripts/zkai_attention_kv_d64_two_head_longseq_fused_softmax_table_native_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-longseq-fused-softmax-table-gate-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-longseq-fused-softmax-table-gate-2026-05.tsv
python3.10 scripts/zkai_attention_kv_fused_softmax_table_route_matrix_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.tsv
python3.10 scripts/zkai_attention_kv_fuller_crossing_grid_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.tsv
```
