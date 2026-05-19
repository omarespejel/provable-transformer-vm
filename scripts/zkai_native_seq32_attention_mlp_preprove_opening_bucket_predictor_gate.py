#!/usr/bin/env python3.10
"""Gate a pre-prove opening-bucket predictor for seq32 attention+MLP labels."""

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
        "zkai_native_seq32_attention_mlp_preprove_opening_bucket_predictor_gate requires Python 3.10+"
    )

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import zkai_native_seq32_attention_mlp_adjacent_label_seed_sweep_gate as seed_gate
from scripts import zkai_native_seq32_attention_mlp_adjacent_probe_b_bucket_attribution_gate as bucket_gate


EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
RUST_SOURCE_PATH = ROOT / "src" / "stwo_backend" / "native_seq32_attention_mlp_single_proof.rs"
CLI_SOURCE_PATH = ROOT / "src" / "bin" / "zkai_native_seq32_attention_mlp_single_proof.rs"
ACCOUNTING_PATH = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-adjacent-label-seed-sweep-accounting-2026-05.json"
JSON_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-preprove-opening-bucket-predictor-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-preprove-opening-bucket-predictor-2026-05.tsv"

SCHEMA = "zkai-native-seq32-attention-mlp-preprove-opening-bucket-predictor-gate-v1"
DECISION = "NO_GO_SOURCE_VISIBLE_PREPROVE_INVENTORY_DOES_NOT_PREDICT_PROBE_B_BUCKET"
RESULT = "ALL_ADJACENT_ROWS_SHARE_ONE_STRUCTURAL_PREPROVE_SIGNATURE_BUT_FINAL_PATH_OPENING_BUCKETS_SPAN_4624_TYPED_BYTES"
CLAIM_BOUNDARY = (
    "SOURCE_VISIBLE_PREPROVE_INPUT_INVENTORY_ONLY;"
    "FINAL_ACCOUNTING_JOIN_USED_ONLY_FOR_EVALUATION;"
    "NO_PROOF_BYTES_OR_ACCOUNTING_BYTES_ALLOWED_IN_PREDICTOR;"
    "NOT_A_PRODUCTION_LABEL_POLICY_NOT_A_NANOZK_COMPARISON"
)
ISSUE_HINT = "https://github.com/omarespejel/provable-transformer-vm/issues/695"
PAYLOAD_DOMAIN = "ptvm:zkai:native-seq32-attention-mlp-preprove-opening-bucket-predictor:v1"

MAX_SOURCE_ARTIFACT_BYTES = 768 * 1024
MAX_INPUT_JSON_BYTES = 4 * 1024 * 1024
MAX_ACCOUNTING_JSON_BYTES = 2 * 1024 * 1024
DETERMINISTIC_TEMP_ATTEMPTS = 16

EXPECTED_RUST_SOURCE_SHA256 = bucket_gate.EXPECTED_RUST_SOURCE_SHA256
EXPECTED_CLI_SOURCE_SHA256 = bucket_gate.EXPECTED_CLI_SOURCE_SHA256
EXPECTED_ACCOUNTING_SHA256 = bucket_gate.EXPECTED_ACCOUNTING_SHA256

PATH_OPENING_GROUPS = bucket_gate.PATH_OPENING_GROUPS
VALUE_GROUPS = bucket_gate.VALUE_GROUPS
GROUPS = bucket_gate.GROUPS
EXPECTED_ROWS = seed_gate.EXPECTED_ROWS

ADJACENT_PROBE_B_FRONTIER_TYPED_BYTES = bucket_gate.ADJACENT_PROBE_B_FRONTIER_TYPED_BYTES
ADJACENT_PROBE_B_FRONTIER_JSON_BYTES = bucket_gate.ADJACENT_PROBE_B_FRONTIER_JSON_BYTES
BEST_BUCKET_VARIANT_ID = "adjacent_label_probe_b"
BEST_PRE_REGISTERED_SEED_ID = "adjacent_seed_02"
BEST_BUCKET_PATH_OPENING_BYTES = 16_560
BEST_PRE_REGISTERED_SEED_PATH_OPENING_BYTES = 19_296
FIXED_ADJACENT_PATH_OPENING_BYTES = 21_184
VALUE_BYTES = 20_924
PATH_OPENING_SPAN_BYTES = 4_624
DISTINCT_FINAL_BUCKETS = 5

