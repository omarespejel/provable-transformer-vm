#!/usr/bin/env python3.10
"""Gate the statement-only attempt-policy transcript profile."""

from __future__ import annotations

import argparse
import copy
import csv
import functools
import hashlib
import io
import json
import os
import pathlib
import sys
from collections.abc import Callable
from typing import Any


if sys.version_info < (3, 10):
    raise RuntimeError("zkai_stwo_statement_only_attempt_transcript_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
RUST_SOURCE_PATH = ROOT / "src" / "stwo_backend" / "native_seq32_attention_mlp_single_proof.rs"
CLI_SOURCE_PATH = ROOT / "src" / "bin" / "zkai_native_seq32_attention_mlp_single_proof.rs"
INNER_ATTEMPT_ACCOUNTING_PATH = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-inner-attempt-domain-accounting-2026-05.json"
STATEMENT_ONLY_ACCOUNTING_PATH = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-statement-only-attempt-accounting-2026-05.json"
PROFILE_ACCOUNTING_PATH = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-attempt-transcript-profile-accounting-2026-05.json"
JSON_OUT = EVIDENCE_DIR / "zkai-stwo-statement-only-attempt-transcript-gate-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-stwo-statement-only-attempt-transcript-gate-2026-05.tsv"
DETERMINISTIC_TEMP_ATTEMPTS = 8

SCHEMA = "zkai-stwo-statement-only-attempt-transcript-gate-v1"
DECISION = "GO_STATEMENT_ONLY_ATTEMPT_POLICY_TRANSCRIPT_REDUCES_REGENERATED_STWO_PROOF_BYTES"
RESULT = "STATEMENT_ONLY_PROBE_B_VERIFIES_AT_39516_TYPED_BYTES_SAVING_1376_VS_FULL_POLICY_MIX"
CLAIM_BOUNDARY = (
    "ATTEMPT_POLICY_REMAINS_IN_STATEMENT_COMMITMENT_MIXED_INTO_FIAT_SHAMIR;"
    "EXTRA_POLICY_FIELD_MIX_REMOVED_FOR_STATEMENT_ONLY_PROFILE;"
    "BOUNDED_TWO_ATTEMPT_DOMAIN_WITH_ONE_BIT_LOSS;"
    "NEW_INNER_POLICY_BOUND_LOCAL_FRONTIER_NOT_LEGACY_WRAPPER_FRONTIER_NOT_NANOZK"
)
ISSUE_HINT = "https://github.com/omarespejel/provable-transformer-vm/issues/680"
PAYLOAD_DOMAIN = "ptvm:zkai:stwo-statement-only-attempt-transcript:v1"

EXPECTED_RUST_SOURCE_SHA256 = "561ed1353365aa22b2b511ed3e7411d9249457ac8a0c11a28b0c4bb1ec866bfd"
EXPECTED_CLI_SOURCE_SHA256 = "9e587a40537e214b24684c50ad488f5732838307669ae86906266d75c597b418"
EXPECTED_INNER_ATTEMPT_ACCOUNTING_SHA256 = "72cad6f598af282215f6579a716816a52e259248a420e27c5759d45482055978"
EXPECTED_STATEMENT_ONLY_ACCOUNTING_SHA256 = "4ca7429d9e97e9fe54526618f36027757ca67a6184478dcfc06045396f765f2c"
EXPECTED_PROFILE_ACCOUNTING_SHA256 = "92d99a4aeb0169ac50e6380f67ad412f11d4985e1e55eb163c4262d965ad8072"
EXPECTED_PAYLOAD_COMMITMENT = "blake2b-256:a60425f6b2fbb4c4b791aab941a41d8a4b0dbeb8a0951252bd33e02f90b9f76d"

SOURCE_ARTIFACT_SPECS = (
    ("rust_native_seq32_attention_mlp_single_proof", RUST_SOURCE_PATH, EXPECTED_RUST_SOURCE_SHA256),
    ("cli_native_seq32_attention_mlp_single_proof", CLI_SOURCE_PATH, EXPECTED_CLI_SOURCE_SHA256),
    ("inner_attempt_accounting", INNER_ATTEMPT_ACCOUNTING_PATH, EXPECTED_INNER_ATTEMPT_ACCOUNTING_SHA256),
    ("statement_only_accounting", STATEMENT_ONLY_ACCOUNTING_PATH, EXPECTED_STATEMENT_ONLY_ACCOUNTING_SHA256),
    ("attempt_transcript_profile_accounting", PROFILE_ACCOUNTING_PATH, EXPECTED_PROFILE_ACCOUNTING_SHA256),
)

ATTEMPT_DOMAIN = ("adjacent_label_probe_a", "adjacent_label_probe_b")
FULL_POLICY_VERSION = "seq32-d128-adjacent-attempt-domain-v1"
FULL_POLICY_STAGE = "inner_statement_transcript_metadata"
COMPACT_POLICY_VERSION = "seq32-d128-adjacent-attempt-domain-compact-transcript-v1"
COMPACT_POLICY_STAGE = "inner_statement_digest_compact_transcript_metadata"
STATEMENT_ONLY_POLICY_VERSION = "seq32-d128-adjacent-attempt-domain-statement-only-transcript-v1"
STATEMENT_ONLY_POLICY_STAGE = "inner_statement_digest_only_transcript_metadata"
ATTEMPT_BUDGET = 2
SECURITY_LOSS_BITS = "1.000000"
SECURITY_LOSS_FORMULA = "log2(2)"
LEGACY_WRAPPER_B_TYPED_BYTES = 37_532
LEGACY_WRAPPER_B_JSON_BYTES = 106_317
FULL_POLICY_B_TYPED_BYTES = 40_892
FULL_POLICY_B_JSON_BYTES = 118_042
COMPACT_B_TYPED_BYTES = 42_156
COMPACT_B_JSON_BYTES = 122_735
STATEMENT_ONLY_A_TYPED_BYTES = 42_780
STATEMENT_ONLY_A_JSON_BYTES = 124_900
STATEMENT_ONLY_B_TYPED_BYTES = 39_516
STATEMENT_ONLY_B_JSON_BYTES = 113_388
PREVIOUS_SINGLE_PROOF_CHAMPION_TYPED_BYTES = 42_068
PREVIOUS_SINGLE_PROOF_CHAMPION_JSON_BYTES = 121_996
MATCHED_TWO_PROOF_FRONTIER_TYPED_BYTES = 47_188
MATCHED_TWO_PROOF_FRONTIER_JSON_BYTES = 140_838
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900

EXPECTED_ATTEMPT_NON_CLAIMS = (
    "not unbounded retry",
    "not post-decommitment selection",
    "not final proof-byte selection",
    "not absolute soundness",
    "not a NANOZK proof-size comparison",
)
NON_CLAIMS = (
    "not a NANOZK proof-size comparison",
    "not a matched external zkML benchmark",
    "not a full transformer block proof",
    "not exact real-valued Softmax",
    "not timing evidence",
    "not production-ready zkML",
    "not a proof-size frontier beyond the legacy wrapper-only 37,532 typed-byte row",
    "not a free retry policy; the two-attempt domain is explicit and charged as one bit",
)

PROFILE_ARTIFACTS = (
    {
        "profile_id": "full_policy_field_mix_probe_b",
        "profile_kind": "full_policy_field_mix",
        "variant_id": "adjacent_label_probe_b",
        "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_b_v1",
        "selected_attempt_id": "adjacent_label_probe_b",
        "selected_attempt_index": 1,
        "policy_version": FULL_POLICY_VERSION,
        "policy_stage": FULL_POLICY_STAGE,
        "input_path": EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-inner-attempt-2026-05.input.json",
        "envelope_path": EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-inner-attempt-2026-05.envelope.json",
        "sampler_path": EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-inner-attempt-2026-05-opening-sampler-2026-05.json",
        "accounting_path": INNER_ATTEMPT_ACCOUNTING_PATH,
        "expected_typed_bytes": FULL_POLICY_B_TYPED_BYTES,
        "expected_json_bytes": FULL_POLICY_B_JSON_BYTES,
    },
    {
        "profile_id": "compact_policy_mix_probe_b",
        "profile_kind": "compact_policy_mix",
        "variant_id": "adjacent_label_probe_b",
        "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_b_v1",
        "selected_attempt_id": "adjacent_label_probe_b",
        "selected_attempt_index": 1,
        "policy_version": COMPACT_POLICY_VERSION,
        "policy_stage": COMPACT_POLICY_STAGE,
        "input_path": EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-compact-transcript-2026-05.input.json",
        "envelope_path": EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-compact-transcript-2026-05.envelope.json",
        "sampler_path": EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-compact-transcript-2026-05-opening-sampler-2026-05.json",
        "accounting_path": PROFILE_ACCOUNTING_PATH,
        "expected_typed_bytes": COMPACT_B_TYPED_BYTES,
        "expected_json_bytes": COMPACT_B_JSON_BYTES,
    },
    {
        "profile_id": "statement_only_probe_a",
        "profile_kind": "statement_only",
        "variant_id": "adjacent_label_probe_a",
        "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_a_v1",
        "selected_attempt_id": "adjacent_label_probe_a",
        "selected_attempt_index": 0,
        "policy_version": STATEMENT_ONLY_POLICY_VERSION,
        "policy_stage": STATEMENT_ONLY_POLICY_STAGE,
        "input_path": EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-statement-only-transcript-2026-05.input.json",
        "envelope_path": EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-statement-only-transcript-2026-05.envelope.json",
        "sampler_path": EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-statement-only-transcript-2026-05-opening-sampler-2026-05.json",
        "accounting_path": STATEMENT_ONLY_ACCOUNTING_PATH,
        "expected_typed_bytes": STATEMENT_ONLY_A_TYPED_BYTES,
        "expected_json_bytes": STATEMENT_ONLY_A_JSON_BYTES,
    },
    {
        "profile_id": "statement_only_probe_b",
        "profile_kind": "statement_only",
        "variant_id": "adjacent_label_probe_b",
        "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_b_v1",
        "selected_attempt_id": "adjacent_label_probe_b",
        "selected_attempt_index": 1,
        "policy_version": STATEMENT_ONLY_POLICY_VERSION,
        "policy_stage": STATEMENT_ONLY_POLICY_STAGE,
        "input_path": EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.input.json",
        "envelope_path": EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.envelope.json",
        "sampler_path": EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05-opening-sampler-2026-05.json",
        "accounting_path": STATEMENT_ONLY_ACCOUNTING_PATH,
        "expected_typed_bytes": STATEMENT_ONLY_B_TYPED_BYTES,
        "expected_json_bytes": STATEMENT_ONLY_B_JSON_BYTES,
    },
)

VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent-label-probe-a-statement-only-transcript docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-statement-only-transcript-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-statement-only-transcript-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-statement-only-transcript-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-statement-only-transcript-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent-label-probe-b-statement-only-transcript docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-statement-only-transcript-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.envelope.json > docs/engineering/evidence/zkai-native-seq32-attention-mlp-statement-only-attempt-accounting-2026-05.json",
    "python3.10 scripts/zkai_stwo_statement_only_attempt_transcript_gate.py --write-json docs/engineering/evidence/zkai-stwo-statement-only-attempt-transcript-gate-2026-05.json --write-tsv docs/engineering/evidence/zkai-stwo-statement-only-attempt-transcript-gate-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_stwo_statement_only_attempt_transcript_gate.py scripts/tests/test_zkai_stwo_statement_only_attempt_transcript_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_stwo_statement_only_attempt_transcript_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_adjacent_label_probe_statement_only_attempt_profile_validates --lib",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend native_seq32_attention_mlp_single_proof --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

PAYLOAD_KEYS = {
    "schema",
    "decision",
    "result",
    "claim_boundary",
    "issue_hint",
    "source_artifacts",
    "profile_rows",
    "binding_summary",
    "interpretation",
    "non_claims",
    "validation_commands",
    "mutation_result",
    "payload_commitment",
}
PROFILE_ROW_KEYS = {
    "profile_id",
    "profile_kind",
    "variant_id",
    "adapter_mode",
    "selected_attempt_id",
    "selected_attempt_index",
    "policy_version",
    "policy_stage",
    "input_path",
    "envelope_path",
    "sampler_path",
    "input_sha256",
    "envelope_sha256",
    "sampler_sha256",
    "proof_sha256",
    "statement_commitment",
    "public_instance_commitment",
    "proof_native_parameter_commitment",
    "proof_json_bytes",
    "typed_bytes",
    "typed_delta_vs_full_policy_b",
    "json_delta_vs_full_policy_b",
    "typed_saving_vs_matched_two_proof_frontier",
    "json_saving_vs_matched_two_proof_frontier",
    "typed_cost_vs_legacy_wrapper_b",
    "json_cost_vs_legacy_wrapper_b",
    "query_locations",
    "query_span",
    "min_pairwise_query_gap",
    "grouped_reconstruction",
    "record_stream_sha256",
}
SUMMARY_KEYS = {
    "statement_commitment_binds_policy",
    "statement_commitment_is_mixed_into_fiat_shamir",
    "extra_policy_field_mix_removed",
    "attempt_budget",
    "security_loss_bits",
    "best_profile_id",
    "best_variant_id",
    "best_typed_bytes",
    "best_json_bytes",
    "best_typed_saving_vs_full_policy_b",
    "best_json_saving_vs_full_policy_b",
    "best_typed_saving_vs_previous_single_proof_champion",
    "best_typed_saving_vs_matched_two_proof_frontier",
    "best_json_saving_vs_matched_two_proof_frontier",
    "best_typed_cost_vs_legacy_wrapper_b",
    "compact_profile_no_go_typed_delta_vs_full_policy_b",
    "statement_only_worst_typed_bytes",
    "inner_policy_bound_frontier_claimed",
    "legacy_wrapper_frontier_claimed",
    "nanozk_comparable_external_rows",
    "nanozk_gap_typed_bytes",
}
MUTATION_NAMES = (
    "decision_drift",
    "claim_boundary_overclaim",
    "rust_source_digest_drift",
    "cli_source_digest_drift",
    "statement_accounting_digest_drift",
    "profile_accounting_digest_drift",
    "policy_version_drift",
    "policy_stage_drift",
    "selected_attempt_changed",
    "attempt_budget_drift",
    "security_loss_understated",
    "statement_policy_removed",
    "typed_bytes_drift",
    "full_policy_saving_erased",
    "compact_profile_promoted",
    "legacy_wrapper_overclaim",
    "nanozk_overclaim",
    "validation_command_drift",
    "removed_non_claim",
    "payload_commitment_drift",
)
EXPECTED_MUTATION_ERRORS = {
    "decision_drift": "decision drift",
    "claim_boundary_overclaim": "claim_boundary drift",
    "rust_source_digest_drift": "source artifact drift",
    "cli_source_digest_drift": "source artifact drift",
    "statement_accounting_digest_drift": "source artifact drift",
    "profile_accounting_digest_drift": "source artifact drift",
    "policy_version_drift": "profile row drift",
    "policy_stage_drift": "profile row drift",
    "selected_attempt_changed": "profile row drift",
    "attempt_budget_drift": "binding summary drift",
    "security_loss_understated": "binding summary drift",
    "statement_policy_removed": "profile row field drift: missing policy_version",
    "typed_bytes_drift": "profile row drift",
    "full_policy_saving_erased": "binding summary drift",
    "compact_profile_promoted": "binding summary drift",
    "legacy_wrapper_overclaim": "binding summary drift",
    "nanozk_overclaim": "claim_boundary drift",
    "validation_command_drift": "validation command drift",
    "removed_non_claim": "non_claims drift",
    "payload_commitment_drift": "payload commitment drift",
}
TSV_COLUMNS = (
    "best_profile_id",
    "best_variant_id",
    "typed_bytes",
    "proof_json_bytes",
    "typed_saving_vs_full_policy_b",
    "json_saving_vs_full_policy_b",
    "typed_saving_vs_matched_two_proof_frontier",
    "json_saving_vs_matched_two_proof_frontier",
    "typed_cost_vs_legacy_wrapper_b",
    "attempt_budget",
    "security_loss_bits",
    "inner_policy_bound_frontier_claimed",
    "legacy_wrapper_frontier_claimed",
    "payload_commitment",
    "mutation_outcomes",
)


class StatementOnlyAttemptTranscriptGateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as err:
        raise StatementOnlyAttemptTranscriptGateError(f"invalid JSON value: {err}") from err


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return "blake2b-256:" + digest.hexdigest()


def read_bytes(path: pathlib.Path) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise StatementOnlyAttemptTranscriptGateError(f"unsafe evidence path: {path}")
    return path.read_bytes()


def read_json(path: pathlib.Path) -> Any:
    try:
        return json.loads(read_bytes(path))
    except json.JSONDecodeError as err:
        raise StatementOnlyAttemptTranscriptGateError(f"invalid JSON in {path}: {err}") from err


def require_output_path(path: pathlib.Path) -> pathlib.Path:
    candidate = path if path.is_absolute() else ROOT / path
    evidence_root = EVIDENCE_DIR.resolve(strict=True)
    try:
        parent = candidate.parent.resolve(strict=True)
    except FileNotFoundError as err:
        raise StatementOnlyAttemptTranscriptGateError(f"output parent missing: {candidate.parent}") from err
    if parent != evidence_root and evidence_root not in parent.parents:
        raise StatementOnlyAttemptTranscriptGateError("output path must stay under evidence directory")
    if candidate.is_symlink():
        raise StatementOnlyAttemptTranscriptGateError("output path must not be a symlink")
    return candidate


def atomic_write_text(path: pathlib.Path, text: str) -> None:
    output = require_output_path(path)
    payload = text.encode("utf-8")
    parent = output.parent
    tmp_path: pathlib.Path | None = None
    for attempt in range(DETERMINISTIC_TEMP_ATTEMPTS):
        candidate = parent / f".{output.name}.tmp.{attempt}"
        try:
            fd = os.open(candidate, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            continue
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
        tmp_path = candidate
        break
    if tmp_path is None:
        raise StatementOnlyAttemptTranscriptGateError(f"deterministic temp file collision for {output.name}")
    try:
        os.replace(tmp_path, output)
    except OSError:
        try:
            tmp_path.unlink()
        finally:
            raise


def _dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise StatementOnlyAttemptTranscriptGateError(f"{label} must be object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise StatementOnlyAttemptTranscriptGateError(f"{label} must be list")
    return value


def _int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise StatementOnlyAttemptTranscriptGateError(f"{label} must be integer")
    return value


def source_artifacts() -> list[dict[str, str]]:
    artifacts = []
    for artifact_id, path, expected_sha in SOURCE_ARTIFACT_SPECS:
        actual_sha = sha256(read_bytes(path))
        if actual_sha != expected_sha:
            raise StatementOnlyAttemptTranscriptGateError(f"source artifact drift: {artifact_id}")
        artifacts.append(
            {
                "id": artifact_id,
                "path": str(path.relative_to(ROOT)),
                "sha256": actual_sha,
            }
        )
    return artifacts


@functools.lru_cache(maxsize=None)
def accounting_rows(path: pathlib.Path) -> dict[str, dict[str, Any]]:
    data = _dict(read_json(path), f"{path.name} accounting")
    rows = _list(data.get("rows"), f"{path.name} rows")
    by_name = {}
    for row in rows:
        row_dict = _dict(row, f"{path.name} row")
        evidence_path = row_dict.get("evidence_relative_path")
        if not isinstance(evidence_path, str):
            raise StatementOnlyAttemptTranscriptGateError(f"{path.name} row missing evidence path")
        by_name[evidence_path] = row_dict
    return by_name


def min_pairwise_gap(locations: list[int]) -> int:
    if len(locations) < 2:
        return 0
    gaps = [b - a for a, b in zip(locations, locations[1:])]
    return min(gaps)


def profile_row(spec: dict[str, Any]) -> dict[str, Any]:
    input_data = _dict(read_json(spec["input_path"]), f"{spec['profile_id']} input")
    envelope = _dict(read_json(spec["envelope_path"]), f"{spec['profile_id']} envelope")
    sampler = _dict(read_json(spec["sampler_path"]), f"{spec['profile_id']} sampler")
    envelope_input = _dict(envelope.get("input"), f"{spec['profile_id']} envelope input")
    policy = _dict(input_data.get("attempt_policy"), f"{spec['profile_id']} attempt policy")
    envelope_policy = _dict(envelope_input.get("attempt_policy"), f"{spec['profile_id']} envelope policy")
    sampler_policy = _dict(sampler.get("attempt_policy"), f"{spec['profile_id']} sampler policy")
    accounting = accounting_rows(spec["accounting_path"])
    accounting_row = accounting.get(spec["envelope_path"].name)
    if accounting_row is None:
        raise StatementOnlyAttemptTranscriptGateError(f"missing accounting row: {spec['profile_id']}")
    local_accounting = _dict(accounting_row.get("local_binary_accounting"), f"{spec['profile_id']} local accounting")
    typed_bytes = _int(local_accounting.get("typed_size_estimate_bytes"), f"{spec['profile_id']} typed bytes")
    json_bytes = _int(accounting_row.get("proof_json_size_bytes"), f"{spec['profile_id']} JSON bytes")
    if typed_bytes != spec["expected_typed_bytes"] or json_bytes != spec["expected_json_bytes"]:
        raise StatementOnlyAttemptTranscriptGateError(f"profile row drift: {spec['profile_id']} bytes")
    for policy_obj in (policy, envelope_policy, sampler_policy):
        for key, expected in (
            ("policy_version", spec["policy_version"]),
            ("policy_stage", spec["policy_stage"]),
            ("selected_attempt_id", spec["selected_attempt_id"]),
            ("selected_attempt_index", spec["selected_attempt_index"]),
            ("attempt_budget", ATTEMPT_BUDGET),
            ("security_loss_bits", SECURITY_LOSS_BITS),
            ("security_loss_formula", SECURITY_LOSS_FORMULA),
        ):
            if policy_obj.get(key) != expected:
                raise StatementOnlyAttemptTranscriptGateError(f"profile row drift: {spec['profile_id']} {key}")
        if tuple(policy_obj.get("attempt_domain", ())) != ATTEMPT_DOMAIN:
            raise StatementOnlyAttemptTranscriptGateError(f"profile row drift: {spec['profile_id']} attempt domain")
        if tuple(policy_obj.get("non_claims", ())) != EXPECTED_ATTEMPT_NON_CLAIMS:
            raise StatementOnlyAttemptTranscriptGateError(f"profile row drift: {spec['profile_id']} non-claims")
    for key in ("adapter_mode", "statement_commitment", "public_instance_commitment", "proof_native_parameter_commitment"):
        if input_data.get(key) != envelope_input.get(key) or input_data.get(key) != sampler.get(key):
            raise StatementOnlyAttemptTranscriptGateError(f"profile row drift: {spec['profile_id']} {key}")
    if input_data.get("adapter_mode") != spec["adapter_mode"]:
        raise StatementOnlyAttemptTranscriptGateError(f"profile row drift: {spec['profile_id']} adapter mode")
    locations = [
        _int(value, f"{spec['profile_id']} query location")
        for value in _list(
            sampler.get("sorted_unique_query_locations"),
            f"{spec['profile_id']} query locations",
        )
    ]
    if not locations:
        raise StatementOnlyAttemptTranscriptGateError(
            f"profile row drift: {spec['profile_id']} query locations"
        )
    grouped = _dict(local_accounting.get("grouped_reconstruction"), f"{spec['profile_id']} grouped reconstruction")
    return {
        "profile_id": spec["profile_id"],
        "profile_kind": spec["profile_kind"],
        "variant_id": spec["variant_id"],
        "adapter_mode": spec["adapter_mode"],
        "selected_attempt_id": spec["selected_attempt_id"],
        "selected_attempt_index": spec["selected_attempt_index"],
        "policy_version": spec["policy_version"],
        "policy_stage": spec["policy_stage"],
        "input_path": str(spec["input_path"].relative_to(ROOT)),
        "envelope_path": str(spec["envelope_path"].relative_to(ROOT)),
        "sampler_path": str(spec["sampler_path"].relative_to(ROOT)),
        "input_sha256": sha256(read_bytes(spec["input_path"])),
        "envelope_sha256": accounting_row["envelope_sha256"],
        "sampler_sha256": sha256(read_bytes(spec["sampler_path"])),
        "proof_sha256": accounting_row["proof_sha256"],
        "statement_commitment": input_data["statement_commitment"],
        "public_instance_commitment": input_data["public_instance_commitment"],
        "proof_native_parameter_commitment": input_data["proof_native_parameter_commitment"],
        "proof_json_bytes": json_bytes,
        "typed_bytes": typed_bytes,
        "typed_delta_vs_full_policy_b": typed_bytes - FULL_POLICY_B_TYPED_BYTES,
        "json_delta_vs_full_policy_b": json_bytes - FULL_POLICY_B_JSON_BYTES,
        "typed_saving_vs_matched_two_proof_frontier": MATCHED_TWO_PROOF_FRONTIER_TYPED_BYTES - typed_bytes,
        "json_saving_vs_matched_two_proof_frontier": MATCHED_TWO_PROOF_FRONTIER_JSON_BYTES - json_bytes,
        "typed_cost_vs_legacy_wrapper_b": typed_bytes - LEGACY_WRAPPER_B_TYPED_BYTES,
        "json_cost_vs_legacy_wrapper_b": json_bytes - LEGACY_WRAPPER_B_JSON_BYTES,
        "query_locations": locations,
        "query_span": max(locations) - min(locations),
        "min_pairwise_query_gap": min_pairwise_gap(locations),
        "grouped_reconstruction": grouped,
        "record_stream_sha256": local_accounting["record_stream_sha256"],
    }


def build_payload() -> dict[str, Any]:
    rows = [profile_row(spec) for spec in PROFILE_ARTIFACTS]
    best = min(rows, key=lambda row: row["typed_bytes"])
    statement_rows = [row for row in rows if row["profile_kind"] == "statement_only"]
    compact = next(row for row in rows if row["profile_kind"] == "compact_policy_mix")
    summary = {
        "statement_commitment_binds_policy": True,
        "statement_commitment_is_mixed_into_fiat_shamir": True,
        "extra_policy_field_mix_removed": True,
        "attempt_budget": ATTEMPT_BUDGET,
        "security_loss_bits": SECURITY_LOSS_BITS,
        "best_profile_id": "statement_only_probe_b",
        "best_variant_id": "adjacent_label_probe_b",
        "best_typed_bytes": STATEMENT_ONLY_B_TYPED_BYTES,
        "best_json_bytes": STATEMENT_ONLY_B_JSON_BYTES,
        "best_typed_saving_vs_full_policy_b": FULL_POLICY_B_TYPED_BYTES - STATEMENT_ONLY_B_TYPED_BYTES,
        "best_json_saving_vs_full_policy_b": FULL_POLICY_B_JSON_BYTES - STATEMENT_ONLY_B_JSON_BYTES,
        "best_typed_saving_vs_previous_single_proof_champion": PREVIOUS_SINGLE_PROOF_CHAMPION_TYPED_BYTES - STATEMENT_ONLY_B_TYPED_BYTES,
        "best_typed_saving_vs_matched_two_proof_frontier": MATCHED_TWO_PROOF_FRONTIER_TYPED_BYTES - STATEMENT_ONLY_B_TYPED_BYTES,
        "best_json_saving_vs_matched_two_proof_frontier": MATCHED_TWO_PROOF_FRONTIER_JSON_BYTES - STATEMENT_ONLY_B_JSON_BYTES,
        "best_typed_cost_vs_legacy_wrapper_b": STATEMENT_ONLY_B_TYPED_BYTES - LEGACY_WRAPPER_B_TYPED_BYTES,
        "compact_profile_no_go_typed_delta_vs_full_policy_b": compact["typed_delta_vs_full_policy_b"],
        "statement_only_worst_typed_bytes": max(row["typed_bytes"] for row in statement_rows),
        "inner_policy_bound_frontier_claimed": True,
        "legacy_wrapper_frontier_claimed": False,
        "nanozk_comparable_external_rows": 0,
        "nanozk_gap_typed_bytes": STATEMENT_ONLY_B_TYPED_BYTES - NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
    }
    if best["profile_id"] != summary["best_profile_id"]:
        raise StatementOnlyAttemptTranscriptGateError("binding summary drift: best profile")
    interpretation = {
        "human_read": (
            "The useful result is that statement binding does not require mixing every policy string field separately. "
            "Because the statement commitment already contains the attempt policy and is mixed into Fiat-Shamir, the "
            "statement-only profile keeps the verifier-facing policy boundary while reducing typed proof bytes."
        ),
        "mechanism": "remove redundant full-policy field mix; keep policy inside statement commitment mixed before lookup challenge draw",
        "go_no_go": {
            "statement_only": "GO for regenerated inner-policy-bound proof-size improvement",
            "compact_policy_mix": "NO_GO; compact policy field mix is heavier than the full-policy baseline",
            "legacy_wrapper": "context only; still smaller but weaker because the policy is not inner statement-bound",
        },
    }
    payload = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "issue_hint": ISSUE_HINT,
        "source_artifacts": source_artifacts(),
        "profile_rows": rows,
        "binding_summary": summary,
        "interpretation": interpretation,
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
        "mutation_result": {},
    }
    payload["mutation_result"] = mutation_result(payload)
    payload["payload_commitment"] = payload_commitment(payload)
    return payload


def validate_payload(payload: dict[str, Any], *, check_commitment: bool = True, check_mutations: bool = True) -> None:
    if set(payload) != PAYLOAD_KEYS:
        raise StatementOnlyAttemptTranscriptGateError("payload key drift")
    for key, expected in (
        ("schema", SCHEMA),
        ("decision", DECISION),
        ("result", RESULT),
        ("claim_boundary", CLAIM_BOUNDARY),
        ("issue_hint", ISSUE_HINT),
    ):
        if payload.get(key) != expected:
            raise StatementOnlyAttemptTranscriptGateError(f"{key} drift")
    if "legacy wrapper frontier" in payload["claim_boundary"].lower() and "NOT_LEGACY_WRAPPER_FRONTIER" not in payload["claim_boundary"]:
        raise StatementOnlyAttemptTranscriptGateError("claim_boundary drift")
    artifacts = _list(payload.get("source_artifacts"), "source artifacts")
    if len(artifacts) != len(SOURCE_ARTIFACT_SPECS):
        raise StatementOnlyAttemptTranscriptGateError("source artifact drift")
    for artifact, expected in zip(artifacts, SOURCE_ARTIFACT_SPECS, strict=True):
        artifact_dict = _dict(artifact, "source artifact")
        if set(artifact_dict) != {"id", "path", "sha256"}:
            raise StatementOnlyAttemptTranscriptGateError("source artifact drift")
        expected_id, expected_path, expected_sha = expected
        if artifact_dict != {
            "id": expected_id,
            "path": str(expected_path.relative_to(ROOT)),
            "sha256": expected_sha,
        }:
            raise StatementOnlyAttemptTranscriptGateError("source artifact drift")
    rows = _list(payload.get("profile_rows"), "profile rows")
    if len(rows) != len(PROFILE_ARTIFACTS):
        raise StatementOnlyAttemptTranscriptGateError("profile row count drift")
    for row, expected in zip(rows, PROFILE_ARTIFACTS, strict=True):
        row_dict = _dict(row, "profile row")
        if set(row_dict) != PROFILE_ROW_KEYS:
            missing = PROFILE_ROW_KEYS - set(row_dict)
            raise StatementOnlyAttemptTranscriptGateError(
                f"profile row field drift: missing {sorted(missing)[0] if missing else 'extra'}"
            )
        for key in ("profile_id", "profile_kind", "variant_id", "adapter_mode", "selected_attempt_id", "selected_attempt_index", "policy_version", "policy_stage"):
            if row_dict[key] != expected[key]:
                raise StatementOnlyAttemptTranscriptGateError("profile row drift")
        if (
            row_dict["typed_bytes"] != expected["expected_typed_bytes"]
            or row_dict["proof_json_bytes"] != expected["expected_json_bytes"]
            or row_dict["typed_delta_vs_full_policy_b"] != expected["expected_typed_bytes"] - FULL_POLICY_B_TYPED_BYTES
            or row_dict["json_delta_vs_full_policy_b"] != expected["expected_json_bytes"] - FULL_POLICY_B_JSON_BYTES
            or row_dict["typed_saving_vs_matched_two_proof_frontier"] != MATCHED_TWO_PROOF_FRONTIER_TYPED_BYTES - expected["expected_typed_bytes"]
            or row_dict["json_saving_vs_matched_two_proof_frontier"] != MATCHED_TWO_PROOF_FRONTIER_JSON_BYTES - expected["expected_json_bytes"]
            or row_dict["typed_cost_vs_legacy_wrapper_b"] != expected["expected_typed_bytes"] - LEGACY_WRAPPER_B_TYPED_BYTES
            or row_dict["json_cost_vs_legacy_wrapper_b"] != expected["expected_json_bytes"] - LEGACY_WRAPPER_B_JSON_BYTES
        ):
            raise StatementOnlyAttemptTranscriptGateError("profile row drift")
    summary = _dict(payload.get("binding_summary"), "binding summary")
    if set(summary) != SUMMARY_KEYS:
        raise StatementOnlyAttemptTranscriptGateError("binding summary field drift")
    expected_summary = {
        "statement_commitment_binds_policy": True,
        "statement_commitment_is_mixed_into_fiat_shamir": True,
        "extra_policy_field_mix_removed": True,
        "attempt_budget": ATTEMPT_BUDGET,
        "security_loss_bits": SECURITY_LOSS_BITS,
        "best_profile_id": "statement_only_probe_b",
        "best_variant_id": "adjacent_label_probe_b",
        "best_typed_bytes": STATEMENT_ONLY_B_TYPED_BYTES,
        "best_json_bytes": STATEMENT_ONLY_B_JSON_BYTES,
        "best_typed_saving_vs_full_policy_b": 1_376,
        "best_json_saving_vs_full_policy_b": 4_654,
        "best_typed_saving_vs_previous_single_proof_champion": 2_552,
        "best_typed_saving_vs_matched_two_proof_frontier": 7_672,
        "best_json_saving_vs_matched_two_proof_frontier": 27_450,
        "best_typed_cost_vs_legacy_wrapper_b": 1_984,
        "compact_profile_no_go_typed_delta_vs_full_policy_b": 1_264,
        "statement_only_worst_typed_bytes": STATEMENT_ONLY_A_TYPED_BYTES,
        "inner_policy_bound_frontier_claimed": True,
        "legacy_wrapper_frontier_claimed": False,
        "nanozk_comparable_external_rows": 0,
        "nanozk_gap_typed_bytes": 32_616,
    }
    if summary != expected_summary:
        raise StatementOnlyAttemptTranscriptGateError("binding summary drift")
    if tuple(payload.get("non_claims", ())) != NON_CLAIMS:
        raise StatementOnlyAttemptTranscriptGateError("non_claims drift")
    if tuple(payload.get("validation_commands", ())) != VALIDATION_COMMANDS:
        raise StatementOnlyAttemptTranscriptGateError("validation command drift")
    if check_mutations:
        mutation = _dict(payload.get("mutation_result"), "mutation result")
        if mutation.get("rejected") != len(MUTATION_NAMES) or mutation.get("accepted") != 0:
            raise StatementOnlyAttemptTranscriptGateError("mutation summary drift")
        outcomes = _dict(mutation.get("outcomes"), "mutation outcomes")
        if set(outcomes) != set(MUTATION_NAMES):
            raise StatementOnlyAttemptTranscriptGateError("mutation outcome drift")
        for name in MUTATION_NAMES:
            if outcomes[name] != "rejected":
                raise StatementOnlyAttemptTranscriptGateError("mutation outcome drift")
    if check_commitment:
        if EXPECTED_PAYLOAD_COMMITMENT != "__TO_FILL__" and payload.get("payload_commitment") != EXPECTED_PAYLOAD_COMMITMENT:
            raise StatementOnlyAttemptTranscriptGateError("payload commitment drift")
        if payload_commitment(payload) != payload.get("payload_commitment"):
            raise StatementOnlyAttemptTranscriptGateError("payload commitment drift")
        if EXPECTED_PAYLOAD_COMMITMENT != "__TO_FILL__" and payload_commitment(payload) != EXPECTED_PAYLOAD_COMMITMENT:
            raise StatementOnlyAttemptTranscriptGateError("payload commitment drift")


def mutation_cases() -> tuple[tuple[str, Callable[[dict[str, Any]], None]], ...]:
    return (
        ("decision_drift", lambda item: item.update({"decision": "NO_GO"})),
        ("claim_boundary_overclaim", lambda item: item.update({"claim_boundary": "NANOZK_COMPARABLE_WIN"})),
        ("rust_source_digest_drift", lambda item: item["source_artifacts"][0].update({"sha256": "00"})),
        ("cli_source_digest_drift", lambda item: item["source_artifacts"][1].update({"sha256": "00"})),
        ("statement_accounting_digest_drift", lambda item: item["source_artifacts"][3].update({"sha256": "00"})),
        ("profile_accounting_digest_drift", lambda item: item["source_artifacts"][4].update({"sha256": "00"})),
        ("policy_version_drift", lambda item: item["profile_rows"][3].update({"policy_version": FULL_POLICY_VERSION})),
        ("policy_stage_drift", lambda item: item["profile_rows"][3].update({"policy_stage": FULL_POLICY_STAGE})),
        ("selected_attempt_changed", lambda item: item["profile_rows"][3].update({"selected_attempt_id": "adjacent_label_probe_a"})),
        ("attempt_budget_drift", lambda item: item["binding_summary"].update({"attempt_budget": 1})),
        ("security_loss_understated", lambda item: item["binding_summary"].update({"security_loss_bits": "0.000000"})),
        ("statement_policy_removed", lambda item: item["profile_rows"][3].pop("policy_version")),
        ("typed_bytes_drift", lambda item: item["profile_rows"][3].update({"typed_bytes": STATEMENT_ONLY_B_TYPED_BYTES + 1})),
        ("full_policy_saving_erased", lambda item: item["binding_summary"].update({"best_typed_saving_vs_full_policy_b": 0})),
        ("compact_profile_promoted", lambda item: item["binding_summary"].update({"best_profile_id": "compact_policy_mix_probe_b"})),
        ("legacy_wrapper_overclaim", lambda item: item["binding_summary"].update({"legacy_wrapper_frontier_claimed": True})),
        ("nanozk_overclaim", lambda item: item.update({"claim_boundary": CLAIM_BOUNDARY + ";NANOZK_PROOF_SIZE_WIN"})),
        ("validation_command_drift", lambda item: item["validation_commands"].append("gh workflow run ci.yml")),
        ("removed_non_claim", lambda item: item["non_claims"].pop()),
        ("payload_commitment_drift", lambda item: item.update({"payload_commitment": "blake2b-256:00"})),
    )


def mutation_result(payload: dict[str, Any]) -> dict[str, Any]:
    outcomes: dict[str, str] = {}
    for name, mutate in mutation_cases():
        mutated = copy.deepcopy(payload)
        mutated["mutation_result"] = {"accepted": 0, "rejected": 0, "outcomes": {}}
        mutated["payload_commitment"] = payload_commitment(mutated)
        mutate(mutated)
        if name != "payload_commitment_drift":
            mutated["payload_commitment"] = payload_commitment(mutated)
        try:
            validate_payload(
                mutated,
                check_commitment=name == "payload_commitment_drift",
                check_mutations=False,
            )
        except StatementOnlyAttemptTranscriptGateError as err:
            message = str(err)
            expected = EXPECTED_MUTATION_ERRORS[name]
            if expected not in message:
                raise StatementOnlyAttemptTranscriptGateError(
                    f"mutation {name} rejected with unexpected error: {message}"
                ) from err
            outcomes[name] = "rejected"
        else:
            raise StatementOnlyAttemptTranscriptGateError(f"mutation {name} unexpectedly accepted")
    return {
        "accepted": 0,
        "rejected": len(outcomes),
        "outcomes": outcomes,
    }


def write_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_tsv(path: pathlib.Path, payload: dict[str, Any]) -> None:
    summary = payload["binding_summary"]
    mutation_outcomes = ",".join(sorted(payload["mutation_result"]["outcomes"]))
    row = {
        "best_profile_id": summary["best_profile_id"],
        "best_variant_id": summary["best_variant_id"],
        "typed_bytes": summary["best_typed_bytes"],
        "proof_json_bytes": summary["best_json_bytes"],
        "typed_saving_vs_full_policy_b": summary["best_typed_saving_vs_full_policy_b"],
        "json_saving_vs_full_policy_b": summary["best_json_saving_vs_full_policy_b"],
        "typed_saving_vs_matched_two_proof_frontier": summary["best_typed_saving_vs_matched_two_proof_frontier"],
        "json_saving_vs_matched_two_proof_frontier": summary["best_json_saving_vs_matched_two_proof_frontier"],
        "typed_cost_vs_legacy_wrapper_b": summary["best_typed_cost_vs_legacy_wrapper_b"],
        "attempt_budget": summary["attempt_budget"],
        "security_loss_bits": summary["security_loss_bits"],
        "inner_policy_bound_frontier_claimed": summary["inner_policy_bound_frontier_claimed"],
        "legacy_wrapper_frontier_claimed": summary["legacy_wrapper_frontier_claimed"],
        "payload_commitment": payload["payload_commitment"],
        "mutation_outcomes": mutation_outcomes,
    }
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=TSV_COLUMNS, dialect="excel-tab", lineterminator="\n")
    writer.writeheader()
    writer.writerow(row)
    atomic_write_text(path, buffer.getvalue())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path, default=None)
    parser.add_argument("--write-tsv", type=pathlib.Path, default=None)
    args = parser.parse_args(argv)
    payload = build_payload()
    validate_payload(payload, check_commitment=EXPECTED_PAYLOAD_COMMITMENT != "__TO_FILL__")
    if args.write_json is not None:
        write_json(args.write_json, payload)
    if args.write_tsv is not None:
        write_tsv(args.write_tsv, payload)
    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "decision": DECISION,
                "result": RESULT,
                "best_profile_id": payload["binding_summary"]["best_profile_id"],
                "best_typed_bytes": payload["binding_summary"]["best_typed_bytes"],
                "typed_saving_vs_full_policy_b": payload["binding_summary"]["best_typed_saving_vs_full_policy_b"],
                "typed_saving_vs_matched_two_proof_frontier": payload["binding_summary"]["best_typed_saving_vs_matched_two_proof_frontier"],
                "payload_commitment": payload["payload_commitment"],
                "mutation_rejections": payload["mutation_result"]["rejected"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
