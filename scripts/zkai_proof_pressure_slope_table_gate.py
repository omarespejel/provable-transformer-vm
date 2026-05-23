#!/usr/bin/env python3.10
"""Paper-facing proof-pressure slope table for issue #715."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import pathlib
import sys
import tempfile
from typing import Any

if sys.version_info < (3, 10):
    raise RuntimeError("zkai_proof_pressure_slope_table_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs" / "engineering"
EVIDENCE_DIR = DOCS_DIR / "evidence"
ROUTE_MATRIX_PATH = EVIDENCE_DIR / "zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json"
MAIN_EVIDENCE_PATH = EVIDENCE_DIR / "zkai-proof-pressure-main-evidence-2026-05.json"
D64_TIMING_PATH = EVIDENCE_DIR / "zkai-attention-kv-d64-sequence-median-timing-raw-2026-05.json"
D256_TIMING_PATH = EVIDENCE_DIR / "zkai-attention-kv-d256-two-head-seq32-median-timing-raw-2026-05.json"
JSON_OUT = EVIDENCE_DIR / "zkai-proof-pressure-slope-table-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-proof-pressure-slope-table-2026-05.tsv"
MD_OUT = DOCS_DIR / "zkai-proof-pressure-slope-table-2026-05-24.md"

SCHEMA = "zkai-proof-pressure-slope-table-v1"
ISSUE = 715
DECISION = "GO_PAPER_SLOPE_TABLE_WITH_SCOPED_BLOCK_NEXT_GATE"
CLAIM_BOUNDARY = (
    "PAPER_FACING_SLOPE_TABLE_FOR_ATTENTION_PROOF_PRESSURE;"
    "PROOF_SIZE_AND_BOUNDARY_SELECTION_SIGNAL_ONLY;"
    "NOT_FULL_BLOCK_NOT_SPEED_CLAIM_NOT_EXTERNAL_COMPARISON"
)
NEXT_GATE = (
    "scoped_d128_seq32_transformer_block_boundary_preflight; "
    "d256_seq64_remains_a_stress_test_not_the_primary_paper_gate"
)
TIMING_POLICY = "reuse_d64_and_d256_median_of_5_release_timing_as_engineering_caveat_only"
VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_proof_pressure_slope_table_gate.py --write-json docs/engineering/evidence/zkai-proof-pressure-slope-table-2026-05.json --write-tsv docs/engineering/evidence/zkai-proof-pressure-slope-table-2026-05.tsv --write-md docs/engineering/zkai-proof-pressure-slope-table-2026-05-24.md",
    "python3.10 -m py_compile scripts/zkai_proof_pressure_slope_table_gate.py scripts/tests/test_zkai_proof_pressure_slope_table_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_proof_pressure_slope_table_gate",
    "git diff --check",
)
NON_CLAIMS = (
    "not a full transformer block proof",
    "not a public proving-speed benchmark",
    "not an external zkML comparison",
    "not a NANOZK proof-size win",
    "not a claim that width scaling is free",
    "not production throughput evidence",
)
TSV_COLUMNS = (
    "row_id",
    "axis",
    "from_profile_id",
    "to_profile_id",
    "lookup_growth",
    "trace_growth",
    "width_growth",
    "fused_proof_growth",
    "split_proof_growth",
    "saving_growth",
    "target_fused_proof_bytes",
    "target_split_proof_bytes",
    "target_saving_bytes",
    "target_fused_to_split_ratio",
    "fused_prove_growth",
    "fused_verify_growth",
    "outcome",
)
SOURCE_ARTIFACTS = (
    ("route_matrix", ROUTE_MATRIX_PATH),
    ("main_evidence", MAIN_EVIDENCE_PATH),
    ("d64_sequence_median_timing", D64_TIMING_PATH),
    ("d256_seq32_median_timing", D256_TIMING_PATH),
)
EXPECTED_SOURCE_DIGESTS = {
    "route_matrix": "f8da6eb33454011e3ef20b7b80cdcce4ff9086764d7b4a3868c684046b434701",
    "main_evidence": "698e07150c77821ef705b4858e9fcbac0f4de4037afd1bd6628b8546901e085c",
    "d64_sequence_median_timing": "6a752b68149ba2a80d28ed14b829c0e2975193530bc6d2de1f02384ed3135702",
    "d256_seq32_median_timing": "39f5392cdb060e9c7d8274ee2603120680cf9cb8f09d5675a69710a107cd5d81",
}
EXPECTED_SOURCE_SIZES = {
    "route_matrix": 92_871,
    "main_evidence": 6_821,
    "d64_sequence_median_timing": 20_998,
    "d256_seq32_median_timing": 5_388,
}
MUTATION_NAMES = (
    "route_matrix_row_count_drift",
    "main_evidence_row_count_drift",
    "source_digest_drift",
    "d64_sequence_growth_drift",
    "d128_sequence_growth_drift",
    "d64_head_axis_drift",
    "d256_width_timing_drift",
    "outcome_overclaim",
    "non_claim_removed",
    "full_block_overclaim",
)
EXPECTED_OUTCOMES = {
    "d64_h1_to_h4_seq16_head_axis": "GO_HEAD_AXIS_LOOKUP_PRESSURE_AMORTIZED",
    "d64_h2_seq32_to_seq64_sequence_axis": "GO_SEQUENCE_AXIS_LOOKUP_PRESSURE_AMORTIZED_WITH_TIMING_CAVEAT",
    "d64_h4_seq32_to_seq64_sequence_axis": "GO_SEQUENCE_AXIS_LOOKUP_PRESSURE_AMORTIZED_WITH_TIMING_CAVEAT",
    "d128_h2_seq32_to_seq64_sequence_axis": "GO_SEQUENCE_AXIS_PROOF_SIZE_ONLY_TIMING_NOT_MEASURED",
    "d128_h4_seq32_to_seq64_sequence_axis": "GO_SEQUENCE_AXIS_PROOF_SIZE_ONLY_TIMING_NOT_MEASURED",
    "d64_to_d128_h1_seq16_width_axis": "CAUTION_WIDTH_AXIS_PROOF_BYTES_GROW_BUT_FUSED_STILL_BEATS_SPLIT",
    "d64_to_d128_h2_seq32_width_axis": "CAUTION_WIDTH_AXIS_PROOF_BYTES_GROW_BUT_FUSED_STILL_BEATS_SPLIT",
    "d128_to_d256_h2_seq32_width_axis": "CAUTION_WIDTH_AXIS_SAVING_WEAKENS_AND_TIMING_IS_NOT_A_SPEED_WIN",
}
OUTCOME_LABELS = {
    "GO_HEAD_AXIS_LOOKUP_PRESSURE_AMORTIZED": "Go: head-axis lookup pressure amortized",
    "GO_SEQUENCE_AXIS_LOOKUP_PRESSURE_AMORTIZED_WITH_TIMING_CAVEAT": (
        "Go: sequence-axis proof-size signal, with timing caveat"
    ),
    "GO_SEQUENCE_AXIS_PROOF_SIZE_ONLY_TIMING_NOT_MEASURED": (
        "Go: sequence-axis proof-size signal, timing not measured"
    ),
    "CAUTION_WIDTH_AXIS_PROOF_BYTES_GROW_BUT_FUSED_STILL_BEATS_SPLIT": (
        "Caution: width grows proof bytes, fused still beats split"
    ),
    "CAUTION_WIDTH_AXIS_SAVING_WEAKENS_AND_TIMING_IS_NOT_A_SPEED_WIN": (
        "Caution: width saving weakens and timing is not a speed win"
    ),
}
EXPECTED_SUMMARY = {
    "row_count": 8,
    "sequence_rows": 4,
    "width_rows": 3,
    "head_rows": 1,
    "sequence_lookup_growth": 3.72973,
    "sequence_trace_growth": 4.0,
    "sequence_fused_proof_growth_min": 1.06491,
    "sequence_fused_proof_growth_max": 1.080697,
    "head_axis_d64_seq16_lookup_growth": 4.0,
    "head_axis_d64_seq16_fused_proof_growth": 0.999457,
    "d256_width_saving_bytes": 30_143,
    "d256_width_fused_to_split_ratio": 0.964602,
    "d256_width_fused_prove_ratio": 1.154002,
    "d256_width_fused_verify_ratio": 1.198076,
    "interpretation": "sequence and head lookup pressure amortize in proof bytes; width pressure remains costly",
    "recommended_next_gate": NEXT_GATE,
}


class ProofPressureSlopeTableError(ValueError):
    pass


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: pathlib.Path, artifact_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = path.read_bytes()
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ProofPressureSlopeTableError(f"{artifact_id} must be a JSON object")
    return payload, {
        "id": artifact_id,
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha256(raw),
        "size_bytes": len(raw),
    }


def ratio(numerator: int | float, denominator: int | float) -> float:
    if denominator == 0:
        raise ProofPressureSlopeTableError("ratio denominator must be nonzero")
    return round(float(numerator) / float(denominator), 6)


def route_row(route: dict[str, Any], profile_id: str) -> dict[str, Any]:
    for row in route.get("route_rows", []):
        if row.get("profile_id") == profile_id:
            return row
    raise ProofPressureSlopeTableError(f"missing route row: {profile_id}")


def main_row(main_evidence: dict[str, Any], row_id: str) -> dict[str, Any]:
    for row in main_evidence.get("rows", []):
        if row.get("row_id") == row_id:
            return row
    raise ProofPressureSlopeTableError(f"missing main evidence row: {row_id}")


def validate_sources(
    route: dict[str, Any],
    main_evidence: dict[str, Any],
    d64_timing: dict[str, Any],
    d256_timing: dict[str, Any],
) -> None:
    if route.get("profiles_checked") != 30 or route.get("matched_comparator_profiles") != 30:
        raise ProofPressureSlopeTableError("route matrix row-count drift")
    aggregate = route.get("aggregate_metrics")
    if not isinstance(aggregate, dict) or aggregate.get("matched_fused_savings_bytes_total") != 766_883:
        raise ProofPressureSlopeTableError("route matrix aggregate drift")
    if main_evidence.get("schema") != "zkai-proof-pressure-main-evidence-v1":
        raise ProofPressureSlopeTableError("main evidence schema drift")
    if len(main_evidence.get("rows", [])) != 5:
        raise ProofPressureSlopeTableError("main evidence row-count drift")
    if d64_timing.get("sample_count") != 5 or d64_timing.get("schema") != "zkai-attention-kv-d64-sequence-median-timing-cli-v1":
        raise ProofPressureSlopeTableError("d64 timing drift")
    if d256_timing.get("sample_count") != 5 or d256_timing.get("schema") != "zkai-attention-kv-d256-two-head-seq32-median-timing-cli-v1":
        raise ProofPressureSlopeTableError("d256 timing drift")
    d256_comparisons = d256_timing.get("comparisons", {})
    if d256_comparisons.get("fused_to_source_plus_sidecar_prove_median_ratio") != 1.154002:
        raise ProofPressureSlopeTableError("d256 prove timing ratio drift")
    if d256_comparisons.get("fused_to_source_plus_sidecar_verify_median_ratio") != 1.198076:
        raise ProofPressureSlopeTableError("d256 verify timing ratio drift")


def pair_row(
    route: dict[str, Any],
    *,
    row_id: str,
    axis: str,
    from_profile_id: str,
    to_profile_id: str,
    outcome: str,
    timing_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = route_row(route, from_profile_id)
    target = route_row(route, to_profile_id)
    row = {
        "row_id": row_id,
        "axis": axis,
        "from_profile_id": from_profile_id,
        "to_profile_id": to_profile_id,
        "lookup_growth": ratio(target["lookup_claims"], source["lookup_claims"]),
        "trace_growth": ratio(target["trace_rows"], source["trace_rows"]),
        "width_growth": ratio(target["key_width"], source["key_width"]),
        "fused_proof_growth": ratio(target["fused_proof_size_bytes"], source["fused_proof_size_bytes"]),
        "split_proof_growth": ratio(
            target["source_plus_sidecar_raw_proof_bytes"],
            source["source_plus_sidecar_raw_proof_bytes"],
        ),
        "saving_growth": ratio(
            target["fused_saves_vs_source_plus_sidecar_bytes"],
            source["fused_saves_vs_source_plus_sidecar_bytes"],
        ),
        "target_fused_proof_bytes": target["fused_proof_size_bytes"],
        "target_split_proof_bytes": target["source_plus_sidecar_raw_proof_bytes"],
        "target_saving_bytes": target["fused_saves_vs_source_plus_sidecar_bytes"],
        "target_fused_to_split_ratio": target["fused_to_source_plus_sidecar_ratio"],
        "fused_prove_growth": None,
        "fused_verify_growth": None,
        "outcome": outcome,
    }
    if timing_row is not None:
        row["fused_prove_growth"] = timing_row["fused_prove_growth"]
        row["fused_verify_growth"] = timing_row["fused_verify_growth"]
    return row


def build_rows(route: dict[str, Any], main_evidence: dict[str, Any]) -> list[dict[str, Any]]:
    d64_h2 = main_row(main_evidence, "d64_h2_seq32_to_seq64")
    d64_h4 = main_row(main_evidence, "d64_h4_seq32_to_seq64")
    return [
        pair_row(
            route,
            row_id="d64_h1_to_h4_seq16_head_axis",
            axis="head",
            from_profile_id="d64_single_head_seq16",
            to_profile_id="d64_four_head_seq16",
            outcome=EXPECTED_OUTCOMES["d64_h1_to_h4_seq16_head_axis"],
        ),
        pair_row(
            route,
            row_id="d64_h2_seq32_to_seq64_sequence_axis",
            axis="sequence",
            from_profile_id="d64_two_head_seq32",
            to_profile_id="d64_two_head_seq64",
            outcome=EXPECTED_OUTCOMES["d64_h2_seq32_to_seq64_sequence_axis"],
            timing_row=d64_h2,
        ),
        pair_row(
            route,
            row_id="d64_h4_seq32_to_seq64_sequence_axis",
            axis="sequence",
            from_profile_id="d64_four_head_seq32",
            to_profile_id="d64_four_head_seq64",
            outcome=EXPECTED_OUTCOMES["d64_h4_seq32_to_seq64_sequence_axis"],
            timing_row=d64_h4,
        ),
        pair_row(
            route,
            row_id="d128_h2_seq32_to_seq64_sequence_axis",
            axis="sequence",
            from_profile_id="d128_two_head_seq32",
            to_profile_id="d128_two_head_seq64",
            outcome=EXPECTED_OUTCOMES["d128_h2_seq32_to_seq64_sequence_axis"],
        ),
        pair_row(
            route,
            row_id="d128_h4_seq32_to_seq64_sequence_axis",
            axis="sequence",
            from_profile_id="d128_four_head_seq32",
            to_profile_id="d128_four_head_seq64",
            outcome=EXPECTED_OUTCOMES["d128_h4_seq32_to_seq64_sequence_axis"],
        ),
        pair_row(
            route,
            row_id="d64_to_d128_h1_seq16_width_axis",
            axis="width",
            from_profile_id="d64_single_head_seq16",
            to_profile_id="d128_single_head_seq16",
            outcome=EXPECTED_OUTCOMES["d64_to_d128_h1_seq16_width_axis"],
        ),
        pair_row(
            route,
            row_id="d64_to_d128_h2_seq32_width_axis",
            axis="width",
            from_profile_id="d64_two_head_seq32",
            to_profile_id="d128_two_head_seq32",
            outcome=EXPECTED_OUTCOMES["d64_to_d128_h2_seq32_width_axis"],
        ),
        pair_row(
            route,
            row_id="d128_to_d256_h2_seq32_width_axis",
            axis="width",
            from_profile_id="d128_two_head_seq32",
            to_profile_id="d256_two_head_seq32",
            outcome=EXPECTED_OUTCOMES["d128_to_d256_h2_seq32_width_axis"],
        ),
    ]


def validate_rows(rows: list[dict[str, Any]]) -> None:
    if len(rows) != 8:
        raise ProofPressureSlopeTableError("slope row count drift")
    by_id = {row["row_id"]: row for row in rows}
    expected = set(EXPECTED_OUTCOMES)
    if set(by_id) != expected:
        raise ProofPressureSlopeTableError("slope row identity drift")
    for row_id, outcome in EXPECTED_OUTCOMES.items():
        if by_id[row_id].get("outcome") != outcome:
            raise ProofPressureSlopeTableError("slope row outcome drift")
    if by_id["d64_h1_to_h4_seq16_head_axis"]["lookup_growth"] != 4.0:
        raise ProofPressureSlopeTableError("d64 head-axis lookup drift")
    if by_id["d64_h1_to_h4_seq16_head_axis"]["fused_proof_growth"] != 0.999457:
        raise ProofPressureSlopeTableError("d64 head-axis fused proof drift")
    for row_id in (
        "d64_h2_seq32_to_seq64_sequence_axis",
        "d64_h4_seq32_to_seq64_sequence_axis",
        "d128_h2_seq32_to_seq64_sequence_axis",
        "d128_h4_seq32_to_seq64_sequence_axis",
    ):
        row = by_id[row_id]
        if row["lookup_growth"] != 3.72973 or row["trace_growth"] != 4.0:
            raise ProofPressureSlopeTableError("sequence work-growth drift")
        if row["fused_proof_growth"] >= 1.1:
            raise ProofPressureSlopeTableError("sequence fused proof growth drift")
    d256 = by_id["d128_to_d256_h2_seq32_width_axis"]
    if d256["target_saving_bytes"] != 30_143 or d256["target_fused_to_split_ratio"] != 0.964602:
        raise ProofPressureSlopeTableError("d256 width proof-size drift")
    if d256["fused_proof_growth"] != 1.842162 or d256["saving_growth"] >= 1.0:
        raise ProofPressureSlopeTableError("d256 width slope drift")


def build_summary(rows: list[dict[str, Any]], d256_timing: dict[str, Any]) -> dict[str, Any]:
    sequence_rows = [row for row in rows if row["axis"] == "sequence"]
    width_rows = [row for row in rows if row["axis"] == "width"]
    head_rows = [row for row in rows if row["axis"] == "head"]
    return {
        "row_count": len(rows),
        "sequence_rows": len(sequence_rows),
        "width_rows": len(width_rows),
        "head_rows": len(head_rows),
        "sequence_lookup_growth": 3.72973,
        "sequence_trace_growth": 4.0,
        "sequence_fused_proof_growth_min": min(row["fused_proof_growth"] for row in sequence_rows),
        "sequence_fused_proof_growth_max": max(row["fused_proof_growth"] for row in sequence_rows),
        "head_axis_d64_seq16_lookup_growth": head_rows[0]["lookup_growth"],
        "head_axis_d64_seq16_fused_proof_growth": head_rows[0]["fused_proof_growth"],
        "d256_width_saving_bytes": 30_143,
        "d256_width_fused_to_split_ratio": 0.964602,
        "d256_width_fused_prove_ratio": d256_timing["comparisons"]["fused_to_source_plus_sidecar_prove_median_ratio"],
        "d256_width_fused_verify_ratio": d256_timing["comparisons"]["fused_to_source_plus_sidecar_verify_median_ratio"],
        "interpretation": "sequence and head lookup pressure amortize in proof bytes; width pressure remains costly",
        "recommended_next_gate": NEXT_GATE,
    }


def build_payload() -> dict[str, Any]:
    route, route_source = read_json(ROUTE_MATRIX_PATH, "route_matrix")
    main_evidence, main_source = read_json(MAIN_EVIDENCE_PATH, "main_evidence")
    d64_timing, d64_source = read_json(D64_TIMING_PATH, "d64_sequence_median_timing")
    d256_timing, d256_source = read_json(D256_TIMING_PATH, "d256_seq32_median_timing")
    validate_sources(route, main_evidence, d64_timing, d256_timing)
    rows = build_rows(route, main_evidence)
    validate_rows(rows)
    payload = {
        "schema": SCHEMA,
        "issue": ISSUE,
        "decision": DECISION,
        "claim_boundary": CLAIM_BOUNDARY,
        "timing_policy": TIMING_POLICY,
        "source_artifacts": [route_source, main_source, d64_source, d256_source],
        "rows": rows,
        "summary": build_summary(rows, d256_timing),
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    validate_payload(payload, require_mutations=False)
    mutation_results = evaluate_mutations(payload)
    payload["mutation_results"] = mutation_results
    payload["mutations_checked"] = len(mutation_results)
    payload["mutations_rejected"] = sum(1 for result in mutation_results if result["rejected"])
    payload["all_mutations_rejected"] = payload["mutations_rejected"] == len(MUTATION_NAMES)
    validate_payload(payload)
    return payload


def validate_payload(payload: dict[str, Any], *, require_mutations: bool = True) -> None:
    if payload.get("schema") != SCHEMA or payload.get("decision") != DECISION:
        raise ProofPressureSlopeTableError("payload identity drift")
    claim_boundary = payload.get("claim_boundary", "").lower()
    if "full block proof" in claim_boundary or "full_block_proof" in claim_boundary:
        raise ProofPressureSlopeTableError("full block overclaim")
    if payload.get("non_claims") != list(NON_CLAIMS):
        raise ProofPressureSlopeTableError("non-claims drift")
    if payload.get("validation_commands") != list(VALIDATION_COMMANDS):
        raise ProofPressureSlopeTableError("validation command drift")
    source_artifacts = payload.get("source_artifacts")
    if not isinstance(source_artifacts, list) or len(source_artifacts) != len(SOURCE_ARTIFACTS):
        raise ProofPressureSlopeTableError("source artifact drift")
    for artifact, (artifact_id, path) in zip(source_artifacts, SOURCE_ARTIFACTS, strict=True):
        if artifact.get("id") != artifact_id or artifact.get("path") != path.relative_to(ROOT).as_posix():
            raise ProofPressureSlopeTableError("source artifact identity drift")
        if artifact.get("sha256") != EXPECTED_SOURCE_DIGESTS[artifact_id]:
            raise ProofPressureSlopeTableError("source artifact digest drift")
        if artifact.get("size_bytes") != EXPECTED_SOURCE_SIZES[artifact_id]:
            raise ProofPressureSlopeTableError("source artifact size drift")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ProofPressureSlopeTableError("rows missing")
    validate_rows(rows)
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        raise ProofPressureSlopeTableError("summary missing")
    if set(summary) != set(EXPECTED_SUMMARY):
        raise ProofPressureSlopeTableError("summary key drift")
    for key, expected in EXPECTED_SUMMARY.items():
        if summary.get(key) != expected:
            raise ProofPressureSlopeTableError(f"summary {key} drift")
    if require_mutations:
        results = payload.get("mutation_results")
        if not isinstance(results, list) or [row.get("name") for row in results] != list(MUTATION_NAMES):
            raise ProofPressureSlopeTableError("mutation result drift")
        if not all(row.get("rejected") is True and row.get("error") for row in results):
            raise ProofPressureSlopeTableError("mutation rejection drift")
        if payload.get("mutations_checked") != len(MUTATION_NAMES) or payload.get("mutations_rejected") != len(MUTATION_NAMES):
            raise ProofPressureSlopeTableError("mutation count drift")
        if payload.get("all_mutations_rejected") is not True:
            raise ProofPressureSlopeTableError("mutation summary drift")


def mutate_payload(payload: dict[str, Any], name: str) -> dict[str, Any]:
    mutated = json.loads(json.dumps(payload))
    for key in ("mutation_results", "mutations_checked", "mutations_rejected", "all_mutations_rejected"):
        mutated.pop(key, None)
    rows = {row["row_id"]: row for row in mutated["rows"]}
    if name == "route_matrix_row_count_drift":
        mutated["source_artifacts"][0]["id"] = "wrong_route_matrix"
    elif name == "main_evidence_row_count_drift":
        mutated["source_artifacts"][1]["path"] = "docs/engineering/evidence/wrong.json"
    elif name == "source_digest_drift":
        mutated["source_artifacts"][0]["sha256"] = "0" * 64
    elif name == "d64_sequence_growth_drift":
        rows["d64_h2_seq32_to_seq64_sequence_axis"]["lookup_growth"] = 3.0
    elif name == "d128_sequence_growth_drift":
        rows["d128_h2_seq32_to_seq64_sequence_axis"]["fused_proof_growth"] = 1.2
    elif name == "d64_head_axis_drift":
        rows["d64_h1_to_h4_seq16_head_axis"]["fused_proof_growth"] = 1.01
    elif name == "d256_width_timing_drift":
        mutated["summary"]["d256_width_fused_prove_ratio"] = 0.9
    elif name == "outcome_overclaim":
        rows["d128_to_d256_h2_seq32_width_axis"]["outcome"] = "GO_WIDTH_AXIS_FREE"
    elif name == "non_claim_removed":
        mutated["non_claims"].pop()
    elif name == "full_block_overclaim":
        mutated["claim_boundary"] = "FULL_BLOCK_PROOF"
    else:
        raise ProofPressureSlopeTableError(f"unknown mutation: {name}")
    return mutated


def evaluate_mutations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for name in MUTATION_NAMES:
        mutated = mutate_payload(payload, name)
        try:
            validate_payload(mutated, require_mutations=False)
        except ProofPressureSlopeTableError as err:
            results.append({"name": name, "rejected": True, "error": str(err)})
        else:
            results.append({"name": name, "rejected": False, "error": "accepted mutated payload"})
    return results


def checked_output_path(path: pathlib.Path, allowed_root: pathlib.Path) -> pathlib.Path:
    if not path.is_absolute():
        path = ROOT / path
    path = path.expanduser()
    try:
        path.relative_to(allowed_root)
    except ValueError as err:
        raise ProofPressureSlopeTableError(f"output must stay inside {allowed_root.relative_to(ROOT)}") from err
    if path.exists() and path.is_symlink():
        raise ProofPressureSlopeTableError("output path must not be a symlink")
    if not path.parent.is_dir():
        raise ProofPressureSlopeTableError("output parent missing")
    resolved_parent = path.parent.resolve(strict=True)
    try:
        resolved_parent.relative_to(allowed_root.resolve(strict=True))
    except ValueError as err:
        raise ProofPressureSlopeTableError(f"output must stay inside {allowed_root.relative_to(ROOT)}") from err
    return path


def reject_same_output_paths(paths: tuple[pathlib.Path, ...]) -> None:
    normalized = [os.fspath(path.resolve(strict=False)) for path in paths]
    if len(set(normalized)) != len(normalized):
        raise ProofPressureSlopeTableError("output paths must point to different files")


def checked_output_paths(
    json_path: pathlib.Path,
    tsv_path: pathlib.Path,
    md_path: pathlib.Path,
) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    checked = (
        checked_output_path(json_path, EVIDENCE_DIR),
        checked_output_path(tsv_path, EVIDENCE_DIR),
        checked_output_path(md_path, DOCS_DIR),
    )
    reject_same_output_paths(checked)
    return checked


def atomic_write(path: pathlib.Path, text: str) -> None:
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        tmp_path = pathlib.Path(handle.name)
        handle.write(text)
    tmp_path.replace(path)


def write_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path = checked_output_path(path, EVIDENCE_DIR)
    validate_payload(payload)
    atomic_write(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_tsv(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path = checked_output_path(path, EVIDENCE_DIR)
    validate_payload(payload)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        tmp_path = pathlib.Path(handle.name)
        writer = csv.DictWriter(handle, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in payload["rows"]:
            writer.writerow({column: row.get(column) for column in TSV_COLUMNS})
    tmp_path.replace(path)


def md_table_row(row: dict[str, Any]) -> str:
    def cell(key: str) -> str:
        value = row.get(key)
        if value is None:
            return "not measured"
        if key == "outcome" and isinstance(value, str):
            return OUTCOME_LABELS.get(value, value.replace("_", " "))
        if isinstance(value, float):
            return f"`{value:.6f}x`"
        if isinstance(value, int):
            return f"`{value:,}`"
        return str(value).replace("_", " ")

    return (
        f"| {row['row_id'].replace('_', ' ')} | {row['axis']} | "
        f"{cell('lookup_growth')} | {cell('trace_growth')} | {cell('width_growth')} | "
        f"{cell('fused_proof_growth')} | {cell('split_proof_growth')} | "
        f"{cell('target_saving_bytes')} | {cell('target_fused_to_split_ratio')} | {cell('outcome')} |"
    )


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    rows = "\n".join(md_table_row(row) for row in payload["rows"])
    commands = "\n".join(payload["validation_commands"])
    non_claims = "\n".join(f"- {item}." for item in payload["non_claims"])
    return f"""# ZKAI Proof-Pressure Slope Table

