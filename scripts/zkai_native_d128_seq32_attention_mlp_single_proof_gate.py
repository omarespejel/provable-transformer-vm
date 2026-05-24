#!/usr/bin/env python3.10
"""Gate the scoped d128 seq32 attention plus d128 MLP single proof object."""

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
from typing import Any, Callable


if sys.version_info < (3, 10):
    raise RuntimeError("zkai_native_d128_seq32_attention_mlp_single_proof_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"

INPUT_PATH = EVIDENCE_DIR / "zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.input.json"
ENVELOPE_PATH = EVIDENCE_DIR / "zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.envelope.json"
SINGLE_ACCOUNTING_PATH = (
    EVIDENCE_DIR / "zkai-native-d128-seq32-attention-mlp-single-proof-binary-accounting-2026-05.json"
)
SPLIT_ACCOUNTING_PATH = (
    EVIDENCE_DIR / "zkai-native-d128-seq32-attention-mlp-split-frontier-binary-accounting-2026-05.json"
)
PREFLIGHT_PATH = EVIDENCE_DIR / "zkai-scoped-d128-seq32-block-boundary-preflight-2026-05.json"

JSON_OUT = EVIDENCE_DIR / "zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.tsv"
MD_OUT = ROOT / "docs" / "engineering" / "zkai-native-d128-seq32-attention-mlp-single-proof-2026-05-24.md"

SCHEMA = "zkai-native-d128-seq32-attention-mlp-single-proof-gate-v1"
DECISION = "GO_COLOCATED_D128_SEQ32_ATTENTION_MLP_SINGLE_PROOF_BEATS_SCOPED_SPLIT_FRONTIER"
RESULT = "SCOPED_D128_SEQ32_SINGLE_PROOF_SAVES_15881_JSON_AND_4608_TYPED_BYTES"
PAYLOAD_DOMAIN = "ptvm:zkai:native-d128-seq32-attention-mlp-single-proof-gate:v1"
ISSUE = 715

SINGLE_PROOF_JSON_BYTES = 504_518
SINGLE_TYPED_BYTES = 204_564
SINGLE_ENVELOPE_JSON_BYTES = 25_409_456
SINGLE_INPUT_JSON_BYTES = 18_752_185
MAX_SINGLE_INPUT_JSON_BYTES = 32 * 1024 * 1024
MAX_SINGLE_ENVELOPE_JSON_BYTES = 32 * 1024 * 1024
MAX_ACCOUNTING_JSON_BYTES = 1 * 1024 * 1024
MAX_PREFLIGHT_JSON_BYTES = 1 * 1024 * 1024
SPLIT_PROOF_JSON_BYTES = 520_399
SPLIT_TYPED_BYTES = 209_172
PROOF_JSON_SAVING_BYTES = 15_881
TYPED_SAVING_BYTES = 4_608
PROOF_JSON_RATIO = "0.969483"
TYPED_RATIO = "0.977970"
STATEMENT_COMMITMENT = "blake2b-256:21eeba5327c21c558433ef7f979702bb4c56c9700e7a0afd44cddb4527069680"
PUBLIC_INSTANCE_COMMITMENT = "blake2b-256:b1d870de6352c1b89e06a1a6292aa98278ce5386b838d91ee7c5fdeccb409f08"
PROOF_SHA256 = "c4949199aa72e61992a6cccb52a77b9617a1a055b80d15cb11f8dd058008739e"
ENVELOPE_SHA256 = "d0048ea0afbb80e72814b4aee9be3cd2f5ecf950c261daeccf738807e7a5b3b6"

EXPECTED_INPUT_METADATA = {
    "schema": "zkai-native-d128-seq32-attention-mlp-single-proof-object-input-v1",
    "decision": "GO_INPUT_FOR_NATIVE_D128_SEQ32_ATTENTION_MLP_SINGLE_PROOF_OBJECT_PROBE",
    "target_id": "attention-kv-d128-two-head-seq32-fused-softmax-table-plus-seq32-derived-d128-rmsnorm-mlp-v1",
    "verifier_domain": "ptvm:zkai:native-d128-seq32-attention-mlp-single-proof-object:v1",
    "attention_lookup_claims": 1_184,
    "attention_table_rows": 9,
    "adapter_status": "NATIVE_AIR_PROVEN_COLOCATED_D128_ADAPTER_QUOTIENT_CHECK",
    "adapter_trace_cells": 1_536,
    "pcs_lifting_log_size": 19,
    "current_two_proof_frontier_typed_bytes": SPLIT_PROOF_JSON_BYTES,
    "current_attention_fused_typed_bytes": 445_888,
    "current_derived_mlp_fused_typed_bytes": 24_272,
}

EXPECTED_ENVELOPE_METADATA = {
    "proof_backend": "stwo",
    "proof_backend_version": "stwo-native-d128-seq32-attention-mlp-single-proof-object-native-adapter-v1",
    "proof_schema_version": "stwo-native-d128-seq32-attention-mlp-single-proof-object-native-adapter-payload-v1",
    "statement_version": "zkai-native-d128-seq32-attention-mlp-single-proof-object-native-adapter-statement-v1",
    "semantic_scope": (
        "d128_two_head_seq32_attention_softmax_table_public_adapter_and_seq32_derived_d128_"
        "rmsnorm_mlp_surfaces_in_one_native_stwo_proof_object"
    ),
    "decision": "GO_SINGLE_NATIVE_STWO_PROOF_OBJECT_WITH_COLOCATED_D128_SEQ32_ATTENTION_AND_D128_MLP_ADAPTER_AIR",
    "target_id": EXPECTED_INPUT_METADATA["target_id"],
    "verifier_domain": EXPECTED_INPUT_METADATA["verifier_domain"],
}

NON_CLAIMS = (
    "not a full transformer block proof",
    "not a model-faithful d128 attention-to-MLP adapter",
    "not enforcing d128 MLP input derivation from attention outputs",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not exact real-valued Softmax",
    "not full autoregressive inference",
    "not timing evidence",
    "not production-ready zkML",
)

VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_d128_seq32_attention_mlp_single_proof -- build-input docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_d128_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.input.json docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_d128_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.envelope.json > docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-binary-accounting-2026-05.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.envelope.json > docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-split-frontier-binary-accounting-2026-05.json",
    "python3.10 scripts/zkai_native_d128_seq32_attention_mlp_single_proof_gate.py --write-json docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.tsv --write-md docs/engineering/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05-24.md",
    "python3.10 -m py_compile scripts/zkai_native_d128_seq32_attention_mlp_single_proof_gate.py scripts/tests/test_zkai_native_d128_seq32_attention_mlp_single_proof_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_native_d128_seq32_attention_mlp_single_proof_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend native_d128_seq32_attention_mlp_single_proof --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
)


