#!/usr/bin/env python3.10
"""Preflight the scoped d128 seq32 transformer-block boundary gate.

This gate does not create a new proof object. It binds the current checked
proof-pressure evidence into the next experiment decision for issue #715:
attack the scoped d128 seq32 boundary before spending effort on d256 seq64.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import pathlib
import sys
import tempfile
from typing import Any

if sys.version_info < (3, 10):
    raise RuntimeError("zkai_scoped_d128_seq32_block_boundary_preflight_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs" / "engineering"
EVIDENCE_DIR = DOCS_DIR / "evidence"

SLOPE_TABLE = EVIDENCE_DIR / "zkai-proof-pressure-slope-table-2026-05.json"
ROUTE_MATRIX = EVIDENCE_DIR / "zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json"
SEQ32_SINGLE = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-single-proof-2026-05.json"
SEQ32_FRONTIER = EVIDENCE_DIR / "zkai-seq32-value-compatible-boundary-frontier-2026-05.json"
D128_ATTENTION = EVIDENCE_DIR / "zkai-attention-kv-stwo-native-d128-two-head-seq32-fused-softmax-table-gate-2026-05.json"
D128_MLP = EVIDENCE_DIR / "zkai-seq32-derived-d128-native-mlp-surface-2026-05.json"

JSON_OUT = EVIDENCE_DIR / "zkai-scoped-d128-seq32-block-boundary-preflight-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-scoped-d128-seq32-block-boundary-preflight-2026-05.tsv"
MD_OUT = DOCS_DIR / "zkai-scoped-d128-seq32-block-boundary-preflight-2026-05-24.md"

SCHEMA = "zkai-scoped-d128-seq32-block-boundary-preflight-v1"
ISSUE = 715
DECISION = "GO_SCOPED_D128_SEQ32_BLOCK_BOUNDARY_PREFLIGHT"
RESULT = "ATTACK_SCOPED_D128_SEQ32_BOUNDARY_BEFORE_D256_SEQ64_STRESS"
CLAIM_BOUNDARY = (
    "PREFLIGHT_FOR_SCOPED_D128_SEQ32_TRANSFORMER_BOUNDARY;"
    "SOURCE_BOUNDARY_AND_PROOF_SIZE_DECISION_ONLY;"
    "NOT_FULL_BLOCK_NOT_SPEED_CLAIM_NOT_EXTERNAL_COMPARISON"
)
PRIMARY_NEXT_GATE = "scoped_d128_seq32_transformer_block_boundary_implementation"
STRESS_GATE = "d256_h2_seq64_falsification_after_scoped_d128_gate"
RECOMMENDED_ACTION = "IMPLEMENT_SCOPED_D128_SEQ32_BOUNDARY_BEFORE_D256_SEQ64"
TIMING_POLICY = "proof_size_preflight_only_no_new_timing_claim"

VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_scoped_d128_seq32_block_boundary_preflight_gate.py --write-json docs/engineering/evidence/zkai-scoped-d128-seq32-block-boundary-preflight-2026-05.json --write-tsv docs/engineering/evidence/zkai-scoped-d128-seq32-block-boundary-preflight-2026-05.tsv --write-md docs/engineering/zkai-scoped-d128-seq32-block-boundary-preflight-2026-05-24.md",
    "python3.10 -m py_compile scripts/zkai_scoped_d128_seq32_block_boundary_preflight_gate.py scripts/tests/test_zkai_scoped_d128_seq32_block_boundary_preflight_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_scoped_d128_seq32_block_boundary_preflight_gate",
    "git diff --check",
)

NON_CLAIMS = (
    "not a full transformer block proof",
    "not a public proving-speed benchmark",
    "not an external zkML comparison",
    "not a NANOZK proof-size win",
    "not exact real-valued Softmax",
    "not full autoregressive inference",
    "not production throughput evidence",
)

EXPECTED_SOURCE_DESCRIPTORS = {
    "slope_table": {
        "path": SLOPE_TABLE,
        "schema": "zkai-proof-pressure-slope-table-v1",
        "decision": "GO_PAPER_SLOPE_TABLE_WITH_SCOPED_BLOCK_NEXT_GATE",
        "sha256": "1bae947f83b9fd49238751391c8445e575e05b464bc6af47a079be4cd1782e2e",
        "bytes": 10_939,
    },
    "route_matrix": {
        "path": ROUTE_MATRIX,
        "schema": "zkai-attention-kv-fused-softmax-table-route-matrix-v1",
        "decision": "GO_NATIVE_STWO_FUSED_SOFTMAX_TABLE_CONTROLLED_ROUTE_MATRIX",
        "sha256": "f8da6eb33454011e3ef20b7b80cdcce4ff9086764d7b4a3868c684046b434701",
        "bytes": 92_871,
    },
    "seq32_single": {
        "path": SEQ32_SINGLE,
        "schema": "zkai-native-seq32-attention-mlp-single-proof-gate-v1",
        "decision": "GO_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_OBJECT_BEATS_MATCHED_FRONTIER",
        "sha256": "d4732af4966599264e34b893d9e24333cabd32e1c9caa45d8d8aac10b6fc98ab",
        "bytes": 9_033,
    },
    "seq32_frontier": {
        "path": SEQ32_FRONTIER,
        "schema": "zkai-seq32-value-compatible-boundary-frontier-v1",
        "decision": "GO_PIN_SEQ32_VALUE_COMPATIBLE_TWO_PROOF_FRONTIER_FOR_NEXT_NATIVE_BOUNDARY",
        "sha256": "406a1b65574c694f208652d4a181e323dd5d66a53b4b58c685e61358dfb58c3d",
        "bytes": 8_807,
    },
    "d128_attention": {
        "path": D128_ATTENTION,
        "schema": "zkai-attention-kv-stwo-native-d128-two-head-seq32-fused-softmax-table-gate-v1",
        "decision": "GO_NATIVE_STWO_FUSED_ATTENTION_ARITHMETIC_AND_SOFTMAX_TABLE_LOGUP_MEMBERSHIP",
        "sha256": "7e7d26cd08b53a34557e9b80f118b815be46cbf4de32d1957c2e7741071514ef",
        "bytes": 12_412,
    },
    "d128_mlp": {
        "path": D128_MLP,
        "schema": "zkai-seq32-derived-d128-native-mlp-surface-gate-v1",
        "decision": "GO_SEQ32_DERIVED_D128_MLP_SURFACE_INPUTS_READY_FOR_NATIVE_PROOF",
        "sha256": "96fdc2435fa7c14f9596f7fbe2a1006861fd8bc7be3c219cf49ac43096cdf1c2",
        "bytes": 3_742,
    },
}

TSV_COLUMNS = (
    "row_id",
    "kind",
    "status",
    "metric_scope",
    "fused_or_single_bytes",
    "split_or_reference_bytes",
    "saving_bytes",
    "ratio",
    "lookup_growth",
    "trace_growth",
    "fused_proof_growth",
    "action",
)

ROW_IDS = (
    "existing_seq32_d128_single_proof_champion",
    "d128_two_head_seq32_attention_route",
    "seq32_derived_d128_mlp_surface",
    "d128_two_head_seq32_sequence_slope",
    "width_axis_caution",
    "next_scoped_boundary_gate",
)

MUTATION_NAMES = (
    "source_digest_drift",
    "source_size_drift",
    "issue_drift",
    "decision_drift",
    "next_gate_drift",
    "d256_primary_overclaim",
    "external_comparison_overclaim",
    "full_block_overclaim",
    "seq32_champion_metric_drift",
    "d128_attention_metric_drift",
    "mlp_surface_metric_drift",
    "sequence_slope_drift",
    "width_caution_drift",
    "row_missing_required_field",
    "non_claim_removed",
    "validation_command_drift",
    "payload_commitment_drift",
)


class ScopedBlockPreflightError(Exception):
    pass


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def payload_for_commitment(payload: dict[str, Any]) -> dict[str, Any]:
    reduced = copy.deepcopy(payload)
    reduced.pop("payload_commitment", None)
    return reduced


def commitment(data: Any) -> str:
    digest = hashlib.blake2b(canonical_json(data).encode("utf-8"), digest_size=32).hexdigest()
    return f"blake2b-256:{digest}"


def expect_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ScopedBlockPreflightError(f"{label} drift: expected {expected!r}, got {actual!r}")


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ScopedBlockPreflightError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ScopedBlockPreflightError(f"{label} must be a list")
    return value


def require_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ScopedBlockPreflightError(f"{label} must be a non-empty string")
    return value


def require_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ScopedBlockPreflightError(f"{label} must be an integer")
    return value


def require_number(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ScopedBlockPreflightError(f"{label} must be a number")
    return float(value)


def load_source(path: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise ScopedBlockPreflightError(f"unable to read source artifact: {path}") from error
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ScopedBlockPreflightError(f"invalid JSON source artifact: {path}") from error
    if not isinstance(data, dict):
        raise ScopedBlockPreflightError(f"{path} must contain a JSON object")
    descriptor = {
        "path": path.relative_to(ROOT).as_posix(),
        "schema": data.get("schema"),
        "decision": data.get("decision"),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }
    return data, descriptor


def load_sources() -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    payloads: dict[str, dict[str, Any]] = {}
    descriptors: list[dict[str, Any]] = []
    for source_id, expected in EXPECTED_SOURCE_DESCRIPTORS.items():
        data, descriptor = load_source(expected["path"])
        descriptor["id"] = source_id
        payloads[source_id] = data
        descriptors.append(descriptor)
    return payloads, descriptors


def route_row(route_matrix: dict[str, Any], profile_id: str) -> dict[str, Any]:
    for row in require_list(route_matrix.get("route_rows"), "route matrix rows"):
        item = require_dict(row, "route row")
        if item.get("profile_id") == profile_id:
            return item
    raise ScopedBlockPreflightError(f"route row not found: {profile_id}")


def slope_row(slope: dict[str, Any], row_id: str) -> dict[str, Any]:
    for row in require_list(slope.get("rows"), "slope rows"):
        item = require_dict(row, "slope row")
        if item.get("row_id") == row_id:
            return item
    raise ScopedBlockPreflightError(f"slope row not found: {row_id}")


def build_rows(sources: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    single_summary = require_dict(sources["seq32_single"].get("summary"), "seq32 single summary")
    frontier_summary = require_dict(sources["seq32_frontier"].get("summary"), "seq32 frontier summary")
    attention = sources["d128_attention"]
    mlp_summary = require_dict(sources["d128_mlp"].get("summary"), "d128 MLP summary")
    d128_attention_row = route_row(sources["route_matrix"], "d128_two_head_seq32")
    d128_sequence = slope_row(sources["slope_table"], "d128_h2_seq32_to_seq64_sequence_axis")
    d64_to_d128_width = slope_row(sources["slope_table"], "d64_to_d128_h2_seq32_width_axis")
    d128_to_d256_width = slope_row(sources["slope_table"], "d128_to_d256_h2_seq32_width_axis")

    expect_equal(
        single_summary.get("matched_two_proof_frontier_typed_bytes"),
        frontier_summary.get("value_compatible_two_proof_frontier_typed_bytes"),
        "seq32 single/frontier typed comparator",
    )
    expect_equal(
        d128_attention_row.get("fused_proof_size_bytes"),
        attention.get("fused_proof_size_bytes"),
        "route matrix/d128 attention fused proof bytes",
    )
    expect_equal(
        d128_attention_row.get("source_plus_sidecar_raw_proof_bytes"),
        attention.get("source_plus_sidecar_raw_proof_bytes"),
        "route matrix/d128 attention split proof bytes",
    )

    return [
        {
            "row_id": "existing_seq32_d128_single_proof_champion",
            "kind": "checked_native_boundary",
            "status": "REGRESSION_BASELINE_GO",
            "metric_scope": "typed_and_json_local_proof_bytes",
            "fused_or_single_bytes": single_summary["native_single_proof_typed_bytes"],
            "split_or_reference_bytes": single_summary["matched_two_proof_frontier_typed_bytes"],
            "saving_bytes": single_summary["typed_saving_vs_matched_frontier_bytes"],
            "ratio": float(single_summary["typed_ratio_vs_matched_frontier"]),
            "lookup_growth": None,
            "trace_growth": None,
            "fused_proof_growth": None,
            "action": "preserve_as_regression_baseline_not_as_full_block_claim",
            "interpretation": (
                "One checked seq32 attention plus d128 MLP native proof already beats "
                "its matched value-compatible two-proof frontier."
            ),
        },
        {
            "row_id": "d128_two_head_seq32_attention_route",
            "kind": "attention_source_route",
            "status": "GO_ATTENTION_SOURCE_FOR_SCOPED_GATE",
            "metric_scope": "raw_proof_bytes",
            "fused_or_single_bytes": attention["fused_proof_size_bytes"],
            "split_or_reference_bytes": attention["source_plus_sidecar_raw_proof_bytes"],
            "saving_bytes": attention["fused_saves_vs_source_plus_sidecar_bytes"],
            "ratio": round(float(attention["fused_to_source_plus_sidecar_ratio"]), 6),
            "lookup_claims": attention["lookup_claims"],
            "trace_rows": attention["trace_rows"],
            "lookup_growth": None,
            "trace_growth": None,
            "fused_proof_growth": None,
            "action": "use_as_d128_attention_source_for_scoped_boundary",
            "interpretation": "The d128 two-head seq32 attention route is proof-size positive against its matched split source plus sidecar.",
        },
        {
            "row_id": "seq32_derived_d128_mlp_surface",
            "kind": "mlp_source_surface",
            "status": "GO_MLP_SOURCE_FOR_SCOPED_GATE",
            "metric_scope": "typed_bytes",
            "fused_or_single_bytes": mlp_summary["fused_typed_bytes"],
            "split_or_reference_bytes": mlp_summary["separate_component_typed_bytes"],
            "saving_bytes": mlp_summary["typed_saving_bytes"],
            "ratio": mlp_summary["fused_typed_ratio"],
            "adapter_mismatches": mlp_summary["seq32_adapter_mismatches"],
            "lookup_growth": None,
            "trace_growth": None,
            "fused_proof_growth": None,
            "action": "use_as_d128_mlp_surface_if_source_value_adapter_stays_pinned",
            "interpretation": "The seq32-derived d128 MLP surface is value-compatible and preserves a large local fusion saving.",
        },
        {
            "row_id": "d128_two_head_seq32_sequence_slope",
            "kind": "scaling_signal",
            "status": "GO_SEQUENCE_AXIS_SUPPORTS_SCOPED_D128_FIRST",
            "metric_scope": "raw_proof_bytes_growth",
            "fused_or_single_bytes": d128_sequence["target_fused_proof_bytes"],
            "split_or_reference_bytes": d128_sequence["target_split_proof_bytes"],
            "saving_bytes": d128_sequence["target_saving_bytes"],
            "ratio": d128_sequence["target_fused_to_split_ratio"],
            "lookup_growth": d128_sequence["lookup_growth"],
            "trace_growth": d128_sequence["trace_growth"],
            "fused_proof_growth": d128_sequence["fused_proof_growth"],
            "action": "treat_seq64_as_followup_after_scoped_seq32_boundary",
            "interpretation": "For d128 two-head attention, seq32 to seq64 grows lookup work much faster than fused proof bytes.",
        },
        {
            "row_id": "width_axis_caution",
            "kind": "claim_guardrail",
            "status": "CAUTION_DO_NOT_JUMP_TO_D256_SEQ64_AS_PRIMARY_GATE",
            "metric_scope": "raw_proof_bytes_growth",
            "fused_or_single_bytes": d128_to_d256_width["target_fused_proof_bytes"],
            "split_or_reference_bytes": d128_to_d256_width["target_split_proof_bytes"],
            "saving_bytes": d128_to_d256_width["target_saving_bytes"],
            "ratio": d128_to_d256_width["target_fused_to_split_ratio"],
            "lookup_growth": d128_to_d256_width["lookup_growth"],
            "trace_growth": d128_to_d256_width["trace_growth"],
            "fused_proof_growth": d128_to_d256_width["fused_proof_growth"],
            "d64_to_d128_fused_proof_growth": d64_to_d128_width["fused_proof_growth"],
            "action": "keep_d256_seq64_as_stress_or_falsification_after_scoped_d128_gate",
            "interpretation": "Width still beats split locally, but proof growth is the cost center and should not lead the paper path.",
        },
        {
            "row_id": "next_scoped_boundary_gate",
            "kind": "implementation_gate",
            "status": "ATTACK_NEXT",
            "metric_scope": "decision_gate",
            "fused_or_single_bytes": None,
            "split_or_reference_bytes": None,
            "saving_bytes": None,
            "ratio": None,
            "lookup_growth": None,
            "trace_growth": None,
            "fused_proof_growth": None,
            "action": RECOMMENDED_ACTION,
            "interpretation": (
                "Build the smallest scoped d128 seq32 boundary that binds the d128 attention source, "
                "the d128 MLP surface, source handles, and the typed statement envelope."
            ),
        },
    ]


def build_payload(include_mutations: bool = True) -> dict[str, Any]:
    sources, descriptors = load_sources()
    rows = build_rows(sources)
    row_map = {row["row_id"]: row for row in rows}
    slope_summary = require_dict(sources["slope_table"].get("summary"), "slope table summary")
    single_summary = require_dict(sources["seq32_single"].get("summary"), "seq32 single summary")
    frontier_summary = require_dict(sources["seq32_frontier"].get("summary"), "seq32 frontier summary")
    mlp_summary = require_dict(sources["d128_mlp"].get("summary"), "d128 MLP summary")

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "issue": ISSUE,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "timing_policy": TIMING_POLICY,
        "source_artifacts": descriptors,
        "summary": {
            "primary_next_gate": PRIMARY_NEXT_GATE,
            "stress_gate": STRESS_GATE,
            "recommended_action": RECOMMENDED_ACTION,
            "paper_claim_status": "NARROW_CLAIM_READY_FOR_SCOPED_BLOCK_PREFLIGHT_NOT_FULL_BLOCK",
            "proof_size_comparable_external_rows": 0,
            "existing_seq32_d128_single_typed_bytes": single_summary["native_single_proof_typed_bytes"],
            "existing_seq32_d128_frontier_typed_bytes": single_summary["matched_two_proof_frontier_typed_bytes"],
            "existing_seq32_d128_typed_saving_bytes": single_summary["typed_saving_vs_matched_frontier_bytes"],
            "existing_seq32_d128_typed_ratio": float(single_summary["typed_ratio_vs_matched_frontier"]),
            "value_compatible_frontier_typed_bytes": frontier_summary["value_compatible_two_proof_frontier_typed_bytes"],
            "d128_attention_lookup_claims": row_map["d128_two_head_seq32_attention_route"]["lookup_claims"],
            "d128_attention_trace_rows": row_map["d128_two_head_seq32_attention_route"]["trace_rows"],
            "d128_attention_fused_proof_bytes": row_map["d128_two_head_seq32_attention_route"]["fused_or_single_bytes"],
            "d128_attention_split_raw_proof_bytes": row_map["d128_two_head_seq32_attention_route"]["split_or_reference_bytes"],
            "d128_attention_saving_bytes": row_map["d128_two_head_seq32_attention_route"]["saving_bytes"],
            "d128_attention_fused_ratio": row_map["d128_two_head_seq32_attention_route"]["ratio"],
            "d128_mlp_fused_typed_bytes": mlp_summary["fused_typed_bytes"],
            "d128_mlp_separate_typed_bytes": mlp_summary["separate_component_typed_bytes"],
            "d128_mlp_typed_saving_bytes": mlp_summary["typed_saving_bytes"],
            "d128_mlp_adapter_mismatches": mlp_summary["seq32_adapter_mismatches"],
            "d128_sequence_lookup_growth": row_map["d128_two_head_seq32_sequence_slope"]["lookup_growth"],
            "d128_sequence_trace_growth": row_map["d128_two_head_seq32_sequence_slope"]["trace_growth"],
            "d128_sequence_fused_proof_growth": row_map["d128_two_head_seq32_sequence_slope"]["fused_proof_growth"],
            "d128_sequence_target_saving_bytes": row_map["d128_two_head_seq32_sequence_slope"]["saving_bytes"],
            "d256_width_fused_proof_growth": row_map["width_axis_caution"]["fused_proof_growth"],
            "d256_width_fused_ratio": row_map["width_axis_caution"]["ratio"],
            "slope_table_recommended_next_gate": slope_summary["recommended_next_gate"],
        },
        "go_gate": [
            "source artifacts and exact sizes remain pinned",
            "d128 attention source output can be value-bound into the d128 MLP surface",
            "the new scoped boundary beats its matched split local frontier before any external comparison",
            "mutation gates reject source drift, envelope mismatch, VK mismatch, model-surface mismatch, and overclaim wording",
        ],
        "no_go_gate": [
            "source-to-MLP value adapter cannot be pinned without relabeling",
            "the scoped proof is equal or heavier than the matched split frontier",
            "the only positive story requires treating d256 seq64 as the primary path",
            "the result needs a full-block, speed, NANOZK, or production-throughput claim to sound interesting",
        ],
        "rows": rows,
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    validate_payload(payload, require_mutations=False, require_commitment=False)
    if include_mutations:
        mutation_results = run_mutations(payload)
        payload["mutation_results"] = mutation_results
        payload["mutations_checked"] = len(mutation_results)
        payload["mutations_rejected"] = sum(1 for item in mutation_results if item["rejected"])
        payload["all_mutations_rejected"] = all(item["rejected"] for item in mutation_results)
    payload["payload_commitment"] = commitment(payload_for_commitment(payload))
    validate_payload(payload, require_mutations=include_mutations)
    return payload


def validate_source_artifacts(payload: dict[str, Any]) -> None:
    source_artifacts = require_list(payload.get("source_artifacts"), "source artifacts")
    expect_equal(len(source_artifacts), len(EXPECTED_SOURCE_DESCRIPTORS), "source artifact count")
    by_id = {require_str(item.get("id"), "source id"): item for item in source_artifacts if isinstance(item, dict)}
    expect_equal(tuple(by_id), tuple(EXPECTED_SOURCE_DESCRIPTORS), "source artifact order")
    for source_id, expected in EXPECTED_SOURCE_DESCRIPTORS.items():
        item = require_dict(by_id.get(source_id), f"{source_id} descriptor")
        expect_equal(item.get("path"), expected["path"].relative_to(ROOT).as_posix(), f"{source_id} path")
        expect_equal(item.get("schema"), expected["schema"], f"{source_id} schema")
        expect_equal(item.get("decision"), expected["decision"], f"{source_id} decision")
        expect_equal(item.get("sha256"), expected["sha256"], f"{source_id} sha256")
        expect_equal(item.get("bytes"), expected["bytes"], f"{source_id} bytes")


def validate_rows(payload: dict[str, Any]) -> None:
    rows = require_list(payload.get("rows"), "rows")
    expect_equal([row.get("row_id") for row in rows if isinstance(row, dict)], list(ROW_IDS), "row id order")
    by_id = {require_str(require_dict(row, "row").get("row_id"), "row id"): require_dict(row, "row") for row in rows}
    for row_id in ROW_IDS:
        row = by_id[row_id]
        for key in ("row_id", "kind", "status", "metric_scope", "action", "interpretation"):
            require_str(row.get(key), f"{row_id}.{key}")

    champion = by_id["existing_seq32_d128_single_proof_champion"]
    expect_equal(champion["status"], "REGRESSION_BASELINE_GO", "champion status")
    expect_equal(champion["fused_or_single_bytes"], 42_068, "champion typed bytes")
    expect_equal(champion["split_or_reference_bytes"], 47_188, "champion frontier")
    expect_equal(champion["saving_bytes"], 5_120, "champion saving")
    expect_equal(champion["ratio"], 0.891498, "champion ratio")
    if "full block" not in champion["action"].replace("-", " ").replace("_", " "):
        raise ScopedBlockPreflightError("champion action must preserve full-block guardrail")

    attention = by_id["d128_two_head_seq32_attention_route"]
    expect_equal(attention["status"], "GO_ATTENTION_SOURCE_FOR_SCOPED_GATE", "d128 attention status")
    expect_equal(attention["lookup_claims"], 1_184, "d128 attention lookup claims")
    expect_equal(attention["trace_rows"], 2_048, "d128 attention trace rows")
    expect_equal(attention["fused_or_single_bytes"], 445_888, "d128 attention fused proof bytes")
    expect_equal(attention["split_or_reference_bytes"], 478_276, "d128 attention split bytes")
    expect_equal(attention["saving_bytes"], 32_388, "d128 attention saving")
    expect_equal(attention["ratio"], 0.932282, "d128 attention ratio")

    mlp = by_id["seq32_derived_d128_mlp_surface"]
    expect_equal(mlp["status"], "GO_MLP_SOURCE_FOR_SCOPED_GATE", "MLP status")
    expect_equal(mlp["fused_or_single_bytes"], 24_272, "MLP fused typed")
    expect_equal(mlp["split_or_reference_bytes"], 54_336, "MLP separate typed")
    expect_equal(mlp["saving_bytes"], 30_064, "MLP saving")
    expect_equal(mlp["adapter_mismatches"], 0, "MLP adapter mismatches")

    sequence = by_id["d128_two_head_seq32_sequence_slope"]
    expect_equal(sequence["lookup_growth"], 3.72973, "d128 sequence lookup growth")
    expect_equal(sequence["trace_growth"], 4.0, "d128 sequence trace growth")
    expect_equal(sequence["fused_proof_growth"], 1.080697, "d128 sequence fused growth")
    expect_equal(sequence["saving_bytes"], 40_317, "d128 sequence saving")
    expect_equal(sequence["ratio"], 0.922792, "d128 sequence ratio")

    width = by_id["width_axis_caution"]
    expect_equal(width["status"], "CAUTION_DO_NOT_JUMP_TO_D256_SEQ64_AS_PRIMARY_GATE", "width caution status")
    expect_equal(width["fused_proof_growth"], 1.842162, "d256 width fused proof growth")
    expect_equal(width["d64_to_d128_fused_proof_growth"], 1.760615, "d64 to d128 width fused proof growth")
    expect_equal(width["saving_bytes"], 30_143, "d256 width saving")
    expect_equal(width["ratio"], 0.964602, "d256 width ratio")

    next_gate = by_id["next_scoped_boundary_gate"]
    expect_equal(next_gate["status"], "ATTACK_NEXT", "next scoped gate status")
    expect_equal(next_gate["action"], RECOMMENDED_ACTION, "next scoped gate action")


def validate_summary(payload: dict[str, Any]) -> None:
    summary = require_dict(payload.get("summary"), "summary")
    expected = {
        "primary_next_gate": PRIMARY_NEXT_GATE,
        "stress_gate": STRESS_GATE,
        "recommended_action": RECOMMENDED_ACTION,
        "paper_claim_status": "NARROW_CLAIM_READY_FOR_SCOPED_BLOCK_PREFLIGHT_NOT_FULL_BLOCK",
        "proof_size_comparable_external_rows": 0,
        "existing_seq32_d128_single_typed_bytes": 42_068,
        "existing_seq32_d128_frontier_typed_bytes": 47_188,
        "existing_seq32_d128_typed_saving_bytes": 5_120,
        "existing_seq32_d128_typed_ratio": 0.891498,
        "value_compatible_frontier_typed_bytes": 47_188,
        "d128_attention_lookup_claims": 1_184,
        "d128_attention_trace_rows": 2_048,
        "d128_attention_fused_proof_bytes": 445_888,
        "d128_attention_split_raw_proof_bytes": 478_276,
        "d128_attention_saving_bytes": 32_388,
        "d128_attention_fused_ratio": 0.932282,
        "d128_mlp_fused_typed_bytes": 24_272,
        "d128_mlp_separate_typed_bytes": 54_336,
        "d128_mlp_typed_saving_bytes": 30_064,
        "d128_mlp_adapter_mismatches": 0,
        "d128_sequence_lookup_growth": 3.72973,
        "d128_sequence_trace_growth": 4.0,
        "d128_sequence_fused_proof_growth": 1.080697,
        "d128_sequence_target_saving_bytes": 40_317,
        "d256_width_fused_proof_growth": 1.842162,
        "d256_width_fused_ratio": 0.964602,
        "slope_table_recommended_next_gate": (
            "scoped_d128_seq32_transformer_block_boundary_preflight; "
            "d256_seq64_remains_a_stress_test_not_the_primary_paper_gate"
        ),
    }
    for key, value in expected.items():
        expect_equal(summary.get(key), value, f"summary.{key}")
    if summary["recommended_action"].startswith("IMPLEMENT_D256"):
        raise ScopedBlockPreflightError("recommended action must not promote d256 as the primary gate")


def validate_payload(
    payload: dict[str, Any],
    *,
    require_mutations: bool = True,
    require_commitment: bool = True,
) -> None:
    expect_equal(payload.get("schema"), SCHEMA, "schema")
    expect_equal(payload.get("issue"), ISSUE, "issue")
    expect_equal(payload.get("decision"), DECISION, "decision")
    expect_equal(payload.get("result"), RESULT, "result")
    claim_boundary = require_str(payload.get("claim_boundary"), "claim boundary")
    for token in ("SCOPED_D128_SEQ32", "NOT_FULL_BLOCK", "NOT_SPEED_CLAIM", "NOT_EXTERNAL_COMPARISON"):
        if token not in claim_boundary:
            raise ScopedBlockPreflightError(f"claim boundary missing {token}")
    expect_equal(payload.get("timing_policy"), TIMING_POLICY, "timing policy")
    validate_source_artifacts(payload)
    validate_summary(payload)
    validate_rows(payload)

    non_claims = tuple(require_list(payload.get("non_claims"), "non claims"))
    expect_equal(non_claims, NON_CLAIMS, "non claims")
    validation_commands = tuple(require_list(payload.get("validation_commands"), "validation commands"))
    expect_equal(validation_commands, VALIDATION_COMMANDS, "validation commands")
    go_gate = tuple(require_list(payload.get("go_gate"), "go gate"))
    no_go_gate = tuple(require_list(payload.get("no_go_gate"), "no-go gate"))
    if len(go_gate) != 4 or len(no_go_gate) != 4:
        raise ScopedBlockPreflightError("GO/NO-GO gates must each have four items")
    if not any("matched split local frontier" in item for item in go_gate):
        raise ScopedBlockPreflightError("GO gate must compare only against matched split local frontier")
    if not any("full-block" in item for item in no_go_gate):
        raise ScopedBlockPreflightError("NO-GO gate must reject full-block promotion")

    if require_mutations:
        expect_equal(payload.get("mutations_checked"), len(MUTATION_NAMES), "mutation count")
        expect_equal(payload.get("mutations_rejected"), len(MUTATION_NAMES), "mutation rejected count")
        expect_equal(payload.get("all_mutations_rejected"), True, "all mutations rejected")
        mutation_results = require_list(payload.get("mutation_results"), "mutation results")
        expect_equal([item.get("name") for item in mutation_results if isinstance(item, dict)], list(MUTATION_NAMES), "mutation order")
        for item in mutation_results:
            result = require_dict(item, "mutation result")
            expect_equal(result.get("rejected"), True, f"{result.get('name')} rejected")
            require_str(result.get("error"), f"{result.get('name')} error")

    if require_commitment:
        expected_commitment = commitment(payload_for_commitment(payload))
        expect_equal(payload.get("payload_commitment"), expected_commitment, "payload commitment")


def mutate_payload(payload: dict[str, Any], name: str) -> dict[str, Any]:
    mutated = copy.deepcopy(payload)
    if name == "source_digest_drift":
        mutated["source_artifacts"][0]["sha256"] = "0" * 64
    elif name == "source_size_drift":
        mutated["source_artifacts"][1]["bytes"] += 1
    elif name == "issue_drift":
        mutated["issue"] = 716
    elif name == "decision_drift":
        mutated["decision"] = "GO_FULL_BLOCK_NOW"
    elif name == "next_gate_drift":
        mutated["summary"]["primary_next_gate"] = "d256_h2_seq64_primary_gate"
    elif name == "d256_primary_overclaim":
        mutated["summary"]["recommended_action"] = "IMPLEMENT_D256_SEQ64_BEFORE_SCOPED_D128_SEQ32"
    elif name == "external_comparison_overclaim":
        mutated["summary"]["proof_size_comparable_external_rows"] = 1
    elif name == "full_block_overclaim":
        mutated["claim_boundary"] = mutated["claim_boundary"].replace("NOT_FULL_BLOCK_", "")
    elif name == "seq32_champion_metric_drift":
        mutated["rows"][0]["saving_bytes"] += 1
    elif name == "d128_attention_metric_drift":
        mutated["rows"][1]["fused_or_single_bytes"] += 1
    elif name == "mlp_surface_metric_drift":
        mutated["rows"][2]["adapter_mismatches"] = 1
    elif name == "sequence_slope_drift":
        mutated["rows"][3]["lookup_growth"] = 1.0
    elif name == "width_caution_drift":
        mutated["rows"][4]["status"] = "GO_JUMP_TO_D256_SEQ64"
    elif name == "row_missing_required_field":
        del mutated["rows"][5]["action"]
    elif name == "non_claim_removed":
        mutated["non_claims"] = mutated["non_claims"][:-1]
    elif name == "validation_command_drift":
        mutated["validation_commands"][0] = "python3.10 scripts/other.py"
    elif name == "payload_commitment_drift":
        mutated["payload_commitment"] = "blake2b-256:" + "0" * 64
    else:
        raise KeyError(f"unknown mutation: {name}")
    return mutated


def run_mutations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for name in MUTATION_NAMES:
        mutated = mutate_payload(payload, name)
        try:
            validate_payload(
                mutated,
                require_mutations=False,
                require_commitment=name == "payload_commitment_drift",
            )
        except ScopedBlockPreflightError as error:
            results.append({"name": name, "rejected": True, "error": str(error)})
        else:
            results.append({"name": name, "rejected": False, "error": "mutation accepted"})
    return results


def ensure_output_path(path: pathlib.Path, root: pathlib.Path) -> pathlib.Path:
    candidate = path if path.is_absolute() else ROOT / path
    try:
        resolved = candidate.resolve()
        root_resolved = root.resolve()
    except OSError as error:
        raise ScopedBlockPreflightError(f"unable to resolve output path: {path}") from error
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ScopedBlockPreflightError(f"output path must stay inside {root.relative_to(ROOT)}: {path}")
    return resolved


def reject_same_output_paths(paths: tuple[pathlib.Path, ...]) -> None:
    resolved = [path.resolve() for path in paths]
    if len(set(resolved)) != len(resolved):
        raise ScopedBlockPreflightError("output paths must be different files")


def checked_output_paths(
    json_path: pathlib.Path,
    tsv_path: pathlib.Path,
    md_path: pathlib.Path,
) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    checked_json = ensure_output_path(json_path, EVIDENCE_DIR)
    checked_tsv = ensure_output_path(tsv_path, EVIDENCE_DIR)
    checked_md = ensure_output_path(md_path, DOCS_DIR)
    reject_same_output_paths((checked_json, checked_tsv, checked_md))
    return checked_json, checked_tsv, checked_md


def atomic_write_text(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        tmp_path = pathlib.Path(handle.name)
        handle.write(text)
    tmp_path.replace(path)


def write_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    output = ensure_output_path(path, EVIDENCE_DIR)
    validate_payload(payload)
    atomic_write_text(output, json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n")


def format_cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def write_tsv(path: pathlib.Path, payload: dict[str, Any]) -> None:
    output = ensure_output_path(path, EVIDENCE_DIR)
    validate_payload(payload)
    rows = require_list(payload["rows"], "rows")
    from io import StringIO

    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=TSV_COLUMNS, delimiter="\t", extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: format_cell(require_dict(row, "row").get(key)) for key in TSV_COLUMNS})
    atomic_write_text(output, handle.getvalue())


def write_md(path: pathlib.Path, payload: dict[str, Any]) -> None:
    output = ensure_output_path(path, DOCS_DIR)
    validate_payload(payload)
    summary = require_dict(payload["summary"], "summary")
    rows = require_list(payload["rows"], "rows")
    row_lines = [
        "| row | status | scope | bytes | reference | saving | ratio | action |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for item in rows:
        row = require_dict(item, "row")
        row_lines.append(
            "| {row_id} | `{status}` | {scope} | {bytes} | {reference} | {saving} | {ratio} | {action} |".format(
                row_id=str(row["row_id"]).replace("_", " "),
                status=row["status"],
                scope=row["metric_scope"],
                bytes=f"`{row['fused_or_single_bytes']:,}`" if isinstance(row.get("fused_or_single_bytes"), int) else "",
                reference=f"`{row['split_or_reference_bytes']:,}`" if isinstance(row.get("split_or_reference_bytes"), int) else "",
                saving=f"`{row['saving_bytes']:,}`" if isinstance(row.get("saving_bytes"), int) else "",
                ratio=f"`{row['ratio']}`" if row.get("ratio") is not None else "",
                action=str(row["action"]).replace("_", " "),
            )
        )
    non_claim_lines = "\n".join(f"- {claim}." for claim in NON_CLAIMS)
    command_lines = "\n".join(VALIDATION_COMMANDS)
    md = f"""# Scoped D128 Seq32 Block Boundary Preflight

