#!/usr/bin/env python3
"""Gate value compatibility for the larger native attention+MLP boundary."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import contextlib
import copy
import csv
import hashlib
import io
import json
import os
import pathlib
import sys
import tempfile
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"

D8_ATTENTION_PATH = EVIDENCE_DIR / "zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json"
SEQ32_ATTENTION_PATH = (
    EVIDENCE_DIR / "zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json"
)
MLP_INPUT_PATH = EVIDENCE_DIR / "zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json"
SELECTOR_PATH = EVIDENCE_DIR / "zkai-larger-native-boundary-candidate-selector-2026-05.json"

JSON_OUT = EVIDENCE_DIR / "zkai-larger-native-boundary-source-compatibility-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-larger-native-boundary-source-compatibility-2026-05.tsv"

SCHEMA = "zkai-larger-native-boundary-source-compatibility-gate-v1"
DECISION = "NO_GO_CURRENT_D128_MLP_INPUT_NOT_VALUE_COMPATIBLE_WITH_TWO_HEAD_SEQ32_ATTENTION"
RESULT = "REGENERATE_SEQ32_DERIVED_D128_MLP_SURFACE_BEFORE_NATIVE_PROOF_OBJECT"
ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/673"
PAYLOAD_DOMAIN = "ptvm:zkai:larger-native-boundary-source-compatibility:v1"

ADAPTER_PRIMARY_COEFF = 9
ADAPTER_MIX_COEFF = 5
ADAPTER_DENOMINATOR = 8
ADAPTER_ROWS = 128

EXPECTED = {
    "d8_adapter_mismatches": 0,
    "d8_adapter_matches": 128,
    "d8_attention_output_rows": 8,
    "d8_attention_flat_cells": 64,
    "seq32_adapter_mismatches": 113,
    "seq32_adapter_matches": 15,
    "seq32_attention_output_rows": 64,
    "seq32_attention_flat_cells": 512,
    "mlp_rmsnorm_input_rows": 128,
    "selected_route": "two_head_seq32_fused_attention",
    "selected_lookup_claims": 1184,
    "selected_attention_typed_bytes": 22916,
    "selected_mlp_typed_bytes": 22576,
    "matched_two_proof_frontier_typed_bytes": 45492,
}

NON_CLAIMS = (
    "not a native larger-boundary proof object",
    "not proof-size savings",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not a full transformer block proof",
    "not permission to ignore adapter value binding",
    "not a reason to promote the seq32 selector to an implementation result",
)

VALIDATION_COMMANDS = (
    "python3 scripts/zkai_larger_native_boundary_source_compatibility_gate.py --write-json docs/engineering/evidence/zkai-larger-native-boundary-source-compatibility-2026-05.json --write-tsv docs/engineering/evidence/zkai-larger-native-boundary-source-compatibility-2026-05.tsv",
    "python3 -m py_compile scripts/zkai_larger_native_boundary_source_compatibility_gate.py scripts/tests/test_zkai_larger_native_boundary_source_compatibility_gate.py",
    "python3 -m unittest scripts.tests.test_zkai_larger_native_boundary_source_compatibility_gate",
    "python3 scripts/research_issue_lint.py --repo-root .",
    "python3 scripts/paper/paper_preflight.py --repo-root .",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

TSV_COLUMNS = (
    "decision",
    "result",
    "d8_adapter_mismatches",
    "seq32_adapter_mismatches",
    "seq32_adapter_matches",
    "mismatch_share",
    "selected_lookup_claims",
    "selected_attention_typed_bytes",
    "matched_two_proof_frontier_typed_bytes",
)

CORE_KEYS = {
    "schema",
    "decision",
    "result",
    "issue",
    "source_artifacts",
    "adapter_policy",
    "summary",
    "selector_context",
    "interpretation",
    "non_claims",
    "validation_commands",
    "source_commitment",
    "payload_commitment",
}
MUTATION_KEYS = {"mutation_result", "mutation_inventory"}
FINAL_KEYS = CORE_KEYS | MUTATION_KEYS

MUTATION_NAMES = (
    "decision_promoted_to_go",
    "seq32_mismatch_count_drift",
    "d8_control_mismatch_drift",
    "matched_frontier_drift",
    "selected_route_drift",
    "native_proof_object_overclaim",
    "adapter_binding_ignored",
    "missing_non_claim",
    "source_commitment_drift",
    "payload_commitment_drift",
)

EXPECTED_MUTATION_REASONS = {
    "decision_promoted_to_go": "decision drift",
    "seq32_mismatch_count_drift": "summary.seq32_adapter_mismatches drift",
    "d8_control_mismatch_drift": "summary.d8_adapter_mismatches drift",
    "matched_frontier_drift": "selector_context.matched_two_proof_frontier_typed_bytes drift",
    "selected_route_drift": "selector_context.selected_route drift",
    "native_proof_object_overclaim": "interpretation.native_larger_boundary_proof_object_exists drift",
    "adapter_binding_ignored": "interpretation.adapter_value_binding_preserved drift",
    "missing_non_claim": "non-claims drift",
    "source_commitment_drift": "source commitment drift",
    "payload_commitment_drift": "payload commitment drift",
}


class LargerNativeBoundaryCompatibilityError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode(
            "utf-8"
        )
    except (TypeError, ValueError) as err:
        raise LargerNativeBoundaryCompatibilityError(f"invalid JSON value: {err}") from err


def read_json_and_raw(path: pathlib.Path, label: str) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
    except OSError as err:
        raise LargerNativeBoundaryCompatibilityError(f"failed to read {label}: {err}") from err
    try:
        return json.loads(raw), raw
    except json.JSONDecodeError as err:
        raise LargerNativeBoundaryCompatibilityError(f"failed to parse {label}: {err}") from err


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LargerNativeBoundaryCompatibilityError(f"{label} must be object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise LargerNativeBoundaryCompatibilityError(f"{label} must be list")
    return value


def require_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise LargerNativeBoundaryCompatibilityError(f"{label} must be integer")
    return value


def require_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise LargerNativeBoundaryCompatibilityError(f"{label} must be non-empty string")
    return value


def source_artifact(artifact_id: str, path: pathlib.Path, payload: Any, raw: bytes) -> dict[str, Any]:
    relative = path.relative_to(ROOT).as_posix()
    return {
        "id": artifact_id,
        "path": relative,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "schema": require_str(require_dict(payload, artifact_id).get("schema"), f"{artifact_id}.schema")
        if "schema" in require_dict(payload, artifact_id)
        else None,
    }


def flat_attention_outputs(payload: dict[str, Any], label: str) -> list[int]:
    rows = require_list(payload.get("attention_outputs"), f"{label}.attention_outputs")
    flat: list[int] = []
    for row_index, row in enumerate(rows):
        values = require_list(row, f"{label}.attention_outputs[{row_index}]")
        for value_index, value in enumerate(values):
            flat.append(require_int(value, f"{label}.attention_outputs[{row_index}][{value_index}]"))
    return flat


def mlp_rmsnorm_inputs(payload: dict[str, Any]) -> list[int]:
    rmsnorm = require_dict(payload.get("rmsnorm_input"), "mlp.rmsnorm_input")
    rows = require_list(rmsnorm.get("rows"), "mlp.rmsnorm_input.rows")
    values = []
    for row_index, row in enumerate(rows):
        row_payload = require_dict(row, f"mlp.rmsnorm_input.rows[{row_index}]")
        values.append(require_int(row_payload.get("input_q8"), f"mlp.rmsnorm_input.rows[{row_index}].input_q8"))
    return values


def adapter_bias_q8(index: int) -> int:
    return ((7 * index + 3) % 9) - 4


def adapter_projection(flat_outputs: list[int], target_rows: int = ADAPTER_ROWS) -> list[dict[str, int]]:
    if not flat_outputs:
        raise LargerNativeBoundaryCompatibilityError("attention output vector is empty")
    rows = []
    for row_index in range(target_rows):
        primary_source_index = row_index % len(flat_outputs)
        mix_source_index = (17 * row_index + 11) % len(flat_outputs)
        primary_q8 = flat_outputs[primary_source_index]
        mix_q8 = flat_outputs[mix_source_index]
        bias_q8 = adapter_bias_q8(row_index)
        numerator_q8 = ADAPTER_PRIMARY_COEFF * primary_q8 + ADAPTER_MIX_COEFF * mix_q8 + bias_q8
        output_q8 = numerator_q8 // ADAPTER_DENOMINATOR
        remainder_q8 = numerator_q8 % ADAPTER_DENOMINATOR
        rows.append(
            {
                "row_index": row_index,
                "primary_source_index": primary_source_index,
                "mix_source_index": mix_source_index,
                "primary_q8": primary_q8,
                "mix_q8": mix_q8,
                "bias_q8": bias_q8,
                "numerator_q8": numerator_q8,
                "output_q8": output_q8,
                "floor_remainder_q8": remainder_q8,
            }
        )
    return rows


def mismatch_summary(flat_outputs: list[int], mlp_inputs: list[int]) -> dict[str, Any]:
    projected = adapter_projection(flat_outputs, len(mlp_inputs))
    mismatches = []
    if len(projected) != len(mlp_inputs):
        raise LargerNativeBoundaryCompatibilityError("adapter projection row count drift")
    for projected_row, expected in zip(projected, mlp_inputs):
        if projected_row["output_q8"] != expected:
            mismatch = dict(projected_row)
            mismatch["expected_mlp_input_q8"] = expected
            mismatches.append(mismatch)
    return {
        "matches": len(mlp_inputs) - len(mismatches),
        "mismatches": len(mismatches),
        "mismatch_share": round(len(mismatches) / len(mlp_inputs), 6),
        "first_mismatches": mismatches[:10],
    }


def selector_context(selector: dict[str, Any]) -> dict[str, Any]:
    summary = require_dict(selector.get("summary"), "selector.summary")
    return {
        "selected_route": require_str(summary.get("selected_candidate"), "selector selected candidate id"),
        "selected_lookup_claims": require_int(summary.get("selected_lookup_claims"), "selector lookup claims"),
        "selected_attention_typed_bytes": require_int(
            summary.get("selected_attention_typed_bytes"), "selector attention typed bytes"
        ),
        "selected_mlp_typed_bytes": EXPECTED["selected_mlp_typed_bytes"],
        "matched_two_proof_frontier_typed_bytes": require_int(
            summary.get("selected_matched_two_proof_frontier_typed_bytes"), "selector frontier"
        ),
    }


def source_commitment(payload: dict[str, Any]) -> str:
    material = {
        "adapter_policy": payload["adapter_policy"],
        "source_artifacts": payload["source_artifacts"],
        "selector_context": payload["selector_context"],
        "summary": payload["summary"],
    }
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("utf-8"))
    digest.update(b"\0source\0")
    digest.update(canonical_json_bytes(material))
    return "blake2b-256:" + digest.hexdigest()


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    return "sha256:" + hashlib.sha256(canonical_json_bytes(material)).hexdigest()


def refresh_payload_commitments(payload: dict[str, Any]) -> None:
    payload["source_commitment"] = source_commitment(payload)
    payload["payload_commitment"] = payload_commitment(payload)


def build_context() -> dict[str, Any]:
    d8, d8_raw = read_json_and_raw(D8_ATTENTION_PATH, "d8 attention input")
    seq32, seq32_raw = read_json_and_raw(SEQ32_ATTENTION_PATH, "seq32 attention input")
    mlp, mlp_raw = read_json_and_raw(MLP_INPUT_PATH, "d128 MLP input")
    selector, selector_raw = read_json_and_raw(SELECTOR_PATH, "larger native boundary selector")
    return {
        "d8": require_dict(d8, "d8 attention input"),
        "d8_raw": d8_raw,
        "seq32": require_dict(seq32, "seq32 attention input"),
        "seq32_raw": seq32_raw,
        "mlp": require_dict(mlp, "d128 MLP input"),
        "mlp_raw": mlp_raw,
        "selector": require_dict(selector, "selector"),
        "selector_raw": selector_raw,
    }


def build_payload(context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or build_context()
    d8_flat = flat_attention_outputs(context["d8"], "d8")
    seq32_flat = flat_attention_outputs(context["seq32"], "seq32")
    mlp_inputs = mlp_rmsnorm_inputs(context["mlp"])
    d8_summary = mismatch_summary(d8_flat, mlp_inputs)
    seq32_summary = mismatch_summary(seq32_flat, mlp_inputs)
    selector = selector_context(context["selector"])
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "source_artifacts": [
            source_artifact("d8_attention_control", D8_ATTENTION_PATH, context["d8"], context["d8_raw"]),
            source_artifact("two_head_seq32_attention_candidate", SEQ32_ATTENTION_PATH, context["seq32"], context["seq32_raw"]),
            source_artifact("attention_derived_d128_mlp_input", MLP_INPUT_PATH, context["mlp"], context["mlp_raw"]),
            source_artifact("larger_native_boundary_selector", SELECTOR_PATH, context["selector"], context["selector_raw"]),
        ],
        "adapter_policy": {
            "row_count": ADAPTER_ROWS,
            "primary_coeff": ADAPTER_PRIMARY_COEFF,
            "mix_coeff": ADAPTER_MIX_COEFF,
            "denominator": ADAPTER_DENOMINATOR,
            "bias": "((7 * row_index + 3) % 9) - 4",
            "source_index_policy": "primary=row_index%flat_attention_cells; mix=(17*row_index+11)%flat_attention_cells",
        },
        "summary": {
            "d8_attention_output_rows": len(require_list(context["d8"].get("attention_outputs"), "d8.attention_outputs")),
            "d8_attention_flat_cells": len(d8_flat),
            "d8_adapter_matches": d8_summary["matches"],
            "d8_adapter_mismatches": d8_summary["mismatches"],
            "seq32_attention_output_rows": len(
                require_list(context["seq32"].get("attention_outputs"), "seq32.attention_outputs")
            ),
            "seq32_attention_flat_cells": len(seq32_flat),
            "seq32_adapter_matches": seq32_summary["matches"],
            "seq32_adapter_mismatches": seq32_summary["mismatches"],
            "seq32_mismatch_share": seq32_summary["mismatch_share"],
            "mlp_rmsnorm_input_rows": len(mlp_inputs),
            "first_seq32_mismatches": seq32_summary["first_mismatches"],
        },
        "selector_context": selector,
        "interpretation": {
            "native_larger_boundary_proof_object_exists": False,
            "adapter_value_binding_preserved": False,
            "why_no_go": (
                "The current d128 RMSNorm/MLP input is value-derived from the d8 attention control, "
                "not from the selected two-head seq32 attention candidate."
            ),
            "next_experiment": "regenerate a seq32-derived d128 RMSNorm/MLP input, then retry the larger native proof object",
        },
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    refresh_payload_commitments(payload)
    payload["mutation_result"] = mutation_result(payload)
    payload["mutation_inventory"] = {"cases": list(MUTATION_NAMES)}
    refresh_payload_commitments(payload)
    validate_payload(payload)
    return payload


def expect_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise LargerNativeBoundaryCompatibilityError(f"{label} drift")


def validate_payload(payload: dict[str, Any]) -> None:
    if set(payload) != FINAL_KEYS:
        raise LargerNativeBoundaryCompatibilityError("top-level key drift")
    expect_equal(payload["schema"], SCHEMA, "schema")
    expect_equal(payload["decision"], DECISION, "decision")
    expect_equal(payload["result"], RESULT, "result")
    expect_equal(payload["issue"], ISSUE, "issue")
    expect_equal(payload["non_claims"], list(NON_CLAIMS), "non-claims")
    expect_equal(payload["validation_commands"], list(VALIDATION_COMMANDS), "validation commands")

    summary = require_dict(payload["summary"], "summary")
    for key in (
        "d8_adapter_mismatches",
        "d8_adapter_matches",
        "d8_attention_output_rows",
        "d8_attention_flat_cells",
        "seq32_adapter_mismatches",
        "seq32_adapter_matches",
        "seq32_attention_output_rows",
        "seq32_attention_flat_cells",
        "mlp_rmsnorm_input_rows",
    ):
        expect_equal(require_int(summary.get(key), f"summary.{key}"), EXPECTED[key], f"summary.{key}")
    expect_equal(summary.get("seq32_mismatch_share"), round(EXPECTED["seq32_adapter_mismatches"] / ADAPTER_ROWS, 6), "summary.seq32_mismatch_share")

    selector = require_dict(payload["selector_context"], "selector_context")
    for key in (
        "selected_route",
        "selected_lookup_claims",
        "selected_attention_typed_bytes",
        "selected_mlp_typed_bytes",
        "matched_two_proof_frontier_typed_bytes",
    ):
        expect_equal(selector.get(key), EXPECTED[key], f"selector_context.{key}")

    interpretation = require_dict(payload["interpretation"], "interpretation")
    expect_equal(
        interpretation.get("native_larger_boundary_proof_object_exists"),
        False,
        "interpretation.native_larger_boundary_proof_object_exists",
    )
    expect_equal(
        interpretation.get("adapter_value_binding_preserved"),
        False,
        "interpretation.adapter_value_binding_preserved",
    )

    expected_source_commitment = source_commitment(payload)
    if payload["source_commitment"] != expected_source_commitment:
        raise LargerNativeBoundaryCompatibilityError("source commitment drift")
    expected_payload_commitment = payload_commitment(payload)
    if payload["payload_commitment"] != expected_payload_commitment:
        raise LargerNativeBoundaryCompatibilityError("payload commitment drift")

    mutation_result = require_dict(payload["mutation_result"], "mutation_result")
    cases = require_list(mutation_result.get("cases"), "mutation_result.cases")
    expect_equal([case["name"] for case in cases], list(MUTATION_NAMES), "mutation case order")
    for case in cases:
        name = require_str(require_dict(case, "mutation case").get("name"), "mutation case name")
        expect_equal(case.get("rejected"), True, f"mutation {name}.rejected")
        expect_equal(case.get("reason"), EXPECTED_MUTATION_REASONS[name], f"mutation {name}.reason")
    inventory = require_dict(payload["mutation_inventory"], "mutation_inventory")
    expect_equal(inventory.get("cases"), list(MUTATION_NAMES), "mutation inventory")


def mutate(payload: dict[str, Any], name: str) -> dict[str, Any]:
    mutated = copy.deepcopy(payload)
    mutated.pop("mutation_result", None)
    mutated.pop("mutation_inventory", None)
    if name == "decision_promoted_to_go":
        mutated["decision"] = "GO_NATIVE_LARGER_BOUNDARY_PROOF_OBJECT_READY"
    elif name == "seq32_mismatch_count_drift":
        mutated["summary"]["seq32_adapter_mismatches"] -= 1
    elif name == "d8_control_mismatch_drift":
        mutated["summary"]["d8_adapter_mismatches"] = 1
    elif name == "matched_frontier_drift":
        mutated["selector_context"]["matched_two_proof_frontier_typed_bytes"] = 40700
    elif name == "selected_route_drift":
        mutated["selector_context"]["selected_route"] = "d8_fused_attention"
    elif name == "native_proof_object_overclaim":
        mutated["interpretation"]["native_larger_boundary_proof_object_exists"] = True
    elif name == "adapter_binding_ignored":
        mutated["interpretation"]["adapter_value_binding_preserved"] = True
    elif name == "missing_non_claim":
        mutated["non_claims"] = [claim for claim in mutated["non_claims"] if claim != "not permission to ignore adapter value binding"]
    elif name == "source_commitment_drift":
        mutated["source_commitment"] = "blake2b-256:" + "0" * 64
        mutated["payload_commitment"] = payload_commitment(mutated)
        return mutated
    elif name == "payload_commitment_drift":
        mutated["payload_commitment"] = "sha256:" + "0" * 64
        return mutated
    else:
        raise AssertionError(f"unknown mutation {name}")
    refresh_payload_commitments(mutated)
    return mutated


def mutation_result(payload: dict[str, Any]) -> dict[str, Any]:
    cases = []
    for name in MUTATION_NAMES:
        mutated = mutate(payload, name)
        try:
            validate_payload({**mutated, "mutation_result": {"cases": []}, "mutation_inventory": {"cases": []}})
        except LargerNativeBoundaryCompatibilityError as err:
            cases.append({"name": name, "rejected": True, "reason": str(err)})
        else:
            cases.append({"name": name, "rejected": False, "reason": "accepted"})
    return {"cases": cases}


def output_path(path: pathlib.Path, label: str) -> pathlib.Path:
    raw_path = path if path.is_absolute() else ROOT / path
    if raw_path.is_symlink():
        raise LargerNativeBoundaryCompatibilityError(f"{label} must not be a symlink: {raw_path}")
    if EVIDENCE_DIR.is_symlink():
        raise LargerNativeBoundaryCompatibilityError(f"evidence directory must not be a symlink: {EVIDENCE_DIR}")
    try:
        root = ROOT.resolve(strict=True)
        evidence = EVIDENCE_DIR.resolve(strict=True)
        parent = raw_path.parent.resolve(strict=True)
    except OSError as err:
        raise LargerNativeBoundaryCompatibilityError(f"failed to resolve {label}: {err}") from err
    if not evidence.is_relative_to(root):
        raise LargerNativeBoundaryCompatibilityError(f"evidence directory escapes repo root: {EVIDENCE_DIR}")
    if parent != evidence:
        raise LargerNativeBoundaryCompatibilityError(f"{label} escapes evidence directory")
    if raw_path.exists() and raw_path.is_dir():
        raise LargerNativeBoundaryCompatibilityError(f"{label} must be a file: {raw_path}")
    return raw_path


def write_text_atomic(path: pathlib.Path, text: str) -> None:
    target = output_path(path, "output path")
    tmp_path: pathlib.Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            tmp_path = pathlib.Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        tmp_path.replace(target)
        try:
            dir_fd = os.open(target.parent, os.O_RDONLY)
        except OSError:
            dir_fd = None
        if dir_fd is not None:
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
    except OSError as err:
        if tmp_path is not None:
            with contextlib.suppress(OSError):
                tmp_path.unlink()
        raise LargerNativeBoundaryCompatibilityError(f"failed to write {target}: {err}") from err


def write_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    validate_payload(payload)
    write_text_atomic(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def to_tsv(payload: dict[str, Any]) -> str:
    validate_payload(payload)
    summary = payload["summary"]
    selector = payload["selector_context"]
    row = {
        "decision": payload["decision"],
        "result": payload["result"],
        "d8_adapter_mismatches": summary["d8_adapter_mismatches"],
        "seq32_adapter_mismatches": summary["seq32_adapter_mismatches"],
        "seq32_adapter_matches": summary["seq32_adapter_matches"],
        "mismatch_share": summary["seq32_mismatch_share"],
        "selected_lookup_claims": selector["selected_lookup_claims"],
        "selected_attention_typed_bytes": selector["selected_attention_typed_bytes"],
        "matched_two_proof_frontier_typed_bytes": selector["matched_two_proof_frontier_typed_bytes"],
    }
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerow(row)
    return out.getvalue()


def write_tsv(path: pathlib.Path, payload: dict[str, Any]) -> None:
    validate_payload(payload)
    write_text_atomic(path, to_tsv(payload))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload()
    if args.write_json:
        write_json(args.write_json, payload)
    if args.write_tsv:
        write_tsv(args.write_tsv, payload)
    if not args.write_json and not args.write_tsv:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
