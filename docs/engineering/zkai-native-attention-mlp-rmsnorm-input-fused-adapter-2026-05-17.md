# zkai native attention+MLP RMSNorm-input fused adapter gate - 2026-05-17

Status: `NO_GO_RMSNORM_INPUT_FUSED_ADAPTER_PROOF_SIZE_FRONTIER`.

This gate tests the next adapter proof-shape attack from issue #641: remove the separate adapter base trace and prove the attention-to-d128 adapter equation inside the existing d128 RMSNorm input component. The route is intentionally source-backed for the adapter fixed columns and still uses the same d8 fused attention + attention-derived d128 RMSNorm-MLP workload.

## Result

The route proves and verifies, but it is not a proof-size frontier.

| route | adapter base cells | JSON proof bytes | local typed bytes |
|---|---:|---:|---:|
| compact selector | 1,024 | 116,091 | 40,812 |
| RMSNorm-input fused adapter | 0 | 118,378 | 41,428 |

The fused route is `616` typed bytes larger than the compact selector and `728` typed bytes above the current `40,700` typed-byte two-proof frontier.

## Accounting Delta

RMSNorm-input fused minus compact selector:

| group | delta bytes |
|---|---:|
| fixed overhead | 0 |
| FRI decommitments | +736 |
| FRI samples | +16 |
| OODS samples | -224 |
| queried values | -168 |
| trace decommitments | +256 |

Human interpretation: semantic fusion worked, but proof-size did not. Removing adapter base cells reduced queried/OODS values, but the transcript paid more in FRI and trace decommitments.

## Claim Boundary

This is a correctness and proof-shape learning result, not a compression breakthrough. The checked claim is only:

> A zero-adapter-base-cell RMSNorm-input fused adapter can prove and verify in the one native Stwo proof object, but this specific proof shape does not beat the compact adapter or the two-proof frontier.

Non-claims:

- not a proof-size improvement
- not a two-proof frontier beat
- not a NANOZK proof-size win
- not a matched external zkML benchmark
- not timing evidence
- not a full transformer block proof
- not production-ready zkML

## Evidence

- Input: `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.input.json`
- Envelope: `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json`
- Accounting: `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-binary-accounting-2026-05.json`
- Gate JSON: `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.json`
- Gate TSV: `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.tsv`

The gate rejects `8 / 8` mutation cases covering metric drift, relabeling, zero-cell drift, frontier overclaim, compact-win overclaim, NANOZK overclaim, and payload commitment drift.

## Reproduction

```sh
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json > docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-binary-accounting-2026-05.json
python3 scripts/zkai_native_attention_mlp_rmsnorm_input_fused_adapter_gate.py --write-json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.tsv
python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_input_fused_adapter_gate
cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_fused_adapter --lib
```

## Next Attack

Do not keep shrinking adapter cells in isolation. The promising next attack is opening/decommitment geometry: either find a component layout that keeps the semantic fusion while avoiding extra FRI/decommitment cost, or move the adapter relation into an already-favorable component boundary without adding a worse transcript shape.
