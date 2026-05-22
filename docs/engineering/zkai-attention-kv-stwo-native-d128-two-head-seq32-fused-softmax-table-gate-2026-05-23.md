# d128 Two-Head Seq32 Fused Softmax-Table Gate

Date: 2026-05-23

Issue: #715

## Result

This slice extends the checked two-head `seq32` fused Softmax-table route from
`d64` to `d128`. It is the first source-backed `d128` attention row in the
proof-pressure grid.

The local native Stwo route verifies one fused proof object for bounded
attention arithmetic plus LogUp Softmax-table membership:

- source arithmetic proof: `443,266` JSON proof bytes
- LogUp sidecar proof: `35,010` JSON proof bytes
- matched split frontier: `478,276` JSON proof bytes
- fused proof: `445,888` JSON proof bytes
- fused saving: `32,388` JSON proof bytes
- fused ratio: `0.932282x`
- lookup claims: `1,184`
- trace rows: `2,048`

The fused proof is `2,622` bytes larger than the source arithmetic proof alone,
so this is not a source-only compression result. The honest comparator is the
matched source-plus-sidecar frontier. Against that comparator, one fused proof
replaces the source arithmetic proof plus LogUp sidecar and saves `32,388`
proof bytes.

## d64 To d128 Width Read

Holding two heads and `seq32` fixed:

| profile | width | lookup claims | trace rows | source proof bytes | sidecar proof bytes | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `d32_two_head_seq32` | `32` | `1,184` | `2,048` | `145,497` | `30,976` | `176,473` | `150,147` | `0.850821x` |
| `d64_two_head_seq32` | `64` | `1,184` | `2,048` | `248,702` | `36,400` | `285,102` | `253,257` | `0.888303x` |
| `d128_two_head_seq32` | `128` | `1,184` | `2,048` | `443,266` | `35,010` | `478,276` | `445,888` | `0.932282x` |

From `d64` to `d128`:

- lookup claims stay `1.000000x`
- trace rows stay `1.000000x`
- source arithmetic proof bytes grow `1.782318x`
- LogUp sidecar proof bytes move to `0.961813x`
- matched split proof bytes grow `1.677561x`
- fused proof bytes grow `1.760615x`
- fused savings grow `1.017051x`

This is a GO for the issue #715 d128 width-frontier gate, but it is not a
victory lap. The result says the fused boundary still beats the matched split
frontier at `d128`, while also showing that width pressure is real. The next
decision gate is whether the positive d128 row survives sequence pressure at
`d128_h2_seq64`.

## Matrix Impact

The controlled route matrix now has:

- `25` matched route rows
- `28,684` total lookup claims
- `49,728` total trace rows
- `4,348,870` matched split proof bytes
- `3,752,538` fused proof bytes
- `596,332` aggregate fused proof-byte savings

The fuller crossing grid is now `25 / 100` proved and `75 / 100` missing.

The wide-grid selector now promotes `d128_h2_seq64` as the next main target.
If that route is too heavy or loses the matched fused-vs-split saving, the
fallback is `d128_h1_seq16` to separate d128 width pressure from sequence
pressure.

## Correctness Discipline

The d128 two-head seq32 route keeps the local-only validation discipline:

- source, sidecar, and fused proof envelopes verify with the native Stwo CLI
- source input invariant tests reject stale width, head, sequence, and
  commitment drift
- sidecar gate rejects `28 / 28` mutation cases
- fused gate rejects `30 / 30` mutation cases
- route matrix rejects drift and overclaim mutations
- fuller grid rejects drift and overclaim mutations
- scaling claim pack rejects drift and overclaim mutations
- wide-grid selector rejects drift and overclaim mutations
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

- `d128_h2_seq64` sequence-pressure decision gate.
- `d128_h1_seq16` fallback width anchor if seq64 is too heavy.
- `d256` attention rows: not produced here.
- typed and binary/raw proof-size accounting for the widened attention rows.
- external same-surface baseline: no EZKL, zkVM, NANOZK, Jolt, or DeepProve row
  is included here.
- a paper-facing slope table after the d128 sequence gate lands or fails.

## Reproduction

```bash
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_native_d128_two_head_seq32_bounded_softmax_table_proof_input
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d128_two_head_seq32_air_private_softmax_table_lookup_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d128_two_head_seq32_fused_softmax_table_native_gate
cargo +nightly-2025-07-14 test --locked attention_kv_native_d128_two_head_seq32 --lib --features stwo-backend
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_two_head_seq32_bounded_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-two-head-seq32-bounded-softmax-table-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_two_head_seq32_softmax_table_lookup_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-two-head-seq32-softmax-table-logup-sidecar-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d128_two_head_seq32_fused_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json
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
