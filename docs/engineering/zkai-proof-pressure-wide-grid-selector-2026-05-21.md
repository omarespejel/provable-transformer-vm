# ZKAI Proof-Pressure Wide Grid Selector

Date: 2026-05-21

Issue: #715

## Question

The next paper-grade agenda asks for `d64`, `d128`, and `d256` scaling with
fused versus split accounting at every point. The selector asks a narrower
question first:

> Which wide row should be attacked next without pretending the wide grid is
> already measured?

## Result

`GO_WIDE_GRID_SELECTOR_PROMOTE_D256_SEQ64_DECISION_GATE`

The current checked route matrix covers `30` source-backed attention rows over
`d8`, `d16`, `d32`, partial `d64`, partial `d128`, and one `d256` row. It
contains the d128 single-head `seq16` anchor, d128 two-head `seq32` and
`seq64`, d128 four-head `seq32` and `seq64`, and the new d256 two-head
`seq32` width-stress row.

The selector therefore promotes `d256_h2_seq64` as the next sequence decision
gate. This is a falsification target, not a measured result.

## Why This Matters

The strongest current signal is lookup-heavy sequence and head-axis scaling:

| Fixed surface | Lookup growth | Trace-row growth | Fused raw proof growth |
|---|---:|---:|---:|
| `d32`, two-head, `seq8` to `seq32` | `11.384615x` | `16.000000x` | `1.193955x` |
| `d64`, two-head, `seq32` to `seq64` | `3.729730x` | `4.000000x` | `1.076519x` |
| `d64`, four-head, `seq32` to `seq64` | `3.729730x` | `4.000000x` | `1.080558x` |
| `d128`, two-head, `seq32` to `seq64` | `3.729730x` | `4.000000x` | `1.080697x` |
| `d128`, four-head, `seq32` to `seq64` | `3.729730x` | `4.000000x` | `1.064910x` |
| `d64`, `seq16`, one head to four heads | `4.000000x` | `4.000000x` | `0.999457x` |
| `d128`, `seq32`, two heads to four heads | `2.000000x` | `2.000000x` | `1.044276x` |

Width is the stress test:

| Fixed surface | Lookup growth | Fused raw proof growth | Saving growth |
|---|---:|---:|---:|
| two-head `seq32`, `d8` to `d32` | `1.000000x` | `2.263739x` | not promoted |
| two-head `seq32`, `d64` to `d128` | `1.000000x` | `1.760615x` | `1.017051x` |
| two-head `seq64`, `d64` to `d128` | `1.000000x` | `1.767448x` | `1.174259x` |
| single-head `seq16`, `d64` to `d128` | `1.000000x` | `1.599924x` | `1.019279x` |
| two-head `seq32`, `d128` to `d256` | `1.000000x` | `1.842162x` | `0.930684x` |

Human read: sequence and head-axis pressure can make lookup work grow much
faster than proof bytes. Width still grows proof bytes without adding lookup
claims. The d256 seq32 row is still positive on raw proof bytes, but local
median timing is not a speed win. The next useful question is whether the
d256 row keeps sequence-axis amortization at `seq64`.

Accounting guardrail: the selector carries typed, JSON, and binary/raw context
from the claim pack separately from the raw route-matrix signal.

| Source | Typed bytes | JSON bytes | Binary/raw bytes | Status |
|---|---:|---:|---:|---|
| attention controlled grid totals | `234,296` | `629,466` | not available for those rows | typed/JSON only |
| statement-only seq32+d128 row | `39,516` | `113,388` | `1,084` | local record-stream accounting |
| route matrix raw saving | not comparable | not comparable | `766,883` saved | raw proof-byte route signal |

## Selected Attack Order

1. `d256_h2_seq64`
   - Next d256 sequence decision row.
   - Tests whether the d256 width-stress row keeps the sequence-axis
     amortization already seen at d64 and d128.
   - GO if source, sidecar, fused, mutation, and accounting gates validate and
     fused beats matched split, or if a clean NO-GO explains the boundary.
   - NO-GO if d256 sequence pressure loses the boundary saving or requires
     special-casing that hides the proof-pressure signal.

## Evidence

- JSON: `docs/engineering/evidence/zkai-proof-pressure-wide-grid-selector-2026-05.json`
- TSV: `docs/engineering/evidence/zkai-proof-pressure-wide-grid-selector-2026-05.tsv`
- Source route matrix:
  `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`
- Source fuller grid:
  `docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json`
- Source claim pack:
  `docs/engineering/evidence/zkai-proof-pressure-scaling-claim-pack-2026-05.json`

## Validation

```bash
python3.10 scripts/zkai_proof_pressure_wide_grid_selector_gate.py --write-json docs/engineering/evidence/zkai-proof-pressure-wide-grid-selector-2026-05.json --write-tsv docs/engineering/evidence/zkai-proof-pressure-wide-grid-selector-2026-05.tsv
python3.10 -m py_compile scripts/zkai_proof_pressure_wide_grid_selector_gate.py scripts/tests/test_zkai_proof_pressure_wide_grid_selector_gate.py
python3.10 -m unittest scripts.tests.test_zkai_proof_pressure_wide_grid_selector_gate
git diff --check
```

## Correctness Guards

The gate rejects `30 / 30` mutations:

- decision drift
- claim-boundary overclaim
- source-artifact digest drift
- wide-row smuggling
- requested-width drift
- requested-head-count drift
- requested-sequence drift
- requested-selector-status drift
- requested-source-id drift
- requested-row-status drift
- current-row-count drift
- d32 sequence-signal drift
- d64 sequence-signal drift
- d64 two-head seq64 signal drift
- d128 width-frontier signal drift
- d128 sequence-frontier signal drift
- d128 head-frontier signal drift
- d128 four-head sequence-frontier signal drift
- d128 seq64 width-frontier signal drift
- d256 width-stress signal drift
- width-pressure-signal drift
- d64 single-head anchor signal drift
- d128 single-head width-anchor signal drift
- d64 head-axis metric drift
- accounting-triplet drift
- candidate-order drift
- candidate-text drift
- validation-command drift
- non-claim removal
- payload-commitment drift

Output writes are restricted to `docs/engineering/evidence`, reject `..`
traversal, and reject symlinked evidence-root ancestors, candidate parent
components, and output components before resolving paths. The writer also
requires output parent directories to exist instead of creating directory
chains during the write path.

## Non-Claims

- Not a complete d64, d128, or d256 attention proof result.
- Not a full transformer block proof.
- Not exact real-valued Softmax.
- Not a NANOZK proof-size comparison.
- Not timing evidence.
- Not production zkML readiness.
