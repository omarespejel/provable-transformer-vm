#!/usr/bin/env python3.10
"""Pin the value-compatible seq32 attention + d128 MLP boundary frontier.

This gate is intentionally not a native one-proof-object claim.  It consumes
the selected two-head seq32 fused attention artifact and the regenerated
seq32-derived d128 RMSNorm/MLP fused artifact, then pins the honest two-proof
frontier for the next native proof-object attempt.
"""

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
import sys
from collections.abc import Callable
from typing import Any


if sys.version_info < (3, 10):
    raise RuntimeError("zkai_seq32_value_compatible_boundary_frontier_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"

SEQ32_ATTENTION_GATE = (
    EVIDENCE_DIR / "zkai-attention-kv-stwo-native-two-head-seq32-fused-softmax-table-gate-2026-05.json"
)
SEQ32_ATTENTION_ENVELOPE = (
    EVIDENCE_DIR / "zkai-attention-kv-stwo-native-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json"
)
ATTENTION_ACCOUNTING = EVIDENCE_DIR / "zkai-larger-native-boundary-candidate-accounting-2026-05.json"
SEQ32_MLP_SURFACE = EVIDENCE_DIR / "zkai-seq32-derived-d128-native-mlp-surface-2026-05.json"
SEQ32_MLP_ENVELOPE = EVIDENCE_DIR / "zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.envelope.json"
SEQ32_MLP_ACCOUNTING = EVIDENCE_DIR / "zkai-seq32-derived-d128-rmsnorm-mlp-fused-binary-accounting-2026-05.json"

JSON_OUT = EVIDENCE_DIR / "zkai-seq32-value-compatible-boundary-frontier-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-seq32-value-compatible-boundary-frontier-2026-05.tsv"

SCHEMA = "zkai-seq32-value-compatible-boundary-frontier-v1"
DECISION = "GO_PIN_SEQ32_VALUE_COMPATIBLE_TWO_PROOF_FRONTIER_FOR_NEXT_NATIVE_BOUNDARY"
RESULT = "SEQ32_ATTENTION_AND_SEQ32_DERIVED_D128_MLP_FORM_47188_TYPED_BYTE_FRONTIER"
ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/678"
NEXT_ISSUE_HINT = "native-seq32-attention-mlp-single-proof-object"
PAYLOAD_DOMAIN = "ptvm:zkai:seq32-value-compatible-boundary-frontier:v1"
CLAIM_BOUNDARY = (
    "VALUE_COMPATIBLE_TWO_PROOF_FRONTIER_FOR_NEXT_NATIVE_ATTENTION_PLUS_MLP_OBJECT;"
    "NOT_ONE_NATIVE_PROOF_OBJECT_NOT_A_NANOZK_COMPARISON_NOT_A_FULL_BLOCK"
)

SEQ32_ATTENTION_TYPED_BYTES = 22_916
SEQ32_ATTENTION_JSON_BYTES = 66_327
SEQ32_ATTENTION_LOOKUP_CLAIMS = 1_184
SEQ32_ATTENTION_TRACE_ROWS = 2_048
SEQ32_ATTENTION_SOURCE_PLUS_SIDECAR_JSON_BYTES = 98_012
SEQ32_ATTENTION_JSON_SAVING_BYTES = 31_685
SEQ32_ATTENTION_FUSION_RATIO = "0.676723"

SEQ32_MLP_TYPED_BYTES = 24_272
SEQ32_MLP_JSON_BYTES = 74_511
SEQ32_MLP_SEPARATE_TYPED_BYTES = 54_336
SEQ32_MLP_SEPARATE_JSON_BYTES = 181_194
SEQ32_MLP_TYPED_SAVING_BYTES = 30_064
SEQ32_MLP_JSON_SAVING_BYTES = 106_683
SEQ32_MLP_TYPED_RATIO = "0.446702"
SEQ32_MLP_ADAPTER_MISMATCHES = 0

FRONTIER_TYPED_BYTES = 47_188
FRONTIER_JSON_BYTES = 140_838
STALE_SELECTOR_FRONTIER_TYPED_BYTES = 45_492
STALE_SELECTOR_FRONTIER_JSON_BYTES = 134_887
D8_FRONTIER_TYPED_BYTES = 40_700
D8_FRONTIER_JSON_BYTES = 116_258
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900

EXPECTED_SUMMARY = {
    "selected_attention_surface": "two_head_seq32_fused_attention",
    "selected_attention_lookup_claims": SEQ32_ATTENTION_LOOKUP_CLAIMS,
    "selected_attention_trace_rows": SEQ32_ATTENTION_TRACE_ROWS,
    "selected_attention_typed_bytes": SEQ32_ATTENTION_TYPED_BYTES,
    "selected_attention_json_proof_bytes": SEQ32_ATTENTION_JSON_BYTES,
    "selected_attention_source_plus_sidecar_json_bytes": SEQ32_ATTENTION_SOURCE_PLUS_SIDECAR_JSON_BYTES,
    "selected_attention_json_saving_bytes": SEQ32_ATTENTION_JSON_SAVING_BYTES,
    "selected_attention_fusion_ratio": SEQ32_ATTENTION_FUSION_RATIO,
    "seq32_derived_mlp_adapter_mismatches": SEQ32_MLP_ADAPTER_MISMATCHES,
    "seq32_derived_mlp_typed_bytes": SEQ32_MLP_TYPED_BYTES,
    "seq32_derived_mlp_json_proof_bytes": SEQ32_MLP_JSON_BYTES,
    "seq32_derived_mlp_separate_typed_bytes": SEQ32_MLP_SEPARATE_TYPED_BYTES,
    "seq32_derived_mlp_separate_json_proof_bytes": SEQ32_MLP_SEPARATE_JSON_BYTES,
    "seq32_derived_mlp_typed_saving_bytes": SEQ32_MLP_TYPED_SAVING_BYTES,
    "seq32_derived_mlp_json_saving_bytes": SEQ32_MLP_JSON_SAVING_BYTES,
    "seq32_derived_mlp_typed_ratio": SEQ32_MLP_TYPED_RATIO,
    "value_compatible_two_proof_frontier_typed_bytes": FRONTIER_TYPED_BYTES,
    "value_compatible_two_proof_frontier_json_bytes": FRONTIER_JSON_BYTES,
    "stale_selector_frontier_typed_bytes": STALE_SELECTOR_FRONTIER_TYPED_BYTES,
    "stale_selector_frontier_json_bytes": STALE_SELECTOR_FRONTIER_JSON_BYTES,
    "frontier_typed_increase_after_value_fix_bytes": FRONTIER_TYPED_BYTES - STALE_SELECTOR_FRONTIER_TYPED_BYTES,
    "frontier_json_increase_after_value_fix_bytes": FRONTIER_JSON_BYTES - STALE_SELECTOR_FRONTIER_JSON_BYTES,
    "d8_two_proof_frontier_typed_bytes": D8_FRONTIER_TYPED_BYTES,
    "d8_two_proof_frontier_json_bytes": D8_FRONTIER_JSON_BYTES,
    "typed_increase_vs_d8_frontier_bytes": FRONTIER_TYPED_BYTES - D8_FRONTIER_TYPED_BYTES,
    "json_increase_vs_d8_frontier_bytes": FRONTIER_JSON_BYTES - D8_FRONTIER_JSON_BYTES,
    "lookup_growth_vs_d8": "22.769231",
    "attention_typed_growth_vs_d8": "1.264401",
    "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
    "typed_bytes_to_remove_to_match_nanozk_reported_row": FRONTIER_TYPED_BYTES
    - NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
    "typed_reduction_share_to_match_nanozk_reported_row": "0.853776",
    "proof_size_comparable_external_rows": 0,
}

EXPECTED_INTERPRETATION = {
    "human_read": (
        "The seq32 correctness fix makes the next boundary honest but heavier: "
        "the value-compatible two-proof target is now 47,188 typed bytes, not "
        "the stale 45,492 byte selector target."
    ),
    "interesting_signal": (
        "The selected attention side still carries 1,184 lookup claims for "
        "22,916 typed bytes, while the regenerated MLP side still saves "
        "30,064 typed bytes versus six separate native component proofs."
    ),
    "next_experiment": (
        "Build one native Stwo proof object over the two-head seq32 fused "
        "attention surface plus the seq32-derived d128 RMSNorm/MLP surface, "
        "then compare against this 47,188 typed-byte two-proof frontier."
    ),
    "guardrail": (
        "This is a value-compatible local frontier, not one native proof object, "
        "not a full transformer block, and not a NANOZK proof-size comparison."
    ),
}

NON_CLAIMS = (
    "not one native attention-plus-MLP proof object",
    "not a full transformer block proof",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not timing evidence",
    "not production-ready zkML",
)

VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_seq32_value_compatible_boundary_frontier_gate.py --write-json docs/engineering/evidence/zkai-seq32-value-compatible-boundary-frontier-2026-05.json --write-tsv docs/engineering/evidence/zkai-seq32-value-compatible-boundary-frontier-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_seq32_value_compatible_boundary_frontier_gate.py scripts/tests/test_zkai_seq32_value_compatible_boundary_frontier_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_seq32_value_compatible_boundary_frontier_gate",
    "python3.10 -m unittest scripts.tests.test_zkai_seq32_derived_d128_mlp_surface_gate",
    "python3 scripts/research_issue_lint.py --repo-root .",
    "python3 scripts/paper/paper_preflight.py --repo-root .",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

TSV_COLUMNS = (
    "decision",
    "result",
    "selected_attention_lookup_claims",
    "selected_attention_typed_bytes",
    "seq32_derived_mlp_typed_bytes",
    "value_compatible_two_proof_frontier_typed_bytes",
    "stale_selector_frontier_typed_bytes",
    "frontier_typed_increase_after_value_fix_bytes",
    "typed_bytes_to_remove_to_match_nanozk_reported_row",
)

MUTATION_NAMES = (
    "stale_frontier_overclaim",
    "frontier_typed_metric_drift",
    "attention_typed_metric_drift",
    "mlp_typed_metric_drift",
    "adapter_mismatch_drift",
    "nanozk_overclaim",
    "native_object_overclaim",
    "source_artifact_digest_drift",
    "source_artifact_valid_path_drift",
    "source_artifact_path_traversal",
    "non_claim_removed",
    "validation_command_drift",
    "payload_commitment_drift",
)

SOURCE_ARTIFACT_SPECS = (
    ("seq32_attention_gate", SEQ32_ATTENTION_GATE),
    ("seq32_attention_envelope", SEQ32_ATTENTION_ENVELOPE),
    ("attention_accounting", ATTENTION_ACCOUNTING),
    ("seq32_mlp_surface_gate", SEQ32_MLP_SURFACE),
    ("seq32_mlp_fused_envelope", SEQ32_MLP_ENVELOPE),
    ("seq32_mlp_accounting", SEQ32_MLP_ACCOUNTING),
)
EXPECTED_SOURCE_ARTIFACTS = tuple(
    (artifact_id, str(path.relative_to(ROOT))) for artifact_id, path in SOURCE_ARTIFACT_SPECS
)


class Seq32ValueCompatibleBoundaryFrontierError(ValueError):
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
        raise Seq32ValueCompatibleBoundaryFrontierError(f"invalid JSON value: {err}") from err


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
        raise Seq32ValueCompatibleBoundaryFrontierError(f"{label} escapes repo root: {path}") from err
    current = root
    try:
        for part in relative.parts:
            current = current / part
            mode = current.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise Seq32ValueCompatibleBoundaryFrontierError(f"{label} must not traverse symlinks")
        fd = os.open(candidate, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            with os.fdopen(fd, "rb") as handle:
                fd = None
                return handle.read()
        finally:
            if fd is not None:
                os.close(fd)
    except OSError as err:
        raise Seq32ValueCompatibleBoundaryFrontierError(f"failed to read {label}: {err}") from err


def read_json(path: pathlib.Path, label: str) -> tuple[dict[str, Any], bytes]:
    raw = read_repo_file(path, label)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as err:
        raise Seq32ValueCompatibleBoundaryFrontierError(f"{label} is not valid JSON: {err}") from err
    if not isinstance(value, dict):
        raise Seq32ValueCompatibleBoundaryFrontierError(f"{label} must be a JSON object")
    return value, raw


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def source_descriptor(path: pathlib.Path, raw: bytes, artifact_id: str) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256(raw),
        "size_bytes": len(raw),
    }


def rows_by_path(accounting: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = accounting.get("rows")
    if not isinstance(rows, list):
        raise Seq32ValueCompatibleBoundaryFrontierError("accounting rows must be a list")
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise Seq32ValueCompatibleBoundaryFrontierError("accounting row must be object")
        path = row.get("evidence_relative_path") or row.get("path")
        if not isinstance(path, str) or not path:
            raise Seq32ValueCompatibleBoundaryFrontierError("accounting row path must be non-empty")
        if path in out:
            raise Seq32ValueCompatibleBoundaryFrontierError(f"duplicate accounting row: {path}")
        out[path] = row
    return out


def typed_bytes(row: dict[str, Any], label: str) -> int:
    value = row.get("local_binary_accounting", {}).get("component_sum_bytes")
    if not isinstance(value, int) or isinstance(value, bool):
        raise Seq32ValueCompatibleBoundaryFrontierError(f"{label} typed bytes must be integer")
    return value


def json_bytes(row: dict[str, Any], label: str) -> int:
    value = row.get("proof_json_size_bytes")
    if not isinstance(value, int) or isinstance(value, bool):
        raise Seq32ValueCompatibleBoundaryFrontierError(f"{label} JSON bytes must be integer")
    return value


def verify_accounting_row(
    accounting: dict[str, dict[str, Any]],
    path: pathlib.Path,
    raw: bytes,
    label: str,
    expected_typed: int,
    expected_json: int,
) -> None:
    relative = str(path.relative_to(EVIDENCE_DIR))
    row = accounting.get(relative)
    if row is None:
        raise Seq32ValueCompatibleBoundaryFrontierError(f"missing accounting row for {label}")
    if row.get("path") != str(path.relative_to(ROOT)):
        raise Seq32ValueCompatibleBoundaryFrontierError(f"{label} accounting path drift")
    if row.get("envelope_sha256") != sha256(raw):
        raise Seq32ValueCompatibleBoundaryFrontierError(f"{label} accounting envelope digest drift")
    if typed_bytes(row, label) != expected_typed:
        raise Seq32ValueCompatibleBoundaryFrontierError(f"{label} typed bytes drift")
    if json_bytes(row, label) != expected_json:
        raise Seq32ValueCompatibleBoundaryFrontierError(f"{label} JSON bytes drift")


def validate_source_path(path_text: str) -> pathlib.Path:
    path = pathlib.Path(path_text)
    if path.is_absolute() or ".." in path.parts:
        raise Seq32ValueCompatibleBoundaryFrontierError("source artifact path traversal")
    candidate = (ROOT / path).resolve(strict=False)
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError as err:
        raise Seq32ValueCompatibleBoundaryFrontierError("source artifact path escapes repo") from err
    return ROOT / path


def build_payload() -> dict[str, Any]:
    attention_gate, attention_gate_raw = read_json(SEQ32_ATTENTION_GATE, "seq32 attention gate")
    if attention_gate.get("lookup_claims") != SEQ32_ATTENTION_LOOKUP_CLAIMS:
        raise Seq32ValueCompatibleBoundaryFrontierError("seq32 attention lookup drift")
    if attention_gate.get("trace_rows") != SEQ32_ATTENTION_TRACE_ROWS:
        raise Seq32ValueCompatibleBoundaryFrontierError("seq32 attention trace-row drift")
    if attention_gate.get("fused_saves_vs_source_plus_sidecar_bytes") != SEQ32_ATTENTION_JSON_SAVING_BYTES:
        raise Seq32ValueCompatibleBoundaryFrontierError("seq32 attention saving drift")

    _attention_envelope, attention_envelope_raw = read_json(SEQ32_ATTENTION_ENVELOPE, "seq32 attention envelope")
    attention_accounting, attention_accounting_raw = read_json(ATTENTION_ACCOUNTING, "attention accounting")
    attention_rows = rows_by_path(attention_accounting)
    verify_accounting_row(
        attention_rows,
        SEQ32_ATTENTION_ENVELOPE,
        attention_envelope_raw,
        "seq32 attention envelope",
        SEQ32_ATTENTION_TYPED_BYTES,
        SEQ32_ATTENTION_JSON_BYTES,
    )

    mlp_surface, mlp_surface_raw = read_json(SEQ32_MLP_SURFACE, "seq32 MLP surface")
    mlp_summary = mlp_surface.get("summary")
    if not isinstance(mlp_summary, dict):
        raise Seq32ValueCompatibleBoundaryFrontierError("seq32 MLP summary must be object")
    for key, expected in (
        ("seq32_adapter_mismatches", SEQ32_MLP_ADAPTER_MISMATCHES),
        ("fused_typed_bytes", SEQ32_MLP_TYPED_BYTES),
        ("fused_proof_json_bytes", SEQ32_MLP_JSON_BYTES),
        ("separate_component_typed_bytes", SEQ32_MLP_SEPARATE_TYPED_BYTES),
        ("separate_component_json_bytes", SEQ32_MLP_SEPARATE_JSON_BYTES),
        ("typed_saving_bytes", SEQ32_MLP_TYPED_SAVING_BYTES),
        ("json_saving_bytes", SEQ32_MLP_JSON_SAVING_BYTES),
    ):
        if mlp_summary.get(key) != expected:
            raise Seq32ValueCompatibleBoundaryFrontierError(f"seq32 MLP {key} drift")

    _mlp_envelope, mlp_envelope_raw = read_json(SEQ32_MLP_ENVELOPE, "seq32 MLP fused envelope")
    mlp_accounting, mlp_accounting_raw = read_json(SEQ32_MLP_ACCOUNTING, "seq32 MLP accounting")
    mlp_rows = rows_by_path(mlp_accounting)
    verify_accounting_row(
        mlp_rows,
        SEQ32_MLP_ENVELOPE,
        mlp_envelope_raw,
        "seq32 MLP fused envelope",
        SEQ32_MLP_TYPED_BYTES,
        SEQ32_MLP_JSON_BYTES,
    )

    source_artifacts = [
        source_descriptor(SEQ32_ATTENTION_GATE, attention_gate_raw, "seq32_attention_gate"),
        source_descriptor(SEQ32_ATTENTION_ENVELOPE, attention_envelope_raw, "seq32_attention_envelope"),
        source_descriptor(ATTENTION_ACCOUNTING, attention_accounting_raw, "attention_accounting"),
        source_descriptor(SEQ32_MLP_SURFACE, mlp_surface_raw, "seq32_mlp_surface_gate"),
        source_descriptor(SEQ32_MLP_ENVELOPE, mlp_envelope_raw, "seq32_mlp_fused_envelope"),
        source_descriptor(SEQ32_MLP_ACCOUNTING, mlp_accounting_raw, "seq32_mlp_accounting"),
    ]

    payload = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "next_issue_hint": NEXT_ISSUE_HINT,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_artifacts": source_artifacts,
        "summary": dict(EXPECTED_SUMMARY),
        "interpretation": dict(EXPECTED_INTERPRETATION),
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
        "payload_commitment": "",
    }
    validate_without_commitment(payload)
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload)
    return payload


