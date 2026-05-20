# zkAI Attention/KV d32 Two-Head Fused Softmax-Table Gate - 2026-05-20

## Question

Does the native Stwo fused Softmax-table route still save proof bytes when the
fixture crosses both width and head count at the shortest checked sequence
length?

This slice checks `d32`, two heads, and `seq8`. It is still the bounded integer
Softmax-table/floor-division fixture, not exact real-valued Softmax and not full
inference.

## Decision

`GO_NATIVE_STWO_FUSED_ATTENTION_ARITHMETIC_AND_SOFTMAX_TABLE_LOGUP_MEMBERSHIP`

The route validates as one native fused proof object with a matched
source-plus-LogUp-sidecar comparator.

## Result

| Metric | Value |
|---|---:|
| key/value width | `32` |
| heads | `2` |
| steps per head | `8` |
| lookup claims | `104` |
| trace rows | `128` |
| source proof bytes | `123,926` |
| sidecar proof bytes | `18,137` |
| source+sidecar proof bytes | `142,063` |
| fused proof bytes | `125,756` |
| fused saving | `16,307` bytes |
| fused ratio | `0.885213x` |
| fused overhead over source | `1,830` bytes |

The useful signal is the overhead number: the standalone LogUp sidecar is
`18,137` proof bytes, but fusing the lookup relation into the source proof adds
only `1,830` bytes over the source proof. That is the shared-plumbing behavior
the route matrix is trying to scale.

## Evidence

- Source input:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-two-head-bounded-softmax-table-proof-2026-05.json`
- Source proof envelope:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-two-head-bounded-softmax-table-proof-2026-05.envelope.json`
- Sidecar proof envelope:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-two-head-softmax-table-logup-sidecar-proof-2026-05.envelope.json`
- Fused proof envelope:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-two-head-fused-softmax-table-proof-2026-05.envelope.json`
- Fused gate JSON:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-two-head-fused-softmax-table-gate-2026-05.json`

The gate rejects `30 / 30` fused-envelope, source-binding, metric, proof-byte,
and overclaim mutations. The source and sidecar gates add their own mutation
checks before this fused route is admitted into the route matrix.

## Claim Boundary

This may be cited as:

> The `d32` two-head `seq8` fused Softmax-table route validates with a matched
> source-plus-sidecar comparator and saves `16,307` proof bytes
> (`0.885213x`), extending the width/head crossing grid.

Do not cite it as:

- exact real-valued Softmax;
- full transformer inference;
- a timing benchmark;
- a NANOZK comparison;
- recursion or PCD;
- production-ready zkML.

## Validation

```bash
python3.10 -m unittest \
  scripts.tests.test_zkai_attention_kv_d32_two_head_bounded_softmax_table_native_gate \
  scripts.tests.test_zkai_attention_kv_d32_two_head_air_private_softmax_table_lookup_gate \
  scripts.tests.test_zkai_attention_kv_d32_two_head_fused_softmax_table_native_gate

cargo +nightly-2025-07-14 test --locked \
  attention_kv_d32_two_head_fused_softmax_table \
  --lib --features stwo-backend

cargo +nightly-2025-07-14 run --locked --features stwo-backend \
  --bin zkai_attention_kv_native_d32_two_head_fused_softmax_table_proof -- \
  verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-two-head-fused-softmax-table-proof-2026-05.envelope.json
```
