# zkAI Native Attention+MLP RMSNorm Opening-Budget Route - 2026-05-17

Status: `CONDITIONAL_GO_OPENING_OVERHANG_ATTACK_WITH_STRICT_WORST_LABEL_TARGET`.

This gate follows the RMSNorm-input label-policy result for issue `#644`.
It does not build a new proof object. It asks whether the current
opening-layout route has enough typed-byte budget to beat the strict
worst-label policy, or whether the route should be abandoned.

## Result

The route is still worth one more structural attack, but only under a strict
target.

Current worst-label policy:

- two-proof frontier: `40,700` typed bytes;
- worst checked RMSNorm-input label: `42,100` typed bytes;
- required reduction to beat frontier: `1,401` typed bytes.

The worst label has `21,184` typed path-opening bytes. The compact selector has
`19,504` typed path-opening bytes. The overhang is therefore `1,680` typed
bytes.

That means:

- removing the canonical `1,008` byte opening overhang is not enough under the
  worst-label policy;
- removing `1,401 / 1,680 = 83.3929%` of the worst-label path-opening overhang
  would beat the two-proof frontier;
- if a future layout brought the worst label all the way down to the compact
  path-opening profile, the modeled object would be `40,420` typed bytes,
  `280` bytes under the current frontier;
- the strict margin after the required reduction is only `279` bytes, so this
  is a narrow route, not a comfortable one.

The useful detail is the value/opening split. RMSNorm-input labels carry `392`
fewer direct value bytes than the compact selector, but lose that advantage to
FRI/trace opening material. If a real component layout can keep the value
advantage while reducing opening material, this route can still move the
frontier.

## Route Matrix

| route candidate | source variant | typed bytes | required reduction | path-opening overhang | required share | modeled full-removal size | policy usable |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| single best label | `label_probe_a` | `40,836` | `137` | `416` | `32.9327%` | `40,420` | no, cherry-pick |
| canonical overhang only | `rmsnorm_input_fused` | `41,428` | `729` | `1,008` | `72.3214%` | `40,420` | no, not worst-label sufficient |
| worst-label path opening to compact | `label_probe_b` | `42,100` | `1,401` | `1,680` | `83.3929%` | `40,420` | conditional |
| compact selector reference | `compact_selector` | `40,812` | `113` | `0` | `0%` | `40,812` | no, not RMSNorm semantic fusion |

## Claim Boundary

The checked claim is only:

> RMSNorm-input opening-layout remains a live exploratory route if, and only
> if, a future variant removes at least `1,401` typed bytes from the worst
> checked label while preserving source binding, the adapter equation, and
> value semantics.

Non-claims:

- not a two-proof frontier beat;
- not a proof-size win;
- not a NANOZK proof-size win;
- not a matched external zkML benchmark;
- not a new proof object;
- not timing evidence;
- not a full transformer block proof;
- not production-ready zkML.

## Evidence

- `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-opening-budget-route-2026-05.json`
- `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-opening-budget-route-2026-05.tsv`
- Source policy gate:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-label-policy-2026-05.json`
- Source sensitivity gate:
  `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-label-sensitivity-2026-05.json`
- Gate script:
  `scripts/zkai_native_attention_mlp_rmsnorm_opening_budget_route_gate.py`
- Tests:
  `scripts/tests/test_zkai_native_attention_mlp_rmsnorm_opening_budget_route_gate.py`

The gate rejects `19 / 19` mutation cases covering frontier overclaim, NANOZK
overclaim, workload-match overclaim, source digest and commitment drift,
required-reduction drift, path-overhang drift, required-share drift, canonical
policy overclaim, modeled-margin drift, single-label promotion, value-saving
erasure, missing route candidates, decision/result/claim-boundary drift,
non-claim erasure, validation-command erasure, and payload-commitment drift.

## Reproduction

```sh
python3 scripts/zkai_native_attention_mlp_rmsnorm_opening_budget_route_gate.py --write-json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-opening-budget-route-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-opening-budget-route-2026-05.tsv
python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_opening_budget_route_gate
python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_label_policy_gate
python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_label_sensitivity_gate
git diff --check
just gate-fast
just gate
```

Recorded gate output:

```json
{"decision":"CONDITIONAL_GO_OPENING_OVERHANG_ATTACK_WITH_STRICT_WORST_LABEL_TARGET","full_removal_frontier_margin_bytes":280,"mutation_count":19,"mutations_rejected":19,"required_share_of_worst_label_path_opening_overhang":0.833929,"result":"WORST_LABEL_PATH_OPENING_OVERHANG_CAN_PAY_THE_1401_BYTE_POLICY_GAP_ONLY_IF_STRUCTURALLY_REMOVED","worst_label_path_opening_overhang_vs_compact_bytes":1680,"worst_label_required_reduction_to_beat_frontier_bytes":1401}
```

## Next Attack

The next implementation should try to build an actual opening-layout variant,
not another accounting-only argument:

- preserve the RMSNorm-input adapter equation;
- preserve source binding and the current value semantics;
- report the full label inventory;
- remove at least `1,401` worst-label typed bytes from FRI/trace opening
  material;
- reject any result that only wins under a favorable transcript label.

If that fails, the honest pivot is away from this opening-layout route and back
toward a different component boundary or a value-connected attention-derived
input route.
