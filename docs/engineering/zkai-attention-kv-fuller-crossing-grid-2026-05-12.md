# zkAI Attention/KV Fuller Width/Head/Sequence Crossing Grid - 2026-05-12

## Question

Which width/head/sequence combinations are already proved by the native Stwo
fused Softmax-table route family, and which combinations are still missing?

The bounded grid now tracks:

- width: `d8`, `d16`, `d32`, `d64`, `d128`;
- head count: `1`, `2`, `4`, `8`, `16`;
- sequence length: `seq8`, `seq16`, `seq32`, `seq64` steps per head.

## Decision

`NO_GO_71_OF_100_GRID_CELLS_DO_NOT_HAVE_NATIVE_FUSED_PROOFS`

This is a coverage manifest, not a full proof-grid result. The current evidence
frontier is `29 / 100` proved cells and `71 / 100` missing cells.

## Evidence

- Gate script:
  `scripts/zkai_attention_kv_fuller_crossing_grid_gate.py`
- Gate tests:
  `scripts/tests/test_zkai_attention_kv_fuller_crossing_grid_gate.py`
- JSON evidence:
  `docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json`
- TSV evidence:
  `docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.tsv`

The gate is derived from the checked route matrix:

- `docs/engineering/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05-09.md`
- `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`

## Result

| Metric | Value |
|---|---:|
| Grid cells | `100` |
| Proved cells | `29` |
| Missing cells | `71` |
| Coverage | `29.0000%` |
| Proved crossing cells | `22` |
| Proved all-axis cells | `16` |
| Missing all-axis cells | `32` |

The proved cells are exactly the checked route-matrix cells:

- `d8_h1_seq8`
- `d8_h2_seq8`
- `d8_h2_seq16`
- `d8_h2_seq32`
- `d8_h4_seq8`
- `d8_h8_seq8`
- `d8_h16_seq8`
- `d16_h1_seq8`
- `d16_h2_seq8`
- `d16_h2_seq16`
- `d16_h2_seq32`
- `d32_h1_seq8`
- `d32_h2_seq8`
- `d32_h2_seq16`
- `d32_h2_seq32`
- `d32_h4_seq16`
- `d32_h4_seq32`
- `d64_h1_seq16`
- `d64_h2_seq16`
- `d64_h2_seq32`
- `d64_h2_seq64`
- `d64_h4_seq16`
- `d64_h4_seq32`
- `d64_h4_seq64`
- `d128_h1_seq16`
- `d128_h2_seq32`
- `d128_h2_seq64`
- `d128_h4_seq32`
- `d128_h4_seq64`

Every other cell is marked
`MISSING_NATIVE_FUSED_PROOF_AND_MATCHED_COMPARATOR` and carries no proof-byte,
ratio, or evidence-path metrics.

## What Changed

The new proved cell is `d128_h1_seq16`. It adds the lower-pressure d128 width
anchor:

- fused proof bytes: `380,342`
- source-plus-sidecar bytes: `397,313`
- saving: `16,971`
- fused ratio: `0.957286x`
- lookup claims: `168`
- trace rows: `256`

This row is a useful anchor, not the main sequence-scaling signal. It says the
fused route still beats split at a low-lookup d128 point, but the margin is
smaller than the lookup-heavy sequence rows.

## GO / NO-GO

GO for a controlled crossing-grid artifact:

- the upstream fused Softmax-table route matrix validates locally;
- exactly `29` checked route cells are marked proved and exactly `71` cells are
  marked missing;
- every proved cell has matched source-plus-LogUp-sidecar comparator evidence;
- missing cells carry no proof-byte, ratio, or evidence-path claims.

NO-GO for stronger claims:

- no full factorial proof-grid claim, because `71 / 100` cells are missing;
- no d256 attention proof claim;
- no timing or public benchmark claim;
- no real-valued Softmax or full-inference claim.

## Next Proof Candidate

The lowest-risk next proof profile is now:

- `d256_two_head_seq32`: width stress test after the positive d128 rows.

Issue-level gates still outside this grid:

- d256 attention rows;
- one same-surface external baseline row;
- median-of-5 timing once proof shapes stabilize;
- scoped transformer-block work only after the width stress test.

## Claim Boundary

This may be cited internally as:

> The fuller crossing grid makes the current native Stwo fused Softmax-table
> evidence frontier explicit: `29 / 100` width/head/sequence cells are proved
> with matched source-plus-sidecar comparators, while `71 / 100` cells remain
> unproved and carry no proof-size claims.

Do not cite it as:

- a full factorial proved grid;
- a full grid of new native Stwo proof profiles;
- timing evidence;
- exact real-valued Softmax;
- implementation-exact model Softmax;
- full transformer inference;
- recursion or PCD.

## Validation

```bash
python3.10 scripts/zkai_attention_kv_fuller_crossing_grid_gate.py \
  --write-json docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json \
  --write-tsv docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.tsv

python3.10 -m unittest scripts.tests.test_zkai_attention_kv_fuller_crossing_grid_gate

python3.10 scripts/zkai_attention_kv_fused_softmax_table_route_matrix_gate.py \
  --write-json docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json \
  --write-tsv docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.tsv

python3.10 -m unittest scripts.tests.test_zkai_attention_kv_fused_softmax_table_route_matrix_gate
```
