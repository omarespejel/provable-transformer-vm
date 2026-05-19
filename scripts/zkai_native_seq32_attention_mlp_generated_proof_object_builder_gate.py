#!/usr/bin/env python3.10
"""Gate source-generated proof-object rows for seq32 attention+MLP labels."""

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
    raise RuntimeError(
        "zkai_native_seq32_attention_mlp_generated_proof_object_builder_gate requires Python 3.10+"
    )

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import zkai_native_seq32_attention_mlp_generated_adjacent_label_inventory_gate as inventory_gate


EVIDENCE_DIR = inventory_gate.EVIDENCE_DIR
GENERATED_INVENTORY_PATH = inventory_gate.JSON_OUT
ACCOUNTING_PATH = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-accounting-2026-05.json"
JSON_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-generated-proof-object-builder-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-generated-proof-object-builder-2026-05.tsv"

SCHEMA = "zkai-native-seq32-attention-mlp-generated-proof-object-builder-gate-v1"
DECISION = "GO_SOURCE_GENERATED_PROOF_OBJECT_ROWS_REPRODUCE_CURRENT_ADJACENT_FRONTIER"
RESULT = "BUILDER_REPRODUCES_THREE_ADJACENT_ROWS_BEST_37532_TYPED_BYTES_AND_FIXED_LABEL_REJECTED_AT_42156"
CLAIM_BOUNDARY = (
    "SOURCE_GENERATED_BUILDER_OVER_EXISTING_STWO_SEQ32_D128_PROOF_ENVELOPES;"
    "JOINS_RUST_CLI_GENERATED_LABELS_TO_PINNED_ACCOUNTING_AND_ENVELOPES;"
    "NOT_A_NEW_PROOF_FRONTIER_NOT_A_NANOZK_WIN_NOT_FRESH_PROOF_GENERATION"
)
ISSUE_HINT = "source-generated-seq32-proof-object-builder"
PAYLOAD_DOMAIN = "ptvm:zkai:native-seq32-attention-mlp-generated-proof-object-builder:v1"

EXPECTED_GENERATED_INVENTORY_SHA256 = "10ef45339f48c41e6cd264906e8ffbcfb49e8e7bb8738ea21174ba8fbb63a1bb"
EXPECTED_GENERATED_INVENTORY_COMMITMENT = "blake2b-256:a1ad83f3dea22610a51dce6530ef699f7112fff70bda55dd7c4250f5a89d1c5f"
EXPECTED_ACCOUNTING_SHA256 = "0841dd4dbf6d3ff76ede4c3e088b301745e04f649024d50aa378fb239cd1ef5c"
EXPECTED_ACCOUNTING_SCHEMA = "zkai-stwo-local-binary-proof-accounting-cli-v1"
EXPECTED_ACCOUNTING_DOMAIN = "zkai:stwo:local-binary-proof-accounting"
EXPECTED_ACCOUNTING_SOURCE = "repo_owned_canonical_local_accounting_from_stwo_2_2_0_typed_StarkProof_fields"
EXPECTED_PROOF_PAYLOAD_KIND = "utf8_json_object_with_single_stark_proof_field"

CURRENT_CHAMPION_TYPED_BYTES = inventory_gate.CURRENT_CHAMPION_TYPED_BYTES
CURRENT_CHAMPION_PATH_OPENING_BYTES = inventory_gate.CURRENT_CHAMPION_PATH_OPENING_BYTES
BEST_GENERATED_LABEL_ID = inventory_gate.BEST_ACCEPTED_LABEL_ID
BEST_GENERATED_TYPED_BYTES = inventory_gate.BEST_ACCEPTED_TYPED_BYTES
WORST_GENERATED_ACCEPTED_LABEL_ID = inventory_gate.WORST_ACCEPTED_LABEL_ID
WORST_GENERATED_ACCEPTED_TYPED_BYTES = inventory_gate.WORST_ACCEPTED_TYPED_BYTES
FIXED_ADJACENT_LABEL_ID = inventory_gate.FIXED_ADJACENT_ID
FIXED_ADJACENT_TYPED_BYTES = inventory_gate.FULL_GENERATED_WORST_TYPED_BYTES
BEST_GENERATED_SAVING_BYTES = inventory_gate.BEST_ACCEPTED_SAVING_BYTES
WORST_ACCEPTED_SAVING_BYTES = inventory_gate.WORST_ACCEPTED_SAVING_BYTES

PATH_OPENING_GROUPS = ("fri_decommitments", "fri_samples", "trace_decommitments")
VALUE_GROUPS = ("oods_samples", "queries_values")

EXPECTED_INTERPRETATION = {
    "human_read": (
        "The source-generated label inventory is now connected to the actual proof-object files. "
        "Each adjacent label has to join to a pinned accounting row and a real envelope whose proof "
        "length, proof hash, envelope hash, and typed accounting all match."
    ),
    "mechanism_read": (
        "This does not create a new proof. It removes a manual promotion gap: a generated Rust/CLI "
        "label cannot become evidence unless the builder can reconstruct the proof-object row from "
        "the accounting artifact and the envelope bytes."
    ),
    "next_experiment": (
        "Move from builder verification over existing envelopes to source-generated proving for "
        "new query/opening-stability labels, then keep only labels that beat the 37,532 typed-byte "
        "best adjacent row without widening the statement."
    ),
}