class NativeD128Seq32SingleProofGateError(ValueError):
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
        raise NativeD128Seq32SingleProofGateError(f"invalid JSON value: {err}") from err


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return "blake2b-256:" + digest.hexdigest()


def read_repo_file(path: pathlib.Path, label: str, max_bytes: int | None = None) -> bytes:
    root = ROOT.resolve()
    candidate = pathlib.Path(os.path.abspath(path if path.is_absolute() else ROOT / path))
    try:
        relative = candidate.relative_to(root)
    except ValueError as err:
        raise NativeD128Seq32SingleProofGateError(f"{label} escapes repo root: {path}") from err
    current = root
    try:
        for part in relative.parts:
            current = current / part
            if stat.S_ISLNK(current.lstat().st_mode):
                raise NativeD128Seq32SingleProofGateError(f"{label} must not traverse symlinks")
        fd = os.open(candidate, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            file_stat = os.fstat(fd)
            if not stat.S_ISREG(file_stat.st_mode):
                raise NativeD128Seq32SingleProofGateError(f"{label} must be a regular file")
            if max_bytes is not None and file_stat.st_size > max_bytes:
                raise NativeD128Seq32SingleProofGateError(
                    f"{label} exceeds max size: got {file_stat.st_size} bytes, limit {max_bytes} bytes"
                )
            with os.fdopen(fd, "rb") as handle:
                fd = None
                if max_bytes is None:
                    return handle.read()
                raw = handle.read(max_bytes + 1)
                if len(raw) > max_bytes:
                    raise NativeD128Seq32SingleProofGateError(
                        f"{label} exceeds max size: got more than {max_bytes} bytes, limit {max_bytes} bytes"
                    )
                return raw
        finally:
            if fd is not None:
                os.close(fd)
    except OSError as err:
        raise NativeD128Seq32SingleProofGateError(f"failed to read {label}: {err}") from err


def read_json(path: pathlib.Path, label: str, max_bytes: int | None = None) -> tuple[dict[str, Any], bytes]:
    raw = read_repo_file(path, label, max_bytes)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as err:
        raise NativeD128Seq32SingleProofGateError(f"{label} is not valid JSON: {err}") from err
    if not isinstance(value, dict):
        raise NativeD128Seq32SingleProofGateError(f"{label} must be a JSON object")
    return value, raw


def source_artifact(
    artifact_id: str,
    path: pathlib.Path,
    label: str,
    max_bytes: int | None = None,
) -> dict[str, Any]:
    payload, raw = read_json(path, label, max_bytes)
    return source_artifact_from_payload(artifact_id, path, payload, raw)


def source_artifact_from_payload(
    artifact_id: str,
    path: pathlib.Path,
    payload: dict[str, Any],
    raw: bytes,
) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "path": path.relative_to(ROOT).as_posix(),
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "payload_sha256": hashlib.sha256(canonical_json_bytes(payload)).hexdigest(),
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise NativeD128Seq32SingleProofGateError(message)


SourceArtifactSpec = tuple[str, pathlib.Path, str, int | None]


def source_artifact_specs() -> tuple[SourceArtifactSpec, ...]:
    return (
        ("scoped_input", INPUT_PATH, "scoped input", MAX_SINGLE_INPUT_JSON_BYTES),
        ("scoped_envelope", ENVELOPE_PATH, "scoped envelope", MAX_SINGLE_ENVELOPE_JSON_BYTES),
        ("single_accounting", SINGLE_ACCOUNTING_PATH, "single accounting", MAX_ACCOUNTING_JSON_BYTES),
        ("split_accounting", SPLIT_ACCOUNTING_PATH, "split accounting", MAX_ACCOUNTING_JSON_BYTES),
        ("preflight_gate", PREFLIGHT_PATH, "preflight gate", MAX_PREFLIGHT_JSON_BYTES),
    )


def expected_source_artifacts() -> list[dict[str, Any]]:
    return [
        source_artifact(artifact_id, path, label, max_bytes)
        for artifact_id, path, label, max_bytes in source_artifact_specs()
    ]


def build_payload() -> dict[str, Any]:
    input_payload, input_raw = read_json(INPUT_PATH, "scoped input", MAX_SINGLE_INPUT_JSON_BYTES)
    envelope, envelope_raw = read_json(ENVELOPE_PATH, "scoped envelope", MAX_SINGLE_ENVELOPE_JSON_BYTES)
    single_accounting, single_accounting_raw = read_json(
        SINGLE_ACCOUNTING_PATH,
        "single accounting",
        MAX_ACCOUNTING_JSON_BYTES,
    )
    split_accounting, split_accounting_raw = read_json(
        SPLIT_ACCOUNTING_PATH,
        "split accounting",
        MAX_ACCOUNTING_JSON_BYTES,
    )
    preflight, preflight_raw = read_json(PREFLIGHT_PATH, "preflight gate", MAX_PREFLIGHT_JSON_BYTES)
    expected_artifacts = [
        source_artifact_from_payload("scoped_input", INPUT_PATH, input_payload, input_raw),
        source_artifact_from_payload("scoped_envelope", ENVELOPE_PATH, envelope, envelope_raw),
        source_artifact_from_payload(
            "single_accounting",
            SINGLE_ACCOUNTING_PATH,
            single_accounting,
            single_accounting_raw,
        ),
        source_artifact_from_payload(
            "split_accounting",
            SPLIT_ACCOUNTING_PATH,
            split_accounting,
            split_accounting_raw,
        ),
        source_artifact_from_payload("preflight_gate", PREFLIGHT_PATH, preflight, preflight_raw),
    ]

    proof = envelope.get("proof")
    require(isinstance(proof, list), "envelope proof must be a list")
    proof_bytes = bytes(int(value) for value in proof)
    proof_sha = hashlib.sha256(proof_bytes).hexdigest()
    envelope_sha = hashlib.sha256(envelope_raw).hexdigest()

    single_rows = single_accounting.get("rows")
    split_rows = split_accounting.get("rows")
    require(isinstance(single_rows, list) and len(single_rows) == 1, "single accounting row count drift")
    require(isinstance(split_rows, list) and len(split_rows) == 2, "split accounting row count drift")
    single_row = single_rows[0]
    single_typed = single_row["local_binary_accounting"]["typed_size_estimate_bytes"]
    split_json = sum(row["proof_json_size_bytes"] for row in split_rows)
    split_typed = sum(row["local_binary_accounting"]["typed_size_estimate_bytes"] for row in split_rows)

    for field, expected in EXPECTED_INPUT_METADATA.items():
        require(input_payload.get(field) == expected, f"input metadata drift: {field}")
    for field, expected in EXPECTED_ENVELOPE_METADATA.items():
        require(envelope.get(field) == expected, f"envelope metadata drift: {field}")
    require(input_payload.get("statement_commitment") == STATEMENT_COMMITMENT, "input statement drift")
    require(input_payload.get("public_instance_commitment") == PUBLIC_INSTANCE_COMMITMENT, "input public drift")
    require(envelope.get("input", {}).get("statement_commitment") == STATEMENT_COMMITMENT, "envelope input statement drift")
    require(len(proof_bytes) == SINGLE_PROOF_JSON_BYTES, "single proof JSON byte drift")
    require(len(input_raw) == SINGLE_INPUT_JSON_BYTES, "single input JSON byte drift")
    require(len(envelope_raw) == SINGLE_ENVELOPE_JSON_BYTES, "single envelope JSON byte drift")
    require(proof_sha == PROOF_SHA256, "proof sha drift")
    require(envelope_sha == ENVELOPE_SHA256, "envelope sha drift")
    require(single_typed == SINGLE_TYPED_BYTES, "single typed byte drift")
    require(split_json == SPLIT_PROOF_JSON_BYTES, "split proof JSON byte drift")
    require(split_typed == SPLIT_TYPED_BYTES, "split typed byte drift")
    require(preflight.get("decision") == "GO_SCOPED_D128_SEQ32_BLOCK_BOUNDARY_PREFLIGHT", "preflight decision drift")

    payload = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "summary": {
            "single_proof_json_bytes": SINGLE_PROOF_JSON_BYTES,
            "split_proof_json_bytes": SPLIT_PROOF_JSON_BYTES,
            "proof_json_saving_bytes": PROOF_JSON_SAVING_BYTES,
            "proof_json_ratio": PROOF_JSON_RATIO,
            "single_typed_bytes": SINGLE_TYPED_BYTES,
            "split_typed_bytes": SPLIT_TYPED_BYTES,
            "typed_saving_bytes": TYPED_SAVING_BYTES,
            "typed_ratio": TYPED_RATIO,
            "single_input_json_bytes": SINGLE_INPUT_JSON_BYTES,
            "single_envelope_json_bytes": SINGLE_ENVELOPE_JSON_BYTES,
            "statement_commitment": STATEMENT_COMMITMENT,
            "public_instance_commitment": PUBLIC_INSTANCE_COMMITMENT,
            "proof_sha256": PROOF_SHA256,
            "envelope_sha256": ENVELOPE_SHA256,
            "d128_attention_fused_proof_json_bytes": 445_888,
            "seq32_derived_d128_mlp_fused_proof_json_bytes": 74_511,
            "d128_attention_fused_typed_bytes": 184_900,
            "seq32_derived_d128_mlp_fused_typed_bytes": 24_272,
            "proof_size_comparable_external_rows": 0,
            "primary_next_gate": "regenerate_model-faithful_d128_mlp_surface_or_d128_seq64_stress",
        },
        "interpretation": {
            "human_read": (
                "One native Stwo proof now co-locates the real d128 two-head seq32 fused attention source, "
                "a verifier-recomputed co-location adapter, and the seq32-derived d128 RMSNorm/MLP surface."
            ),
            "interesting_signal": (
                "The scoped proof is smaller than the matched local split frontier in both proof JSON bytes "
                "and local typed accounting, so the d128 boundary still amortizes some proof plumbing."
            ),
            "guardrail": (
                "The adapter proves quotient and remainder consistency for the co-located rows, but it does "
                "not enforce derivation of the d128 MLP input from attention outputs."
            ),
        },
        "resource_limit_analysis": {
            "single_input_json_bytes": SINGLE_INPUT_JSON_BYTES,
            "single_envelope_json_bytes": SINGLE_ENVELOPE_JSON_BYTES,
            "max_single_input_json_bytes": MAX_SINGLE_INPUT_JSON_BYTES,
            "max_single_envelope_json_bytes": MAX_SINGLE_ENVELOPE_JSON_BYTES,
            "single_input_headroom_bytes": MAX_SINGLE_INPUT_JSON_BYTES - SINGLE_INPUT_JSON_BYTES,
            "single_envelope_headroom_bytes": MAX_SINGLE_ENVELOPE_JSON_BYTES - SINGLE_ENVELOPE_JSON_BYTES,
            "parsing_model": (
                "Python gate bounded-read plus whole-buffer json.loads over repo-local evidence artifacts; "
                "Rust CLIs use whole-buffer serde_json under matching repo-local byte caps"
            ),
            "threat_model": "local research CLI evidence, not untrusted service ingestion",
        },
        "source_artifacts": expected_artifacts,
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload, expected_artifacts=expected_artifacts)
    return payload


