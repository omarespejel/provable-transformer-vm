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

`GO_WIDE_GRID_SELECTOR_KEEP_D64_D128_D256_AS_FALSIFICATION_TARGETS`

The current checked route matrix covers `14` source-backed attention rows over
`d8`, `d16`, and `d32`. It does not yet contain any source-backed `d64`,
`d128`, or `d256` attention route rows. The selector therefore records the wide
grid as a falsification target, not as a result.

## Why This Matters

The strongest current signal is lookup-heavy sequence scaling:

| Fixed surface | Lookup growth | Trace-row growth | Fused raw proof growth |
|---|---:|---:|---:|
| `d32`, two-head, `seq8` to `seq32` | `11.384615x` | `16.000000x` | `1.193955x` |

That is the signal a paper can try to turn into a structural result.

Width is the stress test:

| Fixed surface | Lookup growth | Fused raw proof growth |
|---|---:|---:|
| two-head `seq32`, `d8` to `d32` | `1.000000x` | `2.263739x` |

Human read: sequence makes lookup work grow much faster than proof bytes; width
currently grows proof bytes without adding lookup claims. So `d64`, `d128`, and
`d256` should not be treated as victory laps. They are the next way to check
whether the amortization story survives model width.

Accounting guardrail: the selector carries typed, JSON, and binary/raw context
from the claim pack separately from the raw route-matrix signal.

| Source | Typed bytes | JSON bytes | Binary/raw bytes | Status |
|---|---:|---:|---:|---|
| attention controlled grid totals | `234,296` | `629,466` | not available for those rows | typed/JSON only |
| statement-only seq32+d128 row | `39,516` | `113,388` | `1,084` | local record-stream accounting |
| route matrix raw saving | not comparable | not comparable | `266,325` saved | raw proof-byte route signal |

## Selected Attack Order

1. `d64_h2_seq32`
   - Direct falsification row.
   - Extends the current `d32` two-head `seq32` high-lookup point by width only.
   - GO if source, sidecar, and fused rows exist and fused beats matched split.
   - NO-GO if width pressure removes the fused saving or bounded local artifacts
     become impractical.

2. `d64_h1_seq8`
   - Cheapest width-slope sanity row.
   - Isolates width pressure before spending on `seq32`.

3. `d64_h2_seq16`
   - Midpoint row between cheap width slope and direct `seq32` falsification.

4. `d128_h2_seq32`
   - Only after `d64` is source-backed and still structurally positive.

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

The gate rejects `13 / 13` mutations:

- decision drift
- claim-boundary overclaim
- source-artifact digest drift
- wide-row smuggling
- requested-width drift
- current-row-count drift
- d32 sequence-signal drift
- width-pressure-signal drift
- accounting-triplet drift
- candidate-order drift
- validation-command drift
- non-claim removal
- payload-commitment drift

Output writes are restricted to `docs/engineering/evidence`, reject `..`
traversal, and reject symlinked evidence-root ancestors, candidate parent
components, and output components before resolving paths.

## Non-Claims

- Not a `d64`, `d128`, or `d256` attention proof result.
- Not a full transformer block proof.
- Not exact real-valued Softmax.
- Not a NANOZK proof-size comparison.
- Not timing evidence.
- Not production zkML readiness.
