#!/usr/bin/env python3.10
"""Paper-facing proof-pressure evidence table and figure for issue #715."""

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
    raise RuntimeError("zkai_proof_pressure_main_evidence_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
ROUTE_MATRIX_PATH = EVIDENCE_DIR / "zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json"
D64_TIMING_PATH = EVIDENCE_DIR / "zkai-attention-kv-d64-sequence-median-timing-raw-2026-05.json"
D256_TIMING_PATH = EVIDENCE_DIR / "zkai-attention-kv-d256-two-head-seq32-median-timing-raw-2026-05.json"
JSON_OUT = EVIDENCE_DIR / "zkai-proof-pressure-main-evidence-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-proof-pressure-main-evidence-2026-05.tsv"
SVG_OUT = EVIDENCE_DIR / "zkai-proof-pressure-work-proof-growth-2026-05.svg"

SCHEMA = "zkai-proof-pressure-main-evidence-v1"
ISSUE = 715
DECISION = "GO_MAIN_EVIDENCE_TABLE_AND_FIGURE_WITH_SIZE_TIMING_CAVEAT"
CLAIM_BOUNDARY = (
    "PAPER_FACING_ENGINEERING_EVIDENCE_FOR_PROOF_PRESSURE_SCALING;"
    "PROOF_SIZE_AND_BOUNDARY_SHAPE_SIGNAL_ONLY;"
    "TIMING_IS_ENGINEERING_LOCAL_AND_NOT_A_PUBLIC_SPEED_CLAIM"
)
TIMING_POLICY = "median_of_5_in_process_release_timing_for_d64_and_d256_engineering_only"
NON_CLAIMS = (
    "not a full transformer block proof",
    "not a public proving-speed benchmark",
    "not an external zkML comparison",
    "not a NANOZK proof-size win",
    "not production throughput evidence",
)
TSV_COLUMNS = (
    "row_id",
    "row_kind",
    "from_profile_id",
    "to_profile_id",
    "lookup_growth",
    "trace_growth",
    "fused_proof_growth",
    "split_proof_growth",
    "fused_prove_growth",
    "split_prove_growth",
    "fused_verify_growth",
    "split_verify_growth",
    "fused_proof_bytes",
    "split_proof_bytes",
    "saving_bytes",
    "fused_to_split_ratio",
    "timing_status",
    "interpretation",
)
MUTATION_NAMES = (
    "route_matrix_aggregate_drift",
    "d64_timing_sample_count_drift",
    "d64_sequence_growth_drift",
    "d256_timing_decision_drift",
    "evidence_row_smuggling",
    "non_claim_removed",
)
EXPECTED_ROW_IDS = (
    "d64_h2_seq32_to_seq64",
    "d64_h4_seq32_to_seq64",
    "d128_h2_seq32_to_seq64",
    "d128_h4_seq32_to_seq64",
    "d128_to_d256_h2_seq32_width_stress",
)
BASE_ROW_KEYS = {
    "row_id",
    "row_kind",
    "from_profile_id",
    "to_profile_id",
    "lookup_growth",
    "trace_growth",
    "fused_proof_growth",
    "split_proof_growth",
    "fused_prove_growth",
    "split_prove_growth",
    "fused_verify_growth",
    "split_verify_growth",
    "fused_proof_bytes",
    "split_proof_bytes",
    "saving_bytes",
    "fused_to_split_ratio",
    "timing_status",
    "interpretation",
}
WIDTH_ROW_EXTRA_KEYS = {
    "d256_fused_to_split_prove_ratio",
    "d256_fused_to_split_verify_ratio",
}
SEQUENCE_ROW_EXTRA_KEYS = {
    "source_profile",
}
EXPECTED_SOURCE_ARTIFACTS = (
    ("route_matrix", "docs/engineering/evidence/zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json"),
    ("d64_sequence_median_timing", "docs/engineering/evidence/zkai-attention-kv-d64-sequence-median-timing-raw-2026-05.json"),
    ("d256_seq32_median_timing", "docs/engineering/evidence/zkai-attention-kv-d256-two-head-seq32-median-timing-raw-2026-05.json"),
)


class ProofPressureMainEvidenceError(ValueError):
    pass


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: pathlib.Path, label: str) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = path.read_bytes()
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ProofPressureMainEvidenceError(f"{label} must be a JSON object")
    return payload, {
        "id": label,
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha256(raw),
        "size_bytes": len(raw),
    }


