# Stwo Query-Preview Split Prototype

Date: 2026-05-19
Issue: https://github.com/omarespejel/provable-transformer-vm/issues/704

## Decision

`NARROW_CLAIM_QUERY_PREVIEW_SPLIT_IS_API_FEASIBLE_NOT_SOUND_LABEL_POLICY`

## Result

This gate checks the next opening-geometry attack after the bounded Stwo query
policy hook. The previous result showed that the current Stwo `2.2.0` API draws
FRI queries inside decommitment, so a repo-local wrapper cannot soundly inject
an external query policy.

The source-level read is now sharper:

- Stwo draws canonical queries from the Fiat-Shamir transcript with
  `draw_queries(channel, first_layer_log_size, n_queries)`;
- `FriProver::decommit(channel)` already factors the work into query draw plus
  `decommit_on_queries(&queries)`;
- the verifier samples the same query positions from the transcript;
- the trace/Fri commitments and proof-of-work mix happen before the query draw;
- FRI and trace Merkle decommitments happen after the query draw.

So a prover-side `query_preview_split` is API-feasible: expose the canonical
transcript-drawn query positions after proof-of-work mix and before expensive
FRI/tree decommitment.

The important non-win:

`NO_GO_SOUND_QUERY_GEOMETRY_CONTROL_WITHOUT_GRINDING_OR_POLICY_COMMITMENT`

## Human Read

The current opening-geometry signal remains interesting:

| selected row | typed bytes | path-opening bytes | query span | min pairwise query gap | saving vs two-proof frontier |
| --- | ---: | ---: | ---: | ---: | ---: |
| `adjacent_label_probe_b` | `37,532` | `16,560` | `16,618` | `5,969` | `9,656` typed bytes (`20.4628%`) |

But the split does not let us honestly say "choose the good label after seeing
the queries." By the time queries are previewed, the committed trace, layout,
labels, FRI commitment, and proof-of-work transcript state are already fixed.
Changing them after preview means restarting the proof with a different
transcript. That is transcript grinding, not free proof-size control.

This is still useful. It tells us the next breakthrough path is not more
wrapper-side label guessing. It is either:

1. a deterministic, verifier-bound policy commitment before query draw; or
2. a bounded transcript-grinding experiment with explicit soundness-loss
   accounting and verifier-visible limits.

## Route Classification

| route | status | prover patch | verifier patch | external query choice | can claim probe-B control |
| --- | --- | ---: | ---: | ---: | ---: |
| `preview_only_split` | `FEASIBLE_API_PATCH` | yes | no | no | no |
| `policy_commitment_mix` | `FOLLOWUP_MATCHED_TRANSCRIPT_PATCH` | yes | yes | no | no |
| `external_query_override` | `REJECTED_UNSOUND` | yes | yes | yes | no |
| `transcript_grinding_search` | `FOLLOWUP_SECURITY_BUDGET_REQUIRED` | no | yes | no | no |

## Why This Matters

For the paper path, this separates three things that are easy to confuse:

- proof-size measurement;
- proof-system API structure;
- sound policy control over query/opening geometry.

The current `37,532` typed-byte champion is still the local seq32+d128
opening-geometry signal. This PR does not improve it. It prevents us from
promoting the wrong mechanism. A paper-grade query-geometry claim needs either
a policy that is fixed before the transcript draws queries, or a grinding
budget that is explicit enough to be audited.

## Evidence

Machine-readable evidence:

- `docs/engineering/evidence/zkai-stwo-query-preview-split-prototype-2026-05.json`
- `docs/engineering/evidence/zkai-stwo-query-preview-split-prototype-2026-05.tsv`

Evidence hashes:

- Gate JSON SHA-256:
  `0a3348d51fa36219e8253e1c1a7fdea4d4f5a694f5edc24cc36d5bf7f8cbd442`
- Gate TSV SHA-256:
  `7adcfb39ae6c7f461ee2d2d6549457ff99432067f36600249072ab9c6f3e3864`
- Payload commitment:
  `blake2b-256:e956134a2e69b6d633effe9cf9a9c5f789b47f7d41ce972465ec619b1946800f`
- Mutation guards:
  `18 / 18` rejected.
- Unit tests:
  `18`.

## Reproduction

```bash
python3.10 scripts/zkai_stwo_query_preview_split_prototype_gate.py --write-json docs/engineering/evidence/zkai-stwo-query-preview-split-prototype-2026-05.json --write-tsv docs/engineering/evidence/zkai-stwo-query-preview-split-prototype-2026-05.tsv
python3.10 -m py_compile scripts/zkai_stwo_query_preview_split_prototype_gate.py scripts/tests/test_zkai_stwo_query_preview_split_prototype_gate.py
python3.10 -m unittest scripts.tests.test_zkai_stwo_query_preview_split_prototype_gate
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
- Not a regenerated seq32+d128 proof under a new Stwo API.
- Not a production label-selection policy.
- Not a sound post-query label chooser.
- Not an external query override.
- Not a NANOZK proof-size comparison.
- Not a full transformer block proof.
- Not timing evidence.
- Not production-ready zkML.

## Next Attack

Open a follow-up for bounded transcript grinding or deterministic policy
commitment. The smallest useful experiment should:

- keep canonical Fiat-Shamir query derivation intact;
- make every retry budget explicit;
- account for soundness loss before reporting proof-size improvement;
- bind policy metadata into the verifier-facing statement if a deterministic
  policy is used;
- reject any route that reads final proof bytes or post-decommitment accounting
  before selecting a policy.
