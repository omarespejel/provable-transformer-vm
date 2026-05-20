# zkAI Attention/KV d32 Two-Head Seq16 Fused Softmax-Table Gate - 2026-05-21

## Question

Does the native Stwo fused Softmax-table route still save proof bytes when the
fixture crosses width, head count, and sequence length at `d32`, two heads, and
sixteen steps per head?

This slice is still the bounded integer Softmax-table/floor-division fixture,
not exact real-valued Softmax and not full inference.

## Decision

`GO_NATIVE_STWO_FUSED_ATTENTION_ARITHMETIC_AND_SOFTMAX_TABLE_LOGUP_MEMBERSHIP`

The route validates as one native fused proof object with a matched
source-plus-LogUp-sidecar comparator.

## Result

| Metric | Value |
|---|---:|
| key/value width | `32` |
| heads | `2` |
| steps per head | `16` |
| lookup claims | `336` |
| trace rows | `512` |
| source proof bytes | `135,063` |
| sidecar proof bytes | `27,075` |
| source+sidecar proof bytes | `162,138` |
| fused proof bytes | `132,543` |
| fused saving | `29,595` bytes |
| fused ratio | `0.817470x` |
| fused overhead over source | `-2,520` bytes |

The useful signal is stronger than a simple split-proof saving. The fused proof
is `29,595` bytes smaller than the matched source-plus-sidecar control and is
also `2,520` bytes smaller than the source arithmetic proof alone. This means
adding the LogUp table-membership relation did not merely avoid a standalone
sidecar; in this route the combined proof object landed below the arithmetic
source proof.

Against the previous `d32` two-head `seq8` row, lookup claims grow from `104` to
`336` (`3.230769x`) and trace rows grow from `128` to `512` (`4.000000x`), while
fused proof bytes grow from `125,756` to `132,543` (`1.053970x`). That is the
current strongest local amortization signal for the d32 width/head sequence
path.

## Evidence

- Source input:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-two-head-longseq-bounded-softmax-table-proof-2026-05.json`
- Source proof envelope:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-two-head-longseq-bounded-softmax-table-proof-2026-05.envelope.json`
- Sidecar proof envelope:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-two-head-longseq-softmax-table-logup-sidecar-proof-2026-05.envelope.json`
- Fused proof envelope:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-two-head-longseq-fused-softmax-table-proof-2026-05.envelope.json`
- Fused gate JSON:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-two-head-longseq-fused-softmax-table-gate-2026-05.json`
- Route matrix JSON:
  `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`
- Fuller crossing grid JSON:
  `docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json`

The source input gate rejects `21 / 21` source-shape and source-binding
mutations. The sidecar gate rejects `28 / 28` lookup, proof-envelope, metric,
and overclaim mutations. The fused gate rejects `30 / 30` fused-envelope,
source-binding, metric, proof-byte, and overclaim mutations.

## Route Matrix Impact

This row moves the checked route matrix to `13` matched rows:

- total lookup claims: `4,116`;
- total trace rows: `5,952`;
- total fused proof bytes: `995,026`;
- total matched source-plus-sidecar proof bytes: `1,235,025`;
- aggregate saving against matched source-plus-sidecar: `239,999` bytes;
- fuller grid coverage: `13 / 45` proved, `32 / 45` missing.

## Claim Boundary

This may be cited as:

> The `d32` two-head `seq16` fused Softmax-table route validates with a matched
> source-plus-sidecar comparator and saves `29,595` proof bytes
> (`0.817470x`). Compared with the `d32` two-head `seq8` row, lookup claims grow
> `3.230769x` while fused proof bytes grow only `1.053970x`.

Do not cite it as:

- exact real-valued Softmax;
- full transformer inference;
- a timing benchmark;
- a NANOZK comparison;
- recursion or PCD;
- production-ready zkML.

## Validation

```bash
python3.10 -m unittest \
  scripts.tests.test_zkai_attention_kv_stwo_native_d32_two_head_longseq_bounded_softmax_table_proof_input \
  scripts.tests.test_zkai_attention_kv_d32_two_head_longseq_air_private_softmax_table_lookup_gate \
  scripts.tests.test_zkai_attention_kv_d32_two_head_longseq_fused_softmax_table_native_gate

cargo +nightly-2025-07-14 test --locked \
  attention_kv_native_d32_two_head_longseq \
  --lib --features stwo-backend

cargo +nightly-2025-07-14 run --locked --features stwo-backend \
  --bin zkai_attention_kv_native_d32_two_head_longseq_fused_softmax_table_proof -- \
  verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-two-head-longseq-fused-softmax-table-proof-2026-05.envelope.json

python3.10 scripts/zkai_attention_kv_fused_softmax_table_route_matrix_gate.py \
  --write-json docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json \
  --write-tsv docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.tsv

python3.10 scripts/zkai_attention_kv_fuller_crossing_grid_gate.py \
  --write-json docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json \
  --write-tsv docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.tsv
```
