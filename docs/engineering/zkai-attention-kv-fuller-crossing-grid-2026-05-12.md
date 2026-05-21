# zkAI Attention/KV Fuller Width/Head/Sequence Crossing Grid - 2026-05-12

## Question

Which width/head/sequence combinations are already proved by the native Stwo
fused Softmax-table route family, and which combinations are still missing?

The bounded grid is:

- width: `d8`, `d16`, `d32`, `d64`;
- head count: `1`, `2`, `4`, `8`, `16`;
- sequence length: `seq8`, `seq16`, `seq32` steps per head.

## Decision

`GO_CHECKED_FULLER_CROSSING_GRID_WITH_FULL_PROOF_GRID_NO_GO`

This slice adds a checkable status grid over all `60` width/head/sequence
cells. The current evidence frontier is `17 / 60` proved cells and `43 / 60`
missing cells.

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
| Grid cells | `60` |
| Proved cells | `17` |
| Missing cells | `43` |
| Coverage | `28.3333%` |
| Proved crossing cells | `10` |
| Proved all-axis cells | `6` |
| Missing all-axis cells | `18` |

The proved cells are exactly the checked route-matrix cells:

- `d8_h1_seq8`
- `d16_h1_seq8`
- `d32_h1_seq8`
- `d8_h2_seq8`
- `d8_h4_seq8`
- `d8_h8_seq8`
- `d8_h16_seq8`
- `d8_h2_seq16`
- `d8_h2_seq32`
- `d16_h2_seq8`
- `d32_h2_seq8`
- `d16_h2_seq16`
- `d16_h2_seq32`
- `d32_h2_seq16`
- `d32_h2_seq32`
- `d64_h2_seq16`
- `d64_h2_seq32`

Every other cell is marked
`MISSING_NATIVE_FUSED_PROOF_AND_MATCHED_COMPARATOR` and carries no proof-byte,
ratio, or evidence-path metrics.

## What Changed

The previous gap cell `d16_h2_seq32` is now proved with matched
source-plus-LogUp-sidecar comparator evidence:

- fused proof bytes: `92,363`
- source-plus-sidecar bytes: `127,207`
- saving: `34,844`
- fused ratio: `0.726084x`
- lookup claims: `1,184`
- trace rows: `2,048`

This is the useful lower-width seq32 bridge between the strong d8 seq32 row and
the heavier d32 and d64 seq32 rows.

## GO / NO-GO

GO for a controlled crossing-grid artifact:

- the upstream fused Softmax-table route matrix validates locally;
- exactly `17` checked route cells are marked proved and exactly `43` cells are
  marked missing;
- every proved cell has matched source-plus-LogUp-sidecar comparator evidence;
- missing cells carry no proof-byte, ratio, or evidence-path claims.

NO-GO for stronger claims:

- no full factorial proof-grid claim, because `43 / 60` cells are missing;
- no broad crossing proof claim, because this slice adds only the
  `d16_two_head_seq32` lower-width sequence extension row;
- no timing or public benchmark claim;
- no real-valued Softmax or full-inference claim.

## Next Proof Candidates

The lowest-risk next proof profile is now:

- `d32_four_head_seq16`: test a higher-width head-axis crossing without jumping
  to seq32 first.

Issue-level gates still outside this grid:

- `d128` and `d256` attention rows;
- typed and binary/raw proof-size accounting;
- one same-surface external baseline row;
- median-of-5 timing once proof shapes stabilize.

## Claim Boundary

This may be cited internally as:

> The fuller crossing grid makes the current native Stwo fused Softmax-table
> evidence frontier explicit: `17 / 60` width/head/sequence cells are proved
> with matched source-plus-sidecar comparators, while `43 / 60` cells remain
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
