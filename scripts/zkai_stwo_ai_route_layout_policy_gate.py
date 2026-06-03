#!/usr/bin/env python3
"""Stwo-AI route-layout policy selector for issue #757.

This gate is deliberately cheap: it consumes already checked section-delta and
route-matrix evidence, then selects the next deterministic route-layout
experiment. It does not run the prover and it does not claim a new proof-size
frontier.
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
from io import StringIO
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import zkai_attention_kv_fused_softmax_table_route_matrix_gate as route_matrix
from scripts import zkai_attention_kv_fused_softmax_table_section_delta_gate as section_delta

EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
DOCS_DIR = ROOT / "docs" / "engineering"
SECTION_DELTA_JSON = EVIDENCE_DIR / "zkai-attention-kv-fused-softmax-table-section-delta-2026-05.json"
ROUTE_MATRIX_JSON = EVIDENCE_DIR / "zkai-attention-kv-fused-softmax-table-route-matrix-2026-05.json"
JSON_OUT = EVIDENCE_DIR / "zkai-stwo-ai-route-layout-policy-2026-06.json"
TSV_OUT = EVIDENCE_DIR / "zkai-stwo-ai-route-layout-policy-2026-06.tsv"
MD_OUT = DOCS_DIR / "zkai-stwo-ai-route-layout-policy-2026-06-04.md"

SCHEMA = "zkai-stwo-ai-route-layout-policy-v1"
ISSUE = 757
SOURCE_ISSUE = 531
ROUTE_MATRIX_ISSUE = 505
DECISION = "GO_ROUTE_LAYOUT_POLICY_SELECTOR_FROM_EXISTING_SECTION_DELTA_NO_PROVER_RUN"
ROUTE_ID = "local_stwo_ai_route_layout_policy_selector"
CLAIM_BOUNDARY = (
    "EXPERIMENTAL_STWO_AI_ROUTE_LAYOUT_POLICY_SELECTION_FROM_CHECKED_SECTION_DELTA_EVIDENCE_"
    "NOT_A_NEW_PROOF_SIZE_FRONTIER_NOT_A_STWO_FORK_NOT_POST_QUERY_SELECTION"
)
FORK_STATUS = "NO_GO_FORK_UNTIL_ROUTE_POLICY_HITS_MEASURED_INTERNAL_WALL"
NEXT_POLICY_STATUS = "START_DETERMINISTIC_ROUTE_LAYOUT_POLICY_ON_FAST_SEQUENCE_TARGET"
PROVER_POLICY = "no_prover_run_existing_artifact_accounting_only"
TIMING_POLICY = "no_timing_claim_no_public_benchmark"
SECURITY_POLICY = (
    "route_layout_policy_must_be_fixed_before_proof_generation_and_verifier_bound_before_any_query_draw"
)
BACKEND_VERSION_METADATA = {
    "stwo_crate": "stwo 2.2.0",
    "stwo_crate_checksum": "d400ae91acbeafa6f80070a03e1117a794a95f295050f44538a4c7dd55abd491",
    "stwo_constraint_framework_crate": "stwo-constraint-framework 2.2.0",
    "stwo_constraint_framework_checksum": "47aca0d5d36d4b015703fb14f162a23cb685e67f8aa08dbe7faf39bd66fe93f1",
    "evidence_base_commit": "11411122c02e56ca434a90f54e0afb1988211b8d",
    "fast_target_version_const": (
        "ZKAI_ATTENTION_KV_NATIVE_TWO_HEAD_SEQ32_FUSED_SOFTMAX_TABLE_BACKEND_VERSION="
        "stwo-attention-kv-two-head-seq32-fused-bounded-softmax-table-logup-v1"
    ),
    "pressure_anchor_version_const": (
        "ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ64_FUSED_SOFTMAX_TABLE_BACKEND_VERSION="
        "stwo-attention-kv-d64-four-head-seq64-fused-bounded-softmax-table-logup-v1"
    ),
}
SECTION_DELTA_SHA256 = "046b9997b673f22a9f45eb02c75f2c5f23255eb3fa3b88922dcd8cfe5a27e14d"
ROUTE_MATRIX_SHA256 = "f8da6eb33454011e3ef20b7b80cdcce4ff9086764d7b4a3868c684046b434701"
HEADLINE_PRESSURE_ANCHOR_PROFILE_ID = "d64_four_head_seq64"
FAST_SEQUENCE_TARGET_PROFILE_ID = "d8_two_head_seq32"
ABSORPTION_SANITY_PROFILE_ID = "d16_two_head_seq16"
HEAD_AXIS_FALLBACK_PROFILE_ID = "d8_four_head_seq8"
FAST_SEQUENCE_MIN_STEPS = 32
FAST_SEQUENCE_MIN_LOOKUP_CLAIMS = 1_000
MAX_FAST_TARGET_FUSED_PROOF_BYTES = 100_000
OPENING_BUCKET_KEYS = ("fri_proof", "decommitments")
TSV_COLUMNS = (
    "profile_id",
    "policy_role",
    "key_width",
    "head_count",
    "steps_per_head",
    "lookup_claims",
    "trace_rows",
    "fused_proof_size_bytes",
    "source_plus_sidecar_raw_proof_bytes",
    "fused_saves_vs_source_plus_sidecar_bytes",
    "opening_bucket_savings_bytes",
    "opening_savings_share",
    "sidecar_opening_absorption_share",
    "query_bucket_savings_bytes",
    "fused_opening_minus_source_opening_bytes",
    "selector_reason",
)
NON_CLAIMS = (
    "not a new proof-size result",
    "not a Stwo fork",
    "not a backend patch",
    "not post-query label selection",
    "not transcript grinding",
    "not timing evidence",
    "not production-security parameter evidence",
    "not backend-internal semantic byte attribution",
    "not exact real-valued Softmax",
    "not full transformer inference",
)
VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_stwo_ai_route_layout_policy_gate.py --write-json docs/engineering/evidence/zkai-stwo-ai-route-layout-policy-2026-06.json --write-tsv docs/engineering/evidence/zkai-stwo-ai-route-layout-policy-2026-06.tsv --write-md docs/engineering/zkai-stwo-ai-route-layout-policy-2026-06-04.md",
    "python3.10 -m py_compile scripts/zkai_stwo_ai_route_layout_policy_gate.py scripts/tests/test_zkai_stwo_ai_route_layout_policy_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_stwo_ai_route_layout_policy_gate",
    "git diff --check",
)
EXPECTED_PROFILE_IDS = tuple(section_delta.EXPECTED_PROFILE_IDS)
EXPECTED_PROFILE_COUNT = len(EXPECTED_PROFILE_IDS)
EXPECTED_MUTATION_NAMES = (
    "decision_overclaim",
    "fork_status_premature_promotion",
    "post_query_policy_smuggling",
    "source_artifact_digest_drift",
    "route_matrix_digest_drift",
    "headline_anchor_relabeling",
    "fast_sequence_target_relabeling",
    "fast_target_metric_smuggling",
    "d64_anchor_metric_smuggling",
    "opening_share_metric_smuggling",
    "query_savings_overclaim",
    "unsafe_action_removed",
    "non_claim_removed",
    "payload_commitment_drift",
    "unknown_field_injection",
)
EXPECTED_MUTATION_COUNT = len(EXPECTED_MUTATION_NAMES)
EXPECTED_TOTAL_OPENING_SAVINGS_BYTES = 209_155
EXPECTED_TOTAL_SAVINGS_BYTES = 223_958
EXPECTED_TOTAL_OPENING_SAVINGS_SHARE = 0.933903
EXPECTED_HEADLINE_ANCHOR_SAVINGS_BYTES = 39_282
EXPECTED_FAST_SEQUENCE_TARGET_SAVINGS_BYTES = 31_685
EXPECTED_FAST_SEQUENCE_TARGET_OPENING_SHARE = 0.953227
EXPECTED_FAST_SEQUENCE_TARGET_ABSORPTION_SHARE = 0.926899


class StwoAiRouteLayoutPolicyGateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def blake2b_commitment(value: Any, domain: str) -> str:
    digest = hashlib.blake2b(digest_size=32)
    digest.update(domain.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(value))
    return f"blake2b-256:{digest.hexdigest()}"


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise StwoAiRouteLayoutPolicyGateError(f"{label} must be an integer")
    return value


def require_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise StwoAiRouteLayoutPolicyGateError(f"{label} must be a non-empty string")
    return value


def ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        raise StwoAiRouteLayoutPolicyGateError("ratio denominator must be positive")
    return round(numerator / denominator, 6)


def read_json(path: pathlib.Path, expected_sha256: str, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise StwoAiRouteLayoutPolicyGateError(f"missing {label}: {path}")
    actual_sha256 = sha256_file(path)
    if actual_sha256 != expected_sha256:
        raise StwoAiRouteLayoutPolicyGateError(f"{label} sha256 drift")
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise StwoAiRouteLayoutPolicyGateError(f"{label} must be object")
    return payload


def load_source_artifacts() -> tuple[dict[str, Any], dict[str, Any]]:
    section_payload = read_json(SECTION_DELTA_JSON, SECTION_DELTA_SHA256, "section delta evidence")
    route_payload = read_json(ROUTE_MATRIX_JSON, ROUTE_MATRIX_SHA256, "route matrix evidence")
    section_delta.validate_payload(section_payload)
    route_matrix.validate_result(route_payload)
    return section_payload, route_payload


def route_rows_by_profile(route_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows_by_profile: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(route_payload["route_rows"]):
        profile_id = require_str(row.get("profile_id"), f"route row {index} profile_id")
        if profile_id in rows_by_profile:
            raise StwoAiRouteLayoutPolicyGateError(f"duplicate route matrix profile_id: {profile_id}")
        rows_by_profile[profile_id] = row
    return rows_by_profile


def row_opening_bytes(row: dict[str, Any], role: str) -> int:
    sections = row["artifacts"][role]["section_bytes"]
    return sum(
        require_int(sections[key], f"{row['profile_id']} {role} {key}") for key in OPENING_BUCKET_KEYS
    )


def policy_role(profile_id: str) -> str:
    if profile_id == HEADLINE_PRESSURE_ANCHOR_PROFILE_ID:
        return "headline_pressure_anchor"
    if profile_id == FAST_SEQUENCE_TARGET_PROFILE_ID:
        return "fast_sequence_iteration_target"
    if profile_id == ABSORPTION_SANITY_PROFILE_ID:
        return "absorption_sanity_check"
    if profile_id == HEAD_AXIS_FALLBACK_PROFILE_ID:
        return "head_axis_fallback"
    return "context_profile"


def selector_reason(profile_id: str) -> str:
    if profile_id == HEADLINE_PRESSURE_ANCHOR_PROFILE_ID:
        return "largest checked fused saving and exact headline d64 section-delta row"
    if profile_id == FAST_SEQUENCE_TARGET_PROFILE_ID:
        return "smallest checked seq32 target above the lookup-pressure threshold and below the fast-iteration byte cap"
    if profile_id == ABSORPTION_SANITY_PROFILE_ID:
        return "highest sub-unit sidecar-opening absorption sanity row among low-cost width-plus-sequence fixtures"
    if profile_id == HEAD_AXIS_FALLBACK_PROFILE_ID:
        return "lowest-cost head-axis fallback with fused opening smaller than source opening"
    return "context row for selector stability"


def build_policy_metric_row(row: dict[str, Any], route_row: dict[str, Any]) -> dict[str, Any]:
    proof_sizes = row["proof_size_bytes"]
    source_opening = row_opening_bytes(row, "source")
    sidecar_opening = row_opening_bytes(row, "sidecar")
    fused_opening = row_opening_bytes(row, "fused")
    opening_savings = row["bucket_delta_bytes"]["opening_bucket_bytes"]
    total_savings = proof_sizes["delta"]
    metric = {
        "profile_id": row["profile_id"],
        "policy_role": policy_role(row["profile_id"]),
        "axis_role": row["axis_role"],
        "key_width": row["key_width"],
        "head_count": row["head_count"],
        "steps_per_head": row["steps_per_head"],
        "lookup_claims": row["lookup_claims"],
        "trace_rows": row["trace_rows"],
        "fused_proof_size_bytes": proof_sizes["fused"],
        "source_plus_sidecar_raw_proof_bytes": proof_sizes["source_plus_sidecar"],
        "fused_saves_vs_source_plus_sidecar_bytes": total_savings,
        "opening_bucket_savings_bytes": opening_savings,
        "opening_savings_share": ratio(opening_savings, total_savings),
        "sidecar_opening_bucket_bytes": sidecar_opening,
        "sidecar_opening_absorption_share": ratio(opening_savings, sidecar_opening),
        "query_bucket_savings_bytes": row["bucket_delta_bytes"]["query_bucket_bytes"],
        "fused_opening_minus_source_opening_bytes": fused_opening - source_opening,
        "source_opening_bucket_bytes": source_opening,
        "fused_opening_bucket_bytes": fused_opening,
        "selector_reason": selector_reason(row["profile_id"]),
    }
    for key in (
        "key_width",
        "head_count",
        "steps_per_head",
        "lookup_claims",
        "trace_rows",
        "fused_proof_size_bytes",
        "source_plus_sidecar_raw_proof_bytes",
        "fused_saves_vs_source_plus_sidecar_bytes",
    ):
        if metric[key] != route_row.get(key):
            raise StwoAiRouteLayoutPolicyGateError(f"{row['profile_id']} route matrix cross-check drift for {key}")
    validate_policy_metric_row(metric)
    return metric


def build_policy_metric_rows(
    section_payload: dict[str, Any],
    route_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    route_by_id = route_rows_by_profile(route_payload)
    rows = []
    for row in section_payload["profile_rows"]:
        if row["profile_id"] not in route_by_id:
            raise StwoAiRouteLayoutPolicyGateError("route matrix missing section-delta profile")
        rows.append(build_policy_metric_row(row, route_by_id[row["profile_id"]]))
    if [row["profile_id"] for row in rows] != list(EXPECTED_PROFILE_IDS):
        raise StwoAiRouteLayoutPolicyGateError("policy metric row order drift")
    return rows


def find_row(rows: list[dict[str, Any]], profile_id: str) -> dict[str, Any]:
    for row in rows:
        if row["profile_id"] == profile_id:
            return row
    raise StwoAiRouteLayoutPolicyGateError(f"missing profile row: {profile_id}")


def build_selector(rows: list[dict[str, Any]]) -> dict[str, Any]:
    headline = find_row(rows, HEADLINE_PRESSURE_ANCHOR_PROFILE_ID)
    fast_candidates = [
        row
        for row in rows
        if row["steps_per_head"] >= FAST_SEQUENCE_MIN_STEPS
        and row["lookup_claims"] >= FAST_SEQUENCE_MIN_LOOKUP_CLAIMS
        and row["fused_proof_size_bytes"] <= MAX_FAST_TARGET_FUSED_PROOF_BYTES
    ]
    if not fast_candidates:
        raise StwoAiRouteLayoutPolicyGateError("fast sequence target candidate set empty")
    fast = min(fast_candidates, key=lambda row: (row["fused_proof_size_bytes"], -row["opening_savings_share"]))
    absorption = find_row(rows, ABSORPTION_SANITY_PROFILE_ID)
    fallback = find_row(rows, HEAD_AXIS_FALLBACK_PROFILE_ID)
    selector = {
        "headline_pressure_anchor_profile_id": headline["profile_id"],
        "headline_pressure_anchor_savings_bytes": headline["fused_saves_vs_source_plus_sidecar_bytes"],
        "headline_pressure_anchor_opening_savings_share": headline["opening_savings_share"],
        "fast_sequence_target_profile_id": fast["profile_id"],
        "fast_sequence_target_fused_proof_size_bytes": fast["fused_proof_size_bytes"],
        "fast_sequence_target_savings_bytes": fast["fused_saves_vs_source_plus_sidecar_bytes"],
        "fast_sequence_target_opening_savings_share": fast["opening_savings_share"],
        "fast_sequence_target_sidecar_absorption_share": fast["sidecar_opening_absorption_share"],
        "absorption_sanity_profile_id": absorption["profile_id"],
        "absorption_sanity_sidecar_absorption_share": absorption["sidecar_opening_absorption_share"],
        "head_axis_fallback_profile_id": fallback["profile_id"],
        "head_axis_fallback_fused_opening_minus_source_opening_bytes": fallback[
            "fused_opening_minus_source_opening_bytes"
        ],
        "policy_selector_rule": (
            "use the d64 headline row as the pressure anchor; run the first deterministic route-layout "
            "prototype on the smallest checked seq32 target with at least 1000 lookup claims and under "
            "100000 fused proof bytes; promote only if the policy is fixed before proof generation and "
            "still improves measured fused bytes"
        ),
        "next_action": "prototype_deterministic_route_layout_policy_on_d8_two_head_seq32_then_promote_to_d64_four_head_seq64",
    }
    validate_selector(selector, rows)
    return selector


def build_aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_savings = sum(row["fused_saves_vs_source_plus_sidecar_bytes"] for row in rows)
    total_opening = sum(row["opening_bucket_savings_bytes"] for row in rows)
    aggregate = {
        "profiles_checked": len(rows),
        "total_fused_saves_vs_source_plus_sidecar_bytes": total_savings,
        "total_opening_bucket_savings_bytes": total_opening,
        "total_opening_savings_share": ratio(total_opening, total_savings),
        "largest_savings_profile_id": max(rows, key=lambda row: row["fused_saves_vs_source_plus_sidecar_bytes"])[
            "profile_id"
        ],
        "largest_opening_savings_profile_id": max(rows, key=lambda row: row["opening_bucket_savings_bytes"])[
            "profile_id"
        ],
        "lowest_cost_sequence_profile_id": min(
            (row for row in rows if row["steps_per_head"] >= FAST_SEQUENCE_MIN_STEPS),
            key=lambda row: row["fused_proof_size_bytes"],
        )["profile_id"],
    }
    validate_aggregate(aggregate, rows)
    return aggregate


def build_policy_plan(selector: dict[str, Any]) -> dict[str, Any]:
    plan = {
        "status": NEXT_POLICY_STATUS,
        "fork_status": FORK_STATUS,
        "immediate_target": selector["fast_sequence_target_profile_id"],
        "pressure_anchor": selector["headline_pressure_anchor_profile_id"],
        "promote_after_fast_target_go": selector["headline_pressure_anchor_profile_id"],
        "go_gate": (
            "a verifier-bound deterministic route-layout policy reduces fused proof bytes on "
            "d8_two_head_seq32 without changing statement semantics or selecting after query draw"
        ),
        "no_go_gate": (
            "the policy is equal or heavier, requires post-query selection, or cannot be verifier-bound "
            "before proof generation"
        ),
        "fork_trigger": (
            "fork or patch Stwo only after a deterministic policy hits a measured public-API wall that "
            "prevents verifier-bound layout control"
        ),
        "unsafe_actions_rejected": [
            "choosing labels after transcript queries are sampled",
            "claiming a new proof-size frontier before regenerated proofs exist",
            "forking Stwo before a route-policy wall is measured",
            "using section deltas as backend-internal source-versus-lookup byte attribution",
            "dropping statement binding or route metadata to save bytes",
        ],
    }
    validate_policy_plan(plan, selector)
    return plan


def payload_commitment(payload: dict[str, Any]) -> str:
    payload_for_commitment = copy.deepcopy(payload)
    payload_for_commitment.pop("payload_commitment", None)
    return blake2b_commitment(payload_for_commitment, SCHEMA)


def build_base_payload() -> dict[str, Any]:
    section_payload, route_payload = load_source_artifacts()
    rows = build_policy_metric_rows(section_payload, route_payload)
    selector = build_selector(rows)
    payload = {
        "schema": SCHEMA,
        "issue": ISSUE,
        "source_issue": SOURCE_ISSUE,
        "route_matrix_issue": ROUTE_MATRIX_ISSUE,
        "decision": DECISION,
        "route_id": ROUTE_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "fork_status": FORK_STATUS,
        "next_policy_status": NEXT_POLICY_STATUS,
        "prover_policy": PROVER_POLICY,
        "timing_policy": TIMING_POLICY,
        "security_policy": SECURITY_POLICY,
        "backend_version_metadata": copy.deepcopy(BACKEND_VERSION_METADATA),
        "source_artifacts": {
            "section_delta_json": str(SECTION_DELTA_JSON.relative_to(ROOT)),
            "section_delta_sha256": SECTION_DELTA_SHA256,
            "route_matrix_json": str(ROUTE_MATRIX_JSON.relative_to(ROOT)),
            "route_matrix_sha256": ROUTE_MATRIX_SHA256,
        },
        "profile_ids": list(EXPECTED_PROFILE_IDS),
        "policy_metric_rows": rows,
        "selector": selector,
        "aggregate": build_aggregate(rows),
        "policy_plan": build_policy_plan(selector),
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload, allow_missing_mutation_summary=True)
    return payload


def validate_policy_metric_row(row: Any) -> None:
    if not isinstance(row, dict):
        raise StwoAiRouteLayoutPolicyGateError("policy metric row must be object")
    expected = {
        "profile_id",
        "policy_role",
        "axis_role",
        "key_width",
        "head_count",
        "steps_per_head",
        "lookup_claims",
        "trace_rows",
        "fused_proof_size_bytes",
        "source_plus_sidecar_raw_proof_bytes",
        "fused_saves_vs_source_plus_sidecar_bytes",
        "opening_bucket_savings_bytes",
        "opening_savings_share",
        "sidecar_opening_bucket_bytes",
        "sidecar_opening_absorption_share",
        "query_bucket_savings_bytes",
        "fused_opening_minus_source_opening_bytes",
        "source_opening_bucket_bytes",
        "fused_opening_bucket_bytes",
        "selector_reason",
    }
    if set(row) != expected:
        raise StwoAiRouteLayoutPolicyGateError("policy metric row field drift")
    if row["profile_id"] not in EXPECTED_PROFILE_IDS:
        raise StwoAiRouteLayoutPolicyGateError("profile id drift")
    if row["policy_role"] != policy_role(row["profile_id"]):
        raise StwoAiRouteLayoutPolicyGateError("policy role drift")
    if row["selector_reason"] != selector_reason(row["profile_id"]):
        raise StwoAiRouteLayoutPolicyGateError("selector reason drift")
    for key in (
        "key_width",
        "head_count",
        "steps_per_head",
        "lookup_claims",
        "trace_rows",
        "fused_proof_size_bytes",
        "source_plus_sidecar_raw_proof_bytes",
        "fused_saves_vs_source_plus_sidecar_bytes",
        "opening_bucket_savings_bytes",
        "sidecar_opening_bucket_bytes",
        "query_bucket_savings_bytes",
        "source_opening_bucket_bytes",
        "fused_opening_bucket_bytes",
    ):
        if require_int(row[key], f"{row['profile_id']} {key}") <= 0:
            raise StwoAiRouteLayoutPolicyGateError(f"{row['profile_id']} {key} must be positive")
    require_int(
        row["fused_opening_minus_source_opening_bytes"],
        f"{row['profile_id']} fused_opening_minus_source_opening_bytes",
    )
    if row["opening_bucket_savings_bytes"] > row["fused_saves_vs_source_plus_sidecar_bytes"]:
        raise StwoAiRouteLayoutPolicyGateError("opening savings exceeds total savings")
    if row["opening_savings_share"] != ratio(
        row["opening_bucket_savings_bytes"],
        row["fused_saves_vs_source_plus_sidecar_bytes"],
    ):
        raise StwoAiRouteLayoutPolicyGateError("opening share drift")
    if row["sidecar_opening_absorption_share"] != ratio(
        row["opening_bucket_savings_bytes"],
        row["sidecar_opening_bucket_bytes"],
    ):
        raise StwoAiRouteLayoutPolicyGateError("sidecar absorption share drift")


def validate_selector(selector: Any, rows: list[dict[str, Any]]) -> None:
    if not isinstance(selector, dict):
        raise StwoAiRouteLayoutPolicyGateError("selector must be object")
    expected = {
        "headline_pressure_anchor_profile_id",
        "headline_pressure_anchor_savings_bytes",
        "headline_pressure_anchor_opening_savings_share",
        "fast_sequence_target_profile_id",
        "fast_sequence_target_fused_proof_size_bytes",
        "fast_sequence_target_savings_bytes",
        "fast_sequence_target_opening_savings_share",
        "fast_sequence_target_sidecar_absorption_share",
        "absorption_sanity_profile_id",
        "absorption_sanity_sidecar_absorption_share",
        "head_axis_fallback_profile_id",
        "head_axis_fallback_fused_opening_minus_source_opening_bytes",
        "policy_selector_rule",
        "next_action",
    }
    if set(selector) != expected:
        raise StwoAiRouteLayoutPolicyGateError("selector field drift")
    headline = find_row(rows, HEADLINE_PRESSURE_ANCHOR_PROFILE_ID)
    fast = find_row(rows, FAST_SEQUENCE_TARGET_PROFILE_ID)
    absorption = find_row(rows, ABSORPTION_SANITY_PROFILE_ID)
    fallback = find_row(rows, HEAD_AXIS_FALLBACK_PROFILE_ID)
    exact = {
        "headline_pressure_anchor_profile_id": HEADLINE_PRESSURE_ANCHOR_PROFILE_ID,
        "headline_pressure_anchor_savings_bytes": EXPECTED_HEADLINE_ANCHOR_SAVINGS_BYTES,
        "headline_pressure_anchor_opening_savings_share": headline["opening_savings_share"],
        "fast_sequence_target_profile_id": FAST_SEQUENCE_TARGET_PROFILE_ID,
        "fast_sequence_target_fused_proof_size_bytes": fast["fused_proof_size_bytes"],
        "fast_sequence_target_savings_bytes": EXPECTED_FAST_SEQUENCE_TARGET_SAVINGS_BYTES,
        "fast_sequence_target_opening_savings_share": EXPECTED_FAST_SEQUENCE_TARGET_OPENING_SHARE,
        "fast_sequence_target_sidecar_absorption_share": EXPECTED_FAST_SEQUENCE_TARGET_ABSORPTION_SHARE,
        "absorption_sanity_profile_id": ABSORPTION_SANITY_PROFILE_ID,
        "absorption_sanity_sidecar_absorption_share": absorption["sidecar_opening_absorption_share"],
        "head_axis_fallback_profile_id": HEAD_AXIS_FALLBACK_PROFILE_ID,
        "head_axis_fallback_fused_opening_minus_source_opening_bytes": fallback[
            "fused_opening_minus_source_opening_bytes"
        ],
        "next_action": "prototype_deterministic_route_layout_policy_on_d8_two_head_seq32_then_promote_to_d64_four_head_seq64",
    }
    for key, expected_value in exact.items():
        if selector[key] != expected_value:
            raise StwoAiRouteLayoutPolicyGateError(f"selector drift for {key}")
    if "post" in selector["policy_selector_rule"].lower():
        raise StwoAiRouteLayoutPolicyGateError("selector rule admits post-query selection")
    if "fixed before proof generation" not in selector["policy_selector_rule"]:
        raise StwoAiRouteLayoutPolicyGateError("selector rule lost fixed-policy requirement")
    fast_candidates = [
        row
        for row in rows
        if row["steps_per_head"] >= FAST_SEQUENCE_MIN_STEPS
        and row["lookup_claims"] >= FAST_SEQUENCE_MIN_LOOKUP_CLAIMS
        and row["fused_proof_size_bytes"] <= MAX_FAST_TARGET_FUSED_PROOF_BYTES
    ]
    selected = min(fast_candidates, key=lambda row: (row["fused_proof_size_bytes"], -row["opening_savings_share"]))
    if selector["fast_sequence_target_profile_id"] != selected["profile_id"]:
        raise StwoAiRouteLayoutPolicyGateError("fast sequence target selector drift")


def validate_aggregate(aggregate: Any, rows: list[dict[str, Any]]) -> None:
    if not isinstance(aggregate, dict):
        raise StwoAiRouteLayoutPolicyGateError("aggregate must be object")
    expected = {
        "profiles_checked",
        "total_fused_saves_vs_source_plus_sidecar_bytes",
        "total_opening_bucket_savings_bytes",
        "total_opening_savings_share",
        "largest_savings_profile_id",
        "largest_opening_savings_profile_id",
        "lowest_cost_sequence_profile_id",
    }
    if set(aggregate) != expected:
        raise StwoAiRouteLayoutPolicyGateError("aggregate field drift")
    if aggregate["profiles_checked"] != EXPECTED_PROFILE_COUNT:
        raise StwoAiRouteLayoutPolicyGateError("aggregate profile count drift")
    if aggregate["total_fused_saves_vs_source_plus_sidecar_bytes"] != EXPECTED_TOTAL_SAVINGS_BYTES:
        raise StwoAiRouteLayoutPolicyGateError("aggregate savings drift")
    if aggregate["total_opening_bucket_savings_bytes"] != EXPECTED_TOTAL_OPENING_SAVINGS_BYTES:
        raise StwoAiRouteLayoutPolicyGateError("aggregate opening savings drift")
    if aggregate["total_opening_savings_share"] != EXPECTED_TOTAL_OPENING_SAVINGS_SHARE:
        raise StwoAiRouteLayoutPolicyGateError("aggregate opening share drift")
    if aggregate["largest_savings_profile_id"] != HEADLINE_PRESSURE_ANCHOR_PROFILE_ID:
        raise StwoAiRouteLayoutPolicyGateError("aggregate largest savings profile drift")
    if aggregate["largest_opening_savings_profile_id"] != HEADLINE_PRESSURE_ANCHOR_PROFILE_ID:
        raise StwoAiRouteLayoutPolicyGateError("aggregate largest opening profile drift")
    expected_lowest_sequence = min(
        (row for row in rows if row["steps_per_head"] >= FAST_SEQUENCE_MIN_STEPS),
        key=lambda row: row["fused_proof_size_bytes"],
    )["profile_id"]
    if aggregate["lowest_cost_sequence_profile_id"] != expected_lowest_sequence:
        raise StwoAiRouteLayoutPolicyGateError("aggregate lowest sequence profile drift")


def validate_policy_plan(plan: Any, selector: dict[str, Any]) -> None:
    if not isinstance(plan, dict):
        raise StwoAiRouteLayoutPolicyGateError("policy plan must be object")
    expected = {
        "status",
        "fork_status",
        "immediate_target",
        "pressure_anchor",
        "promote_after_fast_target_go",
        "go_gate",
        "no_go_gate",
        "fork_trigger",
        "unsafe_actions_rejected",
    }
    if set(plan) != expected:
        raise StwoAiRouteLayoutPolicyGateError("policy plan field drift")
    exact = {
        "status": NEXT_POLICY_STATUS,
        "fork_status": FORK_STATUS,
        "immediate_target": selector["fast_sequence_target_profile_id"],
        "pressure_anchor": selector["headline_pressure_anchor_profile_id"],
        "promote_after_fast_target_go": selector["headline_pressure_anchor_profile_id"],
    }
    for key, expected_value in exact.items():
        if plan[key] != expected_value:
            raise StwoAiRouteLayoutPolicyGateError(f"policy plan drift for {key}")
    if "verifier-bound deterministic route-layout policy" not in plan["go_gate"]:
        raise StwoAiRouteLayoutPolicyGateError("GO gate lost verifier-bound deterministic policy")
    if "post-query selection" not in plan["no_go_gate"]:
        raise StwoAiRouteLayoutPolicyGateError("NO-GO gate lost post-query rejection")
    if "public-API wall" not in plan["fork_trigger"]:
        raise StwoAiRouteLayoutPolicyGateError("fork trigger drift")
    if not isinstance(plan["unsafe_actions_rejected"], list) or len(plan["unsafe_actions_rejected"]) != 5:
        raise StwoAiRouteLayoutPolicyGateError("unsafe action inventory drift")
    if "choosing labels after transcript queries are sampled" not in plan["unsafe_actions_rejected"]:
        raise StwoAiRouteLayoutPolicyGateError("unsafe post-query action not rejected")


def validate_payload(
    payload: Any,
    *,
    allow_missing_mutation_summary: bool = False,
    expected_rows: list[dict[str, Any]] | None = None,
) -> None:
    if not isinstance(payload, dict):
        raise StwoAiRouteLayoutPolicyGateError("payload must be object")
    expected = {
        "schema",
        "issue",
        "source_issue",
        "route_matrix_issue",
        "decision",
        "route_id",
        "claim_boundary",
        "fork_status",
        "next_policy_status",
        "prover_policy",
        "timing_policy",
        "security_policy",
        "backend_version_metadata",
        "source_artifacts",
        "profile_ids",
        "policy_metric_rows",
        "selector",
        "aggregate",
        "policy_plan",
        "non_claims",
        "validation_commands",
        "payload_commitment",
    }
    mutation_keys = {"mutation_cases", "mutations_checked", "mutations_rejected", "all_mutations_rejected"}
    if set(payload) - (expected | mutation_keys):
        raise StwoAiRouteLayoutPolicyGateError("payload field drift")
    if expected - set(payload):
        raise StwoAiRouteLayoutPolicyGateError("payload field drift")
    exact = {
        "schema": SCHEMA,
        "issue": ISSUE,
        "source_issue": SOURCE_ISSUE,
        "route_matrix_issue": ROUTE_MATRIX_ISSUE,
        "decision": DECISION,
        "route_id": ROUTE_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "fork_status": FORK_STATUS,
        "next_policy_status": NEXT_POLICY_STATUS,
        "prover_policy": PROVER_POLICY,
        "timing_policy": TIMING_POLICY,
        "security_policy": SECURITY_POLICY,
        "backend_version_metadata": BACKEND_VERSION_METADATA,
        "profile_ids": list(EXPECTED_PROFILE_IDS),
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    for key, expected_value in exact.items():
        if payload[key] != expected_value:
            raise StwoAiRouteLayoutPolicyGateError(f"{key} drift")
    artifacts = payload["source_artifacts"]
    expected_artifacts = {
        "section_delta_json": str(SECTION_DELTA_JSON.relative_to(ROOT)),
        "section_delta_sha256": SECTION_DELTA_SHA256,
        "route_matrix_json": str(ROUTE_MATRIX_JSON.relative_to(ROOT)),
        "route_matrix_sha256": ROUTE_MATRIX_SHA256,
    }
    if artifacts != expected_artifacts:
        raise StwoAiRouteLayoutPolicyGateError("source artifact digest drift")
    rows = payload["policy_metric_rows"]
    if not isinstance(rows, list) or len(rows) != EXPECTED_PROFILE_COUNT:
        raise StwoAiRouteLayoutPolicyGateError("policy metric row count drift")
    if [row.get("profile_id") if isinstance(row, dict) else None for row in rows] != list(EXPECTED_PROFILE_IDS):
        raise StwoAiRouteLayoutPolicyGateError("policy metric row order drift")
    for row in rows:
        validate_policy_metric_row(row)
    if expected_rows is None:
        section_payload, route_payload = load_source_artifacts()
        expected_rows = build_policy_metric_rows(section_payload, route_payload)
    if rows != expected_rows:
        raise StwoAiRouteLayoutPolicyGateError("policy metric row drift")
    expected_selector = build_selector(expected_rows)
    if payload["selector"] != expected_selector:
        raise StwoAiRouteLayoutPolicyGateError("selector drift")
    expected_aggregate = build_aggregate(expected_rows)
    if payload["aggregate"] != expected_aggregate:
        raise StwoAiRouteLayoutPolicyGateError("aggregate drift")
    expected_policy_plan = build_policy_plan(expected_selector)
    if payload["policy_plan"] != expected_policy_plan:
        raise StwoAiRouteLayoutPolicyGateError("policy plan drift")
    validate_selector(payload["selector"], expected_rows)
    validate_aggregate(payload["aggregate"], expected_rows)
    validate_policy_plan(payload["policy_plan"], payload["selector"])
    if payload_commitment(payload) != payload["payload_commitment"]:
        raise StwoAiRouteLayoutPolicyGateError("payload commitment drift")
    if not allow_missing_mutation_summary or any(key in payload for key in mutation_keys):
        if not mutation_keys <= set(payload):
            raise StwoAiRouteLayoutPolicyGateError("mutation summary missing")
        if payload["mutations_checked"] != EXPECTED_MUTATION_COUNT:
            raise StwoAiRouteLayoutPolicyGateError("mutation count drift")
        if payload["mutations_rejected"] != EXPECTED_MUTATION_COUNT:
            raise StwoAiRouteLayoutPolicyGateError("mutation rejection drift")
        if payload["all_mutations_rejected"] is not True:
            raise StwoAiRouteLayoutPolicyGateError("mutation flag drift")
        cases = payload["mutation_cases"]
        if not isinstance(cases, list) or len(cases) != EXPECTED_MUTATION_COUNT:
            raise StwoAiRouteLayoutPolicyGateError("mutation case count drift")
        if [case.get("name") if isinstance(case, dict) else None for case in cases] != list(EXPECTED_MUTATION_NAMES):
            raise StwoAiRouteLayoutPolicyGateError("mutation case name drift")
        for case in cases:
            if not isinstance(case, dict) or set(case) != {"name", "rejected", "error"}:
                raise StwoAiRouteLayoutPolicyGateError("mutation case field drift")
            if case["rejected"] is not True:
                raise StwoAiRouteLayoutPolicyGateError("mutation survived")
            require_str(case["error"], "mutation error")


def mutation_cases_for(payload: dict[str, Any]) -> list[dict[str, Any]]:
    base = copy.deepcopy(payload)
    for key in ("mutation_cases", "mutations_checked", "mutations_rejected", "all_mutations_rejected"):
        base.pop(key, None)
    mutations: list[tuple[str, Any]] = []

    def add(name: str, fn: Any) -> None:
        mutations.append((name, fn))

    add("decision_overclaim", lambda p: p.__setitem__("decision", "GO_NEW_PROOF_SIZE_FRONTIER"))
    add("fork_status_premature_promotion", lambda p: p.__setitem__("fork_status", "GO_FORK_STWO_NOW"))
    add("post_query_policy_smuggling", lambda p: p.__setitem__("security_policy", "choose_layout_after_query_draw"))
    add("source_artifact_digest_drift", lambda p: p["source_artifacts"].__setitem__("section_delta_sha256", "00" * 32))
    add("route_matrix_digest_drift", lambda p: p["source_artifacts"].__setitem__("route_matrix_sha256", "11" * 32))
    add("headline_anchor_relabeling", lambda p: p["selector"].__setitem__("headline_pressure_anchor_profile_id", "d8_two_head_seq32"))
    add("fast_sequence_target_relabeling", lambda p: p["selector"].__setitem__("fast_sequence_target_profile_id", "d64_four_head_seq64"))
    add(
        "fast_target_metric_smuggling",
        lambda p: find_row(p["policy_metric_rows"], FAST_SEQUENCE_TARGET_PROFILE_ID).__setitem__(
            "fused_saves_vs_source_plus_sidecar_bytes",
            1,
        ),
    )
    add(
        "d64_anchor_metric_smuggling",
        lambda p: find_row(p["policy_metric_rows"], HEADLINE_PRESSURE_ANCHOR_PROFILE_ID).__setitem__(
            "fused_saves_vs_source_plus_sidecar_bytes",
            1,
        ),
    )
    add(
        "opening_share_metric_smuggling",
        lambda p: find_row(p["policy_metric_rows"], FAST_SEQUENCE_TARGET_PROFILE_ID).__setitem__(
            "opening_savings_share",
            1.0,
        ),
    )
    add(
        "query_savings_overclaim",
        lambda p: find_row(p["policy_metric_rows"], HEADLINE_PRESSURE_ANCHOR_PROFILE_ID).__setitem__(
            "query_bucket_savings_bytes",
            9_999,
        ),
    )
    add("unsafe_action_removed", lambda p: p["policy_plan"]["unsafe_actions_rejected"].pop(0))
    add("non_claim_removed", lambda p: p["non_claims"].pop(0))
    add("payload_commitment_drift", lambda p: p.__setitem__("payload_commitment", "blake2b-256:" + "aa" * 32))
    add("unknown_field_injection", lambda p: p.__setitem__("unexpected", True))

    if [name for name, _fn in mutations] != list(EXPECTED_MUTATION_NAMES):
        raise StwoAiRouteLayoutPolicyGateError("mutation spec drift")
    cases = []
    for name, fn in mutations:
        candidate = copy.deepcopy(base)
        fn(candidate)
        try:
            validate_payload(candidate, allow_missing_mutation_summary=True)
        except StwoAiRouteLayoutPolicyGateError as err:
            cases.append({"name": name, "rejected": True, "error": str(err)})
        else:
            cases.append({"name": name, "rejected": False, "error": "mutation survived"})
    return cases


def build_payload() -> dict[str, Any]:
    payload = build_base_payload()
    cases = mutation_cases_for(payload)
    payload["mutation_cases"] = cases
    payload["mutations_checked"] = len(cases)
    payload["mutations_rejected"] = sum(1 for case in cases if case["rejected"])
    payload["all_mutations_rejected"] = payload["mutations_checked"] == payload["mutations_rejected"]
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload)
    return payload


def to_tsv(payload: dict[str, Any], *, validate: bool = True) -> str:
    if validate:
        validate_payload(payload)
    rows = []
    for row in payload["policy_metric_rows"]:
        rows.append({column: row[column] for column in TSV_COLUMNS})

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def to_markdown(payload: dict[str, Any]) -> str:
    validate_payload(payload)
    selector = payload["selector"]
    aggregate = payload["aggregate"]
    fast = find_row(payload["policy_metric_rows"], selector["fast_sequence_target_profile_id"])
    headline = find_row(payload["policy_metric_rows"], selector["headline_pressure_anchor_profile_id"])
    return "\n".join(
        [
            "# Stwo-AI Route-Layout Policy Selector",
            "",
            f"- Issue: `#{ISSUE}`",
            f"- Decision: `{DECISION}`",
            f"- Fork status: `{FORK_STATUS}`",
            f"- Prover policy: `{PROVER_POLICY}`",
            f"- Backend metadata: `{BACKEND_VERSION_METADATA['stwo_crate']}` / `{BACKEND_VERSION_METADATA['stwo_constraint_framework_crate']}` at evidence base commit `{BACKEND_VERSION_METADATA['evidence_base_commit']}`",
            f"- Version constants: `{BACKEND_VERSION_METADATA['fast_target_version_const']}`; `{BACKEND_VERSION_METADATA['pressure_anchor_version_const']}`",
            "",
            "## Result",
            "",
            "The next Stwo-AI step is not a fork. The checked section-delta evidence says the measured savings are still mostly opening material, so the fast path is a deterministic route-layout policy experiment.",
            "",
            f"- Checked profiles: `{aggregate['profiles_checked']}`",
            f"- Total fused saving: `{aggregate['total_fused_saves_vs_source_plus_sidecar_bytes']}` bytes",
            f"- Opening-related saving: `{aggregate['total_opening_bucket_savings_bytes']}` bytes (`{aggregate['total_opening_savings_share']:.6f}` share)",
            f"- Pressure anchor: `{headline['profile_id']}` saves `{headline['fused_saves_vs_source_plus_sidecar_bytes']}` bytes, with `{headline['opening_bucket_savings_bytes']}` opening-related bytes",
            f"- Fast first target: `{fast['profile_id']}` saves `{fast['fused_saves_vs_source_plus_sidecar_bytes']}` bytes, with `{fast['opening_savings_share']:.6f}` opening share and `{fast['sidecar_opening_absorption_share']:.6f}` sidecar-opening absorption",
            "",
            "## Next Experiment",
            "",
            "Prototype a verifier-bound deterministic route-layout policy on `d8_two_head_seq32`. If it reduces fused proof bytes without changing semantics or selecting after query draw, promote the same policy to `d64_four_head_seq64`.",
            "",
            "## Non-Claims",
            "",
            *[f"- {item}" for item in NON_CLAIMS],
            "",
            "## Reproduce",
            "",
            "```bash",
            *VALIDATION_COMMANDS,
            "```",
            "",
        ]
    )


def require_evidence_output_path(path: pathlib.Path) -> pathlib.Path:
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()
    if resolved.parent != EVIDENCE_DIR.resolve():
        raise StwoAiRouteLayoutPolicyGateError("evidence output path must be under docs/engineering/evidence")
    return resolved


def require_docs_output_path(path: pathlib.Path) -> pathlib.Path:
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()
    if resolved.parent != DOCS_DIR.resolve():
        raise StwoAiRouteLayoutPolicyGateError("markdown output path must be under docs/engineering")
    return resolved


def write_atomic(path: pathlib.Path, content: str, *, docs: bool = False) -> None:
    resolved = require_docs_output_path(path) if docs else require_evidence_output_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    temp_path: pathlib.Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=resolved.parent,
            prefix=f".{resolved.name}.",
            suffix=".tmp",
            delete=False,
        ) as tmp:
            tmp.write(content)
            temp_path = pathlib.Path(tmp.name)
        temp_path.replace(resolved)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path, tsv_path: pathlib.Path, md_path: pathlib.Path) -> None:
    validate_payload(payload)
    json_resolved = require_evidence_output_path(json_path)
    tsv_resolved = require_evidence_output_path(tsv_path)
    md_resolved = require_docs_output_path(md_path)
    write_atomic(json_resolved, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_atomic(tsv_resolved, to_tsv(payload, validate=False))
    write_atomic(md_resolved, to_markdown(payload), docs=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path, default=JSON_OUT)
    parser.add_argument("--write-tsv", type=pathlib.Path, default=TSV_OUT)
    parser.add_argument("--write-md", type=pathlib.Path, default=MD_OUT)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    payload = build_payload()
    if not args.no_write:
        write_outputs(payload, args.write_json, args.write_tsv, args.write_md)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
