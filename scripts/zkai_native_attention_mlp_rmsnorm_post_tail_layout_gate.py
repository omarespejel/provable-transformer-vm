#!/usr/bin/env python3
"""Gate the RMSNorm-input post-tail opening-layout probe."""

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
ACCOUNTING_PATH = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-post-tail-layout-accounting-2026-05.json"
JSON_OUT = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-post-tail-layout-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-post-tail-layout-2026-05.tsv"
MAX_INPUT_JSON_BYTES = 64 * 1024 * 1024

SCHEMA = "zkai-native-attention-mlp-rmsnorm-post-tail-layout-gate-v1"
DECISION = "NO_GO_POST_TAIL_LAYOUT_LABEL_STABILITY"
RESULT = (
    "POST_TAIL_CANONICAL_MATCHES_ADJACENT_BAD_LABEL_42724_TYPED_BYTES_"
    "AND_DOES_NOT_PROMOTE_FRONTIER"
)
ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/665"
PARENT_ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/641"
PAYLOAD_DOMAIN = "ptvm:zkai:native-attention-mlp-rmsnorm-post-tail-layout:v1"
CLAIM_BOUNDARY = (
    "RMSNORM_INPUT_POST_TAIL_FIXED_COLUMN_LAYOUT_PRESERVES_ZERO_ADAPTER_BASE_CELLS_"
    "BUT_INHERITS_THE_BAD_OPENING_LAYOUT_AND_IS_NOT_A_FRONTIER_PROMOTION"
)

EXPECTED_ACCOUNTING_SHA256 = "476ddfdfaca57fd5726d0cd564d57fb983fb0b454d1781b832af3ff68d193fb2"
TWO_PROOF_FRONTIER_TYPED_BYTES = 40_700
COMPACT_SELECTOR_TYPED_BYTES = 40_812
CANONICAL_RMSNORM_TYPED_BYTES = 41_428
ADJACENT_CANONICAL_TYPED_BYTES = 40_948
ADJACENT_BAD_LABEL_TYPED_BYTES = 42_724
POST_TAIL_CANONICAL_TYPED_BYTES = 42_724
POST_TAIL_BEST_LABEL_TYPED_BYTES = 41_508
POST_TAIL_WORST_LABEL_TYPED_BYTES = 42_724
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900
PATH_OPENING_GROUPS = ("fri_decommitments", "fri_samples", "trace_decommitments")
VALUE_GROUPS = ("oods_samples", "queries_values")

EXPECTED_VARIANTS: dict[str, dict[str, Any]] = {
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
        "policy_group": "reference",
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
        "policy_group": "reference",
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
        "policy_group": "adjacent_reference",
    },
    "adjacent_bad_label": {
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
        "policy_group": "adjacent_bad_label_reference",
    },
    "post_tail_layout": {
        "path": "zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-layout-2026-05.envelope.json",
        "proof_json": 122_976,
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
        "label_probe": False,
        "layout_probe": True,
        "policy_group": "post_tail",
    },
    "post_tail_label_probe_a": {
        "path": "zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-a-2026-05.envelope.json",
        "proof_json": 118_526,
        "typed": 41_508,
        "groups": {
            "fixed_overhead": 48,
            "fri_decommitments": 13_248,
            "fri_samples": 816,
            "oods_samples": 11_952,
            "queries_values": 8_916,
            "trace_decommitments": 6_528,
        },
        "record_stream_sha256": "80c5a9e5f8dcc3df29e415eb8cee5b7173bf8550cba499e5341a94c4ff76f0dd",
        "label_probe": True,
        "layout_probe": True,
        "policy_group": "post_tail",
    },
    "post_tail_label_probe_b": {
        "path": "zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-b-2026-05.envelope.json",
        "proof_json": 123_018,
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
        "policy_group": "post_tail",
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
    "does not close parent issue 641",
)

INTERPRETATION = {
    "human_read": (
        "Moving RMSNorm-input fused fixed columns after the MLP tail keeps zero adapter base cells, "
        "but it lands on the same 42,724 typed-byte opening shape as the adjacent bad-label probe. "
        "This says the bad case is a real query/opening geometry problem, not only a label typo."
    ),
    "next_attack": (
        "Do not promote the post-tail layout. The next useful route should attack label-stable "
        "opening geometry directly or reduce verifier-facing openings before trying another "
        "fixed-column reorder."
    ),
}

VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused-post-tail docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-layout-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-layout-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-layout-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-layout-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused-post-tail-label-probe-a docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-a-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-a-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-a-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-a-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused-post-tail-label-probe-b docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-b-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-b-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-b-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-b-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-layout-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adjacent-label-probe-b-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-layout-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-a-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-post-tail-label-probe-b-2026-05.envelope.json > docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-post-tail-layout-accounting-2026-05.json",
    "python3 scripts/zkai_native_attention_mlp_rmsnorm_post_tail_layout_gate.py --write-json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-post-tail-layout-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-post-tail-layout-2026-05.tsv",
    "python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_post_tail_layout_gate",
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

VARIANT_KEYS = {
    "name",
    "evidence_relative_path",
    "proof_json_bytes",
    "typed_bytes",
    "typed_delta_vs_two_proof_frontier",
    "path_opening_bytes",
    "path_opening_delta_vs_canonical",
    "value_bytes",
    "value_delta_vs_canonical",
    "typed_groups",
    "record_stream_sha256",
    "label_probe",
    "layout_probe",
    "policy_group",
}


class PostTailLayoutGateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode(
            "utf-8"
        )
    except (TypeError, ValueError) as err:
        raise PostTailLayoutGateError(f"invalid JSON value: {err}") from err


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
        raise PostTailLayoutGateError(f"missing input artifact: {path}") from err
    if stat.S_ISLNK(st.st_mode):
        raise PostTailLayoutGateError(f"refusing to read through symlink: {path}")
    if not stat.S_ISREG(st.st_mode):
        raise PostTailLayoutGateError(f"input artifact is not a regular file: {path}")
    resolved = path.resolve()
    evidence_root = EVIDENCE_DIR.resolve()
    if evidence_root != resolved and evidence_root not in resolved.parents:
        raise PostTailLayoutGateError(f"input path outside evidence dir: {path}")
    return resolved


def read_input_bytes(path: pathlib.Path) -> bytes:
    target = normalize_input_path(path)
    if target.stat().st_size > MAX_INPUT_JSON_BYTES:
        raise PostTailLayoutGateError(f"input artifact too large: {path}")
    return target.read_bytes()


