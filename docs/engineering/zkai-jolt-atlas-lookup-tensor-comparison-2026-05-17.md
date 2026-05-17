# zkAI Jolt Atlas Lookup-Tensor Comparison - 2026-05-17

Issue: `#651`

Status: `GO_JOLT_ATLAS_SOURCE_BACKED_COMPARISON_NO_GO_LOCAL_REPRODUCTION`.

This gate records the first source-backed Jolt/Atlas comparison lane. It is
strictly an object-class and reproduction-status gate: it says that Jolt Atlas
is a serious lookup/tensor zkML competitor, and it says exactly why this repo
cannot yet claim a local comparison against it.

## Result

The result is useful context, not a benchmark win.

Important numbers and statuses:

- comparison rows: `8`
- local checked rows: `3`
- external source/context rows: `5`
- local Stwo attention/lookup grid typed savings: `51,288` bytes
- local Stwo attention-plus-MLP two-proof frontier: `40,700` typed bytes
- local GKR tiny `Gemm` fixture: `11,645` proof bytes
- GKR tiny `Gemm` ratio versus Stwo two-proof frontier: `0.286118x`
- Jolt Atlas README-reported GPT-2 proof time: `14.889` seconds
- Jolt Atlas README-reported nanoGPT proof time: `2.288` seconds
- Atlas local reproduction: `false`
- Atlas proof-size row available in this gate: `false`
- matched Atlas workload: `false`
- mutation gate: `8 / 8` rejected

Human meaning: Atlas is relevant because it attacks ML inference at the
ONNX/tensor-operation level with lookup/sumcheck machinery. That is exactly
the right competitor class for lookup-heavy transformer proving. But the
available source-backed rows are not matched to our local proof objects: their
README rows are timing rows on a MacBook M3, while our rows are local
proof-size/accounting rows. No proof-size or timing comparison is promoted.

## Comparison Rows

| row | system | status | primary value | boundary |
| --- | --- | --- | ---: | --- |
| local Stwo attention/lookup grid | Stwo/STARK | local checked | `51,288` typed bytes saved | mechanism evidence, not ONNX |
| local Stwo minimal block frontier | Stwo/STARK | local checked | `40,700` typed bytes | two-proof frontier, not Atlas |
| local GKR tiny Gemm | JSTprove/Remainder-GKR | local checked | `11,645` proof bytes | tiny sidecar only |
| Jolt core zkVM context | Jolt | source context | `cb1e464e...` repo head | zkVM context, not tensor row |
| Jolt Atlas paper architecture | Jolt Atlas | paper-reported context | ONNX lookup/tensor zkML | architecture context only |
| Jolt Atlas GPT-2 README row | Jolt Atlas | repo-reported | `14.889s` proof time | timing context only |
| Jolt Atlas nanoGPT README row | Jolt Atlas | repo-reported | `2.288s` proof time | timing context only |
| Jolt Atlas self-attention example | Jolt Atlas | command available | `cargo run ... --example transformer` | next reproduction target |

## Source Status

Primary source inventory:

- Jolt Atlas paper: `https://arxiv.org/abs/2602.17452`
- Jolt Atlas repository: `https://github.com/ICME-Lab/jolt-atlas`
- Jolt Atlas README: `https://raw.githubusercontent.com/ICME-Lab/jolt-atlas/main/README.md`
- Jolt core repository: `https://github.com/a16z/jolt`
- Jolt lookup/memory-checking docs:
  `https://a16z-jolt.mintlify.app/architecture/theory/memory-checking`

Pinned external heads from `git ls-remote` on 2026-05-17:

- `ICME-Lab/jolt-atlas`: `53b7c873a6662cdc79d9818dececf337bb27d7d0`
- `a16z/jolt`: `cb1e464e5d0978758900fc279a08472bfb8b518d`

A bounded local clone probe was attempted for `ICME-Lab/jolt-atlas`, but it did
not complete before the probe was interrupted during `git index-pack`. No
Atlas proof was run. The status therefore remains
`repo_available_not_locally_reproduced`.

