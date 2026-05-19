# Native Seq32 Attention + D128 MLP Generated Adjacent Label Inventory

Status:
`GO_GENERATED_SUPPORTED_ADJACENT_LABELS_BEAT_CURRENT_CHAMPION_WITH_FULL_INVENTORY_NO_GO`.

This gate follows the deterministic adjacent-label policy. The previous gate
kept the useful numbers honest, but it still operated over an already listed
label inventory. This follow-up derives the current adjacent label family from
the Rust adapter enum and CLI build-input commands, then accepts only generated
labels whose pinned proof accounting beats the current `42,068` typed-byte
seq32+d128 champion.

The workload and statement surface stay fixed:

- two-head `seq32` fused attention with bounded Softmax-table lookup checks;
- the attention-to-d128 adapter;
- the seq32-derived d128 RMSNorm/MLP fused surface.

## Result

| generated label | policy status | typed bytes | typed delta vs champion | path-opening bytes | path-opening delta | value bytes |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| fixed adjacent layout | rejected inflating label | `42,156` | `+88` | `21,184` | `+592` | `20,924` |
| adjacent label probe A | supported label | `40,332` | `-1,736` | `19,360` | `-1,232` | `20,924` |
| adjacent label probe B | supported label | `37,532` | `-4,536` | `16,560` | `-4,032` | `20,924` |

Human read: the good adjacent-label result is no longer just a hand-picked
probe pair. The gate generates the current adjacent family from source:

- Rust adapter modes:
  `rmsnorm_input_fused_adjacent_fixed_v1`,
  `rmsnorm_input_fused_adjacent_label_probe_a_v1`,
  `rmsnorm_input_fused_adjacent_label_probe_b_v1`;
- matching CLI commands:
  `build-input-rmsnorm-fused-adjacent`,
  `build-input-rmsnorm-fused-adjacent-label-probe-a`,
  `build-input-rmsnorm-fused-adjacent-label-probe-b`.

The full generated inventory is still not promotable because the fixed
adjacent label misses the champion by `88` typed bytes. The generated accepted
subset keeps probe A and probe B. Worst accepted remains probe A at `40,332`
typed bytes, saving `1,736` typed bytes (`4.1267%`) versus the champion; best
accepted remains probe B at `37,532` typed bytes, saving `4,536` typed bytes
(`10.7825%`).

## Mechanism

This is a correctness and policy-strengthening result, not a new proof-size
frontier. The proof-size numbers are inherited from the pinned adjacent-label
and deterministic-label gates. The improvement is that accepted labels now have
to satisfy all of the following:

- generated from the pinned Rust adjacent adapter family;
- backed by a matching CLI build-input command;
- backed by proof/accounting rows in the pinned source policy;
- direct value bytes fixed at `20,924`;
- path-opening bytes below the `20,592` champion path-opening budget;
- typed bytes below the `42,068` champion typed-byte budget.

The gate also records rejected unseen examples:

- `rmsnorm_input_fused_adjacent_label_probe_c_v1`, absent from the pinned Rust
  enum and CLI generator surface;
- `rmsnorm_input_fused_post_tail_label_probe_a_v1`, a post-tail label that is
  outside the adjacent family.

## Guardrails

- Not a new proof-size frontier beyond the deterministic label-policy gate.
- Not a final production label-selection policy.
- Not robust to future Rust label additions without regenerating this gate.
- Not a NANOZK proof-size win.
- Not a matched external zkML benchmark.
- Not a full transformer block proof.
- Not exact real-valued Softmax.
- Not timing evidence.
- Not production-ready zkML.

NANOZK's paper-reported d128 block row remains related-work calibration only.
This gate has `0` proof-size-comparable external rows.

## Evidence

- Gate JSON:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-adjacent-label-inventory-2026-05.json`
- Gate TSV:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-adjacent-label-inventory-2026-05.tsv`
- JSON SHA-256:
  `10ef45339f48c41e6cd264906e8ffbcfb49e8e7bb8738ea21174ba8fbb63a1bb`
- TSV SHA-256:
  `c841904da55f409d8746dfa42b76c6ac017010294cb4848a33e1cce1ca10da33`
- Source Rust SHA-256:
  `3d740bda9a3f301edea7a10dc1b9f58878d1a0f067397eecb5ed50465e4b7d95`
- CLI source SHA-256:
  `ef857b997450d683526e0f2d85000da6b5ddfcd33c96640b2e68a323588ec71f`
- Source deterministic policy SHA-256:
  `d5cbe419a545c022036b7347b6fb75a1fbb127dc7a861948d96103e646f338ab`
- Gate schema:
  `zkai-native-seq32-attention-mlp-generated-adjacent-label-inventory-gate-v1`
- Mutation guards:
  `24 / 24` rejected.

The mutation suite rejects decision/result drift, NANOZK overclaims, Rust/CLI
source digest drift, deterministic-policy commitment drift, generated-mode
removal/addition, CLI command drift, accepted-label erasure, fixed-label
promotion, accepted-label value/typed-byte drift, proof-accounting erasure,
unseen-label acceptance, post-tail cross-family acceptance, generator-rule
drift, manual overrides, summary drift, full-inventory promotion,
validation-command drift, removed non-claims, generated-label reordering, and
payload-commitment drift.

## Reproduction

```bash
python3.10 scripts/zkai_native_seq32_attention_mlp_generated_adjacent_label_inventory_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-adjacent-label-inventory-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-adjacent-label-inventory-2026-05.tsv
python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_generated_adjacent_label_inventory_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_generated_adjacent_label_inventory_gate.py
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_generated_adjacent_label_inventory_gate
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_deterministic_adjacent_label_policy_gate
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_adjacent_label_policy_gate
cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_adjacent_label --lib
git diff --check
just gate-fast
just gate
```

## Next Attack

The immediate follow-up is a source-generated proof-object builder:

- label additions should produce input/proof/accounting rows automatically;
- every generated accepted label must still beat `42,068` typed bytes;
- full-inventory promotion remains forbidden until every generated label beats
  the champion;
- external benchmark rows remain non-comparable until proof object and workload
  class match.
