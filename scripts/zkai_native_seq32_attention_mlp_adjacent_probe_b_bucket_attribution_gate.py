#!/usr/bin/env python3.10
"""Attribute the adjacent probe-B seq32 attention+MLP transcript bucket."""

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
    raise RuntimeError(
        "zkai_native_seq32_attention_mlp_adjacent_probe_b_bucket_attribution_gate requires Python 3.10+"
    )

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
RUST_SOURCE_PATH = ROOT / "src" / "stwo_backend" / "native_seq32_attention_mlp_single_proof.rs"
CLI_SOURCE_PATH = ROOT / "src" / "bin" / "zkai_native_seq32_attention_mlp_single_proof.rs"
ACCOUNTING_PATH = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-accounting-2026-05.json"

SCHEMA = "zkai-native-seq32-attention-mlp-adjacent-probe-b-bucket-attribution-gate-v1"
DECISION = "NARROW_CLAIM_PATH_OPENING_BUCKET_ATTRIBUTED_NO_SOURCE_PREDICTOR"
RESULT = "PROBE_B_EDGE_VS_SEED_02_IS_2736_TYPED_BYTES_ALL_FROM_FRI_AND_TRACE_OPENING_GROUPS"
CLAIM_BOUNDARY = (
    "ATTRIBUTES_EXISTING_PROBE_B_TYPED_BYTE_EDGE;"
    "PATH_OPENING_BUCKET_ONLY;"
    "NO_SOURCE_EXPOSED_BUCKET_PREDICTOR;"
    "NOT_A_NEW_FRONTIER_NOT_A_NANOZK_COMPARISON_NOT_A_PRODUCTION_LABEL_POLICY"
)
PAYLOAD_DOMAIN = "ptvm:zkai:native-seq32-attention-mlp-adjacent-probe-b-bucket-attribution:v1"
ISSUE_HINT = "https://github.com/omarespejel/provable-transformer-vm/issues/693"
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

PATH_OPENING_GROUPS = ("fri_decommitments", "fri_samples", "trace_decommitments")
VALUE_GROUPS = ("oods_samples", "queries_values")
GROUPS = ("fixed_overhead", "fri_decommitments", "fri_samples", "oods_samples", "queries_values", "trace_decommitments")

EXPECTED_ROWS = (
    {
        "variant_id": "adjacent_label_probe_b",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_b_v1",
        "role": "frontier_bucket",
        "typed_bytes": 37_532,
        "json_proof_bytes": 106_317,
        "expected_groups": {
            "fixed_overhead": 48,
            "fri_decommitments": 10_240,
            "fri_samples": 688,
            "oods_samples": 11_984,
            "queries_values": 8_940,
            "trace_decommitments": 5_632,
        },
    },
    {
        "variant_id": "adjacent_seed_02",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-02-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_seed_02_v1",
        "role": "best_pre_registered_seed",
        "typed_bytes": 40_268,
        "json_proof_bytes": 115_995,
        "expected_groups": {
            "fixed_overhead": 48,
            "fri_decommitments": 12_256,
            "fri_samples": 768,
            "oods_samples": 11_984,
            "queries_values": 8_940,
            "trace_decommitments": 6_272,
        },
    },
    {
        "variant_id": "adjacent_seed_05",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-05-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_seed_05_v1",
        "role": "probe_a_shape_seed",
        "typed_bytes": 40_332,
        "json_proof_bytes": 116_303,
        "expected_groups": {
            "fixed_overhead": 48,
            "fri_decommitments": 12_320,
            "fri_samples": 768,
            "oods_samples": 11_984,
            "queries_values": 8_940,
            "trace_decommitments": 6_272,
        },
    },
    {
        "variant_id": "fixed_adjacent_layout",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_fixed_v1",
        "role": "fixed_adjacent_reference",
        "typed_bytes": 42_156,
        "json_proof_bytes": 122_688,
        "expected_groups": {
            "fixed_overhead": 48,
            "fri_decommitments": 13_696,
            "fri_samples": 832,
            "oods_samples": 11_984,
            "queries_values": 8_940,
            "trace_decommitments": 6_656,
        },
    },
)

