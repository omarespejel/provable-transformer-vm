# zkAI Attention/KV Fused Softmax-Table Route Matrix - 2026-05-09

## Question

Do the checked native Stwo fused Softmax-table routes still hold when the
fixture changes along controlled axes, when the single-head width axis extends
to `d32`, when width and head count are combined, when sequence length extends
to `seq32`, when width, head count, and sequence length are combined in one
route, and when the first `d64` two-head `seq32` falsification row is added?

The axes are:

- width: `d8` to `d16` to `d32` at one head and eight steps;
- head count: one, two, four, eight, and sixteen heads at `d8` and eight steps;
- sequence length: two heads at `d8`, eight steps per head to sixteen and
  thirty-two steps per head;
- combined width/head: `d16` and `d32`, two heads, eight steps per head;
- combined width/head/sequence: `d16` and `d32`, two heads, sixteen steps per
  head.
- combined width/head/sequence seq32 extension: `d32` and `d64`, two heads,
  thirty-two steps per head.

## Result

GO for a controlled engineering route matrix, now with matched source-plus-LogUp
sidecar comparators for all fifteen profile rows.

The checked matrix is machine-readable at:

- JSON: `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`
- TSV: `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.tsv`

The gate validates the existing per-route fused evidence files, checks the
source-input dimensions, normalizes the matched source-plus-sidecar comparators,
and rejects `38 / 38` matrix drift, provenance-drift, and overclaim mutations.

## Route Matrix

| profile | axis | d | heads | steps/head | lookup claims | trace rows | fused proof bytes | source+sidecar bytes | fused ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| d8 single-head seq8 | baseline | 8 | 1 | 8 | 52 | 64 | 47,698 | 59,437 | 0.802497 |
| d16 single-head seq8 | width | 16 | 1 | 8 | 52 | 64 | 64,503 | 74,961 | 0.860487 |
| d32 single-head seq8 | width extension | 32 | 1 | 8 | 52 | 64 | 107,261 | 116,682 | 0.919259 |
| d8 two-head seq8 | heads | 8 | 2 | 8 | 104 | 128 | 49,508 | 65,208 | 0.759232 |
| d8 four-head seq8 | heads | 8 | 4 | 8 | 208 | 256 | 53,468 | 74,529 | 0.717412 |
| d8 eight-head seq8 | heads | 8 | 8 | 8 | 416 | 512 | 59,375 | 74,086 | 0.801433 |
| d8 sixteen-head seq8 | heads | 8 | 16 | 8 | 832 | 1,024 | 65,006 | 88,711 | 0.732784 |
| d8 two-head seq16 | sequence | 8 | 2 | 16 | 336 | 512 | 60,502 | 79,444 | 0.761568 |
| d8 two-head seq32 | sequence extension | 8 | 2 | 32 | 1,184 | 2,048 | 66,327 | 98,012 | 0.676723 |
| d16 two-head seq8 | combined width/head | 16 | 2 | 8 | 104 | 128 | 78,211 | 91,596 | 0.853869 |
| d32 two-head seq8 | combined width/head extension | 32 | 2 | 8 | 104 | 128 | 125,756 | 142,063 | 0.885213 |
| d16 two-head seq16 | combined width/head/sequence | 16 | 2 | 16 | 336 | 512 | 84,868 | 108,158 | 0.784667 |
| d32 two-head seq16 | combined width/head/sequence extension | 32 | 2 | 16 | 336 | 512 | 132,543 | 162,138 | 0.817470 |
| d32 two-head seq32 | combined width/head/sequence seq32 extension | 32 | 2 | 32 | 1,184 | 2,048 | 150,147 | 176,473 | 0.850821 |
| d64 two-head seq32 | d64 seq32 falsification | 64 | 2 | 32 | 1,184 | 2,048 | 253,257 | 285,102 | 0.888303 |

## Axis Read

Width axis:

- Holding one head, eight steps, `52` lookup claims, and `64` trace rows fixed,
  doubling width from `d8` to `d16` grows fused proof bytes from `47,698` to
  `64,503` (`1.352321x`).
