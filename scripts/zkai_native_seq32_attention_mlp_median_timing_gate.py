#!/usr/bin/env python3.10
"""Gate engineering-local median timing for the seq32+d128 native object."""

from __future__ import annotations

import argparse
import copy
import csv
import functools
import hashlib
import importlib.util
import io
import json
import pathlib
import statistics
import sys
from typing import Any


if sys.version_info < (3, 10):
    raise RuntimeError("zkai_native_seq32_attention_mlp_median_timing_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
RAW_TIMING_PATH = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-median-timing-raw-2026-05.json"
STATEMENT_ONLY_GATE_PATH = EVIDENCE_DIR / "zkai-stwo-statement-only-attempt-transcript-gate-2026-05.json"
STATEMENT_ONLY_GATE_SCRIPT = ROOT / "scripts" / "zkai_stwo_statement_only_attempt_transcript_gate.py"
TIMING_RUST_SOURCE = ROOT / "src" / "bin" / "zkai_native_seq32_attention_mlp_median_timing.rs"
NATIVE_PROOF_RUST_SOURCE = ROOT / "src" / "stwo_backend" / "native_seq32_attention_mlp_single_proof.rs"
JSON_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-median-timing-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-median-timing-2026-05.tsv"

SCHEMA = "zkai-native-seq32-attention-mlp-median-timing-gate-v1"
RAW_SCHEMA = "zkai-native-seq32-attention-mlp-median-timing-cli-v1"
DECISION = "GO_SEQ32_D128_STATEMENT_ONLY_TIMING_CAPTURED_ENGINEERING_LOCAL_ONLY"
RESULT = "GO_MEDIAN_OF_5_BUILD_PROVE_VERIFY_TIMING_CAPTURED_WITH_NON_BENCHMARK_GUARDRAILS"
CLAIM_BOUNDARY = (
    "ENGINEERING_LOCAL_MEDIAN_OF_5_TIMING_FOR_CURRENT_SEQ32_D128_STATEMENT_ONLY_NATIVE_OBJECT;"
    "NO_EXTERNAL_SYSTEM_COMPARISON;NO_PUBLIC_BENCHMARK;NO_PRODUCTION_THROUGHPUT_CLAIM"
)
ISSUE = 681
STATEMENT_ONLY_SCHEMA = "zkai-stwo-statement-only-attempt-transcript-gate-v1"
STATEMENT_ONLY_DECISION = "GO_STATEMENT_ONLY_ATTEMPT_POLICY_TRANSCRIPT_REDUCES_REGENERATED_STWO_PROOF_BYTES"
STATEMENT_ONLY_RESULT = "STATEMENT_ONLY_PROBE_B_VERIFIES_AT_39516_TYPED_BYTES_SAVING_1376_VS_FULL_POLICY_MIX"
RAW_DECISION = "GO_ENGINEERING_LOCAL_MEDIAN_OF_5_TIMING_FOR_SEQ32_D128_STATEMENT_ONLY_FRONTIER"
RAW_RESULT = "GO_TIMING_CAPTURED_ENGINEERING_LOCAL_ONLY"
TIMING_POLICY = "median_of_5_in_process_std_time_instant_microsecond_capture_engineering_only"
TIMING_SCOPE = "build_input_from_source_json_plus_existing_input_prove_plus_existing_envelope_verify"
EXPECTED_SAMPLE_COUNT = 5
EXPECTED_PROFILE_ID = "statement_only_probe_b"
EXPECTED_TYPED_BYTES = 39_516
EXPECTED_JSON_PROOF_BYTES = 113_388
EXPECTED_TWO_PROOF_FRONTIER_TYPED_BYTES = 47_188
EXPECTED_POLICY_VERSION = "seq32-d128-adjacent-attempt-domain-statement-only-transcript-v1"
EXPECTED_POLICY_STAGE = "inner_statement_digest_only_transcript_metadata"
EXPECTED_SELECTED_ATTEMPT_ID = "adjacent_label_probe_b"
EXPECTED_TIMING_METRICS = (
    "build_input_from_source_json_us",
    "prove_existing_input_us",
    "verify_existing_envelope_us",
)
HOST_METADATA_KEYS = {"os", "arch", "family", "logical_cpus", "cargo_profile", "privacy_policy"}
HOST_METADATA_INCLUDED = ("os", "arch", "family", "logical_cpus", "cargo_profile")
HOST_METADATA_EXCLUDED = ("hostname", "username", "absolute_local_paths")
HOST_PRIVACY_POLICY = "hostnames_usernames_and_absolute_local_paths_are_not_recorded"
NON_CLAIMS = (
    "not a public benchmark",
    "not a NANOZK/Jolt/DeepProve/EZKL timing comparison",
    "not a proof-size comparison against external zkML systems",
    "not production proving throughput",
    "not hardware-normalized performance evidence",
    "not GitHub Actions evidence",
    "not a full transformer block benchmark",
)
VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 run --locked --release --features stwo-backend --bin zkai_native_seq32_attention_mlp_median_timing -- --evidence-dir docs/engineering/evidence --runs 5 > docs/engineering/evidence/zkai-native-seq32-attention-mlp-median-timing-raw-2026-05.json",
    "python3.10 scripts/zkai_native_seq32_attention_mlp_median_timing_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-median-timing-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-median-timing-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_median_timing_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_median_timing_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_median_timing_gate",
    "cargo +nightly-2025-07-14 test --locked --release --features stwo-backend --bin zkai_native_seq32_attention_mlp_median_timing",
    "git diff --check",
    "just gate-fast",
    "just gate",
)
PAYLOAD_KEYS = {
    "schema",
    "issue",
    "decision",
    "result",
    "claim_boundary",
    "timing_policy",
    "timing_scope",
    "source_artifacts",
    "target",
    "timing_rows",
    "timing_summary",
    "host_metadata_policy",
    "interpretation",
    "non_claims",
    "validation_commands",
    "mutation_result",
    "payload_commitment",
}
RAW_KEYS = {
    "schema",
    "issue",
    "decision",
    "result",
    "timing_policy",
    "timing_scope",
    "clock",
    "sample_count",
    "target",
    "source_artifacts",
    "timings",
    "generated_proof_json_bytes",
    "host_metadata",
    "non_claims",
    "validation_commands",
}
TIMING_ROW_KEYS = {"metric", "runs_us", "median_us", "min_us", "max_us"}
TSV_COLUMNS = (
    "metric",
    "sample_count",
    "median_us",
    "min_us",
    "max_us",
    "median_ms",
    "timing_policy",
)


