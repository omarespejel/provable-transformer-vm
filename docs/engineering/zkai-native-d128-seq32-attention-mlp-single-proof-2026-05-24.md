# Native D128 Seq32 Attention + D128 MLP Single Proof

Issue: #715

Status: `GO_NATIVE_D128_SEQ32_ATTENTION_MLP_SINGLE_PROOF_BEATS_SCOPED_SPLIT_FRONTIER`.

This gate builds one native Stwo proof object over the real d128 two-head
`seq32` fused attention source, a verifier-recomputed d128 adapter, and the
seq32-derived d128 RMSNorm/MLP surface.

## Result

| object | proof JSON bytes | typed bytes |
| --- | ---: | ---: |
| matched scoped split frontier | `520,399` | `209,172` |
| native scoped single proof | `503,004` | `204,564` |
| saving | `17,395` | `4,608` |
| ratio | `0.966574x` | `0.977970x` |

## Meaning

The d128 scoped boundary is still a local one-proof size win. The win is
smaller than the earlier seq32 champion, which is useful evidence: width
pressure is real, but the boundary still shares enough proof plumbing to beat
the matched split local frontier.

## Guardrail

The adapter is a scoped public binding device for this experiment. This is not
a model-faithful full transformer block and not an external-system comparison.

## Evidence

- JSON gate: `docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.json`
- TSV gate: `docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.tsv`
- Input: `docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.input.json`
- Envelope: `docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.envelope.json`
- Single accounting: `docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-binary-accounting-2026-05.json`
- Split accounting: `docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-split-frontier-binary-accounting-2026-05.json`

## Non-Claims

- not a full transformer block proof.
- not a model-faithful d128 attention-to-MLP adapter.
- not a NANOZK proof-size win.
- not a matched external zkML benchmark.
- not exact real-valued Softmax.
- not full autoregressive inference.
- not timing evidence.
- not production-ready zkML.

## Reproduce

```bash
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_d128_seq32_attention_mlp_single_proof -- build-input docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_d128_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.input.json docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_d128_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.envelope.json > docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-binary-accounting-2026-05.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.envelope.json > docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-split-frontier-binary-accounting-2026-05.json
python3.10 scripts/zkai_native_d128_seq32_attention_mlp_single_proof_gate.py --write-json docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.tsv --write-md docs/engineering/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05-24.md
python3.10 -m py_compile scripts/zkai_native_d128_seq32_attention_mlp_single_proof_gate.py scripts/tests/test_zkai_native_d128_seq32_attention_mlp_single_proof_gate.py
python3.10 -m unittest scripts.tests.test_zkai_native_d128_seq32_attention_mlp_single_proof_gate
cargo +nightly-2025-07-14 test --locked --features stwo-backend native_d128_seq32_attention_mlp_single_proof --lib
git diff --check
just gate-fast
```
