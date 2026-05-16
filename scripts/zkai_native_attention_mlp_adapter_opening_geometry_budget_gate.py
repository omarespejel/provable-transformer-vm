#!/usr/bin/env python3
"""Gate the adapter opening-geometry budget after the current adapter NO-GOs."""

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

ACCOUNTING_SOURCES = {
    "source_backed_selector": {
        "path": EVIDENCE_DIR
        / "zkai-native-attention-mlp-source-backed-adapter-selector-binary-accounting-2026-05.json",
        "raw_digest": "4839315470734e0a6a7c2065c40338a2c08bf07576b9625c8a95c0cd9eb52da0",
        "expected_rows": {
            "zkai-native-attention-mlp-source-backed-duplicate-adapter-2026-05.envelope.json",
            "zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json",
        },
    },
    "preprocessed_output_anchor": {
        "path": EVIDENCE_DIR
        / "zkai-native-attention-mlp-preprocessed-output-anchor-adapter-frontier-binary-accounting-2026-05.json",
        "raw_digest": "77fe892080fbe16fd62d969cdd1538aa78c987a54a41bf28d089a3ce19334394",
        "expected_rows": {
            "zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json",
            "zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.envelope.json",
        },
    },
    "rmsnorm_input_fused": {
        "path": EVIDENCE_DIR
        / "zkai-native-attention-mlp-rmsnorm-input-fused-adapter-binary-accounting-2026-05.json",
        "raw_digest": "bdd2cc67b1590fb79a68d316a9e362c6f996c47c2c43c77fd50c390821d95b2b",
        "expected_rows": {
            "zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json",
            "zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json",
        },
    },
    "native_adapter_air": {
        "path": EVIDENCE_DIR / "zkai-native-attention-mlp-single-proof-binary-accounting-2026-05.json",
        "raw_digest": "96073160916177a2dad18aff8b85616774cac60bdc8734f50d59848c315bdb9a",
        "expected_rows": {
            "zkai-native-attention-mlp-single-proof-2026-05.envelope.json",
        },
    },
}

SOURCE_GATE_ARTIFACTS = {
    "source_backed_selector": {
        "path": EVIDENCE_DIR / "zkai-native-attention-mlp-source-backed-adapter-selector-2026-05.json",
        "schema": "zkai-native-attention-mlp-source-backed-adapter-selector-gate-v1",
        "decision": "NARROW_CLAIM_SOURCE_BACKED_COMPACT_ADAPTER_SELECTOR_VERIFIES",
        "result": "GO_SOURCE_BACKED_COMPACT_ARTIFACT_NO_GO_TWO_PROOF_FRONTIER_BEAT",
        "payload_commitment": "blake2b-256:d3e06d3edb7f62ea1d268a77c574354fcf2166c12cad010390d1f2bfb28fca5f",
        "raw_digest": "68c5440aaf94b02e39bc17c8447bf734215a8e14bb22bea8e741bd358fa3ec65",
    },
    "preprocessed_output_anchor": {
        "path": EVIDENCE_DIR / "zkai-native-attention-mlp-preprocessed-output-anchor-adapter-frontier-2026-05.json",
        "schema": "zkai-native-attention-mlp-preprocessed-output-anchor-adapter-frontier-gate-v1",
        "decision": "NO_GO_PREPROCESSED_OUTPUT_ANCHOR_ADAPTER_FRONTIER",
        "result": "NO_GO_FEWER_ADAPTER_BASE_CELLS_INCREASE_TYPED_PROOF_BYTES",
        "payload_commitment": "blake2b-256:5ce0738ac2a1ccdcdf8f0ba9a25e4b80a60be3cdb0ddb7a576b5cdc0256064fa",
        "raw_digest": "da18c0b7a0f003fda4ce0b5a1f7060fec399b9459ad29d21766a0ba9c2a7f536",
    },
    "rmsnorm_input_fused": {
        "path": EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.json",
        "schema": "zkai-native-attention-mlp-rmsnorm-input-fused-adapter-gate-v1",
        "decision": "NO_GO_RMSNORM_INPUT_FUSED_ADAPTER_PROOF_SIZE_FRONTIER",
        "result": "NO_GO_ZERO_ADAPTER_BASE_COLUMNS_STILL_INCREASE_TYPED_PROOF_BYTES",
        "payload_commitment": "blake2b-256:d7ad10fd1b454668f33dcafb1b6fab2a7d245aa18239deb495ca67e7a4fc7ebe",
        "raw_digest": "74de86d0f2a4c0588a64a19bb34e5f1fded0b24315e7fdc071552480e51a278d",
    },
    "native_adapter_air": {
        "path": EVIDENCE_DIR / "zkai-native-attention-mlp-single-proof-2026-05.json",
        "schema": "zkai-native-attention-mlp-single-proof-object-gate-v1",
        "decision": "GO_NATIVE_ATTENTION_MLP_SINGLE_STWO_PROOF_OBJECT_VERIFIES",
        "result": "NARROW_CLAIM_NATIVE_ADAPTER_AIR_VERIFIES_WITH_TYPED_SIZE_COST",
        "payload_commitment": "sha256:57c3aa505ceabcd86903abaca1127c680b21a7a1771c75d26bcff50163852dd7",
        "raw_digest": "7e68dac61d177b61b98468d1ad788756af7e06890585fa726fa3a5fdfbaade4c",
    },
}

