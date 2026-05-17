#!/usr/bin/env python3
"""Select the next zkML proof-pressure route without cross-system overclaims."""

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
JSON_OUT = EVIDENCE_DIR / "zkai-hybrid-proof-pressure-selector-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-hybrid-proof-pressure-selector-2026-05.tsv"

ISSUE_URL = "https://github.com/omarespejel/provable-transformer-vm/issues/661"
SCHEMA = "zkai-hybrid-proof-pressure-selector-v1"
DECISION = "GO_HYBRID_PROOF_PRESSURE_SELECTOR_NO_GO_MATCHED_EXTERNAL_COMPARISON"
RESULT = "ROUTE_SELECTOR_IDENTIFIES_DENSE_LINEAR_ATTACK_AND_REJECTS_FALSE_COMPARABILITY"

CLAIM_AUDIT = EVIDENCE_DIR / "zkai-claim-audit-comparison-artifacts-2026-05.json"
GKR_BASELINE = EVIDENCE_DIR / "zkai-gkr-dense-sidecar-baseline-2026-05.json"
MINIMAL_BLOCK = EVIDENCE_DIR / "zkai-minimal-transformer-block-benchmark-2026-05.json"
JOLT_ATLAS = EVIDENCE_DIR / "zkai-jolt-atlas-lookup-tensor-comparison-2026-05.json"
TABLERO_BOUNDARY = EVIDENCE_DIR / "zkai-tablero-hybrid-zkml-boundary-2026-05.json"

EXPECTED_STWO_FRONTIER_TYPED_BYTES = 40_700
EXPECTED_NANOZK_REPORTED_BYTES = 6_900
EXPECTED_STWO_DENSE_SUBSTITUTE_TYPED_BYTES = 22_576
EXPECTED_GKR_TINY_GEMM_BYTES = 11_645
EXPECTED_GKR_RESIDUAL_ADD_BYTES = 56_054
EXPECTED_GKR_LAYERNORM_BYTES = 52_080
EXPECTED_CLAIM_AUDIT_COMPARABLE_ROWS = 0
EXPECTED_CLAIM_AUDIT_MUTATIONS = 16
EXPECTED_ROUTE_IDS = {
    "local_stwo_two_proof_frontier",
    "gkr_dense_linear_scaling_candidate",
    "gkr_residual_add_no_go_now",
    "gkr_layernorm_no_go_now",
    "native_d128_block_object_blocker",
    "tablero_statement_boundary_guardrail",
    "nanozk_paper_context_only",
    "jolt_atlas_lookup_tensor_context",
}
SOURCE_ARTIFACT_PATHS = {
    CLAIM_AUDIT.relative_to(ROOT).as_posix(),
    GKR_BASELINE.relative_to(ROOT).as_posix(),
    MINIMAL_BLOCK.relative_to(ROOT).as_posix(),
    JOLT_ATLAS.relative_to(ROOT).as_posix(),
    TABLERO_BOUNDARY.relative_to(ROOT).as_posix(),
}

NON_CLAIMS = (
    "not a NANOZK proof-size win",
    "not a matched local reproduction of NANOZK",
    "not evidence that GKR replaces STARKs",
    "not a full transformer block proof",
    "not a timing claim",
    "not production zkML",
)

ROW_COLUMNS = (
    "route_id",
    "proof_system",
    "object_class",
    "primary_metric",
    "primary_pressure",
    "ratio_vs_stwo_frontier",
    "ratio_vs_nanozk_context",
    "matched_workload",
    "native_equivalent",
    "proof_size_comparable",
    "selector_decision",
    "next_action",
)

ROW_FIELDS = (*ROW_COLUMNS, "source_artifact", "non_claims")

VALIDATION_COMMANDS = (
    "python3 scripts/zkai_hybrid_proof_pressure_selector_gate.py --write-json docs/engineering/evidence/zkai-hybrid-proof-pressure-selector-2026-05.json --write-tsv docs/engineering/evidence/zkai-hybrid-proof-pressure-selector-2026-05.tsv",
    "python3 -m py_compile scripts/zkai_hybrid_proof_pressure_selector_gate.py scripts/tests/test_zkai_hybrid_proof_pressure_selector_gate.py",
    "python3 -m unittest scripts.tests.test_zkai_hybrid_proof_pressure_selector_gate",
    "python3 scripts/research_issue_lint.py --repo-root .",
    "git diff --check",
    "just gate-fast",
    "just gate",
)


class HybridSelectorError(Exception):
    pass


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def commitment(data: Any) -> str:
    return "blake2b-256:" + hashlib.blake2b(canonical_json(data).encode("utf-8"), digest_size=32).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise HybridSelectorError(f"{path} must contain a JSON object")
    return data