Issue: #715

## Decision

`{payload['decision']}`

This table is the paper-facing read of the current attention proof-pressure
grid. It does not add a new proof. It explains what the checked rows say about
where fusion helps and where it starts to hurt.

## Result

The strongest slope is on lookup-heavy sequence and head pressure:

- sequence rows grow lookup work by `{summary['sequence_lookup_growth']:.6f}x`
  and trace rows by `{summary['sequence_trace_growth']:.6f}x`;
- fused proof bytes grow only `{summary['sequence_fused_proof_growth_min']:.6f}x`
  to `{summary['sequence_fused_proof_growth_max']:.6f}x`;
- the d64 seq16 head-axis row grows lookup work by
  `{summary['head_axis_d64_seq16_lookup_growth']:.6f}x` while fused proof bytes
  move `{summary['head_axis_d64_seq16_fused_proof_growth']:.6f}x`.

The width axis is different. The d256 row still beats the matched split
frontier by `{summary['d256_width_saving_bytes']:,}` proof bytes, but its fused
proof ratio is `{summary['d256_width_fused_to_split_ratio']:.6f}x` and local
median timing is not a speed win.

## Slope Table

| row | axis | lookup growth | trace growth | width growth | fused proof growth | split proof growth | target saving | target fused ratio | outcome |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
{rows}

