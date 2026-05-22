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

`GO_WIDE_GRID_SELECTOR_KEEP_PARTIAL_D64_AND_D128_D256_AS_FALSIFICATION_TARGETS`

The current checked route matrix covers `21` source-backed attention rows over
`d8`, `d16`, `d32`, and partial `d64`. It contains checked `d64_h2_seq16`,
`d64_h2_seq32`, `d64_h4_seq16`, and `d64_h4_seq32` rows. It does not yet
contain `d128` or `d256` attention route rows. The selector therefore records
the remaining wide grid as a falsification target, not as a result.

## Why This Matters

The strongest current signal is lookup-heavy sequence scaling:

| Fixed surface | Lookup growth | Trace-row growth | Fused raw proof growth |
|---|---:|---:|---:|
| `d32`, two-head, `seq8` to `seq32` | `11.384615x` | `16.000000x` | `1.193955x` |
| `d64`, two-head, `seq16` to `seq32` | `3.523810x` | `4.000000x` | `1.061856x` |
| `d64`, `seq16`, two heads to four heads | `2.000000x` | `2.000000x` | `0.996193x` |
| `d64`, `seq32`, two heads to four heads | `2.000000x` | `2.000000x` | `1.010393x` |

That is the signal a paper can try to turn into a structural result.

Width is the stress test:

| Fixed surface | Lookup growth | Fused raw proof growth |
|---|---:|---:|
| two-head `seq32`, `d8` to `d32` | `1.000000x` | `2.263739x` |

Human read: sequence and head-axis pressure can make lookup work grow much
faster than proof bytes. Width still grows proof bytes without adding lookup
claims. So `d128` and `d256` should not be treated as victory laps, and the
remaining `d64` cells should be used to check whether the head and sequence
signals are real rather than one lucky row.

Accounting guardrail: the selector carries typed, JSON, and binary/raw context
from the claim pack separately from the raw route-matrix signal.

| Source | Typed bytes | JSON bytes | Binary/raw bytes | Status |
|---|---:|---:|---:|---|
| attention controlled grid totals | `234,296` | `629,466` | not available for those rows | typed/JSON only |
| statement-only seq32+d128 row | `39,516` | `113,388` | `1,084` | local record-stream accounting |
| route matrix raw saving | not comparable | not comparable | `473,678` saved | raw proof-byte route signal |

## Selected Attack Order

1. `d64_h4_seq64`
   - Next d64 four-head sequence stress row.
   - Tests whether the d64 four-head amortization that held at `seq16` and
     `seq32` survives a longer sequence.
   - GO if source, sidecar, and fused rows exist and fused beats matched split.
   - NO-GO if `seq64` breaks artifact limits or fused bytes grow roughly with
     lookup work.

2. `d64_h2_seq64`
   - Sequence extension row after the d64 `seq16` to `seq32` signal.

3. `d64_h1_seq16`
   - Single-head width-slope sanity row.
   - Isolates width pressure before adding another head axis.

4. `d128_h2_seq32`
   - Only after the partial `d64` grid remains structurally positive.

5. `d256_h2_seq32`
   - Only after `d128` is positive or after a generated/generic backend avoids
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

The gate rejects `19 / 19` mutations:

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
- width-pressure-signal drift
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
