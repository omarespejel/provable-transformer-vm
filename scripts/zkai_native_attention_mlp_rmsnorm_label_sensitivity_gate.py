#!/usr/bin/env python3
"""Gate RMSNorm-input label sensitivity for native attention+MLP proofs."""

from __future__ import annotations

import argparse
import contextlib
import copy
import csv
import hashlib
import io
import json
import os
import pathlib
import secrets
import stat
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"

BASE_ACCOUNTING_PATH = (
    EVIDENCE_DIR
    / "zkai-native-attention-mlp-rmsnorm-input-fused-adapter-binary-accounting-2026-05.json"
)
LABEL_ACCOUNTING_PATH = (
    EVIDENCE_DIR
    / "zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-accounting-2026-05.json"
)
JSON_OUT = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-label-sensitivity-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-label-sensitivity-2026-05.tsv"

SCHEMA = "zkai-native-attention-mlp-rmsnorm-label-sensitivity-gate-v1"
DECISION = "NO_GO_FRONTIER_PROMOTION_UNDER_LABEL_SENSITIVITY"
RESULT = "LABEL_ONLY_PROBES_MOVE_PATH_OPENING_BYTES_MORE_THAN_THE_FRONTIER_BUDGET"
ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/644"
CLAIM_BOUNDARY = (
    "RMSNORM_INPUT_FUSED_LABEL_ONLY_PROBES_PRESERVE_THE_ADAPTER_EQUATION_AND_SHOW_"
    "PATH_OPENING_SENSITIVITY_WITHOUT_PROMOTING_A_PROOF_SIZE_WIN"
)
PAYLOAD_DOMAIN = "ptvm:zkai:native-attention-mlp-rmsnorm-label-sensitivity:v1"
PROOF_BACKEND_VERSION = "stwo-native-attention-mlp-single-proof-object-rmsnorm-input-fused-adapter-v1"
PROOF_SCHEMA_VERSION = "stwo-native-attention-mlp-single-proof-object-native-adapter-payload-v1"

MAX_JSON_INPUT_BYTES = 64 * 1024 * 1024
TWO_PROOF_FRONTIER_TYPED_BYTES = 40_700
COMPACT_SELECTOR_TYPED_BYTES = 40_812
RMSNORM_INPUT_FUSED_TYPED_BYTES = 41_428
LABEL_PROBE_A_TYPED_BYTES = 40_836
LABEL_PROBE_B_TYPED_BYTES = 42_100
REQUIRED_REDUCTION_TO_BEAT_FRONTIER_BYTES = 729
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900

PATH_OPENING_GROUPS = ("fri_decommitments", "fri_samples", "trace_decommitments")
VALUE_GROUPS = ("oods_samples", "queries_values")

EXPECTED_SOURCE_SHA256 = {
    "baseline_accounting": "bdd2cc67b1590fb79a68d316a9e362c6f996c47c2c43c77fd50c390821d95b2b",
    "label_probe_accounting": "157a609cfa92ee85c2215e7f6ab22d45980c168a8b8340e6eab51aa2e97ccf9b",
}

EXPECTED_VARIANTS = {
    "compact_selector": {
        "path": "zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json",
        "typed": COMPACT_SELECTOR_TYPED_BYTES,
        "proof_json": 116_091,
        "groups": {
            "fixed_overhead": 48,
            "fri_decommitments": 12_448,
            "fri_samples": 784,
            "oods_samples": 12_176,
            "queries_values": 9_084,
            "trace_decommitments": 6_272,
        },
        "record_stream_sha256": "8ed8db52bfb240a2b742df9877aa8d01ece09334616540771812e28081c5d996",
        "label_probe": False,
    },
    "rmsnorm_input_fused": {
        "path": "zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json",
        "typed": RMSNORM_INPUT_FUSED_TYPED_BYTES,
        "proof_json": 118_378,
        "groups": {
            "fixed_overhead": 48,
            "fri_decommitments": 13_184,
            "fri_samples": 800,
            "oods_samples": 11_952,
            "queries_values": 8_916,
            "trace_decommitments": 6_528,
        },
        "record_stream_sha256": "2f7f36ee6000173dea41ab684dab9a20f36f95277eeb7c9a749a98c185583d91",
        "label_probe": False,
    },
    "label_probe_a": {
        "path": "zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-a-2026-05.envelope.json",
        "typed": LABEL_PROBE_A_TYPED_BYTES,
        "proof_json": 116_332,
        "groups": {
            "fixed_overhead": 48,
            "fri_decommitments": 12_736,
            "fri_samples": 784,
            "oods_samples": 11_952,
            "queries_values": 8_916,
            "trace_decommitments": 6_400,
        },
        "record_stream_sha256": "2842970b3a110bb01ce6c886eef1231981b4e7f9920d091d6c0ab804a436d54f",
        "label_probe": True,
    },
    "label_probe_b": {
        "path": "zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-b-2026-05.envelope.json",
        "typed": LABEL_PROBE_B_TYPED_BYTES,
        "proof_json": 120_694,
        "groups": {
            "fixed_overhead": 48,
            "fri_decommitments": 13_696,
            "fri_samples": 832,
            "oods_samples": 11_952,
            "queries_values": 8_916,
            "trace_decommitments": 6_656,
        },
        "record_stream_sha256": "ee96a72af291c70926a71a03dd6ba46ed88175b7fbc9a4e4c863ee2c12515092",
        "label_probe": True,
    },
}

