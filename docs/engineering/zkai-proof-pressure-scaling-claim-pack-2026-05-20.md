# ZKAI proof-pressure scaling claim pack

Issue: <https://github.com/omarespejel/provable-transformer-vm/issues/715>

## Decision

`GO_BOUNDED_SCALE_SIGNAL_SYNTHESIS_KEEP_ISSUE_OPEN_FOR_FULL_GRID`

This note pins the current bounded evidence for the next paper path. It is a
claim pack over checked artifacts, not a new proof-generation route.

Issue #715 stays open after this claim-pack slice. The full d64/d128/d256 grid,
seq64 row, and one matched external baseline are still follow-up work.

## Result

The checked attention evidence now has two bounded views. The older typed
component grid still gives the strictest typed accounting signal:

| metric | value |
|---|---:|
| checked attention rows | `10` |
| rows where fused beats split typed bytes | `10 / 10` |
| total typed saving across attention rows | `51,288` bytes |
| d8 single-head seq8 lookup claims | `52` |
| d8 two-head seq32 lookup claims | `1,184` |
| lookup growth | `22.769231x` |
| fused typed-byte growth | `1.264401x` |
| d8 single-head typed bytes per lookup claim | `348.538462` |
| d8 two-head seq32 typed bytes per lookup claim | `19.354730` |

The newer route matrix adds raw proof-byte evidence across `14` matched
source-plus-sidecar rows:

| metric | value |
|---|---:|
| checked route rows | `14` |
| total lookup claims | `5,300` |
| total trace rows | `8,000` |
| fused raw proof bytes | `1,145,173` |
| source plus sidecar raw proof bytes | `1,411,498` |
| aggregate raw proof-byte saving | `266,325` bytes |
| d32 two-head seq32 fused proof bytes | `150,147` |
| d32 two-head seq32 source plus sidecar bytes | `176,473` |
| d32 two-head seq32 raw saving | `26,326` bytes |

The d32 two-head sequence ladder is the new useful signal:

| comparison | lookup growth | trace-row growth | fused raw proof-byte growth |
|---|---:|---:|---:|
| seq8 to seq32 | `11.384615x` | `16.000000x` | `1.193955x` |
| seq16 to seq32 | `3.523810x` | `4.000000x` | `1.132817x` |

The current seq32+d128 boundary rows are:

| row | typed bytes | matched frontier | saving |
|---|---:|---:|---:|
| native seq32+d128 single proof | `42,068` | `47,188` | `5,120` |
| statement-only probe B | `39,516` | `47,188` | `7,672` |

The `statement_only_probe_b` row is the current best inner-policy-bound local
row. It is not a NANOZK comparison and not a full block proof.

Binary/raw status is explicit. The two seq32+d128 boundary rows include local
record-stream accounting (`1,084` bytes each), but that is not stable upstream
Stwo wire serialization. The attention route matrix records raw JSON proof
bytes, not stable upstream binary proof serialization. The typed attention
claim remains bounded to the controlled component grid.

## Provenance

| object | evidence | context |
|---|---|---|
| attention grid | `docs/engineering/evidence/zkai-attention-kv-stwo-controlled-component-grid-2026-05.json` | `10` local checked Stwo attention/table profiles; proof-size accounting only |
| attention route matrix | `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json` | `14` matched source-plus-sidecar route rows; raw JSON proof bytes only |
| native seq32+d128 single proof | `docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.json` and `.envelope.json` | backend `stwo`, version `stwo-native-seq32-attention-mlp-single-proof-object-native-adapter-v1` |
| statement-only probe B | `docs/engineering/evidence/zkai-stwo-statement-only-attempt-transcript-gate-2026-05.json` and `zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.envelope.json` | backend `stwo`, version `stwo-native-seq32-attention-mlp-single-proof-object-rmsnorm-input-fused-adjacent-fixed-v1`; attempt policy stays statement-bound |
| local binary accounting | `docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-binary-accounting-2026-05.json`, `zkai-native-seq32-attention-mlp-statement-only-attempt-accounting-2026-05.json`, `zkai-attention-kv-stwo-binary-typed-proof-accounting-2026-05.json`, `zkai-seq32-derived-d128-rmsnorm-mlp-fused-binary-accounting-2026-05.json` | local typed and record-stream accounting; no upstream Stwo serialization claim |
| timing context | `docs/engineering/evidence/zkai-native-seq32-attention-mlp-median-timing-2026-05.json` | median-of-5 engineering-local timing only; not a public benchmark |

