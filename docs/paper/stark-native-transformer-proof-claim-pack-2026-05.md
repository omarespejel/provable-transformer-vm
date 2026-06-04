# STARK-Native Transformer Proof Claim Pack - 2026-05

## Thesis

The current evidence supports a bounded paper-facing thesis:

> STARK-native transformer proofs can fuse attention arithmetic and
> lookup-heavy bounded Softmax-table membership into one proof object, sharing
> commitment and opening plumbing that would otherwise be paid by separate
> source-arithmetic and lookup-sidecar proofs.

This is a proof-architecture claim over checked bounded integer attention
fixtures. It is not a claim about exact real-valued Softmax, full model
inference, public benchmark performance, production readiness, recursion, PCD,
Starknet deployment, or upstream Stwo optimization.

## Defensible Claims

1. Unmodified Stwo-backed evidence now checks source arithmetic, LogUp sidecar,
   and fused proof objects for a controlled Softmax-table route family. The
   contribution is the STARK-native boundary, not a Stwo fork.
2. The checked route matrix has thirty matched `route_rows` entries across
   width, head-count, sequence-length, and combined-axis profiles, with fused
   proof bytes smaller than source-plus-sidecar proof bytes in each entry.
3. The section-delta and typed-size evidence agree on the mechanism: the fused
   object mostly avoids duplicated opening-bucket structure, with the attention
   section-delta split explicitly into FRI proof and decommitment material.
4. The local binary typed accounting slice gives deterministic repo-owned
   accounting over typed Stwo proof fields, while explicitly keeping upstream
   stable proof serialization as a non-claim.
5. The model-faithful bridge checks that the existing d8 bounded Softmax-table
   fixture trace is exactly the trace emitted by a model-facing quantized
   attention policy at the trace boundary.

## Evidence Handles

- Route matrix:
  `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`
- Controlled component grid:
  `docs/engineering/evidence/zkai-attention-kv-stwo-controlled-component-grid-2026-05.json`
- Section delta:
  `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-section-delta-2026-05.json`
- Typed size estimate:
  `docs/engineering/evidence/zkai-attention-kv-stwo-typed-size-estimate-2026-05.json`
- Binary typed accounting:
  `docs/engineering/evidence/zkai-attention-kv-stwo-binary-typed-proof-accounting-2026-05.json`
- Median timing discipline:
  `docs/engineering/evidence/zkai-attention-kv-stwo-softmax-table-median-timing-2026-05.json`
- Seq32 fused route:
  `docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-fused-softmax-table-gate-2026-05.json`
- Model-faithful bridge:
  `docs/engineering/evidence/zkai-attention-kv-model-faithful-quantized-attention-bridge-2026-05.json`
- Stwo-AI layout diagnostic:
  `docs/engineering/evidence/zkai-stwo-ai-d64-four-head-seq64-chunk4-policy-gate-2026-06.json`
- Machine-readable claim pack:
  `docs/paper/evidence/stark-native-transformer-claim-pack-2026-05.json`
- Paper release audit manifest:
  `docs/paper/evidence/stark-native-transformer-paper-release-manifest-2026-06.json`

## Quantitative Core

Reproduction context: the route-matrix numbers below are taken from
`route_rows` in
`docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`
under route id
`local_stwo_attention_kv_fused_softmax_table_controlled_route_matrix` and
timing policy `proof_existence_and_byte_accounting_only_not_public_benchmark`.
They are regenerated with
`python3.10 scripts/zkai_attention_kv_fused_softmax_table_route_matrix_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.tsv`.
The section-delta numbers are taken from `profile_rows` in
`docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-section-delta-2026-05.json`
under route id `local_stwo_attention_kv_fused_softmax_table_section_delta`,
proof-object scope
`matched_serialized_stark_proof_json_sections_for_source_sidecar_and_fused_envelopes`,
and timing policy `proof_bytes_only_not_timing_not_public_benchmark`. They are
regenerated with
`python3.10 scripts/zkai_attention_kv_fused_softmax_table_section_delta_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-section-delta-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-section-delta-2026-05.tsv`.
Per-row Stwo backend versions are recorded in the section-delta artifact fields
`profile_rows[*].artifacts.{source,sidecar,fused}.proof_backend_version`.
The route rows carry the step counts, lookup claims, trace rows, and serialized
proof byte columns used below.

All fused/split rows in the paper-facing route matrix use the same fixed
experimental Stwo configuration: proof-of-work `10` bits, FRI log blowup `1`
(blowup factor `2`), FRI query count `3`, and FRI fold step `1`. The
measurements are proof-byte measurements under that fixed configuration, not
production-security constants and not timing claims.

The route matrix records thirty checked matched `route_rows` entries. Across
those entries,
the fused proof bytes total `6,397,632` versus `7,164,515` bytes for the
matched source-plus-sidecar controls, a `766,883` byte aggregate saving.
Matched fused ratios range from `0.676723` to `0.964602`.