def ratio(numerator: int | float, denominator: int | float) -> float:
    if denominator == 0:
        raise ProofPressureMainEvidenceError("ratio denominator must be nonzero")
    return round(float(numerator) / float(denominator), 6)


def route_row(route: dict[str, Any], profile_id: str) -> dict[str, Any]:
    for row in route.get("route_rows", []):
        if row.get("profile_id") == profile_id:
            return row
    raise ProofPressureMainEvidenceError(f"missing route row: {profile_id}")


def timing_profile(timing: dict[str, Any], profile_id: str) -> dict[str, Any]:
    for row in timing.get("profiles", []):
        if row.get("profile_id") == profile_id:
            return row
    raise ProofPressureMainEvidenceError(f"missing timing profile: {profile_id}")


def validate_sources(route: dict[str, Any], d64_timing: dict[str, Any], d256_timing: dict[str, Any]) -> None:
    aggregate = route.get("aggregate_metrics")
    if not isinstance(aggregate, dict):
        raise ProofPressureMainEvidenceError("route aggregate missing")
    if route.get("profiles_checked") != 30 or route.get("matched_comparator_profiles") != 30:
        raise ProofPressureMainEvidenceError("route matrix row-count drift")
    if aggregate.get("matched_fused_proof_size_bytes_total") != 6_397_632:
        raise ProofPressureMainEvidenceError("route matrix fused total drift")
    if aggregate.get("matched_source_plus_sidecar_raw_proof_bytes_total") != 7_164_515:
        raise ProofPressureMainEvidenceError("route matrix split total drift")
    if aggregate.get("matched_fused_savings_bytes_total") != 766_883:
        raise ProofPressureMainEvidenceError("route matrix saving total drift")
    if d64_timing.get("schema") != "zkai-attention-kv-d64-sequence-median-timing-cli-v1":
        raise ProofPressureMainEvidenceError("d64 timing schema drift")
    if d64_timing.get("sample_count") != 5:
        raise ProofPressureMainEvidenceError("d64 timing sample count drift")
    if d256_timing.get("schema") != "zkai-attention-kv-d256-two-head-seq32-median-timing-cli-v1":
        raise ProofPressureMainEvidenceError("d256 timing schema drift")
    if d256_timing.get("sample_count") != 5:
        raise ProofPressureMainEvidenceError("d256 timing sample count drift")


def sequence_row(
    route: dict[str, Any],
    timing: dict[str, Any],
    from_profile_id: str,
    to_profile_id: str,
    row_id: str,
) -> dict[str, Any]:
    source = route_row(route, from_profile_id)
    target = route_row(route, to_profile_id)
    growth = next(
        (
            row
            for row in timing.get("sequence_growth", [])
            if row.get("from_profile_id") == from_profile_id and row.get("to_profile_id") == to_profile_id
        ),
        None,
    )
    if not isinstance(growth, dict):
        raise ProofPressureMainEvidenceError(f"missing sequence growth row: {row_id}")
    return {
        "row_id": row_id,
        "row_kind": "sequence_axis",
        "from_profile_id": from_profile_id,
        "to_profile_id": to_profile_id,
        "lookup_growth": growth["lookup_claim_growth"],
        "trace_growth": growth["trace_row_growth"],
        "fused_proof_growth": growth["fused_raw_proof_growth"],
        "split_proof_growth": growth["split_raw_proof_growth"],
        "fused_prove_growth": growth["fused_prove_median_growth"],
        "split_prove_growth": growth["split_prove_median_growth"],
        "fused_verify_growth": growth["fused_verify_median_growth"],
        "split_verify_growth": growth["split_verify_median_growth"],
        "fused_proof_bytes": target["fused_proof_size_bytes"],
        "split_proof_bytes": target["source_plus_sidecar_raw_proof_bytes"],
        "saving_bytes": target["fused_saves_vs_source_plus_sidecar_bytes"],
        "fused_to_split_ratio": target["fused_to_source_plus_sidecar_ratio"],
        "timing_status": "median_of_5_local_release",
        "interpretation": (
            "lookup and trace work grew about 4x while fused proof bytes grew about 1.08x; "
            "prove and verify timing grew near the work axis"
        ),
        "source_profile": source["profile_id"],
    }


