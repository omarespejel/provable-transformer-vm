# Native Seq32 Attention+MLP Adjacent Probe-B Bucket Attribution

Date: 2026-05-19
Issue: https://github.com/omarespejel/provable-transformer-vm/issues/693

## Decision

`NARROW_CLAIM_PATH_OPENING_BUCKET_ATTRIBUTED_NO_SOURCE_PREDICTOR`

This gate does not generate a new frontier proof. It explains the existing
`37,532` typed-byte adjacent probe-B row by comparing the local binary
accounting groups against the best pre-registered seed, the probe-A-shaped
seed, and the fixed adjacent layout.

## Result

| comparison | typed gap vs probe B | path-opening gap | value-byte gap | FRI decommitments | FRI samples | trace decommitments |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `adjacent_seed_02` | `2,736` | `2,736` | `0` | `2,016` | `80` | `640` |
| `adjacent_seed_05` | `2,800` | `2,800` | `0` | `2,080` | `80` | `640` |
| `fixed_adjacent_layout` | `4,624` | `4,624` | `0` | `3,456` | `144` | `1,024` |

The important row is the first one. The best pre-registered seed is still
`2,736` typed bytes heavier than probe B, and the entire gap is opening
plumbing:

- direct value bytes are equal at `20,924`;
- fixed overhead is equal at `48`;
- the gap is `2,016` FRI decommitment bytes, `80` FRI sample bytes, and `640`
  trace decommitment bytes.

## Human Read

This is a useful narrowing result. Probe B is not smaller because it checks
less application value data. It is smaller because the Fiat-Shamir/opening
transcript lands in a better decommitment bucket.

That keeps the fusion thesis alive: proof plumbing is a real source of savings.
But it also blocks promotion into a production label policy. We can attribute
the bucket after the proof/accounting exists; we still cannot predict the small
bucket from source-exposed fields before proving.

## Claim Boundary

The checked claim is only:

> The adjacent probe-B edge over the best pre-registered adjacent seed is fully
> attributable to FRI/sample/trace opening groups, not direct opened values; no
> source-exposed bucket predictor is established.

Non-claims:

- not a new proof-size frontier;
- not a source-exposed deterministic label policy;
- not a production label-selection policy;
- not a NANOZK proof-size win;
- not a matched external zkML benchmark;
- not a full transformer block proof;
- not exact real-valued Softmax;
- not timing evidence;
- not production-ready zkML.

## Evidence

- Gate JSON:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-probe-b-bucket-attribution-2026-05.json`
- Gate TSV:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-probe-b-bucket-attribution-2026-05.tsv`
- Source accounting:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-accounting-2026-05.json`
- Gate JSON SHA-256:
  `d2bc8e08a4cb139b8e82f5d5fae339f957a06eebb1fe0f604989604147792b81`
- Gate TSV SHA-256:
  `b2cb451373031633b4be444c451ce571ac89ccd86d8b2c5e44a1e0832ec069ab`
- Source accounting SHA-256:
  `90f04ada7e02f3777615417dec475c27ccff3511f42be0a084e6405b52fcd6db`
- Payload commitment:
  `blake2b-256:ff356aa053c297b3178d6b0d9429d339a3abf1f3543e34ba92801ee1af750526`
- Mutation guards:
  `13 / 13` rejected.

The gate rejects decision drift, overclaim drift, source digest drift,
accounting digest drift, frontier typed-byte drift, value-byte drift, seed-02
delta drift, source-predictor promotion, comparison-row erasure, record-stream
erasure, removed non-claims, validation-command drift, and payload-commitment
drift.

## Reproduction

```bash
python3.10 scripts/zkai_native_seq32_attention_mlp_adjacent_probe_b_bucket_attribution_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-probe-b-bucket-attribution-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-probe-b-bucket-attribution-2026-05.tsv
python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_adjacent_probe_b_bucket_attribution_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_adjacent_probe_b_bucket_attribution_gate.py
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_adjacent_probe_b_bucket_attribution_gate
git diff --check
just gate-fast
just gate
```

## Next Attack

Follow-up issue:
https://github.com/omarespejel/provable-transformer-vm/issues/695.

Stop broad label guessing unless a source-visible predictor is added. The next
useful experiment is a pre-prove query/opening inventory: expose enough
transcript data to test whether a deterministic rule can predict the smaller
opening bucket before generating the proof. If that cannot be done, this label
path should be treated as an attribution result, not a breakthrough path.
