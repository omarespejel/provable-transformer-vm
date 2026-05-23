# ZKAI Proof-Pressure Main Evidence

Issue: #715

## Decision

`GO_MAIN_EVIDENCE_TABLE_AND_FIGURE_WITH_SIZE_TIMING_CAVEAT`

This note packages the current paper-facing signal in one place. It is not a
new proof route. It ties the route matrix, median timing rows, and central
figure together so the claim can be read without overclaiming speed or full
model coverage.

## Result

The strongest result is still proof-size amortization under lookup-heavy
sequence pressure:

| comparison | lookup growth | trace growth | fused proof growth | fused prove-time growth |
|---|---:|---:|---:|---:|
| d64 two-head seq32 to seq64 | `3.729730x` | `4.000000x` | `1.076519x` | `4.019863x` |
| d64 four-head seq32 to seq64 | `3.729730x` | `4.000000x` | `1.080558x` | `3.937449x` |
| d128 two-head seq32 to seq64 | `3.729730x` | `4.000000x` | `1.080697x` | not measured here |
| d128 four-head seq32 to seq64 | `3.729730x` | `4.000000x` | `1.064910x` | not measured here |

The d256 width-stress row remains positive on proof bytes:

| row | fused proof | split frontier | saving | fused ratio |
|---|---:|---:|---:|---:|
| d256 two-head seq32 | `821,398` | `851,541` | `30,143` | `0.964602x` |

But d256 timing is not a speed win in local median-of-5 release timing:

| row | fused prove ratio | fused verify ratio |
|---|---:|---:|
| d256 two-head seq32 versus split | `1.146005x` | `1.141390x` |

## Interpretation

This is the honest breakthrough shape:

> Fused STARK-native attention boundaries can make proof bytes grow slowly even
> when lookup and trace work grow quickly.

It is not:

> Fused proving is faster.

The paper direction should therefore stay on boundary selection and proof-size
amortization. Timing evidence is still useful because it prevents the claim
from drifting into a speed benchmark.

## Evidence

- Main evidence JSON:
  `docs/engineering/evidence/zkai-proof-pressure-main-evidence-2026-05.json`
- Main evidence TSV:
  `docs/engineering/evidence/zkai-proof-pressure-main-evidence-2026-05.tsv`
- Figure:
  `docs/engineering/evidence/zkai-proof-pressure-work-proof-time-growth-2026-05.svg`
- d64 timing:
  `docs/engineering/evidence/zkai-attention-kv-d64-sequence-median-timing-raw-2026-05.json`
- d256 timing:
  `docs/engineering/evidence/zkai-attention-kv-d256-two-head-seq32-median-timing-raw-2026-05.json`

## Validation

```bash
python3.10 scripts/zkai_proof_pressure_main_evidence_gate.py --write-json docs/engineering/evidence/zkai-proof-pressure-main-evidence-2026-05.json --write-tsv docs/engineering/evidence/zkai-proof-pressure-main-evidence-2026-05.tsv --write-svg docs/engineering/evidence/zkai-proof-pressure-work-proof-time-growth-2026-05.svg
python3.10 -m py_compile scripts/zkai_proof_pressure_main_evidence_gate.py scripts/tests/test_zkai_proof_pressure_main_evidence_gate.py
python3.10 -m unittest scripts.tests.test_zkai_proof_pressure_main_evidence_gate
cargo +nightly-2025-07-14 test --locked --release --features stwo-backend --bin zkai_attention_kv_d64_sequence_median_timing
cargo +nightly-2025-07-14 test --locked --release --features stwo-backend --bin zkai_attention_kv_d256_two_head_seq32_median_timing
```

## Non-Claims

- Not a full transformer block proof.
- Not a public proving-speed benchmark.
- Not an external zkML comparison.
- Not a NANOZK proof-size win.
- Not production throughput evidence.
