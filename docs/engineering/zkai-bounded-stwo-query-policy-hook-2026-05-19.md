# Bounded Stwo Query-Policy Hook

Date: 2026-05-19
Issue: https://github.com/omarespejel/provable-transformer-vm/issues/701

## Decision

`NARROW_CLAIM_STWO_2_2_COUPLES_QUERY_DRAW_AND_DECOMMITMENT`

## Result

This gate checks whether the current seq32+d128 opening-geometry signal can be
promoted into a true repo-local pre-decommitment query policy.

It cannot, not with Stwo `2.2.0` as currently exposed.

The current Stwo prover draws FRI query locations inside
`FriProver::decommit(channel)` and then immediately uses those positions for
FRI and trace Merkle decommitments. The verifier samples the same query
positions from the Fiat-Shamir transcript. The current repo wrapper only sees
query locations after `prove_ex` returns `ExtendedStarkProof::aux`.

So the honest result is:

`NO_GO_REPO_LOCAL_QUERY_POLICY_HOOK_WITHOUT_STWO_PROVER_VERIFIER_API_PATCH`

## Human Read

The proof-size signal is still interesting:

| selected row | typed bytes | path-opening bytes | query span | min pairwise query gap | saving vs two-proof frontier |
| --- | ---: | ---: | ---: | ---: | ---: |
| `adjacent_label_probe_b` | `37,532` | `16,560` | `16,618` | `5,969` | `9,656` typed bytes (`20.4628%`) |

The problem is not that the signal disappeared. The problem is control. We can
explain why the selected row is small, but we cannot honestly claim a sound
pre-decommitment query policy from the current wrapper.

## Source Boundary

The gate pins these source facts:

- the repo sampler calls `prove_single_extended(input)?`;
- the sampler reads `extended.aux.unsorted_query_locations`;
- `prove_single_extended` delegates to Stwo `prove_ex`;
- Stwo `prove_ex` calls `commitment_scheme.prove_values(...)`;
- Stwo `CommitmentSchemeProver::prove_values` calls
  `fri_prover.decommit(channel)`;
- Stwo `FriProver::decommit(channel)` calls
  `draw_queries(channel, first_layer_log_size, self.config.n_queries)`;
- Stwo then calls `decommit_on_queries(&queries)`;
- Stwo verifier samples query positions from the transcript channel.

That means a direct external query override would be unsound unless the
verifier derives the same policy from the same bound transcript state.

## Bounded Hook Candidates

| hook | status | prover patch | verifier patch | external query choice | interpretation |
| --- | --- | ---: | ---: | ---: | --- |
| `query_preview_split` | candidate, not present | yes | no | no | Split canonical query drawing from decommitment so the prover can observe transcript-drawn queries before decommitment. |
| `policy_commitment_mix` | candidate, needs matched patch | yes | yes | no | Mix a policy commitment into prover and verifier transcript before canonical query sampling. |
| `external_query_override` | rejected | yes | yes | yes | Not acceptable without verifier and transcript binding. |

## Why This Matters

For the paper path, this sharpens the architecture story. The current
seq32+d128 proof-size win is not just "fusion saves bytes." The evidence now
says there are at least three axes:

1. arithmetic and lookup/table fusion;
2. typed statement binding;
3. transcript/query-opening geometry.

The third axis needs proof-system support. More wrapper-side label probing
would be a local maximum unless it becomes transcript-bound.

## Evidence

Machine-readable evidence:

- `docs/engineering/evidence/zkai-bounded-stwo-query-policy-hook-2026-05.json`
- `docs/engineering/evidence/zkai-bounded-stwo-query-policy-hook-2026-05.tsv`

Evidence hashes:

- Gate JSON SHA-256:
  `3befea24d9291fb6bc716afb31ce0c3ced8995626150038af19e0c646a002019`
- Gate TSV SHA-256:
  `a0182d6e2317425d42cda836a5c430994aab6eb48892fb20a1e9e4f48dfa90fe`
- Payload commitment:
  `blake2b-256:9fd9da6dcd8f16d413e9a601ca3b36be6f293de36e285c7de04294e77417fbea`
- Mutation guards:
  `18 / 18` rejected.
- Unit tests:
  `16`.

## Reproduction

```bash
python3.10 scripts/zkai_bounded_stwo_query_policy_hook_gate.py --write-json docs/engineering/evidence/zkai-bounded-stwo-query-policy-hook-2026-05.json --write-tsv docs/engineering/evidence/zkai-bounded-stwo-query-policy-hook-2026-05.tsv
python3.10 -m py_compile scripts/zkai_bounded_stwo_query_policy_hook_gate.py scripts/tests/test_zkai_bounded_stwo_query_policy_hook_gate.py
python3.10 -m unittest scripts.tests.test_zkai_bounded_stwo_query_policy_hook_gate
git diff --check
just gate-fast
just gate
```

The gate reads Stwo `2.2.0` source from `STWO_SOURCE_ROOT` when set, otherwise
from the local Cargo registry. `STWO_SOURCE_ROOT` supports `~` and environment
variables before validation. If the source is not available locally, run
`cargo fetch` before regenerating the evidence.

## Non-Claims

- Not a new proof-size frontier.
- Not a proof regeneration under a true pre-decommitment query policy.
- Not an external query override in current Stwo.
- Not a production label-selection policy.
- Not a NANOZK proof-size win.
- Not a matched external zkML benchmark.
- Not a full transformer block proof.
- Not exact real-valued Softmax.
- Not timing evidence.
- Not production-ready zkML.

## Next Attack

Follow-up: https://github.com/omarespejel/provable-transformer-vm/issues/704

The bounded Stwo fork/prototype should:

- implement `query_preview_split` first because it is the smallest sound
  surface;
- only then test `policy_commitment_mix`;
- regenerate the seq32+d128 boundary;
- preserve proof verification, source binding, statement binding, and mutation
  gates;
- promote only if the regenerated proof beats or preserves the checked
  `37,532` typed-byte row without reading final proof bytes or post-decommitment
  accounting.