def validate_payload(
    payload: dict[str, Any],
    *,
    expected_artifacts: list[dict[str, Any]] | None = None,
) -> None:
    require(payload.get("schema") == SCHEMA, "schema drift")
    require(payload.get("decision") == DECISION, "decision drift")
    require(payload.get("result") == RESULT, "result drift")
    require(payload.get("issue") == ISSUE, "issue drift")
    summary = payload.get("summary")
    require(isinstance(summary, dict), "summary must be object")
    expected_summary = {
        "single_proof_json_bytes": SINGLE_PROOF_JSON_BYTES,
        "split_proof_json_bytes": SPLIT_PROOF_JSON_BYTES,
        "proof_json_saving_bytes": PROOF_JSON_SAVING_BYTES,
        "proof_json_ratio": PROOF_JSON_RATIO,
        "single_typed_bytes": SINGLE_TYPED_BYTES,
        "split_typed_bytes": SPLIT_TYPED_BYTES,
        "typed_saving_bytes": TYPED_SAVING_BYTES,
        "typed_ratio": TYPED_RATIO,
        "proof_size_comparable_external_rows": 0,
    }
    for field, expected in expected_summary.items():
        require(summary.get(field) == expected, f"summary drift: {field}")
    require(tuple(payload.get("non_claims", ())) == NON_CLAIMS, "non-claims drift")
    require(tuple(payload.get("validation_commands", ())) == VALIDATION_COMMANDS, "validation commands drift")
    artifacts = payload.get("source_artifacts")
    require(isinstance(artifacts, list), "source artifacts must be list")
    if expected_artifacts is None:
        expected_artifacts = expected_source_artifacts()
    require(len(artifacts) == len(expected_artifacts), "source artifact count drift")
    for got, expected in zip(artifacts, expected_artifacts):
        require(isinstance(got, dict), "source artifact entry must be object")
        artifact_id = expected["id"]
        require(got.get("id") == artifact_id, f"source artifact id drift: {artifact_id}")
        require(got.get("path") == expected["path"], f"source artifact path drift: {artifact_id}")
        require(got.get("size_bytes") == expected["size_bytes"], f"source artifact size drift: {artifact_id}")
        require(got.get("sha256") == expected["sha256"], f"source artifact sha256 drift: {artifact_id}")
        require(
            got.get("payload_sha256") == expected["payload_sha256"],
            f"source artifact payload sha256 drift: {artifact_id}",
        )
    resource = payload.get("resource_limit_analysis")
    require(isinstance(resource, dict), "resource limit analysis must be object")
    require(resource.get("max_single_input_json_bytes") == MAX_SINGLE_INPUT_JSON_BYTES, "input cap drift")
    require(
        resource.get("max_single_envelope_json_bytes") == MAX_SINGLE_ENVELOPE_JSON_BYTES,
        "envelope cap drift",
    )
    require(
        resource.get("single_input_headroom_bytes") == MAX_SINGLE_INPUT_JSON_BYTES - SINGLE_INPUT_JSON_BYTES,
        "input headroom drift",
    )
    require(
        resource.get("single_envelope_headroom_bytes")
        == MAX_SINGLE_ENVELOPE_JSON_BYTES - SINGLE_ENVELOPE_JSON_BYTES,
        "envelope headroom drift",
    )
    require(payload.get("payload_commitment") == payload_commitment(payload), "payload commitment drift")


