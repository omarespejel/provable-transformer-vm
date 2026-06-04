# Stwo-AI D64 Chunk4 Layout Policy Gate

- Issue: `#757`
- Decision: `GO_D64_CHUNK4_VERIFIER_BOUND_LAYOUT_POLICY_REDUCES_FUSED_PROOF_BYTES`
- Fork status: `NO_GO_FORK_STWO_ROUTE_POLICY_LAYER_STILL_MOVES_PROOF_BYTES`
- Timing policy: `no_timing_claim_no_public_benchmark`
- Security config: `fri_query_count=3`, `fri_log_blowup=1`, `pow_bits=10`, `fold_step=1`

## Result

`chunk4` is now a verifier-bound d64 route-layout policy. It fixes the schedule before proof generation, changes the source statement commitment, and verifies natively.

- Baseline fused proof bytes: `276503`
- Chunk4 fused proof bytes: `274692`
- Saving vs baseline fused: `1811` bytes
- Matched split frontier: `315785` bytes
- Saving vs split frontier: `41093` bytes
- Chunk4 vs baseline ratio: `0.993450x`
- Chunk4 vs split ratio: `0.869870x`
- Opening delta vs baseline: `-1866` bytes
- FRI delta vs baseline: `-1374` bytes
- Decommitment delta vs baseline: `-492` bytes
- Query delta vs baseline: `53` bytes
- Source statement commitment: `blake2b-256:319ee48ad99dc3aa596380c1ddd82b7f3a67f5ce8d81aa85aebd4c955402fc46`

## Interpretation

This is a GO for route-layout policy as the next Stwo-AI optimization layer. It is still not a reason to fork Stwo: the current backend already lets a verifier-bound deterministic layout reduce proof bytes on the d64 pressure anchor.

## Non-Claims

- not a Stwo fork
- not a backend patch
- not transcript grinding
- not post-query layout selection
- not a proving-speed claim
- not production-security parameters
- not exact real-valued Softmax
- not full transformer inference
- not a NANOZK comparison

## Reproduce

```bash
just gate-fast
python3.10 scripts/zkai_attention_kv_stwo_native_d64_four_head_seq64_bounded_softmax_table_proof_input.py --layout-policy chunk4 --write-json docs/engineering/evidence/zkai-stwo-ai-d64-four-head-seq64-layout-chunk4-input.json --write-tsv docs/engineering/evidence/zkai-stwo-ai-d64-four-head-seq64-layout-chunk4-input.tsv
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_proof -- prove docs/engineering/evidence/zkai-stwo-ai-d64-four-head-seq64-layout-chunk4-input.json docs/engineering/evidence/zkai-stwo-ai-d64-four-head-seq64-layout-chunk4-fused.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_proof -- verify docs/engineering/evidence/zkai-stwo-ai-d64-four-head-seq64-layout-chunk4-fused.envelope.json
python3.10 scripts/zkai_stwo_ai_d64_four_head_seq64_chunk4_policy_gate.py --write-json docs/engineering/evidence/zkai-stwo-ai-d64-four-head-seq64-chunk4-policy-gate-2026-06.json --write-tsv docs/engineering/evidence/zkai-stwo-ai-d64-four-head-seq64-chunk4-policy-gate-2026-06.tsv --write-md docs/engineering/zkai-stwo-ai-d64-four-head-seq64-chunk4-policy-gate-2026-06-04.md
python3.10 -m py_compile scripts/zkai_stwo_ai_d64_four_head_seq64_chunk4_policy_gate.py scripts/tests/test_zkai_stwo_ai_d64_four_head_seq64_chunk4_policy_gate.py
python3.10 -m unittest scripts.tests.test_zkai_stwo_ai_d64_four_head_seq64_chunk4_policy_gate
cargo +nightly-2025-07-14 test --locked attention_kv_native_d64_four_head_seq64_bounded_softmax_table_rejects_layout_policy --lib --features stwo-backend
cargo +nightly-2025-07-14 test --locked attention_kv_native_d64_four_head_seq64_bounded_softmax_table_rejects_unknown_layout_policy --lib --features stwo-backend
git diff --check
just gate-no-nightly
```