EXPECTED_DELTAS = {
    "adjacent_seed_02": {
        "typed_delta": 2_736,
        "json_delta": 9_678,
        "path_opening_delta": 2_736,
        "value_delta": 0,
        "group_deltas": {"fri_decommitments": 2_016, "fri_samples": 80, "trace_decommitments": 640},
    },
    "adjacent_seed_05": {
        "typed_delta": 2_800,
        "json_delta": 9_986,
        "path_opening_delta": 2_800,
        "value_delta": 0,
        "group_deltas": {"fri_decommitments": 2_080, "fri_samples": 80, "trace_decommitments": 640},
    },
    "fixed_adjacent_layout": {
        "typed_delta": 4_624,
        "json_delta": 16_371,
        "path_opening_delta": 4_624,
        "value_delta": 0,
        "group_deltas": {"fri_decommitments": 3_456, "fri_samples": 144, "trace_decommitments": 1_024},
    },
}

VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_native_seq32_attention_mlp_adjacent_probe_b_bucket_attribution_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-probe-b-bucket-attribution-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-adjacent-probe-b-bucket-attribution-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_adjacent_probe_b_bucket_attribution_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_adjacent_probe_b_bucket_attribution_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_adjacent_probe_b_bucket_attribution_gate",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

NON_CLAIMS = (
    "not a new proof-size frontier beyond the 37,532 typed-byte adjacent probe B row",
    "not a source-exposed deterministic label policy",
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
    "frontier_typed_drift",
    "value_byte_drift",
    "seed_02_delta_drift",
    "source_predictor_promotion",
    "comparison_row_erasure",
    "record_stream_erasure",
    "removed_non_claim",
    "validation_command_drift",
    "payload_commitment_drift",
)