Issue: #{ISSUE}

## Decision

`{DECISION}`

Result:

`{RESULT}`

This is a preflight gate, not a new proof object. It binds the current checked
evidence into the next execution decision: attack the scoped `d128 seq32`
boundary before promoting `d256 seq64` into the primary path.

## Human Meaning

The next paper-grade experiment should be a scoped boundary, not a bigger
stress test for its own sake. We already have one checked `seq32 + d128` native
boundary that saves `{summary['existing_seq32_d128_typed_saving_bytes']:,}`
typed bytes against its matched frontier. We also have a `d128` two-head
`seq32` attention route that saves `{summary['d128_attention_saving_bytes']:,}`
raw proof bytes against matched source plus sidecar, and a seq32-derived `d128`
MLP surface that saves `{summary['d128_mlp_typed_saving_bytes']:,}` typed bytes
against its separate-component frontier.

The slope table says why this is the right next gate. On the d128 sequence
axis, lookup work grows `{summary['d128_sequence_lookup_growth']}x` and trace
rows grow `{summary['d128_sequence_trace_growth']}x`, while fused proof bytes
grow only `{summary['d128_sequence_fused_proof_growth']}x`. The width axis is
different: d128 to d256 fused proof bytes grow
`{summary['d256_width_fused_proof_growth']}x`, so d256 stays a stress test
after this scoped gate, not the main paper path.

