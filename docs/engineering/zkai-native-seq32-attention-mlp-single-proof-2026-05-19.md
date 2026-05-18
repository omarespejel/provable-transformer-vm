# Native Seq32 Attention + D128 MLP Single Proof

Status: `GO_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_OBJECT_BEATS_MATCHED_FRONTIER`.

This gate builds one native Stwo proof object over:

- two-head `seq32` fused attention with bounded Softmax-table lookup checks;
- a public attention-output-to-d128 adapter;
- the seq32-derived d128 RMSNorm/MLP fused surface.

The honest comparison is the previously pinned value-compatible two-proof
frontier, not NANOZK and not a full transformer block.

## Result

| object | typed bytes | proof JSON bytes |
| --- | ---: | ---: |
| matched two-proof frontier | `47,188` | `140,838` |
| native seq32+d128 single proof | `42,068` | `121,996` |
| saving | `5,120` | `18,842` |
| ratio | `0.891498x` | `0.866215x` |

Human read: the larger native boundary is now a real local size win. It
proves the same selected seq32 attention plus seq32-derived d128 MLP surface in
one object and saves `10.8502%` typed bytes against the matched local frontier.

## Why This Matters

The earlier signal was that lookup work grew from `52` to `1,184` claims
(`22.769231x`) while typed attention bytes grew only `1.264401x`. This PR turns
that target-selection signal into a checked native-boundary proof object.

The win is structural but still local: shared commitment/opening plumbing beats
the matched two-proof object for this workload. This does not yet prove that the
route beats external systems.

## Guardrails

- Not a NANOZK proof-size win.
- Not a matched external zkML benchmark.
- Not a full transformer block proof.
- Not exact real-valued Softmax.
- Not full autoregressive inference.
- Not timing evidence.
- Not production-ready zkML.

Against NANOZK's paper-reported `6,900` byte d128 row, this object is still
`42,068 / 6,900 = 6.096812x`. That row remains related-work calibration only.

## Evidence

- Gate JSON:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.json`
- Gate TSV:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.tsv`
- Single-proof input:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.input.json`
- Single-proof envelope:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json`
- Binary accounting:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-binary-accounting-2026-05.json`

The gate rejects `15 / 15` mutation cases: typed metric drift, JSON metric
drift, frontier drift, issue-hint drift, NANOZK overclaim drift, source artifact relabeling,
proof/envelope digest drift, validation-command drift, and payload-commitment
drift.

## Reproduction

```bash
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json > docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-binary-accounting-2026-05.json
python3.10 scripts/zkai_native_seq32_attention_mlp_single_proof_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.tsv
python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_single_proof_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_single_proof_gate.py
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_single_proof_gate
cargo +nightly-2025-07-14 test --locked --features stwo-backend native_seq32_attention_mlp_single_proof --lib
git diff --check
just gate-fast
just gate
```

## Next Attack

The next bounded attack is not another loose comparison. It is an
opening-layout/adapter-placement variant for the same workload:

- preserve the checked statement and source bindings;
- target fewer FRI/opening bytes;
- keep the matched frontier fixed at `47,188` typed bytes;
- reject any NANOZK or full-block promotion unless the object class becomes
  matched.