JSON_OUT = EVIDENCE_DIR / "zkai-native-attention-mlp-adapter-opening-geometry-budget-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-attention-mlp-adapter-opening-geometry-budget-2026-05.tsv"

SCHEMA = "zkai-native-attention-mlp-adapter-opening-geometry-budget-gate-v1"
DECISION = "GO_OPENING_GEOMETRY_BUDGET_PINNED"
RESULT = "RMSNORM_INPUT_FUSED_IS_BEST_SEMANTIC_FUSION_ATTACK_BUT_NO_PROOF_SIZE_WIN"
ISSUE = "rmsnorm-input opening-layout follow-up tracked separately"
PAYLOAD_DOMAIN = "ptvm:zkai:native-attention-mlp-adapter-opening-geometry-budget:v1"
CLAIM_BOUNDARY = (
    "CURRENT_ADAPTER_VARIANTS_SHOW_THAT_OPENING_AND_DECOMMITMENT_GEOMETRY_IS_THE_NEXT_ATTACK_SURFACE;"
    "_NO_VARIANT_BEATS_THE_COMPACT_SELECTOR_OR_TWO_PROOF_FRONTIER"
)

TWO_PROOF_FRONTIER_TYPED_BYTES = 40_700
TWO_PROOF_FRONTIER_JSON_BYTES = 116_258
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900
MAX_JSON_INPUT_BYTES = 64 * 1024 * 1024

GROUP_KEYS = (
    "fixed_overhead",
    "fri_decommitments",
    "fri_samples",
    "oods_samples",
    "queries_values",
    "trace_decommitments",
)
PATH_OPENING_GROUPS = ("fri_decommitments", "fri_samples", "trace_decommitments")
VALUE_GROUPS = ("oods_samples", "queries_values")

EXPECTED_VARIANTS = {
    "source_backed_duplicate": {
        "evidence_relative_path": "zkai-native-attention-mlp-source-backed-duplicate-adapter-2026-05.envelope.json",
        "proof_json_size_bytes": 124_585,
        "typed_size_estimate_bytes": 43_228,
        "record_stream_sha256": "d5e901818d55d538f03adfefb910e3e52f34a13eb1465dfd3af76d746f141154",
        "proof_sha256": "1bc12802bbd06279135026921d0ff369cdfbd546c3bb67635bc8d723bbbcf023",
        "envelope_sha256": "8e687006dc13dba216bd18bc06260e5272739d9da96544379a08dcdc7659ba04",
        "typed_groups": {
            "fixed_overhead": 48,
            "fri_decommitments": 14_176,
            "fri_samples": 848,
            "oods_samples": 12_240,
            "queries_values": 9_132,
            "trace_decommitments": 6_784,
        },
        "semantic_fusion_attack": False,
    },
    "compact_selector": {
        "evidence_relative_path": "zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json",
        "proof_json_size_bytes": 116_091,
        "typed_size_estimate_bytes": 40_812,
        "record_stream_sha256": "8ed8db52bfb240a2b742df9877aa8d01ece09334616540771812e28081c5d996",
        "proof_sha256": "fba78004f082a1799ba784ce4fd539bb8659be225804136e5dab723dd121ca9e",
        "envelope_sha256": "7c45e4bdc16c330bac25fbe93884569cd578f8ec988efc4f29723ec490750263",
        "typed_groups": {
            "fixed_overhead": 48,
            "fri_decommitments": 12_448,
            "fri_samples": 784,
            "oods_samples": 12_176,
            "queries_values": 9_084,
            "trace_decommitments": 6_272,
        },
        "semantic_fusion_attack": False,
    },
    "native_adapter_air": {
        "evidence_relative_path": "zkai-native-attention-mlp-single-proof-2026-05.envelope.json",
        "proof_json_size_bytes": 119_790,
        "typed_size_estimate_bytes": 41_932,
        "record_stream_sha256": "4f1b230afc4f7fec71ce632faa2b0b9512276467aa9dd05f48cd1fba4ba581f4",
        "proof_sha256": "853b0ec34805c9c41874659b3e6188670066229acc633f1d2a5dd616c438ba9f",
        "envelope_sha256": "f3391f213531957e1dc0522e2415b3783b9e0eb759c1a52f17b1415cfe4e7585",
        "typed_groups": {
            "fixed_overhead": 48,
            "fri_decommitments": 13_184,
            "fri_samples": 800,
            "oods_samples": 12_240,
            "queries_values": 9_132,
            "trace_decommitments": 6_528,
        },
        "semantic_fusion_attack": False,
    },
    "preprocessed_output_anchor": {
        "evidence_relative_path": "zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.envelope.json",
        "proof_json_size_bytes": 119_360,
        "typed_size_estimate_bytes": 41_704,
        "record_stream_sha256": "a3f5c710b3a7799beffa40085ecd9e1dcf392492dacb56a2e0d6ecdc568afe88",
        "proof_sha256": "239690dc960e4a09776c39b53a3b53ed674dbeee4ea82b875cb8c80d6dcc09fa",
        "envelope_sha256": "876211e34bd0ad7cb1806634f460c766d0495816cfa502bf9c339d7d73f2c6e2",
        "typed_groups": {
            "fixed_overhead": 48,
            "fri_decommitments": 13_248,
            "fri_samples": 816,
            "oods_samples": 12_064,
            "queries_values": 9_000,
            "trace_decommitments": 6_528,
        },
        "semantic_fusion_attack": True,
    },
    "rmsnorm_input_fused": {
        "evidence_relative_path": "zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json",
        "proof_json_size_bytes": 118_378,
        "typed_size_estimate_bytes": 41_428,
        "record_stream_sha256": "2f7f36ee6000173dea41ab684dab9a20f36f95277eeb7c9a749a98c185583d91",
        "proof_sha256": "1dee6c17a18d4179a8a49646a575d0ec22e5f2442d229c6f8a748df53ac34816",
        "envelope_sha256": "d55310b92a1d5e2e8512ca561739f8b997c9c777b05983dbf30743f87fbad3d6",
        "typed_groups": {
            "fixed_overhead": 48,
            "fri_decommitments": 13_184,
            "fri_samples": 800,
            "oods_samples": 11_952,
            "queries_values": 8_916,
            "trace_decommitments": 6_528,
        },
        "semantic_fusion_attack": True,
    },
}