class Seq32TimingGateError(ValueError):
    def __init__(self, message: str, *, layer: str = "parser_or_schema") -> None:
        super().__init__(message)
        self.layer = layer


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blake2b256_bytes(data: bytes) -> str:
    return "blake2b-256:" + hashlib.blake2b(data, digest_size=32).hexdigest()


def require_object(value: Any, label: str, *, layer: str = "parser_or_schema") -> dict[str, Any]:
    if not isinstance(value, dict):
        raise Seq32TimingGateError(f"{label} must be an object", layer=layer)
    return value


def require_list(value: Any, label: str, *, layer: str = "parser_or_schema") -> list[Any]:
    if not isinstance(value, list):
        raise Seq32TimingGateError(f"{label} must be a list", layer=layer)
    return value


def require_int(value: Any, label: str, *, layer: str = "parser_or_schema") -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise Seq32TimingGateError(f"{label} must be an integer", layer=layer)
    return value


def expect_equal(actual: Any, expected: Any, label: str, *, layer: str = "parser_or_schema") -> None:
    if actual != expected:
        raise Seq32TimingGateError(f"{label} mismatch: got {actual!r}, expected {expected!r}", layer=layer)


def expect_keys(value: dict[str, Any], expected: set[str], label: str, *, layer: str = "parser_or_schema") -> None:
    keys = set(value)
    if keys != expected:
        raise Seq32TimingGateError(
            f"{label} keys mismatch: missing={sorted(expected - keys)} extra={sorted(keys - expected)}",
            layer=layer,
        )