## Interpretation

The interesting signal is still the same, but now it is packaged in a stricter
way. In the typed grid, lookup/table work grows much faster than typed proof
bytes. In the raw route matrix, the d32 two-head ladder repeats the pattern:
from seq8 to seq32, lookup claims grow `11.384615x` and trace rows grow
`16.000000x`, while fused raw proof bytes grow only `1.193955x`. The current
seq32+d128 native boundary still beats the matched local two-proof frontier
after statement binding is kept inside the proof-facing object.

This supports a bounded paper claim:

> STARK-native transformer proof boundaries can amortize lookup-heavy proof
> pressure while preserving typed statement validity.

The claim is not that the system proves a full model, beats NANOZK, or has a
matched external zkML benchmark.

## External Baselines

The gate includes external rows only as status labels:

| system | status |
|---|---|
| EZKL | local statement-envelope row only; not proof-size comparable |
| d64 external adapter surface | local no-go for vanilla exact export; not proof-size comparable |
| Jolt Atlas | repo/source context exists; not locally reproduced as a matched workload |
| NANOZK | paper-reported context only; not locally reproduced |

There are still zero proof-size-comparable external rows.

## Open Follow-Ups

The claim pack keeps three open follow-ups explicit:

- add or reject d64/d128/d256 attention-grid rows without widening the claim;
- add or reject a seq64 attention row;
- add one real apples-to-apples external baseline, starting with EZKL or a
  zkVM only if the scoped transformer surface and statement policy match.

## Evidence

- Claim-pack JSON:
  `docs/engineering/evidence/zkai-proof-pressure-scaling-claim-pack-2026-05.json`
- Claim-pack TSV:
  `docs/engineering/evidence/zkai-proof-pressure-scaling-claim-pack-2026-05.tsv`
- Gate script:
  `scripts/zkai_proof_pressure_scaling_claim_pack_gate.py`
- Gate tests:
  `scripts/tests/test_zkai_proof_pressure_scaling_claim_pack_gate.py`

The gate rejects `16 / 16` mutation cases covering lookup-growth drift,
typed-growth drift, route-matrix row-count drift, d32 seq32 raw-saving drift,
attention saving drift, native-boundary saving drift, statement-only saving
drift, external comparability overclaim, d64/d128/d256 completion overclaim,
stable binary serialization overclaim, public benchmark overclaim, non-claim
removal, source-artifact digest/path/manifest drift, validation-command drift,
and payload-commitment drift.

## Validation

```bash
python3.10 scripts/zkai_proof_pressure_scaling_claim_pack_gate.py --write-json docs/engineering/evidence/zkai-proof-pressure-scaling-claim-pack-2026-05.json --write-tsv docs/engineering/evidence/zkai-proof-pressure-scaling-claim-pack-2026-05.tsv
python3.10 -m py_compile scripts/zkai_proof_pressure_scaling_claim_pack_gate.py scripts/tests/test_zkai_proof_pressure_scaling_claim_pack_gate.py
python3.10 -m unittest scripts.tests.test_zkai_proof_pressure_scaling_claim_pack_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_controlled_component_grid_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_fused_softmax_table_route_matrix_gate
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_single_proof_gate
python3.10 -m unittest scripts.tests.test_zkai_stwo_statement_only_attempt_transcript_gate
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_median_timing_gate
git diff --check
just gate-fast
just gate
```

## Non-Claims

- Not a d64/d128/d256 attention grid.
- Not a seq64 proof row.
- Not a full transformer block proof.
- Not a NANOZK proof-size win.
- Not a Jolt Atlas proof-size win.
- Not an EZKL proof-size win.
- Not a matched external zkML benchmark.
- Not stable upstream Stwo binary serialization.
- Not exact real-valued Softmax.
- Not production-ready zkML.
