#!/usr/bin/env python3
"""Gate Tablero typed boundaries for hybrid zkML proof objects."""

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
JSON_OUT = EVIDENCE_DIR / "zkai-tablero-hybrid-zkml-boundary-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-tablero-hybrid-zkml-boundary-2026-05.tsv"

MINIMAL_BENCHMARK = EVIDENCE_DIR / "zkai-minimal-transformer-block-benchmark-2026-05.json"
GKR_BASELINE = EVIDENCE_DIR / "zkai-gkr-dense-sidecar-baseline-2026-05.json"
JOLT_ATLAS_COMPARISON = EVIDENCE_DIR / "zkai-jolt-atlas-lookup-tensor-comparison-2026-05.json"
JSTPROVE_STATEMENT_ENVELOPE = EVIDENCE_DIR / "zkai-jstprove-statement-envelope-benchmark-2026-05.json"
SOURCE_PATHS = (MINIMAL_BENCHMARK, GKR_BASELINE, JOLT_ATLAS_COMPARISON, JSTPROVE_STATEMENT_ENVELOPE)

SCHEMA = "zkai-tablero-hybrid-zkml-boundary-v1"
BOUNDARY_SCHEMA = "tablero-hybrid-zkml-typed-statement-v1"
DECISION = "GO_TABLERO_TYPED_BOUNDARIES_FOR_HYBRID_ZKML_OBJECTS"
RESULT = "TYPED_BOUNDARY_SCHEMA_REJECTS_HYBRID_OBJECT_CLASS_CONFUSION"
ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/652"
PAYLOAD_DOMAIN = "ptvm:zkai:tablero-hybrid-zkml-boundary:v1"
BOUNDARY_DOMAIN = "ptvm:zkai:tablero-hybrid-zkml-typed-statement:v1"

REQUIRED_BINDING_FIELDS = (
    "statement_id",
    "statement_schema",
    "object_class",
    "proof_system",
    "backend",
    "backend_version",
    "workload",
    "source_status",
    "model_binding",
    "input_binding",
    "output_binding",
    "proof_object_binding",
    "approximation_policy",
    "quantization_policy",
    "verifier_semantics",
    "proof_size_policy",
    "timing_policy",
    "native_proof_equivalent",
    "non_claims",
)

BINDING_OBJECT_FIELDS = ("availability", "commitment", "source", "reason")

NON_CLAIMS = (
    "not a recursive composition proof",
    "not a claim that Tablero verifies external proofs itself",
    "not a claim that a statement receipt proves underlying native verifier execution",
    "not a proof-size win over NANOZK",
    "not a proof-size win over Jolt Atlas",
    "not a local Jolt Atlas reproduction",
    "not a full transformer block proof",
    "not exact real-valued transformer arithmetic",
)

