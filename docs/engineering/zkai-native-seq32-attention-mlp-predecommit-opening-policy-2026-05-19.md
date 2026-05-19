# Native Seq32 Attention+MLP Pre-Decommitment Opening Policy

Date: 2026-05-19
Issue: https://github.com/omarespejel/provable-transformer-vm/issues/700

## Decision

`NARROW_CLAIM_CURRENT_STWO_WRAPPER_EXPOSES_QUERY_GEOMETRY_AFTER_PROVE_EX`

## Result

The previous dry-run sampler gave a real mechanism signal: query-location
geometry selects the low-opening adjacent probe-B row without using final proof
bytes or grouped accounting as predictor inputs.

This gate checks whether that can be promoted to a true pre-decommitment
policy. It cannot, not with the current wrapper. The current sampler obtains
query locations only after `prove_single_extended(input)?` returns an
`ExtendedStarkProof`, and `prove_single_extended` delegates to Stwo `prove_ex`.
So the available policy is:

`post_transcript_pre_accounting_not_true_predecommit`

The numbers are still useful:

| selected row | final typed bytes | final path-opening bytes | saving vs `42,068` champion | saving vs best pre-registered seed |
| --- | ---: | ---: | ---: | ---: |
| `adjacent_label_probe_b` | `37,532` | `16,560` | `4,536` typed bytes (`10.7825%`) | `2,736` typed bytes |

## Human Read

This is an honest narrowing result, not a failure of the research direction.
We found a small row because the sampled FRI query locations are unusually
clustered:

- probe B query span: `16,618`;
- probe B minimum pairwise query gap: `5,969`;
- probe B path-opening bucket: `16,560` typed bytes.

The problem is timing. In the current Stwo wrapper, the signal becomes visible
after the proof path has already gone through `prove_ex` and exposed
`ExtendedStarkProof::aux`. That is late enough for explanation and local
selection, but too late to claim a true pre-decommitment policy.

## Why This Matters

For the paper path, this refines the architectural claim:

> STARK-native transformer boundaries are shaped by arithmetic fusion,
> lookup/table fusion, and transcript/query-opening geometry. But making query
> geometry into a reproducible optimization requires a proof-system hook, not a
> post-hoc label table.

That is a stronger and safer claim than pretending we already have production
query control.

## Source Boundary

The gate pins these current-source facts:

- `sample_zkai_native_seq32_attention_mlp_openings` calls
  `prove_single_extended(input)?`;
- the sampler reads `extended.aux.unsorted_query_locations`;
- `prove_single_extended` delegates to
  `prove_ex::<SimdBackend, Blake2sM31MerkleChannel>`;
- the current sampler boundary is
  `PROVER_INTERNAL_EXTENDED_AUX_QUERY_LOCATIONS_ONLY`, not a pre-decommitment
  hook.

## Evidence

Machine-readable evidence:

- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-predecommit-opening-policy-2026-05.json`
- `docs/engineering/evidence/zkai-native-seq32-attention-mlp-predecommit-opening-policy-2026-05.tsv`

Evidence hashes:

The canonical values below come from regenerating the checked JSON/TSV evidence
with the command in the reproduction block. PR descriptions and handoff notes
must be updated to these values after evidence metadata changes.

- Gate JSON SHA-256:
  `aa623005579aa408ba652fad63dedf7020b6cbe1237b66fc8f33febe828d4923`
- Gate TSV SHA-256:
  `9d27db58076a846b5cdfa15b5f8e74cdcd703cf41292c03f33f867a75e531a81`
- Payload commitment:
  `blake2b-256:367bc34be7660e0d4351af47a0ecc6551486dad7acd098ecb73216f447d1790c`
- Mutation guards:
  `18 / 18` rejected.

Reproducibility metadata:

- `selected_backend_version`:
  `stwo-native-seq32-attention-mlp-single-proof-object-rmsnorm-input-fused-adjacent-fixed-v1`
- `selected_adapter_mode`:
  `rmsnorm_input_fused_adjacent_label_probe_b_v1`
- `rust_source_sha256`:
  `7818c25b034da111cddd090783ea6bc66fd0c4dc2c67f95e3281899d0235344b`
- `cli_source_sha256`:
  `ea68996b62dd763255e20479672bf7a392494a710c87eb2c0da84482873b4b52`
- `policy_row_count`: `9`
- `fri_query_count_per_row`: `3`
- `mutation_step_count`: `18`
- `unittest_step_count`: `13`
- `local_release_gate_step_count`: `14`

The mutation suite rejects decision drift, result overclaiming, true
pre-decommitment overclaims, Rust/CLI/evidence digest drift, source-marker
erasure, pre-decommitment availability flips, final-accounting leakage into
policy inputs, row-identity promotion, selected-row drift, saving drift,
required-hook erasure, evaluation-row erasure, validation-command drift,
removed non-claims, and payload-commitment drift.

## Reproduction

```bash
python3.10 scripts/zkai_native_seq32_attention_mlp_predecommit_opening_policy_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-predecommit-opening-policy-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-predecommit-opening-policy-2026-05.tsv
python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_predecommit_opening_policy_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_predecommit_opening_policy_gate.py
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_predecommit_opening_policy_gate
git diff --check
just gate-fast
just gate
```

The gate run evaluates `9` policy rows, checks `3` FRI query locations per row,
and executes `18` mutation cases. The unit-test command currently runs `13`
tests. The full local release gate has `14` steps.

## Non-Claims

- Not a true pre-decommitment selector in the current Stwo wrapper.
- Not a production label-selection policy.
- Not a new proof-size frontier beyond the existing adjacent probe-B row.
- Not a NANOZK proof-size win.
- Not a matched external zkML benchmark.
- Not a full transformer block proof.
- Not exact real-valued Softmax.
- Not timing evidence.
- Not production-ready zkML.

## Next Attack

The next useful issue is a bounded Stwo query-policy hook:
https://github.com/omarespejel/provable-transformer-vm/issues/701

- split query drawing from Merkle/FRI decommitment, or accept a committed
  external query policy before decommitment;
- regenerate the seq32+d128 boundary under that committed policy;
- preserve source binding, verifier checks, and mutation gates;
- only promote if the regenerated proof object beats the current checked row
  without using final accounting as a selector.