def load_json(path: pathlib.Path, *, layer: str = "artifact_binding") -> Any:
    resolved = path.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as err:
        raise Seq32TimingGateError(f"path escapes repository: {path}", layer=layer) from err
    try:
        return json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as err:
        raise Seq32TimingGateError(f"failed to load JSON {path}: {err}", layer=layer) from err


def _load_module(path: pathlib.Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise Seq32TimingGateError(f"failed to load {module_name} from {path}", layer="source_statement_gate")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@functools.lru_cache(maxsize=1)
def statement_only_gate_module() -> Any:
    return _load_module(STATEMENT_ONLY_GATE_SCRIPT, "zkai_statement_only_gate_for_seq32_timing")


@functools.lru_cache(maxsize=1)
def statement_only_payload() -> dict[str, Any]:
    payload = require_object(load_json(STATEMENT_ONLY_GATE_PATH, layer="source_statement_gate"), "statement-only gate", layer="source_statement_gate")
    try:
        statement_only_gate_module().validate_payload(payload)
    except Exception as err:  # noqa: BLE001 - normalize imported validator failures.
        raise Seq32TimingGateError(f"statement-only gate validation failed: {err}", layer="source_statement_gate") from err
    expect_equal(payload.get("schema"), STATEMENT_ONLY_SCHEMA, "statement-only schema", layer="source_statement_gate")
    expect_equal(payload.get("decision"), STATEMENT_ONLY_DECISION, "statement-only decision", layer="source_statement_gate")
    expect_equal(payload.get("result"), STATEMENT_ONLY_RESULT, "statement-only result", layer="source_statement_gate")
    return copy.deepcopy(payload)


def statement_only_best_row() -> dict[str, Any]:
    rows = require_list(statement_only_payload().get("profile_rows"), "statement-only profile rows", layer="source_statement_gate")
    for row in rows:
        row = require_object(row, "statement-only profile row", layer="source_statement_gate")
        if row.get("profile_id") == EXPECTED_PROFILE_ID:
            expect_equal(row.get("typed_bytes"), EXPECTED_TYPED_BYTES, "statement-only typed bytes", layer="source_statement_gate")
            expect_equal(row.get("proof_json_bytes"), EXPECTED_JSON_PROOF_BYTES, "statement-only JSON bytes", layer="source_statement_gate")
            return copy.deepcopy(row)
    raise Seq32TimingGateError("statement-only best row missing", layer="source_statement_gate")


def validate_raw_timing(payload: dict[str, Any]) -> None:
    expect_keys(payload, RAW_KEYS, "raw timing payload")
    expect_equal(payload["schema"], RAW_SCHEMA, "raw schema")
    expect_equal(payload["issue"], ISSUE, "raw issue")
    expect_equal(payload["decision"], RAW_DECISION, "raw decision")
    expect_equal(payload["result"], RAW_RESULT, "raw result")
    expect_equal(payload["timing_policy"], TIMING_POLICY, "raw timing policy", layer="timing_metrics")
    expect_equal(payload["timing_scope"], TIMING_SCOPE, "raw timing scope", layer="timing_metrics")
    expect_equal(payload["sample_count"], EXPECTED_SAMPLE_COUNT, "sample count", layer="timing_metrics")

    target = require_object(payload["target"], "raw target", layer="artifact_binding")
    expect_equal(target.get("profile_id"), EXPECTED_PROFILE_ID, "target profile", layer="artifact_binding")
    expect_equal(target.get("attempt_policy_version"), EXPECTED_POLICY_VERSION, "target policy version", layer="artifact_binding")
    expect_equal(target.get("attempt_policy_stage"), EXPECTED_POLICY_STAGE, "target policy stage", layer="artifact_binding")
    expect_equal(target.get("selected_attempt_id"), EXPECTED_SELECTED_ATTEMPT_ID, "target attempt id", layer="artifact_binding")
    expect_equal(target.get("typed_bytes_from_checked_accounting"), EXPECTED_TYPED_BYTES, "target typed bytes", layer="artifact_binding")
    expect_equal(target.get("json_proof_bytes"), EXPECTED_JSON_PROOF_BYTES, "target JSON proof bytes", layer="artifact_binding")
    expect_equal(target.get("current_two_proof_frontier_typed_bytes"), EXPECTED_TWO_PROOF_FRONTIER_TYPED_BYTES, "two-proof frontier", layer="artifact_binding")
    canonical_row = statement_only_best_row()
    expect_equal(target.get("statement_commitment"), canonical_row.get("statement_commitment"), "statement commitment", layer="artifact_binding")
    expect_equal(target.get("public_instance_commitment"), canonical_row.get("public_instance_commitment"), "public instance commitment", layer="artifact_binding")
    expect_equal(target.get("proof_native_parameter_commitment"), canonical_row.get("proof_native_parameter_commitment"), "proof native parameter commitment", layer="artifact_binding")

    rows = require_list(payload["timings"], "timing rows", layer="timing_metrics")
    metrics = []
    for row in rows:
        row = require_object(row, "timing row", layer="timing_metrics")
        expect_keys(row, TIMING_ROW_KEYS, "timing row", layer="timing_metrics")
        metric = row["metric"]
        metrics.append(metric)
        runs = [require_int(value, f"{metric} run", layer="timing_metrics") for value in require_list(row["runs_us"], f"{metric} runs", layer="timing_metrics")]
        if len(runs) != EXPECTED_SAMPLE_COUNT:
            raise Seq32TimingGateError(f"{metric} must have {EXPECTED_SAMPLE_COUNT} runs", layer="timing_metrics")
        if any(value <= 0 for value in runs):
            raise Seq32TimingGateError(f"{metric} timings must be positive", layer="timing_metrics")
        expect_equal(row["median_us"], int(statistics.median(sorted(runs))), f"{metric} median", layer="timing_metrics")
        expect_equal(row["min_us"], min(runs), f"{metric} min", layer="timing_metrics")
        expect_equal(row["max_us"], max(runs), f"{metric} max", layer="timing_metrics")
    expect_equal(tuple(metrics), EXPECTED_TIMING_METRICS, "timing metric order", layer="timing_metrics")

    generated = [require_int(value, "generated proof JSON bytes", layer="timing_metrics") for value in require_list(payload["generated_proof_json_bytes"], "generated proof JSON bytes", layer="timing_metrics")]
    if len(generated) != EXPECTED_SAMPLE_COUNT:
        raise Seq32TimingGateError("generated proof size inventory length drift", layer="timing_metrics")
    if set(generated) != {EXPECTED_JSON_PROOF_BYTES}:
        raise Seq32TimingGateError("generated proof JSON byte size drift", layer="timing_metrics")

    host = require_object(payload["host_metadata"], "host metadata", layer="timing_metrics")
    expect_keys(host, HOST_METADATA_KEYS, "host metadata", layer="timing_metrics")
    expect_equal(host["privacy_policy"], HOST_PRIVACY_POLICY, "host metadata privacy policy", layer="timing_metrics")
    if host["cargo_profile"] != "release":
        raise Seq32TimingGateError("timing artifact must be generated by release cargo profile", layer="timing_metrics")

    for non_claim in NON_CLAIMS[:2]:
        if non_claim not in payload["non_claims"]:
            raise Seq32TimingGateError(f"raw timing non-claim missing: {non_claim}", layer="claim_boundary")


def raw_timing_payload() -> dict[str, Any]:
    payload = require_object(load_json(RAW_TIMING_PATH), "raw timing payload")
    validate_raw_timing(payload)
    return payload


def source_artifact(id_: str, path: pathlib.Path, kind: str) -> dict[str, Any]:
    return {
        "id": id_,
        "kind": kind,
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def safe_source_path(path_value: str) -> pathlib.Path:
    path = pathlib.PurePosixPath(path_value)
    if path.is_absolute() or ".." in path.parts:
        raise Seq32TimingGateError(f"source artifact path must stay relative inside repo: {path_value}", layer="artifact_binding")
    resolved = (ROOT / pathlib.Path(path_value)).resolve(strict=False)
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as err:
        raise Seq32TimingGateError(f"source artifact path escapes repository: {path_value}", layer="artifact_binding") from err
    return resolved


def timing_row_map(raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["metric"]: row for row in raw["timings"]}


def build_payload() -> dict[str, Any]:
    raw = raw_timing_payload()
    best_row = statement_only_best_row()
    rows = timing_row_map(raw)
    prove_median = rows["prove_existing_input_us"]["median_us"]
    verify_median = rows["verify_existing_envelope_us"]["median_us"]
    raw_host_metadata = {key: raw["host_metadata"][key] for key in sorted(HOST_METADATA_KEYS)}
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "issue": ISSUE,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "timing_policy": TIMING_POLICY,
        "timing_scope": TIMING_SCOPE,
        "source_artifacts": [
            source_artifact("raw_timing_json", RAW_TIMING_PATH, "raw_timing_json"),
            source_artifact("statement_only_gate_json", STATEMENT_ONLY_GATE_PATH, "source_gate_json"),
            source_artifact("timing_rust_source", TIMING_RUST_SOURCE, "rust_source"),
            source_artifact("native_proof_rust_source", NATIVE_PROOF_RUST_SOURCE, "rust_source"),
        ],
        "target": {
            "profile_id": EXPECTED_PROFILE_ID,
            "typed_bytes": EXPECTED_TYPED_BYTES,
            "json_proof_bytes": EXPECTED_JSON_PROOF_BYTES,
            "matched_two_proof_frontier_typed_bytes": EXPECTED_TWO_PROOF_FRONTIER_TYPED_BYTES,
            "typed_saving_vs_matched_two_proof_frontier": best_row["typed_saving_vs_matched_two_proof_frontier"],
            "statement_commitment": raw["target"]["statement_commitment"],
            "public_instance_commitment": raw["target"]["public_instance_commitment"],
            "proof_native_parameter_commitment": raw["target"]["proof_native_parameter_commitment"],
        },
        "timing_rows": raw["timings"],
        "timing_summary": {
            "build_input_median_us": rows["build_input_from_source_json_us"]["median_us"],
            "prove_median_us": prove_median,
            "verify_median_us": verify_median,
            "prove_to_verify_median_ratio": round(prove_median / verify_median, 6),
            "sample_count": EXPECTED_SAMPLE_COUNT,
            "generated_proof_json_bytes_all": raw["generated_proof_json_bytes"],
        },
        "host_metadata_policy": {
            "included": list(HOST_METADATA_INCLUDED),
            "excluded": list(HOST_METADATA_EXCLUDED),
            "raw_host_metadata": raw_host_metadata,
        },
        "interpretation": [
            "The current seq32+d128 statement-only native proof object now has local median-of-5 build/prove/verify timing evidence.",
            "This timing evidence is useful for engineering triage only; it is not a public benchmark or an external-system comparison.",
            "The proof-size frontier remains the paper-relevant result; timing is a guardrail for practicality and future optimization.",
        ],
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
        "mutation_result": {},
    }
    payload["mutation_result"] = mutation_result(payload)
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload)
    return payload