NON_CLAIMS = (
    "not a two-proof frontier beat",
    "not a proof-size win from a new architecture",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not timing evidence",
    "not a full transformer block proof",
    "not production-ready zkML",
)

HUMAN_READ = (
    "Two label-only RMSNorm-input fused probes preserve the same adapter equation and direct value bytes, "
    "but move typed proof size from 40,836 to 42,100 bytes. The best probe is still 136 bytes above "
    "the two-proof frontier and 24 bytes above compact, while the 1,264 byte label-only span exceeds "
    "the 729 byte reduction budget. This is a no-go for frontier promotion and a go for a stricter "
    "multi-label or query-inventory policy."
)
NEXT_ATTACK = (
    "Do not claim a sub-kilobyte opening-layout win from one transcript. The next real attack must "
    "either change the verifier-facing opening geometry structurally or report a multi-label policy "
    "that beats the frontier without cherry-picking."
)
INTERPRETATION = {
    "human_read": HUMAN_READ,
    "next_attack": NEXT_ATTACK,
}

VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused-label-probe-a docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-a-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-a-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-a-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-a-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused-label-probe-b docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-b-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-b-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-b-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-b-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-a-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-b-2026-05.envelope.json > docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-label-probe-accounting-2026-05.json",
    "python3 scripts/zkai_native_attention_mlp_rmsnorm_label_sensitivity_gate.py --write-json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-label-sensitivity-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-label-sensitivity-2026-05.tsv",
    "python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_label_sensitivity_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_fused_label_probe --lib",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend native_attention_mlp_single_proof --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

EXPECTED_MUTATION_NAMES = (
    "frontier_overclaim",
    "nanozk_overclaim",
    "best_probe_typed_drift",
    "best_probe_name_drift",
    "decision_drift",
    "result_drift",
    "issue_drift",
    "claim_boundary_drift",
    "proof_backend_version_drift",
    "interpretation_drift",
    "source_digest_drift",
    "non_claims_erased",
    "validation_commands_erased",
    "label_span_erased",
    "span_warning_erased",
    "value_delta_smuggled",
    "probe_a_group_drift",
    "probe_a_missing_path_opening_group",
    "summary_extra_key",
    "variant_extra_key",
    "payload_commitment_drift",
)

TSV_COLUMNS = (
    "variant",
    "typed_bytes",
    "typed_delta_vs_canonical",
    "typed_delta_vs_two_proof_frontier",
    "path_opening_bytes",
    "path_opening_delta_vs_canonical",
    "value_bytes",
    "value_delta_vs_canonical",
    "proof_json_bytes",
)


