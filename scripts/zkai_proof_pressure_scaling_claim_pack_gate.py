#!/usr/bin/env python3.10
"""Issue #715 proof-pressure scaling claim-pack gate.

This gate does not generate new proofs. It turns the current checked artifacts
into a harder-to-misread research claim pack:

- attention lookup/table pressure scaling from the controlled component grid;
- fused-vs-split savings across checked rows;
- the current seq32+d128 native boundary and statement-only frontier;
- binary/local typed accounting status;
- external baseline status without pretending non-matched rows are comparable.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import pathlib
import re
import sys
from collections.abc import Callable, Iterable
from typing import Any


if sys.version_info < (3, 10):
    raise RuntimeError("zkai_proof_pressure_scaling_claim_pack_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import zkai_attention_kv_stwo_controlled_component_grid_gate as controlled_grid
from scripts import zkai_attention_kv_fuller_crossing_grid_gate as fuller_grid
from scripts import zkai_claim_audit_comparison_artifacts_gate as claim_audit
from scripts import zkai_d64_external_adapter_surface_probe as d64_external
from scripts import zkai_jolt_atlas_lookup_tensor_comparison_gate as jolt_comparison
from scripts import zkai_native_seq32_attention_mlp_single_proof_gate as native_single
from scripts import zkai_stwo_statement_only_attempt_transcript_gate as statement_only


EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
JSON_OUT = EVIDENCE_DIR / "zkai-proof-pressure-scaling-claim-pack-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-proof-pressure-scaling-claim-pack-2026-05.tsv"

CONTROLLED_GRID_PATH = EVIDENCE_DIR / "zkai-attention-kv-stwo-controlled-component-grid-2026-05.json"
FULLER_CROSSING_GRID_PATH = EVIDENCE_DIR / "zkai-attention-kv-fuller-crossing-grid-2026-05.json"
NATIVE_SINGLE_PATH = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-single-proof-2026-05.json"
STATEMENT_ONLY_PATH = EVIDENCE_DIR / "zkai-stwo-statement-only-attempt-transcript-gate-2026-05.json"
NATIVE_SINGLE_ACCOUNTING_PATH = (
    EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-single-proof-binary-accounting-2026-05.json"
)
STATEMENT_ONLY_ACCOUNTING_PATH = (
    EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-statement-only-attempt-accounting-2026-05.json"
)
ATTENTION_BINARY_ACCOUNTING_PATH = EVIDENCE_DIR / "zkai-attention-kv-stwo-binary-typed-proof-accounting-2026-05.json"
SEQ32_MLP_BINARY_ACCOUNTING_PATH = (
    EVIDENCE_DIR / "zkai-seq32-derived-d128-rmsnorm-mlp-fused-binary-accounting-2026-05.json"
)
D64_EXTERNAL_ADAPTER_PATH = EVIDENCE_DIR / "zkai-d64-external-adapter-surface-probe-2026-05.json"
EZKL_ENVELOPE_PATH = EVIDENCE_DIR / "zkai-ezkl-statement-envelope-benchmark-2026-04.json"
JOLT_COMPARISON_PATH = EVIDENCE_DIR / "zkai-jolt-atlas-lookup-tensor-comparison-2026-05.json"
CLAIM_AUDIT_PATH = EVIDENCE_DIR / "zkai-claim-audit-comparison-artifacts-2026-05.json"
MEDIAN_TIMING_PATH = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-median-timing-2026-05.json"

SCHEMA = "zkai-proof-pressure-scaling-claim-pack-v1"
ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/715"
DECISION = "GO_BOUNDED_SCALE_SIGNAL_SYNTHESIS_KEEP_ISSUE_OPEN_FOR_FULL_GRID"
RESULT = "TEN_TYPED_ATTENTION_ROWS_AND_ELEVEN_ROUTE_ROWS_SCALE_PROOF_PRESSURE_WITH_SEQ32_D128_SAVING_7672"
PAYLOAD_DOMAIN = "ptvm:zkai:proof-pressure-scaling-claim-pack:v1"
CLAIM_BOUNDARY = (
    "BOUNDED_SCALE_SYNTHESIS_FOR_STARK_NATIVE_TRANSFORMER_PROOF_PRESSURE;"
    "USES_CHECKED_LOCAL_ARTIFACTS;"
    "NOT_D64_D128_D256_FULL_GRID_NOT_FULL_BLOCK_NOT_NANOZK_WIN_NOT_EXTERNAL_BENCHMARK"
)

VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_proof_pressure_scaling_claim_pack_gate.py --write-json docs/engineering/evidence/zkai-proof-pressure-scaling-claim-pack-2026-05.json --write-tsv docs/engineering/evidence/zkai-proof-pressure-scaling-claim-pack-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_proof_pressure_scaling_claim_pack_gate.py scripts/tests/test_zkai_proof_pressure_scaling_claim_pack_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_proof_pressure_scaling_claim_pack_gate",
    "python3.10 scripts/zkai_attention_kv_fuller_crossing_grid_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.json --write-tsv docs/engineering/evidence/zkai-attention-kv-fuller-crossing-grid-2026-05.tsv",
    "python3.10 -m unittest scripts.tests.test_zkai_attention_kv_fuller_crossing_grid_gate",
    "python3.10 -m unittest scripts.tests.test_zkai_attention_kv_stwo_controlled_component_grid_gate",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_single_proof_gate",
    "python3.10 -m unittest scripts.tests.test_zkai_stwo_statement_only_attempt_transcript_gate",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_median_timing_gate",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

NON_CLAIMS = (
    "not a d64/d128/d256 attention grid",
    "not a seq64 proof row",
    "not a full transformer block proof",
    "not a NANOZK proof-size win",
    "not a Jolt Atlas proof-size win",
    "not an EZKL proof-size win",
    "not a matched external zkML benchmark",
    "not stable upstream Stwo binary serialization",
    "not exact real-valued Softmax",
    "not production-ready zkML",
)

OPEN_FOLLOWUPS = (
    {
        "id": "d64_d128_d256_grid",
        "status": "OPEN_NEEDED",
        "reason": "Issue #715 asked for d64/d128/d256 where feasible, but the checked attention route grid currently covers d8/d16/d32 plus d64/d128 MLP-side surfaces.",
        "go_gate": "add source-backed d64/d128/d256 or explicit no-go rows without changing the claim boundary",
    },
    {
        "id": "seq64_attention_row",
        "status": "OPEN_NEEDED",
        "reason": "seq64 is not present in the checked attention proof grid.",
        "go_gate": "produce a checked seq64 row or record a concrete resource/no-go blocker",
    },
    {
        "id": "external_apples_to_apples_baseline",
        "status": "OPEN_NEEDED",
        "reason": "EZKL/Jolt/RISC Zero rows are context or statement-boundary rows, not matched proof-size rows for the seq32+d128 native boundary.",
        "go_gate": "one locally reproduced scoped transformer-surface proof in an external stack with matching public/private statement policy",
    },
)

FORBIDDEN_CLAIM_PATTERNS = (
    re.compile(r"\bNANOZK\s+(?:proof-size\s+)?win\b", re.IGNORECASE),
    re.compile(r"\bJolt\s+Atlas\s+(?:proof-size\s+)?win\b", re.IGNORECASE),
    re.compile(r"\bEZKL\s+(?:proof-size\s+)?win\b", re.IGNORECASE),
    re.compile(r"\bfull\s+transformer\s+block\s+proof\b", re.IGNORECASE),
    re.compile(r"\bd64/d128/d256\s+(?:full\s+)?grid\s+complete\b", re.IGNORECASE),
    re.compile(r"\bpublic\s+benchmark\b", re.IGNORECASE),
    re.compile(r"\bstable\s+upstream\s+Stwo\s+binary\s+serialization\b", re.IGNORECASE),
)

MUTATION_NAMES = (
    "lookup_growth_drift",
    "typed_growth_drift",
    "fuller_grid_coverage_drift",
    "fuller_grid_d32_metric_drift",
    "fuller_grid_d32_raw_status_overclaim",
    "explicit_no_go_grid_row_promoted",
    "attention_grid_row_loses_saving",
    "native_single_saving_drift",
    "statement_only_saving_drift",
    "external_baseline_marked_comparable",
    "d64_d128_d256_complete_overclaim",
    "stable_binary_serialization_overclaim",
    "public_benchmark_overclaim",
    "non_claim_removed",
    "source_artifact_digest_drift",
    "source_artifact_missing",
    "validation_command_drift",
    "payload_commitment_drift",
)

TSV_COLUMNS = (
    "row_id",
    "category",
    "status",
    "lookup_claims",
    "typed_bytes",
    "matched_frontier_typed_bytes",
    "typed_saving_bytes",
    "typed_saving_share",
    "json_bytes",
    "binary_raw_bytes",
    "binary_raw_status",
    "comparison_status",
    "source_status",
)

ATTENTION_BINARY_RAW_STATUS = "NOT_AVAILABLE_IN_CONTROLLED_COMPONENT_GRID_ROW"
FULLER_ROUTE_FUSED_BINARY_RAW_STATUS = "NOT_AVAILABLE_IN_FULLER_CROSSING_GRID_ROUTE_ROW"
LOCAL_RECORD_STREAM_STATUS = "LOCAL_RECORD_STREAM_ACCOUNTING_NOT_UPSTREAM_STWO_SERIALIZATION"

EXPLICIT_NO_GO_GRID_ROWS = (
    {
        "profile_id": "d64_attention_grid_no_go",
        "status": "NO_GO_NOT_SOURCE_BACKED_NATIVE_FUSED_ATTENTION_ROW",
        "width": 64,
        "head_counts": [1, 2],
        "sequence_lengths": [16, 32],
        "proof_size_comparable": False,
        "reason": "No checked source-backed native fused attention proof row exists for d64 in the current artifact set.",
    },
    {
        "profile_id": "d128_attention_grid_no_go",
        "status": "NO_GO_NOT_SOURCE_BACKED_NATIVE_FUSED_ATTENTION_ROW",
        "width": 128,
        "head_counts": [1, 2],
        "sequence_lengths": [16, 32],
        "proof_size_comparable": False,
        "reason": "Current d128 evidence is MLP/boundary-side; no matched source-backed native fused attention proof row exists.",
    },
    {
        "profile_id": "d256_attention_grid_no_go",
        "status": "NO_GO_NOT_SOURCE_BACKED_NATIVE_FUSED_ATTENTION_ROW",
        "width": 256,
        "head_counts": [1, 2],
        "sequence_lengths": [16, 32],
        "proof_size_comparable": False,
        "reason": "No checked source-backed native fused attention proof row exists for d256 in the current artifact set.",
    },
)

EXPECTED_SOURCE_ARTIFACT_IDS = (
    "controlled_component_grid",
    "fuller_crossing_grid",
    "native_seq32_d128_single_proof",
    "statement_only_attempt_transcript",
    "native_single_binary_accounting",
    "statement_only_binary_accounting",
    "attention_binary_accounting",
    "seq32_mlp_binary_accounting",
    "d64_external_adapter_surface",
    "ezkl_statement_envelope_benchmark",
    "jolt_atlas_lookup_tensor_comparison",
    "claim_audit_comparison_artifacts",
    "seq32_d128_median_timing",
)


class ProofPressureScalingClaimPackError(ValueError):
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
        raise ProofPressureScalingClaimPackError(f"invalid JSON value: {err}") from err


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return "blake2b-256:" + digest.hexdigest()


def _repo_relative_path(value: str | pathlib.Path, label: str) -> pathlib.PurePosixPath:
    raw = str(value).replace("\\", "/")
    if re.match(r"^[A-Za-z]:", raw):
        raise ProofPressureScalingClaimPackError(f"{label} must be repo-relative")
    path = pathlib.PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts:
        raise ProofPressureScalingClaimPackError(f"{label} must be repo-relative")
    return path


def _full_repo_path(relative_path: pathlib.PurePosixPath) -> pathlib.Path:
    return ROOT.joinpath(*relative_path.parts)


def _assert_no_symlink_components_for_output(path: pathlib.Path, label: str) -> None:
    try:
        relative_parts = path.relative_to(ROOT).parts
    except ValueError as err:
        raise ProofPressureScalingClaimPackError(f"{label} must stay inside repo") from err
    current = ROOT
    for part in relative_parts[:-1]:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ProofPressureScalingClaimPackError(f"{label} must not include symlink components")


def _assert_repo_file(path: pathlib.Path, label: str) -> None:
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(ROOT.resolve(strict=True))
    except (FileNotFoundError, ValueError) as err:
        raise ProofPressureScalingClaimPackError(f"{label} must exist inside repo") from err
    try:
        relative_parts = path.relative_to(ROOT).parts
    except ValueError as err:
        raise ProofPressureScalingClaimPackError(f"{label} must stay inside repo") from err
    current = ROOT
    for part in relative_parts:
        current = current / part
        if current.is_symlink():
            raise ProofPressureScalingClaimPackError(f"{label} must not include symlink components")
    if not path.is_file():
        raise ProofPressureScalingClaimPackError(f"{label} must be a file")


def read_json_source(path: pathlib.Path, label: str) -> tuple[dict[str, Any], dict[str, Any]]:
    _assert_repo_file(path, label)
    raw = path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as err:
        raise ProofPressureScalingClaimPackError(f"{label} must be valid JSON") from err
    if not isinstance(payload, dict):
        raise ProofPressureScalingClaimPackError(f"{label} must be a JSON object")
    source = {
        "id": label,
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha256(raw),
        "size_bytes": len(raw),
    }
    return payload, source


def validate_local_binary_accounting_payload(payload: dict[str, Any], label: str) -> None:
    if payload.get("schema") != "zkai-stwo-local-binary-proof-accounting-cli-v1":
        raise ProofPressureScalingClaimPackError(f"{label} accounting schema drift")
    if payload.get("accounting_format_version") != "v1":
        raise ProofPressureScalingClaimPackError(f"{label} accounting format drift")
    if payload.get("accounting_domain") != "zkai:stwo:local-binary-proof-accounting":
        raise ProofPressureScalingClaimPackError(f"{label} accounting domain drift")
    if (
        payload.get("upstream_stwo_serialization_status")
        != "NOT_UPSTREAM_STWO_SERIALIZATION_LOCAL_ACCOUNTING_RECORD_STREAM_ONLY"
    ):
        raise ProofPressureScalingClaimPackError(f"{label} upstream serialization status drift")
    rows = require_list(payload.get("rows"), f"{label} rows")
    if not rows:
        raise ProofPressureScalingClaimPackError(f"{label} rows must be non-empty")
    for index, row_any in enumerate(rows):
        row = require_dict(row_any, f"{label} rows[{index}]")
        local = require_dict(row.get("local_binary_accounting"), f"{label} rows[{index}] local accounting")
        if local.get("format_domain") != "zkai:stwo:local-binary-proof-accounting":
            raise ProofPressureScalingClaimPackError(f"{label} row accounting domain drift")
        if local.get("format_version") != "v1":
            raise ProofPressureScalingClaimPackError(f"{label} row accounting format drift")
        typed = int_field(local.get("typed_size_estimate_bytes"), f"{label} row typed bytes")
        component_sum = int_field(local.get("component_sum_bytes"), f"{label} row component sum")
        raw_stream = int_field(local.get("record_stream_bytes"), f"{label} row record stream bytes")
        if typed != component_sum or raw_stream <= 0:
            raise ProofPressureScalingClaimPackError(f"{label} row accounting byte drift")


def validate_attention_binary_accounting_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "zkai-attention-kv-stwo-binary-typed-proof-accounting-gate-v1":
        raise ProofPressureScalingClaimPackError("attention binary accounting schema drift")
    if payload.get("decision") != "GO_REPO_OWNED_LOCAL_BINARY_TYPED_ACCOUNTING_FOR_D32_MATCHED_ENVELOPES":
        raise ProofPressureScalingClaimPackError("attention binary accounting decision drift")
    if payload.get("accounting_status") != "GO_CANONICAL_LOCAL_BINARY_TYPED_ACCOUNTING_RECORD_STREAM":
        raise ProofPressureScalingClaimPackError("attention binary accounting status drift")
    if payload.get("binary_serialization_status") != "NO_GO_NOT_UPSTREAM_STWO_PROOF_SERIALIZATION":
        raise ProofPressureScalingClaimPackError("attention binary serialization status drift")
    aggregate = require_dict(payload.get("aggregate"), "attention binary aggregate")
    if int_field(aggregate.get("profiles_checked"), "attention binary profiles") <= 0:
        raise ProofPressureScalingClaimPackError("attention binary profiles drift")


def validate_ezkl_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "zkai-ezkl-statement-envelope-benchmark-v1":
        raise ProofPressureScalingClaimPackError("EZKL benchmark schema drift")
    summary = require_dict(payload.get("summary"), "EZKL summary")
    proof_only = require_dict(summary.get("ezkl-proof-only"), "EZKL proof-only summary")
    envelope = require_dict(summary.get("ezkl-statement-envelope"), "EZKL statement-envelope summary")
    if proof_only.get("baseline_accepted") is not True or envelope.get("baseline_accepted") is not True:
        raise ProofPressureScalingClaimPackError("EZKL baseline acceptance drift")
    if envelope.get("all_mutations_rejected") is not True:
        raise ProofPressureScalingClaimPackError("EZKL statement-envelope mutation drift")
    if int_field(envelope.get("mutations_rejected"), "EZKL envelope rejected") != int_field(
        envelope.get("mutation_count"), "EZKL envelope count"
    ):
        raise ProofPressureScalingClaimPackError("EZKL mutation count drift")


def validate_timing_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema") != "zkai-native-seq32-attention-mlp-median-timing-gate-v1":
        raise ProofPressureScalingClaimPackError("median timing schema drift")
    if payload.get("decision") != "GO_SEQ32_D128_STATEMENT_ONLY_TIMING_CAPTURED_ENGINEERING_LOCAL_ONLY":
        raise ProofPressureScalingClaimPackError("median timing decision drift")
    if (
        payload.get("timing_policy")
        != "median_of_5_in_process_std_time_instant_microsecond_capture_engineering_only"
    ):
        raise ProofPressureScalingClaimPackError("median timing policy drift")
    timing_summary = require_dict(payload.get("timing_summary"), "median timing summary")
    if int_field(timing_summary.get("sample_count"), "median timing sample count") != 5:
        raise ProofPressureScalingClaimPackError("median timing sample count drift")
    target = require_dict(payload.get("target"), "median timing target")
    if int_field(target.get("typed_bytes"), "median timing target typed bytes") != 39_516:
        raise ProofPressureScalingClaimPackError("median timing target drift")


def load_checked_payloads() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    sources: dict[str, dict[str, Any]] = {}

    controlled_payload, source = read_json_source(CONTROLLED_GRID_PATH, "controlled_component_grid")
    controlled_grid.validate_payload(controlled_payload)
    sources[source["id"]] = source

    fuller_payload, source = read_json_source(FULLER_CROSSING_GRID_PATH, "fuller_crossing_grid")
    fuller_grid.validate_result(fuller_payload)
    sources[source["id"]] = source

    native_payload, source = read_json_source(NATIVE_SINGLE_PATH, "native_seq32_d128_single_proof")
    native_single.validate_payload(native_payload)
    sources[source["id"]] = source

    statement_payload, source = read_json_source(STATEMENT_ONLY_PATH, "statement_only_attempt_transcript")
    statement_only.validate_payload(statement_payload)
    sources[source["id"]] = source

    native_accounting, source = read_json_source(NATIVE_SINGLE_ACCOUNTING_PATH, "native_single_binary_accounting")
    validate_local_binary_accounting_payload(native_accounting, "native_single_binary_accounting")
    sources[source["id"]] = source

    statement_accounting, source = read_json_source(STATEMENT_ONLY_ACCOUNTING_PATH, "statement_only_binary_accounting")
    validate_local_binary_accounting_payload(statement_accounting, "statement_only_binary_accounting")
    sources[source["id"]] = source

    attention_accounting, source = read_json_source(ATTENTION_BINARY_ACCOUNTING_PATH, "attention_binary_accounting")
    validate_attention_binary_accounting_payload(attention_accounting)
    sources[source["id"]] = source

    seq32_mlp_accounting, source = read_json_source(SEQ32_MLP_BINARY_ACCOUNTING_PATH, "seq32_mlp_binary_accounting")
    validate_local_binary_accounting_payload(seq32_mlp_accounting, "seq32_mlp_binary_accounting")
    sources[source["id"]] = source

    d64_payload, source = read_json_source(D64_EXTERNAL_ADAPTER_PATH, "d64_external_adapter_surface")
    d64_external.validate_probe(d64_payload)
    sources[source["id"]] = source

    ezkl_payload, source = read_json_source(EZKL_ENVELOPE_PATH, "ezkl_statement_envelope_benchmark")
    validate_ezkl_payload(ezkl_payload)
    sources[source["id"]] = source

    jolt_payload, source = read_json_source(JOLT_COMPARISON_PATH, "jolt_atlas_lookup_tensor_comparison")
    jolt_comparison.validate_payload(jolt_payload)
    sources[source["id"]] = source

    claim_payload, source = read_json_source(CLAIM_AUDIT_PATH, "claim_audit_comparison_artifacts")
    claim_audit.validate_payload(claim_payload)
    sources[source["id"]] = source

    timing_payload, source = read_json_source(MEDIAN_TIMING_PATH, "seq32_d128_median_timing")
    validate_timing_payload(timing_payload)
    sources[source["id"]] = source

    payloads = {
        "controlled": controlled_payload,
        "fuller": fuller_payload,
        "native": native_payload,
        "statement": statement_payload,
        "native_accounting": native_accounting,
        "statement_accounting": statement_accounting,
        "attention_accounting": attention_accounting,
        "seq32_mlp_accounting": seq32_mlp_accounting,
        "d64_external": d64_payload,
        "ezkl": ezkl_payload,
        "jolt": jolt_payload,
        "claim_audit": claim_payload,
        "timing": timing_payload,
    }
    return payloads, sources


def ratio_string(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        raise ProofPressureScalingClaimPackError("ratio denominator must be positive")
    return f"{numerator / denominator:.6f}"


def bytes_per_lookup_string(bytes_value: int, lookup_claims: int) -> str:
    if lookup_claims <= 0:
        raise ProofPressureScalingClaimPackError("lookup_claims must be positive")
    return f"{bytes_value / lookup_claims:.6f}"


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProofPressureScalingClaimPackError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ProofPressureScalingClaimPackError(f"{label} must be a list")
    return value


def int_field(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ProofPressureScalingClaimPackError(f"{label} must be an integer")
    return value


def string_field(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProofPressureScalingClaimPackError(f"{label} must be a non-empty string")
    return value


def _row_by_id(rows: Iterable[dict[str, Any]], profile_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("profile_id") == profile_id:
            return row
    raise ProofPressureScalingClaimPackError(f"missing profile row: {profile_id}")


def build_scale_signal(controlled_payload: dict[str, Any], fuller_payload: dict[str, Any]) -> dict[str, Any]:
    rows = require_list(controlled_payload.get("grid_rows"), "controlled grid rows")
    typed_rows = [require_dict(row, f"grid_rows[{index}]") for index, row in enumerate(rows)]
    baseline = _row_by_id(typed_rows, "d8_single_head_seq8")
    seq32 = _row_by_id(typed_rows, "d8_two_head_seq32")
    d16_two_head_seq16 = _row_by_id(typed_rows, "d16_two_head_seq16")

    baseline_lookup = int_field(baseline.get("lookup_claims"), "baseline lookup claims")
    seq32_lookup = int_field(seq32.get("lookup_claims"), "seq32 lookup claims")
    baseline_typed = int_field(baseline.get("fused_typed_size_bytes"), "baseline typed bytes")
    seq32_typed = int_field(seq32.get("fused_typed_size_bytes"), "seq32 typed bytes")
    seq32_split = int_field(seq32.get("source_plus_sidecar_typed_size_bytes"), "seq32 split typed bytes")

    all_rows_save = all(
        int_field(row.get("typed_savings_bytes"), f"{row.get('profile_id')} typed savings") > 0
        for row in typed_rows
    )
    if not all_rows_save:
        raise ProofPressureScalingClaimPackError("controlled grid contains non-positive fused saving")

    aggregate = require_dict(controlled_payload.get("aggregate"), "controlled aggregate")
    fuller_summary = require_dict(fuller_payload.get("summary"), "fuller grid summary")
    fuller_rows = [require_dict(row, "fuller grid row") for row in require_list(fuller_payload.get("grid_rows"), "fuller grid rows")]
    d32_single_head = next((row for row in fuller_rows if row.get("cell_id") == "d32_h1_seq8"), None)
    if d32_single_head is None:
        raise ProofPressureScalingClaimPackError("fuller grid d32 single-head row missing")
    return {
        "status": "GO_SCALE_SIGNAL_FROM_CHECKED_D8_D16_ATTENTION_GRID",
        "profiles_checked": int_field(aggregate.get("profiles_checked"), "profiles checked"),
        "axes_checked": {
            "widths": sorted({int_field(row.get("key_width"), f"{row.get('profile_id')} width") for row in typed_rows}),
            "head_counts": sorted(
                {int_field(row.get("head_count"), f"{row.get('profile_id')} heads") for row in typed_rows}
            ),
            "steps_per_head": sorted(
                {int_field(row.get("steps_per_head"), f"{row.get('profile_id')} steps") for row in typed_rows}
            ),
        },
        "missing_axes": [
            "d64/d128/d256 attention rows are not present in this checked grid",
            "seq64 attention row is not present in this checked grid",
            "full factorial width/head/sequence crossing is not present",
        ],
        "explicit_no_go_grid_rows": list(EXPLICIT_NO_GO_GRID_ROWS),
        "all_checked_attention_rows_save_typed_bytes": all_rows_save,
        "typed_savings_bytes_total": int_field(
            aggregate.get("typed_savings_bytes_total"), "aggregate typed savings"
        ),
        "typed_saving_share_total": aggregate.get("typed_saving_share_total"),
        "min_typed_saving_share": aggregate.get("min_typed_saving_share"),
        "max_typed_saving_share": aggregate.get("max_typed_saving_share"),
        "seq32_vs_d8_single_head": {
            "baseline_profile_id": "d8_single_head_seq8",
            "scaled_profile_id": "d8_two_head_seq32",
            "lookup_claim_growth": ratio_string(seq32_lookup, baseline_lookup),
            "typed_byte_growth": ratio_string(seq32_typed, baseline_typed),
            "baseline_typed_bytes_per_lookup_claim": bytes_per_lookup_string(baseline_typed, baseline_lookup),
            "seq32_typed_bytes_per_lookup_claim": bytes_per_lookup_string(seq32_typed, seq32_lookup),
            "seq32_lookup_claims": seq32_lookup,
            "seq32_fused_typed_bytes": seq32_typed,
            "seq32_split_typed_bytes": seq32_split,
            "seq32_fused_saving_bytes": int_field(seq32.get("typed_savings_bytes"), "seq32 saving"),
            "seq32_fused_saving_share": seq32.get("typed_saving_share"),
        },
        "largest_checked_combined_row": {
            "profile_id": "d16_two_head_seq16",
            "lookup_claims": int_field(d16_two_head_seq16.get("lookup_claims"), "d16 seq16 lookups"),
            "fused_typed_bytes": int_field(
                d16_two_head_seq16.get("fused_typed_size_bytes"), "d16 seq16 typed"
            ),
            "split_typed_bytes": int_field(
                d16_two_head_seq16.get("source_plus_sidecar_typed_size_bytes"), "d16 seq16 split"
            ),
            "typed_saving_bytes": int_field(d16_two_head_seq16.get("typed_savings_bytes"), "d16 seq16 saving"),
            "typed_saving_share": d16_two_head_seq16.get("typed_saving_share"),
        },
        "fuller_crossing_grid": {
            "status": "GO_45_CELL_D8_D16_D32_ROUTE_GRID_WITH_11_PROVED_CELLS",
            "grid_cell_count": int_field(fuller_summary.get("grid_cell_count"), "fuller grid cells"),
            "proved_cell_count": int_field(fuller_summary.get("proved_cell_count"), "fuller proved cells"),
            "missing_cell_count": int_field(fuller_summary.get("missing_cell_count"), "fuller missing cells"),
            "coverage_share": fuller_summary.get("coverage_share"),
            "proved_crossing_cell_count": int_field(
                fuller_summary.get("proved_crossing_cell_count"), "fuller proved crossing cells"
            ),
            "proved_all_axis_cell_count": int_field(
                fuller_summary.get("proved_all_axis_cell_count"), "fuller proved all-axis cells"
            ),
            "highest_proved_width": max(
                int(key) for key in require_dict(fuller_summary.get("proved_counts_by_width"), "fuller width counts")
            ),
            "next_low_risk_profile_ids": [
                string_field(row.get("profile_id"), "next low-risk profile")
                for row in require_list(fuller_payload.get("next_low_risk_profiles"), "fuller next profiles")
            ],
            "d32_single_head_seq8": {
                "profile_id": string_field(d32_single_head.get("profile_id"), "d32 profile id"),
                "lookup_claims": int_field(d32_single_head.get("lookup_claims"), "d32 lookup claims"),
                "fused_json_proof_size_bytes": int_field(
                    d32_single_head.get("fused_proof_size_bytes"), "d32 fused proof bytes"
                ),
                "fused_binary_raw_proof_bytes": None,
                "fused_binary_raw_status": FULLER_ROUTE_FUSED_BINARY_RAW_STATUS,
                "source_plus_sidecar_raw_proof_bytes": int_field(
                    d32_single_head.get("source_plus_sidecar_raw_proof_bytes"), "d32 source plus sidecar bytes"
                ),
                "fused_to_source_plus_sidecar_ratio": d32_single_head.get("fused_to_source_plus_sidecar_ratio"),
            },
        },
    }


def build_attention_rows(controlled_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in require_list(controlled_payload.get("grid_rows"), "controlled rows"):
        row_obj = require_dict(row, "controlled row")
        fused = int_field(row_obj.get("fused_typed_size_bytes"), "fused typed bytes")
        split = int_field(row_obj.get("source_plus_sidecar_typed_size_bytes"), "split typed bytes")
        saving = int_field(row_obj.get("typed_savings_bytes"), "typed saving")
        if split - fused != saving:
            raise ProofPressureScalingClaimPackError("attention row typed saving arithmetic drift")
        rows.append(
            {
                "row_id": string_field(row_obj.get("profile_id"), "profile id"),
                "category": "attention_fused_vs_split",
                "status": "GO_FUSED_BEATS_SPLIT_ON_TYPED_BYTES",
                "axis_role": row_obj.get("axis_role"),
                "width": int_field(row_obj.get("key_width"), "width"),
                "heads": int_field(row_obj.get("head_count"), "heads"),
                "steps_per_head": int_field(row_obj.get("steps_per_head"), "steps"),
                "lookup_claims": int_field(row_obj.get("lookup_claims"), "lookup claims"),
                "typed_bytes": fused,
                "matched_frontier_typed_bytes": split,
                "typed_saving_bytes": saving,
                "typed_saving_share": row_obj.get("typed_saving_share"),
                "json_bytes": int_field(row_obj.get("fused_json_proof_size_bytes"), "fused JSON"),
                "binary_raw_bytes": None,
                "binary_raw_status": ATTENTION_BINARY_RAW_STATUS,
                "comparison_status": "LOCAL_MATCHED_ATTENTION_SOURCE_PLUS_SIDECAR",
                "source_status": "local_checked",
            }
        )
    return rows


def local_record_stream_bytes(
    accounting_payload: dict[str, Any], evidence_path_fragment: str, label: str, expected_typed_bytes: int
) -> int:
    rows = require_list(accounting_payload.get("rows"), f"{label} accounting rows")
    matches = [
        require_dict(row, f"{label} accounting row")
        for row in rows
        if evidence_path_fragment in string_field(
            require_dict(row, f"{label} accounting row").get("evidence_relative_path"),
            f"{label} evidence path",
        )
    ]
    if len(matches) != 1:
        raise ProofPressureScalingClaimPackError(f"{label} accounting row match drift")
    local = require_dict(matches[0].get("local_binary_accounting"), f"{label} local accounting")
    typed = int_field(local.get("typed_size_estimate_bytes"), f"{label} typed accounting")
    if typed != expected_typed_bytes:
        raise ProofPressureScalingClaimPackError(f"{label} typed accounting drift")
    return int_field(local.get("record_stream_bytes"), f"{label} record stream bytes")


def build_boundary_rows(
    native_payload: dict[str, Any],
    statement_payload: dict[str, Any],
    native_accounting_payload: dict[str, Any],
    statement_accounting_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    native_summary = require_dict(native_payload.get("summary"), "native summary")
    statement_summary = require_dict(statement_payload.get("binding_summary"), "statement summary")
    native_typed = int_field(native_summary.get("native_single_proof_typed_bytes"), "native typed")
    statement_typed = int_field(statement_summary.get("best_typed_bytes"), "statement typed")
    native_record_stream_bytes = local_record_stream_bytes(
        native_accounting_payload,
        "zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json",
        "native single boundary",
        native_typed,
    )
    statement_record_stream_bytes = local_record_stream_bytes(
        statement_accounting_payload,
        "probe-b-statement-only-transcript",
        "statement-only probe B boundary",
        statement_typed,
    )

    return [
        {
            "row_id": "seq32_d128_native_single_proof",
            "category": "native_attention_plus_mlp_boundary",
            "status": "GO_SINGLE_NATIVE_STWO_OBJECT_BEATS_MATCHED_TWO_PROOF_FRONTIER",
            "lookup_claims": int_field(native_summary.get("selected_attention_lookup_claims"), "native lookups"),
            "typed_bytes": native_typed,
            "matched_frontier_typed_bytes": int_field(
                native_summary.get("matched_two_proof_frontier_typed_bytes"), "native frontier"
            ),
            "typed_saving_bytes": int_field(
                native_summary.get("typed_saving_vs_matched_frontier_bytes"), "native saving"
            ),
            "typed_saving_share": native_summary.get("typed_saving_vs_matched_frontier_share"),
            "json_bytes": int_field(native_summary.get("native_single_proof_json_bytes"), "native JSON"),
            "binary_raw_bytes": native_record_stream_bytes,
            "binary_raw_status": LOCAL_RECORD_STREAM_STATUS,
            "comparison_status": "LOCAL_MATCHED_SEQ32_D128_TWO_PROOF_FRONTIER",
            "source_status": "local_checked",
        },
        {
            "row_id": "seq32_d128_statement_only_probe_b",
            "category": "statement_bound_native_attention_plus_mlp_boundary",
            "status": "GO_INNER_POLICY_BOUND_STATEMENT_ONLY_PROFILE_BEATS_MATCHED_FRONTIER",
            "lookup_claims": int_field(native_summary.get("selected_attention_lookup_claims"), "statement lookups"),
            "typed_bytes": statement_typed,
            "matched_frontier_typed_bytes": 47_188,
            "typed_saving_bytes": int_field(
                statement_summary.get("best_typed_saving_vs_matched_two_proof_frontier"),
                "statement saving",
            ),
            "typed_saving_share": ratio_string(
                int_field(
                    statement_summary.get("best_typed_saving_vs_matched_two_proof_frontier"),
                    "statement saving",
                ),
                47_188,
            ),
            "json_bytes": int_field(statement_summary.get("best_json_bytes"), "statement JSON"),
            "binary_raw_bytes": statement_record_stream_bytes,
            "binary_raw_status": LOCAL_RECORD_STREAM_STATUS,
            "comparison_status": "LOCAL_MATCHED_SEQ32_D128_TWO_PROOF_FRONTIER",
            "source_status": "local_checked",
        },
    ]


def build_accounting_status(payloads: dict[str, Any]) -> dict[str, Any]:
    accounting_paths = (
        "native_accounting",
        "statement_accounting",
        "attention_accounting",
        "seq32_mlp_accounting",
    )
    statuses = []
    for key in accounting_paths:
        payload = require_dict(payloads[key], key)
        raw_status = (
            payload.get("upstream_stwo_serialization_status")
            or payload.get("cli_upstream_stwo_serialization_status")
            or payload.get("binary_serialization_status")
        )
        statuses.append(string_field(raw_status, f"{key} status"))
    if any(status != "NOT_UPSTREAM_STWO_SERIALIZATION_LOCAL_ACCOUNTING_RECORD_STREAM_ONLY" for status in statuses[:2]):
        raise ProofPressureScalingClaimPackError("seq32 accounting serialization status drift")
    return {
        "status": "GO_LOCAL_TYPED_ACCOUNTING_PRESENT_NO_GO_UPSTREAM_BINARY_SERIALIZATION_CLAIM",
        "local_binary_accounting_artifact_count": len(accounting_paths),
        "upstream_stwo_serialization_statuses": sorted(set(statuses)),
        "guardrail": "typed/local binary accounting is checked, but this is not stable upstream Stwo wire serialization",
    }


def build_external_baseline_status(payloads: dict[str, Any]) -> list[dict[str, Any]]:
    ezkl = require_dict(payloads["ezkl"], "ezkl payload")
    ezkl_summary = require_dict(ezkl.get("summary"), "ezkl summary")
    ezkl_envelope = require_dict(ezkl_summary.get("ezkl-statement-envelope"), "ezkl envelope summary")

    jolt_summary = require_dict(payloads["jolt"].get("summary"), "jolt summary")
    audit_summary = require_dict(payloads["claim_audit"].get("summary"), "claim audit summary")

    return [
        {
            "system": "EZKL",
            "source_status": "local_checked_statement_boundary_only",
            "comparison_status": "NOT_PROOF_SIZE_COMPARABLE",
            "local_result": "statement envelope rejects metadata relabeling",
            "mutations_rejected": int_field(ezkl_envelope.get("mutations_rejected"), "ezkl mutations rejected"),
            "mutation_count": int_field(ezkl_envelope.get("mutation_count"), "ezkl mutation count"),
        },
        {
            "system": "d64 external adapter surface",
            "source_status": "local_checked_no_go_for_vanilla_external_export",
            "comparison_status": "NOT_PROOF_SIZE_COMPARABLE",
            "local_result": string_field(payloads["d64_external"].get("decision"), "d64 decision"),
            "proof_generated": False,
        },
        {
            "system": "Jolt Atlas",
            "source_status": "repo_available_not_locally_reproduced",
            "comparison_status": "NOT_PROOF_SIZE_COMPARABLE",
            "local_result": string_field(payloads["jolt"].get("result"), "jolt result"),
            "matched_workload": bool(jolt_summary.get("matched_atlas_workload")),
        },
        {
            "system": "NANOZK",
            "source_status": "paper_reported_not_locally_reproduced",
            "comparison_status": "NOT_PROOF_SIZE_COMPARABLE",
            "local_result": "paper context row only",
            "paper_reported_d128_row_bytes": int_field(
                audit_summary.get("nanozk_paper_reported_bytes"), "nanozk paper bytes"
            ),
        },
    ]


def build_summary(rows: list[dict[str, Any]], scale_signal: dict[str, Any]) -> dict[str, Any]:
    attention_rows = [row for row in rows if row["category"] == "attention_fused_vs_split"]
    positive_attention_rows = [row for row in attention_rows if int_field(row["typed_saving_bytes"], "row saving") > 0]
    boundary_rows = [row for row in rows if row["category"] != "attention_fused_vs_split"]
    best_boundary = min(boundary_rows, key=lambda row: int_field(row["typed_bytes"], f"{row['row_id']} typed"))
    return {
        "attention_rows_checked": len(attention_rows),
        "attention_rows_with_positive_typed_saving": len(positive_attention_rows),
        "attention_typed_savings_bytes_total": int_field(
            scale_signal.get("typed_savings_bytes_total"), "total typed savings"
        ),
        "seq32_lookup_growth_vs_d8_single_head": require_dict(
            scale_signal.get("seq32_vs_d8_single_head"), "seq32 signal"
        )["lookup_claim_growth"],
        "seq32_attention_typed_growth_vs_d8_single_head": require_dict(
            scale_signal.get("seq32_vs_d8_single_head"), "seq32 signal"
        )["typed_byte_growth"],
        "fuller_grid_cell_count": require_dict(scale_signal.get("fuller_crossing_grid"), "fuller grid")[
            "grid_cell_count"
        ],
        "fuller_grid_proved_cell_count": require_dict(scale_signal.get("fuller_crossing_grid"), "fuller grid")[
            "proved_cell_count"
        ],
        "fuller_grid_missing_cell_count": require_dict(scale_signal.get("fuller_crossing_grid"), "fuller grid")[
            "missing_cell_count"
        ],
        "explicit_no_go_grid_row_count": len(
            require_list(scale_signal.get("explicit_no_go_grid_rows"), "explicit no-go grid rows")
        ),
        "current_best_inner_policy_bound_row": best_boundary["row_id"],
        "current_best_inner_policy_bound_typed_bytes": best_boundary["typed_bytes"],
        "current_best_saving_vs_47188_frontier_bytes": best_boundary["typed_saving_bytes"],
        "proof_size_comparable_external_rows": 0,
        "open_followup_count": len(OPEN_FOLLOWUPS),
    }


def _flatten_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _flatten_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _flatten_strings(item)


def assert_no_forbidden_positive_claims(payload: dict[str, Any]) -> None:
    positive_fields = {
        "decision": payload.get("decision"),
        "result": payload.get("result"),
        "claim_boundary": payload.get("claim_boundary"),
        "scale_signal": payload.get("scale_signal"),
        "summary": payload.get("summary"),
        "external_baseline_status": payload.get("external_baseline_status"),
    }
    for field, value in positive_fields.items():
        for text in _flatten_strings(value):
            for pattern in FORBIDDEN_CLAIM_PATTERNS:
                if pattern.search(text):
                    raise ProofPressureScalingClaimPackError(f"positive claim overclaim in {field}")


def build_payload(*, include_mutations: bool = True) -> dict[str, Any]:
    payloads, sources = load_checked_payloads()
    scale_signal = build_scale_signal(payloads["controlled"], payloads["fuller"])
    rows = build_attention_rows(payloads["controlled"])
    rows.extend(
        build_boundary_rows(
            payloads["native"],
            payloads["statement"],
            payloads["native_accounting"],
            payloads["statement_accounting"],
        )
    )
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "issue": ISSUE,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "scale_signal": scale_signal,
        "fused_vs_split_rows": rows,
        "accounting_status": build_accounting_status(payloads),
        "external_baseline_status": build_external_baseline_status(payloads),
        "summary": build_summary(rows, scale_signal),
        "open_followups": list(OPEN_FOLLOWUPS),
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
        "source_artifacts": list(sources.values()),
    }
    payload["payload_commitment"] = payload_commitment(payload)
    if include_mutations:
        payload["mutation_results"] = run_mutations(payload)
        payload["mutations_checked"] = len(MUTATION_NAMES)
        payload["mutations_rejected"] = len(MUTATION_NAMES)
        payload["all_mutations_rejected"] = True
        payload["payload_commitment"] = payload_commitment(payload)
    return payload


def _with_refreshed_commitment(payload: dict[str, Any]) -> dict[str, Any]:
    payload["payload_commitment"] = payload_commitment(payload)
    return payload


def mutation_cases(payload: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    def mutate_lookup_growth(item: dict[str, Any]) -> None:
        item["scale_signal"]["seq32_vs_d8_single_head"]["lookup_claim_growth"] = "1.000000"

    def mutate_typed_growth(item: dict[str, Any]) -> None:
        item["scale_signal"]["seq32_vs_d8_single_head"]["typed_byte_growth"] = "22.769231"

    def mutate_fuller_grid_coverage(item: dict[str, Any]) -> None:
        item["scale_signal"]["fuller_crossing_grid"]["proved_cell_count"] = 45

    def mutate_fuller_grid_d32_metric(item: dict[str, Any]) -> None:
        item["scale_signal"]["fuller_crossing_grid"]["d32_single_head_seq8"]["fused_json_proof_size_bytes"] = 1

    def mutate_fuller_grid_d32_raw_status(item: dict[str, Any]) -> None:
        item["scale_signal"]["fuller_crossing_grid"]["d32_single_head_seq8"][
            "fused_binary_raw_status"
        ] = "STABLE_UPSTREAM_STWO_BINARY_SERIALIZATION"

    def mutate_explicit_no_go_grid_row(item: dict[str, Any]) -> None:
        item["scale_signal"]["explicit_no_go_grid_rows"][1]["status"] = "GO_SOURCE_BACKED_NATIVE_FUSED_ATTENTION_ROW"

    def mutate_attention_saving(item: dict[str, Any]) -> None:
        row = next(row for row in item["fused_vs_split_rows"] if row["row_id"] == "d8_two_head_seq32")
        row["typed_saving_bytes"] = 0

    def mutate_native_saving(item: dict[str, Any]) -> None:
        row = next(row for row in item["fused_vs_split_rows"] if row["row_id"] == "seq32_d128_native_single_proof")
        row["typed_saving_bytes"] += 1

    def mutate_statement_saving(item: dict[str, Any]) -> None:
        row = next(row for row in item["fused_vs_split_rows"] if row["row_id"] == "seq32_d128_statement_only_probe_b")
        row["typed_bytes"] -= 1

    def mutate_external_comparable(item: dict[str, Any]) -> None:
        item["external_baseline_status"][0]["comparison_status"] = "PROOF_SIZE_COMPARABLE"

    def mutate_grid_complete(item: dict[str, Any]) -> None:
        item["scale_signal"]["status"] = "GO_D64_D128_D256_FULL_GRID_COMPLETE"

    def mutate_binary(item: dict[str, Any]) -> None:
        item["accounting_status"]["upstream_stwo_serialization_statuses"] = [
            "STABLE_UPSTREAM_STWO_BINARY_SERIALIZATION"
        ]

    def mutate_public_benchmark(item: dict[str, Any]) -> None:
        item["result"] = "PUBLIC_BENCHMARK_WIN"

    def mutate_non_claim(item: dict[str, Any]) -> None:
        item["non_claims"].remove("not a NANOZK proof-size win")

    def mutate_source_digest(item: dict[str, Any]) -> None:
        item["source_artifacts"][0]["sha256"] = "0" * 64

    def mutate_source_missing(item: dict[str, Any]) -> None:
        item["source_artifacts"][0]["path"] = "docs/engineering/evidence/does-not-exist.json"

    def mutate_validation(item: dict[str, Any]) -> None:
        item["validation_commands"] = item["validation_commands"][1:]

    def mutate_commitment(item: dict[str, Any]) -> None:
        item["payload_commitment"] = "blake2b-256:" + ("0" * 64)

    mutations: tuple[tuple[str, Callable[[dict[str, Any]], None]], ...] = (
        ("lookup_growth_drift", mutate_lookup_growth),
        ("typed_growth_drift", mutate_typed_growth),
        ("fuller_grid_coverage_drift", mutate_fuller_grid_coverage),
        ("fuller_grid_d32_metric_drift", mutate_fuller_grid_d32_metric),
        ("fuller_grid_d32_raw_status_overclaim", mutate_fuller_grid_d32_raw_status),
        ("explicit_no_go_grid_row_promoted", mutate_explicit_no_go_grid_row),
        ("attention_grid_row_loses_saving", mutate_attention_saving),
        ("native_single_saving_drift", mutate_native_saving),
        ("statement_only_saving_drift", mutate_statement_saving),
        ("external_baseline_marked_comparable", mutate_external_comparable),
        ("d64_d128_d256_complete_overclaim", mutate_grid_complete),
        ("stable_binary_serialization_overclaim", mutate_binary),
        ("public_benchmark_overclaim", mutate_public_benchmark),
        ("non_claim_removed", mutate_non_claim),
        ("source_artifact_digest_drift", mutate_source_digest),
        ("source_artifact_missing", mutate_source_missing),
        ("validation_command_drift", mutate_validation),
        ("payload_commitment_drift", mutate_commitment),
    )
    if tuple(name for name, _ in mutations) != MUTATION_NAMES:
        raise ProofPressureScalingClaimPackError("mutation name order drift")
    cases = []
    for name, mutate in mutations:
        mutated = copy.deepcopy(payload)
        mutate(mutated)
        if name != "payload_commitment_drift":
            _with_refreshed_commitment(mutated)
        cases.append((name, mutated))
    return cases


def run_mutations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    base = copy.deepcopy(payload)
    for key in ("mutation_results", "mutations_checked", "mutations_rejected", "all_mutations_rejected"):
        base.pop(key, None)
    base["payload_commitment"] = payload_commitment(base)
    for name, mutated in mutation_cases(base):
        try:
            validate_payload(mutated, check_mutations=False)
        except ProofPressureScalingClaimPackError as err:
            results.append({"name": name, "rejected": True, "error": str(err)})
        else:
            results.append({"name": name, "rejected": False, "error": ""})
    return results


def validate_source_artifacts(payload: dict[str, Any]) -> None:
    artifacts = require_list(payload.get("source_artifacts"), "source artifacts")
    ids = []
    for index, artifact_any in enumerate(artifacts):
        artifact = require_dict(artifact_any, f"source_artifacts[{index}]")
        artifact_id = string_field(artifact.get("id"), f"source_artifacts[{index}].id")
        if artifact_id in ids:
            raise ProofPressureScalingClaimPackError("duplicate source artifact id")
        ids.append(artifact_id)
        relative = _repo_relative_path(string_field(artifact.get("path"), f"{artifact_id} path"), f"{artifact_id} path")
        full_path = _full_repo_path(relative)
        _assert_repo_file(full_path, f"{artifact_id} path")
        raw = full_path.read_bytes()
        if artifact.get("sha256") != sha256(raw):
            raise ProofPressureScalingClaimPackError(f"{artifact_id} source digest drift")
        if artifact.get("size_bytes") != len(raw):
            raise ProofPressureScalingClaimPackError(f"{artifact_id} source size drift")
    if tuple(ids) != EXPECTED_SOURCE_ARTIFACT_IDS:
        raise ProofPressureScalingClaimPackError("source artifact id drift")


def validate_rows(payload: dict[str, Any]) -> None:
    rows = require_list(payload.get("fused_vs_split_rows"), "fused rows")
    if len(rows) != 12:
        raise ProofPressureScalingClaimPackError("fused row count drift")
    attention_rows = []
    boundary_rows = []
    for row_any in rows:
        row = require_dict(row_any, "row")
        typed = int_field(row.get("typed_bytes"), "row typed bytes")
        frontier = int_field(row.get("matched_frontier_typed_bytes"), "row matched frontier")
        saving = int_field(row.get("typed_saving_bytes"), "row saving")
        if frontier - typed != saving:
            raise ProofPressureScalingClaimPackError("row typed saving arithmetic drift")
        if saving <= 0:
            raise ProofPressureScalingClaimPackError("row saving must be positive")
        if row.get("comparison_status") == "PROOF_SIZE_COMPARABLE":
            raise ProofPressureScalingClaimPackError("external comparability overclaim")
        if row.get("category") == "attention_fused_vs_split":
            if row.get("binary_raw_bytes") is not None:
                raise ProofPressureScalingClaimPackError("attention row binary raw byte overclaim")
            if row.get("binary_raw_status") != ATTENTION_BINARY_RAW_STATUS:
                raise ProofPressureScalingClaimPackError("attention row binary raw status drift")
            attention_rows.append(row)
        else:
            if int_field(row.get("binary_raw_bytes"), "boundary row binary raw bytes") <= 0:
                raise ProofPressureScalingClaimPackError("boundary row binary raw byte drift")
            if row.get("binary_raw_status") != LOCAL_RECORD_STREAM_STATUS:
                raise ProofPressureScalingClaimPackError("boundary row binary raw status drift")
            boundary_rows.append(row)
    if len(attention_rows) != 10 or len(boundary_rows) != 2:
        raise ProofPressureScalingClaimPackError("row category count drift")
    seq32 = next(row for row in attention_rows if row["row_id"] == "d8_two_head_seq32")
    if seq32["typed_saving_bytes"] != 8_796:
        raise ProofPressureScalingClaimPackError("seq32 attention saving drift")
    native = next(row for row in boundary_rows if row["row_id"] == "seq32_d128_native_single_proof")
    if native["typed_bytes"] != 42_068 or native["typed_saving_bytes"] != 5_120:
        raise ProofPressureScalingClaimPackError("native single boundary metric drift")
    statement = next(row for row in boundary_rows if row["row_id"] == "seq32_d128_statement_only_probe_b")
    if statement["typed_bytes"] != 39_516 or statement["typed_saving_bytes"] != 7_672:
        raise ProofPressureScalingClaimPackError("statement-only boundary metric drift")


def validate_scale_signal(payload: dict[str, Any]) -> None:
    signal = require_dict(payload.get("scale_signal"), "scale signal")
    if signal.get("status") != "GO_SCALE_SIGNAL_FROM_CHECKED_D8_D16_ATTENTION_GRID":
        raise ProofPressureScalingClaimPackError("scale status drift")
    if signal.get("profiles_checked") != 10:
        raise ProofPressureScalingClaimPackError("profile count drift")
    if signal.get("all_checked_attention_rows_save_typed_bytes") is not True:
        raise ProofPressureScalingClaimPackError("attention rows must all save typed bytes")
    axes = require_dict(signal.get("axes_checked"), "axes checked")
    if axes.get("widths") != [8, 16] or axes.get("head_counts") != [1, 2, 4, 8, 16] or axes.get(
        "steps_per_head"
    ) != [8, 16, 32]:
        raise ProofPressureScalingClaimPackError("axis coverage drift")
    missing = require_list(signal.get("missing_axes"), "missing axes")
    if not any("d64/d128/d256" in str(item) for item in missing):
        raise ProofPressureScalingClaimPackError("missing d64/d128/d256 guardrail")
    explicit_no_go_rows = require_list(signal.get("explicit_no_go_grid_rows"), "explicit no-go grid rows")
    if explicit_no_go_rows != list(EXPLICIT_NO_GO_GRID_ROWS):
        raise ProofPressureScalingClaimPackError("explicit no-go grid row drift")
    seq32 = require_dict(signal.get("seq32_vs_d8_single_head"), "seq32 signal")
    if seq32.get("lookup_claim_growth") != "22.769231":
        raise ProofPressureScalingClaimPackError("lookup growth drift")
    if seq32.get("typed_byte_growth") != "1.264401":
        raise ProofPressureScalingClaimPackError("typed growth drift")
    if seq32.get("baseline_typed_bytes_per_lookup_claim") != "348.538462":
        raise ProofPressureScalingClaimPackError("baseline bytes per lookup drift")
    if seq32.get("seq32_typed_bytes_per_lookup_claim") != "19.354730":
        raise ProofPressureScalingClaimPackError("seq32 bytes per lookup drift")
    fuller = require_dict(signal.get("fuller_crossing_grid"), "fuller crossing grid")
    if fuller.get("status") != "GO_45_CELL_D8_D16_D32_ROUTE_GRID_WITH_11_PROVED_CELLS":
        raise ProofPressureScalingClaimPackError("fuller grid status drift")
    if fuller.get("grid_cell_count") != 45 or fuller.get("proved_cell_count") != 11:
        raise ProofPressureScalingClaimPackError("fuller grid coverage drift")
    if fuller.get("missing_cell_count") != 34 or fuller.get("coverage_share") != 0.244444:
        raise ProofPressureScalingClaimPackError("fuller grid missing coverage drift")
    if fuller.get("proved_crossing_cell_count") != 4 or fuller.get("proved_all_axis_cell_count") != 1:
        raise ProofPressureScalingClaimPackError("fuller grid crossing count drift")
    if fuller.get("highest_proved_width") != 32:
        raise ProofPressureScalingClaimPackError("fuller grid width drift")
    if fuller.get("next_low_risk_profile_ids") != [
        "d32_two_head_seq8",
        "d16_two_head_seq32",
        "d32_two_head_seq16",
    ]:
        raise ProofPressureScalingClaimPackError("fuller next profile drift")
    d32 = require_dict(fuller.get("d32_single_head_seq8"), "d32 single-head row")
    if d32.get("profile_id") != "d32_single_head_seq8":
        raise ProofPressureScalingClaimPackError("d32 profile drift")
    if d32.get("lookup_claims") != 52 or d32.get("fused_json_proof_size_bytes") != 107_261:
        raise ProofPressureScalingClaimPackError("d32 metric drift")
    if d32.get("fused_binary_raw_proof_bytes") is not None:
        raise ProofPressureScalingClaimPackError("d32 fused raw byte overclaim")
    if d32.get("fused_binary_raw_status") != FULLER_ROUTE_FUSED_BINARY_RAW_STATUS:
        raise ProofPressureScalingClaimPackError("d32 fused raw status drift")
    if d32.get("source_plus_sidecar_raw_proof_bytes") != 116_682:
        raise ProofPressureScalingClaimPackError("d32 comparator metric drift")
    if d32.get("fused_to_source_plus_sidecar_ratio") != 0.919259:
        raise ProofPressureScalingClaimPackError("d32 ratio drift")


def validate_external_status(payload: dict[str, Any]) -> None:
    rows = require_list(payload.get("external_baseline_status"), "external status")
    if len(rows) != 4:
        raise ProofPressureScalingClaimPackError("external baseline row count drift")
    for row_any in rows:
        row = require_dict(row_any, "external row")
        if row.get("comparison_status") != "NOT_PROOF_SIZE_COMPARABLE":
            raise ProofPressureScalingClaimPackError("external baseline marked comparable")
    systems = {row.get("system") for row in rows}
    if systems != {"EZKL", "d64 external adapter surface", "Jolt Atlas", "NANOZK"}:
        raise ProofPressureScalingClaimPackError("external baseline system drift")


def validate_payload(payload: dict[str, Any], *, check_mutations: bool = True) -> None:
    expected_keys = {
        "schema",
        "issue",
        "decision",
        "result",
        "claim_boundary",
        "scale_signal",
        "fused_vs_split_rows",
        "accounting_status",
        "external_baseline_status",
        "summary",
        "open_followups",
        "non_claims",
        "validation_commands",
        "source_artifacts",
        "payload_commitment",
    }
    if check_mutations:
        expected_keys.update({"mutation_results", "mutations_checked", "mutations_rejected", "all_mutations_rejected"})
    if set(payload) != expected_keys:
        raise ProofPressureScalingClaimPackError("payload key drift")
    if payload.get("schema") != SCHEMA:
        raise ProofPressureScalingClaimPackError("schema drift")
    if payload.get("issue") != ISSUE:
        raise ProofPressureScalingClaimPackError("issue drift")
    if payload.get("decision") != DECISION:
        raise ProofPressureScalingClaimPackError("decision drift")
    if payload.get("result") != RESULT:
        raise ProofPressureScalingClaimPackError("result drift")
    if payload.get("claim_boundary") != CLAIM_BOUNDARY:
        raise ProofPressureScalingClaimPackError("claim boundary drift")
    if payload.get("non_claims") != list(NON_CLAIMS):
        raise ProofPressureScalingClaimPackError("non-claims drift")
    if payload.get("validation_commands") != list(VALIDATION_COMMANDS):
        raise ProofPressureScalingClaimPackError("validation command drift")
    if payload.get("open_followups") != list(OPEN_FOLLOWUPS):
        raise ProofPressureScalingClaimPackError("open followup drift")
    assert_no_forbidden_positive_claims(payload)
    validate_scale_signal(payload)
    validate_rows(payload)
    validate_external_status(payload)
    accounting = require_dict(payload.get("accounting_status"), "accounting status")
    if accounting.get("status") != "GO_LOCAL_TYPED_ACCOUNTING_PRESENT_NO_GO_UPSTREAM_BINARY_SERIALIZATION_CLAIM":
        raise ProofPressureScalingClaimPackError("accounting status drift")
    if "STABLE_UPSTREAM_STWO_BINARY_SERIALIZATION" in accounting.get("upstream_stwo_serialization_statuses", []):
        raise ProofPressureScalingClaimPackError("binary serialization overclaim")
    summary = require_dict(payload.get("summary"), "summary")
    if summary.get("proof_size_comparable_external_rows") != 0:
        raise ProofPressureScalingClaimPackError("proof-size comparable external row drift")
    if summary.get("current_best_inner_policy_bound_typed_bytes") != 39_516:
        raise ProofPressureScalingClaimPackError("best boundary summary drift")
    if summary.get("fuller_grid_proved_cell_count") != 11 or summary.get("fuller_grid_missing_cell_count") != 34:
        raise ProofPressureScalingClaimPackError("fuller grid summary drift")
    if summary.get("explicit_no_go_grid_row_count") != len(EXPLICIT_NO_GO_GRID_ROWS):
        raise ProofPressureScalingClaimPackError("explicit no-go summary drift")
    validate_source_artifacts(payload)
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise ProofPressureScalingClaimPackError("payload commitment drift")
    if check_mutations:
        results = require_list(payload.get("mutation_results"), "mutation results")
        if payload.get("mutations_checked") != len(MUTATION_NAMES) or payload.get("mutations_rejected") != len(
            MUTATION_NAMES
        ):
            raise ProofPressureScalingClaimPackError("mutation count drift")
        if payload.get("all_mutations_rejected") is not True:
            raise ProofPressureScalingClaimPackError("mutation rejection drift")
        if [item.get("name") for item in results] != list(MUTATION_NAMES):
            raise ProofPressureScalingClaimPackError("mutation result name drift")
        if any(item.get("rejected") is not True for item in results):
            raise ProofPressureScalingClaimPackError("mutation result acceptance drift")


def render_tsv(payload: dict[str, Any]) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=TSV_COLUMNS, extrasaction="ignore", delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in payload["fused_vs_split_rows"]:
        writer.writerow(row)
    for row in require_dict(payload["scale_signal"], "scale signal")["explicit_no_go_grid_rows"]:
        writer.writerow(
            {
                "row_id": row["profile_id"],
                "category": "explicit_no_go_grid_row",
                "status": row["status"],
                "comparison_status": "NOT_PROOF_SIZE_COMPARABLE",
                "source_status": "explicit_no_go",
            }
        )
    for row in payload["external_baseline_status"]:
        writer.writerow(
            {
                "row_id": row["system"],
                "category": "external_baseline_status",
                "status": row["comparison_status"],
                "comparison_status": row["comparison_status"],
                "source_status": row["source_status"],
            }
        )
    return out.getvalue()


def require_output_path(path: pathlib.Path, expected: pathlib.Path) -> pathlib.Path:
    relative = _repo_relative_path(path, "output path")
    full_path = _full_repo_path(relative)
    if full_path != expected:
        raise ProofPressureScalingClaimPackError(f"output path must be {expected.relative_to(ROOT)}")
    _assert_no_symlink_components_for_output(full_path, "output path")
    if full_path.exists() and full_path.is_symlink():
        raise ProofPressureScalingClaimPackError("output path must not be a symlink")
    parent = full_path.parent
    parent.mkdir(parents=True, exist_ok=True)
    try:
        parent.resolve(strict=True).relative_to(EVIDENCE_DIR.resolve(strict=True))
    except ValueError as err:
        raise ProofPressureScalingClaimPackError("output path must stay under docs/engineering/evidence") from err
    return full_path


def atomic_write_text(path: pathlib.Path, text: str) -> None:
    temp = path.with_name(f".{path.name}.tmp")
    temp.write_text(text, encoding="utf-8", newline="\n")
    temp.replace(path)


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path, tsv_path: pathlib.Path) -> None:
    validate_payload(payload)
    json_out = require_output_path(json_path, JSON_OUT)
    tsv_out = require_output_path(tsv_path, TSV_OUT)
    atomic_write_text(json_out, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    atomic_write_text(tsv_out, render_tsv(payload))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    args = parser.parse_args(argv)

    payload = build_payload()
    validate_payload(payload)

    if args.write_json or args.write_tsv:
        if not args.write_json or not args.write_tsv:
            raise ProofPressureScalingClaimPackError("--write-json and --write-tsv must be provided together")
        write_outputs(payload, args.write_json, args.write_tsv)
    else:
        print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
