# D64 High-Query Paper Audit Packet

Date: 2026-06-27

Repository: `omarespejel/provable-transformer-vm`

Evidence base commit: `61460ebd6b76df876e92484e901ad00d7143e0cd`

Primary paper: `docs/paper/proof-pressure-boundaries-for-stark-native-transformers-2026.md`

## Result Under Audit

Surface: `d64_four_head_seq64_bounded_softmax_table_attention`

Question: if FRI query count is raised under an explicit query-count-only patch,
does the fused boundary remain smaller than the matched source-plus-sidecar
split frontier?

Answer: yes, on this checked d64 surface.

| FRI queries | split proof bytes | fused proof bytes | saving | fused ratio |
|---:|---:|---:|---:|---:|
| `3` | `315,785` | `276,503` | `39,282` | `0.875605x` |
| `6` | `453,733` | `390,437` | `63,296` | `0.860499x` |
| `12` | `727,747` | `612,237` | `115,510` | `0.841277x` |

Interpretation: the fused proof-size advantage survives higher FRI query counts
on the d64 four-head seq64 surface. This is engineering sensitivity evidence,
not production-security parameter evidence and not a d128 high-query result.

## Machine-Readable Evidence

- Summary JSON:
  `docs/engineering/evidence/zkai-attention-kv-d64-high-query-sensitivity-2026-06.json`
- Summary TSV:
  `docs/engineering/evidence/zkai-attention-kv-d64-high-query-sensitivity-2026-06.tsv`
- Engineering note:
  `docs/engineering/zkai-attention-kv-d64-high-query-sensitivity-2026-06.md`
- Paper figure:
  `docs/paper/figures/proof-pressure-d64-high-query-sensitivity-2026-06.svg`
- Figure TSV:
  `docs/paper/figures/proof-pressure-d64-high-query-sensitivity-2026-06.tsv`

Payload commitment:
`blake2b-256:cc78f6ab678f7a60fb48402b371fd1dbe8ad94fd1a312a782807a1587f5f459e`

## Artifact Hashes

| query | role | proof bytes | envelope bytes | sha256 | path |
|---:|---|---:|---:|---|---|
| `3` | source | `272,638` | `73,613,598` | `955de60217be05dd5bf61d51990f6f553050feb87c9051be22cc53869071fcca` | `docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.envelope.json` |
| `3` | sidecar | `43,147` | `71,779,632` | `64cb8b285340eed5e5dcb059fcdb2adb5f1952a2ddea999b8065899c98f1a835` | `docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-softmax-table-logup-sidecar-proof-2026-05.envelope.json` |
| `3` | fused | `276,503` | `73,647,778` | `641bcd4c8b29ad8098b47a4ec293b6972913ad0ceee9548229a219bd3bea7000` | `docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-fused-softmax-table-proof-2026-05.envelope.json` |
| `6` | source | `387,078` | `74,529,118` | `4ce332c04eca0e8749e32e2ff1318deb2f4f520a219cc937e23feb76843c3e60` | `docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q6-source-proof-2026-06.envelope.json` |
| `6` | sidecar | `66,655` | `71,967,696` | `260b849e2aa7bd9e907b75c8988fad3fb3af2cd203d9dc9a52159deb3a5918cb` | `docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q6-sidecar-proof-2026-06.envelope.json` |
| `6` | fused | `390,437` | `74,559,250` | `7eb2c70fcae2bfe5d449498b3a62ddd637473a0a6b1176d4cbabd7ff0e1ad3d5` | `docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q6-fused-proof-2026-06.envelope.json` |
| `12` | source | `601,616` | `76,245,422` | `cd7a2ec0257fe717684ab5965121db9c02c7c9cf1e9ee659af50a8a7eef740da` | `docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q12-source-proof-2026-06.envelope.json` |
| `12` | sidecar | `126,131` | `72,443,504` | `741bc1ffbb527ddcc5c62f4d6a797f6a9ae0c622a637dbdd9c0069d8663b2113` | `docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q12-sidecar-proof-2026-06.envelope.json` |
| `12` | fused | `612,237` | `76,333,650` | `d8b6cc7d993011948f1e532e9c11db6b8ebb52f425287c8ddb92008673f41a2e` | `docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q12-fused-proof-2026-06.envelope.json` |

## Reproduction Commands

The checked paper measurement profile for this row remains q3:

```text
src/stwo_backend/mod.rs:
FriConfig::new(0, 1, 3, 1)
```

This is the fixed experimental Stwo PCS measurement profile for the
bounded-attention paper, not a production-security profile and not the older
Vanilla STARK `publication_v1_stark_options()` path in `src/proof.rs`.

For q6, patch only the FRI query count:

```text
src/stwo_backend/mod.rs:
FriConfig::new(0, 1, 3, 1) -> FriConfig::new(0, 1, 6, 1)
```

For q12, patch only the FRI query count:

```text
src/stwo_backend/mod.rs:
FriConfig::new(0, 1, 3, 1) -> FriConfig::new(0, 1, 12, 1)
```

For q6, run:

```bash
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_bounded_softmax_table_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q6-source-proof-2026-06.envelope.json
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_softmax_table_lookup_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q6-sidecar-proof-2026-06.envelope.json
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q6-fused-proof-2026-06.envelope.json
```

For q12, run the same three commands with `q12` in each output path after
applying the q12 patch:

```bash
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_bounded_softmax_table_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q12-source-proof-2026-06.envelope.json
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_softmax_table_lookup_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q12-sidecar-proof-2026-06.envelope.json
CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_proof -- prove docs/engineering/evidence/zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/high-query/zkai-attention-kv-d64-four-head-seq64-q12-fused-proof-2026-06.envelope.json
```

Then verify every envelope with the same binary and `verify <envelope.json>`.
The full command list is also written in
`docs/engineering/zkai-attention-kv-d64-high-query-sensitivity-2026-06.md`.

## Validation Commands

Use Python 3.10 or newer. On this workstation, the repo venv works:

```bash
PYTHON_BIN=.venv/bin/python scripts/run_proof_pressure_release_gate.sh
```

Expanded core commands:

```bash
python3.10 scripts/zkai_paper_claim_pack_gate.py \
  --write-json docs/paper/evidence/stark-native-transformer-claim-pack-2026-05.json

python3.10 scripts/zkai_attention_kv_d64_high_query_sensitivity_gate.py \
  --write-json docs/engineering/evidence/zkai-attention-kv-d64-high-query-sensitivity-2026-06.json \
  --write-tsv docs/engineering/evidence/zkai-attention-kv-d64-high-query-sensitivity-2026-06.tsv \
  --write-md docs/engineering/zkai-attention-kv-d64-high-query-sensitivity-2026-06.md

python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d64_high_query_sensitivity_gate

python3.10 scripts/paper/generate_proof_pressure_boundaries_figures.py

git diff --check
```

## Non-Claims

- Not production-security parameter evidence.
- Not a proving-time, verifier-time, memory-use, or hardware-efficiency claim.
- Not exact real-valued Softmax.
- Not full transformer inference.
- Not a comparison with NANOZK, Jolt, EZKL, RISC Zero, SP1, zkLLM, or other
  zkML systems.
- Not a Stwo optimization, Stwo-AI fork, new PCS, or new FRI scheme.
- Not evidence that higher query count always improves the fused-to-split ratio.
- Not a d128 high-query row. The attempted cheap `d128_two_head_seq32` q6 probe
  crossed the existing bounded verifier cap and should be treated as separate
  future work, not as part of this launch package.
