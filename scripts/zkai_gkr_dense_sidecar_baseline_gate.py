#!/usr/bin/env python3
"""Gate the GKR/Expander dense-layer sidecar baseline for issue #650."""

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
JSON_OUT = EVIDENCE_DIR / "zkai-gkr-dense-sidecar-baseline-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-gkr-dense-sidecar-baseline-2026-05.tsv"

MINIMAL_BENCHMARK = EVIDENCE_DIR / "zkai-minimal-transformer-block-benchmark-2026-05.json"
JSTPROVE_SHAPE_PROBE = EVIDENCE_DIR / "zkai-jstprove-shape-probe-2026-05.json"
JSTPROVE_STATEMENT_ENVELOPE = EVIDENCE_DIR / "zkai-jstprove-statement-envelope-benchmark-2026-05.json"
SOURCE_PATHS = (MINIMAL_BENCHMARK, JSTPROVE_SHAPE_PROBE, JSTPROVE_STATEMENT_ENVELOPE)

SCHEMA = "zkai-gkr-dense-sidecar-baseline-v1"
DECISION = "GO_GKR_SIDECAR_BASELINE_NO_GO_MATCHED_D128_DENSE_LAYER_COMPARISON"
RESULT = "LOCAL_GKR_ARTIFACTS_EXIST_FOR_TINY_SHAPES_BUT_NOT_MATCHED_D128_TRANSFORMER_LAYER"
ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/650"
PAYLOAD_DOMAIN = "ptvm:zkai:gkr-dense-sidecar-baseline:v1"

PRIMARY_SOURCES = (
    {
        "label": "Polyhedra Expander GKR protocol docs",
        "url": "https://docs.polyhedra.network/expander/prover_internals/gkr",
        "role": "primary docs for GKR/layered-circuit framing",
    },
    {
        "label": "PolyhedraZK/Expander",
        "url": "https://github.com/PolyhedraZK/Expander",
        "role": "open-source GKR prover implementation context",
    },
    {
        "label": "JSTprove arXiv",
        "url": "https://arxiv.org/abs/2510.21024",
        "role": "JSTprove/Remainder zkML toolkit context",
    },
)

NON_CLAIMS = (
    "not a NANOZK proof-size win",
    "not a Jolt or Atlas benchmark win",
    "not a matched d128 transformer-block proof",
    "not a full transformer proof",
    "not a claim that GKR replaces Stwo",
    "not a claim that JSTprove proves our exact RMSNorm/SwiGLU component",
    "not timing evidence beyond previously recorded local fixture timings",
    "not model-faithful accuracy evidence",
)

