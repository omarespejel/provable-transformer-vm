# ZKAI proof-pressure scaling claim pack

Issue: <https://github.com/omarespejel/provable-transformer-vm/issues/715>

## Decision

`GO_BOUNDED_SCALE_SIGNAL_SYNTHESIS_KEEP_ISSUE_OPEN_FOR_FULL_GRID`

This note pins the current bounded evidence for the next paper path. It is a
claim pack over checked artifacts, not a new proof-generation route.

Issue #715 stays open after this claim-pack slice. The d64 and d128 attention
rows now give useful slope evidence, and the first d256 width-stress row is
checked. The next unresolved question is whether d256 keeps the sequence-axis
signal at `seq64`; one matched external baseline is still follow-up work.

## Result

The checked attention evidence has two bounded views. The older typed component
grid still gives the strictest typed accounting signal:

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

The newer route matrix adds raw proof-byte evidence across `30` matched
source-plus-sidecar rows:

| metric | value |
|---|---:|
| checked route rows | `30` |
| total lookup claims | `45,652` |
| total trace rows | `80,704` |
| fused raw proof bytes | `6,397,632` |
| source plus sidecar raw proof bytes | `7,164,515` |
| aggregate raw proof-byte saving | `766,883` bytes |
| d128 single-head seq16 fused proof bytes | `380,342` |
| d128 single-head seq16 source plus sidecar bytes | `397,313` |
| d128 single-head seq16 raw saving | `16,971` bytes |
| d128 four-head seq64 fused proof bytes | `495,854` |
| d128 four-head seq64 source plus sidecar bytes | `539,670` |
| d128 four-head seq64 raw saving | `43,816` bytes |
| d256 two-head seq32 fused proof bytes | `821,398` |
| d256 two-head seq32 source plus sidecar bytes | `851,541` |
| d256 two-head seq32 raw saving | `30,143` bytes |

The useful slope signals are:

| comparison | lookup growth | trace-row growth | fused raw proof-byte growth |
|---|---:|---:|---:|
| d32 two-head seq8 to seq32 | `11.384615x` | `16.000000x` | `1.193955x` |
| d64 four-head seq32 to seq64 | `3.729730x` | `4.000000x` | `1.080558x` |
| d128 two-head seq32 to seq64 | `3.729730x` | `4.000000x` | `1.080697x` |
| d128 four-head seq32 to seq64 | `3.729730x` | `4.000000x` | `1.064910x` |
| d64 seq16 one head to four heads | `4.000000x` | `4.000000x` | `0.999457x` |
| d128 seq32 two heads to four heads | `2.000000x` | `2.000000x` | `1.044276x` |

The width-anchor signal is intentionally more modest:

| comparison | lookup growth | trace-row growth | fused raw proof-byte growth | saving growth |
|---|---:|---:|---:|---:|
| d64 to d128 single-head seq16 | `1.000000x` | `1.000000x` | `1.599924x` | `1.019279x` |
| d128 to d256 two-head seq32 | `1.000000x` | `1.000000x` | `1.842162x` | `0.930684x` |

This matters because it keeps the paper claim honest. Lookup-heavy sequence and
head pressure are where fusion looks strongest. Width pressure grows proof
bytes without adding lookup claims. The d256 seq32 row is still positive on raw
proof bytes, but local timing is not a speed win, so `d256_h2_seq64` is the
next real falsification target.

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
| attention route matrix | `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json` | `30` matched source-plus-sidecar route rows; raw JSON proof bytes only |
| fuller crossing grid | `docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json` | `30 / 120` source-backed cells; not promoted into a full-grid claim |
| native seq32+d128 single proof | `docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.json` and `.envelope.json` | backend `stwo`, version `stwo-native-seq32-attention-mlp-single-proof-object-native-adapter-v1` |
| statement-only probe B | `docs/engineering/evidence/zkai-stwo-statement-only-attempt-transcript-gate-2026-05.json` and `zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.envelope.json` | backend `stwo`, version `stwo-native-seq32-attention-mlp-single-proof-object-rmsnorm-input-fused-adjacent-fixed-v1`; attempt policy stays statement-bound |
| local binary accounting | `docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-binary-accounting-2026-05.json`, `zkai-native-seq32-attention-mlp-statement-only-attempt-accounting-2026-05.json`, `zkai-attention-kv-stwo-binary-typed-proof-accounting-2026-05.json`, `zkai-seq32-derived-d128-rmsnorm-mlp-fused-binary-accounting-2026-05.json` | local typed and record-stream accounting; no upstream Stwo serialization claim |
| timing context | `docs/engineering/evidence/zkai-native-seq32-attention-mlp-median-timing-2026-05.json` | median-of-5 engineering-local timing only; not a public benchmark |

## Interpretation

The interesting signal is still the same, but it is now packaged in a stricter
way. In the typed grid, lookup/table work grows much faster than typed proof
bytes. In the raw route matrix, the d64 and d128 sequence rows repeat the same
shape: lookup claims grow `3.729730x` and trace rows grow `4.000000x`, while
fused raw proof bytes grow only about `1.06x` to `1.08x`.

The new d128 single-head seq16 row is a useful counterweight. It still saves
bytes against split, but it shows width-only pressure is not where the
amortization is strongest.

The d256 two-head seq32 row confirms that the width-stress path still saves raw
proof bytes, but with a weaker ratio: `0.964602x` fused versus split. Its
median-of-5 local timing is slower than the split comparator, so the claim
stays about proof-size amortization and boundary selection, not prover speed.

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

- add d256 seq64 without widening the claim;
- use `d256_h2_seq64` as the next sequence decision gate;
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

The gate rejects `31 / 31` mutation cases covering lookup-growth drift,
typed-growth drift, route-matrix row-count drift, route-ratio drift, d32 seq32
raw-saving drift, d64 and d128 axis-signal drift, route-derived summary drift,
the d256 width-stress signal,
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
python3.10 -m unittest scripts.tests.test_zkai_attention_kv_fuller_crossing_grid_gate
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_single_proof_gate
python3.10 -m unittest scripts.tests.test_zkai_stwo_statement_only_attempt_transcript_gate
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_median_timing_gate
git diff --check
```

## Non-Claims

- Not a complete d64/d128/d256 attention grid.
- Not a complete seq64 grid.
- Not a full transformer block proof.
- Not a NANOZK proof-size win.
- Not a Jolt Atlas proof-size win.
- Not an EZKL proof-size win.
- Not a matched external zkML benchmark.
- Not stable upstream Stwo binary serialization.
- Not exact real-valued Softmax.
- Not production-ready zkML.
