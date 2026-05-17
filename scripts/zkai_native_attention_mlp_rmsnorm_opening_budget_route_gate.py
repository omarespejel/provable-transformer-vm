#!/usr/bin/env python3
"""Gate the RMSNorm-input opening-budget route after label-policy hardening."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import pathlib
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import zkai_native_attention_mlp_rmsnorm_label_policy_gate as policy_gate
from scripts import zkai_native_attention_mlp_rmsnorm_label_sensitivity_gate as sensitivity_gate


EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
LABEL_POLICY_PATH = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-label-policy-2026-05.json"
LABEL_SENSITIVITY_PATH = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-label-sensitivity-2026-05.json"
LABEL_POLICY_RELATIVE_PATH = LABEL_POLICY_PATH.relative_to(ROOT).as_posix()
LABEL_SENSITIVITY_RELATIVE_PATH = LABEL_SENSITIVITY_PATH.relative_to(ROOT).as_posix()
JSON_OUT = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-opening-budget-route-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-opening-budget-route-2026-05.tsv"

SCHEMA = "zkai-native-attention-mlp-rmsnorm-opening-budget-route-gate-v1"
DECISION = "CONDITIONAL_GO_OPENING_OVERHANG_ATTACK_WITH_STRICT_WORST_LABEL_TARGET"
RESULT = "WORST_LABEL_PATH_OPENING_OVERHANG_CAN_PAY_THE_1401_BYTE_POLICY_GAP_ONLY_IF_STRUCTURALLY_REMOVED"
ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/644"
CLAIM_BOUNDARY = (
    "RMSNORM_INPUT_OPENING_LAYOUT_REMAINS_AN_EXPLORATORY_ROUTE_ONLY_IF_A_FUTURE_VARIANT_REMOVES_"
    "AT_LEAST_1401_WORST_LABEL_TYPED_BYTES_WHILE_PRESERVING_SOURCE_BINDING_AND_VALUE_SEMANTICS"
)
PAYLOAD_DOMAIN = "ptvm:zkai:native-attention-mlp-rmsnorm-opening-budget-route:v1"

EXPECTED_LABEL_POLICY_SHA256 = "484bbddc65f7f4b34241b3ec3c5979d81ffbcef16a8ca6af88aee5c96da58642"
EXPECTED_LABEL_POLICY_COMMITMENT = "blake2b-256:ef71b343b14f57f07028247f3184a99bea46996c1d124c2cdb707b49c1304b1c"
EXPECTED_LABEL_SENSITIVITY_SHA256 = "03777754ecf0a99f1ef7371cc038be99bd4471aeac3861ddf9a225697cf29f30"
EXPECTED_LABEL_SENSITIVITY_COMMITMENT = "blake2b-256:ca919cd12acdfb5783a1c017d0b64bdba62adae082c8cf503af739076720df2a"

TWO_PROOF_FRONTIER_TYPED_BYTES = 40_700
COMPACT_SELECTOR_TYPED_BYTES = 40_812
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900
EXPECTED_WORST_LABEL_TYPED_BYTES = 42_100
EXPECTED_WORST_LABEL_PATH_OPENING_OVERHANG_BYTES = 1_680
EXPECTED_WORST_LABEL_REQUIRED_REDUCTION_BYTES = 1_401
EXPECTED_REQUIRED_SHARE_OF_OVERHANG = 0.833929
EXPECTED_FULL_REMOVAL_MODELED_TYPED_BYTES = 40_420
EXPECTED_FULL_REMOVAL_FRONTIER_MARGIN_BYTES = 280
EXPECTED_STRICT_MARGIN_BYTES = 279
EXPECTED_RMSNORM_VALUE_SAVING_VS_COMPACT_BYTES = 392
ISSUE_644_GO_GATE_SATISFIED = False
ISSUE_644_CLOSED_BY_THIS_GATE = False

ROUTE_CANDIDATE_ORDER = (
    "single_best_label",
    "canonical_overhang_only",
    "worst_label_path_opening_to_compact",
    "compact_selector_reference",
)
EXPECTED_ROUTE_CANDIDATE_METADATA = {
    "single_best_label": {
        "source_variant": "label_probe_a",
        "route_status": "REJECTED_CHERRY_PICK",
        "cherry_pick_risk": True,
        "policy_sufficient_if_full_path_opening_removed": False,
    },
    "canonical_overhang_only": {
        "source_variant": "rmsnorm_input_fused",
        "route_status": "NOT_SUFFICIENT_UNDER_WORST_LABEL_POLICY",
        "cherry_pick_risk": False,
        "policy_sufficient_if_full_path_opening_removed": False,
    },
    "worst_label_path_opening_to_compact": {
        "source_variant": "label_probe_b",
        "route_status": "CONDITIONAL_GO_IF_STRUCTURAL_OVERHANG_REMOVAL_EXISTS",
        "cherry_pick_risk": False,
        "policy_sufficient_if_full_path_opening_removed": True,
    },
    "compact_selector_reference": {
        "source_variant": "compact_selector",
        "route_status": "REFERENCE_NOT_RMSNORM_SEMANTIC_FUSION",
        "cherry_pick_risk": False,
        "policy_sufficient_if_full_path_opening_removed": False,
    },
}
ALLOWED_ROUTE_STATUSES = {item["route_status"] for item in EXPECTED_ROUTE_CANDIDATE_METADATA.values()}

HUMAN_READ = (
    "The strict policy gap is 1,401 typed bytes under the worst checked label. "
    "That worst label carries 1,680 typed bytes of path-opening overhang versus the compact selector, "
    "so the route is not dead: removing 83.3929% of that overhang would beat the 40,700 byte frontier. "
    "But this is only a target. No proof object currently removes that overhang."
)
NEXT_ATTACK = (
    "Build a real opening-layout variant and require it to remove at least 1,401 worst-label typed bytes "
    "from FRI/trace opening material while preserving the RMSNorm-input adapter equation, source binding, "
    "and the full label inventory. If it only wins under a favorable label, do not promote it."
)
INTERPRETATION = {
    "human_read": HUMAN_READ,
    "next_attack": NEXT_ATTACK,
}

NON_CLAIMS = (
    "not a two-proof frontier beat",
    "not a proof-size win",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not a new proof object",
    "not timing evidence",
    "not a full transformer block proof",
    "not production-ready zkML",
)

VALIDATION_COMMANDS = (
    "python3 scripts/zkai_native_attention_mlp_rmsnorm_opening_budget_route_gate.py --write-json "
    "docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-opening-budget-route-2026-05.json "
    "--write-tsv docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-opening-budget-route-2026-05.tsv",
    "python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_opening_budget_route_gate",
    "python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_label_policy_gate",
    "python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_label_sensitivity_gate",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

EXPECTED_MUTATION_NAMES = (
    "frontier_overclaim",
    "nanozk_overclaim",
    "nanozk_workload_match_overclaim",
    "source_policy_digest_drift",
    "source_sensitivity_commitment_drift",
    "issue_scope_overclaim",
    "worst_label_required_reduction_drift",
    "worst_label_path_overhang_drift",
    "required_share_drift",
    "canonical_policy_sufficient_overclaim",
    "full_removal_margin_drift",
    "single_label_allowed",
    "value_saving_erased",
    "route_candidate_removed",
    "route_status_drift",
    "route_source_variant_drift",
    "route_margin_drift",
    "decision_drift",
    "result_drift",
    "claim_boundary_drift",
    "non_claims_erased",
    "validation_commands_erased",
    "payload_commitment_drift",
)

TSV_COLUMNS = (
    "route_candidate",
    "source_variant",
    "baseline_typed_bytes",
    "required_reduction_to_beat_frontier_bytes",
    "path_opening_overhang_vs_compact_bytes",
    "required_share_of_path_opening_overhang",
    "modeled_typed_after_full_path_opening_removal",
    "modeled_frontier_margin_after_full_path_opening_removal_bytes",
    "cherry_pick_risk",
    "policy_sufficient_if_full_path_opening_removed",
)


class OpeningBudgetRouteError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode(
            "utf-8"
        )
    except (TypeError, ValueError) as err:
        raise OpeningBudgetRouteError(f"invalid JSON value: {err}") from err


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return "blake2b-256:" + digest.hexdigest()


def refresh_payload_commitment(payload: dict[str, Any]) -> None:
    payload["payload_commitment"] = payload_commitment(payload)


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise OpeningBudgetRouteError(f"{label} must be object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise OpeningBudgetRouteError(f"{label} must be list")
    return value


def _int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise OpeningBudgetRouteError(f"{label} must be integer")
    return value


def _float(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise OpeningBudgetRouteError(f"{label} must be number")
    return float(value)


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        details = []
        if missing:
            details.append(f"missing={missing}")
        if extra:
            details.append(f"extra={extra}")
        raise OpeningBudgetRouteError(f"{label} key drift: {', '.join(details)}")


def reduction_to_beat(value: int, threshold: int) -> int:
    return max(0, value - threshold + 1)


def read_source_payloads() -> tuple[dict[str, Any], bytes, dict[str, Any], bytes]:
    try:
        policy_payload, policy_raw = sensitivity_gate.read_json(LABEL_POLICY_PATH, "label policy")
        sensitivity_payload, sensitivity_raw = sensitivity_gate.read_json(
            LABEL_SENSITIVITY_PATH, "label sensitivity"
        )
        policy_gate.validate_payload(policy_payload)
        sensitivity_gate.validate_payload(sensitivity_payload)
    except (policy_gate.LabelPolicyError, sensitivity_gate.RmsnormLabelSensitivityError) as err:
        raise OpeningBudgetRouteError(f"source gate invalid: {err}") from err

    policy_sha = sha256_hex(policy_raw)
    sensitivity_sha = sha256_hex(sensitivity_raw)
    if policy_sha != EXPECTED_LABEL_POLICY_SHA256:
        raise OpeningBudgetRouteError("label policy source digest drift")
    if policy_payload.get("payload_commitment") != EXPECTED_LABEL_POLICY_COMMITMENT:
        raise OpeningBudgetRouteError("label policy payload commitment drift")
    if sensitivity_sha != EXPECTED_LABEL_SENSITIVITY_SHA256:
        raise OpeningBudgetRouteError("label sensitivity source digest drift")
    if sensitivity_payload.get("payload_commitment") != EXPECTED_LABEL_SENSITIVITY_COMMITMENT:
        raise OpeningBudgetRouteError("label sensitivity payload commitment drift")
    return policy_payload, policy_raw, sensitivity_payload, sensitivity_raw


def variant(sensitivity_payload: dict[str, Any], name: str) -> dict[str, Any]:
    variants = _dict(sensitivity_payload.get("variants"), "sensitivity variants")
    value = _dict(variants.get(name), f"variant {name}")
    if value.get("name") != name:
        raise OpeningBudgetRouteError(f"{name} name drift")
    return value


def route_candidate(
    *,
    name: str,
    source_variant: str,
    baseline_typed_bytes: int,
    path_opening_overhang_vs_compact_bytes: int,
    value_delta_vs_compact_bytes: int,
    required_reduction_to_beat_frontier_bytes: int,
    cherry_pick_risk: bool,
    policy_sufficient_if_full_path_opening_removed: bool,
    route_status: str,
) -> dict[str, Any]:
    modeled_typed = baseline_typed_bytes - path_opening_overhang_vs_compact_bytes
    required_share = (
        round(required_reduction_to_beat_frontier_bytes / path_opening_overhang_vs_compact_bytes, 6)
        if path_opening_overhang_vs_compact_bytes > 0
        else 0.0
    )
    return {
        "name": name,
        "source_variant": source_variant,
        "baseline_typed_bytes": baseline_typed_bytes,
        "baseline_delta_vs_two_proof_frontier_bytes": baseline_typed_bytes
        - TWO_PROOF_FRONTIER_TYPED_BYTES,
        "required_reduction_to_beat_frontier_bytes": required_reduction_to_beat_frontier_bytes,
        "path_opening_overhang_vs_compact_bytes": path_opening_overhang_vs_compact_bytes,
        "value_delta_vs_compact_bytes": value_delta_vs_compact_bytes,
        "required_share_of_path_opening_overhang": required_share,
        "modeled_typed_after_full_path_opening_removal": modeled_typed,
        "modeled_delta_vs_two_proof_frontier_after_full_path_opening_removal_bytes": modeled_typed
        - TWO_PROOF_FRONTIER_TYPED_BYTES,
        "modeled_frontier_margin_after_full_path_opening_removal_bytes": TWO_PROOF_FRONTIER_TYPED_BYTES
        - modeled_typed,
        "strict_margin_after_required_reduction_bytes": path_opening_overhang_vs_compact_bytes
        - required_reduction_to_beat_frontier_bytes,
        "cherry_pick_risk": cherry_pick_risk,
        "policy_sufficient_if_full_path_opening_removed": policy_sufficient_if_full_path_opening_removed,
        "promotion_allowed_now": False,
        "route_status": route_status,
    }


def build_payload(include_mutations: bool = True) -> dict[str, Any]:
    policy_payload, policy_raw, sensitivity_payload, sensitivity_raw = read_source_payloads()
    compact = variant(sensitivity_payload, "compact_selector")
    canonical = variant(sensitivity_payload, "rmsnorm_input_fused")
    best = variant(sensitivity_payload, "label_probe_a")
    worst = variant(sensitivity_payload, "label_probe_b")
    policy_summary = _dict(policy_payload.get("summary"), "policy summary")
    promotion_policy = _dict(policy_payload.get("promotion_policy"), "promotion policy")

    compact_path = _int(compact.get("path_opening_bytes"), "compact.path_opening")
    compact_value = _int(compact.get("value_bytes"), "compact.value")
    worst_required = _int(
        promotion_policy.get("required_reduction_to_beat_frontier_bytes"),
        "policy.required_reduction",
    )
    canonical_required = _int(
        policy_summary.get("canonical_label_reduction_to_beat_frontier_bytes"),
        "policy.canonical_reduction",
    )
    best_required = _int(
        policy_summary.get("single_best_label_reduction_to_beat_frontier_bytes"),
        "policy.best_reduction",
    )

    def path_overhang(item: dict[str, Any]) -> int:
        return _int(item.get("path_opening_bytes"), f"{item.get('name')}.path_opening") - compact_path

    def value_delta(item: dict[str, Any]) -> int:
        return _int(item.get("value_bytes"), f"{item.get('name')}.value") - compact_value

    canonical_overhang = path_overhang(canonical)
    best_overhang = path_overhang(best)
    worst_overhang = path_overhang(worst)
    worst_typed = _int(worst.get("typed_bytes"), "worst.typed")
    if worst_overhang <= 0:
        raise OpeningBudgetRouteError("worst label path-opening overhang must be positive")
    worst_required_share = round(worst_required / worst_overhang, 6)
    full_removal_typed = worst_typed - worst_overhang
    full_removal_frontier_margin = TWO_PROOF_FRONTIER_TYPED_BYTES - full_removal_typed
    strict_margin = worst_overhang - worst_required
    rmsnorm_value_saving = -value_delta(worst)

    if worst_typed != EXPECTED_WORST_LABEL_TYPED_BYTES:
        raise OpeningBudgetRouteError("worst label typed drift")
    if worst_required != EXPECTED_WORST_LABEL_REQUIRED_REDUCTION_BYTES:
        raise OpeningBudgetRouteError("worst label required reduction drift")
    if worst_overhang != EXPECTED_WORST_LABEL_PATH_OPENING_OVERHANG_BYTES:
        raise OpeningBudgetRouteError("worst label path-opening overhang drift")
    if worst_required_share != EXPECTED_REQUIRED_SHARE_OF_OVERHANG:
        raise OpeningBudgetRouteError("worst label required share drift")
    if full_removal_typed != EXPECTED_FULL_REMOVAL_MODELED_TYPED_BYTES:
        raise OpeningBudgetRouteError("full-removal modeled typed drift")
    if full_removal_frontier_margin != EXPECTED_FULL_REMOVAL_FRONTIER_MARGIN_BYTES:
        raise OpeningBudgetRouteError("full-removal frontier margin drift")
    if strict_margin != EXPECTED_STRICT_MARGIN_BYTES:
        raise OpeningBudgetRouteError("strict margin drift")
    if rmsnorm_value_saving != EXPECTED_RMSNORM_VALUE_SAVING_VS_COMPACT_BYTES:
        raise OpeningBudgetRouteError("RMSNorm value saving drift")

    candidates = {
        "single_best_label": route_candidate(
            name="single_best_label",
            source_variant="label_probe_a",
            baseline_typed_bytes=_int(best.get("typed_bytes"), "best.typed"),
            path_opening_overhang_vs_compact_bytes=best_overhang,
            value_delta_vs_compact_bytes=value_delta(best),
            required_reduction_to_beat_frontier_bytes=best_required,
            cherry_pick_risk=True,
            policy_sufficient_if_full_path_opening_removed=False,
            route_status="REJECTED_CHERRY_PICK",
        ),
        "canonical_overhang_only": route_candidate(
            name="canonical_overhang_only",
            source_variant="rmsnorm_input_fused",
            baseline_typed_bytes=_int(canonical.get("typed_bytes"), "canonical.typed"),
            path_opening_overhang_vs_compact_bytes=canonical_overhang,
            value_delta_vs_compact_bytes=value_delta(canonical),
            required_reduction_to_beat_frontier_bytes=canonical_required,
            cherry_pick_risk=False,
            policy_sufficient_if_full_path_opening_removed=False,
            route_status="NOT_SUFFICIENT_UNDER_WORST_LABEL_POLICY",
        ),
        "worst_label_path_opening_to_compact": route_candidate(
            name="worst_label_path_opening_to_compact",
            source_variant="label_probe_b",
            baseline_typed_bytes=worst_typed,
            path_opening_overhang_vs_compact_bytes=worst_overhang,
            value_delta_vs_compact_bytes=value_delta(worst),
            required_reduction_to_beat_frontier_bytes=worst_required,
            cherry_pick_risk=False,
            policy_sufficient_if_full_path_opening_removed=True,
            route_status="CONDITIONAL_GO_IF_STRUCTURAL_OVERHANG_REMOVAL_EXISTS",
        ),
        "compact_selector_reference": route_candidate(
            name="compact_selector_reference",
            source_variant="compact_selector",
            baseline_typed_bytes=_int(compact.get("typed_bytes"), "compact.typed"),
            path_opening_overhang_vs_compact_bytes=0,
            value_delta_vs_compact_bytes=0,
            required_reduction_to_beat_frontier_bytes=reduction_to_beat(
                _int(compact.get("typed_bytes"), "compact.typed"), TWO_PROOF_FRONTIER_TYPED_BYTES
            ),
            cherry_pick_risk=False,
            policy_sufficient_if_full_path_opening_removed=False,
            route_status="REFERENCE_NOT_RMSNORM_SEMANTIC_FUSION",
        ),
    }

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "claim_boundary": CLAIM_BOUNDARY,
        "issue_scope": {
            "tracked_issue": ISSUE,
            "closes_issue": ISSUE_644_CLOSED_BY_THIS_GATE,
            "satisfies_issue_go_gate": ISSUE_644_GO_GATE_SATISFIED,
            "required_next_artifact": (
                "regenerated RMSNorm-input opening-layout proof object with worst-label typed size "
                "strictly below the 40,700 typed-byte frontier"
            ),
        },
        "source_artifacts": [
            {
                "name": "label_policy_gate",
                "path": LABEL_POLICY_RELATIVE_PATH,
                "sha256": sha256_hex(policy_raw),
                "payload_commitment": policy_payload["payload_commitment"],
            },
            {
                "name": "label_sensitivity_gate",
                "path": LABEL_SENSITIVITY_RELATIVE_PATH,
                "sha256": sha256_hex(sensitivity_raw),
                "payload_commitment": sensitivity_payload["payload_commitment"],
            },
        ],
        "frontier": {
            "two_proof_frontier_typed_bytes": TWO_PROOF_FRONTIER_TYPED_BYTES,
            "compact_selector_typed_bytes": COMPACT_SELECTOR_TYPED_BYTES,
            "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
            "frontier_win_claimed": False,
            "nanozk_win_claimed": False,
            "nanozk_workload_matched": False,
        },
        "route_budget": {
            "worst_label_inventory": "label_probe_b",
            "worst_label_typed_bytes": worst_typed,
            "worst_label_delta_vs_frontier_bytes": worst_typed - TWO_PROOF_FRONTIER_TYPED_BYTES,
            "worst_label_required_reduction_to_beat_frontier_bytes": worst_required,
            "compact_selector_path_opening_bytes": compact_path,
            "worst_label_path_opening_bytes": _int(worst.get("path_opening_bytes"), "worst.path"),
            "worst_label_path_opening_overhang_vs_compact_bytes": worst_overhang,
            "required_share_of_path_opening_overhang": worst_required_share,
            "canonical_path_opening_overhang_vs_compact_bytes": canonical_overhang,
            "canonical_overhang_sufficient_under_worst_label_policy": canonical_overhang >= worst_required,
            "rmsnorm_value_saving_vs_compact_bytes": rmsnorm_value_saving,
            "modeled_typed_after_full_worst_label_path_opening_removal": full_removal_typed,
            "modeled_frontier_margin_after_full_worst_label_path_opening_removal_bytes": (
                full_removal_frontier_margin
            ),
            "strict_margin_after_required_reduction_bytes": strict_margin,
            "current_promotion_allowed": False,
        },
        "route_candidates": candidates,
        "summary": {
            "route_alive_if_structural_opening_removal_exists": True,
            "canonical_overhang_alone_is_policy_sufficient": False,
            "worst_label_path_opening_overhang_can_pay_policy_gap": True,
            "worst_label_required_reduction_to_beat_frontier_bytes": worst_required,
            "worst_label_path_opening_overhang_vs_compact_bytes": worst_overhang,
            "required_share_of_worst_label_path_opening_overhang": worst_required_share,
            "full_worst_label_path_opening_removal_modeled_typed_bytes": full_removal_typed,
            "full_worst_label_path_opening_removal_frontier_margin_bytes": full_removal_frontier_margin,
            "strict_margin_after_required_reduction_bytes": strict_margin,
            "rmsnorm_value_saving_vs_compact_bytes": rmsnorm_value_saving,
        },
        "interpretation": dict(INTERPRETATION),
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    refresh_payload_commitment(payload)
    if include_mutations:
        mutation_result = run_mutations(payload)
        validate_mutation_result(mutation_result)
        payload["mutation_result"] = mutation_result
        refresh_payload_commitment(payload)
    validate_payload(payload)
    return payload


def validate_mutation_result(mutation_result: dict[str, Any]) -> None:
    require_exact_keys(mutation_result, {"cases", "mutation_count", "rejected_count"}, "mutation result")
    cases = _list(mutation_result.get("cases"), "mutation cases")
    if _int(mutation_result.get("mutation_count"), "mutation count") != len(EXPECTED_MUTATION_NAMES):
        raise OpeningBudgetRouteError("mutation count drift")
    if _int(mutation_result.get("rejected_count"), "rejected count") != len(EXPECTED_MUTATION_NAMES):
        raise OpeningBudgetRouteError("mutation rejected count drift")
    names = []
    for index, case in enumerate(cases):
        item = _dict(case, f"mutation case {index}")
        require_exact_keys(item, {"name", "rejected"}, f"mutation case {index}")
        name = item.get("name")
        if not isinstance(name, str):
            raise OpeningBudgetRouteError("mutation case name drift")
        names.append(name)
        if item.get("rejected") is not True:
            raise OpeningBudgetRouteError(f"mutation not rejected: {name}")
    if tuple(names) != EXPECTED_MUTATION_NAMES:
        raise OpeningBudgetRouteError("mutation inventory drift")


def validate_route_candidate(candidate: dict[str, Any], expected_name: str) -> None:
    require_exact_keys(
        candidate,
        {
            "name",
            "source_variant",
            "baseline_typed_bytes",
            "baseline_delta_vs_two_proof_frontier_bytes",
            "required_reduction_to_beat_frontier_bytes",
            "path_opening_overhang_vs_compact_bytes",
            "value_delta_vs_compact_bytes",
            "required_share_of_path_opening_overhang",
            "modeled_typed_after_full_path_opening_removal",
            "modeled_delta_vs_two_proof_frontier_after_full_path_opening_removal_bytes",
            "modeled_frontier_margin_after_full_path_opening_removal_bytes",
            "strict_margin_after_required_reduction_bytes",
            "cherry_pick_risk",
            "policy_sufficient_if_full_path_opening_removed",
            "promotion_allowed_now",
            "route_status",
        },
        f"route candidate {expected_name}",
    )
    if candidate.get("name") != expected_name:
        raise OpeningBudgetRouteError(f"{expected_name} name drift")
    metadata = EXPECTED_ROUTE_CANDIDATE_METADATA[expected_name]
    if candidate.get("source_variant") != metadata["source_variant"]:
        raise OpeningBudgetRouteError(f"{expected_name} source variant drift")
    if candidate.get("route_status") not in ALLOWED_ROUTE_STATUSES:
        raise OpeningBudgetRouteError(f"{expected_name} route status not allowed")
    if candidate.get("route_status") != metadata["route_status"]:
        raise OpeningBudgetRouteError(f"{expected_name} route status drift")
    if candidate.get("cherry_pick_risk") is not metadata["cherry_pick_risk"]:
        raise OpeningBudgetRouteError(f"{expected_name} cherry-pick drift")
    if (
        candidate.get("policy_sufficient_if_full_path_opening_removed")
        is not metadata["policy_sufficient_if_full_path_opening_removed"]
    ):
        raise OpeningBudgetRouteError(f"{expected_name} policy sufficiency drift")
    baseline = _int(candidate.get("baseline_typed_bytes"), f"{expected_name}.baseline")
    baseline_delta = _int(
        candidate.get("baseline_delta_vs_two_proof_frontier_bytes"),
        f"{expected_name}.baseline_delta",
    )
    overhang = _int(
        candidate.get("path_opening_overhang_vs_compact_bytes"),
        f"{expected_name}.path_overhang",
    )
    value_delta = _int(candidate.get("value_delta_vs_compact_bytes"), f"{expected_name}.value_delta")
    required = _int(
        candidate.get("required_reduction_to_beat_frontier_bytes"),
        f"{expected_name}.required",
    )
    share = _float(
        candidate.get("required_share_of_path_opening_overhang"),
        f"{expected_name}.required_share",
    )
    modeled = _int(
        candidate.get("modeled_typed_after_full_path_opening_removal"),
        f"{expected_name}.modeled",
    )
    modeled_delta = _int(
        candidate.get("modeled_delta_vs_two_proof_frontier_after_full_path_opening_removal_bytes"),
        f"{expected_name}.modeled_delta",
    )
    modeled_margin = _int(
        candidate.get("modeled_frontier_margin_after_full_path_opening_removal_bytes"),
        f"{expected_name}.modeled_margin",
    )
    strict_margin = _int(
        candidate.get("strict_margin_after_required_reduction_bytes"),
        f"{expected_name}.strict_margin",
    )
    if baseline_delta != baseline - TWO_PROOF_FRONTIER_TYPED_BYTES:
        raise OpeningBudgetRouteError(f"{expected_name} baseline delta drift")
    if modeled != baseline - overhang:
        raise OpeningBudgetRouteError(f"{expected_name} modeled typed drift")
    if modeled_delta != modeled - TWO_PROOF_FRONTIER_TYPED_BYTES:
        raise OpeningBudgetRouteError(f"{expected_name} modeled delta drift")
    if modeled_margin != TWO_PROOF_FRONTIER_TYPED_BYTES - modeled:
        raise OpeningBudgetRouteError(f"{expected_name} modeled margin drift")
    if strict_margin != overhang - required:
        raise OpeningBudgetRouteError(f"{expected_name} strict margin drift")
    if not isinstance(value_delta, int):
        raise OpeningBudgetRouteError(f"{expected_name} value delta drift")
    expected_share = round(required / overhang, 6) if overhang > 0 else 0.0
    if share != expected_share:
        raise OpeningBudgetRouteError(f"{expected_name} required share drift")
    if candidate.get("promotion_allowed_now") is not False:
        raise OpeningBudgetRouteError(f"{expected_name} promotion overclaim")


def validate_payload(payload: dict[str, Any]) -> None:
    expected_top = {
        "schema",
        "decision",
        "result",
        "issue",
        "claim_boundary",
        "issue_scope",
        "source_artifacts",
        "frontier",
        "route_budget",
        "route_candidates",
        "summary",
        "interpretation",
        "non_claims",
        "validation_commands",
        "payload_commitment",
    }
    if "mutation_result" in payload:
        expected_top.add("mutation_result")
    require_exact_keys(payload, expected_top, "payload")
    if payload.get("schema") != SCHEMA:
        raise OpeningBudgetRouteError("schema drift")
    if payload.get("decision") != DECISION:
        raise OpeningBudgetRouteError("decision drift")
    if payload.get("result") != RESULT:
        raise OpeningBudgetRouteError("result drift")
    if payload.get("issue") != ISSUE:
        raise OpeningBudgetRouteError("issue drift")
    if payload.get("claim_boundary") != CLAIM_BOUNDARY:
        raise OpeningBudgetRouteError("claim boundary drift")

    issue_scope = _dict(payload.get("issue_scope"), "issue scope")
    expected_issue_scope = {
        "tracked_issue": ISSUE,
        "closes_issue": False,
        "satisfies_issue_go_gate": False,
        "required_next_artifact": (
            "regenerated RMSNorm-input opening-layout proof object with worst-label typed size "
            "strictly below the 40,700 typed-byte frontier"
        ),
    }
    if issue_scope != expected_issue_scope:
        raise OpeningBudgetRouteError("issue scope drift")
    if issue_scope.get("closes_issue") is not False:
        raise OpeningBudgetRouteError("issue close overclaim")
    if issue_scope.get("satisfies_issue_go_gate") is not False:
        raise OpeningBudgetRouteError("issue GO gate overclaim")

    expected_sources = [
        {
            "name": "label_policy_gate",
            "path": LABEL_POLICY_RELATIVE_PATH,
            "sha256": EXPECTED_LABEL_POLICY_SHA256,
            "payload_commitment": EXPECTED_LABEL_POLICY_COMMITMENT,
        },
        {
            "name": "label_sensitivity_gate",
            "path": LABEL_SENSITIVITY_RELATIVE_PATH,
            "sha256": EXPECTED_LABEL_SENSITIVITY_SHA256,
            "payload_commitment": EXPECTED_LABEL_SENSITIVITY_COMMITMENT,
        },
    ]
    if _list(payload.get("source_artifacts"), "source artifacts") != expected_sources:
        raise OpeningBudgetRouteError("source artifact drift")

    frontier = _dict(payload.get("frontier"), "frontier")
    expected_frontier = {
        "two_proof_frontier_typed_bytes": TWO_PROOF_FRONTIER_TYPED_BYTES,
        "compact_selector_typed_bytes": COMPACT_SELECTOR_TYPED_BYTES,
        "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
        "frontier_win_claimed": False,
        "nanozk_win_claimed": False,
        "nanozk_workload_matched": False,
    }
    if frontier.get("frontier_win_claimed") is not False:
        raise OpeningBudgetRouteError("frontier overclaim")
    if frontier.get("nanozk_win_claimed") is not False:
        raise OpeningBudgetRouteError("NANOZK overclaim")
    if frontier.get("nanozk_workload_matched") is not False:
        raise OpeningBudgetRouteError("NANOZK workload overclaim")
    if frontier != expected_frontier:
        raise OpeningBudgetRouteError("frontier body drift")

    budget = _dict(payload.get("route_budget"), "route budget")
    expected_budget = {
        "worst_label_inventory": "label_probe_b",
        "worst_label_typed_bytes": 42_100,
        "worst_label_delta_vs_frontier_bytes": 1_400,
        "worst_label_required_reduction_to_beat_frontier_bytes": 1_401,
        "compact_selector_path_opening_bytes": 19_504,
        "worst_label_path_opening_bytes": 21_184,
        "worst_label_path_opening_overhang_vs_compact_bytes": 1_680,
        "required_share_of_path_opening_overhang": 0.833929,
        "canonical_path_opening_overhang_vs_compact_bytes": 1_008,
        "canonical_overhang_sufficient_under_worst_label_policy": False,
        "rmsnorm_value_saving_vs_compact_bytes": 392,
        "modeled_typed_after_full_worst_label_path_opening_removal": 40_420,
        "modeled_frontier_margin_after_full_worst_label_path_opening_removal_bytes": 280,
        "strict_margin_after_required_reduction_bytes": 279,
        "current_promotion_allowed": False,
    }
    if budget != expected_budget:
        raise OpeningBudgetRouteError("route budget drift")
    if budget.get("canonical_overhang_sufficient_under_worst_label_policy") is not False:
        raise OpeningBudgetRouteError("canonical overhang policy overclaim")
    if budget.get("current_promotion_allowed") is not False:
        raise OpeningBudgetRouteError("current promotion overclaim")

    candidates = _dict(payload.get("route_candidates"), "route candidates")
    require_exact_keys(candidates, set(ROUTE_CANDIDATE_ORDER), "route candidates")
    for name in ROUTE_CANDIDATE_ORDER:
        validate_route_candidate(_dict(candidates.get(name), f"candidate {name}"), name)
    if candidates["single_best_label"].get("cherry_pick_risk") is not True:
        raise OpeningBudgetRouteError("single best label cherry-pick guard erased")
    if candidates["single_best_label"].get("policy_sufficient_if_full_path_opening_removed") is not False:
        raise OpeningBudgetRouteError("single best label allowed")
    if candidates["canonical_overhang_only"].get("policy_sufficient_if_full_path_opening_removed") is not False:
        raise OpeningBudgetRouteError("canonical policy overclaim")
    if candidates["worst_label_path_opening_to_compact"].get(
        "policy_sufficient_if_full_path_opening_removed"
    ) is not True:
        raise OpeningBudgetRouteError("worst-label conditional route erased")

    summary = _dict(payload.get("summary"), "summary")
    expected_summary = {
        "route_alive_if_structural_opening_removal_exists": True,
        "canonical_overhang_alone_is_policy_sufficient": False,
        "worst_label_path_opening_overhang_can_pay_policy_gap": True,
        "worst_label_required_reduction_to_beat_frontier_bytes": 1_401,
        "worst_label_path_opening_overhang_vs_compact_bytes": 1_680,
        "required_share_of_worst_label_path_opening_overhang": 0.833929,
        "full_worst_label_path_opening_removal_modeled_typed_bytes": 40_420,
        "full_worst_label_path_opening_removal_frontier_margin_bytes": 280,
        "strict_margin_after_required_reduction_bytes": 279,
        "rmsnorm_value_saving_vs_compact_bytes": 392,
    }
    if summary != expected_summary:
        raise OpeningBudgetRouteError("summary drift")
    if _dict(payload.get("interpretation"), "interpretation") != INTERPRETATION:
        raise OpeningBudgetRouteError("interpretation drift")
    if _list(payload.get("non_claims"), "non claims") != list(NON_CLAIMS):
        raise OpeningBudgetRouteError("non-claims drift")
    if _list(payload.get("validation_commands"), "validation commands") != list(VALIDATION_COMMANDS):
        raise OpeningBudgetRouteError("validation commands drift")
    if "mutation_result" in payload:
        validate_mutation_result(_dict(payload.get("mutation_result"), "mutation result"))
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise OpeningBudgetRouteError("payload commitment drift")


def run_mutations(payload: dict[str, Any]) -> dict[str, Any]:
    mutations = (
        ("frontier_overclaim", lambda p: p["frontier"].__setitem__("frontier_win_claimed", True)),
        ("nanozk_overclaim", lambda p: p["frontier"].__setitem__("nanozk_win_claimed", True)),
        (
            "nanozk_workload_match_overclaim",
            lambda p: p["frontier"].__setitem__("nanozk_workload_matched", True),
        ),
        ("source_policy_digest_drift", lambda p: p["source_artifacts"][0].__setitem__("sha256", "00" * 32)),
        (
            "source_sensitivity_commitment_drift",
            lambda p: p["source_artifacts"][1].__setitem__("payload_commitment", "blake2b-256:" + "00" * 32),
        ),
        ("issue_scope_overclaim", lambda p: p["issue_scope"].__setitem__("satisfies_issue_go_gate", True)),
        (
            "worst_label_required_reduction_drift",
            lambda p: p["route_budget"].__setitem__("worst_label_required_reduction_to_beat_frontier_bytes", 137),
        ),
        (
            "worst_label_path_overhang_drift",
            lambda p: p["route_budget"].__setitem__("worst_label_path_opening_overhang_vs_compact_bytes", 1_008),
        ),
        (
            "required_share_drift",
            lambda p: p["route_budget"].__setitem__("required_share_of_path_opening_overhang", 0.723214),
        ),
        (
            "canonical_policy_sufficient_overclaim",
            lambda p: p["route_budget"].__setitem__(
                "canonical_overhang_sufficient_under_worst_label_policy", True
            ),
        ),
        (
            "full_removal_margin_drift",
            lambda p: p["summary"].__setitem__(
                "full_worst_label_path_opening_removal_frontier_margin_bytes", 0
            ),
        ),
        (
            "single_label_allowed",
            lambda p: p["route_candidates"]["single_best_label"].__setitem__(
                "policy_sufficient_if_full_path_opening_removed", True
            ),
        ),
        ("value_saving_erased", lambda p: p["summary"].__setitem__("rmsnorm_value_saving_vs_compact_bytes", 0)),
        ("route_candidate_removed", lambda p: p["route_candidates"].pop("worst_label_path_opening_to_compact")),
        (
            "route_status_drift",
            lambda p: p["route_candidates"]["worst_label_path_opening_to_compact"].__setitem__(
                "route_status", "UNREVIEWED_STATUS"
            ),
        ),
        (
            "route_source_variant_drift",
            lambda p: p["route_candidates"]["worst_label_path_opening_to_compact"].__setitem__(
                "source_variant", "label_probe_a"
            ),
        ),
        (
            "route_margin_drift",
            lambda p: p["route_candidates"]["worst_label_path_opening_to_compact"].__setitem__(
                "modeled_frontier_margin_after_full_path_opening_removal_bytes", 0
            ),
        ),
        ("decision_drift", lambda p: p.__setitem__("decision", "GO_FRONTIER_PROMOTION")),
        ("result_drift", lambda p: p.__setitem__("result", "PROOF_SIZE_WIN")),
        ("claim_boundary_drift", lambda p: p.__setitem__("claim_boundary", "OVERCLAIMED")),
        ("non_claims_erased", lambda p: p.__setitem__("non_claims", [])),
        ("validation_commands_erased", lambda p: p.__setitem__("validation_commands", [])),
        ("payload_commitment_drift", lambda p: p.__setitem__("payload_commitment", "blake2b-256:" + "00" * 32)),
    )
    if tuple(name for name, _ in mutations) != EXPECTED_MUTATION_NAMES:
        raise OpeningBudgetRouteError("mutation definitions drift")
    cases = []
    for name, mutate in mutations:
        mutated = copy.deepcopy(payload)
        mutated.pop("mutation_result", None)
        mutate(mutated)
        if name != "payload_commitment_drift":
            refresh_payload_commitment(mutated)
        rejected = False
        try:
            validate_payload(mutated)
        except OpeningBudgetRouteError:
            rejected = True
        cases.append({"name": name, "rejected": rejected})
    return {
        "mutation_count": len(cases),
        "rejected_count": sum(1 for case in cases if case["rejected"]),
        "cases": cases,
    }


def tsv_text(payload: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for name in ROUTE_CANDIDATE_ORDER:
        candidate = payload["route_candidates"][name]
        writer.writerow(
            {
                "route_candidate": name,
                "source_variant": candidate["source_variant"],
                "baseline_typed_bytes": candidate["baseline_typed_bytes"],
                "required_reduction_to_beat_frontier_bytes": candidate[
                    "required_reduction_to_beat_frontier_bytes"
                ],
                "path_opening_overhang_vs_compact_bytes": candidate[
                    "path_opening_overhang_vs_compact_bytes"
                ],
                "required_share_of_path_opening_overhang": candidate[
                    "required_share_of_path_opening_overhang"
                ],
                "modeled_typed_after_full_path_opening_removal": candidate[
                    "modeled_typed_after_full_path_opening_removal"
                ],
                "modeled_frontier_margin_after_full_path_opening_removal_bytes": candidate[
                    "modeled_frontier_margin_after_full_path_opening_removal_bytes"
                ],
                "cherry_pick_risk": str(candidate["cherry_pick_risk"]).lower(),
                "policy_sufficient_if_full_path_opening_removed": str(
                    candidate["policy_sufficient_if_full_path_opening_removed"]
                ).lower(),
            }
        )
    return output.getvalue()


def normalize_output_path(path: pathlib.Path) -> pathlib.Path:
    try:
        return policy_gate.normalize_output_path(path)
    except policy_gate.LabelPolicyError as err:
        raise OpeningBudgetRouteError(f"failed to normalize output path: {err}") from err


def require_output_suffix(target: pathlib.Path, suffix: str) -> None:
    if target.suffix != suffix:
        raise OpeningBudgetRouteError(f"output path must have {suffix} suffix: {target}")


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path | None, tsv_path: pathlib.Path | None) -> None:
    validate_payload(payload)
    json_target = normalize_output_path(json_path) if json_path is not None else None
    tsv_target = normalize_output_path(tsv_path) if tsv_path is not None else None
    if json_target is not None and tsv_target is not None and json_target.resolve() == tsv_target.resolve():
        raise OpeningBudgetRouteError(f"duplicate output destination: {json_target}")
    if json_target is not None:
        require_output_suffix(json_target, ".json")
    if tsv_target is not None:
        require_output_suffix(tsv_target, ".tsv")
    json_body = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    tsv_body = tsv_text(payload)
    try:
        if json_target is not None and tsv_target is not None:
            policy_gate.write_output_pair_atomically(json_target, json_body, tsv_target, tsv_body)
            return
        if json_target is not None:
            sensitivity_gate.write_text_atomically(json_target, json_body)
        if tsv_target is not None:
            sensitivity_gate.write_text_atomically(tsv_target, tsv_body)
    except (policy_gate.LabelPolicyError, sensitivity_gate.RmsnormLabelSensitivityError) as err:
        raise OpeningBudgetRouteError(f"failed to write output: {err}") from err


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
                "worst_label_required_reduction_to_beat_frontier_bytes": payload["summary"][
                    "worst_label_required_reduction_to_beat_frontier_bytes"
                ],
                "worst_label_path_opening_overhang_vs_compact_bytes": payload["summary"][
                    "worst_label_path_opening_overhang_vs_compact_bytes"
                ],
                "required_share_of_worst_label_path_opening_overhang": payload["summary"][
                    "required_share_of_worst_label_path_opening_overhang"
                ],
                "full_removal_frontier_margin_bytes": payload["summary"][
                    "full_worst_label_path_opening_removal_frontier_margin_bytes"
                ],
                "mutation_count": payload["mutation_result"]["mutation_count"],
                "mutations_rejected": payload["mutation_result"]["rejected_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
