#!/usr/bin/env python3
"""Gate the RMSNorm-input adjacent opening-layout probe."""

from __future__ import annotations

import argparse
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
ACCOUNTING_PATH = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-adjacent-layout-accounting-2026-05.json"
JSON_OUT = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-adjacent-layout-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-adjacent-layout-2026-05.tsv"
MAX_INPUT_JSON_BYTES = 64 * 1024 * 1024

SCHEMA = "zkai-native-attention-mlp-rmsnorm-adjacent-layout-gate-v1"
DECISION = "NO_GO_WORST_LABEL_FRONTIER_PROMOTION_BUT_GO_LAYOUT_LEVER"
RESULT = "ADJACENT_LAYOUT_SAVES_480_TYPED_BYTES_CANONICALLY_BUT_WORST_LABEL_REMAINS_2024_BYTES_ABOVE_FRONTIER"
ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/644"
PAYLOAD_DOMAIN = "ptvm:zkai:native-attention-mlp-rmsnorm-adjacent-layout:v1"
CLAIM_BOUNDARY = (
    "RMSNORM_INPUT_ADJACENT_FIXED_COLUMN_LAYOUT_IS_A_REAL_OPENING_LAYOUT_LEVER_"
    "BUT_DOES_NOT_SATISFY_WORST_LABEL_FRONTIER_PROMOTION"
)

EXPECTED_ACCOUNTING_SHA256 = "64fdab3dbcd5c5c196425121820bf2bc6ec301b98a94fea64d8fa51fb47d5da6"
TWO_PROOF_FRONTIER_TYPED_BYTES = 40_700
COMPACT_SELECTOR_TYPED_BYTES = 40_812
CANONICAL_RMSNORM_TYPED_BYTES = 41_428
ADJACENT_CANONICAL_TYPED_BYTES = 40_948
ADJACENT_WORST_LABEL_TYPED_BYTES = 42_724
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900
PATH_OPENING_GROUPS = ("fri_decommitments", "fri_samples", "trace_decommitments")
VALUE_GROUPS = ("oods_samples", "queries_values")

EXPECTED_VARIANTS = {
    "compact_selector": {
        "path": "zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json",
        "proof_json": 116_091,
        "typed": 40_812,
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
        "layout_probe": False,
    },
    "rmsnorm_input_fused": {
        "path": "zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json",
        "proof_json": 118_378,
        "typed": 41_428,
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
        "layout_probe": False,
    },
    "adjacent_layout": {
        "path": "zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.envelope.json",
        "proof_json": 116_847,
        "typed": 40_948,
        "groups": {
            "fixed_overhead": 48,
            "fri_decommitments": 12_832,
            "fri_samples": 800,
            "oods_samples": 11_952,
            "queries_values": 8_916,
            "trace_decommitments": 6_400,
        },
        "record_stream_sha256": "e363d9a7577d80d7240bde40053732cd5938dcb324b459092d2815a0f0428710",
        "label_probe": False,
        "layout_probe": True,
    },
    "adjacent_label_probe_a": {
        "path": "zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-a-2026-05.envelope.json",
        "proof_json": 116_882,
        "typed": 40_948,
        "groups": {
            "fixed_overhead": 48,
            "fri_decommitments": 12_832,
            "fri_samples": 800,
            "oods_samples": 11_952,
            "queries_values": 8_916,
            "trace_decommitments": 6_400,
        },
        "record_stream_sha256": "e363d9a7577d80d7240bde40053732cd5938dcb324b459092d2815a0f0428710",
        "label_probe": True,
        "layout_probe": True,
    },
    "adjacent_label_probe_b": {
        "path": "zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-b-2026-05.envelope.json",
        "proof_json": 123_141,
        "typed": 42_724,
        "groups": {
            "fixed_overhead": 48,
            "fri_decommitments": 14_176,
            "fri_samples": 848,
            "oods_samples": 11_952,
            "queries_values": 8_916,
            "trace_decommitments": 6_784,
        },
        "record_stream_sha256": "75ff14f548a97546870ea9f4c36951bb7b02d9ca2f736a11ff38a6b83403e28d",
        "label_probe": True,
        "layout_probe": True,
    },
}

NON_CLAIMS = (
    "not a two-proof frontier beat",
    "not a proof-size win",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not a full transformer block proof",
    "not timing evidence",
    "not production-ready zkML",
    "does not close issue 644",
)

VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent-label-probe-a docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-a-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-a-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-a-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-a-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent-label-probe-b docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-b-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-b-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-b-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-b-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-a-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-b-2026-05.envelope.json > docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-adjacent-layout-accounting-2026-05.json",
    "python3 scripts/zkai_native_attention_mlp_rmsnorm_adjacent_layout_gate.py --write-json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-adjacent-layout-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-adjacent-layout-2026-05.tsv",
    "python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_adjacent_layout_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend native_attention_mlp_single_proof --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

TSV_COLUMNS = (
    "variant",
    "typed_bytes",
    "delta_vs_frontier",
    "path_opening_bytes",
    "path_opening_delta_vs_canonical",
    "value_bytes",
    "value_delta_vs_canonical",
    "proof_json_bytes",
    "policy_status",
)


class AdjacentLayoutGateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode(
            "utf-8"
        )
    except (TypeError, ValueError) as err:
        raise AdjacentLayoutGateError(f"invalid JSON value: {err}") from err


def payload_commitment(payload: dict[str, Any]) -> str:
    clone = copy.deepcopy(payload)
    clone.pop("payload_commitment", None)
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("ascii"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(clone))
    return f"blake2b-256:{digest.hexdigest()}"


def normalize_input_path(path: pathlib.Path) -> pathlib.Path:
    try:
        st = os.lstat(path)
    except FileNotFoundError as err:
        raise AdjacentLayoutGateError(f"missing input artifact: {path}") from err
    if stat.S_ISLNK(st.st_mode):
        raise AdjacentLayoutGateError(f"refusing to read through symlink: {path}")
    if not stat.S_ISREG(st.st_mode):
        raise AdjacentLayoutGateError(f"input artifact is not a regular file: {path}")
    resolved = path.resolve()
    evidence_root = EVIDENCE_DIR.resolve()
    if evidence_root != resolved and evidence_root not in resolved.parents:
        raise AdjacentLayoutGateError(f"input path outside evidence dir: {path}")
    return resolved


def read_input_bytes(path: pathlib.Path) -> bytes:
    target = normalize_input_path(path)
    if target.stat().st_size > MAX_INPUT_JSON_BYTES:
        raise AdjacentLayoutGateError(f"input artifact too large: {path}")
    return target.read_bytes()


