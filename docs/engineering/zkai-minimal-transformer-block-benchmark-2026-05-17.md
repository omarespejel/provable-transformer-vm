# zkAI Minimal Transformer-Block Benchmark Contract - 2026-05-17

Issue: `#649`

Status: `GO_MINIMAL_BLOCK_BENCHMARK_CONTRACT_NO_GO_MATCHED_PROOF_CLAIM`.

This gate creates the shared benchmark object for the next research phase. It
does not add a new proof system. It classifies the current block surface so the
next PRs cannot compare a statement artifact, an external SNARK receipt, a
two-proof target, and a missing native block proof as if they were the same
thing.

## Result

The benchmark contract is ready, but the matched proof claim is still a NO-GO.

Important numbers:

- component rows: `10`
- local native Stwo proof components: `2`
- current two-proof frontier: `40,700` typed bytes
- adjacent layout canonical proof object: `40,948` typed bytes
- adjacent worst-label proof object: `42,724` typed bytes
- worst-label gap above frontier: `2,024` typed bytes
- typed public statement chain: `199,553` rows
- external statement receipt: `807` proof bytes
- NANOZK paper-reported d128 block proof context: `6,900` bytes
- mutation gate: `14 / 14` rejected

The human meaning is simple: we now have one table that says what each object
is. That is not the breakthrough yet, but it is the guardrail that prevents the
next benchmark from fooling us.

## Benchmark Contract

The benchmark object pins:

- model-side width: `d128`
- current attention source width: `d8`
- MLP width: `512`
- component contract:
  attention boundary, Softmax-table lookup membership, RMSNorm substitute,
  gate/value projection, bounded SiLU/SwiGLU activation, down projection,
  residual boundary, and typed public statement.

Approximation policy is explicit:

- Softmax is a bounded table/LogUp fixture, not exact real-valued Softmax.
- RMSNorm is the checked substitute, not exact LayerNorm.
- SiLU/SwiGLU is the checked bounded substitute, not exact GELU.
- Model-faithful quantized accuracy is still missing.

## Object Classes

| component | object class | status | primary value | comparison boundary |
| --- | --- | --- | ---: | --- |
| attention boundary + Softmax lookup | `local_native_stwo_proof_component` | `GO` | `18,124` typed bytes | component only |
| RMSNorm/MLP/residual substitute | `local_native_stwo_proof_component` | `GO` | `22,576` typed bytes | substitute semantics |
| attention-to-d128 adapter layout | `local_native_stwo_proof_object_attempt` | `NO_GO` | `42,724` typed bytes | worst-label failure |
| two-proof frontier | `local_two_proof_target` | `GO` | `40,700` typed bytes | internal frontier only |
| typed public statement chain | `local_statement_artifact` | `GO` | `199,553` rows | not a proof-size row |
| external statement receipt | `external_snark_statement_receipt` | `GO` | `807` bytes | not STARK-native block proof |
| native full block proof object | `missing_native_proof_object` | `NO_GO` | missing | required before matched comparison |
| NANOZK context row | `paper_reported_external_context` | context only | `6,900` bytes | not local reproduction |
| GKR/Hyrax sidecar lane | `followup_hypothesis` | issue `#650` | not implemented | exploratory |
| Jolt/Atlas lookup lane | `followup_hypothesis` | issue `#651` | not implemented | exploratory |

## Claim Boundary

Allowed:

- internal frontier comparisons;
- source-backed external context;
- object-class gap accounting;
- follow-up issues for GKR/Hyrax and Jolt/Atlas lanes.

Forbidden:

- NANOZK win;
- Jolt or Atlas win;
- full transformer-block proof claim;
- timing claim;
- model-faithful accuracy claim.

## Non-Claims

- Not a full LLM proof.
- Not production zkML.
- Not exact real-valued Softmax.
- Not exact LayerNorm.
- Not exact GELU.
- Not a NANOZK proof-size win.
- Not a Jolt or Atlas benchmark win.
- Not a GKR or Hyrax implementation.
- Not timing evidence.
- Not recursion or proof-carrying data.

## Evidence

- JSON:
  `docs/engineering/evidence/zkai-minimal-transformer-block-benchmark-2026-05.json`
- TSV:
  `docs/engineering/evidence/zkai-minimal-transformer-block-benchmark-2026-05.tsv`
- Gate:
  `scripts/zkai_minimal_transformer_block_benchmark_gate.py`
- Tests:
  `scripts/tests/test_zkai_minimal_transformer_block_benchmark_gate.py`

Source artifacts:

- `docs/engineering/evidence/zkai-one-transformer-block-surface-2026-05.json`
- `docs/engineering/evidence/zkai-d128-attention-mlp-boundary-frontier-2026-05.json`
- `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-adjacent-layout-2026-05.json`
- `docs/engineering/evidence/zkai-matched-d64-d128-evidence-table-2026-05.json`

## Validation

```bash
python3 scripts/zkai_minimal_transformer_block_benchmark_gate.py --write-json docs/engineering/evidence/zkai-minimal-transformer-block-benchmark-2026-05.json --write-tsv docs/engineering/evidence/zkai-minimal-transformer-block-benchmark-2026-05.tsv
python3 -m py_compile scripts/zkai_minimal_transformer_block_benchmark_gate.py scripts/tests/test_zkai_minimal_transformer_block_benchmark_gate.py
python3 -m unittest scripts.tests.test_zkai_minimal_transformer_block_benchmark_gate
python3 scripts/research_issue_lint.py --repo-root .
git diff --check
just gate-fast
just gate
```
