# d64 Two-Head Seq64 Fused Softmax-Table Gate

Date: 2026-05-22

Issue: #715

## Result

This slice extends the checked `d64_two_head_seq16` and
`d64_two_head_seq32` fused Softmax-table routes to `seq64`.

The local native Stwo route verifies one fused proof object for bounded
attention arithmetic plus LogUp Softmax-table membership:

- source arithmetic proof: `264,403` JSON proof bytes
- LogUp sidecar proof: `42,567` JSON proof bytes
- matched split frontier: `306,970` JSON proof bytes
- fused proof: `272,636` JSON proof bytes
- fused saving: `34,334` JSON proof bytes
- fused ratio: `0.888152x`
- lookup claims: `4,416`
- trace rows: `8,192`

The fused proof is `8,233` bytes larger than the source arithmetic proof alone,
so this is not a source-only compression result. The honest comparator is the
matched source-plus-sidecar frontier. Against that comparator, one fused proof
replaces the source arithmetic proof plus LogUp sidecar and saves `34,334`
proof bytes.

## d64 Two-Head Sequence Read

Holding `d64` and two heads fixed:

| profile | steps per head | lookup claims | trace rows | source proof bytes | sidecar proof bytes | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `d64_two_head_seq16` | `16` | `336` | `512` | `230,688` | `27,106` | `257,794` | `238,504` | `0.925172x` |
| `d64_two_head_seq32` | `32` | `1,184` | `2,048` | `248,702` | `36,400` | `285,102` | `253,257` | `0.888304x` |
| `d64_two_head_seq64` | `64` | `4,416` | `8,192` | `264,403` | `42,567` | `306,970` | `272,636` | `0.888152x` |

From `seq32` to `seq64`:

- lookup claims grow `3.729730x`
- trace rows grow `4.000000x`
- source arithmetic proof bytes grow `1.063132x`
- LogUp sidecar proof bytes grow `1.169423x`
- matched split proof bytes grow `1.076702x`
- fused proof bytes grow `1.076519x`
- fused savings grow `1.078160x`

This is a GO for the issue #715 `d64_h2_seq64` decision gate. The work being
checked grows much faster than the fused proof object, and the fused proof
still beats the matched split frontier. The result is slightly different from
the four-head seq64 row: the saving remains positive, but the saving growth is
closer to flat. That is useful because it narrows the next question to width
pressure rather than sequence pressure alone.

## Matrix Impact

The controlled route matrix now has:

- `23` matched route rows
- `27,332` total lookup claims
- `47,424` total trace rows
- `3,616,219` matched split proof bytes
- `3,068,925` fused proof bytes
- `547,294` aggregate fused proof-byte savings

The fuller crossing grid is now `23 / 80` proved and `57 / 80` missing.

The wide-grid selector no longer treats `d64_h2_seq64` as future work. The next
local selector target is `d64_h1_seq16`, which pins the d64 single-head width
slope before moving to the larger `d128_h2_seq32` target.

## Correctness Discipline

The d64 two-head seq64 route keeps the local-only validation discipline:

- source, sidecar, and fused proof envelopes verify with the native Stwo CLI
- source input invariant tests reject stale width/head/sequence drift
- sidecar gate rejects `28 / 28` mutation cases
- fused gate rejects `30 / 30` mutation cases
- route matrix rejects `56 / 56` drift and overclaim mutations
- fuller grid rejects `18 / 18` drift and overclaim mutations
- scaling claim pack rejects `19 / 19` drift and overclaim mutations
- wide-grid selector rejects `20 / 20` drift and overclaim mutations
- evidence is bound by source commitments, proof-envelope commitments, table
  multiplicities, verifier domains, statement versions, source digests, and
  non-claim text

## Non-Claims

This is not exact real-valued Softmax. It is not full transformer inference or
full autoregressive inference. It is not a full transformer block. It is not
recursion, PCD, production zkML readiness, private-witness privacy, on-chain
verification, timing evidence, or a NANOZK comparison.

The `d64` source row is deterministically extended from checked bounded
fixtures. It is not a model-faithful d64 two-head transformer trace.

## Issue #715 Remaining Gates

This PR is one checked row inside issue #715, not completion of the full issue.
The following issue-level gates remain open:

- `d64_single_head` rows to separate width pressure from head pressure.
- `d128` and `d256` attention rows: not produced here.
- typed and binary/raw proof-size accounting for the widened attention rows.
- external same-surface baseline: no EZKL, zkVM, NANOZK, Jolt, or DeepProve row
  is included here.
- a paper-facing slope table after the next width anchor lands.

## Reproduction

```bash
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_native_d64_two_head_seq64_bounded_softmax_table_proof_input
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d64_two_head_seq64_air_private_softmax_table_lookup_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d64_two_head_seq64_fused_softmax_table_native_gate
cargo +nightly-2025-07-14 test --locked attention_kv_native_d64_two_head_seq64 --lib --features stwo-backend
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_two_head_seq64_bounded_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-seq64-bounded-softmax-table-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_two_head_seq64_softmax_table_lookup_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-seq64-softmax-table-logup-sidecar-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_two_head_seq64_fused_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-seq64-fused-softmax-table-proof-2026-05.envelope.json
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
