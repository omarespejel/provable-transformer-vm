# Native Seq32 Attention + D128 MLP Adjacent Label Policy

Status: `GO_ADJACENT_LABEL_PROBES_BEAT_CURRENT_SEQ32_CHAMPION`.

This gate follows the adapter-variant selector no-go. The previous best
zero-base RMSNorm-adjacent layout missed the current duplicate-base champion
by `88` typed bytes, so this experiment checks whether the gap is stable under
the existing adjacent-layout transcript labels.

The workload and statement surface stay fixed:

- two-head `seq32` fused attention with bounded Softmax-table lookup checks;
- the attention-to-d128 adapter;
- the seq32-derived d128 RMSNorm/MLP fused surface.

## Result

| variant | typed bytes | proof JSON bytes | typed delta vs champion | path-opening bytes | value bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| current duplicate-base champion | `42,068` | `121,996` | `0` | `20,592` | `21,428` |
| fixed adjacent layout | `42,156` | `122,688` | `+88` | `21,184` | `20,924` |
| adjacent label probe A | `40,332` | `116,321` | `-1,736` | `19,360` | `20,924` |
| adjacent label probe B | `37,532` | `106,317` | `-4,536` | `16,560` | `20,924` |

Human read: the adjacent route is not dead. The fixed adjacent label was a
near miss, but both checked adjacent label probes verify and beat the current
seq32+d128 local champion. The worst checked probe saves `1,736` typed bytes
(`4.1267%`); the best saves `4,536` typed bytes (`10.7825%`).

## Mechanism

The direct value bytes are stable across fixed adjacent and both adjacent
label probes: `20,924` typed bytes. The movement comes from opening material:

- fixed adjacent worsens path-opening material by `592` typed bytes versus the
  champion;
- probe A saves `1,232` path-opening typed bytes versus the champion;
- probe B saves `4,032` path-opening typed bytes versus the champion.

This means the next optimization target is transcript/opening stability, not
more adapter arithmetic. The important question is whether we can freeze a
deterministic label policy that keeps the worst supported label near the probe
results, rather than promoting a favorable one-off transcript.

## Guardrails

- Not a NANOZK proof-size win.
- Not a matched external zkML benchmark.
- Not a full transformer block proof.
- Not exact real-valued Softmax.
- Not timing evidence.
- Not production-ready zkML.
- Not a final production label-selection policy.

NANOZK's paper-reported d128 block row remains related-work calibration only.
This gate has `0` proof-size-comparable external rows.

## Evidence

- Backend binary:
  `zkai_native_seq32_attention_mlp_single_proof`
- Adjacent/probe backend version:
  `stwo-native-seq32-attention-mlp-single-proof-object-rmsnorm-input-fused-adjacent-fixed-v1`
- Champion backend version:
  `stwo-native-seq32-attention-mlp-single-proof-object-native-adapter-v1`
- Proof schema:
  `stwo-native-seq32-attention-mlp-single-proof-object-native-adapter-payload-v1`
- Statement version:
  `zkai-native-seq32-attention-mlp-single-proof-object-native-adapter-statement-v1`
- Workload target:
  `attention-kv-two-head-seq32-fused-softmax-table-plus-seq32-derived-d128-rmsnorm-mlp-v1`
- Step/log-size metadata:
  `pcs_lifting_log_size = 19`; adjacent/probe `adapter_trace_cells = 0`.
- Timing mode:
  proof-size/accounting only; no timing claim and no median-of-5.

- Label-policy gate JSON:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-policy-2026-05.json`
- Label-policy gate TSV:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-policy-2026-05.tsv`
- Binary accounting:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-accounting-2026-05.json`
- Probe A envelope:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.envelope.json`
- Probe B envelope:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.envelope.json`

The gate rejects `13 / 13` mutation cases: decision drift, result drift,
saving erasure, best-probe typed drift, adapter-mode relabeling, value-group
drift, path-opening saving erasure, label-span erasure, source-artifact digest
drift, validation-command drift, removed non-claims, NANOZK overclaim, and
payload-commitment drift.

## Reproduction

```bash
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent-label-probe-a docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent-label-probe-b docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.envelope.json > docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-accounting-2026-05.json
python3.10 scripts/zkai_native_seq32_attention_mlp_adjacent_label_policy_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-policy-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-policy-2026-05.tsv
python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_adjacent_label_policy_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_adjacent_label_policy_gate.py
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_adjacent_label_policy_gate
cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_adjacent_label --lib
cargo +nightly-2025-07-14 test --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof
git diff --check
just gate-fast
just gate
```

## Next Attack

The immediate follow-up is a deterministic adjacent-label policy:

- inventory the allowed query/opening labels for this surface;
- reject label policies that preserve arithmetic but inflate path openings;
- require the worst supported adjacent label to beat `42,068` typed bytes;
- keep NANOZK and other external rows out until object classes match.
