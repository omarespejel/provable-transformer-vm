#!/usr/bin/env python3
"""Semantic EZKL same-surface export probe for bounded attention artifacts.

This is not an EZKL proof benchmark. It asks whether the checked bounded
attention source artifact exposes enough exact integer and statement-binding
structure to start an external export probe, and records when a candidate path
must be labeled semantic-neighbor instead of same-surface.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
import subprocess
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = (
    ROOT
    / "docs"
    / "engineering"
    / "evidence"
    / "zkai-attention-kv-stwo-native-d64-two-head-seq32-bounded-softmax-table-proof-2026-05.json"
)
DEFAULT_WRITE_DIR = ROOT / "target" / "zkai-ezkl-same-surface-d64-h2-seq32"
DEFAULT_NOTE = ROOT / "docs" / "engineering" / "zkai-proof-pressure-ezkl-same-surface-export-probe-2026-05.md"

SCHEMA = "zkai-attention-kv-ezkl-same-surface-export-probe-v1"
DECISION = "GO_SOURCE_SHAPE_CONFIRMED_NO_GO_DIRECT_SAME_SURFACE_BASELINE"
SOURCE_TARGET_ID = "attention-kv-d64-two-head-seq32-causal-mask-bounded-softmax-table-v1"
SOURCE_SCHEMA = "zkai-attention-kv-stwo-native-d64-two-head-seq32-bounded-softmax-table-air-proof-input-v1"
SOURCE_STATEMENT_VERSION = "zkai-attention-kv-stwo-native-d64-two-head-seq32-bounded-softmax-table-statement-v1"
SOURCE_VERIFIER_DOMAIN = "ptvm:zkai:attention-kv-stwo-native-d64-two-head-seq32-bounded-softmax-table:v1"
SOURCE_WEIGHT_POLICY = "exp2_half_gap_table_clipped_8_floor_division"
SOURCE_SEMANTICS = "bounded_table_softmax_approx_attention"
SOURCE_MASKING_POLICY = "causal_prefix_position_lte_query_token"

TSV_COLUMNS = (
    "candidate_adapter",
    "gate",
    "same_surface_claim",
    "proof_generated",
    "primary_blocker",
    "next_action",
)
SOURCE_SHAPE_TSV_COLUMNS = (
    "field",
    "value",
)


class SameSurfaceExportProbeError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def blake2b_commitment(value: Any, domain: str) -> str:
    digest = hashlib.blake2b(digest_size=32)
    digest.update(domain.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(value))
    return f"blake2b-256:{digest.hexdigest()}"


def display_path(path: pathlib.Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def git_commit() -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"
    return completed.stdout.strip() or "unavailable"


def load_source(path: pathlib.Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as err:
        raise SameSurfaceExportProbeError(f"failed to read source artifact: {err}") from err
    except json.JSONDecodeError as err:
        raise SameSurfaceExportProbeError(f"failed to decode source artifact JSON: {err}") from err
    if not isinstance(payload, dict):
        raise SameSurfaceExportProbeError("source artifact must be a JSON object")
    return payload


def source_shape(source: dict[str, Any], source_path: pathlib.Path) -> dict[str, Any]:
    required_scalars = {
        "schema": SOURCE_SCHEMA,
        "target_id": SOURCE_TARGET_ID,
        "statement_version": SOURCE_STATEMENT_VERSION,
        "verifier_domain": SOURCE_VERIFIER_DOMAIN,
        "weight_policy": SOURCE_WEIGHT_POLICY,
        "semantics": SOURCE_SEMANTICS,
        "masking_policy": SOURCE_MASKING_POLICY,
        "head_count": 2,
        "sequence_length": 32,
        "key_width": 64,
        "value_width": 64,
        "score_row_count": 1184,
        "trace_row_count": 2048,
    }
    for key, expected in required_scalars.items():
        if source.get(key) != expected:
            raise SameSurfaceExportProbeError(f"source scalar drift for {key}")

    score_rows = source.get("score_rows")
    input_steps = source.get("input_steps")
    attention_outputs = source.get("attention_outputs")
    weight_table = source.get("weight_table")
    if not isinstance(score_rows, list) or len(score_rows) != source["score_row_count"]:
        raise SameSurfaceExportProbeError("score_row_count drift")
    expected_step_count = source["head_count"] * source["sequence_length"]
    if not isinstance(input_steps, list) or len(input_steps) != expected_step_count:
        raise SameSurfaceExportProbeError("input_steps shape drift")
    if not isinstance(attention_outputs, list) or len(attention_outputs) != expected_step_count:
        raise SameSurfaceExportProbeError("attention_outputs row-count drift")
    if any(not isinstance(row, list) or len(row) != source["value_width"] for row in attention_outputs):
        raise SameSurfaceExportProbeError("attention_outputs width drift")
    if not isinstance(weight_table, list) or len(weight_table) != 9:
        raise SameSurfaceExportProbeError("weight_table shape drift")

    required_commitments = (
        "input_steps_commitment",
        "outputs_commitment",
        "public_instance_commitment",
        "score_row_commitment",
        "statement_commitment",
        "weight_table_commitment",
    )
    for key in required_commitments:
        value = source.get(key)
        if not isinstance(value, str) or not value.startswith("blake2b-256:"):
            raise SameSurfaceExportProbeError(f"missing or invalid commitment field {key}")

    non_claims = source.get("non_claims")
    if not isinstance(non_claims, list) or "not exact Softmax attention" not in non_claims:
        raise SameSurfaceExportProbeError("source non-claims drift")
    if "not full transformer inference" not in non_claims:
        raise SameSurfaceExportProbeError("source full-inference non-claim drift")

    return {
        "source_path": display_path(source_path),
        "source_sha256": sha256_file(source_path),
        "schema": source["schema"],
        "target_id": source["target_id"],
        "statement_version": source["statement_version"],
        "verifier_domain": source["verifier_domain"],
        "head_count": source["head_count"],
        "sequence_length": source["sequence_length"],
        "key_width": source["key_width"],
        "value_width": source["value_width"],
        "score_row_count": source["score_row_count"],
        "trace_row_count": source["trace_row_count"],
        "input_step_count": len(input_steps),
        "attention_output_shape": [len(attention_outputs), source["value_width"]],
        "weight_table_entries": len(weight_table),
        "weight_policy": source["weight_policy"],
        "semantics": source["semantics"],
        "masking_policy": source["masking_policy"],
        "commitments": {key: source[key] for key in required_commitments},
        "non_claim_count": len(non_claims),
    }


def equality_conditions() -> list[str]:
    return [
        "row_shape_and_ordering",
        "head_count",
        "sequence_length",
        "key_width",
        "value_width",
        "bounded_score_policy",
        "softmax_table_weight_policy",
        "output_rounding_policy",
        "public_input_commitment",
        "public_output_commitment",
        "model_or_kernel_identifier",
        "verifier_domain",
        "statement_non_claims",
    ]


def candidate_adapters() -> list[dict[str, Any]]:
    return [
        {
            "candidate_adapter": "vanilla_onnx_ezkl_direct_export",
            "gate": "NO_GO_SAME_SURFACE_TODAY",
            "same_surface_claim": "NO_GO",
            "proof_generated": False,
            "primary_blocker": "no_checked_export_preserves_integer_table_policy_and_statement_bindings",
            "next_action": "Do not add a paper baseline row from vanilla ONNX export.",
        },
        {
            "candidate_adapter": "custom_integer_table_ezkl_export_probe",
            "gate": "IMPLEMENT_PROBE_NEXT",
            "same_surface_claim": "NOT_CHECKED",
            "proof_generated": False,
            "primary_blocker": "requires_custom_export_that_preserves_table_policy_rounding_and_public_outputs",
            "next_action": "Build only the semantic exporter first; fail closed before proving.",
        },
        {
            "candidate_adapter": "float_onnx_semantic_neighbor",
            "gate": "NO_GO_FOR_SAME_SURFACE",
            "same_surface_claim": "NO_GO",
            "proof_generated": False,
            "primary_blocker": "float_export_would_define_a_different_statement",
            "next_action": "Use only under a new approximate-statement target with separate non-claims.",
        },
        {
            "candidate_adapter": "zkvm_receipt_fallback",
            "gate": "GO_FOR_RECEIPT_BASELINE_NOT_PROOF_BOUNDARY_BASELINE",
            "same_surface_claim": "SEMANTIC_CONTROL_ONLY",
            "proof_generated": False,
            "primary_blocker": "receipt_bytes_are_not_a_matched_proof_boundary_comparator",
            "next_action": "Use for statement-binding control if EZKL cannot preserve the exact surface.",
        },
    ]


def expected_non_claims() -> list[str]:
    return [
        "not an EZKL proof-generation benchmark",
        "not an EZKL verifier-time benchmark",
        "not a NANOZK comparison",
        "not a full transformer block comparison",
        "not evidence that EZKL is unsuitable",
        "not a public performance claim",
    ]


def build_probe(source_path: pathlib.Path = DEFAULT_SOURCE) -> dict[str, Any]:
    source = load_source(source_path)
    shape = source_shape(source, source_path)
    candidates = candidate_adapters()
    conditions = equality_conditions()
    non_claims = expected_non_claims()
    return {
        "schema": SCHEMA,
        "git_commit": git_commit(),
        "decision": DECISION,
        "source_shape": shape,
        "equality_conditions": conditions,
        "equality_conditions_commitment": blake2b_commitment(
            conditions,
            "ptvm:zkai:attention-kv-ezkl-same-surface-equality-conditions:v1",
        ),
        "candidate_adapters": candidates,
        "candidate_matrix_commitment": blake2b_commitment(
            candidates,
            "ptvm:zkai:attention-kv-ezkl-same-surface-candidates:v1",
        ),
        "prior_evidence": {
            "d64_external_adapter_surface_probe": "docs/engineering/zkai-d64-external-adapter-surface-probe-2026-05-01.md",
            "interpretation": "prior exact integer zkAI surface already recorded NO-GO for vanilla ONNX as a same-statement path",
        },
        "non_claims": non_claims,
    }


def validate_probe(payload: dict[str, Any], source_path: pathlib.Path = DEFAULT_SOURCE) -> None:
    expected_fields = {
        "schema",
        "git_commit",
        "decision",
        "source_shape",
        "equality_conditions",
        "equality_conditions_commitment",
        "candidate_adapters",
        "candidate_matrix_commitment",
        "prior_evidence",
        "non_claims",
    }
    if set(payload) != expected_fields:
        raise SameSurfaceExportProbeError("payload field set mismatch")
    if payload["schema"] != SCHEMA:
        raise SameSurfaceExportProbeError("schema mismatch")
    if payload["decision"] != DECISION:
        raise SameSurfaceExportProbeError("decision drift")
    if payload["source_shape"] != source_shape(load_source(source_path), source_path):
        raise SameSurfaceExportProbeError("source shape drift")
    if payload["equality_conditions"] != equality_conditions():
        raise SameSurfaceExportProbeError("equality conditions drift")
    if payload["equality_conditions_commitment"] != blake2b_commitment(
        equality_conditions(),
        "ptvm:zkai:attention-kv-ezkl-same-surface-equality-conditions:v1",
    ):
        raise SameSurfaceExportProbeError("equality conditions commitment drift")
    if payload["candidate_adapters"] != candidate_adapters():
        raise SameSurfaceExportProbeError("candidate adapter matrix drift")
    if payload["candidate_matrix_commitment"] != blake2b_commitment(
        candidate_adapters(),
        "ptvm:zkai:attention-kv-ezkl-same-surface-candidates:v1",
    ):
        raise SameSurfaceExportProbeError("candidate matrix commitment drift")
    for candidate in payload["candidate_adapters"]:
        if candidate["proof_generated"] is not False:
            raise SameSurfaceExportProbeError("probe must not claim proof generation")
    if payload["non_claims"] != expected_non_claims():
        raise SameSurfaceExportProbeError("non-claims drift")


def rows_for_tsv(payload: dict[str, Any], source_path: pathlib.Path = DEFAULT_SOURCE) -> list[dict[str, Any]]:
    validate_probe(payload, source_path)
    return [
        {
            "candidate_adapter": row["candidate_adapter"],
            "gate": row["gate"],
            "same_surface_claim": row["same_surface_claim"],
            "proof_generated": str(row["proof_generated"]).lower(),
            "primary_blocker": row["primary_blocker"],
            "next_action": row["next_action"],
        }
        for row in payload["candidate_adapters"]
    ]


def source_shape_rows(payload: dict[str, Any], source_path: pathlib.Path = DEFAULT_SOURCE) -> list[dict[str, str]]:
    validate_probe(payload, source_path)
    shape = payload["source_shape"]
    simple_fields = (
        "source_sha256",
        "schema",
        "target_id",
        "statement_version",
        "verifier_domain",
        "head_count",
        "sequence_length",
        "key_width",
        "value_width",
        "score_row_count",
        "trace_row_count",
        "input_step_count",
        "attention_output_shape",
        "weight_table_entries",
        "weight_policy",
        "semantics",
        "masking_policy",
        "non_claim_count",
    )
    return [{"field": key, "value": json.dumps(shape[key], sort_keys=True)} for key in simple_fields]


def render_note(payload: dict[str, Any], source_path: pathlib.Path = DEFAULT_SOURCE) -> str:
    validate_probe(payload, source_path)
    shape = payload["source_shape"]
    return f"""# EZKL Same-Surface Export Probe for Bounded Attention

