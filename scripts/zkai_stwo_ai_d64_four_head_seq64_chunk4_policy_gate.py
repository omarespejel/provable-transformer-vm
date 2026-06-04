#!/usr/bin/env python3
"""Gate the d64 chunk4 verifier-bound route-layout policy result for issue #757."""

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
    EVIDENCE_DIR / "zkai-attention-kv-stwo-native-d64-four-head-seq64-fused-softmax-table-proof-2026-05.envelope.json"
)
CHUNK4_INPUT = EVIDENCE_DIR / "zkai-stwo-ai-d64-four-head-seq64-layout-chunk4-input.json"
CHUNK4_ENVELOPE = EVIDENCE_DIR / "zkai-stwo-ai-d64-four-head-seq64-layout-chunk4-fused.envelope.json"
JSON_OUT = EVIDENCE_DIR / "zkai-stwo-ai-d64-four-head-seq64-chunk4-policy-gate-2026-06.json"
TSV_OUT = EVIDENCE_DIR / "zkai-stwo-ai-d64-four-head-seq64-chunk4-policy-gate-2026-06.tsv"
MD_OUT = DOCS_DIR / "zkai-stwo-ai-d64-four-head-seq64-chunk4-policy-gate-2026-06-04.md"

SCHEMA = "zkai-stwo-ai-d64-four-head-seq64-chunk4-policy-gate-v1"
ISSUE = 757
SOURCE_SURFACE_ISSUE = 715
DECISION = "GO_D64_CHUNK4_VERIFIER_BOUND_LAYOUT_POLICY_REDUCES_FUSED_PROOF_BYTES"
ROUTE_ID = "local_stwo_ai_d64_four_head_seq64_chunk4_layout_policy"
FORK_STATUS = "NO_GO_FORK_STWO_ROUTE_POLICY_LAYER_STILL_MOVES_PROOF_BYTES"
TIMING_POLICY = "no_timing_claim_no_public_benchmark"
SECURITY_CONFIG = {
    "fri_query_count": 3,
    "fri_log_blowup": 1,
    "pow_bits": 10,
    "fold_step": 1,
}
LAYOUT_POLICY = "chunk4"
BASELINE_POLICY = "legacy_implicit_source_step_order"
PROOF_BACKEND = "stwo"
PROOF_BACKEND_VERSION = "stwo-attention-kv-d64-four-head-seq64-fused-bounded-softmax-table-logup-v1"
STATEMENT_VERSION = "zkai-attention-kv-stwo-native-d64-four-head-seq64-fused-softmax-table-logup-statement-v1"
SOURCE_STATEMENT_COMMITMENT = "blake2b-256:319ee48ad99dc3aa596380c1ddd82b7f3a67f5ce8d81aa85aebd4c955402fc46"
SOURCE_INPUT_SHA256 = "8e3b59bc8d77deef5917bdd252d5ea55724d86ed746cb09ad8bf9f0e88bfb5ce"
BASELINE_ENVELOPE_SHA256 = "641bcd4c8b29ad8098b47a4ec293b6972913ad0ceee9548229a219bd3bea7000"
CHUNK4_ENVELOPE_SHA256 = "91f01d0d487010b79ba62b6dc5d92abde16d7b57618114cf739db5b65cd2091e"
BASELINE_PROOF_SIZE_BYTES = 276_503
CHUNK4_PROOF_SIZE_BYTES = 274_692
SOURCE_PLUS_SIDECAR_RAW_PROOF_BYTES = 315_785
SAVING_VS_BASELINE_BYTES = 1_811
SAVING_VS_SPLIT_BYTES = 41_093
CHUNK4_VS_BASELINE_RATIO = "0.993450"
CHUNK4_VS_SPLIT_RATIO = "0.869870"
LOOKUP_CLAIMS = 8_832
TRACE_ROWS = 16_384
TABLE_ROWS = 9
HEAD_COUNT = 4
SEQUENCE_LENGTH = 64
MAX_INPUT_BYTES = 268_435_456
MAX_ENVELOPE_BYTES = 268_435_456
NATIVE_PROVE_COMMAND = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend "
    "--bin zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_proof -- prove "
    "docs/engineering/evidence/zkai-stwo-ai-d64-four-head-seq64-layout-chunk4-input.json "
    "docs/engineering/evidence/zkai-stwo-ai-d64-four-head-seq64-layout-chunk4-fused.envelope.json"
)
NATIVE_VERIFY_COMMAND = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend "
    "--bin zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_proof -- verify "
    "docs/engineering/evidence/zkai-stwo-ai-d64-four-head-seq64-layout-chunk4-fused.envelope.json"
)
VALIDATION_COMMANDS = (
    "just gate-fast",
    "python3.10 scripts/zkai_attention_kv_stwo_native_d64_four_head_seq64_bounded_softmax_table_proof_input.py --layout-policy chunk4 --write-json docs/engineering/evidence/zkai-stwo-ai-d64-four-head-seq64-layout-chunk4-input.json --write-tsv docs/engineering/evidence/zkai-stwo-ai-d64-four-head-seq64-layout-chunk4-input.tsv",
    NATIVE_PROVE_COMMAND,
    NATIVE_VERIFY_COMMAND,
    "python3.10 scripts/zkai_stwo_ai_d64_four_head_seq64_chunk4_policy_gate.py --write-json docs/engineering/evidence/zkai-stwo-ai-d64-four-head-seq64-chunk4-policy-gate-2026-06.json --write-tsv docs/engineering/evidence/zkai-stwo-ai-d64-four-head-seq64-chunk4-policy-gate-2026-06.tsv --write-md docs/engineering/zkai-stwo-ai-d64-four-head-seq64-chunk4-policy-gate-2026-06-04.md",
    "python3.10 -m py_compile scripts/zkai_stwo_ai_d64_four_head_seq64_chunk4_policy_gate.py scripts/tests/test_zkai_stwo_ai_d64_four_head_seq64_chunk4_policy_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_stwo_ai_d64_four_head_seq64_chunk4_policy_gate",
    "cargo +nightly-2025-07-14 test --locked attention_kv_native_d64_four_head_seq64_bounded_softmax_table_rejects_layout_policy --lib --features stwo-backend",
    "cargo +nightly-2025-07-14 test --locked attention_kv_native_d64_four_head_seq64_bounded_softmax_table_rejects_unknown_layout_policy --lib --features stwo-backend",
    "git diff --check",
    "just gate-no-nightly",
)
NON_CLAIMS = (
    "not a Stwo fork",
    "not a backend patch",
    "not transcript grinding",
    "not post-query layout selection",
    "not a proving-speed claim",
    "not production-security parameters",
    "not exact real-valued Softmax",
    "not full transformer inference",
    "not a NANOZK comparison",
)
TSV_COLUMNS = (
    "profile_id",
    "baseline_policy",
    "layout_policy",
    "baseline_proof_size_bytes",
    "chunk4_proof_size_bytes",
    "saving_vs_baseline_bytes",
    "source_plus_sidecar_raw_proof_bytes",
    "saving_vs_split_bytes",
    "chunk4_vs_baseline_ratio",
    "chunk4_vs_split_ratio",
    "opening_delta_vs_baseline_bytes",
    "fri_delta_vs_baseline_bytes",
    "decommitment_delta_vs_baseline_bytes",
    "query_delta_vs_baseline_bytes",
    "source_statement_commitment",
)
EXPECTED_MUTATION_NAMES = (
    "decision_overclaim",
    "fork_status_promotion",
    "layout_policy_relabeling",
    "post_query_policy_smuggling",
    "baseline_digest_drift",
    "chunk4_digest_drift",
    "proof_byte_smuggling",
    "split_saving_smuggling",
    "native_verify_removed",
    "non_claim_removed",
    "payload_commitment_drift",
    "unknown_field_injection",
)
EXPECTED_MUTATION_COUNT = len(EXPECTED_MUTATION_NAMES)


