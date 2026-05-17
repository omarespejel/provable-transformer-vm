#!/usr/bin/env python3
"""Gate RMSNorm-input label-inventory promotion policy."""

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

from scripts import zkai_native_attention_mlp_rmsnorm_label_sensitivity_gate as sensitivity_gate


EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
LABEL_SENSITIVITY_PATH = (
    EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-label-sensitivity-2026-05.json"
)
JSON_OUT = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-label-policy-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-label-policy-2026-05.tsv"

SCHEMA = "zkai-native-attention-mlp-rmsnorm-label-policy-gate-v1"
DECISION = "NO_GO_MULTI_LABEL_FRONTIER_PROMOTION"
RESULT = "WORST_LABEL_INVENTORY_REQUIRES_1401_TYPED_BYTE_REDUCTION_BEFORE_PROMOTION"
ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/644"
CLAIM_BOUNDARY = (
    "RMSNORM_INPUT_FUSED_OPENING_LAYOUT_CLAIMS_REQUIRE_A_MULTI_LABEL_INVENTORY;"
    "_CURRENT_INVENTORY_DOES_NOT_BEAT_THE_TWO_PROOF_FRONTIER"
)
PAYLOAD_DOMAIN = "ptvm:zkai:native-attention-mlp-rmsnorm-label-policy:v1"

EXPECTED_LABEL_SENSITIVITY_SHA256 = (
    "03777754ecf0a99f1ef7371cc038be99bd4471aeac3861ddf9a225697cf29f30"
)
EXPECTED_LABEL_SENSITIVITY_COMMITMENT = (
    "blake2b-256:ca919cd12acdfb5783a1c017d0b64bdba62adae082c8cf503af739076720df2a"
)

TWO_PROOF_FRONTIER_TYPED_BYTES = 40_700
COMPACT_SELECTOR_TYPED_BYTES = 40_812
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900
LABEL_INVENTORY = ("rmsnorm_input_fused", "label_probe_a", "label_probe_b")
POLICY_CANDIDATE_ORDER = (
    "single_best_label",
    "canonical_label",
    "mean_two_label_probes",
    "worst_label_inventory",
)
EXPECTED_LABEL_INVENTORY = {
    "rmsnorm_input_fused": {
        "typed_bytes": 41_428,
        "path_opening_bytes": 20_512,
        "value_bytes": 20_868,
        "value_delta_vs_canonical": 0,
    },
    "label_probe_a": {
        "typed_bytes": 40_836,
        "path_opening_bytes": 19_920,
        "value_bytes": 20_868,
        "value_delta_vs_canonical": 0,
    },
    "label_probe_b": {
        "typed_bytes": 42_100,
        "path_opening_bytes": 21_184,
        "value_bytes": 20_868,
        "value_delta_vs_canonical": 0,
    },
}

HUMAN_READ = (
    "The best observed label is only 136 typed bytes above the two-proof frontier, "
    "but the worst label in the current RMSNorm-input inventory is 1,400 bytes above it. "
    "Under an honest worst-label policy the next route must remove 1,401 typed bytes, "
    "not 137, before a frontier promotion is allowed."
)
NEXT_ATTACK = (
    "A future opening-layout variant must report the full label inventory and beat the "
    "two-proof frontier under the worst observed label. Single favorable labels are recorded "
    "as exploration only."
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
    "not timing evidence",
    "not a full transformer block proof",
    "not production-ready zkML",
)