STRUCTURAL_FEATURE_KEYS = (
    "schema",
    "decision",
    "route_id",
    "target_id",
    "verifier_domain",
    "attention_proof_version",
    "mlp_proof_version",
    "adapter_status",
    "adapter_row_count",
    "adapter_value_columns",
    "adapter_remainder_bit_columns",
    "adapter_trace_cells",
    "pcs_lifting_log_size",
    "attention_lookup_claims",
    "attention_table_rows",
    "mlp_row_count",
    "current_two_proof_frontier_typed_bytes",
    "current_attention_fused_typed_bytes",
    "current_derived_mlp_fused_typed_bytes",
    "nanozk_reported_d128_block_proof_bytes",
)
ROW_IDENTITY_KEYS = (
    "adapter_mode",
    "statement_commitment",
    "public_instance_commitment",
    "proof_native_parameter_commitment",
)
PREPROVE_ROW_KEYS = {
    "variant_id",
    "adapter_mode",
    "family",
    "policy_status",
    "input_path",
    "input_sha256",
    "source_visible_scope",
    "structural_features",
    "structural_signature",
    "row_identity_fields",
    "row_identity_signature",
}
FINAL_JOIN_ROW_KEYS = {
    "variant_id",
    "envelope_path",
    "typed_bytes",
    "json_proof_bytes",
    "path_opening_bytes",
    "value_bytes",
    "groups",
    "record_stream_sha256",
    "envelope_sha256",
    "proof_sha256",
}
SOURCE_ARTIFACT_KEYS = {"id", "path", "sha256", "size_bytes"}
PREDICTOR_ASSESSMENT_KEYS = {
    "source_exposed_bucket_predictor",
    "best_bucket_variant_id",
    "best_bucket_path_opening_bytes",
    "best_pre_registered_seed_id",
    "best_pre_registered_seed_path_opening_bytes",
    "gap_vs_best_seed_path_opening_bytes",
    "path_opening_span_bytes",
    "value_bytes_constant",
    "distinct_final_path_opening_buckets",
    "unique_preprove_structural_signatures",
    "rows_sharing_preprove_structural_signature",
    "row_identity_signatures_unique",
    "candidate_predictors",
    "required_next_artifact",
}
MUTATION_RESULT_KEYS = {"all_mutations_rejected", "mutations_rejected", "mutation_names", "cases"}
MUTATION_CASE_KEYS = {"name", "rejected", "error"}

VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_native_seq32_attention_mlp_preprove_opening_bucket_predictor_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-preprove-opening-bucket-predictor-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-preprove-opening-bucket-predictor-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_preprove_opening_bucket_predictor_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_preprove_opening_bucket_predictor_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_preprove_opening_bucket_predictor_gate",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

NON_CLAIMS = (
    "not a source-exposed predictor for the probe-B opening bucket",
    "not a new proof-size frontier",
    "not a production label-selection policy",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not a full transformer block proof",
    "not exact real-valued Softmax",
    "not timing evidence",
    "not production-ready zkML",
)

EXPECTED_INTERPRETATION = {
    "human_read": (
        "The pre-prove inputs can identify which label is being tried, but they do not expose why "
        "probe B lands in the smaller opening bucket. All checked adjacent rows share the same "
        "source-visible structural signature before proof generation."
    ),
    "mechanism_read": (
        "The final difference is still real and path-opening dominated, but this gate rejects "
        "promoting statement or parameter hashes into a predictor. Those hashes are row identities; "
        "without a query-opening sampler they are only a post-hoc lookup table."
    ),
    "next_experiment": (
        "Build a deeper dry-run transcript/query sampler that emits Fiat-Shamir query/opening "
        "positions after source commitments but before final proof serialization."
    ),
}

MUTATION_NAMES = (
    "decision_drift",
    "claim_boundary_overclaim",
    "rust_source_digest_drift",
    "cli_source_digest_drift",
    "accounting_digest_drift",
    "preprove_row_removed",
    "final_join_row_removed",
    "preprove_final_accounting_leak",
    "source_predictor_promotion",
    "structural_signature_unique_drift",
    "row_identity_promoted_to_predictor",
    "bucket_span_drift",
    "record_stream_erasure",
    "validation_command_drift",
    "removed_non_claim",
    "payload_commitment_drift",
)


class PreproveOpeningBucketPredictorGateError(Exception):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    except (TypeError, ValueError) as err:
        raise PreproveOpeningBucketPredictorGateError(f"non-canonical JSON value: {err}") from err


def blake2b_commitment(domain: str, value: Any) -> str:
    digest = hashlib.blake2b(
        domain.encode() + b"\0" + canonical_json_bytes(value),
        digest_size=32,
    ).hexdigest()
    return f"blake2b-256:{digest}"