EXPECTED_SUMMARY = {
    "best_current_one_proof_variant": "compact_selector",
    "best_current_one_proof_typed_bytes": 40_812,
    "best_current_one_proof_delta_to_frontier_bytes": 112,
    "best_current_one_proof_reduction_to_beat_frontier_bytes": 113,
    "best_semantic_fusion_attack": "rmsnorm_input_fused",
    "best_semantic_fusion_typed_bytes": 41_428,
    "best_semantic_fusion_delta_to_frontier_bytes": 728,
    "best_semantic_fusion_reduction_to_beat_frontier_bytes": 729,
    "best_semantic_fusion_path_opening_overhang_bytes": 1_008,
    "best_semantic_fusion_opening_removal_fraction_to_beat_frontier": 0.723214,
}

NON_CLAIMS = (
    "not a proof-size improvement over the compact selector",
    "not a two-proof frontier beat",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not timing evidence",
    "not a full transformer block proof",
    "not production-ready zkML",
)

VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-source-backed-duplicate-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-single-proof-2026-05.envelope.json",
    "python3 scripts/zkai_native_attention_mlp_adapter_opening_geometry_budget_gate.py --write-json docs/engineering/evidence/zkai-native-attention-mlp-adapter-opening-geometry-budget-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-attention-mlp-adapter-opening-geometry-budget-2026-05.tsv",
    "python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_adapter_opening_geometry_budget_gate",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

RECORDED_VERIFIER_OUTPUTS = (
    {
        "adapter_mode": "duplicate_base_preprocessed_selector_v1",
        "adapter_status": "NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER",
        "adapter_trace_cells": 1536,
        "envelope_path": "docs/engineering/evidence/zkai-native-attention-mlp-source-backed-duplicate-adapter-2026-05.envelope.json",
        "mode": "verify",
        "pcs_lifting_log_size": 19,
        "proof_size_bytes": 124_585,
        "schema": "zkai-native-attention-mlp-single-proof-cli-summary-v1",
        "verified": True,
    },
    {
        "adapter_mode": "compact_base_referenced_fixed_v1",
        "adapter_status": (
            "NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER_COMPACT_BASE_REFERENCED_FIXED_COLUMNS"
        ),
        "adapter_trace_cells": 1024,
        "envelope_path": "docs/engineering/evidence/zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json",
        "mode": "verify",
        "pcs_lifting_log_size": 19,
        "proof_size_bytes": 116_091,
        "schema": "zkai-native-attention-mlp-single-proof-cli-summary-v1",
        "verified": True,
    },
    {
        "adapter_mode": "preprocessed_output_anchor_fixed_v1",
        "adapter_status": (
            "NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER_PREPROCESSED_FIXED_COLUMNS_WITH_OUTPUT_ANCHOR"
        ),
        "adapter_trace_cells": 128,
        "envelope_path": (
            "docs/engineering/evidence/"
            "zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.envelope.json"
        ),
        "mode": "verify",
        "pcs_lifting_log_size": 19,
        "proof_size_bytes": 119_360,
        "schema": "zkai-native-attention-mlp-single-proof-cli-summary-v1",
        "verified": True,
    },
    {
        "adapter_mode": "rmsnorm_input_fused_fixed_v1",
        "adapter_status": "NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER_FUSED_INTO_RMSNORM_INPUT_COMPONENT",
        "adapter_trace_cells": 0,
        "envelope_path": "docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json",
        "mode": "verify",
        "pcs_lifting_log_size": 19,
        "proof_size_bytes": 118_378,
        "schema": "zkai-native-attention-mlp-single-proof-cli-summary-v1",
        "verified": True,
    },
    {
        "adapter_mode": "duplicate_base_preprocessed_v1",
        "adapter_status": "NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER",
        "adapter_trace_cells": 1536,
        "envelope_path": "docs/engineering/evidence/zkai-native-attention-mlp-single-proof-2026-05.envelope.json",
        "mode": "verify",
        "pcs_lifting_log_size": 19,
        "proof_size_bytes": 119_790,
        "schema": "zkai-native-attention-mlp-single-proof-cli-summary-v1",
        "verified": True,
    },
)