def validate_without_commitment(payload: dict[str, Any]) -> None:
    base_keys = {
        "schema",
        "decision",
        "result",
        "issue",
        "next_issue_hint",
        "claim_boundary",
        "source_artifacts",
        "summary",
        "interpretation",
        "non_claims",
        "validation_commands",
        "payload_commitment",
    }
    expected_keys = set(base_keys)
    has_mutation_metadata = "mutation_inventory" in payload or "mutation_result" in payload
    if has_mutation_metadata:
        expected_keys.update({"mutation_inventory", "mutation_result"})
    if set(payload) != expected_keys:
        raise Seq32ValueCompatibleBoundaryFrontierError("payload key drift")
    for key, expected in (
        ("schema", SCHEMA),
        ("decision", DECISION),
        ("result", RESULT),
        ("issue", ISSUE),
        ("next_issue_hint", NEXT_ISSUE_HINT),
        ("claim_boundary", CLAIM_BOUNDARY),
    ):
        if payload.get(key) != expected:
            raise Seq32ValueCompatibleBoundaryFrontierError(f"{key} drift")
    if payload.get("summary") != EXPECTED_SUMMARY:
        raise Seq32ValueCompatibleBoundaryFrontierError("summary drift")
    if payload.get("interpretation") != EXPECTED_INTERPRETATION:
        raise Seq32ValueCompatibleBoundaryFrontierError("interpretation drift")
    if tuple(payload.get("non_claims", ())) != NON_CLAIMS:
        raise Seq32ValueCompatibleBoundaryFrontierError("non-claim inventory drift")
    if tuple(payload.get("validation_commands", ())) != VALIDATION_COMMANDS:
        raise Seq32ValueCompatibleBoundaryFrontierError("validation command inventory drift")

    artifacts = payload.get("source_artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 6:
        raise Seq32ValueCompatibleBoundaryFrontierError("source artifact inventory drift")
    seen: set[str] = set()
    for artifact, expected in zip(artifacts, EXPECTED_SOURCE_ARTIFACTS, strict=True):
        if not isinstance(artifact, dict):
            raise Seq32ValueCompatibleBoundaryFrontierError("source artifact must be object")
        if set(artifact) != {"id", "path", "sha256", "size_bytes"}:
            raise Seq32ValueCompatibleBoundaryFrontierError("source artifact key drift")
        artifact_id = artifact.get("id")
        if not isinstance(artifact_id, str) or not artifact_id:
            raise Seq32ValueCompatibleBoundaryFrontierError("source artifact id drift")
        if artifact_id in seen:
            raise Seq32ValueCompatibleBoundaryFrontierError("duplicate source artifact id")
        seen.add(artifact_id)
        path_text = artifact.get("path")
        if not isinstance(path_text, str):
            raise Seq32ValueCompatibleBoundaryFrontierError("source artifact path drift")
        path = validate_source_path(path_text)
        if (artifact_id, path_text) != expected:
            raise Seq32ValueCompatibleBoundaryFrontierError("source artifact inventory drift")
        raw = read_repo_file(path, f"source artifact {artifact_id}")
        if artifact.get("sha256") != sha256(raw):
            raise Seq32ValueCompatibleBoundaryFrontierError("source artifact digest drift")
        if artifact.get("size_bytes") != len(raw):
            raise Seq32ValueCompatibleBoundaryFrontierError("source artifact size drift")

    if has_mutation_metadata:
        inventory = payload.get("mutation_inventory")
        if not isinstance(inventory, dict):
            raise Seq32ValueCompatibleBoundaryFrontierError("mutation inventory drift")
        if inventory.get("mutation_count") != len(MUTATION_NAMES):
            raise Seq32ValueCompatibleBoundaryFrontierError("mutation inventory drift")
        if tuple(inventory.get("mutation_names", ())) != MUTATION_NAMES:
            raise Seq32ValueCompatibleBoundaryFrontierError("mutation inventory drift")

        mutation_result = payload.get("mutation_result")
        if not isinstance(mutation_result, dict):
            raise Seq32ValueCompatibleBoundaryFrontierError("mutation result drift")
        if mutation_result.get("mutation_count") != len(MUTATION_NAMES):
            raise Seq32ValueCompatibleBoundaryFrontierError("mutation result drift")
        if tuple(mutation_result.get("mutation_names", ())) != MUTATION_NAMES:
            raise Seq32ValueCompatibleBoundaryFrontierError("mutation result drift")
        if mutation_result.get("mutations_rejected") != len(MUTATION_NAMES):
            raise Seq32ValueCompatibleBoundaryFrontierError("mutation result drift")
        if mutation_result.get("all_mutations_rejected") is not True:
            raise Seq32ValueCompatibleBoundaryFrontierError("mutation rejection drift")


def validate_payload(payload: dict[str, Any]) -> None:
    validate_without_commitment(payload)
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise Seq32ValueCompatibleBoundaryFrontierError("payload commitment drift")


def mutate_source_artifact_valid_path_drift(payload: dict[str, Any]) -> None:
    raw = read_repo_file(SEQ32_MLP_SURFACE, "valid in-repo source-artifact path drift")
    payload["source_artifacts"][0]["path"] = str(SEQ32_MLP_SURFACE.relative_to(ROOT))
    payload["source_artifacts"][0]["sha256"] = sha256(raw)
    payload["source_artifacts"][0]["size_bytes"] = len(raw)


def mutation_cases() -> list[tuple[str, Callable[[dict[str, Any]], None]]]:
    return [
        (
            "stale_frontier_overclaim",
            lambda p: p["summary"].__setitem__(
                "value_compatible_two_proof_frontier_typed_bytes",
                STALE_SELECTOR_FRONTIER_TYPED_BYTES,
            ),
        ),
        (
            "frontier_typed_metric_drift",
            lambda p: p["summary"].__setitem__(
                "value_compatible_two_proof_frontier_typed_bytes",
                FRONTIER_TYPED_BYTES - 1,
            ),
        ),
        (
            "attention_typed_metric_drift",
            lambda p: p["summary"].__setitem__("selected_attention_typed_bytes", SEQ32_ATTENTION_TYPED_BYTES - 1),
        ),
        (
            "mlp_typed_metric_drift",
            lambda p: p["summary"].__setitem__("seq32_derived_mlp_typed_bytes", SEQ32_MLP_TYPED_BYTES - 1),
        ),
        (
            "adapter_mismatch_drift",
            lambda p: p["summary"].__setitem__("seq32_derived_mlp_adapter_mismatches", 1),
        ),
        ("nanozk_overclaim", lambda p: p.__setitem__("claim_boundary", CLAIM_BOUNDARY + "_NANOZK_WIN")),
        ("native_object_overclaim", lambda p: p.__setitem__("result", "ONE_NATIVE_SEQ32_ATTENTION_MLP_PROOF_OBJECT")),
        (
            "source_artifact_digest_drift",
            lambda p: p["source_artifacts"][0].__setitem__("sha256", "0" * 64),
        ),
        ("source_artifact_valid_path_drift", mutate_source_artifact_valid_path_drift),
        (
            "source_artifact_path_traversal",
            lambda p: p["source_artifacts"][0].__setitem__("path", "../outside.json"),
        ),
        ("non_claim_removed", lambda p: p["non_claims"].pop()),
        (
            "validation_command_drift",
            lambda p: p["validation_commands"].__setitem__(0, "python3 scripts/fake.py"),
        ),
        ("payload_commitment_drift", lambda p: p.__setitem__("payload_commitment", "blake2b-256:" + "00" * 32)),
    ]


def run_mutations() -> dict[str, Any]:
    baseline = build_payload()
    cases = []
    for name, mutate in mutation_cases():
        candidate = copy.deepcopy(baseline)
        mutate(candidate)
        if name != "payload_commitment_drift":
            candidate["payload_commitment"] = payload_commitment(candidate)
        try:
            validate_payload(candidate)
        except Seq32ValueCompatibleBoundaryFrontierError as err:
            cases.append({"name": name, "rejected": True, "error": str(err)})
        else:
            cases.append({"name": name, "rejected": False, "error": ""})
    rejected = sum(1 for case in cases if case["rejected"])
    return {
        "mutation_count": len(MUTATION_NAMES),
        "mutation_names": list(MUTATION_NAMES),
        "mutations_rejected": rejected,
        "all_mutations_rejected": rejected == len(MUTATION_NAMES),
        "cases": cases,
    }


def payload_with_mutations() -> dict[str, Any]:
    payload = build_payload()
    mutation_result = run_mutations()
    payload["mutation_inventory"] = {
        "mutation_count": len(MUTATION_NAMES),
        "mutation_names": list(MUTATION_NAMES),
    }
    payload["mutation_result"] = mutation_result
    payload["payload_commitment"] = payload_commitment(payload)
    if not mutation_result["all_mutations_rejected"]:
        raise Seq32ValueCompatibleBoundaryFrontierError("mutation rejection drift")
    validate_payload(payload)
    return payload


def pretty_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def normalize_repo_output_path(path: pathlib.Path) -> pathlib.Path:
    candidate = path if path.is_absolute() else ROOT / path
    resolved_root = ROOT.resolve()
    resolved_candidate = candidate.resolve(strict=False)
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as err:
        raise Seq32ValueCompatibleBoundaryFrontierError("output path escapes repo root") from err
    return resolved_candidate


def atomic_write_text(path: pathlib.Path, text: str) -> None:
    candidate = path if path.is_absolute() else ROOT / path
    if candidate.exists() and candidate.is_symlink():
        raise Seq32ValueCompatibleBoundaryFrontierError(f"refusing to write symlink: {candidate}")
    path = normalize_repo_output_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix or ".tmp"
    temp_name = f".{path.name}.{secrets.token_hex(8)}.tmp{suffix}"
    temp_path = path.parent / temp_name
    try:
        with tempfile_open(temp_path) as handle:
            handle.write(text)
        os.replace(temp_path, path)
    finally:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


class tempfile_open:
    def __init__(self, path: pathlib.Path):
        self.path = path
        self.handle = None

    def __enter__(self):
        self.handle = open(self.path, "x", encoding="utf-8")
        return self.handle

    def __exit__(self, exc_type, exc, tb):
        if self.handle is not None:
            self.handle.close()
        return False


def tsv_text(payload: dict[str, Any]) -> str:
    row = {column: payload["summary"].get(column, payload.get(column, "")) for column in TSV_COLUMNS}
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerow(row)
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    args = parser.parse_args()

    payload = payload_with_mutations()
    if args.write_json:
        atomic_write_text(args.write_json, pretty_json(payload))
    if args.write_tsv:
        atomic_write_text(args.write_tsv, tsv_text(payload))
    print(pretty_json(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
