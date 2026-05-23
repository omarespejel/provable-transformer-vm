# d128 Four-Head Seq64 Fused Softmax-Table Gate

Date: 2026-05-23

Issue: #715

## Result

This slice is the d128 four-head sequence-jump decision gate from the proof
pressure scaling plan. It extends the checked `d128_four_head_seq32` row to
`seq64`.

The local native Stwo route verifies one fused proof object for bounded
attention arithmetic plus LogUp Softmax-table membership:

- source arithmetic proof: `490,307` proof bytes
- LogUp sidecar proof: `49,363` proof bytes
- matched split frontier: `539,670` proof bytes
- fused proof: `495,854` proof bytes
- fused saving: `43,816` proof bytes
- fused ratio: `0.918810x`
- lookup claims: `8,832`
- trace rows: `16,384`

The fused proof is `5,547` bytes larger than the source arithmetic proof
alone, so this is not a source-only compression result. The honest comparator
is the matched source-plus-sidecar frontier. Against that comparator, one
fused proof replaces the source arithmetic proof plus LogUp sidecar and saves
`43,816` proof bytes.

## d128 Four-Head Sequence-Axis Read

Holding `d128` and four heads fixed:

| profile | sequence | lookup claims | trace rows | source proof bytes | sidecar proof bytes | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `d128_four_head_seq32` | `32` | `2,368` | `4,096` | `463,410` | `41,524` | `504,934` | `465,630` | `0.922160x` |
| `d128_four_head_seq64` | `64` | `8,832` | `16,384` | `490,307` | `49,363` | `539,670` | `495,854` | `0.918810x` |

From `seq32` to `seq64`:

- lookup claims grow `3.729730x`
- trace rows grow `4.000000x`
- source arithmetic proof bytes grow `1.058041x`
- LogUp sidecar proof bytes grow `1.188782x`
- matched split proof bytes grow `1.068793x`
- fused proof bytes grow `1.064910x`
- fused savings grow `1.114797x`

This is a GO for the issue #715 d128 four-head seq64 decision gate. The work
being checked grows much faster than the fused proof bytes, the fused proof
still beats the matched split frontier, and the saving improves in absolute
bytes. The result does not complete the full grid. The next question is
whether the d128 width story is anchored cleanly at lower pressure and whether
the effect survives a d256 stress row.

## Matrix Impact

The controlled route matrix now has:

- `28` matched route rows
- `44,300` total lookup claims
- `78,400` total trace rows
- `5,915,661` matched split proof bytes
- `5,195,892` fused proof bytes
- `719,769` aggregate fused proof-byte savings

The fuller crossing grid is now `28 / 100` proved and `72 / 100` missing.

The wide-grid selector now promotes `d128_h1_seq16` as the next low-pressure
d128 width anchor, then `d256_h2_seq32` as the next width stress test.

## Reproducibility Metadata

- timing mode: `proof_existence_and_byte_accounting_only_not_public_benchmark`
- heads: `4`
- steps per head: `64`
- key/value width: `128`
- lookup/score rows: `8,832`
- trace rows: `16,384`
- table rows: `9`
- source binary:
  `zkai_attention_kv_native_d128_four_head_seq64_bounded_softmax_table_proof`
- source backend:
  `stwo-attention-kv-d128-four-head-seq64-causal-mask-bounded-softmax-table-v1`
- source proof version:
  `stwo-attention-kv-d128-four-head-seq64-causal-mask-bounded-softmax-table-air-proof-v1`
- source statement version:
  `zkai-attention-kv-stwo-native-d128-four-head-seq64-bounded-softmax-table-statement-v1`
- sidecar binary:
  `zkai_attention_kv_native_d128_four_head_seq64_softmax_table_lookup_proof`
- sidecar backend:
  `attention-kv-d128-four-head-seq64-causal-mask-bounded-softmax-table-logup-sidecar-v1`
- sidecar proof version:
  `stwo-attention-kv-d128-four-head-seq64-softmax-table-logup-sidecar-proof-v1`
- sidecar statement version:
  `zkai-attention-kv-stwo-native-d128-four-head-seq64-softmax-table-logup-sidecar-statement-v1`
- fused binary:
  `zkai_attention_kv_native_d128_four_head_seq64_fused_softmax_table_proof`
- fused backend:
  `stwo-attention-kv-d128-four-head-seq64-fused-bounded-softmax-table-logup-v1`
- fused proof version:
  `stwo-attention-kv-d128-four-head-seq64-fused-bounded-softmax-table-logup-proof-v1`
- fused statement version:
  `zkai-attention-kv-stwo-native-d128-four-head-seq64-fused-softmax-table-logup-statement-v1`

## Large Local Artifacts

The source input and proof envelopes for this row are generated locally but are
not checked into git because each exceeds GitHub's `100 MB` blob limit. Their
sizes, SHA-256 digests, and reproduction commands are tracked in:

`docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq64-large-artifacts-2026-05.json`

The tracked gate JSON, route matrix, fuller grid, claim pack, wide selector,
TSV summaries, Rust modules, and human gate note remain in the PR. The large
source/proof artifacts must be regenerated locally before running the
artifact-heavy native verifier gates.

## Correctness Discipline

The d128 four-head seq64 route keeps the local-only validation discipline:

- source, sidecar, and fused proof envelopes verify with the native Stwo CLI
- source input invariant tests reject stale width, head, sequence, row, and
  commitment drift
- sidecar gate rejects `28 / 28` mutation cases
- fused gate rejects `30 / 30` mutation cases
- the same-size fused proof-byte tamper is rejected by the native verifier
- route matrix rejects `66 / 66` drift and overclaim mutations
- fuller grid rejects `18 / 18` drift and overclaim mutations
- scaling claim pack rejects `27 / 27` drift and overclaim mutations
- wide-grid selector rejects `28 / 28` drift and overclaim mutations
- evidence is bound by source commitments, proof-envelope commitments, table
  multiplicities, verifier domains, statement versions, source digests, and
  non-claim text

The full fused unittest is heavier than the local tool window because shared
setup repeats the native verifier work, so the checked validation for this PR
uses the fused writer, focused fused mutation unittest, and direct same-size
native verifier tamper check rather than claiming that full broad unittest
completed. In a fresh clone, tests that require the oversized local artifacts
skip until those artifacts are regenerated from the manifest.

## Non-Claims

This is not exact real-valued Softmax. It is not full transformer inference or
full autoregressive inference. It is not a full transformer block. It is not
recursion, PCD, production zkML readiness, private-witness privacy, on-chain
verification, timing evidence, or a NANOZK comparison.

The d128 source row is deterministically extended from checked bounded
fixtures. It is not a model-faithful d128 four-head transformer trace.

## Issue #715 Remaining Gates

This PR is one checked decision row inside issue #715, not completion of the
full issue. The following issue-level gates remain open:

- `d128_h1_seq16` as a lower-pressure d128 width anchor.
- `d256_h2_seq32` as the next width stress row.
- typed and binary/raw proof-size accounting for the widened attention rows.
- external same-surface baseline: no EZKL, zkVM, NANOZK, Jolt, or DeepProve
  row is included here.
- a paper-facing slope table after the next width row lands or fails.

## Reproduction

```bash
just gate-fast
python3.10 scripts/zkai_attention_kv_stwo_native_d128_four_head_seq64_bounded_softmax_table_proof_input.py --write-json docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq64-bounded-softmax-table-proof-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq64-bounded-softmax-table-proof-2026-05.tsv
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_four_head_seq64_bounded_softmax_table_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq64-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq64-bounded-softmax-table-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_four_head_seq64_bounded_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq64-bounded-softmax-table-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_four_head_seq64_softmax_table_lookup_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq64-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq64-softmax-table-logup-sidecar-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_four_head_seq64_softmax_table_lookup_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq64-softmax-table-logup-sidecar-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_four_head_seq64_fused_softmax_table_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq64-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq64-fused-softmax-table-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_four_head_seq64_fused_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq64-fused-softmax-table-proof-2026-05.envelope.json
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_native_d128_four_head_seq64_bounded_softmax_table_proof_input
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d128_four_head_seq64_air_private_softmax_table_lookup_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d128_four_head_seq64_fused_softmax_table_native_gate.AttentionKvD128FourHeadSeq64FusedSoftmaxTableNativeGateTests.test_all_declared_mutations_reject
python3.10 scripts/zkai_attention_kv_d128_four_head_seq64_air_private_softmax_table_lookup_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq64-softmax-table-logup-sidecar-gate-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq64-softmax-table-logup-sidecar-gate-2026-05.tsv
python3.10 scripts/zkai_attention_kv_d128_four_head_seq64_fused_softmax_table_native_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq64-fused-softmax-table-gate-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq64-fused-softmax-table-gate-2026-05.tsv
python3.10 scripts/zkai_attention_kv_fused_softmax_table_route_matrix_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.tsv
python3.10 scripts/zkai_attention_kv_fuller_crossing_grid_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.tsv
python3.10 scripts/zkai_proof_pressure_scaling_claim_pack_gate.py --write-json docs/engineering/evidence/zkai-proof-pressure-scaling-claim-pack-2026-05.json --write-tsv docs/engineering/evidence/zkai-proof-pressure-scaling-claim-pack-2026-05.tsv
python3.10 scripts/zkai_proof_pressure_wide_grid_selector_gate.py --write-json docs/engineering/evidence/zkai-proof-pressure-wide-grid-selector-2026-05.json --write-tsv docs/engineering/evidence/zkai-proof-pressure-wide-grid-selector-2026-05.tsv
git diff --check
just gate
```
