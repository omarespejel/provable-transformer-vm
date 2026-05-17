# zkAI GKR Dense Sidecar Baseline - 2026-05-17

Issue: `#650`

Status: `GO_GKR_SIDECAR_BASELINE_NO_GO_MATCHED_D128_DENSE_LAYER_COMPARISON`.

This gate records the first bounded GKR/Expander/JSTprove sidecar baseline for
the transformer-block comparison lane. It is deliberately conservative: it says
where the GKR-style route looks worth exploring, and it also records exactly
why it is not a matched `d128` transformer-block benchmark yet.

## Result

The result is a sidecar/baseline GO, not a Stwo replacement and not a NANOZK
comparison.

Important numbers:

- local Stwo dense substitute: `22,576` typed bytes
- JSTprove/Remainder tiny `Gemm`: `11,645` proof bytes
- tiny `Gemm` ratio versus local Stwo dense typed bytes: `0.515813x`
- JSTprove/Remainder tiny `Gemm + residual_add`: `56,054` proof bytes
- residual-add ratio versus local Stwo dense typed bytes: `2.482902x`
- JSTprove/Remainder tiny `Gemm + layernorm`: `52,080` proof bytes
- layernorm ratio versus local Stwo dense typed bytes: `2.306875x`
- local GKR GO fixture count: `5`
- local GKR NO-GO fixture count: `3`
- comparison rows: `9`
- mutation gate: `6 / 6` rejected

Human meaning: GKR-style tooling is interesting for tiny layered dense
arithmetic, especially projection-shaped fixtures. But when residual or
normalization-like behavior is included in the checked JSTprove fixtures, the
proof bytes already exceed the current local Stwo dense substitute. We should
keep GKR/Expander as a sidecar and baseline lane, not pivot away from Stwo.

## Comparison Rows

| row | system | status | primary value | boundary |
| --- | --- | --- | ---: | --- |
| local Stwo dense substitute | Stwo/STARK | local frontier | `22,576` typed bytes | local typed accounting |
| tiny Gemm | JSTprove/Remainder-GKR | GO | `11,645` proof bytes | tiny projection only |
| tiny Gemm + residual add | JSTprove/Remainder-GKR | GO | `56,054` proof bytes | not d128 MLP |
| tiny Gemm + layernorm | JSTprove/Remainder-GKR | GO | `52,080` proof bytes | not our RMSNorm substitute |
| tiny Gemm + batchnorm | JSTprove/Remainder-GKR | GO | `95,105` proof bytes | normalization-like only |
| tiny Gemm + ReLU | JSTprove/Remainder-GKR | NO-GO | `range_check_capacity` | activation blocker |
| tiny Gemm + Softmax | JSTprove/Remainder-GKR | NO-GO | `unconstrained_backend_op` | nonlinear blocker |
| literal MatMul + residual add | JSTprove/Remainder-GKR | NO-GO | `unsupported_witness_op` | witness/op blocker |
| statement envelope binding | JSTprove/Remainder-GKR | GO | `13` mutations rejected | binding only |

## Claim Boundary

Allowed:

- GKR/Expander/JSTprove is a useful exploratory sidecar and baseline lane.
- Tiny projection-shaped GKR fixtures can be compact enough to be worth
  attacking further.
- The checked local evidence does not support a matched `d128` dense-layer
  comparison.
- The statement-envelope adapter is useful for typed boundaries, not proof-size
  comparison.

Forbidden:

- GKR replaces Stwo.
- This is a NANOZK proof-size win.
- This is a Jolt or Atlas benchmark win.
- This is a matched `d128` transformer-block proof.
- The tiny `Gemm` proof row is comparable to the local Stwo dense substitute.
- The Softmax/ReLU/MatMul blockers are solved.

## Primary Context

The exploration is motivated by layered-circuit and sumcheck/GKR systems:

- Polyhedra Expander GKR docs:
  `https://docs.polyhedra.network/expander/prover_internals/gkr`
- PolyhedraZK/Expander:
  `https://github.com/PolyhedraZK/Expander`
- JSTprove/Remainder paper context:
  `https://arxiv.org/abs/2510.21024`

Those sources are context for why the lane is plausible. They are not local
reproduction of a matched transformer-block benchmark.

## Recommendation

Keep Stwo as the main proof object and use GKR/Expander/JSTprove as one of two
sidecar comparison lanes:

1. dense layered arithmetic sidecar, where tiny projection fixtures are the
   first lead;
2. typed statement-boundary adapter, where proof objects from different
   systems can be compared without pretending they are the same object class.

The next falsifying experiment should be a matched dense-layer fixture: same
width policy, same operations, same statement boundary, and explicit accounting
for setup, verifier key, proof bytes, and statement envelope.

## Non-Claims

- Not a NANOZK proof-size win.
- Not a Jolt or Atlas benchmark win.
- Not a matched `d128` transformer-block proof.
- Not a full transformer proof.
- Not a claim that GKR replaces Stwo.
- Not a claim that JSTprove proves our exact RMSNorm/SwiGLU component.
- Not timing evidence beyond previously recorded local fixture timings.
- Not model-faithful accuracy evidence.

## Evidence

- JSON:
  `docs/engineering/evidence/zkai-gkr-dense-sidecar-baseline-2026-05.json`
- TSV:
  `docs/engineering/evidence/zkai-gkr-dense-sidecar-baseline-2026-05.tsv`
- Gate:
  `scripts/zkai_gkr_dense_sidecar_baseline_gate.py`
- Tests:
  `scripts/tests/test_zkai_gkr_dense_sidecar_baseline_gate.py`

Source artifacts:

- `docs/engineering/evidence/zkai-minimal-transformer-block-benchmark-2026-05.json`
- `docs/engineering/evidence/zkai-jstprove-shape-probe-2026-05.json`
- `docs/engineering/evidence/zkai-jstprove-statement-envelope-benchmark-2026-05.json`

## Validation

```bash
python3 scripts/zkai_gkr_dense_sidecar_baseline_gate.py --write-json docs/engineering/evidence/zkai-gkr-dense-sidecar-baseline-2026-05.json --write-tsv docs/engineering/evidence/zkai-gkr-dense-sidecar-baseline-2026-05.tsv
python3 -m py_compile scripts/zkai_gkr_dense_sidecar_baseline_gate.py scripts/tests/test_zkai_gkr_dense_sidecar_baseline_gate.py
python3 -m unittest scripts.tests.test_zkai_gkr_dense_sidecar_baseline_gate
python3 scripts/research_issue_lint.py --repo-root .
git diff --check
just gate-fast
just gate
```