- Extending the same held-constant row from `d16` to `d32` grows fused proof
  bytes from `64,503` to `107,261` (`1.662884x`) and matched
  source-plus-sidecar bytes from `74,961` to `116,682` (`1.556569x`).
- This is width-axis proof-existence and byte-accounting evidence, not a claim
  that fused proof size is independent of width.

Head axis:

- Holding `d8` and eight steps per head fixed, lookup claims grow `16.000000x`
  from one head to sixteen heads (`52` to `832`), while fused proof bytes grow
  `1.362866x` (`47,698` to `65,006`).
- The eight-to-sixteen step is the most useful new stress point: lookup claims
  double from `416` to `832`, while fused proof bytes grow only `1.094838x`
  (`59,375` to `65,006`).
- Matched source-plus-sidecar ratios are now available for all head-axis rows:
  `0.802497` at one head, `0.759232` at two heads, `0.717412` at four heads,
  `0.801433` at eight heads, and `0.732784` at sixteen heads.
- Issue `#519` turns the earlier sixteen-head sidecar probe from issue `#516`
  into a full matched fused row: the fused proof is `23,705` bytes smaller than
  the matched source-plus-sidecar control (`88,711` bytes).
- The sixteen-head sidecar itself remains an exploratory signal: eight to
  sixteen heads doubles lookup claims (`416` to `832`) while sidecar raw proof
  bytes grow `1.293537x` (`21,694` to `28,062`).

Sequence axis:

- Holding `d8` and two heads fixed, doubling steps per head from `8` to `16`
  increases lookup claims from `104` to `336` (`3.230769x`) and trace rows from
  `128` to `512` (`4.000000x`).
- Fused proof bytes grow from `49,508` to `60,502` (`1.222065x`), and the
  matched source-plus-sidecar pair grows from `65,208` to `79,444`
  (`1.218317x`).
- Extending the same axis from `seq16` to `seq32` grows lookup claims from
  `336` to `1,184` (`3.523810x`) and trace rows from `512` to `2,048`
  (`4.000000x`), while fused proof bytes grow from `60,502` to `66,327`
  (`1.096278x`).
- The `seq32` fused proof is `31,685` bytes smaller than the matched
  source-plus-sidecar control (`98,012` bytes), giving the strongest checked
  fused ratio in the route matrix: `0.676723x`.

Combined width/head row:

- The `d16` two-head row combines the width and head axes in one native Stwo
  proof object instead of checking them only independently.
- Against the `d16` single-head row, lookup claims and trace rows double
  (`52` to `104`, `64` to `128`), while fused proof bytes grow `1.212517x`
  (`64,503` to `78,211`).
- Against the `d8` two-head row, lookup claims and trace rows are held fixed
  (`104` and `128`), while widening from `d8` to `d16` grows fused proof bytes
  `1.579765x` (`49,508` to `78,211`).
- The matched source-plus-sidecar control for the combined row is `91,596`
  bytes; the fused proof is `78,211` bytes, saving `13,385` bytes
  (`0.853869x`).

Combined width/head extension row:

- The `d32` two-head row is the next checked width/head crossing at the shortest
  sequence length.
- Against the `d32` single-head row, lookup claims and trace rows double
  (`52` to `104`, `64` to `128`), while fused proof bytes grow `1.172430x`
  (`107,261` to `125,756`).
- Against the `d16` two-head row, lookup claims and trace rows are held fixed
  (`104` and `128`), while widening from `d16` to `d32` grows fused proof bytes
  `1.607907x` (`78,211` to `125,756`).
- The matched source-plus-sidecar control for the combined extension row is
  `142,063` bytes; the fused proof is `125,756` bytes, saving `16,307` bytes
  (`0.885213x`).

Combined width/head/sequence row:

- The `d16` two-head seq16 row combines all three checked pressure axes in one
  native Stwo proof object.
- Against the `d16` two-head seq8 row, steps per head double, lookup claims grow
  `3.230769x` (`104` to `336`), trace rows grow `4.000000x` (`128` to `512`),
  while fused proof bytes grow `1.085116x` (`78,211` to `84,868`).
