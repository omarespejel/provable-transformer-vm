# Stwo-AI Boundary Pressure Inventory - 2026-06-04

Issue: https://github.com/omarespejel/provable-transformer-vm/issues/757

## Decision

`GO_READ_ONLY_STWO_AI_PRESSURE_INVENTORY_NO_FORK_YET`

## Result

The first Stwo-AI step is not to build a custom prover. It is to inventory where
the checked transformer proof surfaces already spend and save proof bytes.

This gate consumes existing checked evidence:

- the attention plus LogUp section-delta gate;
- the fused Softmax-table route matrix;
- the Stwo query-policy hook evidence;
- the query-preview split prototype evidence.

It does not run a prover and does not add a new proof-size frontier. It turns the
existing measurements into an optimization queue.

## Main Signal

Across the eleven checked attention plus LogUp section-delta profiles:

| metric | value |
|---|---:|
| profiles checked | `11` |
| total fused saving | `223,958` bytes |
| opening saving | `209,155` bytes |
| opening share | `93.3903%` |
| largest profile | `d64_four_head_seq64` |

For the d64 four-head seq64 decision row:

| metric | value |
|---|---:|
| total fused saving | `39,282` bytes |
| opening saving | `37,827` bytes |
| opening share | `96.2960%` |
| FRI saving | `27,012` bytes |
| decommitment saving | `10,815` bytes |
| query saving | `850` bytes |
| source opening surface | `45,896` bytes |
| sidecar opening surface | `40,721` bytes |
| fused opening surface | `48,790` bytes |

Human read: the fused proof does not make the arithmetic disappear. It mostly
avoids paying a second opening surface. In the d64 decision row, the fused
opening surface is only `2,894` bytes larger than the source opening surface,
while the split route also pays the sidecar opening surface of `40,721` bytes.
That accounts for the `37,827` opening-byte saving.

This is the Stwo-AI optimization target.

## Starting Agenda

The generated action queue is:

1. **Proof-section profiler hardening**
   Start now. Keep improving section-level accounting so every route tells us
   which proof bucket moved. This is still serialized-section evidence, not
   backend-internal semantic byte attribution.

2. **Route-level layout policy**
   Start now. Test deterministic route and layout policies that make attention
   arithmetic and lookup-heavy table work share opening and decommitment
   structure without weakening verifier binding.

3. **Local Stwo wrapper or adapter**
   Follow after route policy. A wrapper can enforce deterministic route policy,
   statement metadata, and profiling without maintaining an independent prover.

4. **Upstream Stwo patch or small fork**
   Follow only if a measured API wall is confirmed. Prior query evidence says
   Stwo 2.2 couples query draw and decommitment. Query preview is API-feasible,
   but it is not a sound post-query policy by itself.

5. **Independent Stwo-AI fork**
   No-go now. A fork is justified only after adapter and route-level work hits a
   measured internal wall.

## Unsafe Shortcuts

The inventory rejects the easy but wrong interpretations:

- do not delete FRI proof or decommitment witness material inside a valid proof;
- do not choose route labels after seeing final proof bytes;
- do not choose route labels after Fiat-Shamir queries without a
  verifier-visible retry budget;
- do not override canonical Fiat-Shamir queries externally;
- do not claim backend-internal source-vs-lookup byte attribution from
  serialized proof sections.

## Evidence

Generated evidence:

- `docs/engineering/evidence/zkai-stwo-ai-boundary-pressure-inventory-2026-06.json`
- `docs/engineering/evidence/zkai-stwo-ai-boundary-pressure-inventory-2026-06.tsv`

Source artifacts pinned by digest in the generated JSON:

- `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-section-delta-2026-05.json`
- `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`
- `docs/engineering/evidence/zkai-bounded-stwo-query-policy-hook-2026-05.json`
- `docs/engineering/evidence/zkai-stwo-query-preview-split-prototype-2026-05.json`

Mutation guards:

- `10 / 10` rejected.

Unit tests:

- `8`.

## Reproduction

```bash
python3.10 scripts/zkai_stwo_ai_boundary_pressure_inventory_gate.py --write-json docs/engineering/evidence/zkai-stwo-ai-boundary-pressure-inventory-2026-06.json --write-tsv docs/engineering/evidence/zkai-stwo-ai-boundary-pressure-inventory-2026-06.tsv
python3.10 -m py_compile scripts/zkai_stwo_ai_boundary_pressure_inventory_gate.py scripts/tests/test_zkai_stwo_ai_boundary_pressure_inventory_gate.py
python3.10 -m unittest scripts.tests.test_zkai_stwo_ai_boundary_pressure_inventory_gate
git diff --check
```

## Non-Claims

- Not a Stwo fork.
- Not a custom prover.
- Not a new proof-size frontier.
- Not a proving-speed claim.
- Not backend-internal semantic byte attribution.
- Not permission to delete FRI or decommitment witness material.
- Not a post-query label-selection policy.
- Not an external query override.
- Not an external benchmark against NANOZK, Jolt Atlas, EZKL, RISC Zero, SP1,
  or DeepProve.
- Not a full transformer or full LLM proof claim.

## Next Step

Open the next PR against issue #757 as a route-level layout policy experiment.
The promotion rule should be strict:

- deterministic policy fixed before proof generation;
- no post-query or post-proof-byte selection;
- same verifier binding and mutation gates;
- section-delta evidence showing which opening or decommitment component moved;
- fork only if route and adapter policy cannot reach the target.
