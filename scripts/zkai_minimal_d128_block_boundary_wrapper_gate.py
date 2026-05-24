#!/usr/bin/env python3.10
"""Build the minimal d128 block-boundary wrapper for issue #715."""

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
import stat
import sys
import tempfile
from typing import Any


if sys.version_info < (3, 10):
    raise RuntimeError("zkai_minimal_d128_block_boundary_wrapper_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs" / "engineering"
EVIDENCE_DIR = DOCS_DIR / "evidence"

MODEL_SINGLE = EVIDENCE_DIR / "zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05.json"
MODEL_SINGLE_ACCOUNTING = (
    EVIDENCE_DIR / "zkai-native-d128-seq32-attention-derived-mlp-single-proof-binary-accounting-2026-05.json"
)
MODEL_SPLIT_ACCOUNTING = (
    EVIDENCE_DIR / "zkai-native-d128-seq32-attention-derived-mlp-split-frontier-binary-accounting-2026-05.json"
)
MODEL_PREFLIGHT = EVIDENCE_DIR / "zkai-model-faithful-d128-block-boundary-preflight-2026-05.json"
BLOCK_CHAIN = EVIDENCE_DIR / "zkai-attention-derived-d128-block-statement-chain-2026-05.json"

JSON_OUT = EVIDENCE_DIR / "zkai-minimal-d128-block-boundary-wrapper-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-minimal-d128-block-boundary-wrapper-2026-05.tsv"
MD_OUT = DOCS_DIR / "zkai-minimal-d128-block-boundary-wrapper-2026-05-24.md"

SCHEMA = "zkai-minimal-d128-block-boundary-wrapper-v1"
DECISION = "GO_MINIMAL_D128_ATTENTION_DERIVED_BLOCK_BOUNDARY_WRAPPER"
RESULT = "BOUND_MODEL_FAITHFUL_D128_PROOF_TO_BLOCK_STATEMENT_CHAIN_WITH_ZERO_PROOF_BYTE_DELTA"
ISSUE = 715
PAYLOAD_DOMAIN = "ptvm:zkai:minimal-d128-block-boundary-wrapper:v1"
STATEMENT_DOMAIN = "ptvm:zkai:minimal-d128-block-boundary-wrapper:statement:v1"
MAX_SOURCE_BYTES = 64 * 1024 * 1024
CLAIM_BOUNDARY = (
    "MINIMAL_D128_BLOCK_BOUNDARY_WRAPPER;"
    "BINDS_MODEL_FAITHFUL_PROOF_AND_ATTENTION_DERIVED_BLOCK_STATEMENT_CHAIN;"
    "PRESERVES_LOCAL_PROOF_SIZE_WIN;"
    "NOT_NEW_PROOF_OBJECT_NOT_FULL_BLOCK_NOT_SPEED_CLAIM_NOT_EXTERNAL_COMPARISON"
)
TIMING_POLICY = "statement_boundary_wrapper_only_no_new_proving_or_verify_timing_claim"
EXPECTED_BOUNDARY_STATEMENT_COMMITMENT = (
    "blake2b-256:abb34aa243a583b01b4a7f4516df7563c7be1e0ad6f64b26a52e58df17306f1a"
)
EXPECTED_PAYLOAD_COMMITMENT = "blake2b-256:02541cc4330b086b4207a07ff659cbef46141bd3e37248ba18f049469635f28b"

EXPECTED_SOURCES = {
    "model_faithful_single": {
        "path": MODEL_SINGLE,
        "schema": "zkai-native-d128-seq32-attention-derived-mlp-single-proof-gate-v1",
        "decision": "GO_D128_SEQ32_ATTENTION_DERIVED_MLP_SINGLE_PROOF_BEATS_MATCHED_SPLIT_FRONTIER",
        "result": "D128_ATTENTION_DERIVED_SINGLE_PROOF_SAVES_18913_JSON_AND_5168_TYPED_BYTES",
        "payload_commitment": "blake2b-256:e5ff1233eb91823ce8f1908ed55fa5e484d1dbedc33bb0a8f5cc17a9785ec121",
        "sha256": "0a2200bce9ebbe93d17a030dbd6c7222efccb06bb26ebde97999bfc938469447",
        "bytes": 7_719,
    },
    "model_faithful_single_accounting": {
        "path": MODEL_SINGLE_ACCOUNTING,
        "schema": "zkai-stwo-local-binary-proof-accounting-cli-v1",
        "decision": None,
        "result": None,
        "payload_commitment": None,
        "sha256": "8f0e8ce78fea0be66c98b41aae5c8658083194fce137321a79f094b32956baef",
        "bytes": 5_966,
    },
    "model_faithful_split_accounting": {
        "path": MODEL_SPLIT_ACCOUNTING,
        "schema": "zkai-stwo-local-binary-proof-accounting-cli-v1",
        "decision": None,
        "result": None,
        "payload_commitment": None,
        "sha256": "13f31f75ff1dd95aee63853abee201ac4a7615604ad3a4b30e412dc73c966ee9",
        "bytes": 10_714,
    },
    "model_faithful_block_preflight": {
        "path": MODEL_PREFLIGHT,
        "schema": "zkai-model-faithful-d128-block-boundary-preflight-v1",
        "decision": "GO_MODEL_FAITHFUL_D128_BLOCK_BOUNDARY_PREFLIGHT",
        "result": "ATTACK_MINIMAL_BLOCK_BOUNDARY_AROUND_MODEL_FAITHFUL_D128_ATTENTION_DERIVED_MLP",
        "payload_commitment": "blake2b-256:dfc47f43b47bef2b3d08bf254404641d6188eb0bd373978085cd9591a821d861",
        "sha256": "ba9917138b340bb1c87fc9aaca0be15f9c207fae0c5d4b600973f1b1706c17ee",
        "bytes": 11_456,
    },
    "attention_derived_block_statement_chain": {
        "path": BLOCK_CHAIN,
        "schema": "zkai-attention-derived-d128-block-statement-chain-gate-v1",
        "decision": "GO_ATTENTION_DERIVED_D128_BLOCK_STATEMENT_CHAIN",
        "result": "GO_COMMITTED_SLICE_CHAIN_NO_GO_SINGLE_COMPOSED_PROOF",
        "payload_commitment": "sha256:555998c5aecacc6e1d5e3ae8940f249f263c5b8dd3a40bf07cfa024478f6bd52",
        "sha256": "990602eefeaceb98a9272d00acfd9b1ef387d34d0218d9ae1a736afc2f6163a3",
        "bytes": 14_624,
    },
}

EXPECTED_PROOF_METADATA = {
    "proof_backend": "stwo",
    "proof_backend_version": "stwo-native-d128-seq32-attention-mlp-single-proof-object-native-adapter-v1",
    "proof_schema_version": "stwo-native-d128-seq32-attention-mlp-single-proof-object-native-adapter-payload-v1",
    "statement_version": "zkai-native-d128-seq32-attention-mlp-single-proof-object-native-adapter-statement-v1",
    "target_id": "attention-kv-d128-two-head-seq32-fused-softmax-table-plus-d128-attention-derived-d128-rmsnorm-mlp-v1",
    "verifier_domain": "ptvm:zkai:native-d128-seq32-attention-mlp-single-proof-object:v1",
}

EXPECTED_SINGLE = {
    "proof_json_size_bytes": 503_567,
    "proof_sha256": "29e13ac7f3fa5a5349873b982fb7964e0a8abb68b1e3547520f19ea65365caae",
    "envelope_sha256": "3779b56e651e28d609bd160d9f4e78856b1527deef8cd54f5797660b63850c70",
    "typed_bytes": 204_564,
    "record_stream_sha256": "1b42536d29a0b4af5f8efbc7cb1558847f83a294814751bd5cb8127a0b9a5a67",
    "record_stream_bytes": 1_084,
    "record_count": 13,
}

EXPECTED_SPLIT = {
    "proof_count": 2,
    "proof_json_size_bytes": 522_480,
    "typed_bytes": 209_732,
}

EXPECTED_SPLIT_COMPONENTS = (
    {
        "component_id": "attention_fused_softmax_logup_proof",
        "component_kind": "attention_source_arithmetic_plus_logup",
        "evidence_relative_path": "zkai-attention-kv-stwo-native-d128-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json",
        "proof_backend_version": "stwo-attention-kv-d128-two-head-seq32-fused-bounded-softmax-table-logup-v1",
        "target_id": "attention-kv-d128-two-head-seq32-causal-mask-fused-bounded-softmax-table-logup-v1",
        "verifier_domain": "ptvm:zkai:attention-kv-stwo-native-d128-two-head-seq32-fused-bounded-softmax-table-logup:v1",
        "source_target_id": "attention-kv-d128-two-head-seq32-causal-mask-fused-bounded-softmax-table-logup-v1",
        "source_verifier_domain": "ptvm:zkai:attention-kv-stwo-native-d128-two-head-seq32-fused-bounded-softmax-table-logup:v1",
        "proof_sha256": "6ba7edd634963ebdad0a5515dd743275703daa1c93f9680555851c3bf99faf40",
        "envelope_sha256": "b0e342f4158b94a960e3862426c47102bbb30904d4089a997d0c18865fb4ea94",
        "proof_json_size_bytes": 445_888,
        "typed_bytes": 184_900,
        "contains_logup": True,
    },
    {
        "component_id": "attention_derived_d128_rmsnorm_mlp_proof",
        "component_kind": "attention_derived_d128_rmsnorm_mlp",
        "evidence_relative_path": "zkai-d128-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.envelope.json",
        "proof_backend_version": "stwo-d128-rmsnorm-mlp-fused-air-proof-v1",
        "target_id": "attention-derived-d128-rmsnorm-mlp-fused-proof-v1",
        "verifier_domain": "ptvm:zkai:split-frontier:attention-derived-d128-rmsnorm-mlp-fused-proof:v1",
        "source_target_id": None,
        "source_verifier_domain": None,
        "proof_sha256": "0276a938375d3d2dc11ccc06c0ca96951659d09554cbf5598e37cb53143d22ab",
        "envelope_sha256": "df8822ad3dfaf15e06a63a3a838f57174665c914c44bd9567a5aa8347bce6cff",
        "proof_json_size_bytes": 76_592,
        "typed_bytes": 24_832,
        "contains_logup": False,
    },
)

EXPECTED_BLOCK = {
    "block_statement_commitment": "blake2b-256:5954b84283b2880c878c70ed533935925de1e14026126a406ad04f66c7ce14a5",
    "source_attention_outputs_commitment": "blake2b-256:d6cb4d179ea7685c4371d1827f215ec0821bb3ee3d6172d5dc6e13e030653638",
    "derived_input_activation_commitment": "blake2b-256:8168953e32013f1a7b1e6dce37a1c19900c571608d2f305d64925cdda9e99c35",
    "derived_hidden_activation_commitment": "blake2b-256:8603048df50e0249baaae9a5be031a09a05c5df8152a8a4df61809f0d9568cd4",
    "derived_residual_delta_commitment": "blake2b-256:0f4e5de46d06f4ad106b777f53c820f62c6db6742ad2d4530616e29db8ab02ec",
    "derived_output_activation_commitment": "blake2b-256:25feb3aa6a2a092602c86d10c767f71cdae3c60eade0254a2d121124b712bcf9",
    "slice_count": 6,
    "edge_count": 11,
    "accounted_relation_rows": 199_553,
    "projection_mul_rows": 131_072,
    "down_projection_mul_rows": 65_536,
    "activation_lookup_rows": 2_049,
}

ROW_IDS = (
    "model_faithful_proof_boundary",
    "attention_derived_block_statement_boundary",
    "minimal_wrapper_boundary",
)

TSV_COLUMNS = (
    "row_id",
    "status",
    "metric_scope",
    "proof_json_bytes",
    "typed_bytes",
    "split_reference_bytes",
    "saving_bytes",
    "ratio",
    "commitment",
    "action",
)

NON_CLAIMS = (
    "not a new native proof object",
    "not a full transformer block proof",
    "not recursive proof composition",
    "not a public proving-speed benchmark",
    "not a NANOZK proof-size win",
    "not a matched external zkML comparison",
    "not exact real-valued Softmax",
    "not full autoregressive inference",
)

VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_minimal_d128_block_boundary_wrapper_gate.py --write-json docs/engineering/evidence/zkai-minimal-d128-block-boundary-wrapper-2026-05.json --write-tsv docs/engineering/evidence/zkai-minimal-d128-block-boundary-wrapper-2026-05.tsv --write-md docs/engineering/zkai-minimal-d128-block-boundary-wrapper-2026-05-24.md",
    "python3.10 -m py_compile scripts/zkai_minimal_d128_block_boundary_wrapper_gate.py scripts/tests/test_zkai_minimal_d128_block_boundary_wrapper_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_minimal_d128_block_boundary_wrapper_gate",
    "git diff --check",
    "just gate-fast",
    "CARGO_TERM_COLOR=never cargo +nightly-2025-07-14 test --release --features stwo-backend --lib proof::tests -- --test-threads=4",
    "CARGO_TERM_COLOR=never cargo test --release --test assembly",
    "CARGO_TERM_COLOR=never cargo test --release --test e2e",
    "CARGO_TERM_COLOR=never cargo test --release --test interpreter",
    "CARGO_TERM_COLOR=never cargo test --release --test runtime",
    "bash scripts/run_dependency_audit_suite.sh",
    "uvx --from \"zizmor==1.24.1\" zizmor .github/workflows --format plain",
    "bash scripts/run_shellcheck_suite.sh",
    "CARGO_TERM_COLOR=never cargo +nightly-2025-07-14 test --release --features stwo-backend --lib stwo_backend::decoding::tests::phase28_aggregated_chained_folded_intervalized_state_relation_rejects_header_mismatch_before_nested_checks -- --exact",
    "just gate",
)

