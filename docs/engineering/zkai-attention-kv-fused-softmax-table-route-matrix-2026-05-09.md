# zkAI Attention/KV Fused Softmax-Table Route Matrix - 2026-05-09

## Question

Do the checked native Stwo fused Softmax-table routes keep saving proof bytes
against the honest source-plus-LogUp-sidecar frontier as width, head count, and
sequence length are varied?

The matrix is proof-byte accounting only. It is not timing evidence, exact
real-valued Softmax, full inference, recursion, PCD, or a public benchmark.

## Decision

`GO_NATIVE_STWO_FUSED_SOFTMAX_TABLE_CONTROLLED_ROUTE_MATRIX`

The route matrix now has matched source-plus-LogUp-sidecar comparators for
`29` checked profile rows and rejects route-matrix drift, provenance drift, and
overclaim mutations.

Machine-readable evidence:

- JSON: `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`
- TSV: `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.tsv`

## Route Matrix

| profile | d | heads | steps/head | lookup claims | trace rows | fused proof bytes | source+sidecar bytes | saving | fused ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `d8_single_head_seq8` | 8 | 1 | 8 | 52 | 64 | 47,698 | 59,437 | 11,739 | 0.802497 |
| `d16_single_head_seq8` | 16 | 1 | 8 | 52 | 64 | 64,503 | 74,961 | 10,458 | 0.860487 |
| `d32_single_head_seq8` | 32 | 1 | 8 | 52 | 64 | 107,261 | 116,682 | 9,421 | 0.919259 |
| `d8_two_head_seq8` | 8 | 2 | 8 | 104 | 128 | 49,508 | 65,208 | 15,700 | 0.759232 |
| `d8_four_head_seq8` | 8 | 4 | 8 | 208 | 256 | 53,468 | 74,529 | 21,061 | 0.717412 |
| `d8_eight_head_seq8` | 8 | 8 | 8 | 416 | 512 | 59,375 | 74,086 | 14,711 | 0.801433 |
| `d8_sixteen_head_seq8` | 8 | 16 | 8 | 832 | 1,024 | 65,006 | 88,711 | 23,705 | 0.732784 |
| `d8_two_head_seq16` | 8 | 2 | 16 | 336 | 512 | 60,502 | 79,444 | 18,942 | 0.761568 |
| `d8_two_head_seq32` | 8 | 2 | 32 | 1,184 | 2,048 | 66,327 | 98,012 | 31,685 | 0.676723 |
| `d16_two_head_seq8` | 16 | 2 | 8 | 104 | 128 | 78,211 | 91,596 | 13,385 | 0.853869 |
| `d32_two_head_seq8` | 32 | 2 | 8 | 104 | 128 | 125,756 | 142,063 | 16,307 | 0.885213 |
| `d16_two_head_seq16` | 16 | 2 | 16 | 336 | 512 | 84,868 | 108,158 | 23,290 | 0.784667 |
| `d16_two_head_seq32` | 16 | 2 | 32 | 1,184 | 2,048 | 92,363 | 127,207 | 34,844 | 0.726084 |
| `d32_two_head_seq16` | 32 | 2 | 16 | 336 | 512 | 132,543 | 162,138 | 29,595 | 0.817470 |
| `d32_four_head_seq16` | 32 | 4 | 16 | 672 | 1,024 | 142,334 | 170,018 | 27,684 | 0.837170 |
| `d32_two_head_seq32` | 32 | 2 | 32 | 1,184 | 2,048 | 150,147 | 176,473 | 26,326 | 0.850821 |
| `d32_four_head_seq32` | 32 | 4 | 32 | 2,368 | 4,096 | 154,670 | 192,937 | 38,267 | 0.801661 |
| `d64_single_head_seq16` | 64 | 1 | 16 | 168 | 256 | 237,725 | 254,375 | 16,650 | 0.934545 |
| `d64_two_head_seq16` | 64 | 2 | 16 | 336 | 512 | 238,504 | 257,725 | 19,221 | 0.925421 |
| `d64_four_head_seq16` | 64 | 4 | 16 | 672 | 1,024 | 237,596 | 260,685 | 23,089 | 0.911430 |
| `d64_two_head_seq32` | 64 | 2 | 32 | 1,184 | 2,048 | 253,257 | 285,102 | 31,845 | 0.888303 |
| `d64_two_head_seq64` | 64 | 2 | 64 | 4,416 | 8,192 | 272,636 | 306,970 | 34,334 | 0.888152 |
| `d64_four_head_seq32` | 64 | 4 | 32 | 2,368 | 4,096 | 255,889 | 288,292 | 32,403 | 0.887604 |
| `d64_four_head_seq64` | 64 | 4 | 64 | 8,832 | 16,384 | 276,503 | 315,785 | 39,282 | 0.875605 |
| `d128_single_head_seq16` | 128 | 1 | 16 | 168 | 256 | 380,342 | 397,313 | 16,971 | 0.957286 |
| `d128_two_head_seq32` | 128 | 2 | 32 | 1,184 | 2,048 | 445,888 | 478,276 | 32,388 | 0.932282 |
| `d128_two_head_seq64` | 128 | 2 | 64 | 4,416 | 8,192 | 481,870 | 522,187 | 40,317 | 0.922792 |
| `d128_four_head_seq32` | 128 | 4 | 32 | 2,368 | 4,096 | 465,630 | 504,934 | 39,304 | 0.922160 |
| `d128_four_head_seq64` | 128 | 4 | 64 | 8,832 | 16,384 | 495,854 | 539,670 | 43,816 | 0.918810 |