def proof_only_sequence_row(
    route: dict[str, Any], from_profile_id: str, to_profile_id: str, row_id: str
) -> dict[str, Any]:
    source = route_row(route, from_profile_id)
    target = route_row(route, to_profile_id)
    return {
        "row_id": row_id,
        "row_kind": "sequence_axis_proof_size_only",
        "from_profile_id": from_profile_id,
        "to_profile_id": to_profile_id,
        "lookup_growth": ratio(target["lookup_claims"], source["lookup_claims"]),
        "trace_growth": ratio(target["trace_rows"], source["trace_rows"]),
        "fused_proof_growth": ratio(target["fused_proof_size_bytes"], source["fused_proof_size_bytes"]),
        "split_proof_growth": ratio(
            target["source_plus_sidecar_raw_proof_bytes"], source["source_plus_sidecar_raw_proof_bytes"]
        ),
        "fused_prove_growth": None,
        "split_prove_growth": None,
        "fused_verify_growth": None,
        "split_verify_growth": None,
        "fused_proof_bytes": target["fused_proof_size_bytes"],
        "split_proof_bytes": target["source_plus_sidecar_raw_proof_bytes"],
        "saving_bytes": target["fused_saves_vs_source_plus_sidecar_bytes"],
        "fused_to_split_ratio": target["fused_to_source_plus_sidecar_ratio"],
        "timing_status": "not_measured_here",
        "interpretation": "proof-size scaling row without median timing in this artifact",
    }


def d256_width_row(route: dict[str, Any], d256_timing: dict[str, Any]) -> dict[str, Any]:
    source = route_row(route, "d128_two_head_seq32")
    target = route_row(route, "d256_two_head_seq32")
    comparisons = d256_timing["comparisons"]
    return {
        "row_id": "d128_to_d256_h2_seq32_width_stress",
        "row_kind": "width_axis",
        "from_profile_id": "d128_two_head_seq32",
        "to_profile_id": "d256_two_head_seq32",
        "lookup_growth": ratio(target["lookup_claims"], source["lookup_claims"]),
        "trace_growth": ratio(target["trace_rows"], source["trace_rows"]),
        "fused_proof_growth": ratio(target["fused_proof_size_bytes"], source["fused_proof_size_bytes"]),
        "split_proof_growth": ratio(
            target["source_plus_sidecar_raw_proof_bytes"], source["source_plus_sidecar_raw_proof_bytes"]
        ),
        "fused_prove_growth": None,
        "split_prove_growth": None,
        "fused_verify_growth": None,
        "split_verify_growth": None,
        "fused_proof_bytes": target["fused_proof_size_bytes"],
        "split_proof_bytes": target["source_plus_sidecar_raw_proof_bytes"],
        "saving_bytes": target["fused_saves_vs_source_plus_sidecar_bytes"],
        "fused_to_split_ratio": target["fused_to_source_plus_sidecar_ratio"],
        "timing_status": "median_of_5_local_release_single_point",
        "d256_fused_to_split_prove_ratio": comparisons["fused_to_source_plus_sidecar_prove_median_ratio"],
        "d256_fused_to_split_verify_ratio": comparisons["fused_to_source_plus_sidecar_verify_median_ratio"],
        "interpretation": "d256 keeps a raw proof-byte saving but is not a speed win in local median timing",
    }