VALIDATION_NOTES = (
    "`just gate` passed locally after review fixes: local release gate passed 14 / 14 steps OK.",
)


class MinimalD128BlockBoundaryWrapperError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode(
            "utf-8"
        )
    except (TypeError, ValueError) as err:
        raise MinimalD128BlockBoundaryWrapperError("payload contains non-canonical JSON value") from err


def blake2b_commitment(value: Any, domain: str) -> str:
    digest = hashlib.blake2b(digest_size=32)
    digest.update(domain.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(value))
    return "blake2b-256:" + digest.hexdigest()


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    return blake2b_commitment(material, PAYLOAD_DOMAIN)


def statement_commitment(statement: dict[str, Any]) -> str:
    return blake2b_commitment(statement, STATEMENT_DOMAIN)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MinimalD128BlockBoundaryWrapperError(message)


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MinimalD128BlockBoundaryWrapperError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise MinimalD128BlockBoundaryWrapperError(f"{label} must be a list")
    return value


def require_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise MinimalD128BlockBoundaryWrapperError(f"{label} must be an integer")
    return value


def require_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise MinimalD128BlockBoundaryWrapperError(f"{label} must be a non-empty string")
    return value


def read_repo_file(path: pathlib.Path, label: str) -> bytes:
    root = ROOT.resolve()
    candidate = pathlib.Path(os.path.abspath(path if path.is_absolute() else ROOT / path))
    try:
        relative = candidate.relative_to(root)
    except ValueError as err:
        raise MinimalD128BlockBoundaryWrapperError(f"{label} escapes repo root: {path}") from err
    current = root
    try:
        for part in relative.parts:
            current = current / part
            if stat.S_ISLNK(current.lstat().st_mode):
                raise MinimalD128BlockBoundaryWrapperError(f"{label} must not traverse symlinks")
        fd = os.open(candidate, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            file_stat = os.fstat(fd)
            if not stat.S_ISREG(file_stat.st_mode):
                raise MinimalD128BlockBoundaryWrapperError(f"{label} must be a regular file")
            if file_stat.st_size > MAX_SOURCE_BYTES:
                raise MinimalD128BlockBoundaryWrapperError(f"{label} exceeds max source bytes")
            with os.fdopen(fd, "rb") as handle:
                fd = None
                raw = handle.read(MAX_SOURCE_BYTES + 1)
                if len(raw) > MAX_SOURCE_BYTES:
                    raise MinimalD128BlockBoundaryWrapperError(f"{label} exceeds max source bytes")
                after_stat = os.fstat(handle.fileno())
                before_fingerprint = (
                    file_stat.st_dev,
                    file_stat.st_ino,
                    file_stat.st_size,
                    file_stat.st_mtime_ns,
                    file_stat.st_ctime_ns,
                )
                after_fingerprint = (
                    after_stat.st_dev,
                    after_stat.st_ino,
                    after_stat.st_size,
                    after_stat.st_mtime_ns,
                    after_stat.st_ctime_ns,
                )
                if before_fingerprint != after_fingerprint:
                    raise MinimalD128BlockBoundaryWrapperError(f"{label} changed while reading")
                return raw
        finally:
            if fd is not None:
                os.close(fd)
    except OSError as err:
        raise MinimalD128BlockBoundaryWrapperError(f"failed to read {label}: {err}") from err


def read_json(path: pathlib.Path, label: str) -> tuple[dict[str, Any], bytes]:
    raw = read_repo_file(path, label)

    def reject_non_finite_constant(value: str) -> None:
        raise MinimalD128BlockBoundaryWrapperError(f"{label} contains non-finite JSON constant: {value}")

    try:
        value = json.loads(
            raw,
            parse_constant=reject_non_finite_constant,
            object_pairs_hook=reject_duplicate_json_keys,
        )
    except json.JSONDecodeError as err:
        raise MinimalD128BlockBoundaryWrapperError(f"{label} is not valid JSON: {err}") from err
    except UnicodeDecodeError as err:
        raise MinimalD128BlockBoundaryWrapperError(f"{label} is not valid UTF-8 JSON: {err}") from err
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value, raw


def reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise MinimalD128BlockBoundaryWrapperError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


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
            "payload_commitment": payload.get("payload_commitment"),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
        payloads[source_id] = payload
        descriptors.append(descriptor)
    return payloads, descriptors


def single_accounting_row(accounting: dict[str, Any]) -> dict[str, Any]:
    rows = require_list(accounting.get("rows"), "single accounting rows")
    require(len(rows) == 1, "single accounting row count drift")
    return require_dict(rows[0], "single accounting row")


def split_accounting_totals(accounting: dict[str, Any]) -> dict[str, Any]:
    rows = require_list(accounting.get("rows"), "split accounting rows")
    require(len(rows) == EXPECTED_SPLIT["proof_count"], "split accounting row count drift")
    proof_json = 0
    typed = 0
    components = []
    for index, row_value in enumerate(rows):
        row = require_dict(row_value, f"split accounting row {index}")
        expected = EXPECTED_SPLIT_COMPONENTS[index]
        envelope = require_dict(row.get("envelope_metadata"), f"split accounting row {index} envelope metadata")
        local = require_dict(row.get("local_binary_accounting"), f"split accounting row {index} local accounting")
        component = {
            "component_id": expected["component_id"],
            "component_kind": expected["component_kind"],
            "evidence_relative_path": require_str(
                row.get("evidence_relative_path"), f"split accounting row {index} evidence path"
            ),
            "proof_backend_version": require_str(
                envelope.get("proof_backend_version"), f"split accounting row {index} backend version"
            ),
            "target_id": expected["target_id"],
            "verifier_domain": expected["verifier_domain"],
            "source_target_id": envelope.get("target_id"),
            "source_verifier_domain": envelope.get("verifier_domain"),
            "proof_sha256": require_str(row.get("proof_sha256"), f"split accounting row {index} proof sha256"),
            "envelope_sha256": require_str(
                row.get("envelope_sha256"), f"split accounting row {index} envelope sha256"
            ),
            "proof_json_size_bytes": require_int(
                row.get("proof_json_size_bytes"), f"split accounting row {index} JSON bytes"
            ),
            "typed_bytes": require_int(local.get("component_sum_bytes"), f"split accounting row {index} typed bytes"),
            "contains_logup": expected["contains_logup"],
        }
        for key, expected_value in expected.items():
            require(component.get(key) == expected_value, f"split component {index} {key} drift")
        proof_json += component["proof_json_size_bytes"]
        typed += component["typed_bytes"]
        components.append(component)
    return {"proof_json_size_bytes": proof_json, "typed_bytes": typed, "proof_count": len(rows), "components": components}


def build_boundary_statement(sources: dict[str, dict[str, Any]]) -> dict[str, Any]:
    single = require_dict(sources.get("model_faithful_single"), "model faithful single source")
    single_summary = require_dict(single.get("summary"), "model faithful single summary")
    single_accounting = single_accounting_row(
        require_dict(sources.get("model_faithful_single_accounting"), "single accounting source")
    )
    single_local = require_dict(single_accounting.get("local_binary_accounting"), "single local accounting")
    split = split_accounting_totals(
        require_dict(sources.get("model_faithful_split_accounting"), "split accounting source")
    )
    preflight = require_dict(sources.get("model_faithful_block_preflight"), "preflight source")
    preflight_summary = require_dict(preflight.get("summary"), "preflight summary")
    block = require_dict(sources.get("attention_derived_block_statement_chain"), "block statement chain source")
    block_summary = require_dict(block.get("summary"), "block statement chain summary")

    proof_binding = {
        "proof_backend": require_str(
            require_dict(single_accounting.get("envelope_metadata"), "single envelope metadata").get("proof_backend"),
            "proof backend",
        ),
        "proof_backend_version": require_str(
            require_dict(single_accounting.get("envelope_metadata"), "single envelope metadata").get(
                "proof_backend_version"
            ),
            "proof backend version",
        ),
        "proof_schema_version": require_str(
            require_dict(single_accounting.get("envelope_metadata"), "single envelope metadata").get(
                "proof_schema_version"
            ),
            "proof schema version",
        ),
        "statement_version": require_str(
            require_dict(single_accounting.get("envelope_metadata"), "single envelope metadata").get(
                "statement_version"
            ),
            "statement version",
        ),
        "target_id": require_str(
            require_dict(single_accounting.get("envelope_metadata"), "single envelope metadata").get("target_id"),
            "target id",
        ),
        "verifier_domain": require_str(
            require_dict(single_accounting.get("envelope_metadata"), "single envelope metadata").get(
                "verifier_domain"
            ),
            "verifier domain",
        ),
        "envelope_sha256": require_str(single_accounting.get("envelope_sha256"), "single envelope sha256"),
        "proof_sha256": require_str(single_accounting.get("proof_sha256"), "single proof sha256"),
        "proof_json_size_bytes": require_int(
            single_accounting.get("proof_json_size_bytes"), "single proof JSON bytes"
        ),
        "typed_bytes": require_int(single_local.get("component_sum_bytes"), "single typed bytes"),
        "record_stream_bytes": require_int(single_local.get("record_stream_bytes"), "record stream bytes"),
        "record_stream_sha256": require_str(single_local.get("record_stream_sha256"), "record stream sha256"),
        "record_count": require_int(single_local.get("record_count"), "record count"),
    }
    split_frontier = {
        "proof_count": require_int(split.get("proof_count"), "split proof count"),
        "proof_json_size_bytes": require_int(split.get("proof_json_size_bytes"), "split proof JSON bytes"),
        "typed_bytes": require_int(split.get("typed_bytes"), "split typed bytes"),
        "components": require_list(split.get("components"), "split components"),
    }
    block_binding = {}
    for key, expected_value in EXPECTED_BLOCK.items():
        block_binding[key] = (
            require_int(block_summary.get(key), f"block summary {key}")
            if isinstance(expected_value, int)
            else require_str(block_summary.get(key), f"block summary {key}")
        )
    proof_json_saving = require_int(
        split_frontier.get("proof_json_size_bytes"), "split frontier JSON bytes"
    ) - require_int(proof_binding.get("proof_json_size_bytes"), "proof binding JSON bytes")
    typed_saving = require_int(split_frontier.get("typed_bytes"), "split frontier typed bytes") - require_int(
        proof_binding.get("typed_bytes"), "proof binding typed bytes"
    )
    require(proof_json_saving >= 0, "single proof must not exceed split frontier JSON bytes")
    require(typed_saving >= 0, "single proof must not exceed split frontier typed bytes")
    return {
        "schema": "zkai-minimal-d128-block-boundary-statement-v1",
        "claim_boundary": CLAIM_BOUNDARY,
        "preflight_binding": {
            "payload_commitment": require_str(preflight.get("payload_commitment"), "preflight payload commitment"),
            "decision": require_str(preflight.get("decision"), "preflight decision"),
            "primary_next_gate": require_str(preflight.get("primary_next_gate"), "preflight primary next gate"),
            "current_anchor": require_str(preflight_summary.get("current_anchor"), "preflight current anchor"),
        },
        "proof_binding": proof_binding,
        "split_frontier": split_frontier,
        "block_statement_binding": block_binding,
        "local_size_result": {
            "proof_json_saving_bytes": proof_json_saving,
            "proof_json_ratio": require_str(single_summary.get("proof_json_ratio"), "proof JSON ratio"),
            "typed_saving_bytes": typed_saving,
            "typed_ratio": require_str(single_summary.get("typed_ratio"), "typed ratio"),
            "wrapper_proof_byte_delta": 0,
            "proof_size_comparable_external_rows": require_int(
                single_summary.get("proof_size_comparable_external_rows"), "external row count"
            ),
        },
        "statement_edges": [
            "preflight selects this wrapper as the primary next gate",
            "single proof accounting pins the envelope hash, proof hash, verifier domain, and target id",
            "split accounting pins the matched two-proof frontier",
            "block statement chain pins attention outputs, MLP slice edges, and final residual output",
            "wrapper adds statement binding only; it does not add or subtract proof bytes",
        ],
        "non_claims": list(NON_CLAIMS),
    }


def build_rows(statement: dict[str, Any], statement_hash: str) -> list[dict[str, Any]]:
    proof = require_dict(statement.get("proof_binding"), "proof binding")
    split = require_dict(statement.get("split_frontier"), "split frontier")
    block = require_dict(statement.get("block_statement_binding"), "block statement binding")
    local = require_dict(statement.get("local_size_result"), "local size result")
    return [
        {
            "row_id": "model_faithful_proof_boundary",
            "status": "CURRENT_PROOF_OBJECT_BOUND",
            "metric_scope": "proof_json_and_local_typed_bytes",
            "proof_json_bytes": require_int(proof.get("proof_json_size_bytes"), "proof row JSON bytes"),
            "typed_bytes": require_int(proof.get("typed_bytes"), "proof row typed bytes"),
            "split_reference_bytes": require_int(split.get("proof_json_size_bytes"), "proof row split JSON bytes"),
            "saving_bytes": require_int(local.get("proof_json_saving_bytes"), "proof row saving bytes"),
            "ratio": require_str(local.get("proof_json_ratio"), "proof row ratio"),
            "commitment": require_str(proof.get("proof_sha256"), "proof row commitment"),
            "action": "preserve_as_underlying_local_proof_size_win",
        },
        {
            "row_id": "attention_derived_block_statement_boundary",
            "status": "BLOCK_STATEMENT_CHAIN_BOUND",
            "metric_scope": "statement_chain_relation_rows",
            "proof_json_bytes": None,
            "typed_bytes": require_int(block.get("accounted_relation_rows"), "block row relation rows"),
            "split_reference_bytes": None,
            "saving_bytes": None,
            "ratio": None,
            "commitment": require_str(block.get("block_statement_commitment"), "block row commitment"),
            "action": "bind_attention_output_to_d128_mlp_output_without_full_block_overclaim",
        },
        {
            "row_id": "minimal_wrapper_boundary",
            "status": "STATEMENT_WRAPPER_GO",
            "metric_scope": "statement_binding_not_new_proof_bytes",
            "proof_json_bytes": 0,
            "typed_bytes": len(canonical_json_bytes(statement)),
            "split_reference_bytes": 0,
            "saving_bytes": 0,
            "ratio": "1.000000",
            "commitment": statement_hash,
            "action": "use_as_next_paper_claim_object_then_measure_next_real_native_boundary",
        },
    ]


def build_payload() -> dict[str, Any]:
    sources, descriptors = load_sources()
    statement = build_boundary_statement(sources)
    statement_hash = statement_commitment(statement)
    rows = build_rows(statement, statement_hash)
    proof = require_dict(statement.get("proof_binding"), "proof binding")
    split = require_dict(statement.get("split_frontier"), "split frontier")
    block = require_dict(statement.get("block_statement_binding"), "block statement binding")
    local = require_dict(statement.get("local_size_result"), "local size result")
    payload = {
        "schema": SCHEMA,
        "issue": ISSUE,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "timing_policy": TIMING_POLICY,
        "boundary_statement_commitment": statement_hash,
        "boundary_statement": statement,
        "source_artifacts": descriptors,
        "summary": {
            "underlying_single_proof_json_bytes": require_int(
                proof.get("proof_json_size_bytes"), "single proof JSON bytes"
            ),
            "matched_split_proof_json_bytes": require_int(split.get("proof_json_size_bytes"), "split proof JSON bytes"),
            "proof_json_saving_bytes": require_int(local.get("proof_json_saving_bytes"), "proof JSON saving bytes"),
            "proof_json_ratio": require_str(local.get("proof_json_ratio"), "proof JSON ratio"),
            "underlying_single_typed_bytes": require_int(proof.get("typed_bytes"), "single typed bytes"),
            "matched_split_typed_bytes": require_int(split.get("typed_bytes"), "split typed bytes"),
            "split_component_proof_json_bytes": {
                require_str(component.get("component_id"), "split component id"): require_int(
                    component.get("proof_json_size_bytes"), "split component JSON bytes"
                )
                for component in require_list(split.get("components"), "split components")
            },
            "split_component_typed_bytes": {
                require_str(component.get("component_id"), "split component id"): require_int(
                    component.get("typed_bytes"), "split component typed bytes"
                )
                for component in require_list(split.get("components"), "split components")
            },
            "typed_saving_bytes": require_int(local.get("typed_saving_bytes"), "typed saving bytes"),
            "typed_ratio": require_str(local.get("typed_ratio"), "typed ratio"),
            "wrapper_proof_byte_delta": require_int(local.get("wrapper_proof_byte_delta"), "wrapper proof byte delta"),
            "boundary_statement_canonical_bytes": len(canonical_json_bytes(statement)),
            "block_statement_commitment": require_str(
                block.get("block_statement_commitment"), "block statement commitment"
            ),
            "source_attention_outputs_commitment": require_str(
                block.get("source_attention_outputs_commitment"), "attention output commitment"
            ),
            "derived_output_activation_commitment": require_str(
                block.get("derived_output_activation_commitment"), "derived output activation commitment"
            ),
            "block_statement_relation_rows": require_int(block.get("accounted_relation_rows"), "block relation rows"),
            "block_statement_edge_count": require_int(block.get("edge_count"), "block edge count"),
            "proof_size_comparable_external_rows": require_int(
                local.get("proof_size_comparable_external_rows"), "external row count"
            ),
            "paper_claim_status": "GO_MINIMAL_WRAPPER_NOT_FULL_BLOCK_NOT_NEW_PROOF",
        },
        "go_gate": [
            "proof envelope hash, proof hash, verifier domain, target id, and local typed bytes stay pinned",
            "block statement chain commitment and attention-derived output commitments stay pinned",
            "wrapper keeps zero proof-byte delta and does not turn metadata into proof-size savings",
            "mutation gates reject relabeling, stale source accounting, full-block claims, and external benchmark claims",
        ],
        "no_go_gate": [
            "the wrapper drops the model-faithful proof accounting or verifier-domain binding",
            "the wrapper drops the block statement chain commitment or output activation commitment",
            "the result requires claiming a new native proof object or full transformer block proof",
            "the result requires timing, NANOZK, external-comparison, or production-throughput wording",
        ],
        "rows": rows,
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
        "validation_notes": list(VALIDATION_NOTES),
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
    normalized = [require_dict(artifact, f"source artifact {index}") for index, artifact in enumerate(artifacts)]
    require([artifact.get("id") for artifact in normalized] == list(EXPECTED_SOURCES), "source artifact order drift")
    for artifact in normalized:
        source_id = require_str(artifact.get("id"), "source artifact id")
        require(source_id in EXPECTED_SOURCES, "source artifact id drift")
        expected = EXPECTED_SOURCES[source_id]
        for key in ("schema", "decision", "result", "payload_commitment", "sha256", "bytes"):
            require(artifact.get(key) == expected[key], f"{source_id} {key} drift")
        require(artifact.get("path") == expected["path"].relative_to(ROOT).as_posix(), f"{source_id} path drift")


def validate_boundary_statement(statement: dict[str, Any]) -> None:
    require(statement.get("schema") == "zkai-minimal-d128-block-boundary-statement-v1", "statement schema drift")
    claim = statement.get("claim_boundary")
    require(claim == CLAIM_BOUNDARY, "statement claim boundary drift")

    preflight = require_dict(statement.get("preflight_binding"), "preflight binding")
    require(preflight.get("payload_commitment") == EXPECTED_SOURCES["model_faithful_block_preflight"]["payload_commitment"], "preflight commitment drift")
    require(preflight.get("decision") == EXPECTED_SOURCES["model_faithful_block_preflight"]["decision"], "preflight decision drift")
    require(
        preflight.get("primary_next_gate") == "minimal_scoped_d128_attention_derived_block_boundary_wrapper",
        "preflight primary gate drift",
    )
    require(preflight.get("current_anchor") == "model_faithful_d128_boundary", "preflight current anchor drift")

    proof = require_dict(statement.get("proof_binding"), "proof binding")
    for key, expected in EXPECTED_PROOF_METADATA.items():
        require(proof.get(key) == expected, f"proof {key} drift")
    for key, expected in EXPECTED_SINGLE.items():
        require(proof.get(key) == expected, f"single proof {key} drift")

    split = require_dict(statement.get("split_frontier"), "split frontier")
    for key, expected in EXPECTED_SPLIT.items():
        require(split.get(key) == expected, f"split frontier {key} drift")
    components = require_list(split.get("components"), "split components")
    require(len(components) == len(EXPECTED_SPLIT_COMPONENTS), "split component count drift")
    split_json = 0
    split_typed = 0
    for index, component_value in enumerate(components):
        component = require_dict(component_value, f"split component {index}")
        expected_component = EXPECTED_SPLIT_COMPONENTS[index]
        for key, expected in expected_component.items():
            require(component.get(key) == expected, f"split component {index} {key} drift")
        split_json += require_int(component.get("proof_json_size_bytes"), f"split component {index} JSON bytes")
        split_typed += require_int(component.get("typed_bytes"), f"split component {index} typed bytes")
    require(split_json == split.get("proof_json_size_bytes"), "split component JSON sum drift")
    require(split_typed == split.get("typed_bytes"), "split component typed sum drift")

    block = require_dict(statement.get("block_statement_binding"), "block statement binding")
    for key, expected in EXPECTED_BLOCK.items():
        require(block.get(key) == expected, f"block statement {key} drift")

    local = require_dict(statement.get("local_size_result"), "local size result")
    require(local.get("proof_json_saving_bytes") == 18_913, "proof JSON saving drift")
    require(local.get("proof_json_ratio") == "0.963801", "proof JSON ratio drift")
    require(local.get("typed_saving_bytes") == 5_168, "typed saving drift")
    require(local.get("typed_ratio") == "0.975359", "typed ratio drift")
    require(local.get("wrapper_proof_byte_delta") == 0, "wrapper proof byte delta drift")
    require(local.get("proof_size_comparable_external_rows") == 0, "external row count drift")

    edges = statement.get("statement_edges")
    require(isinstance(edges, list) and len(edges) == 5, "statement edge inventory drift")
    require(all(isinstance(edge, str) and edge for edge in edges), "statement edge inventory drift")
    non_claims = statement.get("non_claims")
    require(non_claims == list(NON_CLAIMS), "statement non-claims drift")


def validate_rows(payload: dict[str, Any]) -> None:
    rows = payload.get("rows")
    require(isinstance(rows, list), "rows missing")
    require(len(rows) == len(ROW_IDS), "row count drift")
    normalized = [require_dict(row, f"row {index}") for index, row in enumerate(rows)]
    require([row.get("row_id") for row in normalized] == list(ROW_IDS), "row order drift")
    by_id = {row["row_id"]: row for row in normalized}
    for row_id in ROW_IDS:
        row = by_id[row_id]
        for key in ("row_id", "status", "metric_scope", "action"):
            require(isinstance(row.get(key), str) and row[key], f"{row_id}.{key} missing")

    proof = by_id["model_faithful_proof_boundary"]
    require(proof.get("proof_json_bytes") == 503_567, "proof row JSON bytes drift")
    require(proof.get("typed_bytes") == 204_564, "proof row typed bytes drift")
    require(proof.get("split_reference_bytes") == 522_480, "proof row split bytes drift")
    require(proof.get("saving_bytes") == 18_913, "proof row saving drift")
    require(proof.get("commitment") == EXPECTED_SINGLE["proof_sha256"], "proof row commitment drift")

    block = by_id["attention_derived_block_statement_boundary"]
    require(block.get("typed_bytes") == 199_553, "block row relation rows drift")
    require(block.get("commitment") == EXPECTED_BLOCK["block_statement_commitment"], "block row commitment drift")

    wrapper = by_id["minimal_wrapper_boundary"]
    statement = require_dict(payload.get("boundary_statement"), "boundary statement")
    require(wrapper.get("proof_json_bytes") == 0, "wrapper row proof bytes drift")
    require(wrapper.get("split_reference_bytes") == 0, "wrapper row split bytes drift")
    require(wrapper.get("saving_bytes") == 0, "wrapper row saving drift")
    require(wrapper.get("typed_bytes") == len(canonical_json_bytes(statement)), "wrapper row statement bytes drift")
    require(wrapper.get("commitment") == payload.get("boundary_statement_commitment"), "wrapper row commitment drift")


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
    require(payload.get("claim_boundary") == CLAIM_BOUNDARY, "claim boundary drift")
    require(payload.get("timing_policy") == TIMING_POLICY, "timing policy drift")
    validate_source_artifacts(payload)
    statement = require_dict(payload.get("boundary_statement"), "boundary statement")
    validate_boundary_statement(statement)
    require(
        payload.get("boundary_statement_commitment") == EXPECTED_BOUNDARY_STATEMENT_COMMITMENT,
        "boundary statement commitment anchor drift",
    )
    require(payload.get("boundary_statement_commitment") == statement_commitment(statement), "boundary statement commitment drift")
    validate_rows(payload)

    summary = require_dict(payload.get("summary"), "summary")
    expected_summary = {
        "underlying_single_proof_json_bytes": 503_567,
        "matched_split_proof_json_bytes": 522_480,
        "proof_json_saving_bytes": 18_913,
        "proof_json_ratio": "0.963801",
        "underlying_single_typed_bytes": 204_564,
        "matched_split_typed_bytes": 209_732,
        "split_component_proof_json_bytes": {
            "attention_fused_softmax_logup_proof": 445_888,
            "attention_derived_d128_rmsnorm_mlp_proof": 76_592,
        },
        "split_component_typed_bytes": {
            "attention_fused_softmax_logup_proof": 184_900,
            "attention_derived_d128_rmsnorm_mlp_proof": 24_832,
        },
        "typed_saving_bytes": 5_168,
        "typed_ratio": "0.975359",
        "wrapper_proof_byte_delta": 0,
        "boundary_statement_canonical_bytes": len(canonical_json_bytes(statement)),
        "block_statement_commitment": EXPECTED_BLOCK["block_statement_commitment"],
        "source_attention_outputs_commitment": EXPECTED_BLOCK["source_attention_outputs_commitment"],
        "derived_output_activation_commitment": EXPECTED_BLOCK["derived_output_activation_commitment"],
        "block_statement_relation_rows": 199_553,
        "block_statement_edge_count": 11,
        "proof_size_comparable_external_rows": 0,
        "paper_claim_status": "GO_MINIMAL_WRAPPER_NOT_FULL_BLOCK_NOT_NEW_PROOF",
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary.{key} drift")
    require(payload.get("non_claims") == list(NON_CLAIMS), "non-claims drift")
    require(payload.get("validation_commands") == list(VALIDATION_COMMANDS), "validation commands drift")
    require(payload.get("validation_notes") == list(VALIDATION_NOTES), "validation notes drift")
    go_gate = payload.get("go_gate")
    no_go_gate = payload.get("no_go_gate")
    require(isinstance(go_gate, list) and len(go_gate) == 4, "GO gate drift")
    require(isinstance(no_go_gate, list) and len(no_go_gate) == 4, "NO-GO gate drift")
    require(all(isinstance(item, str) and item for item in go_gate), "GO gate drift")
    require(all(isinstance(item, str) and item for item in no_go_gate), "NO-GO gate drift")
    require(any("zero proof-byte delta" in item for item in go_gate), "GO gate must keep wrapper accounting honest")
    require(any("full transformer block proof" in item for item in no_go_gate), "NO-GO gate must reject full-block promotion")

    if require_mutations:
        results = payload.get("mutation_results")
        require(isinstance(results, list), "mutation results missing")
        require(payload.get("mutations_checked") == len(MUTATIONS), "mutation count drift")
        require(payload.get("mutations_rejected") == len(MUTATIONS), "mutation rejected count drift")
        require(payload.get("all_mutations_rejected") is True, "all mutations rejected drift")
        require(len(results) == len(MUTATIONS), "mutation result count drift")
        names = [name for name, _ in MUTATIONS]
        normalized_results = [require_dict(result, f"mutation result {index}") for index, result in enumerate(results)]
        require([result.get("name") for result in normalized_results] == names, "mutation order drift")
        for result in normalized_results:
            name = require_str(result.get("name"), "mutation name")
            require(result.get("rejected") is True, f"{name} mutation acceptance drift")
            require(isinstance(result.get("error"), str) and result["error"], f"{name} mutation error missing")
    if require_commitment:
        require(payload.get("payload_commitment") == payload_commitment(payload), "payload commitment drift")
        if require_mutations:
            require(payload.get("payload_commitment") == EXPECTED_PAYLOAD_COMMITMENT, "payload commitment anchor drift")


Mutation = tuple[str, Callable[[dict[str, Any]], None]]


def _payload_commitment_drift(payload: dict[str, Any]) -> None:
    payload["payload_commitment"] = "blake2b-256:" + ("0" * 64)


def _remove_non_claim(payload: dict[str, Any]) -> None:
    payload["non_claims"] = payload["non_claims"][1:]


def _drop_row_field(payload: dict[str, Any]) -> None:
    payload["rows"][0].pop("action", None)


MUTATIONS: tuple[Mutation, ...] = (
    ("source_digest_drift", lambda p: p["source_artifacts"][0].__setitem__("sha256", "0" * 64)),
    ("single_proof_sha_drift", lambda p: p["boundary_statement"]["proof_binding"].__setitem__("proof_sha256", "0" * 64)),
    ("envelope_sha_drift", lambda p: p["boundary_statement"]["proof_binding"].__setitem__("envelope_sha256", "0" * 64)),
    ("verifier_domain_drift", lambda p: p["boundary_statement"]["proof_binding"].__setitem__("verifier_domain", "ptvm:wrong")),
    ("target_id_drift", lambda p: p["boundary_statement"]["proof_binding"].__setitem__("target_id", "wrong-target")),
    ("typed_bytes_drift", lambda p: p["boundary_statement"]["proof_binding"].__setitem__("typed_bytes", 1)),
    ("split_frontier_drift", lambda p: p["boundary_statement"]["split_frontier"].__setitem__("typed_bytes", 1)),
    ("split_component_drift", lambda p: p["boundary_statement"]["split_frontier"]["components"][0].__setitem__("typed_bytes", 1)),
    ("preflight_commitment_drift", lambda p: p["boundary_statement"]["preflight_binding"].__setitem__("payload_commitment", "blake2b-256:" + ("1" * 64))),
    ("preflight_gate_drift", lambda p: p["boundary_statement"]["preflight_binding"].__setitem__("primary_next_gate", "d128_h2_seq64_sequence_stress")),
    ("block_statement_commitment_drift", lambda p: p["boundary_statement"]["block_statement_binding"].__setitem__("block_statement_commitment", "blake2b-256:" + ("2" * 64))),
    ("attention_output_commitment_drift", lambda p: p["boundary_statement"]["block_statement_binding"].__setitem__("source_attention_outputs_commitment", "blake2b-256:" + ("3" * 64))),
    ("mlp_output_commitment_drift", lambda p: p["boundary_statement"]["block_statement_binding"].__setitem__("derived_output_activation_commitment", "blake2b-256:" + ("4" * 64))),
    ("wrapper_byte_delta_overclaim", lambda p: p["boundary_statement"]["local_size_result"].__setitem__("wrapper_proof_byte_delta", -1)),
    ("full_block_overclaim", lambda p: p.__setitem__("claim_boundary", p["claim_boundary"].replace("NOT_FULL_BLOCK_", ""))),
    ("external_comparison_overclaim", lambda p: p.__setitem__("claim_boundary", p["claim_boundary"].replace("NOT_EXTERNAL_COMPARISON", "EXTERNAL_COMPARISON"))),
    ("non_claim_removed", _remove_non_claim),
    ("row_missing_required_field", _drop_row_field),
    ("validation_command_drift", lambda p: p["validation_commands"].append("echo unsafe")),
    ("validation_note_drift", lambda p: p["validation_notes"].append("unsafe full-gate claim")),
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
        except MinimalD128BlockBoundaryWrapperError as err:
            results.append({"name": name, "rejected": True, "error": str(err)})
        else:
            results.append({"name": name, "rejected": False, "error": None})
    return results


def resolve_output_path(path: pathlib.Path, base_dir: pathlib.Path) -> pathlib.Path:
    candidate = path if path.is_absolute() else ROOT / path
    try:
        if stat.S_ISLNK(candidate.lstat().st_mode):
            raise MinimalD128BlockBoundaryWrapperError(f"refusing to write through symlink: {candidate}")
    except FileNotFoundError:
        pass
    try:
        resolved = candidate.resolve(strict=False)
        base_resolved = base_dir.resolve()
    except OSError as err:
        raise MinimalD128BlockBoundaryWrapperError(f"unable to resolve output path: {path}") from err
    if resolved != base_resolved and base_resolved not in resolved.parents:
        raise MinimalD128BlockBoundaryWrapperError(f"output path must stay inside {base_dir}")
    if resolved == base_resolved or (resolved.exists() and resolved.is_dir()):
        raise MinimalD128BlockBoundaryWrapperError(f"output path must be a file: {resolved}")
    if resolved.parent.exists() and not resolved.parent.is_dir():
        raise MinimalD128BlockBoundaryWrapperError(f"output path parent must be a directory: {resolved}")
    try:
        resolved.parent.relative_to(base_resolved)
    except ValueError as err:
        raise MinimalD128BlockBoundaryWrapperError(f"output path parent must stay inside {base_dir}") from err
    return resolved


def checked_output_paths(
    json_path: pathlib.Path, tsv_path: pathlib.Path, md_path: pathlib.Path
) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    resolved = (
        resolve_output_path(json_path, EVIDENCE_DIR),
        resolve_output_path(tsv_path, EVIDENCE_DIR),
        resolve_output_path(md_path, DOCS_DIR),
    )
    if len({str(path) for path in resolved}) != len(resolved):
        raise MinimalD128BlockBoundaryWrapperError("output paths must be different files")
    return resolved


def format_cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def atomic_write_text(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: pathlib.Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            tmp_path = pathlib.Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
        tmp_path = None
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink()
            except FileNotFoundError:
                pass


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
        "| row | status | scope | proof JSON | typed or rows | reference | saving | ratio | commitment | action |",
        "|---|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in payload["rows"]:
        rows.append(
            "| {row_id} | `{status}` | {scope} | {proof_json} | {typed} | {reference} | {saving} | {ratio} | `{commitment}` | {action} |".format(
                row_id=row["row_id"].replace("_", " "),
                status=row["status"],
                scope=row["metric_scope"],
                proof_json=f"`{row['proof_json_bytes']:,}`" if isinstance(row.get("proof_json_bytes"), int) else "",
                typed=f"`{row['typed_bytes']:,}`" if isinstance(row.get("typed_bytes"), int) else "",
                reference=f"`{row['split_reference_bytes']:,}`" if isinstance(row.get("split_reference_bytes"), int) else "",
                saving=f"`{row['saving_bytes']:,}`" if isinstance(row.get("saving_bytes"), int) else "",
                ratio=f"`{row['ratio']}`" if row.get("ratio") is not None else "",
                commitment=row["commitment"],
                action=row["action"].replace("_", " "),
            )
        )
    non_claims = "\n".join(f"- {claim}." for claim in NON_CLAIMS)
    commands = "\n".join(VALIDATION_COMMANDS)
    validation_notes = "\n".join(f"- {note}" for note in VALIDATION_NOTES)
    statement = payload["boundary_statement"]
    proof_binding = statement["proof_binding"]
    preflight_binding = statement["preflight_binding"]
    source_artifacts = "\n".join(
        "- `{id}`: `{path}`, sha256 `{sha256}`, `{bytes:,}` bytes.".format(
            id=artifact["id"],
            path=artifact["path"],
            sha256=artifact["sha256"],
            bytes=artifact["bytes"],
        )
        for artifact in payload["source_artifacts"]
    )
    split_components = "\n".join(
        "- `{component_id}`: `{proof_json_size_bytes:,}` proof JSON bytes / `{typed_bytes:,}` typed bytes; target `{target_id}`; verifier domain `{verifier_domain}`.".format(
            component_id=component["component_id"],
            proof_json_size_bytes=component["proof_json_size_bytes"],
            typed_bytes=component["typed_bytes"],
            target_id=component["target_id"],
            verifier_domain=component["verifier_domain"],
        )
        for component in statement["split_frontier"]["components"]
    )
    md = f"""# Minimal D128 Block-Boundary Wrapper

Issue: #{ISSUE}

Decision: `{payload["decision"]}`

Result: `{payload["result"]}`

Boundary statement commitment: `{payload["boundary_statement_commitment"]}`

Payload commitment: `{payload["payload_commitment"]}`

## What Changed

This gate wraps the current model-faithful d128 attention-derived MLP proof result in a typed block-boundary statement. It binds the proof envelope hash, proof hash, verifier domain, target id, local typed-byte accounting, matched split frontier, and the attention-derived d128 block statement-chain commitment.

The wrapper is deliberately boring in proof-size accounting: it adds `0` proof bytes. It is a statement boundary around an already measured proof object, not a new native proof object.

## Size Anchor

- Underlying single proof JSON bytes: `{summary["underlying_single_proof_json_bytes"]:,}`.
- Matched split proof JSON bytes: `{summary["matched_split_proof_json_bytes"]:,}`.
- JSON saving: `{summary["proof_json_saving_bytes"]:,}` bytes, ratio `{summary["proof_json_ratio"]}`.
- Underlying local typed bytes: `{summary["underlying_single_typed_bytes"]:,}`.
- Matched split local typed bytes: `{summary["matched_split_typed_bytes"]:,}`.
- Typed saving: `{summary["typed_saving_bytes"]:,}` bytes, ratio `{summary["typed_ratio"]}`.
- Wrapper proof-byte delta: `{summary["wrapper_proof_byte_delta"]}`.

## Split Frontier Components

{split_components}

## Proof Binding

- Proof backend: `{proof_binding["proof_backend"]}`.
- Proof backend version: `{proof_binding["proof_backend_version"]}`.
- Proof schema version: `{proof_binding["proof_schema_version"]}`.
- Statement version: `{proof_binding["statement_version"]}`.
- Target id: `{proof_binding["target_id"]}`.
- Verifier domain: `{proof_binding["verifier_domain"]}`.
- Envelope sha256: `{proof_binding["envelope_sha256"]}`.
- Proof sha256: `{proof_binding["proof_sha256"]}`.
- Preflight payload commitment: `{preflight_binding["payload_commitment"]}`.

## Source Artifacts

{source_artifacts}

## Block Statement Binding

- Block statement commitment: `{summary["block_statement_commitment"]}`.
- Attention output commitment: `{summary["source_attention_outputs_commitment"]}`.
- Derived output activation commitment: `{summary["derived_output_activation_commitment"]}`.
- Accounted relation rows: `{summary["block_statement_relation_rows"]:,}`.
- Edge count: `{summary["block_statement_edge_count"]}`.

## Rows

{chr(10).join(rows)}

## Non-Claims

{non_claims}

## Mutation Gates

- Mutations rejected: `{payload["mutations_rejected"]} / {payload["mutations_checked"]}`.

## Validation

```bash
{commands}
```

{validation_notes}
"""
    atomic_write_text(output, md)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path, default=JSON_OUT)
    parser.add_argument("--write-tsv", type=pathlib.Path, default=TSV_OUT)
    parser.add_argument("--write-md", type=pathlib.Path, default=MD_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    json_path, tsv_path, md_path = checked_output_paths(args.write_json, args.write_tsv, args.write_md)
    payload = build_payload()
    write_json(json_path, payload)
    write_tsv(tsv_path, payload)
    write_md(md_path, payload)
    print(json.dumps({"decision": payload["decision"], "payload_commitment": payload["payload_commitment"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