class RmsnormLabelSensitivityError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode(
            "utf-8"
        )
    except (TypeError, ValueError) as err:
        raise RmsnormLabelSensitivityError(f"invalid JSON value: {err}") from err


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
        raise RmsnormLabelSensitivityError(f"{label} must be object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise RmsnormLabelSensitivityError(f"{label} must be list")
    return value


def _int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise RmsnormLabelSensitivityError(f"{label} must be integer")
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
        suffix = ", ".join(details) if details else "key drift"
        raise RmsnormLabelSensitivityError(f"{label} key drift: {suffix}")


def require_no_follow_flag(label: str) -> int:
    nofollow_flag = getattr(os, "O_NOFOLLOW", None)
    if not isinstance(nofollow_flag, int) or nofollow_flag == 0:
        raise RmsnormLabelSensitivityError(f"refusing {label} without O_NOFOLLOW support")
    return nofollow_flag


def read_regular_file(path: pathlib.Path, label: str) -> bytes:
    if path.is_symlink():
        raise RmsnormLabelSensitivityError(f"refusing symlinked {label}: {path}")
    for parent in path.parents:
        if parent.is_symlink():
            raise RmsnormLabelSensitivityError(f"refusing symlinked {label} parent: {parent}")
    nofollow_flag = require_no_follow_flag(f"to read {label}")
    try:
        fd = os.open(path, os.O_RDONLY | nofollow_flag)
    except OSError as err:
        raise RmsnormLabelSensitivityError(f"failed to open {label}: {err}") from err
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise RmsnormLabelSensitivityError(f"{label} must be a regular file")
        if before.st_size > MAX_JSON_INPUT_BYTES:
            raise RmsnormLabelSensitivityError(f"{label} exceeds max size")
        chunks: list[bytes] = []
        remaining = MAX_JSON_INPUT_BYTES + 1
        try:
            while remaining > 0:
                chunk = os.read(fd, min(remaining, 64 * 1024))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
        except OSError as err:
            raise RmsnormLabelSensitivityError(f"failed to read {label}: {err}") from err
        raw = b"".join(chunks)
        if len(raw) > MAX_JSON_INPUT_BYTES:
            raise RmsnormLabelSensitivityError(f"{label} exceeds max size")
        after = os.fstat(fd)
        if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
            raise RmsnormLabelSensitivityError(f"{label} changed while reading")
        if len(raw) != before.st_size:
            raise RmsnormLabelSensitivityError(f"{label} short read")
        return raw
    finally:
        os.close(fd)


def read_json(path: pathlib.Path, label: str) -> tuple[dict[str, Any], bytes]:
    raw = read_regular_file(path, label)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        raise RmsnormLabelSensitivityError(f"failed to parse {label}: {err}") from err
    return _dict(payload, label), raw


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def grouped_bytes(groups: dict[str, Any], group_names: tuple[str, ...], label: str) -> int:
    total = 0
    for group in group_names:
        if group not in groups:
            raise RmsnormLabelSensitivityError(f"missing {label} group: {group}")
        total += _int(groups[group], f"{label}.{group}")
    return total


def path_opening_bytes(groups: dict[str, Any]) -> int:
    return grouped_bytes(groups, PATH_OPENING_GROUPS, "path_opening")


def value_bytes(groups: dict[str, Any]) -> int:
    return grouped_bytes(groups, VALUE_GROUPS, "value")


def row_by_path(accounting: dict[str, Any], relative_path: str) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    for row in _list(accounting.get("rows"), "accounting.rows"):
        row_obj = _dict(row, "accounting row")
        if row_obj.get("evidence_relative_path") == relative_path:
            matches.append(row_obj)
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise RmsnormLabelSensitivityError(f"missing accounting row: {relative_path}")
    raise RmsnormLabelSensitivityError(f"duplicate accounting rows for path: {relative_path}")


def variant_from_row(name: str, row: dict[str, Any]) -> dict[str, Any]:
    expected = EXPECTED_VARIANTS[name]
    local = _dict(row.get("local_binary_accounting"), f"{name}.local_binary_accounting")
    groups = _dict(local.get("grouped_reconstruction"), f"{name}.grouped_reconstruction")
    typed = _int(local.get("typed_size_estimate_bytes"), f"{name}.typed")
    if typed != expected["typed"]:
        raise RmsnormLabelSensitivityError(f"{name} typed bytes drift: got {typed}")
    if _int(row.get("proof_json_size_bytes"), f"{name}.proof_json") != expected["proof_json"]:
        raise RmsnormLabelSensitivityError(f"{name} proof JSON bytes drift")
    for group, expected_value in expected["groups"].items():
        if _int(groups.get(group), f"{name}.{group}") != expected_value:
            raise RmsnormLabelSensitivityError(f"{name}.{group} drift")
    if local.get("record_stream_sha256") != expected["record_stream_sha256"]:
        raise RmsnormLabelSensitivityError(f"{name} record stream drift")
    return {
        "name": name,
        "evidence_relative_path": expected["path"],
        "typed_bytes": typed,
        "typed_delta_vs_two_proof_frontier": typed - TWO_PROOF_FRONTIER_TYPED_BYTES,
        "proof_json_bytes": expected["proof_json"],
        "typed_groups": dict(expected["groups"]),
        "path_opening_bytes": path_opening_bytes(groups),
        "value_bytes": value_bytes(groups),
        "record_stream_sha256": expected["record_stream_sha256"],
        "label_probe": expected["label_probe"],
    }


def build_payload(include_mutations: bool = True) -> dict[str, Any]:
    base, base_raw = read_json(BASE_ACCOUNTING_PATH, "baseline accounting")
    label, label_raw = read_json(LABEL_ACCOUNTING_PATH, "label-probe accounting")
    sources = [
        {
            "name": "baseline_accounting",
            "path": str(BASE_ACCOUNTING_PATH.relative_to(ROOT)),
            "sha256": sha256_hex(base_raw),
        },
        {
            "name": "label_probe_accounting",
            "path": str(LABEL_ACCOUNTING_PATH.relative_to(ROOT)),
            "sha256": sha256_hex(label_raw),
        },
    ]
    for source in sources:
        if source["sha256"] != EXPECTED_SOURCE_SHA256[source["name"]]:
            raise RmsnormLabelSensitivityError(f"{source['name']} source digest drift")

    variants = {
        "compact_selector": variant_from_row(
            "compact_selector", row_by_path(base, EXPECTED_VARIANTS["compact_selector"]["path"])
        ),
        "rmsnorm_input_fused": variant_from_row(
            "rmsnorm_input_fused", row_by_path(base, EXPECTED_VARIANTS["rmsnorm_input_fused"]["path"])
        ),
        "label_probe_a": variant_from_row(
            "label_probe_a", row_by_path(label, EXPECTED_VARIANTS["label_probe_a"]["path"])
        ),
        "label_probe_b": variant_from_row(
            "label_probe_b", row_by_path(label, EXPECTED_VARIANTS["label_probe_b"]["path"])
        ),
    }
    canonical = variants["rmsnorm_input_fused"]
    for variant in variants.values():
        variant["typed_delta_vs_canonical"] = variant["typed_bytes"] - canonical["typed_bytes"]
        variant["path_opening_delta_vs_canonical"] = (
            variant["path_opening_bytes"] - canonical["path_opening_bytes"]
        )
        variant["value_delta_vs_canonical"] = variant["value_bytes"] - canonical["value_bytes"]

    best_probe = min(
        [variants["label_probe_a"], variants["label_probe_b"]],
        key=lambda item: item["typed_bytes"],
    )
    worst_probe = max(
        [variants["label_probe_a"], variants["label_probe_b"]],
        key=lambda item: item["typed_bytes"],
    )
    label_only_span = worst_probe["typed_bytes"] - best_probe["typed_bytes"]
    best_probe_reduction = canonical["typed_bytes"] - best_probe["typed_bytes"]
    if best_probe["typed_bytes"] <= TWO_PROOF_FRONTIER_TYPED_BYTES:
        raise RmsnormLabelSensitivityError("label probe unexpectedly beats frontier")
    if best_probe["typed_bytes"] < COMPACT_SELECTOR_TYPED_BYTES:
        raise RmsnormLabelSensitivityError("label probe unexpectedly beats compact selector")
    if best_probe_reduction != 592 or label_only_span != 1_264:
        raise RmsnormLabelSensitivityError("label sensitivity budget drift")
    if label_only_span <= REQUIRED_REDUCTION_TO_BEAT_FRONTIER_BYTES:
        raise RmsnormLabelSensitivityError("label-only span no longer exceeds frontier budget")
    if variants["label_probe_a"]["value_delta_vs_canonical"] != 0:
        raise RmsnormLabelSensitivityError("label probe A changed direct values")
    if variants["label_probe_b"]["value_delta_vs_canonical"] != 0:
        raise RmsnormLabelSensitivityError("label probe B changed direct values")

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "claim_boundary": CLAIM_BOUNDARY,
        "proof_backend_version": PROOF_BACKEND_VERSION,
        "proof_schema_version": PROOF_SCHEMA_VERSION,
        "frontier": {
            "two_proof_frontier_typed_bytes": TWO_PROOF_FRONTIER_TYPED_BYTES,
            "compact_selector_typed_bytes": COMPACT_SELECTOR_TYPED_BYTES,
            "required_reduction_to_beat_frontier_bytes": REQUIRED_REDUCTION_TO_BEAT_FRONTIER_BYTES,
            "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
            "frontier_win_claimed": False,
            "nanozk_win_claimed": False,
        },
        "source_artifacts": sources,
        "variants": variants,
        "summary": {
            "canonical_rmsnorm_input_fused_typed_bytes": canonical["typed_bytes"],
            "best_label_probe": best_probe["name"],
            "best_label_probe_typed_bytes": best_probe["typed_bytes"],
            "best_label_probe_delta_vs_frontier_bytes": best_probe[
                "typed_delta_vs_two_proof_frontier"
            ],
            "best_label_probe_delta_vs_compact_bytes": best_probe["typed_bytes"]
            - COMPACT_SELECTOR_TYPED_BYTES,
            "best_label_probe_reduction_vs_canonical_bytes": best_probe_reduction,
            "worst_label_probe": worst_probe["name"],
            "worst_label_probe_typed_bytes": worst_probe["typed_bytes"],
            "label_only_typed_span_bytes": label_only_span,
            "label_only_span_exceeds_required_frontier_reduction": True,
            "label_probe_value_delta_vs_canonical_bytes": 0,
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
        raise RmsnormLabelSensitivityError("mutation count drift")
    if _int(mutation_result.get("rejected_count"), "rejected count") != len(EXPECTED_MUTATION_NAMES):
        raise RmsnormLabelSensitivityError("mutation rejected count drift")
    names = []
    for index, case in enumerate(cases):
        case_obj = _dict(case, f"mutation case {index}")
        require_exact_keys(case_obj, {"name", "rejected"}, f"mutation case {index}")
        name = case_obj.get("name")
        if not isinstance(name, str):
            raise RmsnormLabelSensitivityError("mutation case name drift")
        names.append(name)
        if case_obj.get("rejected") is not True:
            raise RmsnormLabelSensitivityError(f"mutation not rejected: {name}")
    if tuple(names) != EXPECTED_MUTATION_NAMES:
        raise RmsnormLabelSensitivityError("mutation inventory drift")


def validate_payload(payload: dict[str, Any]) -> None:
    top_level_keys = {
        "schema",
        "decision",
        "result",
        "issue",
        "claim_boundary",
        "proof_backend_version",
        "proof_schema_version",
        "frontier",
        "source_artifacts",
        "variants",
        "summary",
        "interpretation",
        "non_claims",
        "validation_commands",
        "payload_commitment",
    }
    if "mutation_result" in payload:
        top_level_keys.add("mutation_result")
    require_exact_keys(payload, top_level_keys, "payload")
    if payload.get("schema") != SCHEMA:
        raise RmsnormLabelSensitivityError("schema drift")
    if payload.get("decision") != DECISION:
        raise RmsnormLabelSensitivityError("decision drift")
    if payload.get("result") != RESULT:
        raise RmsnormLabelSensitivityError("result drift")
    if payload.get("issue") != ISSUE:
        raise RmsnormLabelSensitivityError("issue drift")
    if payload.get("claim_boundary") != CLAIM_BOUNDARY:
        raise RmsnormLabelSensitivityError("claim boundary drift")
    if payload.get("proof_backend_version") != PROOF_BACKEND_VERSION:
        raise RmsnormLabelSensitivityError("proof backend version drift")
    if payload.get("proof_schema_version") != PROOF_SCHEMA_VERSION:
        raise RmsnormLabelSensitivityError("proof schema version drift")
    if _list(payload.get("non_claims"), "non_claims") != list(NON_CLAIMS):
        raise RmsnormLabelSensitivityError("non-claims drift")
    if _list(payload.get("validation_commands"), "validation_commands") != list(VALIDATION_COMMANDS):
        raise RmsnormLabelSensitivityError("validation commands drift")
    interpretation = _dict(payload.get("interpretation"), "interpretation")
    if interpretation.get("human_read") != HUMAN_READ:
        raise RmsnormLabelSensitivityError("human_read drift")
    if interpretation.get("next_attack") != NEXT_ATTACK:
        raise RmsnormLabelSensitivityError("next_attack drift")
    if interpretation != INTERPRETATION:
        raise RmsnormLabelSensitivityError("interpretation drift")
    source_artifacts = _list(payload.get("source_artifacts"), "source_artifacts")
    expected_source_artifacts = [
        {
            "name": "baseline_accounting",
            "path": str(BASE_ACCOUNTING_PATH.relative_to(ROOT)),
            "sha256": EXPECTED_SOURCE_SHA256["baseline_accounting"],
        },
        {
            "name": "label_probe_accounting",
            "path": str(LABEL_ACCOUNTING_PATH.relative_to(ROOT)),
            "sha256": EXPECTED_SOURCE_SHA256["label_probe_accounting"],
        },
    ]
    if source_artifacts != expected_source_artifacts:
        raise RmsnormLabelSensitivityError("source artifacts drift")
    frontier = _dict(payload.get("frontier"), "frontier")
    expected_frontier = {
        "two_proof_frontier_typed_bytes": TWO_PROOF_FRONTIER_TYPED_BYTES,
        "compact_selector_typed_bytes": COMPACT_SELECTOR_TYPED_BYTES,
        "required_reduction_to_beat_frontier_bytes": REQUIRED_REDUCTION_TO_BEAT_FRONTIER_BYTES,
        "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
        "frontier_win_claimed": False,
        "nanozk_win_claimed": False,
    }
    if frontier.get("frontier_win_claimed") is not False:
        raise RmsnormLabelSensitivityError("frontier overclaim")
    if frontier.get("nanozk_win_claimed") is not False:
        raise RmsnormLabelSensitivityError("NANOZK overclaim")
    if frontier != expected_frontier:
        raise RmsnormLabelSensitivityError("frontier body drift")
    summary = _dict(payload.get("summary"), "summary")
    require_exact_keys(
        summary,
        {
            "canonical_rmsnorm_input_fused_typed_bytes",
            "best_label_probe",
            "best_label_probe_typed_bytes",
            "best_label_probe_delta_vs_frontier_bytes",
            "best_label_probe_delta_vs_compact_bytes",
            "best_label_probe_reduction_vs_canonical_bytes",
            "worst_label_probe",
            "worst_label_probe_typed_bytes",
            "label_only_typed_span_bytes",
            "label_only_span_exceeds_required_frontier_reduction",
            "label_probe_value_delta_vs_canonical_bytes",
        },
        "summary",
    )
    if _int(summary.get("best_label_probe_typed_bytes"), "best probe") != LABEL_PROBE_A_TYPED_BYTES:
        raise RmsnormLabelSensitivityError("best label probe drift")
    if _int(summary.get("label_only_typed_span_bytes"), "span") != 1_264:
        raise RmsnormLabelSensitivityError("label span drift")
    if summary.get("label_only_span_exceeds_required_frontier_reduction") is not True:
        raise RmsnormLabelSensitivityError("span warning erased")
    if _int(summary.get("label_probe_value_delta_vs_canonical_bytes"), "value delta") != 0:
        raise RmsnormLabelSensitivityError("value delta drift")
    variants = _dict(payload.get("variants"), "variants")
    require_exact_keys(variants, set(EXPECTED_VARIANTS), "variants")
    for name in EXPECTED_VARIANTS:
        variant = _dict(variants.get(name), f"variant {name}")
        require_exact_keys(
            variant,
            {
                "name",
                "evidence_relative_path",
                "typed_bytes",
                "typed_delta_vs_two_proof_frontier",
                "proof_json_bytes",
                "typed_groups",
                "path_opening_bytes",
                "value_bytes",
                "record_stream_sha256",
                "label_probe",
                "typed_delta_vs_canonical",
                "path_opening_delta_vs_canonical",
                "value_delta_vs_canonical",
            },
            f"variant {name}",
        )
        expected = EXPECTED_VARIANTS[name]
        typed = _int(variant.get("typed_bytes"), f"{name}.typed")
        if typed != expected["typed"]:
            raise RmsnormLabelSensitivityError(f"{name} typed drift")
        if variant.get("name") != name:
            raise RmsnormLabelSensitivityError(f"{name} name drift")
        if variant.get("evidence_relative_path") != expected["path"]:
            raise RmsnormLabelSensitivityError(f"{name} evidence path drift")
        if _int(variant.get("proof_json_bytes"), f"{name}.proof_json") != expected["proof_json"]:
            raise RmsnormLabelSensitivityError(f"{name} proof JSON drift")
        if variant.get("record_stream_sha256") != expected["record_stream_sha256"]:
            raise RmsnormLabelSensitivityError(f"{name} record stream drift")
        if variant.get("label_probe") is not expected["label_probe"]:
            raise RmsnormLabelSensitivityError(f"{name} label-probe flag drift")
        groups = _dict(variant.get("typed_groups"), f"{name}.groups")
        if groups != expected["groups"]:
            raise RmsnormLabelSensitivityError(f"{name} groups drift")
        if _int(variant.get("path_opening_bytes"), f"{name}.path_opening") != path_opening_bytes(groups):
            raise RmsnormLabelSensitivityError(f"{name} path-opening bytes drift")
        if _int(variant.get("value_bytes"), f"{name}.value_bytes") != value_bytes(groups):
            raise RmsnormLabelSensitivityError(f"{name} value bytes drift")
        if _int(variant.get("typed_delta_vs_two_proof_frontier"), f"{name}.frontier_delta") != (
            typed - TWO_PROOF_FRONTIER_TYPED_BYTES
        ):
            raise RmsnormLabelSensitivityError(f"{name} frontier delta drift")

    canonical = _dict(variants.get("rmsnorm_input_fused"), "canonical variant")
    canonical_typed = _int(canonical.get("typed_bytes"), "canonical typed")
    canonical_groups = _dict(canonical.get("typed_groups"), "canonical groups")
    canonical_path_opening = path_opening_bytes(canonical_groups)
    canonical_value = value_bytes(canonical_groups)
    derived_probe_value_deltas = []
    for name in EXPECTED_VARIANTS:
        variant = _dict(variants.get(name), f"variant {name}")
        groups = _dict(variant.get("typed_groups"), f"{name}.groups")
        typed = _int(variant.get("typed_bytes"), f"{name}.typed")
        typed_delta = typed - canonical_typed
        path_delta = path_opening_bytes(groups) - canonical_path_opening
        value_delta = value_bytes(groups) - canonical_value
        if _int(variant.get("typed_delta_vs_canonical"), f"{name}.typed_delta") != typed_delta:
            raise RmsnormLabelSensitivityError(f"{name} typed delta drift")
        if _int(variant.get("path_opening_delta_vs_canonical"), f"{name}.path_delta") != path_delta:
            raise RmsnormLabelSensitivityError(f"{name} path-opening delta drift")
        if _int(variant.get("value_delta_vs_canonical"), f"{name}.value_delta") != value_delta:
            raise RmsnormLabelSensitivityError(f"{name} value delta drift")
        if EXPECTED_VARIANTS[name]["label_probe"]:
            derived_probe_value_deltas.append(value_delta)

    probes = [
        _dict(variants.get("label_probe_a"), "label probe A"),
        _dict(variants.get("label_probe_b"), "label probe B"),
    ]
    best_probe = min(probes, key=lambda item: _int(item.get("typed_bytes"), "probe typed"))
    worst_probe = max(probes, key=lambda item: _int(item.get("typed_bytes"), "probe typed"))
    best_probe_typed = _int(best_probe.get("typed_bytes"), "best probe typed")
    worst_probe_typed = _int(worst_probe.get("typed_bytes"), "worst probe typed")
    label_only_span = worst_probe_typed - best_probe_typed
    span_exceeds_budget = label_only_span > REQUIRED_REDUCTION_TO_BEAT_FRONTIER_BYTES

    if _int(summary.get("canonical_rmsnorm_input_fused_typed_bytes"), "canonical summary") != canonical_typed:
        raise RmsnormLabelSensitivityError("canonical summary drift")
    if summary.get("best_label_probe") != best_probe.get("name"):
        raise RmsnormLabelSensitivityError("best label probe name drift")
    if _int(summary.get("best_label_probe_typed_bytes"), "best probe") != best_probe_typed:
        raise RmsnormLabelSensitivityError("best label probe drift")
    if _int(summary.get("best_label_probe_delta_vs_frontier_bytes"), "best frontier delta") != (
        best_probe_typed - TWO_PROOF_FRONTIER_TYPED_BYTES
    ):
        raise RmsnormLabelSensitivityError("best frontier delta drift")
    if _int(summary.get("best_label_probe_delta_vs_compact_bytes"), "best compact delta") != (
        best_probe_typed - COMPACT_SELECTOR_TYPED_BYTES
    ):
        raise RmsnormLabelSensitivityError("best compact delta drift")
    if _int(summary.get("best_label_probe_reduction_vs_canonical_bytes"), "best reduction") != (
        canonical_typed - best_probe_typed
    ):
        raise RmsnormLabelSensitivityError("best reduction drift")
    if summary.get("worst_label_probe") != worst_probe.get("name"):
        raise RmsnormLabelSensitivityError("worst label probe name drift")
    if _int(summary.get("worst_label_probe_typed_bytes"), "worst probe") != worst_probe_typed:
        raise RmsnormLabelSensitivityError("worst label probe drift")
    if _int(summary.get("label_only_typed_span_bytes"), "span") != label_only_span:
        raise RmsnormLabelSensitivityError("label span drift")
    if summary.get("label_only_span_exceeds_required_frontier_reduction") is not span_exceeds_budget:
        raise RmsnormLabelSensitivityError("span warning drift")
    if any(delta != 0 for delta in derived_probe_value_deltas):
        raise RmsnormLabelSensitivityError("derived probe value delta drift")
    if "mutation_result" in payload:
        validate_mutation_result(_dict(payload.get("mutation_result"), "mutation result"))
    expected_commitment = payload_commitment(payload)
    if payload.get("payload_commitment") != expected_commitment:
        raise RmsnormLabelSensitivityError("payload commitment drift")


def run_mutations(payload: dict[str, Any]) -> dict[str, Any]:
    cases = []
    mutations = (
        (
            "frontier_overclaim",
            lambda p: p["frontier"].__setitem__("frontier_win_claimed", True),
        ),
        (
            "nanozk_overclaim",
            lambda p: p["frontier"].__setitem__("nanozk_win_claimed", True),
        ),
        (
            "best_probe_typed_drift",
            lambda p: p["summary"].__setitem__("best_label_probe_typed_bytes", 40_700),
        ),
        (
            "best_probe_name_drift",
            lambda p: p["summary"].__setitem__("best_label_probe", "label_probe_b"),
        ),
        (
            "decision_drift",
            lambda p: p.__setitem__("decision", "GO_FRONTIER_PROMOTION"),
        ),
        (
            "result_drift",
            lambda p: p.__setitem__("result", "LABEL_ONLY_PROBE_BEATS_FRONTIER"),
        ),
        (
            "issue_drift",
            lambda p: p.__setitem__("issue", "https://example.invalid/issue"),
        ),
        (
            "claim_boundary_drift",
            lambda p: p.__setitem__("claim_boundary", "OVERCLAIMED_BOUNDARY"),
        ),
        (
            "proof_backend_version_drift",
            lambda p: p.__setitem__("proof_backend_version", "unversioned"),
        ),
        (
            "interpretation_drift",
            lambda p: p["interpretation"].__setitem__("human_read", "overclaimed"),
        ),
        (
            "source_digest_drift",
            lambda p: p["source_artifacts"][1].__setitem__("sha256", "00" * 32),
        ),
        (
            "non_claims_erased",
            lambda p: p.__setitem__("non_claims", []),
        ),
        (
            "validation_commands_erased",
            lambda p: p.__setitem__("validation_commands", []),
        ),
        (
            "label_span_erased",
            lambda p: p["summary"].__setitem__("label_only_typed_span_bytes", 1),
        ),
        (
            "span_warning_erased",
            lambda p: p["summary"].__setitem__(
                "label_only_span_exceeds_required_frontier_reduction", False
            ),
        ),
        (
            "value_delta_smuggled",
            lambda p: p["summary"].__setitem__("label_probe_value_delta_vs_canonical_bytes", -1),
        ),
        (
            "probe_a_group_drift",
            lambda p: p["variants"]["label_probe_a"]["typed_groups"].__setitem__(
                "fri_decommitments", 12_000
            ),
        ),
        (
            "probe_a_missing_path_opening_group",
            lambda p: p["variants"]["label_probe_a"]["typed_groups"].pop("fri_decommitments"),
        ),
        (
            "summary_extra_key",
            lambda p: p["summary"].__setitem__("frontier_win_claimed", True),
        ),
        (
            "variant_extra_key",
            lambda p: p["variants"]["label_probe_a"].__setitem__("unchecked_note", "misleading"),
        ),
        (
            "payload_commitment_drift",
            lambda p: p.__setitem__("payload_commitment", "blake2b-256:" + "00" * 32),
        ),
    )
    if tuple(name for name, _mutate in mutations) != EXPECTED_MUTATION_NAMES:
        raise RmsnormLabelSensitivityError("mutation definitions drift")
    for name, mutate in mutations:
        mutated = copy.deepcopy(payload)
        mutated.pop("mutation_result", None)
        mutate(mutated)
        if name != "payload_commitment_drift":
            refresh_payload_commitment(mutated)
        rejected = False
        try:
            validate_payload(mutated)
        except RmsnormLabelSensitivityError:
            rejected = True
        cases.append({"name": name, "rejected": rejected})
    rejected_count = sum(1 for case in cases if case["rejected"])
    return {
        "mutation_count": len(cases),
        "rejected_count": rejected_count,
        "cases": cases,
    }


def require_output_path(path: pathlib.Path) -> pathlib.Path:
    raw_candidate = path if path.is_absolute() else ROOT / path
    if raw_candidate.is_symlink():
        raise RmsnormLabelSensitivityError(f"refusing to overwrite symlink: {path}")
    if raw_candidate.parent.is_symlink():
        raise RmsnormLabelSensitivityError(f"output parent must not be a symlink: {path}")
    evidence_dir = resolve_evidence_dir()
    try:
        parent = raw_candidate.parent.resolve(strict=True)
    except OSError as err:
        raise RmsnormLabelSensitivityError(f"failed to resolve output parent for {path}: {err}") from err
    if parent != evidence_dir:
        raise RmsnormLabelSensitivityError(f"output must be in evidence dir: {path}")
    return raw_candidate


def resolve_evidence_dir() -> pathlib.Path:
    if EVIDENCE_DIR.is_symlink():
        raise RmsnormLabelSensitivityError(f"refusing symlinked evidence directory: {EVIDENCE_DIR}")
    try:
        evidence_dir = EVIDENCE_DIR.resolve(strict=True)
        root = ROOT.resolve(strict=True)
    except OSError as err:
        raise RmsnormLabelSensitivityError(f"failed to resolve evidence directory: {err}") from err
    if not evidence_dir.is_relative_to(root):
        raise RmsnormLabelSensitivityError(f"evidence directory must stay under {ROOT}: {EVIDENCE_DIR}")
    return evidence_dir


def write_text_atomically(path: pathlib.Path, text: str) -> None:
    path = require_output_path(path)
    dir_fd: int | None = None
    fd: int | None = None
    tmp_name: str | None = None
    try:
        dir_fd = open_directory_fd(path.parent)
        tmp_name = f".{path.name}.{os.getpid()}.{secrets.token_hex(8)}.tmp"
        temp_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | require_no_follow_flag(
            f"temp-file creation for {path}"
        )
        fd = os.open(tmp_name, temp_flags, 0o666, dir_fd=dir_fd)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            fd = None
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path.name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
        fsync_dir_fd(dir_fd, path.parent)
    except OSError as err:
        if fd is not None:
            with contextlib.suppress(OSError):
                os.close(fd)
        if tmp_name is not None and dir_fd is not None:
            with contextlib.suppress(OSError):
                os.unlink(tmp_name, dir_fd=dir_fd)
        raise RmsnormLabelSensitivityError(f"failed to write {path}: {err}") from err
    finally:
        if dir_fd is not None:
            os.close(dir_fd)


def open_directory_fd(path: pathlib.Path) -> int:
    flags = os.O_RDONLY | require_no_follow_flag(f"directory open for {path}")
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    if isinstance(directory_flag, int) and directory_flag != 0:
        flags |= directory_flag
    return os.open(path, flags)


def fsync_dir_fd(dir_fd: int, path: pathlib.Path) -> None:
    try:
        os.fsync(dir_fd)
    except OSError as err:
        raise RmsnormLabelSensitivityError(f"failed to fsync directory {path}: {err}") from err


def tsv_text(payload: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for name in ("compact_selector", "rmsnorm_input_fused", "label_probe_a", "label_probe_b"):
        variant = payload["variants"][name]
        writer.writerow(
            {
                "variant": name,
                "typed_bytes": variant["typed_bytes"],
                "typed_delta_vs_canonical": variant["typed_delta_vs_canonical"],
                "typed_delta_vs_two_proof_frontier": variant["typed_delta_vs_two_proof_frontier"],
                "path_opening_bytes": variant["path_opening_bytes"],
                "path_opening_delta_vs_canonical": variant["path_opening_delta_vs_canonical"],
                "value_bytes": variant["value_bytes"],
                "value_delta_vs_canonical": variant["value_delta_vs_canonical"],
                "proof_json_bytes": variant["proof_json_bytes"],
            }
        )
    return output.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    args = parser.parse_args()
    payload = build_payload()
    if args.write_json:
        write_text_atomically(args.write_json, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if args.write_tsv:
        write_text_atomically(args.write_tsv, tsv_text(payload))
    print(
        json.dumps(
            {
                "decision": payload["decision"],
                "result": payload["result"],
                "best_label_probe_typed_bytes": payload["summary"]["best_label_probe_typed_bytes"],
                "label_only_typed_span_bytes": payload["summary"]["label_only_typed_span_bytes"],
                "mutations_rejected": payload["mutation_result"]["rejected_count"],
                "mutation_count": payload["mutation_result"]["mutation_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