- Against the `d8` two-head seq16 row, lookup claims and trace rows are held
  fixed (`336` and `512`), while widening from `d8` to `d16` grows fused proof
  bytes `1.402730x` (`60,502` to `84,868`).
- The matched source-plus-sidecar control for the combined width/head/sequence
  row is `108,158` bytes; the fused proof is `84,868` bytes, saving `23,290`
  bytes (`0.784667x`).

Combined width/head/sequence extension row:

- The `d32` two-head seq16 row is the first checked `d32` all-axis extension.
- Against the `d32` two-head seq8 row, steps per head double, lookup claims grow
  `3.230769x` (`104` to `336`), trace rows grow `4.000000x` (`128` to `512`),
  while fused proof bytes grow `1.053970x` (`125,756` to `132,543`).
- Against the `d16` two-head seq16 row, lookup claims and trace rows are held
  fixed (`336` and `512`), while widening from `d16` to `d32` grows fused proof
  bytes `1.561755x` (`84,868` to `132,543`).
- The matched source-plus-sidecar control for the combined extension row is
  `162,138` bytes; the fused proof is `132,543` bytes, saving `29,595` bytes
  (`0.817470x`).
- The fused proof is also `2,520` bytes smaller than the source arithmetic proof
  alone (`135,063` bytes). This is the strongest local signal in this route
  family that table membership can share enough proof plumbing to offset more
  than the standalone sidecar.

Combined width/head/sequence seq32 extension:

- The `d32` two-head seq32 row extends the all-axis route from `seq16` to
  `seq32`.
- Against the `d32` two-head seq16 row, lookup claims grow `3.523810x`
  (`336` to `1,184`) and trace rows grow `4.000000x` (`512` to `2,048`), while
  fused proof bytes grow `1.132817x` (`132,543` to `150,147`).
- The matched source-plus-sidecar control is `176,473` bytes; the fused proof is
  `150,147` bytes, saving `26,326` bytes (`0.850821x`).

d64 seq32 falsification row:

- The `d64` two-head seq32 row holds head count, sequence length, lookup claims,
  and trace rows fixed against the `d32` two-head seq32 row, then doubles width.
- From `d32` to `d64`, source arithmetic proof bytes grow `1.709327x`, matched
  source-plus-sidecar bytes grow `1.615556x`, and fused proof bytes grow
  `1.686727x`.
- The fused proof still beats the matched source-plus-sidecar control:
  `253,257` bytes versus `285,102` bytes, saving `31,845` bytes (`0.888303x`).
- The relative ratio weakens compared with `d32` seq32 (`0.850821x`), so this is
  a GO for the fused-vs-split route and a warning that width pressure remains
  real.

## Aggregate Read

Across the fifteen checked rows:

- total lookup claims: `6,484`;
- total trace rows: `10,048`;
- total fused proof bytes: `1,398,430`;
- total matched source-plus-sidecar proof bytes: `1,696,600`;
- total fused savings against matched source-plus-sidecar: `298,170` bytes;
- matched fused ratios range from `0.676723` to `0.919259`.

## Open Issue #715 Gates

The route matrix is still an internal source-backed attention matrix. It does
not complete the full proof-pressure scaling issue.

Still open:

- no `d128` or `d256` attention row is checked in this matrix;
- no typed or binary/raw proof-size accounting is attached to these attention
  rows yet;
- no same-surface external baseline row is included;
- the `d64` slope has only one checked point, so `d64_two_head_seq16` remains
  the nearest adjacent falsification row.

## Claim Boundary

This is engineering proof-byte accounting for a fixed bounded integer
Softmax-table/floor-division fixture family. It is not:

- real-valued Softmax;
- implementation-exact model Softmax;
- full inference;
- timing evidence;
- public benchmark evidence;
- recursion or PCD.

## Validation

Regenerate the matrix:

```bash
python3 scripts/zkai_attention_kv_fused_softmax_table_route_matrix_gate.py \
  --write-json docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json \
  --write-tsv docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.tsv
```

Run the focused tests:

```bash
python3 -m unittest scripts.tests.test_zkai_attention_kv_fused_softmax_table_route_matrix_gate
```