class D64Chunk4PolicyGateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def blake2b_commitment(value: Any, domain: str) -> str:
    hasher = hashlib.blake2b(digest_size=32, person=b"zkai-d64ch4-v1")
    hasher.update(domain.encode("utf-8"))
    hasher.update(b"\0")
    hasher.update(canonical_json_bytes(value))
    return "blake2b-256:" + hasher.hexdigest()


def sha256_file(path: pathlib.Path, expected_sha256: str | None = None) -> str:
    if not path.is_file():
        raise D64Chunk4PolicyGateError(f"missing artifact: {path}")
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    digest = hasher.hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise D64Chunk4PolicyGateError(f"{path.name} sha256 drift")
    return digest


def read_json(path: pathlib.Path, max_bytes: int, label: str) -> Any:
    if not path.is_file():
        raise D64Chunk4PolicyGateError(f"missing {label}: {path}")
    size = path.stat().st_size
    if size <= 0 or size > max_bytes:
        raise D64Chunk4PolicyGateError(f"{label} size drift")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise D64Chunk4PolicyGateError(f"{label} is not JSON: {err}") from err


def require_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise D64Chunk4PolicyGateError(f"{label} must be non-empty string")
    return value


def require_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise D64Chunk4PolicyGateError(f"{label} must be int")
    return value