def json_from_bytes(raw: bytes, path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as err:
        raise PostTailLayoutGateError(f"invalid JSON in {path}: {err}") from err
    if not isinstance(value, dict):
        raise PostTailLayoutGateError(f"expected object JSON in {path}")
    return value


def _int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise PostTailLayoutGateError(f"{label} must be an integer")
    return value


def _str(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise PostTailLayoutGateError(f"{label} must be a string")
    return value


def grouped(row: dict[str, Any]) -> dict[str, int]:
    accounting = row.get("local_binary_accounting")
    if not isinstance(accounting, dict):
        raise PostTailLayoutGateError("row missing local binary accounting")
    groups = accounting.get("grouped_reconstruction")
    if not isinstance(groups, dict):
        raise PostTailLayoutGateError("row missing grouped reconstruction")
    expected = (
        "fixed_overhead",
        "fri_decommitments",
        "fri_samples",
        "oods_samples",
        "queries_values",
        "trace_decommitments",
    )
    if tuple(sorted(groups)) != tuple(sorted(expected)):
        raise PostTailLayoutGateError("unexpected grouped reconstruction keys")
    return {key: _int(groups[key], f"group {key}") for key in expected}


def path_opening_bytes(groups: dict[str, int]) -> int:
    return sum(groups[key] for key in PATH_OPENING_GROUPS)


def value_bytes(groups: dict[str, int]) -> int:
    return sum(groups[key] for key in VALUE_GROUPS)


def variant_from_row(name: str, row: dict[str, Any]) -> dict[str, Any]:
    expected = EXPECTED_VARIANTS[name]
    path = _str(row.get("evidence_relative_path"), f"{name}.path")
    if path != expected["path"]:
        raise PostTailLayoutGateError(f"{name} path drift: {path}")
    proof_json = _int(row.get("proof_json_size_bytes"), f"{name}.proof_json")
    accounting = row.get("local_binary_accounting")
    if not isinstance(accounting, dict):
        raise PostTailLayoutGateError(f"{name} local accounting missing")
    typed = _int(accounting.get("typed_size_estimate_bytes"), f"{name}.typed")
    groups = grouped(row)
    record_stream_sha256 = _str(accounting.get("record_stream_sha256"), f"{name}.record_stream_sha256")
    if proof_json != expected["proof_json"] or typed != expected["typed"] or groups != expected["groups"]:
        raise PostTailLayoutGateError(f"{name} metric drift")
    if record_stream_sha256 != expected["record_stream_sha256"]:
        raise PostTailLayoutGateError(f"{name} record stream digest drift")
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
        "policy_group": expected["policy_group"],
    }


def rows_by_expected_path(accounting: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = accounting.get("rows")
    if not isinstance(rows, list):
        raise PostTailLayoutGateError("accounting rows missing")
    by_path = {}
    for row in rows:
        if not isinstance(row, dict):
            raise PostTailLayoutGateError("accounting row must be object")
        path = _str(row.get("evidence_relative_path"), "row path")
        if path in by_path:
            raise PostTailLayoutGateError(f"duplicate accounting row path: {path}")
        by_path[path] = row
    expected_paths = {entry["path"] for entry in EXPECTED_VARIANTS.values()}
    if set(by_path) != expected_paths:
        raise PostTailLayoutGateError("accounting row inventory drift")
    return by_path


def build_payload(*, include_mutations: bool = True) -> dict[str, Any]:
    accounting_raw = read_input_bytes(ACCOUNTING_PATH)
    if hashlib.sha256(accounting_raw).hexdigest() != EXPECTED_ACCOUNTING_SHA256:
        raise PostTailLayoutGateError("post-tail accounting source digest drift")
    accounting = json_from_bytes(accounting_raw, ACCOUNTING_PATH)
    by_path = rows_by_expected_path(accounting)
    variants = {name: variant_from_row(name, by_path[entry["path"]]) for name, entry in EXPECTED_VARIANTS.items()}
    post_tail_entries = [
        variants["post_tail_layout"],
        variants["post_tail_label_probe_a"],
        variants["post_tail_label_probe_b"],
    ]
    post_tail = variants["post_tail_layout"]
    canonical = variants["rmsnorm_input_fused"]
    adjacent = variants["adjacent_layout"]
    adjacent_bad = variants["adjacent_bad_label"]
    worst = max(post_tail_entries, key=lambda entry: entry["typed_bytes"])
    best = min(post_tail_entries, key=lambda entry: entry["typed_bytes"])
    if post_tail["typed_bytes"] != adjacent_bad["typed_bytes"]:
        raise PostTailLayoutGateError("post-tail canonical no longer matches adjacent bad-label typed bytes")
    if worst["typed_bytes"] != POST_TAIL_WORST_LABEL_TYPED_BYTES or best["typed_bytes"] != POST_TAIL_BEST_LABEL_TYPED_BYTES:
        raise PostTailLayoutGateError("post-tail label span drift")
    payload = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "parent_issue": PARENT_ISSUE,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_accounting_path": str(ACCOUNTING_PATH.relative_to(ROOT)),
        "source_accounting_sha256": EXPECTED_ACCOUNTING_SHA256,
        "two_proof_frontier_typed_bytes": TWO_PROOF_FRONTIER_TYPED_BYTES,
        "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
        "compact_selector_typed_bytes": COMPACT_SELECTOR_TYPED_BYTES,
        "canonical_rmsnorm_input_fused_typed_bytes": CANONICAL_RMSNORM_TYPED_BYTES,
        "adjacent_canonical_typed_bytes": ADJACENT_CANONICAL_TYPED_BYTES,
        "adjacent_bad_label_typed_bytes": ADJACENT_BAD_LABEL_TYPED_BYTES,
        "post_tail_canonical_typed_bytes": post_tail["typed_bytes"],
        "post_tail_delta_vs_two_proof_frontier_typed_bytes": post_tail["typed_bytes"] - TWO_PROOF_FRONTIER_TYPED_BYTES,
        "post_tail_penalty_vs_adjacent_canonical_typed_bytes": post_tail["typed_bytes"] - adjacent["typed_bytes"],
        "post_tail_penalty_vs_canonical_rmsnorm_typed_bytes": post_tail["typed_bytes"] - canonical["typed_bytes"],
        "post_tail_best_label_typed_bytes": best["typed_bytes"],
        "post_tail_worst_label_typed_bytes": worst["typed_bytes"],
        "post_tail_label_span_typed_bytes": worst["typed_bytes"] - best["typed_bytes"],
        "post_tail_matches_adjacent_bad_label_record_stream": post_tail["record_stream_sha256"] == adjacent_bad["record_stream_sha256"],
        "variants": variants,
        "interpretation": dict(INTERPRETATION),
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
        "parent_issue",
        "claim_boundary",
        "source_accounting_path",
        "source_accounting_sha256",
        "two_proof_frontier_typed_bytes",
        "nanozk_reported_d128_block_proof_bytes",
        "compact_selector_typed_bytes",
        "canonical_rmsnorm_input_fused_typed_bytes",
        "adjacent_canonical_typed_bytes",
        "adjacent_bad_label_typed_bytes",
        "post_tail_canonical_typed_bytes",
        "post_tail_delta_vs_two_proof_frontier_typed_bytes",
        "post_tail_penalty_vs_adjacent_canonical_typed_bytes",
        "post_tail_penalty_vs_canonical_rmsnorm_typed_bytes",
        "post_tail_best_label_typed_bytes",
        "post_tail_worst_label_typed_bytes",
        "post_tail_label_span_typed_bytes",
        "post_tail_matches_adjacent_bad_label_record_stream",
        "variants",
        "interpretation",
        "non_claims",
        "validation_commands",
        "mutation_results",
        "payload_commitment",
    }
    if set(payload) != required:
        raise PostTailLayoutGateError("payload key drift")
    if payload["schema"] != SCHEMA or payload["decision"] != DECISION or payload["result"] != RESULT:
        raise PostTailLayoutGateError("payload metadata drift")
    if payload["issue"] != ISSUE or payload["parent_issue"] != PARENT_ISSUE or payload["claim_boundary"] != CLAIM_BOUNDARY:
        raise PostTailLayoutGateError("claim boundary drift")
    if payload["source_accounting_path"] != str(ACCOUNTING_PATH.relative_to(ROOT)):
        raise PostTailLayoutGateError("source accounting path drift")
    if payload["source_accounting_sha256"] != EXPECTED_ACCOUNTING_SHA256:
        raise PostTailLayoutGateError("source digest drift")
    if payload["two_proof_frontier_typed_bytes"] != TWO_PROOF_FRONTIER_TYPED_BYTES:
        raise PostTailLayoutGateError("frontier drift")
    if payload["nanozk_reported_d128_block_proof_bytes"] != NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES:
        raise PostTailLayoutGateError("NANOZK reference drift")
    variants = payload["variants"]
    if not isinstance(variants, dict) or set(variants) != set(EXPECTED_VARIANTS):
        raise PostTailLayoutGateError("variant inventory drift")
    for name, expected in EXPECTED_VARIANTS.items():
        variant = variants[name]
        if not isinstance(variant, dict):
            raise PostTailLayoutGateError(f"{name} variant is not object")
        if set(variant) != VARIANT_KEYS:
            raise PostTailLayoutGateError(f"{name} variant key drift")
        if variant["name"] != name or variant["evidence_relative_path"] != expected["path"]:
            raise PostTailLayoutGateError(f"{name} variant provenance drift")
        if variant["typed_bytes"] != expected["typed"] or variant["proof_json_bytes"] != expected["proof_json"]:
            raise PostTailLayoutGateError(f"{name} variant metric drift")
        if variant["typed_groups"] != expected["groups"]:
            raise PostTailLayoutGateError(f"{name} group drift")
        if variant["record_stream_sha256"] != expected["record_stream_sha256"]:
            raise PostTailLayoutGateError(f"{name} record stream digest drift")
        if variant["typed_delta_vs_two_proof_frontier"] != expected["typed"] - TWO_PROOF_FRONTIER_TYPED_BYTES:
            raise PostTailLayoutGateError(f"{name} frontier delta drift")
        if variant["path_opening_bytes"] != path_opening_bytes(expected["groups"]):
            raise PostTailLayoutGateError(f"{name} path-opening byte drift")
        if variant["path_opening_delta_vs_canonical"] != path_opening_bytes(expected["groups"]) - path_opening_bytes(
            EXPECTED_VARIANTS["rmsnorm_input_fused"]["groups"]
        ):
            raise PostTailLayoutGateError(f"{name} path-opening delta drift")
        if variant["value_bytes"] != value_bytes(expected["groups"]):
            raise PostTailLayoutGateError(f"{name} value byte drift")
        if variant["value_delta_vs_canonical"] != value_bytes(expected["groups"]) - value_bytes(
            EXPECTED_VARIANTS["rmsnorm_input_fused"]["groups"]
        ):
            raise PostTailLayoutGateError(f"{name} value delta drift")
        if variant["label_probe"] is not expected["label_probe"] or variant["layout_probe"] is not expected["layout_probe"]:
            raise PostTailLayoutGateError(f"{name} probe flag drift")
        if variant["policy_group"] != expected["policy_group"]:
            raise PostTailLayoutGateError(f"{name} policy group drift")
    post_tail = variants["post_tail_layout"]
    canonical = variants["rmsnorm_input_fused"]
    adjacent = variants["adjacent_layout"]
    adjacent_bad = variants["adjacent_bad_label"]
    post_tail_entries = [variants["post_tail_layout"], variants["post_tail_label_probe_a"], variants["post_tail_label_probe_b"]]
    worst = max(post_tail_entries, key=lambda entry: entry["typed_bytes"])
    best = min(post_tail_entries, key=lambda entry: entry["typed_bytes"])
    summary_checks = (
        ("compact_selector_typed_bytes", variants["compact_selector"]["typed_bytes"]),
        ("canonical_rmsnorm_input_fused_typed_bytes", canonical["typed_bytes"]),
        ("adjacent_canonical_typed_bytes", adjacent["typed_bytes"]),
        ("adjacent_bad_label_typed_bytes", adjacent_bad["typed_bytes"]),
        ("post_tail_canonical_typed_bytes", post_tail["typed_bytes"]),
        ("post_tail_best_label_typed_bytes", best["typed_bytes"]),
        ("post_tail_worst_label_typed_bytes", worst["typed_bytes"]),
    )
    for key, expected in summary_checks:
        if payload[key] != expected:
            raise PostTailLayoutGateError(f"{key} summary drift")
    if payload["post_tail_delta_vs_two_proof_frontier_typed_bytes"] != post_tail["typed_bytes"] - TWO_PROOF_FRONTIER_TYPED_BYTES:
        raise PostTailLayoutGateError("post-tail frontier delta drift")
    if payload["post_tail_penalty_vs_adjacent_canonical_typed_bytes"] != post_tail["typed_bytes"] - adjacent["typed_bytes"]:
        raise PostTailLayoutGateError("post-tail adjacent penalty drift")
    if payload["post_tail_penalty_vs_canonical_rmsnorm_typed_bytes"] != post_tail["typed_bytes"] - canonical["typed_bytes"]:
        raise PostTailLayoutGateError("post-tail canonical penalty drift")
    if payload["post_tail_label_span_typed_bytes"] != worst["typed_bytes"] - best["typed_bytes"]:
        raise PostTailLayoutGateError("post-tail label span drift")
    if payload["post_tail_delta_vs_two_proof_frontier_typed_bytes"] <= 0:
        raise PostTailLayoutGateError("frontier overclaim: post-tail layout does not beat frontier")
    if payload["post_tail_matches_adjacent_bad_label_record_stream"] is not True:
        raise PostTailLayoutGateError("post-tail no longer records adjacent bad-label stream match")
    if post_tail["typed_bytes"] != adjacent_bad["typed_bytes"]:
        raise PostTailLayoutGateError("post-tail typed bytes no longer match adjacent bad-label")
    if payload["interpretation"] != INTERPRETATION:
        raise PostTailLayoutGateError("interpretation drift")
    non_claims = payload["non_claims"]
    if not isinstance(non_claims, list) or any(not isinstance(item, str) for item in non_claims):
        raise PostTailLayoutGateError("non-claims must be a list of strings")
    if tuple(non_claims) != NON_CLAIMS:
        raise PostTailLayoutGateError("non-claims drift")
    if tuple(payload["validation_commands"]) != VALIDATION_COMMANDS:
        raise PostTailLayoutGateError("validation command drift")
    if payload["payload_commitment"] != payload_commitment(payload):
        raise PostTailLayoutGateError("payload commitment drift")
    if require_mutations:
        validate_mutation_results(payload["mutation_results"])


MUTATIONS = (
    ("frontier_overclaim", lambda p: p.__setitem__("decision", "GO_FRONTIER_PROMOTION")),
    ("result_overclaim", lambda p: p.__setitem__("result", "POST_TAIL_LAYOUT_BEATS_FRONTIER")),
    ("post_tail_canonical_erased", lambda p: p.__setitem__("post_tail_canonical_typed_bytes", 40_699)),
    ("post_tail_delta_erased", lambda p: p.__setitem__("post_tail_delta_vs_two_proof_frontier_typed_bytes", -1)),
    ("post_tail_penalty_erased", lambda p: p.__setitem__("post_tail_penalty_vs_adjacent_canonical_typed_bytes", 0)),
    ("label_span_drift", lambda p: p.__setitem__("post_tail_label_span_typed_bytes", 1)),
    ("record_stream_match_erased", lambda p: p.__setitem__("post_tail_matches_adjacent_bad_label_record_stream", False)),
    ("nanozk_overclaim", lambda p: p.__setitem__("nanozk_reported_d128_block_proof_bytes", 42_724)),
    ("source_digest_drift", lambda p: p.__setitem__("source_accounting_sha256", "0" * 64)),
    ("non_claims_erased", lambda p: p.__setitem__("non_claims", [])),
    ("validation_commands_erased", lambda p: p.__setitem__("validation_commands", [])),
    ("variant_path_drift", lambda p: p["variants"]["post_tail_layout"].__setitem__("evidence_relative_path", "other.json")),
    ("interpretation_drift", lambda p: p.__setitem__("interpretation", {"human_read": "frontier win"})),
    ("variant_metric_drift", lambda p: p["variants"]["post_tail_layout"].__setitem__("typed_bytes", 40_700)),
    ("group_drift", lambda p: p["variants"]["post_tail_layout"]["typed_groups"].__setitem__("fri_decommitments", 0)),
    ("policy_group_drift", lambda p: p["variants"]["post_tail_layout"].__setitem__("policy_group", "reference")),
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
        except PostTailLayoutGateError as err:
            results.append({"name": name, "rejected": True, "reason": str(err)})
        else:
            results.append({"name": name, "rejected": False, "reason": ""})
    return results


def validate_mutation_results(results: Any) -> None:
    if not isinstance(results, list):
        raise PostTailLayoutGateError("mutation results must be a list")
    if len(results) != len(MUTATIONS):
        raise PostTailLayoutGateError("mutation inventory length drift")
    for entry in results:
        if not isinstance(entry, dict):
            raise PostTailLayoutGateError("mutation entry must be an object")
    names = [entry.get("name") for entry in results]
    if names != [name for name, _ in MUTATIONS]:
        raise PostTailLayoutGateError("mutation inventory drift")
    for entry in results:
        if set(entry) != {"name", "rejected", "reason"}:
            raise PostTailLayoutGateError("mutation entry key drift")
        if entry["rejected"] is not True or not entry["reason"]:
            raise PostTailLayoutGateError(f"mutation did not reject: {entry['name']}")


def tsv_text(payload: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for name in EXPECTED_VARIANTS:
        variant = payload["variants"][name]
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
                "policy_status": "no_go_post_tail" if variant["policy_group"] == "post_tail" else variant["policy_group"],
            }
        )
    return output.getvalue()


def normalize_output_path(path: pathlib.Path) -> pathlib.Path:
    try:
        original_st = os.lstat(path)
    except FileNotFoundError:
        pass
    else:
        if stat.S_ISLNK(original_st.st_mode):
            raise PostTailLayoutGateError(f"refusing to write through symlink: {path}")
        if not stat.S_ISREG(original_st.st_mode):
            raise PostTailLayoutGateError(f"output path is not a regular file: {path}")
    resolved = path.resolve()
    evidence_root = EVIDENCE_DIR.resolve()
    if evidence_root != resolved and evidence_root not in resolved.parents:
        raise PostTailLayoutGateError(f"output path outside evidence dir: {path}")
    try:
        st = os.lstat(resolved)
    except FileNotFoundError:
        return resolved
    if stat.S_ISLNK(st.st_mode):
        raise PostTailLayoutGateError(f"refusing to write through symlink: {path}")
    return resolved


def write_atomic(path: pathlib.Path, data: bytes) -> None:
    target = normalize_output_path(path)
    suffix = target.suffix
    if suffix not in {".json", ".tsv"}:
        raise PostTailLayoutGateError(f"unsupported output suffix: {target}")
    tmp = target.with_name(f".{target.name}.{secrets.token_hex(8)}.tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, target)
    except Exception:
        try:
            tmp.unlink()
        except OSError:
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
                "post_tail_canonical_typed_bytes": payload["post_tail_canonical_typed_bytes"],
                "post_tail_delta_vs_two_proof_frontier_typed_bytes": payload[
                    "post_tail_delta_vs_two_proof_frontier_typed_bytes"
                ],
                "post_tail_penalty_vs_adjacent_canonical_typed_bytes": payload[
                    "post_tail_penalty_vs_adjacent_canonical_typed_bytes"
                ],
                "post_tail_label_span_typed_bytes": payload["post_tail_label_span_typed_bytes"],
                "mutation_count": len(payload["mutation_results"]),
                "mutations_rejected": sum(1 for entry in payload["mutation_results"] if entry["rejected"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
