#!/usr/bin/env python3
"""Preflight the JSTprove/GKR dense-linear route before a d128 projection attempt."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import pathlib
import sys
from collections.abc import Callable
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"

JSON_OUT = EVIDENCE_DIR / "zkai-gkr-d128-projection-scaling-preflight-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-gkr-d128-projection-scaling-preflight-2026-05.tsv"

JSTPROVE_SHAPE_PROBE = EVIDENCE_DIR / "zkai-jstprove-shape-probe-2026-05.json"
STWO_GATE_VALUE_GATE = EVIDENCE_DIR / "zkai-d128-gate-value-compact-preprocessed-gate-2026-05.json"
MINIMAL_BLOCK = EVIDENCE_DIR / "zkai-minimal-transformer-block-benchmark-2026-05.json"
HYBRID_SELECTOR = EVIDENCE_DIR / "zkai-hybrid-proof-pressure-selector-2026-05.json"
TABLERO_BOUNDARY = EVIDENCE_DIR / "zkai-tablero-hybrid-zkml-boundary-2026-05.json"
SOURCE_PATHS = (JSTPROVE_SHAPE_PROBE, STWO_GATE_VALUE_GATE, MINIMAL_BLOCK, HYBRID_SELECTOR, TABLERO_BOUNDARY)

ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/663"
SCHEMA = "zkai-gkr-d128-projection-scaling-preflight-v1"
DECISION = "NO_GO_NOW_D128_PROJECTION_SCALING"
RESULT = "TINY_GEMM_SIGNAL_DOES_NOT_SURVIVE_WIDTH_PRESERVING_PREFLIGHT_KEEP_GKR_AS_BASELINE"
PAYLOAD_DOMAIN = "ptvm:zkai:gkr-d128-projection-scaling-preflight:v1"

EXPECTED_STWO_GATE_VALUE_TYPED_BYTES = 16_360
EXPECTED_STWO_DENSE_SUBSTITUTE_TYPED_BYTES = 22_576
EXPECTED_STWO_FRONTIER_TYPED_BYTES = 40_700
EXPECTED_NANOZK_REPORTED_BYTES = 6_900
EXPECTED_D128_GATE_VALUE_ROWS = 131_072
EXPECTED_LARGEST_CHECKED_GKR_DIM = 4
EXPECTED_JSTPROVE_TINY_GEMM_BYTES = 11_645
EXPECTED_JSTPROVE_DIM_1_BYTES = 11_726
EXPECTED_JSTPROVE_DIM_2_BYTES = 71_040
EXPECTED_JSTPROVE_DIM_4_BYTES = 70_138

NON_CLAIMS = (
    "not a NANOZK proof-size win",
    "not a matched d128 JSTprove projection proof",
    "not a claim that GKR replaces Stwo",
    "not a full transformer block proof",
    "not a proof-size-comparable cross-system benchmark",
    "not a timing claim beyond source artifact timing fields",
    "not production zkML",
)

VALIDATION_COMMANDS = (
    "python3 scripts/zkai_gkr_d128_projection_scaling_preflight_gate.py --write-json docs/engineering/evidence/zkai-gkr-d128-projection-scaling-preflight-2026-05.json --write-tsv docs/engineering/evidence/zkai-gkr-d128-projection-scaling-preflight-2026-05.tsv",
    "python3 -m py_compile scripts/zkai_gkr_d128_projection_scaling_preflight_gate.py scripts/tests/test_zkai_gkr_d128_projection_scaling_preflight_gate.py",
    "python3 -m unittest scripts.tests.test_zkai_gkr_d128_projection_scaling_preflight_gate",
    "python3 scripts/research_issue_lint.py --repo-root .",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

ROW_COLUMNS = (
    "row_id",
    "proof_system",
    "object_class",
    "workload",
    "primary_metric",
    "primary_value",
    "ratio_vs_stwo_gate_value",
    "ratio_vs_stwo_dense_substitute",
    "ratio_vs_nanozk_context",
    "matched_workload",
    "proof_size_comparable",
    "source_status",
    "recommendation",
)
ROW_FIELDS = (*ROW_COLUMNS, "source_artifact", "non_claims")

REQUIRED_ROW_NON_CLAIMS = {
    "local_stwo_d128_gate_value_projection": ("typed local accounting, not external proof bytes",),
    "local_stwo_d128_rmsnorm_mlp_substitute": ("not exact LayerNorm/GELU transformer MLP",),
    "jstprove_tiny_gemm_scalar": ("tiny scalar fixture, not d128 and not width-preserving d128 projection",),
    "jstprove_width_preserving_gemm_dim_1": ("dimension sweep is not d128 and not a matched workload",),
    "jstprove_width_preserving_gemm_dim_2": ("dimension sweep is not d128 and not a matched workload",),
    "jstprove_width_preserving_gemm_dim_4": ("dimension sweep is not d128 and not a matched workload",),
    "tablero_statement_boundary_guardrail": ("not a proof object",),
    "hybrid_selector_prior_attack_next": ("selector route is a hypothesis, not proof-size evidence",),
}


class GkrProjectionPreflightError(ValueError):
    pass


def canonical_json(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def commitment(data: dict[str, Any]) -> str:
    material = copy.deepcopy(data)
    material.pop("payload_commitment", None)
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("ascii"))
    digest.update(b"\0")
    digest.update(canonical_json(material))
    return f"blake2b-256:{digest.hexdigest()}"


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GkrProjectionPreflightError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise GkrProjectionPreflightError(f"{label} must be a list")
    return value


def require_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise GkrProjectionPreflightError(f"{label} must be an integer")
    return value


def require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise GkrProjectionPreflightError(f"{label} must be a boolean")
    return value


def require_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise GkrProjectionPreflightError(f"{label} must be a non-empty string")
    return value


def expect_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise GkrProjectionPreflightError(f"{label} drift: expected {expected!r}, got {actual!r}")


def ratio_string(numerator: int | None, denominator: int | None) -> str:
    if numerator is None or denominator is None:
        return "NA"
    if denominator <= 0:
        raise GkrProjectionPreflightError("ratio denominator must be positive")
    return f"{numerator / denominator:.6f}"


def load_json(path: pathlib.Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise GkrProjectionPreflightError(f"{path} must contain a JSON object")
    return data, raw


def source_descriptor(path: pathlib.Path, data: dict[str, Any], raw: bytes) -> dict[str, Any]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "schema": data.get("schema"),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def load_sources() -> dict[str, dict[str, Any]]:
    loaded: dict[str, dict[str, Any]] = {}
    raws: dict[str, bytes] = {}
    for key, path in (
        ("shape", JSTPROVE_SHAPE_PROBE),
        ("stwo_gate", STWO_GATE_VALUE_GATE),
        ("minimal", MINIMAL_BLOCK),
        ("selector", HYBRID_SELECTOR),
        ("tablero", TABLERO_BOUNDARY),
    ):
        loaded[key], raws[key] = load_json(path)
    expect_equal(loaded["shape"].get("schema"), "zkai-jstprove-shape-probe-v1", "shape schema")
    expect_equal(loaded["stwo_gate"].get("schema"), "zkai-d128-gate-value-compact-preprocessed-gate-v1", "Stwo gate schema")
    expect_equal(loaded["minimal"].get("schema"), "zkai-minimal-transformer-block-benchmark-v1", "minimal schema")
    expect_equal(loaded["selector"].get("schema"), "zkai-hybrid-proof-pressure-selector-v1", "selector schema")
    expect_equal(loaded["tablero"].get("schema"), "zkai-tablero-hybrid-zkml-boundary-v1", "Tablero schema")
    loaded["raw"] = raws  # type: ignore[assignment]
    return loaded


def result_by_fixture(results: list[Any], fixture: str) -> dict[str, Any]:
    for row in results:
        if isinstance(row, dict) and row.get("fixture") == fixture:
            return row
    raise GkrProjectionPreflightError(f"fixture missing: {fixture}")


def sweep_by_dimension(rows: list[Any], dimension: int) -> dict[str, Any]:
    for row in rows:
        if isinstance(row, dict) and row.get("dimension") == dimension:
            return row
    raise GkrProjectionPreflightError(f"dimension sweep row missing: {dimension}")


def component_by_name(rows: list[Any], component: str) -> dict[str, Any]:
    for row in rows:
        if isinstance(row, dict) and row.get("component") == component:
            return row
    raise GkrProjectionPreflightError(f"component row missing: {component}")


def route(
    *,
    row_id: str,
    proof_system: str,
    object_class: str,
    workload: str,
    primary_metric: str,
    primary_value: int | None,
    matched_workload: bool,
    proof_size_comparable: bool,
    source_status: str,
    recommendation: str,
    source_artifact: pathlib.Path,
    non_claims: tuple[str, ...],
) -> dict[str, Any]:
    ratio_value = primary_value if "bytes" in primary_metric else None
    return {
        "row_id": row_id,
        "proof_system": proof_system,
        "object_class": object_class,
        "workload": workload,
        "primary_metric": primary_metric,
        "primary_value": primary_value,
        "ratio_vs_stwo_gate_value": ratio_string(ratio_value, EXPECTED_STWO_GATE_VALUE_TYPED_BYTES),
        "ratio_vs_stwo_dense_substitute": ratio_string(ratio_value, EXPECTED_STWO_DENSE_SUBSTITUTE_TYPED_BYTES),
        "ratio_vs_nanozk_context": ratio_string(ratio_value, EXPECTED_NANOZK_REPORTED_BYTES),
        "matched_workload": matched_workload,
        "proof_size_comparable": proof_size_comparable,
        "source_status": source_status,
        "recommendation": recommendation,
        "source_artifact": source_artifact.relative_to(ROOT).as_posix(),
        "non_claims": list(dict.fromkeys((*non_claims, *NON_CLAIMS))),
    }


def validate_source_numbers(sources: dict[str, dict[str, Any]]) -> None:
    stwo_aggregate = require_dict(sources["stwo_gate"].get("aggregate"), "Stwo gate aggregate")
    minimal_summary = require_dict(sources["minimal"].get("summary"), "minimal summary")
    selector_summary = require_dict(sources["selector"].get("summary"), "selector summary")
    shape_results = require_list(sources["shape"].get("results"), "shape results")
    shape_sweep = require_list(sources["shape"].get("dimension_sweep"), "dimension sweep")

    expect_equal(require_int(stwo_aggregate.get("baseline_local_typed_bytes"), "Stwo gate typed bytes"), EXPECTED_STWO_GATE_VALUE_TYPED_BYTES, "Stwo gate typed bytes")
    expect_equal(require_int(stwo_aggregate.get("row_count"), "Stwo gate row count"), EXPECTED_D128_GATE_VALUE_ROWS, "Stwo gate row count")
    expect_equal(require_int(minimal_summary.get("two_proof_frontier_typed_bytes"), "Stwo frontier typed bytes"), EXPECTED_STWO_FRONTIER_TYPED_BYTES, "Stwo frontier typed bytes")
    expect_equal(require_int(minimal_summary.get("nanozk_reported_d128_block_proof_bytes"), "NANOZK reported bytes"), EXPECTED_NANOZK_REPORTED_BYTES, "NANOZK reported bytes")
    expect_equal(require_bool(minimal_summary.get("missing_native_block_proof_object"), "missing native block flag"), True, "missing native block flag")
    expect_equal(require_int(selector_summary.get("proof_size_comparable_rows"), "selector comparable rows"), 0, "selector comparable rows")
    expect_equal(require_int(result_by_fixture(shape_results, "tiny_gemm").get("proof_bytes"), "tiny Gemm proof bytes"), EXPECTED_JSTPROVE_TINY_GEMM_BYTES, "tiny Gemm proof bytes")
    expect_equal(require_int(sweep_by_dimension(shape_sweep, 1).get("proof_bytes"), "dim1 proof bytes"), EXPECTED_JSTPROVE_DIM_1_BYTES, "dim1 proof bytes")
    expect_equal(require_int(sweep_by_dimension(shape_sweep, 2).get("proof_bytes"), "dim2 proof bytes"), EXPECTED_JSTPROVE_DIM_2_BYTES, "dim2 proof bytes")
    expect_equal(require_int(sweep_by_dimension(shape_sweep, 4).get("proof_bytes"), "dim4 proof bytes"), EXPECTED_JSTPROVE_DIM_4_BYTES, "dim4 proof bytes")


def build_rows(sources: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    validate_source_numbers(sources)
    stwo_aggregate = require_dict(sources["stwo_gate"].get("aggregate"), "Stwo gate aggregate")
    minimal_rows = require_list(sources["minimal"].get("component_rows"), "minimal component rows")
    shape_results = require_list(sources["shape"].get("results"), "shape results")
    shape_sweep = require_list(sources["shape"].get("dimension_sweep"), "dimension sweep")
    dense_substitute = component_by_name(minimal_rows, "rmsnorm_mlp_residual_substitute")
    tablero_summary = require_dict(sources["tablero"].get("summary"), "Tablero summary")
    selector_summary = require_dict(sources["selector"].get("summary"), "selector summary")

    rows = [
        route(
            row_id="local_stwo_d128_gate_value_projection",
            proof_system="Stwo/STARK",
            object_class="local_native_stwo_d128_projection_proof",
            workload="d128 gate/value projection, 131072 multiplication rows",
            primary_metric="typed_proof_field_bytes",
            primary_value=require_int(stwo_aggregate.get("baseline_local_typed_bytes"), "Stwo gate typed bytes"),
            matched_workload=False,
            proof_size_comparable=False,
            source_status="local_checked",
            recommendation="keep_as_local_dense_projection_baseline",
            source_artifact=STWO_GATE_VALUE_GATE,
            non_claims=("typed local accounting, not external proof bytes",),
        ),
        route(
            row_id="local_stwo_d128_rmsnorm_mlp_substitute",
            proof_system="Stwo/STARK",
            object_class=require_str(dense_substitute.get("object_class"), "dense substitute object class"),
            workload="d128 RMSNorm/SwiGLU/down/residual substitute fused component",
            primary_metric=require_str(dense_substitute.get("primary_metric"), "dense substitute metric"),
            primary_value=require_int(dense_substitute.get("primary_value"), "dense substitute bytes"),
            matched_workload=False,
            proof_size_comparable=False,
            source_status="local_checked",
            recommendation="context_for_dense_substitute_not_matched_gkr_workload",
            source_artifact=MINIMAL_BLOCK,
            non_claims=("not exact LayerNorm/GELU transformer MLP",),
        ),
        route(
            row_id="jstprove_tiny_gemm_scalar",
            proof_system="JSTprove/Remainder-GKR",
            object_class="tiny_scalar_gemm_fixture",
            workload="tiny Gemm, input width 2 to scalar output",
            primary_metric="proof_bytes",
            primary_value=require_int(result_by_fixture(shape_results, "tiny_gemm").get("proof_bytes"), "tiny Gemm proof bytes"),
            matched_workload=False,
            proof_size_comparable=False,
            source_status="local_checked_external_tool_artifact",
            recommendation="do_not_promote_tiny_scalar_signal_to_d128_projection",
            source_artifact=JSTPROVE_SHAPE_PROBE,
            non_claims=("tiny scalar fixture, not d128 and not width-preserving d128 projection",),
        ),
    ]
    for dimension in (1, 2, 4):
        row = sweep_by_dimension(shape_sweep, dimension)
        rows.append(
            route(
                row_id=f"jstprove_width_preserving_gemm_dim_{dimension}",
                proof_system="JSTprove/Remainder-GKR",
                object_class="width_preserving_gemm_dimension_sweep",
                workload=f"width-preserving Gemm dim {dimension}",
                primary_metric="proof_bytes",
                primary_value=require_int(row.get("proof_bytes"), f"dim{dimension} proof bytes"),
                matched_workload=False,
                proof_size_comparable=False,
                source_status="local_checked_external_tool_artifact",
                recommendation="no_go_now_for_jstprove_d128_projection_scaling" if dimension in (2, 4) else "context_too_small_for_d128_projection",
                source_artifact=JSTPROVE_SHAPE_PROBE,
                non_claims=("dimension sweep is not d128 and not a matched workload",),
            )
        )
    rows.append(
        route(
            row_id="tablero_statement_boundary_guardrail",
            proof_system="Tablero statement boundary",
            object_class="typed_statement_boundary",
            workload="bind hybrid route claims without proof-object equivalence",
            primary_metric="boundary_example_count",
            primary_value=require_int(tablero_summary.get("boundary_example_count"), "Tablero boundary count"),
            matched_workload=False,
            proof_size_comparable=False,
            source_status="local_checked_statement_boundary",
            recommendation="keep_for_claim_binding_not_proof_size_comparison",
            source_artifact=TABLERO_BOUNDARY,
            non_claims=("not a proof object",),
        )
    )
    rows.append(
        route(
            row_id="hybrid_selector_prior_attack_next",
            proof_system="route selector",
            object_class="prior_route_recommendation",
            workload="hybrid selector before d128 projection preflight",
            primary_metric="attack_next_count",
            primary_value=require_int(selector_summary.get("attack_next_count"), "selector attack-next count"),
            matched_workload=False,
            proof_size_comparable=False,
            source_status="local_checked_selector",
            recommendation="narrow_jstprove_dense_route_after_width_preserving_preflight",
            source_artifact=HYBRID_SELECTOR,
            non_claims=("selector route is a hypothesis, not proof-size evidence",),
        )
    )
    return rows


def row_by_id(rows: list[dict[str, Any]], row_id: str) -> dict[str, Any]:
    for row in rows:
        if row["row_id"] == row_id:
            return row
    raise GkrProjectionPreflightError(f"row missing: {row_id}")


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tiny = row_by_id(rows, "jstprove_tiny_gemm_scalar")
    dim2 = row_by_id(rows, "jstprove_width_preserving_gemm_dim_2")
    dim4 = row_by_id(rows, "jstprove_width_preserving_gemm_dim_4")
    width_preserving_values = [
        require_int(dim2.get("primary_value"), "dim2 proof bytes"),
        require_int(dim4.get("primary_value"), "dim4 proof bytes"),
    ]
    smallest_width_preserving = min(width_preserving_values)
    return {
        "decision_reason": "dim2_dim4_width_preserving_jstprove_gemm_already_exceeds_local_stwo_d128_gate_value_baseline",
        "local_stwo_d128_gate_value_typed_bytes": EXPECTED_STWO_GATE_VALUE_TYPED_BYTES,
        "local_stwo_dense_substitute_typed_bytes": EXPECTED_STWO_DENSE_SUBSTITUTE_TYPED_BYTES,
        "local_stwo_two_proof_frontier_typed_bytes": EXPECTED_STWO_FRONTIER_TYPED_BYTES,
        "nanozk_paper_reported_d128_block_proof_bytes": EXPECTED_NANOZK_REPORTED_BYTES,
        "d128_gate_value_row_count": EXPECTED_D128_GATE_VALUE_ROWS,
        "jstprove_tiny_gemm_scalar_proof_bytes": require_int(tiny.get("primary_value"), "tiny proof bytes"),
        "jstprove_dim2_width_preserving_gemm_proof_bytes": require_int(dim2.get("primary_value"), "dim2 proof bytes"),
        "jstprove_dim4_width_preserving_gemm_proof_bytes": require_int(dim4.get("primary_value"), "dim4 proof bytes"),
        "smallest_width_preserving_gkr_proof_bytes": smallest_width_preserving,
        "tiny_scalar_vs_stwo_gate_value_ratio": ratio_string(require_int(tiny.get("primary_value"), "tiny proof bytes"), EXPECTED_STWO_GATE_VALUE_TYPED_BYTES),
        "smallest_width_preserving_vs_stwo_gate_value_ratio": ratio_string(smallest_width_preserving, EXPECTED_STWO_GATE_VALUE_TYPED_BYTES),
        "smallest_width_preserving_vs_stwo_dense_substitute_ratio": ratio_string(smallest_width_preserving, EXPECTED_STWO_DENSE_SUBSTITUTE_TYPED_BYTES),
        "smallest_width_preserving_vs_nanozk_context_ratio": ratio_string(smallest_width_preserving, EXPECTED_NANOZK_REPORTED_BYTES),
        "largest_checked_gkr_dimension": EXPECTED_LARGEST_CHECKED_GKR_DIM,
        "d128_width_target": 128,
        "width_gap_from_largest_checked_gkr_dim_to_d128": 128 // EXPECTED_LARGEST_CHECKED_GKR_DIM,
        "proof_size_comparable_rows": sum(1 for row in rows if row["proof_size_comparable"]),
        "recommendation": "do_not_spend_next_pr_on_jstprove_d128_projection_without_live_dim8_16_32_sweep_or_new_gkr_backend",
        "attack_next_after_preflight": [
            "native_d128_block_object_blocker",
            "optional_live_gkr_dim8_16_32_sweep_if_jstprove_binary_available",
        ],
        "no_go_now_after_preflight": [
            "jstprove_d128_projection_scaling_from_current_dim_sweep",
        ],
    }


def source_artifacts(sources: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    raws = require_dict(sources["raw"], "raw source inventory")
    return [
        source_descriptor(JSTPROVE_SHAPE_PROBE, sources["shape"], raws["shape"]),
        source_descriptor(STWO_GATE_VALUE_GATE, sources["stwo_gate"], raws["stwo_gate"]),
        source_descriptor(MINIMAL_BLOCK, sources["minimal"], raws["minimal"]),
        source_descriptor(HYBRID_SELECTOR, sources["selector"], raws["selector"]),
        source_descriptor(TABLERO_BOUNDARY, sources["tablero"], raws["tablero"]),
    ]


def base_payload(sources: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    sources = sources or load_sources()
    rows = build_rows(sources)
    return {
        "schema": SCHEMA,
        "issue": ISSUE,
        "decision": DECISION,
        "result": RESULT,
        "summary": build_summary(rows),
        "rows": rows,
        "source_artifacts": source_artifacts(sources),
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }


def validate_row(row: dict[str, Any]) -> None:
    if set(row) != set(ROW_FIELDS):
        raise GkrProjectionPreflightError("row field drift")
    row_id = require_str(row["row_id"], "row id")
    require_str(row["proof_system"], f"{row_id} proof system")
    require_str(row["object_class"], f"{row_id} object class")
    require_str(row["workload"], f"{row_id} workload")
    require_str(row["primary_metric"], f"{row_id} primary metric")
    if row["primary_value"] is not None:
        require_int(row["primary_value"], f"{row_id} primary value")
    require_bool(row["matched_workload"], f"{row_id} matched workload")
    proof_size_comparable = require_bool(row["proof_size_comparable"], f"{row_id} proof comparable")
    require_str(row["source_status"], f"{row_id} source status")
    require_str(row["recommendation"], f"{row_id} recommendation")
    require_str(row["source_artifact"], f"{row_id} source artifact")
    if not isinstance(row["non_claims"], list) or not set(NON_CLAIMS).issubset(set(row["non_claims"])):
        raise GkrProjectionPreflightError(f"{row_id} non-claim inventory drift")
    row_non_claims = set(row["non_claims"])
    required_row_non_claims = REQUIRED_ROW_NON_CLAIMS.get(row_id)
    if required_row_non_claims is None:
        raise GkrProjectionPreflightError(f"{row_id} required row non-claim inventory missing")
    if not set(required_row_non_claims).issubset(row_non_claims):
        raise GkrProjectionPreflightError(f"{row_id} row-specific non-claim inventory drift")
    if proof_size_comparable:
        raise GkrProjectionPreflightError(f"{row_id} proof-size comparability overclaim")
    if row["matched_workload"]:
        raise GkrProjectionPreflightError(f"{row_id} matched workload overclaim")


def validate_payload(payload: dict[str, Any], *, final: bool = True, sources: dict[str, dict[str, Any]] | None = None) -> None:
    expect_equal(payload.get("schema"), SCHEMA, "schema")
    expect_equal(payload.get("issue"), ISSUE, "issue")
    expect_equal(payload.get("decision"), DECISION, "decision")
    expect_equal(payload.get("result"), RESULT, "result")
    expect_equal(payload.get("non_claims"), list(NON_CLAIMS), "global non-claims")
    expect_equal(payload.get("validation_commands"), list(VALIDATION_COMMANDS), "validation commands")
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != 8:
        raise GkrProjectionPreflightError("row inventory drift")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise GkrProjectionPreflightError("row must be an object")
        validate_row(row)
        if row["row_id"] in seen:
            raise GkrProjectionPreflightError("duplicate row id")
        seen.add(row["row_id"])
    summary = require_dict(payload.get("summary"), "summary")
    expect_equal(summary.get("proof_size_comparable_rows"), 0, "summary comparable rows")
    expect_equal(summary.get("recommendation"), "do_not_spend_next_pr_on_jstprove_d128_projection_without_live_dim8_16_32_sweep_or_new_gkr_backend", "summary recommendation")
    if require_int(summary.get("smallest_width_preserving_gkr_proof_bytes"), "width-preserving proof bytes") <= EXPECTED_STWO_GATE_VALUE_TYPED_BYTES:
        raise GkrProjectionPreflightError("width-preserving GKR route promoted")
    if not isinstance(payload.get("source_artifacts"), list) or len(payload["source_artifacts"]) != len(SOURCE_PATHS):
        raise GkrProjectionPreflightError("source artifact inventory drift")
    sources = sources or load_sources()
    expected = base_payload(sources)
    for key in ("summary", "rows", "source_artifacts"):
        if payload.get(key) != expected[key]:
            raise GkrProjectionPreflightError(f"{key} drift")
    if "mutation_results" in payload:
        mutation_results = payload["mutation_results"]
        if not isinstance(mutation_results, list) or len(mutation_results) != len(MUTATIONS):
            raise GkrProjectionPreflightError("mutation result drift")
        expected_names = [name for name, _ in MUTATIONS]
        actual_names = [require_str(result.get("name"), "mutation name") for result in mutation_results if isinstance(result, dict)]
        if actual_names != expected_names:
            raise GkrProjectionPreflightError("mutation result drift")
        rejected = sum(1 for result in mutation_results if isinstance(result, dict) and result.get("rejected") is True)
        if payload.get("mutation_count") != len(MUTATIONS) or payload.get("mutations_rejected") != rejected:
            raise GkrProjectionPreflightError("mutation count drift")
        if rejected != len(MUTATIONS):
            raise GkrProjectionPreflightError("mutation rejection drift")
    if final:
        expected_commitment = payload.get("payload_commitment")
        if not isinstance(expected_commitment, str):
            raise GkrProjectionPreflightError("payload commitment missing")
        if expected_commitment != commitment(payload):
            raise GkrProjectionPreflightError("payload commitment drift")


def mutate_promote_tiny_gemm(payload: dict[str, Any]) -> None:
    row_by_id(payload["rows"], "jstprove_tiny_gemm_scalar")["matched_workload"] = True


def mutate_promote_dim4_comparable(payload: dict[str, Any]) -> None:
    row_by_id(payload["rows"], "jstprove_width_preserving_gemm_dim_4")["proof_size_comparable"] = True


def mutate_width_preserving_bytes(payload: dict[str, Any]) -> None:
    row_by_id(payload["rows"], "jstprove_width_preserving_gemm_dim_4")["primary_value"] = 6_899


def mutate_recommendation(payload: dict[str, Any]) -> None:
    payload["summary"]["recommendation"] = "attack_jstprove_d128_projection_now"


def mutate_remove_non_claim(payload: dict[str, Any]) -> None:
    payload["non_claims"].remove("not a proof-size-comparable cross-system benchmark")


def mutate_remove_width_preserving_non_claim(payload: dict[str, Any]) -> None:
    non_claims = row_by_id(payload["rows"], "jstprove_width_preserving_gemm_dim_4")["non_claims"]
    non_claims.remove("dimension sweep is not d128 and not a matched workload")


def mutate_source_digest(payload: dict[str, Any]) -> None:
    payload["source_artifacts"][0]["sha256"] = "0" * 64


MUTATIONS: tuple[tuple[str, Callable[[dict[str, Any]], None]], ...] = (
    ("promote_tiny_gemm", mutate_promote_tiny_gemm),
    ("promote_dim4_comparable", mutate_promote_dim4_comparable),
    ("width_preserving_bytes_smuggling", mutate_width_preserving_bytes),
    ("recommendation_overclaim", mutate_recommendation),
    ("remove_non_claim", mutate_remove_non_claim),
    ("remove_width_preserving_non_claim", mutate_remove_width_preserving_non_claim),
    ("source_digest_drift", mutate_source_digest),
)


def run_mutations(payload: dict[str, Any], sources: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for name, mutate in MUTATIONS:
        candidate = copy.deepcopy(payload)
        mutate(candidate)
        try:
            validate_payload(candidate, final=False, sources=sources)
        except GkrProjectionPreflightError as err:
            results.append({"name": name, "rejected": True, "reason": str(err)})
        else:
            results.append({"name": name, "rejected": False, "reason": "mutation accepted"})
    return results


def build_payload() -> dict[str, Any]:
    sources = load_sources()
    payload = base_payload(sources)
    mutation_results = run_mutations(payload, sources)
    payload["mutation_results"] = mutation_results
    payload["mutation_count"] = len(mutation_results)
    payload["mutations_rejected"] = sum(1 for result in mutation_results if result["rejected"])
    payload["payload_commitment"] = commitment(payload)
    validate_payload(payload, sources=sources)
    return payload


def tsv_text(payload: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=ROW_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in payload["rows"]:
        writer.writerow({column: row[column] for column in ROW_COLUMNS})
    return output.getvalue()


def require_output_path(path: pathlib.Path | None, suffix: str, label: str) -> pathlib.Path | None:
    if path is None:
        return None
    resolved = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    evidence_root = EVIDENCE_DIR.resolve()
    if evidence_root not in resolved.parents:
        raise GkrProjectionPreflightError(f"{label} output must stay under {EVIDENCE_DIR.relative_to(ROOT).as_posix()}")
    if resolved.suffix != suffix:
        raise GkrProjectionPreflightError(f"{label} output must use {suffix}")
    if resolved in {path.resolve() for path in SOURCE_PATHS}:
        raise GkrProjectionPreflightError(f"{label} output cannot overwrite a source artifact")
    return resolved


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path | None, tsv_path: pathlib.Path | None) -> None:
    json_path = require_output_path(json_path, ".json", "JSON")
    tsv_path = require_output_path(tsv_path, ".tsv", "TSV")
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = json_path.with_suffix(json_path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(json_path)
    if tsv_path is not None:
        tsv_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = tsv_path.with_suffix(tsv_path.suffix + ".tmp")
        tmp.write_text(tsv_text(payload), encoding="utf-8")
        tmp.replace(tsv_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    args = parser.parse_args()
    payload = build_payload()
    write_outputs(payload, args.write_json, args.write_tsv)
    print(
        json.dumps(
            {
                "decision": payload["decision"],
                "result": payload["result"],
                "rows": len(payload["rows"]),
                "mutations_rejected": payload["mutations_rejected"],
                "tiny_scalar_vs_stwo_gate_value_ratio": payload["summary"]["tiny_scalar_vs_stwo_gate_value_ratio"],
                "smallest_width_preserving_vs_stwo_gate_value_ratio": payload["summary"][
                    "smallest_width_preserving_vs_stwo_gate_value_ratio"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
