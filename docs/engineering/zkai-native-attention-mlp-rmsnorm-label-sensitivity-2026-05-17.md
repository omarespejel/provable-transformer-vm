# zkAI Native Attention+MLP RMSNorm Label Sensitivity - 2026-05-17

## Result

This gate attacks issue `#644` from the other side: before trying to promote a
small RMSNorm-input opening-layout win, check whether a label-only transcript
change can move the same proof enough to fake the win.

The result is a useful NO-GO:

- canonical RMSNorm-input fused proof: `41,428` typed bytes;
- label probe A: `40,836` typed bytes;
- label probe B: `42,100` typed bytes;
- label-only span: `1,264` typed bytes;
- required reduction to beat the two-proof frontier: `729` typed bytes;
- best label probe is still `136` typed bytes above the two-proof frontier and
  `24` typed bytes above the compact selector;
- mutation guard rejects `18 / 18` metric, label, metadata, source, and
  overclaim drift cases.

Human interpretation: the route is real, but sub-kilobyte proof-size claims are
not yet stable enough. The same adapter equation and direct value bytes can move
by more than the whole current frontier budget just by changing the transcript
label.

## What Changed

The Rust proof route now has two explicit RMSNorm-input fused label probes:

- `rmsnorm_input_fused_fixed_label_probe_a_v1`;
- `rmsnorm_input_fused_fixed_label_probe_b_v1`.

Both use the same RMSNorm-input fused adapter constraints:

- `0` adapter base cells;
- same adapter equation inside the RMSNorm input component;
- same source binding;
- same direct value bytes: OODS plus queried values stay unchanged versus the
  canonical RMSNorm-input fused route.

The movement is entirely in path/opening groups:

| Variant | Typed bytes | Delta vs canonical | Path-opening delta | Value delta |
| --- | ---: | ---: | ---: | ---: |
| canonical RMSNorm-input fused | `41,428` | `0` | `0` | `0` |
| label probe A | `40,836` | `-592` | `-592` | `0` |
| label probe B | `42,100` | `+672` | `+672` | `0` |

## Why This Matters

The previous budget said the RMSNorm-input fused route needs to remove `729`
typed bytes to beat the two-proof frontier. This gate shows a label-only probe
can move `1,264` typed bytes across two labels while proving the same relation.

That means a future `600` to `900` byte improvement is not automatically a
breakthrough. It must be backed by one of:

1. a structural opening-layout change whose mechanism is visible in the proof;
2. a multi-label or multi-transcript policy;
3. a query-inventory rule that prevents cherry-picking a favorable transcript.

## Non-Claims

- This is not a two-proof frontier beat.
- This is not a proof-size win from a new architecture.
- This is not a NANOZK proof-size win.
- This is not a matched external zkML benchmark.
- This is not timing evidence.
- This is not a full transformer block proof.
- This is not production-ready zkML.

## Evidence

- `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-label-sensitivity-2026-05.json`
- `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-label-sensitivity-2026-05.tsv`
- `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-accounting-2026-05.json`
- `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-a-2026-05.input.json`
- `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-a-2026-05.envelope.json`
- `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-b-2026-05.input.json`
- `docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-b-2026-05.envelope.json`
- `scripts/zkai_native_attention_mlp_rmsnorm_label_sensitivity_gate.py`
- `scripts/tests/test_zkai_native_attention_mlp_rmsnorm_label_sensitivity_gate.py`

## Reproducibility Metadata

- Backend binary: `zkai_native_attention_mlp_single_proof`.
- Proof backend version:
  `stwo-native-attention-mlp-single-proof-object-rmsnorm-input-fused-adapter-v1`.
- Proof schema version:
  `stwo-native-attention-mlp-single-proof-object-native-adapter-payload-v1`.
- Accounting binary: `zkai_stwo_proof_binary_accounting`.
- Gate script: `scripts/zkai_native_attention_mlp_rmsnorm_label_sensitivity_gate.py`.
- Toolchain: `cargo +nightly-2025-07-14`.
- Feature flags: `--features stwo-backend`.
- Variant labels:
  `rmsnorm_input_fused_fixed_label_probe_a_v1` and
  `rmsnorm_input_fused_fixed_label_probe_b_v1`.
- Targeted Rust test label: `rmsnorm_input_fused_label_probe`.
- Timing mode: proof-size accounting only; no prove/verify timing and no
  median-of-5 timing claim.
- PCS/profile note: both label probes keep the same publication-v1 Stwo PCS
  profile with explicit `pcs_lifting_log_size = 19`.
- Checked surface: two RMSNorm-input fused label-probe proof objects that keep
  the adapter equation inside the d128 RMSNorm input component and keep `0`
  adapter base cells.
- Evidence paths: the JSON/TSV, accounting JSON, input JSON, and envelope JSON
  files listed in the Evidence section above.

## Validation

```bash
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused-label-probe-a docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-a-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-a-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-a-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-a-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused-label-probe-b docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-b-2026-05.input.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-b-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-b-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-b-2026-05.envelope.json
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-a-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-b-2026-05.envelope.json > docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-accounting-2026-05.json
python3 scripts/zkai_native_attention_mlp_rmsnorm_label_sensitivity_gate.py --write-json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-label-sensitivity-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-label-sensitivity-2026-05.tsv
python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_label_sensitivity_gate
cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_fused_label_probe --lib
cargo +nightly-2025-07-14 test --locked --features stwo-backend native_attention_mlp_single_proof --lib
git diff --check
just gate-fast
just gate
```

## Recorded Verify Outputs

```json
{"adapter_mode":"rmsnorm_input_fused_fixed_label_probe_a_v1","adapter_status":"NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER_FUSED_INTO_RMSNORM_INPUT_COMPONENT","adapter_trace_cells":0,"envelope_path":"docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-a-2026-05.envelope.json","mode":"verify","pcs_lifting_log_size":19,"proof_size_bytes":116332,"schema":"zkai-native-attention-mlp-single-proof-cli-summary-v1","verified":true}
{"adapter_mode":"rmsnorm_input_fused_fixed_label_probe_b_v1","adapter_status":"NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER_FUSED_INTO_RMSNORM_INPUT_COMPONENT","adapter_trace_cells":0,"envelope_path":"docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-b-2026-05.envelope.json","mode":"verify","pcs_lifting_log_size":19,"proof_size_bytes":120694,"schema":"zkai-native-attention-mlp-single-proof-cli-summary-v1","verified":true}
```
