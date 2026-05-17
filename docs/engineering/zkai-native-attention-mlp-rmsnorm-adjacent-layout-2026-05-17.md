# zkAI Native Attention+MLP RMSNorm Adjacent Layout Gate - 2026-05-17

Status: `NO_GO_WORST_LABEL_FRONTIER_PROMOTION_BUT_GO_LAYOUT_LEVER`.

This follow-up attacks issue `#644` by changing a real proof layout, not only
the accounting around it. The variant keeps the RMSNorm-input fused adapter
equation and keeps adapter base cells at `0`, but moves the fixed adapter
columns next to the d128 RMSNorm public-row columns in the preprocessed trace.

## Result

The layout lever is real, but it does not promote.

| variant | typed bytes | delta vs frontier | path-opening bytes | JSON proof bytes |
| --- | ---: | ---: | ---: | ---: |
| compact selector reference | `40,812` | `+112` | `19,504` | `116,091` |
| canonical RMSNorm-input fused | `41,428` | `+728` | `20,512` | `118,378` |
| adjacent layout | `40,948` | `+248` | `20,032` | `116,847` |
| adjacent label probe A | `40,948` | `+248` | `20,032` | `116,882` |
| adjacent label probe B | `42,724` | `+2,024` | `21,808` | `123,141` |

The adjacent layout saves `480` typed bytes versus canonical RMSNorm-input
fused by reducing opening/decommitment material:

- FRI decommitments: `13,184 -> 12,832`, saving `352` bytes;
- FRI samples: unchanged at `800` bytes;
- trace decommitments: `6,528 -> 6,400`, saving `128` bytes;
- direct value groups remain unchanged at `20,868` bytes.

That is the good news: moving fixed columns can move the proof-size frontier in
the intended mechanism, without weakening source binding or the adapter
equation.

The bad news is the multi-label policy. Adjacent probe B grows to `42,724`
typed bytes, `2,024` bytes above the `40,700` two-proof frontier. Under the
current policy, this is a NO-GO for frontier promotion.

## Claim Boundary

The checked claim is only:

> Adjacent fixed-column placement is a real opening-layout lever for the
> RMSNorm-input fused adapter, saving `480` canonical typed bytes, but the
> current adjacent layout fails the worst-label policy and does not beat the
> two-proof frontier.

Non-claims:

- not a two-proof frontier beat;
- not a proof-size win;
- not a NANOZK proof-size win;
- not a matched external zkML benchmark;
- not a full transformer block proof;
- not timing evidence;
- not production-ready zkML;
- does not close issue `#644`.

## Evidence

- Compact selector comparator envelope:
  `docs/engineering/evidence/zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json`
- Canonical RMSNorm-input fused comparator envelope:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json`
- Adjacent input:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.input.json`
- Adjacent envelope:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.envelope.json`
- Adjacent label probe A envelope:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-a-2026-05.envelope.json`
- Adjacent label probe B envelope:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-b-2026-05.envelope.json`
- Binary accounting:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-adjacent-layout-accounting-2026-05.json`
- Gate JSON:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-adjacent-layout-2026-05.json`
- Gate TSV:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-adjacent-layout-2026-05.tsv`
- Gate script:
  `scripts/zkai_native_attention_mlp_rmsnorm_adjacent_layout_gate.py`
- Tests:
  `scripts/tests/test_zkai_native_attention_mlp_rmsnorm_adjacent_layout_gate.py`

The gate rejects `12 / 12` mutation cases covering frontier overclaim, result
overclaim, worst-label erasure, canonical-saving drift, label-span drift,
NANOZK overclaim, source digest drift, non-claim erasure, validation-command
erasure, variant metric drift, grouped-field drift, and payload-commitment
drift.

## Reproduction

Metadata:

- Backend binary/version:
  `zkai_native_attention_mlp_single_proof` with
  `stwo-native-attention-mlp-single-proof-object-rmsnorm-input-fused-adjacent-fixed-v1`.
- Toolchain/features:
  `cargo +nightly-2025-07-14 --locked --features stwo-backend`.
- Timing mode: proof-size and verification evidence only; no timing claim and
  no median-of-5 policy.
- Step counts: `3` adjacent build/prove/verify runs, `5` accounting rows,
  `12 / 12` mutation guards rejected, `16 / 16` Python tests, `18 / 18`
  targeted Rust tests, and `14 / 14` full local release-gate steps.
- Evidence paths:
  - `docs/engineering/evidence/zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json`
  - `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json`
  - `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.input.json`
  - `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.envelope.json`
  - `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-a-2026-05.input.json`
  - `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-a-2026-05.envelope.json`
  - `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-b-2026-05.input.json`
  - `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-b-2026-05.envelope.json`
  - `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-adjacent-layout-accounting-2026-05.json`
  - `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-adjacent-layout-2026-05.json`
  - `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-adjacent-layout-2026-05.tsv`
- Commands: the following shell block is the exact command list for the
  checked run.

```sh
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent-label-probe-a docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-a-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-a-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-a-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-a-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent-label-probe-b docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-b-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-b-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-b-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-b-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-a-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-b-2026-05.envelope.json > docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-adjacent-layout-accounting-2026-05.json
python3 scripts/zkai_native_attention_mlp_rmsnorm_adjacent_layout_gate.py --write-json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-adjacent-layout-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-adjacent-layout-2026-05.tsv
python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_adjacent_layout_gate
cargo +nightly-2025-07-14 test --locked --features stwo-backend native_attention_mlp_single_proof --lib
git diff --check
just gate-fast
just gate
```

Recorded gate output:

```json
{"adjacent_canonical_saving_vs_canonical_typed_bytes":480,"adjacent_canonical_typed_bytes":40948,"adjacent_worst_label_delta_vs_frontier_typed_bytes":2024,"adjacent_worst_label_typed_bytes":42724,"decision":"NO_GO_WORST_LABEL_FRONTIER_PROMOTION_BUT_GO_LAYOUT_LEVER","mutation_count":12,"mutations_rejected":12,"result":"ADJACENT_LAYOUT_SAVES_480_TYPED_BYTES_CANONICALLY_BUT_WORST_LABEL_REMAINS_2024_BYTES_ABOVE_FRONTIER"}
```

## Next Attack

This result narrows the path. Fixed-column placement can reduce opening bytes,
but the current variant makes the bad label worse. The next experiment should
target label-stable opening geometry: same semantic fusion, same source binding,
same value bytes, but query/opening behavior that stays near `40,948` under the
bad label instead of jumping to `42,724`.
