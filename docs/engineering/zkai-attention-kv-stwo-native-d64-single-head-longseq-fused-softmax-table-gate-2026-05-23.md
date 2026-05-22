# d64 Single-Head Seq16 Fused Softmax-Table Gate

Date: 2026-05-23

Issue: #715

## Result

This slice adds the missing `d64_single_head_seq16` anchor row before the next
width-frontier attempt. It gives the d64 head-axis comparison a real one-head
base instead of only comparing two heads to four heads.

The local native Stwo route verifies one fused proof object for bounded
attention arithmetic plus LogUp Softmax-table membership:

- source arithmetic proof: `231,415` JSON proof bytes
- LogUp sidecar proof: `22,960` JSON proof bytes
- matched split frontier: `254,375` JSON proof bytes
- fused proof: `237,725` JSON proof bytes
- fused saving: `16,650` JSON proof bytes
- fused ratio: `0.934545x`
- lookup claims: `168`
- trace rows: `256`

The fused proof is `6,310` bytes larger than the source arithmetic proof alone,
so this is not a source-only compression result. The honest comparator is the
matched source-plus-sidecar frontier. Against that comparator, one fused proof
replaces the source arithmetic proof plus LogUp sidecar and saves `16,650`
proof bytes.

## d64 Seq16 Head-Axis Read

Holding `d64` and `seq16` fixed:

| profile | heads | lookup claims | trace rows | source proof bytes | sidecar proof bytes | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `d64_single_head_seq16` | `1` | `168` | `256` | `231,415` | `22,960` | `254,375` | `237,725` | `0.934545x` |
| `d64_two_head_seq16` | `2` | `336` | `512` | `230,688` | `27,037` | `257,725` | `238,504` | `0.925421x` |
| `d64_four_head_seq16` | `4` | `672` | `1,024` | `232,991` | `27,694` | `260,685` | `237,596` | `0.911430x` |

From one head to four heads:

- lookup claims grow `4.000000x`
- trace rows grow `4.000000x`
- source arithmetic proof bytes grow `1.006810x`
- LogUp sidecar proof bytes grow `1.206185x`
- matched split proof bytes grow `1.024806x`
- fused proof bytes move to `0.999457x`
- fused savings grow `1.386727x`

This is a GO for the issue #715 d64 single-head anchor. The work being checked
quadruples from one head to four heads, while fused proof bytes stay basically
flat and the fused-vs-split saving remains positive. That does not prove the
wide-grid thesis by itself. It makes the next `d128_h2_seq32` target more
justified because the d64 head-axis slope is now pinned from one head, not only
from two heads.

## Matrix Impact

The controlled route matrix now has:

- `24` matched route rows
- `27,500` total lookup claims
- `47,680` total trace rows
- `3,870,594` matched split proof bytes
- `3,306,650` fused proof bytes
- `563,944` aggregate fused proof-byte savings

The fuller crossing grid is now `24 / 80` proved and `56 / 80` missing.

The wide-grid selector now promotes `d128_h2_seq32` as the next main target.
If that engineering path is too heavy, the fallback is `d64_h1_seq32` to extend
the single-head sequence slope.

## Correctness Discipline

The d64 single-head seq16 route keeps the local-only validation discipline:

- source, sidecar, and fused proof envelopes verify with the native Stwo CLI
- source input invariant tests reject stale width, sequence, and commitment drift
- sidecar gate rejects `19 / 19` mutation cases
- fused gate rejects `26 / 26` mutation cases
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

The `d64` source row is deterministically extended from checked bounded
fixtures. It is not a model-faithful d64 single-head transformer trace.

## Issue #715 Remaining Gates

This PR is one checked row inside issue #715, not completion of the full issue.
The following issue-level gates remain open:

- `d128_h2_seq32` width frontier.
- `d64_h1_seq32` fallback if the d128 row is too heavy.
- `d256` attention rows: not produced here.
- typed and binary/raw proof-size accounting for the widened attention rows.
- external same-surface baseline: no EZKL, zkVM, NANOZK, Jolt, or DeepProve row
  is included here.
- a paper-facing slope table after the d128 decision gate lands.

## Reproduction

```bash
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_native_d64_single_head_longseq_bounded_softmax_table_proof_input
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d64_single_head_longseq_air_private_softmax_table_lookup_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d64_single_head_longseq_fused_softmax_table_native_gate
cargo +nightly-2025-07-14 test --locked attention_kv_native_d64_single_head_longseq --lib --features stwo-backend
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_single_head_longseq_bounded_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-single-head-longseq-bounded-softmax-table-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_single_head_longseq_softmax_table_lookup_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-single-head-longseq-softmax-table-logup-sidecar-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_single_head_longseq_fused_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-single-head-longseq-fused-softmax-table-proof-2026-05.envelope.json
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
