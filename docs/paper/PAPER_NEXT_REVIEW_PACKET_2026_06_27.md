# Proof-Pressure Paper Next Review Packet - 2026-06-27

This is the shortest reviewer entrypoint after the camera-ready hardening pass.

## Review Target

Repository:

```text
omarespejel/provable-transformer-vm
```

Current reviewed release-hygiene base commit:

```text
1a7f85c225a52a7cadf660146136a5c522016769
```

If this handoff packet is moved by a later release-hygiene PR, the public
release commit is the latest merged `main` commit after that PR lands. Review
that exact commit and re-run the release gate there. PR #772 is the last PR that
materially changed the paper's evidence argument; PR #775 completed the fixed
Stwo measurement-profile naming cleanup; PR #776 refreshed the release
provenance packet and gate interpreter contract.

Primary paper:

```text
docs/paper/proof-pressure-boundaries-for-stark-native-transformers-2026.md
```

Companion appendix:

```text
docs/paper/appendix-zkml-statement-validity-2026.md
```

## One-Sentence Claim

For scoped bounded-attention surfaces over an unmodified Stwo backend, fused
STARK-native proof boundaries can keep serialized proof payloads below the
matched source-plus-sidecar split frontier by sharing opening-bucket material
around lookup-heavy work.

## What Changed Since The Earlier Review

1. The d64 higher-query result is now integrated into the paper.
2. The mechanism evidence is tied directly to the d64 four-head seq64 headline
   row.
3. The paper explicitly says the `q=3` Stwo PCS setting is a fixed experimental
   measurement profile, not production security.
4. The fixed Stwo measurement PCS profile is named
   `fixed_stwo_measurement_pcs_config()` in new code. The older
   `publication_v1_pcs_config()` helper remains only as a compatibility alias
   and is distinguished from the Vanilla STARK `publication_v1_stark_options()`
   path with its `96`-bit conjectured floor.
5. The claim pack, reproduction note, release packets, README, and release
   manifest all carry the same profile boundary.
6. PR #775 preserved legacy proof-verifier hardening strings where checked
   evidence expects exact text, so the naming cleanup does not rewrite prior
   evidence claims.

## Numbers To Check First

Main sequence-axis claim:

| checked axis | work growth | fused proof-byte growth |
|---|---:|---:|
| `seq32 -> seq64` | lookup claims about `3.73x`; trace rows `4.0x` | about `1.06x` to `1.08x` |

Mechanism claim:

| category | bytes saved | share |
|---|---:|---:|
| FRI proof material | `129,316` | about `57.7%` |
| Decommitment material | `79,839` | about `35.6%` |
| Other proof material | `14,803` | about `6.6%` |
| Total | `223,958` | about `100%` (shares rounded) |

The combined opening bucket is:

```text
(129,316 + 79,839) / 223,958 = about 93.4%
```

d64 four-head seq64 high-query sensitivity:

| FRI queries | split proof bytes | fused proof bytes | saving | fused ratio |
|---:|---:|---:|---:|---:|
| `3` | `315,785` | `276,503` | `39,282` | about `0.876x` |
| `6` | `453,733` | `390,437` | `63,296` | about `0.860x` |
| `12` | `727,747` | `612,237` | `115,510` | about `0.841x` |

## Reproduction Gate

Run from the repository root:

```bash
scripts/run_proof_pressure_release_gate.sh
```

The gate defaults to `python3.10`. To use the repository venv or another Python
`3.10+` environment with the paper dependencies installed, set `PYTHON_BIN`
explicitly:

```bash
PYTHON_BIN=.venv/bin/python scripts/run_proof_pressure_release_gate.sh
```

Expected result:

```text
Regeneration produced no diff against the committed paper artifacts.
```

The gate regenerates the claim pack, high-query summaries, paper figures, and
preflight outputs, then fails if the committed paper package drifts.

## Files To Read In Order

1. `docs/paper/proof-pressure-boundaries-for-stark-native-transformers-2026.md`
2. `docs/paper/appendix-zkml-statement-validity-2026.md`
3. `docs/paper/stark-native-transformer-proof-claim-pack-2026-05.md`
4. `docs/paper/REPRODUCE.md`
5. `docs/paper/PAPER_D64_HIGH_QUERY_AUDIT_PACKET_2026_06_27.md`
6. `docs/paper/PAPER_RELEASE_AUDIT_PACKET_2026_06_04.md`
7. `docs/paper/evidence/stark-native-transformer-paper-release-manifest-2026-06.json`

## Review Questions

Please answer these before launch:

1. Is the main claim narrow enough for the evidence?
2. Does the paper make the fixed experimental Stwo `q=3` profile clear enough?
3. Is the q6/q12 result framed correctly as engineering sensitivity, not
   production security?
4. Does the mechanism wording match the section-delta evidence?
5. Does the statement-validity appendix avoid implying a new proving protocol?
6. Are all comparisons to NANOZK, Jolt Atlas, EZKL, RISC Zero, SP1, zkLLM, and
   related systems clearly adjacent rather than competitive?
7. Is the paper ready for venue-formatting and external circulation, or does it
   need one more evidence artifact?

## Non-Claims To Preserve

- Not full transformer inference.
- Not exact real-valued Softmax.
- Not production-security parameters.
- Not a proving-speed, verifier-time, memory-use, or hardware-efficiency claim.
- Not a system-level comparison against existing zkML systems.
- Not a NANOZK, Jolt Atlas, EZKL, RISC Zero, SP1, or zkLLM benchmark win.
- Not a Stwo optimization, Stwo-AI fork, new PCS, or new FRI scheme.
- Not evidence that higher query count always improves the fused-to-split ratio.
- Not a d128 high-query result.

## Known Follow-Ups

- d128 high-query sensitivity is future work. A cheap probe crossed the current
  bounded verifier cap, so it should not be folded into this launch package.
- Full transformer-block proving and external apples-to-apples baselines remain
  separate research tracks.

## Reviewer Output Requested

Return one of:

```text
LAUNCHABLE
LAUNCHABLE_AFTER_TEXT_EDITS
NEEDS_ONE_MORE_ARTIFACT
NOT_LAUNCHABLE
```

If the answer is not `LAUNCHABLE`, list the blocking edits or artifacts in
priority order.