def proof_profile(path: pathlib.Path, label: str) -> dict[str, Any]:
    try:
        return section_delta.proof_section_profile(path, MAX_ENVELOPE_BYTES, label)
    except section_delta.FusedSoftmaxTableSectionDeltaGateError as err:
        raise D64Chunk4PolicyGateError(str(err)) from err


def proof_buckets(profile: dict[str, Any]) -> dict[str, int]:
    return section_delta.bucket_bytes(profile["section_bytes"], profile["json_wrapper_bytes"])


def validate_source_input(source_input: dict[str, Any]) -> None:
    if source_input.get("layout_policy") != LAYOUT_POLICY:
        raise D64Chunk4PolicyGateError("source input layout_policy drift")
    if source_input.get("statement_commitment") != SOURCE_STATEMENT_COMMITMENT:
        raise D64Chunk4PolicyGateError("source statement commitment drift")
    steps = source_input.get("input_steps")
    if not isinstance(steps, list) or len(steps) != HEAD_COUNT * SEQUENCE_LENGTH:
        raise D64Chunk4PolicyGateError("source input step count drift")
    expected = []
    for chunk_start in range(0, SEQUENCE_LENGTH, 4):
        for head_index in range(HEAD_COUNT):
            for local_offset in range(4):
                expected.append((head_index, 2 + chunk_start + local_offset))
    observed = [(step.get("head_index"), step.get("token_position")) for step in steps]
    if observed != expected:
        raise D64Chunk4PolicyGateError("chunk4 source step order drift")


def validate_envelope(envelope: dict[str, Any], source_input: dict[str, Any]) -> dict[str, Any]:
    if envelope.get("source_input") != source_input:
        raise D64Chunk4PolicyGateError("source input split-brain drift")
    if envelope.get("proof_backend") != PROOF_BACKEND:
        raise D64Chunk4PolicyGateError("proof backend drift")
    if envelope.get("proof_backend_version") != PROOF_BACKEND_VERSION:
        raise D64Chunk4PolicyGateError("proof backend version drift")
    if envelope.get("statement_version") != STATEMENT_VERSION:
        raise D64Chunk4PolicyGateError("statement version drift")
    summary = envelope.get("fused_summary")
    if not isinstance(summary, dict):
        raise D64Chunk4PolicyGateError("fused summary missing")
    checks = {
        "source_layout_policy": LAYOUT_POLICY,
        "source_statement_commitment": SOURCE_STATEMENT_COMMITMENT,
        "source_head_count": HEAD_COUNT,
        "score_rows": LOOKUP_CLAIMS,
        "trace_rows": TRACE_ROWS,
        "table_rows": TABLE_ROWS,
        "lookup_claims": LOOKUP_CLAIMS,
        "source_plus_sidecar_raw_proof_bytes": SOURCE_PLUS_SIDECAR_RAW_PROOF_BYTES,
    }
    for key, expected in checks.items():
        if summary.get(key) != expected:
            raise D64Chunk4PolicyGateError(f"fused summary {key} drift")
    return summary