class AdjacentProbeBBucketAttributionGateError(Exception):
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
        raise AdjacentProbeBBucketAttributionGateError(f"{label} escapes repo root") from err
    current = root
    try:
        for part in relative.parts:
            current = current / part
            mode = current.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise AdjacentProbeBBucketAttributionGateError(f"{label} must not traverse symlinks")
        fd = os.open(candidate, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            opened_stat = os.fstat(fd)
            if not stat.S_ISREG(opened_stat.st_mode):
                raise AdjacentProbeBBucketAttributionGateError(f"{label} is not a regular file")
            if opened_stat.st_size > max_bytes:
                raise AdjacentProbeBBucketAttributionGateError(
                    f"{label} exceeds max size: got {opened_stat.st_size} bytes, limit {max_bytes} bytes"
                )
            with os.fdopen(fd, "rb") as handle:
                fd = None
                raw = handle.read(max_bytes + 1)
        finally:
            if fd is not None:
                os.close(fd)
    except OSError as err:
        raise AdjacentProbeBBucketAttributionGateError(f"failed to read {label}: {err}") from err
    if len(raw) > max_bytes:
        raise AdjacentProbeBBucketAttributionGateError(
            f"{label} exceeds max size: got at least {len(raw)} bytes, limit {max_bytes} bytes"
        )
    return raw


def read_json_object(path: pathlib.Path, label: str, max_bytes: int) -> tuple[dict[str, Any], bytes]:
    raw = read_bounded_repo_file(path, label, max_bytes)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as err:
        raise AdjacentProbeBBucketAttributionGateError(f"{label} is not valid JSON: {err}") from err
    if not isinstance(value, dict):
        raise AdjacentProbeBBucketAttributionGateError(f"{label} must be a JSON object")
    return value, raw


def source_artifact(path: pathlib.Path, artifact_id: str, expected_sha: str) -> dict[str, Any]:
    raw = read_bounded_repo_file(path, artifact_id, MAX_SOURCE_ARTIFACT_BYTES)
    digest = sha256_bytes(raw)
    if digest != expected_sha:
        raise AdjacentProbeBBucketAttributionGateError(f"{artifact_id} source digest drift")
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
        raise AdjacentProbeBBucketAttributionGateError("accounting digest drift")
    if data.get("schema") != "zkai-stwo-local-binary-proof-accounting-cli-v1":
        raise AdjacentProbeBBucketAttributionGateError("accounting schema drift")
    rows: dict[str, dict[str, Any]] = {}
    for row in data.get("rows", []):
        path = row.get("evidence_relative_path")
        if not isinstance(path, str):
            raise AdjacentProbeBBucketAttributionGateError("accounting row path missing")
        if path in rows:
            raise AdjacentProbeBBucketAttributionGateError(f"duplicate accounting path: {path}")
        rows[path] = row
    return rows


def _int_group(groups: dict[str, Any], name: str, variant_id: str) -> int:
    value = groups.get(name)
    if not isinstance(value, int):
        raise AdjacentProbeBBucketAttributionGateError(f"{variant_id} group {name} missing")
    return value


def proof_row(expected: dict[str, Any], accounting_row: dict[str, Any]) -> dict[str, Any]:
    envelope_path = EVIDENCE_DIR / expected["path"]
    envelope, raw = read_json_object(envelope_path, f"{expected['variant_id']} envelope", MAX_ENVELOPE_JSON_BYTES)
    proof = envelope.get("proof")
    if not isinstance(proof, list):
        raise AdjacentProbeBBucketAttributionGateError(f"{expected['variant_id']} proof field missing")
    envelope_input = envelope.get("input")
    if not isinstance(envelope_input, dict):
        raise AdjacentProbeBBucketAttributionGateError(f"{expected['variant_id']} envelope input missing")
    accounting = accounting_row.get("local_binary_accounting")
    if not isinstance(accounting, dict):
        raise AdjacentProbeBBucketAttributionGateError(f"{expected['variant_id']} accounting missing")
    groups = accounting.get("grouped_reconstruction")
    if not isinstance(groups, dict):
        raise AdjacentProbeBBucketAttributionGateError(f"{expected['variant_id']} grouped accounting missing")

    proof_len = len(proof)
    typed_bytes = accounting.get("typed_size_estimate_bytes")
    expected_groups = expected["expected_groups"]
    if envelope_input.get("adapter_mode") != expected["adapter_mode"]:
        raise AdjacentProbeBBucketAttributionGateError(f"{expected['variant_id']} adapter mode drift")
    if typed_bytes != expected["typed_bytes"]:
        raise AdjacentProbeBBucketAttributionGateError(f"{expected['variant_id']} typed bytes drift")
    if proof_len != expected["json_proof_bytes"]:
        raise AdjacentProbeBBucketAttributionGateError(f"{expected['variant_id']} JSON proof bytes drift")
    for name in GROUPS:
        if _int_group(groups, name, expected["variant_id"]) != expected_groups[name]:
            raise AdjacentProbeBBucketAttributionGateError(f"{expected['variant_id']} {name} drift")
    if accounting_row.get("proof_json_size_bytes") != proof_len:
        raise AdjacentProbeBBucketAttributionGateError(f"{expected['variant_id']} accounting proof length drift")
    if accounting_row.get("envelope_sha256") != sha256_bytes(raw):
        raise AdjacentProbeBBucketAttributionGateError(f"{expected['variant_id']} envelope digest drift")
    proof_bytes = bytes(int(value) for value in proof)
    if accounting_row.get("proof_sha256") != sha256_bytes(proof_bytes):
        raise AdjacentProbeBBucketAttributionGateError(f"{expected['variant_id']} proof digest drift")

    path_opening_bytes = sum(int(groups[name]) for name in PATH_OPENING_GROUPS)
    value_bytes = sum(int(groups[name]) for name in VALUE_GROUPS)
    if typed_bytes != int(groups["fixed_overhead"]) + path_opening_bytes + value_bytes:
        raise AdjacentProbeBBucketAttributionGateError(f"{expected['variant_id']} grouped sum drift")
    return {
        "variant_id": expected["variant_id"],
        "role": expected["role"],
        "adapter_mode": expected["adapter_mode"],
        "path": expected["path"],
        "proof_backend_version": accounting_row["envelope_metadata"]["proof_backend_version"],
        "typed_bytes": typed_bytes,
        "json_proof_bytes": proof_len,
        "groups": {name: int(groups[name]) for name in GROUPS},
        "path_opening_bytes": path_opening_bytes,
        "value_bytes": value_bytes,
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
            raise AdjacentProbeBBucketAttributionGateError(f"missing accounting row: {expected['path']}")
        rows.append(proof_row(expected, row))
    return rows


def row_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        variant_id = row["variant_id"]
        if variant_id in result:
            raise AdjacentProbeBBucketAttributionGateError(f"duplicate row: {variant_id}")
        result[variant_id] = row
    return result


def comparison_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = row_by_id(rows)
    frontier = by_id["adjacent_label_probe_b"]
    comparisons = []
    for variant_id in ("adjacent_seed_02", "adjacent_seed_05", "fixed_adjacent_layout"):
        row = by_id[variant_id]
        group_deltas = {name: row["groups"][name] - frontier["groups"][name] for name in GROUPS}
        path_delta = row["path_opening_bytes"] - frontier["path_opening_bytes"]
        value_delta = row["value_bytes"] - frontier["value_bytes"]
        typed_delta = row["typed_bytes"] - frontier["typed_bytes"]
        expected = EXPECTED_DELTAS[variant_id]
        expected_group_deltas = {name: 0 for name in GROUPS}
        expected_group_deltas.update(expected["group_deltas"])
        if typed_delta != expected["typed_delta"]:
            raise AdjacentProbeBBucketAttributionGateError(f"{variant_id} typed delta drift")
        if row["json_proof_bytes"] - frontier["json_proof_bytes"] != expected["json_delta"]:
            raise AdjacentProbeBBucketAttributionGateError(f"{variant_id} JSON delta drift")
        if path_delta != expected["path_opening_delta"]:
            raise AdjacentProbeBBucketAttributionGateError(f"{variant_id} path delta drift")
        if value_delta != expected["value_delta"]:
            raise AdjacentProbeBBucketAttributionGateError(f"{variant_id} value delta drift")
        if group_deltas != expected_group_deltas:
            raise AdjacentProbeBBucketAttributionGateError(f"{variant_id} group delta drift")
        if typed_delta != path_delta + value_delta + group_deltas["fixed_overhead"]:
            raise AdjacentProbeBBucketAttributionGateError(f"{variant_id} attribution sum drift")
        comparisons.append(
            {
                "variant_id": variant_id,
                "typed_delta_vs_probe_b": typed_delta,
                "json_delta_vs_probe_b": row["json_proof_bytes"] - frontier["json_proof_bytes"],
                "path_opening_delta_vs_probe_b": path_delta,
                "value_delta_vs_probe_b": value_delta,
                "group_deltas_vs_probe_b": group_deltas,
                "attribution": "all typed-byte gap is in FRI/sample/trace opening groups",
            }
        )
    return comparisons


def build_payload_without_mutations() -> dict[str, Any]:
    rows = build_rows()
    by_id = row_by_id(rows)
    frontier = by_id["adjacent_label_probe_b"]
    if frontier["typed_bytes"] != ADJACENT_PROBE_B_FRONTIER_TYPED_BYTES:
        raise AdjacentProbeBBucketAttributionGateError("probe B frontier drift")
    if frontier["json_proof_bytes"] != ADJACENT_PROBE_B_FRONTIER_JSON_BYTES:
        raise AdjacentProbeBBucketAttributionGateError("probe B JSON frontier drift")
    comparisons = comparison_rows(rows)
    best_seed_delta = next(item for item in comparisons if item["variant_id"] == "adjacent_seed_02")
    path_opening_delta_total = sum(item["path_opening_delta_vs_probe_b"] for item in comparisons)
    value_delta_total = sum(item["value_delta_vs_probe_b"] for item in comparisons)
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
        "proof_object_rows": rows,
        "bucket_attribution": {
            "frontier_variant_id": "adjacent_label_probe_b",
            "frontier_typed_bytes": frontier["typed_bytes"],
            "frontier_json_proof_bytes": frontier["json_proof_bytes"],
            "frontier_path_opening_bytes": frontier["path_opening_bytes"],
            "frontier_value_bytes": frontier["value_bytes"],
            "best_seed_id": "adjacent_seed_02",
            "best_seed_gap_typed_bytes": best_seed_delta["typed_delta_vs_probe_b"],
            "best_seed_gap_path_opening_bytes": best_seed_delta["path_opening_delta_vs_probe_b"],
            "best_seed_gap_value_bytes": best_seed_delta["value_delta_vs_probe_b"],
            "best_seed_group_gap_bytes": best_seed_delta["group_deltas_vs_probe_b"],
            "all_compared_rows_have_same_value_bytes": all(row["value_bytes"] == frontier["value_bytes"] for row in rows),
            "all_best_seed_gap_is_path_opening": True,
            "source_exposed_bucket_predictor": False,
            "prediction_status": "NO_GO_SOURCE_EXPOSED_BUCKET_PREDICTOR_ABSENT",
            "attribution_status": "GO_EXISTING_GAP_ATTRIBUTED_TO_OPENING_DECOMMITMENT_BUCKET",
            "path_opening_delta_total_across_comparisons": path_opening_delta_total,
            "value_delta_total_across_comparisons": value_delta_total,
            "current_two_proof_frontier_typed_bytes": CURRENT_TWO_PROOF_FRONTIER_TYPED_BYTES,
            "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
            "proof_size_comparable_external_rows": 0,
        },
        "comparisons_vs_probe_b": comparisons,
        "interpretation": {
            "human_read": (
                "Probe B is not smaller because it opens fewer direct values. "
                "The direct value payload is identical across the compared rows; "
                "the whole edge comes from fewer FRI, sample, and trace opening bytes."
            ),
            "mechanism_read": (
                "The favorable row is an opening/decommitment transcript bucket. "
                "That supports the proof-plumbing thesis, but it does not yet give "
                "a deterministic source-level label policy."
            ),
            "next_experiment": (
                "Expose or reconstruct query/opening inventory before proving, then test "
                "whether any source-visible rule predicts the smaller bucket without "
                "trying labels after the fact."
            ),
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
        ("frontier_typed_drift", lambda item: _row(item, "adjacent_label_probe_b").update({"typed_bytes": 37_000})),
        ("value_byte_drift", lambda item: _row(item, "adjacent_seed_02").update({"value_bytes": 20_000})),
        ("seed_02_delta_drift", lambda item: item["bucket_attribution"].update({"best_seed_gap_typed_bytes": 2_000})),
        ("source_predictor_promotion", lambda item: item["bucket_attribution"].update({"source_exposed_bucket_predictor": True})),
        ("comparison_row_erasure", lambda item: item["comparisons_vs_probe_b"].pop()),
        ("record_stream_erasure", lambda item: _row(item, "adjacent_label_probe_b").update({"record_stream_sha256": ""})),
        ("removed_non_claim", lambda item: item["non_claims"].remove("not a NANOZK proof-size win")),
        ("validation_command_drift", lambda item: item["validation_commands"].append("echo unchecked")),
        ("payload_commitment_drift", lambda item: item.update({"payload_commitment": "blake2b-256:" + "0" * 64})),
    )


def mutation_function_names() -> tuple[str, ...]:
    return tuple(name for name, _ in mutation_functions())


def ensure_mutation_inventory() -> None:
    actual = mutation_function_names()
    if actual != MUTATION_NAMES:
        raise AdjacentProbeBBucketAttributionGateError(
            f"mutation function inventory drift: expected {MUTATION_NAMES!r}, got {actual!r}"
        )


ensure_mutation_inventory()


def _row(payload: dict[str, Any], variant_id: str) -> dict[str, Any]:
    for row in payload["proof_object_rows"]:
        if row["variant_id"] == variant_id:
            return row
    raise AdjacentProbeBBucketAttributionGateError(f"missing row: {variant_id}")


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
                raise AdjacentProbeBBucketAttributionGateError("payload commitment drift")
        except AdjacentProbeBBucketAttributionGateError as error:
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
        raise AdjacentProbeBBucketAttributionGateError("mutation_result missing")
    if mutation.get("mutation_names") != list(MUTATION_NAMES):
        raise AdjacentProbeBBucketAttributionGateError("mutation inventory drift")
    if mutation.get("mutations_rejected") != len(MUTATION_NAMES) or not mutation.get("all_mutations_rejected"):
        raise AdjacentProbeBBucketAttributionGateError("mutation rejection drift")
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise AdjacentProbeBBucketAttributionGateError("payload commitment drift")


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
            raise AdjacentProbeBBucketAttributionGateError(f"{key} drift")
    if "NANOZK_WIN" in str(payload.get("claim_boundary")).split(";"):
        raise AdjacentProbeBBucketAttributionGateError("claim_boundary drift")
    for key in (
        "source_artifacts",
        "proof_object_rows",
        "bucket_attribution",
        "comparisons_vs_probe_b",
        "interpretation",
        "non_claims",
        "validation_commands",
    ):
        if payload.get(key) != expected[key]:
            raise AdjacentProbeBBucketAttributionGateError(f"{key} drift")


def render_tsv(payload: dict[str, Any]) -> str:
    fieldnames = [
        "variant_id",
        "typed_delta_vs_probe_b",
        "json_delta_vs_probe_b",
        "path_opening_delta_vs_probe_b",
        "value_delta_vs_probe_b",
        "fri_decommitments_delta",
        "fri_samples_delta",
        "trace_decommitments_delta",
        "payload_commitment",
        "decision",
        "result",
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in payload["comparisons_vs_probe_b"]:
        group_deltas = row["group_deltas_vs_probe_b"]
        writer.writerow(
            {
                "variant_id": row["variant_id"],
                "typed_delta_vs_probe_b": row["typed_delta_vs_probe_b"],
                "json_delta_vs_probe_b": row["json_delta_vs_probe_b"],
                "path_opening_delta_vs_probe_b": row["path_opening_delta_vs_probe_b"],
                "value_delta_vs_probe_b": row["value_delta_vs_probe_b"],
                "fri_decommitments_delta": group_deltas["fri_decommitments"],
                "fri_samples_delta": group_deltas["fri_samples"],
                "trace_decommitments_delta": group_deltas["trace_decommitments"],
                "payload_commitment": payload["payload_commitment"],
                "decision": payload["decision"],
                "result": payload["result"],
            }
        )
    return output.getvalue()


def require_output_path(path: pathlib.Path) -> pathlib.Path:
    target = pathlib.Path(os.path.abspath(path if path.is_absolute() else ROOT / path))
    evidence_root = EVIDENCE_DIR.resolve()
    try:
        relative = target.relative_to(evidence_root)
    except ValueError as err:
        raise AdjacentProbeBBucketAttributionGateError("output path escapes evidence dir") from err
    current = evidence_root
    for part in relative.parent.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except OSError as err:
            raise AdjacentProbeBBucketAttributionGateError(f"output parent must exist: {current}") from err
        if stat.S_ISLNK(mode):
            raise AdjacentProbeBBucketAttributionGateError("output path must not traverse symlinks")
        if not stat.S_ISDIR(mode):
            raise AdjacentProbeBBucketAttributionGateError(f"output parent must be directory: {current}")
    if target.is_symlink() or (target.exists() and target.is_dir()):
        raise AdjacentProbeBBucketAttributionGateError("output path must be a non-symlink file")
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
        raise AdjacentProbeBBucketAttributionGateError("could not create deterministic temp output")
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
    print(
        json.dumps(
            {
                "decision": payload["decision"],
                "probe_b_typed_bytes": payload["bucket_attribution"]["frontier_typed_bytes"],
                "best_seed_gap_typed_bytes": payload["bucket_attribution"]["best_seed_gap_typed_bytes"],
                "best_seed_gap_path_opening_bytes": payload["bucket_attribution"]["best_seed_gap_path_opening_bytes"],
                "best_seed_gap_value_bytes": payload["bucket_attribution"]["best_seed_gap_value_bytes"],
                "source_exposed_bucket_predictor": payload["bucket_attribution"]["source_exposed_bucket_predictor"],
                "mutations_rejected": payload["mutation_result"]["mutations_rejected"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
