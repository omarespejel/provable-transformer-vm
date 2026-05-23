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

`GO_WIDE_GRID_SELECTOR_PROMOTE_D128_SINGLE_HEAD_ANCHOR_AND_D256_WIDTH_STRESS`

The current checked route matrix covers `29` source-backed attention rows over
`d8`, `d16`, `d32`, partial `d64`, and partial `d128`. It contains the new
`d128_h1_seq16` anchor, d128 two-head `seq32` and `seq64`, and d128 four-head
`seq32` and `seq64`. It still does not contain `d256` attention route rows.

The selector therefore promotes `d256_h2_seq32` as the next width stress test.
This is a falsification target, not a measured result.

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

Human read: sequence and head-axis pressure can make lookup work grow much
faster than proof bytes. Width still grows proof bytes without adding lookup
claims. The d128 single-head anchor is positive but modest, so the next useful
question is whether the signal survives a d256 width stress point.

Accounting guardrail: the selector carries typed, JSON, and binary/raw context
from the claim pack separately from the raw route-matrix signal.

| Source | Typed bytes | JSON bytes | Binary/raw bytes | Status |
|---|---:|---:|---:|---|
| attention controlled grid totals | `234,296` | `629,466` | not available for those rows | typed/JSON only |
| statement-only seq32+d128 row | `39,516` | `113,388` | `1,084` | local record-stream accounting |
| route matrix raw saving | not comparable | not comparable | `736,740` saved | raw proof-byte route signal |

## Selected Attack Order

1. `d256_h2_seq32`
   - Next width stress row.
   - Tests whether the positive d128 frontier survives a harder width point
     before scoped block work.
   - GO if source, sidecar, and fused rows exist and fused beats matched split.
   - NO-GO if copy-per-width engineering dominates research signal or d256
     pressure loses the boundary saving.

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

The gate rejects `29 / 29` mutations:

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
