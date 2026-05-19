#!/usr/bin/env python3.10
"""Gate verifier-facing attempt-domain binding for the seq32+d128 Stwo row."""

from __future__ import annotations

import argparse
import copy
import csv
import functools
import hashlib
import io
import json
import pathlib
import sys
from collections.abc import Callable
from typing import Any


if sys.version_info < (3, 10):
    raise RuntimeError("zkai_stwo_attempt_domain_binding_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import zkai_native_seq32_attention_mlp_generated_proof_object_builder_gate as builder_gate
from scripts import zkai_stwo_query_grinding_budget_gate as budget_gate


EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
BUILDER_PATH = builder_gate.JSON_OUT
BUDGET_PATH = budget_gate.JSON_OUT
JSON_OUT = EVIDENCE_DIR / "zkai-stwo-attempt-domain-binding-gate-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-stwo-attempt-domain-binding-gate-2026-05.tsv"

SCHEMA = "zkai-stwo-attempt-domain-binding-gate-v1"
DECISION = "GO_TYPED_OUTER_ENVELOPE_BINDS_TWO_PROBE_ATTEMPT_DOMAIN_TO_EXISTING_PROOF_ROW"
RESULT = "PROBE_B_ROW_BOUND_WITH_1_BIT_RELATIVE_LOSS_NOT_INNER_STWO_TRANSCRIPT_BINDING"
CLAIM_BOUNDARY = (
    "TYPED_VERIFIER_FACING_ENVELOPE_OVER_EXISTING_SEQ32_D128_STWO_PROOF_ROW;"
    "BINDS_ATTEMPT_DOMAIN_SELECTED_ATTEMPT_AND_PROOF_ARTIFACT_HASHES;"
    "NOT_FRESH_PROOF_GENERATION_NOT_INNER_STWO_TRANSCRIPT_BINDING_NOT_A_NANOZK_WIN"
)
ISSUE_HINT = "https://github.com/omarespejel/provable-transformer-vm/issues/708"
PAYLOAD_DOMAIN = "ptvm:zkai:stwo-attempt-domain-binding:v1"

EXPECTED_BUILDER_SHA256 = "d8685f504a7f9fd935ec1b317aa8afd244c84e83d4e45ef7da9e80bca022f7b1"
EXPECTED_BUILDER_COMMITMENT = "blake2b-256:c25c9d8b0af3394006b266754ba65fc92ee79080f1755066c2fab034161e18dd"
EXPECTED_BUDGET_SHA256 = "a5ef30dc1cdd2aa0bc72163a40f2c66358265a1ef0f29d0e41ff4cf972951303"
EXPECTED_BUDGET_COMMITMENT = "blake2b-256:139ebaf55f70c771cf1d1f9f6fb8a132bc2215118e46a6ca4dbd2d6da4e0aea6"
EXPECTED_PAYLOAD_COMMITMENT = "blake2b-256:1dac8ed53a269f2649da650afce07f4a96810e4f1c0a37426fd3c10a12b86691"

ATTEMPT_DOMAIN = ("adjacent_label_probe_a", "adjacent_label_probe_b")
SELECTED_ATTEMPT_ID = "adjacent_label_probe_b"
REJECTED_ATTEMPT_ID = "fixed_adjacent_layout"
ATTEMPT_BUDGET = 2
SECURITY_LOSS_BITS = "1.000000"
MATCHED_TWO_PROOF_FRONTIER_TYPED_BYTES = 47_188
MATCHED_TWO_PROOF_FRONTIER_JSON_BYTES = 140_838
CURRENT_SINGLE_PROOF_CHAMPION_TYPED_BYTES = 42_068
SELECTED_TYPED_BYTES = 37_532
SELECTED_JSON_BYTES = 106_317
SELECTED_SAVING_VS_SINGLE_PROOF_CHAMPION = 4_536
SELECTED_SAVING_VS_MATCHED_FRONTIER = 9_656

NON_CLAIMS = (
    "not fresh proof generation",
    "not a new proof-size frontier beyond the existing 37,532 typed-byte probe-B row",
    "not inner Stwo transcript binding of the attempt domain",
    "not an absolute soundness claim",
    "not unbounded retry",
    "not post-decommitment proof-byte selection",
    "not a NANOZK proof-size comparison",
    "not a full transformer block proof",
    "not timing evidence",
    "not production-ready zkML",
)
VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_stwo_attempt_domain_binding_gate.py --write-json docs/engineering/evidence/zkai-stwo-attempt-domain-binding-gate-2026-05.json --write-tsv docs/engineering/evidence/zkai-stwo-attempt-domain-binding-gate-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_stwo_attempt_domain_binding_gate.py scripts/tests/test_zkai_stwo_attempt_domain_binding_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_stwo_attempt_domain_binding_gate",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_generated_proof_object_builder_gate",
    "python3.10 -m unittest scripts.tests.test_zkai_stwo_query_grinding_budget_gate",
    "git diff --check",
    "just gate-fast",
    "just gate",
)
MUTATION_NAMES = (
    "decision_drift",
    "result_drift",
    "claim_boundary_overclaim",
    "builder_digest_drift",
    "builder_commitment_drift",
    "budget_digest_drift",
    "budget_commitment_drift",
    "attempt_domain_removed",
    "attempt_domain_reordered",
    "selected_attempt_changed",
    "selected_attempt_outside_domain",
    "attempt_budget_drift",
    "security_loss_understated",
    "unbounded_retry_allowed",
    "final_proof_bytes_allowed",
    "post_decommitment_accounting_allowed",
    "outer_envelope_binding_removed",
    "inner_transcript_overclaim",
    "selected_proof_hash_drift",
    "selected_typed_bytes_drift",
    "new_frontier_overclaim",
    "nanozk_overclaim",
    "validation_command_drift",
    "removed_non_claim",
    "payload_commitment_drift",
)
EXPECTED_MUTATION_ERRORS = {
    "decision_drift": "decision drift",
    "result_drift": "result drift",
    "claim_boundary_overclaim": "claim_boundary drift",
    "builder_digest_drift": "source artifact drift",
    "builder_commitment_drift": "source artifact drift",
    "budget_digest_drift": "source artifact drift",
    "budget_commitment_drift": "source artifact drift",
    "attempt_domain_removed": "attempt domain drift",
    "attempt_domain_reordered": "attempt domain drift",
    "selected_attempt_changed": "selected attempt drift",
    "selected_attempt_outside_domain": "selected attempt drift",
    "attempt_budget_drift": "attempt budget drift",
    "security_loss_understated": "security loss drift",
    "unbounded_retry_allowed": "unbounded retry drift",
    "final_proof_bytes_allowed": "policy input drift",
    "post_decommitment_accounting_allowed": "policy input drift",
    "outer_envelope_binding_removed": "outer envelope binding drift",
    "inner_transcript_overclaim": "inner transcript binding drift",
    "selected_proof_hash_drift": "selected proof artifact drift",
    "selected_typed_bytes_drift": "selected proof artifact drift",
    "new_frontier_overclaim": "binding summary drift",
    "nanozk_overclaim": "claim_boundary drift",
    "validation_command_drift": "validation command drift",
    "removed_non_claim": "non_claims drift",
    "payload_commitment_drift": "payload commitment drift",
}

