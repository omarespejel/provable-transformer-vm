# zkAI Native Attention+MLP RMSNorm Label Policy - 2026-05-17

Status: `NO_GO_MULTI_LABEL_FRONTIER_PROMOTION`.

This gate follows the RMSNorm-input label-sensitivity result for issue `#644`.
It does not build a new proof object. It defines the promotion rule needed
before a future sub-kilobyte opening-layout improvement can be treated as a
frontier result.

## Result

The previous label-sensitivity gate showed that label-only transcript movement
can shift the same relation by `1,264` typed bytes. This policy gate turns that
into a concrete rule:

> A future RMSNorm-input opening-layout claim must beat the two-proof frontier
> under the worst label in the checked label inventory, not under one favorable
> label.

Current numbers:

| policy candidate | typed bytes | delta vs frontier | reduction to beat frontier | cherry-pick risk |
| --- | ---: | ---: | ---: | --- |
| single best label | `40,836` | `+136` | `137` | yes |
| canonical label | `41,428` | `+728` | `729` | no |
| mean of two label probes | `41,468` | `+768` | `769` | yes |
| worst label inventory | `42,100` | `+1,400` | `1,401` | no |

Human interpretation: the route is less close than the best single label makes
it look. A cherry-picked view says the next route is `137` typed bytes away from
the two-proof frontier. An honest worst-label policy says it is `1,401` typed
bytes away.

That is useful. It prevents us from promoting a transcript accident as a
structural STARK-native proof-size win.

## Policy

The current promotion policy is:

- report the full label inventory;
- preserve the adapter equation and source binding inherited from the
  RMSNorm-input fused route;
- preserve direct value bytes across labels;
- require the worst observed label to be below the `40,700` typed-byte
  two-proof frontier;
- reject NANOZK proof-size comparisons unless the workload and proof-object
  class are matched.

Under this policy the current inventory is a NO-GO:

- best label: `40,836`, still `+136` above frontier;
- worst label: `42,100`, `+1,400` above frontier;
- required worst-label reduction to beat frontier: `1,401`;
- required worst-label reduction to beat compact selector: `1,289`;
- direct value delta across label probes: `0`.

## Claim Boundary

The checked claim is only:

> Current RMSNorm-input label inventory does not support frontier promotion.
> Future opening-layout wins must beat the frontier under a worst-label
> inventory policy, because one favorable transcript label is not stable enough
> evidence.

Non-claims:

- not a two-proof frontier beat;
- not a proof-size win;
- not a NANOZK proof-size win;
- not a matched external zkML benchmark;
- not timing evidence;
- not a full transformer block proof;
- not production-ready zkML.

## Evidence

- `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-label-policy-2026-05.json`
- `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-label-policy-2026-05.tsv`
- Source gate:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-label-sensitivity-2026-05.json`
- Gate script:
  `scripts/zkai_native_attention_mlp_rmsnorm_label_policy_gate.py`
- Tests:
  `scripts/tests/test_zkai_native_attention_mlp_rmsnorm_label_policy_gate.py`

The policy gate rejects `17 / 17` mutation cases covering frontier overclaim,
NANOZK overclaim, worst-label metric drift, promotion-policy drift,
single-label promotion, label-span erasure, missing worst-label inventory,
source digest drift, source commitment drift, decision/result/claim-boundary
drift, non-claim erasure, validation-command erasure, interpretation drift,
extra policy keys, and payload-commitment drift.

## Reproduction

```sh
python3 scripts/zkai_native_attention_mlp_rmsnorm_label_policy_gate.py --write-json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-label-policy-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-label-policy-2026-05.tsv
python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_label_policy_gate
python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_label_sensitivity_gate
git diff --check
just gate-fast
just gate
```

Recorded gate output:

```json
{"decision":"NO_GO_MULTI_LABEL_FRONTIER_PROMOTION","mutation_count":17,"mutations_rejected":17,"result":"WORST_LABEL_INVENTORY_REQUIRES_1401_TYPED_BYTE_REDUCTION_BEFORE_PROMOTION","worst_label_inventory_typed_bytes":42100,"worst_label_reduction_to_beat_frontier_bytes":1401}
```

## Next Attack

The next structural opening-layout attempt should not optimize for the single
best label. It should target the worst-label policy:

- remove at least `1,401` typed bytes from the current worst-label inventory;
- preserve `0` direct-value delta across labels;
- keep the RMSNorm-input adapter equation and source binding;
- report every checked label in the inventory;
- only promote if the worst label beats the two-proof frontier.

If a future route only wins under one favorable transcript label, record it as
exploration and do not promote it.
