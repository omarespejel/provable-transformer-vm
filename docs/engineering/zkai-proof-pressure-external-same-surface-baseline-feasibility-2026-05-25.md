# Proof-Pressure External Same-Surface Baseline Feasibility

Date: 2026-05-25

Issue: #749

## Question

Can the proof-pressure paper add one honest external baseline against the same
bounded attention surface, starting with EZKL and falling back to a zkVM receipt
if EZKL is not a clean match?

## Decision

`NARROW_GO_EZKL_EXPORT_PROBE_NEXT; NO_GO_DIRECT_SAME_SURFACE_BASELINE_TODAY`

The baseline is worth pursuing, but the paper should not add a same-surface
external row yet. The current public result is a native Stwo proof-boundary
experiment over bounded attention arithmetic plus Softmax-table membership and
LogUp sidecar or fused proof objects. A matched external row must preserve the
same public inputs, outputs, table policy, and statement boundary closely enough
that the comparison is meaningful.

EZKL is the best first candidate because it has a concrete ONNX-oriented proof
workflow and this repository already has an EZKL statement-envelope benchmark.
However, the existing EZKL artifact is an identity-model statement-binding
benchmark, not an attention proof-pressure baseline. A direct row would require
exporting a bounded attention kernel to ONNX, pinning integer or fixed-point
semantics, and accounting separately for proof bytes, verifier key bytes,
settings, SRS assumptions, and statement-envelope bytes.

The honest next step is therefore an EZKL export probe, not a paper claim.

Prior local evidence already warns against treating a vanilla ONNX export as a
same-statement proof path. The `d64` RMSNorm-SwiGLU external-adapter surface
probe recorded `NO-GO` for an exact vanilla external export because a floating
export would not bind the checked integer rounding, lookup, and commitment
semantics (`docs/engineering/zkai-d64-external-adapter-surface-probe-2026-05-01.md`).
The attention-surface probe proposed here is a different object, but it should
inherit the same fail-closed rule: if export changes the integer table policy or
public-output semantics, the row is not same-surface.

## Candidate Surface

Target the smallest surface that can still connect to the paper's claim:

1. **Probe surface:** bounded two-head attention with table-derived weights,
   public input rows, public output rows, and explicit table policy.
2. **Paper surface target:** `d64_h2_seq32` if the probe is tractable.
3. **Scaling target:** `d64_h2_seq32 -> d64_h2_seq64` only after the `seq32`
   object is reproducible.

The first implementation should not attempt `d128` or four-head `seq64`.

## Required Equality Conditions

An external baseline can be called same-surface only if it pins:

- input row shape and ordering;
- key, query, value, and output width;
- head count;
- sequence length;
- bounded score policy;
- Softmax-table or table-derived weight policy;
- output rounding policy;
- public input and output commitments;
- model or kernel identifier;
- verifier domain;
- proof bytes and verifier artifact bytes as separate columns.

If any of these are changed, the row may still be useful but should be labeled
as a semantic-neighbor baseline rather than same-surface.

## Byte Accounting Method

Any external baseline row must report byte categories with file-level
measurement rules. The measurement method is `stat -f%z <file>` on macOS or
`wc -c <file>` on portable shells, recorded against exact artifact paths and
source digests.

Included byte categories:

- `proof_bytes`: the serialized EZKL proof or zkVM receipt artifact exactly as
  verified by its verifier.
- `verification_key_bytes`: the serialized verifier key, proving settings, image
  identifier, or verifier artifact required by the verifier and not derivable
  from the proof bytes alone.
- `settings_bytes`: EZKL settings, model metadata, or equivalent configuration
  required to reproduce verification.
- `setup_assumptions_bytes`: SRS, trusted setup handle, image ID, or versioned
  setup reference. If the object is a handle rather than a byte artifact, report
  `not_byte_sized_handle` and record the handle value separately.
- `statement_envelope_bytes`: the typed statement envelope that binds model or
  kernel identity, input commitment, output commitment, numeric policy, verifier
  domain, source digest, and non-claims.

Excluded from the primary proof-size row:

- source JSON fixtures used only to generate the witness;
- human-readable notes;
- logs, stdout, timing captures, and temporary build directories;
- duplicate copies of artifacts already counted in a category above.

If a category is unavailable because no proof or export artifact exists, the row
must say `unavailable_not_generated` rather than using zero. That distinction is
important: zero means the artifact is unnecessary; unavailable means the probe
has not produced a comparable proof object.

## EZKL Feasibility

### GO path

EZKL becomes a useful external baseline if we can produce:

- an ONNX model for the bounded attention kernel;
- deterministic input generation from the same source rows used by the Stwo
  artifact;
- proof generation and verification under a pinned EZKL version;
- proof bytes, verifier key bytes, settings bytes, and statement-envelope bytes;
- mutation checks for model/input/output/policy/domain relabeling.

### NO-GO risks

- ONNX export changes semantics enough that the comparison is no longer the same
  surface.
- Table membership becomes ordinary arithmetic or a different lookup encoding,
  making the result a proof-system-neighbor row rather than a matched boundary
  row.
- EZKL setup and verifier artifacts dominate the byte accounting unless reported
  separately.
- The first tractable object is much smaller than the paper's `d64` sequence
  rows, limiting its use to methodology rather than headline evidence.

## zkVM Fallback

A zkVM receipt is a useful fallback for correctness and statement binding, but
not automatically a proof-size baseline. A zkVM can execute an implementation of
the bounded attention kernel and bind the journal to the same public statement.
That is a strong receipt baseline. It is not an apples-to-apples proof-boundary
baseline unless the byte accounting separates:

- receipt bytes;
- verifier or image identity;
- journal bytes;
- statement-envelope bytes;
- included source or method identifiers.

The existing RISC Zero attention receipts in this repository are useful controls
for statement binding and carried-state semantics, but they are not the same
Softmax-table fused attention surface used in the proof-pressure paper.

## Next Implementation Artifact Contract

The next implementation should be a separate probe artifact, not a command hidden
inside this appendix PR. It should take this source evidence file:

- `docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-seq32-bounded-softmax-table-proof-2026-05.json`

It should write:

- a machine-readable probe payload under `target/`;
- a public engineering note under `docs/engineering/`;
- an exact reproduction command in that note after the script exists.

The first probe artifact's responsibility is semantic export and accounting
classification, not proving. It should fail closed if the ONNX export cannot
preserve the table policy and public output semantics.

## Paper Usage

For the current proof-pressure paper:

- do not add an external baseline row yet;
- say external same-surface baselines are future work;
- keep NANOZK, Jolt Atlas, zkLLM, DeepProve, EZKL, RISC Zero, SP1, and Stwo in
  related work only;
- avoid claims that the local Stwo row beats external systems.

## Non-Claims

- Not a NANOZK comparison.
- Not a full transformer block comparison.
- Not a proof that EZKL or zkVM baselines are unsuitable.
- Not evidence against external systems.
- Not a public performance benchmark.