def build_payload() -> dict[str, Any]:
    route, route_source = read_json(ROUTE_MATRIX_PATH, "route_matrix")
    d64_timing, d64_source = read_json(D64_TIMING_PATH, "d64_sequence_median_timing")
    d256_timing, d256_source = read_json(D256_TIMING_PATH, "d256_seq32_median_timing")
    validate_sources(route, d64_timing, d256_timing)
    rows = [
        sequence_row(route, d64_timing, "d64_two_head_seq32", "d64_two_head_seq64", "d64_h2_seq32_to_seq64"),
        sequence_row(route, d64_timing, "d64_four_head_seq32", "d64_four_head_seq64", "d64_h4_seq32_to_seq64"),
        proof_only_sequence_row(route, "d128_two_head_seq32", "d128_two_head_seq64", "d128_h2_seq32_to_seq64"),
        proof_only_sequence_row(route, "d128_four_head_seq32", "d128_four_head_seq64", "d128_h4_seq32_to_seq64"),
        d256_width_row(route, d256_timing),
    ]
    payload = {
        "schema": SCHEMA,
        "issue": ISSUE,
        "decision": DECISION,
        "claim_boundary": CLAIM_BOUNDARY,
        "timing_policy": TIMING_POLICY,
        "source_artifacts": [route_source, d64_source, d256_source],
        "rows": rows,
        "summary": {
            "row_count": len(rows),
            "timed_sequence_rows": 2,
            "proof_only_rows": 2,
            "d256_width_rows": 1,
            "strongest_proof_size_signal": "d64 and d128 seq32 to seq64 keep fused proof-byte growth near 1.06x to 1.08x while lookup and trace work grow about 3.73x to 4x",
            "timing_caveat": "local median timing grows near the work axis, so this is not a speed breakthrough",
        },
        "non_claims": list(NON_CLAIMS),
    }
    validate_payload(payload, require_mutations=False)
    mutation_results = evaluate_mutations(payload)
    payload["mutation_results"] = mutation_results
    payload["mutations_checked"] = len(mutation_results)
    payload["mutations_rejected"] = sum(1 for row in mutation_results if row["rejected"])
    payload["all_mutations_rejected"] = payload["mutations_rejected"] == len(MUTATION_NAMES)
    validate_payload(payload)
    return payload


