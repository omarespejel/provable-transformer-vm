# d32 Two-Head Seq32 Fused Softmax-Table Gate

Date: 2026-05-21

Issue: #720

## Result

This slice extends the checked d32/two-head fused Softmax-table route from seq16 to seq32.

The local native Stwo route verifies one fused proof object for bounded attention arithmetic plus LogUp Softmax-table membership:

- source arithmetic proof: `145,497` JSON proof bytes
- LogUp sidecar proof: `30,976` JSON proof bytes
- matched split frontier: `176,473` JSON proof bytes
- fused proof: `150,147` JSON proof bytes
- fused saving: `26,326` JSON proof bytes
- fused ratio: `0.850821x`
- lookup claims: `1,184`
- trace rows: `2,048`

The fused proof is `4,650` bytes larger than the source arithmetic proof alone, but it replaces the matched source-plus-sidecar frontier and saves `26,326` bytes against that honest comparator.

## Scaling Signal

The useful sequence ladder is now:

| profile | lookup claims | trace rows | split proof bytes | fused proof bytes | fused ratio |
|---|---:|---:|---:|---:|---:|
| `d32_two_head_seq8` | `104` | `128` | `142,063` | `125,756` | `0.885213x` |
| `d32_two_head_seq16` | `336` | `512` | `162,138` | `132,543` | `0.817470x` |
| `d32_two_head_seq32` | `1,184` | `2,048` | `176,473` | `150,147` | `0.850821x` |

From seq16 to seq32:

- lookup claims grow `3.523810x`
- trace rows grow `4.000000x`
- matched split proof bytes grow `1.088412x`
- fused proof bytes grow `1.132817x`

From seq8 to seq32:

- lookup claims grow `11.384615x`
- trace rows grow `16.000000x`
- matched split proof bytes grow `1.242216x`
- fused proof bytes grow `1.193955x`

This supports the narrow proof-pressure claim: lookup-heavy work and trace rows grow much faster than proof bytes in this bounded fixture family.

## Matrix Impact

The controlled route matrix now has:

- `14` matched route rows
- `5,300` total lookup claims
- `8,000` total trace rows
- `1,411,498` matched split proof bytes
- `1,145,173` fused proof bytes
- `266,325` aggregate fused proof-byte savings

The fuller crossing grid is now `14 / 45` proved and `31 / 45` missing.

## Correctness Discipline

The seq32 route keeps the existing local-only validation discipline:

- source, sidecar, and fused proof envelopes verify with the native Stwo CLI
- sidecar gate rejects `28 / 28` mutation cases
- fused gate rejects `30 / 30` mutation cases
- the route matrix and fuller grid reject metric drift and overclaim drift
- evidence is bound by source commitments, proof-envelope commitments, table multiplicities, verifier domains, statement versions, and non-claim text

## Non-Claims

This is not exact real-valued Softmax. It is not full autoregressive inference. It is not a full transformer block. It is not recursion, PCD, private-witness privacy, on-chain verification, timing evidence, or a NANOZK comparison.

The current claim is narrower: in this native Stwo bounded Softmax-table attention family, the fused proof object continues to beat the matched source-plus-sidecar comparator at d32/two-head/seq32 while lookup work grows much faster than proof bytes.

## Reproduction

```bash
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_native_d32_two_head_seq32_bounded_softmax_table_proof_input scripts.tests.test_zkai_attention_kv_d32_two_head_seq32_air_private_softmax_table_lookup_gate scripts.tests.test_zkai_attention_kv_d32_two_head_seq32_fused_softmax_table_native_gate
cargo +nightly-2025-07-14 test --locked attention_kv_native_d32_two_head_seq32 --lib --features stwo-backend
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d32_two_head_seq32_bounded_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-two-head-seq32-bounded-softmax-table-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d32_two_head_seq32_softmax_table_lookup_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-two-head-seq32-softmax-table-logup-sidecar-proof-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d32_two_head_seq32_fused_softmax_table_proof -- verify docs/engineering/evidence/zkai-attention-kv-stwo-native-d32-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json
python3.10 scripts/zkai_attention_kv_fused_softmax_table_route_matrix_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.tsv
python3.10 scripts/zkai_attention_kv_fuller_crossing_grid_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.tsv
```