## Interpretation

The clean paper claim is not that bigger fused proofs always win. It is that
transformer proof boundaries should follow proof pressure. The current evidence
says lookup-heavy sequence and head growth can be amortized in proof bytes, while
width growth is a cost center that needs a narrower or composed boundary.

Next gate:

`{summary['recommended_next_gate']}`

## Evidence

- JSON: `docs/engineering/evidence/zkai-proof-pressure-slope-table-2026-05.json`
- TSV: `docs/engineering/evidence/zkai-proof-pressure-slope-table-2026-05.tsv`
- Route matrix: `docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json`
- Main evidence: `docs/engineering/evidence/zkai-proof-pressure-main-evidence-2026-05.json`

## Validation

```bash
{commands}
```

## Non-Claims

{non_claims}
"""


def write_md(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path = checked_output_path(path, DOCS_DIR)
    validate_payload(payload)
    atomic_write(path, render_markdown(payload))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json", type=pathlib.Path, default=JSON_OUT)
    parser.add_argument("--write-tsv", type=pathlib.Path, default=TSV_OUT)
    parser.add_argument("--write-md", type=pathlib.Path, default=MD_OUT)
    args = parser.parse_args()
    json_path, tsv_path, md_path = checked_output_paths(args.write_json, args.write_tsv, args.write_md)
    payload = build_payload()
    write_json(json_path, payload)
    write_tsv(tsv_path, payload)
    write_md(md_path, payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
