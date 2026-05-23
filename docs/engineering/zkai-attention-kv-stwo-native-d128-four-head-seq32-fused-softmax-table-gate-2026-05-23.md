# d128 Four-Head Seq32 Fused Softmax-Table Gate

Date: 2026-05-23

Issue: #715

## Result

This slice extends the checked d128 attention route from two heads to four
heads at `seq32`. It is the first source-backed d128 head-axis row in the
proof-pressure grid.

The local native Stwo route verifies one fused proof object for bounded
attention arithmetic plus LogUp Softmax-table membership:

- source arithmetic proof: `463,410` proof bytes
- LogUp sidecar proof: `41,524` proof bytes
- matched split frontier: `504,934` proof bytes
- fused proof: `465,630` proof bytes
- fused saving: `39,304` proof bytes
- fused ratio: `0.922160x`
- lookup claims: `2,368`
- trace rows: `4,096`

The fused proof is `2,220` bytes larger than the source arithmetic proof alone,
so this is not a source-only compression result. The honest comparator is the
matched source-plus-sidecar frontier. Against that comparator, one fused proof
replaces the source arithmetic proof plus LogUp sidecar and saves `39,304`
proof bytes.

## d128 Seq32 Head-Axis Read

Holding `d128` and `seq32` fixed:

| profile | heads | lookup claims | trace rows | source proof bytes | sidecar proof bytes | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `d128_two_head_seq32` | `2` | `1,184` | `2,048` | `443,266` | `35,010` | `478,276` | `445,888` | `0.932282x` |
| `d128_four_head_seq32` | `4` | `2,368` | `4,096` | `463,410` | `41,524` | `504,934` | `465,630` | `0.922160x` |

From two heads to four heads:

- lookup claims grow `2.000000x`
- trace rows grow `2.000000x`
- source arithmetic proof bytes grow `1.045444x`
- LogUp sidecar proof bytes grow `1.186061x`
- matched split proof bytes grow `1.055738x`
- fused proof bytes grow `1.044276x`
- fused savings grow `1.213536x`

This is a GO for the issue #715 d128 head-axis gate. The work being checked
doubles, the fused proof still beats the matched split frontier, and fused
proof bytes grow only slightly. The result does not complete d128. The next
question is whether this positive four-head d128 row survives the sequence jump
to `d128_h4_seq64`.

## Matrix Impact

The controlled route matrix now has:

- `27` matched route rows
- `35,468` total lookup claims
- `62,016` total trace rows
- `5,375,991` matched split proof bytes
- `4,700,038` fused proof bytes
- `675,953` aggregate fused proof-byte savings

The fuller crossing grid is now `27 / 100` proved and `73 / 100` missing.

The wide-grid selector now promotes `d128_h4_seq64` as the next main target. If
that route is too heavy or loses the matched fused-vs-split saving, the fallback
is `d128_h1_seq16` to separate d128 width pressure from head and sequence
pressure.

## Correctness Discipline

The d128 four-head seq32 route keeps the local-only validation discipline:

- source, sidecar, and fused proof envelopes verify with the native Stwo CLI
- source input invariant tests reject stale width, head, sequence, and
  commitment drift
- sidecar gate rejects `28 / 28` mutation cases
- fused gate rejects `30 / 30` mutation cases
- route matrix rejects `64 / 64` drift and overclaim mutations
- fuller grid rejects `18 / 18` drift and overclaim mutations
- scaling claim pack rejects `25 / 25` drift and overclaim mutations
- wide-grid selector rejects `27 / 27` drift and overclaim mutations
- evidence is bound by source commitments, proof-envelope commitments, table
  multiplicities, verifier domains, statement versions, source digests, and
  non-claim text

## Non-Claims

This is not exact real-valued Softmax. It is not full transformer inference or
full autoregressive inference. It is not a full transformer block. It is not
recursion, PCD, production zkML readiness, private-witness privacy, on-chain
verification, timing evidence, or a NANOZK comparison.

The d128 source row is deterministically extended from checked bounded
fixtures. It is not a model-faithful d128 four-head transformer trace.

## Issue #715 Remaining Gates

This PR is one checked row inside issue #715, not completion of the full issue.
The following issue-level gates remain open:

- `d128_h4_seq64` sequence jump after the positive d128 four-head seq32 row.
- `d128_h1_seq16` fallback width anchor if the four-head seq64 row is too
  heavy.
- `d256` attention rows: not produced here.
- typed and binary/raw proof-size accounting for the widened attention rows.
- external same-surface baseline: no EZKL, zkVM, NANOZK, Jolt, or DeepProve row
  is included here.
- a paper-facing slope table after the d128 four-head seq64 gate lands or
  fails.

## Reproduction

```bash
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_native_d128_four_head_seq32_bounded_softmax_table_proof_input
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d128_four_head_seq32_air_private_softmax_table_lookup_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d128_four_head_seq32_fused_softmax_table_native_gate
cargo +nightly-2025-07-14 test --locked attention_kv_native_d128_four_head_seq32 --lib --features stwo-backend
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_four_head_seq32_bounded_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq32-bounded-softmax-table-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_four_head_seq32_softmax_table_lookup_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq32-softmax-table-logup-sidecar-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_four_head_seq32_fused_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-four-head-seq32-fused-softmax-table-proof-2026-05.envelope.json
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
