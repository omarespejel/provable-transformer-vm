# Model-Faithful D128 Block-Boundary Preflight

Issue: #715

## Decision

`GO_MODEL_FAITHFUL_D128_BLOCK_BOUNDARY_PREFLIGHT`

Result:

`ATTACK_MINIMAL_BLOCK_BOUNDARY_AROUND_MODEL_FAITHFUL_D128_ATTENTION_DERIVED_MLP`

This is a decision artifact, not a new proof object. It makes the next research
step explicit after PR #744: use the model-faithful d128 attention-derived MLP
single proof as the anchor for the smallest scoped block-boundary wrapper.

## Human Meaning

The previous scoped d128 row was useful, but it still had a limiting caveat:
the MLP input was co-located with attention rather than derived from the actual
d128 attention output artifact. The new model-faithful row removes that caveat and
still beats the matched split frontier.

The important detail is that the stronger binding did not make the proof
heavier. The single proof JSON moved by `-951`
bytes versus the co-located row, typed bytes stayed flat, and the typed saving
improved by `560` bytes.

That makes the next gate a block-boundary question, not a bigger-grid question:
can we wrap the already-bound d128 attention-derived MLP route into the smallest
scoped block boundary without losing the local proof-size win?

## Checked Rows

| row | status | scope | bytes | reference | saving | ratio | action |
|---|---|---|---:|---:|---:|---:|---|
| previous colocated d128 boundary | `BASELINE_SUPERSEDED_BY_MODEL_FAITHFUL_BINDING` | proof_json_and_typed_bytes | `504,518` | `520,399` | `15,881` | `0.969483` | keep as regression baseline not current claim anchor |
| model faithful d128 boundary | `CURRENT_CLAIM_ANCHOR_GO` | proof_json_and_typed_bytes | `503,567` | `522,480` | `18,913` | `0.963801` | use as anchor for minimal scoped block boundary |
| attention derived mlp surface | `VALUE_BOUND_MLP_SURFACE_GO` | component_surface_typed_bytes | `24,832` | `56,976` | `32,144` | `0.435833` | preserve value derivation and residual surface in next boundary |
| d128 sequence stress context | `FALLBACK_STRESS_PATH_NOT_PRIMARY` | raw_proof_bytes_growth | `481,870` | `522,187` | `40,317` | `0.922792` | run d128 h2 seq64 if minimal block wrapper becomes no go |
| next block boundary gate | `ATTACK_NEXT` | decision_gate |  |  |  |  | IMPLEMENT MINIMAL SCOPED BLOCK BOUNDARY AROUND MODEL FAITHFUL D128 ROUTE |

## GO Gate

- the minimal block-boundary wrapper preserves the model-faithful d128 attention-derived MLP binding;
- the new proof beats the matched local split frontier before any external comparison;
- source digests, statement commitments, accounting bytes, and non-claims remain pinned;
- mutation gates reject relabeling, stale co-location claims, full-block claims, and external benchmark claims.

## NO-GO Gate

- the wrapper only works by dropping the attention-derived MLP input binding;
- the scoped proof is equal or heavier than its matched split frontier;
- the next story requires treating d128 seq64 or d256 as the primary claim;
- the result needs speed, NANOZK, full-block, or production-throughput wording to sound interesting.

## Evidence

- JSON: `docs/engineering/evidence/zkai-model-faithful-d128-block-boundary-preflight-2026-05.json`
- TSV: `docs/engineering/evidence/zkai-model-faithful-d128-block-boundary-preflight-2026-05.tsv`
- Model-faithful anchor: `docs/engineering/evidence/zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05.json`
- Prior co-located row: `docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.json`
- Slope table: `docs/engineering/evidence/zkai-proof-pressure-slope-table-2026-05.json`

The gate rejects `15 / 15` mutation cases covering
source drift, issue drift, primary-gate drift, metric drift, legacy caveat
reintroduction, full-block overclaim, external-comparison overclaim, sequence
slope drift, non-claim drift, validation-command drift, and payload-commitment
drift.

## Non-Claims

- not a full transformer block proof.
- not a public proving-speed benchmark.
- not a NANOZK proof-size win.
- not a matched external zkML comparison.
- not exact real-valued Softmax.
- not full autoregressive inference.
- not production-throughput evidence.

## Reproduce

```bash
python3.10 scripts/zkai_model_faithful_d128_block_boundary_preflight_gate.py --write-json docs/engineering/evidence/zkai-model-faithful-d128-block-boundary-preflight-2026-05.json --write-tsv docs/engineering/evidence/zkai-model-faithful-d128-block-boundary-preflight-2026-05.tsv --write-md docs/engineering/zkai-model-faithful-d128-block-boundary-preflight-2026-05-24.md
python3.10 -m py_compile scripts/zkai_model_faithful_d128_block_boundary_preflight_gate.py scripts/tests/test_zkai_model_faithful_d128_block_boundary_preflight_gate.py
python3.10 -m unittest scripts.tests.test_zkai_model_faithful_d128_block_boundary_preflight_gate
git diff --check
just gate-fast
just gate
```