def require_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise HybridSelectorError(f"{label} must be an integer")
    return value


def require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise HybridSelectorError(f"{label} must be a boolean")
    return value


def require_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise HybridSelectorError(f"{label} must be a non-empty string")
    return value


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HybridSelectorError(f"{label} must be an object")
    return value


def require_dict_list(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise HybridSelectorError(f"{label} must be a list")
    if any(not isinstance(item, dict) for item in value):
        raise HybridSelectorError(f"{label} entries must be objects")
    return value


def expect_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise HybridSelectorError(f"{label} drift: expected {expected!r}, got {actual!r}")


def ratio_string(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        raise HybridSelectorError("ratio denominator must be positive")
    return f"{numerator / denominator:.6f}"


def source_descriptor(path: pathlib.Path) -> dict[str, Any]:
    raw = path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise HybridSelectorError(f"{path} must contain a JSON object")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "schema": data.get("schema"),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def row_by_id(rows: list[dict[str, Any]], row_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("row_id") == row_id or row.get("statement_id") == row_id or row.get("route_id") == row_id:
            return row
    raise HybridSelectorError(f"missing source row: {row_id}")


def route(
    *,
    route_id: str,
    proof_system: str,
    object_class: str,
    primary_metric: str,
    primary_pressure: int | None,
    ratio_vs_stwo_frontier: str,
    ratio_vs_nanozk_context: str,
    matched_workload: bool,
    native_equivalent: bool,
    proof_size_comparable: bool,
    selector_decision: str,
    next_action: str,
    source_artifact: pathlib.Path,
    non_claims: tuple[str, ...],
) -> dict[str, Any]:
    row_non_claims = list(dict.fromkeys((*non_claims, *NON_CLAIMS)))
    return {
        "route_id": route_id,
        "proof_system": proof_system,
        "object_class": object_class,
        "primary_metric": primary_metric,
        "primary_pressure": primary_pressure,
        "ratio_vs_stwo_frontier": ratio_vs_stwo_frontier,
        "ratio_vs_nanozk_context": ratio_vs_nanozk_context,
        "matched_workload": matched_workload,
        "native_equivalent": native_equivalent,
        "proof_size_comparable": proof_size_comparable,
        "selector_decision": selector_decision,
        "next_action": next_action,
        "source_artifact": source_artifact.relative_to(ROOT).as_posix(),
        "non_claims": row_non_claims,
    }


def load_sources() -> dict[str, dict[str, Any]]:
    sources = {
        "claim_audit": load_json(CLAIM_AUDIT),
        "gkr": load_json(GKR_BASELINE),
        "minimal_block": load_json(MINIMAL_BLOCK),
        "jolt": load_json(JOLT_ATLAS),
        "tablero": load_json(TABLERO_BOUNDARY),
    }
    expect_equal(sources["claim_audit"].get("schema"), "zkai-claim-audit-comparison-artifacts-v1", "claim audit schema")
    expect_equal(sources["gkr"].get("schema"), "zkai-gkr-dense-sidecar-baseline-v1", "GKR schema")
    expect_equal(sources["minimal_block"].get("schema"), "zkai-minimal-transformer-block-benchmark-v1", "minimal block schema")
    expect_equal(sources["jolt"].get("schema"), "zkai-jolt-atlas-lookup-tensor-comparison-v1", "Jolt schema")
    expect_equal(sources["tablero"].get("schema"), "zkai-tablero-hybrid-zkml-boundary-v1", "Tablero schema")
    return sources


def validate_source_numbers(sources: dict[str, dict[str, Any]]) -> None:
    claim_summary = require_dict(sources["claim_audit"].get("summary"), "claim summary")
    minimal_summary = require_dict(sources["minimal_block"].get("summary"), "minimal block summary")
    gkr_summary = require_dict(sources["gkr"].get("summary"), "GKR summary")
    tablero_examples = require_dict_list(sources["tablero"].get("boundary_examples"), "Tablero boundary_examples")
    tablero_statement = row_by_id(tablero_examples, "compact_statement_chain_boundary")

    expect_equal(
        require_int(claim_summary.get("proof_size_comparable_rows"), "claim comparable rows"),
        EXPECTED_CLAIM_AUDIT_COMPARABLE_ROWS,
        "claim audit comparable rows",
    )
    expect_equal(
        require_int(sources["claim_audit"].get("mutations_rejected"), "claim mutations"),
        EXPECTED_CLAIM_AUDIT_MUTATIONS,
        "claim audit mutation count",
    )
    expect_equal(
        require_int(minimal_summary.get("two_proof_frontier_typed_bytes"), "Stwo frontier"),
        EXPECTED_STWO_FRONTIER_TYPED_BYTES,
        "Stwo frontier",
    )
    expect_equal(
        require_int(minimal_summary.get("nanozk_reported_d128_block_proof_bytes"), "NANOZK paper row"),
        EXPECTED_NANOZK_REPORTED_BYTES,
        "NANOZK paper row",
    )
    expect_equal(
        require_bool(minimal_summary.get("missing_native_block_proof_object"), "missing native block proof flag"),
        True,
        "native block proof object flag",
    )
    expect_equal(
        require_int(gkr_summary.get("local_stwo_dense_typed_bytes"), "Stwo dense substitute"),
        EXPECTED_STWO_DENSE_SUBSTITUTE_TYPED_BYTES,
        "Stwo dense substitute",
    )
    expect_equal(
        require_int(gkr_summary.get("jstprove_tiny_gemm_proof_bytes"), "GKR tiny Gemm"),
        EXPECTED_GKR_TINY_GEMM_BYTES,
        "GKR tiny Gemm",
    )
    expect_equal(
        require_int(gkr_summary.get("jstprove_residual_add_proof_bytes"), "GKR residual add"),
        EXPECTED_GKR_RESIDUAL_ADD_BYTES,
        "GKR residual add",
    )
    expect_equal(
        require_int(gkr_summary.get("jstprove_layernorm_proof_bytes"), "GKR LayerNorm"),
        EXPECTED_GKR_LAYERNORM_BYTES,
        "GKR LayerNorm",
    )
    expect_equal(
        require_bool(gkr_summary.get("matched_d128_dense_layer_comparison"), "matched d128 GKR flag"),
        False,
        "matched d128 GKR flag",
    )
    expect_equal(
        require_str(tablero_statement.get("primary_metric"), "Tablero statement metric"),
        "statement_chain_rows",
        "Tablero statement metric",
    )
    expect_equal(
        require_int(tablero_statement.get("primary_value"), "Tablero statement rows"),
        199_553,
        "Tablero statement rows",
    )


def build_routes(sources: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    gkr_rows = require_dict_list(sources["gkr"].get("rows"), "GKR rows")
    gkr_tiny = row_by_id(gkr_rows, "tiny_gemm")
    gkr_residual = row_by_id(gkr_rows, "tiny_gemm_residual_add")
    gkr_layernorm = row_by_id(gkr_rows, "tiny_gemm_layernorm")
    jolt_timing = row_by_id(require_dict_list(sources["jolt"].get("rows"), "Jolt rows"), "jolt_atlas_repo_gpt2_readme")
    tablero_statement = row_by_id(
        require_dict_list(sources["tablero"].get("boundary_examples"), "Tablero boundary_examples"),
        "compact_statement_chain_boundary",
    )

    return [
        route(
            route_id="local_stwo_two_proof_frontier",
            proof_system="Stwo/STARK",
            object_class="local_two_proof_target",
            primary_metric="typed_proof_field_bytes",
            primary_pressure=EXPECTED_STWO_FRONTIER_TYPED_BYTES,
            ratio_vs_stwo_frontier="1.000000",
            ratio_vs_nanozk_context=ratio_string(EXPECTED_STWO_FRONTIER_TYPED_BYTES, EXPECTED_NANOZK_REPORTED_BYTES),
            matched_workload=False,
            native_equivalent=True,
            proof_size_comparable=False,
            selector_decision="BASELINE_HEAVY_FRONTIER",
            next_action="compress_or_replace_only_after_native_block_object_path_is_explicit",
            source_artifact=MINIMAL_BLOCK,
            non_claims=("not one native full-block proof", "not a NANOZK proof-size win"),
        ),
        route(
            route_id="gkr_dense_linear_scaling_candidate",
            proof_system=require_str(gkr_tiny.get("proof_system"), "GKR tiny system"),
            object_class=require_str(gkr_tiny.get("object_class"), "GKR tiny class"),
            primary_metric=require_str(gkr_tiny.get("primary_metric"), "GKR tiny metric"),
            primary_pressure=EXPECTED_GKR_TINY_GEMM_BYTES,
            ratio_vs_stwo_frontier=ratio_string(EXPECTED_GKR_TINY_GEMM_BYTES, EXPECTED_STWO_FRONTIER_TYPED_BYTES),
            ratio_vs_nanozk_context=ratio_string(EXPECTED_GKR_TINY_GEMM_BYTES, EXPECTED_NANOZK_REPORTED_BYTES),
            matched_workload=False,
            native_equivalent=False,
            proof_size_comparable=False,
            selector_decision="ATTACK_NEXT_UNMATCHED_DENSE_LINEAR_SCALING",
            next_action="scale_gkr_gemm_to_d128_projection_shape_and_bind_with_tablero_statement_boundary",
            source_artifact=GKR_BASELINE,
            non_claims=("not a matched d128 transformer-block proof", "not evidence that GKR replaces STARKs"),
        ),
        route(
            route_id="gkr_residual_add_no_go_now",
            proof_system=require_str(gkr_residual.get("proof_system"), "GKR residual system"),
            object_class=require_str(gkr_residual.get("object_class"), "GKR residual class"),
            primary_metric=require_str(gkr_residual.get("primary_metric"), "GKR residual metric"),
            primary_pressure=EXPECTED_GKR_RESIDUAL_ADD_BYTES,
            ratio_vs_stwo_frontier=ratio_string(EXPECTED_GKR_RESIDUAL_ADD_BYTES, EXPECTED_STWO_FRONTIER_TYPED_BYTES),
            ratio_vs_nanozk_context=ratio_string(EXPECTED_GKR_RESIDUAL_ADD_BYTES, EXPECTED_NANOZK_REPORTED_BYTES),
            matched_workload=False,
            native_equivalent=False,
            proof_size_comparable=False,
            selector_decision="NO_GO_NOW_TINY_RESIDUAL_SHAPE_HEAVIER",
            next_action="do_not_spend_next_pr_on_gkr_residual_until_dense_scaling_succeeds",
            source_artifact=GKR_BASELINE,
            non_claims=("not a matched d128 transformer-block proof", "not a GKR matched d128 proof-size win"),
        ),
        route(
            route_id="gkr_layernorm_no_go_now",
            proof_system=require_str(gkr_layernorm.get("proof_system"), "GKR LayerNorm system"),
            object_class=require_str(gkr_layernorm.get("object_class"), "GKR LayerNorm class"),
            primary_metric=require_str(gkr_layernorm.get("primary_metric"), "GKR LayerNorm metric"),
            primary_pressure=EXPECTED_GKR_LAYERNORM_BYTES,
            ratio_vs_stwo_frontier=ratio_string(EXPECTED_GKR_LAYERNORM_BYTES, EXPECTED_STWO_FRONTIER_TYPED_BYTES),
            ratio_vs_nanozk_context=ratio_string(EXPECTED_GKR_LAYERNORM_BYTES, EXPECTED_NANOZK_REPORTED_BYTES),
            matched_workload=False,
            native_equivalent=False,
            proof_size_comparable=False,
            selector_decision="NO_GO_NOW_TINY_NORM_SHAPE_HEAVIER",
            next_action="keep_rmsnorm_on_stark_native_path_until_a_matched_gkr_norm_route_exists",
            source_artifact=GKR_BASELINE,
            non_claims=("not a matched d128 transformer-block proof", "not a GKR matched d128 proof-size win"),
        ),
        route(
            route_id="native_d128_block_object_blocker",
            proof_system="Stwo/STARK",
            object_class="missing_native_block_proof_object",
            primary_metric="missing_backend_flag",
            primary_pressure=None,
            ratio_vs_stwo_frontier="NA",
            ratio_vs_nanozk_context="NA",
            matched_workload=False,
            native_equivalent=False,
            proof_size_comparable=False,
            selector_decision="ATTACK_NEXT_NATIVE_BLOCK_OBJECT",
            next_action="construct_or_spike_the_native_d128_block_proof_object_before_external_proof_size_claims",
            source_artifact=MINIMAL_BLOCK,
            non_claims=("not a proof-size result", "not a NANOZK comparison row"),
        ),
        route(
            route_id="tablero_statement_boundary_guardrail",
            proof_system="Tablero statement boundary",
            object_class=require_str(tablero_statement.get("object_class"), "Tablero statement class"),
            primary_metric=require_str(tablero_statement.get("primary_metric"), "Tablero statement metric"),
            primary_pressure=require_int(tablero_statement.get("primary_value"), "Tablero statement rows"),
            ratio_vs_stwo_frontier="NA",
            ratio_vs_nanozk_context="NA",
            matched_workload=False,
            native_equivalent=False,
            proof_size_comparable=False,
            selector_decision="KEEP_AS_GUARDRAIL_NOT_PROOF_SIZE_ROW",
            next_action="use_to_bind_hybrid_routes_and_prevent_object_class_confusion",
            source_artifact=TABLERO_BOUNDARY,
            non_claims=("not a proof object", "not proof-size comparable"),
        ),
        route(
            route_id="nanozk_paper_context_only",
            proof_system="NANOZK",
            object_class="paper_reported_external_context",
            primary_metric="reported_proof_size_bytes",
            primary_pressure=EXPECTED_NANOZK_REPORTED_BYTES,
            ratio_vs_stwo_frontier=ratio_string(EXPECTED_NANOZK_REPORTED_BYTES, EXPECTED_STWO_FRONTIER_TYPED_BYTES),
            ratio_vs_nanozk_context="1.000000",
            matched_workload=False,
            native_equivalent=False,
            proof_size_comparable=False,
            selector_decision="CONTEXT_ONLY_NOT_LOCAL_REPRODUCTION",
            next_action="keep_as_paper_context_until_local_reproduction_or_matched_object_exists",
            source_artifact=MINIMAL_BLOCK,
            non_claims=("not locally reproduced", "not a local benchmark"),
        ),
        route(
            route_id="jolt_atlas_lookup_tensor_context",
            proof_system="Jolt Atlas",
            object_class="external_lookup_tensor_zkml_repo_benchmark",
            primary_metric=require_str(jolt_timing.get("primary_metric"), "Jolt timing metric"),
            primary_pressure=None,
            ratio_vs_stwo_frontier="NA",
            ratio_vs_nanozk_context="NA",
            matched_workload=False,
            native_equivalent=False,
            proof_size_comparable=False,
            selector_decision="CONTEXT_ONLY_REPRODUCTION_TARGET",
            next_action="reproduce_only_if_we_need_lookup_tensor_timing_or_architecture_baseline",
            source_artifact=JOLT_ATLAS,
            non_claims=("not a proof-size row", "not locally reproduced"),
        ),
    ]


def summary_from_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    attack_next = [row["route_id"] for row in rows if row["selector_decision"].startswith("ATTACK_NEXT")]
    no_go_now = [row["route_id"] for row in rows if row["selector_decision"].startswith("NO_GO_NOW")]
    proof_size_comparable = [row for row in rows if row["proof_size_comparable"]]
    return {
        "selector_row_count": len(rows),
        "attack_next_count": len(attack_next),
        "no_go_now_count": len(no_go_now),
        "attack_next_routes": attack_next,
        "no_go_now_routes": no_go_now,
        "proof_size_comparable_rows": len(proof_size_comparable),
        "claim_audit_proof_size_comparable_rows": EXPECTED_CLAIM_AUDIT_COMPARABLE_ROWS,
        "stwo_two_proof_frontier_typed_bytes": EXPECTED_STWO_FRONTIER_TYPED_BYTES,
        "nanozk_paper_reported_bytes": EXPECTED_NANOZK_REPORTED_BYTES,
        "gap_to_nanozk_paper_reported_bytes": EXPECTED_STWO_FRONTIER_TYPED_BYTES - EXPECTED_NANOZK_REPORTED_BYTES,
        "gkr_tiny_gemm_proof_bytes": EXPECTED_GKR_TINY_GEMM_BYTES,
        "gkr_tiny_gemm_vs_stwo_dense_substitute_ratio": ratio_string(
            EXPECTED_GKR_TINY_GEMM_BYTES, EXPECTED_STWO_DENSE_SUBSTITUTE_TYPED_BYTES
        ),
        "gkr_tiny_gemm_vs_stwo_frontier_ratio": ratio_string(EXPECTED_GKR_TINY_GEMM_BYTES, EXPECTED_STWO_FRONTIER_TYPED_BYTES),
        "gkr_residual_add_vs_stwo_frontier_ratio": ratio_string(EXPECTED_GKR_RESIDUAL_ADD_BYTES, EXPECTED_STWO_FRONTIER_TYPED_BYTES),
        "gkr_layernorm_vs_stwo_frontier_ratio": ratio_string(EXPECTED_GKR_LAYERNORM_BYTES, EXPECTED_STWO_FRONTIER_TYPED_BYTES),
        "go_gate": "GO_SELECTOR_HAS_ATTACK_NEXT_AND_NO_GO_NOW_WITH_ZERO_COMPARABLE_ROWS",
    }


def validate_route(row: dict[str, Any]) -> None:
    if set(row) != set(ROW_FIELDS):
        raise HybridSelectorError(f"{row.get('route_id', '<missing>')} row field drift")
    route_id = require_str(row["route_id"], "route id")
    require_str(row["proof_system"], f"{route_id} proof system")
    object_class = require_str(row["object_class"], f"{route_id} object class")
    require_str(row["primary_metric"], f"{route_id} primary metric")
    require_str(row["selector_decision"], f"{route_id} decision")
    require_str(row["next_action"], f"{route_id} next action")
    require_str(row["source_artifact"], f"{route_id} source artifact")
    require_bool(row["matched_workload"], f"{route_id} matched workload")
    require_bool(row["native_equivalent"], f"{route_id} native equivalence")
    proof_size_comparable = require_bool(row["proof_size_comparable"], f"{route_id} proof-size comparable")
    if row["primary_pressure"] is not None:
        require_int(row["primary_pressure"], f"{route_id} primary pressure")
    if not isinstance(row["non_claims"], list) or not row["non_claims"]:
        raise HybridSelectorError(f"{route_id} missing non-claims")
    if any(not isinstance(claim, str) or not claim for claim in row["non_claims"]):
        raise HybridSelectorError(f"{route_id} invalid non-claim")
    if not set(NON_CLAIMS).issubset(set(row["non_claims"])):
        raise HybridSelectorError(f"{route_id} row non-claim inventory drift")
    if proof_size_comparable:
        raise HybridSelectorError(f"{route_id} proof-size comparability overclaim")
    if object_class == "local_external_gkr_fixture" and (row["matched_workload"] or row["native_equivalent"]):
        raise HybridSelectorError(f"{route_id} GKR fixture promoted to matched native route")
    if "statement" in object_class and row["ratio_vs_stwo_frontier"] != "NA":
        raise HybridSelectorError(f"{route_id} statement artifact promoted to byte ratio")
    if row["proof_system"] == "NANOZK" and row["matched_workload"]:
        raise HybridSelectorError(f"{route_id} NANOZK paper context promoted to matched workload")
    if row["proof_system"] == "NANOZK" and "not locally reproduced" not in row["non_claims"]:
        raise HybridSelectorError(f"{route_id} NANOZK local reproduction non-claim missing")


def validate_payload(payload: dict[str, Any], *, final: bool = True, sources: dict[str, dict[str, Any]] | None = None) -> None:
    expect_equal(payload.get("schema"), SCHEMA, "schema")
    expect_equal(payload.get("decision"), DECISION, "decision")
    expect_equal(payload.get("result"), RESULT, "result")
    expect_equal(payload.get("issue"), ISSUE_URL, "issue")
    if set(payload.get("non_claims", [])) != set(NON_CLAIMS):
        raise HybridSelectorError("global non-claim drift")
    expect_equal(payload.get("validation_commands"), list(VALIDATION_COMMANDS), "validation command inventory")
    rows = payload.get("selector_rows")
    if not isinstance(rows, list) or not rows:
        raise HybridSelectorError("selector rows missing")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise HybridSelectorError("selector row must be an object")
        validate_route(row)
        route_id = row["route_id"]
        if route_id in seen:
            raise HybridSelectorError(f"duplicate route id: {route_id}")
        seen.add(route_id)
    if seen != EXPECTED_ROUTE_IDS:
        raise HybridSelectorError("selector route inventory drift")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        raise HybridSelectorError("summary missing")
    attack_next_routes = [row["route_id"] for row in rows if row["selector_decision"].startswith("ATTACK_NEXT")]
    no_go_now_routes = [row["route_id"] for row in rows if row["selector_decision"].startswith("NO_GO_NOW")]
    comparable_routes = [row["route_id"] for row in rows if row["proof_size_comparable"]]
    expect_equal(summary.get("selector_row_count"), len(rows), "selector row count")
    expect_equal(summary.get("attack_next_count"), len(attack_next_routes), "attack-next count")
    expect_equal(summary.get("attack_next_routes"), attack_next_routes, "attack-next routes")
    expect_equal(summary.get("no_go_now_count"), len(no_go_now_routes), "no-go-now count")
    expect_equal(summary.get("no_go_now_routes"), no_go_now_routes, "no-go-now routes")
    expect_equal(summary.get("proof_size_comparable_rows"), len(comparable_routes), "selector proof comparable rows")
    expect_equal(summary.get("claim_audit_proof_size_comparable_rows"), 0, "claim audit proof comparable rows")
    expect_equal(summary.get("stwo_two_proof_frontier_typed_bytes"), EXPECTED_STWO_FRONTIER_TYPED_BYTES, "summary frontier")
    expect_equal(summary.get("nanozk_paper_reported_bytes"), EXPECTED_NANOZK_REPORTED_BYTES, "summary NANOZK")
    if not attack_next_routes:
        raise HybridSelectorError("selector has no attack-next route")
    if not no_go_now_routes:
        raise HybridSelectorError("selector has no no-go-now route")
    if comparable_routes:
        raise HybridSelectorError("selector proof comparability overclaim")
    if summary.get("go_gate") != "GO_SELECTOR_HAS_ATTACK_NEXT_AND_NO_GO_NOW_WITH_ZERO_COMPARABLE_ROWS":
        raise HybridSelectorError("GO gate drift")
    if not isinstance(payload.get("source_artifacts"), list) or len(payload["source_artifacts"]) != 5:
        raise HybridSelectorError("source artifact inventory drift")
    seen_source_paths: set[str] = set()
    for descriptor in payload["source_artifacts"]:
        if not isinstance(descriptor, dict):
            raise HybridSelectorError("source artifact descriptor must be an object")
        rel_path = require_str(descriptor.get("path"), "source artifact path")
        if rel_path not in SOURCE_ARTIFACT_PATHS:
            raise HybridSelectorError("source artifact path outside allowlist")
        if rel_path in seen_source_paths:
            raise HybridSelectorError("duplicate source artifact path")
        seen_source_paths.add(rel_path)
        path = ROOT / rel_path
        if descriptor != source_descriptor(path):
            raise HybridSelectorError("source artifact descriptor drift")
    if seen_source_paths != SOURCE_ARTIFACT_PATHS:
        raise HybridSelectorError("source artifact inventory drift")
    if sources is None:
        sources = load_sources()
    validate_source_numbers(sources)
    canonical_rows = build_routes(sources)
    if rows != canonical_rows:
        raise HybridSelectorError("canonical selector row drift")
    canonical_summary = summary_from_rows(canonical_rows)
    if summary != canonical_summary:
        raise HybridSelectorError("canonical summary drift")
    if "mutation_results" in payload:
        mutation_results = payload["mutation_results"]
        if not isinstance(mutation_results, list):
            raise HybridSelectorError("mutation inventory drift")
        if len(mutation_results) != len(MUTATIONS):
            raise HybridSelectorError("mutation inventory drift")
        if any(not isinstance(result, dict) for result in mutation_results):
            raise HybridSelectorError("mutation inventory drift")
        expected_names = [name for name, _ in MUTATIONS]
        actual_names = [require_str(result.get("name"), "mutation name") for result in mutation_results]
        if actual_names != expected_names:
            raise HybridSelectorError("mutation inventory drift")
        rejected = sum(1 for result in mutation_results if result.get("accepted") is False)
        if payload.get("mutation_count") != len(MUTATIONS) or payload.get("mutations_rejected") != rejected:
            raise HybridSelectorError("mutation rejection drift")
        if rejected != len(MUTATIONS):
            raise HybridSelectorError("mutation rejection drift")
    if final:
        expected = payload.get("payload_commitment")
        if not isinstance(expected, str):
            raise HybridSelectorError("payload commitment missing")
        candidate = copy.deepcopy(payload)
        candidate.pop("payload_commitment", None)
        if expected != commitment(candidate):
            raise HybridSelectorError("payload commitment drift")


def base_payload(sources: dict[str, dict[str, Any]]) -> dict[str, Any]:
    validate_source_numbers(sources)
    rows = build_routes(sources)
    summary = summary_from_rows(rows)
    payload = {
        "schema": SCHEMA,
        "issue": ISSUE_URL,
        "decision": DECISION,
        "result": RESULT,
        "summary": summary,
        "selector_rows": rows,
        "non_claims": list(NON_CLAIMS),
        "source_artifacts": [
            source_descriptor(CLAIM_AUDIT),
            source_descriptor(GKR_BASELINE),
            source_descriptor(MINIMAL_BLOCK),
            source_descriptor(JOLT_ATLAS),
            source_descriptor(TABLERO_BOUNDARY),
        ],
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    validate_payload(payload, final=False, sources=sources)
    return payload


def mutate_gkr_dense_promoted(payload: dict[str, Any]) -> None:
    row = next(row for row in payload["selector_rows"] if row["route_id"] == "gkr_dense_linear_scaling_candidate")
    row["matched_workload"] = True
    row["native_equivalent"] = True


def mutate_statement_boundary_ratio(payload: dict[str, Any]) -> None:
    row = next(row for row in payload["selector_rows"] if row["route_id"] == "tablero_statement_boundary_guardrail")
    row["ratio_vs_stwo_frontier"] = "4.903022"


def mutate_any_route_comparable(payload: dict[str, Any]) -> None:
    row = next(row for row in payload["selector_rows"] if row["route_id"] == "gkr_dense_linear_scaling_candidate")
    row["proof_size_comparable"] = True


def mutate_nanozk_matched(payload: dict[str, Any]) -> None:
    row = next(row for row in payload["selector_rows"] if row["route_id"] == "nanozk_paper_context_only")
    row["matched_workload"] = True


def mutate_remove_row_non_claim(payload: dict[str, Any]) -> None:
    row = next(row for row in payload["selector_rows"] if row["route_id"] == "gkr_dense_linear_scaling_candidate")
    row["non_claims"] = []


def mutate_remove_attack_next(payload: dict[str, Any]) -> None:
    for row in payload["selector_rows"]:
        if row["selector_decision"].startswith("ATTACK_NEXT"):
            row["selector_decision"] = "DEFER_ONLY"
    payload["summary"]["attack_next_count"] = 0
    payload["summary"]["attack_next_routes"] = []


def mutate_remove_no_go_now(payload: dict[str, Any]) -> None:
    for row in payload["selector_rows"]:
        if row["selector_decision"].startswith("NO_GO_NOW"):
            row["selector_decision"] = "DEFER_ONLY"
    payload["summary"]["no_go_now_count"] = 0
    payload["summary"]["no_go_now_routes"] = []


def mutate_claim_audit_comparable(payload: dict[str, Any]) -> None:
    payload["summary"]["claim_audit_proof_size_comparable_rows"] = 1


def mutate_summary_attack_route_drift(payload: dict[str, Any]) -> None:
    payload["summary"]["attack_next_routes"] = []


def mutate_stwo_frontier_drift(payload: dict[str, Any]) -> None:
    payload["summary"]["stwo_two_proof_frontier_typed_bytes"] = 39_999


def mutate_source_artifact_digest(payload: dict[str, Any]) -> None:
    payload["source_artifacts"][0]["sha256"] = "0" * 64


def mutate_payload_commitment(payload: dict[str, Any]) -> None:
    payload["payload_commitment"] = "blake2b-256:" + "0" * 64


MUTATIONS: tuple[tuple[str, Callable[[dict[str, Any]], None]], ...] = (
    ("gkr_dense_promoted", mutate_gkr_dense_promoted),
    ("statement_boundary_ratio", mutate_statement_boundary_ratio),
    ("any_route_comparable", mutate_any_route_comparable),
    ("nanozk_matched", mutate_nanozk_matched),
    ("remove_row_non_claim", mutate_remove_row_non_claim),
    ("remove_attack_next", mutate_remove_attack_next),
    ("remove_no_go_now", mutate_remove_no_go_now),
    ("claim_audit_comparable", mutate_claim_audit_comparable),
    ("summary_attack_route_drift", mutate_summary_attack_route_drift),
    ("stwo_frontier_drift", mutate_stwo_frontier_drift),
    ("source_artifact_digest", mutate_source_artifact_digest),
    ("payload_commitment", mutate_payload_commitment),
)


def run_mutations(payload: dict[str, Any], sources: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for name, mutation in MUTATIONS:
        candidate = copy.deepcopy(payload)
        try:
            mutation(candidate)
            validate_payload(candidate, final=name == "payload_commitment", sources=sources)
            results.append({"name": name, "accepted": True, "reason": "mutation accepted"})
        except HybridSelectorError as exc:
            results.append({"name": name, "accepted": False, "reason": str(exc)})
    return results


def build_payload() -> dict[str, Any]:
    sources = load_sources()
    payload = base_payload(sources)
    mutation_results = run_mutations(payload, sources)
    payload["mutation_results"] = mutation_results
    payload["mutation_count"] = len(mutation_results)
    payload["mutations_rejected"] = sum(1 for result in mutation_results if result["accepted"] is False)
    payload["payload_commitment"] = commitment({key: value for key, value in payload.items() if key != "payload_commitment"})
    validate_payload(payload, sources=sources)
    if payload["mutations_rejected"] != payload["mutation_count"]:
        raise HybridSelectorError("mutation rejection drift")
    return payload


def tsv_text(payload: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=ROW_COLUMNS, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    for row in payload["selector_rows"]:
        writer.writerow({column: row[column] for column in ROW_COLUMNS})
    return output.getvalue()


def require_output_path(path: pathlib.Path | None, suffix: str, label: str) -> pathlib.Path | None:
    if path is None:
        return None
    resolved = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    evidence_root = EVIDENCE_DIR.resolve()
    if evidence_root not in resolved.parents:
        raise HybridSelectorError(f"{label} output must stay under {EVIDENCE_DIR.relative_to(ROOT).as_posix()}")
    if resolved.suffix != suffix:
        raise HybridSelectorError(f"{label} output must use {suffix}")
    if resolved in {CLAIM_AUDIT.resolve(), GKR_BASELINE.resolve(), MINIMAL_BLOCK.resolve(), JOLT_ATLAS.resolve(), TABLERO_BOUNDARY.resolve()}:
        raise HybridSelectorError(f"{label} output cannot overwrite a source artifact")
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
                "selector_rows": payload["summary"]["selector_row_count"],
                "attack_next_count": payload["summary"]["attack_next_count"],
                "no_go_now_count": payload["summary"]["no_go_now_count"],
                "proof_size_comparable_rows": payload["summary"]["proof_size_comparable_rows"],
                "mutations_rejected": payload["mutations_rejected"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