## Claim Boundary

Allowed:

- Jolt Atlas is a serious lookup/tensor zkML competitor lane.
- The next reproduction target is the Jolt Atlas `transformer.rs`
  self-attention example.
- Source-reported Atlas timings can be listed as context when clearly marked
  as repo-reported and not local.
- Stwo, GKR, Jolt, and Atlas rows must be separated by object class, workload,
  source status, proof-size policy, and timing policy.

Forbidden:

- Stwo beats Atlas.
- Atlas was locally reproduced.
- The local `40,700` typed-byte Stwo frontier is comparable to Atlas GPT-2 or
  nanoGPT README timing rows.
- The local `11,645` byte GKR tiny `Gemm` proof is comparable to Atlas
  transformer inference.
- A compact Tablero statement-binding object is a tensor/model proof.
- A proof-size comparison exists before Atlas proof bytes are reproduced or
  source-reported for a matched workload.

## Why This Matters

NANOZK pressures us on block-level proof size. Jolt Atlas pressures us from a
different direction: proof-system design around lookup/tensor operations rather
than a STARK-native trace-fusion object. That is useful. It suggests the paper
should not be framed as "STARKs beat every zkML system." The stronger frame is:

> Choose proof boundaries according to proof pressure. Use STARK-native fusion
> where commitment/opening plumbing can be shared, compare lookup/sumcheck
> tensor systems honestly where nonlinear/tensor pressure dominates, and bind
> all objects through typed statements.

## Recommendation

Keep Atlas as an active comparison lane. The next bounded attack should try to
reproduce the `jolt-atlas-core --example transformer` self-attention proof and
capture:

1. proof bytes, if exposed by the implementation;
2. prove and verify time on local hardware;
3. setup/key material included or excluded;
4. model/operator shape;
5. statement boundary fields needed to compare it with the local minimal
   transformer-block contract.

If that run is too heavy or does not expose proof bytes, the follow-up should
record the blocker and build a smaller mirrored ONNX/tensor surface locally
instead of pretending a benchmark exists.

## Non-Claims

- Not a local reproduction of Jolt Atlas.
- Not a proof-size win over Jolt Atlas.
- Not a timing win over Jolt Atlas.
- Not a matched ONNX tensor workload.
- Not a matched self-attention block benchmark.
- Not a Jolt zkVM benchmark.
- Not a NANOZK proof-size comparison.
- Not evidence that Stwo replaces lookup/sumcheck tensor systems.
- Not a claim that compact Tablero statement binding is a model proof.

## Evidence

- JSON:
  `docs/engineering/evidence/zkai-jolt-atlas-lookup-tensor-comparison-2026-05.json`
- TSV:
  `docs/engineering/evidence/zkai-jolt-atlas-lookup-tensor-comparison-2026-05.tsv`
- Gate:
  `scripts/zkai_jolt_atlas_lookup_tensor_comparison_gate.py`
- Tests:
  `scripts/tests/test_zkai_jolt_atlas_lookup_tensor_comparison_gate.py`

Source artifacts:

- `docs/engineering/evidence/zkai-minimal-transformer-block-benchmark-2026-05.json`
- `docs/engineering/evidence/zkai-gkr-dense-sidecar-baseline-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-stwo-controlled-component-grid-2026-05.json`

## Validation

```bash
python3 scripts/zkai_jolt_atlas_lookup_tensor_comparison_gate.py --write-json docs/engineering/evidence/zkai-jolt-atlas-lookup-tensor-comparison-2026-05.json --write-tsv docs/engineering/evidence/zkai-jolt-atlas-lookup-tensor-comparison-2026-05.tsv
python3 -m py_compile scripts/zkai_jolt_atlas_lookup_tensor_comparison_gate.py scripts/tests/test_zkai_jolt_atlas_lookup_tensor_comparison_gate.py
python3 -m unittest scripts.tests.test_zkai_jolt_atlas_lookup_tensor_comparison_gate
python3 scripts/research_issue_lint.py --repo-root .
git diff --check
just gate-fast
just gate
```
