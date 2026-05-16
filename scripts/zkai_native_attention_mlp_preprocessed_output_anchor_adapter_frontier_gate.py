#!/usr/bin/env python3
"""Gate the preprocessed output-anchor adapter frontier probe."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import copy
import csv
import hashlib
import io
import json
import pathlib
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import zkai_native_attention_mlp_single_proof_route_gate as route_gate  # noqa: E402


EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
COMPACT_INPUT_PATH = (
    EVIDENCE_DIR / "zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.input.json"
)
COMPACT_ENVELOPE_PATH = (
    EVIDENCE_DIR / "zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json"
)
ANCHOR_INPUT_PATH = (
    EVIDENCE_DIR
    / "zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.input.json"
)
ANCHOR_ENVELOPE_PATH = (
    EVIDENCE_DIR
    / "zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.envelope.json"
)
ACCOUNTING_PATH = (
    EVIDENCE_DIR
    / "zkai-native-attention-mlp-preprocessed-output-anchor-adapter-frontier-binary-accounting-2026-05.json"
)

JSON_OUT = (
    EVIDENCE_DIR / "zkai-native-attention-mlp-preprocessed-output-anchor-adapter-frontier-2026-05.json"
)
TSV_OUT = EVIDENCE_DIR / "zkai-native-attention-mlp-preprocessed-output-anchor-adapter-frontier-2026-05.tsv"

SCHEMA = "zkai-native-attention-mlp-preprocessed-output-anchor-adapter-frontier-gate-v1"
DECISION = "NO_GO_PREPROCESSED_OUTPUT_ANCHOR_ADAPTER_FRONTIER"
RESULT = "NO_GO_FEWER_ADAPTER_BASE_CELLS_INCREASE_TYPED_PROOF_BYTES"
ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/639"
PAYLOAD_DOMAIN = "ptvm:zkai:native-attention-mlp-preprocessed-output-anchor-adapter-frontier:v1"
CLAIM_BOUNDARY = (
    "SOURCE_BACKED_PREPROCESSED_OUTPUT_ANCHOR_ADAPTER_PROVES_AND_VERIFIES_BUT_DOES_NOT_BEAT_"
    "THE_COMPACT_ADAPTER_OR_THE_TWO_PROOF_FRONTIER"
)

TWO_PROOF_FRONTIER_TYPED_BYTES = 40_700
TWO_PROOF_FRONTIER_JSON_BYTES = 116_258
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900

EXPECTED_VARIANTS = {
    "compact_selector": {
        "input_path": COMPACT_INPUT_PATH,
        "envelope_path": COMPACT_ENVELOPE_PATH,
        "accounting_relative_path": "zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json",
        "adapter_mode": "compact_base_referenced_fixed_v1",
        "adapter_status": "NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER_COMPACT_BASE_REFERENCED_FIXED_COLUMNS",
        "adapter_value_columns": 5,
        "adapter_trace_cells": 1_024,
        "proof_backend_version": "stwo-native-attention-mlp-single-proof-object-compact-adapter-selector-v1",
        "proof_json_size_bytes": 116_091,
        "typed_size_estimate_bytes": 40_812,
        "envelope_size_bytes": 1_224_675,
        "record_stream_sha256": "8ed8db52bfb240a2b742df9877aa8d01ece09334616540771812e28081c5d996",
    },
    "preprocessed_output_anchor": {
        "input_path": ANCHOR_INPUT_PATH,
        "envelope_path": ANCHOR_ENVELOPE_PATH,
        "accounting_relative_path": (
            "zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.envelope.json"
        ),
        "adapter_mode": "preprocessed_output_anchor_fixed_v1",
        "adapter_status": (
            "NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER_"
            "PREPROCESSED_FIXED_COLUMNS_WITH_OUTPUT_ANCHOR"
        ),
        "adapter_value_columns": 1,
        "adapter_trace_cells": 128,
        "proof_backend_version": "stwo-native-attention-mlp-single-proof-object-preprocessed-output-anchor-adapter-v1",
        "proof_json_size_bytes": 119_360,
        "typed_size_estimate_bytes": 41_704,
        "envelope_size_bytes": 1_251_017,
        "record_stream_sha256": "a3f5c710b3a7799beffa40085ecd9e1dcf392492dacb56a2e0d6ecdc568afe88",
    },
}
EXPECTED_ACCOUNTING_RELATIVE_PATHS = frozenset(
    variant["accounting_relative_path"] for variant in EXPECTED_VARIANTS.values()
)

EXPECTED_GROUP_DELTAS_ANCHOR_MINUS_COMPACT = {
    "fixed_overhead": 0,
    "fri_decommitments": 800,
    "fri_samples": 32,
    "oods_samples": -112,
    "queries_values": -84,
    "trace_decommitments": 256,
}

NON_CLAIMS = (
    "not a proof-size improvement",
    "not a compact-adapter replacement",
    "not a two-proof frontier beat",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not timing evidence",
    "not a full transformer block proof",
    "not production-ready zkML",
)

VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-preprocessed-anchor docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-source-backed-preprocessed-output-anchor-adapter-2026-05.envelope.json > docs/engineering/evidence/zkai-native-attention-mlp-preprocessed-output-anchor-adapter-frontier-binary-accounting-2026-05.json",
    "python3 scripts/zkai_native_attention_mlp_preprocessed_output_anchor_adapter_frontier_gate.py --write-json docs/engineering/evidence/zkai-native-attention-mlp-preprocessed-output-anchor-adapter-frontier-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-attention-mlp-preprocessed-output-anchor-adapter-frontier-2026-05.tsv",
    "python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_preprocessed_output_anchor_adapter_frontier_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend preprocessed_output_anchor_adapter --lib",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend native_attention_mlp_single_proof --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

CORE_KEYS = {
    "schema",
    "decision",
    "result",
    "issue",
    "claim_boundary",
    "source_artifacts",
    "variants",
    "comparisons",
    "summary",
    "interpretation",
    "non_claims",
    "validation_commands",
    "payload_commitment",
}
MUTATION_KEYS = {"mutation_inventory", "mutation_result"}
FINAL_KEYS = CORE_KEYS | MUTATION_KEYS

MUTATION_NAMES = (
    "anchor_typed_bytes_drift",
    "compact_typed_bytes_drift",
    "anchor_mode_relabeling",
    "frontier_win_overclaim",
    "nanozk_overclaim",
    "zero_column_support_overclaim",
    "source_artifact_hash_drift",
    "payload_commitment_drift",
)

TSV_COLUMNS = (
    "decision",
    "result",
    "compact_typed_bytes",
    "anchor_typed_bytes",
    "anchor_typed_delta_vs_compact_bytes",
    "anchor_typed_delta_vs_two_proof_frontier_bytes",
    "compact_trace_cells",
    "anchor_trace_cells",
    "anchor_trace_cell_reduction_vs_compact",
    "anchor_json_delta_vs_compact_bytes",
    "anchor_json_delta_vs_two_proof_frontier_bytes",
)


class PreprocessedOutputAnchorFrontierError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode(
            "utf-8"
        )
    except (TypeError, ValueError) as err:
        raise PreprocessedOutputAnchorFrontierError(f"invalid JSON value: {err}") from err


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return "blake2b-256:" + digest.hexdigest()


def refresh_payload_commitment(payload: dict[str, Any]) -> None:
    payload["payload_commitment"] = payload_commitment(payload)


def ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        raise PreprocessedOutputAnchorFrontierError("ratio denominator must be positive")
    return round(numerator / denominator, 6)


def _dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PreprocessedOutputAnchorFrontierError(f"{label} must be object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise PreprocessedOutputAnchorFrontierError(f"{label} must be list")
    return value


def _str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise PreprocessedOutputAnchorFrontierError(f"{label} must be non-empty string")
    return value


def _int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise PreprocessedOutputAnchorFrontierError(f"{label} must be integer")
    return value


def read_json_and_raw(path: pathlib.Path, label: str) -> tuple[Any, bytes]:
    try:
        return route_gate.read_json_and_raw_bytes(path, label)
    except route_gate.NativeAttentionMlpSingleProofRouteError as err:
        raise PreprocessedOutputAnchorFrontierError(str(err)) from err


def build_context() -> dict[str, Any]:
    values: dict[str, Any] = {}
    for key, path in (
        ("compact_input", COMPACT_INPUT_PATH),
        ("compact_envelope", COMPACT_ENVELOPE_PATH),
        ("anchor_input", ANCHOR_INPUT_PATH),
        ("anchor_envelope", ANCHOR_ENVELOPE_PATH),
        ("accounting", ACCOUNTING_PATH),
    ):
        payload, raw = read_json_and_raw(path, key)
        values[key] = _dict(payload, key)
        values[f"{key}_raw"] = raw
    return values


def source_artifacts(context: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = []
    for artifact_id, path, raw_key in (
        ("compact_input", COMPACT_INPUT_PATH, "compact_input_raw"),
        ("compact_envelope", COMPACT_ENVELOPE_PATH, "compact_envelope_raw"),
        ("preprocessed_output_anchor_input", ANCHOR_INPUT_PATH, "anchor_input_raw"),
        ("preprocessed_output_anchor_envelope", ANCHOR_ENVELOPE_PATH, "anchor_envelope_raw"),
        ("preprocessed_output_anchor_binary_accounting", ACCOUNTING_PATH, "accounting_raw"),
    ):
        artifacts.append(
            {
                "id": artifact_id,
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(context[raw_key]).hexdigest(),
            }
        )
    return artifacts


def accounting_rows_by_path(accounting: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_rows = _list(accounting.get("rows"), "accounting rows")
    if len(raw_rows) != len(EXPECTED_ACCOUNTING_RELATIVE_PATHS):
        raise PreprocessedOutputAnchorFrontierError(
            f"expected {len(EXPECTED_ACCOUNTING_RELATIVE_PATHS)} accounting rows, got {len(raw_rows)}"
        )
    rows = {}
    for row in raw_rows:
        row_dict = _dict(row, "accounting row")
        path = _str(row_dict.get("evidence_relative_path"), "accounting relative path")
        if path in rows:
            raise PreprocessedOutputAnchorFrontierError(f"duplicate accounting row path: {path}")
        rows[path] = row_dict
    actual_paths = frozenset(rows)
    if actual_paths != EXPECTED_ACCOUNTING_RELATIVE_PATHS:
        missing = sorted(EXPECTED_ACCOUNTING_RELATIVE_PATHS - actual_paths)
        extra = sorted(actual_paths - EXPECTED_ACCOUNTING_RELATIVE_PATHS)
        raise PreprocessedOutputAnchorFrontierError(f"accounting row path drift: missing={missing} extra={extra}")
    return rows


def variant_payload(role: str, context: dict[str, Any], rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    expected = EXPECTED_VARIANTS[role]
    envelope_key = "compact_envelope" if role == "compact_selector" else "anchor_envelope"
    input_key = "compact_input" if role == "compact_selector" else "anchor_input"
    raw_key = f"{envelope_key}_raw"
    envelope = _dict(context[envelope_key], f"{role} envelope")
    input_payload = _dict(envelope.get("input"), f"{role} envelope input")
    standalone_input = _dict(context[input_key], f"{role} input")
    accounting_path = expected["accounting_relative_path"]
    row = rows.get(accounting_path)
    if row is None:
        raise PreprocessedOutputAnchorFrontierError(f"{role} missing accounting row: {accounting_path}")
    local = _dict(row.get("local_binary_accounting"), f"{role} local accounting")
    metadata = _dict(row.get("envelope_metadata"), f"{role} envelope metadata")
    checks = {
        "adapter_mode": input_payload.get("adapter_mode"),
        "adapter_status": input_payload.get("adapter_status"),
        "adapter_value_columns": input_payload.get("adapter_value_columns"),
        "adapter_trace_cells": input_payload.get("adapter_trace_cells"),
        "proof_backend_version": envelope.get("proof_backend_version"),
        "proof_json_size_bytes": row.get("proof_json_size_bytes"),
        "typed_size_estimate_bytes": local.get("typed_size_estimate_bytes"),
        "envelope_size_bytes": len(context[raw_key]),
        "record_stream_sha256": local.get("record_stream_sha256"),
    }
    for key, expected_value in expected.items():
        if key in {"input_path", "envelope_path", "accounting_relative_path"}:
            continue
        if checks.get(key) != expected_value:
            raise PreprocessedOutputAnchorFrontierError(
                f"{role} {key} drift: got {checks.get(key)!r}, expected {expected_value!r}"
            )
    if standalone_input != input_payload:
        raise PreprocessedOutputAnchorFrontierError(f"{role} standalone input does not match envelope input")
    if metadata.get("proof_backend_version") != expected["proof_backend_version"]:
        raise PreprocessedOutputAnchorFrontierError(f"{role} accounting backend version drift")
    if local.get("component_sum_bytes") != expected["typed_size_estimate_bytes"]:
        raise PreprocessedOutputAnchorFrontierError(f"{role} component sum drift")
    return {
        "adapter_mode": checks["adapter_mode"],
        "adapter_status": checks["adapter_status"],
        "adapter_row_count": input_payload["adapter_row_count"],
        "adapter_value_columns": checks["adapter_value_columns"],
        "adapter_remainder_bit_columns": input_payload["adapter_remainder_bit_columns"],
        "adapter_trace_cells": checks["adapter_trace_cells"],
        "proof_backend_version": checks["proof_backend_version"],
        "statement_commitment": input_payload["statement_commitment"],
        "public_instance_commitment": input_payload["public_instance_commitment"],
        "proof_json_size_bytes": checks["proof_json_size_bytes"],
        "typed_size_estimate_bytes": checks["typed_size_estimate_bytes"],
        "envelope_size_bytes": checks["envelope_size_bytes"],
        "record_stream_sha256": checks["record_stream_sha256"],
        "grouped_reconstruction": local["grouped_reconstruction"],
    }


def build_payload_no_mutations(context: dict[str, Any]) -> dict[str, Any]:
    accounting = _dict(context["accounting"], "accounting")
    rows = accounting_rows_by_path(accounting)
    compact = variant_payload("compact_selector", context, rows)
    anchor = variant_payload("preprocessed_output_anchor", context, rows)
    compact_groups = _dict(compact["grouped_reconstruction"], "compact groups")
    anchor_groups = _dict(anchor["grouped_reconstruction"], "anchor groups")
    group_deltas = {
        key: _int(anchor_groups.get(key), f"anchor {key}") - _int(compact_groups.get(key), f"compact {key}")
        for key in EXPECTED_GROUP_DELTAS_ANCHOR_MINUS_COMPACT
    }
    if group_deltas != EXPECTED_GROUP_DELTAS_ANCHOR_MINUS_COMPACT:
        raise PreprocessedOutputAnchorFrontierError(f"group deltas drift: {group_deltas}")
    typed_delta_vs_compact = anchor["typed_size_estimate_bytes"] - compact["typed_size_estimate_bytes"]
    json_delta_vs_compact = anchor["proof_json_size_bytes"] - compact["proof_json_size_bytes"]
    trace_cell_reduction = compact["adapter_trace_cells"] - anchor["adapter_trace_cells"]
    payload = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_artifacts": source_artifacts(context),
        "variants": {
            "compact_selector": compact,
            "preprocessed_output_anchor": anchor,
        },
        "comparisons": {
            "anchor_vs_compact_selector": {
                "status": "NO_GO_ANCHOR_SMALLER_TRACE_BUT_LARGER_TYPED_PROOF",
                "typed_delta_bytes": typed_delta_vs_compact,
                "typed_ratio": ratio(anchor["typed_size_estimate_bytes"], compact["typed_size_estimate_bytes"]),
                "json_delta_bytes": json_delta_vs_compact,
                "json_ratio": ratio(anchor["proof_json_size_bytes"], compact["proof_json_size_bytes"]),
                "trace_cell_reduction": trace_cell_reduction,
                "group_deltas_bytes": group_deltas,
                "proof_size_improvement_claimed": False,
            },
            "anchor_vs_two_proof_frontier": {
                "status": "NO_GO_TYPED_TWO_PROOF_FRONTIER_NOT_BEATEN",
                "two_proof_frontier_typed_bytes": TWO_PROOF_FRONTIER_TYPED_BYTES,
                "typed_delta_bytes": anchor["typed_size_estimate_bytes"] - TWO_PROOF_FRONTIER_TYPED_BYTES,
                "typed_ratio": ratio(anchor["typed_size_estimate_bytes"], TWO_PROOF_FRONTIER_TYPED_BYTES),
                "two_proof_frontier_json_bytes": TWO_PROOF_FRONTIER_JSON_BYTES,
                "json_delta_bytes": anchor["proof_json_size_bytes"] - TWO_PROOF_FRONTIER_JSON_BYTES,
                "json_ratio": ratio(anchor["proof_json_size_bytes"], TWO_PROOF_FRONTIER_JSON_BYTES),
                "frontier_win_claimed": False,
            },
            "nanozk_boundary": {
                "status": "NO_GO_NOT_NANOZK_COMPARABLE",
                "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
                "anchor_typed_gap_to_nanozk_reported_bytes": anchor["typed_size_estimate_bytes"]
                - NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
                "matched_workload_or_object_class": False,
                "proof_size_win_claimed": False,
            },
            "zero_column_adapter_boundary": {
                "status": "NO_GO_ZERO_BASE_COLUMN_COMPONENT_UNSUPPORTED_BY_CURRENT_STWO_COMPONENT_PATH",
                "zero_column_adapter_supported": False,
                "fallback_checked": "one output-q8 base anchor plus source-backed fixed preprocessed columns",
            },
        },
        "summary": {
            "compact_typed_bytes": compact["typed_size_estimate_bytes"],
            "anchor_typed_bytes": anchor["typed_size_estimate_bytes"],
            "anchor_typed_delta_vs_compact_bytes": typed_delta_vs_compact,
            "anchor_typed_delta_vs_two_proof_frontier_bytes": anchor["typed_size_estimate_bytes"]
            - TWO_PROOF_FRONTIER_TYPED_BYTES,
            "compact_json_bytes": compact["proof_json_size_bytes"],
            "anchor_json_bytes": anchor["proof_json_size_bytes"],
            "anchor_json_delta_vs_compact_bytes": json_delta_vs_compact,
            "anchor_json_delta_vs_two_proof_frontier_bytes": anchor["proof_json_size_bytes"]
            - TWO_PROOF_FRONTIER_JSON_BYTES,
            "compact_trace_cells": compact["adapter_trace_cells"],
            "anchor_trace_cells": anchor["adapter_trace_cells"],
            "anchor_trace_cell_reduction_vs_compact": trace_cell_reduction,
        },
        "interpretation": {
            "human_read": (
                "the one-column output-anchor adapter removes 896 adapter base-trace cells but increases typed "
                "proof accounting by 892 bytes versus the compact selector, because the opening/decommitment "
                "shape gets worse"
            ),
            "promotion_status": "NO_GO_FOR_FRONTIER_REPLACEMENT_GO_FOR_PROOF_SHAPE_EVIDENCE",
            "next_attack": (
                "optimize transcript shape or fuse the adapter constraints into an existing component boundary "
                "instead of only shrinking adapter base columns"
            ),
        },
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
        "payload_commitment": "",
    }
    refresh_payload_commitment(payload)
    return payload


def build_payload(context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = build_context() if context is None else context
    payload = build_payload_no_mutations(context)
    payload["mutation_inventory"] = {"cases": list(MUTATION_NAMES)}
    payload["mutation_result"] = mutation_result_placeholder()
    refresh_payload_commitment(payload)
    validate_payload_core(payload, context=context)
    payload["mutation_result"] = mutation_result(payload, context)
    refresh_payload_commitment(payload)
    validate_payload(payload, context=context)
    return payload


def validate_payload_core(payload: dict[str, Any], *, context: dict[str, Any] | None = None) -> None:
    context = build_context() if context is None else context
    if set(payload) != FINAL_KEYS:
        raise PreprocessedOutputAnchorFrontierError("top-level key drift")
    expected = build_payload_no_mutations(context)
    for key in CORE_KEYS - {"payload_commitment"}:
        if payload.get(key) != expected.get(key):
            raise PreprocessedOutputAnchorFrontierError(f"{key} drift")
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise PreprocessedOutputAnchorFrontierError("payload_commitment drift")
    if payload.get("mutation_inventory") != {"cases": list(MUTATION_NAMES)}:
        raise PreprocessedOutputAnchorFrontierError("mutation inventory drift")


def validate_payload(payload: dict[str, Any], *, context: dict[str, Any] | None = None) -> None:
    context = build_context() if context is None else context
    validate_payload_core(payload, context=context)
    mutation = _dict(payload.get("mutation_result"), "mutation result")
    cases = _list(mutation.get("cases"), "mutation cases")
    if [case.get("name") for case in cases] != list(MUTATION_NAMES):
        raise PreprocessedOutputAnchorFrontierError("mutation inventory drift")
    if not all(case.get("rejected") is True for case in cases):
        raise PreprocessedOutputAnchorFrontierError("mutation rejection drift")
    expected_mutation = mutation_result(payload, context)
    if payload.get("mutation_result") != expected_mutation:
        raise PreprocessedOutputAnchorFrontierError("mutation result drift")


def mutation_result_placeholder() -> dict[str, Any]:
    return {"cases": [{"name": name, "rejected": True, "reason": "placeholder"} for name in MUTATION_NAMES]}


def mutation_result(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    cases = []
    for name, mutator in mutation_cases():
        candidate = copy.deepcopy(payload)
        mutator(candidate)
        try:
            validate_payload_core(candidate, context=context)
        except PreprocessedOutputAnchorFrontierError as err:
            cases.append({"name": name, "rejected": True, "reason": str(err)})
        else:
            cases.append({"name": name, "rejected": False, "reason": "mutation accepted"})
    return {"cases": cases}


def mutation_cases() -> list[tuple[str, Callable[[dict[str, Any]], None]]]:
    return [
        ("anchor_typed_bytes_drift", lambda p: p["summary"].__setitem__("anchor_typed_bytes", 40_700)),
        ("compact_typed_bytes_drift", lambda p: p["summary"].__setitem__("compact_typed_bytes", 40_811)),
        (
            "anchor_mode_relabeling",
            lambda p: p["variants"]["preprocessed_output_anchor"].__setitem__(
                "adapter_mode", "compact_base_referenced_fixed_v1"
            ),
        ),
        (
            "frontier_win_overclaim",
            lambda p: p["comparisons"]["anchor_vs_two_proof_frontier"].__setitem__("frontier_win_claimed", True),
        ),
        (
            "nanozk_overclaim",
            lambda p: p["comparisons"]["nanozk_boundary"].__setitem__("proof_size_win_claimed", True),
        ),
        (
            "zero_column_support_overclaim",
            lambda p: p["comparisons"]["zero_column_adapter_boundary"].__setitem__(
                "zero_column_adapter_supported", True
            ),
        ),
        (
            "source_artifact_hash_drift",
            lambda p: p["source_artifacts"][0].__setitem__("sha256", "1" * 64),
        ),
        ("payload_commitment_drift", lambda p: p.__setitem__("payload_commitment", "blake2b-256:" + "2" * 64)),
    ]


def to_tsv(payload: dict[str, Any], context: dict[str, Any]) -> str:
    validate_payload(payload, context=context)
    row = {
        "decision": payload["decision"],
        "result": payload["result"],
        **payload["summary"],
    }
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=TSV_COLUMNS, extrasaction="ignore", delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerow(row)
    return output.getvalue()


def write_bytes_atomic(path: pathlib.Path, data: bytes, label: str) -> None:
    try:
        route_gate.attribution_gate.write_bytes_atomic(path, data, label)
    except route_gate.attribution_gate.MlpFusionAttributionError as err:
        raise PreprocessedOutputAnchorFrontierError(str(err)) from err


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    args = parser.parse_args()
    context = build_context()
    payload = build_payload(context)
    if args.write_json:
        write_bytes_atomic(
            args.write_json,
            (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8"),
            "preprocessed output-anchor adapter frontier JSON",
        )
    if args.write_tsv:
        write_bytes_atomic(
            args.write_tsv,
            to_tsv(payload, context).encode("utf-8"),
            "preprocessed output-anchor adapter frontier TSV",
        )
    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "result": RESULT,
                "anchor_typed_bytes": payload["summary"]["anchor_typed_bytes"],
                "anchor_typed_delta_vs_compact_bytes": payload["summary"][
                    "anchor_typed_delta_vs_compact_bytes"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