PAYLOAD_KEYS = {
    "schema",
    "decision",
    "result",
    "claim_boundary",
    "issue_hint",
    "source_artifacts",
    "verifier_facing_attempt_envelope",
    "binding_summary",
    "interpretation",
    "non_claims",
    "validation_commands",
    "mutation_result",
    "payload_commitment",
}
SOURCE_ARTIFACT_KEYS = {"id", "path", "sha256", "payload_commitment", "schema", "decision"}
ENVELOPE_KEYS = {
    "envelope_version",
    "verifier_domain",
    "target_id",
    "proof_backend",
    "proof_backend_version",
    "statement_version",
    "proof_schema_version",
    "attempt_domain",
    "attempt_budget",
    "selected_attempt_id",
    "selected_attempt_index",
    "security_loss_bits",
    "security_loss_formula",
    "verifier_rejects_attempts_outside_domain",
    "unbounded_retry_allowed",
    "policy_inputs",
    "bound_source_commitments",
    "bound_proof_artifact",
}
POLICY_INPUT_KEYS = {
    "attempt_domain",
    "selected_attempt_id",
    "security_loss_bits",
    "final_envelope_json",
    "final_proof_bytes",
    "post_decommitment_accounting",
    "unbounded_retry_count",
}
BOUND_SOURCE_KEYS = {
    "generated_proof_object_builder_payload_commitment",
    "query_grinding_budget_payload_commitment",
    "generated_proof_object_builder_sha256",
    "query_grinding_budget_sha256",
}
BOUND_PROOF_KEYS = {
    "variant_id",
    "adapter_mode",
    "policy_status",
    "path",
    "accounting_path",
    "typed_bytes",
    "typed_saving_vs_single_proof_champion",
    "typed_saving_vs_matched_two_proof_frontier",
    "proof_json_bytes",
    "path_opening_bytes",
    "value_bytes",
    "envelope_sha256",
    "proof_sha256",
    "input_sha256",
    "record_stream_sha256",
}
SUMMARY_KEYS = {
    "outer_envelope_binds_attempt_domain",
    "outer_envelope_binds_selected_attempt_id",
    "outer_envelope_binds_selected_proof_hashes",
    "inner_stwo_transcript_binds_attempt_domain",
    "inner_stwo_transcript_binds_selected_attempt_id",
    "proof_object_regenerated",
    "new_frontier_claimed",
    "selected_attempt_id",
    "selected_typed_bytes",
    "selected_json_bytes",
    "attempt_budget",
    "security_loss_bits",
    "saving_vs_current_single_proof_champion_typed_bytes",
    "saving_vs_matched_two_proof_frontier_typed_bytes",
    "result_status",
}
MUTATION_RESULT_KEYS = {"all_mutations_rejected", "mutations_rejected", "mutation_names", "cases"}
MUTATION_CASE_KEYS = {"name", "rejected", "error"}
TSV_COLUMNS = (
    "selected_attempt_id",
    "attempt_domain",
    "attempt_budget",
    "security_loss_bits",
    "typed_bytes",
    "proof_json_bytes",
    "saving_vs_current_single_proof_champion_typed_bytes",
    "saving_vs_matched_two_proof_frontier_typed_bytes",
    "outer_envelope_binds_attempt_domain",
    "inner_stwo_transcript_binds_attempt_domain",
    "new_frontier_claimed",
    "builder_payload_commitment",
    "budget_payload_commitment",
    "selected_envelope_sha256",
    "selected_proof_sha256",
    "payload_commitment",
    "mutation_outcomes",
)

