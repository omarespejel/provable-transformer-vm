# ZKAI d256 Two-Head Seq32 Fused Softmax-Table Gate

Issue: #715

## Decision

`GO_NATIVE_STWO_FUSED_ATTENTION_ARITHMETIC_AND_SOFTMAX_TABLE_LOGUP_MEMBERSHIP`

The d256 two-head seq32 width-stress row validates locally with source,
sidecar, fused, mutation, route-matrix, and timing artifacts.

## Result

| metric | value |
|---|---:|
| source proof bytes | `816,627` |
| LogUp sidecar proof bytes | `34,914` |
| matched split frontier | `851,541` |
| fused proof bytes | `821,398` |
| fused saving | `30,143` |
| fused ratio | `0.964602x` |
| lookup claims | `1,184` |
| trace rows | `2,048` |

The d128 to d256 two-head seq32 width signal is:

| growth | value |
|---|---:|
| key width | `2.000000x` |
| lookup claims | `1.000000x` |
| trace rows | `1.000000x` |
| fused proof bytes | `1.842162x` |
| split proof bytes | `1.780438x` |
| saving | `0.930684x` |

Median-of-5 local release timing is a caveat, not a win:

| timing | value |
|---|---:|
| split prove median | `1,943,179 us` |
| fused prove median | `2,226,893 us` |
| fused prove ratio | `1.146005x` |
| split verify median | `1,213,256 us` |
| fused verify median | `1,384,798 us` |
| fused verify ratio | `1.141390x` |

## Interpretation

The row keeps the proof-size saving alive at d256, but it weakens the ratio and
does not improve proving speed. This supports the paper claim about proof
boundary selection and proof-size amortization, not a speed claim.

The next gate is `d256_h2_seq64`, unless timing or implementation cost pushes
the research toward typed composition instead of monolithic fusion.

## Evidence

- Source input:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-d256-two-head-seq32-bounded-softmax-table-proof-2026-05.json`
- Source proof envelope:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-d256-two-head-seq32-bounded-softmax-table-proof-2026-05.envelope.json`
- Sidecar proof envelope:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-d256-two-head-seq32-softmax-table-logup-sidecar-proof-2026-05.envelope.json`
- Fused proof envelope:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-d256-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json`
- Source gate:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-d256-two-head-seq32-bounded-softmax-table-proof-2026-05.tsv`
- Sidecar gate:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-d256-two-head-seq32-softmax-table-logup-sidecar-gate-2026-05.tsv`
- Fused gate:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-d256-two-head-seq32-fused-softmax-table-gate-2026-05.tsv`
- Median timing:
  `docs/engineering/evidence/zkai-attention-kv-d256-two-head-seq32-median-timing-raw-2026-05.json`

## Validation

```bash
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_native_d256_two_head_seq32_bounded_softmax_table_proof_input
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d256_two_head_seq32_air_private_softmax_table_lookup_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d256_two_head_seq32_fused_softmax_table_native_gate
cargo +nightly-2025-07-14 test --locked attention_kv_native_d256_two_head_seq32_bounded_softmax_table_proof --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked attention_kv_d256_two_head_seq32_softmax_table_lookup --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked attention_kv_d256_two_head_seq32_fused_softmax_table --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked --release --features stwo-backend --bin zkai_attention_kv_d256_two_head_seq32_median_timing
```

## Non-Claims

- Not a full transformer block proof.
- Not a public proving-speed benchmark.
- Not exact real-valued Softmax.
- Not a NANOZK comparison.
- Not production zkML readiness.
