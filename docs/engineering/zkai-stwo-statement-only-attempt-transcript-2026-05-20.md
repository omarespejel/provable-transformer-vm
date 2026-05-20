# ZKAI Stwo Statement-Only Attempt Transcript Gate

Date: 2026-05-20

Issue: https://github.com/omarespejel/provable-transformer-vm/issues/680

## Decision

`GO_STATEMENT_ONLY_ATTEMPT_POLICY_TRANSCRIPT_REDUCES_REGENERATED_STWO_PROOF_BYTES`

## Result

`STATEMENT_ONLY_PROBE_B_VERIFIES_AT_39516_TYPED_BYTES_SAVING_1376_VS_FULL_POLICY_MIX`

The previous inner attempt-domain result regenerated the two accepted adjacent
attempts with policy metadata inside the native Stwo statement and also mixed
the policy fields directly into the Fiat-Shamir channel. This gate checks a
narrower transcript profile:

- keep the attempt policy inside the statement commitment;
- keep the statement commitment mixed into Fiat-Shamir;
- remove the extra direct mix of every policy string field;
- keep the attempt domain bounded to `2` attempts;
- keep the charged relative search loss at `1.000000` bit.

The useful result is that the statement-only profile produces a smaller
regenerated, inner-policy-bound proof object than the full policy-field mix.

## Measurements

| row | typed bytes | proof JSON bytes | delta vs full policy B | status |
| --- | ---: | ---: | ---: | --- |
| legacy wrapper-only probe B | `37,532` | `106,317` | `-3,360` | context only; policy not inner statement-bound |
| full policy-field mix probe B | `40,892` | `118,042` | `0` | prior inner-policy-bound baseline |
| compact policy mix probe B | `42,156` | `122,735` | `+1,264` | no-go |
| statement-only probe A | `42,780` | `124,900` | `+1,888` | verifies but heavier |
| statement-only probe B | `39,516` | `113,388` | `-1,376` | selected new inner-policy-bound frontier |
| previous single-proof champion | `42,068` | `121,996` | n/a | baseline |
| matched two-proof frontier | `47,188` | `140,838` | n/a | baseline |

Best row: `statement_only_probe_b`.

- typed saving versus full policy-field mix probe B: `1,376` bytes
- JSON saving versus full policy-field mix probe B: `4,654` bytes
- typed saving versus previous single-proof champion: `2,552` bytes
- typed saving versus matched two-proof frontier: `7,672` bytes
- JSON saving versus matched two-proof frontier: `27,450` bytes
- typed cost versus legacy wrapper-only probe B: `1,984` bytes
- locally comparable NANOZK rows: `0`

## Interpretation

This is a real proof-boundary improvement, but not a NANOZK comparison.

The earlier wrapper-only row is still smaller at `37,532` typed bytes, but it
does not bind the attempt policy inside the native proof statement. The prior
inner-bound row fixed that correctness gap and cost `3,360` typed bytes. This
new row recovers `1,376` of those bytes while keeping the policy inside the
statement commitment.

The mechanism is narrower than "remove metadata." The policy is still part of
the statement payload. The claim is that once the statement commitment is mixed
into Fiat-Shamir, separately mixing every policy string field can be redundant
for this bounded profile and can move the query/opening geometry in the wrong
direction.

This strengthens the current paper path:

> Transformer proof boundaries should be chosen around proof pressure and
> statement meaning. A STARK-native boundary can sometimes improve proof-size
> accounting by moving policy from duplicated transcript material into the
> statement commitment that the verifier already binds.

## Evidence

Statement-only probe A:

- Input:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-statement-only-transcript-2026-05.input.json`
- Opening sampler:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-statement-only-transcript-2026-05-opening-sampler-2026-05.json`
- Envelope:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-statement-only-transcript-2026-05.envelope.json`

Statement-only probe B:

- Input:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.input.json`
- Opening sampler:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05-opening-sampler-2026-05.json`
- Envelope:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.envelope.json`

Compact profile no-go:

- Input:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-compact-transcript-2026-05.input.json`
- Opening sampler:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-compact-transcript-2026-05-opening-sampler-2026-05.json`
- Envelope:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-compact-transcript-2026-05.envelope.json`

Accounting and gate outputs:

- Statement-only accounting:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-statement-only-attempt-accounting-2026-05.json`
- Transcript profile accounting:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-attempt-transcript-profile-accounting-2026-05.json`
- Gate JSON:
  `docs/engineering/evidence/zkai-stwo-statement-only-attempt-transcript-gate-2026-05.json`
- Gate TSV:
  `docs/engineering/evidence/zkai-stwo-statement-only-attempt-transcript-gate-2026-05.tsv`

## Reproducibility

Gate schema:
`zkai-stwo-statement-only-attempt-transcript-gate-v1`

Proof backend version:
`stwo-native-seq32-attention-mlp-single-proof-object-rmsnorm-input-fused-adjacent-fixed-v1`

Timing mode:
`none; proof-size/accounting correctness gate only`

Gate JSON SHA-256:
`d6e8d8ebe36fc438b61ba879cc9d6979cf437a76fe2beda98477138e0e341881`

Gate TSV SHA-256:
`fcfe6d3d1c849a7e2ab2b1f7c7e20590815e3c35f599672f2dd65194f19f7b6e`

Statement-only accounting SHA-256:
`4ca7429d9e97e9fe54526618f36027757ca67a6184478dcfc06045396f765f2c`

Transcript profile accounting SHA-256:
`92d99a4aeb0169ac50e6380f67ad412f11d4985e1e55eb163c4262d965ad8072`

Payload commitment:
`blake2b-256:a60425f6b2fbb4c4b791aab941a41d8a4b0dbeb8a0951252bd33e02f90b9f76d`

Mutation coverage:

- Python gate mutations: `20 / 20` rejected.
- Python unit tests: `8`.

Commands:

```bash
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent-label-probe-a-statement-only-transcript docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-statement-only-transcript-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-statement-only-transcript-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-statement-only-transcript-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-statement-only-transcript-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent-label-probe-b-statement-only-transcript docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-statement-only-transcript-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.envelope.json > docs/engineering/evidence/zkai-native-seq32-attention-mlp-statement-only-attempt-accounting-2026-05.json
python3.10 scripts/zkai_stwo_statement_only_attempt_transcript_gate.py --write-json docs/engineering/evidence/zkai-stwo-statement-only-attempt-transcript-gate-2026-05.json --write-tsv docs/engineering/evidence/zkai-stwo-statement-only-attempt-transcript-gate-2026-05.tsv
python3.10 -m py_compile scripts/zkai_stwo_statement_only_attempt_transcript_gate.py scripts/tests/test_zkai_stwo_statement_only_attempt_transcript_gate.py
python3.10 -m unittest scripts.tests.test_zkai_stwo_statement_only_attempt_transcript_gate
cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_adjacent_label_probe_statement_only_attempt_profile_validates --lib
cargo +nightly-2025-07-14 test --locked --features stwo-backend native_seq32_attention_mlp_single_proof --lib
git diff --check
just gate-fast
just gate
```

## Non-Claims

- Not a NANOZK proof-size comparison.
- Not a matched external zkML benchmark.
- Not a full transformer block proof.
- Not exact real-valued Softmax.
- Not timing evidence.
- Not production-ready zkML.
- Not a proof-size frontier beyond the legacy wrapper-only `37,532` typed-byte
  row.
- Not a free retry policy; the two-attempt domain is explicit and charged as
  one bit.

## Next Attack

The next useful attack is to reduce the remaining `1,984` typed-byte gap versus
the legacy wrapper-only row without removing the inner statement policy
binding. Candidate directions:

- reduce FRI decommitment and trace decommitment movement caused by the
  statement-only B transcript geometry;
- check whether the policy payload can be canonicalized into a shorter
  statement commitment domain without weakening verifier semantics;
- test a tiny crossing grid to see whether this improvement is structural or
  specific to the current adjacent probe B transcript.
