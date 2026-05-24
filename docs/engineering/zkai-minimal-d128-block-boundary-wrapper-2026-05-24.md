# Minimal D128 Block-Boundary Wrapper

Issue: #715

Decision: `GO_MINIMAL_D128_ATTENTION_DERIVED_BLOCK_BOUNDARY_WRAPPER`

Result: `BOUND_MODEL_FAITHFUL_D128_PROOF_TO_BLOCK_STATEMENT_CHAIN_WITH_ZERO_PROOF_BYTE_DELTA`

Boundary statement commitment: `blake2b-256:abb34aa243a583b01b4a7f4516df7563c7be1e0ad6f64b26a52e58df17306f1a`

Payload commitment: `blake2b-256:02541cc4330b086b4207a07ff659cbef46141bd3e37248ba18f049469635f28b`

## What Changed

This gate wraps the current model-faithful d128 attention-derived MLP proof result in a typed block-boundary statement. It binds the proof envelope hash, proof hash, verifier domain, target id, local typed-byte accounting, matched split frontier, and the attention-derived d128 block statement-chain commitment.

The wrapper is deliberately boring in proof-size accounting: it adds `0` proof bytes. It is a statement boundary around an already measured proof object, not a new native proof object.

## Size Anchor

- Underlying single proof JSON bytes: `503,567`.
- Matched split proof JSON bytes: `522,480`.
- JSON saving: `18,913` bytes, ratio `0.963801`.
- Underlying local typed bytes: `204,564`.
- Matched split local typed bytes: `209,732`.
- Typed saving: `5,168` bytes, ratio `0.975359`.
- Wrapper proof-byte delta: `0`.

## Split Frontier Components

- `attention_fused_softmax_logup_proof`: `445,888` proof JSON bytes / `184,900` typed bytes; target `attention-kv-d128-two-head-seq32-causal-mask-fused-bounded-softmax-table-logup-v1`; verifier domain `ptvm:zkai:attention-kv-stwo-native-d128-two-head-seq32-fused-bounded-softmax-table-logup:v1`.
- `attention_derived_d128_rmsnorm_mlp_proof`: `76,592` proof JSON bytes / `24,832` typed bytes; target `attention-derived-d128-rmsnorm-mlp-fused-proof-v1`; verifier domain `ptvm:zkai:split-frontier:attention-derived-d128-rmsnorm-mlp-fused-proof:v1`.

## Proof Binding

- Proof backend: `stwo`.
- Proof backend version: `stwo-native-d128-seq32-attention-mlp-single-proof-object-native-adapter-v1`.
- Proof schema version: `stwo-native-d128-seq32-attention-mlp-single-proof-object-native-adapter-payload-v1`.
- Statement version: `zkai-native-d128-seq32-attention-mlp-single-proof-object-native-adapter-statement-v1`.
- Target id: `attention-kv-d128-two-head-seq32-fused-softmax-table-plus-d128-attention-derived-d128-rmsnorm-mlp-v1`.
- Verifier domain: `ptvm:zkai:native-d128-seq32-attention-mlp-single-proof-object:v1`.
- Envelope sha256: `3779b56e651e28d609bd160d9f4e78856b1527deef8cd54f5797660b63850c70`.
- Proof sha256: `29e13ac7f3fa5a5349873b982fb7964e0a8abb68b1e3547520f19ea65365caae`.
- Preflight payload commitment: `blake2b-256:dfc47f43b47bef2b3d08bf254404641d6188eb0bd373978085cd9591a821d861`.

## Source Artifacts

- `model_faithful_single`: `docs/engineering/evidence/zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05.json`, sha256 `0a2200bce9ebbe93d17a030dbd6c7222efccb06bb26ebde97999bfc938469447`, `7,719` bytes.
- `model_faithful_single_accounting`: `docs/engineering/evidence/zkai-native-d128-seq32-attention-derived-mlp-single-proof-binary-accounting-2026-05.json`, sha256 `8f0e8ce78fea0be66c98b41aae5c8658083194fce137321a79f094b32956baef`, `5,966` bytes.
- `model_faithful_split_accounting`: `docs/engineering/evidence/zkai-native-d128-seq32-attention-derived-mlp-split-frontier-binary-accounting-2026-05.json`, sha256 `13f31f75ff1dd95aee63853abee201ac4a7615604ad3a4b30e412dc73c966ee9`, `10,714` bytes.
- `model_faithful_block_preflight`: `docs/engineering/evidence/zkai-model-faithful-d128-block-boundary-preflight-2026-05.json`, sha256 `ba9917138b340bb1c87fc9aaca0be15f9c207fae0c5d4b600973f1b1706c17ee`, `11,456` bytes.
- `attention_derived_block_statement_chain`: `docs/engineering/evidence/zkai-attention-derived-d128-block-statement-chain-2026-05.json`, sha256 `990602eefeaceb98a9272d00acfd9b1ef387d34d0218d9ae1a736afc2f6163a3`, `14,624` bytes.

