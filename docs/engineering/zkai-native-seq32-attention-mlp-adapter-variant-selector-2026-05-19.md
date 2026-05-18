# Native Seq32 Attention + D128 MLP Adapter Variant Selector

Status: `NO_GO_ADAPTER_VARIANTS_DO_NOT_BEAT_CURRENT_SEQ32_NATIVE_SINGLE_PROOF`.

This gate tests whether the current seq32+d128 native single-proof result can
be improved by changing only the attention-output-to-d128 adapter placement.
The workload and statement surface stay fixed:

- two-head `seq32` fused attention with bounded Softmax-table lookup checks;
- the attention-to-d128 adapter;
- the seq32-derived d128 RMSNorm/MLP fused surface.

## Result

| variant | adapter cells | typed bytes | proof JSON bytes | typed delta vs champion |
| --- | ---: | ---: | ---: | ---: |
| current duplicate-base champion | `1,536` | `42,068` | `121,996` | `0` |
| compact base | `1,024` | `42,548` | `123,801` | `+480` |
| output-anchor base | `128` | `42,976` | `125,345` | `+908` |
| RMSNorm-input fused | `0` | `42,780` | `124,840` | `+712` |
| RMSNorm-input adjacent layout | `0` | `42,156` | `122,688` | `+88` |
| RMSNorm-input post-tail layout | `0` | `42,780` | `124,774` | `+712` |

Human read: removing adapter base cells is not enough. Three variants remove
the adapter base trace entirely, but the current duplicate-base proof remains
the typed-size champion. The best zero-base adjacent layout misses by only
`88` typed bytes.

## Mechanism

The best adjacent zero-base variant reduces OODS plus queried values by `504`
typed bytes versus the champion, but pays `576` extra bytes in FRI/trace
decommitment material and `16` extra FRI sample bytes. Net result: `+88` typed
bytes.

This is a useful no-go. The next attack should target query/opening stability,
not further adapter base-cell removal.

## Guardrails

- Not a new proof-size frontier.
- Not a NANOZK proof-size win.
- Not a matched external zkML benchmark.
- Not a full transformer block proof.
- Not exact real-valued Softmax.
- Not timing evidence.
- Not production-ready zkML.

The current champion remains `42,068 / 6,900 = 6.096812x` NANOZK's
paper-reported d128 row, which is related-work calibration only.

## Evidence

- Selector gate JSON:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-adapter-variant-selector-2026-05.json`
- Selector gate TSV:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-adapter-variant-selector-2026-05.tsv`
- Binary accounting:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-adapter-variant-selector-accounting-2026-05.json`
- Variant envelopes:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-compact-adapter-2026-05.envelope.json`,
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.envelope.json`,
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json`,
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json`,
  and
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.envelope.json`.

The gate rejects `13 / 13` mutation cases: frontier promotion drift, gap
erasure, current champion drift, variant metric drift, variant metadata drift,
inventory drift, overclaim drift, source artifact drift, validation-command
drift, and payload commitment drift.

## Reproduction

```bash
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-compact docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-compact-adapter-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-compact-adapter-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-compact-adapter-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-compact-adapter-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-preprocessed-anchor docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-post-tail docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-compact-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.envelope.json > docs/engineering/evidence/zkai-native-seq32-attention-mlp-adapter-variant-selector-accounting-2026-05.json
python3.10 scripts/zkai_native_seq32_attention_mlp_adapter_variant_selector_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-adapter-variant-selector-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-adapter-variant-selector-2026-05.tsv
python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_adapter_variant_selector_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_adapter_variant_selector_gate.py
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_adapter_variant_selector_gate
cargo +nightly-2025-07-14 test --locked --features stwo-backend native_seq32_attention_mlp_single_proof --lib
git diff --check
just gate-fast
just gate
```

## Next Attack

The route is still alive, but the target is narrower:

- keep the adjacent zero-base semantics;
- stabilize or reduce FRI/trace decommitment material;
- require the worst checked layout/label to beat `42,068` typed bytes, not one
  favorable transcript;
- keep external comparisons out until the object class is matched.