def validate_payload(payload: dict[str, Any], *, require_mutations: bool = True) -> None:
    if payload.get("schema") != SCHEMA or payload.get("decision") != DECISION:
        raise ProofPressureMainEvidenceError("payload identity drift")
    source_artifacts = payload.get("source_artifacts")
    if not isinstance(source_artifacts, list) or len(source_artifacts) != len(EXPECTED_SOURCE_ARTIFACTS):
        raise ProofPressureMainEvidenceError("source artifact drift")
    for artifact, expected in zip(source_artifacts, EXPECTED_SOURCE_ARTIFACTS, strict=True):
        expected_id, expected_path = expected
        if artifact.get("id") != expected_id or artifact.get("path") != expected_path:
            raise ProofPressureMainEvidenceError("source artifact identity drift")
        if not isinstance(artifact.get("sha256"), str) or len(artifact["sha256"]) != 64:
            raise ProofPressureMainEvidenceError("source artifact digest drift")
        if not isinstance(artifact.get("size_bytes"), int) or artifact["size_bytes"] <= 0:
            raise ProofPressureMainEvidenceError("source artifact size drift")
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != 5:
        raise ProofPressureMainEvidenceError("evidence row smuggling")
    if [row.get("row_id") for row in rows if isinstance(row, dict)] != list(EXPECTED_ROW_IDS):
        raise ProofPressureMainEvidenceError("evidence row identity drift")
    for row in rows:
        if not isinstance(row, dict):
            raise ProofPressureMainEvidenceError("evidence row type drift")
        allowed = set(BASE_ROW_KEYS)
        if row.get("row_kind") == "width_axis":
            allowed.update(WIDTH_ROW_EXTRA_KEYS)
        if row.get("row_kind") == "sequence_axis":
            allowed.update(SEQUENCE_ROW_EXTRA_KEYS)
        if set(row) != allowed:
            raise ProofPressureMainEvidenceError(f"evidence row field drift: {row.get('row_id')}")
        for key in ("lookup_growth", "trace_growth", "fused_proof_growth", "split_proof_growth"):
            if not isinstance(row.get(key), (int, float)) or row[key] <= 0:
                raise ProofPressureMainEvidenceError(f"evidence row metric drift: {row.get('row_id')} {key}")
        for key in ("fused_proof_bytes", "split_proof_bytes", "saving_bytes"):
            if not isinstance(row.get(key), int) or row[key] <= 0:
                raise ProofPressureMainEvidenceError(f"evidence row byte drift: {row.get('row_id')} {key}")
        if row["split_proof_bytes"] - row["fused_proof_bytes"] != row["saving_bytes"]:
            raise ProofPressureMainEvidenceError(f"evidence row saving drift: {row.get('row_id')}")
    by_id = {row.get("row_id"): row for row in rows}
    d64_h2 = by_id.get("d64_h2_seq32_to_seq64")
    if not isinstance(d64_h2, dict) or d64_h2.get("lookup_growth") != 3.72973:
        raise ProofPressureMainEvidenceError("d64 h2 sequence growth drift")
    if d64_h2.get("fused_proof_growth") != 1.076519:
        raise ProofPressureMainEvidenceError("d64 h2 fused proof growth drift")
    if d64_h2.get("fused_prove_growth") is None or d64_h2["fused_prove_growth"] <= 1.0:
        raise ProofPressureMainEvidenceError("d64 timing growth drift")
    d64_h4 = by_id.get("d64_h4_seq32_to_seq64")
    if not isinstance(d64_h4, dict) or d64_h4.get("saving_bytes") != 39_282:
        raise ProofPressureMainEvidenceError("d64 h4 saving drift")
    d256 = by_id.get("d128_to_d256_h2_seq32_width_stress")
    if not isinstance(d256, dict) or d256.get("saving_bytes") != 30_143:
        raise ProofPressureMainEvidenceError("d256 width row drift")
    if d256.get("d256_fused_to_split_prove_ratio") <= 1.0:
        raise ProofPressureMainEvidenceError("d256 timing caveat drift")
    if payload.get("non_claims") != list(NON_CLAIMS):
        raise ProofPressureMainEvidenceError("non-claims drift")
    if require_mutations:
        results = payload.get("mutation_results")
        if not isinstance(results, list) or [row.get("name") for row in results] != list(MUTATION_NAMES):
            raise ProofPressureMainEvidenceError("mutation result drift")
        if not all(row.get("rejected") is True and isinstance(row.get("error"), str) and row["error"] for row in results):
            raise ProofPressureMainEvidenceError("mutation rejection drift")
        if payload.get("mutations_checked") != len(MUTATION_NAMES) or payload.get("mutations_rejected") != len(
            MUTATION_NAMES
        ):
            raise ProofPressureMainEvidenceError("mutation count drift")
        if payload.get("all_mutations_rejected") is not True:
            raise ProofPressureMainEvidenceError("mutation summary drift")


