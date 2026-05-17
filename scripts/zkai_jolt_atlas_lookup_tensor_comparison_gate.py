#!/usr/bin/env python3
"""Gate the Jolt/Atlas lookup-tensor comparison lane for issue #651."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import zkai_minimal_transformer_block_benchmark_gate as minimal_gate

EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
JSON_OUT = EVIDENCE_DIR / "zkai-jolt-atlas-lookup-tensor-comparison-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-jolt-atlas-lookup-tensor-comparison-2026-05.tsv"

MINIMAL_BENCHMARK = EVIDENCE_DIR / "zkai-minimal-transformer-block-benchmark-2026-05.json"
GKR_BASELINE = EVIDENCE_DIR / "zkai-gkr-dense-sidecar-baseline-2026-05.json"
STWO_COMPONENT_GRID = EVIDENCE_DIR / "zkai-attention-kv-stwo-controlled-component-grid-2026-05.json"
SOURCE_PATHS = (MINIMAL_BENCHMARK, GKR_BASELINE, STWO_COMPONENT_GRID)

SCHEMA = "zkai-jolt-atlas-lookup-tensor-comparison-v1"
DECISION = "GO_JOLT_ATLAS_SOURCE_BACKED_COMPARISON_NO_GO_LOCAL_REPRODUCTION"
RESULT = "ATLAS_REPO_AND_SOURCE_NUMBERS_EXIST_BUT_NO_MATCHED_LOCAL_PROOF_SIZE_OR_WORKLOAD"
ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/651"
PAYLOAD_DOMAIN = "ptvm:zkai:jolt-atlas-lookup-tensor-comparison:v1"

JOLT_ATLAS_REPO_HEAD = "53b7c873a6662cdc79d9818dececf337bb27d7d0"
JOLT_CORE_REPO_HEAD = "cb1e464e5d0978758900fc279a08472bfb8b518d"

PRIMARY_SOURCES = (
    {
        "label": "Jolt Atlas arXiv paper",
        "url": "https://arxiv.org/abs/2602.17452",
        "source_kind": "paper",
        "source_status": "paper_reported_not_locally_reproduced",
        "accessed_on": "2026-05-17",
        "role": "lookup-centric ONNX/tensor zkML architecture context",
    },
    {
        "label": "ICME-Lab/jolt-atlas repository",
        "url": "https://github.com/ICME-Lab/jolt-atlas",
        "source_kind": "repository",
        "source_status": "repo_available_not_locally_reproduced",
        "accessed_on": "2026-05-17",
        "head_commit": JOLT_ATLAS_REPO_HEAD,
        "role": "public implementation and README-reported benchmark commands",
    },
    {
        "label": "ICME-Lab/jolt-atlas README",
        "url": "https://raw.githubusercontent.com/ICME-Lab/jolt-atlas/main/README.md",
        "source_kind": "repository_readme",
        "source_status": "repo_reported_not_locally_reproduced",
        "accessed_on": "2026-05-17",
        "head_commit": JOLT_ATLAS_REPO_HEAD,
        "role": "source for GPT-2 and nanoGPT timing rows plus example commands",
    },
    {
        "label": "a16z/jolt repository",
        "url": "https://github.com/a16z/jolt",
        "source_kind": "repository",
        "source_status": "source_context_not_locally_reproduced",
        "accessed_on": "2026-05-17",
        "head_commit": JOLT_CORE_REPO_HEAD,
        "role": "core Jolt zkVM object-class context",
    },
    {
        "label": "Jolt memory checking and lookup docs",
        "url": "https://a16z-jolt.mintlify.app/architecture/theory/memory-checking",
        "source_kind": "documentation",
        "source_status": "source_context_not_locally_reproduced",
        "accessed_on": "2026-05-17",
        "role": "lookup and memory-checking mechanism context",
    },
)

NON_CLAIMS = (
    "not a local reproduction of Jolt Atlas",
    "not a proof-size win over Jolt Atlas",
    "not a timing win over Jolt Atlas",
    "not a matched ONNX tensor workload",
    "not a matched self-attention block benchmark",
    "not a Jolt zkVM benchmark",
    "not a NANOZK proof-size comparison",
    "not evidence that Stwo replaces lookup/sumcheck tensor systems",
    "not a claim that compact Tablero statement binding is a model proof",
)

VALIDATION_COMMANDS = (
    "python3 scripts/zkai_jolt_atlas_lookup_tensor_comparison_gate.py --write-json docs/engineering/evidence/zkai-jolt-atlas-lookup-tensor-comparison-2026-05.json --write-tsv docs/engineering/evidence/zkai-jolt-atlas-lookup-tensor-comparison-2026-05.tsv",
    "python3 -m py_compile scripts/zkai_jolt_atlas_lookup_tensor_comparison_gate.py scripts/tests/test_zkai_jolt_atlas_lookup_tensor_comparison_gate.py",
    "python3 -m unittest scripts.tests.test_zkai_jolt_atlas_lookup_tensor_comparison_gate",
    "python3 scripts/research_issue_lint.py --repo-root .",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

ROW_COLUMNS = (
    "row_id",
    "system",
    "object_class",
    "workload",
    "source_status",
    "primary_metric",
    "primary_value",
    "proof_size_status",
    "timing_status",
    "comparability",
    "evidence",
)

BASELINE_KEYS = (
    "schema",
    "decision",
    "result",
    "issue",
    "comparison_policy",
    "rows",
    "summary",
    "source_artifacts",
    "primary_sources",
    "external_reproduction_probe",
    "non_claims",
    "validation_commands",
)


class JoltAtlasComparisonError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    except (TypeError, ValueError) as err:
        raise JoltAtlasComparisonError(f"invalid JSON value: {err}") from err


def payload_commitment(payload: dict[str, Any]) -> str:
    material = copy.deepcopy(payload)
    material.pop("payload_commitment", None)
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("ascii"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return f"blake2b-256:{digest.hexdigest()}"


def source_descriptor(path: pathlib.Path, payload: dict[str, Any], raw: bytes) -> dict[str, Any]:
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


def load_source(path: pathlib.Path) -> tuple[dict[str, Any], bytes]:
    try:
        payload, raw = minimal_gate.load_json_source(path)
    except Exception as err:  # noqa: BLE001 - normalize imported gate errors.
        raise JoltAtlasComparisonError(str(err)) from err
    return payload, raw


def load_sources() -> dict[str, Any]:
    minimal, minimal_raw = load_source(MINIMAL_BENCHMARK)
    gkr, gkr_raw = load_source(GKR_BASELINE)
    grid, grid_raw = load_source(STWO_COMPONENT_GRID)
    if minimal.get("schema") != "zkai-minimal-transformer-block-benchmark-v1":
        raise JoltAtlasComparisonError("minimal benchmark schema drift")
    if gkr.get("schema") != "zkai-gkr-dense-sidecar-baseline-v1":
        raise JoltAtlasComparisonError("GKR baseline schema drift")
    if grid.get("schema") != "zkai-attention-kv-stwo-controlled-component-grid-v1":
        raise JoltAtlasComparisonError("Stwo component-grid schema drift")
    return {
        "minimal": minimal,
        "gkr": gkr,
        "grid": grid,
        "raw": {"minimal": minimal_raw, "gkr": gkr_raw, "grid": grid_raw},
    }


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise JoltAtlasComparisonError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise JoltAtlasComparisonError(f"{label} must be a list")
    return value


def require_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise JoltAtlasComparisonError(f"{label} must be an integer")
    return value


def require_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise JoltAtlasComparisonError(f"{label} must be a non-empty string")
    return value


def row_by_component(rows: list[Any], component: str) -> dict[str, Any]:
    for row in rows:
        if isinstance(row, dict) and row.get("component") == component:
            return row
    raise JoltAtlasComparisonError(f"missing component row: {component}")


def row_by_id(rows: list[Any], row_id: str) -> dict[str, Any]:
    for row in rows:
        if isinstance(row, dict) and row.get("row_id") == row_id:
            return row
    raise JoltAtlasComparisonError(f"missing row: {row_id}")


def ratio(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        raise JoltAtlasComparisonError("ratio denominator must be positive")
    return f"{numerator / denominator:.6f}"


def build_rows(sources: dict[str, Any]) -> list[dict[str, Any]]:
    minimal_summary = require_dict(sources["minimal"].get("summary"), "minimal summary")
    grid_aggregate = require_dict(sources["grid"].get("aggregate"), "Stwo grid aggregate")
    gkr_summary = require_dict(sources["gkr"].get("summary"), "GKR baseline summary")
    component_rows = require_list(sources["minimal"].get("component_rows"), "minimal component rows")
    atlas_lane = row_by_component(component_rows, "jolt_atlas_lookup_tensor_lane")
    two_proof_bytes = require_int(minimal_summary.get("two_proof_frontier_typed_bytes"), "two-proof typed bytes")
    typed_savings = require_int(grid_aggregate.get("typed_savings_bytes_total"), "Stwo grid typed savings")
    gkr_tiny_gemm = require_int(gkr_summary.get("jstprove_tiny_gemm_proof_bytes"), "GKR tiny Gemm bytes")
    return [
        {
            "row_id": "local_stwo_attention_lookup_grid",
            "system": "Stwo/STARK",
            "object_class": "local_native_stwo_attention_lookup_grid",
            "workload": "controlled fused attention plus Softmax-table LogUp profiles",
            "source_status": "local_checked",
            "primary_metric": "typed_savings_bytes_total",
            "primary_value": typed_savings,
            "proof_size_status": "local_typed_component_accounting",
            "timing_status": "no_median_timing_claim",
            "comparability": "LOCAL_MECHANISM_EVIDENCE_NOT_ONNX_TENSOR_WORKLOAD",
            "evidence": str(STWO_COMPONENT_GRID.relative_to(ROOT)),
        },
        {
            "row_id": "local_stwo_minimal_block_frontier",
            "system": "Stwo/STARK",
            "object_class": "local_two_proof_transformer_block_frontier",
            "workload": "d8 attention proof plus d128 RMSNorm-MLP fused proof",
            "source_status": "local_checked",
            "primary_metric": "two_proof_frontier_typed_bytes",
            "primary_value": two_proof_bytes,
            "proof_size_status": "local_typed_proof_field_accounting",
            "timing_status": "no_median_timing_claim",
            "comparability": "NOT_MATCHED_ATLAS_ONNX_OR_SINGLE_SELF_ATTENTION_BLOCK",
            "evidence": str(MINIMAL_BENCHMARK.relative_to(ROOT)),
        },
        {
            "row_id": "local_gkr_dense_sidecar_tiny_gemm",
            "system": "JSTprove/Remainder-GKR-sumcheck",
            "object_class": "local_external_gkr_fixture",
            "workload": "tiny Gemm projection fixture",
            "source_status": "local_checked",
            "primary_metric": "proof_bytes",
            "primary_value": gkr_tiny_gemm,
            "proof_size_status": "local_fixture_proof_bytes",
            "timing_status": "fixture_timing_only_not_paper_timing",
            "comparability": "SIDE_CAR_BASELINE_ONLY_NOT_ATLAS_OR_D128_LAYER",
            "evidence": str(GKR_BASELINE.relative_to(ROOT)),
        },
        {
            "row_id": "jolt_core_zkvm_context",
            "system": "Jolt",
            "object_class": "external_lookup_centric_riscv_zkvm",
            "workload": "RV64IMAC zkVM execution",
            "source_status": "source_context_not_locally_reproduced",
            "primary_metric": "repo_head_commit",
            "primary_value": JOLT_CORE_REPO_HEAD,
            "proof_size_status": "not_reported_in_this_gate",
            "timing_status": "not_reported_in_this_gate",
            "comparability": "CORE_ZKVM_CONTEXT_NOT_ATLAS_TENSOR_WORKLOAD",
            "evidence": "https://github.com/a16z/jolt",
        },
        {
            "row_id": "jolt_atlas_paper_architecture",
            "system": "Jolt Atlas",
            "object_class": "external_lookup_tensor_zkml_architecture",
            "workload": "ONNX tensor operations with lookup and sumcheck framing",
            "source_status": "paper_reported_not_locally_reproduced",
            "primary_metric": "architecture_class",
            "primary_value": "ONNX_LOOKUP_TENSOR_ZKML",
            "proof_size_status": "paper_context_no_local_proof_bytes",
            "timing_status": "paper_context_no_local_timing",
            "comparability": "ARCHITECTURE_CONTEXT_NOT_NUMERIC_BENCHMARK",
            "evidence": "https://arxiv.org/abs/2602.17452",
        },
        {
            "row_id": "jolt_atlas_repo_gpt2_readme",
            "system": "Jolt Atlas",
            "object_class": "external_lookup_tensor_zkml_repo_benchmark",
            "workload": "GPT-2 125M ONNX inference",
            "source_status": "repo_reported_not_locally_reproduced",
            "primary_metric": "readme_proof_time_seconds",
            "primary_value": "14.889",
            "proof_size_status": "not_reported_in_readme_row",
            "timing_status": "repo_reported_macbook_m3_16gb_not_local",
            "comparability": "TIMING_CONTEXT_ONLY_NOT_LOCAL_AND_NOT_PROOF_SIZE",
            "evidence": "https://github.com/ICME-Lab/jolt-atlas",
        },
        {
            "row_id": "jolt_atlas_repo_nanogpt_readme",
            "system": "Jolt Atlas",
            "object_class": "external_lookup_tensor_zkml_repo_benchmark",
            "workload": "nanoGPT roughly 0.25M parameters, 4 transformer layers",
            "source_status": "repo_reported_not_locally_reproduced",
            "primary_metric": "readme_proof_time_seconds",
            "primary_value": "2.288",
            "proof_size_status": "not_reported_in_readme_row",
            "timing_status": "repo_reported_macbook_m3_16gb_not_local",
            "comparability": "TIMING_CONTEXT_ONLY_NOT_LOCAL_AND_NOT_PROOF_SIZE",
            "evidence": "https://github.com/ICME-Lab/jolt-atlas",
        },
        {
            "row_id": "jolt_atlas_repo_self_attention_example",
            "system": "Jolt Atlas",
            "object_class": "external_lookup_tensor_zkml_reproduction_target",
            "workload": "single self-attention block example",
            "source_status": "repo_command_available_not_locally_reproduced",
            "primary_metric": "example_command",
            "primary_value": "cargo run --release --package jolt-atlas-core --example transformer",
            "proof_size_status": "not_reported_until_local_run",
            "timing_status": "not_reported_until_local_run",
            "comparability": require_str(atlas_lane.get("comparability"), "Atlas lane comparability"),
            "evidence": "https://github.com/ICME-Lab/jolt-atlas",
        },
    ]


def build_summary(rows: list[dict[str, Any]], sources: dict[str, Any]) -> dict[str, Any]:
    grid = row_by_id(rows, "local_stwo_attention_lookup_grid")
    frontier = row_by_id(rows, "local_stwo_minimal_block_frontier")
    gkr = row_by_id(rows, "local_gkr_dense_sidecar_tiny_gemm")
    atlas_gpt2 = row_by_id(rows, "jolt_atlas_repo_gpt2_readme")
    atlas_nanogpt = row_by_id(rows, "jolt_atlas_repo_nanogpt_readme")
    grid_bytes = require_int(grid.get("primary_value"), "grid typed savings")
    frontier_bytes = require_int(frontier.get("primary_value"), "frontier bytes")
    gkr_bytes = require_int(gkr.get("primary_value"), "GKR bytes")
    minimal_summary = require_dict(sources["minimal"].get("summary"), "minimal summary")
    if frontier_bytes != require_int(minimal_summary.get("two_proof_frontier_typed_bytes"), "minimal frontier bytes"):
        raise JoltAtlasComparisonError("minimal frontier byte drift")
    if grid_bytes != require_int(sources["grid"]["aggregate"].get("typed_savings_bytes_total"), "grid aggregate bytes"):
        raise JoltAtlasComparisonError("grid typed-savings drift")
    if gkr_bytes != require_int(sources["gkr"]["summary"].get("jstprove_tiny_gemm_proof_bytes"), "GKR summary bytes"):
        raise JoltAtlasComparisonError("GKR tiny Gemm drift")
    source_statuses = {row["source_status"] for row in rows}
    return {
        "comparison_rows": len(rows),
        "local_rows": sum(1 for row in rows if row["source_status"] == "local_checked"),
        "external_rows": sum(1 for row in rows if row["source_status"] != "local_checked"),
        "atlas_local_reproduced": False,
        "atlas_repo_available": True,
        "atlas_repo_head_commit": JOLT_ATLAS_REPO_HEAD,
        "jolt_core_repo_head_commit": JOLT_CORE_REPO_HEAD,
        "atlas_proof_size_available": False,
        "matched_atlas_workload": False,
        "matched_self_attention_block_local_run": False,
        "local_stwo_attention_lookup_typed_savings_bytes": grid_bytes,
        "local_stwo_two_proof_frontier_typed_bytes": frontier_bytes,
        "local_gkr_tiny_gemm_proof_bytes": gkr_bytes,
        "gkr_tiny_gemm_ratio_vs_stwo_two_proof_frontier": ratio(gkr_bytes, frontier_bytes),
        "atlas_readme_gpt2_proof_seconds": atlas_gpt2["primary_value"],
        "atlas_readme_nanogpt_proof_seconds": atlas_nanogpt["primary_value"],
        "source_statuses": sorted(source_statuses),
        "next_reproduction_target": "jolt-atlas transformer.rs self-attention example",
    }


def base_payload() -> dict[str, Any]:
    sources = load_sources()
    rows = build_rows(sources)
    raw_sources = require_dict(sources["raw"], "source raw inventory")
    return {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "comparison_policy": {
            "object_class_required": True,
            "workload_required": True,
            "reproduction_status_required": True,
            "proof_size_comparison_requires_matched_workload": True,
            "timing_comparison_requires_local_or_same_host_reproduction": True,
            "compact_statement_binding_not_model_proof": True,
        },
        "rows": rows,
        "summary": build_summary(rows, sources),
        "source_artifacts": [
            source_descriptor(MINIMAL_BENCHMARK, sources["minimal"], raw_sources["minimal"]),
            source_descriptor(GKR_BASELINE, sources["gkr"], raw_sources["gkr"]),
            source_descriptor(STWO_COMPONENT_GRID, sources["grid"], raw_sources["grid"]),
        ],
        "primary_sources": list(PRIMARY_SOURCES),
        "external_reproduction_probe": {
            "attempted": True,
            "date": "2026-05-17",
            "command": "git clone --depth 1 https://github.com/ICME-Lab/jolt-atlas.git /tmp/ptvm-jolt-atlas && cargo metadata --no-deps --format-version 1",
            "result": "NO_GO_BOUNDED_PROBE_INTERRUPTED_DURING_GIT_INDEX_PACK",
            "local_reproduction_status": "not_reproduced",
            "reason": "The public repo exists and exposes example commands, but the bounded local clone probe did not complete; no Atlas proof was run.",
        },
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }


def validate_payload(payload: dict[str, Any], *, require_mutations: bool = True) -> None:
    expected_keys = set(BASELINE_KEYS) | {"mutation_results", "mutation_count", "mutations_rejected", "payload_commitment"}
    if set(payload) != expected_keys:
        raise JoltAtlasComparisonError("payload key drift")
    rows = payload["rows"]
    if not isinstance(rows, list) or len(rows) != 8:
        raise JoltAtlasComparisonError("rows inventory drift")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(ROW_COLUMNS):
            raise JoltAtlasComparisonError("row schema drift")
        row_id = row["row_id"]
        if row_id in seen:
            raise JoltAtlasComparisonError("duplicate row id")
        seen.add(row_id)
        if not row["object_class"] or row["object_class"] in {"generic", "proof"}:
            raise JoltAtlasComparisonError("object-class drift")
        if row["source_status"] == "local_checked" and row["row_id"].startswith("jolt"):
            raise JoltAtlasComparisonError("external reproduction overclaim")
        if row["comparability"] in {"MATCHED_ATLAS_WIN", "STWO_BEATS_ATLAS", "PROOF_SIZE_WIN"}:
            raise JoltAtlasComparisonError("comparison overclaim")
    summary = require_dict(payload["summary"], "summary")
    if summary["atlas_local_reproduced"] is not False:
        raise JoltAtlasComparisonError("Atlas local reproduction overclaim")
    if summary["atlas_proof_size_available"] is not False:
        raise JoltAtlasComparisonError("Atlas proof-size availability overclaim")
    if summary["matched_atlas_workload"] is not False:
        raise JoltAtlasComparisonError("matched Atlas workload overclaim")
    if summary["matched_self_attention_block_local_run"] is not False:
        raise JoltAtlasComparisonError("self-attention reproduction overclaim")
    if summary["atlas_repo_head_commit"] != JOLT_ATLAS_REPO_HEAD:
        raise JoltAtlasComparisonError("Atlas repo head drift")
    if summary["jolt_core_repo_head_commit"] != JOLT_CORE_REPO_HEAD:
        raise JoltAtlasComparisonError("Jolt repo head drift")
    sources = payload["primary_sources"]
    if not isinstance(sources, list) or len(sources) != len(PRIMARY_SOURCES):
        raise JoltAtlasComparisonError("primary source inventory drift")
    if "not a local reproduction of Jolt Atlas" not in payload["non_claims"]:
        raise JoltAtlasComparisonError("non-claim drift")
    if "not a proof-size win over Jolt Atlas" not in payload["non_claims"]:
        raise JoltAtlasComparisonError("proof-size non-claim drift")
    probe = require_dict(payload["external_reproduction_probe"], "external reproduction probe")
    if probe.get("local_reproduction_status") != "not_reproduced":
        raise JoltAtlasComparisonError("external reproduction probe overclaim")
    expected = base_payload()
    for key in BASELINE_KEYS:
        if payload[key] != expected[key]:
            raise JoltAtlasComparisonError(f"{key} drift")
    if require_mutations:
        validate_mutations(payload["mutation_results"])
        if payload["mutation_count"] != len(MUTATIONS) or payload["mutations_rejected"] != len(MUTATIONS):
            raise JoltAtlasComparisonError("mutation count drift")
    else:
        if payload["mutation_results"] != [] or payload["mutation_count"] != 0 or payload["mutations_rejected"] != 0:
            raise JoltAtlasComparisonError("unexpected mutation metadata")
    if payload["payload_commitment"] != payload_commitment(payload):
        raise JoltAtlasComparisonError("payload commitment drift")


def promote_atlas_reproduced(payload: dict[str, Any]) -> None:
    payload["summary"]["atlas_local_reproduced"] = True


def promote_stwo_beats_atlas(payload: dict[str, Any]) -> None:
    payload["rows"][1]["comparability"] = "STWO_BEATS_ATLAS"


def promote_atlas_proof_size(payload: dict[str, Any]) -> None:
    payload["summary"]["atlas_proof_size_available"] = True


def mark_jolt_row_local(payload: dict[str, Any]) -> None:
    payload["rows"][5]["source_status"] = "local_checked"


def mutate_atlas_repo_head(payload: dict[str, Any]) -> None:
    payload["summary"]["atlas_repo_head_commit"] = "0" * 40


def remove_primary_source(payload: dict[str, Any]) -> None:
    payload["primary_sources"].pop()


def collapse_object_class(payload: dict[str, Any]) -> None:
    payload["rows"][7]["object_class"] = "proof"


def remove_non_claim(payload: dict[str, Any]) -> None:
    payload["non_claims"].remove("not a proof-size win over Jolt Atlas")


MUTATIONS = (
    ("atlas_reproduced_overclaim", promote_atlas_reproduced),
    ("stwo_beats_atlas_overclaim", promote_stwo_beats_atlas),
    ("atlas_proof_size_overclaim", promote_atlas_proof_size),
    ("external_row_marked_local", mark_jolt_row_local),
    ("atlas_repo_head_drift", mutate_atlas_repo_head),
    ("primary_source_removal", remove_primary_source),
    ("object_class_collapse", collapse_object_class),
    ("non_claim_removal", remove_non_claim),
)


def run_mutations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for name, mutate in MUTATIONS:
        candidate = copy.deepcopy(payload)
        mutate(candidate)
        candidate["payload_commitment"] = payload_commitment(candidate)
        try:
            validate_payload(candidate, require_mutations=False)
        except JoltAtlasComparisonError as err:
            results.append({"name": name, "rejected": True, "reason": str(err)})
        else:
            results.append({"name": name, "rejected": False, "reason": ""})
    return results


def validate_mutations(results: Any) -> None:
    if not isinstance(results, list) or len(results) != len(MUTATIONS):
        raise JoltAtlasComparisonError("mutation result drift")
    expected_names = [name for name, _mutate in MUTATIONS]
    if [entry.get("name") for entry in results if isinstance(entry, dict)] != expected_names:
        raise JoltAtlasComparisonError("mutation order drift")
    for entry in results:
        if not isinstance(entry, dict) or set(entry) != {"name", "rejected", "reason"}:
            raise JoltAtlasComparisonError("mutation entry drift")
        if entry["rejected"] is not True or not entry["reason"]:
            raise JoltAtlasComparisonError(f"mutation did not reject: {entry.get('name')}")


def build_payload() -> dict[str, Any]:
    payload = base_payload()
    payload["mutation_results"] = []
    payload["mutation_count"] = 0
    payload["mutations_rejected"] = 0
    payload["payload_commitment"] = payload_commitment(payload)
    mutations = run_mutations(payload)
    payload["mutation_results"] = mutations
    payload["mutation_count"] = len(mutations)
    payload["mutations_rejected"] = sum(1 for entry in mutations if entry["rejected"])
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload)
    return payload


def tsv_text(payload: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=ROW_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in payload["rows"]:
        writer.writerow({key: row[key] for key in ROW_COLUMNS})
    return output.getvalue()


def normalized_output_target(path: pathlib.Path) -> pathlib.Path:
    try:
        return minimal_gate.normalize_output_path(path)
    except Exception as err:  # noqa: BLE001 - keep gate-specific public error type.
        raise JoltAtlasComparisonError(str(err)) from err


def validated_output_targets(
    payload: dict[str, Any],
    json_path: pathlib.Path | None,
    tsv_path: pathlib.Path | None,
) -> tuple[pathlib.Path | None, pathlib.Path | None]:
    targets: list[tuple[str, pathlib.Path]] = []
    if json_path is not None:
        targets.append(("json", normalized_output_target(json_path)))
    if tsv_path is not None:
        targets.append(("tsv", normalized_output_target(tsv_path)))
    resolved_targets = [target for _label, target in targets]
    if len(set(resolved_targets)) != len(resolved_targets):
        raise JoltAtlasComparisonError("output paths collide")
    for label, target in targets:
        if label == "json" and target.suffix != ".json":
            raise JoltAtlasComparisonError(f"JSON output must use .json suffix: {target}")
        if label == "tsv" and target.suffix != ".tsv":
            raise JoltAtlasComparisonError(f"TSV output must use .tsv suffix: {target}")
    source_paths = {path.resolve() for path in SOURCE_PATHS}
    source_paths |= {
        (ROOT / artifact["path"]).resolve()
        for artifact in payload.get("source_artifacts", [])
        if isinstance(artifact, dict) and isinstance(artifact.get("path"), str)
    }
    for label, target in targets:
        if target in source_paths:
            raise JoltAtlasComparisonError(f"refusing to overwrite source artifact with {label} output: {target}")
    output_by_label = dict(targets)
    return output_by_label.get("json"), output_by_label.get("tsv")


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path | None, tsv_path: pathlib.Path | None) -> None:
    json_target, tsv_target = validated_output_targets(payload, json_path, tsv_path)
    if json_target:
        minimal_gate.write_atomic(json_target, json.dumps(payload, indent=2, sort_keys=True).encode() + b"\n")
    if tsv_target:
        minimal_gate.write_atomic(tsv_target, tsv_text(payload).encode())


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
                "rows": len(payload["rows"]),
                "mutations_rejected": payload["mutations_rejected"],
                "atlas_local_reproduced": payload["summary"]["atlas_local_reproduced"],
                "atlas_proof_size_available": payload["summary"]["atlas_proof_size_available"],
                "atlas_readme_gpt2_proof_seconds": payload["summary"]["atlas_readme_gpt2_proof_seconds"],
                "atlas_readme_nanogpt_proof_seconds": payload["summary"]["atlas_readme_nanogpt_proof_seconds"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