def payload_commitment(payload: dict[str, Any]) -> str:
    without = copy.deepcopy(payload)
    without.pop("payload_commitment", None)
    return blake2b256_bytes(canonical_json_bytes(without))


def mutation_inventory(payload: dict[str, Any]) -> list[tuple[str, str, Any]]:
    return [
        ("decision_relabeling", "claim_boundary", lambda p: p.__setitem__("decision", "GO_PUBLIC_TIMING_BENCHMARK")),
        ("claim_boundary_public_benchmark", "claim_boundary", lambda p: p.__setitem__("claim_boundary", "PUBLIC_BENCHMARK_AGAINST_NANOZK")),
        ("timing_policy_relabeling", "timing_metrics", lambda p: p.__setitem__("timing_policy", "single_run_wall_clock")),
        ("timing_scope_relabeling", "timing_metrics", lambda p: p.__setitem__("timing_scope", "github_actions_public_benchmark")),
        ("target_typed_bytes_drift", "artifact_binding", lambda p: p["target"].__setitem__("typed_bytes", EXPECTED_TYPED_BYTES - 1)),
        ("target_json_bytes_drift", "artifact_binding", lambda p: p["target"].__setitem__("json_proof_bytes", EXPECTED_JSON_PROOF_BYTES - 1)),
        ("source_digest_relabeling", "artifact_binding", lambda p: p["source_artifacts"][0].__setitem__("sha256", "0" * 64)),
        ("sample_count_relabeling", "timing_metrics", lambda p: p["timing_summary"].__setitem__("sample_count", 1)),
        ("prove_metric_zeroed", "timing_metrics", lambda p: p["timing_rows"][1].__setitem__("median_us", 0)),
        ("host_metadata_promoted", "timing_metrics", lambda p: p["host_metadata_policy"].__setitem__("excluded", [])),
        ("host_metadata_extra_key", "timing_metrics", lambda p: p["host_metadata_policy"]["raw_host_metadata"].__setitem__("hostname", "example.local")),
        ("non_claim_removed", "claim_boundary", lambda p: p["non_claims"].remove("not a public benchmark")),
        ("validation_command_removed", "parser_or_schema", lambda p: p["validation_commands"].pop()),
        ("payload_commitment_drift", "parser_or_schema", lambda p: p.__setitem__("payload_commitment", "blake2b-256:" + "0" * 64)),
    ]


