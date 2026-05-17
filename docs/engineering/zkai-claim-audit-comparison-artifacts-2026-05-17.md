# zkML Claim-Audit Comparison Artifacts Gate

Date: 2026-05-17

Issue: https://github.com/omarespejel/provable-transformer-vm/issues/653

## Result

Decision: `GO_ADVERSARIAL_ZKML_CLAIM_AUDIT_NO_GO_UNTYPED_COMPARISONS`

Result: `COMPARISON_MATRIX_REJECTS_OBJECT_CLASS_AND_REPRODUCTION_OVERCLAIMS`

The gate audits the current zkML comparison surface before it becomes paper
language. It normalizes rows from native Stwo artifacts, compact Tablero
statement boundaries, paper-reported NANOZK context, local GKR/JSTprove
fixtures, Jolt Atlas source rows, and RMSNorm opening-layout policy artifacts.

Checked inventory:

- audit rows: `13`
- object classes: `10`
- proof-size-comparable rows: `0`
- adversarial mutations rejected: `13 / 13`
- local Stwo two-proof frontier: `40,700` typed bytes
- NANOZK paper-reported context row: `6,900` bytes
- GKR tiny `Gemm` sidecar: `11,645` proof bytes
- GKR tiny residual-add shape: `56,054` proof bytes
- GKR tiny LayerNorm-like shape: `52,080` proof bytes
- worst-label RMSNorm opening-layout required reduction: `1,401` typed bytes

Human meaning: the repo now says the uncomfortable thing explicitly. Current
Stwo evidence is much heavier than the NANOZK paper-reported d128 row, and the
GKR sidecar is only promising on a tiny linear fixture. None of the current
cross-system rows are matched enough to be called proof-size-comparable.

## What This Guards

The gate rejects:

- compact statement artifacts promoted to native block proofs;
- paper-reported NANOZK rows marked as local reproductions;
- Jolt Atlas source rows promoted to proof-size comparisons without a local run;
- GKR tiny fixtures promoted to matched d128 transformer-layer comparisons;
- rows without explicit object classes;
- timing rows without timing policy;
- favorable-label RMSNorm metrics replacing the worst-label policy;
- required NANOZK, Jolt Atlas, GKR, and compact-statement non-claims being
  removed;
- external fixtures marked as native proof equivalents;
- source-artifact digest drift.

## Claim Boundary

This is not a performance breakthrough. It is a correctness and claim-boundary
gate for the research program.

The current honest state is:

- Stwo has real local proof objects and useful fusion evidence, but the current
  two-proof frontier is still `40,700` typed bytes.
- NANOZK has a paper-reported `6,900` byte d128 row, but we have not locally
  reproduced it and the object/workload class is not matched.
- GKR/JSTprove has one useful tiny `Gemm` sidecar signal at `11,645` proof
  bytes, but residual and normalization-like tiny shapes are already `52 KB+`.
- Tablero is useful as a typed statement boundary and anti-confusion layer; it
  is not an external verifier and not a proof-size win by itself.

## Artifacts

- `docs/engineering/evidence/zkai-claim-audit-comparison-artifacts-2026-05.json`
- `docs/engineering/evidence/zkai-claim-audit-comparison-artifacts-2026-05.tsv`
- `scripts/zkai_claim_audit_comparison_artifacts_gate.py`
- `scripts/tests/test_zkai_claim_audit_comparison_artifacts_gate.py`

## Validation

Local-only validation:

```bash
python3 scripts/zkai_claim_audit_comparison_artifacts_gate.py --write-json docs/engineering/evidence/zkai-claim-audit-comparison-artifacts-2026-05.json --write-tsv docs/engineering/evidence/zkai-claim-audit-comparison-artifacts-2026-05.tsv
python3 -m py_compile scripts/zkai_claim_audit_comparison_artifacts_gate.py scripts/tests/test_zkai_claim_audit_comparison_artifacts_gate.py
python3 -m unittest scripts.tests.test_zkai_claim_audit_comparison_artifacts_gate
python3 scripts/research_issue_lint.py --repo-root .
git diff --check
just gate-fast
just gate
```

GitHub Actions are not part of the normal validation loop.
