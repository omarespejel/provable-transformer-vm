# d128 Two-Head Seq64 Fused Softmax-Table Gate

Date: 2026-05-23

Issue: #715

## Result

This slice extends the checked `d128_two_head_seq32` fused Softmax-table route
to `seq64`. It is the second source-backed `d128` attention row in the
proof-pressure grid.

The local native Stwo route verifies one fused proof object for bounded
attention arithmetic plus LogUp Softmax-table membership:

- source arithmetic proof: `476,773` JSON proof bytes
- LogUp sidecar proof: `45,414` JSON proof bytes
- matched split frontier: `522,187` JSON proof bytes
- fused proof: `481,870` JSON proof bytes
- fused saving: `40,317` JSON proof bytes
- fused ratio: `0.922792x`
- lookup claims: `4,416`
- trace rows: `8,192`

The fused proof is `5,097` bytes larger than the source arithmetic proof alone,
so this is not a source-only compression result. The honest comparator is the
matched source-plus-sidecar frontier. Against that comparator, one fused proof
replaces the source arithmetic proof plus LogUp sidecar and saves `40,317`
proof bytes.

## d128 Two-Head Sequence Read

Holding `d128` and two heads fixed:

| profile | steps per head | lookup claims | trace rows | source proof bytes | sidecar proof bytes | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `d128_two_head_seq32` | `32` | `1,184` | `2,048` | `443,266` | `35,010` | `478,276` | `445,888` | `0.932282x` |
| `d128_two_head_seq64` | `64` | `4,416` | `8,192` | `476,773` | `45,414` | `522,187` | `481,870` | `0.922792x` |

From `seq32` to `seq64`:

- lookup claims grow `3.729730x`
- trace rows grow `4.000000x`
- source arithmetic proof bytes grow `1.075591x`
- LogUp sidecar proof bytes grow `1.297172x`
- matched split proof bytes grow `1.091811x`
- fused proof bytes grow `1.080697x`
- fused savings grow `1.244813x`

This is a GO for the issue #715 d128 sequence-pressure gate. The work being
checked grows much faster than the fused proof object, the fused proof still
beats the matched split frontier, and the saving is larger than the earlier
`d128_two_head_seq32` saving. It is still not a victory lap: the next question
is whether this positive d128 two-head signal survives head-axis pressure at
`d128_h4_seq32`.

## d64 To d128 Seq64 Width Read

Holding two heads and `seq64` fixed:

| profile | width | lookup claims | trace rows | source proof bytes | sidecar proof bytes | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `d64_two_head_seq64` | `64` | `4,416` | `8,192` | `264,403` | `42,567` | `306,970` | `272,636` | `0.888152x` |
| `d128_two_head_seq64` | `128` | `4,416` | `8,192` | `476,773` | `45,414` | `522,187` | `481,870` | `0.922792x` |

From `d64` to `d128`:

- lookup claims stay `1.000000x`
- trace rows stay `1.000000x`
- source arithmetic proof bytes grow `1.803206x`
- LogUp sidecar proof bytes grow `1.066883x`
- matched split proof bytes grow `1.701101x`
- fused proof bytes grow `1.767448x`
- fused savings grow `1.174259x`

Human read: width pressure is real and expensive, but the matched split frontier
also pays that width pressure. The result keeps the fused-vs-split saving
positive at a larger d128 sequence point.

## Matrix Impact

The controlled route matrix now has:

- `26` matched route rows
- `33,100` total lookup claims
- `57,920` total trace rows
- `4,871,057` matched split proof bytes
- `4,234,408` fused proof bytes
- `636,649` aggregate fused proof-byte savings

The fuller crossing grid is now `26 / 100` proved and `74 / 100` missing.

The wide-grid selector now promotes `d128_h4_seq32` as the next main target.
If that route is too heavy or loses the matched fused-vs-split saving, the
fallback is `d128_h1_seq16` to separate d128 width pressure from head pressure.

## Correctness Discipline

The d128 two-head seq64 route keeps the local-only validation discipline:

- source, sidecar, and fused proof envelopes verify with the native Stwo CLI
- source input invariant tests reject stale width, head, sequence, and
  commitment drift
- sidecar gate rejects `28 / 28` mutation cases
- fused gate rejects `30 / 30` mutation cases
- route matrix rejects `62 / 62` drift and overclaim mutations
- fuller grid rejects `18 / 18` drift and overclaim mutations
- scaling claim pack rejects `24 / 24` drift and overclaim mutations
- wide-grid selector rejects `26 / 26` drift and overclaim mutations
- evidence is bound by source commitments, proof-envelope commitments, table
  multiplicities, verifier domains, statement versions, source digests, and
  non-claim text

## Non-Claims

This is not exact real-valued Softmax. It is not full transformer inference or
full autoregressive inference. It is not a full transformer block. It is not
recursion, PCD, production zkML readiness, private-witness privacy, on-chain
verification, timing evidence, or a NANOZK comparison.

The `d128` source row is deterministically extended from checked bounded
fixtures. It is not a model-faithful d128 two-head transformer trace.

## Issue #715 Remaining Gates

This PR is one checked row inside issue #715, not completion of the full issue.
The following issue-level gates remain open:

- `d128_h4_seq32` head-axis decision gate.
- `d128_h1_seq16` fallback width anchor if the four-head row is too heavy.
- `d256` attention rows: not produced here.
- typed and binary/raw proof-size accounting for the widened attention rows.
- external same-surface baseline: no EZKL, zkVM, NANOZK, Jolt, or DeepProve row
  is included here.
- a paper-facing slope table after the d128 head-axis gate lands or fails.

## Reproduction

```bash
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_native_d128_two_head_seq64_bounded_softmax_table_proof_input
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d128_two_head_seq64_air_private_softmax_table_lookup_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d128_two_head_seq64_fused_softmax_table_native_gate
cargo +nightly-2025-07-14 test --locked attention_kv_native_d128_two_head_seq64 --lib --features stwo-backend
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_two_head_seq64_bounded_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-two-head-seq64-bounded-softmax-table-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_two_head_seq64_softmax_table_lookup_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-two-head-seq64-softmax-table-logup-sidecar-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_two_head_seq64_fused_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-two-head-seq64-fused-softmax-table-proof-2026-05.envelope.json
python3.10 scripts/zkai_attention_kv_fused_softmax_table_route_matrix_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.tsv
python3.10 scripts/zkai_attention_kv_fuller_crossing_grid_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.tsv
python3.10 scripts/zkai_proof_pressure_scaling_claim_pack_gate.py --write-json docs/engineering/evidence/zkai-proof-pressure-scaling-claim-pack-2026-05.json --write-tsv docs/engineering/evidence/zkai-proof-pressure-scaling-claim-pack-2026-05.tsv
python3.10 scripts/zkai_proof_pressure_wide_grid_selector_gate.py --write-json docs/engineering/evidence/zkai-proof-pressure-wide-grid-selector-2026-05.json --write-tsv docs/engineering/evidence/zkai-proof-pressure-wide-grid-selector-2026-05.tsv
git diff --check
cargo +nightly-2025-07-14 fmt --all --check
cargo +nightly-2025-07-14 check --locked --features stwo-backend --bins
just gate-fast
just gate
```
