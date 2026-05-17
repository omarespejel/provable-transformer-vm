# Hybrid Proof-Pressure Selector

Date: 2026-05-17

Issue: [#661](https://github.com/omarespejel/provable-transformer-vm/issues/661)

Decision: `GO_HYBRID_PROOF_PRESSURE_SELECTOR_NO_GO_MATCHED_EXTERNAL_COMPARISON`

Result: `ROUTE_SELECTOR_IDENTIFIES_DENSE_LINEAR_ATTACK_AND_REJECTS_FALSE_COMPARABILITY`

## What This Shows

This is a selector gate, not a performance claim.

The current honest comparison state is still heavy:

- local Stwo two-proof frontier: `40,700` typed bytes;
- NANOZK paper-reported context row: `6,900` bytes;
- gap to NANOZK paper row: `33,800` bytes;
- claim-audit proof-size-comparable rows: `0`.

The useful result is that the next attacks are no longer vague.

Checked selector output:

- selector rows: `8`
- attack-next routes: `2`
- no-go-now routes: `2`
- proof-size-comparable rows: `0`
- overclaim mutations rejected: `12 / 12`

## Good Signal

The GKR tiny `Gemm` row remains the only external sidecar route worth attacking
next:

- GKR tiny `Gemm`: `11,645` proof bytes;
- ratio vs local Stwo dense substitute `22,576`: `0.515813x`;
- ratio vs local Stwo two-proof frontier `40,700`: `0.286118x`;
- ratio vs NANOZK context row `6,900`: `1.687681x`.

This is not comparable to NANOZK and not a d128 transformer-block proof. But it
is a real route selector signal: dense linear/projection work is worth scaling
and binding through Tablero.

## Bad Signal

GKR residual and normalization-like tiny routes are current NO-GOs:

- GKR residual-add shape: `56,054` proof bytes, `1.377248x` the local Stwo
  frontier and `8.123768x` the NANOZK context row;
- GKR LayerNorm-like shape: `52,080` proof bytes, `1.279607x` the local Stwo
  frontier and `7.547826x` the NANOZK context row.

Do not spend the next PR trying to move residual or RMSNorm to GKR unless dense
linear scaling first produces a matched d128 route.

## Selected Next Actions

`ATTACK_NEXT_UNMATCHED_DENSE_LINEAR_SCALING`

Scale the GKR `Gemm` fixture toward a d128 projection shape and bind it with a
Tablero statement boundary. This tests whether the only good external sidecar
signal survives a less toy shape.

`ATTACK_NEXT_NATIVE_BLOCK_OBJECT`

Construct or spike the native d128 block proof object before making external
proof-size claims. Without this, every comparison remains object-class
ambiguous.

`KEEP_AS_GUARDRAIL_NOT_PROOF_SIZE_ROW`

Keep Tablero as the boundary mechanism that prevents statement artifacts,
receipts, and proof objects from being compared as if they were the same thing.

## Rejected Overclaims

The gate rejects:

- promoting tiny GKR rows to matched d128 native routes;
- promoting statement-boundary artifacts to proof-size byte ratios;
- marking any route proof-size-comparable while the claim audit has `0`
  comparable rows;
- promoting the NANOZK paper row to a matched/local workload;
- removing per-row non-claims;
- removing all `ATTACK_NEXT` routes;
- removing all `NO_GO_NOW` routes;
- drifting the claim-audit comparable-row count;
- drifting the Stwo frontier;
- drifting source artifact descriptors;
- drifting the payload commitment.

## Reproduction

```bash
python3 scripts/zkai_hybrid_proof_pressure_selector_gate.py \
  --write-json docs/engineering/evidence/zkai-hybrid-proof-pressure-selector-2026-05.json \
  --write-tsv docs/engineering/evidence/zkai-hybrid-proof-pressure-selector-2026-05.tsv

python3 -m py_compile \
  scripts/zkai_hybrid_proof_pressure_selector_gate.py \
  scripts/tests/test_zkai_hybrid_proof_pressure_selector_gate.py

python3 -m unittest scripts.tests.test_zkai_hybrid_proof_pressure_selector_gate
```

Timing mode: validation-only; no proof generation or benchmark timing claim.

Full local readiness should also include:

```bash
python3 scripts/research_issue_lint.py --repo-root .
git diff --check
just gate-fast
just gate
```

## Non-Claims

- not a NANOZK proof-size win;
- not a matched local reproduction of NANOZK;
- not evidence that GKR replaces STARKs;
- not a full transformer block proof;
- not a timing claim;
- not production zkML.
