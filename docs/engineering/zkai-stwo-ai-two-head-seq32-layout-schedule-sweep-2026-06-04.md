# Stwo-AI Two-Head Seq32 Layout Schedule Sweep

- Issue: `#757`
- Decision: `GO_DETERMINISTIC_CHUNK4_LAYOUT_REDUCES_FUSED_PROOF_BYTES_NO_STWO_FORK`
- Fork status: `NO_GO_FORK_STWO_FROM_CHUNK4_SWEEP`
- Promotion status: `NO_GO_D64_PROMOTION_UNTIL_POLICY_IS_IMPLEMENTED_AND_REPROVED_ON_D64`
- Verify policy: `best_chunk4_envelope_native_verify_required`

## Result

`chunk4` is the first checked route-layout win on the fast `d8_two_head_seq32` surface. It uses the same workload as the existing alternating baseline and fixes the schedule before proof generation.

- Baseline proof bytes: `66327`
- Best schedule: `chunk4`
- Best proof bytes: `65998`
- Saving vs baseline: `329` bytes
- Opening delta: `-395` bytes
- FRI delta: `-353` bytes
- Decommitment delta: `-42` bytes
- Query delta: `80` bytes
- Statement commitment: `blake2b-256:b1d5550c3bb5401b2198db8e8693e04a1f34e949d9b2502cb5ee5bbe26321ab7`

## Interpretation

This does not justify a Stwo fork. It says deterministic row scheduling can move proof bytes inside the current backend. The useful next step is to turn `chunk4` into a verifier-bound policy knob and then reprove the d64 pressure anchor.

## Non-Claims

- not a Stwo fork
- not a backend patch
- not post-query schedule selection
- not transcript grinding
- not a d64 or d128 result
- not a production route policy
- not timing evidence
- not exact real-valued Softmax
- not full transformer inference

## Reproduce

```bash
python3.10 scripts/zkai_stwo_ai_two_head_seq32_layout_schedule_sweep_gate.py --write-json docs/engineering/evidence/zkai-stwo-ai-two-head-seq32-layout-schedule-sweep-2026-06.json --write-tsv docs/engineering/evidence/zkai-stwo-ai-two-head-seq32-layout-schedule-sweep-2026-06.tsv --write-md docs/engineering/zkai-stwo-ai-two-head-seq32-layout-schedule-sweep-2026-06-04.md
python3.10 -m py_compile scripts/zkai_stwo_ai_two_head_seq32_layout_schedule_sweep_gate.py scripts/tests/test_zkai_stwo_ai_two_head_seq32_layout_schedule_sweep_gate.py
python3.10 -m unittest scripts.tests.test_zkai_stwo_ai_two_head_seq32_layout_schedule_sweep_gate
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_two_head_seq32_fused_softmax_table_proof -- verify docs/engineering/evidence/zkai-stwo-ai-two-head-seq32-layout-chunk4-fused.envelope.json
for f in docs/engineering/evidence/zkai-stwo-ai-two-head-seq32-layout-*-fused.envelope.json; do cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_two_head_seq32_fused_softmax_table_proof -- verify "$f"; done
git diff --check
```