Issue: #751

## Decision

`{payload["decision"]}`

The checked source artifact has enough typed structure to start a semantic EZKL
export probe, but it is not yet an external baseline row for the proof-pressure
paper. A direct vanilla ONNX path remains `NO_GO` for same-surface comparison
until it preserves the bounded integer table policy, public-output semantics,
and statement binding.

## Source Shape

- source: `{shape["source_path"]}`
- source sha256: `{shape["source_sha256"]}`
- target: `{shape["target_id"]}`
- heads: `{shape["head_count"]}`
- sequence length: `{shape["sequence_length"]}`
- key width: `{shape["key_width"]}`
- value width: `{shape["value_width"]}`
- score rows: `{shape["score_row_count"]}`
- trace rows: `{shape["trace_row_count"]}`
- input steps: `{shape["input_step_count"]}`
- attention output shape: `{shape["attention_output_shape"][0]} x {shape["attention_output_shape"][1]}`
- weight table entries: `{shape["weight_table_entries"]}`
- weight policy: `{shape["weight_policy"]}`
- semantics: `{shape["semantics"]}`
- verifier domain: `{shape["verifier_domain"]}`

## Candidate Matrix

| candidate | gate | same-surface claim | proof generated | blocker |
|---|---|---|---|---|
{chr(10).join(f"| `{row['candidate_adapter']}` | `{row['gate']}` | `{row['same_surface_claim']}` | `{str(row['proof_generated']).lower()}` | {row['primary_blocker']} |" for row in payload["candidate_adapters"])}

