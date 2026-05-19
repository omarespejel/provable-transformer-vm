# ZKAI Stwo Inner Attempt-Domain Statement Gate

Date: 2026-05-19

Issue: https://github.com/omarespejel/provable-transformer-vm/issues/710

## Decision

`GO_REGENERATED_SEQ32_D128_STWO_PROOFS_BIND_ATTEMPT_DOMAIN_INSIDE_NATIVE_STATEMENT`

## Result

The two accepted adjacent attempts were regenerated as native Stwo proof
objects with explicit attempt-policy metadata inside the proof input:

- attempt domain: `adjacent_label_probe_a`, `adjacent_label_probe_b`
- attempt budget: `2`
- relative Fiat-Shamir search loss: `1.000000` bit
- policy stage: `inner_statement_transcript_metadata`

The Rust prover/verifier now supports an optional
`ZkAiNativeSeq32AttentionMlpAttemptPolicy`. When present, the policy is:

- validated against the adapter mode;
- included in the statement commitment payload;
- mixed into the Stwo Fiat-Shamir channel before lookup challenges;
- surfaced in the opening sampler;
- rejected by mutation tests when relabeled, widened, understated, or removed
  from the regenerated proof object.

The old no-policy A/B artifacts remain legacy-verifiable for reproducibility.
The new claim is about the regenerated `inner-attempt` artifacts, not about
rewriting the older wrapper-only row.

## Measurements

| row | typed bytes | proof JSON bytes | status |
| --- | ---: | ---: | --- |
| legacy wrapper-only probe B | `37,532` | `106,317` | still verifies, but attempt policy is outside the inner transcript |
| regenerated inner-bound probe A | `40,892` | `118,134` | verifies |
| regenerated inner-bound probe B | `40,892` | `118,042` | verifies, selected best JSON row |
| previous single-proof champion | `42,068` | `121,996` | baseline |
| matched two-proof frontier | `47,188` | `140,838` | baseline |

Best regenerated inner-bound row: `adjacent_label_probe_b`.

- typed cost versus legacy wrapper-only probe B: `+3,360` bytes
- JSON cost versus legacy wrapper-only probe B: `+11,725` bytes
- typed saving versus single-proof champion: `1,176` bytes
- JSON saving versus single-proof champion: `3,954` bytes
- typed saving versus matched two-proof frontier: `6,296` bytes
- JSON saving versus matched two-proof frontier: `22,796` bytes
- NANOZK paper-reported d128 block row: `6,900` bytes
- locally comparable NANOZK rows: `0`

## Interpretation

This is a correctness upgrade with a measurable cost.

The earlier `37,532` typed-byte row is still the smaller proof object, but its
attempt-domain accounting lived outside the native proof statement. The new
`40,892` typed-byte row makes the two-probe domain, selected attempt, and
one-bit loss part of the native statement/transcript surface.

That matters because the proof is no longer only saying "this variant
verified." It is saying "this variant verified under this bounded attempt
policy." In paper terms, the result moves the query-geometry trick from an
outer wrapper observation toward a statement-valid native proving path.

It is still not a NANOZK comparison and not a full transformer block proof.
The useful claim is narrower:

> A bounded attempt-domain policy can be carried inside the native Stwo
> statement/transcript for the seq32+d128 attention-plus-MLP boundary, and the
> resulting proof still beats the matched local single-proof and two-proof
> frontiers while paying an explicit `3,360` typed-byte cost versus the smaller
> legacy wrapper-only row.

## Evidence

- Input A:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-inner-attempt-2026-05.input.json`
- Envelope A:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-inner-attempt-2026-05.envelope.json`
- Input B:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-inner-attempt-2026-05.input.json`
- Envelope B:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-inner-attempt-2026-05.envelope.json`
- Accounting:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-inner-attempt-domain-accounting-2026-05.json`
- Gate JSON:
  `docs/engineering/evidence/zkai-stwo-inner-attempt-domain-statement-gate-2026-05.json`
- Gate TSV:
  `docs/engineering/evidence/zkai-stwo-inner-attempt-domain-statement-gate-2026-05.tsv`

## Reproducibility

Gate schema:
`zkai-stwo-inner-attempt-domain-statement-gate-v1`

Gate JSON SHA-256:
`55f3afdd1a39c6a22f9c1e7f1383e8c2b38632ba043dc0b01de4a5aad0d1e86d`

Gate TSV SHA-256:
`5e02d2c08f4dd01494c12c6e907ce32b019a421c5696935d4ee8f80bd930689d`

Accounting SHA-256:
`72cad6f598af282215f6579a716816a52e259248a420e27c5759d45482055978`

Payload commitment:
`blake2b-256:24b7220e4387adfa9c4cba6e06a99d0d1e25e8642470c827d15e837bbbe20323`

Mutation coverage:

- Rust mutation/tamper tests: focused adjacent probe tests pass.
- Python gate mutations: `18 / 18` rejected.
- Python unit tests: `7`.

Commands:

```bash
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent-label-probe-a docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-inner-attempt-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-inner-attempt-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-inner-attempt-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-inner-attempt-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent-label-probe-b docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-inner-attempt-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-inner-attempt-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-inner-attempt-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-inner-attempt-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-inner-attempt-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-inner-attempt-2026-05.envelope.json > docs/engineering/evidence/zkai-native-seq32-attention-mlp-inner-attempt-domain-accounting-2026-05.json
python3.10 scripts/zkai_stwo_inner_attempt_domain_statement_gate.py --write-json docs/engineering/evidence/zkai-stwo-inner-attempt-domain-statement-gate-2026-05.json --write-tsv docs/engineering/evidence/zkai-stwo-inner-attempt-domain-statement-gate-2026-05.tsv
python3.10 -m py_compile scripts/zkai_stwo_inner_attempt_domain_statement_gate.py scripts/tests/test_zkai_stwo_inner_attempt_domain_statement_gate.py
python3.10 -m unittest scripts.tests.test_zkai_stwo_inner_attempt_domain_statement_gate
cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_adjacent_label_probe --lib
```

## Non-Claims

- Not a new proof-size frontier beyond the existing `37,532` typed-byte
  legacy wrapper row.
- Not a NANOZK proof-size comparison.
- Not a matched external zkML benchmark.
- Not a full transformer block proof.
- Not timing evidence.
- Not production-ready zkML.
