#!/usr/bin/env python3.10
"""Gate native Stwo statement binding for seq32+d128 attempt-domain proofs."""

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
    raise RuntimeError("zkai_stwo_inner_attempt_domain_statement_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
RUST_SOURCE_PATH = ROOT / "src" / "stwo_backend" / "native_seq32_attention_mlp_single_proof.rs"
CLI_SOURCE_PATH = ROOT / "src" / "bin" / "zkai_native_seq32_attention_mlp_single_proof.rs"
ACCOUNTING_PATH = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-inner-attempt-domain-accounting-2026-05.json"
JSON_OUT = EVIDENCE_DIR / "zkai-stwo-inner-attempt-domain-statement-gate-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-stwo-inner-attempt-domain-statement-gate-2026-05.tsv"

SCHEMA = "zkai-stwo-inner-attempt-domain-statement-gate-v1"
DECISION = "GO_REGENERATED_SEQ32_D128_STWO_PROOFS_BIND_ATTEMPT_DOMAIN_INSIDE_NATIVE_STATEMENT"
RESULT = "POLICY_BOUND_PROBE_B_VERIFIES_AT_40892_TYPED_BYTES_WITH_EXPLICIT_COST_VS_LEGACY_WRAPPER_ROW"
CLAIM_BOUNDARY = (
    "REGENERATED_NATIVE_STWO_SEQ32_D128_ADJACENT_PROBE_A_B_PROOFS;"
    "ATTEMPT_DOMAIN_SELECTED_ATTEMPT_AND_ONE_BIT_LOSS_ARE_STATEMENT_AND_TRANSCRIPT_INPUTS;"
    "NOT_A_NEW_PROOF_SIZE_FRONTIER_NOT_A_NANOZK_WIN_NOT_A_FULL_TRANSFORMER_BLOCK"
)
ISSUE_HINT = "https://github.com/omarespejel/provable-transformer-vm/issues/710"
PAYLOAD_DOMAIN = "ptvm:zkai:stwo-inner-attempt-domain-statement:v1"

EXPECTED_RUST_SOURCE_SHA256 = "05f1d76f3cb39cb9db676f9083060f61c61d43f1ab0e7d539c3b16f9d7767839"
EXPECTED_CLI_SOURCE_SHA256 = "ea68996b62dd763255e20479672bf7a392494a710c87eb2c0da84482873b4b52"
EXPECTED_ACCOUNTING_SHA256 = "72cad6f598af282215f6579a716816a52e259248a420e27c5759d45482055978"
EXPECTED_PAYLOAD_COMMITMENT = "blake2b-256:24b7220e4387adfa9c4cba6e06a99d0d1e25e8642470c827d15e837bbbe20323"

ATTEMPT_DOMAIN = ("adjacent_label_probe_a", "adjacent_label_probe_b")
ATTEMPT_POLICY_VERSION = "seq32-d128-adjacent-attempt-domain-v1"
ATTEMPT_POLICY_STAGE = "inner_statement_transcript_metadata"
ATTEMPT_BUDGET = 2
SECURITY_LOSS_BITS = "1.000000"
SECURITY_LOSS_FORMULA = "log2(2)"
LEGACY_WRAPPER_B_TYPED_BYTES = 37_532
LEGACY_WRAPPER_B_JSON_BYTES = 106_317
CURRENT_SINGLE_PROOF_CHAMPION_TYPED_BYTES = 42_068
MATCHED_TWO_PROOF_FRONTIER_TYPED_BYTES = 47_188
MATCHED_TWO_PROOF_FRONTIER_JSON_BYTES = 140_838
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900

ATTEMPT_ARTIFACTS = (
    {
        "variant_id": "adjacent_label_probe_a",
        "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_a_v1",
        "selected_attempt_id": "adjacent_label_probe_a",
        "selected_attempt_index": 0,
        "input_path": EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-inner-attempt-2026-05.input.json",
        "envelope_path": EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-inner-attempt-2026-05.envelope.json",
    },
    {
        "variant_id": "adjacent_label_probe_b",
        "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_b_v1",
        "selected_attempt_id": "adjacent_label_probe_b",
        "selected_attempt_index": 1,
        "input_path": EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-inner-attempt-2026-05.input.json",
        "envelope_path": EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-inner-attempt-2026-05.envelope.json",
    },
)

EXPECTED_ATTEMPT_NON_CLAIMS = (
    "not unbounded retry",
    "not post-decommitment selection",
    "not final proof-byte selection",
    "not absolute soundness",
    "not a NANOZK proof-size comparison",
)
NON_CLAIMS = (
    "not a new proof-size frontier beyond the existing 37,532 typed-byte legacy wrapper row",
    "not a NANOZK proof-size comparison",
    "not a matched external zkML benchmark",
    "not a full transformer block proof",
    "not exact real-valued Softmax",
    "not timing evidence",
    "not production-ready zkML",
)
VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent-label-probe-a docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-inner-attempt-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-inner-attempt-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-inner-attempt-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-inner-attempt-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent-label-probe-b docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-inner-attempt-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-inner-attempt-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-inner-attempt-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-inner-attempt-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-inner-attempt-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-inner-attempt-2026-05.envelope.json > docs/engineering/evidence/zkai-native-seq32-attention-mlp-inner-attempt-domain-accounting-2026-05.json",
    "python3.10 scripts/zkai_stwo_inner_attempt_domain_statement_gate.py --write-json docs/engineering/evidence/zkai-stwo-inner-attempt-domain-statement-gate-2026-05.json --write-tsv docs/engineering/evidence/zkai-stwo-inner-attempt-domain-statement-gate-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_stwo_inner_attempt_domain_statement_gate.py scripts/tests/test_zkai_stwo_inner_attempt_domain_statement_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_stwo_inner_attempt_domain_statement_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_adjacent_label_probe --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

PAYLOAD_KEYS = {
    "schema",
    "decision",
    "result",
    "claim_boundary",
    "issue_hint",
    "source_artifacts",
    "attempt_rows",
    "binding_summary",
    "interpretation",
    "non_claims",
    "validation_commands",
    "mutation_result",
    "payload_commitment",
}
ATTEMPT_ROW_KEYS = {
    "variant_id",
    "adapter_mode",
    "input_path",
    "envelope_path",
    "input_sha256",
    "envelope_sha256",
    "proof_sha256",
    "statement_commitment",
    "public_instance_commitment",
    "attempt_policy",
    "proof_json_bytes",
    "typed_bytes",
    "typed_cost_vs_legacy_wrapper_b",
    "typed_saving_vs_single_proof_champion",
    "typed_saving_vs_matched_two_proof_frontier",
    "json_cost_vs_legacy_wrapper_b",
    "json_saving_vs_matched_two_proof_frontier",
    "record_stream_sha256",
    "proof_backend_version",
}
SUMMARY_KEYS = {
    "inner_stwo_statement_binds_attempt_domain",
    "inner_stwo_transcript_binds_attempt_domain",
    "legacy_wrapper_row_still_verifies",
    "proof_object_regenerated",
    "new_frontier_claimed",
    "best_inner_attempt_id",
    "best_inner_attempt_typed_bytes",
    "best_inner_attempt_json_bytes",
    "typed_cost_vs_legacy_wrapper_b",
    "typed_saving_vs_single_proof_champion",
    "typed_saving_vs_matched_two_proof_frontier",
    "json_cost_vs_legacy_wrapper_b",
    "json_saving_vs_matched_two_proof_frontier",
    "nanozk_comparable_external_rows",
    "nanozk_gap_typed_bytes",
    "result_status",
}
MUTATION_NAMES = (
    "decision_drift",
    "claim_boundary_overclaim",
    "rust_source_digest_drift",
    "accounting_digest_drift",
    "attempt_domain_reordered",
    "selected_attempt_changed",
    "selected_attempt_index_drift",
    "attempt_budget_drift",
    "security_loss_understated",
    "attempt_policy_removed",
    "typed_bytes_drift",
    "legacy_cost_erased",
    "single_champion_saving_drift",
    "new_frontier_overclaim",
    "nanozk_overclaim",
    "validation_command_drift",
    "removed_non_claim",
    "payload_commitment_drift",
)
EXPECTED_MUTATION_ERRORS = {name: name.replace("_", " ") for name in MUTATION_NAMES}
EXPECTED_MUTATION_ERRORS.update(
    {
        "decision_drift": "decision drift",
        "claim_boundary_overclaim": "claim_boundary drift",
        "rust_source_digest_drift": "source artifact drift",
        "accounting_digest_drift": "source artifact drift",
        "attempt_domain_reordered": "attempt row drift",
        "selected_attempt_changed": "attempt row drift",
        "selected_attempt_index_drift": "attempt row drift",
        "attempt_budget_drift": "attempt row drift",
        "security_loss_understated": "attempt row drift",
        "attempt_policy_removed": "attempt row field drift: missing attempt_policy",
        "typed_bytes_drift": "attempt row drift",
        "legacy_cost_erased": "binding summary drift",
        "single_champion_saving_drift": "binding summary drift",
        "new_frontier_overclaim": "binding summary drift",
        "nanozk_overclaim": "claim_boundary drift",
        "validation_command_drift": "validation command drift",
        "removed_non_claim": "non_claims drift",
        "payload_commitment_drift": "payload commitment drift",
    }
)
TSV_COLUMNS = (
    "best_inner_attempt_id",
    "typed_bytes",
    "proof_json_bytes",
    "typed_cost_vs_legacy_wrapper_b",
    "typed_saving_vs_single_proof_champion",
    "typed_saving_vs_matched_two_proof_frontier",
    "json_cost_vs_legacy_wrapper_b",
    "json_saving_vs_matched_two_proof_frontier",
    "inner_stwo_statement_binds_attempt_domain",
    "inner_stwo_transcript_binds_attempt_domain",
    "new_frontier_claimed",
    "payload_commitment",
    "mutation_outcomes",
)


class InnerAttemptDomainStatementGateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as err:
        raise InnerAttemptDomainStatementGateError(f"invalid JSON value: {err}") from err


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
        raise InnerAttemptDomainStatementGateError(f"{label} must be object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise InnerAttemptDomainStatementGateError(f"{label} must be list")
    return value


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual == expected:
        return
    unexpected = sorted(actual - expected)
    missing = sorted(expected - actual)
    if unexpected:
        raise InnerAttemptDomainStatementGateError(f"{label} field drift: unexpected {unexpected[0]}")
    raise InnerAttemptDomainStatementGateError(f"{label} field drift: missing {missing[0]}")


def read_repo_file(path: pathlib.Path, label: str) -> bytes:
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(ROOT.resolve())
    except (OSError, ValueError) as err:
        raise InnerAttemptDomainStatementGateError(f"{label} path escapes repo") from err
    if not resolved.is_file() or resolved.is_symlink():
        raise InnerAttemptDomainStatementGateError(f"{label} must be a regular file")
    return resolved.read_bytes()


def load_json_file(path: pathlib.Path, label: str) -> tuple[dict[str, Any], bytes]:
    raw = read_repo_file(path, label)
    try:
        return _dict(json.loads(raw), label), raw
    except json.JSONDecodeError as err:
        raise InnerAttemptDomainStatementGateError(f"{label} must be JSON: {err}") from err


def source_artifact(path: pathlib.Path, artifact_id: str, expected_sha: str) -> dict[str, Any]:
    raw = read_repo_file(path, artifact_id)
    actual_sha = sha256(raw)
    if actual_sha != expected_sha:
        raise InnerAttemptDomainStatementGateError("source artifact drift")
    return {
        "id": artifact_id,
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": actual_sha,
        "size_bytes": len(raw),
    }


def proof_bytes_from_envelope(envelope: dict[str, Any]) -> bytes:
    proof = _list(envelope.get("proof"), "envelope proof")
    if not all(isinstance(item, int) and not isinstance(item, bool) and 0 <= item <= 255 for item in proof):
        raise InnerAttemptDomainStatementGateError("envelope proof must be byte array")
    return bytes(proof)


def expected_attempt_policy(selected_attempt_id: str, selected_attempt_index: int) -> dict[str, Any]:
    return {
        "policy_version": ATTEMPT_POLICY_VERSION,
        "policy_stage": ATTEMPT_POLICY_STAGE,
        "attempt_domain": list(ATTEMPT_DOMAIN),
        "selected_attempt_id": selected_attempt_id,
        "selected_attempt_index": selected_attempt_index,
        "attempt_budget": ATTEMPT_BUDGET,
        "security_loss_bits": SECURITY_LOSS_BITS,
        "security_loss_formula": SECURITY_LOSS_FORMULA,
        "non_claims": list(EXPECTED_ATTEMPT_NON_CLAIMS),
    }


def accounting_rows_by_path(accounting: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = {}
    for item in _list(accounting.get("rows"), "accounting rows"):
        row = _dict(item, "accounting row")
        key = row.get("evidence_relative_path")
        if not isinstance(key, str) or not key:
            raise InnerAttemptDomainStatementGateError("accounting path drift")
        if key in rows:
            raise InnerAttemptDomainStatementGateError("accounting duplicate path")
        rows[key] = row
    return rows


def build_attempt_row(spec: dict[str, Any], accounting_row: dict[str, Any]) -> dict[str, Any]:
    input_payload, input_raw = load_json_file(spec["input_path"], f"{spec['variant_id']} input")
    envelope, envelope_raw = load_json_file(spec["envelope_path"], f"{spec['variant_id']} envelope")
    envelope_input = _dict(envelope.get("input"), "envelope input")
    if envelope_input != input_payload:
        raise InnerAttemptDomainStatementGateError("envelope input drift")
    policy = _dict(input_payload.get("attempt_policy"), "attempt policy")
    expected_policy = expected_attempt_policy(spec["selected_attempt_id"], spec["selected_attempt_index"])
    if policy != expected_policy:
        raise InnerAttemptDomainStatementGateError("attempt row drift")
    if input_payload.get("adapter_mode") != spec["adapter_mode"]:
        raise InnerAttemptDomainStatementGateError("attempt row drift")
    if input_payload.get("statement_commitment") != envelope_input.get("statement_commitment"):
        raise InnerAttemptDomainStatementGateError("attempt row drift")
    proof_bytes = proof_bytes_from_envelope(envelope)
    local = _dict(accounting_row.get("local_binary_accounting"), "local binary accounting")
    typed_bytes = local.get("typed_size_estimate_bytes")
    if typed_bytes != local.get("component_sum_bytes"):
        raise InnerAttemptDomainStatementGateError("attempt row drift")
    if accounting_row.get("envelope_sha256") != sha256(envelope_raw):
        raise InnerAttemptDomainStatementGateError("attempt row drift")
    if accounting_row.get("proof_sha256") != sha256(proof_bytes):
        raise InnerAttemptDomainStatementGateError("attempt row drift")
    proof_json_bytes = accounting_row.get("proof_json_size_bytes")
    if proof_json_bytes != len(proof_bytes):
        raise InnerAttemptDomainStatementGateError("attempt row drift")
    return {
        "variant_id": spec["variant_id"],
        "adapter_mode": spec["adapter_mode"],
        "input_path": spec["input_path"].relative_to(ROOT).as_posix(),
        "envelope_path": spec["envelope_path"].relative_to(ROOT).as_posix(),
        "input_sha256": sha256(input_raw),
        "envelope_sha256": sha256(envelope_raw),
        "proof_sha256": sha256(proof_bytes),
        "statement_commitment": input_payload["statement_commitment"],
        "public_instance_commitment": input_payload["public_instance_commitment"],
        "attempt_policy": policy,
        "proof_json_bytes": proof_json_bytes,
        "typed_bytes": typed_bytes,
        "typed_cost_vs_legacy_wrapper_b": typed_bytes - LEGACY_WRAPPER_B_TYPED_BYTES,
        "typed_saving_vs_single_proof_champion": CURRENT_SINGLE_PROOF_CHAMPION_TYPED_BYTES - typed_bytes,
        "typed_saving_vs_matched_two_proof_frontier": MATCHED_TWO_PROOF_FRONTIER_TYPED_BYTES - typed_bytes,
        "json_cost_vs_legacy_wrapper_b": proof_json_bytes - LEGACY_WRAPPER_B_JSON_BYTES,
        "json_saving_vs_matched_two_proof_frontier": MATCHED_TWO_PROOF_FRONTIER_JSON_BYTES - proof_json_bytes,
        "record_stream_sha256": local["record_stream_sha256"],
        "proof_backend_version": envelope["proof_backend_version"],
    }


def build_attempt_rows() -> list[dict[str, Any]]:
    accounting, accounting_raw = load_json_file(ACCOUNTING_PATH, "inner attempt accounting")
    if sha256(accounting_raw) != EXPECTED_ACCOUNTING_SHA256:
        raise InnerAttemptDomainStatementGateError("source artifact drift")
    rows_by_path = accounting_rows_by_path(accounting)
    rows = []
    for spec in ATTEMPT_ARTIFACTS:
        key = spec["envelope_path"].name
        if key not in rows_by_path:
            raise InnerAttemptDomainStatementGateError("accounting path drift")
        rows.append(build_attempt_row(spec, rows_by_path[key]))
    return rows


def binding_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    best = min(rows, key=lambda row: (row["typed_bytes"], row["proof_json_bytes"]))
    return {
        "inner_stwo_statement_binds_attempt_domain": True,
        "inner_stwo_transcript_binds_attempt_domain": True,
        "legacy_wrapper_row_still_verifies": True,
        "proof_object_regenerated": True,
        "new_frontier_claimed": False,
        "best_inner_attempt_id": best["variant_id"],
        "best_inner_attempt_typed_bytes": best["typed_bytes"],
        "best_inner_attempt_json_bytes": best["proof_json_bytes"],
        "typed_cost_vs_legacy_wrapper_b": best["typed_cost_vs_legacy_wrapper_b"],
        "typed_saving_vs_single_proof_champion": best["typed_saving_vs_single_proof_champion"],
        "typed_saving_vs_matched_two_proof_frontier": best["typed_saving_vs_matched_two_proof_frontier"],
        "json_cost_vs_legacy_wrapper_b": best["json_cost_vs_legacy_wrapper_b"],
        "json_saving_vs_matched_two_proof_frontier": best["json_saving_vs_matched_two_proof_frontier"],
        "nanozk_comparable_external_rows": 0,
        "nanozk_gap_typed_bytes": best["typed_bytes"] - NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
        "result_status": "GO_CORRECTNESS_UPGRADE_WITH_3360_TYPED_BYTE_COST_VS_LEGACY_WRAPPER_ROW",
    }


def build_core_payload() -> dict[str, Any]:
    rows = build_attempt_rows()
    return {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "issue_hint": ISSUE_HINT,
        "source_artifacts": [
            source_artifact(RUST_SOURCE_PATH, "rust_native_seq32_attention_mlp_source", EXPECTED_RUST_SOURCE_SHA256),
            source_artifact(CLI_SOURCE_PATH, "cli_native_seq32_attention_mlp_source", EXPECTED_CLI_SOURCE_SHA256),
            source_artifact(ACCOUNTING_PATH, "inner_attempt_domain_accounting", EXPECTED_ACCOUNTING_SHA256),
        ],
        "attempt_rows": rows,
        "binding_summary": binding_summary(rows),
        "interpretation": {
            "human_read": (
                "The earlier B row was smaller, but its attempt-domain policy lived outside the native proof statement. "
                "These regenerated A/B proofs make the two-probe domain and selected attempt part of the native statement and transcript."
            ),
            "research_read": (
                "The correctness upgrade costs 3,360 typed bytes versus the legacy wrapper-only B row, yet the best inner-bound row still "
                "saves 1,176 typed bytes versus the 42,068 typed-byte single-proof champion and 6,296 typed bytes versus the matched two-proof frontier."
            ),
            "claim_boundary": (
                "This is a stronger statement-validity result, not a new proof-size frontier and not a NANOZK-comparable block proof."
            ),
        },
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


def mutation_functions() -> tuple[tuple[str, Callable[[dict[str, Any]], None]], ...]:
    return (
        ("decision_drift", lambda item: item.update({"decision": "NO_GO"})),
        ("claim_boundary_overclaim", lambda item: item.update({"claim_boundary": item["claim_boundary"] + ";NANOZK_WIN"})),
        ("rust_source_digest_drift", lambda item: item["source_artifacts"][0].update({"sha256": "0" * 64})),
        ("accounting_digest_drift", lambda item: item["source_artifacts"][2].update({"sha256": "1" * 64})),
        ("attempt_domain_reordered", lambda item: item["attempt_rows"][1]["attempt_policy"].update({"attempt_domain": list(reversed(ATTEMPT_DOMAIN))})),
        ("selected_attempt_changed", lambda item: item["attempt_rows"][1]["attempt_policy"].update({"selected_attempt_id": "adjacent_label_probe_a"})),
        ("selected_attempt_index_drift", lambda item: item["attempt_rows"][1]["attempt_policy"].update({"selected_attempt_index": 0})),
        ("attempt_budget_drift", lambda item: item["attempt_rows"][1]["attempt_policy"].update({"attempt_budget": 3})),
        ("security_loss_understated", lambda item: item["attempt_rows"][1]["attempt_policy"].update({"security_loss_bits": "0.000000"})),
        ("attempt_policy_removed", lambda item: item["attempt_rows"][1].pop("attempt_policy")),
        ("typed_bytes_drift", lambda item: item["attempt_rows"][1].update({"typed_bytes": 37_532})),
        ("legacy_cost_erased", lambda item: item["binding_summary"].update({"typed_cost_vs_legacy_wrapper_b": 0})),
        ("single_champion_saving_drift", lambda item: item["binding_summary"].update({"typed_saving_vs_single_proof_champion": 0})),
        ("new_frontier_overclaim", lambda item: item["binding_summary"].update({"new_frontier_claimed": True})),
        ("nanozk_overclaim", lambda item: item.update({"claim_boundary": item["claim_boundary"] + ";NANOZK_WIN"})),
        ("validation_command_drift", lambda item: item["validation_commands"].append("echo untracked")),
        ("removed_non_claim", lambda item: item["non_claims"].remove("not a NANOZK proof-size comparison")),
        ("payload_commitment_drift", lambda item: item.update({"payload_commitment": "blake2b-256:" + "0" * 64})),
    )


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
        except InnerAttemptDomainStatementGateError as err:
            cases.append({"name": name, "rejected": True, "error": str(err)})
        else:
            cases.append({"name": name, "rejected": False, "error": ""})
    return {
        "all_mutations_rejected": all(case["rejected"] for case in cases),
        "mutations_rejected": sum(1 for case in cases if case["rejected"]),
        "mutation_names": list(MUTATION_NAMES),
        "cases": cases,
    }


def expected_mutation_result() -> dict[str, Any]:
    return {
        "all_mutations_rejected": True,
        "mutations_rejected": len(MUTATION_NAMES),
        "mutation_names": list(MUTATION_NAMES),
        "cases": [
            {"name": name, "rejected": True, "error": EXPECTED_MUTATION_ERRORS[name]}
            for name in MUTATION_NAMES
        ],
    }


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
            raise InnerAttemptDomainStatementGateError(f"{key} drift")
    if "NANOZK_WIN" in str(payload.get("claim_boundary")).split(";"):
        raise InnerAttemptDomainStatementGateError("claim_boundary drift")
    expected = expected_core_payload()
    if payload.get("source_artifacts") != expected["source_artifacts"]:
        raise InnerAttemptDomainStatementGateError("source artifact drift")
    validate_attempt_rows(_list(payload.get("attempt_rows"), "attempt rows"), expected["attempt_rows"])
    validate_binding_summary(_dict(payload.get("binding_summary"), "binding summary"), expected["binding_summary"])
    if payload.get("interpretation") != expected["interpretation"]:
        raise InnerAttemptDomainStatementGateError("interpretation drift")
    if payload.get("non_claims") != list(NON_CLAIMS):
        raise InnerAttemptDomainStatementGateError("non_claims drift")
    if payload.get("validation_commands") != list(VALIDATION_COMMANDS):
        raise InnerAttemptDomainStatementGateError("validation command drift")
    validate_mutation_result(_dict(payload.get("mutation_result"), "mutation result"))
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise InnerAttemptDomainStatementGateError("payload commitment drift")
    if EXPECTED_PAYLOAD_COMMITMENT and payload.get("payload_commitment") != EXPECTED_PAYLOAD_COMMITMENT:
        raise InnerAttemptDomainStatementGateError("published payload commitment drift")


def validate_attempt_rows(rows: list[Any], expected: list[dict[str, Any]]) -> None:
    for row in rows:
        _require_exact_keys(_dict(row, "attempt row"), ATTEMPT_ROW_KEYS, "attempt row")
    if rows != expected:
        raise InnerAttemptDomainStatementGateError("attempt row drift")


def validate_binding_summary(summary: dict[str, Any], expected: dict[str, Any]) -> None:
    _require_exact_keys(summary, SUMMARY_KEYS, "binding summary")
    if summary != expected:
        raise InnerAttemptDomainStatementGateError("binding summary drift")
    if summary["new_frontier_claimed"]:
        raise InnerAttemptDomainStatementGateError("binding summary drift")
    if summary["nanozk_comparable_external_rows"] != 0:
        raise InnerAttemptDomainStatementGateError("binding summary drift")


def validate_mutation_result(result: dict[str, Any]) -> None:
    if result != expected_mutation_result():
        raise InnerAttemptDomainStatementGateError("mutation result drift")


def render_tsv(payload: dict[str, Any]) -> str:
    summary = payload["binding_summary"]
    outcomes = ",".join(
        f"{case['name']}={'rejected' if case['rejected'] else 'accepted'}:{case['error']}"
        for case in payload["mutation_result"]["cases"]
    )
    row = {
        "best_inner_attempt_id": summary["best_inner_attempt_id"],
        "typed_bytes": summary["best_inner_attempt_typed_bytes"],
        "proof_json_bytes": summary["best_inner_attempt_json_bytes"],
        "typed_cost_vs_legacy_wrapper_b": summary["typed_cost_vs_legacy_wrapper_b"],
        "typed_saving_vs_single_proof_champion": summary["typed_saving_vs_single_proof_champion"],
        "typed_saving_vs_matched_two_proof_frontier": summary["typed_saving_vs_matched_two_proof_frontier"],
        "json_cost_vs_legacy_wrapper_b": summary["json_cost_vs_legacy_wrapper_b"],
        "json_saving_vs_matched_two_proof_frontier": summary["json_saving_vs_matched_two_proof_frontier"],
        "inner_stwo_statement_binds_attempt_domain": summary["inner_stwo_statement_binds_attempt_domain"],
        "inner_stwo_transcript_binds_attempt_domain": summary["inner_stwo_transcript_binds_attempt_domain"],
        "new_frontier_claimed": summary["new_frontier_claimed"],
        "payload_commitment": payload["payload_commitment"],
        "mutation_outcomes": outcomes,
    }
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerow(row)
    return out.getvalue()


def write_text_if_requested(path: str | None, content: str) -> None:
    if not path:
        return
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json")
    parser.add_argument("--write-tsv")
    args = parser.parse_args(argv)
    payload = build_payload()
    write_text_if_requested(args.write_json, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_text_if_requested(args.write_tsv, render_tsv(payload))
    if not args.write_json and not args.write_tsv:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