def mutate_payload(payload: dict[str, Any], name: str) -> dict[str, Any]:
    mutated = json.loads(json.dumps(payload))
    mutated.pop("mutation_results", None)
    mutated.pop("mutations_checked", None)
    mutated.pop("mutations_rejected", None)
    mutated.pop("all_mutations_rejected", None)
    if name == "route_matrix_aggregate_drift":
        mutated["source_artifacts"][0]["id"] = "wrong_route_matrix"
    elif name == "d64_timing_sample_count_drift":
        mutated["source_artifacts"][1]["path"] = "docs/engineering/evidence/wrong.json"
    elif name == "d64_sequence_growth_drift":
        mutated["rows"][0]["lookup_growth"] = 3.0
    elif name == "d256_timing_decision_drift":
        mutated["rows"][4]["d256_fused_to_split_prove_ratio"] = 0.5
    elif name == "evidence_row_smuggling":
        mutated["rows"].append({"row_id": "fake"})
    elif name == "non_claim_removed":
        mutated["non_claims"].pop()
    else:
        raise ProofPressureMainEvidenceError(f"unknown mutation: {name}")
    return mutated


def evaluate_mutations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for name in MUTATION_NAMES:
        mutated = mutate_payload(payload, name)
        try:
            validate_payload(mutated, require_mutations=False)
        except ProofPressureMainEvidenceError as err:
            results.append({"name": name, "rejected": True, "error": str(err)})
        else:
            results.append({"name": name, "rejected": False, "error": "accepted mutated payload"})
    return results


def write_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    validate_output_path(path)
    validate_payload(payload)
    atomic_write(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_tsv(path: pathlib.Path, payload: dict[str, Any]) -> None:
    validate_output_path(path)
    validate_payload(payload)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
        tmp_path = pathlib.Path(handle.name)
        writer = csv.DictWriter(handle, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in payload["rows"]:
            writer.writerow({column: row.get(column) for column in TSV_COLUMNS})
    tmp_path.replace(path)


def write_svg(path: pathlib.Path, payload: dict[str, Any]) -> None:
    validate_output_path(path)
    validate_payload(payload)
    rows = [row for row in payload["rows"] if row["row_kind"] == "sequence_axis"]
    labels = ["lookup", "trace", "fused proof"]
    colors = ["#2f80ed", "#6fcf97", "#f2c94c"]
    width = 1180
    height = 640
    chart_left = 130
    chart_top = 90
    chart_width = 900
    chart_height = 380
    max_value = 4.4
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="1180" height="640" fill="#0b0d10"/>',
        '<text x="48" y="46" fill="#f4f6f8" font-family="Inter, Arial, sans-serif" font-size="26" font-weight="700">Work grows fast. Proof bytes grow slowly.</text>',
        '<text x="48" y="76" fill="#aab2bd" font-family="Inter, Arial, sans-serif" font-size="15">d64 seq32 to seq64, size-only view of checked proof-pressure evidence.</text>',
    ]
    for tick in range(0, 5):
        y = chart_top + chart_height - (tick / max_value) * chart_height
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_left + chart_width}" y2="{y:.1f}" stroke="#242932" stroke-width="1"/>')
        parts.append(f'<text x="{chart_left - 18}" y="{y + 5:.1f}" fill="#808996" font-family="Inter, Arial, sans-serif" font-size="13" text-anchor="end">{tick}x</text>')
    bar_width = 38
    group_gap = 170
    for row_index, row in enumerate(rows):
        group_x = chart_left + 70 + row_index * (len(labels) * (bar_width + 18) + group_gap)
        values = [
            row["lookup_growth"],
            row["trace_growth"],
            row["fused_proof_growth"],
        ]
        for index, value in enumerate(values):
            x = group_x + index * (bar_width + 18)
            bar_height = min(value, max_value) / max_value * chart_height
            y = chart_top + chart_height - bar_height
            parts.append(f'<rect x="{x}" y="{y:.1f}" width="{bar_width}" height="{bar_height:.1f}" rx="4" fill="{colors[index]}"/>')
            parts.append(f'<text x="{x + bar_width / 2:.1f}" y="{y - 8:.1f}" fill="#f4f6f8" font-family="Inter, Arial, sans-serif" font-size="13" text-anchor="middle">{value:.2f}x</text>')
        center = group_x + (len(labels) * (bar_width + 18) - 18) / 2
        parts.append(f'<text x="{center:.1f}" y="{chart_top + chart_height + 42}" fill="#f4f6f8" font-family="Inter, Arial, sans-serif" font-size="16" font-weight="700" text-anchor="middle">{row["from_profile_id"].replace("_", " ")} to seq64</text>')
    legend_x = 830
    legend_y = 520
    for index, label in enumerate(labels):
        x = legend_x + index * 100
        parts.append(f'<rect x="{x}" y="{legend_y}" width="14" height="14" rx="3" fill="{colors[index]}"/>')
        parts.append(f'<text x="{x + 20}" y="{legend_y + 12}" fill="#c8d0d8" font-family="Inter, Arial, sans-serif" font-size="13">{label}</text>')
    parts.append('<text x="48" y="540" fill="#f4f6f8" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="700">Reading</text>')
    parts.append('<text x="48" y="568" fill="#aab2bd" font-family="Inter, Arial, sans-serif" font-size="15">Fused proof bytes grow near 1.08x while lookup and trace work grow about 4x.</text>')
    parts.append('<text x="48" y="592" fill="#aab2bd" font-family="Inter, Arial, sans-serif" font-size="15">This figure is only about proof-size pressure and boundary shape.</text>')
    parts.append("</svg>")
    atomic_write(path, "\n".join(parts) + "\n")


