# d64 Four-Head Seq64 Fused Softmax-Table Gate

Date: 2026-05-22

Issue: #715

## Result

This slice extends the checked `d64_four_head_seq16` and
`d64_four_head_seq32` fused Softmax-table routes to `seq64`.

The local native Stwo route verifies one fused proof object for bounded
attention arithmetic plus LogUp Softmax-table membership:

- source arithmetic proof: `272,638` JSON proof bytes
- LogUp sidecar proof: `43,147` JSON proof bytes
- matched split frontier: `315,785` JSON proof bytes
- fused proof: `276,503` JSON proof bytes
- fused saving: `39,282` JSON proof bytes
- fused ratio: `0.875605x`
- lookup claims: `8,832`
- trace rows: `16,384`

The fused proof is `3,865` bytes larger than the source arithmetic proof alone,
so this is not a source-only compression result. The honest comparator is the
matched source-plus-sidecar frontier. Against that comparator, one fused proof
replaces the source arithmetic proof plus LogUp sidecar and saves `39,282`
proof bytes.

## d64 Four-Head Sequence Read

Holding `d64` and four heads fixed:

| profile | steps per head | lookup claims | trace rows | source proof bytes | sidecar proof bytes | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `d64_four_head_seq16` | `16` | `672` | `1,024` | `232,991` | `27,694` | `260,685` | `237,596` | `0.911430x` |
| `d64_four_head_seq32` | `32` | `2,368` | `4,096` | `254,145` | `34,147` | `288,292` | `255,889` | `0.887604x` |
| `d64_four_head_seq64` | `64` | `8,832` | `16,384` | `272,638` | `43,147` | `315,785` | `276,503` | `0.875605x` |

From `seq32` to `seq64`:

- lookup claims grow `3.729730x`
- trace rows grow `4.000000x`
- source arithmetic proof bytes grow `1.072766x`
- LogUp sidecar proof bytes grow `1.263566x`
- matched split proof bytes grow `1.095365x`
- fused proof bytes grow `1.080558x`
- fused savings grow `1.212295x`

This is a GO for the issue #715 `d64_h4_seq64` decision gate. The work being
checked grows much faster than the fused proof object, and the fused proof beats
the matched split frontier more strongly than the `seq32` row. This supports the
amortization thesis under a harder sequence stress row. It does not prove a full
transformer block or establish a NANOZK comparison.

## Matrix Impact

The controlled route matrix now has:

- `22` matched route rows
- `22,916` total lookup claims
- `39,232` total trace rows
- `3,309,249` matched split proof bytes
- `2,796,289` fused proof bytes
- `512,960` aggregate fused proof-byte savings

The fuller crossing grid is now `22 / 80` proved and `58 / 80` missing.

The wide-grid selector no longer treats `d64_h4_seq64` as future work. The next
local selector target is `d64_h2_seq64`, which separates sequence pressure from
the now-passing four-head sequence crossing.

## Correctness Discipline

The d64 four-head seq64 route keeps the local-only validation discipline:

- source, sidecar, and fused proof envelopes verify with the native Stwo CLI
- source input invariant tests reject stale width/head/sequence drift
- sidecar gate rejects `28 / 28` mutation cases
- fused gate rejects `30 / 30` mutation cases
- route matrix rejects `55 / 55` drift and overclaim mutations
- fuller grid rejects `18 / 18` drift and overclaim mutations
- scaling claim pack rejects `19 / 19` drift and overclaim mutations
- wide-grid selector rejects `19 / 19` drift and overclaim mutations
- evidence is bound by source commitments, proof-envelope commitments, table
  multiplicities, verifier domains, statement versions, source digests, and
  non-claim text

## Non-Claims

This is not exact real-valued Softmax. It is not full transformer inference or
full autoregressive inference. It is not a full transformer block. It is not
recursion, PCD, production zkML readiness, private-witness privacy, on-chain
verification, timing evidence, or a NANOZK comparison.

The `d64` source row is deterministically extended from checked bounded fixtures.
It is not a model-faithful d64 four-head transformer trace.

## Issue #715 Remaining Gates

This PR is one checked row inside issue #715, not completion of the full issue.
The following issue-level gates remain open:

- `d64_two_head_seq64` to isolate sequence pressure without the four-head
  crossing.
- `d64_single_head` rows to separate width pressure from head pressure.
- `d128` and `d256` attention rows: not produced here.
- typed and binary/raw proof-size accounting for the widened attention rows.
- external same-surface baseline: no EZKL, zkVM, NANOZK, Jolt, or DeepProve row
  is included here.

## Reproduction

```bash
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_native_d64_four_head_seq64_bounded_softmax_table_proof_input
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d64_four_head_seq64_air_private_softmax_table_lookup_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d64_four_head_seq64_fused_softmax_table_native_gate
cargo +nightly-2025-07-14 test --locked attention_kv_native_d64_four_head_seq64 --lib --features stwo-backend
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_bounded_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_softmax_table_lookup_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-softmax-table-logup-sidecar-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-fused-softmax-table-proof-2026-05.envelope.json
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
