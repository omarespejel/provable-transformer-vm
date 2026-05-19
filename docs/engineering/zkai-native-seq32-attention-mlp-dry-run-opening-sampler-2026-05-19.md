# zkai native seq32 attention MLP dry-run opening sampler

Date: 2026-05-19

Issue: https://github.com/omarespejel/provable-transformer-vm/issues/697

## Result

Decision:

`GO_QUERY_LOCATION_SAMPLER_PREDICTS_CHECKED_ADJACENT_OPENING_BUCKETS`

The prior pre-prove source-visible inventory was a real NO-GO: all adjacent
rows shared the same structural source signature while final path-opening
buckets split across five values. This follow-up adds a stricter sampler that
uses Stwo prover-internal query locations from `ExtendedStarkProof::aux`, not
envelope JSON, proof bytes, grouped proof accounting, record streams, or final
proof-size rows.

Across the checked adjacent inventory, query-location geometry predicts all
nine final path-opening buckets. The smallest row is still
`adjacent_label_probe_b`: its three sampled query locations form the tightest
cluster, with query span `16,618`, and it lands in the `16,560` typed-byte
path-opening bucket.

## Checked rows

| variant | query span | min pairwise query gap | predicted path-opening bytes | final path-opening bytes |
|---|---:|---:|---:|---:|
| adjacent_label_probe_b | 16,618 | 5,969 | 16,560 | 16,560 |
| adjacent_seed_02 | 86,468 | 32,220 | 19,296 | 19,296 |
| adjacent_label_probe_a | 110,651 | 14,670 | 19,360 | 19,360 |
| adjacent_seed_05 | 125,812 | 15,995 | 19,360 | 19,360 |
| adjacent_seed_01 | 145,631 | 49,574 | 20,512 | 20,512 |
| adjacent_seed_00 | 180,956 | 34,301 | 20,512 | 20,512 |
| fixed_adjacent_layout | 291,186 | 30,179 | 21,184 | 21,184 |
| adjacent_seed_03 | 391,501 | 80,748 | 21,184 | 21,184 |
| adjacent_seed_04 | 422,330 | 57,938 | 21,184 | 21,184 |

## Why this matters

This is a useful research advance, not a new proof-size frontier. It says the
remaining opening-bucket behavior is not random label luck and not visible from
the source inventory alone. The lever is lower in the proof system: query and
opening geometry after transcript commitments.

For the paper path, this sharpens the architecture claim:

> STARK-native transformer proof boundaries need to optimize not only which
> arithmetic and lookup components are fused, but also how the fused boundary
> shapes the transcript queries and Merkle opening overlap.

## Evidence

Machine-readable evidence:

- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-dry-run-opening-sampler-2026-05.json`
- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-dry-run-opening-sampler-2026-05.tsv`

Raw sampler artifacts:

- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05-opening-sampler-2026-05.json`
- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05-opening-sampler-2026-05.json`
- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05-opening-sampler-2026-05.json`
- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-00-2026-05-opening-sampler-2026-05.json`
- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-01-2026-05-opening-sampler-2026-05.json`
- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-02-2026-05-opening-sampler-2026-05.json`
- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-03-2026-05-opening-sampler-2026-05.json`
- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-04-2026-05-opening-sampler-2026-05.json`
- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-05-2026-05-opening-sampler-2026-05.json`

Mutation coverage:

- `15 / 15` mutation guards rejected drift.

## Reproduction commands

```sh
cargo +nightly-2025-07-14 test --locked --features stwo-backend native_seq32_attention_mlp_single_proof --lib
cargo +nightly-2025-07-14 build --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof
for input in docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent*2026-05.input.json; do output="${input%.input.json}-opening-sampler-2026-05.json"; target/debug/zkai_native_seq32_attention_mlp_single_proof sample-openings "$input" "$output"; done
python3.10 scripts/zkai_native_seq32_attention_mlp_dry_run_opening_sampler_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-dry-run-opening-sampler-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-dry-run-opening-sampler-2026-05.tsv
python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_dry_run_opening_sampler_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_dry_run_opening_sampler_gate.py
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_dry_run_opening_sampler_gate
git diff --check
just gate-fast
just gate
```

## Non-claims

- Not a production label-selection policy.
- Not a new proof-size frontier.
- Not a NANOZK proof-size win.
- Not a matched external zkML benchmark.
- Not a full transformer block proof.
- Not timing evidence.
- Not production-ready zkML.

## Next gate

The next useful step is a pre-decommitment sampler or layout policy that can
choose transcript/query geometry before full proof generation, then rerun the
larger boundary under that policy. Until then, this remains a checked mechanism
lead rather than a production proof-size optimization.