NON_CLAIMS = (
    "not fresh proof generation",
    "not a new proof-size frontier beyond the existing 37,532 typed-byte adjacent label probe B row",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not a full transformer block proof",
    "not exact real-valued Softmax",
    "not timing evidence",
    "not production-ready zkML",
)

VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_native_seq32_attention_mlp_generated_proof_object_builder_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-proof-object-builder-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-proof-object-builder-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_generated_proof_object_builder_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_generated_proof_object_builder_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_generated_proof_object_builder_gate",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_generated_adjacent_label_inventory_gate",
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
    "claim_boundary_overclaim",
    "generated_inventory_digest_drift",
    "generated_inventory_commitment_drift",
    "accounting_digest_drift",
    "builder_manual_override_enabled",
    "generated_label_removed",
    "missing_accounting_row",
    "envelope_path_relabeling",
    "envelope_sha_drift",
    "proof_sha_drift",
    "proof_length_drift",
    "typed_accounting_drift",
    "record_stream_drift",
    "proof_backend_version_drift",
    "fixed_label_promoted",
    "best_frontier_drift",
    "validation_command_drift",
    "removed_non_claim",
    "payload_commitment_drift",
)
EXPECTED_MUTATION_ERRORS = {
    "decision_drift": "decision drift",
    "result_drift": "result drift",
    "claim_boundary_overclaim": "claim_boundary drift",
    "generated_inventory_digest_drift": "source artifact drift",
    "generated_inventory_commitment_drift": "source artifact drift",
    "accounting_digest_drift": "source artifact drift",
    "builder_manual_override_enabled": "builder policy drift",
    "generated_label_removed": "builder policy drift",
    "missing_accounting_row": "proof object row order drift",
    "envelope_path_relabeling": "proof object row drift",
    "envelope_sha_drift": "proof object row drift",
    "proof_sha_drift": "proof object row drift",
    "proof_length_drift": "proof object row drift",
    "typed_accounting_drift": "proof object row drift",
    "record_stream_drift": "proof object row drift",
    "proof_backend_version_drift": "proof object row drift",
    "fixed_label_promoted": "proof object row drift",
    "best_frontier_drift": "frontier summary drift",
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
    "builder_policy",
    "proof_object_rows",
    "frontier_summary",
    "interpretation",
    "non_claims",
    "validation_commands",
    "mutation_result",
    "payload_commitment",
}
SOURCE_ARTIFACT_KEYS = {"id", "path", "sha256", "size_bytes", "payload_commitment"}
BUILDER_POLICY_KEYS = {
    "name",
    "source_rule",
    "manual_override_allowed",
    "input_artifact_ids",
    "generated_label_ids",
    "accepted_label_ids",
    "rejected_label_ids",
    "row_join_key",
    "proof_envelope_binding",
    "promotion_rule",
}
PROOF_ROW_KEYS = {
    "variant_id",
    "adapter_mode",
    "rust_enum_variant",
    "cli_command",
    "path",
    "accounting_path",
    "proof_backend",
    "proof_backend_version",
    "proof_schema_version",
    "statement_version",
    "target_id",
    "verifier_domain",
    "policy_status",
    "builder_status",
    "typed_bytes",
    "typed_delta_vs_champion",
    "typed_saving_vs_champion",
    "proof_json_bytes",
    "accounting_proof_json_bytes",
    "proof_len_bytes",
    "path_opening_bytes",
    "value_bytes",
    "fixed_overhead_bytes",
    "fri_decommitment_bytes",
    "fri_sample_bytes",
    "oods_sample_bytes",
    "queried_value_bytes",
    "trace_decommitment_bytes",
    "record_count",
    "record_stream_bytes",
    "record_stream_sha256",
    "envelope_sha256",
    "proof_sha256",
    "input_sha256",
}
FRONTIER_SUMMARY_KEYS = {
    "generated_proof_object_row_count",
    "accepted_row_count",
    "rejected_row_count",
    "current_champion_typed_bytes",
    "current_champion_path_opening_bytes",
    "fixed_adjacent_label_id",
    "fixed_adjacent_typed_bytes",
    "fixed_adjacent_miss_vs_champion_typed_bytes",
    "worst_accepted_label_id",
    "worst_accepted_typed_bytes",
    "worst_accepted_saving_typed_bytes",
    "best_accepted_label_id",
    "best_accepted_typed_bytes",
    "best_accepted_saving_typed_bytes",
    "best_accepted_saving_share",
    "source_generated_builder_frontier_label_id",
    "source_generated_builder_frontier_typed_bytes",
    "new_frontier_claimed",
    "proof_size_comparable_external_rows",
}
MUTATION_RESULT_KEYS = {"all_mutations_rejected", "mutations_rejected", "mutation_names", "cases"}
MUTATION_CASE_KEYS = {"name", "rejected", "error"}
TSV_COLUMNS = (
    "variant_id",
    "adapter_mode",
    "cli_command",
    "policy_status",
    "builder_status",
    "typed_bytes",
    "typed_delta_vs_champion",
    "typed_saving_vs_champion",
    "proof_json_bytes",
    "proof_len_bytes",
    "path_opening_bytes",
    "value_bytes",
    "record_stream_sha256",
    "envelope_sha256",
    "proof_sha256",
    "input_sha256",
    "payload_commitment",
    "source_artifact_digest_pins",
    "source_artifact_payload_commitments",
    "accepted_label_ids",
    "rejected_label_ids",
    "mutation_outcomes",
)


class GeneratedProofObjectBuilderGateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as err:
        raise GeneratedProofObjectBuilderGateError(f"invalid JSON value: {err}") from err


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
        raise GeneratedProofObjectBuilderGateError(f"{label} must be object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise GeneratedProofObjectBuilderGateError(f"{label} must be list")
    return value


def _str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise GeneratedProofObjectBuilderGateError(f"{label} must be non-empty string")
    return value


def _int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise GeneratedProofObjectBuilderGateError(f"{label} must be integer")
    return value


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual == expected:
        return
    unexpected = sorted(actual - expected)
    missing = sorted(expected - actual)
    if unexpected:
        raise GeneratedProofObjectBuilderGateError(f"{label} field drift: unexpected {unexpected[0]}")
    raise GeneratedProofObjectBuilderGateError(f"{label} field drift: missing {missing[0]}")


def load_json_file(path: pathlib.Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        payload, raw = inventory_gate.source_gate.load_json_file(path, label)
    except inventory_gate.source_gate.AdjacentLabelPolicyGateError as err:
        raise GeneratedProofObjectBuilderGateError(str(err)) from err
    return _dict(payload, label), raw


def load_generated_inventory() -> tuple[dict[str, Any], bytes]:
    payload, raw = load_json_file(GENERATED_INVENTORY_PATH, "generated adjacent label inventory")
    if sha256(raw) != EXPECTED_GENERATED_INVENTORY_SHA256:
        raise GeneratedProofObjectBuilderGateError("generated inventory digest drift")
    if payload.get("payload_commitment") != EXPECTED_GENERATED_INVENTORY_COMMITMENT:
        raise GeneratedProofObjectBuilderGateError("generated inventory commitment drift")
    try:
        inventory_gate.validate_payload(payload)
        rebuilt = inventory_gate.build_payload()
        if rebuilt != payload:
            raise GeneratedProofObjectBuilderGateError("generated inventory rebuild drift")
    except inventory_gate.GeneratedAdjacentLabelInventoryGateError as err:
        raise GeneratedProofObjectBuilderGateError(f"generated inventory invalid: {err}") from err
    return payload, raw


def load_accounting() -> tuple[dict[str, Any], bytes]:
    payload, raw = load_json_file(ACCOUNTING_PATH, "adjacent label probe accounting")
    if sha256(raw) != EXPECTED_ACCOUNTING_SHA256:
        raise GeneratedProofObjectBuilderGateError("accounting digest drift")
    expected_top = {
        "schema": EXPECTED_ACCOUNTING_SCHEMA,
        "accounting_domain": EXPECTED_ACCOUNTING_DOMAIN,
        "accounting_source": EXPECTED_ACCOUNTING_SOURCE,
        "proof_payload_kind": EXPECTED_PROOF_PAYLOAD_KIND,
        "accounting_format_version": "v1",
        "upstream_stwo_serialization_status": "NOT_UPSTREAM_STWO_SERIALIZATION_LOCAL_ACCOUNTING_RECORD_STREAM_ONLY",
    }
    for key, expected in expected_top.items():
        if payload.get(key) != expected:
            raise GeneratedProofObjectBuilderGateError("accounting schema drift")
    rows = _list(payload.get("rows"), "accounting rows")
    if len(rows) != 4:
        raise GeneratedProofObjectBuilderGateError("accounting row count drift")
    return payload, raw


def source_artifact_rows(raws: dict[str, bytes], generated_inventory: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": "generated_adjacent_label_inventory",
            "path": GENERATED_INVENTORY_PATH.relative_to(ROOT).as_posix(),
            "sha256": sha256(raws["generated_inventory"]),
            "size_bytes": len(raws["generated_inventory"]),
            "payload_commitment": generated_inventory["payload_commitment"],
        },
        {
            "id": "adjacent_label_probe_accounting",
            "path": ACCOUNTING_PATH.relative_to(ROOT).as_posix(),
            "sha256": sha256(raws["accounting"]),
            "size_bytes": len(raws["accounting"]),
            "payload_commitment": None,
        },
    ]


def generated_rows_by_id(generated_inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = {}
    for item in _list(generated_inventory.get("generated_label_inventory"), "generated label inventory"):
        row = _dict(item, "generated label row")
        variant_id = _str(row.get("variant_id"), "generated variant id")
        if variant_id in rows:
            raise GeneratedProofObjectBuilderGateError("generated label inventory duplicate variant_id")
        rows[variant_id] = row
    return rows


def accounting_rows_by_path(accounting: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = {}
    for item in _list(accounting.get("rows"), "accounting rows"):
        row = _dict(item, "accounting row")
        key = _str(row.get("evidence_relative_path"), "accounting evidence_relative_path")
        if key in rows:
            raise GeneratedProofObjectBuilderGateError("accounting rows duplicate evidence_relative_path")
        rows[key] = row
    return rows


def evidence_path_from_row(row: dict[str, Any]) -> pathlib.Path:
    relative_path = _str(row.get("evidence_relative_path"), "accounting evidence_relative_path")
    path = EVIDENCE_DIR / relative_path
    try:
        path.resolve().relative_to(EVIDENCE_DIR.resolve())
    except ValueError as err:
        raise GeneratedProofObjectBuilderGateError("accounting envelope path escapes evidence dir") from err
    return path


def load_envelope(path: pathlib.Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = inventory_gate.source_gate.read_repo_file(path, f"{path.name} envelope")
    except inventory_gate.source_gate.AdjacentLabelPolicyGateError as err:
        raise GeneratedProofObjectBuilderGateError(str(err)) from err
    try:
        return _dict(json.loads(raw), f"{path.name} envelope"), raw
    except json.JSONDecodeError as err:
        raise GeneratedProofObjectBuilderGateError(f"{path.name} envelope must be JSON: {err}") from err


def proof_bytes_from_envelope(envelope: dict[str, Any]) -> bytes:
    proof = _list(envelope.get("proof"), "envelope proof")
    if not all(isinstance(item, int) and not isinstance(item, bool) and 0 <= item <= 255 for item in proof):
        raise GeneratedProofObjectBuilderGateError("envelope proof must be byte array")
    return bytes(proof)


def grouped_accounting(accounting_row: dict[str, Any]) -> dict[str, int]:
    local = _dict(accounting_row.get("local_binary_accounting"), "local binary accounting")
    grouped = _dict(local.get("grouped_reconstruction"), "grouped reconstruction")
    required = {"fixed_overhead", "fri_decommitments", "fri_samples", "oods_samples", "queries_values", "trace_decommitments"}
    _require_exact_keys(grouped, required, "grouped reconstruction")
    return {key: _int(value, f"grouped {key}") for key, value in grouped.items()}


def envelope_metadata_fields(envelope: dict[str, Any], metadata: dict[str, Any]) -> dict[str, str]:
    fields = {}
    for key in metadata:
        fields[key] = _str(envelope.get(key), f"envelope {key}")
    if metadata != fields:
        raise GeneratedProofObjectBuilderGateError("envelope metadata drift")
    return fields


def proof_object_row(
    generated_row: dict[str, Any],
    accounting_row: dict[str, Any],
) -> dict[str, Any]:
    envelope_path = evidence_path_from_row(accounting_row)
    envelope, envelope_raw = load_envelope(envelope_path)
    proof_bytes = proof_bytes_from_envelope(envelope)
    local = _dict(accounting_row.get("local_binary_accounting"), "local binary accounting")
    grouped = grouped_accounting(accounting_row)
    metadata = _dict(accounting_row.get("envelope_metadata"), "envelope metadata")
    path = _str(generated_row.get("path"), "generated proof path")
    if path != _str(accounting_row.get("evidence_relative_path"), "accounting evidence_relative_path"):
        raise GeneratedProofObjectBuilderGateError("proof object row path drift")
    if _str(accounting_row.get("path"), "accounting path") != f"docs/engineering/evidence/{path}":
        raise GeneratedProofObjectBuilderGateError("proof object row path drift")
    if sha256(envelope_raw) != _str(accounting_row.get("envelope_sha256"), "envelope sha256"):
        raise GeneratedProofObjectBuilderGateError("envelope sha drift")
    if sha256(proof_bytes) != _str(accounting_row.get("proof_sha256"), "proof sha256"):
        raise GeneratedProofObjectBuilderGateError("proof sha drift")
    proof_json_bytes = _int(generated_row.get("proof_json_bytes"), "generated proof_json_bytes")
    if proof_json_bytes != _int(accounting_row.get("proof_json_size_bytes"), "accounting proof_json_size_bytes"):
        raise GeneratedProofObjectBuilderGateError("proof json size drift")
    if proof_json_bytes != len(proof_bytes):
        raise GeneratedProofObjectBuilderGateError("proof length drift")
    typed_bytes = _int(local.get("typed_size_estimate_bytes"), "typed_size_estimate_bytes")
    if typed_bytes != _int(local.get("component_sum_bytes"), "component_sum_bytes"):
        raise GeneratedProofObjectBuilderGateError("typed accounting drift")
    if typed_bytes != _int(generated_row.get("typed_bytes"), "generated typed bytes"):
        raise GeneratedProofObjectBuilderGateError("typed accounting drift")
    path_opening_bytes = sum(grouped[key] for key in PATH_OPENING_GROUPS)
    value_bytes = sum(grouped[key] for key in VALUE_GROUPS)
    if path_opening_bytes != _int(generated_row.get("path_opening_bytes"), "generated path_opening_bytes"):
        raise GeneratedProofObjectBuilderGateError("path opening accounting drift")
    if value_bytes != _int(generated_row.get("value_bytes"), "generated value_bytes"):
        raise GeneratedProofObjectBuilderGateError("value accounting drift")
    metadata_fields = envelope_metadata_fields(envelope, metadata)
    envelope_input = _dict(envelope.get("input"), "envelope input")
    return {
        "variant_id": generated_row["variant_id"],
        "adapter_mode": generated_row["adapter_mode"],
        "rust_enum_variant": generated_row["rust_enum_variant"],
        "cli_command": generated_row["cli_command"],
        "path": path,
        "accounting_path": ACCOUNTING_PATH.relative_to(ROOT).as_posix(),
        "proof_backend": metadata_fields["proof_backend"],
        "proof_backend_version": metadata_fields["proof_backend_version"],
        "proof_schema_version": metadata_fields["proof_schema_version"],
        "statement_version": metadata_fields["statement_version"],
        "target_id": metadata_fields["target_id"],
        "verifier_domain": metadata_fields["verifier_domain"],
        "policy_status": generated_row["policy_status"],
        "builder_status": "reconstructed_from_generated_label_accounting_and_envelope",
        "typed_bytes": typed_bytes,
        "typed_delta_vs_champion": generated_row["typed_delta_vs_champion"],
        "typed_saving_vs_champion": CURRENT_CHAMPION_TYPED_BYTES - typed_bytes,
        "proof_json_bytes": proof_json_bytes,
        "accounting_proof_json_bytes": accounting_row["proof_json_size_bytes"],
        "proof_len_bytes": len(proof_bytes),
        "path_opening_bytes": path_opening_bytes,
        "value_bytes": value_bytes,
        "fixed_overhead_bytes": grouped["fixed_overhead"],
        "fri_decommitment_bytes": grouped["fri_decommitments"],
        "fri_sample_bytes": grouped["fri_samples"],
        "oods_sample_bytes": grouped["oods_samples"],
        "queried_value_bytes": grouped["queries_values"],
        "trace_decommitment_bytes": grouped["trace_decommitments"],
        "record_count": local["record_count"],
        "record_stream_bytes": local["record_stream_bytes"],
        "record_stream_sha256": local["record_stream_sha256"],
        "envelope_sha256": accounting_row["envelope_sha256"],
        "proof_sha256": accounting_row["proof_sha256"],
        "input_sha256": sha256(canonical_json_bytes(envelope_input)),
    }


def build_proof_object_rows(generated_inventory: dict[str, Any], accounting: dict[str, Any]) -> list[dict[str, Any]]:
    generated = generated_rows_by_id(generated_inventory)
    accounting_by_path = accounting_rows_by_path(accounting)
    rows = []
    for variant_id in generated_inventory["generator_policy"]["generated_label_ids"]:
        generated_row = generated[variant_id]
        path = _str(generated_row.get("path"), "generated row path")
        accounting_row = accounting_by_path.get(path)
        if accounting_row is None:
            raise GeneratedProofObjectBuilderGateError("missing accounting row for generated label")
        rows.append(proof_object_row(generated_row, accounting_row))
    return rows


def build_frontier_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [row for row in rows if row["policy_status"] == "supported_label"]
    rejected = [row for row in rows if row["policy_status"].startswith("rejected")]
    if not accepted:
        raise GeneratedProofObjectBuilderGateError("frontier summary drift")
    best = min(accepted, key=lambda row: row["typed_bytes"])
    worst_accepted = max(accepted, key=lambda row: row["typed_bytes"])
    fixed = None
    for row in rows:
        if row["variant_id"] == FIXED_ADJACENT_LABEL_ID:
            fixed = row
            break
    if fixed is None:
        raise GeneratedProofObjectBuilderGateError("frontier summary drift")
    return {
        "generated_proof_object_row_count": len(rows),
        "accepted_row_count": len(accepted),
        "rejected_row_count": len(rejected),
        "current_champion_typed_bytes": CURRENT_CHAMPION_TYPED_BYTES,
        "current_champion_path_opening_bytes": CURRENT_CHAMPION_PATH_OPENING_BYTES,
        "fixed_adjacent_label_id": fixed["variant_id"],
        "fixed_adjacent_typed_bytes": fixed["typed_bytes"],
        "fixed_adjacent_miss_vs_champion_typed_bytes": fixed["typed_bytes"] - CURRENT_CHAMPION_TYPED_BYTES,
        "worst_accepted_label_id": worst_accepted["variant_id"],
        "worst_accepted_typed_bytes": worst_accepted["typed_bytes"],
        "worst_accepted_saving_typed_bytes": CURRENT_CHAMPION_TYPED_BYTES - worst_accepted["typed_bytes"],
        "best_accepted_label_id": best["variant_id"],
        "best_accepted_typed_bytes": best["typed_bytes"],
        "best_accepted_saving_typed_bytes": CURRENT_CHAMPION_TYPED_BYTES - best["typed_bytes"],
        "best_accepted_saving_share": f"{(CURRENT_CHAMPION_TYPED_BYTES - best['typed_bytes']) / CURRENT_CHAMPION_TYPED_BYTES:.6f}",
        "source_generated_builder_frontier_label_id": best["variant_id"],
        "source_generated_builder_frontier_typed_bytes": best["typed_bytes"],
        "new_frontier_claimed": False,
        "proof_size_comparable_external_rows": 0,
    }


def build_core_payload() -> dict[str, Any]:
    generated_inventory, generated_inventory_raw = load_generated_inventory()
    accounting, accounting_raw = load_accounting()
    rows = build_proof_object_rows(generated_inventory, accounting)
    accepted_label_ids = [
        row["variant_id"]
        for row in rows
        if row["policy_status"] == "supported_label"
    ]
    rejected_label_ids = [
        row["variant_id"]
        for row in rows
        if row["policy_status"].startswith("rejected")
    ]
    return {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "issue_hint": ISSUE_HINT,
        "source_artifacts": source_artifact_rows(
            {
                "generated_inventory": generated_inventory_raw,
                "accounting": accounting_raw,
            },
            generated_inventory,
        ),
        "builder_policy": {
            "name": "source_generated_seq32_attention_mlp_proof_object_builder_v1",
            "source_rule": "generated adjacent labels from Rust+CLI inventory must join to the pinned local binary accounting row and the referenced envelope bytes",
            "manual_override_allowed": False,
            "input_artifact_ids": [
                "generated_adjacent_label_inventory",
                "adjacent_label_probe_accounting",
            ],
            "generated_label_ids": [row["variant_id"] for row in rows],
            "accepted_label_ids": accepted_label_ids,
            "rejected_label_ids": rejected_label_ids,
            "row_join_key": "generated_label_inventory.path == accounting.evidence_relative_path",
            "proof_envelope_binding": [
                "accounting.envelope_sha256 == sha256(raw envelope JSON bytes)",
                "accounting.proof_sha256 == sha256(envelope.proof byte array)",
                "accounting.proof_json_size_bytes == len(envelope.proof byte array)",
                "local_binary_accounting.typed_size_estimate_bytes == generated typed_bytes",
            ],
            "promotion_rule": (
                "a source-generated label is promotable only when it is accepted by the generated "
                "inventory policy and the builder reconstructs its proof-object row without drift"
            ),
        },
        "proof_object_rows": rows,
        "frontier_summary": build_frontier_summary(rows),
        "interpretation": copy.deepcopy(EXPECTED_INTERPRETATION),
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }


def build_payload() -> dict[str, Any]:
    payload = build_core_payload()
    payload["mutation_result"] = mutation_result(payload)
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload)
    return payload


@functools.lru_cache(maxsize=1)
def expected_payload_with_empty_mutations() -> dict[str, Any]:
    payload = build_core_payload()
    payload["mutation_result"] = expected_mutation_result()
    payload["payload_commitment"] = payload_commitment(payload)
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
        except GeneratedProofObjectBuilderGateError as err:
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
        ("generated_inventory_digest_drift", lambda item: item["source_artifacts"][0].update({"sha256": "0" * 64})),
        ("generated_inventory_commitment_drift", lambda item: item["source_artifacts"][0].update({"payload_commitment": "blake2b-256:" + "0" * 64})),
        ("accounting_digest_drift", lambda item: item["source_artifacts"][1].update({"sha256": "0" * 64})),
        ("builder_manual_override_enabled", lambda item: item["builder_policy"].update({"manual_override_allowed": True})),
        ("generated_label_removed", lambda item: item["builder_policy"]["generated_label_ids"].remove("adjacent_label_probe_a")),
        ("missing_accounting_row", lambda item: item["proof_object_rows"].pop(1)),
        ("envelope_path_relabeling", lambda item: item["proof_object_rows"][1].update({"path": "other.envelope.json"})),
        ("envelope_sha_drift", lambda item: item["proof_object_rows"][1].update({"envelope_sha256": "1" * 64})),
        ("proof_sha_drift", lambda item: item["proof_object_rows"][1].update({"proof_sha256": "2" * 64})),
        ("proof_length_drift", lambda item: item["proof_object_rows"][1].update({"proof_len_bytes": 1})),
        ("typed_accounting_drift", lambda item: item["proof_object_rows"][1].update({"typed_bytes": CURRENT_CHAMPION_TYPED_BYTES})),
        ("record_stream_drift", lambda item: item["proof_object_rows"][1].update({"record_stream_sha256": "3" * 64})),
        ("proof_backend_version_drift", lambda item: item["proof_object_rows"][1].update({"proof_backend_version": "wrong"})),
        ("fixed_label_promoted", lambda item: item["proof_object_rows"][0].update({"policy_status": "supported_label"})),
        ("best_frontier_drift", lambda item: item["frontier_summary"].update({"source_generated_builder_frontier_typed_bytes": CURRENT_CHAMPION_TYPED_BYTES})),
        ("validation_command_drift", lambda item: item["validation_commands"].append("echo untracked")),
        ("removed_non_claim", lambda item: item["non_claims"].remove("not a NANOZK proof-size win")),
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
            raise GeneratedProofObjectBuilderGateError(f"{key} drift")
    if "NANOZK_WIN" in str(payload.get("claim_boundary")).split(";"):
        raise GeneratedProofObjectBuilderGateError("claim_boundary drift")
    expected = expected_payload_with_empty_mutations()
    validate_source_artifacts(_list(payload.get("source_artifacts"), "source artifacts"), expected["source_artifacts"])
    validate_builder_policy(_dict(payload.get("builder_policy"), "builder policy"), expected["builder_policy"])
    validate_proof_object_rows(
        _list(payload.get("proof_object_rows"), "proof object rows"),
        expected["proof_object_rows"],
    )
    validate_frontier_summary(_dict(payload.get("frontier_summary"), "frontier summary"), expected["frontier_summary"])
    if payload.get("interpretation") != EXPECTED_INTERPRETATION:
        raise GeneratedProofObjectBuilderGateError("interpretation drift")
    if payload.get("non_claims") != list(NON_CLAIMS):
        raise GeneratedProofObjectBuilderGateError("non_claims drift")
    if payload.get("validation_commands") != list(VALIDATION_COMMANDS):
        raise GeneratedProofObjectBuilderGateError("validation command drift")
    validate_mutation_result(_dict(payload.get("mutation_result"), "mutation result"))
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise GeneratedProofObjectBuilderGateError("payload commitment drift")


def validate_source_artifacts(artifacts: list[Any], expected: list[dict[str, Any]]) -> None:
    for item in artifacts:
        _require_exact_keys(_dict(item, "source artifact"), SOURCE_ARTIFACT_KEYS, "source artifact")
    if artifacts != expected:
        raise GeneratedProofObjectBuilderGateError("source artifact drift")


def validate_builder_policy(policy: dict[str, Any], expected: dict[str, Any]) -> None:
    _require_exact_keys(policy, BUILDER_POLICY_KEYS, "builder policy")
    if policy.get("manual_override_allowed") is not False:
        raise GeneratedProofObjectBuilderGateError("builder policy drift")
    if policy != expected:
        raise GeneratedProofObjectBuilderGateError("builder policy drift")


def validate_proof_object_rows(rows: list[Any], expected: list[dict[str, Any]]) -> None:
    for item in rows:
        _require_exact_keys(_dict(item, "proof object row"), PROOF_ROW_KEYS, "proof object row")
    if [row.get("variant_id") for row in rows] != [row["variant_id"] for row in expected]:
        raise GeneratedProofObjectBuilderGateError("proof object row order drift")
    if rows != expected:
        raise GeneratedProofObjectBuilderGateError("proof object row drift")
    for row in rows:
        if row["proof_json_bytes"] != row["accounting_proof_json_bytes"] or row["proof_json_bytes"] != row["proof_len_bytes"]:
            raise GeneratedProofObjectBuilderGateError("proof object row drift")
        if row["typed_bytes"] != CURRENT_CHAMPION_TYPED_BYTES - row["typed_saving_vs_champion"]:
            raise GeneratedProofObjectBuilderGateError("proof object row drift")
        if row["policy_status"] == "supported_label" and row["typed_bytes"] >= CURRENT_CHAMPION_TYPED_BYTES:
            raise GeneratedProofObjectBuilderGateError("proof object row drift")
        if row["variant_id"] == FIXED_ADJACENT_LABEL_ID and row["policy_status"] != "rejected_inflating_label":
            raise GeneratedProofObjectBuilderGateError("proof object row drift")


def validate_frontier_summary(summary: dict[str, Any], expected: dict[str, Any]) -> None:
    _require_exact_keys(summary, FRONTIER_SUMMARY_KEYS, "frontier summary")
    if summary.get("new_frontier_claimed") is not False:
        raise GeneratedProofObjectBuilderGateError("frontier summary drift")
    if summary != expected:
        raise GeneratedProofObjectBuilderGateError("frontier summary drift")


def validate_mutation_result(result: dict[str, Any]) -> None:
    _require_exact_keys(result, MUTATION_RESULT_KEYS, "mutation result")
    cases = _list(result.get("cases"), "mutation cases")
    for case in cases:
        _require_exact_keys(_dict(case, "mutation case"), MUTATION_CASE_KEYS, "mutation case")
    if result != expected_mutation_result():
        raise GeneratedProofObjectBuilderGateError("mutation result drift")


def _tsv_cell(value: Any) -> str:
    text = str(value)
    if "\t" in text or "\n" in text or "\r" in text:
        raise GeneratedProofObjectBuilderGateError("tsv audit field contains unsafe whitespace")
    return text


def _join_tsv_items(items: list[str]) -> str:
    return ",".join(_tsv_cell(item) for item in items)


def tsv_audit_columns(payload: dict[str, Any]) -> dict[str, str]:
    mutation_cases = _list(payload["mutation_result"]["cases"], "mutation cases")
    return {
        "payload_commitment": _tsv_cell(payload["payload_commitment"]),
        "source_artifact_digest_pins": _join_tsv_items(
            [
                f"{row['id']}={row['sha256']}"
                for row in _list(payload["source_artifacts"], "source artifacts")
            ]
        ),
        "source_artifact_payload_commitments": _join_tsv_items(
            [
                f"{row['id']}={row['payload_commitment'] or 'none'}"
                for row in _list(payload["source_artifacts"], "source artifacts")
            ]
        ),
        "accepted_label_ids": _join_tsv_items(_list(payload["builder_policy"]["accepted_label_ids"], "accepted label ids")),
        "rejected_label_ids": _join_tsv_items(_list(payload["builder_policy"]["rejected_label_ids"], "rejected label ids")),
        "mutation_outcomes": _join_tsv_items(
            [
                f"{case['name']}={'rejected' if case['rejected'] else 'accepted'}:{case['error']}"
                for case in mutation_cases
            ]
        ),
    }


def render_tsv(payload: dict[str, Any]) -> str:
    validate_payload(payload)
    audit_columns = tsv_audit_columns(payload)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in payload["proof_object_rows"]:
        row_columns = {
            column: row[column]
            for column in TSV_COLUMNS
            if column in PROOF_ROW_KEYS
        }
        writer.writerow({**row_columns, **audit_columns})
    return output.getvalue()


def atomic_write_text(path: pathlib.Path, text: str) -> None:
    try:
        inventory_gate.source_gate.atomic_write_text(path, text)
    except inventory_gate.source_gate.AdjacentLabelPolicyGateError as err:
        raise GeneratedProofObjectBuilderGateError(str(err)) from err
    except Exception as err:
        raise GeneratedProofObjectBuilderGateError(f"failed to write output: {err}") from err


def require_output_path(path: pathlib.Path) -> pathlib.Path:
    try:
        return inventory_gate.source_gate.require_output_path(path)
    except inventory_gate.source_gate.AdjacentLabelPolicyGateError as err:
        raise GeneratedProofObjectBuilderGateError(str(err)) from err
    except Exception as err:
        raise GeneratedProofObjectBuilderGateError(f"failed to prepare output path: {err}") from err


def staged_output_path(path: pathlib.Path, text: str) -> pathlib.Path:
    target = require_output_path(path)
    text_hash = sha256(text.encode("utf-8"))[:16]
    return target.with_name(f".{target.name}.paired-stage.{text_hash}")


def cleanup_staged_outputs(paths: list[pathlib.Path]) -> None:
    for path in paths:
        try:
            target = require_output_path(path)
            if target.exists():
                target.unlink()
        except GeneratedProofObjectBuilderGateError:
            continue
        except OSError:
            continue


def read_existing_output_text(path: pathlib.Path) -> str | None:
    target = require_output_path(path)
    if not target.exists():
        return None
    try:
        return target.read_text(encoding="utf-8")
    except OSError as err:
        raise GeneratedProofObjectBuilderGateError(f"failed to read existing output: {err}") from err


def restore_outputs(previous: list[tuple[pathlib.Path, str | None]]) -> None:
    for path, text in previous:
        target = require_output_path(path)
        if text is None:
            try:
                if target.exists():
                    target.unlink()
            except OSError as err:
                raise GeneratedProofObjectBuilderGateError(f"failed to roll back output: {err}") from err
        else:
            atomic_write_text(path, text)


def publish_outputs_atomically(outputs: list[tuple[pathlib.Path, str]]) -> None:
    if len(outputs) <= 1:
        for path, text in outputs:
            atomic_write_text(path, text)
        return

    staged: list[pathlib.Path] = []
    try:
        for path, text in outputs:
            stage_path = staged_output_path(path, text)
            atomic_write_text(stage_path, text)
            staged.append(stage_path)
        previous = [(path, read_existing_output_text(path)) for path, _text in outputs]
        try:
            for path, text in outputs:
                atomic_write_text(path, text)
        except GeneratedProofObjectBuilderGateError:
            restore_outputs(previous)
            raise
    finally:
        cleanup_staged_outputs(staged)


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path | None, tsv_path: pathlib.Path | None) -> None:
    validate_payload(payload)
    if (json_path is None) != (tsv_path is None):
        raise GeneratedProofObjectBuilderGateError("paired JSON/TSV output paths required")
    outputs = []
    if json_path is not None:
        outputs.append((json_path, json.dumps(payload, indent=2, sort_keys=True) + "\n"))
    if tsv_path is not None:
        outputs.append((tsv_path, render_tsv(payload)))
    publish_outputs_atomically(outputs)


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
                "generated_proof_object_row_count": payload["frontier_summary"]["generated_proof_object_row_count"],
                "best_accepted_typed_bytes": payload["frontier_summary"]["best_accepted_typed_bytes"],
                "best_accepted_saving_typed_bytes": payload["frontier_summary"]["best_accepted_saving_typed_bytes"],
                "mutations_rejected": payload["mutation_result"]["mutations_rejected"],
                "json_out": str(args.write_json) if args.write_json else None,
                "tsv_out": str(args.write_tsv) if args.write_tsv else None,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
