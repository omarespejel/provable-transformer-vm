#!/usr/bin/env python3.10
"""Gate a source-generated adjacent-label inventory for seq32 attention+MLP proofs."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import pathlib
import re
import sys
from collections.abc import Callable
from typing import Any


if sys.version_info < (3, 10):
    raise RuntimeError(
        "zkai_native_seq32_attention_mlp_generated_adjacent_label_inventory_gate requires Python 3.10+"
    )

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import zkai_native_seq32_attention_mlp_adjacent_label_policy_gate as source_gate
from scripts import zkai_native_seq32_attention_mlp_deterministic_adjacent_label_policy_gate as deterministic_gate


EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
RUST_SOURCE_PATH = ROOT / "src" / "stwo_backend" / "native_seq32_attention_mlp_single_proof.rs"
CLI_SOURCE_PATH = ROOT / "src" / "bin" / "zkai_native_seq32_attention_mlp_single_proof.rs"
SOURCE_POLICY_PATH = deterministic_gate.SOURCE_POLICY_PATH
DETERMINISTIC_POLICY_PATH = deterministic_gate.JSON_OUT
JSON_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-generated-adjacent-label-inventory-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-generated-adjacent-label-inventory-2026-05.tsv"

SCHEMA = "zkai-native-seq32-attention-mlp-generated-adjacent-label-inventory-gate-v1"
DECISION = "GO_GENERATED_SUPPORTED_ADJACENT_LABELS_BEAT_CURRENT_CHAMPION_WITH_FULL_INVENTORY_NO_GO"
RESULT = "WORST_GENERATED_ACCEPTED_LABEL_SAVES_1736_TYPED_BYTES_AND_FULL_GENERATED_WORST_MISSES_BY_88"
CLAIM_BOUNDARY = (
    "SOURCE_GENERATED_POLICY_OVER_CURRENT_RUST_ADJACENT_LABEL_FAMILY;"
    "ACCEPTS_ONLY_SOURCE_GENERATED_LABELS_WITH_PINNED_ACCOUNTING_BELOW_42068;"
    "NOT_A_NEW_PROOF_SIZE_FRONTIER_NOT_A_NANOZK_WIN"
)
ISSUE_HINT = "generator-backed-seq32-adjacent-label-inventory"
PAYLOAD_DOMAIN = "ptvm:zkai:native-seq32-attention-mlp-generated-adjacent-label-inventory:v1"

EXPECTED_RUST_SOURCE_SHA256 = "3d740bda9a3f301edea7a10dc1b9f58878d1a0f067397eecb5ed50465e4b7d95"
EXPECTED_CLI_SOURCE_SHA256 = "8408ccfe9a4882b19484326f9bad1670a87c582313f4d93d75305177cdfd8e17"
EXPECTED_DETERMINISTIC_POLICY_SHA256 = "d5cbe419a545c022036b7347b6fb75a1fbb127dc7a861948d96103e646f338ab"
EXPECTED_DETERMINISTIC_POLICY_COMMITMENT = "blake2b-256:cb60558f8b274ffa44d51de3367a34759b408b5c1dd3427583d3031ef9017fdd"

EXPECTED_ADJACENT_MODES = (
    "rmsnorm_input_fused_adjacent_fixed_v1",
    "rmsnorm_input_fused_adjacent_label_probe_a_v1",
    "rmsnorm_input_fused_adjacent_label_probe_b_v1",
)
EXPECTED_CLI_COMMANDS = (
    "build-input-rmsnorm-fused-adjacent",
    "build-input-rmsnorm-fused-adjacent-label-probe-a",
    "build-input-rmsnorm-fused-adjacent-label-probe-b",
)
ADAPTER_MODE_TO_LABEL_ID = {
    "rmsnorm_input_fused_adjacent_fixed_v1": "fixed_adjacent_layout",
    "rmsnorm_input_fused_adjacent_label_probe_a_v1": "adjacent_label_probe_a",
    "rmsnorm_input_fused_adjacent_label_probe_b_v1": "adjacent_label_probe_b",
}
ADAPTER_MODE_TO_CLI_COMMAND = dict(zip(EXPECTED_ADJACENT_MODES, EXPECTED_CLI_COMMANDS, strict=True))

CURRENT_CHAMPION_ID = deterministic_gate.CURRENT_CHAMPION_ID
CURRENT_CHAMPION_TYPED_BYTES = deterministic_gate.CURRENT_CHAMPION_TYPED_BYTES
CURRENT_CHAMPION_PATH_OPENING_BYTES = deterministic_gate.CURRENT_CHAMPION_PATH_OPENING_BYTES
CURRENT_CHAMPION_VALUE_BYTES = deterministic_gate.CURRENT_CHAMPION_VALUE_BYTES
ADJACENT_VALUE_BYTES = deterministic_gate.ADJACENT_VALUE_BYTES
FIXED_ADJACENT_ID = deterministic_gate.FIXED_ADJACENT_ID
ACCEPTED_LABEL_IDS = deterministic_gate.SUPPORTED_LABEL_IDS
REJECTED_LABEL_IDS = (FIXED_ADJACENT_ID,)
WORST_ACCEPTED_LABEL_ID = deterministic_gate.WORST_SUPPORTED_LABEL_ID
WORST_ACCEPTED_TYPED_BYTES = deterministic_gate.WORST_SUPPORTED_TYPED_BYTES
WORST_ACCEPTED_SAVING_BYTES = deterministic_gate.WORST_SUPPORTED_SAVING_BYTES
BEST_ACCEPTED_LABEL_ID = deterministic_gate.BEST_SUPPORTED_LABEL_ID
BEST_ACCEPTED_TYPED_BYTES = deterministic_gate.BEST_SUPPORTED_TYPED_BYTES
BEST_ACCEPTED_SAVING_BYTES = deterministic_gate.BEST_SUPPORTED_SAVING_BYTES
FULL_GENERATED_WORST_LABEL_ID = deterministic_gate.FULL_INVENTORY_WORST_LABEL_ID
FULL_GENERATED_WORST_TYPED_BYTES = deterministic_gate.FULL_INVENTORY_WORST_TYPED_BYTES
FULL_GENERATED_MISS_BYTES = deterministic_gate.FULL_INVENTORY_MISS_BYTES
FIXED_PATH_OPENING_OVERHANG_BYTES = deterministic_gate.FIXED_PATH_OPENING_OVERHANG_BYTES
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = deterministic_gate.NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES

EXPECTED_REJECTED_UNSEEN_LABELS = (
    {
        "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_c_v1",
        "reason": "adapter mode is absent from the pinned Rust enum and CLI generator surface",
    },
    {
        "adapter_mode": "rmsnorm_input_fused_post_tail_label_probe_a_v1",
        "reason": "adapter mode belongs to the post-tail family, not the pinned adjacent family",
    },
)

EXPECTED_INTERPRETATION = {
    "human_read": (
        "The good adjacent-label numbers are no longer just a hand-picked probe pair. The gate "
        "derives the current adjacent label family from Rust enum variants and CLI build commands, "
        "then accepts only the generated labels whose pinned proof accounting beats the 42,068 "
        "typed-byte champion."
    ),
    "mechanism_read": (
        "The full generated adjacent family is still not promotable because the fixed adjacent "
        "label remains 88 typed bytes above the champion. The source-generated accepted subset "
        "keeps probe A and probe B; worst accepted proof size remains 40,332 typed bytes."
    ),
    "next_experiment": (
        "Move from source-generated label policy to a source-generated proof-object builder so "
        "future label additions produce proof/accounting rows automatically before promotion."
    ),
}

NON_CLAIMS = (
    "not a new proof-size frontier beyond the deterministic label-policy gate",
    "not a final production label-selection policy",
    "not robust to future Rust label additions without regenerating this gate",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not a full transformer block proof",
    "not exact real-valued Softmax",
    "not timing evidence",
    "not production-ready zkML",
)

VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_native_seq32_attention_mlp_generated_adjacent_label_inventory_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-adjacent-label-inventory-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-generated-adjacent-label-inventory-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_generated_adjacent_label_inventory_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_generated_adjacent_label_inventory_gate.py",
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
    "rust_source_digest_drift",
    "cli_source_digest_drift",
    "deterministic_policy_commitment_drift",
    "generated_mode_removed",
    "generated_mode_extra",
    "cli_command_drift",
    "accepted_label_erased",
    "fixed_label_accepted",
    "accepted_value_drift",
    "accepted_typed_drift",
    "proof_accounting_erased",
    "unseen_label_accepted",
    "post_tail_cross_family_accepted",
    "generator_rule_drift",
    "manual_override_enabled",
    "summary_worst_accepted_drift",
    "full_inventory_promoted",
    "validation_command_drift",
    "removed_non_claim",
    "label_order_drift",
    "payload_commitment_drift",
)
EXPECTED_MUTATION_ERRORS = {
    "decision_drift": "decision drift",
    "result_drift": "result drift",
    "claim_boundary_overclaim": "claim_boundary drift",
    "rust_source_digest_drift": "source artifact drift",
    "cli_source_digest_drift": "source artifact drift",
    "deterministic_policy_commitment_drift": "source artifact drift",
    "generated_mode_removed": "generator policy drift",
    "generated_mode_extra": "generator policy drift",
    "cli_command_drift": "generator policy drift",
    "accepted_label_erased": "generator policy drift",
    "fixed_label_accepted": "generated label inventory drift",
    "accepted_value_drift": "generated label inventory drift",
    "accepted_typed_drift": "generated label inventory drift",
    "proof_accounting_erased": "generated label inventory drift",
    "unseen_label_accepted": "rejected unseen label drift",
    "post_tail_cross_family_accepted": "rejected unseen label drift",
    "generator_rule_drift": "generator policy drift",
    "manual_override_enabled": "generator policy drift",
    "summary_worst_accepted_drift": "policy summary drift",
    "full_inventory_promoted": "policy summary drift",
    "validation_command_drift": "validation command drift",
    "removed_non_claim": "non_claims drift",
    "label_order_drift": "generated label order drift",
    "payload_commitment_drift": "payload commitment drift",
}

PAYLOAD_KEYS = {
    "schema",
    "decision",
    "result",
    "claim_boundary",
    "issue_hint",
    "source_artifacts",
    "generator_policy",
    "generated_label_inventory",
    "rejected_unseen_labels",
    "policy_summary",
    "interpretation",
    "non_claims",
    "validation_commands",
    "mutation_result",
    "payload_commitment",
}
SOURCE_ARTIFACT_KEYS = {"id", "path", "sha256", "size_bytes", "payload_commitment"}
GENERATOR_POLICY_KEYS = {
    "name",
    "source_rule",
    "manual_override_allowed",
    "generated_adapter_modes",
    "generated_cli_commands",
    "generated_label_ids",
    "accepted_label_ids",
    "rejected_label_ids",
    "acceptance_criteria",
    "rejection_criteria",
}
LABEL_ROW_KEYS = {
    "variant_id",
    "adapter_mode",
    "rust_enum_variant",
    "cli_command",
    "path",
    "typed_bytes",
    "proof_json_bytes",
    "path_opening_bytes",
    "value_bytes",
    "typed_delta_vs_champion",
    "path_opening_delta_vs_champion",
    "policy_status",
    "status_reason",
    "proof_accounting_pinned",
}
SUMMARY_KEYS = {
    "current_champion_typed_bytes",
    "current_champion_path_opening_bytes",
    "current_champion_value_bytes",
    "generated_label_count",
    "accepted_label_count",
    "rejected_label_count",
    "full_generated_inventory_promotable_vs_current_champion",
    "full_generated_worst_label_id",
    "full_generated_worst_typed_bytes",
    "full_generated_miss_vs_champion_typed_bytes",
    "fixed_adjacent_path_opening_overhang_vs_champion",
    "worst_accepted_label_id",
    "worst_accepted_typed_bytes",
    "worst_accepted_saving_typed_bytes",
    "worst_accepted_saving_share",
    "best_accepted_label_id",
    "best_accepted_typed_bytes",
    "best_accepted_saving_typed_bytes",
    "accepted_value_bytes_stable",
    "proof_size_comparable_external_rows",
    "nanozk_reported_d128_block_proof_bytes",
}
MUTATION_RESULT_KEYS = {"all_mutations_rejected", "mutations_rejected", "mutation_names", "cases"}
MUTATION_CASE_KEYS = {"name", "rejected", "error"}
TSV_COLUMNS = (
    "variant_id",
    "adapter_mode",
    "cli_command",
    "policy_status",
    "typed_bytes",
    "typed_delta_vs_champion",
    "path_opening_bytes",
    "path_opening_delta_vs_champion",
    "value_bytes",
    "proof_accounting_pinned",
    "payload_commitment",
    "source_artifact_digest_pins",
    "source_artifact_payload_commitments",
    "generated_label_ids",
    "accepted_label_ids",
    "rejected_label_ids",
    "rejected_unseen_adapter_modes",
    "mutation_outcomes",
)


class GeneratedAdjacentLabelInventoryGateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as err:
        raise GeneratedAdjacentLabelInventoryGateError(f"invalid JSON value: {err}") from err


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
        raise GeneratedAdjacentLabelInventoryGateError(f"{label} must be object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise GeneratedAdjacentLabelInventoryGateError(f"{label} must be list")
    return value


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual == expected:
        return
    unexpected = sorted(actual - expected)
    missing = sorted(expected - actual)
    if unexpected:
        raise GeneratedAdjacentLabelInventoryGateError(f"{label} field drift: unexpected {unexpected[0]}")
    raise GeneratedAdjacentLabelInventoryGateError(f"{label} field drift: missing {missing[0]}")


def read_source(path: pathlib.Path, label: str, expected_sha256: str) -> bytes:
    try:
        raw = source_gate.read_repo_file(path, label)
    except source_gate.AdjacentLabelPolicyGateError as err:
        raise GeneratedAdjacentLabelInventoryGateError(str(err)) from err
    digest = sha256(raw)
    if digest != expected_sha256:
        raise GeneratedAdjacentLabelInventoryGateError(f"{label} digest drift")
    return raw


def decode_utf8(raw: bytes, label: str) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as err:
        raise GeneratedAdjacentLabelInventoryGateError(f"{label} must be UTF-8") from err


def load_json_file(path: pathlib.Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        payload, raw = source_gate.load_json_file(path, label)
    except source_gate.AdjacentLabelPolicyGateError as err:
        raise GeneratedAdjacentLabelInventoryGateError(str(err)) from err
    return _dict(payload, label), raw


def load_source_policy() -> tuple[dict[str, Any], bytes]:
    try:
        source, raw = deterministic_gate.load_source_policy()
    except deterministic_gate.DeterministicAdjacentLabelPolicyGateError as err:
        raise GeneratedAdjacentLabelInventoryGateError(str(err)) from err
    if sha256(raw) != deterministic_gate.EXPECTED_SOURCE_POLICY_SHA256:
        raise GeneratedAdjacentLabelInventoryGateError("source policy digest drift")
    if source.get("payload_commitment") != deterministic_gate.EXPECTED_SOURCE_POLICY_COMMITMENT:
        raise GeneratedAdjacentLabelInventoryGateError("source policy commitment drift")
    return source, raw


def load_deterministic_policy() -> tuple[dict[str, Any], bytes]:
    payload, raw = load_json_file(DETERMINISTIC_POLICY_PATH, "deterministic adjacent label policy")
    if sha256(raw) != EXPECTED_DETERMINISTIC_POLICY_SHA256:
        raise GeneratedAdjacentLabelInventoryGateError("deterministic policy digest drift")
    if payload.get("payload_commitment") != EXPECTED_DETERMINISTIC_POLICY_COMMITMENT:
        raise GeneratedAdjacentLabelInventoryGateError("deterministic policy commitment drift")
    try:
        deterministic_gate.validate_payload(payload)
    except deterministic_gate.DeterministicAdjacentLabelPolicyGateError as err:
        raise GeneratedAdjacentLabelInventoryGateError(f"deterministic policy invalid: {err}") from err
    return payload, raw


def rust_adjacent_adapter_modes(raw: bytes) -> list[dict[str, str]]:
    text = decode_utf8(raw, "rust native seq32 attention mlp source")
    rows = []
    pattern = re.compile(
        r'#\[serde\(rename = "(rmsnorm_input_fused_adjacent_[^"]+)"\)\]\s*'
        r"([A-Za-z0-9]+),",
        re.MULTILINE,
    )
    for adapter_mode, rust_enum_variant in pattern.findall(text):
        rows.append({"adapter_mode": adapter_mode, "rust_enum_variant": rust_enum_variant})
    if tuple(row["adapter_mode"] for row in rows) != EXPECTED_ADJACENT_MODES:
        raise GeneratedAdjacentLabelInventoryGateError("generated adapter mode drift")
    return rows


def cli_adjacent_commands(raw: bytes, mode_to_variant: dict[str, str]) -> list[dict[str, str]]:
    text = decode_utf8(raw, "cli native seq32 attention mlp source")
    pattern = re.compile(
        r'"(build-input-rmsnorm-fused-adjacent(?:-label-probe-[ab])?)"\s*=>\s*\{\s*'
        r"Some\(ZkAiNativeSeq32AttentionMlpAdapterMode::([A-Za-z0-9]+)\)",
        re.MULTILINE | re.DOTALL,
    )
    rows = []
    variant_to_mode = {variant: mode for mode, variant in mode_to_variant.items()}
    for command, rust_enum_variant in pattern.findall(text):
        adapter_mode = variant_to_mode.get(rust_enum_variant)
        if adapter_mode is None:
            raise GeneratedAdjacentLabelInventoryGateError("cli command adapter drift")
        rows.append(
            {
                "cli_command": command,
                "adapter_mode": adapter_mode,
                "rust_enum_variant": rust_enum_variant,
            }
        )
    rows.sort(key=lambda row: EXPECTED_CLI_COMMANDS.index(row["cli_command"]))
    if tuple(row["cli_command"] for row in rows) != EXPECTED_CLI_COMMANDS:
        raise GeneratedAdjacentLabelInventoryGateError("generated CLI command drift")
    if tuple(row["adapter_mode"] for row in rows) != EXPECTED_ADJACENT_MODES:
        raise GeneratedAdjacentLabelInventoryGateError("generated CLI adapter drift")
    return rows


def variants_by_id(source_policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    variants = {}
    for item in _list(source_policy.get("variants"), "source variants"):
        row = _dict(item, "source variant")
        variant_id = row.get("variant_id")
        if not isinstance(variant_id, str):
            raise GeneratedAdjacentLabelInventoryGateError("source variant id drift")
        variants[variant_id] = row
    return variants


def deterministic_rows_by_id(deterministic_policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = {}
    for item in _list(deterministic_policy.get("label_inventory"), "deterministic label inventory"):
        row = _dict(item, "deterministic label row")
        variant_id = row.get("variant_id")
        if not isinstance(variant_id, str):
            raise GeneratedAdjacentLabelInventoryGateError("deterministic row id drift")
        rows[variant_id] = row
    return rows


def source_artifact_rows(raws: dict[str, bytes], source_policy: dict[str, Any], deterministic_policy: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": "rust_native_seq32_attention_mlp_source",
            "path": RUST_SOURCE_PATH.relative_to(ROOT).as_posix(),
            "sha256": sha256(raws["rust"]),
            "size_bytes": len(raws["rust"]),
            "payload_commitment": None,
        },
        {
            "id": "cli_native_seq32_attention_mlp_source",
            "path": CLI_SOURCE_PATH.relative_to(ROOT).as_posix(),
            "sha256": sha256(raws["cli"]),
            "size_bytes": len(raws["cli"]),
            "payload_commitment": None,
        },
        {
            "id": "source_adjacent_label_policy",
            "path": deterministic_gate.SOURCE_POLICY_RELATIVE_PATH,
            "sha256": sha256(raws["source_policy"]),
            "size_bytes": len(raws["source_policy"]),
            "payload_commitment": source_policy["payload_commitment"],
        },
        {
            "id": "deterministic_adjacent_label_policy",
            "path": DETERMINISTIC_POLICY_PATH.relative_to(ROOT).as_posix(),
            "sha256": sha256(raws["deterministic_policy"]),
            "size_bytes": len(raws["deterministic_policy"]),
            "payload_commitment": deterministic_policy["payload_commitment"],
        },
    ]


def build_generated_label_inventory(
    source_policy: dict[str, Any],
    deterministic_policy: dict[str, Any],
    rust_modes: list[dict[str, str]],
    cli_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    source_rows = variants_by_id(source_policy)
    deterministic_rows = deterministic_rows_by_id(deterministic_policy)
    cli_by_mode = {row["adapter_mode"]: row for row in cli_rows}
    rows = []
    for mode_row in rust_modes:
        adapter_mode = mode_row["adapter_mode"]
        variant_id = ADAPTER_MODE_TO_LABEL_ID[adapter_mode]
        if variant_id not in source_rows or variant_id not in deterministic_rows:
            raise GeneratedAdjacentLabelInventoryGateError("generated label missing proof accounting")
        source_row = source_rows[variant_id]
        policy_row = deterministic_rows[variant_id]
        if source_row["adapter_mode"] != adapter_mode or policy_row["adapter_mode"] != adapter_mode:
            raise GeneratedAdjacentLabelInventoryGateError("generated label adapter drift")
        if policy_row["policy_status"] in ("supported_label", "rejected_inflating_label"):
            proof_accounting_pinned = True
        else:
            raise GeneratedAdjacentLabelInventoryGateError("generated label status drift")
        rows.append(
            {
                "variant_id": variant_id,
                "adapter_mode": adapter_mode,
                "rust_enum_variant": mode_row["rust_enum_variant"],
                "cli_command": cli_by_mode[adapter_mode]["cli_command"],
                "path": source_row["path"],
                "typed_bytes": source_row["typed_bytes"],
                "proof_json_bytes": source_row["proof_json_bytes"],
                "path_opening_bytes": policy_row["path_opening_bytes"],
                "value_bytes": source_row["value_bytes"],
                "typed_delta_vs_champion": policy_row["typed_delta_vs_champion"],
                "path_opening_delta_vs_champion": policy_row["path_opening_delta_vs_champion"],
                "policy_status": policy_row["policy_status"],
                "status_reason": policy_row["status_reason"],
                "proof_accounting_pinned": proof_accounting_pinned,
            }
        )
    return rows


def build_core_payload() -> dict[str, Any]:
    rust_raw = read_source(RUST_SOURCE_PATH, "rust native seq32 attention mlp source", EXPECTED_RUST_SOURCE_SHA256)
    cli_raw = read_source(CLI_SOURCE_PATH, "cli native seq32 attention mlp source", EXPECTED_CLI_SOURCE_SHA256)
    source_policy, source_policy_raw = load_source_policy()
    deterministic_policy, deterministic_policy_raw = load_deterministic_policy()
    rust_modes = rust_adjacent_adapter_modes(rust_raw)
    mode_to_variant = {row["adapter_mode"]: row["rust_enum_variant"] for row in rust_modes}
    cli_rows = cli_adjacent_commands(cli_raw, mode_to_variant)
    label_inventory = build_generated_label_inventory(source_policy, deterministic_policy, rust_modes, cli_rows)
    accepted = [row for row in label_inventory if row["policy_status"] == "supported_label"]
    rejected = [row for row in label_inventory if row["policy_status"].startswith("rejected")]
    worst_generated = max(label_inventory, key=lambda row: row["typed_bytes"])
    worst_accepted = max(accepted, key=lambda row: row["typed_bytes"])
    best_accepted = min(accepted, key=lambda row: row["typed_bytes"])
    generated_label_ids = [row["variant_id"] for row in label_inventory]
    accepted_label_ids = [row["variant_id"] for row in accepted]
    rejected_label_ids = [row["variant_id"] for row in rejected]
    raws = {
        "rust": rust_raw,
        "cli": cli_raw,
        "source_policy": source_policy_raw,
        "deterministic_policy": deterministic_policy_raw,
    }
    return {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "issue_hint": ISSUE_HINT,
        "source_artifacts": source_artifact_rows(raws, source_policy, deterministic_policy),
        "generator_policy": {
            "name": "rust_cli_generated_adjacent_label_inventory_v1",
            "source_rule": "Rust serde adapter modes with prefix rmsnorm_input_fused_adjacent_ plus matching CLI build-input-rmsnorm-fused-adjacent commands",
            "manual_override_allowed": False,
            "generated_adapter_modes": [row["adapter_mode"] for row in rust_modes],
            "generated_cli_commands": [row["cli_command"] for row in cli_rows],
            "generated_label_ids": generated_label_ids,
            "accepted_label_ids": accepted_label_ids,
            "rejected_label_ids": rejected_label_ids,
            "acceptance_criteria": [
                "adapter mode is generated from the pinned Rust adjacent family",
                "matching CLI build-input command exists",
                "proof/accounting row exists in the pinned source policy",
                "direct value bytes equal 20924",
                "path-opening bytes are below the 20592-byte champion path-opening budget",
                "typed bytes are below the 42068-byte champion typed budget",
            ],
            "rejection_criteria": [
                "adapter mode is absent from the pinned Rust adjacent family",
                "matching CLI build-input command is absent",
                "proof/accounting row is missing",
                "direct value bytes drift from 20924",
                "path-opening bytes are greater than or equal to 20592",
                "typed bytes are greater than or equal to 42068",
            ],
        },
        "generated_label_inventory": label_inventory,
        "rejected_unseen_labels": copy.deepcopy(list(EXPECTED_REJECTED_UNSEEN_LABELS)),
        "policy_summary": {
            "current_champion_typed_bytes": CURRENT_CHAMPION_TYPED_BYTES,
            "current_champion_path_opening_bytes": CURRENT_CHAMPION_PATH_OPENING_BYTES,
            "current_champion_value_bytes": CURRENT_CHAMPION_VALUE_BYTES,
            "generated_label_count": len(label_inventory),
            "accepted_label_count": len(accepted),
            "rejected_label_count": len(rejected),
            "full_generated_inventory_promotable_vs_current_champion": False,
            "full_generated_worst_label_id": worst_generated["variant_id"],
            "full_generated_worst_typed_bytes": worst_generated["typed_bytes"],
            "full_generated_miss_vs_champion_typed_bytes": worst_generated["typed_bytes"] - CURRENT_CHAMPION_TYPED_BYTES,
            "fixed_adjacent_path_opening_overhang_vs_champion": FIXED_PATH_OPENING_OVERHANG_BYTES,
            "worst_accepted_label_id": worst_accepted["variant_id"],
            "worst_accepted_typed_bytes": worst_accepted["typed_bytes"],
            "worst_accepted_saving_typed_bytes": CURRENT_CHAMPION_TYPED_BYTES - worst_accepted["typed_bytes"],
            "worst_accepted_saving_share": f"{(CURRENT_CHAMPION_TYPED_BYTES - worst_accepted['typed_bytes']) / CURRENT_CHAMPION_TYPED_BYTES:.6f}",
            "best_accepted_label_id": best_accepted["variant_id"],
            "best_accepted_typed_bytes": best_accepted["typed_bytes"],
            "best_accepted_saving_typed_bytes": CURRENT_CHAMPION_TYPED_BYTES - best_accepted["typed_bytes"],
            "accepted_value_bytes_stable": all(row["value_bytes"] == ADJACENT_VALUE_BYTES for row in accepted),
            "proof_size_comparable_external_rows": 0,
            "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
        },
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
        except GeneratedAdjacentLabelInventoryGateError as err:
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
        ("rust_source_digest_drift", lambda item: item["source_artifacts"][0].update({"sha256": "0" * 64})),
        ("cli_source_digest_drift", lambda item: item["source_artifacts"][1].update({"sha256": "0" * 64})),
        ("deterministic_policy_commitment_drift", lambda item: item["source_artifacts"][3].update({"payload_commitment": "blake2b-256:" + "0" * 64})),
        ("generated_mode_removed", lambda item: item["generator_policy"]["generated_adapter_modes"].pop()),
        ("generated_mode_extra", lambda item: item["generator_policy"]["generated_adapter_modes"].append("rmsnorm_input_fused_adjacent_label_probe_c_v1")),
        ("cli_command_drift", lambda item: item["generator_policy"]["generated_cli_commands"].__setitem__(1, "build-input-rmsnorm-fused-adjacent-label-probe-c")),
        ("accepted_label_erased", lambda item: item["generator_policy"]["accepted_label_ids"].remove("adjacent_label_probe_a")),
        ("fixed_label_accepted", lambda item: item["generated_label_inventory"][0].update({"policy_status": "supported_label"})),
        ("accepted_value_drift", lambda item: item["generated_label_inventory"][1].update({"value_bytes": CURRENT_CHAMPION_VALUE_BYTES})),
        ("accepted_typed_drift", lambda item: item["generated_label_inventory"][1].update({"typed_bytes": CURRENT_CHAMPION_TYPED_BYTES})),
        ("proof_accounting_erased", lambda item: item["generated_label_inventory"][2].update({"proof_accounting_pinned": False})),
        ("unseen_label_accepted", lambda item: item["rejected_unseen_labels"][0].update({"reason": "accepted"})),
        ("post_tail_cross_family_accepted", lambda item: item["rejected_unseen_labels"][1].update({"reason": "accepted"})),
        ("generator_rule_drift", lambda item: item["generator_policy"].update({"source_rule": "manual list"})),
        ("manual_override_enabled", lambda item: item["generator_policy"].update({"manual_override_allowed": True})),
        ("summary_worst_accepted_drift", lambda item: item["policy_summary"].update({"worst_accepted_typed_bytes": CURRENT_CHAMPION_TYPED_BYTES})),
        ("full_inventory_promoted", lambda item: item["policy_summary"].update({"full_generated_inventory_promotable_vs_current_champion": True})),
        ("validation_command_drift", lambda item: item["validation_commands"].append("echo untracked")),
        ("removed_non_claim", lambda item: item["non_claims"].remove("not a NANOZK proof-size win")),
        ("label_order_drift", lambda item: item["generated_label_inventory"].reverse()),
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
            raise GeneratedAdjacentLabelInventoryGateError(f"{key} drift")
    if "NANOZK_WIN" in str(payload.get("claim_boundary")).split(";"):
        raise GeneratedAdjacentLabelInventoryGateError("claim_boundary drift")
    expected = expected_payload_with_empty_mutations()
    validate_source_artifacts(_list(payload.get("source_artifacts"), "source artifacts"), expected["source_artifacts"])
    validate_generator_policy(_dict(payload.get("generator_policy"), "generator policy"), expected["generator_policy"])
    validate_generated_label_inventory(
        _list(payload.get("generated_label_inventory"), "generated label inventory"),
        expected["generated_label_inventory"],
    )
    if payload.get("rejected_unseen_labels") != expected["rejected_unseen_labels"]:
        raise GeneratedAdjacentLabelInventoryGateError("rejected unseen label drift")
    validate_policy_summary(_dict(payload.get("policy_summary"), "policy summary"), expected["policy_summary"])
    if payload.get("interpretation") != EXPECTED_INTERPRETATION:
        raise GeneratedAdjacentLabelInventoryGateError("interpretation drift")
    if payload.get("non_claims") != list(NON_CLAIMS):
        raise GeneratedAdjacentLabelInventoryGateError("non_claims drift")
    if payload.get("validation_commands") != list(VALIDATION_COMMANDS):
        raise GeneratedAdjacentLabelInventoryGateError("validation command drift")
    validate_mutation_result(_dict(payload.get("mutation_result"), "mutation result"))
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise GeneratedAdjacentLabelInventoryGateError("payload commitment drift")


def validate_source_artifacts(artifacts: list[Any], expected: list[dict[str, Any]]) -> None:
    for item in artifacts:
        _require_exact_keys(_dict(item, "source artifact"), SOURCE_ARTIFACT_KEYS, "source artifact")
    if artifacts != expected:
        raise GeneratedAdjacentLabelInventoryGateError("source artifact drift")


def validate_generator_policy(policy: dict[str, Any], expected: dict[str, Any]) -> None:
    _require_exact_keys(policy, GENERATOR_POLICY_KEYS, "generator policy")
    if policy.get("manual_override_allowed") is not False:
        raise GeneratedAdjacentLabelInventoryGateError("generator policy drift")
    if policy != expected:
        raise GeneratedAdjacentLabelInventoryGateError("generator policy drift")


def validate_generated_label_inventory(rows: list[Any], expected: list[dict[str, Any]]) -> None:
    for item in rows:
        _require_exact_keys(_dict(item, "generated label row"), LABEL_ROW_KEYS, "generated label row")
    if [row.get("variant_id") for row in rows] != [row["variant_id"] for row in expected]:
        raise GeneratedAdjacentLabelInventoryGateError("generated label order drift")
    if rows != expected:
        raise GeneratedAdjacentLabelInventoryGateError("generated label inventory drift")
    for row in rows:
        if row["policy_status"] == "supported_label":
            if row["value_bytes"] != ADJACENT_VALUE_BYTES:
                raise GeneratedAdjacentLabelInventoryGateError("generated label inventory drift")
            if row["typed_bytes"] >= CURRENT_CHAMPION_TYPED_BYTES:
                raise GeneratedAdjacentLabelInventoryGateError("generated label inventory drift")
            if row["path_opening_bytes"] >= CURRENT_CHAMPION_PATH_OPENING_BYTES:
                raise GeneratedAdjacentLabelInventoryGateError("generated label inventory drift")
        if not row["proof_accounting_pinned"]:
            raise GeneratedAdjacentLabelInventoryGateError("generated label inventory drift")


def validate_policy_summary(summary: dict[str, Any], expected: dict[str, Any]) -> None:
    _require_exact_keys(summary, SUMMARY_KEYS, "policy summary")
    if summary.get("full_generated_inventory_promotable_vs_current_champion") is not False:
        raise GeneratedAdjacentLabelInventoryGateError("policy summary drift")
    if summary != expected:
        raise GeneratedAdjacentLabelInventoryGateError("policy summary drift")


def validate_mutation_result(result: dict[str, Any]) -> None:
    _require_exact_keys(result, MUTATION_RESULT_KEYS, "mutation result")
    cases = _list(result.get("cases"), "mutation cases")
    for case in cases:
        _require_exact_keys(_dict(case, "mutation case"), MUTATION_CASE_KEYS, "mutation case")
    if result != expected_mutation_result():
        raise GeneratedAdjacentLabelInventoryGateError("mutation result drift")


def _tsv_cell(value: Any) -> str:
    text = str(value)
    if "\t" in text or "\n" in text or "\r" in text:
        raise GeneratedAdjacentLabelInventoryGateError("tsv audit field contains unsafe whitespace")
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
        "generated_label_ids": _join_tsv_items(
            _list(payload["generator_policy"]["generated_label_ids"], "generated label ids")
        ),
        "accepted_label_ids": _join_tsv_items(
            _list(payload["generator_policy"]["accepted_label_ids"], "accepted label ids")
        ),
        "rejected_label_ids": _join_tsv_items(
            _list(payload["generator_policy"]["rejected_label_ids"], "rejected label ids")
        ),
        "rejected_unseen_adapter_modes": _join_tsv_items(
            [
                row["adapter_mode"]
                for row in _list(payload["rejected_unseen_labels"], "rejected unseen labels")
            ]
        ),
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
    for row in payload["generated_label_inventory"]:
        row_columns = {
            column: row[column]
            for column in TSV_COLUMNS
            if column in LABEL_ROW_KEYS
        }
        writer.writerow({**row_columns, **audit_columns})
    return output.getvalue()


def atomic_write_text(path: pathlib.Path, text: str) -> None:
    try:
        source_gate.atomic_write_text(path, text)
    except source_gate.AdjacentLabelPolicyGateError as err:
        raise GeneratedAdjacentLabelInventoryGateError(str(err)) from err
    except Exception as err:
        raise GeneratedAdjacentLabelInventoryGateError(f"failed to write output: {err}") from err


def require_output_path(path: pathlib.Path) -> pathlib.Path:
    try:
        return source_gate.require_output_path(path)
    except source_gate.AdjacentLabelPolicyGateError as err:
        raise GeneratedAdjacentLabelInventoryGateError(str(err)) from err
    except Exception as err:
        raise GeneratedAdjacentLabelInventoryGateError(f"failed to prepare output path: {err}") from err


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
        except GeneratedAdjacentLabelInventoryGateError:
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
        raise GeneratedAdjacentLabelInventoryGateError(f"failed to read existing output: {err}") from err


def restore_outputs(previous: list[tuple[pathlib.Path, str | None]]) -> None:
    for path, text in previous:
        target = require_output_path(path)
        if text is None:
            try:
                if target.exists():
                    target.unlink()
            except OSError as err:
                raise GeneratedAdjacentLabelInventoryGateError(f"failed to roll back output: {err}") from err
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
        except GeneratedAdjacentLabelInventoryGateError:
            restore_outputs(previous)
            raise
    finally:
        cleanup_staged_outputs(staged)


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path | None, tsv_path: pathlib.Path | None) -> None:
    validate_payload(payload)
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
                "generated_label_count": payload["policy_summary"]["generated_label_count"],
                "worst_accepted_typed_bytes": payload["policy_summary"]["worst_accepted_typed_bytes"],
                "worst_accepted_saving_typed_bytes": payload["policy_summary"]["worst_accepted_saving_typed_bytes"],
                "mutations_rejected": payload["mutation_result"]["mutations_rejected"],
                "json_out": str(args.write_json) if args.write_json else None,
                "tsv_out": str(args.write_tsv) if args.write_tsv else None,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