EXPECTED_INTERPRETATION = {
    "human_read": (
        "The proof row is already real and artifact-bound. This gate adds the missing typed statement "
        "wrapper: a verifier-facing envelope names the only allowed attempts, names probe B as the "
        "selected attempt, and binds that choice to the selected proof hashes."
    ),
    "security_read": (
        "The envelope charges the two-probe search as 1.000000 bit of relative Fiat-Shamir loss and "
        "forbids final proof bytes, post-decommitment accounting, and unbounded retry as policy inputs."
    ),
    "research_read": (
        "This is a correctness promotion for the existing 37,532 typed-byte row, not a fresh proof-size "
        "frontier. The next stronger result is a regenerated proof whose inner statement metadata also "
        "carries the attempt domain and selected attempt id."
    ),
}


class AttemptDomainBindingGateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as err:
        raise AttemptDomainBindingGateError(f"invalid JSON value: {err}") from err


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return "blake2b-256:" + digest.hexdigest()


def _dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AttemptDomainBindingGateError(f"{label} must be object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise AttemptDomainBindingGateError(f"{label} must be list")
    return value


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual == expected:
        return
    unexpected = sorted(actual - expected)
    missing = sorted(expected - actual)
    if unexpected:
        raise AttemptDomainBindingGateError(f"{label} field drift: unexpected {unexpected[0]}")
    raise AttemptDomainBindingGateError(f"{label} field drift: missing {missing[0]}")


def load_json_file(path: pathlib.Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        payload, raw = builder_gate.load_json_file(path, label)
    except builder_gate.GeneratedProofObjectBuilderGateError as err:
        raise AttemptDomainBindingGateError(str(err)) from err
    return _dict(payload, label), raw


def load_builder_payload() -> tuple[dict[str, Any], bytes]:
    payload, raw = load_json_file(BUILDER_PATH, "generated proof-object builder")
    if sha256(raw) != EXPECTED_BUILDER_SHA256:
        raise AttemptDomainBindingGateError("builder digest drift")
    if payload.get("payload_commitment") != EXPECTED_BUILDER_COMMITMENT:
        raise AttemptDomainBindingGateError("builder commitment drift")
    try:
        builder_gate.validate_payload(payload)
        if builder_gate.build_payload() != payload:
            raise AttemptDomainBindingGateError("builder rebuild drift")
    except builder_gate.GeneratedProofObjectBuilderGateError as err:
        raise AttemptDomainBindingGateError(f"builder invalid: {err}") from err
    return payload, raw


def load_budget_payload() -> tuple[dict[str, Any], bytes]:
    payload, raw = load_json_file(BUDGET_PATH, "query grinding budget")
    if sha256(raw) != EXPECTED_BUDGET_SHA256:
        raise AttemptDomainBindingGateError("budget digest drift")
    if payload.get("payload_commitment") != EXPECTED_BUDGET_COMMITMENT:
        raise AttemptDomainBindingGateError("budget commitment drift")
    try:
        budget_gate.validate_payload(payload)
        if budget_gate.build_payload() != payload:
            raise AttemptDomainBindingGateError("budget rebuild drift")
    except budget_gate.StwoQueryGrindingBudgetGateError as err:
        raise AttemptDomainBindingGateError(f"budget invalid: {err}") from err
    return payload, raw


def source_artifacts(builder_payload: dict[str, Any], budget_payload: dict[str, Any], raws: dict[str, bytes]) -> list[dict[str, Any]]:
    return [
        {
            "id": "generated_proof_object_builder",
            "path": BUILDER_PATH.relative_to(ROOT).as_posix(),
            "sha256": sha256(raws["builder"]),
            "payload_commitment": builder_payload["payload_commitment"],
            "schema": builder_payload["schema"],
            "decision": builder_payload["decision"],
        },
        {
            "id": "query_grinding_budget",
            "path": BUDGET_PATH.relative_to(ROOT).as_posix(),
            "sha256": sha256(raws["budget"]),
            "payload_commitment": budget_payload["payload_commitment"],
            "schema": budget_payload["schema"],
            "decision": budget_payload["decision"],
        },
    ]


def proof_row_by_id(builder_payload: dict[str, Any], variant_id: str) -> dict[str, Any]:
    matches = [
        row
        for row in _list(builder_payload.get("proof_object_rows"), "proof object rows")
        if _dict(row, "proof object row").get("variant_id") == variant_id
    ]
    if len(matches) != 1:
        raise AttemptDomainBindingGateError(f"proof row missing: {variant_id}")
    return _dict(matches[0], "proof object row")


def policy_row_by_id(budget_payload: dict[str, Any], policy_id: str) -> dict[str, Any]:
    try:
        return budget_gate.policy_row(budget_payload, policy_id)
    except budget_gate.StwoQueryGrindingBudgetGateError as err:
        raise AttemptDomainBindingGateError(str(err)) from err


def build_verifier_envelope(builder_payload: dict[str, Any], budget_payload: dict[str, Any]) -> dict[str, Any]:
    selected = proof_row_by_id(builder_payload, SELECTED_ATTEMPT_ID)
    for attempt_id in ATTEMPT_DOMAIN:
        row = proof_row_by_id(builder_payload, attempt_id)
        if row["policy_status"] != "supported_label":
            raise AttemptDomainBindingGateError("attempt domain drift")
    rejected = proof_row_by_id(builder_payload, REJECTED_ATTEMPT_ID)
    if rejected["policy_status"] == "supported_label":
        raise AttemptDomainBindingGateError("attempt domain drift")
    policy = policy_row_by_id(budget_payload, "two_probe_budget_2")
    if tuple(ATTEMPT_DOMAIN) != ("adjacent_label_probe_a", "adjacent_label_probe_b"):
        raise AttemptDomainBindingGateError("attempt domain drift")
    if policy["attempt_budget"] != ATTEMPT_BUDGET or policy["best_variant_id"] != SELECTED_ATTEMPT_ID:
        raise AttemptDomainBindingGateError("attempt budget drift")
    if policy["security_loss_bits"] != SECURITY_LOSS_BITS:
        raise AttemptDomainBindingGateError("security loss drift")
    if selected["typed_bytes"] != SELECTED_TYPED_BYTES or selected["proof_json_bytes"] != SELECTED_JSON_BYTES:
        raise AttemptDomainBindingGateError("selected proof artifact drift")
    return {
        "envelope_version": "ptvm-zkai-stwo-attempt-domain-envelope-v1",
        "verifier_domain": selected["verifier_domain"],
        "target_id": selected["target_id"],
        "proof_backend": selected["proof_backend"],
        "proof_backend_version": selected["proof_backend_version"],
        "statement_version": selected["statement_version"],
        "proof_schema_version": selected["proof_schema_version"],
        "attempt_domain": list(ATTEMPT_DOMAIN),
        "attempt_budget": ATTEMPT_BUDGET,
        "selected_attempt_id": SELECTED_ATTEMPT_ID,
        "selected_attempt_index": list(ATTEMPT_DOMAIN).index(SELECTED_ATTEMPT_ID),
        "security_loss_bits": SECURITY_LOSS_BITS,
        "security_loss_formula": "log2(attempt_budget)",
        "verifier_rejects_attempts_outside_domain": True,
        "unbounded_retry_allowed": False,
        "policy_inputs": {
            "attempt_domain": True,
            "selected_attempt_id": True,
            "security_loss_bits": True,
            "final_envelope_json": False,
            "final_proof_bytes": False,
            "post_decommitment_accounting": False,
            "unbounded_retry_count": False,
        },
        "bound_source_commitments": {
            "generated_proof_object_builder_payload_commitment": builder_payload["payload_commitment"],
            "query_grinding_budget_payload_commitment": budget_payload["payload_commitment"],
            "generated_proof_object_builder_sha256": EXPECTED_BUILDER_SHA256,
            "query_grinding_budget_sha256": EXPECTED_BUDGET_SHA256,
        },
        "bound_proof_artifact": {
            "variant_id": selected["variant_id"],
            "adapter_mode": selected["adapter_mode"],
            "policy_status": selected["policy_status"],
            "path": selected["path"],
            "accounting_path": selected["accounting_path"],
            "typed_bytes": selected["typed_bytes"],
            "typed_saving_vs_single_proof_champion": SELECTED_SAVING_VS_SINGLE_PROOF_CHAMPION,
            "typed_saving_vs_matched_two_proof_frontier": SELECTED_SAVING_VS_MATCHED_FRONTIER,
            "proof_json_bytes": selected["proof_json_bytes"],
            "path_opening_bytes": selected["path_opening_bytes"],
            "value_bytes": selected["value_bytes"],
            "envelope_sha256": selected["envelope_sha256"],
            "proof_sha256": selected["proof_sha256"],
            "input_sha256": selected["input_sha256"],
            "record_stream_sha256": selected["record_stream_sha256"],
        },
    }


def binding_summary(envelope: dict[str, Any]) -> dict[str, Any]:
    proof = envelope["bound_proof_artifact"]
    return {
        "outer_envelope_binds_attempt_domain": True,
        "outer_envelope_binds_selected_attempt_id": True,
        "outer_envelope_binds_selected_proof_hashes": True,
        "inner_stwo_transcript_binds_attempt_domain": False,
        "inner_stwo_transcript_binds_selected_attempt_id": False,
        "proof_object_regenerated": False,
        "new_frontier_claimed": False,
        "selected_attempt_id": envelope["selected_attempt_id"],
        "selected_typed_bytes": proof["typed_bytes"],
        "selected_json_bytes": proof["proof_json_bytes"],
        "attempt_budget": envelope["attempt_budget"],
        "security_loss_bits": envelope["security_loss_bits"],
        "saving_vs_current_single_proof_champion_typed_bytes": SELECTED_SAVING_VS_SINGLE_PROOF_CHAMPION,
        "saving_vs_matched_two_proof_frontier_typed_bytes": SELECTED_SAVING_VS_MATCHED_FRONTIER,
        "result_status": "GO_OUTER_ENVELOPE_BINDING_NEEDS_REGENERATED_INNER_METADATA_NEXT",
    }


def build_core_payload() -> dict[str, Any]:
    builder_payload, builder_raw = load_builder_payload()
    budget_payload, budget_raw = load_budget_payload()
    envelope = build_verifier_envelope(builder_payload, budget_payload)
    return {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "issue_hint": ISSUE_HINT,
        "source_artifacts": source_artifacts(builder_payload, budget_payload, {"builder": builder_raw, "budget": budget_raw}),
        "verifier_facing_attempt_envelope": envelope,
        "binding_summary": binding_summary(envelope),
        "interpretation": copy.deepcopy(EXPECTED_INTERPRETATION),
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }


@functools.lru_cache(maxsize=1)
def expected_core_payload() -> dict[str, Any]:
    return build_core_payload()


def build_payload() -> dict[str, Any]:
    payload = build_core_payload()
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
        except AttemptDomainBindingGateError as err:
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
        ("claim_boundary_overclaim", lambda item: item.update({"claim_boundary": item["claim_boundary"] + ";NANOZK_WIN"})),
        ("builder_digest_drift", lambda item: item["source_artifacts"][0].update({"sha256": "0" * 64})),
        ("builder_commitment_drift", lambda item: item["source_artifacts"][0].update({"payload_commitment": "blake2b-256:" + "0" * 64})),
        ("budget_digest_drift", lambda item: item["source_artifacts"][1].update({"sha256": "1" * 64})),
        ("budget_commitment_drift", lambda item: item["source_artifacts"][1].update({"payload_commitment": "blake2b-256:" + "1" * 64})),
        ("attempt_domain_removed", lambda item: item["verifier_facing_attempt_envelope"]["attempt_domain"].pop()),
        ("attempt_domain_reordered", lambda item: item["verifier_facing_attempt_envelope"].update({"attempt_domain": list(reversed(ATTEMPT_DOMAIN))})),
        ("selected_attempt_changed", lambda item: item["verifier_facing_attempt_envelope"].update({"selected_attempt_id": "adjacent_label_probe_a"})),
        ("selected_attempt_outside_domain", lambda item: item["verifier_facing_attempt_envelope"].update({"selected_attempt_id": "outside"})),
        ("attempt_budget_drift", lambda item: item["verifier_facing_attempt_envelope"].update({"attempt_budget": 3})),
        ("security_loss_understated", lambda item: item["verifier_facing_attempt_envelope"].update({"security_loss_bits": "0.000000"})),
        ("unbounded_retry_allowed", lambda item: item["verifier_facing_attempt_envelope"].update({"unbounded_retry_allowed": True})),
        ("final_proof_bytes_allowed", lambda item: item["verifier_facing_attempt_envelope"]["policy_inputs"].update({"final_proof_bytes": True})),
        ("post_decommitment_accounting_allowed", lambda item: item["verifier_facing_attempt_envelope"]["policy_inputs"].update({"post_decommitment_accounting": True})),
        ("outer_envelope_binding_removed", lambda item: item["binding_summary"].update({"outer_envelope_binds_attempt_domain": False})),
        ("inner_transcript_overclaim", lambda item: item["binding_summary"].update({"inner_stwo_transcript_binds_attempt_domain": True})),
        ("selected_proof_hash_drift", lambda item: item["verifier_facing_attempt_envelope"]["bound_proof_artifact"].update({"proof_sha256": "2" * 64})),
        ("selected_typed_bytes_drift", lambda item: item["verifier_facing_attempt_envelope"]["bound_proof_artifact"].update({"typed_bytes": SELECTED_TYPED_BYTES + 1})),
        ("new_frontier_overclaim", lambda item: item["binding_summary"].update({"new_frontier_claimed": True})),
        ("nanozk_overclaim", lambda item: item.update({"claim_boundary": item["claim_boundary"] + ";NANOZK_WIN"})),
        ("validation_command_drift", lambda item: item["validation_commands"].append("echo untracked")),
        ("removed_non_claim", lambda item: item["non_claims"].remove("not a NANOZK proof-size comparison")),
        ("payload_commitment_drift", lambda item: item.update({"payload_commitment": "blake2b-256:" + "0" * 64})),
    )


def validate_payload(payload: dict[str, Any]) -> None:
    _require_exact_keys(payload, PAYLOAD_KEYS, "payload")
    for key, expected in {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "issue_hint": ISSUE_HINT,
    }.items():
        if payload.get(key) != expected:
            raise AttemptDomainBindingGateError(f"{key} drift")
    if "NANOZK_WIN" in str(payload.get("claim_boundary")).split(";"):
        raise AttemptDomainBindingGateError("claim_boundary drift")
    expected = expected_core_payload()
    validate_source_artifacts(_list(payload.get("source_artifacts"), "source artifacts"), expected["source_artifacts"])
    validate_verifier_envelope(
        _dict(payload.get("verifier_facing_attempt_envelope"), "verifier-facing attempt envelope"),
        expected["verifier_facing_attempt_envelope"],
    )
    validate_binding_summary(_dict(payload.get("binding_summary"), "binding summary"), expected["binding_summary"])
    if payload.get("interpretation") != EXPECTED_INTERPRETATION:
        raise AttemptDomainBindingGateError("interpretation drift")
    if payload.get("non_claims") != list(NON_CLAIMS):
        raise AttemptDomainBindingGateError("non_claims drift")
    if payload.get("validation_commands") != list(VALIDATION_COMMANDS):
        raise AttemptDomainBindingGateError("validation command drift")
    validate_mutation_result(_dict(payload.get("mutation_result"), "mutation result"))
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise AttemptDomainBindingGateError("payload commitment drift")
    if EXPECTED_PAYLOAD_COMMITMENT and payload.get("payload_commitment") != EXPECTED_PAYLOAD_COMMITMENT:
        raise AttemptDomainBindingGateError("published payload commitment drift")


def validate_source_artifacts(artifacts: list[Any], expected: list[dict[str, Any]]) -> None:
    for item in artifacts:
        _require_exact_keys(_dict(item, "source artifact"), SOURCE_ARTIFACT_KEYS, "source artifact")
    if artifacts != expected:
        raise AttemptDomainBindingGateError("source artifact drift")


def validate_verifier_envelope(envelope: dict[str, Any], expected: dict[str, Any]) -> None:
    _require_exact_keys(envelope, ENVELOPE_KEYS, "verifier-facing attempt envelope")
    if envelope.get("attempt_domain") != list(ATTEMPT_DOMAIN):
        raise AttemptDomainBindingGateError("attempt domain drift")
    if envelope.get("selected_attempt_id") != SELECTED_ATTEMPT_ID or envelope.get("selected_attempt_id") not in envelope["attempt_domain"]:
        raise AttemptDomainBindingGateError("selected attempt drift")
    if envelope.get("attempt_budget") != ATTEMPT_BUDGET or envelope.get("attempt_budget") != len(envelope["attempt_domain"]):
        raise AttemptDomainBindingGateError("attempt budget drift")
    if envelope.get("security_loss_bits") != SECURITY_LOSS_BITS:
        raise AttemptDomainBindingGateError("security loss drift")
    if envelope.get("unbounded_retry_allowed") is not False:
        raise AttemptDomainBindingGateError("unbounded retry drift")
    if envelope.get("verifier_rejects_attempts_outside_domain") is not True:
        raise AttemptDomainBindingGateError("attempt domain drift")
    validate_policy_inputs(_dict(envelope.get("policy_inputs"), "policy inputs"))
    validate_bound_sources(_dict(envelope.get("bound_source_commitments"), "bound source commitments"))
    validate_bound_proof(
        _dict(envelope.get("bound_proof_artifact"), "bound proof artifact"),
        expected["bound_proof_artifact"],
    )
    if envelope != expected:
        raise AttemptDomainBindingGateError("verifier envelope drift")


def validate_policy_inputs(inputs: dict[str, Any]) -> None:
    _require_exact_keys(inputs, POLICY_INPUT_KEYS, "policy inputs")
    for key in ("attempt_domain", "selected_attempt_id", "security_loss_bits"):
        if inputs.get(key) is not True:
            raise AttemptDomainBindingGateError("policy input drift")
    for key in ("final_envelope_json", "final_proof_bytes", "post_decommitment_accounting", "unbounded_retry_count"):
        if inputs.get(key) is not False:
            raise AttemptDomainBindingGateError("policy input drift")


def validate_bound_sources(sources: dict[str, Any]) -> None:
    _require_exact_keys(sources, BOUND_SOURCE_KEYS, "bound source commitments")
    if sources != {
        "generated_proof_object_builder_payload_commitment": EXPECTED_BUILDER_COMMITMENT,
        "query_grinding_budget_payload_commitment": EXPECTED_BUDGET_COMMITMENT,
        "generated_proof_object_builder_sha256": EXPECTED_BUILDER_SHA256,
        "query_grinding_budget_sha256": EXPECTED_BUDGET_SHA256,
    }:
        raise AttemptDomainBindingGateError("source artifact drift")


def validate_bound_proof(proof: dict[str, Any], expected: dict[str, Any]) -> None:
    _require_exact_keys(proof, BOUND_PROOF_KEYS, "bound proof artifact")
    if proof.get("variant_id") != SELECTED_ATTEMPT_ID or proof.get("policy_status") != "supported_label":
        raise AttemptDomainBindingGateError("selected proof artifact drift")
    if proof.get("typed_bytes") != SELECTED_TYPED_BYTES or proof.get("proof_json_bytes") != SELECTED_JSON_BYTES:
        raise AttemptDomainBindingGateError("selected proof artifact drift")
    if proof.get("typed_saving_vs_single_proof_champion") != SELECTED_SAVING_VS_SINGLE_PROOF_CHAMPION:
        raise AttemptDomainBindingGateError("selected proof artifact drift")
    if proof.get("typed_saving_vs_matched_two_proof_frontier") != SELECTED_SAVING_VS_MATCHED_FRONTIER:
        raise AttemptDomainBindingGateError("selected proof artifact drift")
    if proof != expected:
        raise AttemptDomainBindingGateError("selected proof artifact drift")


def validate_binding_summary(summary: dict[str, Any], expected: dict[str, Any]) -> None:
    _require_exact_keys(summary, SUMMARY_KEYS, "binding summary")
    if summary.get("outer_envelope_binds_attempt_domain") is not True:
        raise AttemptDomainBindingGateError("outer envelope binding drift")
    if summary.get("outer_envelope_binds_selected_attempt_id") is not True:
        raise AttemptDomainBindingGateError("outer envelope binding drift")
    if summary.get("inner_stwo_transcript_binds_attempt_domain") is not False:
        raise AttemptDomainBindingGateError("inner transcript binding drift")
    if summary.get("inner_stwo_transcript_binds_selected_attempt_id") is not False:
        raise AttemptDomainBindingGateError("inner transcript binding drift")
    if summary.get("proof_object_regenerated") is not False or summary.get("new_frontier_claimed") is not False:
        raise AttemptDomainBindingGateError("binding summary drift")
    if summary != expected:
        raise AttemptDomainBindingGateError("binding summary drift")


def validate_mutation_result(result: dict[str, Any]) -> None:
    _require_exact_keys(result, MUTATION_RESULT_KEYS, "mutation result")
    cases = _list(result.get("cases"), "mutation cases")
    for case in cases:
        _require_exact_keys(_dict(case, "mutation case"), MUTATION_CASE_KEYS, "mutation case")
    if result != expected_mutation_result():
        raise AttemptDomainBindingGateError("mutation result drift")


def _tsv_cell(value: Any) -> str:
    text = ",".join(value) if isinstance(value, list) else str(value)
    if "\t" in text or "\n" in text or "\r" in text:
        raise AttemptDomainBindingGateError("tsv field contains unsafe whitespace")
    return text


def render_tsv(payload: dict[str, Any]) -> str:
    validate_payload(payload)
    envelope = payload["verifier_facing_attempt_envelope"]
    proof = envelope["bound_proof_artifact"]
    summary = payload["binding_summary"]
    mutation_cases = payload["mutation_result"]["cases"]
    row = {
        "selected_attempt_id": envelope["selected_attempt_id"],
        "attempt_domain": envelope["attempt_domain"],
        "attempt_budget": envelope["attempt_budget"],
        "security_loss_bits": envelope["security_loss_bits"],
        "typed_bytes": proof["typed_bytes"],
        "proof_json_bytes": proof["proof_json_bytes"],
        "saving_vs_current_single_proof_champion_typed_bytes": summary["saving_vs_current_single_proof_champion_typed_bytes"],
        "saving_vs_matched_two_proof_frontier_typed_bytes": summary["saving_vs_matched_two_proof_frontier_typed_bytes"],
        "outer_envelope_binds_attempt_domain": summary["outer_envelope_binds_attempt_domain"],
        "inner_stwo_transcript_binds_attempt_domain": summary["inner_stwo_transcript_binds_attempt_domain"],
        "new_frontier_claimed": summary["new_frontier_claimed"],
        "builder_payload_commitment": envelope["bound_source_commitments"]["generated_proof_object_builder_payload_commitment"],
        "budget_payload_commitment": envelope["bound_source_commitments"]["query_grinding_budget_payload_commitment"],
        "selected_envelope_sha256": proof["envelope_sha256"],
        "selected_proof_sha256": proof["proof_sha256"],
        "payload_commitment": payload["payload_commitment"],
        "mutation_outcomes": ",".join(
            f"{case['name']}={'rejected' if case['rejected'] else 'accepted'}:{case['error']}"
            for case in mutation_cases
        ),
    }
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerow({key: _tsv_cell(row[key]) for key in TSV_COLUMNS})
    return output.getvalue()


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path | None, tsv_path: pathlib.Path | None) -> None:
    validate_payload(payload)
    if (json_path is None) != (tsv_path is None):
        raise AttemptDomainBindingGateError("paired JSON/TSV output paths required")
    outputs = []
    if json_path is not None:
        outputs.append((json_path, json.dumps(payload, indent=2, sort_keys=True) + "\n"))
    if tsv_path is not None:
        outputs.append((tsv_path, render_tsv(payload)))
    builder_gate.publish_outputs_atomically(outputs)


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
                "selected_attempt_id": payload["binding_summary"]["selected_attempt_id"],
                "selected_typed_bytes": payload["binding_summary"]["selected_typed_bytes"],
                "security_loss_bits": payload["binding_summary"]["security_loss_bits"],
                "mutations_rejected": payload["mutation_result"]["mutations_rejected"],
                "json_out": str(args.write_json) if args.write_json else None,
                "tsv_out": str(args.write_tsv) if args.write_tsv else None,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except (AttemptDomainBindingGateError, builder_gate.GeneratedProofObjectBuilderGateError, budget_gate.StwoQueryGrindingBudgetGateError) as err:
        print(f"attempt-domain binding gate failed: {err}", file=sys.stderr)
        raise SystemExit(2) from err
