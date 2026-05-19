#!/usr/bin/env python3.10
"""Gate the deterministic adjacent-label policy for the seq32 attention+MLP proof."""

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


if sys.version_info < (3, 10):
    raise RuntimeError("zkai_native_seq32_attention_mlp_deterministic_adjacent_label_policy_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import zkai_native_seq32_attention_mlp_adjacent_label_policy_gate as source_gate


EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
SOURCE_POLICY_PATH = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-policy-2026-05.json"
SOURCE_POLICY_RELATIVE_PATH = SOURCE_POLICY_PATH.relative_to(ROOT).as_posix()
JSON_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-deterministic-adjacent-label-policy-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-deterministic-adjacent-label-policy-2026-05.tsv"

SCHEMA = "zkai-native-seq32-attention-mlp-deterministic-adjacent-label-policy-gate-v1"
DECISION = "GO_SUPPORTED_ADJACENT_LABEL_POLICY_BEATS_CURRENT_CHAMPION"
RESULT = "WORST_SUPPORTED_ADJACENT_LABEL_SAVES_1736_TYPED_BYTES_VS_42068_CHAMPION"
CLAIM_BOUNDARY = (
    "DETERMINISTIC_POLICY_OVER_EXISTING_SEQ32_ADJACENT_LABEL_INVENTORY;"
    "REJECTS_FIXED_LABEL_PATH_OPENING_INFLATION;NOT_A_FINAL_LABEL_GENERATOR_NOT_A_NANOZK_WIN"
)
ISSUE_HINT = "seq32-deterministic-adjacent-label-policy"
PAYLOAD_DOMAIN = "ptvm:zkai:native-seq32-attention-mlp-deterministic-adjacent-label-policy:v1"

EXPECTED_SOURCE_POLICY_SHA256 = "b85b9001dc0e9387b4cc2fc49302c9d7bbe7e9ff8d8f6c9b31c394a21b14b9d1"
EXPECTED_SOURCE_POLICY_COMMITMENT = "blake2b-256:f2bcfec2552cc89befcb489271b357063cf13ea302fb91732cb416249ea427a2"

CURRENT_CHAMPION_ID = "current_duplicate_base"
FIXED_ADJACENT_ID = "fixed_adjacent_layout"
SUPPORTED_LABEL_IDS = ("adjacent_label_probe_a", "adjacent_label_probe_b")
ADJACENT_LABEL_INVENTORY = (FIXED_ADJACENT_ID, *SUPPORTED_LABEL_IDS)
CURRENT_CHAMPION_TYPED_BYTES = 42_068
CURRENT_CHAMPION_JSON_BYTES = 121_996
CURRENT_CHAMPION_PATH_OPENING_BYTES = 20_592
CURRENT_CHAMPION_VALUE_BYTES = 21_428
ADJACENT_VALUE_BYTES = 20_924
WORST_SUPPORTED_LABEL_ID = "adjacent_label_probe_a"
WORST_SUPPORTED_TYPED_BYTES = 40_332
WORST_SUPPORTED_SAVING_BYTES = 1_736
BEST_SUPPORTED_LABEL_ID = "adjacent_label_probe_b"
BEST_SUPPORTED_TYPED_BYTES = 37_532
BEST_SUPPORTED_SAVING_BYTES = 4_536
FULL_INVENTORY_WORST_LABEL_ID = FIXED_ADJACENT_ID
FULL_INVENTORY_WORST_TYPED_BYTES = 42_156
FULL_INVENTORY_MISS_BYTES = 88
FIXED_PATH_OPENING_OVERHANG_BYTES = 592
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900

EXPECTED_INTERPRETATION = {
    "human_read": (
        "The full adjacent label inventory is not promotable because the fixed adjacent label is "
        "88 typed bytes above the current champion. The deterministic supported-label policy rejects "
        "that path-opening-inflating label and keeps the two checked labels whose worst case saves "
        "1,736 typed bytes."
    ),
    "mechanism_read": (
        "The policy is not changing arithmetic. Direct value bytes stay fixed at 20,924; the policy "
        "only rejects labels whose path-opening material grows beyond the current champion."
    ),
    "next_experiment": (
        "Turn this policy into a generator-backed label inventory, then test whether unseen labels "
        "still keep the worst supported proof below 42,068 typed bytes."
    ),
}

NON_CLAIMS = (
    "not a final production label-selection policy",
    "not a generator-backed label inventory",
    "not robust to unseen labels",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not a full transformer block proof",
    "not exact real-valued Softmax",
    "not timing evidence",
    "not production-ready zkML",
)

VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_native_seq32_attention_mlp_deterministic_adjacent_label_policy_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-deterministic-adjacent-label-policy-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-deterministic-adjacent-label-policy-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_deterministic_adjacent_label_policy_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_deterministic_adjacent_label_policy_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_deterministic_adjacent_label_policy_gate",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_adjacent_label_policy_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_adjacent_label --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

MUTATION_NAMES = (
    "decision_drift",
    "result_drift",
    "full_inventory_overclaim",
    "fixed_label_supported",
    "probe_a_rejected",
    "worst_supported_typed_drift",
    "worst_supported_saving_erased",
    "support_criteria_erased",
    "value_stability_erased",
    "source_digest_drift",
    "source_commitment_drift",
    "validation_command_drift",
    "removed_non_claim",
    "nanozk_overclaim",
    "final_policy_overclaim",
    "unknown_policy_field",
    "label_inventory_order_drift",
    "label_adapter_mode_drift",
    "label_proof_json_drift",
    "label_status_reason_drift",
    "champion_value_drift",
    "payload_commitment_drift",
)
EXPECTED_MUTATION_ERRORS = {
    "decision_drift": "decision drift",
    "result_drift": "result drift",
    "full_inventory_overclaim": "full inventory overclaim",
    "fixed_label_supported": "label inventory drift",
    "probe_a_rejected": "label inventory drift",
    "worst_supported_typed_drift": "deterministic policy drift",
    "worst_supported_saving_erased": "policy summary drift",
    "support_criteria_erased": "deterministic policy drift",
    "value_stability_erased": "policy summary drift",
    "source_digest_drift": "source artifact drift",
    "source_commitment_drift": "source artifact drift",
    "validation_command_drift": "validation command drift",
    "removed_non_claim": "non_claims drift",
    "nanozk_overclaim": "claim_boundary drift",
    "final_policy_overclaim": "non_claims drift",
    "unknown_policy_field": "deterministic policy field drift: unexpected unchecked",
    "label_inventory_order_drift": "label inventory order drift",
    "label_adapter_mode_drift": "label inventory drift",
    "label_proof_json_drift": "label inventory drift",
    "label_status_reason_drift": "label inventory drift",
    "champion_value_drift": "label inventory drift",
    "payload_commitment_drift": "payload commitment drift",
}

TSV_COLUMNS = (
    "variant_id",
    "policy_status",
    "typed_bytes",
    "typed_delta_vs_champion",
    "path_opening_bytes",
    "path_opening_delta_vs_champion",
    "value_bytes",
    "status_reason",
)

PAYLOAD_KEYS = {
    "schema",
    "decision",
    "result",
    "claim_boundary",
    "issue_hint",
    "source_artifacts",
    "full_inventory_policy",
    "deterministic_policy",
    "label_inventory",
    "policy_summary",
    "interpretation",
    "non_claims",
    "validation_commands",
    "mutation_result",
    "payload_commitment",
}
SOURCE_ARTIFACT_KEYS = {"id", "path", "sha256", "payload_commitment"}
FULL_POLICY_KEYS = {
    "name",
    "full_inventory_label_ids",
    "worst_full_inventory_label_id",
    "worst_full_inventory_typed_bytes",
    "delta_vs_current_champion_typed_bytes",
    "full_inventory_promotable_vs_current_champion",
    "reason",
}
DETERMINISTIC_POLICY_KEYS = {
    "name",
    "support_criteria",
    "rejection_criteria",
    "supported_label_ids",
    "rejected_label_ids",
    "worst_supported_label_id",
    "worst_supported_typed_bytes",
    "worst_supported_saving_typed_bytes",
    "worst_supported_saving_share",
    "best_supported_label_id",
    "best_supported_typed_bytes",
    "best_supported_saving_typed_bytes",
    "supported_label_count",
    "rejected_label_count",
    "supported_labels_promotable_vs_current_champion",
}
LABEL_ROW_KEYS = {
    "variant_id",
    "adapter_mode",
    "typed_bytes",
    "proof_json_bytes",
    "path_opening_bytes",
    "value_bytes",
    "typed_delta_vs_champion",
    "path_opening_delta_vs_champion",
    "policy_status",
    "status_reason",
}
SUMMARY_KEYS = {
    "current_champion_typed_bytes",
    "current_champion_json_bytes",
    "current_champion_path_opening_bytes",
    "fixed_adjacent_path_opening_overhang_vs_champion",
    "adjacent_value_bytes",
    "full_inventory_worst_label_id",
    "full_inventory_worst_typed_bytes",
    "full_inventory_miss_vs_champion_typed_bytes",
    "supported_label_count",
    "rejected_label_count",
    "worst_supported_label_id",
    "worst_supported_typed_bytes",
    "worst_supported_saving_typed_bytes",
    "worst_supported_saving_share",
    "best_supported_label_id",
    "best_supported_typed_bytes",
    "best_supported_saving_typed_bytes",
    "supported_value_bytes_stable",
    "proof_size_comparable_external_rows",
    "nanozk_reported_d128_block_proof_bytes",
}
MUTATION_RESULT_KEYS = {"all_mutations_rejected", "mutations_rejected", "mutation_names", "cases"}
MUTATION_CASE_KEYS = {"name", "rejected", "error"}


class DeterministicAdjacentLabelPolicyGateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as err:
        raise DeterministicAdjacentLabelPolicyGateError(f"invalid JSON value: {err}") from err


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return "blake2b-256:" + digest.hexdigest()


def _dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DeterministicAdjacentLabelPolicyGateError(f"{label} must be object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise DeterministicAdjacentLabelPolicyGateError(f"{label} must be list")
    return value


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual == expected:
        return
    unexpected = sorted(actual - expected)
    missing = sorted(expected - actual)
    if unexpected:
        raise DeterministicAdjacentLabelPolicyGateError(f"{label} field drift: unexpected {unexpected[0]}")
    raise DeterministicAdjacentLabelPolicyGateError(f"{label} field drift: missing {missing[0]}")


def load_source_policy() -> tuple[dict[str, Any], bytes]:
    try:
        source, raw = source_gate.load_json_file(SOURCE_POLICY_PATH, "source adjacent label policy")
        source_gate.validate_payload(source)
    except source_gate.AdjacentLabelPolicyGateError as err:
        raise DeterministicAdjacentLabelPolicyGateError(f"source adjacent label policy invalid: {err}") from err
    source_sha = source_gate.sha256(raw)
    if source_sha != EXPECTED_SOURCE_POLICY_SHA256:
        raise DeterministicAdjacentLabelPolicyGateError("source policy digest drift")
    if source.get("payload_commitment") != EXPECTED_SOURCE_POLICY_COMMITMENT:
        raise DeterministicAdjacentLabelPolicyGateError("source policy commitment drift")
    return source, raw


def source_variants_by_id(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    variants = {}
    for item in _list(source.get("variants"), "source variants"):
        row = _dict(item, "source variant")
        variant_id = row.get("variant_id")
        if not isinstance(variant_id, str):
            raise DeterministicAdjacentLabelPolicyGateError("source variant id drift")
        variants[variant_id] = row
    for required in (CURRENT_CHAMPION_ID, *ADJACENT_LABEL_INVENTORY):
        if required not in variants:
            raise DeterministicAdjacentLabelPolicyGateError(f"missing source variant: {required}")
    return variants


def classify_label(row: dict[str, Any], champion: dict[str, Any]) -> tuple[str, str]:
    variant_id = row["variant_id"]
    if variant_id == CURRENT_CHAMPION_ID:
        return "comparison_champion", "baseline for typed/path-opening deltas"
    if row["value_bytes"] != ADJACENT_VALUE_BYTES:
        return "rejected_value_drift", "direct value bytes differ from adjacent policy value bytes"
    if row["path_opening_bytes"] >= champion["path_opening_bytes"]:
        return "rejected_inflating_label", "path-opening bytes are not below the current champion"
    if row["typed_bytes"] >= champion["typed_bytes"]:
        return "rejected_inflating_label", "typed proof bytes are not below the current champion"
    return "supported_label", "value bytes stable and path-opening/typed bytes beat the current champion"


def build_label_inventory(source: dict[str, Any]) -> list[dict[str, Any]]:
    variants = source_variants_by_id(source)
    champion = variants[CURRENT_CHAMPION_ID]
    rows = []
    for variant_id in (CURRENT_CHAMPION_ID, *ADJACENT_LABEL_INVENTORY):
        source_row = variants[variant_id]
        policy_status, status_reason = classify_label(source_row, champion)
        rows.append(
            {
                "variant_id": variant_id,
                "adapter_mode": source_row["adapter_mode"],
                "typed_bytes": source_row["typed_bytes"],
                "proof_json_bytes": source_row["proof_json_bytes"],
                "path_opening_bytes": source_row["path_opening_bytes"],
                "value_bytes": source_row["value_bytes"],
                "typed_delta_vs_champion": source_row["typed_bytes"] - champion["typed_bytes"],
                "path_opening_delta_vs_champion": source_row["path_opening_bytes"] - champion["path_opening_bytes"],
                "policy_status": policy_status,
                "status_reason": status_reason,
            }
        )
    return rows


def build_payload() -> dict[str, Any]:
    source, raw = load_source_policy()
    inventory = build_label_inventory(source)
    by_id = {row["variant_id"]: row for row in inventory}
    champion = by_id[CURRENT_CHAMPION_ID]
    adjacent_rows = [by_id[variant_id] for variant_id in ADJACENT_LABEL_INVENTORY]
    supported = [row for row in adjacent_rows if row["policy_status"] == "supported_label"]
    rejected = [row for row in adjacent_rows if row["policy_status"].startswith("rejected")]
    if tuple(row["variant_id"] for row in supported) != SUPPORTED_LABEL_IDS:
        raise DeterministicAdjacentLabelPolicyGateError("supported label inventory drift")
    if tuple(row["variant_id"] for row in rejected) != (FIXED_ADJACENT_ID,):
        raise DeterministicAdjacentLabelPolicyGateError("rejected label inventory drift")
    worst_supported = max(supported, key=lambda row: row["typed_bytes"])
    best_supported = min(supported, key=lambda row: row["typed_bytes"])
    worst_full_inventory = max(adjacent_rows, key=lambda row: row["typed_bytes"])
    full_inventory_policy = {
        "name": "full_adjacent_inventory_worst_label_v1",
        "full_inventory_label_ids": list(ADJACENT_LABEL_INVENTORY),
        "worst_full_inventory_label_id": worst_full_inventory["variant_id"],
        "worst_full_inventory_typed_bytes": worst_full_inventory["typed_bytes"],
        "delta_vs_current_champion_typed_bytes": worst_full_inventory["typed_bytes"] - champion["typed_bytes"],
        "full_inventory_promotable_vs_current_champion": False,
        "reason": "the fixed adjacent label inflates path-opening material and misses the champion by 88 typed bytes",
    }
    deterministic_policy = {
        "name": "reject_path_opening_inflation_v1",
        "support_criteria": [
            "adapter_mode is an adjacent label probe",
            "direct value bytes equal 20924",
            "path_opening_bytes are below the current champion",
            "typed_bytes are below the current champion",
            "source envelope and accounting are pinned by digest and payload commitment",
        ],
        "rejection_criteria": [
            "path_opening_bytes are greater than or equal to the current champion",
            "typed_bytes are greater than or equal to the current champion",
            "direct value bytes drift from the adjacent label inventory",
        ],
        "supported_label_ids": [row["variant_id"] for row in supported],
        "rejected_label_ids": [row["variant_id"] for row in rejected],
        "worst_supported_label_id": worst_supported["variant_id"],
        "worst_supported_typed_bytes": worst_supported["typed_bytes"],
        "worst_supported_saving_typed_bytes": champion["typed_bytes"] - worst_supported["typed_bytes"],
        "worst_supported_saving_share": f"{(champion['typed_bytes'] - worst_supported['typed_bytes']) / champion['typed_bytes']:.6f}",
        "best_supported_label_id": best_supported["variant_id"],
        "best_supported_typed_bytes": best_supported["typed_bytes"],
        "best_supported_saving_typed_bytes": champion["typed_bytes"] - best_supported["typed_bytes"],
        "supported_label_count": len(supported),
        "rejected_label_count": len(rejected),
        "supported_labels_promotable_vs_current_champion": True,
    }
    policy_summary = {
        "current_champion_typed_bytes": champion["typed_bytes"],
        "current_champion_json_bytes": champion["proof_json_bytes"],
        "current_champion_path_opening_bytes": champion["path_opening_bytes"],
        "fixed_adjacent_path_opening_overhang_vs_champion": by_id[FIXED_ADJACENT_ID]["path_opening_bytes"] - champion["path_opening_bytes"],
        "adjacent_value_bytes": ADJACENT_VALUE_BYTES,
        "full_inventory_worst_label_id": worst_full_inventory["variant_id"],
        "full_inventory_worst_typed_bytes": worst_full_inventory["typed_bytes"],
        "full_inventory_miss_vs_champion_typed_bytes": worst_full_inventory["typed_bytes"] - champion["typed_bytes"],
        "supported_label_count": len(supported),
        "rejected_label_count": len(rejected),
        "worst_supported_label_id": worst_supported["variant_id"],
        "worst_supported_typed_bytes": worst_supported["typed_bytes"],
        "worst_supported_saving_typed_bytes": champion["typed_bytes"] - worst_supported["typed_bytes"],
        "worst_supported_saving_share": deterministic_policy["worst_supported_saving_share"],
        "best_supported_label_id": best_supported["variant_id"],
        "best_supported_typed_bytes": best_supported["typed_bytes"],
        "best_supported_saving_typed_bytes": champion["typed_bytes"] - best_supported["typed_bytes"],
        "supported_value_bytes_stable": all(row["value_bytes"] == ADJACENT_VALUE_BYTES for row in supported),
        "proof_size_comparable_external_rows": 0,
        "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
    }
    payload = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "issue_hint": ISSUE_HINT,
        "source_artifacts": [
            {
                "id": "source_adjacent_label_policy",
                "path": SOURCE_POLICY_RELATIVE_PATH,
                "sha256": source_gate.sha256(raw),
                "payload_commitment": source["payload_commitment"],
            }
        ],
        "full_inventory_policy": full_inventory_policy,
        "deterministic_policy": deterministic_policy,
        "label_inventory": inventory,
        "policy_summary": policy_summary,
        "interpretation": copy.deepcopy(EXPECTED_INTERPRETATION),
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    payload["mutation_result"] = mutation_result(payload)
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload)
    return payload


def expected_mutation_cases() -> list[dict[str, Any]]:
    return [
        {"name": name, "rejected": True, "error": EXPECTED_MUTATION_ERRORS[name]}
        for name in MUTATION_NAMES
    ]


def expected_mutation_result() -> dict[str, Any]:
    return {
        "all_mutations_rejected": True,
        "mutations_rejected": len(MUTATION_NAMES),
        "mutation_names": list(MUTATION_NAMES),
        "cases": expected_mutation_cases(),
    }


def mutation_result(payload: dict[str, Any]) -> dict[str, Any]:
    cases = []
    for name, mutate in mutation_functions():
        item = copy.deepcopy(payload)
        item.pop("mutation_result", None)
        item.pop("payload_commitment", None)
        mutate(item)
        item["mutation_result"] = expected_mutation_result()
        if name != "payload_commitment_drift":
            item["payload_commitment"] = payload_commitment(item)
        try:
            validate_payload(item)
        except DeterministicAdjacentLabelPolicyGateError as err:
            cases.append({"name": name, "rejected": True, "error": str(err)})
        else:
            cases.append({"name": name, "rejected": False, "error": ""})
    return {
        "all_mutations_rejected": all(case["rejected"] for case in cases),
        "mutations_rejected": sum(1 for case in cases if case["rejected"]),
        "mutation_names": list(MUTATION_NAMES),
        "cases": cases,
    }


def mutation_functions() -> tuple[tuple[str, Callable[[dict[str, Any]], None]], ...]:
    return (
        ("decision_drift", lambda item: item.update({"decision": "NO_GO"})),
        ("result_drift", lambda item: item.update({"result": "NO_RESULT"})),
        ("full_inventory_overclaim", lambda item: item["full_inventory_policy"].update({"full_inventory_promotable_vs_current_champion": True})),
        ("fixed_label_supported", lambda item: item["label_inventory"][1].update({"policy_status": "supported_label"})),
        ("probe_a_rejected", lambda item: item["label_inventory"][2].update({"policy_status": "rejected_inflating_label"})),
        ("worst_supported_typed_drift", lambda item: item["deterministic_policy"].update({"worst_supported_typed_bytes": 42_156})),
        ("worst_supported_saving_erased", lambda item: item["policy_summary"].update({"worst_supported_saving_typed_bytes": 0})),
        ("support_criteria_erased", lambda item: item["deterministic_policy"].update({"support_criteria": []})),
        ("value_stability_erased", lambda item: item["policy_summary"].update({"supported_value_bytes_stable": False})),
        ("source_digest_drift", lambda item: item["source_artifacts"][0].update({"sha256": "0" * 64})),
        ("source_commitment_drift", lambda item: item["source_artifacts"][0].update({"payload_commitment": "blake2b-256:" + "0" * 64})),
        ("validation_command_drift", lambda item: item["validation_commands"].append("echo untracked")),
        ("removed_non_claim", lambda item: item["non_claims"].remove("not robust to unseen labels")),
        ("nanozk_overclaim", lambda item: item.update({"claim_boundary": item["claim_boundary"] + ";NANOZK_WIN"})),
        ("final_policy_overclaim", lambda item: item["non_claims"].remove("not a final production label-selection policy")),
        ("unknown_policy_field", lambda item: item["deterministic_policy"].update({"unchecked": True})),
        ("label_inventory_order_drift", lambda item: item["label_inventory"].reverse()),
        ("label_adapter_mode_drift", lambda item: item["label_inventory"][2].update({"adapter_mode": "relabelled"})),
        ("label_proof_json_drift", lambda item: item["label_inventory"][3].update({"proof_json_bytes": 1})),
        ("label_status_reason_drift", lambda item: item["label_inventory"][1].update({"status_reason": "supported"})),
        ("champion_value_drift", lambda item: item["label_inventory"][0].update({"value_bytes": ADJACENT_VALUE_BYTES})),
        ("payload_commitment_drift", lambda item: item.update({"payload_commitment": "blake2b-256:" + "0" * 64})),
    )


def validate_payload(payload: dict[str, Any]) -> None:
    _require_exact_keys(payload, PAYLOAD_KEYS, "payload")
    expected_top = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "issue_hint": ISSUE_HINT,
    }
    for key, expected in expected_top.items():
        if payload.get(key) != expected:
            raise DeterministicAdjacentLabelPolicyGateError(f"{key} drift")
    if "NANOZK_WIN" in str(payload.get("claim_boundary")).split(";"):
        raise DeterministicAdjacentLabelPolicyGateError("claim_boundary drift")
    validate_source_artifacts(_list(payload.get("source_artifacts"), "source artifacts"))
    validate_full_inventory_policy(_dict(payload.get("full_inventory_policy"), "full inventory policy"))
    validate_deterministic_policy(_dict(payload.get("deterministic_policy"), "deterministic policy"))
    validate_label_inventory(_list(payload.get("label_inventory"), "label inventory"))
    validate_policy_summary(_dict(payload.get("policy_summary"), "policy summary"))
    if payload.get("interpretation") != EXPECTED_INTERPRETATION:
        raise DeterministicAdjacentLabelPolicyGateError("interpretation drift")
    if payload.get("non_claims") != list(NON_CLAIMS):
        raise DeterministicAdjacentLabelPolicyGateError("non_claims drift")
    if payload.get("validation_commands") != list(VALIDATION_COMMANDS):
        raise DeterministicAdjacentLabelPolicyGateError("validation command drift")
    validate_mutation_result(_dict(payload.get("mutation_result"), "mutation result"))
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise DeterministicAdjacentLabelPolicyGateError("payload commitment drift")


def validate_source_artifacts(artifacts: list[Any]) -> None:
    expected = [
        {
            "id": "source_adjacent_label_policy",
            "path": SOURCE_POLICY_RELATIVE_PATH,
            "sha256": EXPECTED_SOURCE_POLICY_SHA256,
            "payload_commitment": EXPECTED_SOURCE_POLICY_COMMITMENT,
        }
    ]
    for item in artifacts:
        _require_exact_keys(_dict(item, "source artifact"), SOURCE_ARTIFACT_KEYS, "source artifact")
    if artifacts != expected:
        raise DeterministicAdjacentLabelPolicyGateError("source artifact drift")


def validate_full_inventory_policy(policy: dict[str, Any]) -> None:
    _require_exact_keys(policy, FULL_POLICY_KEYS, "full inventory policy")
    expected = {
        "name": "full_adjacent_inventory_worst_label_v1",
        "full_inventory_label_ids": list(ADJACENT_LABEL_INVENTORY),
        "worst_full_inventory_label_id": FULL_INVENTORY_WORST_LABEL_ID,
        "worst_full_inventory_typed_bytes": FULL_INVENTORY_WORST_TYPED_BYTES,
        "delta_vs_current_champion_typed_bytes": FULL_INVENTORY_MISS_BYTES,
        "full_inventory_promotable_vs_current_champion": False,
        "reason": "the fixed adjacent label inflates path-opening material and misses the champion by 88 typed bytes",
    }
    if policy.get("full_inventory_promotable_vs_current_champion") is not False:
        raise DeterministicAdjacentLabelPolicyGateError("full inventory overclaim")
    if policy != expected:
        raise DeterministicAdjacentLabelPolicyGateError("full inventory policy drift")


def validate_deterministic_policy(policy: dict[str, Any]) -> None:
    _require_exact_keys(policy, DETERMINISTIC_POLICY_KEYS, "deterministic policy")
    expected = {
        "name": "reject_path_opening_inflation_v1",
        "support_criteria": [
            "adapter_mode is an adjacent label probe",
            "direct value bytes equal 20924",
            "path_opening_bytes are below the current champion",
            "typed_bytes are below the current champion",
            "source envelope and accounting are pinned by digest and payload commitment",
        ],
        "rejection_criteria": [
            "path_opening_bytes are greater than or equal to the current champion",
            "typed_bytes are greater than or equal to the current champion",
            "direct value bytes drift from the adjacent label inventory",
        ],
        "supported_label_ids": list(SUPPORTED_LABEL_IDS),
        "rejected_label_ids": [FIXED_ADJACENT_ID],
        "worst_supported_label_id": WORST_SUPPORTED_LABEL_ID,
        "worst_supported_typed_bytes": WORST_SUPPORTED_TYPED_BYTES,
        "worst_supported_saving_typed_bytes": WORST_SUPPORTED_SAVING_BYTES,
        "worst_supported_saving_share": "0.041267",
        "best_supported_label_id": BEST_SUPPORTED_LABEL_ID,
        "best_supported_typed_bytes": BEST_SUPPORTED_TYPED_BYTES,
        "best_supported_saving_typed_bytes": BEST_SUPPORTED_SAVING_BYTES,
        "supported_label_count": 2,
        "rejected_label_count": 1,
        "supported_labels_promotable_vs_current_champion": True,
    }
    if policy != expected:
        raise DeterministicAdjacentLabelPolicyGateError("deterministic policy drift")


def validate_label_inventory(rows: list[Any]) -> None:
    expected_ids = (CURRENT_CHAMPION_ID, *ADJACENT_LABEL_INVENTORY)
    parsed = []
    for item in rows:
        row = _dict(item, "label inventory item")
        _require_exact_keys(row, LABEL_ROW_KEYS, "label inventory item")
        parsed.append(row)
    if tuple(row["variant_id"] for row in parsed) != expected_ids:
        raise DeterministicAdjacentLabelPolicyGateError("label inventory order drift")
    expected_status = {
        CURRENT_CHAMPION_ID: "comparison_champion",
        FIXED_ADJACENT_ID: "rejected_inflating_label",
        "adjacent_label_probe_a": "supported_label",
        "adjacent_label_probe_b": "supported_label",
    }
    expected_typed = {
        CURRENT_CHAMPION_ID: CURRENT_CHAMPION_TYPED_BYTES,
        FIXED_ADJACENT_ID: FULL_INVENTORY_WORST_TYPED_BYTES,
        "adjacent_label_probe_a": WORST_SUPPORTED_TYPED_BYTES,
        "adjacent_label_probe_b": BEST_SUPPORTED_TYPED_BYTES,
    }
    expected_path_opening = {
        CURRENT_CHAMPION_ID: CURRENT_CHAMPION_PATH_OPENING_BYTES,
        FIXED_ADJACENT_ID: CURRENT_CHAMPION_PATH_OPENING_BYTES + FIXED_PATH_OPENING_OVERHANG_BYTES,
        "adjacent_label_probe_a": 19_360,
        "adjacent_label_probe_b": 16_560,
    }
    expected_metadata = {
        CURRENT_CHAMPION_ID: {
            "adapter_mode": "duplicate_base_preprocessed_v1",
            "proof_json_bytes": CURRENT_CHAMPION_JSON_BYTES,
            "status_reason": "baseline for typed/path-opening deltas",
            "value_bytes": CURRENT_CHAMPION_VALUE_BYTES,
        },
        FIXED_ADJACENT_ID: {
            "adapter_mode": "rmsnorm_input_fused_adjacent_fixed_v1",
            "proof_json_bytes": 122_688,
            "status_reason": "path-opening bytes are not below the current champion",
            "value_bytes": ADJACENT_VALUE_BYTES,
        },
        "adjacent_label_probe_a": {
            "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_a_v1",
            "proof_json_bytes": 116_321,
            "status_reason": "value bytes stable and path-opening/typed bytes beat the current champion",
            "value_bytes": ADJACENT_VALUE_BYTES,
        },
        "adjacent_label_probe_b": {
            "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_b_v1",
            "proof_json_bytes": 106_317,
            "status_reason": "value bytes stable and path-opening/typed bytes beat the current champion",
            "value_bytes": ADJACENT_VALUE_BYTES,
        },
    }
    for row in parsed:
        variant_id = row["variant_id"]
        if row["policy_status"] != expected_status[variant_id]:
            raise DeterministicAdjacentLabelPolicyGateError("label inventory drift")
        for field, expected in expected_metadata[variant_id].items():
            if row[field] != expected:
                raise DeterministicAdjacentLabelPolicyGateError("label inventory drift")
        if row["typed_bytes"] != expected_typed[variant_id]:
            raise DeterministicAdjacentLabelPolicyGateError("label inventory drift")
        if row["path_opening_bytes"] != expected_path_opening[variant_id]:
            raise DeterministicAdjacentLabelPolicyGateError("label inventory drift")
        if row["typed_delta_vs_champion"] != row["typed_bytes"] - CURRENT_CHAMPION_TYPED_BYTES:
            raise DeterministicAdjacentLabelPolicyGateError("label inventory drift")
        if row["path_opening_delta_vs_champion"] != row["path_opening_bytes"] - CURRENT_CHAMPION_PATH_OPENING_BYTES:
            raise DeterministicAdjacentLabelPolicyGateError("label inventory drift")


def validate_policy_summary(summary: dict[str, Any]) -> None:
    _require_exact_keys(summary, SUMMARY_KEYS, "policy summary")
    expected = {
        "current_champion_typed_bytes": CURRENT_CHAMPION_TYPED_BYTES,
        "current_champion_json_bytes": CURRENT_CHAMPION_JSON_BYTES,
        "current_champion_path_opening_bytes": CURRENT_CHAMPION_PATH_OPENING_BYTES,
        "fixed_adjacent_path_opening_overhang_vs_champion": FIXED_PATH_OPENING_OVERHANG_BYTES,
        "adjacent_value_bytes": ADJACENT_VALUE_BYTES,
        "full_inventory_worst_label_id": FULL_INVENTORY_WORST_LABEL_ID,
        "full_inventory_worst_typed_bytes": FULL_INVENTORY_WORST_TYPED_BYTES,
        "full_inventory_miss_vs_champion_typed_bytes": FULL_INVENTORY_MISS_BYTES,
        "supported_label_count": 2,
        "rejected_label_count": 1,
        "worst_supported_label_id": WORST_SUPPORTED_LABEL_ID,
        "worst_supported_typed_bytes": WORST_SUPPORTED_TYPED_BYTES,
        "worst_supported_saving_typed_bytes": WORST_SUPPORTED_SAVING_BYTES,
        "worst_supported_saving_share": "0.041267",
        "best_supported_label_id": BEST_SUPPORTED_LABEL_ID,
        "best_supported_typed_bytes": BEST_SUPPORTED_TYPED_BYTES,
        "best_supported_saving_typed_bytes": BEST_SUPPORTED_SAVING_BYTES,
        "supported_value_bytes_stable": True,
        "proof_size_comparable_external_rows": 0,
        "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
    }
    if summary != expected:
        raise DeterministicAdjacentLabelPolicyGateError("policy summary drift")


def validate_mutation_result(result: dict[str, Any]) -> None:
    _require_exact_keys(result, MUTATION_RESULT_KEYS, "mutation result")
    if result.get("mutation_names") != list(MUTATION_NAMES):
        raise DeterministicAdjacentLabelPolicyGateError("mutation result drift")
    cases = [_dict(case, "mutation case") for case in _list(result.get("cases"), "mutation cases")]
    for case in cases:
        _require_exact_keys(case, MUTATION_CASE_KEYS, "mutation case")
    if result.get("mutations_rejected") != len(MUTATION_NAMES) or result.get("all_mutations_rejected") is not True:
        raise DeterministicAdjacentLabelPolicyGateError("mutation result drift")
    if cases != expected_mutation_cases():
        raise DeterministicAdjacentLabelPolicyGateError("mutation result drift")


def render_tsv(payload: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in payload["label_inventory"]:
        writer.writerow({column: row[column] for column in TSV_COLUMNS})
    return output.getvalue()


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path | None, tsv_path: pathlib.Path | None) -> None:
    validate_payload(payload)
    if json_path is not None:
        source_gate.atomic_write_text(json_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if tsv_path is not None:
        source_gate.atomic_write_text(tsv_path, render_tsv(payload))


def payload_with_mutations() -> dict[str, Any]:
    return build_payload()


def main() -> None:
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
                "full_inventory_worst_typed_bytes": payload["policy_summary"]["full_inventory_worst_typed_bytes"],
                "worst_supported_typed_bytes": payload["policy_summary"]["worst_supported_typed_bytes"],
                "worst_supported_saving_typed_bytes": payload["policy_summary"]["worst_supported_saving_typed_bytes"],
                "mutations_rejected": payload["mutation_result"]["mutations_rejected"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
