# Larger Native Boundary Candidate Selector

Date: 2026-05-18

Issue: [#671](https://github.com/omarespejel/provable-transformer-vm/issues/671)

## Decision

`GO_SELECT_TWO_HEAD_SEQ32_LARGER_NATIVE_BOUNDARY_IMPLEMENTATION_CANDIDATE`

Result:

`TWO_HEAD_SEQ32_HAS_1184_LOOKUP_CLAIMS_22916_TYPED_BYTES_AND_19_354730_TYPED_BYTES_PER_LOOKUP`

This is a selector gate, not a new proof object. It chooses the next larger
source-bound native boundary candidate using existing verified attention
artifacts plus fresh local typed accounting.

## Checked Candidates

| candidate | status | attention typed bytes | lookup claims | typed bytes / lookup | matched two-proof frontier |
| --- | --- | ---: | ---: | ---: | ---: |
| d8 fused attention | `BASELINE_CURRENT_LOCAL_FRONTIER` | `18,124` | `52` | `348.538462` | `40,700` |
| d16 fused attention | `PARK_TYPED_PER_LOOKUP_WORSE_THAN_D8` | `28,876` | `52` | `555.307692` | `51,452` |
| d16 two-head fused attention | `PARK_RATIO_WORSE_THAN_SEQ32` | `29,908` | `104` | `287.576923` | `52,484` |
| d16 two-head longseq fused attention | `PARK_HEAVIER_THAN_SEQ32` | `31,508` | `336` | `93.773810` | `54,084` |
| two-head seq32 fused attention | `ATTACK_NEXT_LARGER_NATIVE_BOUNDARY` | `22,916` | `1,184` | `19.354730` | `45,492` |

The selected route is `two_head_seq32_fused_attention`. Compared with the d8
baseline, lookup claims grow from `52` to `1,184` (`22.769231x`), while local
typed attention proof bytes grow only from `18,124` to `22,916` (`1.264401x`).
The selected route is therefore `18.007922x` better on typed bytes per lookup
claim than the d8 fused-attention baseline.

The incremental cost is also small: `4,792` more typed attention bytes buy
`1,132` more lookup claims, or `4.233216` typed bytes per extra lookup claim.

## Why This Matters

The previous budget showed that the strict d8 attention plus d128 MLP single
object needs to recover `1,233` typed bytes to beat the local `40,700` typed-byte
two-proof frontier. This selector says the next implementation should not just
repeat the d8 surface. The two-head seq32 attention proof has much more work
for only a modest typed-byte increase, and its source-plus-sidecar JSON fusion
ratio is the strongest in this candidate set: `0.676723x`, saving `31,685`
JSON proof bytes versus its matched source-plus-sidecar attention comparator.

That makes two-head seq32 the better larger-boundary attack surface for testing
whether shared opening, FRI, and trace-decommitment plumbing can amortize across
attention and MLP in one native proof object.

## Next Experiment

Implement a source-bound native proof object for:

- two-head seq32 fused attention with bounded Softmax-table LogUp; and
- the attention-derived d128 RMSNorm-MLP fused surface.

The matched local two-proof frontier for that implementation is now pinned at
`45,492` typed bytes (`22,916` attention + `22,576` MLP). The implementation
should compare against that matched frontier first, not against the older d8
`40,700` typed-byte frontier and not against NANOZK.

## Non-Claims

- Not a new native attention-plus-MLP proof object.
- Not a NANOZK proof-size win.
- Not a matched external zkML benchmark.
- Not a full transformer block proof.
- Not exact real-valued Softmax.
- Not timing evidence.
- Not production-ready zkML.

## Evidence

- Accounting JSON:
  `docs/engineering/evidence/zkai-larger-native-boundary-candidate-accounting-2026-05.json`
- Gate JSON:
  `docs/engineering/evidence/zkai-larger-native-boundary-candidate-selector-2026-05.json`
- Gate TSV:
  `docs/engineering/evidence/zkai-larger-native-boundary-candidate-selector-2026-05.tsv`
- Gate:
  `scripts/zkai_larger_native_boundary_candidate_selector_gate.py`
- Tests:
  `scripts/tests/test_zkai_larger_native_boundary_candidate_selector_gate.py`

The gate rejects `17 / 17` mutations covering selected-candidate drift, selected
metric drift, d8 baseline drift, bytes-per-lookup overclaim, NANOZK overclaim,
full-block overclaim, source digest/id/path/envelope digest drift, accounting row
removal, non-claim removal/addition, validation-command drift, interpretation
overclaim, and payload commitment drift.

## Reproduce

```bash
cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-fused-softmax-table-proof-2026-05.envelope.json docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-fused-softmax-table-proof-2026-05.envelope.json docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-two-head-fused-softmax-table-proof-2026-05.envelope.json docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-two-head-longseq-fused-softmax-table-proof-2026-05.envelope.json docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.envelope.json > docs/engineering/evidence/zkai-larger-native-boundary-candidate-accounting-2026-05.json
python3 scripts/zkai_larger_native_boundary_candidate_selector_gate.py --write-json docs/engineering/evidence/zkai-larger-native-boundary-candidate-selector-2026-05.json --write-tsv docs/engineering/evidence/zkai-larger-native-boundary-candidate-selector-2026-05.tsv
python3 -m py_compile scripts/zkai_larger_native_boundary_candidate_selector_gate.py scripts/tests/test_zkai_larger_native_boundary_candidate_selector_gate.py
python3 -m unittest scripts.tests.test_zkai_larger_native_boundary_candidate_selector_gate
python3 scripts/research_issue_lint.py --repo-root .
python3 scripts/paper/paper_preflight.py --repo-root .
git diff --check
just gate-fast
just gate
```
