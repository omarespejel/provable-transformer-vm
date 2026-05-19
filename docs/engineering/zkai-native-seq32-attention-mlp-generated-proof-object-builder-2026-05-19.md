# ZKAI Native Seq32 Attention+MLP Generated Proof-Object Builder

Date: 2026-05-19

## Decision

`GO_SOURCE_GENERATED_PROOF_OBJECT_ROWS_REPRODUCE_CURRENT_ADJACENT_FRONTIER`

This gate connects the source-generated adjacent label inventory to the real
proof-object artifacts. The builder does not generate a new Stwo proof. It
reconstructs the three current adjacent proof-object rows from:

- the generated Rust/CLI adjacent label inventory;
- the local binary accounting artifact; and
- the referenced Stwo proof envelope bytes.

## Result

The generated builder reproduces all three current adjacent rows:

| label | status | typed bytes | JSON proof bytes | delta vs 42,068 champion |
| --- | --- | ---: | ---: | ---: |
| fixed adjacent | rejected | 42,156 | 122,688 | +88 |
| probe A | accepted | 40,332 | 116,321 | -1,736 |
| probe B | accepted | 37,532 | 106,317 | -4,536 |

The best row remains probe B at `37,532` typed bytes, saving `4,536` typed
bytes (`10.7825%`) versus the `42,068` typed-byte seq32+d128 champion. This is
not a new frontier beyond the prior probe B result. The new contribution is
that the proof-object rows are now source-generated and artifact-bound instead
of manually trusted.

## What The Builder Checks

For every generated adjacent label, the gate requires:

- `generated_label_inventory.path == accounting.evidence_relative_path`;
- `accounting.envelope_sha256 == sha256(raw envelope JSON bytes)`;
- `accounting.proof_sha256 == sha256(envelope.proof byte array)`;
- `accounting.proof_json_size_bytes == len(envelope.proof byte array)`;
- `local_binary_accounting.typed_size_estimate_bytes == generated typed_bytes`;
- path-opening and value-byte totals match the generated policy row;
- metadata in the accounting row matches the envelope metadata; and
- accepted/rejected label status matches the generated label policy.

The generated proof-object builder rejected `21 / 21` mutation classes,
including source-artifact digest drift, generated inventory commitment drift,
missing accounting rows, envelope path relabeling, envelope/proof hash drift,
proof-length drift, typed-accounting drift, record-stream drift, backend-version
drift, fixed-label promotion, best-frontier drift, validation-command drift,
removed non-claims, and payload-commitment drift.

## Why This Matters

The breakthrough path depends on not fooling ourselves with hand-selected rows.
The prior source-generated inventory answered "which labels are currently in
the Rust/CLI surface?" This builder answers the next question: "does every
generated label have a real, pinned proof object with matching accounting?"

That closes an important promotion gap. Future label experiments can add Rust
and CLI surface area, but a label should not become evidence unless this builder
can reconstruct its envelope-bound proof-object row and the mutation gate stays
green.

## Non-Claims

- This is not fresh proof generation.
- This is not a new proof-size frontier beyond the existing `37,532` typed-byte
  adjacent label probe B row.
- This is not a NANOZK proof-size win.
- This is not a matched external zkML benchmark.
- This is not a full transformer block proof.
- This is not exact real-valued Softmax.
- This is not timing evidence.
- This is not production-ready zkML.

## Evidence

Machine-readable outputs:

- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-proof-object-builder-2026-05.json`
- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-proof-object-builder-2026-05.tsv`

Pinned input artifacts:

- generated inventory SHA-256:
  `6aee314a31847d1239ae790ddd8933018215c30a4e6a3d507fd86efc27281238`
- generated inventory payload commitment:
  `blake2b-256:e1653c5b5082171c34406ed29e84209ad29c9aaf7921d782e718a5541da32eea`
- adjacent accounting SHA-256:
  `0841dd4dbf6d3ff76ede4c3e088b301745e04f649024d50aa378fb239cd1ef5c`

## Reproduction

```bash
python3.10 scripts/zkai_native_seq32_attention_mlp_generated_proof_object_builder_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-proof-object-builder-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-proof-object-builder-2026-05.tsv
python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_generated_proof_object_builder_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_generated_proof_object_builder_gate.py
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_generated_proof_object_builder_gate
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_generated_adjacent_label_inventory_gate
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_deterministic_adjacent_label_policy_gate
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_adjacent_label_policy_gate
cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_adjacent_label --lib
git diff --check
just gate-fast
just gate
```

## Next Experiment

Use this builder as the promotion harness for new query/opening-stability
labels. The next proof-size attack is no longer manual table selection; it is
source-generated proving for labels that can beat the `37,532` typed-byte probe
B frontier without widening the statement or dropping correctness bindings.
