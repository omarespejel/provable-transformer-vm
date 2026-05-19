# Native Seq32 Attention+MLP Adjacent Label Seed Sweep

Date: 2026-05-19
Issue: https://github.com/omarespejel/provable-transformer-vm/issues/691

## Decision

`NO_GO_PRE_REGISTERED_ADJACENT_SEEDS_DO_NOT_BEAT_FRONTIER`

This gate pre-registers six adjacent-only label seeds, exposes each one through
the Rust source and CLI, generates real Stwo proof objects for every seed, and
reports all rows. The purpose is to test whether the prior adjacent probe-B
frontier is reproducible across a small seed family or just a favorable
transcript bucket.

## Result

| variant | typed bytes | JSON proof bytes | delta vs 37,532 frontier | path-opening bytes |
| --- | ---: | ---: | ---: | ---: |
| adjacent probe B | `37,532` | `106,317` | `0` | `16,560` |
| adjacent seed 02 | `40,268` | `115,995` | `+2,736` | `19,296` |
| adjacent seed 05 | `40,332` | `116,303` | `+2,800` | `19,360` |
| adjacent seed 00 | `41,484` | `120,158` | `+3,952` | `20,512` |
| adjacent seed 01 | `41,484` | `120,064` | `+3,952` | `20,512` |
| adjacent seed 03 | `42,156` | `122,588` | `+4,624` | `21,184` |
| adjacent seed 04 | `42,156` | `122,648` | `+4,624` | `21,184` |

Best seeded row: `adjacent_seed_02` at `40,268` typed bytes. It is better than
old adjacent probe A (`40,332`) by `64` typed bytes, but it remains `2,736`
typed bytes heavier than the `37,532` adjacent probe-B frontier.

Seed distribution:

- min: `40,268` typed bytes;
- median: `41,484` typed bytes;
- worst: `42,156` typed bytes;
- span: `1,888` typed bytes.

## Human Read

This is a useful NO-GO. The earlier adjacent probe-B result is not reproduced
by a simple pre-registered label seed family. Labels still matter, but blind
label seeding is not a robust compression mechanism yet.

The interesting new detail is that seeds collapse into proof-shape buckets:

- `seed-03` and `seed-04` match the fixed adjacent layout shape;
- `seed-00` and `seed-01` match each other;
- `seed-05` matches the old adjacent probe-A typed shape;
- `seed-02` is the best new bucket, but still misses the frontier.

So the next attack should not be broader seed guessing. It should inspect why
the adjacent probe-B transcript lands in the unusually small path-opening
bucket.

## Claim Boundary

The checked claim is only:

> A six-seed pre-registered adjacent-only label sweep does not reproduce the
> `37,532` typed-byte adjacent probe-B frontier; seeded labels fall into
> repeated opening/transcript buckets, with best seed `02` still `2,736` typed
> bytes above the frontier.

Non-claims:

- not a new proof-size frontier;
- not a production label-selection policy;
- not a NANOZK proof-size win;
- not a matched external zkML benchmark;
- not a full transformer block proof;
- not exact real-valued Softmax;
- not timing evidence;
- not production-ready zkML.

## Evidence

- Seed sweep accounting:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-accounting-2026-05.json`
- Gate JSON:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-2026-05.json`
- Gate TSV:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-2026-05.tsv`
- Seed inputs/envelopes:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-{00..05}-2026-05.{input,envelope}.json`
- Gate JSON SHA-256:
  `7c42d8b2d80cf4150059f894b706f06b0b125205bf8ea1be562f0938aea9d736`
- Gate TSV SHA-256:
  `10e7c26d4f912ad349c9cd47b0bb7c96cc8dd2a9d6ffb1d9321a05cfb62ac229`
- Accounting SHA-256:
  `90f04ada7e02f3777615417dec475c27ccff3511f42be0a084e6405b52fcd6db`
- Payload commitment:
  `blake2b-256:a775e08bbb5efc31221a9998b52a56fda5a414f389de3fd8fe9a2c64a26fb986`
- Mutation guards:
  `13 / 13` rejected.

The gate rejects decision drift, overclaim drift, source digest drift,
accounting digest drift, seed inventory erasure, frontier promotion, best-seed
typed-byte drift, adapter-mode relabeling, path-opening drift, shape-class
erasure, removed non-claims, validation-command drift, and payload-commitment
drift.

## Reproduction

```bash
for seed in 00 01 02 03 04 05; do
  cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- "build-input-rmsnorm-fused-adjacent-seed-$seed" docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json "docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-$seed-2026-05.input.json"
  cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove "docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-$seed-2026-05.input.json" "docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-$seed-2026-05.envelope.json"
  cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify "docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-$seed-2026-05.envelope.json"
done
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-00-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-01-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-02-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-03-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-04-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-05-2026-05.envelope.json > docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-accounting-2026-05.json
python3.10 scripts/zkai_native_seq32_attention_mlp_adjacent_label_seed_sweep_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-2026-05.tsv
python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_adjacent_label_seed_sweep_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_adjacent_label_seed_sweep_gate.py
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_adjacent_label_seed_sweep_gate
cargo +nightly-2025-07-14 test --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof
cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_adjacent_seed --lib
git diff --check
just gate-fast
just gate
```

## Next Attack

Follow-up issue:
https://github.com/omarespejel/provable-transformer-vm/issues/693.

The falsifying experiment should compare query/sample/opening reconstruction
fields between adjacent probe B, seed `02`, seed `05`, and the fixed adjacent
layout, then explain which transcript bucket removes the extra `2,736` typed
bytes.
