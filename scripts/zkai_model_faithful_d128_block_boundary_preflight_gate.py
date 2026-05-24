#!/usr/bin/env python3.10
"""Preflight the model-faithful d128 block-boundary decision for issue #715."""

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
import tempfile
from typing import Any, Callable


if sys.version_info < (3, 10):
    raise RuntimeError("zkai_model_faithful_d128_block_boundary_preflight_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs" / "engineering"
EVIDENCE_DIR = DOCS_DIR / "evidence"

COLOCATED_SINGLE = EVIDENCE_DIR / "zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.json"
MODEL_SINGLE = EVIDENCE_DIR / "zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05.json"
MODEL_SINGLE_ACCOUNTING = (
    EVIDENCE_DIR / "zkai-native-d128-seq32-attention-derived-mlp-single-proof-binary-accounting-2026-05.json"
)
MODEL_SPLIT_ACCOUNTING = (
    EVIDENCE_DIR / "zkai-native-d128-seq32-attention-derived-mlp-split-frontier-binary-accounting-2026-05.json"
)
MODEL_MLP_SURFACE = EVIDENCE_DIR / "zkai-d128-attention-derived-d128-native-mlp-surface-2026-05.json"
MODEL_INPUT = EVIDENCE_DIR / "zkai-d128-attention-derived-d128-input-2026-05.json"
SLOPE_TABLE = EVIDENCE_DIR / "zkai-proof-pressure-slope-table-2026-05.json"

JSON_OUT = EVIDENCE_DIR / "zkai-model-faithful-d128-block-boundary-preflight-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-model-faithful-d128-block-boundary-preflight-2026-05.tsv"
MD_OUT = DOCS_DIR / "zkai-model-faithful-d128-block-boundary-preflight-2026-05-24.md"

SCHEMA = "zkai-model-faithful-d128-block-boundary-preflight-v1"
DECISION = "GO_MODEL_FAITHFUL_D128_BLOCK_BOUNDARY_PREFLIGHT"
RESULT = "ATTACK_MINIMAL_BLOCK_BOUNDARY_AROUND_MODEL_FAITHFUL_D128_ATTENTION_DERIVED_MLP"
ISSUE = 715
PAYLOAD_DOMAIN = "ptvm:zkai:model-faithful-d128-block-boundary-preflight:v1"
PRIMARY_NEXT_GATE = "minimal_scoped_d128_attention_derived_block_boundary_wrapper"
FALLBACK_GATE = "d128_h2_seq64_sequence_stress_if_block_wrapper_no_go"
RECOMMENDED_ACTION = "IMPLEMENT_MINIMAL_SCOPED_BLOCK_BOUNDARY_AROUND_MODEL_FAITHFUL_D128_ROUTE"
CLAIM_BOUNDARY = (
    "MODEL_FAITHFUL_D128_SEQ32_ATTENTION_DERIVED_MLP_PREFLIGHT;"
    "NEXT_GATE_IS_MINIMAL_SCOPED_BLOCK_BOUNDARY;"
    "NOT_FULL_BLOCK_NOT_SPEED_CLAIM_NOT_EXTERNAL_COMPARISON"
)
TIMING_POLICY = "proof_size_and_statement_binding_preflight_only_no_new_timing_claim"

EXPECTED_SOURCES = {
    "previous_colocated_single": {
        "path": COLOCATED_SINGLE,
        "schema": "zkai-native-d128-seq32-attention-mlp-single-proof-gate-v1",
        "decision": "GO_COLOCATED_D128_SEQ32_ATTENTION_MLP_SINGLE_PROOF_BEATS_SCOPED_SPLIT_FRONTIER",
        "result": "SCOPED_D128_SEQ32_SINGLE_PROOF_SAVES_15881_JSON_AND_4608_TYPED_BYTES",
        "sha256": "be132be07bbb493ae549ff0315e326c058b9713998ccbe3ed564a69cefc43866",
        "bytes": 9_116,
    },
    "model_faithful_single": {
        "path": MODEL_SINGLE,
        "schema": "zkai-native-d128-seq32-attention-derived-mlp-single-proof-gate-v1",
        "decision": "GO_D128_SEQ32_ATTENTION_DERIVED_MLP_SINGLE_PROOF_BEATS_MATCHED_SPLIT_FRONTIER",
        "result": "D128_ATTENTION_DERIVED_SINGLE_PROOF_SAVES_18913_JSON_AND_5168_TYPED_BYTES",
        "sha256": "0a2200bce9ebbe93d17a030dbd6c7222efccb06bb26ebde97999bfc938469447",
        "bytes": 7_719,
    },
    "model_faithful_single_accounting": {
        "path": MODEL_SINGLE_ACCOUNTING,
        "schema": "zkai-stwo-local-binary-proof-accounting-cli-v1",
        "decision": None,
        "result": None,
        "sha256": "8f0e8ce78fea0be66c98b41aae5c8658083194fce137321a79f094b32956baef",
        "bytes": 5_966,
    },
    "model_faithful_split_accounting": {
        "path": MODEL_SPLIT_ACCOUNTING,
        "schema": "zkai-stwo-local-binary-proof-accounting-cli-v1",
        "decision": None,
        "result": None,
        "sha256": "13f31f75ff1dd95aee63853abee201ac4a7615604ad3a4b30e412dc73c966ee9",
        "bytes": 10_714,
    },
    "model_faithful_mlp_surface": {
        "path": MODEL_MLP_SURFACE,
        "schema": "zkai-d128-attention-derived-d128-native-mlp-surface-gate-v1",
        "decision": "GO_D128_ATTENTION_DERIVED_D128_MLP_SURFACE_INPUTS_READY_FOR_NATIVE_PROOF",
        "result": "D128_ATTENTION_DERIVED_D128_MLP_SURFACE_REGENERATED_FROM_VALUE_COMPATIBLE_ATTENTION_OUTPUTS",
        "sha256": "be2d7edd41f0e8552da4e3a6a2a691db0853fc139a86a1f96ecd04547986685b",
        "bytes": 3_891,
    },
    "model_faithful_input": {
        "path": MODEL_INPUT,
        "schema": "zkai-d128-attention-derived-d128-input-gate-v1",
        "decision": "GO_D128_ATTENTION_DERIVED_D128_INPUT_FIXTURE",
        "result": "GO_VALUE_CONNECTED_D128_ATTENTION_DERIVED_D128_INPUT_ARTIFACT",
        "sha256": "fa37beb536e976b462accdeb07934c0fd5a1470ab331c4e3a2c66a02fdc59a66",
        "bytes": 37_718,
    },
    "slope_table": {
        "path": SLOPE_TABLE,
        "schema": "zkai-proof-pressure-slope-table-v1",
        "decision": "GO_PAPER_SLOPE_TABLE_WITH_SCOPED_BLOCK_NEXT_GATE",
        "result": None,
        "sha256": "1bae947f83b9fd49238751391c8445e575e05b464bc6af47a079be4cd1782e2e",
        "bytes": 10_939,
    },
}

ROW_IDS = (
    "previous_colocated_d128_boundary",
    "model_faithful_d128_boundary",
    "attention_derived_mlp_surface",
    "d128_sequence_stress_context",
    "next_block_boundary_gate",
)

TSV_COLUMNS = (
    "row_id",
    "status",
    "metric_scope",
    "single_or_fused_bytes",
    "split_or_reference_bytes",
    "saving_bytes",
    "ratio",
    "action",
)

NON_CLAIMS = (
    "not a full transformer block proof",
    "not a public proving-speed benchmark",
    "not a NANOZK proof-size win",
    "not a matched external zkML comparison",
    "not exact real-valued Softmax",
    "not full autoregressive inference",
    "not production-throughput evidence",
)

VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_model_faithful_d128_block_boundary_preflight_gate.py --write-json docs/engineering/evidence/zkai-model-faithful-d128-block-boundary-preflight-2026-05.json --write-tsv docs/engineering/evidence/zkai-model-faithful-d128-block-boundary-preflight-2026-05.tsv --write-md docs/engineering/zkai-model-faithful-d128-block-boundary-preflight-2026-05-24.md",
    "python3.10 -m py_compile scripts/zkai_model_faithful_d128_block_boundary_preflight_gate.py scripts/tests/test_zkai_model_faithful_d128_block_boundary_preflight_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_model_faithful_d128_block_boundary_preflight_gate",
    "git diff --check",
    "just gate-fast",
    "just gate",
)


