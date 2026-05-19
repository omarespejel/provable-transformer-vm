# Native Seq32 Attention + D128 MLP Deterministic Adjacent Label Policy

Status: `GO_SUPPORTED_ADJACENT_LABEL_POLICY_BEATS_CURRENT_CHAMPION`.

This gate follows the adjacent-label probe result. The previous experiment
showed that two adjacent transcript labels beat the current seq32+d128 native
champion, but the fixed adjacent layout still missed by `88` typed bytes. This
experiment refuses to promote the whole inventory and instead checks a
deterministic supported-label rule over the already generated adjacent-label
evidence.

The workload and statement surface stay fixed:

- two-head `seq32` fused attention with bounded Softmax-table lookup checks;
- the attention-to-d128 adapter;
- the seq32-derived d128 RMSNorm/MLP fused surface.

## Result

| variant | policy status | typed bytes | typed delta vs champion | path-opening bytes | path-opening delta | value bytes |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| current duplicate-base champion | comparison champion | `42,068` | `0` | `20,592` | `0` | `21,428` |
| fixed adjacent layout | rejected inflating label | `42,156` | `+88` | `21,184` | `+592` | `20,924` |
| adjacent label probe A | supported label | `40,332` | `-1,736` | `19,360` | `-1,232` | `20,924` |
| adjacent label probe B | supported label | `37,532` | `-4,536` | `16,560` | `-4,032` | `20,924` |

Human read: the full adjacent-label inventory is still not promotable. The
fixed adjacent label preserves the arithmetic/value surface but inflates
path-opening material enough to miss the champion. The supported-label policy
rejects that label and keeps the two checked labels whose worst case saves
`1,736` typed bytes (`4.1267%`) versus the `42,068` typed-byte champion. The
best checked supported label saves `4,536` typed bytes (`10.7825%`).

## Mechanism

The policy is not changing the arithmetic. The adjacent rows keep direct value
bytes stable at `20,924`. The decision is driven by opening material:

- fixed adjacent: `+592` path-opening typed bytes versus the champion;
- probe A: `-1,232` path-opening typed bytes versus the champion;
- probe B: `-4,032` path-opening typed bytes versus the champion.

This keeps the research signal narrow: transcript/opening layout matters for
the larger native boundary, and the supported-label policy is only acceptable
when the source artifact, digest, payload commitment, value bytes, path-opening
bytes, and typed-byte deltas are all pinned.

## Guardrails

- Not a final production label-selection policy.
- Not a generator-backed label inventory.
- Not robust to unseen labels.
- Not a NANOZK proof-size win.
- Not a matched external zkML benchmark.
- Not a full transformer block proof.
- Not exact real-valued Softmax.
- Not timing evidence.
- Not production-ready zkML.

NANOZK's paper-reported d128 block row remains related-work calibration only.
This gate has `0` proof-size-comparable external rows.

## Evidence

- Source adjacent-label policy JSON:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-policy-2026-05.json`
- Source adjacent-label policy SHA-256:
  `b85b9001dc0e9387b4cc2fc49302c9d7bbe7e9ff8d8f6c9b31c394a21b14b9d1`
- Source adjacent-label payload commitment:
  `blake2b-256:f2bcfec2552cc89befcb489271b357063cf13ea302fb91732cb416249ea427a2`
- Deterministic policy gate JSON:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-deterministic-adjacent-label-policy-2026-05.json`
- Deterministic policy gate TSV:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-deterministic-adjacent-label-policy-2026-05.tsv`
- Gate schema:
  `zkai-native-seq32-attention-mlp-deterministic-adjacent-label-policy-gate-v1`
- Decision:
  `GO_SUPPORTED_ADJACENT_LABEL_POLICY_BEATS_CURRENT_CHAMPION`
- Result:
  `WORST_SUPPORTED_ADJACENT_LABEL_SAVES_1736_TYPED_BYTES_VS_42068_CHAMPION`
- Mutation guards:
  `22 / 22` rejected.

The mutation suite rejects decision/result drift, full-inventory overclaims,
fixed-label relabeling, supported-label rejection, typed-byte drift, saving
erasure, support-criteria erasure, value-stability erasure, source digest and
commitment drift, validation-command drift, removed non-claims, explicit
NANOZK overclaims, final-policy overclaims, unknown deterministic-policy
fields, inventory reordering, label metadata drift, proof JSON byte drift,
status-reason drift, champion value-byte drift, and payload-commitment drift.

## Reproduction

```bash
python3.10 scripts/zkai_native_seq32_attention_mlp_deterministic_adjacent_label_policy_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-deterministic-adjacent-label-policy-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-deterministic-adjacent-label-policy-2026-05.tsv
python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_deterministic_adjacent_label_policy_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_deterministic_adjacent_label_policy_gate.py
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_deterministic_adjacent_label_policy_gate
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_adjacent_label_policy_gate
cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_adjacent_label --lib
git diff --check
just gate-fast
just gate
```

## Next Attack

The immediate follow-up is generator-backed label inventory:

- derive the supported labels from source-level label generation rather than a
  hand-curated existing inventory;
- add unseen-label checks so the worst accepted label still beats `42,068`
  typed bytes;
- keep the full-inventory NO-GO explicit until every generated label is
  below the current champion;
- continue treating external rows as non-comparable until the proof object and
  workload class match.
