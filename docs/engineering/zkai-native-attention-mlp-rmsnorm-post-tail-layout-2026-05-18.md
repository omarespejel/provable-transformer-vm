# zkAI Native Attention+MLP RMSNorm Post-Tail Layout Gate - 2026-05-18

Status: `NO_GO_POST_TAIL_LAYOUT_LABEL_STABILITY`.

This follow-up attacks issue `#665` under the broader adapter proof-shape
optimization issue `#641`. The question was narrow: keep the RMSNorm-input
fused adapter equation and keep adapter base cells at `0`, but move the
RMSNorm-input fused fixed columns after the MLP tail in the preprocessed trace.
If the bad adjacent-label result was mostly an unlucky local ordering, this
could have stabilized the opening layout.

It did not.

## Result

| variant | typed bytes | delta vs frontier | path-opening bytes | JSON proof bytes |
| --- | ---: | ---: | ---: | ---: |
| compact selector reference | `40,812` | `+112` | `19,504` | `116,091` |
| canonical RMSNorm-input fused | `41,428` | `+728` | `20,512` | `118,378` |
| adjacent layout | `40,948` | `+248` | `20,032` | `116,847` |
| adjacent bad label | `42,724` | `+2,024` | `21,808` | `123,141` |
| post-tail layout | `42,724` | `+2,024` | `21,808` | `122,976` |
| post-tail label probe A | `41,508` | `+808` | `20,592` | `118,526` |
| post-tail label probe B | `42,724` | `+2,024` | `21,808` | `123,018` |

The post-tail canonical layout verifies, preserves zero adapter base cells, and
keeps the RMSNorm-input fused adapter equation. But it lands on the same local
typed proof-field shape as the adjacent bad-label case:

- post-tail canonical typed bytes: `42,724`;
- adjacent bad-label typed bytes: `42,724`;
- post-tail canonical penalty versus adjacent canonical: `1,776` typed bytes;
- post-tail canonical penalty versus canonical RMSNorm-input fused: `1,296`
  typed bytes;
- post-tail canonical delta versus the `40,700` two-proof frontier: `2,024`
  typed bytes.

The exact overhang is path/opening material, not direct values:

- FRI decommitments: `13,184 -> 14,176`, `+992` bytes versus canonical
  RMSNorm-input fused;
- FRI samples: `800 -> 848`, `+48` bytes;
- trace decommitments: `6,528 -> 6,784`, `+256` bytes;
- direct value groups stay unchanged at `20,868` bytes.

Post-tail probe A is better at `41,508` typed bytes, but still sits `808` bytes
above the two-proof frontier and `560` bytes above the adjacent canonical
layout. That means the post-tail move does not solve label stability.

## Claim Boundary

The checked claim is only:

> Moving the RMSNorm-input fused fixed columns after the MLP tail preserves the
> zero-base semantic fusion route, but it inherits the bad opening geometry and
> is not a frontier promotion.

Non-claims:

- not a two-proof frontier beat;
- not a proof-size win;
- not a NANOZK proof-size win;
- not a matched external zkML benchmark;
- not a full transformer block proof;
- not timing evidence;
- not production-ready zkML;
- does not close parent issue `#641`.

## Evidence

- Compact selector comparator envelope:
  `docs/engineering/evidence/zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json`
- Canonical RMSNorm-input fused comparator envelope:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json`
- Adjacent layout comparator envelope:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.envelope.json`
- Adjacent bad-label comparator envelope:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-b-2026-05.envelope.json`
- Post-tail input:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-layout-2026-05.input.json`
- Post-tail envelope:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-layout-2026-05.envelope.json`
- Post-tail label-probe A envelope:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-a-2026-05.envelope.json`
- Post-tail label-probe B envelope:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-b-2026-05.envelope.json`
- Binary accounting:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-post-tail-layout-accounting-2026-05.json`
- Gate JSON:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-post-tail-layout-2026-05.json`
- Gate TSV:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-post-tail-layout-2026-05.tsv`
- Gate script:
  `scripts/zkai_native_attention_mlp_rmsnorm_post_tail_layout_gate.py`
- Tests:
  `scripts/tests/test_zkai_native_attention_mlp_rmsnorm_post_tail_layout_gate.py`

The gate rejects `17 / 17` mutation cases covering frontier overclaim,
result overclaim, post-tail metric erasure, frontier-delta erasure,
adjacent-penalty erasure, label-span drift, record-stream match erasure,
NANOZK overclaim, source digest drift, non-claim erasure, validation-command
erasure, variant provenance drift, interpretation drift, variant metric drift,
grouped-field drift, policy-group drift, and payload-commitment drift.

## Reproduction

Metadata:

- Backend binary:
  `zkai_native_attention_mlp_single_proof`.
- Backend version:
  `stwo-native-attention-mlp-single-proof-object-rmsnorm-input-fused-post-tail-fixed-v1`.
- Toolchain/features:
  `cargo +nightly-2025-07-14 --locked --features stwo-backend`.
- Timing mode: proof-size and verification evidence only; no timing claim and
  no median-of-5 policy.
- Step counts: `3` post-tail build/prove/verify runs, `7` accounting rows,
  `17 / 17` mutation guards rejected, `19 / 19` Python tests, `21 / 21`
  targeted Rust tests.

Commands:

```sh
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused-post-tail docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-layout-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-layout-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-layout-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-layout-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused-post-tail-label-probe-a docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-a-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-a-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-a-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-a-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused-post-tail-label-probe-b docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-b-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-b-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-b-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-b-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-b-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-layout-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-a-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-b-2026-05.envelope.json > docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-post-tail-layout-accounting-2026-05.json
python3 scripts/zkai_native_attention_mlp_rmsnorm_post_tail_layout_gate.py --write-json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-post-tail-layout-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-post-tail-layout-2026-05.tsv
python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_post_tail_layout_gate
cargo +nightly-2025-07-14 test --locked --features stwo-backend native_attention_mlp_single_proof --lib
git diff --check
just gate-fast
just gate
```

Recorded gate output:

```json
{"decision":"NO_GO_POST_TAIL_LAYOUT_LABEL_STABILITY","mutation_count":17,"mutations_rejected":17,"post_tail_canonical_typed_bytes":42724,"post_tail_delta_vs_two_proof_frontier_typed_bytes":2024,"post_tail_label_span_typed_bytes":1216,"post_tail_penalty_vs_adjacent_canonical_typed_bytes":1776,"result":"POST_TAIL_CANONICAL_MATCHES_ADJACENT_BAD_LABEL_42724_TYPED_BYTES_AND_DOES_NOT_PROMOTE_FRONTIER"}
```

## Next Attack

Post-tail placement should be parked. The evidence points away from another
local fixed-column reorder and toward either:

1. label-stable query/opening geometry, where multiple label probes remain
   near the same typed size;
2. a different native block boundary that reduces verifier-facing openings
   before the adapter/RMSNorm-input edge;
3. a larger d128 block-object route where the proof-size benefit comes from
   sharing more proof plumbing, not from sub-kilobyte layout tuning.
