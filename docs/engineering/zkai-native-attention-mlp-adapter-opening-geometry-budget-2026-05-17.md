# zkai native attention+MLP adapter opening-geometry budget - 2026-05-17

Status: `GO_OPENING_GEOMETRY_BUDGET_PINNED`.

This gate turns the last adapter NO-GOs into an explicit attack budget for issue #641. It does not introduce a new proof object. It reads the checked binary-accounting artifacts for the current attention-plus-MLP adapter variants and asks which proof-field groups must shrink before another native Rust variant is worth building.

## Result

The compact selector is still the smallest current one-proof object. The RMSNorm-input fused route is the best semantic-fusion attack surface because it has the largest useful value-group reduction and the lowest opening-overhang reduction needed to beat the two-proof frontier.

| variant | typed bytes | delta vs two-proof frontier | reduction to beat frontier | path-opening overhang vs compact | value-group delta vs compact |
|---|---:|---:|---:|---:|---:|
| source-backed duplicate | 43,228 | +2,528 | 2,529 | +2,304 | +112 |
| compact selector | 40,812 | +112 | 113 | 0 | 0 |
| native adapter AIR | 41,932 | +1,232 | 1,233 | +1,008 | +112 |
| preprocessed output-anchor | 41,704 | +1,004 | 1,005 | +1,088 | -196 |
| RMSNorm-input fused | 41,428 | +728 | 729 | +1,008 | -392 |

Human interpretation:

- The best current one-proof object is still `compact_selector`: `40,812` typed bytes, `112` typed bytes above the two-proof frontier.
- The best semantic-fusion target is `rmsnorm_input_fused`: `41,428` typed bytes, `728` typed bytes above the frontier.
- To beat the two-proof frontier, `rmsnorm_input_fused` needs to remove `729` typed bytes.
- Its path-opening overhang versus compact is `1,008` typed bytes, so the target is concrete: remove `72.3214%` of that opening overhead while keeping the semantic fusion.

This is useful because it narrows the next breakthrough attempt. The target is not "remove adapter cells"; we already did that and the proof got larger. The target is "keep semantic fusion while reducing FRI samples, FRI decommitments, or trace decommitments."

## Claim Boundary

The checked claim is only:

> Current attention-plus-MLP adapter variants show that opening/decommitment geometry is the next attack surface; among semantic-fusion variants, RMSNorm-input fused has the best reduction budget, but no current variant beats the compact selector or the two-proof frontier.

Non-claims:

- not a proof-size improvement over the compact selector
- not a two-proof frontier beat
- not a NANOZK proof-size win
- not a matched external zkML benchmark
- not timing evidence
- not a full transformer block proof
- not production-ready zkML

## Evidence

- Gate JSON: `docs/engineering/evidence/zkai-native-attention-mlp-adapter-opening-geometry-budget-2026-05.json`
- Gate TSV: `docs/engineering/evidence/zkai-native-attention-mlp-adapter-opening-geometry-budget-2026-05.tsv`
- Source-backed selector accounting: `docs/engineering/evidence/zkai-native-attention-mlp-source-backed-adapter-selector-binary-accounting-2026-05.json`
- Output-anchor accounting: `docs/engineering/evidence/zkai-native-attention-mlp-preprocessed-output-anchor-adapter-frontier-binary-accounting-2026-05.json`
- RMSNorm-input fused accounting: `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-binary-accounting-2026-05.json`
- Native adapter AIR accounting: `docs/engineering/evidence/zkai-native-attention-mlp-single-proof-binary-accounting-2026-05.json`
- Source-backed duplicate proof envelope: `docs/engineering/evidence/zkai-native-attention-mlp-source-backed-duplicate-adapter-2026-05.envelope.json`
- Source-backed compact proof envelope: `docs/engineering/evidence/zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json`
- Preprocessed output-anchor proof envelope: `docs/engineering/evidence/zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.envelope.json`
- RMSNorm-input fused proof envelope: `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json`
- Native adapter AIR proof envelope: `docs/engineering/evidence/zkai-native-attention-mlp-single-proof-2026-05.envelope.json`
- Positive verifier outputs: recorded in the Gate JSON field `recorded_verifier_outputs` and in the reproduction transcript below.