def json_from_bytes(raw: bytes, path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as err:
        raise AdjacentLayoutGateError(f"invalid JSON in {path}: {err}") from err
    if not isinstance(value, dict):
        raise AdjacentLayoutGateError(f"expected object JSON in {path}")
    return value


def _int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise AdjacentLayoutGateError(f"{label} must be an integer")
    return value


def _str(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise AdjacentLayoutGateError(f"{label} must be a string")
    return value


def grouped(row: dict[str, Any]) -> dict[str, int]:
    accounting = row.get("local_binary_accounting")
    if not isinstance(accounting, dict):
        raise AdjacentLayoutGateError("row missing local binary accounting")
    groups = accounting.get("grouped_reconstruction")
    if not isinstance(groups, dict):
        raise AdjacentLayoutGateError("row missing grouped reconstruction")
    expected = ("fixed_overhead", "fri_decommitments", "fri_samples", "oods_samples", "queries_values", "trace_decommitments")
    if tuple(sorted(groups)) != tuple(sorted(expected)):
        raise AdjacentLayoutGateError("unexpected grouped reconstruction keys")
    return {key: _int(groups[key], f"group {key}") for key in expected}


def path_opening_bytes(groups: dict[str, int]) -> int:
    return sum(groups[key] for key in PATH_OPENING_GROUPS)


def value_bytes(groups: dict[str, int]) -> int:
    return sum(groups[key] for key in VALUE_GROUPS)


def variant_from_row(name: str, row: dict[str, Any]) -> dict[str, Any]:
    expected = EXPECTED_VARIANTS[name]
    path = _str(row.get("evidence_relative_path"), f"{name}.path")
    if path != expected["path"]:
        raise AdjacentLayoutGateError(f"{name} path drift: {path}")
    proof_json = _int(row.get("proof_json_size_bytes"), f"{name}.proof_json")
    accounting = row.get("local_binary_accounting")
    if not isinstance(accounting, dict):
        raise AdjacentLayoutGateError(f"{name} local accounting missing")
    typed = _int(accounting.get("typed_size_estimate_bytes"), f"{name}.typed")
    groups = grouped(row)
    record_stream_sha256 = _str(accounting.get("record_stream_sha256"), f"{name}.record_stream_sha256")
    if proof_json != expected["proof_json"] or typed != expected["typed"] or groups != expected["groups"]:
        raise AdjacentLayoutGateError(f"{name} metric drift")
    if record_stream_sha256 != expected["record_stream_sha256"]:
        raise AdjacentLayoutGateError(f"{name} record stream digest drift")
    return {
        "name": name,
        "evidence_relative_path": path,
        "proof_json_bytes": proof_json,
        "typed_bytes": typed,
        "typed_delta_vs_two_proof_frontier": typed - TWO_PROOF_FRONTIER_TYPED_BYTES,
        "path_opening_bytes": path_opening_bytes(groups),
        "path_opening_delta_vs_canonical": path_opening_bytes(groups)
        - path_opening_bytes(EXPECTED_VARIANTS["rmsnorm_input_fused"]["groups"]),
        "value_bytes": value_bytes(groups),
        "value_delta_vs_canonical": value_bytes(groups) - value_bytes(EXPECTED_VARIANTS["rmsnorm_input_fused"]["groups"]),
        "typed_groups": groups,
        "record_stream_sha256": record_stream_sha256,
        "label_probe": expected["label_probe"],
        "layout_probe": expected["layout_probe"],
    }


def rows_by_expected_path(accounting: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = accounting.get("rows")
    if not isinstance(rows, list):
        raise AdjacentLayoutGateError("accounting rows missing")
    by_path = {}
    for row in rows:
        if not isinstance(row, dict):
            raise AdjacentLayoutGateError("accounting row must be object")
        path = _str(row.get("evidence_relative_path"), "row path")
        if path in by_path:
            raise AdjacentLayoutGateError(f"duplicate accounting row path: {path}")
        by_path[path] = row
    expected_paths = {entry["path"] for entry in EXPECTED_VARIANTS.values()}
    if set(by_path) != expected_paths:
        raise AdjacentLayoutGateError("accounting row inventory drift")
    return by_path


def build_payload(*, include_mutations: bool = True) -> dict[str, Any]:
    accounting_raw = read_input_bytes(ACCOUNTING_PATH)
    if hashlib.sha256(accounting_raw).hexdigest() != EXPECTED_ACCOUNTING_SHA256:
        raise AdjacentLayoutGateError("adjacent accounting source digest drift")
    accounting = json_from_bytes(accounting_raw, ACCOUNTING_PATH)
    by_path = rows_by_expected_path(accounting)
    variants = {
        name: variant_from_row(name, by_path[entry["path"]])
        for name, entry in EXPECTED_VARIANTS.items()
    }
    adjacent = variants["adjacent_layout"]
    canonical = variants["rmsnorm_input_fused"]
    worst = max(
        [variants["adjacent_layout"], variants["adjacent_label_probe_a"], variants["adjacent_label_probe_b"]],
        key=lambda entry: entry["typed_bytes"],
    )
    best = min(
        [variants["adjacent_layout"], variants["adjacent_label_probe_a"], variants["adjacent_label_probe_b"]],
        key=lambda entry: entry["typed_bytes"],
    )
    canonical_saving = canonical["typed_bytes"] - adjacent["typed_bytes"]
    if canonical_saving != 480:
        raise AdjacentLayoutGateError("canonical adjacent saving drift")
    if worst["typed_bytes"] != ADJACENT_WORST_LABEL_TYPED_BYTES:
        raise AdjacentLayoutGateError("worst adjacent label drift")
    payload = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_accounting_path": str(ACCOUNTING_PATH.relative_to(ROOT)),
        "source_accounting_sha256": EXPECTED_ACCOUNTING_SHA256,
        "two_proof_frontier_typed_bytes": TWO_PROOF_FRONTIER_TYPED_BYTES,
        "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
        "compact_selector_typed_bytes": COMPACT_SELECTOR_TYPED_BYTES,
        "canonical_rmsnorm_input_fused_typed_bytes": CANONICAL_RMSNORM_TYPED_BYTES,
        "adjacent_canonical_typed_bytes": ADJACENT_CANONICAL_TYPED_BYTES,
        "adjacent_canonical_saving_vs_canonical_typed_bytes": canonical_saving,
        "adjacent_canonical_delta_vs_frontier_typed_bytes": adjacent["typed_bytes"] - TWO_PROOF_FRONTIER_TYPED_BYTES,
        "adjacent_worst_label_typed_bytes": worst["typed_bytes"],
        "adjacent_worst_label_delta_vs_frontier_typed_bytes": worst["typed_bytes"] - TWO_PROOF_FRONTIER_TYPED_BYTES,
        "adjacent_best_label_typed_bytes": best["typed_bytes"],
        "adjacent_label_span_typed_bytes": worst["typed_bytes"] - best["typed_bytes"],
        "variants": variants,
        "interpretation": {
            "human_read": (
                "Moving the RMSNorm-input fixed adapter columns next to the RMSNorm public-row columns is a real "
                "proof-layout lever: canonical typed bytes drop by 480. It is not enough for promotion because "
                "the bad adjacent label is 42,724 typed bytes, 2,024 above the two-proof frontier."
            ),
            "next_attack": (
                "Do not claim a frontier win. The next useful route must stabilize query/opening behavior across "
                "labels or find another component ordering that keeps the 480-byte canonical saving without the "
                "1,776-byte adjacent label penalty."
            ),
        },
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
        "mutation_results": [],
    }
    payload["payload_commitment"] = payload_commitment(payload)
    if include_mutations:
        payload["mutation_results"] = run_mutations(payload)
        payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload, require_mutations=include_mutations)
    return payload


def validate_payload(payload: dict[str, Any], *, require_mutations: bool = True) -> None:
    required = {
        "schema",
        "decision",
        "result",
        "issue",
        "claim_boundary",
        "source_accounting_path",
        "source_accounting_sha256",
        "two_proof_frontier_typed_bytes",
        "nanozk_reported_d128_block_proof_bytes",
        "compact_selector_typed_bytes",
        "canonical_rmsnorm_input_fused_typed_bytes",
        "adjacent_canonical_typed_bytes",
        "adjacent_canonical_saving_vs_canonical_typed_bytes",
        "adjacent_canonical_delta_vs_frontier_typed_bytes",
        "adjacent_worst_label_typed_bytes",
        "adjacent_worst_label_delta_vs_frontier_typed_bytes",
        "adjacent_best_label_typed_bytes",
        "adjacent_label_span_typed_bytes",
        "variants",
        "interpretation",
        "non_claims",
        "validation_commands",
        "mutation_results",
        "payload_commitment",
    }
    if set(payload) != required:
        raise AdjacentLayoutGateError("payload key drift")
    if payload["schema"] != SCHEMA or payload["decision"] != DECISION or payload["result"] != RESULT:
        raise AdjacentLayoutGateError("payload metadata drift")
    if payload["claim_boundary"] != CLAIM_BOUNDARY or payload["issue"] != ISSUE:
        raise AdjacentLayoutGateError("claim boundary drift")
    if payload["source_accounting_path"] != str(ACCOUNTING_PATH.relative_to(ROOT)):
        raise AdjacentLayoutGateError("source accounting path drift")
    if payload["source_accounting_sha256"] != EXPECTED_ACCOUNTING_SHA256:
        raise AdjacentLayoutGateError("source digest drift")
    if payload["two_proof_frontier_typed_bytes"] != TWO_PROOF_FRONTIER_TYPED_BYTES:
        raise AdjacentLayoutGateError("frontier drift")
    if payload["nanozk_reported_d128_block_proof_bytes"] != NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES:
        raise AdjacentLayoutGateError("NANOZK reference drift")
    variants = payload["variants"]
    if not isinstance(variants, dict) or set(variants) != set(EXPECTED_VARIANTS):
        raise AdjacentLayoutGateError("variant inventory drift")
    for name, expected in EXPECTED_VARIANTS.items():
        variant = variants[name]
        if not isinstance(variant, dict):
            raise AdjacentLayoutGateError(f"{name} variant is not object")
        if variant["typed_bytes"] != expected["typed"] or variant["proof_json_bytes"] != expected["proof_json"]:
            raise AdjacentLayoutGateError(f"{name} variant metric drift")
        if variant["typed_groups"] != expected["groups"]:
            raise AdjacentLayoutGateError(f"{name} group drift")
    adjacent = variants["adjacent_layout"]
    canonical = variants["rmsnorm_input_fused"]
    compact = variants["compact_selector"]
    worst = max(
        [variants["adjacent_layout"], variants["adjacent_label_probe_a"], variants["adjacent_label_probe_b"]],
        key=lambda entry: entry["typed_bytes"],
    )
    best = min(
        [variants["adjacent_layout"], variants["adjacent_label_probe_a"], variants["adjacent_label_probe_b"]],
        key=lambda entry: entry["typed_bytes"],
    )
    if payload["compact_selector_typed_bytes"] != compact["typed_bytes"]:
        raise AdjacentLayoutGateError("compact selector summary drift")
    if payload["canonical_rmsnorm_input_fused_typed_bytes"] != canonical["typed_bytes"]:
        raise AdjacentLayoutGateError("canonical RMSNorm-input summary drift")
    if payload["adjacent_canonical_typed_bytes"] != adjacent["typed_bytes"]:
        raise AdjacentLayoutGateError("adjacent canonical summary drift")
    if payload["adjacent_canonical_saving_vs_canonical_typed_bytes"] != canonical["typed_bytes"] - adjacent["typed_bytes"]:
        raise AdjacentLayoutGateError("adjacent canonical saving arithmetic drift")
    if payload["adjacent_canonical_delta_vs_frontier_typed_bytes"] != adjacent["typed_bytes"] - TWO_PROOF_FRONTIER_TYPED_BYTES:
        raise AdjacentLayoutGateError("adjacent frontier delta arithmetic drift")
    if payload["adjacent_worst_label_typed_bytes"] != worst["typed_bytes"]:
        raise AdjacentLayoutGateError("worst label summary drift")
    if payload["adjacent_worst_label_delta_vs_frontier_typed_bytes"] != worst["typed_bytes"] - TWO_PROOF_FRONTIER_TYPED_BYTES:
        raise AdjacentLayoutGateError("worst label frontier delta drift")
    if payload["adjacent_best_label_typed_bytes"] != best["typed_bytes"]:
        raise AdjacentLayoutGateError("best label summary drift")
    if payload["adjacent_label_span_typed_bytes"] != worst["typed_bytes"] - best["typed_bytes"]:
        raise AdjacentLayoutGateError("label span drift")
    if payload["adjacent_worst_label_delta_vs_frontier_typed_bytes"] <= 0:
        raise AdjacentLayoutGateError("frontier overclaim: worst adjacent label does not beat frontier")
    non_claims = payload["non_claims"]
    if not isinstance(non_claims, list) or any(not isinstance(item, str) for item in non_claims):
        raise AdjacentLayoutGateError("non-claims must be a list of strings")
    if tuple(non_claims) != NON_CLAIMS:
        raise AdjacentLayoutGateError("non-claims drift")
    if tuple(payload["validation_commands"]) != VALIDATION_COMMANDS:
        raise AdjacentLayoutGateError("validation command drift")
    if payload["payload_commitment"] != payload_commitment(payload):
        raise AdjacentLayoutGateError("payload commitment drift")
    if require_mutations:
        validate_mutation_results(payload["mutation_results"])


MUTATIONS = (
    ("frontier_overclaim", lambda p: p.__setitem__("decision", "GO_FRONTIER_PROMOTION")),
    ("result_overclaim", lambda p: p.__setitem__("result", "ADJACENT_LAYOUT_BEATS_FRONTIER")),
    ("worst_label_erased", lambda p: p.__setitem__("adjacent_worst_label_typed_bytes", 40_699)),
    ("canonical_saving_drift", lambda p: p.__setitem__("adjacent_canonical_saving_vs_canonical_typed_bytes", 481)),
    ("label_span_drift", lambda p: p.__setitem__("adjacent_label_span_typed_bytes", 1)),
    ("nanozk_overclaim", lambda p: p.__setitem__("nanozk_reported_d128_block_proof_bytes", 40_948)),
    ("source_digest_drift", lambda p: p.__setitem__("source_accounting_sha256", "0" * 64)),
    ("non_claims_erased", lambda p: p.__setitem__("non_claims", [])),
    ("validation_commands_erased", lambda p: p.__setitem__("validation_commands", [])),
    ("variant_metric_drift", lambda p: p["variants"]["adjacent_layout"].__setitem__("typed_bytes", 40_700)),
    ("group_drift", lambda p: p["variants"]["adjacent_layout"]["typed_groups"].__setitem__("fri_decommitments", 0)),
    ("payload_commitment_drift", lambda p: p.__setitem__("payload_commitment", "blake2b-256:" + "0" * 64)),
)


def run_mutations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    clean = copy.deepcopy(payload)
    clean["mutation_results"] = []
    clean["payload_commitment"] = payload_commitment(clean)
    for name, mutator in MUTATIONS:
        mutated = copy.deepcopy(clean)
        mutator(mutated)
        if name != "payload_commitment_drift":
            mutated["payload_commitment"] = payload_commitment(mutated)
        try:
            validate_payload(mutated, require_mutations=False)
        except AdjacentLayoutGateError as err:
            results.append({"name": name, "rejected": True, "reason": str(err)})
        else:
            results.append({"name": name, "rejected": False, "reason": ""})
    return results


def validate_mutation_results(results: Any) -> None:
    if not isinstance(results, list):
        raise AdjacentLayoutGateError("mutation results must be a list")
    if len(results) != len(MUTATIONS):
        raise AdjacentLayoutGateError("mutation inventory length drift")
    for entry in results:
        if not isinstance(entry, dict):
            raise AdjacentLayoutGateError("mutation entry must be an object")
    names = [entry.get("name") for entry in results]
    if names != [name for name, _ in MUTATIONS]:
        raise AdjacentLayoutGateError("mutation inventory drift")
    for entry in results:
        if set(entry) != {"name", "rejected", "reason"}:
            raise AdjacentLayoutGateError("mutation entry key drift")
        if entry["rejected"] is not True or not entry["reason"]:
            raise AdjacentLayoutGateError(f"mutation did not reject: {entry['name']}")


def tsv_text(payload: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for name in EXPECTED_VARIANTS:
        variant = payload["variants"][name]
        policy_status = "no_go_worst_label" if name.startswith("adjacent") else "reference"
        writer.writerow(
            {
                "variant": name,
                "typed_bytes": variant["typed_bytes"],
                "delta_vs_frontier": variant["typed_delta_vs_two_proof_frontier"],
                "path_opening_bytes": variant["path_opening_bytes"],
                "path_opening_delta_vs_canonical": variant["path_opening_delta_vs_canonical"],
                "value_bytes": variant["value_bytes"],
                "value_delta_vs_canonical": variant["value_delta_vs_canonical"],
                "proof_json_bytes": variant["proof_json_bytes"],
                "policy_status": policy_status,
            }
        )
    return output.getvalue()


def normalize_output_path(path: pathlib.Path) -> pathlib.Path:
    resolved = path.resolve()
    evidence_root = EVIDENCE_DIR.resolve()
    if evidence_root != resolved and evidence_root not in resolved.parents:
        raise AdjacentLayoutGateError(f"output path outside evidence dir: {path}")
    try:
        st = os.lstat(resolved)
    except FileNotFoundError:
        return resolved
    if stat.S_ISLNK(st.st_mode):
        raise AdjacentLayoutGateError(f"refusing to write through symlink: {path}")
    return resolved


def write_atomic(path: pathlib.Path, data: bytes) -> None:
    target = normalize_output_path(path)
    suffix = target.suffix
    if suffix not in {".json", ".tsv"}:
        raise AdjacentLayoutGateError(f"unsupported output suffix: {target}")
    tmp = target.with_name(f".{target.name}.{secrets.token_hex(8)}.tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, target)
    except Exception:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path | None, tsv_path: pathlib.Path | None) -> None:
    if json_path:
        write_atomic(json_path, json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    if tsv_path:
        write_atomic(tsv_path, tsv_text(payload).encode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    args = parser.parse_args()
    payload = build_payload(include_mutations=True)
    write_outputs(payload, args.write_json, args.write_tsv)
    print(
        json.dumps(
            {
                "decision": payload["decision"],
                "result": payload["result"],
                "adjacent_canonical_typed_bytes": payload["adjacent_canonical_typed_bytes"],
                "adjacent_canonical_saving_vs_canonical_typed_bytes": payload[
                    "adjacent_canonical_saving_vs_canonical_typed_bytes"
                ],
                "adjacent_worst_label_typed_bytes": payload["adjacent_worst_label_typed_bytes"],
                "adjacent_worst_label_delta_vs_frontier_typed_bytes": payload[
                    "adjacent_worst_label_delta_vs_frontier_typed_bytes"
                ],
                "mutation_count": len(payload["mutation_results"]),
                "mutations_rejected": sum(1 for entry in payload["mutation_results"] if entry["rejected"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
