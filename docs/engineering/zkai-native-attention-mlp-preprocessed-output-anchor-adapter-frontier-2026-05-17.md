# Preprocessed output-anchor adapter frontier

Issue: [#639](https://github.com/omarespejel/provable-transformer-vm/issues/639)

## Result

`NO_GO_FEWER_ADAPTER_BASE_CELLS_INCREASE_TYPED_PROOF_BYTES`

This probe tested the obvious next attack after the source-backed compact
adapter near-miss: remove nearly all adapter base columns and leave only one
`output_q8` base anchor, while keeping the deterministic adapter columns in the
verifier-recomputed preprocessed trace.

The one-column route proves and verifies, but it is not smaller under the local
typed accounting surface. That makes it a useful no-go: shrinking the adapter
trace does not automatically shrink the proof object because the transcript,
query, and decommitment shape can move in the wrong direction.

## Numbers

| Route | Adapter base cells | JSON proof bytes | Local typed bytes |
|---|---:|---:|---:|
| Source-backed compact selector | `1,024` | `116,091` | `40,812` |
| Preprocessed output-anchor adapter | `128` | `119,360` | `41,704` |
| Current two-proof frontier | n/a | `116,258` | `40,700` |

The output-anchor adapter removes `896` adapter base cells versus the compact
selector, but increases the local typed proof estimate by `892` bytes and JSON
proof size by `3,269` bytes.

Against the current two-proof frontier, the output-anchor proof is `1,004`
typed bytes heavier and `3,102` JSON bytes heavier.

## Why It Lost

The local typed deltas versus the compact selector are:

| Group | Anchor minus compact bytes |
|---|---:|
| OODS samples | `-112` |
| Query values | `-84` |
| FRI samples | `32` |
| FRI decommitments | `800` |
| Trace decommitments | `256` |
| Fixed overhead | `0` |

The direct opened-value surface improves by `196` bytes, but FRI and trace
decommitments get `1,088` bytes worse. Net result: `+892` typed bytes.

Human meaning: this is not a simple column-count problem anymore. The next
attack needs to preserve or improve proof-path shape, not just remove witness
columns.

## Claim Boundary

This PR shows:

- the output-anchor adapter mode exists in the Rust backend;
- it produces a real verifying Stwo proof artifact;
- it proves only one adapter base value column;
- it preserves source-backed fixed preprocessed columns;
- reducing adapter base cells can still increase proof bytes.

This PR does not show:

- a proof-size improvement;
- a compact-adapter replacement;
- a two-proof frontier beat;
- a NANOZK proof-size win;
- a matched external zkML benchmark;
- timing evidence;
- a full transformer block proof;
- production readiness.

## Evidence

- `docs/engineering/evidence/zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.input.json`
- `docs/engineering/evidence/zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.envelope.json`
- `docs/engineering/evidence/zkai-native-attention-mlp-preprocessed-output-anchor-adapter-frontier-binary-accounting-2026-05.json`
- `docs/engineering/evidence/zkai-native-attention-mlp-preprocessed-output-anchor-adapter-frontier-2026-05.json`
- `docs/engineering/evidence/zkai-native-attention-mlp-preprocessed-output-anchor-adapter-frontier-2026-05.tsv`

## Reproducibility metadata

- Backend binary: `zkai_native_attention_mlp_single_proof`
- Backend version:
  `stwo-native-attention-mlp-single-proof-object-preprocessed-output-anchor-adapter-v1`
- Timing mode: proof-size accounting only; no timing or median-of-5 claim.
- Toolchain: `nightly-2025-07-14`
- PCS/profile note: publication-v1 PCS with explicit lifting log size `19`.
- Checked surface: native attention-plus-MLP single proof over d8 fused
  attention and d128 RMSNorm-MLP, with a `128`-row adapter and one
  output-anchor base column.

## Reproduction

```bash
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-preprocessed-anchor docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.envelope.json > docs/engineering/evidence/zkai-native-attention-mlp-preprocessed-output-anchor-adapter-frontier-binary-accounting-2026-05.json
python3 scripts/zkai_native_attention_mlp_preprocessed_output_anchor_adapter_frontier_gate.py --write-json docs/engineering/evidence/zkai-native-attention-mlp-preprocessed-output-anchor-adapter-frontier-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-attention-mlp-preprocessed-output-anchor-adapter-frontier-2026-05.tsv
python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_preprocessed_output_anchor_adapter_frontier_gate
cargo +nightly-2025-07-14 test --locked --features stwo-backend preprocessed_output_anchor_adapter --lib
cargo +nightly-2025-07-14 test --locked --features stwo-backend native_attention_mlp_single_proof --lib
git diff --check
just gate-fast
just gate
```