The paper headline is narrower than the full route matrix. It focuses on four
sequence-axis rows where `seq32` to `seq64` grows lookup claims by
`3.729730x` and trace rows by `4.000000x`, while fused proof payload bytes grow
only `1.064910x` to `1.080697x`. The split frontier is also sublinear, so the
claim is not that only fusion has logarithmic STARK behavior. The claim is that
the fused route keeps the smaller proof-size frontier against the matched split
comparator.

The controlled component grid records ten checked fine-grained typed-component
profiles. The source-plus-sidecar typed estimate totals `285,584` bytes and the
fused typed estimate totals `234,296` bytes, a `51,288` byte (`17.9590%`)
aggregate saving. Per-profile typed saving ranges from `9.1035%` to `27.7371%`.

The section-delta evidence now checks eleven profiles, including the
`d64_four_head_seq64` decision-gate row. It records `1,129,927` source-plus-sidecar
serialized proof bytes, `905,969` fused serialized proof bytes, and `223,958`
saved bytes. Of that saving, `209,155` bytes, or `93.3903%`, are in the opening
bucket, dominated by FRI proof and decommitment material.

| attention section-delta category | bytes saved | share of total saving |
|---|---:|---:|
| FRI proof material | `129,316` | `57.7412%` |
| Decommitment material | `79,839` | `35.6491%` |
| Other proof material | `14,803` | `6.6097%` |
| Total | `223,958` | `100.0000%` |

The `d64_four_head_seq64` row ties that mechanism to the main headline surface:
`315,785` split proof bytes versus `276,503` fused proof bytes, saving `39,282`
bytes at a `0.875605` fused ratio. Its opening bucket accounts for `37,827` of
those saved bytes.

The attention-derived `d128` MLP-side attribution is a separate typed-accounting
slice, not the same surface as the attention sequence rows. It still points in
the same direction: six separate proof objects total `59,344` typed bytes, the
fused proof is `22,576` typed bytes, and FRI plus trace decommitments account
for `33,280` of `36,768` saved typed bytes (`90.5135%`).

## GO / NO-GO Posture

GO:

- Use the claim that bounded attention arithmetic and Softmax-table membership
  can be fused into one native Stwo proof object.
- Use matched proof-byte, typed-size, section-delta, and component-grid evidence
  as proof-architecture support.
- Say the observed savings are dominated by shared opening-bucket plumbing,
  specifically FRI proof and decommitment material in the checked attention
  section-delta artifact.
- Say the d8 fixture now has a checked model-facing quantized-attention bridge
  at the trace boundary.
- Say Stwo-AI remains future backend-specialization work around openings,
  decommitments, table identity, and layout, not an assumption behind the current
  result.

NO-GO:

- Do not describe this as exact real-valued Softmax.
- Do not describe this as full inference or a complete transformer runtime.
- Do not describe this as a public benchmark or a verifier-time win.
- Do not describe this as production-ready or Starknet deployed.
- Do not describe the local accounting stream as upstream Stwo proof
  serialization.
- Do not claim backend-internal source-vs-lookup byte attribution.
- Do not describe this as a Stwo fork, upstream Stwo patch, SIMD improvement, or
  custom Stwo-AI prover result.

## Blockers

1. Stable verifier-facing binary Stwo proof serialization is not exposed on this
   repo surface.
2. Backend-internal attribution between source arithmetic and lookup columns is
   still missing.
3. The local median-of-5 timing gate is discipline only; it does not support a
   fused verifier-time win claim.
4. The model-faithful bridge covers the checked d8 fixture trace only.
5. Starknet verifier packaging, calldata accounting, deployment, release gates,
   and adversarial integration hardening remain incomplete.
6. No tokenizer/model-weight import, full runtime, accuracy, or perplexity gate
   is bound.
7. Stwo-AI backend specialization remains a future-work agenda until it produces
   repeated verifier-bound gains on the same surfaces.

## Validation

```bash
python3.10 scripts/zkai_paper_claim_pack_gate.py \
  --write-json docs/paper/evidence/stark-native-transformer-claim-pack-2026-05.json

python3.10 -m py_compile \
  scripts/zkai_paper_claim_pack_gate.py \
  scripts/tests/test_zkai_paper_claim_pack_gate.py

python3.10 -m unittest scripts.tests.test_zkai_paper_claim_pack_gate

python3.10 scripts/paper/paper_preflight.py --repo-root .

scripts/run_paper_preflight_suite.sh

git diff --check

git diff --exit-code \
  docs/paper/evidence/stark-native-transformer-claim-pack-2026-05.json \
  docs/paper/stark-native-transformer-proof-claim-pack-2026-05.md \
  docs/paper/proof-pressure-boundaries-for-stark-native-transformers-2026.md
```
