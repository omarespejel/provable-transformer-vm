#!/usr/bin/env python3.10
"""Read-only Stwo-AI boundary pressure inventory for issue #757."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import pathlib
import sys
from typing import Any


if sys.version_info < (3, 10):
    raise RuntimeError("zkai_stwo_ai_boundary_pressure_inventory_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import zkai_attention_kv_fused_softmax_table_section_delta_gate as section_gate


EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
JSON_OUT = EVIDENCE_DIR / "zkai-stwo-ai-boundary-pressure-inventory-2026-06.json"
TSV_OUT = EVIDENCE_DIR / "zkai-stwo-ai-boundary-pressure-inventory-2026-06.tsv"
SECTION_DELTA_JSON = EVIDENCE_DIR / "zkai-attention-kv-fused-softmax-table-section-delta-2026-05.json"
ROUTE_MATRIX_JSON = EVIDENCE_DIR / "zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json"
QUERY_HOOK_JSON = EVIDENCE_DIR / "zkai-bounded-stwo-query-policy-hook-2026-05.json"
QUERY_PREVIEW_JSON = EVIDENCE_DIR / "zkai-stwo-query-preview-split-prototype-2026-05.json"

SCHEMA = "zkai-stwo-ai-boundary-pressure-inventory-v1"
ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/757"
PARENT_PROOF_PRESSURE_ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/715"
DECISION = "GO_READ_ONLY_STWO_AI_PRESSURE_INVENTORY_NO_FORK_YET"
CLAIM_BOUNDARY = (
    "READ_ONLY_STWO_AI_BOUNDARY_PRESSURE_INVENTORY_FROM_CHECKED_SECTION_DELTA_AND_QUERY_POLICY_EVIDENCE;"
    "NOT_A_PROVER_FORK_NOT_A_NEW_PROOF_SIZE_FRONTIER_NOT_TIMING"
)
FORK_STATUS = "NO_GO_FORK_UNTIL_ADAPTER_LAYER_OR_ROUTE_POLICY_HITS_MEASURED_STWO_INTERNAL_WALL"
UPSTREAM_PATCH_STATUS = "FOLLOWUP_ONLY_IF_ROUTE_POLICY_CANNOT_EXPOSE_REQUIRED_OPENING_OR_QUERY_POLICY_HOOKS"
FIRST_ACTION = "ROUTE_LEVEL_LAYOUT_POLICY_AND_PROOF_SECTION_PROFILER_HARDENING"
PAYLOAD_DOMAIN = "ptvm:zkai:stwo-ai-boundary-pressure-inventory:v1"

EXPECTED_PROFILE_COUNT = 11
EXPECTED_TOTAL_SAVING_BYTES = 223_958
EXPECTED_TOTAL_OPENING_SAVING_BYTES = 209_155
EXPECTED_TOTAL_OPENING_SAVING_SHARE = 0.933903
EXPECTED_LARGEST_PROFILE_ID = "d64_four_head_seq64"
EXPECTED_D64_TOTAL_SAVING_BYTES = 39_282
EXPECTED_D64_OPENING_SAVING_BYTES = 37_827
EXPECTED_D64_FRI_SAVING_BYTES = 27_012
EXPECTED_D64_DECOMMITMENT_SAVING_BYTES = 10_815
EXPECTED_D64_QUERY_SAVING_BYTES = 850
EXPECTED_D64_SOURCE_OPENING_BYTES = 45_896
EXPECTED_D64_SIDECAR_OPENING_BYTES = 40_721
EXPECTED_D64_FUSED_OPENING_BYTES = 48_790
EXPECTED_QUERY_HOOK_DECISION = "NARROW_CLAIM_STWO_2_2_COUPLES_QUERY_DRAW_AND_DECOMMITMENT"
EXPECTED_QUERY_PREVIEW_DECISION = "NARROW_CLAIM_QUERY_PREVIEW_SPLIT_IS_API_FEASIBLE_NOT_SOUND_LABEL_POLICY"
EXPECTED_QUERY_PREVIEW_RESULT = "NO_GO_SOUND_QUERY_GEOMETRY_CONTROL_WITHOUT_GRINDING_OR_POLICY_COMMITMENT"
EXPECTED_ACTION_COUNT = 5

TSV_COLUMNS = (
    "profile_id",
    "axis_role",
    "total_saving_bytes",
    "opening_saving_bytes",
    "opening_saving_share",
    "fri_saving_bytes",
    "decommitment_saving_bytes",
    "query_saving_bytes",
    "sidecar_opening_surface_bytes",
    "fused_opening_minus_source_opening_bytes",
    "sidecar_opening_absorption_share",
    "first_action",
    "fork_status",
)

VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_stwo_ai_boundary_pressure_inventory_gate.py --write-json docs/engineering/evidence/zkai-stwo-ai-boundary-pressure-inventory-2026-06.json --write-tsv docs/engineering/evidence/zkai-stwo-ai-boundary-pressure-inventory-2026-06.tsv",
    "python3.10 -m py_compile scripts/zkai_stwo_ai_boundary_pressure_inventory_gate.py scripts/tests/test_zkai_stwo_ai_boundary_pressure_inventory_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_stwo_ai_boundary_pressure_inventory_gate",
    "git diff --check",
)

NON_CLAIMS = (
    "not a Stwo fork",
    "not a custom prover",
    "not a new proof-size frontier",
    "not a proving-speed claim",
    "not a backend-internal semantic byte attribution",
    "not permission to delete FRI or decommitment witness material",
    "not a post-query label-selection policy",
    "not an external query override",
    "not a NANOZK, Jolt Atlas, EZKL, RISC Zero, SP1, or DeepProve comparison",
    "not a full transformer or full LLM proof claim",
)

MUTATION_NAMES = (
    "decision_overclaim",
    "fork_status_promoted",
    "total_saving_smuggling",
    "opening_share_smuggling",
    "largest_profile_relabeling",
    "d64_opening_metric_smuggling",
    "query_preview_result_overclaim",
    "unsafe_action_removed",
    "source_artifact_digest_drift",
    "payload_commitment_drift",
)


class StwoAiBoundaryPressureInventoryError(Exception):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    except (TypeError, ValueError) as err:
        raise StwoAiBoundaryPressureInventoryError(f"non-canonical JSON value: {err}") from err


def blake2b_commitment(domain: str, value: Any) -> str:
    return "blake2b-256:" + hashlib.blake2b(
        domain.encode() + b"\0" + canonical_json_bytes(value),
        digest_size=32,
    ).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload_commitment(payload: dict[str, Any]) -> str:
    item = copy.deepcopy(payload)
    for key in (
        "payload_commitment",
        "mutation_results",
        "mutations_checked",
        "mutations_rejected",
        "all_mutations_rejected",
    ):
        item.pop(key, None)
    return blake2b_commitment(PAYLOAD_DOMAIN, item)


def ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        raise StwoAiBoundaryPressureInventoryError("ratio denominator must be positive")
    return round(numerator / denominator, 6)


def read_json(path: pathlib.Path) -> Any:
    if not path.is_file():
        raise StwoAiBoundaryPressureInventoryError(f"missing evidence file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise StwoAiBoundaryPressureInventoryError(f"invalid JSON: {path}: {err}") from err


def source_artifact(path: pathlib.Path, artifact_id: str) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def load_section_delta_payload() -> dict[str, Any]:
    payload = read_json(SECTION_DELTA_JSON)
    if not isinstance(payload, dict):
        raise StwoAiBoundaryPressureInventoryError("section delta payload must be object")
    section_gate.validate_payload(payload, expected_rows=payload.get("profile_rows"))
    return payload


def opening_bytes(artifact: dict[str, Any]) -> int:
    sections = artifact["section_bytes"]
    return int(sections["fri_proof"]) + int(sections["decommitments"])


def query_bytes(section_delta: dict[str, int]) -> int:
    return int(section_delta["sampled_values"]) + int(section_delta["queried_values"])


def classify_row(row: dict[str, Any]) -> dict[str, Any]:
    sizes = row["proof_size_bytes"]
    buckets = row["bucket_delta_bytes"]
    sections = row["section_delta_bytes"]
    source_opening = opening_bytes(row["artifacts"]["source"])
    sidecar_opening = opening_bytes(row["artifacts"]["sidecar"])
    fused_opening = opening_bytes(row["artifacts"]["fused"])
    total_saving = int(sizes["delta"])
    opening_saving = int(buckets["opening_bucket_bytes"])
    query_saving = query_bytes(sections)
    fused_over_source = fused_opening - source_opening
    if opening_saving != sidecar_opening - fused_over_source:
        raise StwoAiBoundaryPressureInventoryError(f"{row['profile_id']} opening algebra drift")
    first_action = FIRST_ACTION
    if opening_saving < 0:
        first_action = "NO_GO_OPENING_REGRESSION_ANALYSIS"
    elif ratio(opening_saving, total_saving) < 0.8:
        first_action = "PROFILER_HARDENING_BEFORE_ROUTE_POLICY"
    return {
        "profile_id": row["profile_id"],
        "axis_role": row["axis_role"],
        "key_width": row["key_width"],
        "value_width": row["value_width"],
        "head_count": row["head_count"],
        "steps_per_head": row["steps_per_head"],
        "lookup_claims": row["lookup_claims"],
        "trace_rows": row["trace_rows"],
        "total_saving_bytes": total_saving,
        "opening_saving_bytes": opening_saving,
        "opening_saving_share": ratio(opening_saving, total_saving),
        "fri_saving_bytes": int(sections["fri_proof"]),
        "decommitment_saving_bytes": int(sections["decommitments"]),
        "query_saving_bytes": query_saving,
        "commitment_saving_bytes": int(sections["commitments"]),
        "source_opening_surface_bytes": source_opening,
        "sidecar_opening_surface_bytes": sidecar_opening,
        "fused_opening_surface_bytes": fused_opening,
        "fused_opening_minus_source_opening_bytes": fused_over_source,
        "sidecar_opening_absorption_share": ratio(opening_saving, sidecar_opening),
        "first_action": first_action,
        "fork_status": FORK_STATUS,
        "upstream_patch_status": UPSTREAM_PATCH_STATUS,
    }


def action_queue(query_hook: dict[str, Any], query_preview: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "action": "proof_section_profiler_hardening",
            "status": "START_NOW",
            "reason": "existing evidence shows opening/decommitment dominance but remains serialized-section, not backend-internal attribution",
        },
        {
            "rank": 2,
            "action": "route_level_layout_policy",
            "status": "START_NOW",
            "reason": "d64_four_head_seq64 saves 37,827 opening bytes while query data moves only 850 bytes",
        },
        {
            "rank": 3,
            "action": "local_stwo_wrapper_or_adapter",
            "status": "FOLLOWUP_AFTER_ROUTE_POLICY",
            "reason": "wrapper can enforce deterministic route and statement policy without changing Stwo internals",
        },
        {
            "rank": 4,
            "action": "upstream_stwo_patch_or_small_fork",
            "status": "FOLLOWUP_ONLY_IF_API_WALL_CONFIRMED",
            "reason": (
                "query evidence says Stwo 2.2 couples query draw and decommitment; preview is API-feasible but not a sound "
                "post-query policy"
            ),
            "query_hook_decision": query_hook["decision"],
            "query_preview_decision": query_preview["decision"],
            "query_preview_result": query_preview["result"],
        },
        {
            "rank": 5,
            "action": "actual_independent_stwo_ai_fork",
            "status": "NO_GO_NOW",
            "reason": "no measured adapter-layer wall yet; a fork would create maintenance cost before the optimization target is isolated",
        },
    ]


def build_payload() -> dict[str, Any]:
    section_payload = load_section_delta_payload()
    route_matrix = read_json(ROUTE_MATRIX_JSON)
    query_hook = read_json(QUERY_HOOK_JSON)
    query_preview = read_json(QUERY_PREVIEW_JSON)
    rows = [classify_row(row) for row in section_payload["profile_rows"]]
    largest = max(rows, key=lambda row: row["total_saving_bytes"])
    d64 = next(row for row in rows if row["profile_id"] == EXPECTED_LARGEST_PROFILE_ID)
    opening_total = sum(row["opening_saving_bytes"] for row in rows)
    saving_total = sum(row["total_saving_bytes"] for row in rows)
    payload = {
        "schema": SCHEMA,
        "issue": ISSUE,
        "parent_proof_pressure_issue": PARENT_PROOF_PRESSURE_ISSUE,
        "decision": DECISION,
        "claim_boundary": CLAIM_BOUNDARY,
        "fork_status": FORK_STATUS,
        "upstream_patch_status": UPSTREAM_PATCH_STATUS,
        "source_artifacts": [
            source_artifact(SECTION_DELTA_JSON, "section_delta_json"),
            source_artifact(ROUTE_MATRIX_JSON, "route_matrix_json"),
            source_artifact(QUERY_HOOK_JSON, "query_hook_json"),
            source_artifact(QUERY_PREVIEW_JSON, "query_preview_json"),
        ],
        "source_evidence": {
            "section_delta_schema": section_payload["schema"],
            "section_delta_commitment": section_payload["section_delta_commitment"],
            "route_matrix_schema": route_matrix["schema"],
            "query_hook_schema": query_hook["schema"],
            "query_hook_decision": query_hook["decision"],
            "query_preview_schema": query_preview["schema"],
            "query_preview_decision": query_preview["decision"],
            "query_preview_result": query_preview["result"],
        },
        "aggregate": {
            "profiles_checked": len(rows),
            "total_saving_bytes": saving_total,
            "total_opening_saving_bytes": opening_total,
            "total_opening_saving_share": ratio(opening_total, saving_total),
            "largest_profile_id": largest["profile_id"],
            "largest_profile_saving_bytes": largest["total_saving_bytes"],
            "d64_four_head_seq64": {
                "total_saving_bytes": d64["total_saving_bytes"],
                "opening_saving_bytes": d64["opening_saving_bytes"],
                "opening_saving_share": d64["opening_saving_share"],
                "fri_saving_bytes": d64["fri_saving_bytes"],
                "decommitment_saving_bytes": d64["decommitment_saving_bytes"],
                "query_saving_bytes": d64["query_saving_bytes"],
                "source_opening_surface_bytes": d64["source_opening_surface_bytes"],
                "sidecar_opening_surface_bytes": d64["sidecar_opening_surface_bytes"],
                "fused_opening_surface_bytes": d64["fused_opening_surface_bytes"],
                "fused_opening_minus_source_opening_bytes": d64["fused_opening_minus_source_opening_bytes"],
                "sidecar_opening_absorption_share": d64["sidecar_opening_absorption_share"],
            },
        },
        "pressure_rows": rows,
        "action_queue": action_queue(query_hook, query_preview),
        "unsafe_actions": [
            "delete FRI proof or decommitment witness material inside a valid proof",
            "choose route labels after seeing final proof bytes",
            "choose route labels after Fiat-Shamir queries without a verifier-visible retry budget",
            "override canonical Fiat-Shamir queries externally",
            "claim backend-internal source-vs-lookup byte attribution from serialized proof sections",
        ],
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload, require_mutations=False)
    payload["mutation_results"] = mutation_results(payload)
    payload["mutations_checked"] = len(payload["mutation_results"])
    payload["mutations_rejected"] = sum(1 for item in payload["mutation_results"] if item["rejected"])
    payload["all_mutations_rejected"] = payload["mutations_checked"] == payload["mutations_rejected"]
    validate_payload(payload)
    return payload


def validate_payload(payload: Any, *, require_mutations: bool = True) -> None:
    if not isinstance(payload, dict):
        raise StwoAiBoundaryPressureInventoryError("payload must be object")
    expected = {
        "schema",
        "issue",
        "parent_proof_pressure_issue",
        "decision",
        "claim_boundary",
        "fork_status",
        "upstream_patch_status",
        "source_artifacts",
        "source_evidence",
        "aggregate",
        "pressure_rows",
        "action_queue",
        "unsafe_actions",
        "non_claims",
        "validation_commands",
        "payload_commitment",
    }
    mutation_keys = {"mutation_results", "mutations_checked", "mutations_rejected", "all_mutations_rejected"}
    allowed = expected | mutation_keys
    if set(payload) - allowed or expected - set(payload):
        raise StwoAiBoundaryPressureInventoryError("payload field drift")
    for key, value in (
        ("schema", SCHEMA),
        ("issue", ISSUE),
        ("parent_proof_pressure_issue", PARENT_PROOF_PRESSURE_ISSUE),
        ("decision", DECISION),
        ("claim_boundary", CLAIM_BOUNDARY),
        ("fork_status", FORK_STATUS),
        ("upstream_patch_status", UPSTREAM_PATCH_STATUS),
        ("non_claims", list(NON_CLAIMS)),
        ("validation_commands", list(VALIDATION_COMMANDS)),
    ):
        if payload[key] != value:
            raise StwoAiBoundaryPressureInventoryError(f"{key} drift")
    if "delete FRI proof or decommitment witness material inside a valid proof" not in payload["unsafe_actions"]:
        raise StwoAiBoundaryPressureInventoryError("unsafe action inventory drift")
    if len(payload["source_artifacts"]) != 4:
        raise StwoAiBoundaryPressureInventoryError("source artifact inventory drift")
    for artifact in payload["source_artifacts"]:
        if set(artifact) != {"id", "path", "sha256", "size_bytes"}:
            raise StwoAiBoundaryPressureInventoryError("source artifact field drift")
        path = ROOT / artifact["path"]
        if not path.is_file() or sha256_file(path) != artifact["sha256"]:
            raise StwoAiBoundaryPressureInventoryError("source artifact digest drift")
        if path.stat().st_size != artifact["size_bytes"]:
            raise StwoAiBoundaryPressureInventoryError("source artifact size drift")
    evidence = payload["source_evidence"]
    if evidence["query_hook_decision"] != EXPECTED_QUERY_HOOK_DECISION:
        raise StwoAiBoundaryPressureInventoryError("query hook decision drift")
    if evidence["query_preview_decision"] != EXPECTED_QUERY_PREVIEW_DECISION:
        raise StwoAiBoundaryPressureInventoryError("query preview decision drift")
    if evidence["query_preview_result"] != EXPECTED_QUERY_PREVIEW_RESULT:
        raise StwoAiBoundaryPressureInventoryError("query preview result drift")
    rows = payload["pressure_rows"]
    if not isinstance(rows, list) or len(rows) != EXPECTED_PROFILE_COUNT:
        raise StwoAiBoundaryPressureInventoryError("pressure row count drift")
    if [row.get("profile_id") for row in rows if isinstance(row, dict)] != list(section_gate.EXPECTED_PROFILE_IDS):
        raise StwoAiBoundaryPressureInventoryError("pressure row order drift")
    for row in rows:
        validate_pressure_row(row)
    aggregate = payload["aggregate"]
    if aggregate["profiles_checked"] != EXPECTED_PROFILE_COUNT:
        raise StwoAiBoundaryPressureInventoryError("profile count drift")
    if aggregate["total_saving_bytes"] != EXPECTED_TOTAL_SAVING_BYTES:
        raise StwoAiBoundaryPressureInventoryError("total saving drift")
    if aggregate["total_opening_saving_bytes"] != EXPECTED_TOTAL_OPENING_SAVING_BYTES:
        raise StwoAiBoundaryPressureInventoryError("opening saving drift")
    if aggregate["total_opening_saving_share"] != EXPECTED_TOTAL_OPENING_SAVING_SHARE:
        raise StwoAiBoundaryPressureInventoryError("opening share drift")
    if aggregate["largest_profile_id"] != EXPECTED_LARGEST_PROFILE_ID:
        raise StwoAiBoundaryPressureInventoryError("largest profile drift")
    d64 = aggregate["d64_four_head_seq64"]
    expected_d64 = {
        "total_saving_bytes": EXPECTED_D64_TOTAL_SAVING_BYTES,
        "opening_saving_bytes": EXPECTED_D64_OPENING_SAVING_BYTES,
        "fri_saving_bytes": EXPECTED_D64_FRI_SAVING_BYTES,
        "decommitment_saving_bytes": EXPECTED_D64_DECOMMITMENT_SAVING_BYTES,
        "query_saving_bytes": EXPECTED_D64_QUERY_SAVING_BYTES,
        "source_opening_surface_bytes": EXPECTED_D64_SOURCE_OPENING_BYTES,
        "sidecar_opening_surface_bytes": EXPECTED_D64_SIDECAR_OPENING_BYTES,
        "fused_opening_surface_bytes": EXPECTED_D64_FUSED_OPENING_BYTES,
    }
    for key, value in expected_d64.items():
        if d64[key] != value:
            raise StwoAiBoundaryPressureInventoryError(f"d64 {key} drift")
    if len(payload["action_queue"]) != EXPECTED_ACTION_COUNT:
        raise StwoAiBoundaryPressureInventoryError("action queue count drift")
    if payload["action_queue"][0]["action"] != "proof_section_profiler_hardening":
        raise StwoAiBoundaryPressureInventoryError("first action drift")
    if payload["action_queue"][-1]["status"] != "NO_GO_NOW":
        raise StwoAiBoundaryPressureInventoryError("fork action status drift")
    if payload_commitment(payload) != payload["payload_commitment"]:
        raise StwoAiBoundaryPressureInventoryError("payload commitment drift")
    if require_mutations:
        if not mutation_keys <= set(payload):
            raise StwoAiBoundaryPressureInventoryError("mutation summary missing")
        if payload["mutations_checked"] != len(MUTATION_NAMES):
            raise StwoAiBoundaryPressureInventoryError("mutation count drift")
        if payload["mutations_rejected"] != len(MUTATION_NAMES):
            raise StwoAiBoundaryPressureInventoryError("mutation rejection drift")
        if payload["all_mutations_rejected"] is not True:
            raise StwoAiBoundaryPressureInventoryError("mutation rejection flag drift")


def validate_pressure_row(row: Any) -> None:
    if not isinstance(row, dict):
        raise StwoAiBoundaryPressureInventoryError("pressure row must be object")
    expected = {
        "profile_id",
        "axis_role",
        "key_width",
        "value_width",
        "head_count",
        "steps_per_head",
        "lookup_claims",
        "trace_rows",
        "total_saving_bytes",
        "opening_saving_bytes",
        "opening_saving_share",
        "fri_saving_bytes",
        "decommitment_saving_bytes",
        "query_saving_bytes",
        "commitment_saving_bytes",
        "source_opening_surface_bytes",
        "sidecar_opening_surface_bytes",
        "fused_opening_surface_bytes",
        "fused_opening_minus_source_opening_bytes",
        "sidecar_opening_absorption_share",
        "first_action",
        "fork_status",
        "upstream_patch_status",
    }
    if set(row) != expected:
        raise StwoAiBoundaryPressureInventoryError("pressure row field drift")
    if row["fork_status"] != FORK_STATUS:
        raise StwoAiBoundaryPressureInventoryError("pressure row fork status drift")
    if row["upstream_patch_status"] != UPSTREAM_PATCH_STATUS:
        raise StwoAiBoundaryPressureInventoryError("pressure row upstream status drift")
    if row["total_saving_bytes"] <= 0:
        raise StwoAiBoundaryPressureInventoryError("pressure row must save bytes")
    if row["opening_saving_bytes"] != row["fri_saving_bytes"] + row["decommitment_saving_bytes"]:
        raise StwoAiBoundaryPressureInventoryError("pressure row opening sum drift")
    if row["opening_saving_share"] != ratio(row["opening_saving_bytes"], row["total_saving_bytes"]):
        raise StwoAiBoundaryPressureInventoryError("pressure row opening share drift")
    expected_absorption = ratio(row["opening_saving_bytes"], row["sidecar_opening_surface_bytes"])
    if row["sidecar_opening_absorption_share"] != expected_absorption:
        raise StwoAiBoundaryPressureInventoryError("sidecar absorption drift")
    if row["opening_saving_bytes"] != row["sidecar_opening_surface_bytes"] - row["fused_opening_minus_source_opening_bytes"]:
        raise StwoAiBoundaryPressureInventoryError("opening algebra drift")


def mutate_payload(payload: dict[str, Any], name: str) -> dict[str, Any]:
    out = copy.deepcopy(payload)
    for key in ("mutation_results", "mutations_checked", "mutations_rejected", "all_mutations_rejected"):
        out.pop(key, None)
    if name == "decision_overclaim":
        out["decision"] = "GO_BUILD_CUSTOM_STWO_AI_FORK_NOW"
    elif name == "fork_status_promoted":
        out["fork_status"] = "GO_FORK_NOW"
    elif name == "total_saving_smuggling":
        out["aggregate"]["total_saving_bytes"] += 1
    elif name == "opening_share_smuggling":
        out["aggregate"]["total_opening_saving_share"] = 1.0
    elif name == "largest_profile_relabeling":
        out["aggregate"]["largest_profile_id"] = "d8_single_head_seq8"
    elif name == "d64_opening_metric_smuggling":
        out["aggregate"]["d64_four_head_seq64"]["opening_saving_bytes"] += 1
    elif name == "query_preview_result_overclaim":
        out["source_evidence"]["query_preview_result"] = "GO_SOUND_POST_QUERY_LABEL_POLICY"
    elif name == "unsafe_action_removed":
        out["unsafe_actions"].remove("delete FRI proof or decommitment witness material inside a valid proof")
    elif name == "source_artifact_digest_drift":
        out["source_artifacts"][0]["sha256"] = "0" * 64
    elif name == "payload_commitment_drift":
        out["payload_commitment"] = "blake2b-256:" + "0" * 64
    else:
        raise StwoAiBoundaryPressureInventoryError(f"unknown mutation: {name}")
    return out


def mutation_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for name in MUTATION_NAMES:
        try:
            validate_payload(mutate_payload(payload, name), require_mutations=False)
        except StwoAiBoundaryPressureInventoryError as err:
            results.append({"name": name, "rejected": True, "error": str(err)})
        else:
            results.append({"name": name, "rejected": False, "error": ""})
    return results


def to_tsv(payload: dict[str, Any]) -> str:
    rows = []
    for row in payload["pressure_rows"]:
        rows.append({key: row[key] for key in TSV_COLUMNS})
    from io import StringIO

    out = StringIO()
    writer = csv.DictWriter(out, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def reject_bad_output_path(path: pathlib.Path) -> None:
    resolved = path.resolve()
    evidence = EVIDENCE_DIR.resolve()
    try:
        resolved.parent.relative_to(evidence)
    except ValueError as err:
        raise StwoAiBoundaryPressureInventoryError("output path must stay inside evidence dir") from err
    if resolved.parent.is_symlink():
        raise StwoAiBoundaryPressureInventoryError("output path parent must not be symlink")


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path, tsv_path: pathlib.Path) -> None:
    if json_path.resolve() == tsv_path.resolve():
        raise StwoAiBoundaryPressureInventoryError("JSON and TSV output paths must differ")
    reject_bad_output_path(json_path)
    reject_bad_output_path(tsv_path)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tsv_path.write_text(to_tsv(payload), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    args = parser.parse_args()
    payload = build_payload()
    if args.write_json or args.write_tsv:
        if not (args.write_json and args.write_tsv):
            raise StwoAiBoundaryPressureInventoryError("--write-json and --write-tsv must be used together")
        write_outputs(payload, args.write_json, args.write_tsv)
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
