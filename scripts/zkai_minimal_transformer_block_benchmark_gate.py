#!/usr/bin/env python3
"""Gate the minimal transformer-block benchmark contract."""

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
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
JSON_OUT = EVIDENCE_DIR / "zkai-minimal-transformer-block-benchmark-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-minimal-transformer-block-benchmark-2026-05.tsv"
MAX_SOURCE_BYTES = 32 * 1024 * 1024

ONE_BLOCK_SURFACE = EVIDENCE_DIR / "zkai-one-transformer-block-surface-2026-05.json"
BOUNDARY_FRONTIER = EVIDENCE_DIR / "zkai-d128-attention-mlp-boundary-frontier-2026-05.json"
ADJACENT_LAYOUT = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-adjacent-layout-2026-05.json"
MATCHED_TABLE = EVIDENCE_DIR / "zkai-matched-d64-d128-evidence-table-2026-05.json"

SCHEMA = "zkai-minimal-transformer-block-benchmark-v1"
DECISION = "GO_MINIMAL_BLOCK_BENCHMARK_CONTRACT_NO_GO_MATCHED_PROOF_CLAIM"
RESULT = "BENCHMARK_CONTRACT_READY_MISSING_NATIVE_BLOCK_PROOF_OBJECT"
ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/649"
PAYLOAD_DOMAIN = "ptvm:zkai:minimal-transformer-block-benchmark:v1"
CLAIM_BOUNDARY = (
    "MINIMAL_TRANSFORMER_BLOCK_BENCHMARK_CONTRACT_WITH_EXPLICIT_OBJECT_CLASSES_"
    "NO_MATCHED_EXTERNAL_WIN_NO_NATIVE_FULL_BLOCK_PROOF"
)

NON_CLAIMS = (
    "not a full LLM proof",
    "not production zkML",
    "not exact real-valued Softmax",
    "not exact LayerNorm",
    "not exact GELU",
    "not a NANOZK proof-size win",
    "not a Jolt or Atlas benchmark win",
    "not a GKR or Hyrax implementation",
    "not timing evidence",
    "not recursion or proof-carrying data",
)

