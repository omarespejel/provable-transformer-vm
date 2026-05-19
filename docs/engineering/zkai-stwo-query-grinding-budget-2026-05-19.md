# Stwo Query-Grinding Budget

Date: 2026-05-19
Issue: https://github.com/omarespejel/provable-transformer-vm/issues/706

## Decision

`NARROW_CLAIM_SMALL_VERIFIER_BOUND_RETRY_BUDGET_CAN_RECOVER_PROBE_B_INVENTORY`

## Result

`GO_MECHANISM_LEAD_NOT_PROOF_SIZE_FRONTIER`

This gate checks whether the query-preview split can become a controlled
research mechanism instead of post-hoc label selection.

The answer is narrowly positive:

- a fixed two-probe attempt domain recovers the current probe-B row;
- the relative Fiat-Shamir grinding loss is `log2(2) = 1.000000` bit;
- the result saves `4,624` typed bytes versus the fixed adjacent layout;
- it does not improve the current champion, because the best row is still
  `adjacent_label_probe_b` at `37,532` typed bytes;
- it is not promotable as a proof-size frontier until regenerated proofs bind
  the attempt domain in verifier-facing metadata.

## Human Read

The useful result is small but real. We have a way to talk about query geometry
without pretending that the prover gets free choice after seeing queries.

Instead of saying "pick the label that gives the smallest proof," the honest
mechanism is:

1. predefine a small attempt domain;
2. bind that domain into the verifier-facing statement;
3. let the prover try only those attempts;
4. charge the Fiat-Shamir search space by `log2(attempt_budget)`;
5. reject unbounded retry or final-proof-byte selection.

On the checked inventory, the two-probe domain
`adjacent_label_probe_a, adjacent_label_probe_b` is enough to recover the
champion:

| policy | attempts | loss bits | best row | best typed bytes | vs fixed layout | vs champion |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| `fixed_layout_budget_1` | `1` | `0.000000` | `fixed_adjacent_layout` | `42,156` | `0` | `-4,624` |
| `two_probe_budget_2` | `2` | `1.000000` | `adjacent_label_probe_b` | `37,532` | `+4,624` | `0` |
| `seed_only_budget_6` | `6` | `2.584963` | `adjacent_seed_02` | `40,268` | `+1,888` | `-2,736` |
| `all_inventory_budget_9` | `9` | `3.169925` | `adjacent_label_probe_b` | `37,532` | `+4,624` | `0` |

The seed-only sweep is a no-go: it spends more budget and still misses the
champion by `2,736` typed bytes. The all-inventory sweep is also a no-go: it
spends `3.169925` bits to get the same result as the two-probe policy.

## Why This Matters

For the paper path, this turns query/opening geometry into a proof-system policy
problem:

- the retry budget is explicit;
- the security cost is explicit;
- the allowed attempts are bounded;
- the non-claim is explicit: no regenerated proof object and no new frontier.

This is better than both extremes:

- it avoids throwing away the query-geometry signal;
- it avoids pretending post-query selection is free compression.

## Evidence

Machine-readable evidence:

- `docs/engineering/evidence/zkai-stwo-query-grinding-budget-2026-05.json`
- `docs/engineering/evidence/zkai-stwo-query-grinding-budget-2026-05.tsv`

Evidence hashes:

- Gate JSON SHA-256:
  `85c9dd80c68063006d9822c5022aff276f8c025269255cdfce47800451d0e3ec`
- Gate TSV SHA-256:
  `6961f51c3863814883bcb6cd554b919572d532bdfe34bebffe1099f6ec2bb587`
- Inventory commitment:
  `blake2b-256:f39a42cb0945b73cc326e2993e409af1e5b69c9bfc1f79faa2ad0e4db874e1b5`
- Payload commitment:
  `blake2b-256:9dd16fba4ad07e7a61748742041ebe41df64e8e3785de94aa98ca1550ac926c8`
- Mutation guards:
  `21 / 21` rejected.
- Unit tests:
  `18`.

## Reproduction

```bash
python3.10 scripts/zkai_stwo_query_grinding_budget_gate.py --write-json docs/engineering/evidence/zkai-stwo-query-grinding-budget-2026-05.json --write-tsv docs/engineering/evidence/zkai-stwo-query-grinding-budget-2026-05.tsv
python3.10 -m py_compile scripts/zkai_stwo_query_grinding_budget_gate.py scripts/tests/test_zkai_stwo_query_grinding_budget_gate.py
python3.10 -m unittest scripts.tests.test_zkai_stwo_query_grinding_budget_gate
git diff --check
just gate-fast
just gate
```

## Non-Claims

- Not a new proof-size frontier.
- Not regenerated proof objects under a grinding API.
- Not an absolute soundness claim.
- Not a verifier implementation.
- Not a production query policy.
- Not a NANOZK proof-size comparison.
- Not a full transformer block proof.
- Not timing evidence.

## Next Attack

The next implementation should bind the allowed attempt domain and selected
attempt id in the verifier-facing statement, then regenerate the seq32+d128
proof under the two-probe policy. A future claim is only promotable if the
verifier rejects attempts outside the domain and mutation guards reject
unbounded retry, final proof bytes, and post-decommitment accounting as policy
inputs.
