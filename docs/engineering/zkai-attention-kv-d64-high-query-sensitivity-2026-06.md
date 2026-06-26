# d64 High-Query Sensitivity

- Issue: `#769`
- Decision: `GO_D64_H4_SEQ64_HIGH_QUERY_SENSITIVITY_Q6_Q12`
- Surface: `d64_four_head_seq64_bounded_softmax_table_attention`
- Backend: `unmodified_stwo_2_2_0_with_explicit_query_count_patch`

## Result

This is a larger-surface higher-query sensitivity slice, not a production-security claim. It reruns the d64 four-head seq64 bounded Softmax-table attention surface with higher FRI query counts and the same split-versus-fused comparator.

| FRI queries | split proof bytes | fused proof bytes | saving | fused/split | fused growth vs q3 | split growth vs q3 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 315785 | 276503 | 39282 | 0.875605 | 1.000000 | 1.000000 |
| 6 | 453733 | 390437 | 63296 | 0.860499 | 1.412053 | 1.436842 |
| 12 | 727747 | 612237 | 115510 | 0.841277 | 2.214215 | 2.304565 |

## Interpretation

On the d64 four-head seq64 surface, q6 and q12 preserve the fused proof-size win. The absolute saving grows from 39282 bytes at q3 to 63296 bytes at q6 and 115510 bytes at q12. The q12 fused/split ratio is 0.841277x under the same fixed PoW, blowup, fold-step, and query-count-only patch discipline. This is engineering evidence for boundary-selection robustness under higher FRI query count, not a production-security or timing claim.

The important signal is not that q12 is a production-security profile. It is that increasing FRI query count on the existing d64 four-head seq64 surface did not erase the fused proof-size win. The absolute saving grew because the split path pays duplicated source and sidecar proof plumbing.

## Reproduction

Use a throwaway worktree. Do not commit the temporary query-count patch to the publication branch.

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
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_bounded_softmax_table_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q6-source-proof-2026-06.envelope.json
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_bounded_softmax_table_proof -- verify docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q6-source-proof-2026-06.envelope.json
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_softmax_table_lookup_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q6-sidecar-proof-2026-06.envelope.json
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_softmax_table_lookup_proof -- verify docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q6-sidecar-proof-2026-06.envelope.json
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q6-fused-proof-2026-06.envelope.json
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_proof -- verify docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q6-fused-proof-2026-06.envelope.json
```

After applying the q12 patch, run:

```bash
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_bounded_softmax_table_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q12-source-proof-2026-06.envelope.json
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_bounded_softmax_table_proof -- verify docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q12-source-proof-2026-06.envelope.json
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_softmax_table_lookup_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q12-sidecar-proof-2026-06.envelope.json
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_softmax_table_lookup_proof -- verify docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q12-sidecar-proof-2026-06.envelope.json
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q12-fused-proof-2026-06.envelope.json
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_proof -- verify docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q12-fused-proof-2026-06.envelope.json
```

The checked envelopes are stored under `docs/engineering/evidence/high-query/` and this gate parses their proof configs, byte sizes, and hashes.

## Non-Claims

- not production-security parameter evidence
- not a proving-time or verifier-time claim
- not exact real-valued Softmax
- not full transformer inference
- not a comparison with external zkML systems
- not evidence that higher query count always improves fused-to-split ratio
- not a permanent Stwo-AI backend change
- not a change to the publication/default q3 backend configuration
