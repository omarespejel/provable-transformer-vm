# Larger Native Boundary Source Compatibility

Date: 2026-05-18

Issue: [#673](https://github.com/omarespejel/provable-transformer-vm/issues/673)

Follow-up: [#674](https://github.com/omarespejel/provable-transformer-vm/issues/674)

## Decision

`NO_GO_CURRENT_D128_MLP_INPUT_NOT_VALUE_COMPATIBLE_WITH_TWO_HEAD_SEQ32_ATTENTION`

Result:

`REGENERATE_SEQ32_DERIVED_D128_MLP_SURFACE_BEFORE_NATIVE_PROOF_OBJECT`

This is a correctness gate. It prevents the larger-boundary selector result
from being promoted into a native proof-object implementation before the source
values match.

## Checked Compatibility

| source | attention output rows | flat cells | adapter matches | adapter mismatches |
| --- | ---: | ---: | ---: | ---: |
| d8 control | `8` | `64` | `128` | `0` |
| two-head seq32 candidate | `64` | `512` | `15` | `113` |

The existing attention-derived d128 RMSNorm/MLP input is value-compatible with
the d8 control. It is not value-compatible with the selected two-head seq32
attention candidate: `113 / 128` adapter rows mismatch.

## Why This Matters

The previous selector found the right larger attention pressure surface:
two-head seq32 has `1,184` lookup claims and only `22,916` local typed attention
bytes. That is still interesting. But the current d128 MLP surface was derived
from the d8 attention output vector. Combining the seq32 attention proof with
that d8-derived MLP input would mix two different value sources.

So the correct next step is not to force a proof. The correct next step is to
regenerate a seq32-derived d128 RMSNorm/MLP surface, then retry the larger
native proof object against a fresh matched frontier.

## Current Frontier Boundary

The selector's matched local frontier remains:

- seq32 attention typed bytes: `22,916`
- d128 MLP typed bytes: `22,576`
- matched two-proof frontier: `45,492` typed bytes

But this frontier is not yet implementable as a sound value-bound native object
with the current MLP input. The `45,492` number remains a target, not a proof
object.

## Next Experiment

Regenerate the d128 RMSNorm/MLP input from the two-head seq32 attention output
vector using an explicit adapter policy. The next GO gate should require:

- `0 / 128` seq32 adapter mismatches;
- regenerated source commitments;
- regenerated native d128 RMSNorm/MLP fused proof input and envelope;
- fresh binary/typed accounting;
- mutation rejection for d8 fallback and source-digest drift.

## Non-Claims

- Not a native larger-boundary proof object.
- Not proof-size savings.
- Not a NANOZK proof-size win.
- Not a matched external zkML benchmark.
- Not a full transformer block proof.
- Not permission to ignore adapter value binding.
- Not a reason to promote the seq32 selector to an implementation result.

## Evidence

- Gate JSON:
  `docs/engineering/evidence/zkai-larger-native-boundary-source-compatibility-2026-05.json`
- Gate TSV:
  `docs/engineering/evidence/zkai-larger-native-boundary-source-compatibility-2026-05.tsv`
- Gate:
  `scripts/zkai_larger_native_boundary_source_compatibility_gate.py`
- Tests:
  `scripts/tests/test_zkai_larger_native_boundary_source_compatibility_gate.py`

The gate rejects `10 / 10` mutations covering decision promotion, seq32
mismatch drift, d8 control drift, matched-frontier drift, selected-route drift,
native proof-object overclaim, adapter-binding overclaim, non-claim removal,
source-commitment drift, and payload-commitment drift.

## Reproduce

```bash
python3 scripts/zkai_larger_native_boundary_source_compatibility_gate.py --write-json docs/engineering/evidence/zkai-larger-native-boundary-source-compatibility-2026-05.json --write-tsv docs/engineering/evidence/zkai-larger-native-boundary-source-compatibility-2026-05.tsv
python3 -m py_compile scripts/zkai_larger_native_boundary_source_compatibility_gate.py scripts/tests/test_zkai_larger_native_boundary_source_compatibility_gate.py
python3 -m unittest scripts.tests.test_zkai_larger_native_boundary_source_compatibility_gate
python3 scripts/research_issue_lint.py --repo-root .
python3 scripts/paper/paper_preflight.py --repo-root .
git diff --check
just gate-fast
just gate
```
