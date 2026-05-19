# Native Seq32 Attention+MLP Pre-Prove Opening-Bucket Predictor

Date: 2026-05-19
Issue: https://github.com/omarespejel/provable-transformer-vm/issues/695

## Decision

`NO_GO_SOURCE_VISIBLE_PREPROVE_INVENTORY_DOES_NOT_PREDICT_PROBE_B_BUCKET`

This gate tests whether the smaller adjacent probe-B opening bucket can be
predicted from source-visible input JSON and statement fields before proof
generation. It cannot, at least not from the current inventory.

## Result

All nine checked adjacent rows share one pre-prove structural signature, but
their final path-opening buckets split into five values. The final bucket edge
therefore remains real, but the current source-visible inventory does not
explain it before the proof is generated.

| variant | final path-opening bytes | final typed bytes | final JSON proof bytes | final value bytes |
| --- | ---: | ---: | ---: | ---: |
| `fixed_adjacent_layout` | `21,184` | `42,156` | `122,688` | `20,924` |
| `adjacent_label_probe_a` | `19,360` | `40,332` | `116,321` | `20,924` |
| `adjacent_label_probe_b` | `16,560` | `37,532` | `106,317` | `20,924` |
| `adjacent_seed_00` | `20,512` | `41,484` | `120,158` | `20,924` |
| `adjacent_seed_01` | `20,512` | `41,484` | `120,064` | `20,924` |
| `adjacent_seed_02` | `19,296` | `40,268` | `115,995` | `20,924` |
| `adjacent_seed_03` | `21,184` | `42,156` | `122,588` | `20,924` |
| `adjacent_seed_04` | `21,184` | `42,156` | `122,648` | `20,924` |
| `adjacent_seed_05` | `19,360` | `40,332` | `116,303` | `20,924` |

Pinned summary:

- source-exposed bucket predictor: `false`;
- unique pre-prove structural signatures: `1`;
- distinct final path-opening buckets: `5`;
- rows sharing the pre-prove structural signature: `9`;
- best final bucket: `adjacent_label_probe_b` at `16,560` path-opening bytes;
- best pre-registered seed: `adjacent_seed_02` at `19,296` path-opening bytes;
- gap versus that seed: `2,736` typed bytes;
- direct value bytes stay constant at `20,924`;
- final path-opening span: `4,624` typed bytes.

## Human Read

This is a useful NO-GO. The previous probe-B result showed that proof plumbing
matters: the value bytes stay fixed while FRI/sample/trace opening bytes move.
This gate asks the next question: can we choose that better bucket before
paying for the proof?

The answer is no from the current source-visible fields. The input JSON can
identify which row we tried, but that is only row identity. It is not a
mechanism. Treating `adapter_mode`, `statement_commitment`, or parameter
commitment as a predictor would be a post-hoc lookup table over already-known
rows.

The next useful experiment is deeper than input inventory: a dry-run transcript
or query-opening sampler that emits the relevant Fiat-Shamir query/opening
positions after source commitments but before final proof serialization.

## Claim Boundary

The checked claim is only:

> The current source-visible pre-prove inventory cannot predict the adjacent
> probe-B opening bucket; all checked adjacent rows share one structural
> signature before proving, while final opening buckets split into five values.

Non-claims:

- not a source-exposed predictor for the probe-B opening bucket;
- not a new proof-size frontier;
- not a production label-selection policy;
- not a NANOZK proof-size win;
- not a matched external zkML benchmark;
- not a full transformer block proof;
- not exact real-valued Softmax;
- not timing evidence;
- not production-ready zkML.

## Evidence

- Gate JSON:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-preprove-opening-bucket-predictor-2026-05.json`
- Gate TSV:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-preprove-opening-bucket-predictor-2026-05.tsv`
- Source accounting:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-accounting-2026-05.json`
- Gate JSON SHA-256:
  `98bcd9b9a574aa934c4ad571ae78aa1d738f0fb720488cb992be88609a8b785b`
- Gate TSV SHA-256:
  `9d402a85204c7c02d661b956fa94090f070e8e5a4e0d0894e413d5a766bdeb59`
- Source accounting SHA-256:
  `90f04ada7e02f3777615417dec475c27ccff3511f42be0a084e6405b52fcd6db`
- Payload commitment:
  `blake2b-256:a86044d35f5c6ce8b3f372d24b2e0afe2db8fef5a5b124711f801dfd53d8455b`
- Mutation guards:
  `16 / 16` rejected.

The gate rejects decision drift, claim-boundary overclaim, source digest drift,
accounting digest drift, row erasure, final-accounting leakage into pre-prove
rows, source-predictor promotion, structural-signature drift, row-identity
promotion, bucket-span drift, record-stream erasure, validation-command drift,
removed non-claims, and payload-commitment drift.

## Reproduction

```bash
python3.10 scripts/zkai_native_seq32_attention_mlp_preprove_opening_bucket_predictor_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-preprove-opening-bucket-predictor-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-preprove-opening-bucket-predictor-2026-05.tsv
python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_preprove_opening_bucket_predictor_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_preprove_opening_bucket_predictor_gate.py
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_preprove_opening_bucket_predictor_gate
git diff --check
just gate-fast
just gate
```

## Next Attack

Follow-up issue:
https://github.com/omarespejel/provable-transformer-vm/issues/697.

The GO gate should predict the `16,560` probe-B bucket and the seed buckets
without using final proof bytes, grouped accounting, record streams, or
envelope hashes. If it needs those final artifacts, this path stays an
attribution result rather than a deterministic proof-size optimization.