VALIDATION_COMMANDS = (
    "python3 scripts/zkai_tablero_hybrid_zkml_boundary_gate.py --write-json docs/engineering/evidence/zkai-tablero-hybrid-zkml-boundary-2026-05.json --write-tsv docs/engineering/evidence/zkai-tablero-hybrid-zkml-boundary-2026-05.tsv",
    "python3 -m py_compile scripts/zkai_tablero_hybrid_zkml_boundary_gate.py scripts/tests/test_zkai_tablero_hybrid_zkml_boundary_gate.py",
    "python3 -m unittest scripts.tests.test_zkai_tablero_hybrid_zkml_boundary_gate",
    "python3 scripts/research_issue_lint.py --repo-root .",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

ROW_COLUMNS = (
    "statement_id",
    "object_class",
    "proof_system",
    "backend",
    "source_status",
    "primary_metric",
    "primary_value",
    "native_proof_equivalent",
    "proof_size_policy",
    "timing_policy",
    "claim_boundary",
)

BASELINE_KEYS = (
    "schema",
    "decision",
    "result",
    "issue",
    "typed_statement_schema",
    "boundary_examples",
    "summary",
    "source_artifacts",
    "non_claims",
    "validation_commands",
)

PINNED_BOUNDARY_CONTRACT_FIELDS = (
    "statement_id",
    "object_class",
    "proof_system",
    "backend",
    "backend_version",
    "workload",
    "source_status",
    "approximation_policy",
    "quantization_policy",
    "verifier_semantics",
    "proof_size_policy",
    "timing_policy",
    "native_proof_equivalent",
    "primary_metric",
    "primary_value",
    "non_claims",
)

NATIVE_PROOF_EQUIVALENT_OBJECT_CLASSES = frozenset({"local_two_proof_transformer_block_frontier"})

PINNED_BASELINE = {
    "schema": "zkai-tablero-hybrid-zkml-boundary-v1",
    "decision": "GO_TABLERO_TYPED_BOUNDARIES_FOR_HYBRID_ZKML_OBJECTS",
    "result": "TYPED_BOUNDARY_SCHEMA_REJECTS_HYBRID_OBJECT_CLASS_CONFUSION",
    "issue": "https://github.com/omarespejel/provable-transformer-vm/issues/652",
    "typed_statement_schema": {
        "schema": "tablero-hybrid-zkml-typed-statement-v1",
        "required_fields": [
            "statement_id",
            "statement_schema",
            "object_class",
            "proof_system",
            "backend",
            "backend_version",
            "workload",
            "source_status",
            "model_binding",
            "input_binding",
            "output_binding",
            "proof_object_binding",
            "approximation_policy",
            "quantization_policy",
            "verifier_semantics",
            "proof_size_policy",
            "timing_policy",
            "native_proof_equivalent",
            "non_claims",
        ],
        "binding_object_fields": ["availability", "commitment", "source", "reason"],
        "native_proof_equivalent_rule": "only actual local native proof objects may set true",
        "unavailable_digest_rule": "unavailable external fields must be explicit binding objects, never omitted",
        "comparison_rule": "proof-size and timing comparisons require matched workload, object class, source status, and policy",
    },
    "boundary_examples": [
        {
            "statement_id": "stwo_two_proof_frontier_boundary",
            "object_class": "local_two_proof_transformer_block_frontier",
            "proof_system": "Stwo/STARK",
            "backend": "stwo-native",
            "backend_version": "minimal-transformer-block-benchmark-v1",
            "workload": "INTERNAL_FRONTIER_ONLY",
            "source_status": "local_checked",
            "approximation_policy": "bounded quantized attention plus d128 RMSNorm/SwiGLU substitute; not exact Softmax, LayerNorm, or GELU",
            "quantization_policy": "quantized integer fixture policy from checked local evidence",
            "verifier_semantics": "local proof-size accounting over two verified Stwo proof objects",
            "proof_size_policy": "typed proof-field accounting, local only, not external comparable",
            "timing_policy": "no median-of-5 timing claim",
            "native_proof_equivalent": True,
            "primary_metric": "two_proof_frontier_typed_bytes",
            "primary_value": 40700,
            "non_claims": ["not one native full-block proof", "not external benchmark comparable", "not exact transformer arithmetic"],
        },
        {
            "statement_id": "compact_statement_chain_boundary",
            "object_class": "local_statement_artifact",
            "proof_system": "Tablero statement boundary",
            "backend": "statement-binding",
            "backend_version": "minimal-transformer-block-benchmark-v1",
            "workload": "STATEMENT_VALIDITY_SURFACE_NOT_PROOF_SIZE_ROW",
            "source_status": "local_checked",
            "approximation_policy": "inherits the local benchmark approximation policy; statement-validity only",
            "quantization_policy": "inherits checked local quantized fixture policy",
            "verifier_semantics": "statement binding and object classification only",
            "proof_size_policy": "not comparable to native proof bytes",
            "timing_policy": "no timing claim",
            "native_proof_equivalent": False,
            "primary_metric": "statement_chain_rows",
            "primary_value": 199553,
            "non_claims": ["not a proof object", "not native verifier execution", "not proof-size comparable"],
        },
        {
            "statement_id": "jstprove_statement_envelope_boundary",
            "object_class": "external_sidecar_statement_envelope",
            "proof_system": "JSTprove/Remainder-GKR-sumcheck",
            "backend": "jstprove-statement-envelope",
            "backend_version": "zkai-jstprove-statement-envelope-benchmark-v1",
            "workload": "tiny Gemm statement-envelope adapter",
            "source_status": "local_checked_external_fixture",
            "approximation_policy": "tiny Gemm external fixture, not transformer-block arithmetic",
            "quantization_policy": "external fixture policy, not model-faithful transformer quantization",
            "verifier_semantics": "statement-envelope rejects relabeling; does not make Tablero an external verifier",
            "proof_size_policy": "statement-envelope binding, not native Stwo proof-size comparison",
            "timing_policy": "no timing claim",
            "native_proof_equivalent": False,
            "primary_metric": "mutations_rejected",
            "primary_value": 13,
            "non_claims": ["not native Stwo proof", "not d128 transformer block", "not Tablero verifying external proof internally"],
        },
        {
            "statement_id": "gkr_dense_sidecar_boundary",
            "object_class": "local_external_gkr_sidecar_fixture",
            "proof_system": "JSTprove/Remainder-GKR-sumcheck",
            "backend": "jstprove-gkr-sidecar",
            "backend_version": "zkai-gkr-dense-sidecar-baseline-v1",
            "workload": "Gemm",
            "source_status": "local_checked_external_fixture",
            "approximation_policy": "tiny projection-shaped dense arithmetic only",
            "quantization_policy": "fixture-local arithmetic policy, not d128 model-faithful attention",
            "verifier_semantics": "sidecar/baseline context, not Stwo replacement",
            "proof_size_policy": "local fixture proof bytes, not matched transformer-layer proof bytes",
            "timing_policy": "fixture timing only, not paper timing",
            "native_proof_equivalent": False,
            "primary_metric": "proof_bytes",
            "primary_value": 11645,
            "non_claims": ["not Stwo replacement", "not matched d128 dense-layer proof", "not Atlas or NANOZK comparison"],
        },
        {
            "statement_id": "jolt_atlas_self_attention_source_boundary",
            "object_class": "external_lookup_tensor_zkml_reproduction_target",
            "proof_system": "Jolt Atlas",
            "backend": "jolt-atlas",
            "backend_version": "53b7c873a6662cdc79d9818dececf337bb27d7d0",
            "workload": "single self-attention block example",
            "source_status": "repo_command_available_not_locally_reproduced",
            "approximation_policy": "external ONNX/tensor semantics unknown locally until reproduction",
            "quantization_policy": "external repository policy unavailable locally until reproduction",
            "verifier_semantics": "source-context row only; no local Atlas verifier execution",
            "proof_size_policy": "not reported until local run",
            "timing_policy": "not reported until local run",
            "native_proof_equivalent": False,
            "primary_metric": "example_command",
            "primary_value": "cargo run --release --package jolt-atlas-core --example transformer",
            "non_claims": ["not locally reproduced", "not proof-size comparable", "not timing comparable"],
        },
    ],
    "summary": {
        "boundary_example_count": 5,
        "object_class_count": 5,
        "object_classes": [
            "external_lookup_tensor_zkml_reproduction_target",
            "external_sidecar_statement_envelope",
            "local_external_gkr_sidecar_fixture",
            "local_statement_artifact",
            "local_two_proof_transformer_block_frontier",
        ],
        "local_or_local_external_rows": 4,
        "non_native_equivalent_rows": 4,
        "native_equivalent_rows": 1,
        "required_binding_fields": [
            "statement_id",
            "statement_schema",
            "object_class",
            "proof_system",
            "backend",
            "backend_version",
            "workload",
            "source_status",
            "model_binding",
            "input_binding",
            "output_binding",
            "proof_object_binding",
            "approximation_policy",
            "quantization_policy",
            "verifier_semantics",
            "proof_size_policy",
            "timing_policy",
            "native_proof_equivalent",
            "non_claims",
        ],
        "binding_object_fields": ["availability", "commitment", "source", "reason"],
        "jstprove_statement_envelope_mutations_rejected": 13,
        "jstprove_statement_envelope_mutation_count": 13,
        "jolt_atlas_local_reproduced": False,
        "jolt_atlas_proof_size_available": False,
        "tablero_role": "typed_statement_boundary_not_external_verifier",
        "hybrid_architecture_status": "GO_TYPED_BOUNDARIES_NO_GO_FALSE_EQUIVALENCE",
    },
    "source_artifacts": [
        {
            "path": "docs/engineering/evidence/zkai-minimal-transformer-block-benchmark-2026-05.json",
            "file_sha256": "300ac6886019e7670e4a1dbb25a70803e9605dffd71907d8c1220fad1ba6436f",
            "payload_sha256": "c5c9e6381c8a1ffe176552fc93fa64cd1421630045628dc22f07228967e358e1",
            "schema": "zkai-minimal-transformer-block-benchmark-v1",
            "decision": "GO_MINIMAL_BLOCK_BENCHMARK_CONTRACT_NO_GO_MATCHED_PROOF_CLAIM",
        },
        {
            "path": "docs/engineering/evidence/zkai-gkr-dense-sidecar-baseline-2026-05.json",
            "file_sha256": "06c1d45d97fd027faf59d4d1a827bfa5b93218edb87cb9711ad233f865dc47b8",
            "payload_sha256": "a434ca1ffdb09dfed4fbf89b5e2bd001aae49dc42f9b53481a8a84871879936d",
            "schema": "zkai-gkr-dense-sidecar-baseline-v1",
            "decision": "GO_GKR_SIDECAR_BASELINE_NO_GO_MATCHED_D128_DENSE_LAYER_COMPARISON",
        },
        {
            "path": "docs/engineering/evidence/zkai-jolt-atlas-lookup-tensor-comparison-2026-05.json",
            "file_sha256": "4f8ba12387cfba96a54af3391013c0b3bbbe5dbc47bdd520fe09f2653139b34e",
            "payload_sha256": "e5b54ec59baeb72b5a87ad842333086a0357bc17e820fd31dd1506e8f2347996",
            "schema": "zkai-jolt-atlas-lookup-tensor-comparison-v1",
            "decision": "GO_JOLT_ATLAS_SOURCE_BACKED_COMPARISON_NO_GO_LOCAL_REPRODUCTION",
        },
        {
            "path": "docs/engineering/evidence/zkai-jstprove-statement-envelope-benchmark-2026-05.json",
            "file_sha256": "1ddbd75355003ad6313dd4b1d521bb1f1de96be6546cc35a0156267a8be5ea37",
            "payload_sha256": "41df8f5d6c6762bec3127632a81ca4905981862d4e3f7631cdd8fa9c11f79025",
            "schema": "zkai-jstprove-statement-envelope-benchmark-v1",
        },
    ],
    "non_claims": [
        "not a recursive composition proof",
        "not a claim that Tablero verifies external proofs itself",
        "not a claim that a statement receipt proves underlying native verifier execution",
        "not a proof-size win over NANOZK",
        "not a proof-size win over Jolt Atlas",
        "not a local Jolt Atlas reproduction",
        "not a full transformer block proof",
        "not exact real-valued transformer arithmetic",
    ],
    "validation_commands": [
        "python3 scripts/zkai_tablero_hybrid_zkml_boundary_gate.py --write-json docs/engineering/evidence/zkai-tablero-hybrid-zkml-boundary-2026-05.json --write-tsv docs/engineering/evidence/zkai-tablero-hybrid-zkml-boundary-2026-05.tsv",
        "python3 -m py_compile scripts/zkai_tablero_hybrid_zkml_boundary_gate.py scripts/tests/test_zkai_tablero_hybrid_zkml_boundary_gate.py",
        "python3 -m unittest scripts.tests.test_zkai_tablero_hybrid_zkml_boundary_gate",
        "python3 scripts/research_issue_lint.py --repo-root .",
        "git diff --check",
        "just gate-fast",
        "just gate",
    ],
}


class TableroHybridBoundaryError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    except (TypeError, ValueError) as err:
        raise TableroHybridBoundaryError(f"invalid JSON value: {err}") from err


def digest_value(value: Any, domain: str) -> str:
    digest = hashlib.blake2b(digest_size=32)
    digest.update(domain.encode("ascii"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(value))
    return f"blake2b-256:{digest.hexdigest()}"


def payload_commitment(payload: dict[str, Any]) -> str:
    material = copy.deepcopy(payload)
    material.pop("payload_commitment", None)
    return digest_value(material, PAYLOAD_DOMAIN)


def statement_commitment(statement: dict[str, Any]) -> str:
    material = copy.deepcopy(statement)
    material.pop("statement_commitment", None)
    return digest_value(material, BOUNDARY_DOMAIN)


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
        raise TableroHybridBoundaryError(str(err)) from err
    return payload, raw


def load_sources() -> dict[str, Any]:
    minimal, minimal_raw = load_source(MINIMAL_BENCHMARK)
    gkr, gkr_raw = load_source(GKR_BASELINE)
    jolt, jolt_raw = load_source(JOLT_ATLAS_COMPARISON)
    jstprove, jstprove_raw = load_source(JSTPROVE_STATEMENT_ENVELOPE)
    if minimal.get("schema") != "zkai-minimal-transformer-block-benchmark-v1":
        raise TableroHybridBoundaryError("minimal benchmark schema drift")
    if gkr.get("schema") != "zkai-gkr-dense-sidecar-baseline-v1":
        raise TableroHybridBoundaryError("GKR baseline schema drift")
    if jolt.get("schema") != "zkai-jolt-atlas-lookup-tensor-comparison-v1":
        raise TableroHybridBoundaryError("Jolt/Atlas comparison schema drift")
    if jstprove.get("schema") != "zkai-jstprove-statement-envelope-benchmark-v1":
        raise TableroHybridBoundaryError("JSTprove statement-envelope schema drift")
    return {
        "minimal": minimal,
        "gkr": gkr,
        "jolt": jolt,
        "jstprove": jstprove,
        "raw": {
            "minimal": minimal_raw,
            "gkr": gkr_raw,
            "jolt": jolt_raw,
            "jstprove": jstprove_raw,
        },
    }


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TableroHybridBoundaryError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise TableroHybridBoundaryError(f"{label} must be a list")
    return value


def require_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TableroHybridBoundaryError(f"{label} must be an integer")
    return value


def require_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise TableroHybridBoundaryError(f"{label} must be a non-empty string")
    return value


def row_by_component(rows: list[Any], component: str) -> dict[str, Any]:
    matches = [row for row in rows if isinstance(row, dict) and row.get("component") == component]
    if len(matches) > 1:
        raise TableroHybridBoundaryError(f"duplicate component row: {component}")
    if matches:
        return matches[0]
    raise TableroHybridBoundaryError(f"missing component row: {component}")


def row_by_id(rows: list[Any], row_id: str) -> dict[str, Any]:
    matches = [row for row in rows if isinstance(row, dict) and row.get("row_id") == row_id]
    if len(matches) > 1:
        raise TableroHybridBoundaryError(f"duplicate row: {row_id}")
    if matches:
        return matches[0]
    raise TableroHybridBoundaryError(f"missing row: {row_id}")


def binding(kind: str, source: str, material: Any, reason: str) -> dict[str, Any]:
    if kind not in {"bound", "unavailable_explicit", "source_reported"}:
        raise TableroHybridBoundaryError(f"invalid binding availability: {kind}")
    payload = {"availability": kind, "source": source, "material": material, "reason": reason}
    return {
        "availability": kind,
        "commitment": digest_value(payload, f"{BOUNDARY_DOMAIN}:binding"),
        "source": source,
        "reason": reason,
    }


def boundary_statement(
    *,
    statement_id: str,
    object_class: str,
    proof_system: str,
    backend: str,
    backend_version: str,
    workload: str,
    source_status: str,
    model_binding: dict[str, Any],
    input_binding: dict[str, Any],
    output_binding: dict[str, Any],
    proof_object_binding: dict[str, Any],
    approximation_policy: str,
    quantization_policy: str,
    verifier_semantics: str,
    proof_size_policy: str,
    timing_policy: str,
    native_proof_equivalent: bool,
    primary_metric: str,
    primary_value: Any,
    non_claims: tuple[str, ...],
) -> dict[str, Any]:
    statement = {
        "statement_id": statement_id,
        "statement_schema": BOUNDARY_SCHEMA,
        "object_class": object_class,
        "proof_system": proof_system,
        "backend": backend,
        "backend_version": backend_version,
        "workload": workload,
        "source_status": source_status,
        "model_binding": model_binding,
        "input_binding": input_binding,
        "output_binding": output_binding,
        "proof_object_binding": proof_object_binding,
        "approximation_policy": approximation_policy,
        "quantization_policy": quantization_policy,
        "verifier_semantics": verifier_semantics,
        "proof_size_policy": proof_size_policy,
        "timing_policy": timing_policy,
        "native_proof_equivalent": native_proof_equivalent,
        "primary_metric": primary_metric,
        "primary_value": primary_value,
        "non_claims": list(non_claims),
    }
    statement["statement_commitment"] = statement_commitment(statement)
    return statement


def build_boundary_examples(sources: dict[str, Any]) -> list[dict[str, Any]]:
    minimal_summary = require_dict(sources["minimal"].get("summary"), "minimal summary")
    minimal_rows = require_list(sources["minimal"].get("component_rows"), "minimal component rows")
    gkr_rows = require_list(sources["gkr"].get("rows"), "GKR rows")
    jolt_rows = require_list(sources["jolt"].get("rows"), "Jolt rows")
    jstprove_summary = require_dict(sources["jstprove"].get("summary"), "JSTprove summary")

    two_proof = row_by_component(minimal_rows, "two_proof_frontier")
    statement_chain = row_by_component(minimal_rows, "typed_public_statement_chain")
    gkr_tiny = row_by_id(gkr_rows, "tiny_gemm")
    atlas_self_attention = row_by_id(jolt_rows, "jolt_atlas_repo_self_attention_example")
    envelope_summary = require_dict(jstprove_summary.get("jstprove-statement-envelope"), "JSTprove envelope summary")

    frontier_bytes = require_int(minimal_summary.get("two_proof_frontier_typed_bytes"), "frontier bytes")
    if frontier_bytes != require_int(two_proof.get("primary_value"), "two-proof row bytes"):
        raise TableroHybridBoundaryError("two-proof frontier drift")
    statement_rows = require_int(statement_chain.get("primary_value"), "statement chain rows")
    gkr_bytes = require_int(gkr_tiny.get("primary_value"), "GKR tiny proof bytes")
    jst_mutations = require_int(envelope_summary.get("mutations_rejected"), "JSTprove statement mutations")

    return [
        boundary_statement(
            statement_id="stwo_two_proof_frontier_boundary",
            object_class="local_two_proof_transformer_block_frontier",
            proof_system="Stwo/STARK",
            backend="stwo-native",
            backend_version="minimal-transformer-block-benchmark-v1",
            workload=require_str(two_proof.get("comparability"), "two-proof workload boundary"),
            source_status="local_checked",
            model_binding=binding("bound", str(MINIMAL_BENCHMARK.relative_to(ROOT)), two_proof, "model/profile facts are bound through local benchmark contract"),
            input_binding=binding("bound", str(MINIMAL_BENCHMARK.relative_to(ROOT)), minimal_summary, "input facts are bound by source artifact digests"),
            output_binding=binding("bound", str(MINIMAL_BENCHMARK.relative_to(ROOT)), statement_chain, "output statement-chain facts are source-bound"),
            proof_object_binding=binding("bound", str(MINIMAL_BENCHMARK.relative_to(ROOT)), two_proof, "two local proof objects, not one native block proof"),
            approximation_policy="bounded quantized attention plus d128 RMSNorm/SwiGLU substitute; not exact Softmax, LayerNorm, or GELU",
            quantization_policy="quantized integer fixture policy from checked local evidence",
            verifier_semantics="local proof-size accounting over two verified Stwo proof objects",
            proof_size_policy="typed proof-field accounting, local only, not external comparable",
            timing_policy="no median-of-5 timing claim",
            native_proof_equivalent=True,
            primary_metric="two_proof_frontier_typed_bytes",
            primary_value=frontier_bytes,
            non_claims=(
                "not one native full-block proof",
                "not external benchmark comparable",
                "not exact transformer arithmetic",
            ),
        ),
        boundary_statement(
            statement_id="compact_statement_chain_boundary",
            object_class="local_statement_artifact",
            proof_system="Tablero statement boundary",
            backend="statement-binding",
            backend_version="minimal-transformer-block-benchmark-v1",
            workload=require_str(statement_chain.get("comparability"), "statement-chain boundary"),
            source_status="local_checked",
            model_binding=binding("bound", str(MINIMAL_BENCHMARK.relative_to(ROOT)), statement_chain, "statement chain carries model/workload contract metadata"),
            input_binding=binding("bound", str(MINIMAL_BENCHMARK.relative_to(ROOT)), statement_chain, "statement input facts are bound but not re-proven here"),
            output_binding=binding("bound", str(MINIMAL_BENCHMARK.relative_to(ROOT)), statement_chain, "statement output facts are bound but not native proof execution"),
            proof_object_binding=binding("bound", str(MINIMAL_BENCHMARK.relative_to(ROOT)), statement_chain, "compact statement artifact, not native proof object"),
            approximation_policy="inherits the local benchmark approximation policy; statement-validity only",
            quantization_policy="inherits checked local quantized fixture policy",
            verifier_semantics="statement binding and object classification only",
            proof_size_policy="not comparable to native proof bytes",
            timing_policy="no timing claim",
            native_proof_equivalent=False,
            primary_metric="statement_chain_rows",
            primary_value=statement_rows,
            non_claims=(
                "not a proof object",
                "not native verifier execution",
                "not proof-size comparable",
            ),
        ),
        boundary_statement(
            statement_id="jstprove_statement_envelope_boundary",
            object_class="external_sidecar_statement_envelope",
            proof_system="JSTprove/Remainder-GKR-sumcheck",
            backend="jstprove-statement-envelope",
            backend_version="zkai-jstprove-statement-envelope-benchmark-v1",
            workload="tiny Gemm statement-envelope adapter",
            source_status="local_checked_external_fixture",
            model_binding=binding("bound", str(JSTPROVE_STATEMENT_ENVELOPE.relative_to(ROOT)), envelope_summary, "tiny model fixture metadata is statement-bound"),
            input_binding=binding("bound", str(JSTPROVE_STATEMENT_ENVELOPE.relative_to(ROOT)), envelope_summary, "input fixture metadata is statement-bound"),
            output_binding=binding("bound", str(JSTPROVE_STATEMENT_ENVELOPE.relative_to(ROOT)), envelope_summary, "output fixture metadata is statement-bound"),
            proof_object_binding=binding("bound", str(JSTPROVE_STATEMENT_ENVELOPE.relative_to(ROOT)), sources["jstprove"], "external proof-backed statement envelope"),
            approximation_policy="tiny Gemm external fixture, not transformer-block arithmetic",
            quantization_policy="external fixture policy, not model-faithful transformer quantization",
            verifier_semantics="statement-envelope rejects relabeling; does not make Tablero an external verifier",
            proof_size_policy="statement-envelope binding, not native Stwo proof-size comparison",
            timing_policy="no timing claim",
            native_proof_equivalent=False,
            primary_metric="mutations_rejected",
            primary_value=jst_mutations,
            non_claims=(
                "not native Stwo proof",
                "not d128 transformer block",
                "not Tablero verifying external proof internally",
            ),
        ),
        boundary_statement(
            statement_id="gkr_dense_sidecar_boundary",
            object_class="local_external_gkr_sidecar_fixture",
            proof_system="JSTprove/Remainder-GKR-sumcheck",
            backend="jstprove-gkr-sidecar",
            backend_version="zkai-gkr-dense-sidecar-baseline-v1",
            workload=require_str(gkr_tiny.get("workload"), "GKR tiny workload"),
            source_status="local_checked_external_fixture",
            model_binding=binding("bound", str(GKR_BASELINE.relative_to(ROOT)), gkr_tiny, "tiny Gemm fixture source-bound"),
            input_binding=binding("bound", str(GKR_BASELINE.relative_to(ROOT)), gkr_tiny, "tiny Gemm input fixture source-bound"),
            output_binding=binding("bound", str(GKR_BASELINE.relative_to(ROOT)), gkr_tiny, "tiny Gemm output fixture source-bound"),
            proof_object_binding=binding("bound", str(GKR_BASELINE.relative_to(ROOT)), gkr_tiny, "local external GKR fixture proof bytes"),
            approximation_policy="tiny projection-shaped dense arithmetic only",
            quantization_policy="fixture-local arithmetic policy, not d128 model-faithful attention",
            verifier_semantics="sidecar/baseline context, not Stwo replacement",
            proof_size_policy="local fixture proof bytes, not matched transformer-layer proof bytes",
            timing_policy="fixture timing only, not paper timing",
            native_proof_equivalent=False,
            primary_metric="proof_bytes",
            primary_value=gkr_bytes,
            non_claims=(
                "not Stwo replacement",
                "not matched d128 dense-layer proof",
                "not Atlas or NANOZK comparison",
            ),
        ),
        boundary_statement(
            statement_id="jolt_atlas_self_attention_source_boundary",
            object_class="external_lookup_tensor_zkml_reproduction_target",
            proof_system="Jolt Atlas",
            backend="jolt-atlas",
            backend_version="53b7c873a6662cdc79d9818dececf337bb27d7d0",
            workload=require_str(atlas_self_attention.get("workload"), "Atlas workload"),
            source_status=require_str(atlas_self_attention.get("source_status"), "Atlas source status"),
            model_binding=binding("source_reported", str(JOLT_ATLAS_COMPARISON.relative_to(ROOT)), atlas_self_attention, "repo command available; model/input details unavailable until local run"),
            input_binding=binding("unavailable_explicit", str(JOLT_ATLAS_COMPARISON.relative_to(ROOT)), atlas_self_attention, "input digest unavailable because Atlas was not locally reproduced"),
            output_binding=binding("unavailable_explicit", str(JOLT_ATLAS_COMPARISON.relative_to(ROOT)), atlas_self_attention, "output digest unavailable because Atlas was not locally reproduced"),
            proof_object_binding=binding("unavailable_explicit", str(JOLT_ATLAS_COMPARISON.relative_to(ROOT)), atlas_self_attention, "proof bytes unavailable until local self-attention run"),
            approximation_policy="external ONNX/tensor semantics unknown locally until reproduction",
            quantization_policy="external repository policy unavailable locally until reproduction",
            verifier_semantics="source-context row only; no local Atlas verifier execution",
            proof_size_policy="not reported until local run",
            timing_policy="not reported until local run",
            native_proof_equivalent=False,
            primary_metric=require_str(atlas_self_attention.get("primary_metric"), "Atlas primary metric"),
            primary_value=require_str(atlas_self_attention.get("primary_value"), "Atlas primary value"),
            non_claims=(
                "not locally reproduced",
                "not proof-size comparable",
                "not timing comparable",
            ),
        ),
    ]


def typed_statement_schema() -> dict[str, Any]:
    return {
        "schema": BOUNDARY_SCHEMA,
        "required_fields": list(REQUIRED_BINDING_FIELDS),
        "binding_object_fields": list(BINDING_OBJECT_FIELDS),
        "native_proof_equivalent_rule": "only actual local native proof objects may set true",
        "unavailable_digest_rule": "unavailable external fields must be explicit binding objects, never omitted",
        "comparison_rule": "proof-size and timing comparisons require matched workload, object class, source status, and policy",
    }


def build_summary(examples: list[dict[str, Any]], sources: dict[str, Any]) -> dict[str, Any]:
    object_classes = sorted({require_str(row.get("object_class"), "object class") for row in examples})
    local_rows = [row for row in examples if row["source_status"].startswith("local")]
    statement_rows = [row for row in examples if row["native_proof_equivalent"] is False]
    jst = require_dict(sources["jstprove"]["summary"].get("jstprove-statement-envelope"), "JSTprove statement summary")
    jolt_summary = require_dict(sources["jolt"].get("summary"), "Jolt summary")
    return {
        "boundary_example_count": len(examples),
        "object_class_count": len(object_classes),
        "object_classes": object_classes,
        "local_or_local_external_rows": len(local_rows),
        "non_native_equivalent_rows": len(statement_rows),
        "native_equivalent_rows": sum(1 for row in examples if row["native_proof_equivalent"] is True),
        "required_binding_fields": list(REQUIRED_BINDING_FIELDS),
        "binding_object_fields": list(BINDING_OBJECT_FIELDS),
        "jstprove_statement_envelope_mutations_rejected": require_int(jst.get("mutations_rejected"), "JSTprove mutations rejected"),
        "jstprove_statement_envelope_mutation_count": require_int(jst.get("mutation_count"), "JSTprove mutation count"),
        "jolt_atlas_local_reproduced": jolt_summary.get("atlas_local_reproduced"),
        "jolt_atlas_proof_size_available": jolt_summary.get("atlas_proof_size_available"),
        "tablero_role": "typed_statement_boundary_not_external_verifier",
        "hybrid_architecture_status": "GO_TYPED_BOUNDARIES_NO_GO_FALSE_EQUIVALENCE",
    }


def base_payload() -> dict[str, Any]:
    sources = load_sources()
    examples = build_boundary_examples(sources)
    raw_sources = require_dict(sources["raw"], "source raw inventory")
    return {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "typed_statement_schema": typed_statement_schema(),
        "boundary_examples": examples,
        "summary": build_summary(examples, sources),
        "source_artifacts": [
            source_descriptor(MINIMAL_BENCHMARK, sources["minimal"], raw_sources["minimal"]),
            source_descriptor(GKR_BASELINE, sources["gkr"], raw_sources["gkr"]),
            source_descriptor(JOLT_ATLAS_COMPARISON, sources["jolt"], raw_sources["jolt"]),
            source_descriptor(JSTPROVE_STATEMENT_ENVELOPE, sources["jstprove"], raw_sources["jstprove"]),
        ],
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }


def validate_binding_object(value: Any, label: str) -> None:
    binding_obj = require_dict(value, label)
    if set(binding_obj) != set(BINDING_OBJECT_FIELDS):
        raise TableroHybridBoundaryError(f"{label} field drift")
    availability = require_str(binding_obj.get("availability"), f"{label}.availability")
    if availability not in {"bound", "unavailable_explicit", "source_reported"}:
        raise TableroHybridBoundaryError(f"{label} invalid availability")
    commitment = require_str(binding_obj.get("commitment"), f"{label}.commitment")
    if not commitment.startswith("blake2b-256:"):
        raise TableroHybridBoundaryError(f"{label} commitment drift")
    require_str(binding_obj.get("source"), f"{label}.source")
    require_str(binding_obj.get("reason"), f"{label}.reason")


def validate_boundary_statement(row: Any) -> None:
    statement = require_dict(row, "boundary statement")
    expected_keys = set(REQUIRED_BINDING_FIELDS) | {"primary_metric", "primary_value", "statement_commitment"}
    if set(statement) != expected_keys:
        raise TableroHybridBoundaryError("boundary statement field drift")
    for field in REQUIRED_BINDING_FIELDS:
        if field not in statement:
            raise TableroHybridBoundaryError(f"missing statement field: {field}")
    if statement["statement_schema"] != BOUNDARY_SCHEMA:
        raise TableroHybridBoundaryError("statement schema drift")
    for field in ("model_binding", "input_binding", "output_binding", "proof_object_binding"):
        validate_binding_object(statement[field], field)
    for field in (
        "statement_id",
        "object_class",
        "proof_system",
        "backend",
        "backend_version",
        "workload",
        "source_status",
        "approximation_policy",
        "quantization_policy",
        "verifier_semantics",
        "proof_size_policy",
        "timing_policy",
        "primary_metric",
    ):
        require_str(statement.get(field), field)
    if statement["approximation_policy"].lower() in {"unknown", "na", "n/a"}:
        raise TableroHybridBoundaryError("approximation policy missing")
    if not isinstance(statement["native_proof_equivalent"], bool):
        raise TableroHybridBoundaryError("native proof equivalence must be boolean")
    if statement["native_proof_equivalent"] is True:
        if statement["object_class"] not in NATIVE_PROOF_EQUIVALENT_OBJECT_CLASSES:
            raise TableroHybridBoundaryError("native proof equivalence overclaim")
        if not statement["source_status"].startswith("local"):
            raise TableroHybridBoundaryError("native proof equivalence provenance overclaim")
        if statement["backend"] != "stwo-native" or statement["proof_system"] != "Stwo/STARK":
            raise TableroHybridBoundaryError("native proof equivalence backend overclaim")
    if statement["native_proof_equivalent"] is False and "native proof" in statement["proof_size_policy"].lower() and "not" not in statement["proof_size_policy"].lower():
        raise TableroHybridBoundaryError("false proof-size equivalence")
    if statement["source_status"].startswith("local") and statement["backend"] == "jolt-atlas":
        raise TableroHybridBoundaryError("external source marked local")
    non_claims = require_list(statement.get("non_claims"), "statement non-claims")
    if not non_claims:
        raise TableroHybridBoundaryError("statement non-claims missing")
    if statement["statement_commitment"] != statement_commitment(statement):
        raise TableroHybridBoundaryError("statement commitment drift")


def boundary_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {field: row[field] for field in PINNED_BOUNDARY_CONTRACT_FIELDS}


def validate_pinned_baseline(payload: dict[str, Any]) -> None:
    for key in ("schema", "decision", "result", "issue", "typed_statement_schema", "summary", "source_artifacts", "non_claims", "validation_commands"):
        if payload[key] != PINNED_BASELINE[key]:
            raise TableroHybridBoundaryError(f"{key} drift")
    contracts = [boundary_contract(row) for row in payload["boundary_examples"]]
    if contracts != PINNED_BASELINE["boundary_examples"]:
        raise TableroHybridBoundaryError("boundary_examples drift")


def validate_payload(payload: dict[str, Any], *, require_mutations: bool = True) -> None:
    expected_keys = set(BASELINE_KEYS) | {"mutation_results", "mutation_count", "mutations_rejected", "payload_commitment"}
    if set(payload) != expected_keys:
        raise TableroHybridBoundaryError("payload key drift")
    schema = require_dict(payload.get("typed_statement_schema"), "typed statement schema")
    if schema.get("required_fields") != list(REQUIRED_BINDING_FIELDS):
        raise TableroHybridBoundaryError("typed schema required-field drift")
    if schema.get("binding_object_fields") != list(BINDING_OBJECT_FIELDS):
        raise TableroHybridBoundaryError("typed schema binding-field drift")
    examples = require_list(payload.get("boundary_examples"), "boundary examples")
    if len(examples) != 5:
        raise TableroHybridBoundaryError("boundary example inventory drift")
    seen = set()
    for row in examples:
        validate_boundary_statement(row)
        statement_id = row["statement_id"]
        if statement_id in seen:
            raise TableroHybridBoundaryError("duplicate statement id")
        seen.add(statement_id)
    summary = require_dict(payload.get("summary"), "summary")
    if summary.get("jstprove_statement_envelope_mutations_rejected") != 13:
        raise TableroHybridBoundaryError("JSTprove statement-envelope mutation drift")
    if summary.get("jolt_atlas_local_reproduced") is not False:
        raise TableroHybridBoundaryError("Jolt Atlas reproduction overclaim")
    if summary.get("jolt_atlas_proof_size_available") is not False:
        raise TableroHybridBoundaryError("Jolt Atlas proof-size overclaim")
    if "not a claim that Tablero verifies external proofs itself" not in payload["non_claims"]:
        raise TableroHybridBoundaryError("Tablero non-claim drift")
    if "not a claim that a statement receipt proves underlying native verifier execution" not in payload["non_claims"]:
        raise TableroHybridBoundaryError("statement receipt non-claim drift")
    validate_pinned_baseline(payload)
    if require_mutations:
        validate_mutations(payload["mutation_results"])
        if payload["mutation_count"] != len(MUTATIONS) or payload["mutations_rejected"] != len(MUTATIONS):
            raise TableroHybridBoundaryError("mutation count drift")
    else:
        if payload["mutation_results"] != [] or payload["mutation_count"] != 0 or payload["mutations_rejected"] != 0:
            raise TableroHybridBoundaryError("unexpected mutation metadata")
    if payload["payload_commitment"] != payload_commitment(payload):
        raise TableroHybridBoundaryError("payload commitment drift")


def promote_compact_statement_as_native(payload: dict[str, Any]) -> None:
    payload["boundary_examples"][1]["native_proof_equivalent"] = True


def remove_model_binding(payload: dict[str, Any]) -> None:
    payload["boundary_examples"][0].pop("model_binding")


def erase_approximation_policy(payload: dict[str, Any]) -> None:
    payload["boundary_examples"][2]["approximation_policy"] = "unknown"


def mutate_backend_version(payload: dict[str, Any]) -> None:
    payload["boundary_examples"][4]["backend_version"] = "latest"


def mark_atlas_local(payload: dict[str, Any]) -> None:
    payload["boundary_examples"][4]["source_status"] = "local_checked"


def mark_atlas_creative_local(payload: dict[str, Any]) -> None:
    payload["boundary_examples"][4]["source_status"] = "local_checked_external_fixture"


def mark_native_equivalent_external_backend(payload: dict[str, Any]) -> None:
    payload["boundary_examples"][0]["backend"] = "jstprove-gkr-sidecar"


def mutate_statement_commitment(payload: dict[str, Any]) -> None:
    payload["boundary_examples"][3]["statement_commitment"] = "blake2b-256:" + "0" * 64


def remove_unavailable_output_binding(payload: dict[str, Any]) -> None:
    payload["boundary_examples"][4]["output_binding"].pop("reason")


def promote_atlas_proof_size(payload: dict[str, Any]) -> None:
    payload["summary"]["jolt_atlas_proof_size_available"] = True


def remove_schema_field(payload: dict[str, Any]) -> None:
    payload["typed_statement_schema"]["required_fields"].remove("approximation_policy")


def remove_global_non_claim(payload: dict[str, Any]) -> None:
    payload["non_claims"].remove("not a claim that Tablero verifies external proofs itself")


MUTATIONS = (
    ("compact_statement_as_native_overclaim", promote_compact_statement_as_native),
    ("missing_model_binding", remove_model_binding),
    ("missing_approximation_policy", erase_approximation_policy),
    ("backend_version_drift", mutate_backend_version),
    ("atlas_marked_local", mark_atlas_local),
    ("atlas_marked_creative_local", mark_atlas_creative_local),
    ("native_equivalent_external_backend", mark_native_equivalent_external_backend),
    ("statement_commitment_drift", mutate_statement_commitment),
    ("unavailable_binding_field_removed", remove_unavailable_output_binding),
    ("atlas_proof_size_overclaim", promote_atlas_proof_size),
    ("typed_schema_field_removed", remove_schema_field),
    ("global_non_claim_removed", remove_global_non_claim),
)


def run_mutations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for name, mutate in MUTATIONS:
        candidate = copy.deepcopy(payload)
        mutate(candidate)
        candidate["payload_commitment"] = payload_commitment(candidate)
        try:
            validate_payload(candidate, require_mutations=False)
        except TableroHybridBoundaryError as err:
            results.append({"name": name, "rejected": True, "reason": str(err)})
        else:
            results.append({"name": name, "rejected": False, "reason": ""})
    return results


def validate_mutations(results: Any) -> None:
    if not isinstance(results, list) or len(results) != len(MUTATIONS):
        raise TableroHybridBoundaryError("mutation result drift")
    expected_names = [name for name, _mutate in MUTATIONS]
    if [entry.get("name") for entry in results if isinstance(entry, dict)] != expected_names:
        raise TableroHybridBoundaryError("mutation order drift")
    for entry in results:
        if not isinstance(entry, dict) or set(entry) != {"name", "rejected", "reason"}:
            raise TableroHybridBoundaryError("mutation entry drift")
        if entry["rejected"] is not True or not entry["reason"]:
            raise TableroHybridBoundaryError(f"mutation did not reject: {entry.get('name')}")


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
    for row in payload["boundary_examples"]:
        writer.writerow(
            {
                "statement_id": row["statement_id"],
                "object_class": row["object_class"],
                "proof_system": row["proof_system"],
                "backend": row["backend"],
                "source_status": row["source_status"],
                "primary_metric": row["primary_metric"],
                "primary_value": row["primary_value"],
                "native_proof_equivalent": row["native_proof_equivalent"],
                "proof_size_policy": row["proof_size_policy"],
                "timing_policy": row["timing_policy"],
                "claim_boundary": row["verifier_semantics"],
            }
        )
    return output.getvalue()


def normalized_output_target(path: pathlib.Path) -> pathlib.Path:
    try:
        return minimal_gate.normalize_output_path(path)
    except Exception as err:  # noqa: BLE001 - keep gate-specific public error type.
        raise TableroHybridBoundaryError(str(err)) from err


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
        raise TableroHybridBoundaryError("output paths collide")
    for label, target in targets:
        if label == "json" and target.suffix != ".json":
            raise TableroHybridBoundaryError(f"JSON output must use .json suffix: {target}")
        if label == "tsv" and target.suffix != ".tsv":
            raise TableroHybridBoundaryError(f"TSV output must use .tsv suffix: {target}")
    source_paths = {path.resolve() for path in SOURCE_PATHS}
    source_paths |= {
        (ROOT / artifact["path"]).resolve()
        for artifact in payload.get("source_artifacts", [])
        if isinstance(artifact, dict) and isinstance(artifact.get("path"), str)
    }
    for label, target in targets:
        if target in source_paths:
            raise TableroHybridBoundaryError(f"refusing to overwrite source artifact with {label} output: {target}")
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
                "boundary_examples": payload["summary"]["boundary_example_count"],
                "object_classes": payload["summary"]["object_class_count"],
                "mutations_rejected": payload["mutations_rejected"],
                "jolt_atlas_local_reproduced": payload["summary"]["jolt_atlas_local_reproduced"],
                "tablero_role": payload["summary"]["tablero_role"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
