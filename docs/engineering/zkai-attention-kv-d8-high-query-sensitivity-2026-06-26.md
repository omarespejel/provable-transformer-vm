# d8 High-Query Sensitivity

- Issue: `#765`
- Decision: `GO_SMALL_SURFACE_HIGH_QUERY_SENSITIVITY_QUERY_COUNT_ONLY`
- Surface: `d8_single_head_seq8_bounded_softmax_table_attention`
- Backend: `unmodified_stwo_2_2_0_with_explicit_query_count_patch`

## Result

This is a small higher-query sensitivity slice, not a new headline row. It reruns the d8 single-head seq8 bounded Softmax-table attention surface with higher FRI query counts and the same split-versus-fused comparator.

| FRI queries | split proof bytes | fused proof bytes | saving | fused/split | fused growth vs q3 | split growth vs q3 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 59437 | 47698 | 11739 | 0.802497 | 1.000000 | 1.000000 |
| 6 | 82115 | 62889 | 19226 | 0.765865 | 1.318483 | 1.381547 |
| 12 | 111430 | 85900 | 25530 | 0.770888 | 1.800914 | 1.874758 |

## Interpretation

On this small d8 surface, q6 and q12 preserve the fused proof-size win. The absolute saving grows from 11739 bytes at q3 to 19226 at q6 and 25530 at q12. Both higher-query rows now require only an explicit FRI-query-count patch; the publication profile remains the default q3 configuration.

The q12 run is useful but should stay engineering-scoped: it is a small d8 sensitivity rerun under an explicit query-count patch, not a headline d64/d128 row or a production-security profile.

## Reproduction

Use a throwaway worktree. Do not change the publication branch's default `publication_v1_pcs_config`.

For q6, patch:

```text
src/stwo_backend/mod.rs:
FriConfig::new(0, 1, 3, 1) -> FriConfig::new(0, 1, 6, 1)
```

For q12, patch:

```text
src/stwo_backend/mod.rs:
FriConfig::new(0, 1, 3, 1) -> FriConfig::new(0, 1, 12, 1)
```

After applying the q6 patch, run:

```bash
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d8_bounded_softmax_table_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d8-q6-source-proof-2026-06.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d8_bounded_softmax_table_proof -- verify docs/engineering/evidence/high-query/zkai-attention-kv-d8-q6-source-proof-2026-06.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d8_softmax_table_lookup_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d8-q6-sidecar-proof-2026-06.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d8_softmax_table_lookup_proof -- verify docs/engineering/evidence/high-query/zkai-attention-kv-d8-q6-sidecar-proof-2026-06.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d8_fused_softmax_table_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d8-q6-fused-proof-2026-06.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d8_fused_softmax_table_proof -- verify docs/engineering/evidence/high-query/zkai-attention-kv-d8-q6-fused-proof-2026-06.envelope.json
```

After applying the q12 patch, run:

```bash
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d8_bounded_softmax_table_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d8-q12-source-proof-2026-06.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d8_bounded_softmax_table_proof -- verify docs/engineering/evidence/high-query/zkai-attention-kv-d8-q12-source-proof-2026-06.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d8_softmax_table_lookup_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d8-q12-sidecar-proof-2026-06.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d8_softmax_table_lookup_proof -- verify docs/engineering/evidence/high-query/zkai-attention-kv-d8-q12-sidecar-proof-2026-06.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d8_fused_softmax_table_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d8-q12-fused-proof-2026-06.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d8_fused_softmax_table_proof -- verify docs/engineering/evidence/high-query/zkai-attention-kv-d8-q12-fused-proof-2026-06.envelope.json
```

The checked envelopes are stored under `docs/engineering/evidence/high-query/` and this gate parses their proof configs, byte sizes, and hashes.

## Non-Claims

- not a headline d64 or d128 high-query rerun
- not production-security parameter evidence
- not a proving-time or verifier-time claim
- not exact real-valued Softmax
- not full transformer inference
- not a comparison with external zkML systems
- not evidence that higher query count always improves fused-to-split ratio
- not a permanent Stwo-AI backend change
