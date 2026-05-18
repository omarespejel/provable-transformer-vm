# Seq32-Derived d128 Native MLP Surface

Date: 2026-05-18

Issue: [#674](https://github.com/omarespejel/provable-transformer-vm/issues/674)

## Decision

`GO_SEQ32_DERIVED_D128_MLP_SURFACE_INPUTS_READY_FOR_NATIVE_PROOF`

Result:

`SEQ32_DERIVED_D128_MLP_SURFACE_REGENERATED_FROM_VALUE_COMPATIBLE_ATTENTION_OUTPUTS`

This resolves the correctness blocker from issue `#673`: the selected
two-head seq32 attention candidate no longer has to be paired with the old
d8-derived MLP input. The new d128 MLP surface is regenerated from the selected
seq32 attention output vector and validates with `0 / 128` adapter mismatches.

## Human Meaning

The previous larger-boundary path had a real problem. The best attention
surface was the two-head seq32 proof, but the MLP side still came from the d8
attention vector. That would have mixed two different value sources inside one
claimed transformer boundary.

This PR fixes that source mismatch. It does not yet prove attention plus MLP in
one native object. It gives the next native proof-object PR a value-compatible
MLP half.

## Checked Proof Accounting

| object | JSON proof bytes | local typed bytes |
| --- | ---: | ---: |
| fused seq32-derived d128 RMSNorm/MLP | `74,511` | `24,272` |
| six separate seq32-derived d128 MLP components | `181,194` | `54,336` |
| saving from MLP-side fusion | `106,683` | `30,064` |
| fused ratio | `0.411222x` | `0.446702x` |

The new MLP surface is slightly heavier than the old d8-derived MLP surface:
`24,272` typed bytes instead of `22,576`. That is expected because the source
values changed. The important point is that it is now value-correct.

The updated local two-proof target for the next larger boundary is:

| piece | local typed bytes | JSON proof bytes |
| --- | ---: | ---: |
| selected two-head seq32 fused attention | `22,916` | `66,327` |
| seq32-derived d128 RMSNorm/MLP fused proof | `24,272` | `74,511` |
| value-compatible two-proof frontier | `47,188` | `140,838` |

The old `45,492` typed-byte target was useful for selection, but it was based
on the old d8-derived MLP surface. The honest target after regenerating source
values is `47,188` typed bytes.

## Correctness Boundary

The checked surface now has:

- `0 / 128` seq32 adapter mismatches.
- Six regenerated seq32-derived MLP component input artifacts.
- Six separate native Stwo component proof envelopes that verify locally.
- One regenerated fused native Stwo RMSNorm/MLP proof envelope that verifies
  locally.
- Binary/typed proof accounting for the fused proof and all six component
  proofs.
- Gate-level rejection for d8 attention fallback, source-commitment drift,
  source-artifact digest drift, NANOZK overclaim drift, larger-boundary
  overclaim drift, and metric drift. The mutation inventory rejects `7 / 7`
  cases.

## Why This Matters For The Breakthrough Path

This is not the breakthrough result by itself. It is the cleanup needed before
the next breakthrough attempt can be honest.

The interesting architecture signal remains the same: proof-size savings are
coming from shared proof plumbing when adjacent transformer relations are fused
into one native STARK object. On this regenerated MLP side alone, fusing six
native components saves `30,064` typed bytes. The next question is whether any
of that amortization can transfer across the attention-to-MLP boundary without
breaking value binding or worsening opening geometry.

## Non-Claims

- Not a full transformer block proof.
- Not attention plus MLP in one native proof object.
- Not a NANOZK proof-size win.
- Not a matched external zkML benchmark.
- Not timing evidence.
- Not production-ready zkML.

## Evidence

- Gate JSON:
  `docs/engineering/evidence/zkai-seq32-derived-d128-native-mlp-surface-2026-05.json`
- Gate TSV:
  `docs/engineering/evidence/zkai-seq32-derived-d128-native-mlp-surface-2026-05.tsv`
- Fused proof envelope:
  `docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.envelope.json`
- Fused proof input:
  `docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json`
- Binary/typed accounting:
  `docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-binary-accounting-2026-05.json`
- Gate:
  `scripts/zkai_seq32_derived_d128_mlp_surface_gate.py`
- Tests:
  `scripts/tests/test_zkai_seq32_derived_d128_mlp_surface_gate.py`

## Reproduce

```bash
python3.10 scripts/zkai_seq32_derived_d128_mlp_surface_gate.py --write-inputs --write-json docs/engineering/evidence/zkai-seq32-derived-d128-native-mlp-surface-2026-05.json --write-tsv docs/engineering/evidence/zkai-seq32-derived-d128-native-mlp-surface-2026-05.tsv
python3.10 -m py_compile scripts/zkai_seq32_derived_d128_mlp_surface_gate.py scripts/tests/test_zkai_seq32_derived_d128_mlp_surface_gate.py
python3.10 -m unittest scripts.tests.test_zkai_seq32_derived_d128_mlp_surface_gate
cargo +nightly-2025-07-14 test --locked --features stwo-backend d128_native_rmsnorm_mlp_fused_proof --lib
python3 scripts/research_issue_lint.py --repo-root .
python3 scripts/paper/paper_preflight.py --repo-root .
git diff --check
just gate-fast
just gate
```