## Prior Evidence

The earlier `d64` external-adapter surface probe already recorded `NO-GO` for a
vanilla ONNX path as an exact same-statement proof route on an integer zkAI
surface:

`docs/engineering/zkai-d64-external-adapter-surface-probe-2026-05-01.md`

This attention probe is still worth doing, but it inherits the same rule: if
export changes table policy, rounding, public outputs, commitments, or
verifier-domain meaning, label it semantic-neighbor rather than same-surface.

## Non-Claims

{chr(10).join(f"- {item}" for item in payload["non_claims"])}

## Reproduce

```bash
python3 scripts/zkai_attention_kv_ezkl_same_surface_export_probe.py \\
  --source {shape["source_path"]} \\
  --write-dir target/zkai-ezkl-same-surface-d64-h2-seq32 \\
  --write-note docs/engineering/zkai-proof-pressure-ezkl-same-surface-export-probe-2026-05.md
```
"""


def write_outputs(payload: dict[str, Any], write_dir: pathlib.Path, write_note: pathlib.Path, source_path: pathlib.Path) -> None:
    validate_probe(payload, source_path)
    try:
        write_dir.mkdir(parents=True, exist_ok=True)
        (write_dir / "probe.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with (write_dir / "adapter_matrix.tsv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows_for_tsv(payload, source_path))
        with (write_dir / "source_shape.tsv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=SOURCE_SHAPE_TSV_COLUMNS, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(source_shape_rows(payload, source_path))
        write_note.parent.mkdir(parents=True, exist_ok=True)
        write_note.write_text(render_note(payload, source_path), encoding="utf-8")
    except OSError as err:
        raise SameSurfaceExportProbeError(f"failed to write probe outputs: {err}") from err


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=pathlib.Path, default=DEFAULT_SOURCE)
    parser.add_argument("--write-dir", type=pathlib.Path, default=DEFAULT_WRITE_DIR)
    parser.add_argument("--write-note", type=pathlib.Path, default=DEFAULT_NOTE)
    parser.add_argument("--json", action="store_true", help="print the full probe payload")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_path = args.source
    if not source_path.is_absolute():
        source_path = ROOT / source_path
    write_dir = args.write_dir if args.write_dir.is_absolute() else ROOT / args.write_dir
    write_note = args.write_note if args.write_note.is_absolute() else ROOT / args.write_note
    payload = build_probe(source_path)
    validate_probe(payload, source_path)
    write_outputs(payload, write_dir, write_note, source_path)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps({"schema": SCHEMA, "decision": payload["decision"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
