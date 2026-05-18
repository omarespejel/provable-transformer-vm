#!/usr/bin/env python3
"""Gate the larger native block-boundary amortization budget.

This is a budget gate, not a new proof object. It answers the narrow next
question after the pivot selector: how much of the checked MLP-side native
fusion saving has to transfer across a larger attention-to-MLP boundary before
the route beats the current local frontier, and where the NANOZK comparison
still remains blocked.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import pathlib
from collections.abc import Callable
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"

PIVOT_SELECTOR = EVIDENCE_DIR / "zkai-native-block-boundary-pivot-selector-2026-05.json"
NATIVE_SINGLE = EVIDENCE_DIR / "zkai-native-attention-mlp-single-proof-2026-05.json"
ATTENTION_MLP_FRONTIER = EVIDENCE_DIR / "zkai-d128-attention-mlp-boundary-frontier-2026-05.json"
MLP_FUSED = EVIDENCE_DIR / "zkai-d128-rmsnorm-mlp-fused-gate-2026-05.json"
POST_TAIL = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-post-tail-layout-2026-05.json"
GKR_PREFLIGHT = EVIDENCE_DIR / "zkai-gkr-d128-projection-scaling-preflight-2026-05.json"
COMPACT_PREPROCESSED = EVIDENCE_DIR / "zkai-d128-component-compact-preprocessed-reprove-gate-2026-05.json"
MINIMAL_BLOCK = EVIDENCE_DIR / "zkai-minimal-transformer-block-benchmark-2026-05.json"

JSON_OUT = EVIDENCE_DIR / "zkai-larger-native-block-boundary-amortization-budget-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-larger-native-block-boundary-amortization-budget-2026-05.tsv"

ISSUE = 669
SCHEMA = "zkai-larger-native-block-boundary-amortization-budget-v1"
DECISION = "GO_ATTACK_LARGER_NATIVE_BOUNDARY_LOCAL_FRONTIER_BUDGET"
RESULT = "LOCAL_FRONTIER_REQUIRES_1233_TYPED_BYTES_OR_3_8359_PERCENT_OF_MLP_FUSION_SAVING_NANOZK_REMAINS_BLOCKED"
CLAIM_BOUNDARY = (
    "BUDGETS_NEXT_LARGER_NATIVE_BLOCK_BOUNDARY_FROM_CHECKED_LOCAL_EVIDENCE;"
    "_NO_NEW_PROOF_OBJECT_NO_NANOZK_OR_FULL_BLOCK_CLAIM"
)
SELECTED_NEXT_ROUTE = "larger_native_block_boundary_amortization"

TWO_PROOF_FRONTIER_TYPED_BYTES = 40_700
STRICT_NATIVE_SINGLE_TYPED_BYTES = 41_932
COMPACT_SELECTOR_TYPED_BYTES = 40_812
POST_TAIL_TYPED_BYTES = 42_724
GKR_WIDTH_PRESERVING_TYPED_BYTES = 70_138
COMPACT_PREPROCESSED_TYPED_BYTES = 6_264
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900
MLP_FUSION_TYPED_SAVING_BYTES = 32_144
MLP_FUSION_TYPED_SAVING_RATIO = "0.564167"
FOUR_PERCENT_TRANSFER_BYTES = 1_286
FOUR_PERCENT_TRANSFER_MODELED_TYPED_BYTES = 40_646
FOUR_PERCENT_TRANSFER_MARGIN_VS_FRONTIER_BYTES = 54

STRICT_REDUCTION_TO_BEAT_FRONTIER_BYTES = 1_233
STRICT_SHARE_TO_BEAT_FRONTIER = "0.038359"
COMPACT_REDUCTION_TO_BEAT_FRONTIER_BYTES = 113
COMPACT_SHARE_TO_BEAT_FRONTIER = "0.003515"
POST_TAIL_REDUCTION_TO_BEAT_FRONTIER_BYTES = 2_025
POST_TAIL_SHARE_TO_BEAT_FRONTIER = "0.062998"
GKR_REDUCTION_TO_BEAT_FRONTIER_BYTES = 29_439
GKR_SHARE_TO_BEAT_FRONTIER = "0.915847"
STRICT_REDUCTION_TO_BEAT_NANOZK_BYTES = 35_033
STRICT_SHARE_TO_BEAT_NANOZK = "1.089877"
TWO_PROOF_REDUCTION_TO_BEAT_NANOZK_BYTES = 33_801
TWO_PROOF_SHARE_TO_BEAT_NANOZK = "1.051549"

ROW_COLUMNS = (
    "row_id",
    "status",
    "comparison_scope",
    "current_typed_bytes",
    "reference_typed_bytes",
    "delta_vs_reference_typed_bytes",
    "reduction_to_beat_reference_bytes",
    "share_of_mlp_fusion_saving_to_beat_reference",
    "proof_size_comparable_to_nanozk",
    "interpretation",
)

EXPECTED_ROW_IDS = (
    "strict_native_single_vs_two_proof_frontier",
    "compact_selector_vs_two_proof_frontier",
    "post_tail_worst_label_vs_two_proof_frontier",
    "gkr_width_preserving_vs_two_proof_frontier",
    "strict_native_single_vs_nanozk_context",
    "two_proof_frontier_vs_nanozk_context",
    "compact_preprocessed_vs_nanozk_context",
)

NON_CLAIMS = (
    "not a NANOZK proof-size win",
    "not a matched NANOZK benchmark",
    "not a full transformer block proof",
    "not a new native proof object",
    "not timing evidence",
    "not evidence that GKR replaces Stwo",
    "not production zkML",
)

VALIDATION_COMMANDS = (
    "python3 scripts/zkai_larger_native_block_boundary_amortization_budget_gate.py --write-json docs/engineering/evidence/zkai-larger-native-block-boundary-amortization-budget-2026-05.json --write-tsv docs/engineering/evidence/zkai-larger-native-block-boundary-amortization-budget-2026-05.tsv",
    "python3 -m py_compile scripts/zkai_larger_native_block_boundary_amortization_budget_gate.py scripts/tests/test_zkai_larger_native_block_boundary_amortization_budget_gate.py",
    "python3 -m unittest scripts.tests.test_zkai_larger_native_block_boundary_amortization_budget_gate",
    "python3 scripts/research_issue_lint.py --repo-root .",
    "python3 scripts/paper/paper_preflight.py --repo-root .",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

SOURCE_PATHS = (
    PIVOT_SELECTOR,
    NATIVE_SINGLE,
    ATTENTION_MLP_FRONTIER,
    MLP_FUSED,
    POST_TAIL,
    GKR_PREFLIGHT,
    COMPACT_PREPROCESSED,
    MINIMAL_BLOCK,
)
SOURCE_ARTIFACTS_KEY = "__source_artifacts"
SOURCE_ARTIFACT_KEYS = ("path", "schema", "decision", "result", "sha256", "bytes")

INTERPRETATION_HUMAN_READ = (
    "The larger native boundary is worth one implementation attack on local-frontier grounds: "
    "the strict single native object needs 1,233 typed bytes to beat the current 40,700 typed-byte "
    "two-proof frontier, which is only 3.8359% of the checked 32,144 typed-byte MLP fusion saving."
)
INTERPRETATION_NANOZK_GUARDRAIL = (
    "The same budget says not to frame this as NANOZK-comparable: the strict native single object "
    "would need 35,033 typed bytes to beat the paper-reported 6,900 byte context row, which is "
    "108.9877% of the observed MLP-side fusion saving and still not a matched workload or object class."
)
INTERPRETATION_NEXT_EXPERIMENT = (
    "Build the next source-bound native boundary only if it targets shared opening, FRI, and trace "
    "decommitment amortization; kill or narrow the route if it cannot recover at least 1,233 typed bytes "
    "without using compact public-row artifacts as full-block proof rows."
)


class AmortizationBudgetError(Exception):
    pass


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def commitment(data: Any) -> str:
    return "blake2b-256:" + hashlib.blake2b(canonical_json(data).encode("utf-8"), digest_size=32).hexdigest()


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AmortizationBudgetError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise AmortizationBudgetError(f"{label} must be a list")
    return value


def require_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise AmortizationBudgetError(f"{label} must be an integer")
    return value


def require_float(value: Any, label: str) -> float:
    if not isinstance(value, (float, int)) or isinstance(value, bool):
        raise AmortizationBudgetError(f"{label} must be a number")
    return float(value)


def require_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise AmortizationBudgetError(f"{label} must be a non-empty string")
    return value


def require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise AmortizationBudgetError(f"{label} must be a boolean")
    return value


def expect_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AmortizationBudgetError(f"{label} drift: expected {expected!r}, got {actual!r}")


def load_source_artifact(path: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise AmortizationBudgetError(f"unable to read source artifact: {path}") from error
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AmortizationBudgetError(f"invalid JSON source artifact: {path}") from error
    if not isinstance(data, dict):
        raise AmortizationBudgetError(f"{path} must contain a JSON object")
    descriptor = {
        "path": path.relative_to(ROOT).as_posix(),
        "schema": data.get("schema"),
        "decision": data.get("decision"),
        "result": data.get("result"),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }
    return data, descriptor


def load_sources() -> dict[str, Any]:
    source_items = (
        ("pivot", PIVOT_SELECTOR),
        ("native_single", NATIVE_SINGLE),
        ("frontier", ATTENTION_MLP_FRONTIER),
        ("mlp_fused", MLP_FUSED),
        ("post_tail", POST_TAIL),
        ("gkr", GKR_PREFLIGHT),
        ("compact_preprocessed", COMPACT_PREPROCESSED),
        ("minimal_block", MINIMAL_BLOCK),
    )
    sources: dict[str, Any] = {}
    source_artifacts: list[dict[str, Any]] = []
    for label, path in source_items:
        payload, descriptor = load_source_artifact(path)
        sources[label] = payload
        source_artifacts.append(descriptor)
    sources[SOURCE_ARTIFACTS_KEY] = source_artifacts
    expect_equal(sources["pivot"].get("schema"), "zkai-native-block-boundary-pivot-selector-v1", "pivot schema")
    expect_equal(sources["native_single"].get("schema"), "zkai-native-attention-mlp-single-proof-object-gate-v1", "native single schema")
    expect_equal(sources["frontier"].get("schema"), "zkai-d128-attention-mlp-boundary-frontier-gate-v1", "frontier schema")
    expect_equal(sources["mlp_fused"].get("schema"), "zkai-d128-rmsnorm-mlp-fused-gate-v1", "MLP fused schema")
    expect_equal(sources["post_tail"].get("schema"), "zkai-native-attention-mlp-rmsnorm-post-tail-layout-gate-v1", "post-tail schema")
    expect_equal(sources["gkr"].get("schema"), "zkai-gkr-d128-projection-scaling-preflight-v1", "GKR schema")
    expect_equal(sources["compact_preprocessed"].get("schema"), "zkai-d128-component-compact-preprocessed-reprove-gate-v1", "compact preprocessed schema")
    expect_equal(sources["minimal_block"].get("schema"), "zkai-minimal-transformer-block-benchmark-v1", "minimal block schema")
    return sources


def validate_source_numbers(sources: dict[str, Any]) -> None:
    pivot_summary = require_dict(sources["pivot"].get("summary"), "pivot summary")
    expect_equal(sources["pivot"].get("decision"), "ATTACK_NEXT_LARGER_NATIVE_BLOCK_BOUNDARY", "pivot decision")
    expect_equal(pivot_summary.get("selected_next_route"), "larger_native_block_boundary", "pivot selected route")
    expect_equal(require_int(pivot_summary.get("proof_size_comparable_rows"), "pivot comparable rows"), 0, "pivot comparable rows")
    expect_equal(require_int(pivot_summary.get("strict_native_adapter_typed_bytes"), "pivot strict typed"), STRICT_NATIVE_SINGLE_TYPED_BYTES, "pivot strict typed")
    expect_equal(require_int(pivot_summary.get("strict_native_adapter_gap_bytes"), "pivot strict gap"), STRICT_NATIVE_SINGLE_TYPED_BYTES - TWO_PROOF_FRONTIER_TYPED_BYTES, "pivot strict gap")
    expect_equal(require_int(pivot_summary.get("mlp_fusion_typed_saving_bytes"), "pivot MLP saving"), MLP_FUSION_TYPED_SAVING_BYTES, "pivot MLP saving")

    native_summary = require_dict(sources["native_single"].get("summary"), "native single summary")
    expect_equal(require_bool(native_summary.get("native_adapter_air_proven"), "native adapter proven"), True, "native adapter proven")
    expect_equal(require_int(native_summary.get("single_proof_typed_bytes"), "single typed"), STRICT_NATIVE_SINGLE_TYPED_BYTES, "single typed")
    expect_equal(require_int(native_summary.get("two_proof_frontier_typed_bytes"), "single frontier"), TWO_PROOF_FRONTIER_TYPED_BYTES, "single frontier")
    expect_equal(require_int(native_summary.get("typed_delta_vs_two_proof_bytes"), "single frontier delta"), STRICT_NATIVE_SINGLE_TYPED_BYTES - TWO_PROOF_FRONTIER_TYPED_BYTES, "single frontier delta")
    expect_equal(require_int(native_summary.get("typed_gap_to_nanozk_reported_bytes"), "single NANOZK gap"), STRICT_NATIVE_SINGLE_TYPED_BYTES - NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES, "single NANOZK gap")

    frontier_summary = require_dict(sources["frontier"].get("summary"), "frontier summary")
    expect_equal(require_int(frontier_summary.get("two_proof_frontier_typed_bytes"), "two-proof frontier"), TWO_PROOF_FRONTIER_TYPED_BYTES, "two-proof frontier")
    expect_equal(require_int(frontier_summary.get("nanozk_reported_d128_block_proof_bytes"), "frontier NANOZK row"), NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES, "frontier NANOZK row")
    expect_equal(require_int(frontier_summary.get("typed_gap_to_nanozk_reported_bytes"), "frontier NANOZK gap"), TWO_PROOF_FRONTIER_TYPED_BYTES - NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES, "frontier NANOZK gap")
    expect_equal(require_int(frontier_summary.get("typed_saving_vs_six_separate_mlp_plus_attention_fused_bytes"), "frontier saving"), 36_768, "frontier saving")

    mlp_aggregate = require_dict(sources["mlp_fused"].get("aggregate"), "MLP aggregate")
    expect_equal(require_int(mlp_aggregate.get("typed_saving_vs_separate_bytes"), "MLP saving"), MLP_FUSION_TYPED_SAVING_BYTES, "MLP saving")
    expect_equal(
        f"{require_float(mlp_aggregate.get('typed_saving_ratio_vs_separate'), 'MLP saving ratio'):.6f}",
        MLP_FUSION_TYPED_SAVING_RATIO,
        "MLP saving ratio",
    )
    expect_equal(require_int(mlp_aggregate.get("fused_total_row_count"), "MLP fused rows"), 197_504, "MLP fused rows")

    expect_equal(sources["post_tail"].get("decision"), "NO_GO_POST_TAIL_LAYOUT_LABEL_STABILITY", "post-tail decision")
    expect_equal(require_int(sources["post_tail"].get("post_tail_canonical_typed_bytes"), "post-tail typed"), POST_TAIL_TYPED_BYTES, "post-tail typed")
    expect_equal(require_int(sources["post_tail"].get("post_tail_delta_vs_two_proof_frontier_typed_bytes"), "post-tail gap"), POST_TAIL_TYPED_BYTES - TWO_PROOF_FRONTIER_TYPED_BYTES, "post-tail gap")
    expect_equal(require_bool(sources["post_tail"].get("post_tail_matches_adjacent_bad_label_record_stream"), "post-tail bad-label match"), True, "post-tail bad-label match")

    gkr_summary = require_dict(sources["gkr"].get("summary"), "GKR summary")
    expect_equal(sources["gkr"].get("decision"), "NO_GO_NOW_D128_PROJECTION_SCALING", "GKR decision")
    expect_equal(require_int(gkr_summary.get("smallest_width_preserving_gkr_proof_bytes"), "GKR width-preserving bytes"), GKR_WIDTH_PRESERVING_TYPED_BYTES, "GKR width-preserving bytes")
    expect_equal(require_int(gkr_summary.get("proof_size_comparable_rows"), "GKR comparable rows"), 0, "GKR comparable rows")

    compact_aggregate = require_dict(sources["compact_preprocessed"].get("aggregate"), "compact preprocessed aggregate")
    expect_equal(require_int(compact_aggregate.get("compact_local_typed_bytes"), "compact preprocessed typed"), COMPACT_PREPROCESSED_TYPED_BYTES, "compact preprocessed typed")
    expect_equal(compact_aggregate.get("comparison_status"), "below_nanozk_reported_row_under_local_typed_accounting_not_matched_benchmark", "compact preprocessed comparison status")

    minimal_summary = require_dict(sources["minimal_block"].get("summary"), "minimal block summary")
    expect_equal(require_bool(minimal_summary.get("missing_native_block_proof_object"), "missing native block object"), True, "missing native block object")
    expect_equal(require_int(minimal_summary.get("two_proof_frontier_typed_bytes"), "minimal frontier"), TWO_PROOF_FRONTIER_TYPED_BYTES, "minimal frontier")


def reduction_to_beat(current_typed_bytes: int, reference_typed_bytes: int) -> int:
    return max(0, current_typed_bytes - reference_typed_bytes + 1)


def share_to_beat(current_typed_bytes: int, reference_typed_bytes: int) -> str:
    return f"{reduction_to_beat(current_typed_bytes, reference_typed_bytes) / MLP_FUSION_TYPED_SAVING_BYTES:.6f}"


def budget_row(
    row_id: str,
    status: str,
    comparison_scope: str,
    current_typed_bytes: int,
    reference_typed_bytes: int,
    proof_size_comparable_to_nanozk: bool,
    interpretation: str,
) -> dict[str, Any]:
    return {
        "row_id": row_id,
        "status": status,
        "comparison_scope": comparison_scope,
        "current_typed_bytes": current_typed_bytes,
        "reference_typed_bytes": reference_typed_bytes,
        "delta_vs_reference_typed_bytes": current_typed_bytes - reference_typed_bytes,
        "reduction_to_beat_reference_bytes": reduction_to_beat(current_typed_bytes, reference_typed_bytes),
        "share_of_mlp_fusion_saving_to_beat_reference": share_to_beat(current_typed_bytes, reference_typed_bytes),
        "proof_size_comparable_to_nanozk": proof_size_comparable_to_nanozk,
        "interpretation": interpretation,
    }


def base_payload(sources: dict[str, Any]) -> dict[str, Any]:
    validate_source_numbers(sources)
    rows = [
        budget_row(
            "strict_native_single_vs_two_proof_frontier",
            "ATTACK_NEXT_LOCAL_FRONTIER",
            "local_frontier",
            STRICT_NATIVE_SINGLE_TYPED_BYTES,
            TWO_PROOF_FRONTIER_TYPED_BYTES,
            False,
            "Recovering 1,233 typed bytes would beat the local two-proof frontier; this is only 3.8359% of observed MLP fusion saving.",
        ),
        budget_row(
            "compact_selector_vs_two_proof_frontier",
            "PARK_LABEL_FRAGILE",
            "local_frontier",
            COMPACT_SELECTOR_TYPED_BYTES,
            TWO_PROOF_FRONTIER_TYPED_BYTES,
            False,
            "The raw gap is tiny, but prior label probes make this unsafe as the next headline route.",
        ),
        budget_row(
            "post_tail_worst_label_vs_two_proof_frontier",
            "PARK_LOCAL_REORDER",
            "local_frontier",
            POST_TAIL_TYPED_BYTES,
            TWO_PROOF_FRONTIER_TYPED_BYTES,
            False,
            "Another local reorder has to recover 2,025 typed bytes under worst-label policy, so it is parked behind the larger boundary attack.",
        ),
        budget_row(
            "gkr_width_preserving_vs_two_proof_frontier",
            "PARK_CURRENT_GKR",
            "local_frontier",
            GKR_WIDTH_PRESERVING_TYPED_BYTES,
            TWO_PROOF_FRONTIER_TYPED_BYTES,
            False,
            "The current GKR projection preflight would need 91.5847% of the MLP fusion saving just to beat the local frontier.",
        ),
        budget_row(
            "strict_native_single_vs_nanozk_context",
            "BLOCKED_NOT_MATCHED",
            "external_context_guardrail",
            STRICT_NATIVE_SINGLE_TYPED_BYTES,
            NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
            False,
            "Beating the NANOZK context row would require more typed bytes than the entire observed MLP-side fusion saving, and the workload is not matched.",
        ),
        budget_row(
            "two_proof_frontier_vs_nanozk_context",
            "CONTEXT_ONLY_NOT_MATCHED",
            "external_context_guardrail",
            TWO_PROOF_FRONTIER_TYPED_BYTES,
            NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
            False,
            "The current local frontier is still 33,800 typed bytes above the NANOZK context row and is not a matched external comparison.",
        ),
        budget_row(
            "compact_preprocessed_vs_nanozk_context",
            "MECHANISM_LEAD_NOT_COMPARABLE",
            "external_context_guardrail",
            COMPACT_PREPROCESSED_TYPED_BYTES,
            NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
            False,
            "This is below the paper-reported row only for a scoped public-row surface, not for a full d128 block proof.",
        ),
    ]
    summary = {
        "issue": ISSUE,
        "selected_next_route": SELECTED_NEXT_ROUTE,
        "row_count": len(rows),
        "attack_next_count": sum(1 for row in rows if row["status"] == "ATTACK_NEXT_LOCAL_FRONTIER"),
        "park_count": sum(1 for row in rows if row["status"].startswith("PARK_")),
        "external_context_guardrail_count": sum(1 for row in rows if row["comparison_scope"] == "external_context_guardrail"),
        "proof_size_comparable_rows": sum(1 for row in rows if row["proof_size_comparable_to_nanozk"]),
        "two_proof_frontier_typed_bytes": TWO_PROOF_FRONTIER_TYPED_BYTES,
        "strict_native_single_typed_bytes": STRICT_NATIVE_SINGLE_TYPED_BYTES,
        "strict_native_delta_vs_frontier_typed_bytes": STRICT_NATIVE_SINGLE_TYPED_BYTES - TWO_PROOF_FRONTIER_TYPED_BYTES,
        "strict_native_reduction_to_beat_frontier_bytes": STRICT_REDUCTION_TO_BEAT_FRONTIER_BYTES,
        "strict_native_share_of_mlp_fusion_saving_to_beat_frontier": STRICT_SHARE_TO_BEAT_FRONTIER,
        "four_percent_transfer_model_bytes": FOUR_PERCENT_TRANSFER_BYTES,
        "four_percent_transfer_model_typed_bytes": FOUR_PERCENT_TRANSFER_MODELED_TYPED_BYTES,
        "four_percent_transfer_model_margin_vs_frontier_bytes": FOUR_PERCENT_TRANSFER_MARGIN_VS_FRONTIER_BYTES,
        "post_tail_reduction_to_beat_frontier_bytes": POST_TAIL_REDUCTION_TO_BEAT_FRONTIER_BYTES,
        "gkr_reduction_to_beat_frontier_bytes": GKR_REDUCTION_TO_BEAT_FRONTIER_BYTES,
        "mlp_fusion_typed_saving_bytes": MLP_FUSION_TYPED_SAVING_BYTES,
        "mlp_fusion_typed_saving_ratio": MLP_FUSION_TYPED_SAVING_RATIO,
        "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
        "strict_native_reduction_to_beat_nanozk_context_bytes": STRICT_REDUCTION_TO_BEAT_NANOZK_BYTES,
        "strict_native_share_of_mlp_fusion_saving_to_beat_nanozk_context": STRICT_SHARE_TO_BEAT_NANOZK,
        "two_proof_reduction_to_beat_nanozk_context_bytes": TWO_PROOF_REDUCTION_TO_BEAT_NANOZK_BYTES,
        "two_proof_share_of_mlp_fusion_saving_to_beat_nanozk_context": TWO_PROOF_SHARE_TO_BEAT_NANOZK,
        "compact_preprocessed_typed_bytes": COMPACT_PREPROCESSED_TYPED_BYTES,
    }
    return {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "summary": summary,
        "budget_rows": rows,
        "interpretation": {
            "human_read": INTERPRETATION_HUMAN_READ,
            "nanozk_guardrail": INTERPRETATION_NANOZK_GUARDRAIL,
            "next_experiment": INTERPRETATION_NEXT_EXPERIMENT,
        },
        "source_artifacts": copy.deepcopy(require_list(sources.get(SOURCE_ARTIFACTS_KEY), "source artifact snapshot")),
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }


def validate_payload(
    payload: dict[str, Any],
    *,
    final: bool = True,
    expected_source_artifacts: list[dict[str, Any]] | None = None,
) -> None:
    expected_keys = {
        "budget_rows",
        "claim_boundary",
        "decision",
        "interpretation",
        "mutation_count",
        "mutation_results",
        "mutations_rejected",
        "non_claims",
        "payload_commitment",
        "result",
        "schema",
        "source_artifacts",
        "summary",
        "validation_commands",
    }
    if final:
        if set(payload) != expected_keys:
            raise AmortizationBudgetError("top-level key inventory drift")
        expected_commitment = commitment({key: value for key, value in payload.items() if key != "payload_commitment"})
        expect_equal(payload.get("payload_commitment"), expected_commitment, "payload commitment")
    else:
        allowed = expected_keys - {"mutation_count", "mutation_results", "mutations_rejected", "payload_commitment"}
        if not set(payload).issubset(allowed):
            raise AmortizationBudgetError("draft top-level key inventory drift")

    expect_equal(payload.get("schema"), SCHEMA, "schema")
    expect_equal(payload.get("decision"), DECISION, "decision")
    expect_equal(payload.get("result"), RESULT, "result")
    expect_equal(payload.get("claim_boundary"), CLAIM_BOUNDARY, "claim boundary")

    summary = require_dict(payload.get("summary"), "summary")
    expect_equal(summary.get("selected_next_route"), SELECTED_NEXT_ROUTE, "selected next route")
    expect_equal(require_int(summary.get("row_count"), "row count"), len(EXPECTED_ROW_IDS), "row count")
    expect_equal(require_int(summary.get("attack_next_count"), "attack-next count"), 1, "attack-next count")
    expect_equal(require_int(summary.get("park_count"), "park count"), 3, "park count")
    expect_equal(require_int(summary.get("external_context_guardrail_count"), "external guardrail count"), 3, "external guardrail count")
    expect_equal(require_int(summary.get("proof_size_comparable_rows"), "proof-size comparable rows"), 0, "proof-size comparable rows")
    expect_equal(require_int(summary.get("two_proof_frontier_typed_bytes"), "frontier"), TWO_PROOF_FRONTIER_TYPED_BYTES, "frontier")
    expect_equal(require_int(summary.get("strict_native_single_typed_bytes"), "strict native typed"), STRICT_NATIVE_SINGLE_TYPED_BYTES, "strict native typed")
    expect_equal(require_int(summary.get("strict_native_delta_vs_frontier_typed_bytes"), "strict native gap"), STRICT_NATIVE_SINGLE_TYPED_BYTES - TWO_PROOF_FRONTIER_TYPED_BYTES, "strict native gap")
    expect_equal(require_int(summary.get("strict_native_reduction_to_beat_frontier_bytes"), "strict beat frontier"), STRICT_REDUCTION_TO_BEAT_FRONTIER_BYTES, "strict beat frontier")
    expect_equal(summary.get("strict_native_share_of_mlp_fusion_saving_to_beat_frontier"), STRICT_SHARE_TO_BEAT_FRONTIER, "strict share to beat frontier")
    expect_equal(require_int(summary.get("four_percent_transfer_model_bytes"), "four percent transfer"), FOUR_PERCENT_TRANSFER_BYTES, "four percent transfer")
    expect_equal(require_int(summary.get("four_percent_transfer_model_typed_bytes"), "four percent modeled typed"), FOUR_PERCENT_TRANSFER_MODELED_TYPED_BYTES, "four percent modeled typed")
    expect_equal(require_int(summary.get("four_percent_transfer_model_margin_vs_frontier_bytes"), "four percent margin"), FOUR_PERCENT_TRANSFER_MARGIN_VS_FRONTIER_BYTES, "four percent margin")
    expect_equal(require_int(summary.get("post_tail_reduction_to_beat_frontier_bytes"), "post-tail beat frontier"), POST_TAIL_REDUCTION_TO_BEAT_FRONTIER_BYTES, "post-tail beat frontier")
    expect_equal(require_int(summary.get("gkr_reduction_to_beat_frontier_bytes"), "GKR beat frontier"), GKR_REDUCTION_TO_BEAT_FRONTIER_BYTES, "GKR beat frontier")
    expect_equal(require_int(summary.get("mlp_fusion_typed_saving_bytes"), "MLP saving"), MLP_FUSION_TYPED_SAVING_BYTES, "MLP saving")
    expect_equal(summary.get("mlp_fusion_typed_saving_ratio"), MLP_FUSION_TYPED_SAVING_RATIO, "MLP saving ratio")
    expect_equal(require_int(summary.get("nanozk_reported_d128_block_proof_bytes"), "NANOZK context"), NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES, "NANOZK context")
    expect_equal(require_int(summary.get("strict_native_reduction_to_beat_nanozk_context_bytes"), "strict beat NANOZK context"), STRICT_REDUCTION_TO_BEAT_NANOZK_BYTES, "strict beat NANOZK context")
    expect_equal(summary.get("strict_native_share_of_mlp_fusion_saving_to_beat_nanozk_context"), STRICT_SHARE_TO_BEAT_NANOZK, "strict share to beat NANOZK context")
    expect_equal(require_int(summary.get("two_proof_reduction_to_beat_nanozk_context_bytes"), "two-proof beat NANOZK context"), TWO_PROOF_REDUCTION_TO_BEAT_NANOZK_BYTES, "two-proof beat NANOZK context")
    expect_equal(summary.get("two_proof_share_of_mlp_fusion_saving_to_beat_nanozk_context"), TWO_PROOF_SHARE_TO_BEAT_NANOZK, "two-proof share to beat NANOZK context")
    expect_equal(require_int(summary.get("compact_preprocessed_typed_bytes"), "compact preprocessed typed"), COMPACT_PREPROCESSED_TYPED_BYTES, "compact preprocessed typed")

    rows = [require_dict(row, "budget row") for row in require_list(payload.get("budget_rows"), "budget rows")]
    expect_equal([require_str(row.get("row_id"), "row id") for row in rows], list(EXPECTED_ROW_IDS), "row order")
    for row in rows:
        if set(row) != set(ROW_COLUMNS):
            raise AmortizationBudgetError("budget row key inventory drift")
        if require_bool(row.get("proof_size_comparable_to_nanozk"), "proof-size comparable"):
            raise AmortizationBudgetError("NANOZK proof-size comparability overclaim")
        expected_delta = require_int(row.get("current_typed_bytes"), "current typed") - require_int(row.get("reference_typed_bytes"), "reference typed")
        expect_equal(require_int(row.get("delta_vs_reference_typed_bytes"), "delta"), expected_delta, f"{row['row_id']} delta")
        expected_reduction = reduction_to_beat(row["current_typed_bytes"], row["reference_typed_bytes"])
        expect_equal(require_int(row.get("reduction_to_beat_reference_bytes"), "reduction to beat"), expected_reduction, f"{row['row_id']} reduction to beat")
        expect_equal(row.get("share_of_mlp_fusion_saving_to_beat_reference"), share_to_beat(row["current_typed_bytes"], row["reference_typed_bytes"]), f"{row['row_id']} share to beat")

    rows_by_id = {row["row_id"]: row for row in rows}
    expect_equal(rows_by_id["strict_native_single_vs_two_proof_frontier"]["status"], "ATTACK_NEXT_LOCAL_FRONTIER", "strict row status")
    expect_equal(rows_by_id["strict_native_single_vs_two_proof_frontier"]["reduction_to_beat_reference_bytes"], STRICT_REDUCTION_TO_BEAT_FRONTIER_BYTES, "strict row beat frontier")
    expect_equal(rows_by_id["strict_native_single_vs_two_proof_frontier"]["share_of_mlp_fusion_saving_to_beat_reference"], STRICT_SHARE_TO_BEAT_FRONTIER, "strict row share")
    expect_equal(rows_by_id["compact_selector_vs_two_proof_frontier"]["status"], "PARK_LABEL_FRAGILE", "compact row status")
    expect_equal(rows_by_id["compact_selector_vs_two_proof_frontier"]["reduction_to_beat_reference_bytes"], COMPACT_REDUCTION_TO_BEAT_FRONTIER_BYTES, "compact row beat frontier")
    expect_equal(rows_by_id["post_tail_worst_label_vs_two_proof_frontier"]["reduction_to_beat_reference_bytes"], POST_TAIL_REDUCTION_TO_BEAT_FRONTIER_BYTES, "post-tail row beat frontier")
    expect_equal(rows_by_id["post_tail_worst_label_vs_two_proof_frontier"]["share_of_mlp_fusion_saving_to_beat_reference"], POST_TAIL_SHARE_TO_BEAT_FRONTIER, "post-tail row share")
    expect_equal(rows_by_id["gkr_width_preserving_vs_two_proof_frontier"]["status"], "PARK_CURRENT_GKR", "GKR row status")
    expect_equal(rows_by_id["gkr_width_preserving_vs_two_proof_frontier"]["share_of_mlp_fusion_saving_to_beat_reference"], GKR_SHARE_TO_BEAT_FRONTIER, "GKR row share")
    expect_equal(rows_by_id["strict_native_single_vs_nanozk_context"]["status"], "BLOCKED_NOT_MATCHED", "strict NANOZK status")
    expect_equal(rows_by_id["strict_native_single_vs_nanozk_context"]["reduction_to_beat_reference_bytes"], STRICT_REDUCTION_TO_BEAT_NANOZK_BYTES, "strict NANOZK reduction")
    expect_equal(rows_by_id["strict_native_single_vs_nanozk_context"]["share_of_mlp_fusion_saving_to_beat_reference"], STRICT_SHARE_TO_BEAT_NANOZK, "strict NANOZK share")
    expect_equal(rows_by_id["two_proof_frontier_vs_nanozk_context"]["reduction_to_beat_reference_bytes"], TWO_PROOF_REDUCTION_TO_BEAT_NANOZK_BYTES, "two-proof NANOZK reduction")
    expect_equal(rows_by_id["two_proof_frontier_vs_nanozk_context"]["share_of_mlp_fusion_saving_to_beat_reference"], TWO_PROOF_SHARE_TO_BEAT_NANOZK, "two-proof NANOZK share")
    expect_equal(rows_by_id["compact_preprocessed_vs_nanozk_context"]["status"], "MECHANISM_LEAD_NOT_COMPARABLE", "compact preprocessed status")
    expect_equal(rows_by_id["compact_preprocessed_vs_nanozk_context"]["reduction_to_beat_reference_bytes"], 0, "compact preprocessed reduction")

    interpretation = require_dict(payload.get("interpretation"), "interpretation")
    expect_equal(require_str(interpretation.get("human_read"), "human interpretation"), INTERPRETATION_HUMAN_READ, "human interpretation")
    expect_equal(require_str(interpretation.get("nanozk_guardrail"), "NANOZK interpretation"), INTERPRETATION_NANOZK_GUARDRAIL, "NANOZK interpretation")
    expect_equal(require_str(interpretation.get("next_experiment"), "next experiment interpretation"), INTERPRETATION_NEXT_EXPERIMENT, "next experiment interpretation")

    source_artifacts = [require_dict(row, "source artifact row") for row in require_list(payload.get("source_artifacts"), "source artifacts")]
    for row in source_artifacts:
        if set(row) != set(SOURCE_ARTIFACT_KEYS):
            raise AmortizationBudgetError("source artifact row key inventory drift")
        require_str(row.get("schema"), "source artifact schema")
        require_str(row.get("decision"), "source artifact decision")
        require_str(row.get("result"), "source artifact result")
        digest = require_str(row.get("sha256"), "source artifact sha256")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise AmortizationBudgetError("source artifact sha256 format drift")
        if require_int(row.get("bytes"), "source artifact bytes") <= 0:
            raise AmortizationBudgetError("source artifact bytes must be positive")
    expected_source_paths = [path.relative_to(ROOT).as_posix() for path in SOURCE_PATHS]
    actual_source_paths = [require_str(row.get("path"), "source path") for row in source_artifacts]
    expect_equal(actual_source_paths, expected_source_paths, "source artifact paths")
    if expected_source_artifacts is None:
        expected_source_artifacts = [
            require_dict(row, "expected source artifact row")
            for row in require_list(load_sources().get(SOURCE_ARTIFACTS_KEY), "expected source artifacts")
        ]
    expect_equal(source_artifacts, expected_source_artifacts, "source artifact descriptor")

    non_claims = require_list(payload.get("non_claims"), "non-claims")
    if not set(NON_CLAIMS).issubset(set(non_claims)):
        raise AmortizationBudgetError("payload missing non-claims")
    expect_equal(tuple(payload.get("validation_commands", ())), VALIDATION_COMMANDS, "validation command inventory")

    if final:
        mutation_results = [require_dict(row, "mutation result row") for row in require_list(payload.get("mutation_results"), "mutation results")]
        expect_equal([row.get("name") for row in mutation_results], [name for name, _ in MUTATIONS], "mutation inventory")
        if not all(row.get("rejected") is True for row in mutation_results):
            raise AmortizationBudgetError("mutation inventory drift")
        expect_equal(require_int(payload.get("mutation_count"), "mutation count"), len(MUTATIONS), "mutation count")
        expect_equal(require_int(payload.get("mutations_rejected"), "mutations rejected"), len(MUTATIONS), "mutations rejected")


def mutate_promote_nanozk_comparable(payload: dict[str, Any]) -> None:
    payload["budget_rows"][4]["proof_size_comparable_to_nanozk"] = True


def mutate_selected_route_to_local_reorder(payload: dict[str, Any]) -> None:
    payload["summary"]["selected_next_route"] = "sub_kilobyte_adapter_reorder"
    payload["budget_rows"][0]["status"] = "PARK_LOCAL_REORDER"
    payload["budget_rows"][2]["status"] = "ATTACK_NEXT_LOCAL_FRONTIER"


def mutate_strict_frontier_gap_erased(payload: dict[str, Any]) -> None:
    payload["summary"]["strict_native_reduction_to_beat_frontier_bytes"] = 0


def mutate_four_percent_projection_erased(payload: dict[str, Any]) -> None:
    payload["summary"]["four_percent_transfer_model_margin_vs_frontier_bytes"] = 0


def mutate_mlp_saving_inflated(payload: dict[str, Any]) -> None:
    payload["summary"]["mlp_fusion_typed_saving_bytes"] = 64_288


def mutate_nanozk_gap_erased(payload: dict[str, Any]) -> None:
    payload["budget_rows"][4]["reduction_to_beat_reference_bytes"] = 0


def mutate_compact_preprocessed_promoted(payload: dict[str, Any]) -> None:
    payload["budget_rows"][6]["status"] = "ATTACK_NEXT_LOCAL_FRONTIER"
    payload["budget_rows"][6]["proof_size_comparable_to_nanozk"] = True


def mutate_gkr_unparked(payload: dict[str, Any]) -> None:
    payload["budget_rows"][3]["status"] = "ATTACK_NEXT_LOCAL_FRONTIER"


def mutate_interpretation_overclaim(payload: dict[str, Any]) -> None:
    payload["interpretation"]["nanozk_guardrail"] = "This is now a matched NANOZK proof-size win."


def mutate_source_descriptor_drift(payload: dict[str, Any]) -> None:
    payload["source_artifacts"][0]["sha256"] = "0" * 64


def mutate_remove_non_claim(payload: dict[str, Any]) -> None:
    payload["non_claims"] = payload["non_claims"][:-1]


def mutate_validation_command_drift(payload: dict[str, Any]) -> None:
    payload["validation_commands"] = payload["validation_commands"][:-1]


def mutate_payload_commitment(payload: dict[str, Any]) -> None:
    payload["payload_commitment"] = "blake2b-256:" + "0" * 64


MUTATIONS: tuple[tuple[str, Callable[[dict[str, Any]], None]], ...] = (
    ("promote_nanozk_comparable", mutate_promote_nanozk_comparable),
    ("selected_route_changed_to_local_reorder", mutate_selected_route_to_local_reorder),
    ("strict_frontier_gap_erased", mutate_strict_frontier_gap_erased),
    ("four_percent_projection_erased", mutate_four_percent_projection_erased),
    ("mlp_saving_inflated", mutate_mlp_saving_inflated),
    ("nanozk_gap_erased", mutate_nanozk_gap_erased),
    ("compact_preprocessed_promoted", mutate_compact_preprocessed_promoted),
    ("gkr_unparked", mutate_gkr_unparked),
    ("interpretation_overclaim", mutate_interpretation_overclaim),
    ("source_descriptor_drift", mutate_source_descriptor_drift),
    ("non_claim_removed", mutate_remove_non_claim),
    ("validation_command_drift", mutate_validation_command_drift),
    ("payload_commitment_drift", mutate_payload_commitment),
)


def run_mutations(payload: dict[str, Any], expected_source_artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for name, mutator in MUTATIONS:
        mutated = copy.deepcopy(payload)
        mutator(mutated)
        if name != "payload_commitment_drift":
            try:
                validate_payload(mutated, final=False, expected_source_artifacts=expected_source_artifacts)
            except AmortizationBudgetError as error:
                results.append({"name": name, "rejected": True, "error": str(error)})
            else:
                results.append({"name": name, "rejected": False, "error": "accepted"})
        else:
            mutated["mutation_results"] = []
            mutated["mutation_count"] = 0
            mutated["mutations_rejected"] = 0
            try:
                validate_payload(mutated, final=True, expected_source_artifacts=expected_source_artifacts)
            except AmortizationBudgetError as error:
                results.append({"name": name, "rejected": True, "error": str(error)})
            else:
                results.append({"name": name, "rejected": False, "error": "accepted"})
    return results


def build_payload() -> dict[str, Any]:
    sources = load_sources()
    expected_source_artifacts = [
        require_dict(row, "expected source artifact row")
        for row in require_list(sources.get(SOURCE_ARTIFACTS_KEY), "expected source artifacts")
    ]
    payload = base_payload(sources)
    mutation_results = run_mutations(payload, expected_source_artifacts)
    payload["mutation_results"] = mutation_results
    payload["mutation_count"] = len(mutation_results)
    payload["mutations_rejected"] = sum(1 for row in mutation_results if row["rejected"])
    payload["payload_commitment"] = commitment(payload)
    validate_payload(payload, expected_source_artifacts=expected_source_artifacts)
    return payload


def tsv_text(payload: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=ROW_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in payload["budget_rows"]:
        writer.writerow({key: row[key] for key in ROW_COLUMNS})
    return output.getvalue()


def write_text(path: pathlib.Path, text: str) -> None:
    raw_path = path if path.is_absolute() else ROOT / path
    if raw_path.suffix not in {".json", ".tsv"}:
        raise AmortizationBudgetError(f"unsupported output suffix: {raw_path}")
    resolved_evidence = EVIDENCE_DIR.resolve(strict=False)
    resolved_path = raw_path.resolve(strict=False)
    try:
        resolved_path.relative_to(resolved_evidence)
    except ValueError as error:
        raise AmortizationBudgetError(f"output path must be under evidence dir: {raw_path}") from error

    cursor = raw_path
    while True:
        if cursor.is_symlink():
            raise AmortizationBudgetError(f"output path must not use a symlink: {cursor}")
        if cursor == EVIDENCE_DIR or cursor == cursor.parent:
            break
        cursor = cursor.parent

    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_path.write_text(text, encoding="utf-8")


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path, tsv_path: pathlib.Path | None) -> None:
    write_text(json_path, json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    if tsv_path is not None:
        write_text(tsv_path, tsv_text(payload))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path, default=JSON_OUT)
    parser.add_argument("--write-tsv", type=pathlib.Path, default=TSV_OUT)
    args = parser.parse_args()

    payload = build_payload()
    write_outputs(payload, args.write_json, args.write_tsv)
    print(
        json.dumps(
            {
                "decision": payload["decision"],
                "result": payload["result"],
                "selected_next_route": payload["summary"]["selected_next_route"],
                "strict_native_reduction_to_beat_frontier_bytes": payload["summary"][
                    "strict_native_reduction_to_beat_frontier_bytes"
                ],
                "strict_native_share_of_mlp_fusion_saving_to_beat_frontier": payload["summary"][
                    "strict_native_share_of_mlp_fusion_saving_to_beat_frontier"
                ],
                "mutation_count": payload["mutation_count"],
                "mutations_rejected": payload["mutations_rejected"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
