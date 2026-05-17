# zkAI Tablero Hybrid zkML Boundary - 2026-05-17

Issue: `#652`

Status: `GO_TABLERO_TYPED_BOUNDARIES_FOR_HYBRID_ZKML_OBJECTS`.

This gate defines a typed Tablero boundary for the hybrid zkML research lane.
It is not a new proof system and not a recursive composition claim. Its job is
more basic and more important for correctness: every proof-like object must
carry enough typed statement metadata that proof validity cannot be mistaken
for statement validity.

## Result

The gate records `5` typed boundary examples across `5` object classes and
rejects `10 / 10` mutation attacks.

Boundary examples:

- local Stwo two-proof frontier: `40,700` typed bytes
- compact statement-chain boundary: `199,553` statement rows
- JSTprove/Remainder statement envelope: `13 / 13` relabeling mutations rejected
- GKR tiny `Gemm` sidecar fixture: `11,645` proof bytes
- Jolt Atlas self-attention source row: command available, not locally reproduced

Human meaning: this is the schema layer that lets the paper say "proof-system
aware transformer architecture" without turning heterogeneity into an
overclaim. Stwo, GKR, statement receipts, and Atlas-source rows can sit in the
same research matrix only if each row declares object class, workload, source
status, approximation policy, verifier semantics, and proof-size policy.

## Typed Boundary Fields

Every boundary example must include:

- `statement_id`
- `statement_schema`
- `object_class`
- `proof_system`
- `backend`
- `backend_version`
- `workload`
- `source_status`
- `model_binding`
- `input_binding`
- `output_binding`
- `proof_object_binding`
- `approximation_policy`
- `quantization_policy`
- `verifier_semantics`
- `proof_size_policy`
- `timing_policy`
- `native_proof_equivalent`
- `non_claims`

Each binding object must include:

- `availability`
- `commitment`
- `source`
- `reason`

Unavailable external facts are allowed only when they are explicit typed
objects, not omitted fields. For example, the Atlas self-attention row records
that input/output/proof-object commitments are unavailable until local
reproduction. It does not pretend they exist.

## Claim Boundary

Allowed:

- Tablero can be the typed statement boundary between heterogeneous proof
  objects and source-reported comparison rows.
- A local native Stwo proof frontier can set `native_proof_equivalent = true`
  only when the row is local, uses the `Stwo/STARK` proof system, uses the
  `stwo-native` backend, and belongs to the explicit native-frontier allowlist.
- Compact statement artifacts, statement receipts, GKR sidecars, and Atlas
  source rows remain `native_proof_equivalent = false`.
- Unavailable external model/input/output/proof facts must be represented as
  explicit unavailable bindings.

Forbidden:

- A compact statement wrapper is a native block proof.
- Tablero verifies external proofs by itself.
- A statement receipt proves native verifier execution unless that verifier
  execution is actually proven.
- Atlas is locally reproduced.
- Atlas proof bytes exist before local reproduction or source-backed matched
  proof-byte reporting.
- External rows can be marked local checked without a local run.
- Unknown approximation policy can be used in a paper-facing boundary row.

## Mutation Gate

Rejected mutations:

- compact statement artifact promoted as native proof
- missing model binding
- erased approximation policy
- backend-version drift
- Atlas row marked local
- Atlas row marked with another local-prefixed source status
- native-equivalent row moved to a non-Stwo backend
- statement commitment drift
- unavailable binding field removed
- Atlas proof-size overclaim
- typed schema required-field removal
- global Tablero non-claim removal

This is the main hardening value: the gate does not just generate a schema; it
checks the ways we are most likely to fool ourselves.

## How This Fits The Research

The current strongest technical mechanism is still STARK-native fusion: shared
commitment/opening/decommitment plumbing can save proof bytes when the workload
is represented as one native proof object. The hybrid result here does not
replace that.

Instead, Tablero provides the boundary discipline needed for the next phase:

1. keep Stwo-native proof objects as proof objects;
2. keep compact statement artifacts as statement artifacts;
3. keep GKR sidecars as sidecars or baselines;
4. keep Jolt/Atlas rows as source context until reproduced;
5. compare only when object class, workload, source status, and policy match.

That is what makes proof-system-aware layer selection possible. A future
transformer block may choose Stwo-native proving for attention/lookup fusion,
GKR-style sidecars for repeated dense arithmetic, and source-backed Jolt/Atlas
rows as reproduction targets. Tablero is the typed boundary that keeps those
choices honest: selecting a proof path for a layer does not let a statement
artifact become a native proof object, does not let an external row become
local, and does not weaken statement validity by hiding unavailable
model/input/output/proof bindings.

## Non-Claims

- Not a recursive composition proof.
- Not a claim that Tablero verifies external proofs itself.
- Not a claim that a statement receipt proves underlying native verifier
  execution.
- Not a proof-size win over NANOZK.
- Not a proof-size win over Jolt Atlas.
- Not a local Jolt Atlas reproduction.
- Not a full transformer block proof.
- Not exact real-valued transformer arithmetic.

## Evidence

- JSON:
  `docs/engineering/evidence/zkai-tablero-hybrid-zkml-boundary-2026-05.json`
- TSV:
  `docs/engineering/evidence/zkai-tablero-hybrid-zkml-boundary-2026-05.tsv`
- Gate:
  `scripts/zkai_tablero_hybrid_zkml_boundary_gate.py`
- Tests:
  `scripts/tests/test_zkai_tablero_hybrid_zkml_boundary_gate.py`

Source artifacts:

- `docs/engineering/evidence/zkai-minimal-transformer-block-benchmark-2026-05.json`
- `docs/engineering/evidence/zkai-gkr-dense-sidecar-baseline-2026-05.json`
- `docs/engineering/evidence/zkai-jolt-atlas-lookup-tensor-comparison-2026-05.json`
- `docs/engineering/evidence/zkai-jstprove-statement-envelope-benchmark-2026-05.json`

## Validation

```bash
python3 scripts/zkai_tablero_hybrid_zkml_boundary_gate.py --write-json docs/engineering/evidence/zkai-tablero-hybrid-zkml-boundary-2026-05.json --write-tsv docs/engineering/evidence/zkai-tablero-hybrid-zkml-boundary-2026-05.tsv
python3 -m py_compile scripts/zkai_tablero_hybrid_zkml_boundary_gate.py scripts/tests/test_zkai_tablero_hybrid_zkml_boundary_gate.py
python3 -m unittest scripts.tests.test_zkai_tablero_hybrid_zkml_boundary_gate
python3 scripts/research_issue_lint.py --repo-root .
git diff --check
just gate-fast
just gate
```