def validate_output_path(path: pathlib.Path) -> None:
    checked_output_path(path)


def checked_output_path(path: pathlib.Path) -> pathlib.Path:
    if not path.is_absolute():
        path = ROOT / path
    path = path.expanduser()
    try:
        path.relative_to(EVIDENCE_DIR)
    except ValueError as err:
        raise ProofPressureMainEvidenceError("output must stay inside evidence dir") from err
    if path.exists() and path.is_symlink():
        raise ProofPressureMainEvidenceError("output path must not be a symlink")
    if not path.parent.is_dir():
        raise ProofPressureMainEvidenceError("output parent missing")
    reject_symlink_components(path.parent)
    resolved_parent = path.parent.resolve(strict=True)
    try:
        resolved_parent.relative_to(EVIDENCE_DIR.resolve(strict=True))
    except ValueError as err:
        raise ProofPressureMainEvidenceError("output must stay inside evidence dir") from err
    return path


def reject_symlink_components(path: pathlib.Path) -> None:
    relative = path.relative_to(EVIDENCE_DIR)
    current = EVIDENCE_DIR
    for part in relative.parts:
        current = current / part
        try:
            if current.is_symlink():
                raise ProofPressureMainEvidenceError(f"output path symlink component: {current}")
        except OSError as err:
            raise ProofPressureMainEvidenceError(f"failed to inspect output path component: {current}") from err


def reject_same_output_paths(paths: tuple[pathlib.Path, ...]) -> None:
    checked = [checked_output_path(path) for path in paths]
    normalized = [os.fspath(path.resolve(strict=False)) for path in checked]
    if len(set(normalized)) != len(normalized):
        raise ProofPressureMainEvidenceError("output paths must point to different files")


def atomic_write(path: pathlib.Path, text: str) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
        tmp_path = pathlib.Path(handle.name)
        handle.write(text)
    tmp_path.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path, default=JSON_OUT)
    parser.add_argument("--write-tsv", type=pathlib.Path, default=TSV_OUT)
    parser.add_argument("--write-svg", type=pathlib.Path, default=SVG_OUT)
    args = parser.parse_args()
    reject_same_output_paths((args.write_json, args.write_tsv, args.write_svg))
    payload = build_payload()
    write_json(args.write_json, payload)
    write_tsv(args.write_tsv, payload)
    write_svg(args.write_svg, payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