Mutation = tuple[str, Callable[[dict[str, Any]], None]]


def mutation_cases() -> tuple[Mutation, ...]:
    return (
        ("proof_json_metric_drift", lambda p: p["summary"].__setitem__("single_proof_json_bytes", SINGLE_PROOF_JSON_BYTES + 1)),
        ("typed_metric_drift", lambda p: p["summary"].__setitem__("single_typed_bytes", SINGLE_TYPED_BYTES + 1)),
        ("split_frontier_drift", lambda p: p["summary"].__setitem__("split_typed_bytes", SPLIT_TYPED_BYTES - 1)),
        ("external_overclaim", lambda p: p["summary"].__setitem__("proof_size_comparable_external_rows", 1)),
        ("decision_drift", lambda p: p.__setitem__("decision", "GO_FULL_BLOCK")),
        ("issue_drift", lambda p: p.__setitem__("issue", ISSUE + 1)),
        ("non_claim_removed", lambda p: p.__setitem__("non_claims", p["non_claims"][:-1])),
        ("validation_command_drift", lambda p: p["validation_commands"].__setitem__(0, "python3.10 scripts/other.py")),
        ("resource_cap_drift", lambda p: p["resource_limit_analysis"].__setitem__("max_single_envelope_json_bytes", 64 * 1024 * 1024)),
        ("source_digest_drift", lambda p: p["source_artifacts"][0].__setitem__("sha256", "0" * 64)),
        ("payload_commitment_drift", lambda p: p.__setitem__("payload_commitment", "blake2b-256:" + "0" * 64)),
    )