The gate rejects `9 / 9` mutation cases covering compact typed-byte drift, RMSNorm opening-budget drift, output-anchor opening-budget drift, semantic-attack ranking drift, frontier overclaim, NANOZK overclaim, source-gate commitment drift, source-gate raw-digest drift, and payload commitment drift.

## Reproduction

```sh
# Timing mode: proof-size accounting only; no prove/verify timing or median-of-5 claim.
# Checked surface: existing verified adapter proof objects and their binary-accounting artifacts.
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-source-backed-duplicate-adapter-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-single-proof-2026-05.envelope.json
python3 scripts/zkai_native_attention_mlp_adapter_opening_geometry_budget_gate.py --write-json docs/engineering/evidence/zkai-native-attention-mlp-adapter-opening-geometry-budget-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-attention-mlp-adapter-opening-geometry-budget-2026-05.tsv
python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_adapter_opening_geometry_budget_gate
git diff --check
just gate-fast
just gate
```

Recorded verifier outputs:

```json
{"adapter_mode":"duplicate_base_preprocessed_selector_v1","adapter_status":"NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER","adapter_trace_cells":1536,"envelope_path":"docs/engineering/evidence/zkai-native-attention-mlp-source-backed-duplicate-adapter-2026-05.envelope.json","mode":"verify","pcs_lifting_log_size":19,"proof_size_bytes":124585,"schema":"zkai-native-attention-mlp-single-proof-cli-summary-v1","verified":true}
{"adapter_mode":"compact_base_referenced_fixed_v1","adapter_status":"NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER_COMPACT_BASE_REFERENCED_FIXED_COLUMNS","adapter_trace_cells":1024,"envelope_path":"docs/engineering/evidence/zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json","mode":"verify","pcs_lifting_log_size":19,"proof_size_bytes":116091,"schema":"zkai-native-attention-mlp-single-proof-cli-summary-v1","verified":true}
{"adapter_mode":"preprocessed_output_anchor_fixed_v1","adapter_status":"NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER_PREPROCESSED_FIXED_COLUMNS_WITH_OUTPUT_ANCHOR","adapter_trace_cells":128,"envelope_path":"docs/engineering/evidence/zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.envelope.json","mode":"verify","pcs_lifting_log_size":19,"proof_size_bytes":119360,"schema":"zkai-native-attention-mlp-single-proof-cli-summary-v1","verified":true}
{"adapter_mode":"rmsnorm_input_fused_fixed_v1","adapter_status":"NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER_FUSED_INTO_RMSNORM_INPUT_COMPONENT","adapter_trace_cells":0,"envelope_path":"docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json","mode":"verify","pcs_lifting_log_size":19,"proof_size_bytes":118378,"schema":"zkai-native-attention-mlp-single-proof-cli-summary-v1","verified":true}
{"adapter_mode":"duplicate_base_preprocessed_v1","adapter_status":"NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER","adapter_trace_cells":1536,"envelope_path":"docs/engineering/evidence/zkai-native-attention-mlp-single-proof-2026-05.envelope.json","mode":"verify","pcs_lifting_log_size":19,"proof_size_bytes":119790,"schema":"zkai-native-attention-mlp-single-proof-cli-summary-v1","verified":true}
```

## Next Attack

The separate RMSNorm-input opening-layout follow-up (issue `#644`, not closed by this budget gate) should target the RMSNorm-input fused route, but only if it changes the opening geometry. The concrete future GO gate is:

- preserve source binding and the RMSNorm-input adapter equation;
- keep or improve the value-group savings of `-392` typed bytes versus compact;
- remove at least `729` typed bytes from path-opening overhead;
- reject any NANOZK comparison unless the workload/object class is matched.

If the next variant cannot plausibly reduce FRI/decommitment shape, it should be recorded as NO-GO before spending proving time.