VALIDATION_COMMANDS = (
    "python3 scripts/zkai_gkr_dense_sidecar_baseline_gate.py --write-json docs/engineering/evidence/zkai-gkr-dense-sidecar-baseline-2026-05.json --write-tsv docs/engineering/evidence/zkai-gkr-dense-sidecar-baseline-2026-05.tsv",
    "python3 -m py_compile scripts/zkai_gkr_dense_sidecar_baseline_gate.py scripts/tests/test_zkai_gkr_dense_sidecar_baseline_gate.py",
    "python3 -m unittest scripts.tests.test_zkai_gkr_dense_sidecar_baseline_gate",
    "python3 scripts/research_issue_lint.py --repo-root .",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

ROW_COLUMNS = (
    "row_id",
    "proof_system",
    "object_class",
    "workload",
    "status",
    "primary_metric",
    "primary_value",
    "prove_seconds",
    "verify_seconds",
    "comparability",
    "evidence_path",
)

BASELINE_KEYS = (
    "schema",
    "decision",
    "result",
    "issue",
    "selected_dense_surface",
    "rows",
    "summary",
    "source_artifacts",
    "primary_sources",
    "non_claims",
    "validation_commands",
)


class GkrDenseBaselineError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    except (TypeError, ValueError) as err:
        raise GkrDenseBaselineError(f"invalid JSON value: {err}") from err


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
    except Exception as err:  # noqa: BLE001 - normalize imported gate errors for this gate.
        raise GkrDenseBaselineError(str(err)) from err
    return payload, raw


def load_sources() -> dict[str, Any]:
    minimal, minimal_raw = load_source(MINIMAL_BENCHMARK)
    shape, shape_raw = load_source(JSTPROVE_SHAPE_PROBE)
    envelope, envelope_raw = load_source(JSTPROVE_STATEMENT_ENVELOPE)
    if minimal.get("schema") != "zkai-minimal-transformer-block-benchmark-v1":
        raise GkrDenseBaselineError("minimal benchmark schema drift")
    if shape.get("schema") != "zkai-jstprove-shape-probe-v1":
        raise GkrDenseBaselineError("JSTprove shape schema drift")
    if envelope.get("schema") != "zkai-jstprove-statement-envelope-benchmark-v1":
        raise GkrDenseBaselineError("JSTprove envelope schema drift")
    return {
        "minimal": minimal,
        "shape": shape,
        "envelope": envelope,
        "raw": {
            "minimal": minimal_raw,
            "shape": shape_raw,
            "envelope": envelope_raw,
        },
    }


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GkrDenseBaselineError(f"{label} must be an object")
    return value


def require_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise GkrDenseBaselineError(f"{label} must be an integer")
    return value


def require_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise GkrDenseBaselineError(f"{label} must be a non-empty string")
    return value


def ratio(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        raise GkrDenseBaselineError("ratio denominator must be positive")
    return f"{numerator / denominator:.6f}"


def row_by_component(rows: list[dict[str, Any]], component: str) -> dict[str, Any]:
    for row in rows:
        if row.get("component") == component:
            return row
    raise GkrDenseBaselineError(f"component row missing: {component}")


def require_row_by_id(rows: list[dict[str, Any]], row_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get("row_id") == row_id:
            return row
    raise GkrDenseBaselineError(f"missing summary row: {row_id}")


def shape_result_by_fixture(results: list[Any], fixture: str) -> dict[str, Any]:
    for row in results:
        if isinstance(row, dict) and row.get("fixture") == fixture:
            return row
    raise GkrDenseBaselineError(f"JSTprove fixture missing: {fixture}")


def result_row(result: dict[str, Any], *, comparability: str) -> dict[str, Any]:
    status = require_str(result.get("status"), "fixture status")
    proof_bytes = result.get("proof_bytes")
    if status == "GO":
        primary_metric = "proof_bytes"
        primary_value = require_int(proof_bytes, "fixture proof bytes")
    else:
        primary_metric = require_str(result.get("failure_kind"), "fixture failure kind")
        primary_value = None
    return {
        "row_id": require_str(result.get("fixture"), "fixture"),
        "proof_system": "JSTprove/Remainder-GKR-sumcheck",
        "object_class": "local_external_gkr_fixture",
        "workload": require_str(result.get("op_sequence"), "fixture op sequence"),
        "status": status,
        "primary_metric": primary_metric,
        "primary_value": primary_value,
        "prove_seconds": require_str(result.get("prove_seconds"), "fixture prove seconds"),
        "verify_seconds": require_str(result.get("verify_seconds"), "fixture verify seconds"),
        "comparability": comparability,
        "evidence_path": str(JSTPROVE_SHAPE_PROBE.relative_to(ROOT)),
    }


def build_rows(sources: dict[str, Any]) -> list[dict[str, Any]]:
    minimal = sources["minimal"]
    shape = sources["shape"]
    component_rows = minimal["component_rows"]
    stwo_dense = row_by_component(component_rows, "rmsnorm_mlp_residual_substitute")
    stwo_dense_bytes = require_int(stwo_dense.get("primary_value"), "Stwo dense typed bytes")
    results = shape.get("results")
    if not isinstance(results, list):
        raise GkrDenseBaselineError("JSTprove results must be a list")
    tiny_gemm = shape_result_by_fixture(results, "tiny_gemm")
    gemm_add = shape_result_by_fixture(results, "tiny_gemm_add")
    residual = shape_result_by_fixture(results, "tiny_gemm_residual_add")
    layernorm = shape_result_by_fixture(results, "tiny_gemm_layernorm")
    batchnorm = shape_result_by_fixture(results, "tiny_gemm_batchnorm")
    relu = shape_result_by_fixture(results, "tiny_gemm_relu")
    softmax = shape_result_by_fixture(results, "tiny_gemm_softmax")
    matmul = shape_result_by_fixture(results, "tiny_matmul_residual_add")
    envelope_summary = require_dict(sources["envelope"].get("summary"), "JSTprove envelope summary")
    statement_summary = require_dict(envelope_summary.get("jstprove-statement-envelope"), "statement envelope summary")
    return [
        {
            "row_id": "local_stwo_dense_substitute",
            "proof_system": "Stwo/STARK",
            "object_class": require_str(stwo_dense.get("object_class"), "Stwo dense object class"),
            "workload": "d128 RMSNorm/SwiGLU/down/residual substitute component",
            "status": "LOCAL_COMPONENT_FRONTIER",
            "primary_metric": require_str(stwo_dense.get("primary_metric"), "Stwo dense primary metric"),
            "primary_value": stwo_dense_bytes,
            "prove_seconds": "NA",
            "verify_seconds": "NA",
            "comparability": "LOCAL_STWO_TYPED_ACCOUNTING_NOT_MATCHED_GKR_WORKLOAD",
            "evidence_path": str(MINIMAL_BENCHMARK.relative_to(ROOT)),
        },
        result_row(tiny_gemm, comparability="TINY_LINEAR_PROJECTION_ONLY_NOT_D128_MLP"),
        result_row(gemm_add, comparability="TINY_LINEAR_PLUS_ADD_SHAPE_NOT_D128_MLP"),
        result_row(residual, comparability="TINY_RESIDUAL_ADD_SHAPE_NOT_D128_MLP"),
        result_row(layernorm, comparability="TINY_NORMALIZATION_SHAPE_NOT_OUR_RMSNORM_COMPONENT"),
        result_row(batchnorm, comparability="TINY_NORMALIZATION_LIKE_SHAPE_NOT_OUR_RMSNORM_COMPONENT"),
        result_row(relu, comparability="NO_GO_ACTIVATION_RANGE_CHECK_CAPACITY"),
        result_row(softmax, comparability="NO_GO_UNCONSTRAINED_SOFTMAX_BACKEND_OP"),
        result_row(matmul, comparability="NO_GO_LITERAL_MATMUL_WITNESS_UNSUPPORTED"),
        {
            "row_id": "jstprove_statement_envelope_binding",
            "proof_system": "JSTprove/Remainder-GKR-sumcheck",
            "object_class": "external_statement_binding_adapter",
            "workload": "tiny_gemm statement-envelope relabeling adapter",
            "status": "GO_STATEMENT_ENVELOPE_REJECTS_RELABELING",
            "primary_metric": "mutations_rejected",
            "primary_value": require_int(statement_summary.get("mutations_rejected"), "statement mutations rejected"),
            "prove_seconds": "NA",
            "verify_seconds": "NA",
            "comparability": "STATEMENT_BINDING_ONLY_NOT_DENSE_LAYER_PROOF_SIZE",
            "evidence_path": str(JSTPROVE_STATEMENT_ENVELOPE.relative_to(ROOT)),
        },
    ]


def build_summary(rows: list[dict[str, Any]], sources: dict[str, Any]) -> dict[str, Any]:
    stwo = require_row_by_id(rows, "local_stwo_dense_substitute")
    tiny = require_row_by_id(rows, "tiny_gemm")
    residual = require_row_by_id(rows, "tiny_gemm_residual_add")
    layernorm = require_row_by_id(rows, "tiny_gemm_layernorm")
    stwo_bytes = require_int(stwo.get("primary_value"), "Stwo dense summary typed bytes")
    tiny_bytes = require_int(tiny.get("primary_value"), "tiny_gemm summary proof bytes")
    residual_bytes = require_int(residual.get("primary_value"), "residual summary proof bytes")
    layernorm_bytes = require_int(layernorm.get("primary_value"), "layernorm summary proof bytes")
    go_rows = [row for row in rows if row["status"].startswith("GO") or row["status"] == "LOCAL_COMPONENT_FRONTIER"]
    no_go_rows = [row for row in rows if row["status"] == "NO_GO"]
    shape_conclusion = require_dict(sources["shape"].get("conclusion"), "shape conclusion")
    source_go_count = require_int(shape_conclusion.get("go_count"), "shape go_count")
    source_no_go_count = require_int(shape_conclusion.get("no_go_count"), "shape no_go_count")
    shape_fixture_rows = [row for row in rows if row["object_class"] == "local_external_gkr_fixture"]
    derived_go_count = sum(1 for row in shape_fixture_rows if row["status"] == "GO")
    derived_no_go_count = sum(1 for row in shape_fixture_rows if row["status"] == "NO_GO")
    if source_go_count != derived_go_count or source_no_go_count != derived_no_go_count:
        raise GkrDenseBaselineError("shape conclusion fixture counts drift")
    return {
        "local_stwo_dense_typed_bytes": stwo_bytes,
        "jstprove_tiny_gemm_proof_bytes": tiny_bytes,
        "jstprove_tiny_gemm_ratio_vs_stwo_dense_typed": ratio(tiny_bytes, stwo_bytes),
        "jstprove_residual_add_proof_bytes": residual_bytes,
        "jstprove_residual_add_ratio_vs_stwo_dense_typed": ratio(residual_bytes, stwo_bytes),
        "jstprove_layernorm_proof_bytes": layernorm_bytes,
        "jstprove_layernorm_ratio_vs_stwo_dense_typed": ratio(layernorm_bytes, stwo_bytes),
        "local_gkr_go_fixture_count": source_go_count,
        "local_gkr_no_go_fixture_count": source_no_go_count,
        "comparison_rows": len(rows),
        "go_rows": len(go_rows),
        "no_go_rows": len(no_go_rows),
        "sidecar_candidate": "YES_FOR_TINY_PROJECTION_RESIDUAL_NORMALIZATION_EXPLORATION",
        "matched_d128_dense_layer_comparison": False,
        "gkr_route_classification": "SIDECAR_OR_BASELINE_CANDIDATE_NOT_STWO_REPLACEMENT",
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
        "selected_dense_surface": {
            "local_component": "rmsnorm_mlp_residual_substitute",
            "local_metric": "derived_mlp_fused_typed_bytes",
            "local_evidence": str(MINIMAL_BENCHMARK.relative_to(ROOT)),
            "external_candidate": "JSTprove/Remainder-GKR tiny Gemm/residual/normalization fixtures",
            "object_class_policy": "context and sidecar feasibility only until a matched d128 dense-layer proof exists",
        },
        "rows": rows,
        "summary": build_summary(rows, sources),
        "source_artifacts": [
            source_descriptor(MINIMAL_BENCHMARK, sources["minimal"], raw_sources["minimal"]),
            source_descriptor(JSTPROVE_SHAPE_PROBE, sources["shape"], raw_sources["shape"]),
            source_descriptor(JSTPROVE_STATEMENT_ENVELOPE, sources["envelope"], raw_sources["envelope"]),
        ],
        "primary_sources": list(PRIMARY_SOURCES),
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }


def validate_payload(payload: dict[str, Any], *, require_mutations: bool = True) -> None:
    expected_keys = set(BASELINE_KEYS) | {"mutation_results", "mutation_count", "mutations_rejected", "payload_commitment"}
    if set(payload) != expected_keys:
        raise GkrDenseBaselineError("payload key drift")
    rows = payload["rows"]
    if not isinstance(rows, list) or len(rows) != 10:
        raise GkrDenseBaselineError("rows inventory drift")
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(ROW_COLUMNS):
            raise GkrDenseBaselineError("row schema drift")
        if row["comparability"] in {"MATCHED_EXTERNAL_BENCHMARK", "NANOZK_WIN", "GKR_REPLACES_STWO"}:
            raise GkrDenseBaselineError("rows comparison overclaim")
    if payload["summary"]["matched_d128_dense_layer_comparison"] is not False:
        raise GkrDenseBaselineError("matched comparison overclaim")
    if payload["summary"]["gkr_route_classification"] == "GKR_REPLACES_STWO":
        raise GkrDenseBaselineError("summary overclaim")
    if "not a matched d128 transformer-block proof" not in payload["non_claims"]:
        raise GkrDenseBaselineError("non-claim drift")
    expected = base_payload()
    for key in BASELINE_KEYS:
        if payload[key] != expected[key]:
            raise GkrDenseBaselineError(f"{key} drift")
    if require_mutations:
        validate_mutations(payload["mutation_results"])
        if payload["mutation_count"] != len(MUTATIONS) or payload["mutations_rejected"] != len(MUTATIONS):
            raise GkrDenseBaselineError("mutation count drift")
    else:
        if payload["mutation_results"] != [] or payload["mutation_count"] != 0 or payload["mutations_rejected"] != 0:
            raise GkrDenseBaselineError("unexpected mutation metadata")
    if payload["payload_commitment"] != payload_commitment(payload):
        raise GkrDenseBaselineError("payload commitment drift")


def promote_matched_comparison(payload: dict[str, Any]) -> None:
    payload["summary"]["matched_d128_dense_layer_comparison"] = True


def promote_gkr_replacement(payload: dict[str, Any]) -> None:
    payload["summary"]["gkr_route_classification"] = "GKR_REPLACES_STWO"


def promote_row_comparability(payload: dict[str, Any]) -> None:
    payload["rows"][1]["comparability"] = "MATCHED_EXTERNAL_BENCHMARK"


def mutate_tiny_gemm_bytes(payload: dict[str, Any]) -> None:
    payload["rows"][1]["primary_value"] += 1


def remove_softmax_no_go(payload: dict[str, Any]) -> None:
    payload["rows"] = [row for row in payload["rows"] if row["row_id"] != "tiny_gemm_softmax"]


def remove_non_claim(payload: dict[str, Any]) -> None:
    payload["non_claims"].remove("not a claim that GKR replaces Stwo")


MUTATIONS = (
    ("matched_comparison_overclaim", promote_matched_comparison),
    ("gkr_replacement_overclaim", promote_gkr_replacement),
    ("row_comparability_overclaim", promote_row_comparability),
    ("tiny_gemm_metric_drift", mutate_tiny_gemm_bytes),
    ("softmax_no_go_removal", remove_softmax_no_go),
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
        except GkrDenseBaselineError as err:
            results.append({"name": name, "rejected": True, "reason": str(err)})
        else:
            results.append({"name": name, "rejected": False, "reason": ""})
    return results


def validate_mutations(results: Any) -> None:
    if not isinstance(results, list) or len(results) != len(MUTATIONS):
        raise GkrDenseBaselineError("mutation result drift")
    expected_names = [name for name, _mutate in MUTATIONS]
    if [entry.get("name") for entry in results if isinstance(entry, dict)] != expected_names:
        raise GkrDenseBaselineError("mutation order drift")
    for entry in results:
        if not isinstance(entry, dict) or set(entry) != {"name", "rejected", "reason"}:
            raise GkrDenseBaselineError("mutation entry drift")
        if entry["rejected"] is not True or not entry["reason"]:
            raise GkrDenseBaselineError(f"mutation did not reject: {entry.get('name')}")


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


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path | None, tsv_path: pathlib.Path | None) -> None:
    json_target, tsv_target = validated_output_targets(payload, json_path, tsv_path)
    if json_target:
        minimal_gate.write_atomic(json_target, json.dumps(payload, indent=2, sort_keys=True).encode() + b"\n")
    if tsv_target:
        minimal_gate.write_atomic(tsv_target, tsv_text(payload).encode())


def normalized_output_target(path: pathlib.Path) -> pathlib.Path:
    try:
        return minimal_gate.normalize_output_path(path)
    except Exception as err:  # noqa: BLE001 - keep gate-specific public error type.
        raise GkrDenseBaselineError(str(err)) from err


def validated_output_targets(
    payload: dict[str, Any],
    json_path: pathlib.Path | None,
    tsv_path: pathlib.Path | None,
) -> tuple[pathlib.Path | None, pathlib.Path | None]:
    targets: list[tuple[str, pathlib.Path]] = []
    if json_path is not None:
        json_target = normalized_output_target(json_path)
        targets.append(("json", json_target))
    if tsv_path is not None:
        tsv_target = normalized_output_target(tsv_path)
        targets.append(("tsv", tsv_target))
    resolved_targets = [target for _label, target in targets]
    if len(set(resolved_targets)) != len(resolved_targets):
        raise GkrDenseBaselineError("output paths collide")
    for label, target in targets:
        if label == "json" and target.suffix != ".json":
            raise GkrDenseBaselineError(f"JSON output must use .json suffix: {target}")
        if label == "tsv" and target.suffix != ".tsv":
            raise GkrDenseBaselineError(f"TSV output must use .tsv suffix: {target}")
    source_paths = {path.resolve() for path in SOURCE_PATHS}
    source_paths |= {
        (ROOT / artifact["path"]).resolve()
        for artifact in payload.get("source_artifacts", [])
        if isinstance(artifact, dict) and isinstance(artifact.get("path"), str)
    }
    for label, target in targets:
        if target in source_paths:
            raise GkrDenseBaselineError(f"refusing to overwrite source artifact with {label} output: {target}")
    output_by_label = dict(targets)
    return output_by_label.get("json"), output_by_label.get("tsv")


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
                "local_stwo_dense_typed_bytes": payload["summary"]["local_stwo_dense_typed_bytes"],
                "jstprove_tiny_gemm_proof_bytes": payload["summary"]["jstprove_tiny_gemm_proof_bytes"],
                "matched_d128_dense_layer_comparison": payload["summary"]["matched_d128_dense_layer_comparison"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