def mutation_result(payload: dict[str, Any]) -> dict[str, Any]:
    rejected: list[str] = []
    details: list[dict[str, str]] = []
    for name, layer, mutate in mutation_inventory(payload):
        candidate = copy.deepcopy(payload)
        candidate["mutation_result"] = {"status": "not_checked_during_mutation"}
        candidate["payload_commitment"] = payload_commitment(candidate)
        mutate(candidate)
        try:
            validate_payload(candidate, check_mutations=False)
        except Seq32TimingGateError as err:
            rejected.append(name)
            details.append({"name": name, "layer": err.layer or layer, "error": str(err)})
        else:
            raise Seq32TimingGateError(f"mutation was accepted: {name}", layer=layer)
    return {
        "all_rejected": True,
        "rejected_count": len(rejected),
        "rejected_mutations": rejected,
        "details": details,
    }


def validate_payload(payload: dict[str, Any], *, check_mutations: bool = True) -> None:
    expect_keys(payload, PAYLOAD_KEYS, "payload")
    expect_equal(payload["schema"], SCHEMA, "schema")
    expect_equal(payload["issue"], ISSUE, "issue")
    expect_equal(payload["decision"], DECISION, "decision", layer="claim_boundary")
    expect_equal(payload["result"], RESULT, "result", layer="claim_boundary")
    expect_equal(payload["claim_boundary"], CLAIM_BOUNDARY, "claim boundary", layer="claim_boundary")
    expect_equal(payload["timing_policy"], TIMING_POLICY, "timing policy", layer="timing_metrics")
    expect_equal(payload["timing_scope"], TIMING_SCOPE, "timing scope", layer="timing_metrics")
    expect_equal(payload["target"]["profile_id"], EXPECTED_PROFILE_ID, "target profile", layer="artifact_binding")
    expect_equal(payload["target"]["typed_bytes"], EXPECTED_TYPED_BYTES, "target typed bytes", layer="artifact_binding")
    expect_equal(payload["target"]["json_proof_bytes"], EXPECTED_JSON_PROOF_BYTES, "target JSON proof bytes", layer="artifact_binding")
    expect_equal(payload["timing_summary"]["sample_count"], EXPECTED_SAMPLE_COUNT, "sample count", layer="timing_metrics")
    if payload["timing_summary"]["prove_median_us"] <= 0 or payload["timing_summary"]["verify_median_us"] <= 0:
        raise Seq32TimingGateError("timing medians must be positive", layer="timing_metrics")
    if payload["timing_summary"]["generated_proof_json_bytes_all"] != [EXPECTED_JSON_PROOF_BYTES] * EXPECTED_SAMPLE_COUNT:
        raise Seq32TimingGateError("generated proof JSON bytes drift", layer="timing_metrics")
    host_policy = require_object(payload["host_metadata_policy"], "host metadata policy", layer="timing_metrics")
    if host_policy["included"] != list(HOST_METADATA_INCLUDED):
        raise Seq32TimingGateError("host metadata included-key boundary drift", layer="timing_metrics")
    if host_policy["excluded"] != list(HOST_METADATA_EXCLUDED):
        raise Seq32TimingGateError("host metadata privacy boundary drift", layer="timing_metrics")
    raw_host = require_object(host_policy["raw_host_metadata"], "raw host metadata", layer="timing_metrics")
    expect_keys(raw_host, HOST_METADATA_KEYS, "raw host metadata", layer="timing_metrics")
    expect_equal(raw_host["privacy_policy"], HOST_PRIVACY_POLICY, "raw host metadata privacy policy", layer="timing_metrics")
    for source in payload["source_artifacts"]:
        source = require_object(source, "source artifact", layer="artifact_binding")
        path = safe_source_path(source["path"])
        expect_equal(source["sha256"], sha256_file(path), f"source digest {source['id']}", layer="artifact_binding")
    for non_claim in NON_CLAIMS:
        if non_claim not in payload["non_claims"]:
            raise Seq32TimingGateError(f"missing non-claim: {non_claim}", layer="claim_boundary")
    for command in VALIDATION_COMMANDS:
        if command not in payload["validation_commands"]:
            raise Seq32TimingGateError(f"missing validation command: {command}", layer="parser_or_schema")
    if check_mutations:
        result = require_object(payload["mutation_result"], "mutation result")
        expect_equal(result.get("all_rejected"), True, "mutation rejection")
        expect_equal(result.get("rejected_count"), len(mutation_inventory(payload)), "mutation count")
    expect_equal(payload["payload_commitment"], payload_commitment(payload), "payload commitment", layer="parser_or_schema")


def write_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_tsv(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in payload["timing_rows"]:
            writer.writerow(
                {
                    "metric": row["metric"],
                    "sample_count": payload["timing_summary"]["sample_count"],
                    "median_us": row["median_us"],
                    "min_us": row["min_us"],
                    "max_us": row["max_us"],
                    "median_ms": f"{row['median_us'] / 1000:.3f}",
                    "timing_policy": payload["timing_policy"],
                }
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    args = parser.parse_args(argv)

    try:
        payload = build_payload()
        if args.write_json:
            write_json(args.write_json, payload)
        if args.write_tsv:
            write_tsv(args.write_tsv, payload)
    except Seq32TimingGateError as err:
        print(f"error[{err.layer}]: {err}", file=sys.stderr)
        return 1

    if not args.write_json and not args.write_tsv:
        buffer = io.StringIO()
        json.dump(payload, buffer, indent=2, sort_keys=True, ensure_ascii=False)
        print(buffer.getvalue())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
