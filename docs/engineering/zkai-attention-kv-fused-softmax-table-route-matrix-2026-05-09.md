# zkAI Attention/KV Fused Softmax-Table Route Matrix - 2026-05-09

## Question

Do the checked native Stwo fused Softmax-table routes keep saving proof bytes
against the honest source-plus-LogUp-sidecar frontier as width, head count, and
sequence length are varied?

The matrix is proof-byte accounting only. It is not timing evidence, exact
real-valued Softmax, full inference, recursion, PCD, or a public benchmark.

## Decision

`GO_NATIVE_STWO_FUSED_SOFTMAX_TABLE_CONTROLLED_ROUTE_MATRIX`

The route matrix now has matched source-plus-LogUp-sidecar comparators for all
`17` checked profile rows and rejects `45 / 45` matrix drift, provenance drift,
and overclaim mutations.

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
| `d32_two_head_seq32` | 32 | 2 | 32 | 1,184 | 2,048 | 150,147 | 176,473 | 26,326 | 0.850821 |
| `d64_two_head_seq16` | 64 | 2 | 16 | 336 | 512 | 238,504 | 257,725 | 19,221 | 0.925421 |
| `d64_two_head_seq32` | 64 | 2 | 32 | 1,184 | 2,048 | 253,257 | 285,102 | 31,845 | 0.888303 |

## Current Signal

The strongest evidence is still structural amortization, not a full zkML
benchmark.

At fixed `d16` and two heads, moving from `seq16` to `seq32` grows checked
lookup work from `336` to `1,184` claims (`3.523810x`) and trace rows from
`512` to `2,048` (`4.000000x`). The fused proof grows from `84,868` to
`92,363` bytes (`1.088314x`).

At fixed `d64` and two heads, moving from `seq16` to `seq32` grows the same
lookup and trace axes while fused proof bytes grow `1.061856x`.

That is the proof-pressure signal worth attacking: sequence-driven lookup work
is growing much faster than the fused proof object. Width is different. At
fixed `seq32`, widening from `d16` to `d32` grows fused proof bytes
`1.625618x`, and widening from `d32` to `d64` grows them `1.686727x`.

## Aggregate Read

Across the `17` checked rows:

- total lookup claims: `8,004`;
- total trace rows: `12,608`;
- total matched source-plus-sidecar proof bytes: `2,081,532`;
- total fused proof bytes: `1,729,297`;
- total fused savings against matched source-plus-sidecar: `352,235` bytes;
- matched fused ratios range from `0.676723` to `0.925421`.

## Open Issue #715 Gates

The matrix is still an internal source-backed bounded Softmax-table attention
family. It does not complete the full proof-pressure scaling issue.

Still open:

- no `d128` or `d256` attention row is checked in this matrix;
- no typed or binary/raw proof-size accounting is attached to these attention
  rows yet;
- no same-surface external baseline row is included;
- no timing claim is attached;
- no full transformer block or model-faithful Softmax claim is attached.

## Claim Boundary

This may be cited internally as:

> In the checked native Stwo bounded Softmax-table attention family, every one
> of the `17` matched fused routes beats its source-plus-LogUp-sidecar
> comparator, and the `seq16` to `seq32` rows show lookup work growing much
> faster than fused proof bytes at fixed width.

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
