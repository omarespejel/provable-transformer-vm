# d64 Four-Head Seq16 Fused Softmax-Table Gate

Date: 2026-05-22

Issue: #715

## Result

This slice extends the checked `d64` two-head `seq16` fused Softmax-table route
to four heads.

The local native Stwo route verifies one fused proof object for bounded
attention arithmetic plus LogUp Softmax-table membership:

- source arithmetic proof: `232,991` JSON proof bytes
- LogUp sidecar proof: `27,694` JSON proof bytes
- matched split frontier: `260,685` JSON proof bytes
- fused proof: `237,596` JSON proof bytes
- fused saving: `23,089` JSON proof bytes
- fused ratio: `0.911430x`
- lookup claims: `672`
- trace rows: `1,024`

The fused proof is `4,605` bytes larger than the source arithmetic proof alone,
so this is not a source-only compression result. It is a matched split-frontier
result: one fused proof replaces the source arithmetic proof plus LogUp sidecar
and saves `23,089` proof bytes against that honest comparator.

## d64 Head-Axis Read

Holding `d64` and `seq16` fixed:

| profile | heads | lookup claims | trace rows | source proof bytes | sidecar proof bytes | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `d64_two_head_seq16` | `2` | `336` | `512` | `230,688` | `27,037` | `257,725` | `238,504` | `0.925421x` |
| `d64_four_head_seq16` | `4` | `672` | `1,024` | `232,991` | `27,694` | `260,685` | `237,596` | `0.911430x` |

From two heads to four heads:

- lookup claims grow `2.000000x`
- trace rows grow `2.000000x`
- source arithmetic proof bytes grow `1.009983x`
- LogUp sidecar proof bytes grow `1.024300x`
- matched split proof bytes grow `1.011485x`
- fused proof bytes move to `0.996193x`
- fused savings grow `1.201238x`

This is the cleanest d64 head-axis signal so far: the work being checked
doubles, while the fused proof object is slightly smaller. That supports the
amortization thesis. It does not yet prove a full transformer block or
establish a NANOZK comparison.

## Matrix Impact

The controlled route matrix now has:

- `21` matched route rows
- `14,084` total lookup claims
- `22,848` total trace rows
- `2,993,464` matched split proof bytes
- `2,519,786` fused proof bytes
- `473,678` aggregate fused proof-byte savings

The fuller crossing grid is now `21 / 60` proved and `39 / 60` missing.

The wide-grid selector now treats `d64_h4_seq16` as source-backed and promotes
`d64_h4_seq64` as the next high-signal stress row.

## Correctness Discipline

The d64 four-head seq16 route keeps the local-only validation discipline:

- source, sidecar, and fused proof envelopes verify with the native Stwo CLI
- source input invariant tests reject stale width/head/sequence drift
- sidecar gate rejects `28 / 28` mutation cases
- fused gate rejects `30 / 30` mutation cases
- route matrix rejects `53 / 53` drift and overclaim mutations
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

The `d64` source row is deterministically widened from the checked `d64`
two-head `seq16` source fixture and extends the head axis. It is not a
model-faithful d64 four-head transformer trace.

## Issue #715 Remaining Gates

This PR is one checked row inside issue #715, not completion of the full issue.
The following issue-level gates remain open:

- `d64_four_head_seq64` to test whether the d64 four-head head-axis signal
  survives a longer sequence.
- `d64_two_head_seq64` to isolate the d64 sequence-axis extension.
- `d64_single_head` rows to separate width pressure from head pressure.
- `d128` and `d256` attention rows: not produced here.
- typed and binary/raw proof-size accounting for the widened attention rows.
- external same-surface baseline: no EZKL, zkVM, NANOZK, Jolt, or DeepProve row
  is included here.

## Reproduction

```bash
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_native_d64_four_head_longseq_bounded_softmax_table_proof_input
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d64_four_head_longseq_air_private_softmax_table_lookup_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d64_four_head_longseq_fused_softmax_table_native_gate
cargo +nightly-2025-07-14 test --locked attention_kv_native_d64_four_head_longseq --lib --features stwo-backend
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_fused_softmax_table_route_matrix_gate scripts.tests.test_zkai_attention_kv_fuller_crossing_grid_gate scripts.tests.test_zkai_proof_pressure_scaling_claim_pack_gate scripts.tests.test_zkai_proof_pressure_wide_grid_selector_gate
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
