# Stwo-AI Route-Layout Policy Selector

- Issue: `#757`
- Decision: `GO_ROUTE_LAYOUT_POLICY_SELECTOR_FROM_EXISTING_SECTION_DELTA_NO_PROVER_RUN`
- Fork status: `NO_GO_FORK_UNTIL_ROUTE_POLICY_HITS_MEASURED_INTERNAL_WALL`
- Prover policy: `no_prover_run_existing_artifact_accounting_only`
- Backend metadata: `stwo 2.2.0` / `stwo-constraint-framework 2.2.0` at evidence base commit `11411122c02e56ca434a90f54e0afb1988211b8d`
- Version constants: `ZKAI_ATTENTION_KV_NATIVE_TWO_HEAD_SEQ32_FUSED_SOFTMAX_TABLE_BACKEND_VERSION=stwo-attention-kv-two-head-seq32-fused-bounded-softmax-table-logup-v1`; `ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ64_FUSED_SOFTMAX_TABLE_BACKEND_VERSION=stwo-attention-kv-d64-four-head-seq64-fused-bounded-softmax-table-logup-v1`

## Result

The next Stwo-AI step is not a fork. The checked section-delta evidence says the measured savings are still mostly opening material, so the fast path is a deterministic route-layout policy experiment.

- Checked profiles: `11`
- Total fused saving: `223958` bytes
- Opening-related saving: `209155` bytes (`0.933903` share)
- Pressure anchor: `d64_four_head_seq64` saves `39282` bytes, with `37827` opening-related bytes
- Fast first target: `d8_two_head_seq32` saves `31685` bytes, with `0.953227` opening share and `0.926899` sidecar-opening absorption

## Next Experiment

Prototype a verifier-bound deterministic route-layout policy on `d8_two_head_seq32`. If it reduces fused proof bytes without changing semantics or selecting after query draw, promote the same policy to `d64_four_head_seq64`.

## Non-Claims

- not a new proof-size result
- not a Stwo fork
- not a backend patch
- not post-query label selection
- not transcript grinding
- not timing evidence
- not production-security parameter evidence
- not backend-internal semantic byte attribution
- not exact real-valued Softmax
- not full transformer inference

## Reproduce

```bash
just gate-fast
python3.10 scripts/zkai_stwo_ai_route_layout_policy_gate.py --write-json docs/engineering/evidence/zkai-stwo-ai-route-layout-policy-2026-06.json --write-tsv docs/engineering/evidence/zkai-stwo-ai-route-layout-policy-2026-06.tsv --write-md docs/engineering/zkai-stwo-ai-route-layout-policy-2026-06-04.md
python3.10 -m py_compile scripts/zkai_stwo_ai_route_layout_policy_gate.py scripts/tests/test_zkai_stwo_ai_route_layout_policy_gate.py
python3.10 -m unittest scripts.tests.test_zkai_stwo_ai_route_layout_policy_gate
git diff --check
just gate-no-nightly
```