def run_mutations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    expected_artifacts = expected_source_artifacts()
    for name, mutate in mutation_cases():
        candidate = copy.deepcopy(payload)
        mutate(candidate)
        if name != "payload_commitment_drift":
            candidate["payload_commitment"] = payload_commitment(candidate)
        try:
            validate_payload(candidate, expected_artifacts=expected_artifacts)
        except NativeD128Seq32SingleProofGateError as err:
            results.append({"name": name, "rejected": True, "error": str(err)})
        else:
            results.append({"name": name, "rejected": False, "error": ""})
    return results


def write_json(path: pathlib.Path, payload: dict[str, Any], mutation_results: list[dict[str, Any]]) -> None:
    out = dict(payload)
    out["mutations_checked"] = len(mutation_results)
    out["mutations_rejected"] = sum(1 for result in mutation_results if result["rejected"])
    out["all_mutations_rejected"] = all(result["rejected"] for result in mutation_results)
    out["mutation_results"] = mutation_results
    path.write_text(json.dumps(out, sort_keys=True, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_tsv(path: pathlib.Path, payload: dict[str, Any]) -> None:
    columns = [
        "decision",
        "single_proof_json_bytes",
        "split_proof_json_bytes",
        "proof_json_saving_bytes",
        "proof_json_ratio",
        "single_typed_bytes",
        "split_typed_bytes",
        "typed_saving_bytes",
        "typed_ratio",
    ]
    row = {"decision": payload["decision"], **payload["summary"]}
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=columns,
        delimiter="\t",
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerow(row)
    path.write_text(output.getvalue(), encoding="utf-8")


def write_md(path: pathlib.Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    body = f"""# Native D128 Seq32 Attention + D128 MLP Single Proof

Issue: #715

Status: `{payload['decision']}`.

This gate builds one native Stwo proof object over the real d128 two-head
`seq32` fused attention source, a verifier-recomputed co-location adapter, and the
seq32-derived d128 RMSNorm/MLP surface.

## Result

| object | proof JSON bytes | typed bytes |
| --- | ---: | ---: |
| matched scoped split frontier | `{s['split_proof_json_bytes']:,}` | `{s['split_typed_bytes']:,}` |
| native scoped single proof | `{s['single_proof_json_bytes']:,}` | `{s['single_typed_bytes']:,}` |
| saving | `{s['proof_json_saving_bytes']:,}` | `{s['typed_saving_bytes']:,}` |
| ratio | `{s['proof_json_ratio']}x` | `{s['typed_ratio']}x` |

## Meaning

The d128 scoped boundary is still a local one-proof size win. The win is
smaller than the earlier seq32 champion, which is useful evidence: width
pressure is real, but the boundary still shares enough proof plumbing to beat
the matched split local frontier.

## Guardrail

The adapter proves quotient and remainder consistency for the co-located rows.
It does not prove that the d128 MLP input was derived from the d128 attention
outputs. That semantics gap is the next decision gate, not something hidden in
this result.

## Resource Bounds

The single input is `{s['single_input_json_bytes']:,}` JSON bytes and the
single envelope is `{s['single_envelope_json_bytes']:,}` JSON bytes. The Rust
CLIs cap both at `{MAX_SINGLE_INPUT_JSON_BYTES:,}` bytes because they parse
whole JSON buffers with `serde_json`. These artifacts are repo-local evidence
inputs, not untrusted service payloads.

## Evidence

- JSON gate: `docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.json`
- TSV gate: `docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.tsv`
- Input: `docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.input.json`
- Envelope: `docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-2026-05.envelope.json`
- Single accounting: `docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-single-proof-binary-accounting-2026-05.json`
- Split accounting: `docs/engineering/evidence/zkai-native-d128-seq32-attention-mlp-split-frontier-binary-accounting-2026-05.json`

## Non-Claims

{chr(10).join(f'- {claim}.' for claim in NON_CLAIMS)}

## Reproduce

```bash
{chr(10).join(VALIDATION_COMMANDS)}
```
"""
    path.write_text(body, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    parser.add_argument("--write-md", type=pathlib.Path)
    args = parser.parse_args(argv)

    payload = build_payload()
    mutation_results = run_mutations(payload)
    if args.write_json:
        write_json(args.write_json, payload, mutation_results)
    if args.write_tsv:
        write_tsv(args.write_tsv, payload)
    if args.write_md:
        write_md(args.write_md, payload)
    rejected = sum(1 for result in mutation_results if result["rejected"])
    print(f"{DECISION}: {rejected}/{len(mutation_results)} mutations rejected")
    return 0 if rejected == len(mutation_results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