MUTATION_NAMES = (
    "compact_typed_bytes_drift",
    "rmsnorm_path_opening_budget_drift",
    "anchor_path_opening_budget_drift",
    "semantic_attack_rank_drift",
    "frontier_win_overclaim",
    "nanozk_overclaim",
    "source_gate_commitment_drift",
    "source_gate_raw_digest_drift",
    "payload_commitment_drift",
)

TSV_COLUMNS = (
    "variant",
    "typed_size_estimate_bytes",
    "proof_json_size_bytes",
    "typed_delta_vs_two_proof_frontier_bytes",
    "reduction_to_match_frontier_bytes",
    "reduction_to_beat_frontier_bytes",
    "typed_delta_vs_compact_bytes",
    "path_opening_overhang_vs_compact_bytes",
    "value_group_delta_vs_compact_bytes",
    "opening_removal_fraction_to_beat_frontier",
    "semantic_fusion_attack",
)


class AdapterOpeningGeometryBudgetError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode(
            "utf-8"
        )
    except (TypeError, ValueError) as err:
        raise AdapterOpeningGeometryBudgetError(f"invalid JSON value: {err}") from err


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return "blake2b-256:" + digest.hexdigest()


def refresh_payload_commitment(payload: dict[str, Any]) -> None:
    payload["payload_commitment"] = payload_commitment(payload)


def ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 6)