## Checked Rows

{chr(10).join(row_lines)}

## GO Gate

- source artifacts and exact sizes remain pinned;
- d128 attention source output can be value-bound into the d128 MLP surface;
- the new scoped boundary beats its matched split local frontier before any external comparison;
- mutation gates reject source drift, envelope mismatch, VK mismatch, model-surface mismatch, and overclaim wording.

## NO-GO Gate

- source-to-MLP value adapter cannot be pinned without relabeling;
- the scoped proof is equal or heavier than the matched split frontier;
- the only positive story requires treating d256 seq64 as the primary path;
- the result needs a full-block, speed, NANOZK, or production-throughput claim to sound interesting.

## Evidence

- JSON: `docs/engineering/evidence/zkai-scoped-d128-seq32-block-boundary-preflight-2026-05.json`
- TSV: `docs/engineering/evidence/zkai-scoped-d128-seq32-block-boundary-preflight-2026-05.tsv`
- Slope table: `docs/engineering/evidence/zkai-proof-pressure-slope-table-2026-05.json`
- Route matrix: `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`
- Seq32 one-proof champion: `docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.json`

The gate rejects `{len(MUTATION_NAMES)} / {len(MUTATION_NAMES)}` mutation cases
covering source drift, issue drift, next-gate drift, d256 overclaim, external
comparison overclaim, full-block overclaim, row metric drift, non-claim drift,
validation-command drift, and payload-commitment drift.

## Non-Claims

{non_claim_lines}

## Reproduce

```bash
{command_lines}
```
"""
    atomic_write_text(output, md)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path, default=JSON_OUT)
    parser.add_argument("--write-tsv", type=pathlib.Path, default=TSV_OUT)
    parser.add_argument("--write-md", type=pathlib.Path, default=MD_OUT)
    args = parser.parse_args(argv)

    json_path, tsv_path, md_path = checked_output_paths(args.write_json, args.write_tsv, args.write_md)
    payload = build_payload()
    write_json(json_path, payload)
    write_tsv(tsv_path, payload)
    write_md(md_path, payload)
    print(
        f"{DECISION}: {payload['mutations_rejected']}/{payload['mutations_checked']} mutations rejected; "
        f"next={PRIMARY_NEXT_GATE}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
