#!/usr/bin/env python3.10
"""Select the next wide proof-pressure grid rows without overclaiming them."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
ROUTE_MATRIX_PATH = EVIDENCE_DIR / "zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json"
FULLER_GRID_PATH = EVIDENCE_DIR / "zkai-attention-kv-fuller-crossing-grid-2026-05.json"
CLAIM_PACK_PATH = EVIDENCE_DIR / "zkai-proof-pressure-scaling-claim-pack-2026-05.json"
JSON_OUT = EVIDENCE_DIR / "zkai-proof-pressure-wide-grid-selector-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-proof-pressure-wide-grid-selector-2026-05.tsv"

SCHEMA = "zkai-proof-pressure-wide-grid-selector-v1"
DECISION = "GO_WIDE_GRID_SELECTOR_KEEP_D64_D128_D256_AS_FALSIFICATION_TARGETS"
ROUTE_ID = "local_stwo_attention_kv_wide_grid_selector_from_checked_route_matrix"
ISSUE = 715
CLAIM_BOUNDARY = (
    "SELECTS_D64_D128_D256_ATTENTION_ROUTE_TARGETS_FROM_CHECKED_D8_D16_D32_ROUTE_MATRIX;"
    "NO_D64_D128_D256_ATTENTION_PROOF_ROWS_YET;"
    "NOT_A_WIDE_GRID_RESULT_NOT_A_NANOZK_COMPARISON_NOT_A_FULL_BLOCK_PROOF"
)
TIMING_POLICY = "proof_existence_and_byte_accounting_only_not_public_benchmark"

ROUTE_MATRIX_SHA256 = "cb2601042c1ae8fbbc081d0962b278f7aff4a7db633adbfbdb2b7124b7f03dc1"
FULLER_GRID_SHA256 = "cabd3e0294e293f56d2b542ded040c8bde20fe2bec1bc5280ba85968a7bc84c1"
CLAIM_PACK_SHA256 = "369da58f91fd9575b81c4287d1b2cb8a8bdcc5e1af1a600c23c5d24e65c2cdc1"

REQUESTED_WIDTHS = (64, 128, 256)
REQUESTED_HEAD_COUNTS = (1, 2)
REQUESTED_SEQUENCES = (16, 32, 64)
SUPPORTED_ATTENTION_WIDTHS = (8, 16, 32)
SUPPORTED_ATTENTION_SEQUENCES = (8, 16, 32)
EXPECTED_MATCH_STATUS = "GO_MATCHED_SOURCE_PLUS_LOGUP_SIDECAR_COMPARATOR_RECORDED"

VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_proof_pressure_wide_grid_selector_gate.py --write-json docs/engineering/evidence/zkai-proof-pressure-wide-grid-selector-2026-05.json --write-tsv docs/engineering/evidence/zkai-proof-pressure-wide-grid-selector-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_proof_pressure_wide_grid_selector_gate.py scripts/tests/test_zkai_proof_pressure_wide_grid_selector_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_proof_pressure_wide_grid_selector_gate",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

NON_CLAIMS = (
    "not a d64, d128, or d256 attention proof result",
    "not a full transformer block proof",
    "not exact real-valued Softmax",
    "not a NANOZK proof-size comparison",
    "not timing evidence",
    "not production zkML readiness",
    "does not widen the claim beyond checked d8, d16, and d32 attention rows",
)

TSV_COLUMNS = (
    "priority",
    "profile_id",
    "key_width",
    "head_count",
    "steps_per_head",
    "selector_status",
    "why_this_row",
    "go_gate",
    "no_go_gate",
)

MUTATION_NAMES = (
    "decision_drift",
    "claim_boundary_overclaim",
    "source_artifact_digest_drift",
    "wide_row_smuggling",
    "requested_widths_drift",
    "current_row_count_drift",
    "d32_sequence_signal_drift",
    "width_pressure_signal_drift",
    "accounting_triplet_drift",
    "candidate_order_drift",
    "validation_command_drift",
    "non_claim_removed",
    "payload_commitment_drift",
)


class ProofPressureWideGridSelectorError(ValueError):
    pass


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def commitment(value: Any) -> str:
    digest = hashlib.blake2b(digest_size=32)
    digest.update(b"ptvm:zkai:proof-pressure-wide-grid-selector:v1\0")
    digest.update(canonical_bytes(value))
    return f"blake2b-256:{digest.hexdigest()}"


def ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        raise ProofPressureWideGridSelectorError("ratio denominator must be nonzero")
    return round(numerator / denominator, 6)


def load_json(path: pathlib.Path, expected_sha256: str, label: str) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    actual = sha256_bytes(raw)
    if actual != expected_sha256:
        raise ProofPressureWideGridSelectorError(f"{label} digest drift")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ProofPressureWideGridSelectorError(f"{label} must be an object")
    return payload, raw


def row_by_id(rows: list[dict[str, Any]], profile_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("profile_id") == profile_id:
            return row
    raise ProofPressureWideGridSelectorError(f"missing route row: {profile_id}")


def load_sources() -> tuple[dict[str, dict[str, Any]], dict[str, bytes]]:
    route_matrix, route_raw = load_json(ROUTE_MATRIX_PATH, ROUTE_MATRIX_SHA256, "route matrix")
    fuller_grid, fuller_raw = load_json(FULLER_GRID_PATH, FULLER_GRID_SHA256, "fuller crossing grid")
    claim_pack, claim_raw = load_json(CLAIM_PACK_PATH, CLAIM_PACK_SHA256, "claim pack")
    return (
        {
            "route_matrix": route_matrix,
            "fuller_grid": fuller_grid,
            "claim_pack": claim_pack,
        },
        {
            "route_matrix": route_raw,
            "fuller_grid": fuller_raw,
            "claim_pack": claim_raw,
        },
    )


def source_artifacts(raws: dict[str, bytes]) -> list[dict[str, Any]]:
    return [
        {
            "id": "fused_softmax_route_matrix",
            "path": str(ROUTE_MATRIX_PATH.relative_to(ROOT)),
            "sha256": sha256_bytes(raws["route_matrix"]),
            "size_bytes": len(raws["route_matrix"]),
        },
        {
            "id": "fuller_crossing_grid",
            "path": str(FULLER_GRID_PATH.relative_to(ROOT)),
            "sha256": sha256_bytes(raws["fuller_grid"]),
            "size_bytes": len(raws["fuller_grid"]),
        },
        {
            "id": "proof_pressure_claim_pack",
            "path": str(CLAIM_PACK_PATH.relative_to(ROOT)),
            "sha256": sha256_bytes(raws["claim_pack"]),
            "size_bytes": len(raws["claim_pack"]),
        },
    ]


def requested_grid_rows() -> list[dict[str, Any]]:
    rows = []
    for width in REQUESTED_WIDTHS:
        for head_count in REQUESTED_HEAD_COUNTS:
            for steps in REQUESTED_SEQUENCES:
                rows.append(
                    {
                        "profile_id": f"d{width}_h{head_count}_seq{steps}",
                        "key_width": width,
                        "head_count": head_count,
                        "steps_per_head": steps,
                        "selector_status": "MISSING_SOURCE_BACKED_ATTENTION_ROUTE_ROW",
                    }
                )
    return rows


def build_current_signal(route_matrix: dict[str, Any], fuller_grid: dict[str, Any]) -> dict[str, Any]:
    try:
        rows = route_matrix.get("route_rows")
        if not isinstance(rows, list):
            raise ProofPressureWideGridSelectorError("route matrix rows missing")
        proved = [row for row in rows if row.get("matched_source_sidecar_status") == EXPECTED_MATCH_STATUS]
        if len(proved) != 14:
            raise ProofPressureWideGridSelectorError("current route row count drift")
        for row in proved:
            fused_saving = row["fused_saves_vs_source_plus_sidecar_bytes"]
            if not isinstance(fused_saving, (int, float)) or isinstance(fused_saving, bool):
                raise ProofPressureWideGridSelectorError("route matrix signal field type drift")
            if fused_saving <= 0:
                raise ProofPressureWideGridSelectorError("current fused saving sign drift")

        d32_seq8 = row_by_id(proved, "d32_two_head_seq8")
        d32_seq32 = row_by_id(proved, "d32_two_head_seq32")
        d8_seq32 = row_by_id(proved, "d8_two_head_seq32")
        d8_h1 = row_by_id(proved, "d8_single_head_seq8")
        d32_h1 = row_by_id(proved, "d32_single_head_seq8")

        fuller_summary = fuller_grid.get("summary")
        if not isinstance(fuller_summary, dict):
            raise ProofPressureWideGridSelectorError("fuller grid summary missing")

        aggregates = route_matrix.get("aggregate_metrics")
        if not isinstance(aggregates, dict):
            raise ProofPressureWideGridSelectorError("route matrix aggregate metrics missing")

        return {
            "checked_attention_route_rows": len(proved),
            "checked_widths": sorted({row["key_width"] for row in proved}),
            "checked_head_counts": sorted({row["head_count"] for row in proved}),
            "checked_sequences": sorted({row["steps_per_head"] for row in proved}),
            "all_checked_rows_have_positive_fused_saving": True,
            "raw_fused_bytes_total": aggregates["matched_fused_proof_size_bytes_total"],
            "raw_split_bytes_total": aggregates["matched_source_plus_sidecar_raw_proof_bytes_total"],
            "raw_saving_bytes_total": aggregates["matched_fused_savings_bytes_total"],
            "fuller_grid_cells": fuller_summary["grid_cell_count"],
            "fuller_grid_proved_cells": fuller_summary["proved_cell_count"],
            "fuller_grid_missing_cells": fuller_summary["missing_cell_count"],
            "d32_two_head_seq8_to_seq32": {
                "lookup_claim_growth": ratio(d32_seq32["lookup_claims"], d32_seq8["lookup_claims"]),
                "trace_row_growth": ratio(d32_seq32["trace_rows"], d32_seq8["trace_rows"]),
                "fused_raw_proof_growth": ratio(d32_seq32["fused_proof_size_bytes"], d32_seq8["fused_proof_size_bytes"]),
                "split_raw_proof_growth": ratio(
                    d32_seq32["source_plus_sidecar_raw_proof_bytes"],
                    d32_seq8["source_plus_sidecar_raw_proof_bytes"],
                ),
                "saving_growth": ratio(
                    d32_seq32["fused_saves_vs_source_plus_sidecar_bytes"],
                    d32_seq8["fused_saves_vs_source_plus_sidecar_bytes"],
                ),
            },
            "d8_to_d32_two_head_seq32_width_pressure": {
                "lookup_claim_growth": ratio(d32_seq32["lookup_claims"], d8_seq32["lookup_claims"]),
                "fused_raw_proof_growth": ratio(d32_seq32["fused_proof_size_bytes"], d8_seq32["fused_proof_size_bytes"]),
                "split_raw_proof_growth": ratio(
                    d32_seq32["source_plus_sidecar_raw_proof_bytes"],
                    d8_seq32["source_plus_sidecar_raw_proof_bytes"],
                ),
            },
            "d8_to_d32_single_head_seq8_width_pressure": {
                "lookup_claim_growth": ratio(d32_h1["lookup_claims"], d8_h1["lookup_claims"]),
                "fused_raw_proof_growth": ratio(d32_h1["fused_proof_size_bytes"], d8_h1["fused_proof_size_bytes"]),
                "split_raw_proof_growth": ratio(
                    d32_h1["source_plus_sidecar_raw_proof_bytes"],
                    d8_h1["source_plus_sidecar_raw_proof_bytes"],
                ),
                "saving_growth": ratio(
                    d32_h1["fused_saves_vs_source_plus_sidecar_bytes"],
                    d8_h1["fused_saves_vs_source_plus_sidecar_bytes"],
                ),
            },
        }
    except KeyError as err:
        raise ProofPressureWideGridSelectorError("route matrix signal field missing") from err


def build_accounting_triplet_signal(claim_pack: dict[str, Any]) -> dict[str, Any]:
    rows = claim_pack.get("fused_vs_split_rows")
    if not isinstance(rows, list):
        raise ProofPressureWideGridSelectorError("claim pack fused rows missing")
    attention_rows = [row for row in rows if row.get("category") == "attention_fused_vs_split"]
    if len(attention_rows) != 10:
        raise ProofPressureWideGridSelectorError("attention typed row count drift")
    statement_rows = [row for row in rows if row.get("row_id") == "seq32_d128_statement_only_probe_b"]
    if len(statement_rows) != 1:
        raise ProofPressureWideGridSelectorError("statement bound row drift")
    summary = claim_pack.get("summary")
    accounting_status = claim_pack.get("accounting_status")
    if not isinstance(summary, dict) or not isinstance(accounting_status, dict):
        raise ProofPressureWideGridSelectorError("claim pack accounting summary missing")

    try:
        return {
            "status": (
                "CARRIES_TYPED_JSON_AND_BINARY_RAW_CONTEXT_FROM_CLAIM_PACK;"
                "RAW_ROUTE_MATRIX_WIDTH_SELECTOR_REMAINS_SEPARATE"
            ),
            "guardrail": accounting_status["guardrail"],
            "attention_typed_rows": len(attention_rows),
            "attention_typed_bytes_total": sum(row["typed_bytes"] for row in attention_rows),
            "attention_json_bytes_total": sum(row["json_bytes"] for row in attention_rows),
            "attention_typed_savings_bytes_total": summary["attention_typed_savings_bytes_total"],
            "attention_raw_proof_savings_bytes_total": summary["attention_raw_proof_savings_bytes_total"],
            "binary_raw_available_rows": sum(1 for row in rows if row.get("binary_raw_bytes") is not None),
            "binary_raw_missing_rows": sum(1 for row in rows if row.get("binary_raw_bytes") is None),
            "current_best_inner_policy_bound_row": {
                "row_id": statement_rows[0]["row_id"],
                "typed_bytes": statement_rows[0]["typed_bytes"],
                "json_bytes": statement_rows[0]["json_bytes"],
                "binary_raw_bytes": statement_rows[0]["binary_raw_bytes"],
                "matched_frontier_typed_bytes": statement_rows[0]["matched_frontier_typed_bytes"],
                "typed_saving_bytes": statement_rows[0]["typed_saving_bytes"],
            },
        }
    except KeyError as err:
        raise ProofPressureWideGridSelectorError("claim pack accounting field missing") from err


def build_requested_grid_signal(current_signal: dict[str, Any]) -> dict[str, Any]:
    rows = requested_grid_rows()
    checked_widths = set(current_signal["checked_widths"])
    source_backed_rows = [row for row in rows if row["key_width"] in checked_widths]
    return {
        "requested_widths": list(REQUESTED_WIDTHS),
        "requested_head_counts": list(REQUESTED_HEAD_COUNTS),
        "requested_sequences": list(REQUESTED_SEQUENCES),
        "requested_cell_count": len(rows),
        "source_backed_requested_cell_count": len(source_backed_rows),
        "missing_requested_cell_count": len(rows) - len(source_backed_rows),
        "missing_requested_widths": [width for width in REQUESTED_WIDTHS if width not in checked_widths],
        "requested_rows": rows,
        "selector_status": "NO_D64_D128_D256_ATTENTION_ROUTE_ROWS_YET",
    }


def build_candidate_order() -> list[dict[str, Any]]:
    return [
        {
            "priority": 1,
            "profile_id": "d64_h2_seq32",
            "key_width": 64,
            "head_count": 2,
            "steps_per_head": 32,
            "selector_status": "FIRST_FALSIFICATION_ROW",
            "why_this_row": "extends the current d32 two-head seq32 high-lookup signal by width only",
            "go_gate": "source, sidecar, and fused native proof rows exist and fused beats matched split without widening the claim boundary",
            "no_go_gate": "width pressure removes the fused saving or proof generation cannot stay within bounded local artifact limits",
        },
        {
            "priority": 2,
            "profile_id": "d64_h1_seq8",
            "key_width": 64,
            "head_count": 1,
            "steps_per_head": 8,
            "selector_status": "CHEAP_WIDTH_SLOPE_ROW",
            "why_this_row": "isolates width pressure before spending on seq32",
            "go_gate": "fused and split rows quantify d32-to-d64 width growth under the cheapest attention shape",
            "no_go_gate": "proof bytes grow roughly with width and savings shrink versus the d32 single-head row",
        },
        {
            "priority": 3,
            "profile_id": "d64_h2_seq16",
            "key_width": 64,
            "head_count": 2,
            "steps_per_head": 16,
            "selector_status": "MIDPOINT_GRID_ROW",
            "why_this_row": "bridges the cheap d64 width row and the seq32 falsification row",
            "go_gate": "keeps d64 sequence-axis growth bounded and still fused-smaller-than-split",
            "no_go_gate": "midpoint already loses the fused saving or breaks artifact limits",
        },
        {
            "priority": 4,
            "profile_id": "d128_h2_seq32",
            "key_width": 128,
            "head_count": 2,
            "steps_per_head": 32,
            "selector_status": "ONLY_AFTER_D64_GO",
            "why_this_row": "approaches model-width relevance, but should not be attacked before d64 falsifies or confirms the slope",
            "go_gate": "d64 rows are source-backed and the d128 row keeps a positive fused-vs-split saving",
            "no_go_gate": "d64 already shows width pressure dominates lookup amortization",
        },
        {
            "priority": 5,
            "profile_id": "d256_h2_seq32",
            "key_width": 256,
            "head_count": 2,
            "steps_per_head": 32,
            "selector_status": "ONLY_AFTER_D128_GO_OR_GENERIC_BACKEND",
            "why_this_row": "tests the aspirational wide frontier after the proving path is no longer copy-per-width",
            "go_gate": "generic or generated backend exists and d128 stays structurally positive",
            "no_go_gate": "copy-per-width engineering dominates research signal or d128 fails",
        },
    ]


def build_interpretation() -> dict[str, Any]:
    return {
        "human_read": (
            "The current evidence says the lookup-heavy sequence direction is promising, but width is the stress test. "
            "Going wider from d8 to d32 at fixed seq32 keeps lookup claims flat while proof bytes grow about 2.26x. "
            "So d64/d128/d256 are not victory laps; they are the next way to check whether the paper claim survives model width."
        ),
        "paper_relevance": (
            "A paper-grade result needs the fused-vs-split saving to survive beyond the d8/d16/d32 grid. "
            "The selector therefore promotes d64 two-head seq32 as the first falsification row and keeps d128/d256 gated."
        ),
        "research_recommendation": (
            "Do d64_h2_seq32 first if the goal is the direct breakthrough gate. "
            "Do d64_h1_seq8 first if the goal is the cheapest width-slope sanity check."
        ),
    }


def build_payload() -> dict[str, Any]:
    sources, raws = load_sources()
    expected_source_artifacts = source_artifacts(raws)
    current_signal = build_current_signal(sources["route_matrix"], sources["fuller_grid"])
    current_signal["accounting_triplet_signal"] = build_accounting_triplet_signal(sources["claim_pack"])
    requested_signal = build_requested_grid_signal(current_signal)
    payload = {
        "schema": SCHEMA,
        "decision": DECISION,
        "route_id": ROUTE_ID,
        "issue": ISSUE,
        "claim_boundary": CLAIM_BOUNDARY,
        "timing_policy": TIMING_POLICY,
        "source_artifacts": expected_source_artifacts,
        "current_signal": current_signal,
        "requested_grid_signal": requested_signal,
        "candidate_order": build_candidate_order(),
        "interpretation": build_interpretation(),
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    payload["mutation_result"] = run_mutations(payload, expected_source_artifacts)
    payload["payload_commitment"] = commitment({k: v for k, v in payload.items() if k != "payload_commitment"})
    validate_payload(payload, expected_source_artifacts)
    return payload


def validate_payload(payload: dict[str, Any], expected_source_artifacts: list[dict[str, Any]]) -> None:
    if payload.get("schema") != SCHEMA:
        raise ProofPressureWideGridSelectorError("schema drift")
    if payload.get("decision") != DECISION:
        raise ProofPressureWideGridSelectorError("decision drift")
    if payload.get("claim_boundary") != CLAIM_BOUNDARY:
        raise ProofPressureWideGridSelectorError("claim_boundary drift")
    if payload.get("source_artifacts") != expected_source_artifacts:
        raise ProofPressureWideGridSelectorError("source artifact drift")
    current = payload.get("current_signal")
    if not isinstance(current, dict):
        raise ProofPressureWideGridSelectorError("current signal missing")
    if current.get("checked_attention_route_rows") != 14:
        raise ProofPressureWideGridSelectorError("current route row count drift")
    if current.get("checked_widths") != list(SUPPORTED_ATTENTION_WIDTHS):
        raise ProofPressureWideGridSelectorError("checked widths drift")
    if current.get("raw_fused_bytes_total") != 1_145_173:
        raise ProofPressureWideGridSelectorError("raw fused total drift")
    if current.get("raw_split_bytes_total") != 1_411_498:
        raise ProofPressureWideGridSelectorError("raw split total drift")
    if current.get("raw_saving_bytes_total") != 266_325:
        raise ProofPressureWideGridSelectorError("raw saving total drift")
    d32_seq = current.get("d32_two_head_seq8_to_seq32")
    if not isinstance(d32_seq, dict) or d32_seq.get("lookup_claim_growth") != 11.384615:
        raise ProofPressureWideGridSelectorError("d32 sequence signal drift")
    if d32_seq.get("fused_raw_proof_growth") != 1.193955:
        raise ProofPressureWideGridSelectorError("d32 sequence proof-growth drift")
    width_pressure = current.get("d8_to_d32_two_head_seq32_width_pressure")
    if not isinstance(width_pressure, dict) or width_pressure.get("fused_raw_proof_growth") != 2.263739:
        raise ProofPressureWideGridSelectorError("width pressure signal drift")
    accounting = current.get("accounting_triplet_signal")
    if not isinstance(accounting, dict):
        raise ProofPressureWideGridSelectorError("accounting triplet missing")
    if accounting.get("attention_typed_rows") != 10:
        raise ProofPressureWideGridSelectorError("accounting typed row count drift")
    if accounting.get("attention_typed_bytes_total") != 234_296:
        raise ProofPressureWideGridSelectorError("accounting typed total drift")
    if accounting.get("attention_typed_savings_bytes_total") != 51_288:
        raise ProofPressureWideGridSelectorError("accounting triplet drift")
    if accounting.get("attention_json_bytes_total") != 629_466:
        raise ProofPressureWideGridSelectorError("accounting JSON drift")
    if accounting.get("attention_raw_proof_savings_bytes_total") != 266_325:
        raise ProofPressureWideGridSelectorError("accounting raw drift")
    if accounting.get("binary_raw_available_rows") != 2 or accounting.get("binary_raw_missing_rows") != 10:
        raise ProofPressureWideGridSelectorError("binary raw availability drift")
    requested = payload.get("requested_grid_signal")
    if not isinstance(requested, dict):
        raise ProofPressureWideGridSelectorError("requested grid signal missing")
    if requested.get("requested_widths") != list(REQUESTED_WIDTHS):
        raise ProofPressureWideGridSelectorError("requested widths drift")
    if requested.get("source_backed_requested_cell_count") != 0:
        raise ProofPressureWideGridSelectorError("wide row smuggling")
    if requested.get("missing_requested_widths") != list(REQUESTED_WIDTHS):
        raise ProofPressureWideGridSelectorError("missing requested widths drift")
    candidates = payload.get("candidate_order")
    if not isinstance(candidates, list) or [row.get("profile_id") for row in candidates] != [
        "d64_h2_seq32",
        "d64_h1_seq8",
        "d64_h2_seq16",
        "d128_h2_seq32",
        "d256_h2_seq32",
    ]:
        raise ProofPressureWideGridSelectorError("candidate order drift")
    if payload.get("validation_commands") != list(VALIDATION_COMMANDS):
        raise ProofPressureWideGridSelectorError("validation command drift")
    if payload.get("non_claims") != list(NON_CLAIMS):
        raise ProofPressureWideGridSelectorError("non_claims drift")
    if "mutation_result" in payload:
        mutation = payload.get("mutation_result")
        if not isinstance(mutation, dict) or mutation.get("all_mutations_rejected") is not True:
            raise ProofPressureWideGridSelectorError("mutation result drift")
    if "payload_commitment" in payload:
        expected_commitment = commitment({k: v for k, v in payload.items() if k != "payload_commitment"})
        if payload.get("payload_commitment") != expected_commitment:
            raise ProofPressureWideGridSelectorError("payload commitment drift")


def mutation_cases(payload: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    return (
        ("decision_drift", lambda p: p.__setitem__("decision", "GO_WIDE_GRID_PROVED")),
        ("claim_boundary_overclaim", lambda p: p.__setitem__("claim_boundary", "D64_D128_D256_ATTENTION_ROWS_PROVED")),
        ("source_artifact_digest_drift", lambda p: p["source_artifacts"][0].__setitem__("sha256", "0" * 64)),
        ("wide_row_smuggling", lambda p: p["requested_grid_signal"].__setitem__("source_backed_requested_cell_count", 1)),
        ("requested_widths_drift", lambda p: p["requested_grid_signal"].__setitem__("requested_widths", [64, 128])),
        ("current_row_count_drift", lambda p: p["current_signal"].__setitem__("checked_attention_route_rows", 15)),
        (
            "d32_sequence_signal_drift",
            lambda p: p["current_signal"]["d32_two_head_seq8_to_seq32"].__setitem__("lookup_claim_growth", 1.0),
        ),
        (
            "width_pressure_signal_drift",
            lambda p: p["current_signal"]["d8_to_d32_two_head_seq32_width_pressure"].__setitem__(
                "fused_raw_proof_growth", 1.0
            ),
        ),
        (
            "accounting_triplet_drift",
            lambda p: p["current_signal"]["accounting_triplet_signal"].__setitem__(
                "attention_typed_savings_bytes_total", 0
            ),
        ),
        ("candidate_order_drift", lambda p: p["candidate_order"].reverse()),
        ("validation_command_drift", lambda p: p["validation_commands"].append("just gate")),
        ("non_claim_removed", lambda p: p["non_claims"].pop()),
        ("payload_commitment_drift", lambda p: p.__setitem__("payload_commitment", "blake2b-256:" + "0" * 64)),
    )


def run_mutations(payload: dict[str, Any], expected_source_artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    results = []
    for name, mutate in mutation_cases(payload):
        mutated = copy.deepcopy(payload)
        mutate(mutated)
        try:
            validate_payload(mutated, expected_source_artifacts)
        except ProofPressureWideGridSelectorError as err:
            results.append({"name": name, "rejected": True, "error": str(err)})
        else:
            results.append({"name": name, "rejected": False, "error": ""})
    return {
        "all_mutations_rejected": all(row["rejected"] for row in results),
        "mutations_checked": len(results),
        "mutations_rejected": sum(1 for row in results if row["rejected"]),
        "mutation_names": [row["name"] for row in results],
        "cases": results,
    }


def reject_symlink_components(path: pathlib.Path, label: str) -> None:
    """Reject symlinked components without resolving them away first."""
    if not path.is_absolute():
        path = ROOT / path
    current = pathlib.Path(path.anchor)
    parts = path.parts[1:] if path.anchor else path.parts
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise ProofPressureWideGridSelectorError(
                f"output path must not contain symlink components: {label}: {current}"
            )
        if not current.exists():
            raise ProofPressureWideGridSelectorError(f"output path parent directory must exist: {label}: {current}")


def checked_output_path(path: pathlib.Path) -> pathlib.Path:
    if any(part == ".." for part in path.parts):
        raise ProofPressureWideGridSelectorError(f"output path must stay inside evidence dir: {path}")
    candidate = path if path.is_absolute() else ROOT / path
    reject_symlink_components(EVIDENCE_DIR, "evidence root")
    try:
        candidate.relative_to(EVIDENCE_DIR)
    except ValueError as err:
        raise ProofPressureWideGridSelectorError(f"output path must stay inside evidence dir: {candidate}") from err
    reject_symlink_components(candidate.parent, "candidate parent")
    if not candidate.parent.is_dir():
        raise ProofPressureWideGridSelectorError(f"output path parent directory must exist: {candidate.parent}")
    evidence_root = EVIDENCE_DIR.resolve(strict=True)
    try:
        candidate.resolve(strict=False).relative_to(evidence_root)
    except ValueError as err:
        raise ProofPressureWideGridSelectorError(f"output path must stay inside evidence dir: {candidate}") from err
    if candidate.is_symlink():
        raise ProofPressureWideGridSelectorError(f"output path must not contain symlink components: {candidate}")
    relative = candidate.relative_to(EVIDENCE_DIR)
    current = EVIDENCE_DIR
    for part in relative.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ProofPressureWideGridSelectorError(f"output path must not contain symlink components: {current}")
    return candidate


def write_json(path: pathlib.Path, payload: dict[str, Any], expected_source_artifacts: list[dict[str, Any]]) -> None:
    path = checked_output_path(path)
    validate_payload(payload, expected_source_artifacts)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
        tmp_path = pathlib.Path(handle.name)
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    try:
        validate_payload(json.loads(tmp_path.read_text(encoding="utf-8")), expected_source_artifacts)
        path = checked_output_path(path)
        tmp_path.replace(path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def write_tsv(path: pathlib.Path, payload: dict[str, Any], expected_source_artifacts: list[dict[str, Any]]) -> None:
    path = checked_output_path(path)
    validate_payload(payload, expected_source_artifacts)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
        tmp_path = pathlib.Path(handle.name)
        writer = csv.DictWriter(handle, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in payload["candidate_order"]:
            writer.writerow({column: row[column] for column in TSV_COLUMNS})
    try:
        with tmp_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        if len(rows) != len(payload["candidate_order"]):
            raise ProofPressureWideGridSelectorError("TSV row count drift")
        path = checked_output_path(path)
        tmp_path.replace(path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path, default=JSON_OUT)
    parser.add_argument("--write-tsv", type=pathlib.Path, default=TSV_OUT)
    args = parser.parse_args()
    payload = build_payload()
    _, current_raws = load_sources()
    expected_source_artifacts = source_artifacts(current_raws)
    write_json(args.write_json, payload, expected_source_artifacts)
    write_tsv(args.write_tsv, payload, expected_source_artifacts)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