def payload_commitment(payload: dict[str, Any]) -> str:
    item = copy.deepcopy(payload)
    item.pop("payload_commitment", None)
    return blake2b_commitment(PAYLOAD_DOMAIN, item)


def read_bounded_repo_file(path: pathlib.Path, label: str, max_bytes: int) -> bytes:
    root = ROOT.resolve()
    candidate = pathlib.Path(os.path.abspath(path if path.is_absolute() else ROOT / path))
    try:
        relative = candidate.relative_to(root)
    except ValueError as err:
        raise PreproveOpeningBucketPredictorGateError(f"{label} escapes repo root") from err
    current = root
    try:
        for part in relative.parts:
            current = current / part
            mode = current.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise PreproveOpeningBucketPredictorGateError(f"{label} must not traverse symlinks")
        fd = os.open(candidate, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            opened_stat = os.fstat(fd)
            if not stat.S_ISREG(opened_stat.st_mode):
                raise PreproveOpeningBucketPredictorGateError(f"{label} is not a regular file")
            if opened_stat.st_size > max_bytes:
                raise PreproveOpeningBucketPredictorGateError(
                    f"{label} exceeds max size: got {opened_stat.st_size} bytes, limit {max_bytes} bytes"
                )
            with os.fdopen(fd, "rb") as handle:
                fd = None
                raw = handle.read(max_bytes + 1)
        finally:
            if fd is not None:
                os.close(fd)
    except OSError as err:
        raise PreproveOpeningBucketPredictorGateError(f"failed to read {label}: {err}") from err
    if len(raw) > max_bytes:
        raise PreproveOpeningBucketPredictorGateError(
            f"{label} exceeds max size: got at least {len(raw)} bytes, limit {max_bytes} bytes"
        )
    return raw


def read_json_object(path: pathlib.Path, label: str, max_bytes: int) -> tuple[dict[str, Any], bytes]:
    raw = read_bounded_repo_file(path, label, max_bytes)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as err:
        raise PreproveOpeningBucketPredictorGateError(f"{label} is not valid JSON: {err}") from err
    if not isinstance(value, dict):
        raise PreproveOpeningBucketPredictorGateError(f"{label} must be a JSON object")
    return value, raw


def source_artifact(path: pathlib.Path, artifact_id: str, expected_sha: str) -> dict[str, Any]:
    raw = read_bounded_repo_file(path, artifact_id, MAX_SOURCE_ARTIFACT_BYTES)
    digest = sha256_bytes(raw)
    if digest != expected_sha:
        raise PreproveOpeningBucketPredictorGateError(f"{artifact_id} source digest drift")
    return {
        "id": artifact_id,
        "path": str(path.relative_to(ROOT)),
        "sha256": digest,
        "size_bytes": len(raw),
    }


def input_path_for_row(expected: dict[str, Any]) -> pathlib.Path:
    envelope_path = expected["path"]
    if not isinstance(envelope_path, str) or not envelope_path.endswith(".envelope.json"):
        raise PreproveOpeningBucketPredictorGateError("expected row envelope path drift")
    return EVIDENCE_DIR / envelope_path.replace(".envelope.json", ".input.json")


def require_str(value: dict[str, Any], key: str, label: str) -> str:
    item = value.get(key)
    if not isinstance(item, str):
        raise PreproveOpeningBucketPredictorGateError(f"{label}.{key} missing")
    return item


def require_int(value: dict[str, Any], key: str, label: str) -> int:
    item = value.get(key)
    if not isinstance(item, int) or isinstance(item, bool):
        raise PreproveOpeningBucketPredictorGateError(f"{label}.{key} missing")
    return item


def preprove_inventory_row(expected: dict[str, Any]) -> dict[str, Any]:
    variant_id = require_str(expected, "variant_id", "expected row")
    input_path = input_path_for_row(expected)
    input_json, input_raw = read_json_object(input_path, f"{variant_id} input", MAX_INPUT_JSON_BYTES)
    adapter_mode = require_str(input_json, "adapter_mode", variant_id)
    if adapter_mode != expected["adapter_mode"]:
        raise PreproveOpeningBucketPredictorGateError(f"{variant_id} input adapter mode drift")
    structural_features: dict[str, Any] = {}
    for key in STRUCTURAL_FEATURE_KEYS:
        if key.endswith("_bytes") or key.endswith("_count") or key in {
            "adapter_value_columns",
            "adapter_remainder_bit_columns",
            "adapter_trace_cells",
            "pcs_lifting_log_size",
            "attention_lookup_claims",
            "attention_table_rows",
            "mlp_row_count",
            "current_two_proof_frontier_typed_bytes",
            "current_attention_fused_typed_bytes",
            "current_derived_mlp_fused_typed_bytes",
            "nanozk_reported_d128_block_proof_bytes",
        }:
            structural_features[key] = require_int(input_json, key, variant_id)
        else:
            structural_features[key] = require_str(input_json, key, variant_id)
    row_identity = {key: require_str(input_json, key, variant_id) for key in ROW_IDENTITY_KEYS}
    return {
        "variant_id": variant_id,
        "adapter_mode": adapter_mode,
        "family": require_str(expected, "family", "expected row"),
        "policy_status": require_str(expected, "policy_status", "expected row"),
        "input_path": str(input_path.relative_to(ROOT)),
        "input_sha256": sha256_bytes(input_raw),
        "source_visible_scope": "input_json_before_prove_no_envelope_no_accounting_no_proof_bytes",
        "structural_features": structural_features,
        "structural_signature": blake2b_commitment(
            "ptvm:zkai:preprove-structural-signature:v1",
            structural_features,
        ),
        "row_identity_fields": row_identity,
        "row_identity_signature": blake2b_commitment(
            "ptvm:zkai:preprove-row-identity-signature:v1",
            row_identity,
        ),
    }


def accounting_rows_by_path() -> dict[str, dict[str, Any]]:
    data, raw = read_json_object(ACCOUNTING_PATH, "adjacent seed-sweep accounting", MAX_ACCOUNTING_JSON_BYTES)
    if sha256_bytes(raw) != EXPECTED_ACCOUNTING_SHA256:
        raise PreproveOpeningBucketPredictorGateError("adjacent seed-sweep accounting digest drift")
    raw_rows = data.get("rows")
    if not isinstance(raw_rows, list):
        raise PreproveOpeningBucketPredictorGateError("accounting rows must be a JSON array")
    rows: dict[str, dict[str, Any]] = {}
    for row in raw_rows:
        if not isinstance(row, dict):
            raise PreproveOpeningBucketPredictorGateError("accounting row must be a JSON object")
        path = row.get("evidence_relative_path")
        if not isinstance(path, str):
            raise PreproveOpeningBucketPredictorGateError("accounting row path missing")
        if path in rows:
            raise PreproveOpeningBucketPredictorGateError(f"duplicate accounting row: {path}")
        rows[path] = row
    return rows


def final_accounting_join_row(expected: dict[str, Any], accounting_by_path: dict[str, dict[str, Any]]) -> dict[str, Any]:
    variant_id = require_str(expected, "variant_id", "expected row")
    path = require_str(expected, "path", "expected row")
    row = accounting_by_path.get(path)
    if row is None:
        raise PreproveOpeningBucketPredictorGateError(f"{variant_id} accounting row missing")
    local = row.get("local_binary_accounting")
    if not isinstance(local, dict):
        raise PreproveOpeningBucketPredictorGateError(f"{variant_id} local accounting missing")
    groups = local.get("stwo_grouped_breakdown")
    if not isinstance(groups, dict):
        raise PreproveOpeningBucketPredictorGateError(f"{variant_id} grouped breakdown missing")
    normalized_groups: dict[str, int] = {}
    for group in GROUPS:
        value = groups.get(group)
        if not isinstance(value, int) or isinstance(value, bool):
            raise PreproveOpeningBucketPredictorGateError(f"{variant_id} group {group} missing")
        normalized_groups[group] = value
    typed_bytes = local.get("typed_size_estimate_bytes")
    if not isinstance(typed_bytes, int) or isinstance(typed_bytes, bool):
        raise PreproveOpeningBucketPredictorGateError(f"{variant_id} typed bytes missing")
    json_proof_bytes = row.get("proof_json_size_bytes")
    if not isinstance(json_proof_bytes, int) or isinstance(json_proof_bytes, bool):
        raise PreproveOpeningBucketPredictorGateError(f"{variant_id} JSON proof bytes missing")
    if typed_bytes != expected["typed_bytes"]:
        raise PreproveOpeningBucketPredictorGateError(f"{variant_id} typed byte drift")
    if json_proof_bytes != expected["json_proof_bytes"]:
        raise PreproveOpeningBucketPredictorGateError(f"{variant_id} JSON proof byte drift")
    path_opening_bytes = sum(normalized_groups[group] for group in PATH_OPENING_GROUPS)
    value_bytes = sum(normalized_groups[group] for group in VALUE_GROUPS)
    if typed_bytes != normalized_groups["fixed_overhead"] + path_opening_bytes + value_bytes:
        raise PreproveOpeningBucketPredictorGateError(f"{variant_id} grouped sum drift")
    record_stream_sha256 = local.get("record_stream_sha256")
    if not isinstance(record_stream_sha256, str):
        raise PreproveOpeningBucketPredictorGateError(f"{variant_id} record stream digest missing")
    return {
        "variant_id": variant_id,
        "envelope_path": path,
        "typed_bytes": typed_bytes,
        "json_proof_bytes": json_proof_bytes,
        "path_opening_bytes": path_opening_bytes,
        "value_bytes": value_bytes,
        "groups": normalized_groups,
        "record_stream_sha256": record_stream_sha256,
        "envelope_sha256": require_str(row, "envelope_sha256", variant_id),
        "proof_sha256": require_str(row, "proof_sha256", variant_id),
    }


def build_preprove_rows() -> list[dict[str, Any]]:
    return [preprove_inventory_row(expected) for expected in EXPECTED_ROWS]


def build_final_join_rows() -> list[dict[str, Any]]:
    accounting_by_path = accounting_rows_by_path()
    return [final_accounting_join_row(expected, accounting_by_path) for expected in EXPECTED_ROWS]


def predictor_assessment(
    preprove_rows: list[dict[str, Any]],
    final_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    structural_signatures = {row["structural_signature"] for row in preprove_rows}
    row_identity_signatures = {row["row_identity_signature"] for row in preprove_rows}
    path_opening_values = [row["path_opening_bytes"] for row in final_rows]
    value_values = {row["value_bytes"] for row in final_rows}
    best = min(final_rows, key=lambda row: row["path_opening_bytes"])
    seed_02 = next((row for row in final_rows if row["variant_id"] == BEST_PRE_REGISTERED_SEED_ID), None)
    if seed_02 is None:
        raise PreproveOpeningBucketPredictorGateError("adjacent_seed_02 final accounting row missing")
    if best["variant_id"] != BEST_BUCKET_VARIANT_ID:
        raise PreproveOpeningBucketPredictorGateError("best bucket variant drift")
    if best["path_opening_bytes"] != BEST_BUCKET_PATH_OPENING_BYTES:
        raise PreproveOpeningBucketPredictorGateError("best bucket path-opening drift")
    if seed_02["path_opening_bytes"] != BEST_PRE_REGISTERED_SEED_PATH_OPENING_BYTES:
        raise PreproveOpeningBucketPredictorGateError("seed 02 path-opening drift")
    if max(path_opening_values) - min(path_opening_values) != PATH_OPENING_SPAN_BYTES:
        raise PreproveOpeningBucketPredictorGateError("path-opening span drift")
    if value_values != {VALUE_BYTES}:
        raise PreproveOpeningBucketPredictorGateError("value byte constancy drift")
    return {
        "source_exposed_bucket_predictor": False,
        "best_bucket_variant_id": best["variant_id"],
        "best_bucket_path_opening_bytes": best["path_opening_bytes"],
        "best_pre_registered_seed_id": seed_02["variant_id"],
        "best_pre_registered_seed_path_opening_bytes": seed_02["path_opening_bytes"],
        "gap_vs_best_seed_path_opening_bytes": seed_02["path_opening_bytes"] - best["path_opening_bytes"],
        "path_opening_span_bytes": max(path_opening_values) - min(path_opening_values),
        "value_bytes_constant": VALUE_BYTES,
        "distinct_final_path_opening_buckets": len(set(path_opening_values)),
        "unique_preprove_structural_signatures": len(structural_signatures),
        "rows_sharing_preprove_structural_signature": len(preprove_rows),
        "row_identity_signatures_unique": len(row_identity_signatures) == len(preprove_rows),
        "candidate_predictors": [
            {
                "candidate": "source_visible_structural_signature",
                "status": "NO_GO_COLLIDES_ACROSS_DISTINCT_FINAL_BUCKETS",
                "unique_preprove_values": len(structural_signatures),
                "distinct_final_buckets_under_same_signature": len(set(path_opening_values)),
                "reason": "all checked adjacent rows share one structural signature before proving",
            },
            {
                "candidate": "adapter_mode_or_statement_commitment_lookup",
                "status": "REJECTED_AS_POST_HOC_ROW_IDENTITY_LOOKUP",
                "unique_preprove_values": len(row_identity_signatures),
                "distinct_final_buckets_under_same_signature": 1,
                "reason": "identifies a row but does not explain or predict the opening bucket without learned final accounting",
            },
            {
                "candidate": "final_record_stream_or_grouped_accounting",
                "status": "REJECTED_AS_FINAL_PROOF_ACCOUNTING_LEAKAGE",
                "unique_preprove_values": 0,
                "distinct_final_buckets_under_same_signature": 0,
                "reason": "uses the artifact the predictor is supposed to precede",
            },
        ],
        "required_next_artifact": "dry_run_query_opening_sampler_before_final_proof_serialization",
    }


def build_payload_without_mutations() -> dict[str, Any]:
    preprove_rows = build_preprove_rows()
    final_rows = build_final_join_rows()
    return {
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
        "preprove_inventory_policy": {
            "prediction_scope": "input_json_and_source_visible_statement_fields_before_prove",
            "proof_envelope_allowed_for_prediction": False,
            "final_accounting_allowed_for_prediction": False,
            "final_accounting_allowed_for_evaluation": True,
            "row_identity_hashes_are_predictors": False,
        },
        "preprove_inventory_rows": preprove_rows,
        "final_accounting_join_rows": final_rows,
        "predictor_assessment": predictor_assessment(preprove_rows, final_rows),
        "interpretation": EXPECTED_INTERPRETATION,
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }


def _row(rows: list[dict[str, Any]], variant_id: str) -> dict[str, Any]:
    for row in rows:
        if row["variant_id"] == variant_id:
            return row
    raise PreproveOpeningBucketPredictorGateError(f"missing row: {variant_id}")


def mutation_functions() -> tuple[tuple[str, Callable[[dict[str, Any]], None]], ...]:
    return (
        ("decision_drift", lambda item: item.update({"decision": "GO"})),
        ("claim_boundary_overclaim", lambda item: item.update({"claim_boundary": item["claim_boundary"] + ";PREDICTOR_FOUND"})),
        ("rust_source_digest_drift", lambda item: item["source_artifacts"][0].update({"sha256": "0" * 64})),
        ("cli_source_digest_drift", lambda item: item["source_artifacts"][1].update({"sha256": "0" * 64})),
        ("accounting_digest_drift", lambda item: item["source_artifacts"][2].update({"sha256": "0" * 64})),
        ("preprove_row_removed", lambda item: item["preprove_inventory_rows"].pop()),
        ("final_join_row_removed", lambda item: item["final_accounting_join_rows"].pop()),
        ("preprove_final_accounting_leak", lambda item: _row(item["preprove_inventory_rows"], BEST_BUCKET_VARIANT_ID).update({"path_opening_bytes": BEST_BUCKET_PATH_OPENING_BYTES})),
        ("source_predictor_promotion", lambda item: item["predictor_assessment"].update({"source_exposed_bucket_predictor": True})),
        ("structural_signature_unique_drift", lambda item: item["predictor_assessment"].update({"unique_preprove_structural_signatures": 9})),
        ("row_identity_promoted_to_predictor", lambda item: item["preprove_inventory_policy"].update({"row_identity_hashes_are_predictors": True})),
        ("bucket_span_drift", lambda item: item["predictor_assessment"].update({"path_opening_span_bytes": 0})),
        ("record_stream_erasure", lambda item: _row(item["final_accounting_join_rows"], BEST_BUCKET_VARIANT_ID).update({"record_stream_sha256": ""})),
        ("validation_command_drift", lambda item: item["validation_commands"].append("echo unchecked")),
        ("removed_non_claim", lambda item: item["non_claims"].remove("not a source-exposed predictor for the probe-B opening bucket")),
        ("payload_commitment_drift", lambda item: item.update({"payload_commitment": "blake2b-256:" + "0" * 64})),
    )


def mutation_function_names() -> tuple[str, ...]:
    return tuple(name for name, _ in mutation_functions())


def ensure_mutation_inventory() -> None:
    actual = mutation_function_names()
    if actual != MUTATION_NAMES:
        raise PreproveOpeningBucketPredictorGateError(
            f"mutation function inventory drift: expected {MUTATION_NAMES!r}, got {actual!r}"
        )


ensure_mutation_inventory()


def mutation_result(payload: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    ensure_mutation_inventory()
    cases = []
    expected_core = copy.deepcopy(expected)
    for name, mutate in mutation_functions():
        item = copy.deepcopy(payload)
        item.pop("payload_commitment", None)
        item["mutation_result"] = {"all_mutations_rejected": True, "mutations_rejected": 0, "cases": []}
        mutate(item)
        if name != "payload_commitment_drift":
            item["payload_commitment"] = payload_commitment(item)
        try:
            validate_payload_core(item, expected_core)
            if item.get("payload_commitment") != payload_commitment(item):
                raise PreproveOpeningBucketPredictorGateError("payload commitment drift")
        except PreproveOpeningBucketPredictorGateError as error:
            cases.append({"name": name, "rejected": True, "error": str(error)})
        else:
            cases.append({"name": name, "rejected": False, "error": ""})
    return {
        "all_mutations_rejected": all(case["rejected"] for case in cases),
        "mutations_rejected": sum(1 for case in cases if case["rejected"]),
        "mutation_names": list(MUTATION_NAMES),
        "cases": cases,
    }


def build_payload() -> dict[str, Any]:
    expected = build_payload_without_mutations()
    payload = copy.deepcopy(expected)
    payload["mutation_result"] = mutation_result(payload, expected)
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload, expected)
    return payload


def validate_payload(payload: dict[str, Any], expected: dict[str, Any] | None = None) -> None:
    ensure_mutation_inventory()
    expected_payload = expected if expected is not None else build_payload_without_mutations()
    validate_payload_core(payload, expected_payload)
    mutation = payload.get("mutation_result")
    if not isinstance(mutation, dict):
        raise PreproveOpeningBucketPredictorGateError("mutation_result missing")
    if set(mutation) != MUTATION_RESULT_KEYS:
        raise PreproveOpeningBucketPredictorGateError("mutation_result schema drift")
    if mutation.get("mutation_names") != list(MUTATION_NAMES):
        raise PreproveOpeningBucketPredictorGateError("mutation inventory drift")
    if mutation.get("mutations_rejected") != len(MUTATION_NAMES) or not mutation.get("all_mutations_rejected"):
        raise PreproveOpeningBucketPredictorGateError("mutation rejection drift")
    cases = mutation.get("cases")
    if not isinstance(cases, list) or len(cases) != len(MUTATION_NAMES):
        raise PreproveOpeningBucketPredictorGateError("mutation cases drift")
    for case in cases:
        if not isinstance(case, dict) or set(case) != MUTATION_CASE_KEYS:
            raise PreproveOpeningBucketPredictorGateError("mutation case schema drift")
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise PreproveOpeningBucketPredictorGateError("payload commitment drift")


def validate_payload_core(payload: dict[str, Any], expected: dict[str, Any]) -> None:
    for key, value in {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "issue_hint": ISSUE_HINT,
    }.items():
        if payload.get(key) != value:
            raise PreproveOpeningBucketPredictorGateError(f"{key} drift")
    if "PREDICTOR_FOUND" in str(payload.get("claim_boundary")).split(";"):
        raise PreproveOpeningBucketPredictorGateError("claim_boundary drift")
    for key in (
        "source_artifacts",
        "preprove_inventory_policy",
        "preprove_inventory_rows",
        "final_accounting_join_rows",
        "predictor_assessment",
        "interpretation",
        "non_claims",
        "validation_commands",
    ):
        if payload.get(key) != expected[key]:
            raise PreproveOpeningBucketPredictorGateError(f"{key} drift")
    if payload["predictor_assessment"]["source_exposed_bucket_predictor"]:
        raise PreproveOpeningBucketPredictorGateError("predictor promotion drift")
    if payload["preprove_inventory_policy"]["row_identity_hashes_are_predictors"]:
        raise PreproveOpeningBucketPredictorGateError("row identity predictor drift")
    if payload["predictor_assessment"]["unique_preprove_structural_signatures"] != 1:
        raise PreproveOpeningBucketPredictorGateError("structural signature drift")
    if payload["predictor_assessment"]["distinct_final_path_opening_buckets"] != DISTINCT_FINAL_BUCKETS:
        raise PreproveOpeningBucketPredictorGateError("bucket count drift")
    for artifact in payload["source_artifacts"]:
        if not isinstance(artifact, dict) or set(artifact) != SOURCE_ARTIFACT_KEYS:
            raise PreproveOpeningBucketPredictorGateError("source artifact schema drift")
    for row in payload["preprove_inventory_rows"]:
        if not isinstance(row, dict) or set(row) != PREPROVE_ROW_KEYS:
            raise PreproveOpeningBucketPredictorGateError("preprove row schema drift")
        forbidden = {"typed_bytes", "json_proof_bytes", "path_opening_bytes", "value_bytes", "groups", "record_stream_sha256", "envelope_sha256", "proof_sha256"}
        if forbidden.intersection(row):
            raise PreproveOpeningBucketPredictorGateError("preprove row leaked final accounting")
    for row in payload["final_accounting_join_rows"]:
        if not isinstance(row, dict) or set(row) != FINAL_JOIN_ROW_KEYS:
            raise PreproveOpeningBucketPredictorGateError("final join row schema drift")
        if not isinstance(row["record_stream_sha256"], str) or not row["record_stream_sha256"]:
            raise PreproveOpeningBucketPredictorGateError("final join record stream drift")
    if set(payload["predictor_assessment"]) != PREDICTOR_ASSESSMENT_KEYS:
        raise PreproveOpeningBucketPredictorGateError("predictor assessment schema drift")
    if "not a source-exposed predictor for the probe-B opening bucket" not in payload["non_claims"]:
        raise PreproveOpeningBucketPredictorGateError("non_claims drift")
    if payload["validation_commands"] != list(VALIDATION_COMMANDS):
        raise PreproveOpeningBucketPredictorGateError("validation command drift")


TSV_COLUMNS = (
    "variant_id",
    "adapter_mode",
    "family",
    "policy_status",
    "input_sha256",
    "structural_signature",
    "row_identity_signature",
    "final_typed_bytes",
    "final_path_opening_bytes",
    "final_value_bytes",
    "final_record_stream_sha256",
)


def render_tsv(payload: dict[str, Any]) -> str:
    final_by_id = {row["variant_id"]: row for row in payload["final_accounting_join_rows"]}
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in payload["preprove_inventory_rows"]:
        final = final_by_id[row["variant_id"]]
        writer.writerow(
            {
                "variant_id": row["variant_id"],
                "adapter_mode": row["adapter_mode"],
                "family": row["family"],
                "policy_status": row["policy_status"],
                "input_sha256": row["input_sha256"],
                "structural_signature": row["structural_signature"],
                "row_identity_signature": row["row_identity_signature"],
                "final_typed_bytes": final["typed_bytes"],
                "final_path_opening_bytes": final["path_opening_bytes"],
                "final_value_bytes": final["value_bytes"],
                "final_record_stream_sha256": final["record_stream_sha256"],
            }
        )
    return out.getvalue()


def require_output_path(path: pathlib.Path) -> pathlib.Path:
    target = pathlib.Path(os.path.abspath(path if path.is_absolute() else ROOT / path))
    evidence_root = EVIDENCE_DIR.resolve()
    try:
        relative = target.relative_to(evidence_root)
    except ValueError as err:
        raise PreproveOpeningBucketPredictorGateError("output path must stay inside evidence dir") from err
    current = evidence_root
    for part in relative.parent.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except OSError as err:
            raise PreproveOpeningBucketPredictorGateError(f"output parent must exist: {current}") from err
        if stat.S_ISLNK(mode):
            raise PreproveOpeningBucketPredictorGateError("output path must not traverse symlinks")
        if not stat.S_ISDIR(mode):
            raise PreproveOpeningBucketPredictorGateError(f"output parent must be directory: {current}")
    if target.is_symlink() or (target.exists() and target.is_dir()):
        raise PreproveOpeningBucketPredictorGateError("output path must be a non-symlink file")
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
        raise PreproveOpeningBucketPredictorGateError("could not create deterministic temp output")
    finally:
        os.close(parent_fd)


def write_outputs(json_path: pathlib.Path, tsv_path: pathlib.Path, payload: dict[str, Any]) -> None:
    atomic_write(json_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    atomic_write(tsv_path, render_tsv(payload))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    args = parser.parse_args(argv)
    if (args.write_json is None) != (args.write_tsv is None):
        parser.error("--write-json and --write-tsv must be provided together")
    payload = build_payload()
    if args.write_json is not None and args.write_tsv is not None:
        write_outputs(args.write_json, args.write_tsv, payload)
    print(
        json.dumps(
            {
                "decision": payload["decision"],
                "source_exposed_bucket_predictor": payload["predictor_assessment"][
                    "source_exposed_bucket_predictor"
                ],
                "unique_preprove_structural_signatures": payload["predictor_assessment"][
                    "unique_preprove_structural_signatures"
                ],
                "distinct_final_path_opening_buckets": payload["predictor_assessment"][
                    "distinct_final_path_opening_buckets"
                ],
                "best_bucket_path_opening_bytes": payload["predictor_assessment"][
                    "best_bucket_path_opening_bytes"
                ],
                "gap_vs_best_seed_path_opening_bytes": payload["predictor_assessment"][
                    "gap_vs_best_seed_path_opening_bytes"
                ],
                "mutations_rejected": payload["mutation_result"]["mutations_rejected"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
