# Stwo Attempt-Domain Binding Gate

Date: 2026-05-19
Issue: https://github.com/omarespejel/provable-transformer-vm/issues/708

## Decision

`GO_TYPED_OUTER_ENVELOPE_BINDS_TWO_PROBE_ATTEMPT_DOMAIN_TO_EXISTING_PROOF_ROW`

## Result

`PROBE_B_ROW_BOUND_WITH_1_BIT_RELATIVE_LOSS_NOT_INNER_STWO_TRANSCRIPT_BINDING`

This gate promotes the previous query-grinding budget result one step toward a
verifier-facing statement boundary.

The important change is not a smaller proof. The important change is that the
allowed attempt domain is now an explicit typed envelope around the existing
proof row:

- attempt domain:
  `adjacent_label_probe_a, adjacent_label_probe_b`
- selected attempt: `adjacent_label_probe_b`
- attempt budget: `2`
- relative Fiat-Shamir loss: `log2(2) = 1.000000` bit
- selected proof row: `37,532` typed bytes / `106,317` JSON proof bytes
- saving versus current single-proof champion: `4,536` typed bytes
- saving versus matched two-proof frontier: `9,656` typed bytes

The gate also refreshes the source-generated inventory underneath the builder:
the current Rust/CLI adjacent surface has nine labels, not three. Probe A and
probe B remain the only accepted labels. The fixed label and six seed labels are
now visible rejected rows instead of invisible source drift.

## Human Read

The previous result showed that a small bounded retry budget can recover the
probe-B row. This result says what the verifier-facing object has to remember
for that to be meaningful.

The envelope binds:

- the allowed attempt domain;
- which attempt won;
- the charged security loss;
- the builder payload commitment;
- the query-budget payload commitment;
- the selected envelope hash, proof hash, input hash, and record-stream hash.

It also forbids the dangerous policy inputs:

- final envelope JSON;
- final proof bytes;
- post-decommitment accounting;
- unbounded retry count.

This is still not inner Stwo transcript binding. The existing proof object was
not regenerated with the attempt-domain metadata inside the native statement.
So the honest claim is:

> The outer verifier-facing envelope binds the two-probe attempt domain around
> the existing proof row. The next stronger result must regenerate the proof so
> the inner statement metadata carries the attempt domain and selected attempt
> id.

## Source-Completeness Refresh

While building this gate, the source-generated inventory caught stale evidence:
the current Rust enum and CLI expose nine adjacent labels:

| label | status | typed bytes | path-opening bytes |
| --- | --- | ---: | ---: |
| `fixed_adjacent_layout` | rejected inflating label | `42,156` | `21,184` |
| `adjacent_label_probe_a` | supported label | `40,332` | `19,360` |
| `adjacent_label_probe_b` | supported label | `37,532` | `16,560` |
| `adjacent_seed_00` | rejected unpromoted seed | `41,484` | `20,512` |
| `adjacent_seed_01` | rejected unpromoted seed | `41,484` | `20,512` |
| `adjacent_seed_02` | rejected unpromoted seed | `40,268` | `19,296` |
| `adjacent_seed_03` | rejected inflating label | `42,156` | `21,184` |
| `adjacent_seed_04` | rejected inflating label | `42,156` | `21,184` |
| `adjacent_seed_05` | rejected unpromoted seed | `40,332` | `19,360` |

The proof-object builder now reconstructs all nine rows from real envelopes and
the nine-row local binary accounting artifact. That keeps the two-probe domain
honest: seed labels are not missing, they are explicitly rejected for this
policy.

## Evidence

Machine-readable evidence:

- `docs/engineering/evidence/zkai-stwo-attempt-domain-binding-gate-2026-05.json`
- `docs/engineering/evidence/zkai-stwo-attempt-domain-binding-gate-2026-05.tsv`

Supporting refreshed evidence:

- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-2026-05.json`
- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-adjacent-label-inventory-2026-05.json`
- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-proof-object-builder-2026-05.json`

Evidence hashes:

- Attempt-domain JSON SHA-256:
  `807f0d5a6018d488d36ed03fc6f265f285dd8baf409cfec97c7169303f2fb3e0`
- Attempt-domain TSV SHA-256:
  `ea0a484ad0edc055663baf34eedcfd2acc678293fc175c307bca0bf1e1798653`
- Attempt-domain payload commitment:
  `blake2b-256:1dac8ed53a269f2649da650afce07f4a96810e4f1c0a37426fd3c10a12b86691`
- Builder JSON SHA-256:
  `d8685f504a7f9fd935ec1b317aa8afd244c84e83d4e45ef7da9e80bca022f7b1`
- Builder payload commitment:
  `blake2b-256:c25c9d8b0af3394006b266754ba65fc92ee79080f1755066c2fab034161e18dd`
- Generated inventory JSON SHA-256:
  `9f65bb46dab42bacb1530dc7f6cb31da9b4097dc5e2866feda26a72fa0611929`
- Generated inventory payload commitment:
  `blake2b-256:8a0697d929b242d9894f58c61716bbca2b13612d76670ef5500258c490587851`
- Seed-sweep JSON SHA-256:
  `a3be0b33193fe661cb75dc32342e9c221bdf0016a98f7cf7f9ec71369fc801e4`
- Seed-sweep payload commitment:
  `blake2b-256:68b16bb7614972f29d5f1a0015ea9d2e3d2cdf2ce33c42afdf6eaed7cbe933db`
- Mutation guards:
  `25 / 25` rejected for the attempt-domain gate.
- Unit tests:
  `7` for the attempt-domain gate.

## Reproduction

```bash
python3.10 scripts/zkai_native_seq32_attention_mlp_adjacent_label_seed_sweep_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-2026-05.tsv
python3.10 scripts/zkai_native_seq32_attention_mlp_generated_adjacent_label_inventory_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-adjacent-label-inventory-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-adjacent-label-inventory-2026-05.tsv
python3.10 scripts/zkai_native_seq32_attention_mlp_generated_proof_object_builder_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-proof-object-builder-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-proof-object-builder-2026-05.tsv
python3.10 scripts/zkai_stwo_attempt_domain_binding_gate.py --write-json docs/engineering/evidence/zkai-stwo-attempt-domain-binding-gate-2026-05.json --write-tsv docs/engineering/evidence/zkai-stwo-attempt-domain-binding-gate-2026-05.tsv
python3.10 -m py_compile scripts/zkai_stwo_attempt_domain_binding_gate.py scripts/tests/test_zkai_stwo_attempt_domain_binding_gate.py
python3.10 -m unittest scripts.tests.test_zkai_stwo_attempt_domain_binding_gate
git diff --check
just gate-fast
just gate
```

## Non-Claims

- Not fresh proof generation.
- Not a new proof-size frontier beyond the existing `37,532` typed-byte row.
- Not inner Stwo transcript binding of the attempt domain.
- Not an absolute soundness claim.
- Not unbounded retry.
- Not post-decommitment proof-byte selection.
- Not a NANOZK proof-size comparison.
- Not a full transformer block proof.
- Not timing evidence.
- Not production-ready zkML.

## Next Attack

Regenerate the native seq32+d128 proof object with the attempt domain and
selected attempt id inside the proof statement metadata. The promotion gate is:

- verifier rejects attempts outside the declared domain;
- mutation guards reject relabeling of selected attempt, source commitments, and
  proof artifact hashes;
- proof-size accounting still reports the selected row honestly;
- the result remains scoped as a local Stwo statement-bound mechanism, not a
  NANOZK comparison.
