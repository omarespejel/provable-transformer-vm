# Larger Native Block-Boundary Amortization Budget

Date: 2026-05-18

Issue: [#669](https://github.com/omarespejel/provable-transformer-vm/issues/669)

## Decision

`GO_ATTACK_LARGER_NATIVE_BOUNDARY_LOCAL_FRONTIER_BUDGET`

Result:

`LOCAL_FRONTIER_REQUIRES_1233_TYPED_BYTES_OR_3_8359_PERCENT_OF_MLP_FUSION_SAVING_NANOZK_REMAINS_BLOCKED`

This is a budget gate, not a new proof object. It tells us whether the route
selected by the pivot selector is worth implementing next.

## Checked Budget

| row | status | current bytes | reference bytes | beat reference | share of MLP saving |
| --- | --- | ---: | ---: | ---: | ---: |
| strict native single vs two-proof frontier | `ATTACK_NEXT_LOCAL_FRONTIER` | `41,932` | `40,700` | `1,233` | `3.8359%` |
| compact selector vs two-proof frontier | `PARK_LABEL_FRAGILE` | `40,812` | `40,700` | `113` | `0.3515%` |
| post-tail worst label vs two-proof frontier | `PARK_LOCAL_REORDER` | `42,724` | `40,700` | `2,025` | `6.2998%` |
| GKR width-preserving vs two-proof frontier | `PARK_CURRENT_GKR` | `70,138` | `40,700` | `29,439` | `91.5847%` |
| strict native single vs NANOZK context | `BLOCKED_NOT_MATCHED` | `41,932` | `6,900` | `35,033` | `108.9877%` |
| two-proof frontier vs NANOZK context | `CONTEXT_ONLY_NOT_MATCHED` | `40,700` | `6,900` | `33,801` | `105.1549%` |
| compact-preprocessed vs NANOZK context | `MECHANISM_LEAD_NOT_COMPARABLE` | `6,264` | `6,900` | `0` | `0.0000%` |

The positive local signal is sharp: the strict native single object is only
`1,232` typed bytes above the current `40,700` typed-byte two-proof frontier.
To beat that frontier by one byte, the next larger native boundary has to
recover `1,233` typed bytes. That is only `3.8359%` of the checked
six-component MLP-side fusion saving of `32,144` typed bytes.

A simple model shows the scale. If only `4%` of the observed MLP-side fusion
saving transferred into the larger attention-to-MLP boundary, the modeled
object would be `40,646` typed bytes, `54` bytes below the current frontier.
This is not evidence of a proof-size win; it is the reason the implementation
attack is worth one bounded PR.

## NANOZK Guardrail

The same gate keeps the external comparison honest. The strict native single
object would need to remove `35,033` typed bytes to beat the paper-reported
`6,900` byte NANOZK context row. That is `108.9877%` of the entire observed
MLP-side fusion saving, and the workload/object class is still not matched.

So the next result can be interesting if it beats the local frontier, but it
must not be described as a NANOZK proof-size win.

## Next Experiment

Build the next source-bound native boundary only if it explicitly targets
shared opening, FRI, and trace-decommitment amortization. Kill or narrow the
route if the new object cannot recover at least `1,233` typed bytes without
using compact public-row artifacts as full-block proof rows.

The next implementation should preserve:

- native adapter value binding;
- source and statement commitments;
- local typed proof accounting;
- NANOZK non-comparability guardrails;
- local validation and mutation rejection.

## Non-Claims

- Not a NANOZK proof-size win.
- Not a matched NANOZK benchmark.
- Not a full transformer block proof.
- Not a new native proof object.
- Not timing evidence.
- Not evidence that GKR replaces Stwo.
- Not production zkML.

## Evidence

- Gate JSON:
  `docs/engineering/evidence/zkai-larger-native-block-boundary-amortization-budget-2026-05.json`
- Gate TSV:
  `docs/engineering/evidence/zkai-larger-native-block-boundary-amortization-budget-2026-05.tsv`
- Gate:
  `scripts/zkai_larger_native_block_boundary_amortization_budget_gate.py`
- Tests:
  `scripts/tests/test_zkai_larger_native_block_boundary_amortization_budget_gate.py`

The gate rejects `14 / 14` mutations covering NANOZK comparability, selected
route drift, local-frontier gap erasure, four-percent projection erasure, MLP
saving drift, NANOZK gap erasure, compact-preprocessed promotion, GKR
unparking, interpretation overclaim, source-descriptor drift, non-claim
erasure, non-claim addition, validation-command drift, and payload commitment
drift.

## Reproduce

```bash
python3 scripts/zkai_larger_native_block_boundary_amortization_budget_gate.py --write-json docs/engineering/evidence/zkai-larger-native-block-boundary-amortization-budget-2026-05.json --write-tsv docs/engineering/evidence/zkai-larger-native-block-boundary-amortization-budget-2026-05.tsv
python3 -m py_compile scripts/zkai_larger_native_block_boundary_amortization_budget_gate.py scripts/tests/test_zkai_larger_native_block_boundary_amortization_budget_gate.py
python3 -m unittest scripts.tests.test_zkai_larger_native_block_boundary_amortization_budget_gate
python3 scripts/research_issue_lint.py --repo-root .
python3 scripts/paper/paper_preflight.py --repo-root .
git diff --check
just gate-fast
just gate
```
