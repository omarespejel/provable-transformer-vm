# Seq32 Value-Compatible Boundary Frontier

Date: 2026-05-18
Follow-up issue: https://github.com/omarespejel/provable-transformer-vm/issues/678

## Decision

`GO_PIN_SEQ32_VALUE_COMPATIBLE_TWO_PROOF_FRONTIER_FOR_NEXT_NATIVE_BOUNDARY`.

The selected two-head `seq32` fused attention surface and the regenerated
seq32-derived `d128` RMSNorm/MLP surface now form the honest value-compatible
two-proof target for the next native attention-plus-MLP proof-object attempt.

Human meaning: the correctness fix made the target heavier but real. The next
native proof object must beat `47,188` typed bytes / `140,838` JSON proof bytes,
not the stale pre-fix `45,492` typed-byte selector target.

## Evidence

| surface | JSON proof bytes | typed bytes | note |
|---|---:|---:|---|
| two-head `seq32` fused attention | `66,327` | `22,916` | `1,184` lookup claims, `2,048` trace rows |
| seq32-derived `d128` RMSNorm/MLP fused | `74,511` | `24,272` | `0 / 128` adapter mismatches |
| value-compatible two-proof frontier | `140,838` | `47,188` | target for the next native object |
| stale selector frontier | `134,887` | `45,492` | obsolete after the source-value fix |
| old `d8` two-proof frontier | `116,258` | `40,700` | smaller but not the selected larger surface |

The attention-side amortization signal is still alive: lookup claims grew
`22.769231x` versus `d8`, while attention typed bytes grew only `1.264401x`.
The MLP side still has strong local fusion evidence: `24,272` typed bytes fused
versus `54,336` typed bytes across six separate regenerated native component
proofs, saving `30,064` typed bytes.

The price of being value-correct is explicit: the frontier is now `1,696` typed
bytes and `5,951` JSON proof bytes heavier than the stale selector target.

## NANOZK Boundary

This gate records zero proof-size-comparable external rows.

NANOZK reports a `6,900` byte `d128` transformer-block proof row. The current
local target is `47,188` typed bytes, so matching that reported row would
require removing `40,288` typed bytes, or `85.3776%` of the current local typed
frontier. That is a gap, not a win.

The useful interpretation is not "we beat NANOZK." The useful interpretation is
that we now have a corrected local target for testing whether one larger
STARK-native boundary can share enough proof plumbing across attention and MLP
work to beat the matched two-proof frontier.

## Non-Claims

- Not one native attention-plus-MLP proof object.
- Not a full transformer block proof.
- Not a NANOZK proof-size win.
- Not a matched external zkML benchmark.
- Not timing evidence.
- Not production-ready zkML.

## Reproduction

Reproducibility metadata:

- Gate schema/version:
  `zkai-seq32-value-compatible-boundary-frontier-v1`.
- Source backend versions:
  `stwo-attention-kv-two-head-seq32-fused-bounded-softmax-table-logup-v1`
  and `stwo-d128-rmsnorm-mlp-fused-air-proof-v1`.
- Source statement versions:
  `zkai-attention-kv-stwo-native-two-head-seq32-fused-softmax-table-logup-statement-v1`
  and `zkai-d128-rmsnorm-mlp-fused-statement-v1`.
- Runtime/toolchain:
  Python `3.10+`; source Stwo artifacts were generated under the repo-pinned
  `nightly-2025-07-14` flow.
- Timing mode:
  proof-size/accounting only; no timing claim and no median-of-5 run.
- Step-count scope:
  two proof envelopes only: one two-head `seq32` fused attention proof and one
  seq32-derived `d128` RMSNorm/MLP fused proof.

```bash
python3.10 scripts/zkai_seq32_value_compatible_boundary_frontier_gate.py --write-json docs/engineering/evidence/zkai-seq32-value-compatible-boundary-frontier-2026-05.json --write-tsv docs/engineering/evidence/zkai-seq32-value-compatible-boundary-frontier-2026-05.tsv
python3.10 -m py_compile scripts/zkai_seq32_value_compatible_boundary_frontier_gate.py scripts/tests/test_zkai_seq32_value_compatible_boundary_frontier_gate.py
python3.10 -m unittest scripts.tests.test_zkai_seq32_value_compatible_boundary_frontier_gate
python3.10 -m unittest scripts.tests.test_zkai_seq32_derived_d128_mlp_surface_gate
```

## Checked Artifacts

- `docs/engineering/evidence/zkai-seq32-value-compatible-boundary-frontier-2026-05.json`
- `docs/engineering/evidence/zkai-seq32-value-compatible-boundary-frontier-2026-05.tsv`
- `scripts/zkai_seq32_value_compatible_boundary_frontier_gate.py`
- `scripts/tests/test_zkai_seq32_value_compatible_boundary_frontier_gate.py`

The gate rejects `13 / 13` mutations covering stale-frontier overclaim,
metric drift, adapter mismatch drift, NANOZK overclaim, native-object
overclaim, source artifact digest drift, valid in-repo source path drift,
path traversal, non-claim drift, validation-command drift, and payload
commitment drift.
