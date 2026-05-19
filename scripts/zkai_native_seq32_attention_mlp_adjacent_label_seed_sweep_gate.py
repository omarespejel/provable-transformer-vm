#!/usr/bin/env python3.10
"""Gate the pre-registered adjacent-only seq32 attention+MLP label seed sweep."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import os
import pathlib
import stat
import sys
from collections.abc import Callable
from typing import Any


if sys.version_info < (3, 10):
    raise RuntimeError("zkai_native_seq32_attention_mlp_adjacent_label_seed_sweep_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
RUST_SOURCE_PATH = ROOT / "src" / "stwo_backend" / "native_seq32_attention_mlp_single_proof.rs"
CLI_SOURCE_PATH = ROOT / "src" / "bin" / "zkai_native_seq32_attention_mlp_single_proof.rs"
ACCOUNTING_PATH = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-accounting-2026-05.json"

SCHEMA = "zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-gate-v1"
DECISION = "NO_GO_PRE_REGISTERED_ADJACENT_SEEDS_DO_NOT_BEAT_FRONTIER"
RESULT = "BEST_SEED_02_IS_40268_TYPED_BYTES_VS_37532_FRONTIER_WITH_2736_BYTE_GAP"
CLAIM_BOUNDARY = (
    "PRE_REGISTERED_ADJACENT_ONLY_LABEL_SEED_SWEEP;"
    "REPORTS_ALL_SEEDS_NOT_ONLY_WINNERS;"
    "NOT_A_FRONTIER_WIN_NOT_A_NANOZK_COMPARISON_NOT_A_PRODUCTION_LABEL_POLICY"
)
PAYLOAD_DOMAIN = "ptvm:zkai:native-seq32-attention-mlp-adjacent-label-seed-sweep:v1"
ISSUE_HINT = "pre-registered-adjacent-label-seed-sweep"
DETERMINISTIC_TEMP_ATTEMPTS = 16
MAX_SOURCE_ARTIFACT_BYTES = 768 * 1024
MAX_ACCOUNTING_JSON_BYTES = 2 * 1024 * 1024
MAX_ENVELOPE_JSON_BYTES = 8 * 1024 * 1024

EXPECTED_RUST_SOURCE_SHA256 = "35014074e972386ef8e1b261bb407eb842fc1b98037f4cac1f4da1a7e52cf6fb"
EXPECTED_CLI_SOURCE_SHA256 = "6515f8a3e05661dc267b4c106d2e06d576d4f74d39bcc0821c892ac7e3b4bdac"
EXPECTED_ACCOUNTING_SHA256 = "90f04ada7e02f3777615417dec475c27ccff3511f42be0a084e6405b52fcd6db"

ADJACENT_PROBE_B_FRONTIER_TYPED_BYTES = 37_532
ADJACENT_PROBE_B_FRONTIER_JSON_BYTES = 106_317
CURRENT_TWO_PROOF_FRONTIER_TYPED_BYTES = 47_188
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900
PRE_REGISTERED_SEED_IDS = (
    "adjacent_seed_00",
    "adjacent_seed_01",
    "adjacent_seed_02",
    "adjacent_seed_03",
    "adjacent_seed_04",
    "adjacent_seed_05",
)
PATH_OPENING_GROUPS = ("fri_decommitments", "fri_samples", "trace_decommitments")
VALUE_GROUPS = ("oods_samples", "queries_values")

EXPECTED_ROWS = (
    {
        "variant_id": "fixed_adjacent_layout",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_fixed_v1",
        "family": "adjacent_reference",
        "policy_status": "reference_layout",
        "typed_bytes": 42_156,
        "json_proof_bytes": 122_688,
    },
    {
        "variant_id": "adjacent_label_probe_a",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_a_v1",
        "family": "adjacent_existing_probe",
        "policy_status": "existing_non_frontier_probe",
        "typed_bytes": 40_332,
        "json_proof_bytes": 116_321,
    },
    {
        "variant_id": "adjacent_label_probe_b",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_b_v1",
        "family": "adjacent_existing_probe",
        "policy_status": "current_frontier",
        "typed_bytes": 37_532,
        "json_proof_bytes": 106_317,
    },
    {
        "variant_id": "adjacent_seed_00",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-00-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_seed_00_v1",
        "family": "pre_registered_seed",
        "policy_status": "seed_no_go",
        "typed_bytes": 41_484,
        "json_proof_bytes": 120_158,
    },
    {
        "variant_id": "adjacent_seed_01",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-01-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_seed_01_v1",
        "family": "pre_registered_seed",
        "policy_status": "seed_no_go",
        "typed_bytes": 41_484,
        "json_proof_bytes": 120_064,
    },
    {
        "variant_id": "adjacent_seed_02",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-02-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_seed_02_v1",
        "family": "pre_registered_seed",
        "policy_status": "best_seed_but_no_go",
        "typed_bytes": 40_268,
        "json_proof_bytes": 115_995,
    },
    {
        "variant_id": "adjacent_seed_03",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-03-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_seed_03_v1",
        "family": "pre_registered_seed",
        "policy_status": "seed_no_go",
        "typed_bytes": 42_156,
        "json_proof_bytes": 122_588,
    },
    {
        "variant_id": "adjacent_seed_04",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-04-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_seed_04_v1",
        "family": "pre_registered_seed",
        "policy_status": "seed_no_go",
        "typed_bytes": 42_156,
        "json_proof_bytes": 122_648,
    },
    {
        "variant_id": "adjacent_seed_05",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-05-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_seed_05_v1",
        "family": "pre_registered_seed",
        "policy_status": "seed_no_go",
        "typed_bytes": 40_332,
        "json_proof_bytes": 116_303,
    },
)

VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent-seed-00 docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-00-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-00-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-00-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-00-2026-05.envelope.json",
    "repeat the same build/prove/verify pattern for adjacent seeds 01 through 05",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-00-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-01-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-02-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-03-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-04-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-05-2026-05.envelope.json > docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-accounting-2026-05.json",
    "python3.10 scripts/zkai_native_seq32_attention_mlp_adjacent_label_seed_sweep_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_adjacent_label_seed_sweep_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_adjacent_label_seed_sweep_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_adjacent_label_seed_sweep_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_adjacent_seed --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

NON_CLAIMS = (
    "not a new proof-size frontier beyond the 37,532 typed-byte adjacent probe B row",
    "not a production label-selection policy",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not a full transformer block proof",
    "not exact real-valued Softmax",
    "not timing evidence",
    "not production-ready zkML",
)

MUTATION_NAMES = (
    "decision_drift",
    "claim_boundary_overclaim",
    "source_digest_drift",
    "accounting_digest_drift",
    "seed_inventory_erasure",
    "frontier_promotion",
    "best_seed_typed_drift",
    "adapter_mode_relabeling",
    "path_opening_mechanism_drift",
    "shape_class_erasure",
    "removed_non_claim",
    "validation_command_drift",
    "payload_commitment_drift",
)


class AdjacentSeedSweepGateError(Exception):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def payload_commitment(payload: dict[str, Any]) -> str:
    item = copy.deepcopy(payload)
    item.pop("payload_commitment", None)
    raw = json.dumps(item, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.blake2b(PAYLOAD_DOMAIN.encode() + b"\0" + raw, digest_size=32).hexdigest()
    return f"blake2b-256:{digest}"


def read_bounded_repo_file(path: pathlib.Path, label: str, max_bytes: int) -> bytes:
    root = ROOT.resolve()
    candidate = pathlib.Path(os.path.abspath(path if path.is_absolute() else ROOT / path))
    try:
        relative = candidate.relative_to(root)
    except ValueError as err:
        raise AdjacentSeedSweepGateError(f"{label} escapes repo root") from err
    current = root
    try:
        for part in relative.parts:
            current = current / part
            mode = current.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise AdjacentSeedSweepGateError(f"{label} must not traverse symlinks")
        fd = os.open(candidate, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            opened_stat = os.fstat(fd)
            if not stat.S_ISREG(opened_stat.st_mode):
                raise AdjacentSeedSweepGateError(f"{label} is not a regular file")
            if opened_stat.st_size > max_bytes:
                raise AdjacentSeedSweepGateError(
                    f"{label} exceeds max size: got {opened_stat.st_size} bytes, limit {max_bytes} bytes"
                )
            with os.fdopen(fd, "rb") as handle:
                fd = None
                raw = handle.read(max_bytes + 1)
        finally:
            if fd is not None:
                os.close(fd)
    except OSError as err:
        raise AdjacentSeedSweepGateError(f"failed to read {label}: {err}") from err
    if len(raw) > max_bytes:
        raise AdjacentSeedSweepGateError(
            f"{label} exceeds max size: got at least {len(raw)} bytes, limit {max_bytes} bytes"
        )
    return raw


def read_json_object(path: pathlib.Path, label: str, max_bytes: int) -> tuple[dict[str, Any], bytes]:
    raw = read_bounded_repo_file(path, label, max_bytes)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as err:
        raise AdjacentSeedSweepGateError(f"{label} is not valid JSON: {err}") from err
    if not isinstance(value, dict):
        raise AdjacentSeedSweepGateError(f"{label} must be a JSON object")
    return value, raw


def source_artifact(path: pathlib.Path, artifact_id: str, expected_sha: str) -> dict[str, Any]:
    raw = read_bounded_repo_file(path, artifact_id, MAX_SOURCE_ARTIFACT_BYTES)
    digest = sha256_bytes(raw)
    if digest != expected_sha:
        raise AdjacentSeedSweepGateError(f"{artifact_id} source digest drift")
    return {
        "id": artifact_id,
        "path": str(path.relative_to(ROOT)),
        "sha256": digest,
        "size_bytes": len(raw),
    }


def accounting_rows_by_path() -> dict[str, dict[str, Any]]:
    data, raw = read_json_object(ACCOUNTING_PATH, "adjacent seed-sweep accounting", MAX_ACCOUNTING_JSON_BYTES)
    digest = sha256_bytes(raw)
    if digest != EXPECTED_ACCOUNTING_SHA256:
        raise AdjacentSeedSweepGateError("accounting digest drift")
    if data.get("schema") != "zkai-stwo-local-binary-proof-accounting-cli-v1":
        raise AdjacentSeedSweepGateError("accounting schema drift")
    rows: dict[str, dict[str, Any]] = {}
    for row in data.get("rows", []):
        path = row.get("evidence_relative_path")
        if not isinstance(path, str):
            raise AdjacentSeedSweepGateError("accounting row path missing")
        if path in rows:
            raise AdjacentSeedSweepGateError(f"duplicate accounting path: {path}")
        rows[path] = row
    return rows


def proof_row(expected: dict[str, Any], accounting_row: dict[str, Any]) -> dict[str, Any]:
    envelope_path = EVIDENCE_DIR / expected["path"]
    envelope, raw = read_json_object(envelope_path, f"{expected['variant_id']} envelope", MAX_ENVELOPE_JSON_BYTES)
    proof = envelope.get("proof")
    if not isinstance(proof, list):
        raise AdjacentSeedSweepGateError(f"{expected['variant_id']} proof field missing")
    envelope_input = envelope.get("input")
    if not isinstance(envelope_input, dict):
        raise AdjacentSeedSweepGateError(f"{expected['variant_id']} envelope input missing")
    accounting = accounting_row.get("local_binary_accounting")
    if not isinstance(accounting, dict):
        raise AdjacentSeedSweepGateError(f"{expected['variant_id']} accounting missing")
    groups = accounting.get("grouped_reconstruction")
    if not isinstance(groups, dict):
        raise AdjacentSeedSweepGateError(f"{expected['variant_id']} grouped accounting missing")

    proof_len = len(proof)
    typed_bytes = accounting.get("typed_size_estimate_bytes")
    if envelope_input.get("adapter_mode") != expected["adapter_mode"]:
        raise AdjacentSeedSweepGateError(f"{expected['variant_id']} adapter mode drift")
    if typed_bytes != expected["typed_bytes"]:
        raise AdjacentSeedSweepGateError(f"{expected['variant_id']} typed bytes drift")
    if proof_len != expected["json_proof_bytes"]:
        raise AdjacentSeedSweepGateError(f"{expected['variant_id']} JSON proof bytes drift")
    if accounting_row.get("proof_json_size_bytes") != proof_len:
        raise AdjacentSeedSweepGateError(f"{expected['variant_id']} accounting proof length drift")
    if accounting_row.get("envelope_sha256") != sha256_bytes(raw):
        raise AdjacentSeedSweepGateError(f"{expected['variant_id']} envelope digest drift")
    proof_bytes = bytes(int(value) for value in proof)
    if accounting_row.get("proof_sha256") != sha256_bytes(proof_bytes):
        raise AdjacentSeedSweepGateError(f"{expected['variant_id']} proof digest drift")

    path_opening_bytes = sum(int(groups[name]) for name in PATH_OPENING_GROUPS)
    value_bytes = sum(int(groups[name]) for name in VALUE_GROUPS)
    return {
        "variant_id": expected["variant_id"],
        "family": expected["family"],
        "policy_status": expected["policy_status"],
        "adapter_mode": expected["adapter_mode"],
        "path": expected["path"],
        "proof_backend_version": accounting_row["envelope_metadata"]["proof_backend_version"],
        "typed_bytes": typed_bytes,
        "json_proof_bytes": proof_len,
        "path_opening_bytes": path_opening_bytes,
        "value_bytes": value_bytes,
        "typed_delta_vs_adjacent_probe_b": typed_bytes - ADJACENT_PROBE_B_FRONTIER_TYPED_BYTES,
        "json_delta_vs_adjacent_probe_b": proof_len - ADJACENT_PROBE_B_FRONTIER_JSON_BYTES,
        "envelope_sha256": accounting_row["envelope_sha256"],
        "proof_sha256": accounting_row["proof_sha256"],
        "record_stream_sha256": accounting["record_stream_sha256"],
    }


def build_rows() -> list[dict[str, Any]]:
    accounting = accounting_rows_by_path()
    rows = []
    for expected in EXPECTED_ROWS:
        row = accounting.get(expected["path"])
        if row is None:
            raise AdjacentSeedSweepGateError(f"missing accounting row: {expected['path']}")
        rows.append(proof_row(expected, row))
    return rows


def shape_classes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    classes: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        classes.setdefault(row["record_stream_sha256"], []).append(row)
    result = []
    for digest, members in sorted(classes.items(), key=lambda item: min(row["typed_bytes"] for row in item[1])):
        result.append(
            {
                "record_stream_sha256": digest,
                "variant_ids": [row["variant_id"] for row in members],
                "typed_bytes": members[0]["typed_bytes"],
                "path_opening_bytes": members[0]["path_opening_bytes"],
            }
        )
    return result


def median(values: list[int]) -> int:
    if not values:
        raise AdjacentSeedSweepGateError("median requires values")
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) // 2


def build_payload_without_mutations() -> dict[str, Any]:
    rows = build_rows()
    seed_rows = [row for row in rows if row["variant_id"] in PRE_REGISTERED_SEED_IDS]
    if [row["variant_id"] for row in seed_rows] != list(PRE_REGISTERED_SEED_IDS):
        raise AdjacentSeedSweepGateError("seed inventory drift")
    adjacent_frontier = next(row for row in rows if row["variant_id"] == "adjacent_label_probe_b")
    if adjacent_frontier["typed_bytes"] != ADJACENT_PROBE_B_FRONTIER_TYPED_BYTES:
        raise AdjacentSeedSweepGateError("adjacent frontier drift")
    best_seed = min(seed_rows, key=lambda row: row["typed_bytes"])
    if best_seed["typed_bytes"] <= adjacent_frontier["typed_bytes"]:
        raise AdjacentSeedSweepGateError("seed unexpectedly beats adjacent frontier")

    seed_typed = [int(row["typed_bytes"]) for row in seed_rows]
    seed_shape_classes = shape_classes(seed_rows)
    payload = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "issue_hint": ISSUE_HINT,
        "source_artifacts": [
            source_artifact(RUST_SOURCE_PATH, "rust_native_seq32_attention_mlp_source", EXPECTED_RUST_SOURCE_SHA256),
            source_artifact(CLI_SOURCE_PATH, "cli_native_seq32_attention_mlp_source", EXPECTED_CLI_SOURCE_SHA256),
            source_artifact(ACCOUNTING_PATH, "adjacent_label_seed_sweep_accounting", EXPECTED_ACCOUNTING_SHA256),
        ],
        "seed_policy": {
            "pre_registered": True,
            "seed_ids": list(PRE_REGISTERED_SEED_IDS),
            "seed_count": len(PRE_REGISTERED_SEED_IDS),
            "reporting_rule": "report every generated seed row whether it wins or loses",
            "promotion_rule": "a seed must verify and beat the 37,532 typed-byte adjacent probe B frontier before promotion",
        },
        "proof_object_rows": rows,
        "frontier_summary": {
            "current_two_proof_frontier_typed_bytes": CURRENT_TWO_PROOF_FRONTIER_TYPED_BYTES,
            "adjacent_probe_b_frontier_typed_bytes": ADJACENT_PROBE_B_FRONTIER_TYPED_BYTES,
            "adjacent_probe_b_frontier_json_bytes": ADJACENT_PROBE_B_FRONTIER_JSON_BYTES,
            "best_seed_id": best_seed["variant_id"],
            "best_seed_typed_bytes": best_seed["typed_bytes"],
            "best_seed_json_bytes": best_seed["json_proof_bytes"],
            "best_seed_gap_vs_adjacent_probe_b_typed_bytes": best_seed["typed_bytes"] - adjacent_frontier["typed_bytes"],
            "seed_min_typed_bytes": min(seed_typed),
            "seed_median_typed_bytes": median(seed_typed),
            "seed_worst_typed_bytes": max(seed_typed),
            "seed_span_typed_bytes": max(seed_typed) - min(seed_typed),
            "seed_promotable": False,
            "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
            "proof_size_comparable_external_rows": 0,
        },
        "shape_classes": seed_shape_classes,
        "interpretation": {
            "human_read": "The pre-registered adjacent seeds verified, but none reproduced the 37,532 typed-byte adjacent probe B frontier.",
            "mechanism_read": "Seed labels fall into repeated record-stream shape classes, so blind label seeding is not a robust compression mechanism yet.",
            "next_experiment": "Stop broad seed guessing; inspect the query/opening transcript bucket that makes adjacent probe B special.",
        },
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
        "mutation_result": {"all_mutations_rejected": True, "mutations_rejected": 0, "cases": []},
    }
    return payload


def build_payload() -> dict[str, Any]:
    payload = build_payload_without_mutations()
    payload["mutation_result"] = mutation_result(payload)
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload)
    return payload


def mutation_functions() -> tuple[tuple[str, Callable[[dict[str, Any]], None]], ...]:
    return (
        ("decision_drift", lambda item: item.update({"decision": "GO"})),
        ("claim_boundary_overclaim", lambda item: item.update({"claim_boundary": item["claim_boundary"] + ";NANOZK_WIN"})),
        ("source_digest_drift", lambda item: item["source_artifacts"][0].update({"sha256": "0" * 64})),
        ("accounting_digest_drift", lambda item: item["source_artifacts"][2].update({"sha256": "0" * 64})),
        ("seed_inventory_erasure", lambda item: item["seed_policy"].update({"seed_ids": item["seed_policy"]["seed_ids"][:-1]})),
        ("frontier_promotion", lambda item: item["frontier_summary"].update({"seed_promotable": True})),
        ("best_seed_typed_drift", lambda item: _row(item, "adjacent_seed_02").update({"typed_bytes": 37_000})),
        ("adapter_mode_relabeling", lambda item: _row(item, "adjacent_seed_02").update({"adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_b_v1"})),
        ("path_opening_mechanism_drift", lambda item: _row(item, "adjacent_seed_02").update({"path_opening_bytes": 1})),
        ("shape_class_erasure", lambda item: item.update({"shape_classes": []})),
        ("removed_non_claim", lambda item: item["non_claims"].remove("not a NANOZK proof-size win")),
        ("validation_command_drift", lambda item: item["validation_commands"].append("echo unchecked")),
        ("payload_commitment_drift", lambda item: item.update({"payload_commitment": "blake2b-256:" + "0" * 64})),
    )


def mutation_function_names() -> tuple[str, ...]:
    return tuple(name for name, _ in mutation_functions())


def ensure_mutation_inventory() -> None:
    actual = mutation_function_names()
    if actual != MUTATION_NAMES:
        raise AdjacentSeedSweepGateError(
            f"mutation function inventory drift: expected {MUTATION_NAMES!r}, got {actual!r}"
        )


ensure_mutation_inventory()


def _row(payload: dict[str, Any], variant_id: str) -> dict[str, Any]:
    for row in payload["proof_object_rows"]:
        if row["variant_id"] == variant_id:
            return row
    raise AdjacentSeedSweepGateError(f"missing row: {variant_id}")


def mutation_result(payload: dict[str, Any]) -> dict[str, Any]:
    ensure_mutation_inventory()
    cases = []
    for name, mutate in mutation_functions():
        item = copy.deepcopy(payload)
        item.pop("payload_commitment", None)
        item["mutation_result"] = {"all_mutations_rejected": True, "mutations_rejected": 0, "cases": []}
        mutate(item)
        if name != "payload_commitment_drift":
            item["payload_commitment"] = payload_commitment(item)
        try:
            validate_payload_core(item)
            if item.get("payload_commitment") != payload_commitment(item):
                raise AdjacentSeedSweepGateError("payload commitment drift")
        except AdjacentSeedSweepGateError as error:
            cases.append({"name": name, "rejected": True, "error": str(error)})
        else:
            cases.append({"name": name, "rejected": False, "error": ""})
    return {
        "all_mutations_rejected": all(case["rejected"] for case in cases),
        "mutations_rejected": sum(1 for case in cases if case["rejected"]),
        "mutation_names": list(MUTATION_NAMES),
        "cases": cases,
    }


def validate_payload(payload: dict[str, Any]) -> None:
    ensure_mutation_inventory()
    validate_payload_core(payload)
    mutation = payload.get("mutation_result")
    if not isinstance(mutation, dict):
        raise AdjacentSeedSweepGateError("mutation_result missing")
    if mutation.get("mutation_names") != list(MUTATION_NAMES):
        raise AdjacentSeedSweepGateError("mutation inventory drift")
    if mutation.get("mutations_rejected") != len(MUTATION_NAMES) or not mutation.get("all_mutations_rejected"):
        raise AdjacentSeedSweepGateError("mutation rejection drift")
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise AdjacentSeedSweepGateError("payload commitment drift")


def validate_payload_core(payload: dict[str, Any]) -> None:
    expected = build_payload_without_mutations()
    for key, value in {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "issue_hint": ISSUE_HINT,
    }.items():
        if payload.get(key) != value:
            raise AdjacentSeedSweepGateError(f"{key} drift")
    if "NANOZK_WIN" in str(payload.get("claim_boundary")).split(";"):
        raise AdjacentSeedSweepGateError("claim_boundary drift")
    for key in (
        "source_artifacts",
        "seed_policy",
        "proof_object_rows",
        "frontier_summary",
        "shape_classes",
        "interpretation",
        "non_claims",
        "validation_commands",
    ):
        if payload.get(key) != expected[key]:
            raise AdjacentSeedSweepGateError(f"{key} drift")


def render_tsv(payload: dict[str, Any]) -> str:
    fieldnames = [
        "variant_id",
        "family",
        "policy_status",
        "adapter_mode",
        "typed_bytes",
        "json_proof_bytes",
        "typed_delta_vs_adjacent_probe_b",
        "path_opening_bytes",
        "value_bytes",
        "record_stream_sha256",
        "payload_commitment",
        "decision",
        "result",
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in payload["proof_object_rows"]:
        writer.writerow({key: row.get(key, payload.get(key, "")) for key in fieldnames})
    return output.getvalue()


def require_output_path(path: pathlib.Path) -> pathlib.Path:
    target = pathlib.Path(os.path.abspath(path if path.is_absolute() else ROOT / path))
    evidence_root = EVIDENCE_DIR.resolve()
    try:
        relative = target.relative_to(evidence_root)
    except ValueError as err:
        raise AdjacentSeedSweepGateError("output path escapes evidence dir") from err
    current = evidence_root
    for part in relative.parent.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except OSError as err:
            raise AdjacentSeedSweepGateError(f"output parent must exist: {current}") from err
        if stat.S_ISLNK(mode):
            raise AdjacentSeedSweepGateError("output path must not traverse symlinks")
        if not stat.S_ISDIR(mode):
            raise AdjacentSeedSweepGateError(f"output parent must be directory: {current}")
    if target.is_symlink() or (target.exists() and target.is_dir()):
        raise AdjacentSeedSweepGateError("output path must be a non-symlink file")
    return target


def atomic_write(path: pathlib.Path, text: str) -> None:
    target = require_output_path(path)
    parent_fd = os.open(
        target.parent,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        for attempt in range(DETERMINISTIC_TEMP_ATTEMPTS):
            tmp_name = f".{target.name}.tmp.{attempt}"
            tmp_created = False
            fd: int | None = None
            try:
                fd = os.open(
                    tmp_name,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=parent_fd,
                )
            except FileExistsError:
                continue
            try:
                tmp_created = True
                try:
                    handle = os.fdopen(fd, "w", encoding="utf-8", newline="")
                except Exception:
                    os.close(fd)
                    fd = None
                    raise
                fd = None
                with handle:
                    handle.write(text)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(tmp_name, target.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
                os.fsync(parent_fd)
                return
            except Exception:
                if fd is not None:
                    os.close(fd)
                if tmp_created:
                    try:
                        os.unlink(tmp_name, dir_fd=parent_fd)
                    except FileNotFoundError:
                        pass
                raise
        raise AdjacentSeedSweepGateError("could not create deterministic temp output")
    finally:
        os.close(parent_fd)


def write_outputs(json_path: pathlib.Path, tsv_path: pathlib.Path, payload: dict[str, Any]) -> None:
    atomic_write(json_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    atomic_write(tsv_path, render_tsv(payload))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    args = parser.parse_args()
    if bool(args.write_json) != bool(args.write_tsv):
        raise SystemExit("--write-json and --write-tsv must be provided together")
    payload = build_payload()
    if args.write_json and args.write_tsv:
        write_outputs(args.write_json, args.write_tsv, payload)
    print(json.dumps({
        "decision": payload["decision"],
        "best_seed_id": payload["frontier_summary"]["best_seed_id"],
        "best_seed_typed_bytes": payload["frontier_summary"]["best_seed_typed_bytes"],
        "best_seed_gap_vs_adjacent_probe_b_typed_bytes": payload["frontier_summary"]["best_seed_gap_vs_adjacent_probe_b_typed_bytes"],
        "seed_median_typed_bytes": payload["frontier_summary"]["seed_median_typed_bytes"],
        "seed_shape_class_count": len(payload["shape_classes"]),
        "mutations_rejected": payload["mutation_result"]["mutations_rejected"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