def artifact_row() -> dict[str, Any]:
    baseline_sha = sha256_file(BASELINE_ENVELOPE, BASELINE_ENVELOPE_SHA256)
    input_sha = sha256_file(CHUNK4_INPUT, SOURCE_INPUT_SHA256)
    chunk4_sha = sha256_file(CHUNK4_ENVELOPE, CHUNK4_ENVELOPE_SHA256)
    source_input = read_json(CHUNK4_INPUT, MAX_INPUT_BYTES, "chunk4 input")
    validate_source_input(source_input)
    envelope = read_json(CHUNK4_ENVELOPE, MAX_ENVELOPE_BYTES, "chunk4 envelope")
    summary = validate_envelope(envelope, source_input)
    baseline_profile = proof_profile(BASELINE_ENVELOPE, "baseline envelope")
    chunk4_profile = proof_profile(CHUNK4_ENVELOPE, "chunk4 envelope")
    if baseline_profile["proof_size_bytes"] != BASELINE_PROOF_SIZE_BYTES:
        raise D64Chunk4PolicyGateError("baseline proof size drift")
    if chunk4_profile["proof_size_bytes"] != CHUNK4_PROOF_SIZE_BYTES:
        raise D64Chunk4PolicyGateError("chunk4 proof size drift")
    baseline_sections = baseline_profile["section_bytes"]
    chunk4_sections = chunk4_profile["section_bytes"]
    baseline_buckets = proof_buckets(baseline_profile)
    chunk4_buckets = proof_buckets(chunk4_profile)
    row = {
        "profile_id": "d64_four_head_seq64",
        "baseline_policy": BASELINE_POLICY,
        "layout_policy": LAYOUT_POLICY,
        "source_input_path": str(CHUNK4_INPUT.relative_to(ROOT)),
        "source_input_sha256": input_sha,
        "baseline_envelope_path": str(BASELINE_ENVELOPE.relative_to(ROOT)),
        "baseline_envelope_sha256": baseline_sha,
        "chunk4_envelope_path": str(CHUNK4_ENVELOPE.relative_to(ROOT)),
        "chunk4_envelope_sha256": chunk4_sha,
        "proof_backend": PROOF_BACKEND,
        "proof_backend_version": PROOF_BACKEND_VERSION,
        "statement_version": STATEMENT_VERSION,
        "source_statement_commitment": SOURCE_STATEMENT_COMMITMENT,
        "baseline_proof_size_bytes": baseline_profile["proof_size_bytes"],
        "chunk4_proof_size_bytes": chunk4_profile["proof_size_bytes"],
        "saving_vs_baseline_bytes": baseline_profile["proof_size_bytes"] - chunk4_profile["proof_size_bytes"],
        "source_plus_sidecar_raw_proof_bytes": SOURCE_PLUS_SIDECAR_RAW_PROOF_BYTES,
        "saving_vs_split_bytes": SOURCE_PLUS_SIDECAR_RAW_PROOF_BYTES - chunk4_profile["proof_size_bytes"],
        "chunk4_vs_baseline_ratio": CHUNK4_VS_BASELINE_RATIO,
        "chunk4_vs_split_ratio": CHUNK4_VS_SPLIT_RATIO,
        "section_delta_vs_baseline_bytes": {
            key: chunk4_sections[key] - baseline_sections[key] for key in section_delta.PROOF_SECTION_KEYS
        },
        "bucket_delta_vs_baseline_bytes": {
            key: chunk4_buckets[key] - baseline_buckets[key] for key in section_delta.PROOF_BUCKET_KEYS
        },
        "workload": {
            "head_count": HEAD_COUNT,
            "sequence_length": SEQUENCE_LENGTH,
            "lookup_claims": summary["lookup_claims"],
            "trace_rows": summary["trace_rows"],
            "table_rows": summary["table_rows"],
        },
    }
    validate_row(row)
    return row