def read_json_and_raw(path: pathlib.Path) -> tuple[Any, bytes]:
    fd: int | None = None
    try:
        if path.is_symlink():
            raise AdapterOpeningGeometryBudgetError(f"refusing to read symlink: {path}")
        nofollow_flag = getattr(os, "O_NOFOLLOW", None)
        if not isinstance(nofollow_flag, int) or nofollow_flag == 0:
            raise AdapterOpeningGeometryBudgetError(f"refusing to read without O_NOFOLLOW support: {path}")
        flags = os.O_RDONLY | nofollow_flag
        fd = os.open(path, flags)
        file_stat = os.fstat(fd)
        if not stat.S_ISREG(file_stat.st_mode):
            raise AdapterOpeningGeometryBudgetError(f"refusing to read non-regular file: {path}")
        if file_stat.st_size > MAX_JSON_INPUT_BYTES:
            raise AdapterOpeningGeometryBudgetError(
                f"refusing to read {path}: {file_stat.st_size} bytes exceeds {MAX_JSON_INPUT_BYTES}"
            )
        with os.fdopen(fd, "rb") as handle:
            fd = None
            raw = handle.read(MAX_JSON_INPUT_BYTES + 1)
        if len(raw) > MAX_JSON_INPUT_BYTES:
            raise AdapterOpeningGeometryBudgetError(f"refusing to read oversized JSON input: {path}")
        return json.loads(raw.decode("utf-8")), raw
    except OSError as err:
        raise AdapterOpeningGeometryBudgetError(f"failed to read {path}: {err}") from err
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        raise AdapterOpeningGeometryBudgetError(f"failed to parse {path}: {err}") from err
    finally:
        if fd is not None:
            os.close(fd)


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AdapterOpeningGeometryBudgetError(f"{label} must be object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise AdapterOpeningGeometryBudgetError(f"{label} must be list")
    return value


def require_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise AdapterOpeningGeometryBudgetError(f"{label} must be integer")
    return value


def require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise AdapterOpeningGeometryBudgetError(f"{label} must be boolean")
    return value


def require_sha256_hex(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise AdapterOpeningGeometryBudgetError(f"{label} must be 64-character lowercase hex SHA-256")
    return value


def require_typed_groups(value: Any, label: str) -> dict[str, int]:
    groups = require_dict(value, label)
    if set(groups) != set(GROUP_KEYS):
        raise AdapterOpeningGeometryBudgetError(
            f"{label} key drift: got {sorted(groups)}, expected {sorted(GROUP_KEYS)}"
        )
    return {key: require_int(groups[key], f"{label} {key}") for key in GROUP_KEYS}


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def build_context() -> dict[str, Any]:
    accounting_sources = {}
    for name, spec in ACCOUNTING_SOURCES.items():
        payload, raw = read_json_and_raw(spec["path"])
        accounting_sources[name] = {
            "path": spec["path"],
            "payload": require_dict(payload, f"{name} accounting"),
            "sha256": sha256_hex(raw),
            "raw_digest": spec["raw_digest"],
            "expected_rows": spec["expected_rows"],
        }
    source_gate_artifacts = {}
    for name, spec in SOURCE_GATE_ARTIFACTS.items():
        payload, raw = read_json_and_raw(spec["path"])
        source_gate_artifacts[name] = {
            "path": spec["path"],
            "payload": require_dict(payload, f"{name} source gate"),
            "sha256": sha256_hex(raw),
            "expected": spec,
        }
    return {
        "accounting_sources": accounting_sources,
        "source_gate_artifacts": source_gate_artifacts,
    }


def validate_source_gate_artifacts(context: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = []
    for name, artifact in context["source_gate_artifacts"].items():
        payload = require_dict(artifact["payload"], f"{name} source gate payload")
        expected = artifact["expected"]
        if artifact["sha256"] != expected["raw_digest"]:
            raise AdapterOpeningGeometryBudgetError(f"{name} source gate raw digest drift")
        for key in ("schema", "decision", "result", "payload_commitment"):
            if payload.get(key) != expected[key]:
                raise AdapterOpeningGeometryBudgetError(f"{name} source gate {key} drift")
        artifacts.append(
            {
                "name": name,
                "path": str(expected["path"].relative_to(ROOT)),
                "sha256": artifact["sha256"],
                "schema": expected["schema"],
                "decision": expected["decision"],
                "result": expected["result"],
                "payload_commitment": expected["payload_commitment"],
                "raw_digest": expected["raw_digest"],
            }
        )
    return artifacts


def collect_accounting_rows(context: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows_by_path: dict[str, dict[str, Any]] = {}
    for name, source in context["accounting_sources"].items():
        if source["sha256"] != source["raw_digest"]:
            raise AdapterOpeningGeometryBudgetError(f"{name} accounting raw digest drift")
        payload = require_dict(source["payload"], f"{name} accounting payload")
        rows = require_list(payload.get("rows"), f"{name} accounting rows")
        seen_in_source = set()
        for raw_row in rows:
            row = require_dict(raw_row, f"{name} accounting row")
            path = row.get("evidence_relative_path")
            if not isinstance(path, str) or not path:
                raise AdapterOpeningGeometryBudgetError(f"{name} accounting row path must be non-empty string")
            if path in seen_in_source:
                raise AdapterOpeningGeometryBudgetError(f"{name} duplicate accounting row path: {path}")
            seen_in_source.add(path)
            canonical_row = canonical_row_payload(path, row)
            existing = rows_by_path.get(path)
            if existing is not None and existing != canonical_row:
                raise AdapterOpeningGeometryBudgetError(f"cross-source accounting drift for {path}")
            rows_by_path[path] = canonical_row
        expected_rows = source["expected_rows"]
        if seen_in_source != expected_rows:
            raise AdapterOpeningGeometryBudgetError(
                f"{name} accounting row drift: got {sorted(seen_in_source)}, expected {sorted(expected_rows)}"
            )
    expected_paths = {spec["evidence_relative_path"] for spec in EXPECTED_VARIANTS.values()}
    if set(rows_by_path) != expected_paths:
        raise AdapterOpeningGeometryBudgetError(
            f"aggregated accounting row drift: got {sorted(rows_by_path)}, expected {sorted(expected_paths)}"
        )
    return rows_by_path


def canonical_row_payload(path: str, row: dict[str, Any]) -> dict[str, Any]:
    local = require_dict(row.get("local_binary_accounting"), f"{path} local binary accounting")
    return {
        "evidence_relative_path": path,
        "proof_json_size_bytes": require_int(row.get("proof_json_size_bytes"), f"{path} proof JSON bytes"),
        "typed_size_estimate_bytes": require_int(local.get("component_sum_bytes"), f"{path} component sum bytes"),
        "typed_groups": require_typed_groups(local.get("grouped_reconstruction"), f"{path} typed groups"),
        "record_stream_sha256": require_sha256_hex(local.get("record_stream_sha256"), f"{path} record stream"),
        "proof_sha256": require_sha256_hex(row.get("proof_sha256"), f"{path} proof sha256"),
        "envelope_sha256": require_sha256_hex(row.get("envelope_sha256"), f"{path} envelope sha256"),
    }


def variant_payload(name: str, rows_by_path: dict[str, dict[str, Any]], compact_groups: dict[str, int]) -> dict[str, Any]:
    expected = EXPECTED_VARIANTS[name]
    row = rows_by_path[expected["evidence_relative_path"]]
    for key in (
        "proof_json_size_bytes",
        "typed_size_estimate_bytes",
        "record_stream_sha256",
        "proof_sha256",
        "envelope_sha256",
    ):
        if row[key] != expected[key]:
            raise AdapterOpeningGeometryBudgetError(f"{name} {key} drift")
    if row["typed_groups"] != expected["typed_groups"]:
        raise AdapterOpeningGeometryBudgetError(f"{name} typed group drift")

    group_deltas = {key: row["typed_groups"][key] - compact_groups[key] for key in GROUP_KEYS}
    path_opening_overhang = sum(group_deltas[key] for key in PATH_OPENING_GROUPS)
    value_group_delta = sum(group_deltas[key] for key in VALUE_GROUPS)
    typed_delta_vs_frontier = row["typed_size_estimate_bytes"] - TWO_PROOF_FRONTIER_TYPED_BYTES
    reduction_to_match = max(0, typed_delta_vs_frontier)
    reduction_to_beat = max(0, typed_delta_vs_frontier + 1)
    return {
        "name": name,
        "evidence_relative_path": expected["evidence_relative_path"],
        "proof_json_size_bytes": row["proof_json_size_bytes"],
        "typed_size_estimate_bytes": row["typed_size_estimate_bytes"],
        "typed_groups": row["typed_groups"],
        "typed_group_deltas_vs_compact": group_deltas,
        "typed_delta_vs_two_proof_frontier_bytes": typed_delta_vs_frontier,
        "typed_delta_vs_compact_bytes": row["typed_size_estimate_bytes"]
        - EXPECTED_VARIANTS["compact_selector"]["typed_size_estimate_bytes"],
        "reduction_to_match_two_proof_frontier_bytes": reduction_to_match,
        "reduction_to_beat_two_proof_frontier_bytes": reduction_to_beat,
        "path_opening_overhang_vs_compact_bytes": path_opening_overhang,
        "value_group_delta_vs_compact_bytes": value_group_delta,
        "opening_removal_fraction_to_beat_frontier": ratio(reduction_to_beat, path_opening_overhang),
        "semantic_fusion_attack": expected["semantic_fusion_attack"],
        "record_stream_sha256": row["record_stream_sha256"],
        "proof_sha256": row["proof_sha256"],
        "envelope_sha256": row["envelope_sha256"],
    }


def build_payload(context: dict[str, Any] | None = None, *, include_mutations: bool = True) -> dict[str, Any]:
    if context is None:
        context = build_context()
    source_artifacts = validate_source_gate_artifacts(context)
    rows_by_path = collect_accounting_rows(context)
    compact_groups = EXPECTED_VARIANTS["compact_selector"]["typed_groups"]
    variants = {name: variant_payload(name, rows_by_path, compact_groups) for name in EXPECTED_VARIANTS}

    best_current = min(variants.values(), key=lambda item: item["typed_size_estimate_bytes"])
    semantic_attacks = [variant for variant in variants.values() if variant["semantic_fusion_attack"]]
    viable_semantic_attacks = [
        variant for variant in semantic_attacks if variant["opening_removal_fraction_to_beat_frontier"] is not None
    ]
    if not viable_semantic_attacks:
        raise AdapterOpeningGeometryBudgetError("no viable semantic-fusion attack variants")
    best_semantic_attack = min(
        viable_semantic_attacks,
        key=lambda item: item["opening_removal_fraction_to_beat_frontier"],
    )
    summary = {
        "best_current_one_proof_variant": best_current["name"],
        "best_current_one_proof_typed_bytes": best_current["typed_size_estimate_bytes"],
        "best_current_one_proof_delta_to_frontier_bytes": best_current[
            "typed_delta_vs_two_proof_frontier_bytes"
        ],
        "best_current_one_proof_reduction_to_beat_frontier_bytes": best_current[
            "reduction_to_beat_two_proof_frontier_bytes"
        ],
        "best_semantic_fusion_attack": best_semantic_attack["name"],
        "best_semantic_fusion_typed_bytes": best_semantic_attack["typed_size_estimate_bytes"],
        "best_semantic_fusion_delta_to_frontier_bytes": best_semantic_attack[
            "typed_delta_vs_two_proof_frontier_bytes"
        ],
        "best_semantic_fusion_reduction_to_beat_frontier_bytes": best_semantic_attack[
            "reduction_to_beat_two_proof_frontier_bytes"
        ],
        "best_semantic_fusion_path_opening_overhang_bytes": best_semantic_attack[
            "path_opening_overhang_vs_compact_bytes"
        ],
        "best_semantic_fusion_opening_removal_fraction_to_beat_frontier": best_semantic_attack[
            "opening_removal_fraction_to_beat_frontier"
        ],
    }
    if summary != EXPECTED_SUMMARY:
        raise AdapterOpeningGeometryBudgetError(f"summary drift: got {summary}, expected {EXPECTED_SUMMARY}")

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "claim_boundary": CLAIM_BOUNDARY,
        "frontier": {
            "two_proof_frontier_typed_bytes": TWO_PROOF_FRONTIER_TYPED_BYTES,
            "two_proof_frontier_json_bytes": TWO_PROOF_FRONTIER_JSON_BYTES,
            "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
            "nanozk_workload_matched": False,
            "nanozk_win_claimed": False,
            "two_proof_frontier_win_claimed": False,
        },
        "source_artifacts": source_artifacts,
        "variants": variants,
        "summary": summary,
        "interpretation": {
            "human_read": (
                "The compact selector is still the smallest current one-proof object at 40,812 typed bytes, "
                "112 typed bytes above the two-proof frontier. Among semantic-fusion attacks, the "
                "RMSNorm-input fused route is the best next target: it is 728 typed bytes above the "
                "frontier, but carries 1,008 bytes of path-opening overhang versus compact, so removing "
                "729 bytes of that overhang would beat the current two-proof target."
            ),
            "next_attack": (
                "Do not add another adapter variant unless it explicitly reduces FRI samples, FRI "
                "decommitments, or trace decommitments. The first concrete target is the RMSNorm-input "
                "fused route with a transcript/opening layout that removes at least 729 typed bytes."
            ),
        },
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
        "recorded_verifier_outputs": copy.deepcopy(RECORDED_VERIFIER_OUTPUTS),
    }
    refresh_payload_commitment(payload)
    if include_mutations:
        payload["mutation_result"] = mutation_result(payload, context=context)
        refresh_payload_commitment(payload)
    return payload


def validate_payload(
    payload: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
    require_mutation_result: bool = True,
) -> None:
    if context is None:
        context = build_context()
    summary = require_dict(payload.get("summary"), "summary")
    frontier = require_dict(payload.get("frontier"), "frontier")
    variants = require_dict(payload.get("variants"), "variants")

    if summary != EXPECTED_SUMMARY:
        raise AdapterOpeningGeometryBudgetError("summary drift")
    if require_bool(frontier.get("two_proof_frontier_win_claimed"), "two-proof frontier claim"):
        raise AdapterOpeningGeometryBudgetError("two-proof frontier win overclaim")
    if require_bool(frontier.get("nanozk_win_claimed"), "NANOZK claim"):
        raise AdapterOpeningGeometryBudgetError("NANOZK win overclaim")
    if require_bool(frontier.get("nanozk_workload_matched"), "NANOZK workload"):
        raise AdapterOpeningGeometryBudgetError("NANOZK workload overclaim")

    compact = require_dict(variants.get("compact_selector"), "compact selector variant")
    rmsnorm = require_dict(variants.get("rmsnorm_input_fused"), "rmsnorm input fused variant")
    anchor = require_dict(variants.get("preprocessed_output_anchor"), "preprocessed output anchor variant")
    if require_int(compact.get("typed_size_estimate_bytes"), "compact typed bytes") != 40_812:
        raise AdapterOpeningGeometryBudgetError("compact typed byte drift")
    if require_int(rmsnorm.get("path_opening_overhang_vs_compact_bytes"), "rmsnorm path opening overhang") != 1_008:
        raise AdapterOpeningGeometryBudgetError("rmsnorm opening budget drift")
    if (
        require_int(anchor.get("path_opening_overhang_vs_compact_bytes"), "anchor path opening overhang")
        != 1_088
    ):
        raise AdapterOpeningGeometryBudgetError("anchor opening budget drift")
    if rmsnorm.get("opening_removal_fraction_to_beat_frontier") != 0.723214:
        raise AdapterOpeningGeometryBudgetError("rmsnorm opening fraction drift")
    if summary.get("best_semantic_fusion_attack") != "rmsnorm_input_fused":
        raise AdapterOpeningGeometryBudgetError("semantic attack rank drift")

    provided_mutation_result = (
        require_dict(payload.get("mutation_result"), "mutation_result") if require_mutation_result else None
    )
    actual = copy.deepcopy(payload)
    actual.pop("mutation_result", None)
    actual.pop("payload_commitment", None)
    expected_payload = build_payload(context, include_mutations=False)
    expected_core = copy.deepcopy(expected_payload)
    expected_core.pop("payload_commitment", None)
    if actual != expected_core:
        raise AdapterOpeningGeometryBudgetError("payload body drift")
    if require_mutation_result and provided_mutation_result != mutation_result(expected_payload, context=context):
        raise AdapterOpeningGeometryBudgetError("mutation result drift")
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise AdapterOpeningGeometryBudgetError("payload commitment drift")


def mutation_result(payload: dict[str, Any], *, context: dict[str, Any] | None = None) -> dict[str, Any]:
    if context is None:
        context = build_context()
    cases = []
    for name in MUTATION_NAMES:
        candidate = copy.deepcopy(payload)
        candidate.pop("mutation_result", None)
        if name == "compact_typed_bytes_drift":
            candidate["variants"]["compact_selector"]["typed_size_estimate_bytes"] += 1
        elif name == "rmsnorm_path_opening_budget_drift":
            candidate["variants"]["rmsnorm_input_fused"]["path_opening_overhang_vs_compact_bytes"] -= 1
        elif name == "anchor_path_opening_budget_drift":
            candidate["variants"]["preprocessed_output_anchor"]["path_opening_overhang_vs_compact_bytes"] -= 1
        elif name == "semantic_attack_rank_drift":
            candidate["summary"]["best_semantic_fusion_attack"] = "preprocessed_output_anchor"
        elif name == "frontier_win_overclaim":
            candidate["frontier"]["two_proof_frontier_win_claimed"] = True
        elif name == "nanozk_overclaim":
            candidate["frontier"]["nanozk_win_claimed"] = True
        elif name == "source_gate_commitment_drift":
            candidate["source_artifacts"][0]["payload_commitment"] = "blake2b-256:" + "00" * 32
        elif name == "source_gate_raw_digest_drift":
            candidate["source_artifacts"][0]["raw_digest"] = "0" * 64
        elif name == "payload_commitment_drift":
            candidate["payload_commitment"] = "blake2b-256:" + "00" * 32
        else:
            raise AssertionError(name)
        if name != "payload_commitment_drift":
            refresh_payload_commitment(candidate)
        rejected = False
        try:
            validate_payload(candidate, context=context, require_mutation_result=False)
        except AdapterOpeningGeometryBudgetError:
            rejected = True
        cases.append({"name": name, "rejected": rejected})
    return {
        "mutation_count": len(cases),
        "rejected_count": sum(1 for case in cases if case["rejected"]),
        "cases": cases,
    }


def build_tsv_text(payload: dict[str, Any]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=TSV_COLUMNS, dialect="excel-tab", lineterminator="\n")
    writer.writeheader()
    for variant_name in sorted(payload["variants"]):
        variant = payload["variants"][variant_name]
        writer.writerow(
            {
                "variant": variant["name"],
                "typed_size_estimate_bytes": variant["typed_size_estimate_bytes"],
                "proof_json_size_bytes": variant["proof_json_size_bytes"],
                "typed_delta_vs_two_proof_frontier_bytes": variant["typed_delta_vs_two_proof_frontier_bytes"],
                "reduction_to_match_frontier_bytes": variant["reduction_to_match_two_proof_frontier_bytes"],
                "reduction_to_beat_frontier_bytes": variant["reduction_to_beat_two_proof_frontier_bytes"],
                "typed_delta_vs_compact_bytes": variant["typed_delta_vs_compact_bytes"],
                "path_opening_overhang_vs_compact_bytes": variant["path_opening_overhang_vs_compact_bytes"],
                "value_group_delta_vs_compact_bytes": variant["value_group_delta_vs_compact_bytes"],
                "opening_removal_fraction_to_beat_frontier": variant["opening_removal_fraction_to_beat_frontier"],
                "semantic_fusion_attack": variant["semantic_fusion_attack"],
            }
        )
    return buffer.getvalue()


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path | None, tsv_path: pathlib.Path | None) -> None:
    validate_payload(payload)
    if json_path is not None:
        json_path = require_output_path(json_path, ".json")
        write_text_atomically(json_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if tsv_path is not None:
        tsv_path = require_output_path(tsv_path, ".tsv")
        write_text_atomically(tsv_path, build_tsv_text(payload))


def require_output_path(path: pathlib.Path, suffix: str) -> pathlib.Path:
    candidate = path if path.is_absolute() else ROOT / path
    if candidate.suffix != suffix:
        raise AdapterOpeningGeometryBudgetError(f"output path must use {suffix} suffix: {path}")
    if candidate.is_symlink():
        raise AdapterOpeningGeometryBudgetError(f"refusing to overwrite symlink: {candidate}")
    try:
        if EVIDENCE_DIR.is_symlink():
            raise AdapterOpeningGeometryBudgetError(f"refusing symlinked evidence directory: {EVIDENCE_DIR}")
        evidence_dir = EVIDENCE_DIR.resolve(strict=True)
        root = ROOT.resolve(strict=True)
        if not evidence_dir.is_relative_to(root):
            raise AdapterOpeningGeometryBudgetError(f"evidence directory must stay under {ROOT}: {EVIDENCE_DIR}")
        parent = candidate.parent.resolve(strict=True)
    except OSError as err:
        raise AdapterOpeningGeometryBudgetError(f"failed to resolve output path {path}: {err}") from err
    if parent != evidence_dir:
        raise AdapterOpeningGeometryBudgetError(f"output path must be inside {EVIDENCE_DIR}: {path}")
    return candidate


def write_text_atomically(path: pathlib.Path, text: str) -> None:
    if path.is_symlink():
        raise AdapterOpeningGeometryBudgetError(f"refusing to overwrite symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise AdapterOpeningGeometryBudgetError(f"refusing symlinked output parent: {path.parent}")
    dir_fd: int | None = None
    fd: int | None = None
    tmp_name: str | None = None
    try:
        dir_fd = open_directory_fd(path.parent)
        tmp_name = f".{path.name}.{os.getpid()}.{secrets.token_hex(8)}.tmp"
        fd = os.open(tmp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666, dir_fd=dir_fd)
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
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
        raise AdapterOpeningGeometryBudgetError(f"failed to write {path}: {err}") from err
    finally:
        if dir_fd is not None:
            os.close(dir_fd)


def open_directory_fd(path: pathlib.Path) -> int:
    nofollow_flag = getattr(os, "O_NOFOLLOW", None)
    if not isinstance(nofollow_flag, int) or nofollow_flag == 0:
        raise AdapterOpeningGeometryBudgetError(f"refusing directory open without O_NOFOLLOW support: {path}")
    flags = os.O_RDONLY | nofollow_flag
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    if isinstance(directory_flag, int) and directory_flag != 0:
        flags |= directory_flag
    return os.open(path, flags)


def fsync_dir_fd(dir_fd: int, path: pathlib.Path) -> None:
    try:
        os.fsync(dir_fd)
    except OSError as err:
        raise AdapterOpeningGeometryBudgetError(f"failed to fsync directory {path}: {err}") from err


def fsync_parent_dir(path: pathlib.Path) -> None:
    if os.name == "nt":
        return
    dir_fd: int | None = None
    try:
        dir_fd = open_directory_fd(path.parent)
        fsync_dir_fd(dir_fd, path.parent)
    except OSError as err:
        raise AdapterOpeningGeometryBudgetError(f"failed to fsync parent directory for {path}: {err}") from err
    finally:
        if dir_fd is not None:
            os.close(dir_fd)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json", type=pathlib.Path, default=None)
    parser.add_argument("--write-tsv", type=pathlib.Path, default=None)
    args = parser.parse_args()

    payload = build_payload()
    write_outputs(payload, args.write_json, args.write_tsv)
    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "decision": payload["decision"],
                "result": payload["result"],
                "best_current_one_proof_typed_bytes": payload["summary"]["best_current_one_proof_typed_bytes"],
                "best_semantic_fusion_attack": payload["summary"]["best_semantic_fusion_attack"],
                "best_semantic_fusion_opening_removal_fraction_to_beat_frontier": payload["summary"][
                    "best_semantic_fusion_opening_removal_fraction_to_beat_frontier"
                ],
                "mutation_rejections": payload["mutation_result"]["rejected_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
