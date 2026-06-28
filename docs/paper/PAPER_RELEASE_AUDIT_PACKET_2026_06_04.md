# Proof-Pressure Paper Release Audit Packet - 2026-06-04

This packet exists to remove provenance ambiguity before public release.

## Correct Repository

The proof-pressure paper package lives in:

```text
omarespejel/provable-transformer-vm
```

Do not use same-number PRs from `starknet-innovation/mezcal` or any other
repository as paper provenance. That repository has an unrelated PR namespace.

## Current Release Hardening

The latest merged release-hardening PR before this packet refresh was:

```text
PR: #776
Title: Refresh proof-pressure release provenance
Merge commit: 1a7f85c225a52a7cadf660146136a5c522016769
```

PR #772 is the last PR that materially changed the paper's evidence argument.
PR #775 completed the fixed Stwo measurement-profile naming cleanup and
preserved legacy proof-verifier hardening strings where checked evidence expects
exact text. PR #776 refreshed the release provenance packet and made the release
gate interpreter selection explicit. Because this repository uses rebase merge
for PRs, the final public release commit must be read from GitHub after the last
launch-hygiene PR lands. Do not launch from a stale PR number or from a
same-number PR in another repository.

## Release Manifest

Machine-readable manifest:

```text
docs/paper/evidence/stark-native-transformer-paper-release-manifest-2026-06.json
```

Pinned launch artifacts in that manifest:

```text
docs/paper/proof-pressure-boundaries-for-stark-native-transformers-2026.md
sha256: 2ca42a0cac960ab4a67b7e9320a7eb97d026a477f663e83f37c8d3c1b984329a

docs/paper/stark-native-transformer-proof-claim-pack-2026-05.md
sha256: 7cf52471c1c5e53afbea6f478ecd5f8ad219a96cc97f7937d82d25b5e1a85067

docs/paper/evidence/stark-native-transformer-claim-pack-2026-05.json
sha256: 54feffcf81c511691e549dd57f29ec7f5d522034c9b1788530cfbf2fbb47ff98
```

## Required Launch Commands

Run the canonical release gate on the final public release commit:

```bash
scripts/run_proof_pressure_release_gate.sh
```

If the default `python3.10` binary is unavailable, use any Python `3.10+`
interpreter via `PYTHON_BIN`, for example:

```bash
PYTHON_BIN=.venv/bin/python scripts/run_proof_pressure_release_gate.sh
```

The gate regenerates the claim pack, high-query evidence, figures, paper
preflight outputs, and the full no-drift set pinned in the release manifest. Do
not replace it with a shortened `git diff --exit-code` artifact list.

This is a paper-artifact no-drift gate. It checks regenerated paper summaries,
figures, and release packets against committed or digest-pinned evidence. It is
not the default heavy proof-regeneration path for every large proof envelope.
Large envelopes remain covered by their digest manifests and separate
regenerate/verify commands.

The launch statement should include:

```text
Regeneration produced no diff against the committed paper artifacts.
```

## Fixed Experimental Configuration

The paper-facing fused/split proof-byte rows use a fixed experimental Stwo
configuration:

| parameter | value |
|---|---:|
| proof-of-work bits | `10` |
| FRI log blowup | `1` |
| FRI blowup factor | `2` |
| FRI query count | `3` |
| FRI fold step | `1` |
| backend | unmodified Stwo backend surface |

These are experimental measurement settings, not production-security parameter
recommendations. The canonical helper
`fixed_stwo_measurement_pcs_config()` names this fixed Stwo measurement profile.
The older `publication_v1_pcs_config()` helper remains only as a compatibility
alias for older generated modules; both are separate from the older Vanilla
STARK `publication_v1_stark_options()` helper in `src/proof.rs`.

## Mechanism Accounting

The attention section-delta mechanism claim is:

| category | bytes saved | share |
|---|---:|---:|
| FRI proof material | `129,316` | `57.7412%` |
| Decommitment material | `79,839` | `35.6491%` |
| Other proof material | `14,803` | `6.6097%` |
| Total | `223,958` | `100.0000%` |

The `93.3903%` phrase refers to the combined opening bucket:

```text
(129,316 + 79,839) / 223,958 = 93.3903%
```

## Non-Claims

- Not full transformer inference.
- Not exact real-valued Softmax.
- Not a proving-speed, verifier-time, memory-use, or hardware-efficiency claim.
- Not a production-security parameter recommendation.
- Not a public benchmark.
- Not a system-level comparison against NANOZK, Jolt Atlas, DeepProve, zkLLM,
  EZKL, RISC Zero, SP1, or other zkML systems.
- Not a Stwo optimization, upstream Stwo patch, or Stwo-AI fork result.