class ModelFaithfulD128BlockBoundaryPreflightError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode(
            "utf-8"
        )
    except (TypeError, ValueError) as err:
        raise ModelFaithfulD128BlockBoundaryPreflightError("payload contains non-canonical JSON value") from err


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return "blake2b-256:" + digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ModelFaithfulD128BlockBoundaryPreflightError(message)


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ModelFaithfulD128BlockBoundaryPreflightError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ModelFaithfulD128BlockBoundaryPreflightError(f"{label} must be a list")
    return value


def require_int_field(container: dict[str, Any], key: str, label: str) -> int:
    value = container.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ModelFaithfulD128BlockBoundaryPreflightError(f"{label} must be an integer")
    return value


def require_str_field(container: dict[str, Any], key: str, label: str) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not value:
        raise ModelFaithfulD128BlockBoundaryPreflightError(f"{label} must be a non-empty string")
    return value


def require_number_field(container: dict[str, Any], key: str, label: str) -> float:
    value = container.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ModelFaithfulD128BlockBoundaryPreflightError(f"{label} must be a number")
    return float(value)


def read_repo_file(path: pathlib.Path, label: str) -> bytes:
    root = ROOT.resolve()
    candidate = pathlib.Path(os.path.abspath(path if path.is_absolute() else ROOT / path))
    try:
        relative = candidate.relative_to(root)
    except ValueError as err:
        raise ModelFaithfulD128BlockBoundaryPreflightError(f"{label} escapes repo root: {path}") from err
    current = root
    try:
        for part in relative.parts:
            current = current / part
            if stat.S_ISLNK(current.lstat().st_mode):
                raise ModelFaithfulD128BlockBoundaryPreflightError(f"{label} must not traverse symlinks")
        fd = os.open(candidate, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            file_stat = os.fstat(fd)
            if not stat.S_ISREG(file_stat.st_mode):
                raise ModelFaithfulD128BlockBoundaryPreflightError(f"{label} must be a regular file")
            with os.fdopen(fd, "rb") as handle:
                fd = None
                return handle.read()
        finally:
            if fd is not None:
                os.close(fd)
    except OSError as err:
        raise ModelFaithfulD128BlockBoundaryPreflightError(f"failed to read {label}: {err}") from err


def read_json(path: pathlib.Path, label: str) -> tuple[dict[str, Any], bytes]:
    raw = read_repo_file(path, label)
    def reject_non_finite_constant(value: str) -> None:
        raise ModelFaithfulD128BlockBoundaryPreflightError(f"{label} contains non-finite JSON constant: {value}")

    try:
        value = json.loads(raw, parse_constant=reject_non_finite_constant)
    except json.JSONDecodeError as err:
        raise ModelFaithfulD128BlockBoundaryPreflightError(f"{label} is not valid JSON: {err}") from err
    except UnicodeDecodeError as err:
        raise ModelFaithfulD128BlockBoundaryPreflightError(f"{label} is not valid UTF-8 JSON: {err}") from err
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value, raw


def load_sources() -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    payloads: dict[str, dict[str, Any]] = {}
    descriptors: list[dict[str, Any]] = []
    for source_id, expected in EXPECTED_SOURCES.items():
        payload, raw = read_json(expected["path"], source_id)
        descriptor = {
            "id": source_id,
            "path": expected["path"].relative_to(ROOT).as_posix(),
            "schema": payload.get("schema"),
            "decision": payload.get("decision"),
            "result": payload.get("result"),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
        payloads[source_id] = payload
        descriptors.append(descriptor)
    return payloads, descriptors


def accounting_typed_bytes(accounting: dict[str, Any]) -> int:
    rows = accounting.get("rows")
    require(isinstance(rows, list) and rows, "accounting rows missing")
    total = 0
    for index, row in enumerate(rows):
        require(isinstance(row, dict), f"accounting row {index} must be object")
        local = row.get("local_binary_accounting")
        require(isinstance(local, dict), f"accounting row {index} local accounting missing")
        value = local.get("component_sum_bytes")
        require(isinstance(value, int) and not isinstance(value, bool), f"accounting row {index} typed bytes drift")
        total += value
    return total


def slope_row(slope: dict[str, Any], row_id: str) -> dict[str, Any]:
    rows = slope.get("rows")
    require(isinstance(rows, list), "slope rows missing")
    for row in rows:
        require(isinstance(row, dict), "slope row must be object")
        if row.get("row_id") == row_id:
            return row
    raise ModelFaithfulD128BlockBoundaryPreflightError(f"slope row not found: {row_id}")


def build_rows(sources: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    previous = require_dict(
        require_dict(sources.get("previous_colocated_single"), "previous colocated source").get("summary"),
        "previous colocated summary",
    )
    model = require_dict(
        require_dict(sources.get("model_faithful_single"), "model faithful source").get("summary"),
        "model faithful summary",
    )
    mlp = require_dict(
        require_dict(sources.get("model_faithful_mlp_surface"), "model faithful MLP surface source").get("summary"),
        "model faithful MLP surface summary",
    )
    sequence = slope_row(
        require_dict(sources.get("slope_table"), "slope table source"),
        "d128_h2_seq32_to_seq64_sequence_axis",
    )

    return [
        {
            "row_id": "previous_colocated_d128_boundary",
            "status": "BASELINE_SUPERSEDED_BY_MODEL_FAITHFUL_BINDING",
            "metric_scope": "proof_json_and_typed_bytes",
            "single_or_fused_bytes": require_int_field(
                previous, "single_proof_json_bytes", "previous single proof JSON bytes"
            ),
            "split_or_reference_bytes": require_int_field(
                previous, "split_proof_json_bytes", "previous split proof JSON bytes"
            ),
            "saving_bytes": require_int_field(previous, "proof_json_saving_bytes", "previous proof JSON saving"),
            "ratio": require_str_field(previous, "proof_json_ratio", "previous proof JSON ratio"),
            "typed_bytes": require_int_field(previous, "single_typed_bytes", "previous typed bytes"),
            "typed_saving_bytes": require_int_field(previous, "typed_saving_bytes", "previous typed saving"),
            "typed_ratio": require_str_field(previous, "typed_ratio", "previous typed ratio"),
            "action": "keep_as_regression_baseline_not_current_claim_anchor",
        },
        {
            "row_id": "model_faithful_d128_boundary",
            "status": "CURRENT_CLAIM_ANCHOR_GO",
            "metric_scope": "proof_json_and_typed_bytes",
            "single_or_fused_bytes": require_int_field(
                model, "single_proof_json_bytes", "model faithful single proof JSON bytes"
            ),
            "split_or_reference_bytes": require_int_field(
                model, "split_proof_json_bytes", "model faithful split proof JSON bytes"
            ),
            "saving_bytes": require_int_field(model, "proof_json_saving_bytes", "model faithful proof JSON saving"),
            "ratio": require_str_field(model, "proof_json_ratio", "model faithful proof JSON ratio"),
            "typed_bytes": require_int_field(model, "single_typed_bytes", "model faithful typed bytes"),
            "typed_saving_bytes": require_int_field(model, "typed_saving_bytes", "model faithful typed saving"),
            "typed_ratio": require_str_field(model, "typed_ratio", "model faithful typed ratio"),
            "action": "use_as_anchor_for_minimal_scoped_block_boundary",
        },
        {
            "row_id": "attention_derived_mlp_surface",
            "status": "VALUE_BOUND_MLP_SURFACE_GO",
            "metric_scope": "component_surface_typed_bytes",
            "single_or_fused_bytes": require_int_field(mlp, "fused_typed_bytes", "MLP fused typed bytes"),
            "split_or_reference_bytes": require_int_field(
                mlp, "separate_component_typed_bytes", "MLP separate typed bytes"
            ),
            "saving_bytes": require_int_field(mlp, "typed_saving_bytes", "MLP typed saving"),
            "ratio": f"{require_number_field(mlp, 'fused_typed_ratio', 'MLP fused typed ratio'):.6f}",
            "adapter_mismatches": require_int_field(
                mlp, "d128_attention_adapter_mismatches", "MLP adapter mismatches"
            ),
            "action": "preserve_value_derivation_and_residual_surface_in_next_boundary",
        },
        {
            "row_id": "d128_sequence_stress_context",
            "status": "FALLBACK_STRESS_PATH_NOT_PRIMARY",
            "metric_scope": "raw_proof_bytes_growth",
            "single_or_fused_bytes": require_int_field(
                sequence, "target_fused_proof_bytes", "sequence target fused proof bytes"
            ),
            "split_or_reference_bytes": require_int_field(
                sequence, "target_split_proof_bytes", "sequence target split proof bytes"
            ),
            "saving_bytes": require_int_field(sequence, "target_saving_bytes", "sequence target saving bytes"),
            "ratio": f"{require_number_field(sequence, 'target_fused_to_split_ratio', 'sequence target ratio'):.6f}",
            "lookup_growth": require_number_field(sequence, "lookup_growth", "sequence lookup growth"),
            "trace_growth": require_number_field(sequence, "trace_growth", "sequence trace growth"),
            "fused_proof_growth": require_number_field(
                sequence, "fused_proof_growth", "sequence fused proof growth"
            ),
            "action": "run_d128_h2_seq64_if_minimal_block_wrapper_becomes_no_go",
        },
        {
            "row_id": "next_block_boundary_gate",
            "status": "ATTACK_NEXT",
            "metric_scope": "decision_gate",
            "single_or_fused_bytes": None,
            "split_or_reference_bytes": None,
            "saving_bytes": None,
            "ratio": None,
            "action": RECOMMENDED_ACTION,
        },
    ]


def build_payload() -> dict[str, Any]:
    sources, descriptors = load_sources()
    rows = build_rows(sources)
    row_map = {row["row_id"]: row for row in rows}
    previous = row_map["previous_colocated_d128_boundary"]
    model = row_map["model_faithful_d128_boundary"]
    mlp = row_map["attention_derived_mlp_surface"]
    sequence = row_map["d128_sequence_stress_context"]
    single_typed = accounting_typed_bytes(sources["model_faithful_single_accounting"])
    split_typed = accounting_typed_bytes(sources["model_faithful_split_accounting"])

    payload = {
        "schema": SCHEMA,
        "issue": ISSUE,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "timing_policy": TIMING_POLICY,
        "primary_next_gate": PRIMARY_NEXT_GATE,
        "fallback_gate": FALLBACK_GATE,
        "recommended_action": RECOMMENDED_ACTION,
        "source_artifacts": descriptors,
        "summary": {
            "current_anchor": "model_faithful_d128_boundary",
            "previous_colocated_single_proof_json_bytes": previous["single_or_fused_bytes"],
            "previous_colocated_split_proof_json_bytes": previous["split_or_reference_bytes"],
            "previous_colocated_proof_json_saving_bytes": previous["saving_bytes"],
            "previous_colocated_typed_bytes": previous["typed_bytes"],
            "previous_colocated_typed_saving_bytes": previous["typed_saving_bytes"],
            "model_faithful_single_proof_json_bytes": model["single_or_fused_bytes"],
            "model_faithful_split_proof_json_bytes": model["split_or_reference_bytes"],
            "model_faithful_proof_json_saving_bytes": model["saving_bytes"],
            "model_faithful_typed_bytes": model["typed_bytes"],
            "model_faithful_split_typed_bytes": split_typed,
            "model_faithful_typed_saving_bytes": model["typed_saving_bytes"],
            "model_faithful_accounting_typed_bytes": single_typed,
            "model_faithful_json_delta_vs_colocated_bytes": model["single_or_fused_bytes"] - previous["single_or_fused_bytes"],
            "model_faithful_typed_delta_vs_colocated_bytes": model["typed_bytes"] - previous["typed_bytes"],
            "model_faithful_typed_saving_delta_vs_colocated_bytes": model["typed_saving_bytes"] - previous["typed_saving_bytes"],
            "legacy_non_derivation_caveat_removed": True,
            "mlp_surface_adapter_mismatches": mlp["adapter_mismatches"],
            "mlp_surface_typed_saving_bytes": mlp["saving_bytes"],
            "d128_sequence_lookup_growth": sequence["lookup_growth"],
            "d128_sequence_trace_growth": sequence["trace_growth"],
            "d128_sequence_fused_proof_growth": sequence["fused_proof_growth"],
            "proof_size_comparable_external_rows": 0,
            "paper_claim_status": "GO_NEXT_MINIMAL_BLOCK_BOUNDARY_PREFLIGHT_NOT_FULL_BLOCK",
        },
        "go_gate": [
            "the minimal block-boundary wrapper preserves the model-faithful d128 attention-derived MLP binding",
            "the new proof beats the matched local split frontier before any external comparison",
            "source digests, statement commitments, accounting bytes, and non-claims remain pinned",
            "mutation gates reject relabeling, stale co-location claims, full-block claims, and external benchmark claims",
        ],
        "no_go_gate": [
            "the wrapper only works by dropping the attention-derived MLP input binding",
            "the scoped proof is equal or heavier than its matched split frontier",
            "the next story requires treating d128 seq64 or d256 as the primary claim",
            "the result needs speed, NANOZK, full-block, or production-throughput wording to sound interesting",
        ],
        "rows": rows,
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    payload["mutation_results"] = run_mutations(payload)
    payload["mutations_checked"] = len(payload["mutation_results"])
    payload["mutations_rejected"] = sum(1 for result in payload["mutation_results"] if result["rejected"])
    payload["all_mutations_rejected"] = payload["mutations_rejected"] == payload["mutations_checked"]
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload)
    return payload


def validate_source_artifacts(payload: dict[str, Any]) -> None:
    artifacts = payload.get("source_artifacts")
    require(isinstance(artifacts, list), "source artifacts missing")
    require(len(artifacts) == len(EXPECTED_SOURCES), "source artifact count drift")
    normalized_artifacts = [require_dict(artifact, "source artifact") for artifact in artifacts]
    ids = [artifact.get("id") for artifact in normalized_artifacts]
    require(ids == list(EXPECTED_SOURCES), "source artifact order drift")
    for artifact in normalized_artifacts:
        artifact_id = artifact.get("id")
        require(isinstance(artifact_id, str) and artifact_id in EXPECTED_SOURCES, "source artifact id drift")
        expected = EXPECTED_SOURCES[artifact_id]
        for key in ("schema", "decision", "result", "sha256", "bytes"):
            require(artifact.get(key) == expected[key], f"{artifact_id} {key} drift")
        require(artifact.get("path") == expected["path"].relative_to(ROOT).as_posix(), f"{artifact_id} path drift")


def validate_rows(payload: dict[str, Any]) -> None:
    rows = payload.get("rows")
    require(isinstance(rows, list), "rows missing")
    require(len(rows) == len(ROW_IDS), "row count drift")
    normalized_rows = [require_dict(row, f"row {index}") for index, row in enumerate(rows)]
    require([row.get("row_id") for row in normalized_rows] == list(ROW_IDS), "row order drift")
    by_id = {row["row_id"]: row for row in normalized_rows}
    for row_id in ROW_IDS:
        row = by_id[row_id]
        for key in ("row_id", "status", "metric_scope", "action"):
            require(isinstance(row.get(key), str) and row[key], f"{row_id}.{key} missing")

    previous = by_id["previous_colocated_d128_boundary"]
    require(previous.get("single_or_fused_bytes") == 504_518, "previous JSON bytes drift")
    require(previous.get("split_or_reference_bytes") == 520_399, "previous split JSON bytes drift")
    require(previous.get("saving_bytes") == 15_881, "previous JSON saving drift")
    require(previous.get("typed_bytes") == 204_564, "previous typed bytes drift")
    require(previous.get("typed_saving_bytes") == 4_608, "previous typed saving drift")

    model = by_id["model_faithful_d128_boundary"]
    require(model.get("single_or_fused_bytes") == 503_567, "model JSON bytes drift")
    require(model.get("split_or_reference_bytes") == 522_480, "model split JSON bytes drift")
    require(model.get("saving_bytes") == 18_913, "model JSON saving drift")
    require(model.get("typed_bytes") == 204_564, "model typed bytes drift")
    require(model.get("typed_saving_bytes") == 5_168, "model typed saving drift")

    mlp = by_id["attention_derived_mlp_surface"]
    require(mlp.get("adapter_mismatches") == 0, "MLP adapter mismatch drift")
    require(mlp.get("saving_bytes") == 32_144, "MLP typed saving drift")

    sequence = by_id["d128_sequence_stress_context"]
    require(sequence.get("lookup_growth") == 3.72973, "sequence lookup growth drift")
    require(sequence.get("trace_growth") == 4.0, "sequence trace growth drift")
    require(sequence.get("fused_proof_growth") == 1.080697, "sequence proof growth drift")
    require(
        isinstance(sequence.get("action"), str) and sequence["action"].startswith("run_d128_h2_seq64_if"),
        "sequence must stay fallback",
    )

    next_gate = by_id["next_block_boundary_gate"]
    require(next_gate.get("action") == RECOMMENDED_ACTION, "next gate action drift")


def validate_payload(
    payload: dict[str, Any],
    *,
    require_mutations: bool = True,
    require_commitment: bool = True,
) -> None:
    require(payload.get("schema") == SCHEMA, "schema drift")
    require(payload.get("issue") == ISSUE, "issue drift")
    require(payload.get("decision") == DECISION, "decision drift")
    require(payload.get("result") == RESULT, "result drift")
    claim_boundary = payload.get("claim_boundary")
    require(isinstance(claim_boundary, str), "claim boundary missing")
    for token in ("MODEL_FAITHFUL_D128", "NOT_FULL_BLOCK", "NOT_SPEED_CLAIM", "NOT_EXTERNAL_COMPARISON"):
        require(token in claim_boundary, f"claim boundary missing {token}")
    require(payload.get("primary_next_gate") == PRIMARY_NEXT_GATE, "primary next gate drift")
    require(payload.get("fallback_gate") == FALLBACK_GATE, "fallback gate drift")
    require(payload.get("recommended_action") == RECOMMENDED_ACTION, "recommended action drift")
    require(payload.get("timing_policy") == TIMING_POLICY, "timing policy drift")
    validate_source_artifacts(payload)
    validate_rows(payload)

    summary = payload.get("summary")
    require(isinstance(summary, dict), "summary missing")
    expected_summary = {
        "current_anchor": "model_faithful_d128_boundary",
        "previous_colocated_single_proof_json_bytes": 504_518,
        "previous_colocated_split_proof_json_bytes": 520_399,
        "previous_colocated_proof_json_saving_bytes": 15_881,
        "previous_colocated_typed_bytes": 204_564,
        "previous_colocated_typed_saving_bytes": 4_608,
        "model_faithful_single_proof_json_bytes": 503_567,
        "model_faithful_split_proof_json_bytes": 522_480,
        "model_faithful_proof_json_saving_bytes": 18_913,
        "model_faithful_typed_bytes": 204_564,
        "model_faithful_split_typed_bytes": 209_732,
        "model_faithful_typed_saving_bytes": 5_168,
        "model_faithful_accounting_typed_bytes": 204_564,
        "model_faithful_json_delta_vs_colocated_bytes": -951,
        "model_faithful_typed_delta_vs_colocated_bytes": 0,
        "model_faithful_typed_saving_delta_vs_colocated_bytes": 560,
        "legacy_non_derivation_caveat_removed": True,
        "mlp_surface_adapter_mismatches": 0,
        "mlp_surface_typed_saving_bytes": 32_144,
        "d128_sequence_lookup_growth": 3.72973,
        "d128_sequence_trace_growth": 4.0,
        "d128_sequence_fused_proof_growth": 1.080697,
        "proof_size_comparable_external_rows": 0,
        "paper_claim_status": "GO_NEXT_MINIMAL_BLOCK_BOUNDARY_PREFLIGHT_NOT_FULL_BLOCK",
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary.{key} drift")
    non_claims = payload.get("non_claims")
    require(isinstance(non_claims, list), "non-claims drift")
    require("not enforcing d128 MLP input derivation from attention outputs" not in non_claims, "legacy caveat leaked")
    require(non_claims == list(NON_CLAIMS), "non-claims drift")
    require(payload.get("validation_commands") == list(VALIDATION_COMMANDS), "validation commands drift")
    go_gate = payload.get("go_gate")
    no_go_gate = payload.get("no_go_gate")
    require(isinstance(go_gate, list) and len(go_gate) == 4, "GO gate drift")
    require(all(isinstance(item, str) and item for item in go_gate), "GO gate drift")
    require(isinstance(no_go_gate, list) and len(no_go_gate) == 4, "NO-GO gate drift")
    require(all(isinstance(item, str) and item for item in no_go_gate), "NO-GO gate drift")
    require(any("matched local split frontier" in item for item in go_gate), "GO gate must stay local")
    require(any("full-block" in item for item in no_go_gate), "NO-GO gate must reject full-block promotion")

    if require_mutations:
        results = payload.get("mutation_results")
        require(isinstance(results, list), "mutation results missing")
        require(payload.get("mutations_checked") == len(MUTATIONS), "mutation count drift")
        require(payload.get("mutations_rejected") == len(MUTATIONS), "mutation rejected count drift")
        require(payload.get("all_mutations_rejected") is True, "all mutations rejected drift")
        require(len(results) == len(MUTATIONS), "mutation result count drift")
        mutation_names = [name for name, _ in MUTATIONS]
        normalized_results = [require_dict(result, f"mutation result {index}") for index, result in enumerate(results)]
        require([result.get("name") for result in normalized_results] == mutation_names, "mutation order drift")
        for result in normalized_results:
            name = result.get("name")
            require(isinstance(name, str) and name, "mutation name missing")
            require(result.get("rejected") is True, f"{name} mutation acceptance drift")
            require(isinstance(result.get("error"), str) and result["error"], f"{name} mutation error missing")
    if require_commitment:
        require(payload.get("payload_commitment") == payload_commitment(payload), "payload commitment drift")


Mutation = tuple[str, Callable[[dict[str, Any]], None]]


def _remove_first_non_claim(payload: dict[str, Any]) -> None:
    payload["non_claims"] = payload["non_claims"][1:]


def _drop_row_field(payload: dict[str, Any]) -> None:
    payload["rows"][1].pop("action", None)


def _payload_commitment_drift(payload: dict[str, Any]) -> None:
    payload["payload_commitment"] = "blake2b-256:" + ("0" * 64)


MUTATIONS: tuple[Mutation, ...] = (
    ("source_digest_drift", lambda p: p["source_artifacts"][1].__setitem__("sha256", "0" * 64)),
    ("issue_drift", lambda p: p.__setitem__("issue", ISSUE + 1)),
    ("decision_drift", lambda p: p.__setitem__("decision", "NO_GO")),
    ("primary_gate_drift", lambda p: p.__setitem__("primary_next_gate", FALLBACK_GATE)),
    ("fallback_promoted_to_primary", lambda p: p.__setitem__("recommended_action", "IMPLEMENT_D128_H2_SEQ64_FIRST")),
    ("previous_metric_drift", lambda p: p["summary"].__setitem__("previous_colocated_typed_saving_bytes", 0)),
    ("model_metric_drift", lambda p: p["summary"].__setitem__("model_faithful_typed_saving_bytes", 0)),
    ("legacy_caveat_reintroduced", lambda p: p["non_claims"].append("not enforcing d128 MLP input derivation from attention outputs")),
    ("full_block_overclaim", lambda p: p.__setitem__("claim_boundary", p["claim_boundary"].replace("NOT_FULL_BLOCK_", ""))),
    ("external_overclaim", lambda p: p.__setitem__("claim_boundary", p["claim_boundary"].replace("NOT_EXTERNAL_COMPARISON", "EXTERNAL_COMPARISON"))),
    ("sequence_slope_drift", lambda p: p["rows"][3].__setitem__("fused_proof_growth", 4.0)),
    ("non_claim_removed", _remove_first_non_claim),
    ("row_missing_required_field", _drop_row_field),
    ("validation_command_drift", lambda p: p["validation_commands"].append("echo unsafe")),
    ("payload_commitment_drift", _payload_commitment_drift),
)


def run_mutations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for name, mutate in MUTATIONS:
        candidate = copy.deepcopy(payload)
        candidate.pop("mutation_results", None)
        candidate.pop("mutations_checked", None)
        candidate.pop("mutations_rejected", None)
        candidate.pop("all_mutations_rejected", None)
        mutate(candidate)
        if name != "payload_commitment_drift":
            candidate["payload_commitment"] = payload_commitment(candidate)
        try:
            validate_payload(candidate, require_mutations=False)
        except ModelFaithfulD128BlockBoundaryPreflightError as err:
            results.append({"name": name, "rejected": True, "error": str(err)})
        else:
            results.append({"name": name, "rejected": False, "error": None})
    return results


def resolve_output_path(path: pathlib.Path, base_dir: pathlib.Path) -> pathlib.Path:
    candidate = path if path.is_absolute() else ROOT / path
    if candidate.exists() and candidate.is_symlink():
        raise ModelFaithfulD128BlockBoundaryPreflightError(f"refusing to write through symlink: {candidate}")
    try:
        resolved = candidate.resolve(strict=False)
        base_resolved = base_dir.resolve()
    except OSError as err:
        raise ModelFaithfulD128BlockBoundaryPreflightError(f"unable to resolve output path: {path}") from err
    if resolved != base_resolved and base_resolved not in resolved.parents:
        raise ModelFaithfulD128BlockBoundaryPreflightError(f"output path must stay inside {base_dir}")
    if resolved == base_resolved or (resolved.exists() and resolved.is_dir()):
        raise ModelFaithfulD128BlockBoundaryPreflightError(f"output path must be a file: {resolved}")
    if resolved.parent.exists() and not resolved.parent.is_dir():
        raise ModelFaithfulD128BlockBoundaryPreflightError(f"output path parent must be a directory: {resolved}")
    try:
        resolved.parent.relative_to(base_resolved)
    except ValueError as err:
        raise ModelFaithfulD128BlockBoundaryPreflightError(f"output path parent must stay inside {base_dir}") from err
    return resolved


def format_cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def checked_output_paths(json_path: pathlib.Path, tsv_path: pathlib.Path, md_path: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    resolved = (
        resolve_output_path(json_path, EVIDENCE_DIR),
        resolve_output_path(tsv_path, EVIDENCE_DIR),
        resolve_output_path(md_path, DOCS_DIR),
    )
    if len({str(path) for path in resolved}) != len(resolved):
        raise ModelFaithfulD128BlockBoundaryPreflightError("output paths must be different files")
    return resolved


def atomic_write_text(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        tmp_path = pathlib.Path(handle.name)
        handle.write(text)
    os.replace(tmp_path, path)


def write_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    output = resolve_output_path(path, EVIDENCE_DIR)
    validate_payload(payload)
    atomic_write_text(output, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_tsv(path: pathlib.Path, payload: dict[str, Any]) -> None:
    output = resolve_output_path(path, EVIDENCE_DIR)
    validate_payload(payload)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in require_list(payload.get("rows"), "rows"):
        row_obj = require_dict(row, "row")
        writer.writerow({column: format_cell(row_obj.get(column, "")) for column in TSV_COLUMNS})
    atomic_write_text(output, buffer.getvalue())


def write_md(path: pathlib.Path, payload: dict[str, Any]) -> None:
    output = resolve_output_path(path, DOCS_DIR)
    validate_payload(payload)
    summary = payload["summary"]
    rows = [
        "| row | status | scope | bytes | reference | saving | ratio | action |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in payload["rows"]:
        rows.append(
            "| {row_id} | `{status}` | {scope} | {bytes} | {reference} | {saving} | {ratio} | {action} |".format(
                row_id=row["row_id"].replace("_", " "),
                status=row["status"],
                scope=row["metric_scope"],
                bytes=f"`{row['single_or_fused_bytes']:,}`" if isinstance(row.get("single_or_fused_bytes"), int) else "",
                reference=f"`{row['split_or_reference_bytes']:,}`" if isinstance(row.get("split_or_reference_bytes"), int) else "",
                saving=f"`{row['saving_bytes']:,}`" if isinstance(row.get("saving_bytes"), int) else "",
                ratio=f"`{row['ratio']}`" if row.get("ratio") is not None else "",
                action=row["action"].replace("_", " "),
            )
        )
    non_claims = "\n".join(f"- {claim}." for claim in NON_CLAIMS)
    commands = "\n".join(VALIDATION_COMMANDS)
    md = f"""# Model-Faithful D128 Block-Boundary Preflight

Issue: #{ISSUE}

## Decision

`{DECISION}`

Result:

`{RESULT}`

This is a decision artifact, not a new proof object. It makes the next research
step explicit after PR #744: use the model-faithful d128 attention-derived MLP
single proof as the anchor for the smallest scoped block-boundary wrapper.

## Human Meaning

The previous scoped d128 row was useful, but it still had a limiting caveat:
the MLP input was co-located with attention rather than derived from the actual
d128 attention output artifact. The new model-faithful row removes that caveat and
still beats the matched split frontier.

The important detail is that the stronger binding did not make the proof
heavier. The single proof JSON moved by `{summary['model_faithful_json_delta_vs_colocated_bytes']:,}`
bytes versus the co-located row, typed bytes stayed flat, and the typed saving
improved by `{summary['model_faithful_typed_saving_delta_vs_colocated_bytes']:,}` bytes.

That makes the next gate a block-boundary question, not a bigger-grid question:
can we wrap the already-bound d128 attention-derived MLP route into the smallest
scoped block boundary without losing the local proof-size win?

## Checked Rows

{chr(10).join(rows)}

## GO Gate

- the minimal block-boundary wrapper preserves the model-faithful d128 attention-derived MLP binding;
- the new proof beats the matched local split frontier before any external comparison;
- source digests, statement commitments, accounting bytes, and non-claims remain pinned;
- mutation gates reject relabeling, stale co-location claims, full-block claims, and external benchmark claims.

## NO-GO Gate

- the wrapper only works by dropping the attention-derived MLP input binding;
- the scoped proof is equal or heavier than its matched split frontier;
- the next story requires treating d128 seq64 or d256 as the primary claim;
- the result needs speed, NANOZK, full-block, or production-throughput wording to sound interesting.

## Evidence

- JSON: `docs/engineering/evidence/zkai-model-faithful-d128-block-boundary-preflight-2026-05.json`
- TSV: `docs/engineering/evidence/zkai-model-faithful-d128-block-boundary-preflight-2026-05.tsv`
- Model-faithful anchor: `docs/engineering/evidence/zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05.json`
- Prior co-located row: `docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.json`
- Slope table: `docs/engineering/evidence/zkai-proof-pressure-slope-table-2026-05.json`

The gate rejects `{len(MUTATIONS)} / {len(MUTATIONS)}` mutation cases covering
source drift, issue drift, primary-gate drift, metric drift, legacy caveat
reintroduction, full-block overclaim, external-comparison overclaim, sequence
slope drift, non-claim drift, validation-command drift, and payload-commitment
drift.

## Non-Claims

{non_claims}

## Reproduce

```bash
{commands}
```
"""
    atomic_write_text(output, md)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path, default=JSON_OUT)
    parser.add_argument("--write-tsv", type=pathlib.Path, default=TSV_OUT)
    parser.add_argument("--write-md", type=pathlib.Path, default=MD_OUT)
    args = parser.parse_args()
    json_path, tsv_path, md_path = checked_output_paths(args.write_json, args.write_tsv, args.write_md)
    payload = build_payload()
    write_json(json_path, payload)
    write_tsv(tsv_path, payload)
    write_md(md_path, payload)
    print(
        f"{DECISION}: {payload['mutations_rejected']}/{payload['mutations_checked']} mutations rejected; "
        f"next={PRIMARY_NEXT_GATE}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
