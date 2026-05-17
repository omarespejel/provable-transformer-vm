#!/usr/bin/env python3
"""Select the next native block-boundary attack after recent NO-GOs.

This gate is deliberately a selector, not a proof-size win. It consumes the
checked adapter-layout, GKR preflight, native single-proof, and MLP-fusion
artifacts and pins the next execution route without promoting partial surfaces
to matched external comparisons.
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

POST_TAIL = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-post-tail-layout-2026-05.json"
GKR_PREFLIGHT = EVIDENCE_DIR / "zkai-gkr-d128-projection-scaling-preflight-2026-05.json"
COMPACT_SELECTOR = EVIDENCE_DIR / "zkai-native-attention-mlp-source-backed-adapter-selector-2026-05.json"
NATIVE_SINGLE = EVIDENCE_DIR / "zkai-native-attention-mlp-single-proof-2026-05.json"
MLP_FUSED = EVIDENCE_DIR / "zkai-d128-rmsnorm-mlp-fused-gate-2026-05.json"
COMPACT_PREPROCESSED = EVIDENCE_DIR / "zkai-d128-component-compact-preprocessed-reprove-gate-2026-05.json"
MINIMAL_BLOCK = EVIDENCE_DIR / "zkai-minimal-transformer-block-benchmark-2026-05.json"
ATTENTION_MLP_FRONTIER = EVIDENCE_DIR / "zkai-d128-attention-mlp-boundary-frontier-2026-05.json"

JSON_OUT = EVIDENCE_DIR / "zkai-native-block-boundary-pivot-selector-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-block-boundary-pivot-selector-2026-05.tsv"

ISSUE = 667
SCHEMA = "zkai-native-block-boundary-pivot-selector-v1"
DECISION = "ATTACK_NEXT_LARGER_NATIVE_BLOCK_BOUNDARY"
RESULT = "PIVOT_TO_LARGER_NATIVE_BOUNDARY_NOT_LOCAL_REORDER_OR_CURRENT_GKR"
CLAIM_BOUNDARY = (
    "SELECT_NEXT_NATIVE_ZKML_ROUTE_FROM_CHECKED_EVIDENCE_WITH_NO_NANOZK_OR_FRONTIER_OVERCLAIM"
)
SELECTED_NEXT_ROUTE = "larger_native_block_boundary"

TWO_PROOF_FRONTIER_TYPED_BYTES = 40_700
NANOZK_PAPER_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900
STRICT_NATIVE_ADAPTER_TYPED_BYTES = 41_932
STRICT_NATIVE_ADAPTER_GAP_BYTES = 1_232
COMPACT_SELECTOR_TYPED_BYTES = 40_812
COMPACT_SELECTOR_GAP_BYTES = 112
POST_TAIL_TYPED_BYTES = 42_724
POST_TAIL_GAP_BYTES = 2_024
POST_TAIL_LABEL_SPAN_BYTES = 1_216
GKR_SMALLEST_WIDTH_PRESERVING_BYTES = 70_138
MLP_FUSED_TYPED_BYTES = 24_832
MLP_SEPARATE_TYPED_BYTES = 56_976
MLP_FUSION_TYPED_SAVING_BYTES = 32_144
MLP_FUSION_TYPED_SAVING_RATIO = "0.564167"
COMPACT_PREPROCESSED_TYPED_BYTES = 6_264
COMPACT_PREPROCESSED_VS_NANOZK_RATIO = "0.907826"
ATTENTION_FUSED_TYPED_BYTES = 18_124
DERIVED_MLP_FUSED_TYPED_BYTES = 22_576

NON_CLAIMS = (
    "not a NANOZK proof-size win",
    "not a matched NANOZK benchmark",
    "not a full transformer block proof",
    "not a timing result",
    "not evidence that GKR replaces Stwo",
    "not production zkML",
)

VALIDATION_COMMANDS = (
    "python3 scripts/zkai_native_block_boundary_pivot_selector_gate.py --write-json docs/engineering/evidence/zkai-native-block-boundary-pivot-selector-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-block-boundary-pivot-selector-2026-05.tsv",
    "python3 -m py_compile scripts/zkai_native_block_boundary_pivot_selector_gate.py scripts/tests/test_zkai_native_block_boundary_pivot_selector_gate.py",
    "python3 -m unittest scripts.tests.test_zkai_native_block_boundary_pivot_selector_gate",
    "python3 scripts/research_issue_lint.py --repo-root .",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

SOURCE_PATHS = (
    POST_TAIL,
    GKR_PREFLIGHT,
    COMPACT_SELECTOR,
    NATIVE_SINGLE,
    MLP_FUSED,
    COMPACT_PREPROCESSED,
    MINIMAL_BLOCK,
    ATTENTION_MLP_FRONTIER,
)
SOURCE_ARTIFACTS_KEY = "__source_artifacts"

LARGER_NATIVE_BOUNDARY_EVIDENCE = (
    "six-component MLP fusion saves 32,144 typed bytes while current adapter/reorder routes are label-fragile"
)
SUB_KILOBYTE_REORDER_EVIDENCE = (
    "post-tail canonical is 42,724 typed bytes and matches the adjacent bad-label record stream"
)
CURRENT_GKR_PROJECTION_EVIDENCE = (
    "width-preserving GKR dim2/dim4 rows are already heavier than local Stwo dense baselines"
)
COMPACT_PREPROCESSED_EVIDENCE = (
    "6,264 typed bytes is below the NANOZK paper row but only for selected public RMSNorm plus bridge"
)
COMPARISON_GUARDRAIL_EVIDENCE = (
    "minimal block benchmark still has missing native block proof object and zero matched external proof-size rows"
)
LARGER_NATIVE_BOUNDARY_NEXT_GATE = (
    "build a larger source-bound native boundary or amortization gate before another local reorder"
)
SUB_KILOBYTE_REORDER_NEXT_GATE = (
    "reopen only with label-stable query/opening policy and worst-label proof below 40,700 typed bytes"
)
CURRENT_GKR_PROJECTION_NEXT_GATE = "reopen only with a live dim8/16/32 sweep or a new GKR backend"
COMPACT_PREPROCESSED_NEXT_GATE = (
    "extend only to public-row-like surfaces; do not compare as a full d128 block proof"
)
COMPARISON_GUARDRAIL_NEXT_GATE = (
    "keep comparison table separated by object class, source status, and local reproduction status"
)
ROUTE_TEXT_EXPECTATIONS = {
    "larger_native_block_boundary": (LARGER_NATIVE_BOUNDARY_EVIDENCE, LARGER_NATIVE_BOUNDARY_NEXT_GATE),
    "sub_kilobyte_adapter_reorder": (SUB_KILOBYTE_REORDER_EVIDENCE, SUB_KILOBYTE_REORDER_NEXT_GATE),
    "current_gkr_projection_sidecar": (CURRENT_GKR_PROJECTION_EVIDENCE, CURRENT_GKR_PROJECTION_NEXT_GATE),
    "compact_preprocessed_public_rows": (COMPACT_PREPROCESSED_EVIDENCE, COMPACT_PREPROCESSED_NEXT_GATE),
    "comparison_claim_guardrail": (COMPARISON_GUARDRAIL_EVIDENCE, COMPARISON_GUARDRAIL_NEXT_GATE),
}
INTERPRETATION_HUMAN_READ = (
    "The next serious attack is a larger native proof boundary. The local reorder route is now "
    "label-fragile, current GKR projection scaling is parked, and the positive mechanism remains "
    "shared native STARK plumbing across larger adjacent transformer surfaces."
)
INTERPRETATION_WHY_NOT_LOCAL_REORDER = (
    "The compact selector is only 112 typed bytes above the two-proof frontier, but post-tail and "
    "label probes move opening bytes by more than that. A small favorable label is not a robust result."
)
INTERPRETATION_WHY_LARGER_BOUNDARY = (
    "The six-component d128 RMSNorm-to-residual MLP proof saves 32,144 typed bytes versus separate "
    "native objects, which is a structural signal rather than a sub-kilobyte layout artifact."
)

ROW_COLUMNS = (
    "route_id",
    "selector_status",
    "primary_evidence",
    "typed_bytes",
    "delta_vs_frontier_typed_bytes",
    "proof_size_comparable_to_nanozk",
    "next_gate",
)

EXPECTED_ROUTE_IDS = (
    "larger_native_block_boundary",
    "sub_kilobyte_adapter_reorder",
    "current_gkr_projection_sidecar",
    "compact_preprocessed_public_rows",
    "comparison_claim_guardrail",
)


class PivotSelectorError(Exception):
    pass


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def commitment(data: Any) -> str:
    return "blake2b-256:" + hashlib.blake2b(canonical_json(data).encode("utf-8"), digest_size=32).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except OSError as error:
        raise PivotSelectorError(f"unable to read JSON source: {path}") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PivotSelectorError(f"invalid JSON source: {path}") from error
    if not isinstance(payload, dict):
        raise PivotSelectorError(f"{path} must contain a JSON object")
    return payload


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PivotSelectorError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise PivotSelectorError(f"{label} must be a list")
    return value


def require_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise PivotSelectorError(f"{label} must be an integer")
    return value


def require_float(value: Any, label: str) -> float:
    if not isinstance(value, (float, int)) or isinstance(value, bool):
        raise PivotSelectorError(f"{label} must be a number")
    return float(value)


def require_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise PivotSelectorError(f"{label} must be a non-empty string")
    return value


def require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise PivotSelectorError(f"{label} must be a boolean")
    return value


def expect_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise PivotSelectorError(f"{label} drift: expected {expected!r}, got {actual!r}")


def source_descriptor_from_snapshot(path: pathlib.Path, raw: bytes, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "schema": data.get("schema"),
        "decision": data.get("decision"),
        "result": data.get("result"),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def load_source_artifact(path: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise PivotSelectorError(f"unable to read source artifact: {path}") from error
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PivotSelectorError(f"invalid JSON source artifact: {path}") from error
    if not isinstance(data, dict):
        raise PivotSelectorError(f"{path} must contain a JSON object")
    return data, source_descriptor_from_snapshot(path, raw, data)


def source_descriptor(path: pathlib.Path) -> dict[str, Any]:
    _, descriptor = load_source_artifact(path)
    return descriptor


def load_sources() -> dict[str, Any]:
    source_items = (
        ("post_tail", POST_TAIL),
        ("gkr", GKR_PREFLIGHT),
        ("compact_selector", COMPACT_SELECTOR),
        ("native_single", NATIVE_SINGLE),
        ("mlp_fused", MLP_FUSED),
        ("compact_preprocessed", COMPACT_PREPROCESSED),
        ("minimal_block", MINIMAL_BLOCK),
        ("attention_mlp_frontier", ATTENTION_MLP_FRONTIER),
    )
    sources: dict[str, Any] = {}
    source_artifacts: list[dict[str, Any]] = []
    for label, path in source_items:
        payload, descriptor = load_source_artifact(path)
        sources[label] = payload
        source_artifacts.append(descriptor)
    sources[SOURCE_ARTIFACTS_KEY] = source_artifacts
    expect_equal(sources["post_tail"].get("schema"), "zkai-native-attention-mlp-rmsnorm-post-tail-layout-gate-v1", "post-tail schema")
    expect_equal(sources["gkr"].get("schema"), "zkai-gkr-d128-projection-scaling-preflight-v1", "GKR schema")
    expect_equal(sources["compact_selector"].get("schema"), "zkai-native-attention-mlp-source-backed-adapter-selector-gate-v1", "compact selector schema")
    expect_equal(sources["native_single"].get("schema"), "zkai-native-attention-mlp-single-proof-object-gate-v1", "native single schema")
    expect_equal(sources["mlp_fused"].get("schema"), "zkai-d128-rmsnorm-mlp-fused-gate-v1", "MLP fused schema")
    expect_equal(sources["compact_preprocessed"].get("schema"), "zkai-d128-component-compact-preprocessed-reprove-gate-v1", "compact preprocessed schema")
    expect_equal(sources["minimal_block"].get("schema"), "zkai-minimal-transformer-block-benchmark-v1", "minimal block schema")
    expect_equal(sources["attention_mlp_frontier"].get("schema"), "zkai-d128-attention-mlp-boundary-frontier-gate-v1", "attention MLP frontier schema")
    return sources


def validate_source_numbers(sources: dict[str, Any]) -> None:
    post_tail = sources["post_tail"]
    expect_equal(post_tail.get("decision"), "NO_GO_POST_TAIL_LAYOUT_LABEL_STABILITY", "post-tail decision")
    expect_equal(
        require_int(post_tail.get("post_tail_canonical_typed_bytes"), "post-tail typed bytes"),
        POST_TAIL_TYPED_BYTES,
        "post-tail typed bytes",
    )
    expect_equal(
        require_int(post_tail.get("post_tail_delta_vs_two_proof_frontier_typed_bytes"), "post-tail gap"),
        POST_TAIL_GAP_BYTES,
        "post-tail gap",
    )
    expect_equal(
        require_int(post_tail.get("post_tail_label_span_typed_bytes"), "post-tail label span"),
        POST_TAIL_LABEL_SPAN_BYTES,
        "post-tail label span",
    )
    expect_equal(require_int(post_tail.get("compact_selector_typed_bytes"), "compact selector typed bytes"), COMPACT_SELECTOR_TYPED_BYTES, "post-tail compact selector typed bytes")
    expect_equal(
        require_bool(post_tail.get("post_tail_matches_adjacent_bad_label_record_stream"), "post-tail record-stream match"),
        True,
        "post-tail record-stream match",
    )

    gkr_summary = require_dict(sources["gkr"].get("summary"), "GKR summary")
    expect_equal(sources["gkr"].get("decision"), "NO_GO_NOW_D128_PROJECTION_SCALING", "GKR decision")
    expect_equal(
        require_int(gkr_summary.get("smallest_width_preserving_gkr_proof_bytes"), "GKR smallest width bytes"),
        GKR_SMALLEST_WIDTH_PRESERVING_BYTES,
        "GKR smallest width bytes",
    )
    expect_equal(gkr_summary.get("recommendation"), "do_not_spend_next_pr_on_jstprove_d128_projection_without_live_dim8_16_32_sweep_or_new_gkr_backend", "GKR recommendation")
    expect_equal(require_int(gkr_summary.get("proof_size_comparable_rows"), "GKR comparable rows"), 0, "GKR comparable rows")

    compact_summary = require_dict(sources["compact_selector"].get("summary"), "compact selector summary")
    expect_equal(require_int(compact_summary.get("compact_typed_bytes"), "compact typed"), COMPACT_SELECTOR_TYPED_BYTES, "compact typed")
    expect_equal(require_int(compact_summary.get("compact_typed_delta_vs_two_proof_bytes"), "compact gap"), COMPACT_SELECTOR_GAP_BYTES, "compact gap")
    expect_equal(require_int(compact_summary.get("direct_opening_value_saving_bytes"), "direct opening saving"), 112, "direct opening saving")
    expect_equal(require_int(compact_summary.get("path_sensitive_saving_bytes"), "path sensitive saving"), 2_304, "path sensitive saving")

    native_summary = require_dict(sources["native_single"].get("summary"), "native single summary")
    expect_equal(require_bool(native_summary.get("native_adapter_air_proven"), "native adapter proven"), True, "native adapter proven")
    expect_equal(require_int(native_summary.get("single_proof_typed_bytes"), "native single typed"), STRICT_NATIVE_ADAPTER_TYPED_BYTES, "native single typed")
    expect_equal(require_int(native_summary.get("typed_delta_vs_two_proof_bytes"), "native single gap"), STRICT_NATIVE_ADAPTER_GAP_BYTES, "native single gap")

    mlp_aggregate = require_dict(sources["mlp_fused"].get("aggregate"), "MLP aggregate")
    expect_equal(require_int(mlp_aggregate.get("fused_local_typed_bytes"), "MLP fused typed"), MLP_FUSED_TYPED_BYTES, "MLP fused typed")
    expect_equal(require_int(mlp_aggregate.get("separate_local_typed_bytes"), "MLP separate typed"), MLP_SEPARATE_TYPED_BYTES, "MLP separate typed")
    expect_equal(require_int(mlp_aggregate.get("typed_saving_vs_separate_bytes"), "MLP saving"), MLP_FUSION_TYPED_SAVING_BYTES, "MLP saving")
    expect_equal(
        f"{require_float(mlp_aggregate.get('typed_saving_ratio_vs_separate'), 'MLP saving ratio'):.6f}",
        MLP_FUSION_TYPED_SAVING_RATIO,
        "MLP saving ratio",
    )

    compact_preprocessed = require_dict(sources["compact_preprocessed"].get("aggregate"), "compact-preprocessed aggregate")
    expect_equal(require_int(compact_preprocessed.get("compact_local_typed_bytes"), "compact preprocessed typed"), COMPACT_PREPROCESSED_TYPED_BYTES, "compact preprocessed typed")
    expect_equal(
        f"{require_float(compact_preprocessed.get('typed_ratio_vs_nanozk_paper_row'), 'compact preprocessed NANOZK ratio'):.6f}",
        COMPACT_PREPROCESSED_VS_NANOZK_RATIO,
        "compact preprocessed NANOZK ratio",
    )
    expect_equal(
        compact_preprocessed.get("comparison_status"),
        "below_nanozk_reported_row_under_local_typed_accounting_not_matched_benchmark",
        "compact preprocessed comparison status",
    )

    minimal_summary = require_dict(sources["minimal_block"].get("summary"), "minimal block summary")
    expect_equal(require_bool(minimal_summary.get("missing_native_block_proof_object"), "missing native block object"), True, "missing native block object")
    expect_equal(require_int(minimal_summary.get("two_proof_frontier_typed_bytes"), "minimal frontier"), TWO_PROOF_FRONTIER_TYPED_BYTES, "minimal frontier")
    expect_equal(require_int(minimal_summary.get("nanozk_reported_d128_block_proof_bytes"), "minimal NANOZK"), NANOZK_PAPER_REPORTED_D128_BLOCK_PROOF_BYTES, "minimal NANOZK")

    frontier_summary = require_dict(sources["attention_mlp_frontier"].get("summary"), "attention MLP frontier summary")
    expect_equal(require_int(frontier_summary.get("attention_fused_typed_bytes"), "attention typed"), ATTENTION_FUSED_TYPED_BYTES, "attention typed")
    expect_equal(require_int(frontier_summary.get("derived_mlp_fused_typed_bytes"), "derived MLP typed"), DERIVED_MLP_FUSED_TYPED_BYTES, "derived MLP typed")
    expect_equal(require_int(frontier_summary.get("two_proof_frontier_typed_bytes"), "two-proof frontier"), TWO_PROOF_FRONTIER_TYPED_BYTES, "two-proof frontier")


def route(
    route_id: str,
    selector_status: str,
    primary_evidence: str,
    typed_bytes: int | None,
    delta_vs_frontier_typed_bytes: int | None,
    proof_size_comparable_to_nanozk: bool,
    next_gate: str,
) -> dict[str, Any]:
    return {
        "route_id": route_id,
        "selector_status": selector_status,
        "primary_evidence": primary_evidence,
        "typed_bytes": typed_bytes,
        "delta_vs_frontier_typed_bytes": delta_vs_frontier_typed_bytes,
        "proof_size_comparable_to_nanozk": proof_size_comparable_to_nanozk,
        "next_gate": next_gate,
        "non_claims": list(NON_CLAIMS),
    }


def base_payload(sources: dict[str, Any]) -> dict[str, Any]:
    validate_source_numbers(sources)
    routes = [
        route(
            "larger_native_block_boundary",
            "ATTACK_NEXT",
            LARGER_NATIVE_BOUNDARY_EVIDENCE,
            STRICT_NATIVE_ADAPTER_TYPED_BYTES,
            STRICT_NATIVE_ADAPTER_GAP_BYTES,
            False,
            LARGER_NATIVE_BOUNDARY_NEXT_GATE,
        ),
        route(
            "sub_kilobyte_adapter_reorder",
            "PARK_NOW",
            SUB_KILOBYTE_REORDER_EVIDENCE,
            POST_TAIL_TYPED_BYTES,
            POST_TAIL_GAP_BYTES,
            False,
            SUB_KILOBYTE_REORDER_NEXT_GATE,
        ),
        route(
            "current_gkr_projection_sidecar",
            "PARK_NOW",
            CURRENT_GKR_PROJECTION_EVIDENCE,
            GKR_SMALLEST_WIDTH_PRESERVING_BYTES,
            GKR_SMALLEST_WIDTH_PRESERVING_BYTES - TWO_PROOF_FRONTIER_TYPED_BYTES,
            False,
            CURRENT_GKR_PROJECTION_NEXT_GATE,
        ),
        route(
            "compact_preprocessed_public_rows",
            "USE_SELECTIVELY",
            COMPACT_PREPROCESSED_EVIDENCE,
            COMPACT_PREPROCESSED_TYPED_BYTES,
            COMPACT_PREPROCESSED_TYPED_BYTES - TWO_PROOF_FRONTIER_TYPED_BYTES,
            False,
            COMPACT_PREPROCESSED_NEXT_GATE,
        ),
        route(
            "comparison_claim_guardrail",
            "GUARDRAIL",
            COMPARISON_GUARDRAIL_EVIDENCE,
            None,
            None,
            False,
            COMPARISON_GUARDRAIL_NEXT_GATE,
        ),
    ]
    summary = {
        "issue": ISSUE,
        "selected_next_route": SELECTED_NEXT_ROUTE,
        "route_count": len(routes),
        "attack_next_count": sum(1 for row in routes if row["selector_status"] == "ATTACK_NEXT"),
        "park_now_count": sum(1 for row in routes if row["selector_status"] == "PARK_NOW"),
        "use_selectively_count": sum(1 for row in routes if row["selector_status"] == "USE_SELECTIVELY"),
        "guardrail_count": sum(1 for row in routes if row["selector_status"] == "GUARDRAIL"),
        "proof_size_comparable_rows": sum(1 for row in routes if row["proof_size_comparable_to_nanozk"]),
        "two_proof_frontier_typed_bytes": TWO_PROOF_FRONTIER_TYPED_BYTES,
        "nanozk_paper_reported_d128_block_proof_bytes": NANOZK_PAPER_REPORTED_D128_BLOCK_PROOF_BYTES,
        "strict_native_adapter_typed_bytes": STRICT_NATIVE_ADAPTER_TYPED_BYTES,
        "strict_native_adapter_gap_bytes": STRICT_NATIVE_ADAPTER_GAP_BYTES,
        "compact_selector_typed_bytes": COMPACT_SELECTOR_TYPED_BYTES,
        "compact_selector_gap_bytes": COMPACT_SELECTOR_GAP_BYTES,
        "post_tail_typed_bytes": POST_TAIL_TYPED_BYTES,
        "post_tail_gap_bytes": POST_TAIL_GAP_BYTES,
        "post_tail_label_span_bytes": POST_TAIL_LABEL_SPAN_BYTES,
        "gkr_smallest_width_preserving_bytes": GKR_SMALLEST_WIDTH_PRESERVING_BYTES,
        "mlp_fused_typed_bytes": MLP_FUSED_TYPED_BYTES,
        "mlp_fusion_typed_saving_bytes": MLP_FUSION_TYPED_SAVING_BYTES,
        "mlp_fusion_typed_saving_ratio": MLP_FUSION_TYPED_SAVING_RATIO,
        "compact_preprocessed_typed_bytes": COMPACT_PREPROCESSED_TYPED_BYTES,
        "compact_preprocessed_vs_nanozk_ratio": COMPACT_PREPROCESSED_VS_NANOZK_RATIO,
    }
    return {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "summary": summary,
        "routes": routes,
        "interpretation": {
            "human_read": INTERPRETATION_HUMAN_READ,
            "why_not_local_reorder": INTERPRETATION_WHY_NOT_LOCAL_REORDER,
            "why_larger_boundary": INTERPRETATION_WHY_LARGER_BOUNDARY,
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
        "claim_boundary",
        "decision",
        "interpretation",
        "mutation_count",
        "mutation_results",
        "mutations_rejected",
        "non_claims",
        "payload_commitment",
        "result",
        "routes",
        "schema",
        "source_artifacts",
        "summary",
        "validation_commands",
    }
    if final:
        if set(payload) != expected_keys:
            raise PivotSelectorError("top-level key inventory drift")
        expected_commitment = commitment({key: value for key, value in payload.items() if key != "payload_commitment"})
        expect_equal(payload.get("payload_commitment"), expected_commitment, "payload commitment")
    else:
        allowed = expected_keys - {"mutation_count", "mutation_results", "mutations_rejected", "payload_commitment"}
        if not set(payload).issubset(allowed):
            raise PivotSelectorError("draft top-level key inventory drift")

    expect_equal(payload.get("schema"), SCHEMA, "schema")
    expect_equal(payload.get("decision"), DECISION, "decision")
    expect_equal(payload.get("result"), RESULT, "result")
    expect_equal(payload.get("claim_boundary"), CLAIM_BOUNDARY, "claim boundary")
    summary = require_dict(payload.get("summary"), "summary")
    expect_equal(summary.get("selected_next_route"), SELECTED_NEXT_ROUTE, "selected next route")
    expect_equal(require_int(summary.get("route_count"), "route count"), len(EXPECTED_ROUTE_IDS), "route count")
    expect_equal(require_int(summary.get("attack_next_count"), "attack-next count"), 1, "attack-next count")
    expect_equal(require_int(summary.get("park_now_count"), "park-now count"), 2, "park-now count")
    expect_equal(require_int(summary.get("use_selectively_count"), "use-selectively count"), 1, "use-selectively count")
    expect_equal(require_int(summary.get("guardrail_count"), "guardrail count"), 1, "guardrail count")
    expect_equal(require_int(summary.get("proof_size_comparable_rows"), "proof-size comparable rows"), 0, "proof-size comparable rows")
    expect_equal(require_int(summary.get("two_proof_frontier_typed_bytes"), "frontier"), TWO_PROOF_FRONTIER_TYPED_BYTES, "frontier")
    expect_equal(require_int(summary.get("nanozk_paper_reported_d128_block_proof_bytes"), "NANOZK row"), NANOZK_PAPER_REPORTED_D128_BLOCK_PROOF_BYTES, "NANOZK row")
    expect_equal(require_int(summary.get("strict_native_adapter_typed_bytes"), "strict native adapter typed"), STRICT_NATIVE_ADAPTER_TYPED_BYTES, "strict native adapter typed")
    expect_equal(require_int(summary.get("strict_native_adapter_gap_bytes"), "strict native adapter gap"), STRICT_NATIVE_ADAPTER_GAP_BYTES, "strict native adapter gap")
    expect_equal(require_int(summary.get("compact_selector_typed_bytes"), "compact selector typed"), COMPACT_SELECTOR_TYPED_BYTES, "compact selector typed")
    expect_equal(require_int(summary.get("compact_selector_gap_bytes"), "compact selector gap"), COMPACT_SELECTOR_GAP_BYTES, "compact selector gap")
    expect_equal(require_int(summary.get("post_tail_typed_bytes"), "post-tail typed"), POST_TAIL_TYPED_BYTES, "post-tail typed")
    expect_equal(require_int(summary.get("post_tail_gap_bytes"), "post-tail gap"), POST_TAIL_GAP_BYTES, "post-tail gap")
    expect_equal(require_int(summary.get("post_tail_label_span_bytes"), "post-tail label span"), POST_TAIL_LABEL_SPAN_BYTES, "post-tail label span")
    expect_equal(require_int(summary.get("gkr_smallest_width_preserving_bytes"), "GKR width-preserving bytes"), GKR_SMALLEST_WIDTH_PRESERVING_BYTES, "GKR width-preserving bytes")
    expect_equal(require_int(summary.get("mlp_fused_typed_bytes"), "MLP fused typed"), MLP_FUSED_TYPED_BYTES, "MLP fused typed")
    expect_equal(require_int(summary.get("mlp_fusion_typed_saving_bytes"), "MLP saving"), MLP_FUSION_TYPED_SAVING_BYTES, "MLP saving")
    expect_equal(summary.get("mlp_fusion_typed_saving_ratio"), MLP_FUSION_TYPED_SAVING_RATIO, "MLP saving ratio")
    expect_equal(require_int(summary.get("compact_preprocessed_typed_bytes"), "compact preprocessed typed"), COMPACT_PREPROCESSED_TYPED_BYTES, "compact preprocessed typed")
    expect_equal(summary.get("compact_preprocessed_vs_nanozk_ratio"), COMPACT_PREPROCESSED_VS_NANOZK_RATIO, "compact preprocessed ratio")

    routes = [require_dict(row, "route row") for row in require_list(payload.get("routes"), "routes")]
    expect_equal([require_str(row.get("route_id"), "route id") for row in routes], list(EXPECTED_ROUTE_IDS), "route order")
    for row in routes:
        if set(row) != set(ROW_COLUMNS) | {"non_claims"}:
            raise PivotSelectorError("route row key inventory drift")
        if require_bool(row.get("proof_size_comparable_to_nanozk"), "proof-size comparable"):
            raise PivotSelectorError("NANOZK proof-size comparability overclaim")
        row_non_claims = require_list(row.get("non_claims"), "route non-claims")
        if not set(NON_CLAIMS).issubset(set(row_non_claims)):
            raise PivotSelectorError("route missing non-claims")
    route_by_id = {row["route_id"]: row for row in routes}
    for route_id, (expected_evidence, expected_next_gate) in ROUTE_TEXT_EXPECTATIONS.items():
        row = route_by_id[route_id]
        expect_equal(
            require_str(row.get("primary_evidence"), f"{route_id} primary evidence"),
            expected_evidence,
            f"{route_id} primary evidence",
        )
        expect_equal(
            require_str(row.get("next_gate"), f"{route_id} next gate"),
            expected_next_gate,
            f"{route_id} next gate",
        )
    expect_equal(route_by_id[SELECTED_NEXT_ROUTE]["selector_status"], "ATTACK_NEXT", "selected route status")
    expect_equal(route_by_id[SELECTED_NEXT_ROUTE]["typed_bytes"], STRICT_NATIVE_ADAPTER_TYPED_BYTES, "selected route typed bytes")
    expect_equal(route_by_id[SELECTED_NEXT_ROUTE]["delta_vs_frontier_typed_bytes"], STRICT_NATIVE_ADAPTER_GAP_BYTES, "selected route frontier delta")
    selected_evidence = require_str(route_by_id[SELECTED_NEXT_ROUTE].get("primary_evidence"), "selected route evidence")
    expect_equal(selected_evidence, LARGER_NATIVE_BOUNDARY_EVIDENCE, "selected route evidence")
    expect_equal(route_by_id["sub_kilobyte_adapter_reorder"]["selector_status"], "PARK_NOW", "local reorder status")
    expect_equal(route_by_id["sub_kilobyte_adapter_reorder"]["typed_bytes"], POST_TAIL_TYPED_BYTES, "local reorder typed bytes")
    expect_equal(route_by_id["sub_kilobyte_adapter_reorder"]["delta_vs_frontier_typed_bytes"], POST_TAIL_GAP_BYTES, "local reorder frontier delta")
    expect_equal(route_by_id["current_gkr_projection_sidecar"]["selector_status"], "PARK_NOW", "GKR status")
    expect_equal(route_by_id["current_gkr_projection_sidecar"]["typed_bytes"], GKR_SMALLEST_WIDTH_PRESERVING_BYTES, "GKR typed bytes")
    expect_equal(
        route_by_id["current_gkr_projection_sidecar"]["delta_vs_frontier_typed_bytes"],
        GKR_SMALLEST_WIDTH_PRESERVING_BYTES - TWO_PROOF_FRONTIER_TYPED_BYTES,
        "GKR frontier delta",
    )
    expect_equal(route_by_id["compact_preprocessed_public_rows"]["selector_status"], "USE_SELECTIVELY", "compact preprocessed status")
    expect_equal(route_by_id["compact_preprocessed_public_rows"]["typed_bytes"], COMPACT_PREPROCESSED_TYPED_BYTES, "compact preprocessed route typed bytes")
    expect_equal(route_by_id["comparison_claim_guardrail"]["selector_status"], "GUARDRAIL", "guardrail status")

    interpretation = require_dict(payload.get("interpretation"), "interpretation")
    expect_equal(require_str(interpretation.get("human_read"), "human interpretation"), INTERPRETATION_HUMAN_READ, "human interpretation")
    expect_equal(
        require_str(interpretation.get("why_not_local_reorder"), "local reorder interpretation"),
        INTERPRETATION_WHY_NOT_LOCAL_REORDER,
        "local reorder interpretation",
    )
    expect_equal(
        require_str(interpretation.get("why_larger_boundary"), "larger boundary interpretation"),
        INTERPRETATION_WHY_LARGER_BOUNDARY,
        "larger boundary interpretation",
    )

    source_artifacts = [
        require_dict(row, "source artifact row")
        for row in require_list(payload.get("source_artifacts"), "source artifacts")
    ]
    expected_source_paths = [path.relative_to(ROOT).as_posix() for path in SOURCE_PATHS]
    actual_source_paths = [require_str(row.get("path"), "source path") for row in source_artifacts]
    expect_equal(actual_source_paths, expected_source_paths, "source artifact paths")
    if len(set(actual_source_paths)) != len(actual_source_paths):
        raise PivotSelectorError("duplicate source artifact path")
    if expected_source_artifacts is None:
        expected_source_artifacts = [
            require_dict(row, "expected source artifact row")
            for row in require_list(load_sources().get(SOURCE_ARTIFACTS_KEY), "expected source artifacts")
        ]
    expect_equal(source_artifacts, expected_source_artifacts, "source artifact descriptor")

    non_claims = require_list(payload.get("non_claims"), "non-claims")
    if not set(NON_CLAIMS).issubset(set(non_claims)):
        raise PivotSelectorError("payload missing non-claims")
    expect_equal(tuple(payload.get("validation_commands", ())), VALIDATION_COMMANDS, "validation command inventory")

    if final:
        mutation_results = [
            require_dict(row, "mutation result row")
            for row in require_list(payload.get("mutation_results"), "mutation results")
        ]
        expect_equal([row.get("name") for row in mutation_results], [name for name, _ in MUTATIONS], "mutation inventory")
        if not all(row.get("rejected") is True for row in mutation_results):
            raise PivotSelectorError("mutation inventory drift")
        expect_equal(require_int(payload.get("mutation_count"), "mutation count"), len(MUTATIONS), "mutation count")
        expect_equal(require_int(payload.get("mutations_rejected"), "mutations rejected"), len(MUTATIONS), "mutations rejected")


def mutate_promote_nanozk(payload: dict[str, Any]) -> None:
    payload["routes"][0]["proof_size_comparable_to_nanozk"] = True


def mutate_next_route_to_post_tail(payload: dict[str, Any]) -> None:
    payload["summary"]["selected_next_route"] = "sub_kilobyte_adapter_reorder"
    payload["routes"][0]["selector_status"] = "PARK_NOW"
    payload["routes"][1]["selector_status"] = "ATTACK_NEXT"


def mutate_unpark_gkr(payload: dict[str, Any]) -> None:
    payload["routes"][2]["selector_status"] = "ATTACK_NEXT"


def mutate_compact_gap_erased(payload: dict[str, Any]) -> None:
    payload["summary"]["compact_selector_gap_bytes"] = 0


def mutate_post_tail_no_go_erased(payload: dict[str, Any]) -> None:
    payload["routes"][1]["selector_status"] = "ATTACK_NEXT"
    payload["routes"][1]["typed_bytes"] = 40_000


def mutate_mlp_saving_erased(payload: dict[str, Any]) -> None:
    payload["summary"]["mlp_fusion_typed_saving_bytes"] = 0


def mutate_compact_preprocessed_overclaimed(payload: dict[str, Any]) -> None:
    payload["routes"][3]["next_gate"] = "compare directly to NANOZK block proof"
    payload["routes"][3]["proof_size_comparable_to_nanozk"] = True


def mutate_native_adapter_binding_demoted(payload: dict[str, Any]) -> None:
    payload["routes"][0]["primary_evidence"] = "ignore adapter binding and use the smaller statement artifact"


def mutate_nonselected_route_rationale_drift(payload: dict[str, Any]) -> None:
    payload["routes"][3]["primary_evidence"] = "compact preprocessed route is a matched NANOZK benchmark"


def mutate_route_next_gate_drift(payload: dict[str, Any]) -> None:
    payload["routes"][2]["next_gate"] = "reopen now and compare directly to external block proofs"


def mutate_source_descriptor_field_drift(payload: dict[str, Any]) -> None:
    payload["source_artifacts"][0]["sha256"] = "0" * 64


def mutate_remove_non_claim(payload: dict[str, Any]) -> None:
    payload["non_claims"] = payload["non_claims"][:-1]


def mutate_validation_command_drift(payload: dict[str, Any]) -> None:
    payload["validation_commands"] = payload["validation_commands"][:-1]


def mutate_source_path_drift(payload: dict[str, Any]) -> None:
    payload["source_artifacts"][0]["path"] = "docs/engineering/evidence/not-the-source.json"


def mutate_payload_commitment(payload: dict[str, Any]) -> None:
    payload["payload_commitment"] = "blake2b-256:" + "0" * 64


MUTATIONS: tuple[tuple[str, Callable[[dict[str, Any]], None]], ...] = (
    ("promote_nanozk_comparable", mutate_promote_nanozk),
    ("next_route_changed_to_post_tail", mutate_next_route_to_post_tail),
    ("gkr_unparked_without_new_backend", mutate_unpark_gkr),
    ("compact_selector_gap_erased", mutate_compact_gap_erased),
    ("post_tail_no_go_erased", mutate_post_tail_no_go_erased),
    ("mlp_fusion_saving_erased", mutate_mlp_saving_erased),
    ("compact_preprocessed_overclaimed", mutate_compact_preprocessed_overclaimed),
    ("native_adapter_binding_demoted", mutate_native_adapter_binding_demoted),
    ("nonselected_route_rationale_drift", mutate_nonselected_route_rationale_drift),
    ("route_next_gate_drift", mutate_route_next_gate_drift),
    ("source_descriptor_field_drift", mutate_source_descriptor_field_drift),
    ("non_claim_removed", mutate_remove_non_claim),
    ("validation_command_drift", mutate_validation_command_drift),
    ("source_descriptor_path_drift", mutate_source_path_drift),
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
            except PivotSelectorError as error:
                results.append({"name": name, "rejected": True, "error": str(error)})
            else:
                results.append({"name": name, "rejected": False, "error": "accepted"})
        else:
            mutated["mutation_results"] = []
            mutated["mutation_count"] = 0
            mutated["mutations_rejected"] = 0
            try:
                validate_payload(mutated, final=True, expected_source_artifacts=expected_source_artifacts)
            except PivotSelectorError as error:
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
    for row in payload["routes"]:
        writer.writerow({key: row[key] for key in ROW_COLUMNS})
    return output.getvalue()


def write_text(path: pathlib.Path, text: str) -> None:
    raw_path = path if path.is_absolute() else ROOT / path
    if raw_path.suffix not in {".json", ".tsv"}:
        raise PivotSelectorError(f"unsupported output suffix: {raw_path}")
    resolved_evidence = EVIDENCE_DIR.resolve(strict=False)
    resolved_path = raw_path.resolve(strict=False)
    try:
        resolved_path.relative_to(resolved_evidence)
    except ValueError as error:
        raise PivotSelectorError(f"output path must be under evidence dir: {raw_path}") from error

    cursor = raw_path
    while True:
        if cursor.is_symlink():
            raise PivotSelectorError(f"output path must not use a symlink: {cursor}")
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
                "mutation_count": payload["mutation_count"],
                "mutations_rejected": payload["mutations_rejected"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
