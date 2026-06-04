# Proof-Pressure Paper Release Audit Packet - 2026-06-04

This packet exists to remove provenance ambiguity before public release.

## Correct Repository

The proof-pressure paper package lives in:

```text
omarespejel/provable-transformer-vm
```

Do not use same-number PRs from `starknet-innovation/mezcal` or any other
repository as paper provenance. That repository has an unrelated PR namespace.

## Current Paper Sync

The last merged paper-sync PR before this hardening packet was:

```text
PR: #763
Title: Sync proof-pressure claim pack with current evidence
Merge commit: 9d16c0bad1b9c2584f92b33b9958b66340ad1eb3
```

This hardening packet adds reviewer-facing provenance and wording fixes on top
of that merged state. Because this repository uses rebase merge for PRs, the
final public release commit must be read from GitHub after this hardening PR
lands. Do not launch from a stale PR number or from a same-number PR in another
repository.

## Release Manifest

Machine-readable manifest:

```text
docs/paper/evidence/stark-native-transformer-paper-release-manifest-2026-06.json
```

Pinned launch artifacts in that manifest:

```text
docs/paper/proof-pressure-boundaries-for-stark-native-transformers-2026.md
sha256: fbe43618f5078bde340547e0025e981c74159778425c1443288f5392bde97b68

docs/paper/stark-native-transformer-proof-claim-pack-2026-05.md
sha256: ffcba356c93b84a831009141d7523bb05d610db01bae93f942296ce6ed00e64d

docs/paper/evidence/stark-native-transformer-claim-pack-2026-05.json
sha256: 9a0d8c09ce0b37d6d14330ac9f1a214a12c2b70d9eb5b40f55f83a9fc04d3166
```

## Required Launch Commands

Run these on the final public release commit:

```bash
python3.10 scripts/zkai_paper_claim_pack_gate.py \
  --write-json docs/paper/evidence/stark-native-transformer-claim-pack-2026-05.json

python3.10 -m py_compile \
  scripts/zkai_paper_claim_pack_gate.py \
  scripts/tests/test_zkai_paper_claim_pack_gate.py

python3.10 -m unittest scripts.tests.test_zkai_paper_claim_pack_gate

python3.10 scripts/paper/paper_preflight.py --repo-root .

scripts/run_paper_preflight_suite.sh

git diff --check

git diff --exit-code \
  docs/paper/evidence/stark-native-transformer-claim-pack-2026-05.json \
  docs/paper/stark-native-transformer-proof-claim-pack-2026-05.md \
  docs/paper/proof-pressure-boundaries-for-stark-native-transformers-2026.md
```

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
recommendations.

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