## Current Signal

The strongest evidence is still structural amortization, not a full zkML
benchmark.

Sequence pressure is the clearest signal. At fixed `d128` and four heads,
moving from `seq32` to `seq64` grows lookup claims `3.729730x` and trace rows
`4.000000x`, while fused proof bytes grow only `1.064910x`. At fixed `d64` and
four heads, the same sequence jump grows fused proof bytes `1.080558x`.

Head pressure is also favorable. At fixed `d64` and `seq16`, moving from one
head to four heads grows lookup claims and trace rows `4.000000x`, while fused
proof bytes move to `0.999457x`. At fixed `d128` and `seq32`, moving from two
heads to four heads doubles lookup claims and trace rows, while fused proof
bytes grow `1.044276x`.

Width is the harder axis. At fixed one head and `seq16`, moving from `d64` to
`d128` keeps lookup claims and trace rows fixed while fused proof bytes grow
`1.599924x`. The `d128_single_head_seq16` row still saves `16,971` bytes
against split, but the saving is modest. This is why the next selector target
is `d256_h2_seq32`: it stress-tests width before scoped block work.

## Aggregate Read

Across the `29` checked rows:

- total lookup claims: `44,468`;
- total trace rows: `78,656`;
- total matched source-plus-sidecar proof bytes: `6,312,974`;
- total fused proof bytes: `5,576,234`;
- total fused savings against matched source-plus-sidecar: `736,740` bytes;
- matched fused ratios range from `0.676723` to `0.957286`.

## Open Issue #715 Gates

The matrix is still an internal source-backed bounded Softmax-table attention
family. It does not complete the full proof-pressure scaling issue.

Still open:

- no `d256` attention row is checked in this matrix;
- the `d64` and `d128` grids are still partial;
- no same-surface external baseline row is included;
- no timing claim is attached;
- no full transformer block or model-faithful Softmax claim is attached.

## Claim Boundary

This may be cited internally as:

> In the checked native Stwo bounded Softmax-table attention family, every one
> of the `29` matched fused routes beats its source-plus-LogUp-sidecar
> comparator. The strongest slope signal is on lookup-heavy sequence and head
> axes; width is the next falsification target.

Do not cite it as:

- real-valued Softmax;
- implementation-exact model Softmax;
- full inference;
- timing evidence;
- public benchmark evidence;
- recursion or PCD;
- a NANOZK comparison.

## Validation

```bash
python3.10 scripts/zkai_attention_kv_fused_softmax_table_route_matrix_gate.py \
  --write-json docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json \
  --write-tsv docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.tsv

python3.10 -m unittest scripts.tests.test_zkai_attention_kv_fused_softmax_table_route_matrix_gate
```
