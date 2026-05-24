# EZKL Same-Surface Export Probe for Bounded Attention

Issue: #751

## Decision

`GO_SOURCE_SHAPE_CONFIRMED_NO_GO_DIRECT_SAME_SURFACE_BASELINE`

The checked source artifact has enough typed structure to start a semantic EZKL
export probe, but it is not yet an external baseline row for the proof-pressure
paper. A direct vanilla ONNX path remains `NO_GO` for same-surface comparison
until it preserves the bounded integer table policy, public-output semantics,
and statement binding.

## Source Shape

- source: `docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-seq32-bounded-softmax-table-proof-2026-05.json`
- source sha256: `38e5e287cfb31eaa7a7e7e17ecec662495cf818cc24e5553c8ce13b16aa0b0b8`
- target: `attention-kv-d64-two-head-seq32-causal-mask-bounded-softmax-table-v1`
- heads: `2`
- sequence length: `32`
- key width: `64`
- value width: `64`
- score rows: `1184`
- trace rows: `2048`
- input steps: `64`
- attention output shape: `64 x 64`
- weight table entries: `9`
- weight policy: `exp2_half_gap_table_clipped_8_floor_division`
- semantics: `bounded_table_softmax_approx_attention`
- verifier domain: `ptvm:zkai:attention-kv-stwo-native-d64-two-head-seq32-bounded-softmax-table:v1`

## Candidate Matrix

| candidate | gate | same-surface claim | proof generated | blocker |
|---|---|---|---|---|
| `vanilla_onnx_ezkl_direct_export` | `NO_GO_SAME_SURFACE_TODAY` | `NO_GO` | `false` | no_checked_export_preserves_integer_table_policy_and_statement_bindings |
| `custom_integer_table_ezkl_export_probe` | `IMPLEMENT_PROBE_NEXT` | `NOT_CHECKED` | `false` | requires_custom_export_that_preserves_table_policy_rounding_and_public_outputs |
| `float_onnx_semantic_neighbor` | `NO_GO_FOR_SAME_SURFACE` | `NO_GO` | `false` | float_export_would_define_a_different_statement |
| `zkvm_receipt_fallback` | `GO_FOR_RECEIPT_BASELINE_NOT_PROOF_BOUNDARY_BASELINE` | `SEMANTIC_CONTROL_ONLY` | `false` | receipt_bytes_are_not_a_matched_proof_boundary_comparator |

## Prior Evidence

The earlier `d64` external-adapter surface probe already recorded `NO-GO` for a
vanilla ONNX path as an exact same-statement proof route on an integer zkAI
surface:

`docs/engineering/zkai-d64-external-adapter-surface-probe-2026-05-01.md`

This attention probe is still worth doing, but it inherits the same rule: if
export changes table policy, rounding, public outputs, commitments, or
verifier-domain meaning, label it semantic-neighbor rather than same-surface.

## Non-Claims

- not an EZKL proof-generation benchmark
- not an EZKL verifier-time benchmark
- not a NANOZK comparison
- not a full transformer block comparison
- not evidence that EZKL is unsuitable
- not a public performance claim

## Reproduce

```bash
python3 scripts/zkai_attention_kv_ezkl_same_surface_export_probe.py \
  --source docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-two-head-seq32-bounded-softmax-table-proof-2026-05.json \
  --write-dir target/zkai-ezkl-same-surface-d64-h2-seq32 \
  --write-note docs/engineering/zkai-proof-pressure-ezkl-same-surface-export-probe-2026-05.md
```
