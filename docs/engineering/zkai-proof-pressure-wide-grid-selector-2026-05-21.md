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

`GO_WIDE_GRID_SELECTOR_PROMOTE_D128_HEAD_AXIS_WITH_D256_STILL_FALSIFICATION_TARGET`

The current checked route matrix covers `26` source-backed attention rows over
`d8`, `d16`, `d32`, partial `d64`, and two `d128` two-head rows. It contains
checked d64 two-head and four-head sequence rows through `seq64`, plus
`d128_h2_seq32` and `d128_h2_seq64`. It still does not contain `d256`
attention route rows. The selector therefore promotes the next d128 head-axis
row while keeping d256 as a falsification target, not as a measured result.

## Why This Matters

The strongest current signal is lookup-heavy sequence scaling:

| Fixed surface | Lookup growth | Trace-row growth | Fused raw proof growth |
|---|---:|---:|---:|
| `d32`, two-head, `seq8` to `seq32` | `11.384615x` | `16.000000x` | `1.193955x` |
| `d64`, two-head, `seq16` to `seq32` | `3.523810x` | `4.000000x` | `1.061856x` |
| `d64`, two-head, `seq32` to `seq64` | `3.729730x` | `4.000000x` | `1.076519x` |
| `d64`, four-head, `seq32` to `seq64` | `3.729730x` | `4.000000x` | `1.080558x` |
| `d128`, two-head, `seq32` to `seq64` | `3.729730x` | `4.000000x` | `1.080697x` |
| `d64`, `seq16`, two heads to four heads | `2.000000x` | `2.000000x` | `0.996193x` |
| `d64`, `seq32`, two heads to four heads | `2.000000x` | `2.000000x` | `1.010393x` |

That is the signal a paper can try to turn into a structural result.

Width is the stress test:

| Fixed surface | Lookup growth | Fused raw proof growth |
|---|---:|---:|
| two-head `seq32`, `d8` to `d32` | `1.000000x` | `2.263739x` |
| two-head `seq32`, `d64` to `d128` | `1.000000x` | `1.760615x` |
| two-head `seq64`, `d64` to `d128` | `1.000000x` | `1.767448x` |

Human read: sequence and head-axis pressure can make lookup work grow much
faster than proof bytes. Width still grows proof bytes without adding lookup
claims. The new d128 seq64 row is useful because the sequence signal survives
one real d128 extension, but width remains the stress test. The next question
is whether d128 also survives head-axis pressure.

Accounting guardrail: the selector carries typed, JSON, and binary/raw context
from the claim pack separately from the raw route-matrix signal.

| Source | Typed bytes | JSON bytes | Binary/raw bytes | Status |
|---|---:|---:|---:|---|
| attention controlled grid totals | `234,296` | `629,466` | not available for those rows | typed/JSON only |
| statement-only seq32+d128 row | `39,516` | `113,388` | `1,084` | local record-stream accounting |
| route matrix raw saving | not comparable | not comparable | `636,649` saved | raw proof-byte route signal |

## Selected Attack Order

1. `d128_h4_seq32`
   - Next d128 head-axis stress row.
   - Tests whether the positive d128 two-head rows survive a wider head surface
     before jumping to d256.
   - GO if source, sidecar, and fused rows exist and fused beats matched split.
   - NO-GO if d128 four-head proof generation is too heavy, fails mutation
     guards, or loses the matched fused-vs-split saving.

2. `d128_h1_seq16`
   - Lower-pressure d128 width anchor fallback.
   - Separates d128 width pressure from head pressure if the four-head row is
     too heavy.

3. `d256_h2_seq32`
   - Only after d128 head-axis evidence stays structurally positive or after a
     generated/generic backend avoids
     copy-per-width engineering dominating the research.

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
just gate-fast
just gate
```

## Correctness Guards

The gate rejects `26 / 26` mutations:

- decision drift
- claim-boundary overclaim
- source-artifact digest drift
- wide-row smuggling
- requested-width drift
- requested-head-count drift
- requested-sequence drift
- requested-source-id drift
- requested-row-status drift
- current-row-count drift
- d32 sequence-signal drift
- d64 sequence-signal drift
- d64 two-head seq64 signal drift
- d128 width-frontier signal drift
- d128 sequence-frontier signal drift
- d128 seq64 width-frontier signal drift
- width-pressure-signal drift
- d64 single-head anchor signal drift
- d64 head-axis metric drift
- accounting-triplet drift
- candidate-order drift
- validation-command drift
- non-claim removal
- payload-commitment drift

Output writes are restricted to `docs/engineering/evidence`, reject `..`
traversal, and reject symlinked evidence-root ancestors, candidate parent
components, and output components before resolving paths. The writer also
requires output parent directories to exist instead of creating directory
chains during the write path.

## Non-Claims

- Not a `d64`, `d128`, or `d256` attention proof result.
- Not a full transformer block proof.
- Not exact real-valued Softmax.
- Not a NANOZK proof-size comparison.
- Not timing evidence.
- Not production zkML readiness.