VALIDATION_COMMANDS = (
    "python3 scripts/zkai_native_attention_mlp_rmsnorm_label_policy_gate.py --write-json "
    "docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-label-policy-2026-05.json "
    "--write-tsv docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-label-policy-2026-05.tsv",
    "python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_label_policy_gate",
    "python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_label_sensitivity_gate",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

EXPECTED_MUTATION_NAMES = (
    "frontier_overclaim",
    "nanozk_overclaim",
    "worst_label_typed_drift",
    "worst_policy_reduction_drift",
    "single_label_promoted",
    "label_span_erased",
    "inventory_byte_drift",
    "candidate_missing_worst_label",
    "source_digest_drift",
    "source_commitment_drift",
    "decision_drift",
    "result_drift",
    "claim_boundary_drift",
    "non_claims_erased",
    "validation_commands_erased",
    "interpretation_drift",
    "policy_extra_key",
    "payload_commitment_drift",
)

TSV_COLUMNS = (
    "policy_candidate",
    "typed_bytes",
    "delta_vs_two_proof_frontier_bytes",
    "reduction_to_beat_frontier_bytes",
    "delta_vs_compact_selector_bytes",
    "reduction_to_beat_compact_selector_bytes",
    "frontier_promotable",
    "cherry_pick_risk",
)


class LabelPolicyError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode(
            "utf-8"
        )
    except (TypeError, ValueError) as err:
        raise LabelPolicyError(f"invalid JSON value: {err}") from err


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return "blake2b-256:" + digest.hexdigest()


def refresh_payload_commitment(payload: dict[str, Any]) -> None:
    payload["payload_commitment"] = payload_commitment(payload)


def _dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LabelPolicyError(f"{label} must be object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise LabelPolicyError(f"{label} must be list")
    return value


def _int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise LabelPolicyError(f"{label} must be integer")
    return value


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
        raise LabelPolicyError(f"{label} key drift: {', '.join(details)}")


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def reduction_to_beat(value: int, threshold: int) -> int:
    return max(0, value - threshold + 1)


def read_label_sensitivity_payload() -> tuple[dict[str, Any], bytes]:
    try:
        payload, raw = sensitivity_gate.read_json(LABEL_SENSITIVITY_PATH, "label sensitivity")
        sensitivity_gate.validate_payload(payload)
    except sensitivity_gate.RmsnormLabelSensitivityError as err:
        raise LabelPolicyError(f"label sensitivity source invalid: {err}") from err
    source_sha = sha256_hex(raw)
    if source_sha != EXPECTED_LABEL_SENSITIVITY_SHA256:
        raise LabelPolicyError("label sensitivity source digest drift")
    if payload.get("payload_commitment") != EXPECTED_LABEL_SENSITIVITY_COMMITMENT:
        raise LabelPolicyError("label sensitivity payload commitment drift")
    return payload, raw


def policy_candidate(name: str, typed_bytes: int, *, label_source: str, cherry_pick_risk: bool) -> dict[str, Any]:
    return {
        "name": name,
        "label_source": label_source,
        "typed_bytes": typed_bytes,
        "delta_vs_two_proof_frontier_bytes": typed_bytes - TWO_PROOF_FRONTIER_TYPED_BYTES,
        "reduction_to_beat_frontier_bytes": reduction_to_beat(
            typed_bytes, TWO_PROOF_FRONTIER_TYPED_BYTES
        ),
        "delta_vs_compact_selector_bytes": typed_bytes - COMPACT_SELECTOR_TYPED_BYTES,
        "reduction_to_beat_compact_selector_bytes": reduction_to_beat(
            typed_bytes, COMPACT_SELECTOR_TYPED_BYTES
        ),
        "frontier_promotable": typed_bytes < TWO_PROOF_FRONTIER_TYPED_BYTES,
        "compact_promotable": typed_bytes < COMPACT_SELECTOR_TYPED_BYTES,
        "cherry_pick_risk": cherry_pick_risk,
    }


def build_payload(include_mutations: bool = True) -> dict[str, Any]:
    source, raw = read_label_sensitivity_payload()
    variants = _dict(source.get("variants"), "source variants")
    inventory = []
    for name in LABEL_INVENTORY:
        variant = _dict(variants.get(name), f"source variant {name}")
        inventory.append(
            {
                "name": name,
                "typed_bytes": _int(variant.get("typed_bytes"), f"{name}.typed"),
                "path_opening_bytes": _int(
                    variant.get("path_opening_bytes"), f"{name}.path_opening"
                ),
                "value_bytes": _int(variant.get("value_bytes"), f"{name}.value"),
                "value_delta_vs_canonical": _int(
                    variant.get("value_delta_vs_canonical"), f"{name}.value_delta"
                ),
            }
        )

    canonical = next(item for item in inventory if item["name"] == "rmsnorm_input_fused")
    probe_a = next(item for item in inventory if item["name"] == "label_probe_a")
    probe_b = next(item for item in inventory if item["name"] == "label_probe_b")
    best_label = min(inventory, key=lambda item: item["typed_bytes"])
    worst_label = max(inventory, key=lambda item: item["typed_bytes"])
    label_span = worst_label["typed_bytes"] - best_label["typed_bytes"]
    mean_probe_typed = (probe_a["typed_bytes"] + probe_b["typed_bytes"]) // 2

    candidates = {
        "single_best_label": policy_candidate(
            "single_best_label",
            best_label["typed_bytes"],
            label_source=best_label["name"],
            cherry_pick_risk=True,
        ),
        "canonical_label": policy_candidate(
            "canonical_label",
            canonical["typed_bytes"],
            label_source=canonical["name"],
            cherry_pick_risk=False,
        ),
        "mean_two_label_probes": policy_candidate(
            "mean_two_label_probes",
            mean_probe_typed,
            label_source="mean(label_probe_a,label_probe_b)",
            cherry_pick_risk=True,
        ),
        "worst_label_inventory": policy_candidate(
            "worst_label_inventory",
            worst_label["typed_bytes"],
            label_source=worst_label["name"],
            cherry_pick_risk=False,
        ),
    }
    worst_policy = candidates["worst_label_inventory"]
    if worst_policy["reduction_to_beat_frontier_bytes"] != 1_401:
        raise LabelPolicyError("worst-label frontier budget drift")
    if any(item["value_delta_vs_canonical"] != 0 for item in inventory if item["name"] != "rmsnorm_input_fused"):
        raise LabelPolicyError("label inventory changed direct value bytes")

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_artifacts": [
            {
                "name": "label_sensitivity_gate",
                "path": str(LABEL_SENSITIVITY_PATH.relative_to(ROOT)),
                "sha256": sha256_hex(raw),
                "payload_commitment": source["payload_commitment"],
            }
        ],
        "frontier": {
            "two_proof_frontier_typed_bytes": TWO_PROOF_FRONTIER_TYPED_BYTES,
            "compact_selector_typed_bytes": COMPACT_SELECTOR_TYPED_BYTES,
            "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
            "frontier_win_claimed": False,
            "nanozk_win_claimed": False,
            "nanozk_workload_matched": False,
        },
        "label_inventory": inventory,
        "policy_candidates": candidates,
        "promotion_policy": {
            "policy": "worst_label_inventory_must_beat_two_proof_frontier",
            "required_reduction_to_beat_frontier_bytes": worst_policy[
                "reduction_to_beat_frontier_bytes"
            ],
            "required_reduction_to_beat_compact_selector_bytes": worst_policy[
                "reduction_to_beat_compact_selector_bytes"
            ],
            "multi_label_frontier_promotable": False,
            "single_label_frontier_promotable": False,
            "single_label_cherry_pick_rejected": True,
        },
        "summary": {
            "best_observed_label": best_label["name"],
            "best_observed_label_typed_bytes": best_label["typed_bytes"],
            "best_observed_label_delta_vs_frontier_bytes": best_label["typed_bytes"]
            - TWO_PROOF_FRONTIER_TYPED_BYTES,
            "single_best_label_reduction_to_beat_frontier_bytes": candidates[
                "single_best_label"
            ]["reduction_to_beat_frontier_bytes"],
            "canonical_label_reduction_to_beat_frontier_bytes": candidates["canonical_label"][
                "reduction_to_beat_frontier_bytes"
            ],
            "mean_two_label_probes_reduction_to_beat_frontier_bytes": candidates[
                "mean_two_label_probes"
            ]["reduction_to_beat_frontier_bytes"],
            "worst_label_inventory": worst_label["name"],
            "worst_label_inventory_typed_bytes": worst_label["typed_bytes"],
            "worst_label_inventory_delta_vs_frontier_bytes": worst_label["typed_bytes"]
            - TWO_PROOF_FRONTIER_TYPED_BYTES,
            "worst_label_inventory_reduction_to_beat_frontier_bytes": worst_policy[
                "reduction_to_beat_frontier_bytes"
            ],
            "worst_label_inventory_reduction_to_beat_compact_selector_bytes": worst_policy[
                "reduction_to_beat_compact_selector_bytes"
            ],
            "label_span_typed_bytes": label_span,
            "value_delta_preserved_across_labels": True,
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
        raise LabelPolicyError("mutation count drift")
    if _int(mutation_result.get("rejected_count"), "rejected count") != len(EXPECTED_MUTATION_NAMES):
        raise LabelPolicyError("mutation rejected count drift")
    names = []
    for index, case in enumerate(cases):
        case_obj = _dict(case, f"mutation case {index}")
        require_exact_keys(case_obj, {"name", "rejected"}, f"mutation case {index}")
        name = case_obj.get("name")
        if not isinstance(name, str):
            raise LabelPolicyError("mutation case name drift")
        names.append(name)
        if case_obj.get("rejected") is not True:
            raise LabelPolicyError(f"mutation not rejected: {name}")
    if tuple(names) != EXPECTED_MUTATION_NAMES:
        raise LabelPolicyError("mutation inventory drift")


def validate_payload(payload: dict[str, Any]) -> None:
    expected_top = {
        "schema",
        "decision",
        "result",
        "issue",
        "claim_boundary",
        "source_artifacts",
        "frontier",
        "label_inventory",
        "policy_candidates",
        "promotion_policy",
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
        raise LabelPolicyError("schema drift")
    if payload.get("decision") != DECISION:
        raise LabelPolicyError("decision drift")
    if payload.get("result") != RESULT:
        raise LabelPolicyError("result drift")
    if payload.get("issue") != ISSUE:
        raise LabelPolicyError("issue drift")
    if payload.get("claim_boundary") != CLAIM_BOUNDARY:
        raise LabelPolicyError("claim boundary drift")

    source_artifacts = _list(payload.get("source_artifacts"), "source artifacts")
    expected_source = [
        {
            "name": "label_sensitivity_gate",
            "path": str(LABEL_SENSITIVITY_PATH.relative_to(ROOT)),
            "sha256": EXPECTED_LABEL_SENSITIVITY_SHA256,
            "payload_commitment": EXPECTED_LABEL_SENSITIVITY_COMMITMENT,
        }
    ]
    if source_artifacts != expected_source:
        raise LabelPolicyError("source artifact drift")

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
        raise LabelPolicyError("frontier overclaim")
    if frontier.get("nanozk_win_claimed") is not False:
        raise LabelPolicyError("NANOZK overclaim")
    if frontier.get("nanozk_workload_matched") is not False:
        raise LabelPolicyError("NANOZK workload drift")
    if frontier != expected_frontier:
        raise LabelPolicyError("frontier body drift")

    inventory = _list(payload.get("label_inventory"), "label inventory")
    if tuple(item.get("name") for item in inventory if isinstance(item, dict)) != LABEL_INVENTORY:
        raise LabelPolicyError("label inventory order drift")
    value_deltas = []
    inventory_by_name = {}
    for item in inventory:
        label = _dict(item, "label inventory item")
        require_exact_keys(
            label,
            {"name", "typed_bytes", "path_opening_bytes", "value_bytes", "value_delta_vs_canonical"},
            "label inventory item",
        )
        name = label.get("name")
        if name not in LABEL_INVENTORY:
            raise LabelPolicyError("unknown label inventory item")
        inventory_by_name[name] = label
        value_deltas.append(_int(label.get("value_delta_vs_canonical"), f"{name}.value_delta"))
        for field, expected_value in EXPECTED_LABEL_INVENTORY[name].items():
            if _int(label.get(field), f"{name}.{field}") != expected_value:
                raise LabelPolicyError(f"{name} inventory byte drift")
    if any(delta != 0 for delta in value_deltas[1:]):
        raise LabelPolicyError("label value delta drift")

    candidates = _dict(payload.get("policy_candidates"), "policy candidates")
    require_exact_keys(candidates, set(POLICY_CANDIDATE_ORDER), "policy candidates")
    expected_candidate_values = {
        "single_best_label": ("label_probe_a", 40_836, True),
        "canonical_label": ("rmsnorm_input_fused", 41_428, False),
        "mean_two_label_probes": ("mean(label_probe_a,label_probe_b)", 41_468, True),
        "worst_label_inventory": ("label_probe_b", 42_100, False),
    }
    for name in POLICY_CANDIDATE_ORDER:
        candidate = _dict(candidates.get(name), f"candidate {name}")
        require_exact_keys(
            candidate,
            {
                "name",
                "label_source",
                "typed_bytes",
                "delta_vs_two_proof_frontier_bytes",
                "reduction_to_beat_frontier_bytes",
                "delta_vs_compact_selector_bytes",
                "reduction_to_beat_compact_selector_bytes",
                "frontier_promotable",
                "compact_promotable",
                "cherry_pick_risk",
            },
            f"candidate {name}",
        )
        label_source, typed, cherry_pick = expected_candidate_values[name]
        if candidate.get("name") != name:
            raise LabelPolicyError(f"{name} name drift")
        if candidate.get("label_source") != label_source:
            raise LabelPolicyError(f"{name} label source drift")
        if _int(candidate.get("typed_bytes"), f"{name}.typed") != typed:
            raise LabelPolicyError(f"{name} typed drift")
        if candidate.get("cherry_pick_risk") is not cherry_pick:
            raise LabelPolicyError(f"{name} cherry-pick drift")
        if candidate.get("frontier_promotable") is not False:
            raise LabelPolicyError(f"{name} frontier overclaim")
        if candidate.get("compact_promotable") is not False:
            raise LabelPolicyError(f"{name} compact overclaim")
        if _int(candidate.get("delta_vs_two_proof_frontier_bytes"), f"{name}.frontier_delta") != (
            typed - TWO_PROOF_FRONTIER_TYPED_BYTES
        ):
            raise LabelPolicyError(f"{name} frontier delta drift")
        if _int(candidate.get("reduction_to_beat_frontier_bytes"), f"{name}.frontier_reduction") != (
            reduction_to_beat(typed, TWO_PROOF_FRONTIER_TYPED_BYTES)
        ):
            raise LabelPolicyError(f"{name} frontier reduction drift")
        if _int(candidate.get("delta_vs_compact_selector_bytes"), f"{name}.compact_delta") != (
            typed - COMPACT_SELECTOR_TYPED_BYTES
        ):
            raise LabelPolicyError(f"{name} compact delta drift")
        if _int(candidate.get("reduction_to_beat_compact_selector_bytes"), f"{name}.compact_reduction") != (
            reduction_to_beat(typed, COMPACT_SELECTOR_TYPED_BYTES)
        ):
            raise LabelPolicyError(f"{name} compact reduction drift")

    policy = _dict(payload.get("promotion_policy"), "promotion policy")
    require_exact_keys(
        policy,
        {
            "policy",
            "required_reduction_to_beat_frontier_bytes",
            "required_reduction_to_beat_compact_selector_bytes",
            "multi_label_frontier_promotable",
            "single_label_frontier_promotable",
            "single_label_cherry_pick_rejected",
        },
        "promotion policy",
    )
    if policy.get("policy") != "worst_label_inventory_must_beat_two_proof_frontier":
        raise LabelPolicyError("promotion policy drift")
    if _int(policy.get("required_reduction_to_beat_frontier_bytes"), "policy frontier reduction") != 1_401:
        raise LabelPolicyError("policy frontier reduction drift")
    if _int(policy.get("required_reduction_to_beat_compact_selector_bytes"), "policy compact reduction") != 1_289:
        raise LabelPolicyError("policy compact reduction drift")
    if policy.get("multi_label_frontier_promotable") is not False:
        raise LabelPolicyError("multi-label frontier overclaim")
    if policy.get("single_label_frontier_promotable") is not False:
        raise LabelPolicyError("single-label frontier overclaim")
    if policy.get("single_label_cherry_pick_rejected") is not True:
        raise LabelPolicyError("single-label cherry-pick guard erased")

    summary = _dict(payload.get("summary"), "summary")
    expected_summary = {
        "best_observed_label": "label_probe_a",
        "best_observed_label_typed_bytes": 40_836,
        "best_observed_label_delta_vs_frontier_bytes": 136,
        "single_best_label_reduction_to_beat_frontier_bytes": 137,
        "canonical_label_reduction_to_beat_frontier_bytes": 729,
        "mean_two_label_probes_reduction_to_beat_frontier_bytes": 769,
        "worst_label_inventory": "label_probe_b",
        "worst_label_inventory_typed_bytes": 42_100,
        "worst_label_inventory_delta_vs_frontier_bytes": 1_400,
        "worst_label_inventory_reduction_to_beat_frontier_bytes": 1_401,
        "worst_label_inventory_reduction_to_beat_compact_selector_bytes": 1_289,
        "label_span_typed_bytes": 1_264,
        "value_delta_preserved_across_labels": True,
    }
    if summary != expected_summary:
        raise LabelPolicyError("summary drift")
    if _dict(payload.get("interpretation"), "interpretation") != INTERPRETATION:
        raise LabelPolicyError("interpretation drift")
    if _list(payload.get("non_claims"), "non_claims") != list(NON_CLAIMS):
        raise LabelPolicyError("non-claims drift")
    if _list(payload.get("validation_commands"), "validation_commands") != list(VALIDATION_COMMANDS):
        raise LabelPolicyError("validation commands drift")
    if "mutation_result" in payload:
        validate_mutation_result(_dict(payload.get("mutation_result"), "mutation result"))
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise LabelPolicyError("payload commitment drift")


def run_mutations(payload: dict[str, Any]) -> dict[str, Any]:
    mutations = (
        ("frontier_overclaim", lambda p: p["frontier"].__setitem__("frontier_win_claimed", True)),
        ("nanozk_overclaim", lambda p: p["frontier"].__setitem__("nanozk_win_claimed", True)),
        ("worst_label_typed_drift", lambda p: p["summary"].__setitem__("worst_label_inventory_typed_bytes", 40_700)),
        (
            "worst_policy_reduction_drift",
            lambda p: p["promotion_policy"].__setitem__("required_reduction_to_beat_frontier_bytes", 137),
        ),
        (
            "single_label_promoted",
            lambda p: p["promotion_policy"].__setitem__("single_label_frontier_promotable", True),
        ),
        ("label_span_erased", lambda p: p["summary"].__setitem__("label_span_typed_bytes", 0)),
        ("inventory_byte_drift", lambda p: p["label_inventory"][0].__setitem__("typed_bytes", 41_429)),
        ("candidate_missing_worst_label", lambda p: p["policy_candidates"].pop("worst_label_inventory")),
        ("source_digest_drift", lambda p: p["source_artifacts"][0].__setitem__("sha256", "00" * 32)),
        (
            "source_commitment_drift",
            lambda p: p["source_artifacts"][0].__setitem__("payload_commitment", "blake2b-256:" + "00" * 32),
        ),
        ("decision_drift", lambda p: p.__setitem__("decision", "GO_MULTI_LABEL_FRONTIER_PROMOTION")),
        ("result_drift", lambda p: p.__setitem__("result", "LABEL_INVENTORY_BEATS_FRONTIER")),
        ("claim_boundary_drift", lambda p: p.__setitem__("claim_boundary", "OVERCLAIMED")),
        ("non_claims_erased", lambda p: p.__setitem__("non_claims", [])),
        ("validation_commands_erased", lambda p: p.__setitem__("validation_commands", [])),
        ("interpretation_drift", lambda p: p["interpretation"].__setitem__("human_read", "overclaimed")),
        ("policy_extra_key", lambda p: p["promotion_policy"].__setitem__("unchecked", True)),
        ("payload_commitment_drift", lambda p: p.__setitem__("payload_commitment", "blake2b-256:" + "00" * 32)),
    )
    if tuple(name for name, _ in mutations) != EXPECTED_MUTATION_NAMES:
        raise LabelPolicyError("mutation definitions drift")
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
        except LabelPolicyError:
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
    for name in POLICY_CANDIDATE_ORDER:
        candidate = payload["policy_candidates"][name]
        writer.writerow(
            {
                "policy_candidate": name,
                "typed_bytes": candidate["typed_bytes"],
                "delta_vs_two_proof_frontier_bytes": candidate["delta_vs_two_proof_frontier_bytes"],
                "reduction_to_beat_frontier_bytes": candidate["reduction_to_beat_frontier_bytes"],
                "delta_vs_compact_selector_bytes": candidate["delta_vs_compact_selector_bytes"],
                "reduction_to_beat_compact_selector_bytes": candidate[
                    "reduction_to_beat_compact_selector_bytes"
                ],
                "frontier_promotable": str(candidate["frontier_promotable"]).lower(),
                "cherry_pick_risk": str(candidate["cherry_pick_risk"]).lower(),
            }
        )
    return output.getvalue()


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path | None, tsv_path: pathlib.Path | None) -> None:
    validate_payload(payload)
    try:
        if json_path is not None:
            sensitivity_gate.write_text_atomically(
                json_path, json.dumps(payload, indent=2, sort_keys=True) + "\n"
            )
        if tsv_path is not None:
            sensitivity_gate.write_text_atomically(tsv_path, tsv_text(payload))
    except sensitivity_gate.RmsnormLabelSensitivityError as err:
        raise LabelPolicyError(f"failed to write output: {err}") from err


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
                "worst_label_inventory_typed_bytes": payload["summary"][
                    "worst_label_inventory_typed_bytes"
                ],
                "worst_label_reduction_to_beat_frontier_bytes": payload["summary"][
                    "worst_label_inventory_reduction_to_beat_frontier_bytes"
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
