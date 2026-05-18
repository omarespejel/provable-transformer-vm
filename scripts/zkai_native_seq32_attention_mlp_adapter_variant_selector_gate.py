#!/usr/bin/env python3.10
"""Gate seq32+d128 adapter-layout variants against the current native single proof."""

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
    raise RuntimeError("zkai_native_seq32_attention_mlp_adapter_variant_selector_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"

ACCOUNTING = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-adapter-variant-selector-accounting-2026-05.json"
JSON_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-adapter-variant-selector-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-adapter-variant-selector-2026-05.tsv"

SCHEMA = "zkai-native-seq32-attention-mlp-adapter-variant-selector-gate-v1"
DECISION = "NO_GO_ADAPTER_VARIANTS_DO_NOT_BEAT_CURRENT_SEQ32_NATIVE_SINGLE_PROOF"
RESULT = "BEST_ZERO_BASE_ADJACENT_VARIANT_MISSES_CURRENT_CHAMPION_BY_88_TYPED_BYTES"
ISSUE_HINT = "native-seq32-attention-mlp-adapter-variant-selector"
PAYLOAD_DOMAIN = "ptvm:zkai:native-seq32-attention-mlp-adapter-variant-selector-gate:v1"
CLAIM_BOUNDARY = (
    "SEQ32_D128_ADAPTER_LAYOUT_VARIANTS_ARE_CHECKED_AGAINST_THE_EXISTING_NATIVE_SINGLE_PROOF;"
    "CURRENT_DUPLICATE_BASE_PROOF_REMAINS_THE_TYPED_SIZE_CHAMPION;"
    "NOT_A_NEW_PROOF_SIZE_WIN_NOT_A_NANOZK_WIN_NOT_A_FULL_TRANSFORMER_BLOCK"
)

FRONTIER_TYPED_BYTES = 47_188
CURRENT_CHAMPION_PATH = "zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json"
CURRENT_CHAMPION_TYPED_BYTES = 42_068
CURRENT_CHAMPION_JSON_BYTES = 121_996
CURRENT_CHAMPION_ADAPTER_CELLS = 1_536
BEST_VARIANT_PATH = "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json"
BEST_VARIANT_TYPED_BYTES = 42_156
BEST_VARIANT_JSON_BYTES = 122_688
BEST_VARIANT_GAP_TYPED_BYTES = 88
BEST_VARIANT_JSON_GAP_BYTES = 692
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900

EXPECTED_ROWS = (
    {
        "variant_id": "current_duplicate_base",
        "path": CURRENT_CHAMPION_PATH,
        "adapter_mode": "duplicate_base_preprocessed_v1",
        "adapter_trace_cells": CURRENT_CHAMPION_ADAPTER_CELLS,
        "typed_bytes": CURRENT_CHAMPION_TYPED_BYTES,
        "proof_json_bytes": CURRENT_CHAMPION_JSON_BYTES,
        "typed_delta_vs_champion": 0,
        "proof_json_delta_vs_champion": 0,
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
        "variant_id": "compact_base",
        "path": "zkai-native-seq32-attention-mlp-compact-adapter-2026-05.envelope.json",
        "adapter_mode": "compact_base_referenced_fixed_v1",
        "adapter_trace_cells": 1_024,
        "typed_bytes": 42_548,
        "proof_json_bytes": 123_801,
        "typed_delta_vs_champion": 480,
        "proof_json_delta_vs_champion": 1_805,
        "grouped": {
            "fixed_overhead": 48,
            "fri_decommitments": 13_696,
            "fri_samples": 832,
            "oods_samples": 12_208,
            "queries_values": 9_108,
            "trace_decommitments": 6_656,
        },
    },
    {
        "variant_id": "output_anchor",
        "path": "zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.envelope.json",
        "adapter_mode": "preprocessed_output_anchor_fixed_v1",
        "adapter_trace_cells": 128,
        "typed_bytes": 42_976,
        "proof_json_bytes": 125_345,
        "typed_delta_vs_champion": 908,
        "proof_json_delta_vs_champion": 3_349,
        "grouped": {
            "fixed_overhead": 48,
            "fri_decommitments": 14_176,
            "fri_samples": 848,
            "oods_samples": 12_096,
            "queries_values": 9_024,
            "trace_decommitments": 6_784,
        },
    },
    {
        "variant_id": "rmsnorm_input_fused",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_fixed_v1",
        "adapter_trace_cells": 0,
        "typed_bytes": 42_780,
        "proof_json_bytes": 124_840,
        "typed_delta_vs_champion": 712,
        "proof_json_delta_vs_champion": 2_844,
        "grouped": {
            "fixed_overhead": 48,
            "fri_decommitments": 14_176,
            "fri_samples": 848,
            "oods_samples": 11_984,
            "queries_values": 8_940,
            "trace_decommitments": 6_784,
        },
    },
    {
        "variant_id": "rmsnorm_adjacent_layout",
        "path": BEST_VARIANT_PATH,
        "adapter_mode": "rmsnorm_input_fused_adjacent_fixed_v1",
        "adapter_trace_cells": 0,
        "typed_bytes": BEST_VARIANT_TYPED_BYTES,
        "proof_json_bytes": BEST_VARIANT_JSON_BYTES,
        "typed_delta_vs_champion": BEST_VARIANT_GAP_TYPED_BYTES,
        "proof_json_delta_vs_champion": BEST_VARIANT_JSON_GAP_BYTES,
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
        "variant_id": "rmsnorm_post_tail_layout",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_post_tail_fixed_v1",
        "adapter_trace_cells": 0,
        "typed_bytes": 42_780,
        "proof_json_bytes": 124_774,
        "typed_delta_vs_champion": 712,
        "proof_json_delta_vs_champion": 2_778,
        "grouped": {
            "fixed_overhead": 48,
            "fri_decommitments": 14_176,
            "fri_samples": 848,
            "oods_samples": 11_984,
            "queries_values": 8_940,
            "trace_decommitments": 6_784,
        },
    },
)

EXPECTED_VARIANT_IDS = tuple(row["variant_id"] for row in EXPECTED_ROWS)

NON_CLAIMS = (
    "not a new proof-size frontier",
    "not a NANOZK proof-size win",
    "not a full transformer block proof",
    "not exact real-valued Softmax",
    "not full autoregressive inference",
    "not timing evidence",
    "not production-ready zkML",
)

VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-compact docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-compact-adapter-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-compact-adapter-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-compact-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-compact-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-preprocessed-anchor docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-post-tail docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-compact-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.envelope.json > docs/engineering/evidence/zkai-native-seq32-attention-mlp-adapter-variant-selector-accounting-2026-05.json",
    "python3.10 scripts/zkai_native_seq32_attention_mlp_adapter_variant_selector_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-adapter-variant-selector-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-adapter-variant-selector-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_adapter_variant_selector_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_adapter_variant_selector_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_adapter_variant_selector_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend native_seq32_attention_mlp_single_proof --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

SOURCE_ARTIFACT_SPECS = (("variant_accounting", ACCOUNTING),) + tuple(
    (row["variant_id"] + "_envelope", EVIDENCE_DIR / row["path"]) for row in EXPECTED_ROWS
)
EXPECTED_SOURCE_ARTIFACTS = tuple(
    (artifact_id, str(path.relative_to(ROOT))) for artifact_id, path in SOURCE_ARTIFACT_SPECS
)

MUTATION_NAMES = (
    "best_variant_promoted_to_champion",
    "best_variant_gap_erased",
    "current_champion_typed_drift",
    "variant_typed_metric_drift",
    "variant_json_metric_drift",
    "variant_inventory_drift",
    "claim_boundary_overclaim",
    "removed_non_claim",
    "source_artifact_digest_drift",
    "source_artifact_path_traversal",
    "validation_command_drift",
    "payload_commitment_drift",
)

TSV_COLUMNS = (
    "decision",
    "result",
    "current_champion_typed_bytes",
    "best_variant_id",
    "best_variant_typed_bytes",
    "best_variant_gap_typed_bytes",
    "best_variant_json_bytes",
    "best_variant_gap_json_bytes",
    "frontier_typed_bytes",
    "current_champion_saving_vs_frontier_bytes",
    "proof_size_comparable_external_rows",
)

DETERMINISTIC_TEMP_ATTEMPTS = 16


class NativeSeq32AdapterVariantSelectorGateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode(
            "utf-8"
        )
    except (TypeError, ValueError) as err:
        raise NativeSeq32AdapterVariantSelectorGateError(f"invalid JSON value: {err}") from err


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return "blake2b-256:" + digest.hexdigest()


def require_output_path(path: pathlib.Path) -> pathlib.Path:
    resolved = path.resolve()
    evidence = EVIDENCE_DIR.resolve()
    try:
        resolved.relative_to(evidence)
    except ValueError as err:
        raise NativeSeq32AdapterVariantSelectorGateError(
            f"output path escapes evidence dir: {resolved}"
        ) from err
    return resolved


def reject_symlinked_ancestors(path: pathlib.Path) -> None:
    for ancestor in path.resolve().parents:
        if ancestor == ancestor.parent:
            break
        try:
            if ancestor.is_symlink():
                raise NativeSeq32AdapterVariantSelectorGateError(f"refusing symlinked parent: {ancestor}")
        except OSError as err:
            raise NativeSeq32AdapterVariantSelectorGateError(f"failed to inspect parent {ancestor}: {err}") from err


def read_repo_file(path: pathlib.Path, label: str) -> bytes:
    resolved = path.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as err:
        raise NativeSeq32AdapterVariantSelectorGateError(f"{label} escapes repo: {path}") from err
    reject_symlinked_ancestors(resolved)
    try:
        metadata = os.lstat(resolved)
    except FileNotFoundError as err:
        raise NativeSeq32AdapterVariantSelectorGateError(f"missing {label}: {path}") from err
    if stat.S_ISLNK(metadata.st_mode):
        raise NativeSeq32AdapterVariantSelectorGateError(f"{label} is a symlink: {path}")
    if not stat.S_ISREG(metadata.st_mode):
        raise NativeSeq32AdapterVariantSelectorGateError(f"{label} is not a regular file: {path}")
    return resolved.read_bytes()


def read_json_file(path: pathlib.Path, label: str) -> Any:
    try:
        return json.loads(read_repo_file(path, label))
    except json.JSONDecodeError as err:
        raise NativeSeq32AdapterVariantSelectorGateError(f"invalid {label} JSON: {err}") from err


def _dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise NativeSeq32AdapterVariantSelectorGateError(f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise NativeSeq32AdapterVariantSelectorGateError(f"{label} must be a list")
    return value


def _int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise NativeSeq32AdapterVariantSelectorGateError(f"{label} must be an integer")
    return value


def _str(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise NativeSeq32AdapterVariantSelectorGateError(f"{label} must be a string")
    return value


def artifact_record(artifact_id: str, path: pathlib.Path) -> dict[str, Any]:
    raw = read_repo_file(path, artifact_id)
    return {
        "id": artifact_id,
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256(raw),
        "size_bytes": len(raw),
    }


def source_artifacts() -> list[dict[str, Any]]:
    return [artifact_record(artifact_id, path) for artifact_id, path in SOURCE_ARTIFACT_SPECS]


def load_variant_rows() -> list[dict[str, Any]]:
    accounting = _dict(read_json_file(ACCOUNTING, "variant accounting"), "variant accounting")
    rows = _list(accounting.get("rows"), "accounting rows")
    if len(rows) != len(EXPECTED_ROWS):
        raise NativeSeq32AdapterVariantSelectorGateError("variant inventory drift")
    parsed = []
    for expected, row in zip(EXPECTED_ROWS, rows):
        path = _str(row.get("evidence_relative_path"), "evidence path")
        if path != expected["path"]:
            raise NativeSeq32AdapterVariantSelectorGateError("variant path drift")
        envelope = _dict(read_json_file(EVIDENCE_DIR / path, f"{path} envelope"), "envelope")
        envelope_input = _dict(envelope.get("input"), "envelope input")
        proof = _list(envelope.get("proof"), "envelope proof")
        try:
            proof_bytes = bytes(proof)
        except (TypeError, ValueError) as err:
            raise NativeSeq32AdapterVariantSelectorGateError("envelope proof must contain bytes") from err
        accounting_row = _dict(row.get("local_binary_accounting"), "local binary accounting")
        grouped = _dict(accounting_row.get("grouped_reconstruction"), "grouped reconstruction")
        actual = {
            "variant_id": expected["variant_id"],
            "path": path,
            "adapter_mode": _str(envelope_input.get("adapter_mode"), "adapter mode"),
            "adapter_trace_cells": _int(envelope_input.get("adapter_trace_cells"), "adapter cells"),
            "typed_bytes": _int(accounting_row.get("typed_size_estimate_bytes"), "typed bytes"),
            "proof_json_bytes": _int(row.get("proof_json_size_bytes"), "proof JSON bytes"),
            "typed_delta_vs_champion": _int(accounting_row.get("typed_size_estimate_bytes"), "typed bytes")
            - CURRENT_CHAMPION_TYPED_BYTES,
            "proof_json_delta_vs_champion": _int(row.get("proof_json_size_bytes"), "proof JSON bytes")
            - CURRENT_CHAMPION_JSON_BYTES,
            "proof_sha256": _str(row.get("proof_sha256"), "proof sha256"),
            "envelope_sha256": _str(row.get("envelope_sha256"), "envelope sha256"),
            "proof_backend_version": _str(
                _dict(row.get("envelope_metadata"), "envelope metadata").get("proof_backend_version"),
                "proof backend version",
            ),
            "proof_len_bytes": len(proof_bytes),
            "grouped": {key: _int(grouped.get(key), f"{expected['variant_id']} {key}") for key in expected["grouped"]},
        }
        if actual["proof_len_bytes"] != actual["proof_json_bytes"]:
            raise NativeSeq32AdapterVariantSelectorGateError("proof JSON byte drift")
        comparable = {key: actual[key] for key in expected if key != "grouped"}
        if comparable != {key: expected[key] for key in expected if key != "grouped"}:
            raise NativeSeq32AdapterVariantSelectorGateError("variant summary drift")
        if actual["grouped"] != expected["grouped"]:
            raise NativeSeq32AdapterVariantSelectorGateError("variant grouped accounting drift")
        parsed.append(actual)
    return parsed


def build_payload() -> dict[str, Any]:
    variants = load_variant_rows()
    champion = variants[0]
    if champion["path"] != CURRENT_CHAMPION_PATH or champion["typed_bytes"] != CURRENT_CHAMPION_TYPED_BYTES:
        raise NativeSeq32AdapterVariantSelectorGateError("current champion drift")
    best_variant = min(variants[1:], key=lambda row: row["typed_bytes"])
    if best_variant["path"] != BEST_VARIANT_PATH:
        raise NativeSeq32AdapterVariantSelectorGateError("best variant drift")

    champion_opening = champion["grouped"]["fri_decommitments"] + champion["grouped"]["trace_decommitments"]
    best_opening = best_variant["grouped"]["fri_decommitments"] + best_variant["grouped"]["trace_decommitments"]
    champion_queries = champion["grouped"]["oods_samples"] + champion["grouped"]["queries_values"]
    best_queries = best_variant["grouped"]["oods_samples"] + best_variant["grouped"]["queries_values"]

    summary = {
        "current_champion_id": champion["variant_id"],
        "current_champion_adapter_mode": champion["adapter_mode"],
        "current_champion_adapter_trace_cells": champion["adapter_trace_cells"],
        "current_champion_typed_bytes": champion["typed_bytes"],
        "current_champion_proof_json_bytes": champion["proof_json_bytes"],
        "best_variant_id": best_variant["variant_id"],
        "best_variant_adapter_mode": best_variant["adapter_mode"],
        "best_variant_adapter_trace_cells": best_variant["adapter_trace_cells"],
        "best_variant_typed_bytes": best_variant["typed_bytes"],
        "best_variant_json_bytes": best_variant["proof_json_bytes"],
        "best_variant_gap_typed_bytes": best_variant["typed_delta_vs_champion"],
        "best_variant_gap_json_bytes": best_variant["proof_json_delta_vs_champion"],
        "frontier_typed_bytes": FRONTIER_TYPED_BYTES,
        "current_champion_saving_vs_frontier_bytes": FRONTIER_TYPED_BYTES - champion["typed_bytes"],
        "current_champion_saving_vs_frontier_share": f"{(FRONTIER_TYPED_BYTES - champion['typed_bytes']) / FRONTIER_TYPED_BYTES:.6f}",
        "variant_count": len(variants) - 1,
        "zero_base_variant_count": sum(1 for row in variants[1:] if row["adapter_trace_cells"] == 0),
        "best_variant_opening_overhang_bytes": best_opening - champion_opening,
        "best_variant_oods_queries_saving_bytes": champion_queries - best_queries,
        "best_variant_fri_sample_overhang_bytes": best_variant["grouped"]["fri_samples"] - champion["grouped"]["fri_samples"],
        "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
        "current_champion_typed_ratio_to_nanozk_reported_row": f"{champion['typed_bytes'] / NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES:.6f}",
        "proof_size_comparable_external_rows": 0,
    }
    interpretation = {
        "human_read": (
            "Five adapter-layout variants verified for the same seq32+d128 native proof surface, but none "
            "beat the existing duplicate-base proof on typed bytes."
        ),
        "interesting_signal": (
            "The best zero-base variant removes the adapter base trace entirely yet lands at 42,156 typed "
            "bytes, only 88 bytes heavier than the current 42,068-byte champion."
        ),
        "mechanism_read": (
            "Adapter cell count is not the active bottleneck: the best variant saves 504 bytes in OODS plus "
            "queried values but pays 576 extra bytes in FRI/trace decommitment material."
        ),
        "next_experiment": (
            "Attack query/opening stability for the adjacent zero-base layout, not additional base-cell removal."
        ),
    }
    payload = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue_hint": ISSUE_HINT,
        "claim_boundary": CLAIM_BOUNDARY,
        "summary": summary,
        "variants": variants,
        "interpretation": interpretation,
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
        item["mutation_result"] = {
            "all_mutations_rejected": True,
            "mutations_rejected": len(MUTATION_NAMES),
            "mutation_names": list(MUTATION_NAMES),
            "cases": [{"name": n, "rejected": True, "error": "placeholder"} for n in MUTATION_NAMES],
        }
        if name != "payload_commitment_drift":
            item["payload_commitment"] = payload_commitment(item)
        try:
            validate_payload(item)
        except NativeSeq32AdapterVariantSelectorGateError as err:
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
        ("best_variant_promoted_to_champion", lambda item: item["summary"].update({"current_champion_id": "rmsnorm_adjacent_layout"})),
        ("best_variant_gap_erased", lambda item: item["summary"].update({"best_variant_gap_typed_bytes": 0})),
        ("current_champion_typed_drift", lambda item: item["summary"].update({"current_champion_typed_bytes": 42_156})),
        ("variant_typed_metric_drift", lambda item: item["variants"][4].update({"typed_bytes": 42_000})),
        ("variant_json_metric_drift", lambda item: item["variants"][4].update({"proof_json_bytes": 121_000})),
        ("variant_inventory_drift", lambda item: item["variants"].pop()),
        ("claim_boundary_overclaim", lambda item: item.update({"claim_boundary": item["claim_boundary"] + ";NANOZK_WIN"})),
        ("removed_non_claim", lambda item: item["non_claims"].remove("not a new proof-size frontier")),
        ("source_artifact_digest_drift", lambda item: item["source_artifacts"][0].update({"sha256": "0" * 64})),
        ("source_artifact_path_traversal", lambda item: item["source_artifacts"][0].update({"path": "../outside.json"})),
        ("validation_command_drift", lambda item: item["validation_commands"].append("echo untracked validation")),
        ("payload_commitment_drift", lambda item: item.update({"payload_commitment": "blake2b-256:" + "0" * 64})),
    )


def validate_payload(payload: dict[str, Any]) -> None:
    expected_top = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue_hint": ISSUE_HINT,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    for key, expected in expected_top.items():
        if payload.get(key) != expected:
            raise NativeSeq32AdapterVariantSelectorGateError(f"{key} drift")
    if payload.get("non_claims") != list(NON_CLAIMS):
        raise NativeSeq32AdapterVariantSelectorGateError("non_claims drift")
    if payload.get("validation_commands") != list(VALIDATION_COMMANDS):
        raise NativeSeq32AdapterVariantSelectorGateError("validation command drift")
    validate_summary(_dict(payload.get("summary"), "summary"))
    validate_variants(_list(payload.get("variants"), "variants"))
    validate_source_artifacts(_list(payload.get("source_artifacts"), "source artifacts"))
    if "mutation_result" in payload:
        validate_mutation_result(_dict(payload["mutation_result"], "mutation result"))
    expected_commitment = payload_commitment(payload)
    if payload.get("payload_commitment") != expected_commitment:
        raise NativeSeq32AdapterVariantSelectorGateError("payload commitment drift")


def validate_summary(summary: dict[str, Any]) -> None:
    expected = {
        "current_champion_id": "current_duplicate_base",
        "current_champion_adapter_mode": "duplicate_base_preprocessed_v1",
        "current_champion_adapter_trace_cells": CURRENT_CHAMPION_ADAPTER_CELLS,
        "current_champion_typed_bytes": CURRENT_CHAMPION_TYPED_BYTES,
        "current_champion_proof_json_bytes": CURRENT_CHAMPION_JSON_BYTES,
        "best_variant_id": "rmsnorm_adjacent_layout",
        "best_variant_adapter_mode": "rmsnorm_input_fused_adjacent_fixed_v1",
        "best_variant_adapter_trace_cells": 0,
        "best_variant_typed_bytes": BEST_VARIANT_TYPED_BYTES,
        "best_variant_json_bytes": BEST_VARIANT_JSON_BYTES,
        "best_variant_gap_typed_bytes": BEST_VARIANT_GAP_TYPED_BYTES,
        "best_variant_gap_json_bytes": BEST_VARIANT_JSON_GAP_BYTES,
        "frontier_typed_bytes": FRONTIER_TYPED_BYTES,
        "current_champion_saving_vs_frontier_bytes": 5_120,
        "current_champion_saving_vs_frontier_share": "0.108502",
        "variant_count": 5,
        "zero_base_variant_count": 3,
        "best_variant_opening_overhang_bytes": 576,
        "best_variant_oods_queries_saving_bytes": 504,
        "best_variant_fri_sample_overhang_bytes": 16,
        "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
        "current_champion_typed_ratio_to_nanozk_reported_row": "6.096812",
        "proof_size_comparable_external_rows": 0,
    }
    if summary != expected:
        raise NativeSeq32AdapterVariantSelectorGateError("summary drift")


def validate_variants(variants: list[Any]) -> None:
    if len(variants) != len(EXPECTED_ROWS):
        raise NativeSeq32AdapterVariantSelectorGateError("variant inventory drift")
    for actual, expected in zip(variants, EXPECTED_ROWS):
        row = _dict(actual, "variant row")
        for key in (
            "variant_id",
            "path",
            "adapter_mode",
            "adapter_trace_cells",
            "typed_bytes",
            "proof_json_bytes",
            "typed_delta_vs_champion",
            "proof_json_delta_vs_champion",
        ):
            if row.get(key) != expected[key]:
                raise NativeSeq32AdapterVariantSelectorGateError("variant summary drift")
        if _dict(row.get("grouped"), "variant grouped") != expected["grouped"]:
            raise NativeSeq32AdapterVariantSelectorGateError("variant grouped drift")


def validate_source_artifacts(artifacts: list[Any]) -> None:
    expected_inventory = EXPECTED_SOURCE_ARTIFACTS
    actual_inventory = tuple(
        (_str(_dict(item, "source artifact").get("id"), "source artifact id"), _str(item.get("path"), "source artifact path"))
        for item in artifacts
    )
    if actual_inventory != expected_inventory:
        raise NativeSeq32AdapterVariantSelectorGateError("source artifact inventory drift")
    for item in artifacts:
        artifact = _dict(item, "source artifact")
        path = ROOT / _str(artifact.get("path"), "source artifact path")
        raw = read_repo_file(path, "source artifact")
        if artifact.get("sha256") != sha256(raw) or artifact.get("size_bytes") != len(raw):
            raise NativeSeq32AdapterVariantSelectorGateError("source artifact digest drift")


def validate_mutation_result(result: dict[str, Any]) -> None:
    if result.get("mutation_names") != list(MUTATION_NAMES):
        raise NativeSeq32AdapterVariantSelectorGateError("mutation result drift")
    cases = _list(result.get("cases"), "mutation cases")
    if [case.get("name") for case in cases if isinstance(case, dict)] != list(MUTATION_NAMES):
        raise NativeSeq32AdapterVariantSelectorGateError("mutation result drift")
    if result.get("mutations_rejected") != len(MUTATION_NAMES) or result.get("all_mutations_rejected") is not True:
        raise NativeSeq32AdapterVariantSelectorGateError("mutation result drift")
    for case in cases:
        row = _dict(case, "mutation case")
        if row.get("rejected") is not True or not row.get("error"):
            raise NativeSeq32AdapterVariantSelectorGateError("mutation result drift")


def payload_with_mutations() -> dict[str, Any]:
    return build_payload()


def render_tsv(payload: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    summary = payload["summary"]
    writer.writerow(
        {
            "decision": payload["decision"],
            "result": payload["result"],
            "current_champion_typed_bytes": summary["current_champion_typed_bytes"],
            "best_variant_id": summary["best_variant_id"],
            "best_variant_typed_bytes": summary["best_variant_typed_bytes"],
            "best_variant_gap_typed_bytes": summary["best_variant_gap_typed_bytes"],
            "best_variant_json_bytes": summary["best_variant_json_bytes"],
            "best_variant_gap_json_bytes": summary["best_variant_gap_json_bytes"],
            "frontier_typed_bytes": summary["frontier_typed_bytes"],
            "current_champion_saving_vs_frontier_bytes": summary["current_champion_saving_vs_frontier_bytes"],
            "proof_size_comparable_external_rows": summary["proof_size_comparable_external_rows"],
        }
    )
    return output.getvalue()


def atomic_write_text(path: pathlib.Path, text: str) -> None:
    target = require_output_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    reject_symlinked_ancestors(target)
    if target.exists() and target.is_symlink():
        raise NativeSeq32AdapterVariantSelectorGateError(f"refusing to overwrite symlink: {target}")
    for attempt in range(DETERMINISTIC_TEMP_ATTEMPTS):
        tmp = target.with_name(f".{target.name}.tmp.{attempt}")
        try:
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            continue
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, target)
            return
        except Exception:
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass
            raise
    raise NativeSeq32AdapterVariantSelectorGateError(f"deterministic temp file collision for {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
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
                "current_champion_typed_bytes": payload["summary"]["current_champion_typed_bytes"],
                "best_variant_id": payload["summary"]["best_variant_id"],
                "best_variant_typed_bytes": payload["summary"]["best_variant_typed_bytes"],
                "best_variant_gap_typed_bytes": payload["summary"]["best_variant_gap_typed_bytes"],
                "mutations_rejected": payload["mutation_result"]["mutations_rejected"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