def validate_row(row: Any) -> None:
    if not isinstance(row, dict):
        raise D64Chunk4PolicyGateError("row must be object")
    expected_keys = {
        "profile_id",
        "baseline_policy",
        "layout_policy",
        "source_input_path",
        "source_input_sha256",
        "baseline_envelope_path",
        "baseline_envelope_sha256",
        "chunk4_envelope_path",
        "chunk4_envelope_sha256",
        "proof_backend",
        "proof_backend_version",
        "statement_version",
        "source_statement_commitment",
        "baseline_proof_size_bytes",
        "chunk4_proof_size_bytes",
        "saving_vs_baseline_bytes",
        "source_plus_sidecar_raw_proof_bytes",
        "saving_vs_split_bytes",
        "chunk4_vs_baseline_ratio",
        "chunk4_vs_split_ratio",
        "section_delta_vs_baseline_bytes",
        "bucket_delta_vs_baseline_bytes",
        "workload",
    }
    if set(row) != expected_keys:
        raise D64Chunk4PolicyGateError("row field drift")
    exact = {
        "profile_id": "d64_four_head_seq64",
        "baseline_policy": BASELINE_POLICY,
        "layout_policy": LAYOUT_POLICY,
        "source_input_sha256": SOURCE_INPUT_SHA256,
        "baseline_envelope_sha256": BASELINE_ENVELOPE_SHA256,
        "chunk4_envelope_sha256": CHUNK4_ENVELOPE_SHA256,
        "proof_backend": PROOF_BACKEND,
        "proof_backend_version": PROOF_BACKEND_VERSION,
        "statement_version": STATEMENT_VERSION,
        "source_statement_commitment": SOURCE_STATEMENT_COMMITMENT,
        "baseline_proof_size_bytes": BASELINE_PROOF_SIZE_BYTES,
        "chunk4_proof_size_bytes": CHUNK4_PROOF_SIZE_BYTES,
        "saving_vs_baseline_bytes": SAVING_VS_BASELINE_BYTES,
        "source_plus_sidecar_raw_proof_bytes": SOURCE_PLUS_SIDECAR_RAW_PROOF_BYTES,
        "saving_vs_split_bytes": SAVING_VS_SPLIT_BYTES,
        "chunk4_vs_baseline_ratio": CHUNK4_VS_BASELINE_RATIO,
        "chunk4_vs_split_ratio": CHUNK4_VS_SPLIT_RATIO,
        "workload": {
            "head_count": HEAD_COUNT,
            "sequence_length": SEQUENCE_LENGTH,
            "lookup_claims": LOOKUP_CLAIMS,
            "trace_rows": TRACE_ROWS,
            "table_rows": TABLE_ROWS,
        },
    }
    for key, expected in exact.items():
        if row[key] != expected:
            raise D64Chunk4PolicyGateError(f"{key} drift")
    if set(row["section_delta_vs_baseline_bytes"]) != set(section_delta.PROOF_SECTION_KEYS):
        raise D64Chunk4PolicyGateError("section delta key drift")
    if set(row["bucket_delta_vs_baseline_bytes"]) != set(section_delta.PROOF_BUCKET_KEYS):
        raise D64Chunk4PolicyGateError("bucket delta key drift")
    if row["bucket_delta_vs_baseline_bytes"]["opening_bucket_bytes"] != -1_866:
        raise D64Chunk4PolicyGateError("opening delta drift")
    if row["section_delta_vs_baseline_bytes"]["fri_proof"] != -1_374:
        raise D64Chunk4PolicyGateError("FRI delta drift")
    if row["section_delta_vs_baseline_bytes"]["decommitments"] != -492:
        raise D64Chunk4PolicyGateError("decommitment delta drift")
    if row["bucket_delta_vs_baseline_bytes"]["query_bucket_bytes"] != 53:
        raise D64Chunk4PolicyGateError("query delta drift")


def payload_commitment(payload: dict[str, Any]) -> str:
    candidate = copy.deepcopy(payload)
    candidate.pop("payload_commitment", None)
    return blake2b_commitment(candidate, SCHEMA)


def build_base_payload() -> dict[str, Any]:
    row = artifact_row()
    payload = {
        "schema": SCHEMA,
        "issue": ISSUE,
        "source_surface_issue": SOURCE_SURFACE_ISSUE,
        "decision": DECISION,
        "route_id": ROUTE_ID,
        "fork_status": FORK_STATUS,
        "timing_policy": TIMING_POLICY,
        "security_config": SECURITY_CONFIG,
        "result": row,
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload, allow_missing_mutation_summary=True, expected_row=row)
    return payload


