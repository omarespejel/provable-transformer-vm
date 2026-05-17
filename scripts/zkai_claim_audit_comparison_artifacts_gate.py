#!/usr/bin/env python3
"""Audit zkML comparison artifacts for object-class and overclaim drift."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import pathlib
import sys
from typing import Any, Callable

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import zkai_minimal_transformer_block_benchmark_gate as minimal_gate

EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
JSON_OUT = EVIDENCE_DIR / "zkai-claim-audit-comparison-artifacts-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-claim-audit-comparison-artifacts-2026-05.tsv"

MINIMAL_BENCHMARK = EVIDENCE_DIR / "zkai-minimal-transformer-block-benchmark-2026-05.json"
GKR_BASELINE = EVIDENCE_DIR / "zkai-gkr-dense-sidecar-baseline-2026-05.json"
JOLT_ATLAS_COMPARISON = EVIDENCE_DIR / "zkai-jolt-atlas-lookup-tensor-comparison-2026-05.json"
TABLERO_BOUNDARY = EVIDENCE_DIR / "zkai-tablero-hybrid-zkml-boundary-2026-05.json"
LABEL_POLICY = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-label-policy-2026-05.json"
OPENING_BUDGET = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-opening-budget-route-2026-05.json"
ADJACENT_LAYOUT = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-adjacent-layout-2026-05.json"
SOURCE_PATHS = (
    MINIMAL_BENCHMARK,
    GKR_BASELINE,
    JOLT_ATLAS_COMPARISON,
    TABLERO_BOUNDARY,
    LABEL_POLICY,
    OPENING_BUDGET,
    ADJACENT_LAYOUT,
)

SCHEMA = "zkai-claim-audit-comparison-artifacts-v1"
DECISION = "GO_ADVERSARIAL_ZKML_CLAIM_AUDIT_NO_GO_UNTYPED_COMPARISONS"
RESULT = "COMPARISON_MATRIX_REJECTS_OBJECT_CLASS_AND_REPRODUCTION_OVERCLAIMS"
ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/653"
PAYLOAD_DOMAIN = "ptvm:zkai:claim-audit-comparison-artifacts:v1"

REQUIRED_ROW_FIELDS = (
    "row_id",
    "source_artifact",
    "system",
    "object_class",
    "workload",
    "source_status",
    "locally_reproduced",
    "matched_workload",
    "native_proof_equivalent",
    "proof_size_comparable",
    "primary_metric",
    "primary_value",
    "proof_size_policy",
    "timing_policy",
    "claim_boundary",
    "non_claims",
)

ROW_COLUMNS = (
    "row_id",
    "system",
    "object_class",
    "workload",
    "source_status",
    "locally_reproduced",
    "matched_workload",
    "native_proof_equivalent",
    "proof_size_comparable",
    "primary_metric",
    "primary_value",
    "proof_size_policy",
    "timing_policy",
    "claim_boundary",
)

NON_CLAIMS = (
    "not a NANOZK proof-size win",
    "not a Jolt Atlas proof-size win",
    "not a GKR matched d128 proof-size win",
    "not a local reproduction of paper-reported external rows",
    "not a compact statement-binding proof-size comparison",
    "not a full transformer block proof",
    "not timing evidence unless timing_policy is explicit",
)

VALIDATION_COMMANDS = (
    "python3 scripts/zkai_claim_audit_comparison_artifacts_gate.py --write-json docs/engineering/evidence/zkai-claim-audit-comparison-artifacts-2026-05.json --write-tsv docs/engineering/evidence/zkai-claim-audit-comparison-artifacts-2026-05.tsv",
    "python3 -m py_compile scripts/zkai_claim_audit_comparison_artifacts_gate.py scripts/tests/test_zkai_claim_audit_comparison_artifacts_gate.py",
    "python3 -m unittest scripts.tests.test_zkai_claim_audit_comparison_artifacts_gate",
    "python3 scripts/research_issue_lint.py --repo-root .",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

EXTERNAL_SOURCE_STATUSES = (
    "paper_reported",
    "repo_reported",
    "repo_command_available",
    "source_context",
)

LOCAL_SOURCE_STATUSES = {
    "local_checked",
    "LOCAL_COMPONENT_FRONTIER",
    "GO_CURRENT_COMPARISON_FRONTIER_NOT_ONE_PROOF",
    "GO_STATEMENT_BOUNDARY_NOT_PROOF_OBJECT",
}

REQUIRED_ROW_NON_CLAIMS = {
    "nanozk_paper_reported_context": (
        "not a NANOZK proof-size win",
        "not locally reproduced",
    ),
    "gkr_tiny_gemm_sidecar": (
        "not a matched d128 transformer-block proof",
        "not a GKR matched d128 proof-size win",
    ),
    "gkr_tiny_residual_add_heavier_shape": (
        "not a matched d128 transformer-block proof",
        "not a GKR matched d128 proof-size win",
    ),
    "gkr_tiny_layernorm_heavier_shape": (
        "not a matched d128 transformer-block proof",
        "not a GKR matched d128 proof-size win",
    ),
    "jolt_atlas_repo_gpt2_timing_context": (
        "not a timing win over Jolt Atlas",
        "not locally reproduced",
    ),
    "jolt_atlas_self_attention_reproduction_target": (
        "not a local reproduction of Jolt Atlas",
        "not a Jolt Atlas proof-size win",
    ),
}

SOURCE_SCHEMAS = {
    "minimal": "zkai-minimal-transformer-block-benchmark-v1",
    "gkr": "zkai-gkr-dense-sidecar-baseline-v1",
    "jolt": "zkai-jolt-atlas-lookup-tensor-comparison-v1",
    "tablero": "zkai-tablero-hybrid-zkml-boundary-v1",
    "label_policy": "zkai-native-attention-mlp-rmsnorm-label-policy-gate-v1",
    "opening_budget": "zkai-native-attention-mlp-rmsnorm-opening-budget-route-gate-v1",
    "adjacent_layout": "zkai-native-attention-mlp-rmsnorm-adjacent-layout-gate-v1",
}


class ClaimAuditError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    except (TypeError, ValueError) as err:
        raise ClaimAuditError(f"invalid JSON value: {err}") from err


def payload_commitment(payload: dict[str, Any]) -> str:
    material = copy.deepcopy(payload)
    material.pop("payload_commitment", None)
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("ascii"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return f"blake2b-256:{digest.hexdigest()}"


def relative_source_path(path: pathlib.Path) -> str:
    return path.relative_to(ROOT).as_posix()


def source_descriptor(path: pathlib.Path, payload: dict[str, Any], raw: bytes) -> dict[str, Any]:
    descriptor = {
        "path": relative_source_path(path),
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
        raise ClaimAuditError(str(err)) from err
    return payload, raw


def load_sources() -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    raw: dict[str, bytes] = {}
    path_by_key = {
        "minimal": MINIMAL_BENCHMARK,
        "gkr": GKR_BASELINE,
        "jolt": JOLT_ATLAS_COMPARISON,
        "tablero": TABLERO_BOUNDARY,
        "label_policy": LABEL_POLICY,
        "opening_budget": OPENING_BUDGET,
        "adjacent_layout": ADJACENT_LAYOUT,
    }
    for key, path in path_by_key.items():
        payload, source_bytes = load_source(path)
        expected_schema = SOURCE_SCHEMAS[key]
        if payload.get("schema") != expected_schema:
            raise ClaimAuditError(f"{key} schema drift")
        loaded[key] = payload
        raw[key] = source_bytes
    loaded["raw"] = raw
    return loaded


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ClaimAuditError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ClaimAuditError(f"{label} must be a list")
    return value


def require_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ClaimAuditError(f"{label} must be a non-empty string")
    return value


def require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ClaimAuditError(f"{label} must be a boolean")
    return value


def require_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ClaimAuditError(f"{label} must be an integer")
    return value


def row_by_component(rows: list[Any], component: str) -> dict[str, Any]:
    matches = [row for row in rows if isinstance(row, dict) and row.get("component") == component]
    if len(matches) != 1:
        raise ClaimAuditError(f"component row cardinality drift: {component}")
    return matches[0]


def row_by_id(rows: list[Any], row_id: str) -> dict[str, Any]:
    matches = [row for row in rows if isinstance(row, dict) and row.get("row_id") == row_id]
    if len(matches) != 1:
        raise ClaimAuditError(f"row id cardinality drift: {row_id}")
    return matches[0]


def tablero_statement(rows: list[Any], statement_id: str) -> dict[str, Any]:
    matches = [row for row in rows if isinstance(row, dict) and row.get("statement_id") == statement_id]
    if len(matches) != 1:
        raise ClaimAuditError(f"statement id cardinality drift: {statement_id}")
    return matches[0]


def non_claims_from(payload: dict[str, Any]) -> tuple[str, ...]:
    return tuple(require_str(item, "non-claim") for item in require_list(payload.get("non_claims"), "non_claims"))


def row_non_claims(*items: str) -> tuple[str, ...]:
    claims = list(dict.fromkeys(items))
    if not claims:
        raise ClaimAuditError("row non-claims missing")
    return tuple(claims)


def audit_row(
    *,
    row_id: str,
    source_artifact: pathlib.Path,
    system: str,
    object_class: str,
    workload: str,
    source_status: str,
    locally_reproduced: bool,
    matched_workload: bool,
    native_proof_equivalent: bool,
    proof_size_comparable: bool,
    primary_metric: str,
    primary_value: Any,
    proof_size_policy: str,
    timing_policy: str,
    claim_boundary: str,
    non_claims: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "row_id": row_id,
        "source_artifact": relative_source_path(source_artifact),
        "system": system,
        "object_class": object_class,
        "workload": workload,
        "source_status": source_status,
        "locally_reproduced": locally_reproduced,
        "matched_workload": matched_workload,
        "native_proof_equivalent": native_proof_equivalent,
        "proof_size_comparable": proof_size_comparable,
        "primary_metric": primary_metric,
        "primary_value": primary_value,
        "proof_size_policy": proof_size_policy,
        "timing_policy": timing_policy,
        "claim_boundary": claim_boundary,
        "non_claims": list(non_claims),
    }


def build_audit_rows(sources: dict[str, Any]) -> list[dict[str, Any]]:
    minimal = require_dict(sources["minimal"], "minimal source")
    gkr = require_dict(sources["gkr"], "GKR source")
    jolt = require_dict(sources["jolt"], "Jolt source")
    tablero = require_dict(sources["tablero"], "Tablero source")
    label_policy = require_dict(sources["label_policy"], "label-policy source")
    opening_budget = require_dict(sources["opening_budget"], "opening-budget source")
    adjacent_layout = require_dict(sources["adjacent_layout"], "adjacent-layout source")

    minimal_rows = require_list(minimal.get("component_rows"), "minimal component rows")
    gkr_rows = require_list(gkr.get("rows"), "GKR rows")
    jolt_rows = require_list(jolt.get("rows"), "Jolt rows")
    tablero_rows = require_list(tablero.get("boundary_examples"), "Tablero boundary examples")
    label_summary = require_dict(label_policy.get("summary"), "label-policy summary")
    opening_summary = require_dict(opening_budget.get("summary"), "opening-budget summary")
    route_candidates = require_dict(opening_budget.get("route_candidates"), "opening-budget route candidates")

    two_proof = row_by_component(minimal_rows, "two_proof_frontier")
    statement_chain = row_by_component(minimal_rows, "typed_public_statement_chain")
    nanozk = row_by_component(minimal_rows, "nanozk_context_row")
    gkr_tiny = row_by_id(gkr_rows, "tiny_gemm")
    gkr_residual = row_by_id(gkr_rows, "tiny_gemm_residual_add")
    gkr_layernorm = row_by_id(gkr_rows, "tiny_gemm_layernorm")
    jolt_gpt2 = row_by_id(jolt_rows, "jolt_atlas_repo_gpt2_readme")
    jolt_self_attention = row_by_id(jolt_rows, "jolt_atlas_repo_self_attention_example")
    tablero_frontier = tablero_statement(tablero_rows, "stwo_two_proof_frontier_boundary")
    tablero_statement_chain = tablero_statement(tablero_rows, "compact_statement_chain_boundary")
    single_best = require_dict(route_candidates.get("single_best_label"), "single-best route")
    worst_label = require_dict(route_candidates.get("worst_label_path_opening_to_compact"), "worst-label route")

    rows = [
        audit_row(
            row_id="local_stwo_two_proof_frontier",
            source_artifact=MINIMAL_BENCHMARK,
            system=require_str(two_proof.get("proof_system"), "two-proof system"),
            object_class=require_str(two_proof.get("object_class"), "two-proof object class"),
            workload=require_str(two_proof.get("comparability"), "two-proof workload"),
            source_status=require_str(two_proof.get("local_status"), "two-proof source status"),
            locally_reproduced=True,
            matched_workload=False,
            native_proof_equivalent=False,
            proof_size_comparable=False,
            primary_metric=require_str(two_proof.get("primary_metric"), "two-proof metric"),
            primary_value=require_int(two_proof.get("primary_value"), "two-proof bytes"),
            proof_size_policy="internal frontier only; two proof objects, not external-comparable",
            timing_policy="no median-of-5 timing claim",
            claim_boundary=require_str(two_proof.get("claim_boundary"), "two-proof claim boundary"),
            non_claims=row_non_claims("not one native full-block proof", "not a NANOZK proof-size win"),
        ),
        audit_row(
            row_id="compact_statement_chain_not_proof",
            source_artifact=MINIMAL_BENCHMARK,
            system=require_str(statement_chain.get("proof_system"), "statement system"),
            object_class=require_str(statement_chain.get("object_class"), "statement object class"),
            workload=require_str(statement_chain.get("comparability"), "statement workload"),
            source_status=require_str(statement_chain.get("local_status"), "statement source status"),
            locally_reproduced=True,
            matched_workload=False,
            native_proof_equivalent=False,
            proof_size_comparable=False,
            primary_metric=require_str(statement_chain.get("primary_metric"), "statement metric"),
            primary_value=require_int(statement_chain.get("primary_value"), "statement rows"),
            proof_size_policy="not comparable to native proof bytes",
            timing_policy="no timing claim",
            claim_boundary=require_str(statement_chain.get("claim_boundary"), "statement claim boundary"),
            non_claims=row_non_claims("not a proof object", "not native verifier execution"),
        ),
        audit_row(
            row_id="nanozk_paper_reported_context",
            source_artifact=MINIMAL_BENCHMARK,
            system="NANOZK",
            object_class=require_str(nanozk.get("object_class"), "NANOZK object class"),
            workload=require_str(nanozk.get("comparability"), "NANOZK workload"),
            source_status="paper_reported_not_locally_reproduced",
            locally_reproduced=False,
            matched_workload=False,
            native_proof_equivalent=False,
            proof_size_comparable=False,
            primary_metric=require_str(nanozk.get("primary_metric"), "NANOZK metric"),
            primary_value=require_int(nanozk.get("primary_value"), "NANOZK bytes"),
            proof_size_policy="paper context only; not local reproduction and not matched workload",
            timing_policy="not reported in this local audit",
            claim_boundary=require_str(nanozk.get("claim_boundary"), "NANOZK claim boundary"),
            non_claims=row_non_claims("not a NANOZK proof-size win", "not locally reproduced"),
        ),
        audit_row(
            row_id="gkr_tiny_gemm_sidecar",
            source_artifact=GKR_BASELINE,
            system=require_str(gkr_tiny.get("proof_system"), "GKR system"),
            object_class=require_str(gkr_tiny.get("object_class"), "GKR object class"),
            workload=require_str(gkr_tiny.get("workload"), "GKR workload"),
            source_status=require_str(gkr_tiny.get("status"), "GKR status"),
            locally_reproduced=True,
            matched_workload=False,
            native_proof_equivalent=False,
            proof_size_comparable=False,
            primary_metric=require_str(gkr_tiny.get("primary_metric"), "GKR metric"),
            primary_value=require_int(gkr_tiny.get("primary_value"), "GKR bytes"),
            proof_size_policy="tiny fixture proof bytes; not matched d128 transformer-layer proof bytes",
            timing_policy="fixture timing only, not paper timing",
            claim_boundary=require_str(gkr_tiny.get("comparability"), "GKR claim boundary"),
            non_claims=row_non_claims("not a matched d128 transformer-block proof", "not a GKR matched d128 proof-size win"),
        ),
        audit_row(
            row_id="gkr_tiny_residual_add_heavier_shape",
            source_artifact=GKR_BASELINE,
            system=require_str(gkr_residual.get("proof_system"), "GKR residual system"),
            object_class=require_str(gkr_residual.get("object_class"), "GKR residual object class"),
            workload=require_str(gkr_residual.get("workload"), "GKR residual workload"),
            source_status=require_str(gkr_residual.get("status"), "GKR residual status"),
            locally_reproduced=True,
            matched_workload=False,
            native_proof_equivalent=False,
            proof_size_comparable=False,
            primary_metric=require_str(gkr_residual.get("primary_metric"), "GKR residual metric"),
            primary_value=require_int(gkr_residual.get("primary_value"), "GKR residual bytes"),
            proof_size_policy="tiny residual shape only; heavier than the local Stwo dense substitute",
            timing_policy="fixture timing only, not paper timing",
            claim_boundary=require_str(gkr_residual.get("comparability"), "GKR residual claim boundary"),
            non_claims=row_non_claims("not a matched d128 transformer-block proof", "not a GKR matched d128 proof-size win"),
        ),
        audit_row(
            row_id="gkr_tiny_layernorm_heavier_shape",
            source_artifact=GKR_BASELINE,
            system=require_str(gkr_layernorm.get("proof_system"), "GKR layernorm system"),
            object_class=require_str(gkr_layernorm.get("object_class"), "GKR layernorm object class"),
            workload=require_str(gkr_layernorm.get("workload"), "GKR layernorm workload"),
            source_status=require_str(gkr_layernorm.get("status"), "GKR layernorm status"),
            locally_reproduced=True,
            matched_workload=False,
            native_proof_equivalent=False,
            proof_size_comparable=False,
            primary_metric=require_str(gkr_layernorm.get("primary_metric"), "GKR layernorm metric"),
            primary_value=require_int(gkr_layernorm.get("primary_value"), "GKR layernorm bytes"),
            proof_size_policy="tiny normalization-like shape only; not our RMSNorm component",
            timing_policy="fixture timing only, not paper timing",
            claim_boundary=require_str(gkr_layernorm.get("comparability"), "GKR layernorm claim boundary"),
            non_claims=row_non_claims("not a matched d128 transformer-block proof", "not a GKR matched d128 proof-size win"),
        ),
        audit_row(
            row_id="jolt_atlas_repo_gpt2_timing_context",
            source_artifact=JOLT_ATLAS_COMPARISON,
            system=require_str(jolt_gpt2.get("system"), "Jolt GPT2 system"),
            object_class=require_str(jolt_gpt2.get("object_class"), "Jolt GPT2 object class"),
            workload=require_str(jolt_gpt2.get("workload"), "Jolt GPT2 workload"),
            source_status=require_str(jolt_gpt2.get("source_status"), "Jolt GPT2 source status"),
            locally_reproduced=False,
            matched_workload=False,
            native_proof_equivalent=False,
            proof_size_comparable=False,
            primary_metric=require_str(jolt_gpt2.get("primary_metric"), "Jolt GPT2 metric"),
            primary_value=require_str(jolt_gpt2.get("primary_value"), "Jolt GPT2 timing"),
            proof_size_policy=require_str(jolt_gpt2.get("proof_size_status"), "Jolt GPT2 proof-size status"),
            timing_policy=require_str(jolt_gpt2.get("timing_status"), "Jolt GPT2 timing status"),
            claim_boundary=require_str(jolt_gpt2.get("comparability"), "Jolt GPT2 claim boundary"),
            non_claims=row_non_claims("not a timing win over Jolt Atlas", "not locally reproduced"),
        ),
        audit_row(
            row_id="jolt_atlas_self_attention_reproduction_target",
            source_artifact=JOLT_ATLAS_COMPARISON,
            system=require_str(jolt_self_attention.get("system"), "Jolt self-attention system"),
            object_class=require_str(jolt_self_attention.get("object_class"), "Jolt self-attention object class"),
            workload=require_str(jolt_self_attention.get("workload"), "Jolt self-attention workload"),
            source_status=require_str(jolt_self_attention.get("source_status"), "Jolt self-attention source status"),
            locally_reproduced=False,
            matched_workload=False,
            native_proof_equivalent=False,
            proof_size_comparable=False,
            primary_metric=require_str(jolt_self_attention.get("primary_metric"), "Jolt self-attention metric"),
            primary_value=require_str(jolt_self_attention.get("primary_value"), "Jolt self-attention command"),
            proof_size_policy=require_str(jolt_self_attention.get("proof_size_status"), "Jolt self-attention proof-size status"),
            timing_policy=require_str(jolt_self_attention.get("timing_status"), "Jolt self-attention timing status"),
            claim_boundary=require_str(jolt_self_attention.get("comparability"), "Jolt self-attention claim boundary"),
            non_claims=row_non_claims("not a local reproduction of Jolt Atlas", "not a Jolt Atlas proof-size win"),
        ),
        audit_row(
            row_id="tablero_native_frontier_boundary",
            source_artifact=TABLERO_BOUNDARY,
            system=require_str(tablero_frontier.get("proof_system"), "Tablero frontier system"),
            object_class=require_str(tablero_frontier.get("object_class"), "Tablero frontier object class"),
            workload=require_str(tablero_frontier.get("workload"), "Tablero frontier workload"),
            source_status=require_str(tablero_frontier.get("source_status"), "Tablero frontier source status"),
            locally_reproduced=True,
            matched_workload=False,
            native_proof_equivalent=require_bool(tablero_frontier.get("native_proof_equivalent"), "Tablero native flag"),
            proof_size_comparable=False,
            primary_metric=require_str(tablero_frontier.get("primary_metric"), "Tablero frontier metric"),
            primary_value=require_int(tablero_frontier.get("primary_value"), "Tablero frontier bytes"),
            proof_size_policy=require_str(tablero_frontier.get("proof_size_policy"), "Tablero frontier proof policy"),
            timing_policy=require_str(tablero_frontier.get("timing_policy"), "Tablero frontier timing policy"),
            claim_boundary=require_str(tablero_frontier.get("verifier_semantics"), "Tablero frontier claim boundary"),
            non_claims=tuple(require_list(tablero_frontier.get("non_claims"), "Tablero frontier non-claims")),
        ),
        audit_row(
            row_id="tablero_compact_statement_boundary",
            source_artifact=TABLERO_BOUNDARY,
            system=require_str(tablero_statement_chain.get("proof_system"), "Tablero statement system"),
            object_class=require_str(tablero_statement_chain.get("object_class"), "Tablero statement object class"),
            workload=require_str(tablero_statement_chain.get("workload"), "Tablero statement workload"),
            source_status=require_str(tablero_statement_chain.get("source_status"), "Tablero statement source status"),
            locally_reproduced=True,
            matched_workload=False,
            native_proof_equivalent=require_bool(tablero_statement_chain.get("native_proof_equivalent"), "Tablero statement native flag"),
            proof_size_comparable=False,
            primary_metric=require_str(tablero_statement_chain.get("primary_metric"), "Tablero statement metric"),
            primary_value=require_int(tablero_statement_chain.get("primary_value"), "Tablero statement rows"),
            proof_size_policy=require_str(tablero_statement_chain.get("proof_size_policy"), "Tablero statement proof policy"),
            timing_policy=require_str(tablero_statement_chain.get("timing_policy"), "Tablero statement timing policy"),
            claim_boundary=require_str(tablero_statement_chain.get("verifier_semantics"), "Tablero statement claim boundary"),
            non_claims=tuple(require_list(tablero_statement_chain.get("non_claims"), "Tablero statement non-claims")),
        ),
        audit_row(
            row_id="rmsnorm_single_best_label_rejected",
            source_artifact=LABEL_POLICY,
            system="Stwo/STARK",
            object_class="local_native_stwo_proof_object_attempt_label_policy",
            workload="RMSNorm-input opening layout label probe",
            source_status="local_checked",
            locally_reproduced=True,
            matched_workload=False,
            native_proof_equivalent=False,
            proof_size_comparable=False,
            primary_metric="best_observed_label_typed_bytes",
            primary_value=require_int(label_summary.get("best_observed_label_typed_bytes"), "best label bytes"),
            proof_size_policy="single best label rejected; worst-label inventory required",
            timing_policy="no timing claim",
            claim_boundary="favorable label cannot replace worst-label policy",
            non_claims=row_non_claims("not a two-proof frontier beat", "not a proof-size win"),
        ),
        audit_row(
            row_id="rmsnorm_worst_label_opening_target",
            source_artifact=OPENING_BUDGET,
            system="Stwo/STARK",
            object_class="local_native_stwo_opening_layout_target",
            workload=require_str(worst_label.get("source_variant"), "worst label source variant"),
            source_status="local_checked",
            locally_reproduced=True,
            matched_workload=False,
            native_proof_equivalent=False,
            proof_size_comparable=False,
            primary_metric="worst_label_required_reduction_to_beat_frontier_bytes",
            primary_value=require_int(opening_summary.get("worst_label_required_reduction_to_beat_frontier_bytes"), "worst label required reduction"),
            proof_size_policy="target only; no proof object currently removes the required opening bytes",
            timing_policy="no timing claim",
            claim_boundary=require_str(worst_label.get("route_status"), "worst label route status"),
            non_claims=row_non_claims("not a proof-size win", "not a new proof object"),
        ),
        audit_row(
            row_id="adjacent_layout_worst_label_no_go",
            source_artifact=ADJACENT_LAYOUT,
            system="Stwo/STARK",
            object_class="local_native_stwo_proof_object_attempt",
            workload="adjacent RMSNorm-input layout under worst-label policy",
            source_status="local_checked",
            locally_reproduced=True,
            matched_workload=False,
            native_proof_equivalent=False,
            proof_size_comparable=False,
            primary_metric="adjacent_worst_label_typed_bytes",
            primary_value=require_int(adjacent_layout.get("adjacent_worst_label_typed_bytes"), "adjacent worst label bytes"),
            proof_size_policy="NO-GO under worst-label policy",
            timing_policy="no timing claim",
            claim_boundary=require_str(adjacent_layout.get("claim_boundary"), "adjacent claim boundary"),
            non_claims=tuple(require_list(adjacent_layout.get("non_claims"), "adjacent non-claims")),
        ),
    ]

    if require_bool(single_best.get("promotion_allowed_now"), "single-best promotion flag"):
        raise ClaimAuditError("single-best label already promoted upstream")
    if require_bool(worst_label.get("promotion_allowed_now"), "worst-label promotion flag"):
        raise ClaimAuditError("worst-label target promoted upstream")
    return rows


def is_external_source_status(source_status: str) -> bool:
    return source_status.startswith(EXTERNAL_SOURCE_STATUSES)


def is_local_source_status(source_status: str, object_class: str) -> bool:
    if source_status in LOCAL_SOURCE_STATUSES:
        return True
    return source_status == "GO" and object_class.startswith("local_external_gkr")


def validate_non_claim_inventory(payload: dict[str, Any]) -> None:
    claims = non_claims_from(payload)
    claim_set = set(claims)
    expected = set(NON_CLAIMS)
    if len(claims) != len(NON_CLAIMS) or claim_set != expected:
        missing = sorted(expected - claim_set)
        extra = sorted(claim_set - expected)
        raise ClaimAuditError(f"global non-claim drift: missing={missing[:1]} extra={extra[:1]}")


def validate_source_artifacts(source_artifacts: list[Any]) -> None:
    if len(source_artifacts) != len(SOURCE_PATHS):
        raise ClaimAuditError("source artifact count drift")
    expected_artifacts = base_payload(load_sources())["source_artifacts"]
    if source_artifacts != expected_artifacts:
        raise ClaimAuditError("source artifact descriptor drift")


def validate_row(row: dict[str, Any]) -> None:
    if set(row) != set(REQUIRED_ROW_FIELDS):
        raise ClaimAuditError(f"row field drift: {row.get('row_id', '<missing>')}")
    row_id = require_str(row["row_id"], "row id")
    object_class = require_str(row["object_class"], f"{row_id} object class")
    source_status = require_str(row["source_status"], f"{row_id} source status")
    proof_size_policy = require_str(row["proof_size_policy"], f"{row_id} proof-size policy")
    timing_policy = require_str(row["timing_policy"], f"{row_id} timing policy")
    claim_boundary = require_str(row["claim_boundary"], f"{row_id} claim boundary")
    non_claims = tuple(require_str(item, f"{row_id} non-claim") for item in require_list(row["non_claims"], f"{row_id} non-claims"))
    locally_reproduced = require_bool(row["locally_reproduced"], f"{row_id} locally reproduced")
    matched_workload = require_bool(row["matched_workload"], f"{row_id} matched workload")
    native_equivalent = require_bool(row["native_proof_equivalent"], f"{row_id} native equivalent")
    proof_size_comparable = require_bool(row["proof_size_comparable"], f"{row_id} proof-size comparable")
    require_str(row["source_artifact"], f"{row_id} source artifact")
    require_str(row["system"], f"{row_id} system")
    require_str(row["workload"], f"{row_id} workload")
    require_str(row["primary_metric"], f"{row_id} primary metric")
    if claim_boundary.lower() in {"matched", "comparable"}:
        raise ClaimAuditError(f"{row_id} claim boundary too weak")
    if is_external_source_status(source_status) and locally_reproduced:
        raise ClaimAuditError(f"{row_id} external source marked local")
    if not is_local_source_status(source_status, object_class) and locally_reproduced:
        raise ClaimAuditError(f"{row_id} non-local status marked reproduced")
    if "statement" in object_class and (native_equivalent or proof_size_comparable):
        raise ClaimAuditError(f"{row_id} compact statement promoted as proof")
    if "paper_reported" in object_class and (locally_reproduced or proof_size_comparable or matched_workload):
        raise ClaimAuditError(f"{row_id} paper-reported row promoted")
    if object_class.startswith("external_lookup") and (locally_reproduced or proof_size_comparable):
        raise ClaimAuditError(f"{row_id} external lookup row promoted")
    if object_class.startswith("local_external_gkr") and matched_workload:
        raise ClaimAuditError(f"{row_id} GKR fixture promoted to matched workload")
    if native_equivalent and not (
        object_class == "local_two_proof_transformer_block_frontier"
        and row["system"] == "Stwo/STARK"
        and source_status.startswith("local")
    ):
        raise ClaimAuditError(f"{row_id} native equivalence overclaim")
    if proof_size_comparable and not (locally_reproduced and matched_workload and native_equivalent):
        raise ClaimAuditError(f"{row_id} proof-size comparability overclaim")
    if "not_reported" in proof_size_policy and proof_size_comparable:
        raise ClaimAuditError(f"{row_id} proof size not reported but comparable")
    metric_lower = require_str(row["primary_metric"], f"{row_id} metric").lower()
    if ("time" in metric_lower or metric_lower.endswith("_seconds")) and "not local" not in timing_policy and "repo_reported" not in timing_policy:
        raise ClaimAuditError(f"{row_id} timing policy missing source qualifier")
    if timing_policy in {"", "NA", "unknown"}:
        raise ClaimAuditError(f"{row_id} timing policy missing")
    if row_id == "rmsnorm_single_best_label_rejected" and "single best label rejected" not in proof_size_policy:
        raise ClaimAuditError("favorable-label policy drift")
    if row_id == "rmsnorm_worst_label_opening_target" and row["primary_value"] != 1401:
        raise ClaimAuditError("worst-label required reduction drift")
    required_non_claims = REQUIRED_ROW_NON_CLAIMS.get(row_id, ())
    for required in required_non_claims:
        if required not in non_claims:
            raise ClaimAuditError(f"{row_id} exact non-claim missing: {required}")


def validate_payload(payload: dict[str, Any], *, final: bool = True) -> None:
    expected = {
        "schema",
        "decision",
        "result",
        "issue",
        "audit_rows",
        "summary",
        "source_artifacts",
        "non_claims",
        "validation_commands",
        "mutation_results",
        "mutation_count",
        "mutations_rejected",
        "payload_commitment",
    }
    if final and set(payload) != expected:
        raise ClaimAuditError("payload field drift")
    if payload.get("schema") != SCHEMA:
        raise ClaimAuditError("schema drift")
    if payload.get("decision") != DECISION:
        raise ClaimAuditError("decision drift")
    if payload.get("result") != RESULT:
        raise ClaimAuditError("result drift")
    validate_non_claim_inventory(payload)
    validate_source_artifacts(require_list(payload.get("source_artifacts"), "source artifacts"))
    rows = require_list(payload.get("audit_rows"), "audit rows")
    row_ids = [require_str(require_dict(row, "audit row").get("row_id"), "row id") for row in rows]
    if len(row_ids) != len(set(row_ids)):
        raise ClaimAuditError("duplicate audit row id")
    for row in rows:
        validate_row(require_dict(row, "audit row"))
    summary = require_dict(payload.get("summary"), "summary")
    if summary.get("audit_row_count") != len(rows):
        raise ClaimAuditError("audit row count drift")
    if summary.get("object_class_count") != len({require_str(row["object_class"], "object class") for row in rows}):
        raise ClaimAuditError("object class count drift")
    if summary.get("proof_size_comparable_rows") != 0:
        raise ClaimAuditError("proof-size comparable row drift")
    if final:
        mutation_results = require_list(payload.get("mutation_results"), "mutation results")
        mutation_count = require_int(payload.get("mutation_count"), "mutation count")
        mutations_rejected = require_int(payload.get("mutations_rejected"), "mutations rejected")
        if mutation_count != len(MUTATIONS) or len(mutation_results) != len(MUTATIONS):
            raise ClaimAuditError("mutation inventory drift")
        if mutations_rejected != len(MUTATIONS):
            raise ClaimAuditError("mutation rejection drift")
        if any(result.get("accepted") is not False for result in mutation_results if isinstance(result, dict)):
            raise ClaimAuditError("mutation accepted")
        if payload.get("payload_commitment") != payload_commitment(payload):
            raise ClaimAuditError("payload commitment drift")


def base_payload(sources: dict[str, Any]) -> dict[str, Any]:
    raw_sources = require_dict(sources["raw"], "raw sources")
    rows = build_audit_rows(sources)
    source_artifacts = [
        source_descriptor(MINIMAL_BENCHMARK, require_dict(sources["minimal"], "minimal"), require_bytes(raw_sources["minimal"], "minimal raw")),
        source_descriptor(GKR_BASELINE, require_dict(sources["gkr"], "GKR"), require_bytes(raw_sources["gkr"], "GKR raw")),
        source_descriptor(JOLT_ATLAS_COMPARISON, require_dict(sources["jolt"], "Jolt"), require_bytes(raw_sources["jolt"], "Jolt raw")),
        source_descriptor(TABLERO_BOUNDARY, require_dict(sources["tablero"], "Tablero"), require_bytes(raw_sources["tablero"], "Tablero raw")),
        source_descriptor(LABEL_POLICY, require_dict(sources["label_policy"], "label policy"), require_bytes(raw_sources["label_policy"], "label policy raw")),
        source_descriptor(OPENING_BUDGET, require_dict(sources["opening_budget"], "opening budget"), require_bytes(raw_sources["opening_budget"], "opening budget raw")),
        source_descriptor(ADJACENT_LAYOUT, require_dict(sources["adjacent_layout"], "adjacent layout"), require_bytes(raw_sources["adjacent_layout"], "adjacent layout raw")),
    ]
    summary = {
        "audit_row_count": len(rows),
        "object_class_count": len({row["object_class"] for row in rows}),
        "locally_reproduced_rows": sum(1 for row in rows if row["locally_reproduced"]),
        "external_or_source_reported_rows": sum(1 for row in rows if is_external_source_status(row["source_status"])),
        "proof_size_comparable_rows": sum(1 for row in rows if row["proof_size_comparable"]),
        "native_equivalent_rows": sum(1 for row in rows if row["native_proof_equivalent"]),
        "stwo_two_proof_frontier_typed_bytes": row_by_id(rows, "local_stwo_two_proof_frontier")["primary_value"],
        "nanozk_paper_reported_bytes": row_by_id(rows, "nanozk_paper_reported_context")["primary_value"],
        "gkr_tiny_gemm_proof_bytes": row_by_id(rows, "gkr_tiny_gemm_sidecar")["primary_value"],
        "gkr_tiny_residual_add_proof_bytes": row_by_id(rows, "gkr_tiny_residual_add_heavier_shape")["primary_value"],
        "gkr_tiny_layernorm_proof_bytes": row_by_id(rows, "gkr_tiny_layernorm_heavier_shape")["primary_value"],
        "worst_label_required_reduction_bytes": row_by_id(rows, "rmsnorm_worst_label_opening_target")["primary_value"],
        "claim_audit_role": "prevent_false_cross_object_class_comparisons",
    }
    return {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "audit_rows": rows,
        "summary": summary,
        "source_artifacts": source_artifacts,
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }


def require_bytes(value: Any, label: str) -> bytes:
    if not isinstance(value, bytes):
        raise ClaimAuditError(f"{label} must be bytes")
    return value


def mutate_compact_statement_as_native(payload: dict[str, Any]) -> None:
    row_by_id(payload["audit_rows"], "tablero_compact_statement_boundary")["native_proof_equivalent"] = True


def mutate_nanozk_marked_local(payload: dict[str, Any]) -> None:
    row = row_by_id(payload["audit_rows"], "nanozk_paper_reported_context")
    row["source_status"] = "local_checked"
    row["locally_reproduced"] = True


def mutate_jolt_proof_size_comparable(payload: dict[str, Any]) -> None:
    row_by_id(payload["audit_rows"], "jolt_atlas_self_attention_reproduction_target")["proof_size_comparable"] = True


def mutate_gkr_matched_d128(payload: dict[str, Any]) -> None:
    row = row_by_id(payload["audit_rows"], "gkr_tiny_gemm_sidecar")
    row["matched_workload"] = True
    row["proof_size_comparable"] = True


def mutate_missing_object_class(payload: dict[str, Any]) -> None:
    del row_by_id(payload["audit_rows"], "local_stwo_two_proof_frontier")["object_class"]


def mutate_missing_timing_policy(payload: dict[str, Any]) -> None:
    row_by_id(payload["audit_rows"], "jolt_atlas_repo_gpt2_timing_context")["timing_policy"] = ""


def mutate_unqualified_timing_policy(payload: dict[str, Any]) -> None:
    row_by_id(payload["audit_rows"], "jolt_atlas_repo_gpt2_timing_context")["timing_policy"] = "benchmark_timing"


def mutate_single_best_label_promoted(payload: dict[str, Any]) -> None:
    row_by_id(payload["audit_rows"], "rmsnorm_single_best_label_rejected")["proof_size_policy"] = "single best label accepted as frontier"


def remove_if_present(values: list[str], value: str) -> None:
    if value in values:
        values.remove(value)


def mutate_remove_nanozk_non_claim(payload: dict[str, Any]) -> None:
    remove_if_present(payload["non_claims"], "not a NANOZK proof-size win")


def mutate_remove_jolt_non_claim(payload: dict[str, Any]) -> None:
    remove_if_present(payload["non_claims"], "not a Jolt Atlas proof-size win")


def mutate_remove_gkr_non_claim(payload: dict[str, Any]) -> None:
    remove_if_present(payload["non_claims"], "not a GKR matched d128 proof-size win")


def mutate_remove_gkr_row_non_claim(payload: dict[str, Any]) -> None:
    remove_if_present(row_by_id(payload["audit_rows"], "gkr_tiny_gemm_sidecar")["non_claims"], "not a GKR matched d128 proof-size win")


def mutate_unlisted_local_source_status(payload: dict[str, Any]) -> None:
    row_by_id(payload["audit_rows"], "local_stwo_two_proof_frontier")["source_status"] = "GO_UNLISTED_LOCAL_BYPASS"


def mutate_external_native_equivalence(payload: dict[str, Any]) -> None:
    row_by_id(payload["audit_rows"], "gkr_tiny_gemm_sidecar")["native_proof_equivalent"] = True


def mutate_missing_proof_size_policy(payload: dict[str, Any]) -> None:
    row_by_id(payload["audit_rows"], "local_stwo_two_proof_frontier")["proof_size_policy"] = ""


def mutate_source_artifact_digest(payload: dict[str, Any]) -> None:
    payload["source_artifacts"][0]["file_sha256"] = "0" * 64
    payload["summary"]["audit_row_count"] = len(payload["audit_rows"])


MUTATIONS: tuple[tuple[str, Callable[[dict[str, Any]], None]], ...] = (
    ("compact_statement_as_native", mutate_compact_statement_as_native),
    ("nanozk_marked_local", mutate_nanozk_marked_local),
    ("jolt_proof_size_comparable", mutate_jolt_proof_size_comparable),
    ("gkr_matched_d128", mutate_gkr_matched_d128),
    ("missing_object_class", mutate_missing_object_class),
    ("missing_timing_policy", mutate_missing_timing_policy),
    ("unqualified_timing_policy", mutate_unqualified_timing_policy),
    ("single_best_label_promoted", mutate_single_best_label_promoted),
    ("remove_nanozk_non_claim", mutate_remove_nanozk_non_claim),
    ("remove_jolt_non_claim", mutate_remove_jolt_non_claim),
    ("remove_gkr_non_claim", mutate_remove_gkr_non_claim),
    ("remove_gkr_row_non_claim", mutate_remove_gkr_row_non_claim),
    ("unlisted_local_source_status", mutate_unlisted_local_source_status),
    ("external_native_equivalence", mutate_external_native_equivalence),
    ("missing_proof_size_policy", mutate_missing_proof_size_policy),
    ("source_artifact_digest", mutate_source_artifact_digest),
)


def run_mutations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for name, mutation in MUTATIONS:
        candidate = copy.deepcopy(payload)
        mutation(candidate)
        candidate["payload_commitment"] = payload_commitment(candidate)
        try:
            validate_payload(candidate, final=False)
        except ClaimAuditError as err:
            results.append({"name": name, "accepted": False, "reason": str(err)})
        else:
            results.append({"name": name, "accepted": True, "reason": "mutation accepted"})
    return results


def build_payload() -> dict[str, Any]:
    payload = base_payload(load_sources())
    mutation_results = run_mutations(payload)
    payload["mutation_results"] = mutation_results
    payload["mutation_count"] = len(mutation_results)
    payload["mutations_rejected"] = sum(1 for result in mutation_results if result["accepted"] is False)
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload)
    return payload


def tsv_text(payload: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=ROW_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in payload["audit_rows"]:
        writer.writerow({column: row[column] for column in ROW_COLUMNS})
    return output.getvalue()


def require_output_path(path: pathlib.Path | None, suffix: str, label: str) -> pathlib.Path | None:
    if path is None:
        return None
    resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    if resolved.suffix != suffix:
        raise ClaimAuditError(f"{label} output must use {suffix} suffix")
    if resolved in {source.resolve() for source in SOURCE_PATHS}:
        raise ClaimAuditError(f"{label} output cannot overwrite source artifact")
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as err:
        raise ClaimAuditError(f"{label} output outside repository") from err
    return resolved


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path | None, tsv_path: pathlib.Path | None) -> None:
    json_path = require_output_path(json_path, ".json", "JSON")
    tsv_path = require_output_path(tsv_path, ".tsv", "TSV")
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = json_path.with_suffix(json_path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(json_path)
    if tsv_path is not None:
        tsv_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = tsv_path.with_suffix(tsv_path.suffix + ".tmp")
        tmp.write_text(tsv_text(payload), encoding="utf-8")
        tmp.replace(tsv_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    args = parser.parse_args(argv)
    payload = build_payload()
    write_outputs(payload, args.write_json, args.write_tsv)
    print(
        json.dumps(
            {
                "audit_rows": payload["summary"]["audit_row_count"],
                "decision": payload["decision"],
                "mutations_rejected": payload["mutations_rejected"],
                "object_classes": payload["summary"]["object_class_count"],
                "proof_size_comparable_rows": payload["summary"]["proof_size_comparable_rows"],
                "result": payload["result"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
