# zkai native seq32 attention MLP median timing

Issue: <https://github.com/omarespejel/provable-transformer-vm/issues/681>

## Decision

`GO_SEQ32_D128_STATEMENT_ONLY_TIMING_CAPTURED_ENGINEERING_LOCAL_ONLY`

The current seq32+d128 statement-only native proof object now has local
median-of-5 timing evidence for build-input, prove, and verify windows.

This is engineering-local timing evidence only. It is not a public benchmark,
not a NANOZK/Jolt/DeepProve/EZKL timing comparison, and not production
throughput evidence.

## Target

The timed object is the checked `statement_only_probe_b` profile from the
Stwo statement-only attempt transcript gate:

| metric | value |
|---|---:|
| typed proof bytes | `39,516` |
| JSON proof bytes | `113,388` |
| matched local two-proof frontier | `47,188` typed bytes |
| typed saving vs matched frontier | `7,672` bytes |

The timed envelope keeps the statement-only attempt policy in the
verifier-facing statement commitment:

- policy version:
  `seq32-d128-adjacent-attempt-domain-statement-only-transcript-v1`
- selected attempt: `adjacent_label_probe_b`
- statement commitment:
  `blake2b-256:6a14c2912df3b2dcd3ce298d8bde566317468be53d084a42104249d7304cf712`

## Local Timing

Captured on a local macOS/aarch64 release build with hostnames, usernames, and
absolute local paths intentionally excluded from the artifact.

| window | median | min | max |
|---|---:|---:|---:|
| build input from source JSON | `778,465 us` | `760,109 us` | `793,783 us` |
| prove existing input | `1,292,909 us` | `1,233,365 us` | `1,310,328 us` |
| verify existing envelope | `898,432 us` | `889,941 us` | `922,254 us` |

The five prover runs all regenerated `113,388` JSON proof bytes.

## Interpretation

This is useful because the current best local proof-size object is not only a
small accounting row. It can be regenerated and verified locally with bounded
median timing evidence. The proving median is about `1.44x` the verifier median
on this host.

The claim remains narrow:

- the proof-size result is still the paper-relevant frontier;
- timing is a practicality guardrail for engineering triage;
- no external-system timing comparison is made;
- no production performance claim is made.

## Evidence

- Raw timing JSON:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-median-timing-raw-2026-05.json`
- Gated timing JSON:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-median-timing-2026-05.json`
- Gated timing TSV:
  `docs/engineering/evidence/zkai-native-seq32-attention-mlp-median-timing-2026-05.tsv`
- Gate script:
  `scripts/zkai_native_seq32_attention_mlp_median_timing_gate.py`
- Rust timing CLI:
  `src/bin/zkai_native_seq32_attention_mlp_median_timing.rs`

## Validation

```bash
cargo +nightly-2025-07-14 run --locked --release --features stwo-backend --bin zkai_native_seq32_attention_mlp_median_timing -- --evidence-dir docs/engineering/evidence --runs 5 > docs/engineering/evidence/zkai-native-seq32-attention-mlp-median-timing-raw-2026-05.json
python3.10 scripts/zkai_native_seq32_attention_mlp_median_timing_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-median-timing-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-median-timing-2026-05.tsv
python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_median_timing_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_median_timing_gate.py
python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_median_timing_gate
cargo +nightly-2025-07-14 test --locked --release --features stwo-backend --bin zkai_native_seq32_attention_mlp_median_timing
```

The gate rejects `13 / 13` timing-policy, source-binding, public-benchmark,
NANOZK-overclaim, host-metadata, validation-command, and payload-commitment
mutations.
