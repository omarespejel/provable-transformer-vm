# ZKAI Proof-Pressure Slope Table

Issue: #715

## Decision

`GO_PAPER_SLOPE_TABLE_WITH_SCOPED_BLOCK_NEXT_GATE`

This table is the paper-facing read of the current attention proof-pressure
grid. It does not add a new proof. It explains what the checked rows say about
where fusion helps and where it starts to hurt.

## Result

The strongest slope is on lookup-heavy sequence and head pressure:

- sequence rows grow lookup work by `3.729730x`
  and trace rows by `4.000000x`;
- fused proof bytes grow only `1.064910x`
  to `1.080697x`;
- the d64 seq16 head-axis row grows lookup work by
  `4.000000x` while fused proof bytes
  move `0.999457x`.

The width axis is different. The d256 row still beats the matched split
frontier by `30,143` proof bytes, but its fused
proof ratio is `0.964602x` and local
median timing is not a speed win.

## Slope Table

| row | axis | lookup growth | trace growth | width growth | fused proof growth | split proof growth | target saving | target fused ratio | outcome |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| d64 h1 to h4 seq16 head axis | head | `4.000000x` | `4.000000x` | `1.000000x` | `0.999457x` | `1.024806x` | `23,089` | `0.911430x` | Go: head-axis lookup pressure amortized |
| d64 h2 seq32 to seq64 sequence axis | sequence | `3.729730x` | `4.000000x` | `1.000000x` | `1.076519x` | `1.076702x` | `34,334` | `0.888152x` | Go: sequence-axis proof-size signal, with timing caveat |
| d64 h4 seq32 to seq64 sequence axis | sequence | `3.729730x` | `4.000000x` | `1.000000x` | `1.080558x` | `1.095365x` | `39,282` | `0.875605x` | Go: sequence-axis proof-size signal, with timing caveat |
| d128 h2 seq32 to seq64 sequence axis | sequence | `3.729730x` | `4.000000x` | `1.000000x` | `1.080697x` | `1.091811x` | `40,317` | `0.922792x` | Go: sequence-axis proof-size signal, timing not measured |
| d128 h4 seq32 to seq64 sequence axis | sequence | `3.729730x` | `4.000000x` | `1.000000x` | `1.064910x` | `1.068793x` | `43,816` | `0.918810x` | Go: sequence-axis proof-size signal, timing not measured |
| d64 to d128 h1 seq16 width axis | width | `1.000000x` | `1.000000x` | `2.000000x` | `1.599924x` | `1.561918x` | `16,971` | `0.957286x` | Caution: width grows proof bytes, fused still beats split |
| d64 to d128 h2 seq32 width axis | width | `1.000000x` | `1.000000x` | `2.000000x` | `1.760615x` | `1.677561x` | `32,388` | `0.932282x` | Caution: width grows proof bytes, fused still beats split |
| d128 to d256 h2 seq32 width axis | width | `1.000000x` | `1.000000x` | `2.000000x` | `1.842162x` | `1.780438x` | `30,143` | `0.964602x` | Caution: width saving weakens and timing is not a speed win |

## Interpretation

The clean paper claim is not that bigger fused proofs always win. It is that
transformer proof boundaries should follow proof pressure. The current evidence
says lookup-heavy sequence and head growth can be amortized in proof bytes, while
width growth is a cost center that needs a narrower or composed boundary.

Next gate:

`scoped_d128_seq32_transformer_block_boundary_preflight; d256_seq64_remains_a_stress_test_not_the_primary_paper_gate`

## Evidence

- JSON: `docs/engineering/evidence/zkai-proof-pressure-slope-table-2026-05.json`
- TSV: `docs/engineering/evidence/zkai-proof-pressure-slope-table-2026-05.tsv`
- Route matrix: `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`
- Main evidence: `docs/engineering/evidence/zkai-proof-pressure-main-evidence-2026-05.json`

## Validation

```bash
python3.10 scripts/zkai_proof_pressure_slope_table_gate.py --write-json docs/engineering/evidence/zkai-proof-pressure-slope-table-2026-05.json --write-tsv docs/engineering/evidence/zkai-proof-pressure-slope-table-2026-05.tsv --write-md docs/engineering/zkai-proof-pressure-slope-table-2026-05-24.md
python3.10 -m py_compile scripts/zkai_proof_pressure_slope_table_gate.py scripts/tests/test_zkai_proof_pressure_slope_table_gate.py
python3.10 -m unittest scripts.tests.test_zkai_proof_pressure_slope_table_gate
git diff --check
```

## Non-Claims

- not a full transformer block proof.
- not a public proving-speed benchmark.
- not an external zkML comparison.
- not a NANOZK proof-size win.
- not a claim that width scaling is free.
- not production throughput evidence.
