# Native Block-Boundary Pivot Selector

Date: 2026-05-18

Issue: [#667](https://github.com/omarespejel/provable-transformer-vm/issues/667)

## Decision

`ATTACK_NEXT_LARGER_NATIVE_BLOCK_BOUNDARY`

Result:

`PIVOT_TO_LARGER_NATIVE_BOUNDARY_NOT_LOCAL_REORDER_OR_CURRENT_GKR`

This is a selector gate, not a new proof-size win. It turns the latest positive
and negative evidence into the next execution route.

## Checked State

| route | status | typed bytes | delta vs `40,700` frontier | why |
| --- | --- | ---: | ---: | --- |
| larger native block boundary | `ATTACK_NEXT` | `41,932` | `+1,232` | strict native adapter object is close enough to attack through broader boundary amortization |
| sub-kilobyte adapter reorder | `PARK_NOW` | `42,724` | `+2,024` | post-tail canonical matches the adjacent bad-label record stream |
| current GKR projection sidecar | `PARK_NOW` | `70,138` | `+29,438` | width-preserving GKR preflight is heavier than local Stwo dense baselines |
| compact-preprocessed public rows | `USE_SELECTIVELY` | `6,264` | `-34,436` | useful scoped mechanism, not a full d128 block proof |
| comparison claim guardrail | `GUARDRAIL` | | | no matched external proof-size rows today |

## Human Meaning

The next serious attack is not another local fixed-column reorder. The compact
selector is only `112` typed bytes above the two-proof frontier, but the
post-tail and label probes move opening material by more than that. A favorable
sub-kilobyte label is not robust enough for a paper claim.

The stronger signal is larger-boundary fusion:

- six-component d128 RMSNorm-to-residual MLP fused proof: `24,832` typed bytes;
- six separate native MLP-side objects: `56,976` typed bytes;
- saving: `32,144` typed bytes;
- saving share: `56.4167%`.

That is structural. It comes from shared commitment/opening/FRI/decommitment
plumbing, not from a tiny label accident.

## What This Selects

The next implementation route should build a larger source-bound native
boundary or amortization gate before spending more effort on local reorder
variants. The target is still strict:

- preserve native adapter value binding;
- preserve source and statement commitments;
- report worst-label or label-stable accounting;
- compare first against the `40,700` typed-byte local two-proof frontier;
- do not compare to NANOZK until workload and object class are matched.

## Non-Claims

- Not a NANOZK proof-size win.
- Not a matched NANOZK benchmark.
- Not a full transformer block proof.
- Not a timing result.
- Not evidence that GKR replaces Stwo.
- Not production zkML.

## Evidence

- Gate JSON:
  `docs/engineering/evidence/zkai-native-block-boundary-pivot-selector-2026-05.json`
- Gate TSV:
  `docs/engineering/evidence/zkai-native-block-boundary-pivot-selector-2026-05.tsv`
- Gate:
  `scripts/zkai_native_block_boundary_pivot_selector_gate.py`
- Tests:
  `scripts/tests/test_zkai_native_block_boundary_pivot_selector_gate.py`

The gate rejects `15 / 15` mutations covering NANOZK comparability, route
selection drift, route-rationale drift, next-gate drift, GKR unparking,
compact-gap erasure, post-tail overclaim, MLP fusion erasure,
compact-preprocessed overclaim, adapter-binding demotion, source-descriptor
drift, non-claim erasure, validation-command drift, source-path drift, and
payload commitment drift.

## Reproduce

```bash
python3 scripts/zkai_native_block_boundary_pivot_selector_gate.py --write-json docs/engineering/evidence/zkai-native-block-boundary-pivot-selector-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-block-boundary-pivot-selector-2026-05.tsv
python3 -m py_compile scripts/zkai_native_block_boundary_pivot_selector_gate.py scripts/tests/test_zkai_native_block_boundary_pivot_selector_gate.py
python3 -m unittest scripts.tests.test_zkai_native_block_boundary_pivot_selector_gate
python3 scripts/research_issue_lint.py --repo-root .
git diff --check
just gate-fast
just gate
```