## Block Statement Binding

- Block statement commitment: `blake2b-256:5954b84283b2880c878c70ed533935925de1e14026126a406ad04f66c7ce14a5`.
- Attention output commitment: `blake2b-256:d6cb4d179ea7685c4371d1827f215ec0821bb3ee3d6172d5dc6e13e030653638`.
- Derived output activation commitment: `blake2b-256:25feb3aa6a2a092602c86d10c767f71cdae3c60eade0254a2d121124b712bcf9`.
- Accounted relation rows: `199,553`.
- Edge count: `11`.

## Rows

| row | status | scope | proof JSON | typed or rows | reference | saving | ratio | commitment | action |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| model faithful proof boundary | `CURRENT_PROOF_OBJECT_BOUND` | proof_json_and_local_typed_bytes | `503,567` | `204,564` | `522,480` | `18,913` | `0.963801` | `29e13ac7f3fa5a5349873b982fb7964e0a8abb68b1e3547520f19ea65365caae` | preserve as underlying local proof size win |
| attention derived block statement boundary | `BLOCK_STATEMENT_CHAIN_BOUND` | statement_chain_relation_rows |  | `199,553` |  |  |  | `blake2b-256:5954b84283b2880c878c70ed533935925de1e14026126a406ad04f66c7ce14a5` | bind attention output to d128 mlp output without full block overclaim |
| minimal wrapper boundary | `STATEMENT_WRAPPER_GO` | statement_binding_not_new_proof_bytes | `0` | `5,142` | `0` | `0` | `1.000000` | `blake2b-256:abb34aa243a583b01b4a7f4516df7563c7be1e0ad6f64b26a52e58df17306f1a` | use as next paper claim object then measure next real native boundary |

## Non-Claims

- not a new native proof object.
- not a full transformer block proof.
- not recursive proof composition.
- not a public proving-speed benchmark.
- not a NANOZK proof-size win.
- not a matched external zkML comparison.
- not exact real-valued Softmax.
- not full autoregressive inference.

## Mutation Gates

- Mutations rejected: `21 / 21`.

## Validation

```bash
python3.10 scripts/zkai_minimal_d128_block_boundary_wrapper_gate.py --write-json docs/engineering/evidence/zkai-minimal-d128-block-boundary-wrapper-2026-05.json --write-tsv docs/engineering/evidence/zkai-minimal-d128-block-boundary-wrapper-2026-05.tsv --write-md docs/engineering/zkai-minimal-d128-block-boundary-wrapper-2026-05-24.md
python3.10 -m py_compile scripts/zkai_minimal_d128_block_boundary_wrapper_gate.py scripts/tests/test_zkai_minimal_d128_block_boundary_wrapper_gate.py
python3.10 -m unittest scripts.tests.test_zkai_minimal_d128_block_boundary_wrapper_gate
git diff --check
just gate-fast
CARGO_TERM_COLOR=never cargo +nightly-2025-07-14 test --release --features stwo-backend --lib proof::tests -- --test-threads=4
CARGO_TERM_COLOR=never cargo test --release --test assembly
CARGO_TERM_COLOR=never cargo test --release --test e2e
CARGO_TERM_COLOR=never cargo test --release --test interpreter
CARGO_TERM_COLOR=never cargo test --release --test runtime
bash scripts/run_dependency_audit_suite.sh
uvx --from "zizmor==1.24.1" zizmor .github/workflows --format plain
bash scripts/run_shellcheck_suite.sh
CARGO_TERM_COLOR=never cargo +nightly-2025-07-14 test --release --features stwo-backend --lib stwo_backend::decoding::tests::phase28_aggregated_chained_folded_intervalized_state_relation_rejects_header_mismatch_before_nested_checks -- --exact
just gate
```

- `just gate` passed locally after review fixes: local release gate passed 14 / 14 steps OK.
