# Native Seq32 Attention+MLP Expanded Label Probe

Date: 2026-05-19
Issue: https://github.com/omarespejel/provable-transformer-vm/issues/690
Follow-up issue: https://github.com/omarespejel/provable-transformer-vm/issues/691

## Decision

`NO_GO_EXPANDED_LABEL_PROBES_DO_NOT_BEAT_ADJACENT_PROBE_B_FRONTIER`

This gate exposes four already-existing Rust label-probe modes through the
`zkai_native_seq32_attention_mlp_single_proof` CLI, generates real Stwo proof
objects for them, and compares them against the current local seq32+d128
frontier.

## Result

| variant | family | typed bytes | JSON proof bytes | delta vs 37,532 frontier |
| --- | --- | ---: | ---: | ---: |
| adjacent probe B | adjacent | `37,532` | `106,317` | `0` |
| fixed-label probe B | fixed | `40,476` | `116,661` | `+2,944` |
| post-tail probe B | post-tail | `41,564` | `120,368` | `+4,032` |
| fixed-label probe A | fixed | `42,156` | `122,655` | `+4,624` |
| post-tail probe A | post-tail | `42,156` | `122,418` | `+4,624` |

The new probes all verify locally, and fixed-label probe B is still interesting
because it beats the older `42,068` typed-byte duplicate-base champion by
`1,592` typed bytes. But none of the new probes beat the current `37,532`
typed-byte adjacent probe B frontier.

## Human Read

This narrows the mechanism. The previous result was not just "any label change
can make the proof smaller." The best current behavior needs the adjacent
RMSNorm-input layout and the favorable probe-B transcript. Moving the same
label-probe idea to the fixed and post-tail layouts keeps correctness but loses
path-opening efficiency.

## Mechanism

Direct value bytes stay fixed at `20,924` across adjacent probe B and the new
probe rows. The difference is path-opening and FRI material:

- adjacent probe B path-opening bytes: `16,560`;
- fixed-label probe B path-opening bytes: `19,360`;
- post-tail probe B path-opening bytes: `20,592`.

So the current lead is still transcript/opening geometry, but it is
layout-sensitive. The next valid exploration should be a bounded adjacent-only
label-seed sweep that reports every seed, not just the best one.

## Guardrails

- Not a new proof-size frontier beyond the `37,532` typed-byte adjacent probe B
  row.
- Not a production label-selection policy.
- Not a NANOZK proof-size win.
- Not a matched external zkML benchmark.
- Not a full transformer block proof.
- Not exact real-valued Softmax.
- Not timing evidence.
- Not production-ready zkML.

## Evidence

- Gate JSON:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-expanded-label-probe-2026-05.json`
- Gate TSV:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-expanded-label-probe-2026-05.tsv`
- Expanded accounting:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-expanded-label-probe-accounting-2026-05.json`
- Gate JSON SHA-256:
  `81fa5c1d06669a4b4665be2c4e1155982c9ff62545d7b8ebdab78e12d9f90d01`
- Payload commitment:
  `blake2b-256:2cbce6165b6c0da4dbdf09d16ba2782d6fdb1f89d59538051d968c035384df14`
- Mutation guards:
  `10 / 10` rejected.

The gate rejects decision drift, NANOZK overclaim drift, accounting digest
drift, frontier-promotion drift, new-probe typed-byte drift, adapter-mode
relabeling, path-opening mechanism drift, validation-command drift, removed
non-claims, and payload-commitment drift.

## Reproduction

```bash
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-label-probe-a docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-fused-label-probe-a-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-label-probe-b docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-fused-label-probe-b-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-post-tail-label-probe-a docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-label-probe-a-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-post-tail-label-probe-b docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-label-probe-b-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-fused-label-probe-a-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-fused-label-probe-b-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-label-probe-a-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-label-probe-b-2026-05.envelope.json > docs/engineering/evidence/zkai-native-seq32-attention-mlp-expanded-label-probe-accounting-2026-05.json
python3.10 scripts/zkai_native_seq32_attention_mlp_expanded_label_probe_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-expanded-label-probe-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-expanded-label-probe-2026-05.tsv
python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_expanded_label_probe_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_expanded_label_probe_gate.py
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_expanded_label_probe_gate
cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_adjacent_label --lib
git diff --check
just gate-fast
just gate
```

## Next Attack

Run a pre-registered adjacent-only seed sweep. The acceptance rule should be
strict: every generated proof object must be source-exposed, envelope-bound,
typed-accounted, mutation-guarded, and reported whether it wins or loses.