VALIDATION_COMMANDS = (
    "python3 scripts/zkai_minimal_transformer_block_benchmark_gate.py --write-json docs/engineering/evidence/zkai-minimal-transformer-block-benchmark-2026-05.json --write-tsv docs/engineering/evidence/zkai-minimal-transformer-block-benchmark-2026-05.tsv",
    "python3 -m py_compile scripts/zkai_minimal_transformer_block_benchmark_gate.py scripts/tests/test_zkai_minimal_transformer_block_benchmark_gate.py",
    "python3 -m unittest scripts.tests.test_zkai_minimal_transformer_block_benchmark_gate",
    "python3 scripts/research_issue_lint.py --repo-root .",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

TSV_COLUMNS = (
    "component",
    "object_class",
    "local_status",
    "proof_system",
    "evidence_path",
    "primary_metric",
    "primary_value",
    "comparability",
    "claim_boundary",
)

BASELINE_KEYS = (
    "schema",
    "decision",
    "result",
    "issue",
    "claim_boundary",
    "benchmark_spec",
    "component_rows",
    "comparison_policy",
    "summary",
    "source_artifacts",
    "non_claims",
    "validation_commands",
)


class MinimalBlockBenchmarkError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode(
            "utf-8"
        )
    except (TypeError, ValueError) as err:
        raise MinimalBlockBenchmarkError(f"invalid JSON value: {err}") from err


def payload_commitment(payload: dict[str, Any]) -> str:
    material = copy.deepcopy(payload)
    material.pop("payload_commitment", None)
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("ascii"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return f"blake2b-256:{digest.hexdigest()}"


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _reject_duplicate_json_keys(items: list[tuple[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in items:
        if key in payload:
            raise ValueError(f"duplicate JSON key: {key}")
        payload[key] = value
    return payload


def read_source_bytes(path: pathlib.Path) -> bytes:
    root = ROOT.resolve()
    candidate = pathlib.Path(os.path.abspath(path if path.is_absolute() else ROOT / path))
    try:
        relative = candidate.relative_to(root)
    except ValueError as err:
        raise MinimalBlockBenchmarkError(f"source path outside repository: {path}") from err
    current = root
    pre_stat = None
    try:
        for part in relative.parts:
            current = current / part
            part_stat = current.lstat()
            if stat.S_ISLNK(part_stat.st_mode):
                raise MinimalBlockBenchmarkError(f"source path traverses symlink: {path}")
            pre_stat = part_stat
        if pre_stat is None or not stat.S_ISREG(pre_stat.st_mode):
            raise MinimalBlockBenchmarkError(f"source path is not a regular file: {path}")
        fd = os.open(candidate, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            post_stat = os.fstat(fd)
            if (post_stat.st_dev, post_stat.st_ino) != (pre_stat.st_dev, pre_stat.st_ino):
                raise MinimalBlockBenchmarkError(f"source changed while reading: {path}")
            opened_fingerprint = (
                post_stat.st_dev,
                post_stat.st_ino,
                post_stat.st_size,
                post_stat.st_mtime_ns,
                post_stat.st_ctime_ns,
            )
            with os.fdopen(fd, "rb") as handle:
                fd = None
                raw = handle.read(MAX_SOURCE_BYTES + 1)
                final_stat = os.fstat(handle.fileno())
                final_fingerprint = (
                    final_stat.st_dev,
                    final_stat.st_ino,
                    final_stat.st_size,
                    final_stat.st_mtime_ns,
                    final_stat.st_ctime_ns,
                )
                if final_fingerprint != opened_fingerprint:
                    raise MinimalBlockBenchmarkError(f"source changed while reading: {path}")
        finally:
            if fd is not None:
                os.close(fd)
    except OSError as err:
        raise MinimalBlockBenchmarkError(f"failed to read source {path}: {err}") from err
    if len(raw) > MAX_SOURCE_BYTES:
        raise MinimalBlockBenchmarkError(f"source too large: {path}")
    return raw


def load_json(path: pathlib.Path) -> dict[str, Any]:
    raw = read_source_bytes(path)
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            parse_constant=_reject_json_constant,
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as err:
        raise MinimalBlockBenchmarkError(f"failed to parse JSON source {path}: {err}") from err
    if not isinstance(payload, dict):
        raise MinimalBlockBenchmarkError(f"JSON source must be object: {path}")
    return payload


def source_descriptor(path: pathlib.Path, payload: dict[str, Any]) -> dict[str, Any]:
    raw = read_source_bytes(path)
    descriptor = {
        "path": str(path.relative_to(ROOT)),
        "file_sha256": hashlib.sha256(raw).hexdigest(),
        "payload_sha256": hashlib.sha256(canonical_json_bytes(payload)).hexdigest(),
    }
    if isinstance(payload.get("schema"), str):
        descriptor["schema"] = payload["schema"]
    if isinstance(payload.get("decision"), str):
        descriptor["decision"] = payload["decision"]
    return descriptor


def _dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MinimalBlockBenchmarkError(f"{label} must be an object")
    return value


def _int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise MinimalBlockBenchmarkError(f"{label} must be an integer")
    return value


def _load_sources() -> dict[str, dict[str, Any]]:
    one_block = load_json(ONE_BLOCK_SURFACE)
    frontier = load_json(BOUNDARY_FRONTIER)
    adjacent = load_json(ADJACENT_LAYOUT)
    matched = load_json(MATCHED_TABLE)
    if one_block.get("schema") != "zkai-one-transformer-block-surface-v1":
        raise MinimalBlockBenchmarkError("one-block surface schema drift")
    if frontier.get("schema") != "zkai-d128-attention-mlp-boundary-frontier-gate-v1":
        raise MinimalBlockBenchmarkError("frontier schema drift")
    if adjacent.get("schema") != "zkai-native-attention-mlp-rmsnorm-adjacent-layout-gate-v1":
        raise MinimalBlockBenchmarkError("adjacent layout schema drift")
    if matched.get("schema") != "zkai-matched-d64-d128-evidence-table-v1":
        raise MinimalBlockBenchmarkError("matched table schema drift")
    return {
        "one_block": one_block,
        "frontier": frontier,
        "adjacent": adjacent,
        "matched": matched,
    }


def _benchmark_spec() -> dict[str, Any]:
    return {
        "benchmark_id": "minimal_attention_derived_d128_transformer_block_v1",
        "model_width": 128,
        "attention_source_width": 8,
        "ffn_width": 512,
        "sequence_policy": "bounded local fixtures only; not full autoregressive inference",
        "component_contract": [
            "attention boundary",
            "Softmax-table lookup membership",
            "RMSNorm substitute for LayerNorm",
            "gate/value projection",
            "bounded SiLU/SwiGLU activation substitute for GELU",
            "down projection",
            "residual boundary",
            "typed public statement",
        ],
        "approximation_policy": {
            "attention": "bounded Softmax-table / LogUp fixture, not exact real-valued Softmax",
            "normalization": "RMSNorm substitute, not exact LayerNorm",
            "activation": "bounded SiLU/SwiGLU substitute, not exact GELU",
            "quantization": "integer/field-bounded fixtures; model-faithful accuracy bridge is missing",
        },
        "public_statement_bindings": [
            "model_artifact_commitment",
            "input_activation_commitment",
            "attention_output_commitment",
            "block_output_commitment",
            "proof_commitment_or_receipt_commitment",
            "object_class",
        ],
    }


def _component_rows(sources: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    one_block = sources["one_block"]
    frontier = sources["frontier"]
    adjacent = sources["adjacent"]
    one_summary = _dict(one_block.get("summary"), "one-block summary")
    frontier_summary = _dict(frontier.get("summary"), "frontier summary")
    adjacent_variants = _dict(adjacent.get("variants"), "adjacent variants")
    adjacent_layout = _dict(adjacent_variants.get("adjacent_layout"), "adjacent layout variant")
    adjacent_bad = _dict(adjacent_variants.get("adjacent_label_probe_b"), "adjacent label probe B")
    return [
        {
            "component": "attention_boundary_and_softmax_lookup",
            "object_class": "local_native_stwo_proof_component",
            "local_status": "GO_EXISTING_COMPONENT_PROOF_NOT_FULL_BLOCK",
            "proof_system": "Stwo/STARK",
            "evidence_path": str(BOUNDARY_FRONTIER.relative_to(ROOT)),
            "primary_metric": "attention_fused_typed_bytes",
            "primary_value": _int(frontier_summary.get("attention_fused_typed_bytes"), "attention fused typed bytes"),
            "comparability": "LOCAL_COMPONENT_ONLY_NOT_MATCHED_EXTERNAL_BENCHMARK",
            "claim_boundary": "attention arithmetic and lookup membership surface only",
        },
        {
            "component": "rmsnorm_mlp_residual_substitute",
            "object_class": "local_native_stwo_proof_component",
            "local_status": "GO_DERIVED_D128_RMSNORM_MLP_FUSED_COMPONENT",
            "proof_system": "Stwo/STARK",
            "evidence_path": str(BOUNDARY_FRONTIER.relative_to(ROOT)),
            "primary_metric": "derived_mlp_fused_typed_bytes",
            "primary_value": _int(frontier_summary.get("derived_mlp_fused_typed_bytes"), "derived MLP typed bytes"),
            "comparability": "RMSNORM_SWIGLU_SUBSTITUTE_NOT_EXACT_LAYER_NORM_GELU",
            "claim_boundary": "RMSNorm/SwiGLU/down/residual substitute surface, not exact transformer layer semantics",
        },
        {
            "component": "attention_to_d128_adapter_layout",
            "object_class": "local_native_stwo_proof_object_attempt",
            "local_status": "NO_GO_WORST_LABEL_FRONTIER_PROMOTION",
            "proof_system": "Stwo/STARK",
            "evidence_path": str(ADJACENT_LAYOUT.relative_to(ROOT)),
            "primary_metric": "adjacent_worst_label_typed_bytes",
            "primary_value": _int(adjacent_bad.get("typed_bytes"), "adjacent worst label typed bytes"),
            "comparability": "PROOF_OBJECT_ATTEMPT_STILL_ABOVE_TWO_PROOF_FRONTIER",
            "claim_boundary": "real layout lever; fails worst-label policy by 2,024 typed bytes",
        },
        {
            "component": "two_proof_frontier",
            "object_class": "local_two_proof_target",
            "local_status": "GO_CURRENT_COMPARISON_FRONTIER_NOT_ONE_PROOF",
            "proof_system": "Stwo/STARK",
            "evidence_path": str(BOUNDARY_FRONTIER.relative_to(ROOT)),
            "primary_metric": "two_proof_frontier_typed_bytes",
            "primary_value": _int(frontier_summary.get("two_proof_frontier_typed_bytes"), "two-proof frontier"),
            "comparability": "INTERNAL_FRONTIER_ONLY",
            "claim_boundary": "current honest frontier is two proof objects, not one block proof",
        },
        {
            "component": "typed_public_statement_chain",
            "object_class": "local_statement_artifact",
            "local_status": "GO_STATEMENT_BOUNDARY_NOT_PROOF_OBJECT",
            "proof_system": "statement artifact",
            "evidence_path": str(ONE_BLOCK_SURFACE.relative_to(ROOT)),
            "primary_metric": "statement_chain_rows",
            "primary_value": _int(
                one_summary.get("attention_derived_d128_statement_chain_rows"), "statement chain rows"
            ),
            "comparability": "STATEMENT_VALIDITY_SURFACE_NOT_PROOF_SIZE_ROW",
            "claim_boundary": "binds the object to a statement chain; does not prove the whole block natively",
        },
        {
            "component": "external_statement_receipt",
            "object_class": "external_snark_statement_receipt",
            "local_status": "GO_EXECUTABLE_STATEMENT_RECEIPT_NOT_STARK_NATIVE_BLOCK_PROOF",
            "proof_system": "Groth16/SNARK",
            "evidence_path": str(ONE_BLOCK_SURFACE.relative_to(ROOT)),
            "primary_metric": "external_receipt_proof_bytes",
            "primary_value": _int(
                one_summary.get("attention_derived_d128_snark_receipt_proof_bytes"), "SNARK receipt proof bytes"
            ),
            "comparability": "EXTERNAL_RECEIPT_NOT_NATIVE_STARK_PROOF",
            "claim_boundary": "useful verifier-facing package signal; not the STARK-native benchmark row",
        },
        {
            "component": "native_full_block_proof_object",
            "object_class": "missing_native_proof_object",
            "local_status": "NO_GO_NATIVE_BLOCK_PROOF_OBJECT_MISSING",
            "proof_system": "Stwo/STARK",
            "evidence_path": "",
            "primary_metric": "native_block_proof_bytes",
            "primary_value": None,
            "comparability": "REQUIRED_BEFORE_NANOZK_OR_JOLT_PROOF_SIZE_COMPARISON",
            "claim_boundary": "missing object; benchmark cannot claim matched proof-size or timing",
        },
        {
            "component": "nanozk_context_row",
            "object_class": "paper_reported_external_context",
            "local_status": "SOURCE_BACKED_CONTEXT_ONLY",
            "proof_system": "paper-reported",
            "evidence_path": str(BOUNDARY_FRONTIER.relative_to(ROOT)),
            "primary_metric": "reported_proof_size_bytes",
            "primary_value": _int(frontier_summary.get("nanozk_reported_d128_block_proof_bytes"), "NANOZK bytes"),
            "comparability": "CONTEXT_ONLY_NOT_LOCAL_REPRODUCTION_NOT_MATCHED_WORKLOAD",
            "claim_boundary": "paper-reported context only",
        },
        {
            "component": "gkr_hyrax_sidecar_lane",
            "object_class": "followup_hypothesis",
            "local_status": "FOLLOWUP_ISSUE_650_NOT_IMPLEMENTED",
            "proof_system": "GKR/Hyrax candidate",
            "evidence_path": "https://github.com/omarespejel/provable-transformer-vm/issues/650",
            "primary_metric": "implemented",
            "primary_value": False,
            "comparability": "NOT_IMPLEMENTED_BASELINE",
            "claim_boundary": "exploratory dense-layer sidecar lane only",
        },
        {
            "component": "jolt_atlas_lookup_tensor_lane",
            "object_class": "followup_hypothesis",
            "local_status": "FOLLOWUP_ISSUE_651_NOT_IMPLEMENTED",
            "proof_system": "Jolt/Atlas candidate",
            "evidence_path": "https://github.com/omarespejel/provable-transformer-vm/issues/651",
            "primary_metric": "implemented",
            "primary_value": False,
            "comparability": "NOT_IMPLEMENTED_BASELINE",
            "claim_boundary": "exploratory lookup/tensor comparison lane only",
        },
    ]


def _comparison_policy() -> dict[str, Any]:
    return {
        "matched_external_comparison_requires": [
            "same block semantics",
            "same dimensions or an explicit scaling model",
            "same object class",
            "source-backed or locally reproduced external numbers",
            "proof-size accounting policy",
            "median-of-5 timing policy before time claims",
        ],
        "allowed_now": [
            "internal frontier comparisons",
            "source-backed external context",
            "object-class gap accounting",
            "follow-up issue generation",
        ],
        "forbidden_now": [
            "NANOZK win",
            "Jolt or Atlas win",
            "full transformer-block proof claim",
            "timing claim",
            "model-faithful accuracy claim",
        ],
    }


def _base_payload() -> dict[str, Any]:
    sources = _load_sources()
    frontier_summary = _dict(sources["frontier"].get("summary"), "frontier summary")
    one_summary = _dict(sources["one_block"].get("summary"), "one-block summary")
    adjacent = sources["adjacent"]
    component_rows = _component_rows(sources)
    source_artifacts = [
        source_descriptor(ONE_BLOCK_SURFACE, sources["one_block"]),
        source_descriptor(BOUNDARY_FRONTIER, sources["frontier"]),
        source_descriptor(ADJACENT_LAYOUT, sources["adjacent"]),
        source_descriptor(MATCHED_TABLE, sources["matched"]),
    ]
    summary = {
        "component_count": len(component_rows),
        "proof_component_count": sum(1 for row in component_rows if "proof_component" in row["object_class"]),
        "missing_native_block_proof_object": True,
        "two_proof_frontier_typed_bytes": _int(frontier_summary.get("two_proof_frontier_typed_bytes"), "frontier"),
        "adjacent_layout_canonical_typed_bytes": _int(adjacent.get("adjacent_canonical_typed_bytes"), "adjacent"),
        "adjacent_worst_label_typed_bytes": _int(adjacent.get("adjacent_worst_label_typed_bytes"), "worst label"),
        "adjacent_worst_label_gap_typed_bytes": _int(
            adjacent.get("adjacent_worst_label_delta_vs_frontier_typed_bytes"), "worst label gap"
        ),
        "statement_chain_rows": _int(
            one_summary.get("attention_derived_d128_statement_chain_rows"), "statement rows"
        ),
        "external_statement_receipt_proof_bytes": _int(
            one_summary.get("attention_derived_d128_snark_receipt_proof_bytes"), "receipt bytes"
        ),
        "nanozk_reported_d128_block_proof_bytes": _int(
            frontier_summary.get("nanozk_reported_d128_block_proof_bytes"), "NANOZK bytes"
        ),
        "gap_to_nanozk_from_two_proof_frontier_typed_bytes": _int(
            frontier_summary.get("typed_gap_to_nanozk_reported_bytes"), "NANOZK gap"
        ),
    }
    return {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "claim_boundary": CLAIM_BOUNDARY,
        "benchmark_spec": _benchmark_spec(),
        "component_rows": component_rows,
        "comparison_policy": _comparison_policy(),
        "summary": summary,
        "source_artifacts": source_artifacts,
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
        "mutation_results": [],
        "mutation_count": 0,
        "mutations_rejected": 0,
        "payload_commitment": "",
    }


def build_payload(*, include_mutations: bool = True) -> dict[str, Any]:
    payload = _base_payload()
    payload["payload_commitment"] = payload_commitment(payload)
    if include_mutations:
        payload["mutation_results"] = run_mutations(payload)
        payload["mutation_count"] = len(payload["mutation_results"])
        payload["mutations_rejected"] = sum(1 for entry in payload["mutation_results"] if entry["rejected"])
        payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload, require_mutations=include_mutations)
    return payload


def validate_payload(payload: dict[str, Any], *, require_mutations: bool = True) -> None:
    expected_keys = set(BASELINE_KEYS) | {"mutation_results", "mutation_count", "mutations_rejected", "payload_commitment"}
    if set(payload) != expected_keys:
        raise MinimalBlockBenchmarkError("payload key drift")
    expected = _base_payload()
    for key in BASELINE_KEYS:
        if key == "component_rows":
            continue
        if payload[key] != expected[key]:
            raise MinimalBlockBenchmarkError(f"{key} drift")
    rows = payload["component_rows"]
    if not isinstance(rows, list) or len(rows) != 10:
        raise MinimalBlockBenchmarkError("component row inventory drift")
    expected_row_keys = set(TSV_COLUMNS)
    component_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise MinimalBlockBenchmarkError("component row must be an object")
        if set(row) != expected_row_keys:
            raise MinimalBlockBenchmarkError("component row key drift")
        if not isinstance(row["component"], str) or not row["component"]:
            raise MinimalBlockBenchmarkError("component row name drift")
        component_rows.append(row)
    if any(row["comparability"] == "MATCHED_EXTERNAL_BENCHMARK" for row in component_rows):
        raise MinimalBlockBenchmarkError("external comparability overclaim")
    native_row = next((row for row in component_rows if row["component"] == "native_full_block_proof_object"), None)
    if native_row is None:
        raise MinimalBlockBenchmarkError("native_full_block_proof_object row missing")
    if native_row["object_class"] != "missing_native_proof_object" or native_row["primary_value"] is not None:
        raise MinimalBlockBenchmarkError("native block proof object overclaim")
    if payload["summary"]["missing_native_block_proof_object"] is not True:
        raise MinimalBlockBenchmarkError("missing native block summary drift")
    if payload["summary"]["adjacent_worst_label_gap_typed_bytes"] <= 0:
        raise MinimalBlockBenchmarkError("worst-label frontier overclaim")
    if component_rows != expected["component_rows"]:
        raise MinimalBlockBenchmarkError("component_rows drift")
    approximation_policy = payload["benchmark_spec"]["approximation_policy"]
    for required in ("attention", "normalization", "activation", "quantization"):
        if required not in approximation_policy:
            raise MinimalBlockBenchmarkError("approximation policy drift")
    if tuple(payload["non_claims"]) != NON_CLAIMS:
        raise MinimalBlockBenchmarkError("non-claims drift")
    if tuple(payload["validation_commands"]) != VALIDATION_COMMANDS:
        raise MinimalBlockBenchmarkError("validation commands drift")
    if require_mutations:
        validate_mutations(payload["mutation_results"])
        if payload["mutation_count"] != len(MUTATIONS) or payload["mutations_rejected"] != len(MUTATIONS):
            raise MinimalBlockBenchmarkError("mutation count drift")
    else:
        if payload["mutation_results"] != [] or payload["mutation_count"] != 0 or payload["mutations_rejected"] != 0:
            raise MinimalBlockBenchmarkError("unexpected mutation metadata")
    if payload["payload_commitment"] != payload_commitment(payload):
        raise MinimalBlockBenchmarkError("payload commitment drift")


def row_by_component(payload: dict[str, Any], component: str) -> dict[str, Any]:
    for row in payload["component_rows"]:
        if row.get("component") == component:
            return row
    raise MinimalBlockBenchmarkError(f"component row missing: {component}")


def remove_row_by_component(payload: dict[str, Any], component: str) -> None:
    payload["component_rows"] = [row for row in payload["component_rows"] if row.get("component") != component]


def source_by_path(payload: dict[str, Any], path: pathlib.Path) -> dict[str, Any]:
    expected_path = str(path.relative_to(ROOT))
    for artifact in payload["source_artifacts"]:
        if artifact.get("path") == expected_path:
            return artifact
    raise MinimalBlockBenchmarkError(f"source artifact missing: {expected_path}")


def promote_native_block_proof(payload: dict[str, Any]) -> None:
    row_by_component(payload, "native_full_block_proof_object").update(
        {"object_class": "local_native_stwo_proof_object", "primary_value": 6900}
    )


MUTATIONS = (
    ("component_omitted", lambda p: remove_row_by_component(p, "attention_boundary_and_softmax_lookup")),
    ("native_block_proof_promoted", promote_native_block_proof),
    ("approximation_policy_removed", lambda p: p["benchmark_spec"].__setitem__("approximation_policy", {})),
    (
        "nanozk_marked_matched",
        lambda p: row_by_component(p, "nanozk_context_row").__setitem__(
            "comparability", "MATCHED_EXTERNAL_BENCHMARK"
        ),
    ),
    ("source_digest_drift", lambda p: source_by_path(p, ONE_BLOCK_SURFACE).__setitem__("file_sha256", "0" * 64)),
    ("non_claim_removed", lambda p: p.__setitem__("non_claims", p["non_claims"][:-1])),
    ("statement_binding_removed", lambda p: p["benchmark_spec"].__setitem__("public_statement_bindings", [])),
    ("gkr_lane_hidden", lambda p: remove_row_by_component(p, "gkr_hyrax_sidecar_lane")),
    ("jolt_lane_hidden", lambda p: remove_row_by_component(p, "jolt_atlas_lookup_tensor_lane")),
    ("two_proof_frontier_reduced", lambda p: p["summary"].__setitem__("two_proof_frontier_typed_bytes", 6900)),
    ("worst_label_gap_zeroed", lambda p: p["summary"].__setitem__("adjacent_worst_label_gap_typed_bytes", 0)),
    ("validation_commands_erased", lambda p: p.__setitem__("validation_commands", [])),
    ("issue_link_drift", lambda p: p.__setitem__("issue", "https://github.com/omarespejel/provable-transformer-vm/issues/650")),
    ("payload_commitment_drift", lambda p: p.__setitem__("payload_commitment", "blake2b-256:" + "0" * 64)),
)


def run_mutations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    clean = copy.deepcopy(payload)
    clean["mutation_results"] = []
    clean["mutation_count"] = 0
    clean["mutations_rejected"] = 0
    clean["payload_commitment"] = payload_commitment(clean)
    results = []
    for name, mutator in MUTATIONS:
        mutated = copy.deepcopy(clean)
        mutator(mutated)
        if name != "payload_commitment_drift":
            mutated["payload_commitment"] = payload_commitment(mutated)
        try:
            validate_payload(mutated, require_mutations=False)
        except MinimalBlockBenchmarkError as err:
            results.append({"name": name, "rejected": True, "reason": str(err)})
        else:
            results.append({"name": name, "rejected": False, "reason": ""})
    return results


def validate_mutations(results: Any) -> None:
    if not isinstance(results, list) or len(results) != len(MUTATIONS):
        raise MinimalBlockBenchmarkError("mutation inventory drift")
    names = [entry.get("name") for entry in results if isinstance(entry, dict)]
    if names != [name for name, _ in MUTATIONS]:
        raise MinimalBlockBenchmarkError("mutation name drift")
    for entry in results:
        if not isinstance(entry, dict) or set(entry) != {"name", "rejected", "reason"}:
            raise MinimalBlockBenchmarkError("mutation entry drift")
        if entry["rejected"] is not True or not entry["reason"]:
            raise MinimalBlockBenchmarkError(f"mutation did not reject: {entry.get('name')}")


def tsv_text(payload: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in payload["component_rows"]:
        writer.writerow({key: row[key] for key in TSV_COLUMNS})
    return output.getvalue()


def normalize_output_path(path: pathlib.Path) -> pathlib.Path:
    if not path.is_absolute():
        path = ROOT / path
    try:
        original_st = os.lstat(path)
    except FileNotFoundError:
        pass
    else:
        if stat.S_ISLNK(original_st.st_mode):
            raise MinimalBlockBenchmarkError(f"refusing to write through symlink: {path}")
        if not stat.S_ISREG(original_st.st_mode):
            raise MinimalBlockBenchmarkError(f"output path is not a regular file: {path}")
    resolved = path.resolve()
    evidence_root = EVIDENCE_DIR.resolve()
    if evidence_root != resolved and evidence_root not in resolved.parents:
        raise MinimalBlockBenchmarkError(f"output path outside evidence dir: {path}")
    return resolved


def write_atomic(path: pathlib.Path, data: bytes) -> None:
    target = normalize_output_path(path)
    if target.suffix not in {".json", ".tsv"}:
        raise MinimalBlockBenchmarkError(f"unsupported output suffix: {target}")
    tmp = target.with_name(f".{target.name}.{secrets.token_hex(8)}.tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, target)
    except Exception:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def validated_output_targets(
    payload: dict[str, Any],
    json_path: pathlib.Path | None,
    tsv_path: pathlib.Path | None,
) -> tuple[pathlib.Path | None, pathlib.Path | None]:
    targets: list[tuple[str, pathlib.Path]] = []
    if json_path is not None:
        json_target = normalize_output_path(json_path)
        targets.append(("json", json_target))
    if tsv_path is not None:
        tsv_target = normalize_output_path(tsv_path)
        targets.append(("tsv", tsv_target))
    resolved_targets = [target for _label, target in targets]
    if len(set(resolved_targets)) != len(resolved_targets):
        raise MinimalBlockBenchmarkError("output paths collide")
    for label, target in targets:
        if label == "json" and target.suffix != ".json":
            raise MinimalBlockBenchmarkError(f"JSON output must use .json suffix: {target}")
        if label == "tsv" and target.suffix != ".tsv":
            raise MinimalBlockBenchmarkError(f"TSV output must use .tsv suffix: {target}")
    source_paths = {
        (ROOT / artifact["path"]).resolve()
        for artifact in payload.get("source_artifacts", [])
        if isinstance(artifact, dict) and isinstance(artifact.get("path"), str)
    }
    for label, target in targets:
        if target in source_paths:
            raise MinimalBlockBenchmarkError(f"refusing to overwrite source artifact with {label} output: {target}")
    output_by_label = dict(targets)
    return output_by_label.get("json"), output_by_label.get("tsv")


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path | None, tsv_path: pathlib.Path | None) -> None:
    json_target, tsv_target = validated_output_targets(payload, json_path, tsv_path)
    if json_target:
        write_atomic(json_target, json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    if tsv_target:
        write_atomic(tsv_target, tsv_text(payload).encode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    args = parser.parse_args()
    payload = build_payload()
    write_outputs(payload, args.write_json, args.write_tsv)
    print(
        json.dumps(
            {
                "decision": payload["decision"],
                "result": payload["result"],
                "component_count": payload["summary"]["component_count"],
                "two_proof_frontier_typed_bytes": payload["summary"]["two_proof_frontier_typed_bytes"],
                "native_full_block_proof_object": "missing",
                "mutation_count": payload["mutation_count"],
                "mutations_rejected": payload["mutations_rejected"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
