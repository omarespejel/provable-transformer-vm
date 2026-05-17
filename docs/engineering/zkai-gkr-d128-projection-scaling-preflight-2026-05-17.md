# GKR d128 Projection Scaling Preflight

Date: 2026-05-17

Issue: [#663](https://github.com/omarespejel/provable-transformer-vm/issues/663)

Decision: `NO_GO_NOW_D128_PROJECTION_SCALING`

Result: `TINY_GEMM_SIGNAL_DOES_NOT_SURVIVE_WIDTH_PRESERVING_PREFLIGHT_KEEP_GKR_AS_BASELINE`

## What This Shows

This gate tests the strongest GKR-sidecar lead from the hybrid proof-pressure
selector before spending a PR on a `d128` projection implementation.

The prior selector found a tempting tiny `Gemm` signal:

- JSTprove/Remainder tiny scalar `Gemm`: `11,645` proof bytes
  from `zkai-jstprove-shape-probe-2026-05.json`
- local Stwo `d128` gate/value projection baseline: `16,360` typed bytes
  from `zkai-d128-gate-value-compact-preprocessed-gate-2026-05.json`
- tiny scalar ratio versus Stwo gate/value baseline: `0.711797x`

That signal does not survive the current width-preserving preflight:

- width-preserving `Gemm` dim `2`: `71,040` proof bytes
  from `zkai-jstprove-shape-probe-2026-05.json`
- width-preserving `Gemm` dim `4`: `70,138` proof bytes
  from `zkai-jstprove-shape-probe-2026-05.json`
- smallest checked width-preserving row: `70,138` proof bytes
- ratio versus local Stwo gate/value baseline: `4.287164x`
- ratio versus local Stwo dense substitute: `3.106751x`
- ratio versus NANOZK paper context row: `10.164928x`, using the
  `6,900` byte context row pinned in
  `zkai-minimal-transformer-block-benchmark-2026-05.json`

Human meaning: tiny GKR projection-shaped fixtures are still worth tracking, but
the checked JSTprove/Remainder width-preserving route is not currently the next
best attack for a `d128` projection. Keep it as a baseline and comparison lane;
do not pivot the main architecture away from Stwo on this evidence.

## Claim Boundary

Allowed:

- The tiny scalar GKR `Gemm` row is a useful exploratory signal.
- The current width-preserving JSTprove/Remainder preflight is a NO-GO for a
  rushed `d128` projection PR.
- The next GKR step should be a live dim `8/16/32` sweep or a stronger GKR
  backend before attempting a `d128` sidecar.
- Stwo remains the main native proof-object route for the current zkML lane.

Forbidden:

- This is not a NANOZK proof-size win.
- This is not a matched `d128` JSTprove projection proof.
- This is not a claim that GKR replaces Stwo.
- This is not a full transformer block proof.
- This is not a proof-size-comparable cross-system benchmark.
- This is not production zkML.

## Why The NO-GO Is Useful

The selector did its job: it identified a plausible lead, and this preflight
bounded it before we built the wrong thing.

The gap is not subtle. The smallest checked width-preserving GKR row is already
`4.287164x` the local Stwo gate/value baseline while still only reaching dim
`4`. The target width is `128`, leaving a `32x` width gap from the largest
checked GKR dimension to the target.

This does not kill GKR, Hyrax, Expander, or JSTprove as research inputs. It says
their current local evidence should stay in the baseline/sidecar lane until a
new sweep shows better scaling.

## Selected Next Actions

`ATTACK_NEXT_NATIVE_BLOCK_OBJECT`

The main breakthrough blocker remains the native `d128` block proof object. The
current Stwo route has checked components and boundaries, but not yet the
matched block object needed for a clean NANOZK-style comparison.

`OPTIONAL_LIVE_GKR_DIM8_16_32_SWEEP`

Only spend another GKR PR if the local toolchain can generate live dim `8`,
`16`, and `32` width-preserving rows. Without that sweep, the current checked
dim `2/4` rows are enough to keep the JSTprove `d128` projection route in
NO-GO status.

`KEEP_TABLERO_AS_CLAIM_BINDING`

Tablero remains useful as a typed boundary and claim-binding guardrail. It is
not a proof-size row, so the preflight emits `NA` ratios for non-byte
statement-boundary metrics.

## Rejected Overclaims

The gate rejects:

- promoting the tiny scalar `Gemm` row to a matched workload;
- marking width-preserving GKR rows as proof-size comparable;
- smuggling smaller width-preserving byte values into the output;
- changing the recommendation from NO-GO to attack-now;
- removing global non-claims;
- removing row-specific non-claims;
- inserting malformed row non-claim entries;
- drifting source artifact digests;
- removing the explicit tiny-fixture `not d128` non-claim.

## Evidence

- JSON:
  `docs/engineering/evidence/zkai-gkr-d128-projection-scaling-preflight-2026-05.json`
- TSV:
  `docs/engineering/evidence/zkai-gkr-d128-projection-scaling-preflight-2026-05.tsv`
- Gate:
  `scripts/zkai_gkr_d128_projection_scaling_preflight_gate.py`
- Tests:
  `scripts/tests/test_zkai_gkr_d128_projection_scaling_preflight_gate.py`

Source artifacts:

- `docs/engineering/evidence/zkai-jstprove-shape-probe-2026-05.json`
- `docs/engineering/evidence/zkai-d128-gate-value-compact-preprocessed-gate-2026-05.json`
- `docs/engineering/evidence/zkai-minimal-transformer-block-benchmark-2026-05.json`
- `docs/engineering/evidence/zkai-hybrid-proof-pressure-selector-2026-05.json`
- `docs/engineering/evidence/zkai-tablero-hybrid-zkml-boundary-2026-05.json`

## Validation

```bash
python3 scripts/zkai_gkr_d128_projection_scaling_preflight_gate.py \
  --write-json docs/engineering/evidence/zkai-gkr-d128-projection-scaling-preflight-2026-05.json \
  --write-tsv docs/engineering/evidence/zkai-gkr-d128-projection-scaling-preflight-2026-05.tsv

python3 -m py_compile \
  scripts/zkai_gkr_d128_projection_scaling_preflight_gate.py \
  scripts/tests/test_zkai_gkr_d128_projection_scaling_preflight_gate.py

python3 -m unittest scripts.tests.test_zkai_gkr_d128_projection_scaling_preflight_gate
python3 scripts/research_issue_lint.py --repo-root .
git diff --check
just gate-fast
just gate
```

Timing mode: validation-only; no benchmark timing claim.