def validate_payload(
    payload: Any,
    *,
    allow_missing_mutation_summary: bool = False,
    expected_row: dict[str, Any] | None = None,
) -> None:
    if not isinstance(payload, dict):
        raise D64Chunk4PolicyGateError("payload must be object")
    expected_keys = {
        "schema",
        "issue",
        "source_surface_issue",
        "decision",
        "route_id",
        "fork_status",
        "timing_policy",
        "security_config",
        "result",
        "non_claims",
        "validation_commands",
        "payload_commitment",
    }
    mutation_keys = {"mutation_cases", "mutations_checked", "mutations_rejected", "all_mutations_rejected"}
    if set(payload) - (expected_keys | mutation_keys):
        raise D64Chunk4PolicyGateError("payload field drift")
    if expected_keys - set(payload):
        raise D64Chunk4PolicyGateError("payload field drift")
    exact = {
        "schema": SCHEMA,
        "issue": ISSUE,
        "source_surface_issue": SOURCE_SURFACE_ISSUE,
        "decision": DECISION,
        "route_id": ROUTE_ID,
        "fork_status": FORK_STATUS,
        "timing_policy": TIMING_POLICY,
        "security_config": SECURITY_CONFIG,
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    for key, expected in exact.items():
        if payload[key] != expected:
            raise D64Chunk4PolicyGateError(f"{key} drift")
    if expected_row is None:
        expected_row = artifact_row()
    if payload["result"] != expected_row:
        raise D64Chunk4PolicyGateError("result row drift")
    validate_row(payload["result"])
    if payload_commitment(payload) != payload["payload_commitment"]:
        raise D64Chunk4PolicyGateError("payload commitment drift")
    if not allow_missing_mutation_summary or any(key in payload for key in mutation_keys):
        if not mutation_keys <= set(payload):
            raise D64Chunk4PolicyGateError("mutation summary missing")
        if payload["mutations_checked"] != EXPECTED_MUTATION_COUNT:
            raise D64Chunk4PolicyGateError("mutation count drift")
        if payload["mutations_rejected"] != EXPECTED_MUTATION_COUNT:
            raise D64Chunk4PolicyGateError("mutation rejection drift")
        if payload["all_mutations_rejected"] is not True:
            raise D64Chunk4PolicyGateError("mutation flag drift")
        cases = payload["mutation_cases"]
        if not isinstance(cases, list) or len(cases) != EXPECTED_MUTATION_COUNT:
            raise D64Chunk4PolicyGateError("mutation case count drift")
        if [case.get("name") if isinstance(case, dict) else None for case in cases] != list(EXPECTED_MUTATION_NAMES):
            raise D64Chunk4PolicyGateError("mutation case name drift")
        for case in cases:
            if not isinstance(case, dict) or set(case) != {"name", "rejected", "error"}:
                raise D64Chunk4PolicyGateError("mutation case field drift")
            if case["rejected"] is not True:
                raise D64Chunk4PolicyGateError("mutation survived")
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
    add("layout_policy_relabeling", lambda p: p["result"].__setitem__("layout_policy", "head_blocked"))
    add("post_query_policy_smuggling", lambda p: p["result"].__setitem__("layout_policy", "choose_after_queries"))
    add("baseline_digest_drift", lambda p: p["result"].__setitem__("baseline_envelope_sha256", "00" * 32))
    add("chunk4_digest_drift", lambda p: p["result"].__setitem__("chunk4_envelope_sha256", "11" * 32))
    add("proof_byte_smuggling", lambda p: p["result"].__setitem__("chunk4_proof_size_bytes", 1))
    add("split_saving_smuggling", lambda p: p["result"].__setitem__("saving_vs_split_bytes", 99_999))
    add("native_verify_removed", lambda p: p["validation_commands"].remove(NATIVE_VERIFY_COMMAND))
    add("non_claim_removed", lambda p: p["non_claims"].remove("not a Stwo fork"))
    add("payload_commitment_drift", lambda p: p.__setitem__("payload_commitment", "blake2b-256:" + "bb" * 32))
    add("unknown_field_injection", lambda p: p.__setitem__("unexpected", True))

    if [name for name, _fn in mutations] != list(EXPECTED_MUTATION_NAMES):
        raise D64Chunk4PolicyGateError("mutation spec drift")
    expected_row = payload["result"]
    cases = []
    for name, fn in mutations:
        candidate = copy.deepcopy(base)
        fn(candidate)
        try:
            validate_payload(candidate, allow_missing_mutation_summary=True, expected_row=expected_row)
        except D64Chunk4PolicyGateError as err:
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


def to_tsv(payload: dict[str, Any], *, validated: bool = False) -> str:
    if not validated:
        validate_payload(payload)
    row = payload["result"]
    section = row["section_delta_vs_baseline_bytes"]
    buckets = row["bucket_delta_vs_baseline_bytes"]
    out = StringIO()
    writer = csv.DictWriter(out, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerow(
        {
            "profile_id": row["profile_id"],
            "baseline_policy": row["baseline_policy"],
            "layout_policy": row["layout_policy"],
            "baseline_proof_size_bytes": row["baseline_proof_size_bytes"],
            "chunk4_proof_size_bytes": row["chunk4_proof_size_bytes"],
            "saving_vs_baseline_bytes": row["saving_vs_baseline_bytes"],
            "source_plus_sidecar_raw_proof_bytes": row["source_plus_sidecar_raw_proof_bytes"],
            "saving_vs_split_bytes": row["saving_vs_split_bytes"],
            "chunk4_vs_baseline_ratio": row["chunk4_vs_baseline_ratio"],
            "chunk4_vs_split_ratio": row["chunk4_vs_split_ratio"],
            "opening_delta_vs_baseline_bytes": buckets["opening_bucket_bytes"],
            "fri_delta_vs_baseline_bytes": section["fri_proof"],
            "decommitment_delta_vs_baseline_bytes": section["decommitments"],
            "query_delta_vs_baseline_bytes": buckets["query_bucket_bytes"],
            "source_statement_commitment": row["source_statement_commitment"],
        }
    )
    return out.getvalue()


def to_markdown(payload: dict[str, Any], *, validated: bool = False) -> str:
    if not validated:
        validate_payload(payload)
    row = payload["result"]
    section = row["section_delta_vs_baseline_bytes"]
    buckets = row["bucket_delta_vs_baseline_bytes"]
    return "\n".join(
        [
            "# Stwo-AI D64 Chunk4 Layout Policy Gate",
            "",
            f"- Issue: `#{ISSUE}`",
            f"- Decision: `{DECISION}`",
            f"- Fork status: `{FORK_STATUS}`",
            f"- Timing policy: `{TIMING_POLICY}`",
            f"- Security config: `fri_query_count=3`, `fri_log_blowup=1`, `pow_bits=10`, `fold_step=1`",
            "",
            "## Result",
            "",
            "`chunk4` is now a verifier-bound d64 route-layout policy. It fixes the schedule before proof generation, changes the source statement commitment, and verifies natively.",
            "",
            f"- Baseline fused proof bytes: `{row['baseline_proof_size_bytes']}`",
            f"- Chunk4 fused proof bytes: `{row['chunk4_proof_size_bytes']}`",
            f"- Saving vs baseline fused: `{row['saving_vs_baseline_bytes']}` bytes",
            f"- Matched split frontier: `{row['source_plus_sidecar_raw_proof_bytes']}` bytes",
            f"- Saving vs split frontier: `{row['saving_vs_split_bytes']}` bytes",
            f"- Chunk4 vs baseline ratio: `{row['chunk4_vs_baseline_ratio']}x`",
            f"- Chunk4 vs split ratio: `{row['chunk4_vs_split_ratio']}x`",
            f"- Opening delta vs baseline: `{buckets['opening_bucket_bytes']}` bytes",
            f"- FRI delta vs baseline: `{section['fri_proof']}` bytes",
            f"- Decommitment delta vs baseline: `{section['decommitments']}` bytes",
            f"- Query delta vs baseline: `{buckets['query_bucket_bytes']}` bytes",
            f"- Source statement commitment: `{row['source_statement_commitment']}`",
            "",
            "## Interpretation",
            "",
            "This is a GO for route-layout policy as the next Stwo-AI optimization layer. It is still not a reason to fork Stwo: the current backend already lets a verifier-bound deterministic layout reduce proof bytes on the d64 pressure anchor.",
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
        raise D64Chunk4PolicyGateError("evidence output path must be under docs/engineering/evidence")
    return resolved


def require_docs_output_path(path: pathlib.Path) -> pathlib.Path:
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()
    if resolved.parent != DOCS_DIR.resolve():
        raise D64Chunk4PolicyGateError("markdown output path must be under docs/engineering")
    return resolved


def write_atomic(path: pathlib.Path, content: str, *, docs: bool = False) -> None:
    resolved = require_docs_output_path(path) if docs else require_evidence_output_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    temp_path: pathlib.Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=resolved.parent, delete=False) as handle:
            temp_path = pathlib.Path(handle.name)
            handle.write(content)
        temp_path.replace(resolved)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path, tsv_path: pathlib.Path, md_path: pathlib.Path) -> None:
    validate_payload(payload)
    write_atomic(json_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    write_atomic(tsv_path, to_tsv(payload, validated=True))
    write_atomic(md_path, to_markdown(payload, validated=True), docs=True)


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
