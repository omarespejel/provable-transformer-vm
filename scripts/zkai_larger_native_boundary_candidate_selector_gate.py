#!/usr/bin/env python3
"""Select the next larger native attention+MLP boundary candidate."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import copy
import csv
import hashlib
import io
import json
import os
import pathlib
import secrets
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"

ACCOUNTING_PATH = EVIDENCE_DIR / "zkai-larger-native-boundary-candidate-accounting-2026-05.json"
JSON_OUT = EVIDENCE_DIR / "zkai-larger-native-boundary-candidate-selector-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-larger-native-boundary-candidate-selector-2026-05.tsv"

SCHEMA = "zkai-larger-native-boundary-candidate-selector-v1"
DECISION = "GO_SELECT_TWO_HEAD_SEQ32_LARGER_NATIVE_BOUNDARY_IMPLEMENTATION_CANDIDATE"
RESULT = (
    "TWO_HEAD_SEQ32_HAS_1184_LOOKUP_CLAIMS_22916_TYPED_BYTES_"
    "AND_19_354730_TYPED_BYTES_PER_LOOKUP"
)
ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/671"
PAYLOAD_DOMAIN = "ptvm:zkai:larger-native-boundary-candidate-selector:v1"
CLAIM_BOUNDARY = (
    "SELECTS_A_SOURCE_BACKED_LARGER_NATIVE_BOUNDARY_IMPLEMENTATION_CANDIDATE;"
    "_NO_NEW_NATIVE_ATTENTION_MLP_PROOF_OBJECT_NO_NANOZK_OR_FULL_BLOCK_CLAIM"
)

MLP_FUSED_ENVELOPE = "zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.envelope.json"
MLP_TYPED_BYTES = 22_576
MLP_JSON_PROOF_BYTES = 68_560
CURRENT_D8_TWO_PROOF_FRONTIER_TYPED_BYTES = 40_700
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900

EXPECTED_CANDIDATES: dict[str, dict[str, Any]] = {
    "d8_fused_attention": {
        "status": "BASELINE_CURRENT_LOCAL_FRONTIER",
        "attention_gate_path": "zkai-attention-kv-stwo-native-d8-fused-softmax-table-gate-2026-05.json",
        "attention_envelope_path": "zkai-attention-kv-stwo-native-d8-fused-softmax-table-proof-2026-05.envelope.json",
        "attention_typed_bytes": 18_124,
        "attention_json_proof_bytes": 47_698,
        "lookup_claims": 52,
        "source_plus_sidecar_json_proof_bytes": 59_437,
        "fused_saves_vs_source_plus_sidecar_json_bytes": 11_739,
        "fused_to_source_plus_sidecar_ratio": "0.802497",
        "matched_two_proof_frontier_typed_bytes": 40_700,
        "matched_two_proof_frontier_json_bytes": 116_258,
        "typed_bytes_per_lookup_claim": "348.538462",
    },
    "d16_fused_attention": {
        "status": "PARK_TYPED_PER_LOOKUP_WORSE_THAN_D8",
        "attention_gate_path": "zkai-attention-kv-stwo-native-d16-fused-softmax-table-gate-2026-05.json",
        "attention_envelope_path": "zkai-attention-kv-stwo-native-d16-fused-softmax-table-proof-2026-05.envelope.json",
        "attention_typed_bytes": 28_876,
        "attention_json_proof_bytes": 64_503,
        "lookup_claims": 52,
        "source_plus_sidecar_json_proof_bytes": 74_961,
        "fused_saves_vs_source_plus_sidecar_json_bytes": 10_458,
        "fused_to_source_plus_sidecar_ratio": "0.860487",
        "matched_two_proof_frontier_typed_bytes": 51_452,
        "matched_two_proof_frontier_json_bytes": 133_063,
        "typed_bytes_per_lookup_claim": "555.307692",
    },
    "d16_two_head_fused_attention": {
        "status": "PARK_RATIO_WORSE_THAN_SEQ32",
        "attention_gate_path": "zkai-attention-kv-stwo-native-d16-two-head-fused-softmax-table-gate-2026-05.json",
        "attention_envelope_path": "zkai-attention-kv-stwo-native-d16-two-head-fused-softmax-table-proof-2026-05.envelope.json",
        "attention_typed_bytes": 29_908,
        "attention_json_proof_bytes": 78_211,
        "lookup_claims": 104,
        "source_plus_sidecar_json_proof_bytes": 91_596,
        "fused_saves_vs_source_plus_sidecar_json_bytes": 13_385,
        "fused_to_source_plus_sidecar_ratio": "0.853869",
        "matched_two_proof_frontier_typed_bytes": 52_484,
        "matched_two_proof_frontier_json_bytes": 146_771,
        "typed_bytes_per_lookup_claim": "287.576923",
    },
    "d16_two_head_longseq_fused_attention": {
        "status": "PARK_HEAVIER_THAN_SEQ32",
        "attention_gate_path": "zkai-attention-kv-stwo-native-d16-two-head-longseq-fused-softmax-table-gate-2026-05.json",
        "attention_envelope_path": "zkai-attention-kv-stwo-native-d16-two-head-longseq-fused-softmax-table-proof-2026-05.envelope.json",
        "attention_typed_bytes": 31_508,
        "attention_json_proof_bytes": 84_868,
        "lookup_claims": 336,
        "source_plus_sidecar_json_proof_bytes": 108_158,
        "fused_saves_vs_source_plus_sidecar_json_bytes": 23_290,
        "fused_to_source_plus_sidecar_ratio": "0.784667",
        "matched_two_proof_frontier_typed_bytes": 54_084,
        "matched_two_proof_frontier_json_bytes": 153_428,
        "typed_bytes_per_lookup_claim": "93.773810",
    },
    "two_head_seq32_fused_attention": {
        "status": "ATTACK_NEXT_LARGER_NATIVE_BOUNDARY",
        "attention_gate_path": "zkai-attention-kv-stwo-native-two-head-seq32-fused-softmax-table-gate-2026-05.json",
        "attention_envelope_path": "zkai-attention-kv-stwo-native-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json",
        "attention_typed_bytes": 22_916,
        "attention_json_proof_bytes": 66_327,
        "lookup_claims": 1_184,
        "source_plus_sidecar_json_proof_bytes": 98_012,
        "fused_saves_vs_source_plus_sidecar_json_bytes": 31_685,
        "fused_to_source_plus_sidecar_ratio": "0.676723",
        "matched_two_proof_frontier_typed_bytes": 45_492,
        "matched_two_proof_frontier_json_bytes": 134_887,
        "typed_bytes_per_lookup_claim": "19.354730",
    },
}

EXPECTED_SUMMARY = {
    "issue": 671,
    "candidate_count": 5,
    "selected_candidate": "two_head_seq32_fused_attention",
    "selected_status": "ATTACK_NEXT_LARGER_NATIVE_BOUNDARY",
    "selected_attention_typed_bytes": 22_916,
    "selected_attention_json_proof_bytes": 66_327,
    "selected_lookup_claims": 1_184,
    "selected_matched_two_proof_frontier_typed_bytes": 45_492,
    "selected_matched_two_proof_frontier_json_bytes": 134_887,
    "selected_source_plus_sidecar_json_saving_bytes": 31_685,
    "selected_fused_to_source_plus_sidecar_ratio": "0.676723",
    "d8_attention_typed_bytes": 18_124,
    "d8_lookup_claims": 52,
    "d8_matched_two_proof_frontier_typed_bytes": 40_700,
    "selected_extra_typed_bytes_vs_d8_attention": 4_792,
    "selected_extra_lookup_claims_vs_d8": 1_132,
    "selected_attention_typed_growth_vs_d8": "1.264401",
    "selected_lookup_growth_vs_d8": "22.769231",
    "selected_bytes_per_lookup_improvement_vs_d8": "18.007922",
    "selected_incremental_typed_bytes_per_extra_lookup_vs_d8": "4.233216",
    "mlp_fused_typed_bytes": 22_576,
    "mlp_fused_json_proof_bytes": 68_560,
    "nanozk_reported_d128_block_proof_bytes": 6_900,
    "proof_size_comparable_external_rows": 0,
}

EXPECTED_INTERPRETATION = {
    "human_read": (
        "The two-head seq32 attention surface is the strongest next larger-boundary "
        "candidate: lookup claims grow from 52 to 1,184 versus d8, while local typed "
        "attention proof bytes grow only from 18,124 to 22,916."
    ),
    "why_selected": (
        "It has 19.354730 typed bytes per lookup claim, an 18.007922x improvement "
        "over the d8 fused-attention baseline, and the best source-plus-sidecar JSON "
        "fusion ratio in this candidate set at 0.676723x."
    ),
    "next_experiment": (
        "Implement a source-bound native proof object for the selected two-head seq32 "
        "attention surface plus the attention-derived d128 RMSNorm-MLP fused surface, "
        "then compare against its matched 45,492 typed-byte two-proof frontier."
    ),
    "guardrail": (
        "This is not NANOZK-comparable and not a proof-size win: it selects an "
        "implementation candidate using local typed accounting over existing artifacts."
    ),
}

NON_CLAIMS = (
    "not a new native attention-plus-MLP proof object",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not a full transformer block proof",
    "not exact real-valued Softmax",
    "not timing evidence",
    "not production-ready zkML",
)

VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-fused-softmax-table-proof-2026-05.envelope.json docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-fused-softmax-table-proof-2026-05.envelope.json docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-two-head-fused-softmax-table-proof-2026-05.envelope.json docs/engineering/evidence/zkai-attention-kv-stwo-native-d16-two-head-longseq-fused-softmax-table-proof-2026-05.envelope.json docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.envelope.json > docs/engineering/evidence/zkai-larger-native-boundary-candidate-accounting-2026-05.json",
    "python3 scripts/zkai_larger_native_boundary_candidate_selector_gate.py --write-json docs/engineering/evidence/zkai-larger-native-boundary-candidate-selector-2026-05.json --write-tsv docs/engineering/evidence/zkai-larger-native-boundary-candidate-selector-2026-05.tsv",
    "python3 -m py_compile scripts/zkai_larger_native_boundary_candidate_selector_gate.py scripts/tests/test_zkai_larger_native_boundary_candidate_selector_gate.py",
    "python3 -m unittest scripts.tests.test_zkai_larger_native_boundary_candidate_selector_gate",
    "python3 scripts/research_issue_lint.py --repo-root .",
    "python3 scripts/paper/paper_preflight.py --repo-root .",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

TSV_COLUMNS = (
    "candidate_id",
    "status",
    "attention_typed_bytes",
    "attention_json_proof_bytes",
    "lookup_claims",
    "typed_bytes_per_lookup_claim",
    "matched_two_proof_frontier_typed_bytes",
    "matched_two_proof_frontier_json_bytes",
    "fused_to_source_plus_sidecar_ratio",
    "fused_saves_vs_source_plus_sidecar_json_bytes",
)

CORE_KEYS = {
    "schema",
    "decision",
    "result",
    "issue",
    "claim_boundary",
    "source_artifacts",
    "candidates",
    "summary",
    "interpretation",
    "non_claims",
    "validation_commands",
    "payload_commitment",
}
MUTATION_KEYS = {"mutation_inventory", "mutation_result"}
FINAL_KEYS = CORE_KEYS | MUTATION_KEYS

MUTATION_NAMES = (
    "selected_candidate_drift",
    "selected_typed_bytes_drift",
    "selected_lookup_claims_drift",
    "d8_baseline_typed_bytes_drift",
    "bytes_per_lookup_overclaim",
    "nanozk_overclaim",
    "full_block_overclaim",
    "source_artifact_digest_drift",
    "source_artifact_id_drift",
    "source_artifact_path_traversal",
    "source_artifact_envelope_digest_drift",
    "accounting_row_removed",
    "non_claim_removed",
    "non_claim_added",
    "validation_command_drift",
    "interpretation_overclaim",
    "payload_commitment_drift",
)


EXPECTED_ACCOUNTING_IDENTITY = {
    "schema": "zkai-stwo-local-binary-proof-accounting-cli-v1",
    "accounting_domain": "zkai:stwo:local-binary-proof-accounting",
    "accounting_format_version": "v1",
    "accounting_source": "repo_owned_canonical_local_accounting_from_stwo_2_2_0_typed_StarkProof_fields",
    "proof_payload_kind": "utf8_json_object_with_single_stark_proof_field",
    "upstream_stwo_serialization_status": "NOT_UPSTREAM_STWO_SERIALIZATION_LOCAL_ACCOUNTING_RECORD_STREAM_ONLY",
}

EXPECTED_GATE_IDENTITIES = {
    "d8_fused_attention": {
        "schema": "zkai-attention-kv-stwo-native-d8-fused-softmax-table-gate-v1",
        "route_id": "local_stwo_attention_kv_d8_fused_bounded_softmax_table_logup_proof",
        "decision": "GO_NATIVE_STWO_FUSED_ATTENTION_ARITHMETIC_AND_SOFTMAX_TABLE_LOGUP_MEMBERSHIP",
        "fusion_status": "GO_ONE_NATIVE_STWO_PROOF_OBJECT_WITH_ATTENTION_ARITHMETIC_AND_LOGUP_MEMBERSHIP",
        "issue": 478,
    },
    "d16_fused_attention": {
        "schema": "zkai-attention-kv-stwo-native-d16-fused-softmax-table-gate-v1",
        "route_id": "local_stwo_attention_kv_d16_fused_bounded_softmax_table_logup_proof",
        "decision": "GO_NATIVE_STWO_FUSED_ATTENTION_ARITHMETIC_AND_SOFTMAX_TABLE_LOGUP_MEMBERSHIP",
        "fusion_status": "GO_ONE_NATIVE_STWO_PROOF_OBJECT_WITH_ATTENTION_ARITHMETIC_AND_LOGUP_MEMBERSHIP",
        "issue": 501,
    },
    "d16_two_head_fused_attention": {
        "schema": "zkai-attention-kv-stwo-native-d16-two-head-fused-softmax-table-gate-v1",
        "route_id": "local_stwo_attention_kv_d16_two_head_fused_bounded_softmax_table_logup_proof",
        "decision": "GO_NATIVE_STWO_FUSED_ATTENTION_ARITHMETIC_AND_SOFTMAX_TABLE_LOGUP_MEMBERSHIP",
        "fusion_status": "GO_ONE_NATIVE_STWO_PROOF_OBJECT_WITH_ATTENTION_ARITHMETIC_AND_LOGUP_MEMBERSHIP",
        "issue": 521,
    },
    "d16_two_head_longseq_fused_attention": {
        "schema": "zkai-attention-kv-stwo-native-d16-two-head-longseq-fused-softmax-table-gate-v1",
        "route_id": "local_stwo_attention_kv_d16_two_head_longseq_fused_bounded_softmax_table_logup_proof",
        "decision": "GO_NATIVE_STWO_FUSED_ATTENTION_ARITHMETIC_AND_SOFTMAX_TABLE_LOGUP_MEMBERSHIP",
        "fusion_status": "GO_ONE_NATIVE_STWO_PROOF_OBJECT_WITH_ATTENTION_ARITHMETIC_AND_LOGUP_MEMBERSHIP",
        "issue": 525,
    },
    "two_head_seq32_fused_attention": {
        "schema": "zkai-attention-kv-stwo-native-two-head-seq32-fused-softmax-table-gate-v1",
        "route_id": "local_stwo_attention_kv_two_head_seq32_fused_bounded_softmax_table_logup_proof",
        "decision": "GO_NATIVE_STWO_TWO_HEAD_SEQ32_FUSED_ATTENTION_ARITHMETIC_AND_SOFTMAX_TABLE_LOGUP_MEMBERSHIP",
        "fusion_status": "GO_ONE_NATIVE_STWO_PROOF_OBJECT_WITH_ATTENTION_ARITHMETIC_AND_LOGUP_MEMBERSHIP",
        "issue": 537,
    },
}


class LargerNativeBoundaryCandidateSelectorError(ValueError):
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
        raise LargerNativeBoundaryCandidateSelectorError(f"invalid JSON value: {err}") from err


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return "blake2b-256:" + digest.hexdigest()


def refresh_payload_commitment(payload: dict[str, Any]) -> None:
    payload["payload_commitment"] = payload_commitment(payload)


def read_json_and_raw(path: pathlib.Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError as err:
        raise LargerNativeBoundaryCandidateSelectorError(f"failed to read {label}: {err}") from err
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as err:
        raise LargerNativeBoundaryCandidateSelectorError(f"{label} is not valid JSON: {err}") from err
    if not isinstance(value, dict):
        raise LargerNativeBoundaryCandidateSelectorError(f"{label} must be a JSON object")
    return value, raw


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def ratio(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        raise LargerNativeBoundaryCandidateSelectorError("ratio denominator must be positive")
    return f"{numerator / denominator:.6f}"


def row_by_relative_path(accounting: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = accounting.get("rows")
    if not isinstance(rows, list):
        raise LargerNativeBoundaryCandidateSelectorError("accounting rows must be a list")
    by_path: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise LargerNativeBoundaryCandidateSelectorError("accounting row must be object")
        path = row.get("evidence_relative_path")
        if not isinstance(path, str) or not path:
            raise LargerNativeBoundaryCandidateSelectorError("accounting row path must be non-empty")
        if path in by_path:
            raise LargerNativeBoundaryCandidateSelectorError(f"duplicate accounting row: {path}")
        by_path[path] = row
    return by_path


def int_field(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise LargerNativeBoundaryCandidateSelectorError(f"{label} must be integer")
    return value


def str_field(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise LargerNativeBoundaryCandidateSelectorError(f"{label} must be non-empty string")
    return value


def source_descriptor(path: pathlib.Path, raw: bytes, artifact_id: str) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "path": str(path.relative_to(ROOT)),
        "sha256": digest(raw),
        "size_bytes": len(raw),
    }


def expected_source_artifacts() -> tuple[tuple[str, str], ...]:
    artifacts = [("candidate_accounting", str(ACCOUNTING_PATH.relative_to(ROOT)))]
    for candidate_id, expected in EXPECTED_CANDIDATES.items():
        artifacts.append(
            (
                f"{candidate_id}_gate",
                str((EVIDENCE_DIR / expected["attention_gate_path"]).relative_to(ROOT)),
            )
        )
        artifacts.append(
            (
                f"{candidate_id}_envelope",
                str((EVIDENCE_DIR / expected["attention_envelope_path"]).relative_to(ROOT)),
            )
        )
    artifacts.append(
        (
            "mlp_fused_envelope",
            str((EVIDENCE_DIR / MLP_FUSED_ENVELOPE).relative_to(ROOT)),
        )
    )
    return tuple(artifacts)


def validate_identity_fields(
    artifact: dict[str, Any],
    expected: dict[str, Any],
    label: str,
) -> None:
    for key, expected_value in expected.items():
        if artifact.get(key) != expected_value:
            raise LargerNativeBoundaryCandidateSelectorError(f"{label} {key} drift")


def validate_accounting_identity(accounting: dict[str, Any]) -> None:
    validate_identity_fields(accounting, EXPECTED_ACCOUNTING_IDENTITY, "accounting")


def validate_gate_identity(candidate_id: str, gate: dict[str, Any]) -> None:
    expected = EXPECTED_GATE_IDENTITIES.get(candidate_id)
    if expected is None:
        raise LargerNativeBoundaryCandidateSelectorError(f"unknown gate identity {candidate_id}")
    validate_identity_fields(gate, expected, f"{candidate_id} gate")


def verify_envelope_accounting_source(
    row: dict[str, Any],
    envelope_path: pathlib.Path,
    envelope_raw: bytes,
    label: str,
) -> None:
    expected_path = str(envelope_path.relative_to(ROOT))
    if row.get("path") != expected_path:
        raise LargerNativeBoundaryCandidateSelectorError(f"{label} accounting path drift")
    if row.get("envelope_sha256") != digest(envelope_raw):
        raise LargerNativeBoundaryCandidateSelectorError(f"{label} accounting envelope digest drift")


def repo_relative_path(path_text: str, label: str) -> pathlib.Path:
    path = pathlib.Path(path_text)
    if path.is_absolute():
        raise LargerNativeBoundaryCandidateSelectorError(f"{label} must be relative")
    if ".." in path.parts:
        raise LargerNativeBoundaryCandidateSelectorError(f"{label} must not contain traversal")
    candidate = ROOT / path
    try:
        candidate.resolve().relative_to(ROOT.resolve())
    except ValueError as err:
        raise LargerNativeBoundaryCandidateSelectorError(f"{label} escapes repo root") from err
    return candidate


def verified_mlp_accounting(
    accounting_rows: dict[str, dict[str, Any]],
    envelope_raw: bytes,
) -> dict[str, int]:
    row = accounting_rows.get(MLP_FUSED_ENVELOPE)
    if row is None:
        raise LargerNativeBoundaryCandidateSelectorError(
            f"missing accounting row for {MLP_FUSED_ENVELOPE}"
        )
    verify_envelope_accounting_source(
        row,
        EVIDENCE_DIR / MLP_FUSED_ENVELOPE,
        envelope_raw,
        "MLP fused envelope",
    )
    typed_bytes = int_field(
        row.get("local_binary_accounting", {}).get("component_sum_bytes"),
        "MLP fused typed bytes",
    )
    json_proof_bytes = int_field(row.get("proof_json_size_bytes"), "MLP fused JSON bytes")
    if typed_bytes != MLP_TYPED_BYTES:
        raise LargerNativeBoundaryCandidateSelectorError("MLP fused typed bytes drift")
    if json_proof_bytes != MLP_JSON_PROOF_BYTES:
        raise LargerNativeBoundaryCandidateSelectorError("MLP fused JSON bytes drift")
    return {
        "typed_bytes": typed_bytes,
        "json_proof_bytes": json_proof_bytes,
    }


def build_candidate_rows(
    accounting_rows: dict[str, dict[str, Any]],
    source_artifacts: list[dict[str, Any]],
    mlp_accounting: dict[str, int],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for candidate_id, expected in EXPECTED_CANDIDATES.items():
        gate_path = EVIDENCE_DIR / expected["attention_gate_path"]
        gate, gate_raw = read_json_and_raw(gate_path, f"{candidate_id} gate")
        validate_gate_identity(candidate_id, gate)
        source_artifacts.append(source_descriptor(gate_path, gate_raw, f"{candidate_id}_gate"))
        envelope_path = expected["attention_envelope_path"]
        if envelope_path not in accounting_rows:
            raise LargerNativeBoundaryCandidateSelectorError(
                f"missing accounting row for {envelope_path}"
            )
        full_envelope_path = EVIDENCE_DIR / envelope_path
        _, envelope_raw = read_json_and_raw(full_envelope_path, f"{candidate_id} envelope")
        source_artifacts.append(
            source_descriptor(full_envelope_path, envelope_raw, f"{candidate_id}_envelope")
        )
        row = accounting_rows[envelope_path]
        verify_envelope_accounting_source(row, full_envelope_path, envelope_raw, candidate_id)
        accounting_typed = int_field(
            row.get("local_binary_accounting", {}).get("component_sum_bytes"),
            f"{candidate_id} typed bytes",
        )
        accounting_json = int_field(row.get("proof_json_size_bytes"), f"{candidate_id} JSON bytes")
        gate_lookup_claims = int_field(gate.get("lookup_claims"), f"{candidate_id} lookup claims")
        gate_source_plus = int_field(
            gate.get("source_plus_sidecar_raw_proof_bytes"),
            f"{candidate_id} source plus sidecar bytes",
        )
        gate_saving = int_field(
            gate.get("fused_saves_vs_source_plus_sidecar_bytes"),
            f"{candidate_id} fused saving",
        )
        gate_ratio = ratio(accounting_json, gate_source_plus)
        matched_typed = accounting_typed + mlp_accounting["typed_bytes"]
        matched_json = accounting_json + mlp_accounting["json_proof_bytes"]
        candidate = {
            "candidate_id": candidate_id,
            "status": expected["status"],
            "attention_gate_path": expected["attention_gate_path"],
            "attention_envelope_path": envelope_path,
            "attention_typed_bytes": accounting_typed,
            "attention_json_proof_bytes": accounting_json,
            "lookup_claims": gate_lookup_claims,
            "typed_bytes_per_lookup_claim": ratio(accounting_typed, gate_lookup_claims),
            "matched_two_proof_frontier_typed_bytes": matched_typed,
            "matched_two_proof_frontier_json_bytes": matched_json,
            "source_plus_sidecar_json_proof_bytes": gate_source_plus,
            "fused_saves_vs_source_plus_sidecar_json_bytes": gate_saving,
            "fused_to_source_plus_sidecar_ratio": gate_ratio,
        }
        for key, expected_value in expected.items():
            if candidate.get(key) != expected_value:
                raise LargerNativeBoundaryCandidateSelectorError(
                    f"{candidate_id} {key} drift: got {candidate.get(key)!r}, expected {expected_value!r}"
                )
        candidates.append(candidate)
    return candidates


def build_payload() -> dict[str, Any]:
    accounting, accounting_raw = read_json_and_raw(ACCOUNTING_PATH, "candidate accounting")
    validate_accounting_identity(accounting)
    accounting_rows = row_by_relative_path(accounting)
    source_artifacts = [source_descriptor(ACCOUNTING_PATH, accounting_raw, "candidate_accounting")]
    mlp_path = EVIDENCE_DIR / MLP_FUSED_ENVELOPE
    _, mlp_raw = read_json_and_raw(mlp_path, "MLP fused envelope")
    mlp_accounting = verified_mlp_accounting(accounting_rows, mlp_raw)
    candidates = build_candidate_rows(accounting_rows, source_artifacts, mlp_accounting)
    source_artifacts.append(source_descriptor(mlp_path, mlp_raw, "mlp_fused_envelope"))
    by_id = {row["candidate_id"]: row for row in candidates}
    selected = by_id["two_head_seq32_fused_attention"]
    d8 = by_id["d8_fused_attention"]

    summary = {
        "issue": 671,
        "candidate_count": len(candidates),
        "selected_candidate": selected["candidate_id"],
        "selected_status": selected["status"],
        "selected_attention_typed_bytes": selected["attention_typed_bytes"],
        "selected_attention_json_proof_bytes": selected["attention_json_proof_bytes"],
        "selected_lookup_claims": selected["lookup_claims"],
        "selected_matched_two_proof_frontier_typed_bytes": selected[
            "matched_two_proof_frontier_typed_bytes"
        ],
        "selected_matched_two_proof_frontier_json_bytes": selected[
            "matched_two_proof_frontier_json_bytes"
        ],
        "selected_source_plus_sidecar_json_saving_bytes": selected[
            "fused_saves_vs_source_plus_sidecar_json_bytes"
        ],
        "selected_fused_to_source_plus_sidecar_ratio": selected[
            "fused_to_source_plus_sidecar_ratio"
        ],
        "d8_attention_typed_bytes": d8["attention_typed_bytes"],
        "d8_lookup_claims": d8["lookup_claims"],
        "d8_matched_two_proof_frontier_typed_bytes": d8[
            "matched_two_proof_frontier_typed_bytes"
        ],
        "selected_extra_typed_bytes_vs_d8_attention": selected["attention_typed_bytes"]
        - d8["attention_typed_bytes"],
        "selected_extra_lookup_claims_vs_d8": selected["lookup_claims"] - d8["lookup_claims"],
        "selected_attention_typed_growth_vs_d8": ratio(
            selected["attention_typed_bytes"], d8["attention_typed_bytes"]
        ),
        "selected_lookup_growth_vs_d8": ratio(selected["lookup_claims"], d8["lookup_claims"]),
        "selected_bytes_per_lookup_improvement_vs_d8": ratio(
            d8["attention_typed_bytes"] * selected["lookup_claims"],
            d8["lookup_claims"] * selected["attention_typed_bytes"],
        ),
        "selected_incremental_typed_bytes_per_extra_lookup_vs_d8": ratio(
            selected["attention_typed_bytes"] - d8["attention_typed_bytes"],
            selected["lookup_claims"] - d8["lookup_claims"],
        ),
        "mlp_fused_typed_bytes": mlp_accounting["typed_bytes"],
        "mlp_fused_json_proof_bytes": mlp_accounting["json_proof_bytes"],
        "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
        "proof_size_comparable_external_rows": 0,
    }

    payload = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_artifacts": source_artifacts,
        "candidates": candidates,
        "summary": summary,
        "interpretation": EXPECTED_INTERPRETATION,
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
        "payload_commitment": "",
    }
    validate_payload_without_commitment(payload)
    refresh_payload_commitment(payload)
    validate_payload(payload)
    return payload


def validate_payload_without_commitment(payload: dict[str, Any]) -> None:
    keys = set(payload)
    allowed_keys = FINAL_KEYS if "mutation_inventory" in keys or "mutation_result" in keys else CORE_KEYS
    if keys != allowed_keys:
        raise LargerNativeBoundaryCandidateSelectorError(
            f"payload key drift: got {sorted(keys)}, expected {sorted(allowed_keys)}"
        )
    expected_scalars = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    for key, expected in expected_scalars.items():
        if payload.get(key) != expected:
            raise LargerNativeBoundaryCandidateSelectorError(f"{key} drift")
    if tuple(payload.get("non_claims", ())) != NON_CLAIMS:
        raise LargerNativeBoundaryCandidateSelectorError("non-claim inventory drift")
    if tuple(payload.get("validation_commands", ())) != VALIDATION_COMMANDS:
        raise LargerNativeBoundaryCandidateSelectorError("validation command inventory drift")
    if "mutation_inventory" in payload:
        inventory = payload.get("mutation_inventory")
        if not isinstance(inventory, dict):
            raise LargerNativeBoundaryCandidateSelectorError("mutation inventory must be object")
        if inventory.get("mutation_count") != len(MUTATION_NAMES):
            raise LargerNativeBoundaryCandidateSelectorError("mutation count drift")
        if tuple(inventory.get("mutation_names", ())) != MUTATION_NAMES:
            raise LargerNativeBoundaryCandidateSelectorError("mutation name inventory drift")
        mutation_result = payload.get("mutation_result")
        if not isinstance(mutation_result, dict):
            raise LargerNativeBoundaryCandidateSelectorError("mutation result must be object")
        if mutation_result.get("mutations_rejected") != len(MUTATION_NAMES):
            raise LargerNativeBoundaryCandidateSelectorError("mutation rejected count drift")
        if mutation_result.get("all_mutations_rejected") is not True:
            raise LargerNativeBoundaryCandidateSelectorError("mutation rejection drift")
        cases = mutation_result.get("cases")
        if not isinstance(cases, list) or len(cases) != len(MUTATION_NAMES):
            raise LargerNativeBoundaryCandidateSelectorError("mutation case inventory drift")
        for expected_name, case in zip(MUTATION_NAMES, cases, strict=True):
            if not isinstance(case, dict):
                raise LargerNativeBoundaryCandidateSelectorError("mutation case must be object")
            if case.get("name") != expected_name:
                raise LargerNativeBoundaryCandidateSelectorError("mutation case name drift")
            if case.get("rejected") is not True:
                raise LargerNativeBoundaryCandidateSelectorError("mutation case rejection drift")
            if not isinstance(case.get("error"), str) or not case["error"]:
                raise LargerNativeBoundaryCandidateSelectorError("mutation case error drift")
    if payload.get("interpretation") != EXPECTED_INTERPRETATION:
        raise LargerNativeBoundaryCandidateSelectorError("interpretation drift")
    if payload.get("summary") != EXPECTED_SUMMARY:
        raise LargerNativeBoundaryCandidateSelectorError("summary drift")

    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != len(EXPECTED_CANDIDATES):
        raise LargerNativeBoundaryCandidateSelectorError("candidate row count drift")
    seen = set()
    ordered_ids = []
    for row in candidates:
        if not isinstance(row, dict):
            raise LargerNativeBoundaryCandidateSelectorError("candidate row must be object")
        candidate_id = row.get("candidate_id")
        if candidate_id in seen:
            raise LargerNativeBoundaryCandidateSelectorError("duplicate candidate row")
        seen.add(candidate_id)
        ordered_ids.append(candidate_id)
        expected = EXPECTED_CANDIDATES.get(candidate_id)
        if expected is None:
            raise LargerNativeBoundaryCandidateSelectorError(f"unknown candidate row {candidate_id!r}")
        for key, expected_value in expected.items():
            if row.get(key) != expected_value:
                raise LargerNativeBoundaryCandidateSelectorError(
                    f"{candidate_id} {key} drift"
                )
    if tuple(ordered_ids) != tuple(EXPECTED_CANDIDATES):
        raise LargerNativeBoundaryCandidateSelectorError("candidate order drift")

    artifacts = payload.get("source_artifacts")
    expected_artifacts = expected_source_artifacts()
    if not isinstance(artifacts, list) or len(artifacts) != len(expected_artifacts):
        raise LargerNativeBoundaryCandidateSelectorError("source artifact count drift")
    observed_artifacts = []
    seen_artifact_ids = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise LargerNativeBoundaryCandidateSelectorError("source artifact must be object")
        artifact_id = str_field(artifact.get("id"), "source artifact id")
        if artifact_id in seen_artifact_ids:
            raise LargerNativeBoundaryCandidateSelectorError("duplicate source artifact id")
        seen_artifact_ids.add(artifact_id)
        path_text = str_field(artifact.get("path"), "source artifact path")
        repo_relative_path(path_text, "source artifact path")
        observed_artifacts.append((artifact_id, path_text))
    if tuple(observed_artifacts) != expected_artifacts:
        raise LargerNativeBoundaryCandidateSelectorError("source artifact inventory drift")
    for artifact in artifacts:
        path = repo_relative_path(
            str_field(artifact.get("path"), "source artifact path"),
            "source artifact path",
        )
        _, raw = read_json_and_raw(path, f"source artifact {path}")
        if artifact.get("sha256") != digest(raw):
            raise LargerNativeBoundaryCandidateSelectorError("source artifact digest drift")
        if artifact.get("size_bytes") != len(raw):
            raise LargerNativeBoundaryCandidateSelectorError("source artifact size drift")


def validate_payload(payload: dict[str, Any]) -> None:
    validate_payload_without_commitment(payload)
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise LargerNativeBoundaryCandidateSelectorError("payload commitment drift")


def mutation_cases(payload: dict[str, Any]) -> list[tuple[str, Callable[[dict[str, Any]], None]]]:
    return [
        ("selected_candidate_drift", lambda p: p["summary"].__setitem__("selected_candidate", "d16_fused_attention")),
        ("selected_typed_bytes_drift", lambda p: p["summary"].__setitem__("selected_attention_typed_bytes", 22_915)),
        ("selected_lookup_claims_drift", lambda p: p["summary"].__setitem__("selected_lookup_claims", 1_183)),
        ("d8_baseline_typed_bytes_drift", lambda p: p["summary"].__setitem__("d8_attention_typed_bytes", 18_123)),
        (
            "bytes_per_lookup_overclaim",
            lambda p: p["summary"].__setitem__("selected_bytes_per_lookup_improvement_vs_d8", "180.000000"),
        ),
        (
            "nanozk_overclaim",
            lambda p: p.__setitem__("claim_boundary", CLAIM_BOUNDARY + "_NANOZK_WIN"),
        ),
        (
            "full_block_overclaim",
            lambda p: p.__setitem__("result", RESULT + "_FULL_BLOCK_PROOF"),
        ),
        (
            "source_artifact_digest_drift",
            lambda p: p["source_artifacts"][0].__setitem__("sha256", "0" * 64),
        ),
        (
            "source_artifact_id_drift",
            lambda p: p["source_artifacts"][0].__setitem__("id", "external_accounting"),
        ),
        (
            "source_artifact_path_traversal",
            lambda p: p["source_artifacts"][0].__setitem__("path", "../../tmp/external.json"),
        ),
        (
            "source_artifact_envelope_digest_drift",
            lambda p: p["source_artifacts"][2].__setitem__("sha256", "0" * 64),
        ),
        ("accounting_row_removed", lambda p: p["candidates"].pop()),
        ("non_claim_removed", lambda p: p["non_claims"].remove("not a NANOZK proof-size win")),
        ("non_claim_added", lambda p: p["non_claims"].append("not reviewed")),
        ("validation_command_drift", lambda p: p["validation_commands"].pop(0)),
        (
            "interpretation_overclaim",
            lambda p: p["interpretation"].__setitem__("guardrail", "This is a matched NANOZK proof-size win."),
        ),
        ("payload_commitment_drift", lambda p: p.__setitem__("payload_commitment", "blake2b-256:" + "0" * 64)),
    ]


def run_mutations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for name, mutator in mutation_cases(payload):
        mutated = copy.deepcopy(payload)
        mutator(mutated)
        if name != "payload_commitment_drift":
            refresh_payload_commitment(mutated)
        try:
            validate_payload(mutated)
        except LargerNativeBoundaryCandidateSelectorError as err:
            results.append({"name": name, "rejected": True, "error": str(err)})
        else:
            results.append({"name": name, "rejected": False, "error": ""})
    return results


def finalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    mutations = run_mutations(payload)
    mutation_names = tuple(item["name"] for item in mutations)
    if mutation_names != MUTATION_NAMES:
        raise LargerNativeBoundaryCandidateSelectorError("mutation inventory drift")
    rejected = sum(1 for item in mutations if item["rejected"])
    if rejected != len(mutations):
        raise LargerNativeBoundaryCandidateSelectorError(
            f"mutation rejection drift: rejected {rejected} / {len(mutations)}"
        )
    payload = copy.deepcopy(payload)
    payload["mutation_inventory"] = {
        "mutation_count": len(mutations),
        "mutation_names": list(MUTATION_NAMES),
    }
    payload["mutation_result"] = {
        "mutations_rejected": rejected,
        "all_mutations_rejected": rejected == len(mutations),
        "cases": mutations,
    }
    refresh_payload_commitment(payload)
    validate_payload(payload)
    return payload


def tsv_bytes(payload: dict[str, Any]) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in payload["candidates"]:
        writer.writerow({key: row[key] for key in TSV_COLUMNS})
    return output.getvalue().encode("utf-8")


def write_bytes(path: pathlib.Path, data: bytes) -> None:
    if path.exists() and path.is_symlink():
        raise LargerNativeBoundaryCandidateSelectorError(f"refusing to write symlink: {path}")
    tmp = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    fd = None
    try:
        fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as handle:
            fd = None
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        tmp.replace(path)
    except OSError as err:
        raise LargerNativeBoundaryCandidateSelectorError(f"failed to write {path}: {err}") from err
    finally:
        if fd is not None:
            os.close(fd)
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    payload = finalize_payload(build_payload())
    if args.write_json:
        write_bytes(args.write_json, json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    if args.write_tsv:
        write_bytes(args.write_tsv, tsv_bytes(payload))
    print(
        json.dumps(
            {
                "decision": payload["decision"],
                "result": payload["result"],
                "selected_candidate": payload["summary"]["selected_candidate"],
                "selected_attention_typed_bytes": payload["summary"][
                    "selected_attention_typed_bytes"
                ],
                "selected_lookup_claims": payload["summary"]["selected_lookup_claims"],
                "typed_bytes_per_lookup_claim": EXPECTED_CANDIDATES[
                    "two_head_seq32_fused_attention"
                ]["typed_bytes_per_lookup_claim"],
                "mutation_count": payload["mutation_inventory"]["mutation_count"],
                "mutations_rejected": payload["mutation_result"]["mutations_rejected"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
