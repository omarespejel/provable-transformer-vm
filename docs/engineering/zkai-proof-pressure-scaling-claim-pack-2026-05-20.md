# ZKAI proof-pressure scaling claim pack

Issue: <https://github.com/omarespejel/provable-transformer-vm/issues/715>

## Decision

`GO_BOUNDED_SCALE_SIGNAL_SYNTHESIS_NO_GO_FULL_BLOCK_OR_EXTERNAL_WIN`

This note pins the current bounded evidence for the next paper path. It is a
claim pack over checked artifacts, not a new proof-generation route.

## Result

The checked attention grid still gives the strongest scaling signal:

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

The current seq32+d128 boundary rows are:

| row | typed bytes | matched frontier | saving |
|---|---:|---:|---:|
| native seq32+d128 single proof | `42,068` | `47,188` | `5,120` |
| statement-only probe B | `39,516` | `47,188` | `7,672` |

The `statement_only_probe_b` row is the current best inner-policy-bound local
row. It is not a NANOZK comparison and not a full block proof.

## Interpretation

The interesting signal is still the same, but now it is packaged in a stricter
way: the lookup/table work can grow much faster than the proof-byte accounting,
and the current seq32+d128 native boundary beats the matched local two-proof
frontier after statement binding is kept inside the proof-facing object.

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

The gate rejects `14 / 14` mutation cases covering lookup-growth drift,
typed-growth drift, attention saving drift, native-boundary saving drift,
statement-only saving drift, external comparability overclaim, d64/d128/d256
completion overclaim, stable binary serialization overclaim, public benchmark
overclaim, non-claim removal, source-artifact drift, missing source artifact,
validation-command drift, and payload-commitment drift.

## Validation

```bash
python3.10 scripts/zkai_proof_pressure_scaling_claim_pack_gate.py --write-json docs/engineering/evidence/zkai-proof-pressure-scaling-claim-pack-2026-05.json --write-tsv docs/engineering/evidence/zkai-proof-pressure-scaling-claim-pack-2026-05.tsv
python3.10 -m py_compile scripts/zkai_proof_pressure_scaling_claim_pack_gate.py scripts/tests/test_zkai_proof_pressure_scaling_claim_pack_gate.py
python3.10 -m unittest scripts.tests.test_zkai_proof_pressure_scaling_claim_pack_gate
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_controlled_component_grid_gate
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
