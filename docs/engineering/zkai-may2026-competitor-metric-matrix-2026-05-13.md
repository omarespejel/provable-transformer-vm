# zkAI May 2026 Competitor Metric Matrix - 2026-05-13

## Question

How should the repo compare itself against May 2026 zkML systems without
pretending that the current local evidence is a matched public benchmark?

## Decision

GO for a source-backed comparison matrix. NO-GO for matched benchmark claims.

The comparison posture is:

> NANOZK, Jolt Atlas, and EZKL are the relevant public metric references for
> layerwise or end-to-end zkML proving. This repository should compare against
> them honestly, but its current strongest local result is still architectural:
> STARK-native boundaries can share opening/decommitment plumbing, and the
> current checked seq32+d128 statement-only proof object is a local frontier,
> not a matched external benchmark.

## Evidence

- JSON:
  `docs/engineering/evidence/zkai-may2026-competitor-metric-matrix.json`
- TSV:
  `docs/engineering/evidence/zkai-may2026-competitor-metric-matrix.tsv`
- Gate:
  `scripts/zkai_may2026_competitor_metric_matrix_gate.py`
- Tests:
  `scripts/tests/test_zkai_may2026_competitor_metric_matrix_gate.py`

## Dependency Discipline

The evidence graph is intentionally acyclic:

```text
published zkML TSV -> one-block surface -> package accounting -> competitor matrix
statement-only seq32+d128 gate ----------------------------^
```

The one-block surface reads the published zkML TSV directly for NANOZK context.
The competitor matrix can therefore consume package accounting without feeding
back into the surface that package accounting depends on. The statement-only
gate is consumed as a separate local source artifact so the newest native
seq32+d128 row is pinned by its own mutation and overclaim guards.

## Source-Backed External Rows

The gate consumes `docs/paper/evidence/published-zkml-numbers-2026-04.tsv` and
checks the rows used for comparison:

| System | Workload | Prove | Verify | Proof size | Provenance |
| --- | --- | ---: | ---: | ---: | --- |
| NANOZK | Transformer block proof | `6.3s` | `0.023s` | `6.9 KB` | Halo2 IPA SNARK + lookups; arXiv `2603.18046`, Table 3 + Section 6.2; GPT-2-scale block `d=768`, `dff=3072`; single Intel Xeon CPU @ 2.4GHz with 64GB RAM; timing mode from source, wall/CPU split not reported; evidence path `docs/paper/evidence/published-zkml-numbers-2026-04.tsv`. |
| NANOZK | GPT-2-Small full model | `516s` | `NA` | `NA` | Halo2 IPA SNARK + lookups; arXiv `2603.18046`, Section 6.2; GPT-2-Small, 12 sequential layers; includes setup; single Intel Xeon CPU @ 2.4GHz with 64GB RAM; verify/proof-size not reported by source; evidence path `docs/paper/evidence/published-zkml-numbers-2026-04.tsv`. |
| Jolt Atlas | NanoGPT proof | `14s` | `0.517s` | `NA` | Lookup-centric sumcheck SNARK; arXiv `2602.17452`, Table 1; NanoGPT, about 0.25M params, 4 transformer layers; hardware not reported by source; proof size not reported by source; evidence path `docs/paper/evidence/published-zkml-numbers-2026-04.tsv`. |
| Jolt Atlas | GPT-2 proof | `38s` | `NA` | `NA` | Lookup-centric sumcheck SNARK; arXiv `2602.17452`, Table 3; GPT-2, 125M parameters; hardware and verifier time not reported by source; proof size not reported by source; evidence path `docs/paper/evidence/published-zkml-numbers-2026-04.tsv`. |
| EZKL (reported by Jolt Atlas) | NanoGPT proof | `237s` | `0.34s` | `NA` | Halo2-style zkML with lookups, reported by Jolt Atlas; arXiv `2602.17452`, Table 2; NanoGPT, about 0.25M params, 4 transformer layers; hardware not reported by source; proof size not reported by source; evidence path `docs/paper/evidence/published-zkml-numbers-2026-04.tsv`. |

These are source-backed context rows, not local reproductions.

## Local Rows

| Local surface | Status | Metric |
| --- | --- | ---: |
| Stwo attention/Softmax-table fusion | `GO_BOUNDED_ARCHITECTURE_MECHANISM` | `194,097` matched JSON proof bytes saved |
| d64 RMSNorm/SwiGLU/residual block receipt | `GO_STATEMENT_BOUND_RECEIPT_COMPOSITION` | `49,600` checked slice rows |
| d128 RMSNorm/SwiGLU/residual comparator target | `NO_GO_LOCAL_D128_PROOF_ARTIFACT_MISSING` | `196,608` estimated linear multiplications |
| seq32+d128 statement-only native proof object | `GO_STWO_SEQ32_D128_INNER_POLICY_BOUND_FRONTIER` | `39,516` typed proof bytes; `113,388` JSON proof bytes; saves `7,672` typed bytes versus matched local two-proof frontier |
| attention-derived d128 executable package without VK | `GO_EXTERNAL_RECEIPT_PACKAGE_ACCOUNTING_NO_GO_NATIVE_LAYER_PROOF` | `4,752` bytes, `0.324945x` source |
| attention-derived d128 executable package with VK | `GO_EXTERNAL_RECEIPT_PACKAGE_ACCOUNTING_NO_GO_NATIVE_LAYER_PROOF` | `10,608` bytes, `0.725383x` source |

## Interpretation

The repo should not claim that it beats NANOZK or Jolt Atlas on layer proof
size or end-to-end proving time. It now has a checked seq32+d128 local proof
object, but the object class is still not matched to those external layerwise
or end-to-end rows.

The sharper claim is that the STARK-native route exposes a different mechanism:
attention arithmetic, lookup-heavy table membership, and statement-bound
metadata can share proof-system opening structure when fused into one native
proof object.

The newest local row is the statement-only attempt transcript profile:

```text
matched local two-proof frontier: 47,188 typed bytes
previous single-proof champion: 42,068 typed bytes
statement-only seq32+d128 proof object: 39,516 typed bytes
JSON proof bytes: 113,388
NANOZK-comparable external rows: 0
```

That is a real local improvement, but it is not a NANOZK/Jolt/DeepProve
comparison. The matrix keeps the external rows as source-backed context only.

The new package-accounting rows are useful because they make the attention-derived
one-block statement route comparable as an artifact package:

```text
source statement chain: 14,624 bytes
compressed transcript + proof + public signals: 4,752 bytes
compressed transcript + proof + public signals + VK: 10,608 bytes
```

This package accounting is still not native layer proof-size evidence. The next
comparison milestone is object-class matching: full transformer-block surface,
stable binary accounting, and timing policy before any NANOZK/Jolt/DeepProve
comparison.

## Non-Claims

- Not a matched benchmark against NANOZK, Jolt Atlas, EZKL, DeepProve-1, or RISC Zero.
- Not a proof-size or verifier-time comparison against any external zkML system.
- Not a full d128 transformer block proof.
- Not native proof-size evidence from the external package-accounting rows.
- Not full transformer inference.
- Not exact real-valued Softmax.
- Not production-ready.

## Validation

```bash
python3.10 scripts/zkai_may2026_competitor_metric_matrix_gate.py \
  --write-json docs/engineering/evidence/zkai-may2026-competitor-metric-matrix.json \
  --write-tsv docs/engineering/evidence/zkai-may2026-competitor-metric-matrix.tsv

python3.10 -m unittest scripts.tests.test_zkai_may2026_competitor_metric_matrix_gate

git diff --check

just gate-fast

just gate
```
