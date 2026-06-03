#!/usr/bin/env python3
"""Deterministic layout-schedule sweep gate for issue #757.

This gate records the first measured Stwo-AI route-layout experiment on the
existing `d8_two_head_seq32` fused attention surface. The schedules are fixed
before proof generation and bound through the source input and statement
commitments. The result is intentionally narrow: `chunk4` is smaller than the
checked alternating baseline on this one surface.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import pathlib
import sys
import tempfile
from io import StringIO
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import zkai_attention_kv_fused_softmax_table_section_delta_gate as section_delta

EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
DOCS_DIR = ROOT / "docs" / "engineering"
BASELINE_ENVELOPE = (
    EVIDENCE_DIR / "zkai-attention-kv-stwo-native-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json"
)
JSON_OUT = EVIDENCE_DIR / "zkai-stwo-ai-two-head-seq32-layout-schedule-sweep-2026-06.json"
TSV_OUT = EVIDENCE_DIR / "zkai-stwo-ai-two-head-seq32-layout-schedule-sweep-2026-06.tsv"
MD_OUT = DOCS_DIR / "zkai-stwo-ai-two-head-seq32-layout-schedule-sweep-2026-06-04.md"

SCHEMA = "zkai-stwo-ai-two-head-seq32-layout-schedule-sweep-v1"
ISSUE = 757
SOURCE_SURFACE_ISSUE = 537
DECISION = "GO_DETERMINISTIC_CHUNK4_LAYOUT_REDUCES_FUSED_PROOF_BYTES_NO_STWO_FORK"
ROUTE_ID = "local_stwo_ai_two_head_seq32_layout_schedule_sweep"
CLAIM_BOUNDARY = (
    "EXPERIMENTAL_D8_TWO_HEAD_SEQ32_DETERMINISTIC_SOURCE_LAYOUT_SCHEDULE_SWEEP_"
    "SAME_WORKLOAD_ONE_SMALL_PROOF_SIZE_REDUCTION_NOT_A_STWO_FORK_NOT_D64_PROMOTION"
)
FORK_STATUS = "NO_GO_FORK_STWO_FROM_CHUNK4_SWEEP"
PROMOTION_STATUS = "NO_GO_D64_PROMOTION_UNTIL_POLICY_IS_IMPLEMENTED_AND_REPROVED_ON_D64"
TIMING_POLICY = "no_timing_claim_no_public_benchmark"
VERIFY_POLICY = "best_chunk4_envelope_native_verify_required"
BASELINE_POLICY = "checked_existing_alternating_input_step_order"
BEST_SCHEDULE_ID = "chunk4"
BASELINE_PROOF_SIZE_BYTES = 66_327
EXPECTED_BEST_PROOF_SIZE_BYTES = 65_998
EXPECTED_BEST_SAVING_BYTES = 329
EXPECTED_BEST_OPENING_DELTA_BYTES = -395
EXPECTED_BEST_FRI_DELTA_BYTES = -353
EXPECTED_BEST_DECOMMITMENT_DELTA_BYTES = -42
EXPECTED_BEST_QUERY_DELTA_BYTES = 80
SOURCE_PLUS_SIDECAR_RAW_PROOF_BYTES = 98_012
LOOKUP_CLAIMS = 1_184
TRACE_ROWS = 2_048
TABLE_ROWS = 9
HEAD_COUNT = 2
SEQUENCE_LENGTH = 32
KEY_WIDTH = 8
VALUE_WIDTH = 8
MAX_BASELINE_ENVELOPE_BYTES = 8_388_608
MAX_VARIANT_ENVELOPE_BYTES = 4_194_304
MAX_VARIANT_INPUT_BYTES = 2_097_152
BASELINE_ENVELOPE_SHA256 = "550adc4681dca0f5075b65cb046ef4e027364d34d6f70925c5f82d5190afc933"
BASELINE_STATEMENT_COMMITMENT = "blake2b-256:03267fbc084726c1249fbd6025cc3ec3fdc30214f7c75693810c5b72188ace55"
PROOF_BACKEND_VERSION = "stwo-attention-kv-two-head-seq32-fused-bounded-softmax-table-logup-v1"
STATEMENT_VERSION = "zkai-attention-kv-stwo-native-two-head-seq32-fused-softmax-table-logup-statement-v1"
WEIGHT_TABLE_COMMITMENT = "blake2b-256:79dd63cc0ca1403a4d4e9673ecdfd6aa3ab728841e54ae14cca309322b7e38f2"
NATIVE_VERIFY_COMMAND = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend "
    "--bin zkai_attention_kv_native_two_head_seq32_fused_softmax_table_proof -- verify "
    "docs/engineering/evidence/zkai-stwo-ai-two-head-seq32-layout-chunk4-fused.envelope.json"
)
NATIVE_VERIFY_ALL_COMMAND = (
    "for f in docs/engineering/evidence/zkai-stwo-ai-two-head-seq32-layout-*-fused.envelope.json; do "
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend "
    "--bin zkai_attention_kv_native_two_head_seq32_fused_softmax_table_proof -- verify \"$f\"; "
    "done"
)
VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_stwo_ai_two_head_seq32_layout_schedule_sweep_gate.py --write-json docs/engineering/evidence/zkai-stwo-ai-two-head-seq32-layout-schedule-sweep-2026-06.json --write-tsv docs/engineering/evidence/zkai-stwo-ai-two-head-seq32-layout-schedule-sweep-2026-06.tsv --write-md docs/engineering/zkai-stwo-ai-two-head-seq32-layout-schedule-sweep-2026-06-04.md",
    "python3.10 -m py_compile scripts/zkai_stwo_ai_two_head_seq32_layout_schedule_sweep_gate.py scripts/tests/test_zkai_stwo_ai_two_head_seq32_layout_schedule_sweep_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_stwo_ai_two_head_seq32_layout_schedule_sweep_gate",
    NATIVE_VERIFY_COMMAND,
    NATIVE_VERIFY_ALL_COMMAND,
    "git diff --check",
)
NON_CLAIMS = (
    "not a Stwo fork",
    "not a backend patch",
    "not post-query schedule selection",
    "not transcript grinding",
    "not a d64 or d128 result",
    "not a production route policy",
    "not timing evidence",
    "not exact real-valued Softmax",
    "not full transformer inference",
)
TSV_COLUMNS = (
    "schedule_id",
    "proof_size_bytes",
    "saves_vs_baseline_bytes",
    "proof_delta_vs_baseline_bytes",
    "opening_delta_vs_baseline_bytes",
    "fri_delta_vs_baseline_bytes",
    "decommitment_delta_vs_baseline_bytes",
    "query_delta_vs_baseline_bytes",
    "statement_commitment",
    "schedule_policy",
)
VARIANT_SPECS = (
    {
        "schedule_id": "reverse_alternating",
        "file_slug": "reverse-alternating",
        "schedule_policy": "reverse the existing alternating step order",
        "envelope_sha256": "85ab4b30bb1e0b55075ed25d92553a1c780b2ab9dd3177ec4e5a64813c38db9c",
        "input_sha256": "95babd06f046ed12de8cf71957a62de1e438a87a87301b98544873ee2c9ce7eb",
    },
    {
        "schedule_id": "chunk2",
        "file_slug": "chunk2",
        "schedule_policy": "two-row deterministic source chunks",
        "envelope_sha256": "0a87e669d64b950d84d41da02c4b2a936028b9b27a65d4abcedef62b2a51b52b",
        "input_sha256": "56b1e486549b61eb7cde2d534d26b383638296f0ea6e9fa6636d213542c8a493",
    },
    {
        "schedule_id": "chunk4",
        "file_slug": "chunk4",
        "schedule_policy": "four-row deterministic source chunks",
        "envelope_sha256": "e446a1ac6ce98387b7ef14e95ed61ff513cc5f65ff0116fe71ef83dc8fdc2e70",
        "input_sha256": "3c68b609318aa8bfe513b709a4ad16aabc63ba2b222fb69d643801dfa4ab5c96",
    },
    {
        "schedule_id": "chunk8",
        "file_slug": "chunk8",
        "schedule_policy": "eight-row deterministic source chunks",
        "envelope_sha256": "bebd10ca7ab35d7532cf69724890c18c82ea5e57ec725acca1ec9d7bc5dbbb12",
        "input_sha256": "41d6d3fb1199197d38c65d10a6bc6986dd50f4e6e6d0795266b869e56b056b13",
    },
    {
        "schedule_id": "chunk16",
        "file_slug": "chunk16",
        "schedule_policy": "sixteen-row deterministic source chunks",
        "envelope_sha256": "ca9b6a53ec579a57fb43d8b342edbdaf2b7bd00bb0d09b714bc3817688ce89cd",
        "input_sha256": "7873e319100f81a9d967c7abd062d70c1aeb282b6f3069b01616f2496d8422ca",
    },
    {
        "schedule_id": "head_blocked",
        "file_slug": "head-blocked",
        "schedule_policy": "head-zero rows then head-one rows",
        "envelope_sha256": "a0fb09abfd067572383a20b705d27d76bed145bae87749ba249df18768649af8",
        "input_sha256": "0ad5c6b9b1a4c33461cc29e2c3598510690249a6d56b52c93246c25edfae5819",
    },
    {
        "schedule_id": "head1_blocked",
        "file_slug": "head1-blocked",
        "schedule_policy": "head-one rows then head-zero rows",
        "envelope_sha256": "89d235d12f0831635bf7fb81f5597b65b5775dabf3a1ca5ce09f8c8a4c2b1452",
        "input_sha256": "5108315dabadc30e2ec8d2f0301b9e79095500ded789de05da1ac2372136148e",
    },
)
EXPECTED_MUTATION_NAMES = (
    "decision_overclaim",
    "fork_status_promotion",
    "d64_promotion_overclaim",
    "post_query_policy_smuggling",
    "baseline_digest_drift",
    "artifact_digest_drift",
    "best_schedule_relabeling",
    "proof_byte_smuggling",
    "statement_commitment_smuggling",
    "native_verify_removed",
    "non_claim_removed",
    "payload_commitment_drift",
    "unknown_field_injection",
)
EXPECTED_MUTATION_COUNT = len(EXPECTED_MUTATION_NAMES)


class LayoutScheduleSweepGateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def blake2b_commitment(value: Any, domain: str) -> str:
    hasher = hashlib.blake2b(digest_size=32, person=b"zkai-layout-v1")
    hasher.update(domain.encode("utf-8"))
    hasher.update(b"\0")
    hasher.update(canonical_json_bytes(value))
    return "blake2b-256:" + hasher.hexdigest()


def sha256_file(path: pathlib.Path, expected_sha256: str | None = None) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise LayoutScheduleSweepGateError(f"{path.name} sha256 drift")
    return digest


def read_bounded_json(path: pathlib.Path, max_bytes: int, label: str) -> Any:
    if not path.is_file():
        raise LayoutScheduleSweepGateError(f"missing {label}: {path}")
    size = path.stat().st_size
    if size <= 0 or size > max_bytes:
        raise LayoutScheduleSweepGateError(f"{label} size drift")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise LayoutScheduleSweepGateError(f"{label} is not JSON: {err}") from err


def require_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise LayoutScheduleSweepGateError(f"{label} must be non-empty string")
    return value


def require_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise LayoutScheduleSweepGateError(f"{label} must be int")
    return value


def variant_input_path(spec: dict[str, str]) -> pathlib.Path:
    return EVIDENCE_DIR / f"zkai-stwo-ai-two-head-seq32-layout-{spec['file_slug']}-input.json"


def variant_envelope_path(spec: dict[str, str]) -> pathlib.Path:
    return EVIDENCE_DIR / f"zkai-stwo-ai-two-head-seq32-layout-{spec['file_slug']}-fused.envelope.json"


def proof_profile(path: pathlib.Path, max_bytes: int, label: str) -> dict[str, Any]:
    try:
        return section_delta.proof_section_profile(path, max_bytes, label)
    except section_delta.FusedSoftmaxTableSectionDeltaGateError as err:
        raise LayoutScheduleSweepGateError(str(err)) from err


def proof_buckets(profile: dict[str, Any]) -> dict[str, int]:
    return section_delta.bucket_bytes(profile["section_bytes"], profile["json_wrapper_bytes"])


def validate_same_workload(summary: dict[str, Any], label: str) -> None:
    checks = {
        "source_head_count": HEAD_COUNT,
        "score_rows": LOOKUP_CLAIMS,
        "trace_rows": TRACE_ROWS,
        "table_rows": TABLE_ROWS,
        "lookup_claims": LOOKUP_CLAIMS,
        "source_plus_sidecar_raw_proof_bytes": SOURCE_PLUS_SIDECAR_RAW_PROOF_BYTES,
        "source_weight_table_commitment": WEIGHT_TABLE_COMMITMENT,
    }
    for key, expected in checks.items():
        if summary.get(key) != expected:
            raise LayoutScheduleSweepGateError(f"{label} workload drift: {key}")


def load_baseline() -> dict[str, Any]:
    sha256_file(BASELINE_ENVELOPE, BASELINE_ENVELOPE_SHA256)
    envelope = read_bounded_json(BASELINE_ENVELOPE, MAX_BASELINE_ENVELOPE_BYTES, "baseline envelope")
    summary = envelope.get("fused_summary")
    if not isinstance(summary, dict):
        raise LayoutScheduleSweepGateError("baseline summary missing")
    validate_same_workload(summary, "baseline")
    if envelope.get("proof_backend_version") != PROOF_BACKEND_VERSION:
        raise LayoutScheduleSweepGateError("baseline backend version drift")
    if envelope.get("statement_version") != STATEMENT_VERSION:
        raise LayoutScheduleSweepGateError("baseline statement version drift")
    if summary.get("source_statement_commitment") != BASELINE_STATEMENT_COMMITMENT:
        raise LayoutScheduleSweepGateError("baseline statement commitment drift")
    profile = proof_profile(BASELINE_ENVELOPE, MAX_BASELINE_ENVELOPE_BYTES, "baseline envelope")
    if profile["proof_size_bytes"] != BASELINE_PROOF_SIZE_BYTES:
        raise LayoutScheduleSweepGateError("baseline proof size drift")
    return {
        "path": str(BASELINE_ENVELOPE.relative_to(ROOT)),
        "sha256": BASELINE_ENVELOPE_SHA256,
        "proof_size_bytes": profile["proof_size_bytes"],
        "section_bytes": profile["section_bytes"],
        "bucket_bytes": proof_buckets(profile),
        "statement_commitment": BASELINE_STATEMENT_COMMITMENT,
    }


def build_variant_row(spec: dict[str, str], baseline: dict[str, Any]) -> dict[str, Any]:
    input_path = variant_input_path(spec)
    envelope_path = variant_envelope_path(spec)
    input_sha256 = sha256_file(input_path, spec["input_sha256"])
    envelope_sha256 = sha256_file(envelope_path, spec["envelope_sha256"])
    source_input = read_bounded_json(input_path, MAX_VARIANT_INPUT_BYTES, f"{spec['schedule_id']} input")
    envelope = read_bounded_json(envelope_path, MAX_VARIANT_ENVELOPE_BYTES, f"{spec['schedule_id']} envelope")
    if envelope.get("source_input") != source_input:
        raise LayoutScheduleSweepGateError(f"{spec['schedule_id']} source input split-brain drift")
    summary = envelope.get("fused_summary")
    if not isinstance(summary, dict):
        raise LayoutScheduleSweepGateError(f"{spec['schedule_id']} summary missing")
    validate_same_workload(summary, spec["schedule_id"])
    if envelope.get("proof_backend_version") != PROOF_BACKEND_VERSION:
        raise LayoutScheduleSweepGateError(f"{spec['schedule_id']} backend version drift")
    if envelope.get("statement_version") != STATEMENT_VERSION:
        raise LayoutScheduleSweepGateError(f"{spec['schedule_id']} statement version drift")
    statement_commitment = require_str(summary.get("source_statement_commitment"), f"{spec['schedule_id']} statement")
    if statement_commitment != source_input.get("statement_commitment"):
        raise LayoutScheduleSweepGateError(f"{spec['schedule_id']} statement commitment split-brain drift")
    profile = proof_profile(envelope_path, MAX_VARIANT_ENVELOPE_BYTES, f"{spec['schedule_id']} envelope")
    sections = profile["section_bytes"]
    buckets = proof_buckets(profile)
    baseline_sections = baseline["section_bytes"]
    baseline_buckets = baseline["bucket_bytes"]
    proof_delta = profile["proof_size_bytes"] - baseline["proof_size_bytes"]
    row = {
        "schedule_id": spec["schedule_id"],
        "file_slug": spec["file_slug"],
        "schedule_policy": spec["schedule_policy"],
        "input_path": str(input_path.relative_to(ROOT)),
        "input_sha256": input_sha256,
        "envelope_path": str(envelope_path.relative_to(ROOT)),
        "envelope_sha256": envelope_sha256,
        "proof_size_bytes": profile["proof_size_bytes"],
        "envelope_size_bytes": profile["envelope_size_bytes"],
        "statement_commitment": statement_commitment,
        "public_instance_commitment": require_str(
            summary.get("source_public_instance_commitment"),
            f"{spec['schedule_id']} public instance",
        ),
        "proof_delta_vs_baseline_bytes": proof_delta,
        "saves_vs_baseline_bytes": -proof_delta,
        "section_delta_vs_baseline_bytes": {
            key: sections[key] - baseline_sections[key] for key in section_delta.PROOF_SECTION_KEYS
        },
        "bucket_delta_vs_baseline_bytes": {
            key: buckets[key] - baseline_buckets[key] for key in section_delta.PROOF_BUCKET_KEYS
        },
        "same_workload": {
            "key_width": KEY_WIDTH,
            "value_width": VALUE_WIDTH,
            "head_count": HEAD_COUNT,
            "sequence_length": SEQUENCE_LENGTH,
            "lookup_claims": LOOKUP_CLAIMS,
            "trace_rows": TRACE_ROWS,
            "table_rows": TABLE_ROWS,
            "source_plus_sidecar_raw_proof_bytes": SOURCE_PLUS_SIDECAR_RAW_PROOF_BYTES,
        },
    }
    validate_variant_row(row)
    return row


def build_rows(baseline: dict[str, Any]) -> list[dict[str, Any]]:
    return [build_variant_row(spec, baseline) for spec in VARIANT_SPECS]


def find_row(rows: list[dict[str, Any]], schedule_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("schedule_id") == schedule_id:
            return row
    raise LayoutScheduleSweepGateError(f"missing schedule row: {schedule_id}")


def build_aggregate(rows: list[dict[str, Any]], baseline: dict[str, Any]) -> dict[str, Any]:
    best = min(rows, key=lambda row: (row["proof_size_bytes"], row["schedule_id"]))
    worst = max(rows, key=lambda row: (row["proof_size_bytes"], row["schedule_id"]))
    best_buckets = best["bucket_delta_vs_baseline_bytes"]
    best_sections = best["section_delta_vs_baseline_bytes"]
    aggregate = {
        "baseline_proof_size_bytes": baseline["proof_size_bytes"],
        "variants_checked": len(rows),
        "best_schedule_id": best["schedule_id"],
        "best_proof_size_bytes": best["proof_size_bytes"],
        "best_saves_vs_baseline_bytes": best["saves_vs_baseline_bytes"],
        "best_opening_delta_vs_baseline_bytes": best_buckets["opening_bucket_bytes"],
        "best_fri_delta_vs_baseline_bytes": best_sections["fri_proof"],
        "best_decommitment_delta_vs_baseline_bytes": best_sections["decommitments"],
        "best_query_delta_vs_baseline_bytes": best_buckets["query_bucket_bytes"],
        "worst_schedule_id": worst["schedule_id"],
        "worst_proof_delta_vs_baseline_bytes": worst["proof_delta_vs_baseline_bytes"],
    }
    validate_aggregate(aggregate)
    return aggregate


def validate_variant_row(row: Any) -> None:
    if not isinstance(row, dict):
        raise LayoutScheduleSweepGateError("variant row must be object")
    expected = {
        "schedule_id",
        "file_slug",
        "schedule_policy",
        "input_path",
        "input_sha256",
        "envelope_path",
        "envelope_sha256",
        "proof_size_bytes",
        "envelope_size_bytes",
        "statement_commitment",
        "public_instance_commitment",
        "proof_delta_vs_baseline_bytes",
        "saves_vs_baseline_bytes",
        "section_delta_vs_baseline_bytes",
        "bucket_delta_vs_baseline_bytes",
        "same_workload",
    }
    if set(row) != expected:
        raise LayoutScheduleSweepGateError("variant row field drift")
    require_str(row["schedule_id"], "schedule_id")
    require_str(row["schedule_policy"], "schedule_policy")
    proof_size = require_int(row["proof_size_bytes"], f"{row['schedule_id']} proof size")
    if proof_size <= 0:
        raise LayoutScheduleSweepGateError("proof size must be positive")
    if row["saves_vs_baseline_bytes"] != -row["proof_delta_vs_baseline_bytes"]:
        raise LayoutScheduleSweepGateError("proof delta sign drift")
    if set(row["section_delta_vs_baseline_bytes"]) != set(section_delta.PROOF_SECTION_KEYS):
        raise LayoutScheduleSweepGateError("section delta key drift")
    if set(row["bucket_delta_vs_baseline_bytes"]) != set(section_delta.PROOF_BUCKET_KEYS):
        raise LayoutScheduleSweepGateError("bucket delta key drift")
    if row["same_workload"] != {
        "key_width": KEY_WIDTH,
        "value_width": VALUE_WIDTH,
        "head_count": HEAD_COUNT,
        "sequence_length": SEQUENCE_LENGTH,
        "lookup_claims": LOOKUP_CLAIMS,
        "trace_rows": TRACE_ROWS,
        "table_rows": TABLE_ROWS,
        "source_plus_sidecar_raw_proof_bytes": SOURCE_PLUS_SIDECAR_RAW_PROOF_BYTES,
    }:
        raise LayoutScheduleSweepGateError("same workload drift")


def validate_aggregate(aggregate: Any) -> None:
    if not isinstance(aggregate, dict):
        raise LayoutScheduleSweepGateError("aggregate must be object")
    expected = {
        "baseline_proof_size_bytes": BASELINE_PROOF_SIZE_BYTES,
        "variants_checked": len(VARIANT_SPECS),
        "best_schedule_id": BEST_SCHEDULE_ID,
        "best_proof_size_bytes": EXPECTED_BEST_PROOF_SIZE_BYTES,
        "best_saves_vs_baseline_bytes": EXPECTED_BEST_SAVING_BYTES,
        "best_opening_delta_vs_baseline_bytes": EXPECTED_BEST_OPENING_DELTA_BYTES,
        "best_fri_delta_vs_baseline_bytes": EXPECTED_BEST_FRI_DELTA_BYTES,
        "best_decommitment_delta_vs_baseline_bytes": EXPECTED_BEST_DECOMMITMENT_DELTA_BYTES,
        "best_query_delta_vs_baseline_bytes": EXPECTED_BEST_QUERY_DELTA_BYTES,
        "worst_schedule_id": "chunk8",
        "worst_proof_delta_vs_baseline_bytes": 4_050,
    }
    if aggregate != expected:
        raise LayoutScheduleSweepGateError("aggregate drift")


def payload_commitment(payload: dict[str, Any]) -> str:
    payload_for_commitment = copy.deepcopy(payload)
    payload_for_commitment.pop("payload_commitment", None)
    return blake2b_commitment(payload_for_commitment, SCHEMA)


def build_base_payload() -> dict[str, Any]:
    baseline = load_baseline()
    rows = build_rows(baseline)
    payload = {
        "schema": SCHEMA,
        "issue": ISSUE,
        "source_surface_issue": SOURCE_SURFACE_ISSUE,
        "decision": DECISION,
        "route_id": ROUTE_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "fork_status": FORK_STATUS,
        "promotion_status": PROMOTION_STATUS,
        "timing_policy": TIMING_POLICY,
        "verify_policy": VERIFY_POLICY,
        "baseline_policy": BASELINE_POLICY,
        "baseline_artifact": baseline,
        "schedule_ids": [spec["schedule_id"] for spec in VARIANT_SPECS],
        "variant_rows": rows,
        "aggregate": build_aggregate(rows, baseline),
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload, allow_missing_mutation_summary=True, expected_rows=rows, expected_baseline=baseline)
    return payload


def validate_payload(
    payload: Any,
    *,
    allow_missing_mutation_summary: bool = False,
    expected_rows: list[dict[str, Any]] | None = None,
    expected_baseline: dict[str, Any] | None = None,
) -> None:
    if not isinstance(payload, dict):
        raise LayoutScheduleSweepGateError("payload must be object")
    expected = {
        "schema",
        "issue",
        "source_surface_issue",
        "decision",
        "route_id",
        "claim_boundary",
        "fork_status",
        "promotion_status",
        "timing_policy",
        "verify_policy",
        "baseline_policy",
        "baseline_artifact",
        "schedule_ids",
        "variant_rows",
        "aggregate",
        "non_claims",
        "validation_commands",
        "payload_commitment",
    }
    mutation_keys = {"mutation_cases", "mutations_checked", "mutations_rejected", "all_mutations_rejected"}
    if set(payload) - (expected | mutation_keys):
        raise LayoutScheduleSweepGateError("payload field drift")
    if expected - set(payload):
        raise LayoutScheduleSweepGateError("payload field drift")
    exact = {
        "schema": SCHEMA,
        "issue": ISSUE,
        "source_surface_issue": SOURCE_SURFACE_ISSUE,
        "decision": DECISION,
        "route_id": ROUTE_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "fork_status": FORK_STATUS,
        "promotion_status": PROMOTION_STATUS,
        "timing_policy": TIMING_POLICY,
        "verify_policy": VERIFY_POLICY,
        "baseline_policy": BASELINE_POLICY,
        "schedule_ids": [spec["schedule_id"] for spec in VARIANT_SPECS],
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    for key, expected_value in exact.items():
        if payload[key] != expected_value:
            raise LayoutScheduleSweepGateError(f"{key} drift")
    if expected_baseline is None:
        expected_baseline = load_baseline()
    if payload["baseline_artifact"] != expected_baseline:
        raise LayoutScheduleSweepGateError("baseline artifact drift")
    rows = payload["variant_rows"]
    if not isinstance(rows, list) or len(rows) != len(VARIANT_SPECS):
        raise LayoutScheduleSweepGateError("variant row count drift")
    if [row.get("schedule_id") if isinstance(row, dict) else None for row in rows] != [
        spec["schedule_id"] for spec in VARIANT_SPECS
    ]:
        raise LayoutScheduleSweepGateError("variant row order drift")
    for row in rows:
        validate_variant_row(row)
    if expected_rows is None:
        expected_rows = build_rows(expected_baseline)
    if rows != expected_rows:
        raise LayoutScheduleSweepGateError("variant row drift")
    expected_aggregate = build_aggregate(expected_rows, expected_baseline)
    if payload["aggregate"] != expected_aggregate:
        raise LayoutScheduleSweepGateError("aggregate drift")
    validate_aggregate(payload["aggregate"])
    best = find_row(rows, BEST_SCHEDULE_ID)
    if best["proof_size_bytes"] >= expected_baseline["proof_size_bytes"]:
        raise LayoutScheduleSweepGateError("best schedule is not smaller than baseline")
    if payload_commitment(payload) != payload["payload_commitment"]:
        raise LayoutScheduleSweepGateError("payload commitment drift")
    if not allow_missing_mutation_summary or any(key in payload for key in mutation_keys):
        if not mutation_keys <= set(payload):
            raise LayoutScheduleSweepGateError("mutation summary missing")
        if payload["mutations_checked"] != EXPECTED_MUTATION_COUNT:
            raise LayoutScheduleSweepGateError("mutation count drift")
        if payload["mutations_rejected"] != EXPECTED_MUTATION_COUNT:
            raise LayoutScheduleSweepGateError("mutation rejection drift")
        if payload["all_mutations_rejected"] is not True:
            raise LayoutScheduleSweepGateError("mutation flag drift")
        cases = payload["mutation_cases"]
        if not isinstance(cases, list) or len(cases) != EXPECTED_MUTATION_COUNT:
            raise LayoutScheduleSweepGateError("mutation case count drift")
        if [case.get("name") if isinstance(case, dict) else None for case in cases] != list(EXPECTED_MUTATION_NAMES):
            raise LayoutScheduleSweepGateError("mutation case name drift")
        for case in cases:
            if not isinstance(case, dict) or set(case) != {"name", "rejected", "error"}:
                raise LayoutScheduleSweepGateError("mutation case field drift")
            if case["rejected"] is not True:
                raise LayoutScheduleSweepGateError("mutation survived")
            require_str(case["error"], "mutation error")


def mutation_cases_for(payload: dict[str, Any]) -> list[dict[str, Any]]:
    base = copy.deepcopy(payload)
    for key in ("mutation_cases", "mutations_checked", "mutations_rejected", "all_mutations_rejected"):
        base.pop(key, None)
    mutations: list[tuple[str, Any]] = []

    def add(name: str, fn: Any) -> None:
        mutations.append((name, fn))

    add("decision_overclaim", lambda p: p.__setitem__("decision", "GO_STWO_AI_FORK_BREAKTHROUGH"))
    add("fork_status_promotion", lambda p: p.__setitem__("fork_status", "GO_FORK_STWO_NOW"))
    add("d64_promotion_overclaim", lambda p: p.__setitem__("promotion_status", "GO_PROMOTE_TO_D64_NOW"))
    add("post_query_policy_smuggling", lambda p: p["variant_rows"][0].__setitem__("schedule_policy", "choose after queries"))
    add("baseline_digest_drift", lambda p: p["baseline_artifact"].__setitem__("sha256", "00" * 32))
    add("artifact_digest_drift", lambda p: find_row(p["variant_rows"], BEST_SCHEDULE_ID).__setitem__("envelope_sha256", "11" * 32))
    add("best_schedule_relabeling", lambda p: p["aggregate"].__setitem__("best_schedule_id", "chunk2"))
    add("proof_byte_smuggling", lambda p: find_row(p["variant_rows"], BEST_SCHEDULE_ID).__setitem__("proof_size_bytes", 1))
    add(
        "statement_commitment_smuggling",
        lambda p: find_row(p["variant_rows"], BEST_SCHEDULE_ID).__setitem__("statement_commitment", "blake2b-256:" + "aa" * 32),
    )
    add("native_verify_removed", lambda p: p["validation_commands"].remove(NATIVE_VERIFY_COMMAND))
    add("non_claim_removed", lambda p: p["non_claims"].remove("not a Stwo fork"))
    add("payload_commitment_drift", lambda p: p.__setitem__("payload_commitment", "blake2b-256:" + "bb" * 32))
    add("unknown_field_injection", lambda p: p.__setitem__("unexpected", True))

    if [name for name, _fn in mutations] != list(EXPECTED_MUTATION_NAMES):
        raise LayoutScheduleSweepGateError("mutation spec drift")
    expected_baseline = payload["baseline_artifact"]
    expected_rows = payload["variant_rows"]
    cases = []
    for name, fn in mutations:
        candidate = copy.deepcopy(base)
        fn(candidate)
        try:
            validate_payload(
                candidate,
                allow_missing_mutation_summary=True,
                expected_rows=expected_rows,
                expected_baseline=expected_baseline,
            )
        except LayoutScheduleSweepGateError as err:
            cases.append({"name": name, "rejected": True, "error": str(err)})
        else:
            cases.append({"name": name, "rejected": False, "error": "mutation survived"})
    return cases


def build_payload() -> dict[str, Any]:
    payload = build_base_payload()
    cases = mutation_cases_for(payload)
    payload["mutation_cases"] = cases
    payload["mutations_checked"] = len(cases)
    payload["mutations_rejected"] = sum(1 for case in cases if case["rejected"])
    payload["all_mutations_rejected"] = payload["mutations_checked"] == payload["mutations_rejected"]
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload)
    return payload


def to_tsv(payload: dict[str, Any]) -> str:
    validate_payload(payload)
    rows = []
    for row in payload["variant_rows"]:
        section_delta_row = row["section_delta_vs_baseline_bytes"]
        bucket_delta_row = row["bucket_delta_vs_baseline_bytes"]
        rows.append(
            {
                "schedule_id": row["schedule_id"],
                "proof_size_bytes": row["proof_size_bytes"],
                "saves_vs_baseline_bytes": row["saves_vs_baseline_bytes"],
                "proof_delta_vs_baseline_bytes": row["proof_delta_vs_baseline_bytes"],
                "opening_delta_vs_baseline_bytes": bucket_delta_row["opening_bucket_bytes"],
                "fri_delta_vs_baseline_bytes": section_delta_row["fri_proof"],
                "decommitment_delta_vs_baseline_bytes": section_delta_row["decommitments"],
                "query_delta_vs_baseline_bytes": bucket_delta_row["query_bucket_bytes"],
                "statement_commitment": row["statement_commitment"],
                "schedule_policy": row["schedule_policy"],
            }
        )
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def to_markdown(payload: dict[str, Any]) -> str:
    validate_payload(payload)
    aggregate = payload["aggregate"]
    best = find_row(payload["variant_rows"], BEST_SCHEDULE_ID)
    return "\n".join(
        [
            "# Stwo-AI Two-Head Seq32 Layout Schedule Sweep",
            "",
            f"- Issue: `#{ISSUE}`",
            f"- Decision: `{DECISION}`",
            f"- Fork status: `{FORK_STATUS}`",
            f"- Promotion status: `{PROMOTION_STATUS}`",
            f"- Verify policy: `{VERIFY_POLICY}`",
            "",
            "## Result",
            "",
            "`chunk4` is the first checked route-layout win on the fast `d8_two_head_seq32` surface. It uses the same workload as the existing alternating baseline and fixes the schedule before proof generation.",
            "",
            f"- Baseline proof bytes: `{aggregate['baseline_proof_size_bytes']}`",
            f"- Best schedule: `{aggregate['best_schedule_id']}`",
            f"- Best proof bytes: `{aggregate['best_proof_size_bytes']}`",
            f"- Saving vs baseline: `{aggregate['best_saves_vs_baseline_bytes']}` bytes",
            f"- Opening delta: `{aggregate['best_opening_delta_vs_baseline_bytes']}` bytes",
            f"- FRI delta: `{aggregate['best_fri_delta_vs_baseline_bytes']}` bytes",
            f"- Decommitment delta: `{aggregate['best_decommitment_delta_vs_baseline_bytes']}` bytes",
            f"- Query delta: `{aggregate['best_query_delta_vs_baseline_bytes']}` bytes",
            f"- Statement commitment: `{best['statement_commitment']}`",
            "",
            "## Interpretation",
            "",
            "This does not justify a Stwo fork. It says deterministic row scheduling can move proof bytes inside the current backend. The useful next step is to turn `chunk4` into a verifier-bound policy knob and then reprove the d64 pressure anchor.",
            "",
            "## Non-Claims",
            "",
            *[f"- {item}" for item in NON_CLAIMS],
            "",
            "## Reproduce",
            "",
            "```bash",
            *VALIDATION_COMMANDS,
            "```",
            "",
        ]
    )


def require_evidence_output_path(path: pathlib.Path) -> pathlib.Path:
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()
    if resolved.parent != EVIDENCE_DIR.resolve():
        raise LayoutScheduleSweepGateError("evidence output path must be under docs/engineering/evidence")
    return resolved


def require_docs_output_path(path: pathlib.Path) -> pathlib.Path:
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()
    if resolved.parent != DOCS_DIR.resolve():
        raise LayoutScheduleSweepGateError("markdown output path must be under docs/engineering")
    return resolved


def write_atomic(path: pathlib.Path, content: str, *, docs: bool = False) -> None:
    resolved = require_docs_output_path(path) if docs else require_evidence_output_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    temp_path: pathlib.Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=resolved.parent,
            delete=False,
        ) as handle:
            temp_path = pathlib.Path(handle.name)
            handle.write(content)
        temp_path.replace(resolved)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path, tsv_path: pathlib.Path, md_path: pathlib.Path) -> None:
    validate_payload(payload)
    write_atomic(json_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_atomic(tsv_path, to_tsv(payload))
    write_atomic(md_path, to_markdown(payload), docs=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    parser.add_argument("--write-md", type=pathlib.Path)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    payload = build_payload()
    if args.no_write:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    write_outputs(payload, args.write_json or JSON_OUT, args.write_tsv or TSV_OUT, args.write_md or MD_OUT)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
