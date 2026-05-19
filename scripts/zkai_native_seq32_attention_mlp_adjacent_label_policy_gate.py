#!/usr/bin/env python3.10
"""Gate seq32 adjacent-layout label probes for the native attention+MLP proof."""

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
    raise RuntimeError("zkai_native_seq32_attention_mlp_adjacent_label_policy_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"

ACCOUNTING_PATH = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-accounting-2026-05.json"
JSON_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-policy-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-policy-2026-05.tsv"

SCHEMA = "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-policy-gate-v1"
DECISION = "GO_ADJACENT_LABEL_PROBES_BEAT_CURRENT_SEQ32_CHAMPION"
RESULT = "WORST_CHECKED_ADJACENT_LABEL_PROBE_SAVES_1736_TYPED_BYTES_VS_42068_CHAMPION"
CLAIM_BOUNDARY = (
    "TWO_EXISTING_RMSNORM_ADJACENT_LABEL_PROBES_VERIFY_AND_BOTH_BEAT_THE_CURRENT_LOCAL_"
    "SEQ32_D128_NATIVE_CHAMPION;NOT_A_NANOZK_WIN_NOT_A_FINAL_LABEL_POLICY_NOT_AN_EXTERNAL_BENCHMARK"
)
ISSUE_HINT = "seq32-adjacent-opening-stability"
PAYLOAD_DOMAIN = "ptvm:zkai:native-seq32-attention-mlp-rmsnorm-adjacent-label-policy:v1"
EXPECTED_INTERPRETATION = {
    "human_read": (
        "The adjacent layout looked like an 88-byte NO-GO under its fixed label, but both existing "
        "adjacent label probes verify and beat the current champion. The worst checked probe saves "
        "1,736 typed bytes; the best saves 4,536 typed bytes."
    ),
    "mechanism_read": (
        "The direct value bytes stay fixed across the adjacent label probes. The savings come from "
        "path-opening and FRI material, so this is a transcript/opening-stability signal."
    ),
    "next_experiment": (
        "Freeze a deterministic label policy before promoting this as a durable proof-size frontier."
    ),
}

CURRENT_CHAMPION_ID = "current_duplicate_base"
CURRENT_CHAMPION_TYPED_BYTES = 42_068
CURRENT_CHAMPION_JSON_BYTES = 121_996
FIXED_ADJACENT_TYPED_BYTES = 42_156
FIXED_ADJACENT_JSON_BYTES = 122_688
PROBE_A_TYPED_BYTES = 40_332
PROBE_A_JSON_BYTES = 116_321
PROBE_B_TYPED_BYTES = 37_532
PROBE_B_JSON_BYTES = 106_317
WORST_PROBE_TYPED_BYTES = PROBE_A_TYPED_BYTES
BEST_PROBE_TYPED_BYTES = PROBE_B_TYPED_BYTES
WORST_PROBE_SAVING_BYTES = CURRENT_CHAMPION_TYPED_BYTES - WORST_PROBE_TYPED_BYTES
BEST_PROBE_SAVING_BYTES = CURRENT_CHAMPION_TYPED_BYTES - BEST_PROBE_TYPED_BYTES
WORST_PROBE_JSON_SAVING_BYTES = CURRENT_CHAMPION_JSON_BYTES - PROBE_A_JSON_BYTES
BEST_PROBE_JSON_SAVING_BYTES = CURRENT_CHAMPION_JSON_BYTES - PROBE_B_JSON_BYTES
LABEL_SPAN_TYPED_BYTES = PROBE_A_TYPED_BYTES - PROBE_B_TYPED_BYTES
LABEL_SPAN_JSON_BYTES = PROBE_A_JSON_BYTES - PROBE_B_JSON_BYTES
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900

PATH_OPENING_GROUPS = ("fri_decommitments", "fri_samples", "trace_decommitments")
VALUE_GROUPS = ("oods_samples", "queries_values")

EXPECTED_ROWS: tuple[dict[str, Any], ...] = (
    {
        "variant_id": CURRENT_CHAMPION_ID,
        "path": "zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json",
        "adapter_mode": "duplicate_base_preprocessed_v1",
        "proof_backend_version": "stwo-native-seq32-attention-mlp-single-proof-object-native-adapter-v1",
        "typed_bytes": CURRENT_CHAMPION_TYPED_BYTES,
        "proof_json_bytes": CURRENT_CHAMPION_JSON_BYTES,
        "proof_sha256": "9242c16a3aba3ebd1a39c77bffcbec3f78c93db4d097e6872c4e640316692ce1",
        "envelope_sha256": "c5107022445b27d8061c2c96c1f5a5710e94695e8647efdf903682385be03414",
        "record_stream_sha256": "d2b9ef1587963a0c1b2c10c396e0e1f23c1f108696c0a9b275c21d85b75736fa",
        "grouped": {
            "fixed_overhead": 48,
            "fri_decommitments": 13_248,
            "fri_samples": 816,
            "oods_samples": 12_272,
            "queries_values": 9_156,
            "trace_decommitments": 6_528,
        },
    },
    {
        "variant_id": "fixed_adjacent_layout",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_fixed_v1",
        "proof_backend_version": "stwo-native-seq32-attention-mlp-single-proof-object-rmsnorm-input-fused-adjacent-fixed-v1",
        "typed_bytes": FIXED_ADJACENT_TYPED_BYTES,
        "proof_json_bytes": FIXED_ADJACENT_JSON_BYTES,
        "proof_sha256": "f1a495236e06cb3bb76e7f7cb900b9b96eb203809f791d28238fc948514126ed",
        "envelope_sha256": "91d6866982629e829ef4b53502c99c7215e0d6bb257336cdf2910b8c94ce52b3",
        "record_stream_sha256": "24e3f16bf92320fd79059257ec70ca97bbf76b5859610c2013c58a7511f1feaf",
        "grouped": {
            "fixed_overhead": 48,
            "fri_decommitments": 13_696,
            "fri_samples": 832,
            "oods_samples": 11_984,
            "queries_values": 8_940,
            "trace_decommitments": 6_656,
        },
    },
    {
        "variant_id": "adjacent_label_probe_a",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_a_v1",
        "proof_backend_version": "stwo-native-seq32-attention-mlp-single-proof-object-rmsnorm-input-fused-adjacent-fixed-v1",
        "typed_bytes": PROBE_A_TYPED_BYTES,
        "proof_json_bytes": PROBE_A_JSON_BYTES,
        "proof_sha256": "3421ac16f96bda07540698ccdbf1ea705ca384583c3b3275fc99471b5a156d7d",
        "envelope_sha256": "2f15a7b6c6e15b889ffc61c6a74235efc43b416fe7384452ca07d5818447f0aa",
        "record_stream_sha256": "ab9c27d7b780f81ec8f8f562997392362c18c9ddc6315d1db303520e3fd7e682",
        "grouped": {
            "fixed_overhead": 48,
            "fri_decommitments": 12_320,
            "fri_samples": 768,
            "oods_samples": 11_984,
            "queries_values": 8_940,
            "trace_decommitments": 6_272,
        },
    },
    {
        "variant_id": "adjacent_label_probe_b",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_b_v1",
        "proof_backend_version": "stwo-native-seq32-attention-mlp-single-proof-object-rmsnorm-input-fused-adjacent-fixed-v1",
        "typed_bytes": PROBE_B_TYPED_BYTES,
        "proof_json_bytes": PROBE_B_JSON_BYTES,
        "proof_sha256": "4a5dc66d63ee3ddd3acad65e88c42259fb925ee31768a3fdecdb528722630845",
        "envelope_sha256": "8e3ba831ac7e858d069f1edfcb6ad46783b0d72f3f47666ae621bc159ac2c0df",
        "record_stream_sha256": "d0540f5cd1a69991226bcfb81475cec78ba0d416a39317503ad204b660aae1e0",
        "grouped": {
            "fixed_overhead": 48,
            "fri_decommitments": 10_240,
            "fri_samples": 688,
            "oods_samples": 11_984,
            "queries_values": 8_940,
            "trace_decommitments": 5_632,
        },
    },
)

NON_CLAIMS = (
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not a full transformer block proof",
    "not exact real-valued Softmax",
    "not timing evidence",
    "not production-ready zkML",
    "not a final production label-selection policy",
)

VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent-label-probe-a docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent-label-probe-b docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.envelope.json > docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-accounting-2026-05.json",
    "python3.10 scripts/zkai_native_seq32_attention_mlp_adjacent_label_policy_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-policy-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-policy-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_adjacent_label_policy_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_adjacent_label_policy_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_adjacent_label_policy_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_adjacent_label --lib",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

MUTATION_NAMES = (
    "decision_drift",
    "result_drift",
    "worst_probe_saving_erased",
    "best_probe_typed_drift",
    "probe_adapter_mode_relabel",
    "probe_value_group_drift",
    "path_opening_saving_erased",
    "label_span_erased",
    "source_artifact_digest_drift",
    "validation_command_drift",
    "removed_non_claim",
    "interpretation_drift",
    "nanozk_overclaim",
    "payload_commitment_drift",
)
EXPECTED_MUTATION_ERRORS = {
    "decision_drift": "decision drift",
    "result_drift": "result drift",
    "worst_probe_saving_erased": "summary drift",
    "best_probe_typed_drift": "variant metadata drift",
    "probe_adapter_mode_relabel": "variant metadata drift",
    "probe_value_group_drift": "variant metadata drift",
    "path_opening_saving_erased": "summary drift",
    "label_span_erased": "summary drift",
    "source_artifact_digest_drift": "source artifact digest drift",
    "validation_command_drift": "validation command drift",
    "removed_non_claim": "non_claims drift",
    "interpretation_drift": "interpretation drift",
    "nanozk_overclaim": "claim_boundary drift",
    "payload_commitment_drift": "payload commitment drift",
}

TSV_COLUMNS = (
    "variant_id",
    "typed_bytes",
    "proof_json_bytes",
    "typed_delta_vs_champion",
    "proof_json_delta_vs_champion",
    "path_opening_bytes",
    "path_opening_delta_vs_champion",
    "value_bytes",
    "value_delta_vs_champion",
)

DETERMINISTIC_TEMP_ATTEMPTS = 16
PAYLOAD_KEYS = {
    "schema",
    "decision",
    "result",
    "claim_boundary",
    "issue_hint",
    "summary",
    "variants",
    "interpretation",
    "non_claims",
    "source_artifacts",
    "validation_commands",
    "mutation_result",
    "payload_commitment",
}
VARIANT_KEYS = {
    "variant_id",
    "path",
    "adapter_mode",
    "proof_backend_version",
    "typed_bytes",
    "proof_json_bytes",
    "proof_sha256",
    "envelope_sha256",
    "record_stream_sha256",
    "grouped",
    "path_opening_bytes",
    "value_bytes",
    "typed_delta_vs_champion",
    "proof_json_delta_vs_champion",
    "path_opening_delta_vs_champion",
    "value_delta_vs_champion",
}
SOURCE_ARTIFACT_KEYS = {"id", "path", "sha256", "size_bytes"}
MUTATION_RESULT_KEYS = {"all_mutations_rejected", "mutations_rejected", "mutation_names", "cases"}
MUTATION_CASE_KEYS = {"name", "rejected", "error"}


class AdjacentLabelPolicyGateError(ValueError):
    pass


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as err:
        raise AdjacentLabelPolicyGateError(f"invalid JSON value: {err}") from err


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return "blake2b-256:" + digest.hexdigest()


def read_repo_file(path: pathlib.Path, label: str) -> bytes:
    root = ROOT.resolve()
    candidate = pathlib.Path(os.path.abspath(path if path.is_absolute() else ROOT / path))
    try:
        relative = candidate.relative_to(root)
    except ValueError as err:
        raise AdjacentLabelPolicyGateError(f"{label} path escapes repo") from err
    try:
        current = root
        for part in relative.parts:
            current = current / part
            mode = current.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise AdjacentLabelPolicyGateError(f"{label} path must not traverse symlinks")
        fd = os.open(candidate, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            with os.fdopen(fd, "rb") as handle:
                fd = None
                return handle.read()
        finally:
            if fd is not None:
                os.close(fd)
    except OSError as err:
        raise AdjacentLabelPolicyGateError(f"failed to read {label}: {err}") from err


def load_json_file(path: pathlib.Path, label: str) -> Any:
    raw = read_repo_file(path, label)
    try:
        return json.loads(raw), raw
    except json.JSONDecodeError as err:
        raise AdjacentLabelPolicyGateError(f"{label} must be JSON: {err}") from err


def _dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AdjacentLabelPolicyGateError(f"{label} must be object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise AdjacentLabelPolicyGateError(f"{label} must be list")
    return value


def _group_int(groups: dict[str, Any], group: str) -> int:
    if group not in groups:
        raise AdjacentLabelPolicyGateError(f"missing accounting group: {group}")
    value = groups[group]
    if isinstance(value, bool) or not isinstance(value, int):
        raise AdjacentLabelPolicyGateError(f"accounting group must be int: {group}")
    return value


def _require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual == expected:
        return
    unexpected = sorted(actual - expected)
    missing = sorted(expected - actual)
    if unexpected:
        raise AdjacentLabelPolicyGateError(f"{label} field drift: unexpected {unexpected[0]}")
    raise AdjacentLabelPolicyGateError(f"{label} field drift: missing {missing[0]}")


def grouped(row: dict[str, Any]) -> dict[str, int]:
    local_accounting = _dict(row.get("local_binary_accounting"), "local accounting")
    return _dict(local_accounting.get("grouped_reconstruction"), "grouped")


def path_opening_bytes(groups: dict[str, int]) -> int:
    return sum(_group_int(groups, group) for group in PATH_OPENING_GROUPS)


def value_bytes(groups: dict[str, int]) -> int:
    return sum(_group_int(groups, group) for group in VALUE_GROUPS)


def expected_by_path() -> dict[str, dict[str, Any]]:
    return {row["path"]: row for row in EXPECTED_ROWS}


def load_rows() -> list[dict[str, Any]]:
    accounting, _raw = load_json_file(ACCOUNTING_PATH, "accounting")
    rows = _list(_dict(accounting, "accounting").get("rows"), "accounting rows")
    if len(rows) != len(EXPECTED_ROWS):
        raise AdjacentLabelPolicyGateError("row inventory drift")
    expected = expected_by_path()
    parsed = []
    for actual in rows:
        row = _dict(actual, "accounting row")
        path = row.get("evidence_relative_path")
        if path not in expected:
            raise AdjacentLabelPolicyGateError("unexpected accounting path")
        want = expected[path]
        envelope_path = EVIDENCE_DIR / str(path)
        envelope, envelope_raw = load_json_file(envelope_path, f"envelope {path}")
        proof = _list(_dict(envelope, "envelope").get("proof"), "proof bytes")
        try:
            proof_raw = bytes(proof)
        except ValueError as err:
            raise AdjacentLabelPolicyGateError("proof bytes must be byte values") from err
        actual_groups = grouped(row)
        parsed_row = {
            "variant_id": want["variant_id"],
            "path": path,
            "adapter_mode": _dict(envelope.get("input"), "envelope input").get("adapter_mode"),
            "proof_backend_version": _dict(row.get("envelope_metadata"), "envelope metadata").get("proof_backend_version"),
            "typed_bytes": _dict(row.get("local_binary_accounting"), "local accounting").get("typed_size_estimate_bytes"),
            "proof_json_bytes": row.get("proof_json_size_bytes"),
            "proof_sha256": row.get("proof_sha256"),
            "envelope_sha256": row.get("envelope_sha256"),
            "record_stream_sha256": _dict(row.get("local_binary_accounting"), "local accounting").get("record_stream_sha256"),
            "grouped": actual_groups,
            "path_opening_bytes": path_opening_bytes(actual_groups),
            "value_bytes": value_bytes(actual_groups),
        }
        for key in ("adapter_mode", "proof_backend_version", "typed_bytes", "proof_json_bytes", "proof_sha256", "envelope_sha256", "record_stream_sha256"):
            if parsed_row[key] != want[key]:
                raise AdjacentLabelPolicyGateError(f"{want['variant_id']} {key} drift")
        if parsed_row["grouped"] != want["grouped"]:
            raise AdjacentLabelPolicyGateError(f"{want['variant_id']} grouped drift")
        if sha256(envelope_raw) != want["envelope_sha256"] or sha256(proof_raw) != want["proof_sha256"]:
            raise AdjacentLabelPolicyGateError(f"{want['variant_id']} digest drift")
        parsed.append(parsed_row)
    if [row["variant_id"] for row in parsed] != [row["variant_id"] for row in EXPECTED_ROWS]:
        raise AdjacentLabelPolicyGateError("row order drift")
    return parsed


def source_artifacts() -> list[dict[str, Any]]:
    artifacts = []
    for artifact_id, path in (
        ("accounting", ACCOUNTING_PATH),
        *((row["variant_id"], EVIDENCE_DIR / row["path"]) for row in EXPECTED_ROWS),
    ):
        raw = read_repo_file(path, artifact_id)
        artifacts.append(
            {
                "id": artifact_id,
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(raw),
                "size_bytes": len(raw),
            }
        )
    return artifacts


def build_payload() -> dict[str, Any]:
    rows = load_rows()
    champion = rows[0]
    fixed = rows[1]
    probe_a = rows[2]
    probe_b = rows[3]
    probes = [probe_a, probe_b]
    worst = max(probes, key=lambda row: row["typed_bytes"])
    best = min(probes, key=lambda row: row["typed_bytes"])
    summary = {
        "current_champion_id": champion["variant_id"],
        "current_champion_typed_bytes": champion["typed_bytes"],
        "current_champion_json_bytes": champion["proof_json_bytes"],
        "fixed_adjacent_typed_bytes": fixed["typed_bytes"],
        "fixed_adjacent_json_bytes": fixed["proof_json_bytes"],
        "fixed_adjacent_typed_delta_vs_champion": fixed["typed_bytes"] - champion["typed_bytes"],
        "fixed_adjacent_json_delta_vs_champion": fixed["proof_json_bytes"] - champion["proof_json_bytes"],
        "probe_count": len(probes),
        "worst_probe_id": worst["variant_id"],
        "worst_probe_typed_bytes": worst["typed_bytes"],
        "worst_probe_json_bytes": worst["proof_json_bytes"],
        "worst_probe_saving_typed_bytes": champion["typed_bytes"] - worst["typed_bytes"],
        "worst_probe_saving_json_bytes": champion["proof_json_bytes"] - worst["proof_json_bytes"],
        "worst_probe_saving_share": f"{(champion['typed_bytes'] - worst['typed_bytes']) / champion['typed_bytes']:.6f}",
        "best_probe_id": best["variant_id"],
        "best_probe_typed_bytes": best["typed_bytes"],
        "best_probe_json_bytes": best["proof_json_bytes"],
        "best_probe_saving_typed_bytes": champion["typed_bytes"] - best["typed_bytes"],
        "best_probe_saving_json_bytes": champion["proof_json_bytes"] - best["proof_json_bytes"],
        "best_probe_saving_share": f"{(champion['typed_bytes'] - best['typed_bytes']) / champion['typed_bytes']:.6f}",
        "label_span_typed_bytes": worst["typed_bytes"] - best["typed_bytes"],
        "label_span_json_bytes": worst["proof_json_bytes"] - best["proof_json_bytes"],
        "probe_value_bytes_equal_fixed_adjacent": all(row["value_bytes"] == fixed["value_bytes"] for row in probes),
        "worst_probe_path_opening_saving_vs_champion": champion["path_opening_bytes"] - worst["path_opening_bytes"],
        "best_probe_path_opening_saving_vs_champion": champion["path_opening_bytes"] - best["path_opening_bytes"],
        "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
        "proof_size_comparable_external_rows": 0,
    }
    enriched_rows = []
    for row in rows:
        item = copy.deepcopy(row)
        item["typed_delta_vs_champion"] = item["typed_bytes"] - champion["typed_bytes"]
        item["proof_json_delta_vs_champion"] = item["proof_json_bytes"] - champion["proof_json_bytes"]
        item["path_opening_delta_vs_champion"] = item["path_opening_bytes"] - champion["path_opening_bytes"]
        item["value_delta_vs_champion"] = item["value_bytes"] - champion["value_bytes"]
        enriched_rows.append(item)
    payload = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "issue_hint": ISSUE_HINT,
        "summary": summary,
        "variants": enriched_rows,
        "interpretation": copy.deepcopy(EXPECTED_INTERPRETATION),
        "non_claims": list(NON_CLAIMS),
        "source_artifacts": source_artifacts(),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    payload["mutation_result"] = mutation_result(payload)
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload)
    return payload


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
        except AdjacentLabelPolicyGateError as err:
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
        ("worst_probe_saving_erased", lambda item: item["summary"].update({"worst_probe_saving_typed_bytes": 0})),
        ("best_probe_typed_drift", lambda item: item["variants"][3].update({"typed_bytes": 42_100})),
        ("probe_adapter_mode_relabel", lambda item: item["variants"][2].update({"adapter_mode": "rmsnorm_input_fused_adjacent_fixed_v1"})),
        ("probe_value_group_drift", lambda item: item["variants"][2]["grouped"].update({"queries_values": 9_000})),
        ("path_opening_saving_erased", lambda item: item["summary"].update({"worst_probe_path_opening_saving_vs_champion": 0})),
        ("label_span_erased", lambda item: item["summary"].update({"label_span_typed_bytes": 0})),
        ("source_artifact_digest_drift", lambda item: item["source_artifacts"][0].update({"sha256": "0" * 64})),
        ("validation_command_drift", lambda item: item["validation_commands"].append("echo untracked")),
        ("removed_non_claim", lambda item: item["non_claims"].remove("not a final production label-selection policy")),
        ("interpretation_drift", lambda item: item["interpretation"].update({"human_read": "overclaim"})),
        ("nanozk_overclaim", lambda item: item.update({"claim_boundary": item["claim_boundary"] + ";NANOZK_WIN"})),
        ("payload_commitment_drift", lambda item: item.update({"payload_commitment": "blake2b-256:" + "0" * 64})),
    )


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
            raise AdjacentLabelPolicyGateError(f"{key} drift")
    if payload.get("non_claims") != list(NON_CLAIMS):
        raise AdjacentLabelPolicyGateError("non_claims drift")
    if payload.get("validation_commands") != list(VALIDATION_COMMANDS):
        raise AdjacentLabelPolicyGateError("validation command drift")
    if payload.get("interpretation") != EXPECTED_INTERPRETATION:
        raise AdjacentLabelPolicyGateError("interpretation drift")
    validate_summary(_dict(payload.get("summary"), "summary"))
    validate_variants(_list(payload.get("variants"), "variants"))
    validate_source_artifacts(_list(payload.get("source_artifacts"), "source artifacts"))
    validate_mutation_result(_dict(payload.get("mutation_result"), "mutation result"))
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise AdjacentLabelPolicyGateError("payload commitment drift")


def validate_summary(summary: dict[str, Any]) -> None:
    expected = {
        "current_champion_id": CURRENT_CHAMPION_ID,
        "current_champion_typed_bytes": CURRENT_CHAMPION_TYPED_BYTES,
        "current_champion_json_bytes": CURRENT_CHAMPION_JSON_BYTES,
        "fixed_adjacent_typed_bytes": FIXED_ADJACENT_TYPED_BYTES,
        "fixed_adjacent_json_bytes": FIXED_ADJACENT_JSON_BYTES,
        "fixed_adjacent_typed_delta_vs_champion": 88,
        "fixed_adjacent_json_delta_vs_champion": 692,
        "probe_count": 2,
        "worst_probe_id": "adjacent_label_probe_a",
        "worst_probe_typed_bytes": WORST_PROBE_TYPED_BYTES,
        "worst_probe_json_bytes": PROBE_A_JSON_BYTES,
        "worst_probe_saving_typed_bytes": WORST_PROBE_SAVING_BYTES,
        "worst_probe_saving_json_bytes": WORST_PROBE_JSON_SAVING_BYTES,
        "worst_probe_saving_share": "0.041267",
        "best_probe_id": "adjacent_label_probe_b",
        "best_probe_typed_bytes": BEST_PROBE_TYPED_BYTES,
        "best_probe_json_bytes": PROBE_B_JSON_BYTES,
        "best_probe_saving_typed_bytes": BEST_PROBE_SAVING_BYTES,
        "best_probe_saving_json_bytes": BEST_PROBE_JSON_SAVING_BYTES,
        "best_probe_saving_share": "0.107825",
        "label_span_typed_bytes": LABEL_SPAN_TYPED_BYTES,
        "label_span_json_bytes": LABEL_SPAN_JSON_BYTES,
        "probe_value_bytes_equal_fixed_adjacent": True,
        "worst_probe_path_opening_saving_vs_champion": 1_232,
        "best_probe_path_opening_saving_vs_champion": 4_032,
        "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
        "proof_size_comparable_external_rows": 0,
    }
    if summary != expected:
        raise AdjacentLabelPolicyGateError("summary drift")


def validate_variants(variants: list[Any]) -> None:
    if len(variants) != len(EXPECTED_ROWS):
        raise AdjacentLabelPolicyGateError("variant inventory drift")
    variant_rows = [_dict(item, "variant") for item in variants]
    for row in variant_rows:
        _require_exact_keys(row, VARIANT_KEYS, "variant")
    if [row.get("variant_id") for row in variant_rows] != [row["variant_id"] for row in EXPECTED_ROWS]:
        raise AdjacentLabelPolicyGateError("variant order drift")
    expected = expected_by_path()
    champion = next(
        row
        for row in variant_rows
        if row.get("variant_id") == CURRENT_CHAMPION_ID
    )
    for row in variant_rows:
        path = row.get("path")
        if path not in expected:
            raise AdjacentLabelPolicyGateError("variant path drift")
        want = expected[str(path)]
        for key in (
            "variant_id",
            "path",
            "adapter_mode",
            "proof_backend_version",
            "typed_bytes",
            "proof_json_bytes",
            "proof_sha256",
            "envelope_sha256",
            "record_stream_sha256",
            "grouped",
        ):
            if row.get(key) != want.get(key):
                raise AdjacentLabelPolicyGateError("variant metadata drift")
        if row.get("path_opening_bytes") != path_opening_bytes(want["grouped"]):
            raise AdjacentLabelPolicyGateError("variant path-opening bytes drift")
        if row.get("value_bytes") != value_bytes(want["grouped"]):
            raise AdjacentLabelPolicyGateError("variant value bytes drift")
        if row.get("typed_delta_vs_champion") != row["typed_bytes"] - champion["typed_bytes"]:
            raise AdjacentLabelPolicyGateError("variant typed delta drift")
        if row.get("proof_json_delta_vs_champion") != row["proof_json_bytes"] - champion["proof_json_bytes"]:
            raise AdjacentLabelPolicyGateError("variant json delta drift")
        if row.get("path_opening_delta_vs_champion") != row["path_opening_bytes"] - champion["path_opening_bytes"]:
            raise AdjacentLabelPolicyGateError("variant path-opening delta drift")
        if row.get("value_delta_vs_champion") != row["value_bytes"] - champion["value_bytes"]:
            raise AdjacentLabelPolicyGateError("variant value delta drift")


def validate_source_artifacts(artifacts: list[Any]) -> None:
    expected_inventory = (
        ("accounting", str(ACCOUNTING_PATH.relative_to(ROOT))),
        *((row["variant_id"], f"docs/engineering/evidence/{row['path']}") for row in EXPECTED_ROWS),
    )
    artifact_rows = [_dict(item, "source artifact") for item in artifacts]
    for artifact in artifact_rows:
        _require_exact_keys(artifact, SOURCE_ARTIFACT_KEYS, "source artifact")
    actual_inventory = tuple((artifact.get("id"), artifact.get("path")) for artifact in artifact_rows)
    if actual_inventory != expected_inventory:
        raise AdjacentLabelPolicyGateError("source artifact inventory drift")
    for artifact in artifact_rows:
        path = ROOT / str(artifact.get("path"))
        raw = read_repo_file(path, "source artifact")
        if artifact.get("sha256") != sha256(raw) or artifact.get("size_bytes") != len(raw):
            raise AdjacentLabelPolicyGateError("source artifact digest drift")


def validate_mutation_result(result: dict[str, Any]) -> None:
    _require_exact_keys(result, MUTATION_RESULT_KEYS, "mutation result")
    if result.get("mutation_names") != list(MUTATION_NAMES):
        raise AdjacentLabelPolicyGateError("mutation result drift")
    cases = _list(result.get("cases"), "mutation cases")
    case_rows = [_dict(case, "mutation case") for case in cases]
    for case in case_rows:
        _require_exact_keys(case, MUTATION_CASE_KEYS, "mutation case")
    if [case.get("name") for case in case_rows] != list(MUTATION_NAMES):
        raise AdjacentLabelPolicyGateError("mutation result drift")
    if result.get("mutations_rejected") != len(MUTATION_NAMES) or result.get("all_mutations_rejected") is not True:
        raise AdjacentLabelPolicyGateError("mutation result drift")
    for case in case_rows:
        if case.get("rejected") is not True:
            raise AdjacentLabelPolicyGateError("mutation result drift")
    if case_rows != expected_mutation_cases():
        raise AdjacentLabelPolicyGateError("mutation result drift")


def render_tsv(payload: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in payload["variants"]:
        writer.writerow({column: row[column] for column in TSV_COLUMNS})
    return output.getvalue()


def require_output_path(path: pathlib.Path) -> pathlib.Path:
    target = pathlib.Path(os.path.abspath(path if path.is_absolute() else ROOT / path))
    evidence_root = EVIDENCE_DIR.resolve()
    try:
        relative = target.relative_to(evidence_root)
    except ValueError as err:
        raise AdjacentLabelPolicyGateError("output path escapes evidence dir") from err
    current = evidence_root
    for part in relative.parent.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except OSError as err:
            raise AdjacentLabelPolicyGateError(f"output parent must exist: {current}") from err
        if stat.S_ISLNK(mode):
            raise AdjacentLabelPolicyGateError("output path must not traverse symlinks")
        if not stat.S_ISDIR(mode):
            raise AdjacentLabelPolicyGateError(f"output parent must be directory: {current}")
    if target.is_symlink() or (target.exists() and target.is_dir()):
        raise AdjacentLabelPolicyGateError("output path must be a non-symlink file")
    return target


def atomic_write_text(path: pathlib.Path, text: str) -> None:
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
                tmp_created = False
                os.fsync(parent_fd)
                return
            except Exception:
                if tmp_created:
                    try:
                        os.unlink(tmp_name, dir_fd=parent_fd)
                    except OSError:
                        pass
                raise
            finally:
                if fd is not None:
                    os.close(fd)
        raise AdjacentLabelPolicyGateError(f"deterministic temp file collision for {target}")
    finally:
        os.close(parent_fd)


def payload_with_mutations() -> dict[str, Any]:
    return build_payload()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    args = parser.parse_args()
    payload = build_payload()
    if args.write_json:
        atomic_write_text(args.write_json, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if args.write_tsv:
        atomic_write_text(args.write_tsv, render_tsv(payload))
    print(
        json.dumps(
            {
                "decision": payload["decision"],
                "worst_probe_typed_bytes": payload["summary"]["worst_probe_typed_bytes"],
                "worst_probe_saving_typed_bytes": payload["summary"]["worst_probe_saving_typed_bytes"],
                "best_probe_typed_bytes": payload["summary"]["best_probe_typed_bytes"],
                "best_probe_saving_typed_bytes": payload["summary"]["best_probe_saving_typed_bytes"],
                "mutations_rejected": payload["mutation_result"]["mutations_rejected"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
