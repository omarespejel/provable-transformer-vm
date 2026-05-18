#!/usr/bin/env python3.10
"""Gate the native seq32 attention + d128 MLP single proof object."""

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
    raise RuntimeError("zkai_native_seq32_attention_mlp_single_proof_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"

FRONTIER_GATE = EVIDENCE_DIR / "zkai-seq32-value-compatible-boundary-frontier-2026-05.json"
SINGLE_INPUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-single-proof-2026-05.input.json"
SINGLE_ENVELOPE = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json"
SINGLE_ACCOUNTING = (
    EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-single-proof-binary-accounting-2026-05.json"
)

JSON_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-single-proof-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-single-proof-2026-05.tsv"

SCHEMA = "zkai-native-seq32-attention-mlp-single-proof-gate-v1"
DECISION = "GO_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_OBJECT_BEATS_MATCHED_FRONTIER"
RESULT = "NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_SAVES_5120_TYPED_BYTES_VS_47188_FRONTIER"
ISSUE_HINT = "native-seq32-attention-mlp-single-proof-object"
PAYLOAD_DOMAIN = "ptvm:zkai:native-seq32-attention-mlp-single-proof-gate:v1"
CLAIM_BOUNDARY = (
    "ONE_NATIVE_STWO_PROOF_OBJECT_OVER_TWO_HEAD_SEQ32_FUSED_ATTENTION_PLUS_SEQ32_DERIVED_D128_"
    "RMSNORM_MLP_BEATS_THE_MATCHED_LOCAL_TWO_PROOF_FRONTIER;"
    "NOT_A_NANOZK_WIN_NOT_A_FULL_TRANSFORMER_BLOCK_NOT_AN_EXTERNAL_BENCHMARK"
)

SINGLE_TYPED_BYTES = 42_068
SINGLE_PROOF_JSON_BYTES = 121_996
SINGLE_ENVELOPE_JSON_BYTES = 3_312_940
SINGLE_INPUT_JSON_BYTES = 2_085_159
FRONTIER_TYPED_BYTES = 47_188
FRONTIER_PROOF_JSON_BYTES = 140_838
TYPED_SAVING_BYTES = 5_120
PROOF_JSON_SAVING_BYTES = 18_842
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900
ATTENTION_LOOKUP_CLAIMS = 1_184
ATTENTION_TRACE_ROWS = 2_048
ATTENTION_TYPED_BYTES = 22_916
DERIVED_MLP_TYPED_BYTES = 24_272
MLP_ROWS = 197_504
ADAPTER_TRACE_CELLS = 1_536
PCS_LIFTING_LOG_SIZE = 19
PROOF_COMMITMENTS = 4
TRACE_DECOMMITMENT_HASHES = 200
FRI_DECOMMITMENT_HASHES = 396
OODS_SAMPLES = 767
QUERIED_VALUES = 2_289

EXPECTED_SUMMARY = {
    "selected_attention_surface": "two_head_seq32_fused_attention",
    "selected_attention_lookup_claims": ATTENTION_LOOKUP_CLAIMS,
    "selected_attention_trace_rows": ATTENTION_TRACE_ROWS,
    "selected_attention_typed_bytes": ATTENTION_TYPED_BYTES,
    "seq32_derived_d128_mlp_typed_bytes": DERIVED_MLP_TYPED_BYTES,
    "seq32_derived_d128_mlp_rows": MLP_ROWS,
    "native_single_proof_typed_bytes": SINGLE_TYPED_BYTES,
    "native_single_proof_json_bytes": SINGLE_PROOF_JSON_BYTES,
    "native_single_input_json_bytes": SINGLE_INPUT_JSON_BYTES,
    "native_single_envelope_json_bytes": SINGLE_ENVELOPE_JSON_BYTES,
    "matched_two_proof_frontier_typed_bytes": FRONTIER_TYPED_BYTES,
    "matched_two_proof_frontier_json_bytes": FRONTIER_PROOF_JSON_BYTES,
    "typed_saving_vs_matched_frontier_bytes": TYPED_SAVING_BYTES,
    "typed_saving_vs_matched_frontier_share": "0.108502",
    "typed_ratio_vs_matched_frontier": "0.891498",
    "json_saving_vs_matched_frontier_bytes": PROOF_JSON_SAVING_BYTES,
    "json_saving_vs_matched_frontier_share": "0.133785",
    "json_ratio_vs_matched_frontier": "0.866215",
    "adapter_mode": "duplicate_base_preprocessed_v1",
    "adapter_status": "NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER",
    "adapter_trace_cells": ADAPTER_TRACE_CELLS,
    "pcs_lifting_log_size": PCS_LIFTING_LOG_SIZE,
    "proof_commitments": PROOF_COMMITMENTS,
    "trace_decommitment_hashes": TRACE_DECOMMITMENT_HASHES,
    "fri_decommitment_hashes": FRI_DECOMMITMENT_HASHES,
    "oods_samples": OODS_SAMPLES,
    "queried_values": QUERIED_VALUES,
    "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
    "typed_gap_to_nanozk_reported_row_bytes": SINGLE_TYPED_BYTES
    - NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
    "typed_ratio_to_nanozk_reported_row": "6.096812",
    "typed_reduction_share_to_match_nanozk_reported_row": "0.835980",
    "proof_size_comparable_external_rows": 0,
}

EXPECTED_INTERPRETATION = {
    "human_read": (
        "One native Stwo object now verifies the selected two-head seq32 fused attention surface, "
        "the public attention-to-d128 adapter, and the seq32-derived d128 RMSNorm/MLP surface."
    ),
    "interesting_signal": (
        "The proof is 42,068 typed bytes versus the 47,188 typed-byte matched two-proof frontier, "
        "a 5,120 byte saving. This is the first seq32+d128 native-boundary size win in this lane."
    ),
    "guardrail": (
        "The object is still not a full transformer block and is not comparable to NANOZK's reported "
        "6.9 KB d128 row. It remains 6.096812x that paper-reported row."
    ),
    "next_experiment": (
        "Try opening-layout and adapter-placement variants only if they preserve this statement binding "
        "and target additional FRI/opening reductions without changing the workload."
    ),
}

NON_CLAIMS = (
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not a full transformer block proof",
    "not exact real-valued Softmax",
    "not full autoregressive inference",
    "not timing evidence",
    "not production-ready zkML",
)

VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json > docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-binary-accounting-2026-05.json",
    "python3.10 scripts/zkai_native_seq32_attention_mlp_single_proof_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_single_proof_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_single_proof_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_single_proof_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend native_seq32_attention_mlp_single_proof --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

SOURCE_ARTIFACT_SPECS = (
    ("matched_frontier_gate", FRONTIER_GATE),
    ("native_single_input", SINGLE_INPUT),
    ("native_single_envelope", SINGLE_ENVELOPE),
    ("native_single_accounting", SINGLE_ACCOUNTING),
)
EXPECTED_SOURCE_ARTIFACTS = tuple(
    (artifact_id, str(path.relative_to(ROOT))) for artifact_id, path in SOURCE_ARTIFACT_SPECS
)

MUTATION_NAMES = (
    "typed_saving_erased",
    "typed_metric_drift",
    "json_metric_drift",
    "frontier_metric_drift",
    "issue_hint_drift",
    "nanozk_overclaim_boundary",
    "native_object_overclaim_removed_nonclaim",
    "source_artifact_digest_drift",
    "source_artifact_path_traversal",
    "source_artifact_valid_path_swap",
    "proof_verification_drift",
    "proof_sha_drift",
    "envelope_sha_drift",
    "validation_command_drift",
    "payload_commitment_drift",
)

TSV_COLUMNS = (
    "decision",
    "result",
    "native_single_proof_typed_bytes",
    "matched_two_proof_frontier_typed_bytes",
    "typed_saving_vs_matched_frontier_bytes",
    "typed_ratio_vs_matched_frontier",
    "native_single_proof_json_bytes",
    "matched_two_proof_frontier_json_bytes",
    "json_saving_vs_matched_frontier_bytes",
    "typed_ratio_to_nanozk_reported_row",
    "proof_size_comparable_external_rows",
)
DETERMINISTIC_TEMP_ATTEMPTS = 16


class NativeSeq32AttentionMlpSingleProofGateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as err:
        raise NativeSeq32AttentionMlpSingleProofGateError(f"invalid JSON value: {err}") from err


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return "blake2b-256:" + digest.hexdigest()


def refresh_payload_commitment(payload: dict[str, Any]) -> None:
    payload["payload_commitment"] = payload_commitment(payload)


def read_repo_file(path: pathlib.Path, label: str) -> bytes:
    root = ROOT.resolve()
    candidate = pathlib.Path(os.path.abspath(path if path.is_absolute() else ROOT / path))
    try:
        relative = candidate.relative_to(root)
    except ValueError as err:
        raise NativeSeq32AttentionMlpSingleProofGateError(f"{label} escapes repo root: {path}") from err
    current = root
    try:
        for part in relative.parts:
            current = current / part
            mode = current.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise NativeSeq32AttentionMlpSingleProofGateError(f"{label} must not traverse symlinks")
        fd = os.open(candidate, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            with os.fdopen(fd, "rb") as handle:
                fd = None
                return handle.read()
        finally:
            if fd is not None:
                os.close(fd)
    except OSError as err:
        raise NativeSeq32AttentionMlpSingleProofGateError(f"failed to read {label}: {err}") from err


def read_json(path: pathlib.Path, label: str) -> tuple[dict[str, Any], bytes]:
    raw = read_repo_file(path, label)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as err:
        raise NativeSeq32AttentionMlpSingleProofGateError(f"{label} is not valid JSON: {err}") from err
    if not isinstance(value, dict):
        raise NativeSeq32AttentionMlpSingleProofGateError(f"{label} must be a JSON object")
    return value, raw


def source_artifact(artifact_id: str, path: pathlib.Path) -> dict[str, Any]:
    raw = read_repo_file(path, artifact_id)
    return {
        "id": artifact_id,
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256(raw),
        "size_bytes": len(raw),
    }


def _dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise NativeSeq32AttentionMlpSingleProofGateError(f"{label} must be object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise NativeSeq32AttentionMlpSingleProofGateError(f"{label} must be list")
    return value


def _int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise NativeSeq32AttentionMlpSingleProofGateError(f"{label} must be integer")
    return value


def proof_bytes_from_envelope(envelope: dict[str, Any]) -> bytes:
    proof = _list(envelope.get("proof"), "envelope proof")
    try:
        return bytes(proof)
    except ValueError as err:
        raise NativeSeq32AttentionMlpSingleProofGateError("envelope proof must contain bytes") from err


def load_checked_metrics() -> dict[str, Any]:
    frontier, _ = read_json(FRONTIER_GATE, "matched frontier gate")
    input_value, input_raw = read_json(SINGLE_INPUT, "native single input")
    envelope, envelope_raw = read_json(SINGLE_ENVELOPE, "native single envelope")
    accounting, _ = read_json(SINGLE_ACCOUNTING, "native single accounting")

    input_from_envelope = _dict(envelope.get("input"), "envelope input")
    if input_from_envelope != input_value:
        raise NativeSeq32AttentionMlpSingleProofGateError("envelope input drift")
    proof_bytes = proof_bytes_from_envelope(envelope)
    rows = _list(accounting.get("rows"), "accounting rows")
    if len(rows) != 1:
        raise NativeSeq32AttentionMlpSingleProofGateError("accounting must contain exactly one row")
    row = _dict(rows[0], "accounting row")
    local_accounting = _dict(row.get("local_binary_accounting"), "local binary accounting")
    grouped = _dict(local_accounting.get("grouped_reconstruction"), "grouped reconstruction")
    records = _list(local_accounting.get("records"), "accounting records")
    records_by_path = {_dict(record, "record")["path"]: _dict(record, "record") for record in records}
    frontier_summary = _dict(frontier.get("summary"), "frontier summary")

    return {
        "frontier": frontier,
        "input": input_value,
        "input_size": len(input_raw),
        "envelope": envelope,
        "envelope_bytes": envelope_raw,
        "envelope_size": len(envelope_raw),
        "proof_bytes": proof_bytes,
        "accounting_row": row,
        "typed_bytes": _int(local_accounting.get("typed_size_estimate_bytes"), "typed bytes"),
        "proof_json_bytes": _int(row.get("proof_json_size_bytes"), "proof JSON bytes"),
        "grouped": grouped,
        "records_by_path": records_by_path,
        "frontier_typed": _int(
            frontier_summary.get("value_compatible_two_proof_frontier_typed_bytes"),
            "frontier typed bytes",
        ),
        "frontier_json": _int(
            frontier_summary.get("value_compatible_two_proof_frontier_json_bytes"),
            "frontier JSON bytes",
        ),
    }


def checked_summary(metrics: dict[str, Any]) -> dict[str, Any]:
    input_value = _dict(metrics["input"], "input")
    row = _dict(metrics["accounting_row"], "accounting row")
    grouped = _dict(metrics["grouped"], "grouped")
    records = metrics["records_by_path"]
    proof_bytes = metrics["proof_bytes"]
    if not input_value.get("validation_commands"):
        raise NativeSeq32AttentionMlpSingleProofGateError("input validation commands missing")
    if not metrics["envelope"].get("proof_backend") == "stwo":
        raise NativeSeq32AttentionMlpSingleProofGateError("envelope backend drift")
    if len(proof_bytes) != row.get("proof_json_size_bytes"):
        raise NativeSeq32AttentionMlpSingleProofGateError("proof payload byte length drift")
    if sha256(proof_bytes) != row.get("proof_sha256"):
        raise NativeSeq32AttentionMlpSingleProofGateError("proof sha drift")
    if sha256(metrics["envelope_bytes"]) != row.get("envelope_sha256"):
        raise NativeSeq32AttentionMlpSingleProofGateError("envelope sha drift")

    typed = metrics["typed_bytes"]
    frontier_typed = metrics["frontier_typed"]
    proof_json = metrics["proof_json_bytes"]
    frontier_json = metrics["frontier_json"]
    summary = {
        "selected_attention_surface": "two_head_seq32_fused_attention",
        "selected_attention_lookup_claims": _int(
            input_value.get("attention_lookup_claims"), "attention lookup claims"
        ),
        "selected_attention_trace_rows": ATTENTION_TRACE_ROWS,
        "selected_attention_typed_bytes": _int(
            input_value.get("current_attention_fused_typed_bytes"), "attention typed bytes"
        ),
        "seq32_derived_d128_mlp_typed_bytes": _int(
            input_value.get("current_derived_mlp_fused_typed_bytes"), "derived MLP typed bytes"
        ),
        "seq32_derived_d128_mlp_rows": _int(input_value.get("mlp_row_count"), "MLP row count"),
        "native_single_proof_typed_bytes": typed,
        "native_single_proof_json_bytes": proof_json,
        "native_single_input_json_bytes": metrics["input_size"],
        "native_single_envelope_json_bytes": metrics["envelope_size"],
        "matched_two_proof_frontier_typed_bytes": frontier_typed,
        "matched_two_proof_frontier_json_bytes": frontier_json,
        "typed_saving_vs_matched_frontier_bytes": frontier_typed - typed,
        "typed_saving_vs_matched_frontier_share": f"{(frontier_typed - typed) / frontier_typed:.6f}",
        "typed_ratio_vs_matched_frontier": f"{typed / frontier_typed:.6f}",
        "json_saving_vs_matched_frontier_bytes": frontier_json - proof_json,
        "json_saving_vs_matched_frontier_share": f"{(frontier_json - proof_json) / frontier_json:.6f}",
        "json_ratio_vs_matched_frontier": f"{proof_json / frontier_json:.6f}",
        "adapter_mode": input_value.get("adapter_mode"),
        "adapter_status": input_value.get("adapter_status"),
        "adapter_trace_cells": _int(input_value.get("adapter_trace_cells"), "adapter trace cells"),
        "pcs_lifting_log_size": _int(input_value.get("pcs_lifting_log_size"), "PCS lifting log size"),
        "proof_commitments": _int(records["pcs.commitments"]["item_count"], "proof commitments"),
        "trace_decommitment_hashes": _int(
            records["pcs.trace_decommitments.hash_witness"]["item_count"],
            "trace decommitment hashes",
        ),
        "fri_decommitment_hashes": _int(
            records["pcs.fri.first_layer.decommitment.hash_witness"]["item_count"],
            "first FRI decommitment hashes",
        )
        + _int(
            records["pcs.fri.inner_layers.decommitment.hash_witness"]["item_count"],
            "inner FRI decommitment hashes",
        ),
        "oods_samples": _int(records["pcs.sampled_values"]["item_count"], "OODS samples"),
        "queried_values": _int(records["pcs.queried_values"]["item_count"], "queried values"),
        "nanozk_reported_d128_block_proof_bytes": _int(
            input_value.get("nanozk_reported_d128_block_proof_bytes"), "NANOZK reported row"
        ),
        "typed_gap_to_nanozk_reported_row_bytes": typed
        - _int(input_value.get("nanozk_reported_d128_block_proof_bytes"), "NANOZK reported row"),
        "typed_ratio_to_nanozk_reported_row": f"{typed / NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES:.6f}",
        "typed_reduction_share_to_match_nanozk_reported_row": (
            f"{(typed - NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES) / typed:.6f}"
        ),
        "proof_size_comparable_external_rows": 0,
    }
    if grouped.get("fri_decommitments") != 13_248 or grouped.get("trace_decommitments") != 6_528:
        raise NativeSeq32AttentionMlpSingleProofGateError("opening-group accounting drift")
    return summary


def base_payload() -> dict[str, Any]:
    metrics = load_checked_metrics()
    summary = checked_summary(metrics)
    payload = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue_hint": ISSUE_HINT,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_artifacts": [source_artifact(artifact_id, path) for artifact_id, path in SOURCE_ARTIFACT_SPECS],
        "summary": summary,
        "interpretation": EXPECTED_INTERPRETATION,
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    refresh_payload_commitment(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> None:
    expected_keys = {
        "schema",
        "decision",
        "result",
        "issue_hint",
        "claim_boundary",
        "source_artifacts",
        "summary",
        "interpretation",
        "non_claims",
        "validation_commands",
        "payload_commitment",
    }
    if "mutation_result" in payload:
        expected_keys.add("mutation_result")
    if set(payload) != expected_keys:
        raise NativeSeq32AttentionMlpSingleProofGateError("payload key drift")
    if payload["schema"] != SCHEMA:
        raise NativeSeq32AttentionMlpSingleProofGateError("schema drift")
    if payload["decision"] != DECISION:
        raise NativeSeq32AttentionMlpSingleProofGateError("decision drift")
    if payload["result"] != RESULT:
        raise NativeSeq32AttentionMlpSingleProofGateError("result drift")
    if payload["issue_hint"] != ISSUE_HINT:
        raise NativeSeq32AttentionMlpSingleProofGateError("issue_hint drift")
    if payload["claim_boundary"] != CLAIM_BOUNDARY:
        raise NativeSeq32AttentionMlpSingleProofGateError("claim_boundary drift")
    if payload["summary"] != EXPECTED_SUMMARY:
        raise NativeSeq32AttentionMlpSingleProofGateError("summary drift")
    if payload["interpretation"] != EXPECTED_INTERPRETATION:
        raise NativeSeq32AttentionMlpSingleProofGateError("interpretation drift")
    if tuple(payload["non_claims"]) != NON_CLAIMS:
        raise NativeSeq32AttentionMlpSingleProofGateError("non-claims drift")
    if "not a NANOZK proof-size win" not in payload["non_claims"]:
        raise NativeSeq32AttentionMlpSingleProofGateError("NANOZK non-claim missing")
    if tuple(payload["validation_commands"]) != VALIDATION_COMMANDS:
        raise NativeSeq32AttentionMlpSingleProofGateError("validation command drift")
    artifacts = _list(payload["source_artifacts"], "source artifacts")
    inventory = tuple((artifact.get("id"), artifact.get("path")) for artifact in artifacts)
    if inventory != EXPECTED_SOURCE_ARTIFACTS:
        raise NativeSeq32AttentionMlpSingleProofGateError("source artifact inventory drift")
    for artifact in artifacts:
        path = ROOT / artifact["path"]
        raw = read_repo_file(path, artifact["id"])
        if artifact.get("sha256") != sha256(raw) or artifact.get("size_bytes") != len(raw):
            raise NativeSeq32AttentionMlpSingleProofGateError("source artifact digest drift")
        try:
            pathlib.Path(artifact["path"]).relative_to("docs/engineering/evidence")
        except ValueError as err:
            raise NativeSeq32AttentionMlpSingleProofGateError("source artifact path traversal") from err
    summary = _dict(payload["summary"], "summary")
    if summary["native_single_proof_typed_bytes"] >= summary["matched_two_proof_frontier_typed_bytes"]:
        raise NativeSeq32AttentionMlpSingleProofGateError("typed saving missing")
    if summary["typed_saving_vs_matched_frontier_bytes"] != TYPED_SAVING_BYTES:
        raise NativeSeq32AttentionMlpSingleProofGateError("typed saving drift")
    if summary["proof_size_comparable_external_rows"] != 0:
        raise NativeSeq32AttentionMlpSingleProofGateError("external comparison overclaim")
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise NativeSeq32AttentionMlpSingleProofGateError("payload commitment drift")
    if "mutation_result" in payload:
        result = _dict(payload["mutation_result"], "mutation result")
        if not result.get("all_mutations_rejected"):
            raise NativeSeq32AttentionMlpSingleProofGateError("mutation result drift")
        if result.get("mutations_rejected") != len(MUTATION_NAMES):
            raise NativeSeq32AttentionMlpSingleProofGateError("mutation result drift")
        if tuple(result.get("mutation_names", ())) != MUTATION_NAMES:
            raise NativeSeq32AttentionMlpSingleProofGateError("mutation result drift")
        cases = _list(result.get("cases"), "mutation cases")
        if tuple(case.get("name") for case in cases) != MUTATION_NAMES:
            raise NativeSeq32AttentionMlpSingleProofGateError("mutation result drift")
        for case in cases:
            if case.get("rejected") is not True or not case.get("error"):
                raise NativeSeq32AttentionMlpSingleProofGateError("mutation result drift")


def mutation_result(payload: dict[str, Any]) -> dict[str, Any]:
    mutations: tuple[tuple[str, Callable[[dict[str, Any]], None]], ...] = (
        ("typed_saving_erased", lambda item: item["summary"].update({"typed_saving_vs_matched_frontier_bytes": 0})),
        ("typed_metric_drift", lambda item: item["summary"].update({"native_single_proof_typed_bytes": 47_188})),
        ("json_metric_drift", lambda item: item["summary"].update({"native_single_proof_json_bytes": 140_838})),
        (
            "frontier_metric_drift",
            lambda item: item["summary"].update({"matched_two_proof_frontier_typed_bytes": 45_492}),
        ),
        ("issue_hint_drift", lambda item: item.update({"issue_hint": "different-issue"})),
        ("nanozk_overclaim_boundary", lambda item: item.update({"claim_boundary": item["claim_boundary"] + "_NANOZK_WIN"})),
        ("native_object_overclaim_removed_nonclaim", lambda item: item["non_claims"].remove("not a full transformer block proof")),
        ("source_artifact_digest_drift", lambda item: item["source_artifacts"][0].update({"sha256": "0" * 64})),
        ("source_artifact_path_traversal", lambda item: item["source_artifacts"][0].update({"path": "../outside.json"})),
        (
            "source_artifact_valid_path_swap",
            lambda item: item["source_artifacts"][0].update(
                {
                    "path": str(SINGLE_ACCOUNTING.relative_to(ROOT)),
                    "sha256": source_artifact("tmp", SINGLE_ACCOUNTING)["sha256"],
                    "size_bytes": source_artifact("tmp", SINGLE_ACCOUNTING)["size_bytes"],
                }
            ),
        ),
        ("proof_verification_drift", lambda item: item["summary"].update({"proof_size_comparable_external_rows": 1})),
        ("proof_sha_drift", lambda item: item["source_artifacts"][2].update({"sha256": "f" * 64})),
        ("envelope_sha_drift", lambda item: item["source_artifacts"][2].update({"size_bytes": 1})),
        ("validation_command_drift", lambda item: item["validation_commands"].append("gh workflow run ci.yml")),
        ("payload_commitment_drift", lambda item: item.update({"payload_commitment": "blake2b-256:" + "1" * 64})),
    )
    cases = []
    for name, mutate in mutations:
        candidate = copy.deepcopy(payload)
        mutate(candidate)
        if name != "payload_commitment_drift":
            refresh_payload_commitment(candidate)
        try:
            validate_payload(candidate)
        except NativeSeq32AttentionMlpSingleProofGateError as err:
            cases.append({"name": name, "rejected": True, "error": str(err)})
        else:
            cases.append({"name": name, "rejected": False, "error": ""})
    return {
        "mutation_names": [name for name, _ in mutations],
        "mutations_rejected": sum(1 for case in cases if case["rejected"]),
        "all_mutations_rejected": all(case["rejected"] for case in cases),
        "cases": cases,
    }


def payload_with_mutations() -> dict[str, Any]:
    payload = base_payload()
    validate_payload(payload)
    payload["mutation_result"] = mutation_result(payload)
    refresh_payload_commitment(payload)
    validate_payload(payload)
    return payload


def tsv_text(payload: dict[str, Any]) -> str:
    row = {column: "" for column in TSV_COLUMNS}
    row["decision"] = payload["decision"]
    row["result"] = payload["result"]
    for key, value in payload["summary"].items():
        if key in row:
            row[key] = value
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerow(row)
    return buffer.getvalue()


def require_output_path(path: pathlib.Path) -> pathlib.Path:
    target = pathlib.Path(os.path.abspath(path if path.is_absolute() else ROOT / path))
    evidence_root = EVIDENCE_DIR.resolve()
    try:
        relative = target.relative_to(evidence_root)
    except ValueError as err:
        raise NativeSeq32AttentionMlpSingleProofGateError("output path escapes evidence dir") from err
    current = evidence_root
    for part in relative.parent.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except OSError as err:
            raise NativeSeq32AttentionMlpSingleProofGateError(f"output parent must exist: {current}") from err
        if stat.S_ISLNK(mode):
            raise NativeSeq32AttentionMlpSingleProofGateError("output path must not traverse symlinks")
        if not stat.S_ISDIR(mode):
            raise NativeSeq32AttentionMlpSingleProofGateError(f"output parent must be directory: {current}")
    if target.is_symlink() or (target.exists() and target.is_dir()):
        raise NativeSeq32AttentionMlpSingleProofGateError("output path must be a non-symlink file")
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
        raise NativeSeq32AttentionMlpSingleProofGateError(
            f"deterministic temp file collision for output: {target}"
        )
    finally:
        os.close(parent_fd)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json", type=pathlib.Path, default=JSON_OUT)
    parser.add_argument("--write-tsv", type=pathlib.Path, default=TSV_OUT)
    args = parser.parse_args()

    payload = payload_with_mutations()
    json_text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    atomic_write_text(args.write_json, json_text)
    atomic_write_text(args.write_tsv, tsv_text(payload))
    print(
        json.dumps(
            {
                "decision": payload["decision"],
                "result": payload["result"],
                "native_single_proof_typed_bytes": payload["summary"]["native_single_proof_typed_bytes"],
                "matched_frontier_typed_bytes": payload["summary"]["matched_two_proof_frontier_typed_bytes"],
                "typed_saving_bytes": payload["summary"]["typed_saving_vs_matched_frontier_bytes"],
                "mutation_count": len(MUTATION_NAMES),
                "mutations_rejected": payload["mutation_result"]["mutations_rejected"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
