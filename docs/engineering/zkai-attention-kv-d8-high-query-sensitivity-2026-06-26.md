# d8 High-Query Sensitivity

- Issue: `#765`
- Decision: `GO_SMALL_SURFACE_HIGH_QUERY_SENSITIVITY_WITH_RESOURCE_LIMIT_CAVEAT`
- Surface: `d8_single_head_seq8_bounded_softmax_table_attention`
- Backend: `unmodified_stwo_2_2_0_with_scratch_pcs_config_patch`

## Result

This is a small higher-query sensitivity slice, not a new headline row. It reruns the d8 single-head seq8 bounded Softmax-table attention surface with higher FRI query counts and the same split-versus-fused comparator.

| FRI queries | split proof bytes | fused proof bytes | saving | fused/split | fused growth vs q3 | split growth vs q3 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 59437 | 47698 | 11739 | 0.802497 | 1.000000 | 1.000000 |
| 6 | 82115 | 62889 | 19226 | 0.765865 | 1.318483 | 1.381547 |
| 12 | 111430 | 85900 | 25530 | 0.770888 | 1.800914 | 1.874758 |

## Interpretation

On this small d8 surface, q6 and q12 preserve the fused proof-size win. The absolute saving grows from 11739 bytes at q3 to 19226 at q6 and 25530 at q12. The q12 source proof also exceeds the current default d8 source proof byte ceiling, so higher-query experiments need explicit resource-limit retuning before promotion.

The q12 run is useful but should stay engineering-scoped: the source proof exceeded the current default d8 source proof byte ceiling and verified only after a scratch resource-limit retune.

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

src/stwo_backend/attention_kv_native_d8_bounded_softmax_table_proof.rs:
ZKAI_ATTENTION_KV_NATIVE_D8_BOUNDED_SOFTMAX_TABLE_MAX_PROOF_BYTES = 65_536
->
ZKAI_ATTENTION_KV_NATIVE_D8_BOUNDED_SOFTMAX_TABLE_MAX_PROOF_BYTES = 262_144
```

Then run source, sidecar, and fused prove plus verify commands for the d8 bounded Softmax-table input. The checked envelopes are stored under `docs/engineering/evidence/high-query/` and this gate parses their proof configs, byte sizes, and hashes.

## Non-Claims

- not a headline d64 or d128 high-query rerun
- not production-security parameter evidence
- not a proving-time or verifier-time claim
- not exact real-valued Softmax
- not full transformer inference
- not a comparison with external zkML systems
- not evidence that higher query count always improves fused-to-split ratio
- not a permanent Stwo-AI backend change
