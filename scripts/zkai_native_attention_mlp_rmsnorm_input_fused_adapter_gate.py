#!/usr/bin/env python3
"""Gate the RMSNorm-input fused adapter proof-shape probe."""

from __future__ import annotations

import argparse
import contextlib
import copy
import csv
import hashlib
import io
import json
import os
import pathlib
import tempfile
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"

COMPACT_INPUT_PATH = (
    EVIDENCE_DIR / "zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.input.json"
)
COMPACT_ENVELOPE_PATH = (
    EVIDENCE_DIR / "zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json"
)
FUSED_INPUT_PATH = (
    EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.input.json"
)
FUSED_ENVELOPE_PATH = (
    EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json"
)
ACCOUNTING_PATH = (
    EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-input-fused-adapter-binary-accounting-2026-05.json"
)

JSON_OUT = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.tsv"

SCHEMA = "zkai-native-attention-mlp-rmsnorm-input-fused-adapter-gate-v1"
DECISION = "NO_GO_RMSNORM_INPUT_FUSED_ADAPTER_PROOF_SIZE_FRONTIER"
RESULT = "NO_GO_ZERO_ADAPTER_BASE_COLUMNS_STILL_INCREASE_TYPED_PROOF_BYTES"
ISSUE = "https://github.com/omarespejel/provable-transformer-vm/issues/641"
PAYLOAD_DOMAIN = "ptvm:zkai:native-attention-mlp-rmsnorm-input-fused-adapter:v1"
CLAIM_BOUNDARY = (
    "RMSNORM_INPUT_FUSED_ADAPTER_PROVES_AND_VERIFIES_WITH_ZERO_ADAPTER_BASE_COLUMNS_BUT_DOES_NOT_"
    "BEAT_THE_COMPACT_ADAPTER_OR_THE_TWO_PROOF_FRONTIER"
)

TWO_PROOF_FRONTIER_TYPED_BYTES = 40_700
TWO_PROOF_FRONTIER_JSON_BYTES = 116_258
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900

EXPECTED_VARIANTS = {
    "compact_selector": {
        "input_path": COMPACT_INPUT_PATH,
        "envelope_path": COMPACT_ENVELOPE_PATH,
        "accounting_relative_path": "zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json",
        "adapter_mode": "compact_base_referenced_fixed_v1",
        "adapter_status": "NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER_COMPACT_BASE_REFERENCED_FIXED_COLUMNS",
        "adapter_value_columns": 5,
        "adapter_trace_cells": 1_024,
        "proof_backend_version": "stwo-native-attention-mlp-single-proof-object-compact-adapter-selector-v1",
        "proof_json_size_bytes": 116_091,
        "typed_size_estimate_bytes": 40_812,
        "record_stream_sha256": "8ed8db52bfb240a2b742df9877aa8d01ece09334616540771812e28081c5d996",
    },
    "rmsnorm_input_fused": {
        "input_path": FUSED_INPUT_PATH,
        "envelope_path": FUSED_ENVELOPE_PATH,
        "accounting_relative_path": "zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_fixed_v1",
        "adapter_status": "NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER_FUSED_INTO_RMSNORM_INPUT_COMPONENT",
        "adapter_value_columns": 0,
        "adapter_trace_cells": 0,
        "proof_backend_version": "stwo-native-attention-mlp-single-proof-object-rmsnorm-input-fused-adapter-v1",
        "proof_json_size_bytes": 118_378,
        "typed_size_estimate_bytes": 41_428,
        "record_stream_sha256": "2f7f36ee6000173dea41ab684dab9a20f36f95277eeb7c9a749a98c185583d91",
    },
}
VARIANT_CONTEXT_PREFIX = {
    "compact_selector": "compact",
    "rmsnorm_input_fused": "fused",
}

EXPECTED_GROUP_DELTAS_FUSED_MINUS_COMPACT = {
    "fixed_overhead": 0,
    "fri_decommitments": 736,
    "fri_samples": 16,
    "oods_samples": -224,
    "queries_values": -168,
    "trace_decommitments": 256,
}
EXPECTED_TYPED_GROUP_KEYS = tuple(EXPECTED_GROUP_DELTAS_FUSED_MINUS_COMPACT)

NON_CLAIMS = (
    "not a proof-size improvement",
    "not a two-proof frontier beat",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not timing evidence",
    "not a full transformer block proof",
    "not production-ready zkML",
)

VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- build-input-rmsnorm-fused docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.input.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json > docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-binary-accounting-2026-05.json",
    "python3 scripts/zkai_native_attention_mlp_rmsnorm_input_fused_adapter_gate.py --write-json docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-attention-mlp-rmsnorm-input-fused-adapter-2026-05.tsv",
    "python3 -m unittest scripts.tests.test_zkai_native_attention_mlp_rmsnorm_input_fused_adapter_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_fused_adapter --lib",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend native_attention_mlp_single_proof --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

MUTATION_NAMES = (
    "fused_typed_bytes_drift",
    "compact_typed_bytes_drift",
    "fused_mode_relabeling",
    "zero_adapter_trace_cells_drift",
    "frontier_win_overclaim",
    "compact_win_overclaim",
    "nanozk_overclaim",
    "payload_commitment_drift",
)

TSV_COLUMNS = (
    "decision",
    "result",
    "compact_typed_bytes",
    "fused_typed_bytes",
    "fused_typed_delta_vs_compact_bytes",
    "fused_typed_delta_vs_two_proof_frontier_bytes",
    "compact_adapter_trace_cells",
    "fused_adapter_trace_cells",
    "fused_json_delta_vs_compact_bytes",
    "fused_group_delta_fixed_overhead_bytes",
    "fused_group_delta_fri_decommitments_bytes",
    "fused_group_delta_fri_samples_bytes",
    "fused_group_delta_oods_samples_bytes",
    "fused_group_delta_queries_values_bytes",
    "fused_group_delta_trace_decommitments_bytes",
)


class RmsnormInputFusedAdapterGateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode(
            "utf-8"
        )
    except (TypeError, ValueError) as err:
        raise RmsnormInputFusedAdapterGateError(f"invalid JSON value: {err}") from err


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return "blake2b-256:" + digest.hexdigest()


def refresh_payload_commitment(payload: dict[str, Any]) -> None:
    payload["payload_commitment"] = payload_commitment(payload)


def read_json(path: pathlib.Path) -> Any:
    try:
        with path.open("rb") as handle:
            return json.loads(handle.read().decode("utf-8"))
    except OSError as err:
        raise RmsnormInputFusedAdapterGateError(f"failed to read {path}: {err}") from err
    except json.JSONDecodeError as err:
        raise RmsnormInputFusedAdapterGateError(f"failed to parse {path}: {err}") from err


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RmsnormInputFusedAdapterGateError(f"{label} must be object")
    return value


def require_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise RmsnormInputFusedAdapterGateError(f"{label} must be integer")
    return value


def require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise RmsnormInputFusedAdapterGateError(f"{label} must be boolean")
    return value


def require_sha256_hex(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise RmsnormInputFusedAdapterGateError(f"{label} must be 64-character lowercase hex SHA-256")
    return value


def require_typed_groups(value: Any, label: str) -> dict[str, int]:
    groups = require_dict(value, label)
    expected_keys = set(EXPECTED_TYPED_GROUP_KEYS)
    if set(groups) != expected_keys:
        raise RmsnormInputFusedAdapterGateError(
            f"{label} key drift: got {sorted(groups)}, expected {sorted(expected_keys)}"
        )
    return {key: require_int(groups[key], f"{label} {key}") for key in EXPECTED_TYPED_GROUP_KEYS}


def build_context() -> dict[str, Any]:
    return {
        "compact_input": require_dict(read_json(COMPACT_INPUT_PATH), "compact input"),
        "compact_envelope": require_dict(read_json(COMPACT_ENVELOPE_PATH), "compact envelope"),
        "fused_input": require_dict(read_json(FUSED_INPUT_PATH), "fused input"),
        "fused_envelope": require_dict(read_json(FUSED_ENVELOPE_PATH), "fused envelope"),
        "accounting": require_dict(read_json(ACCOUNTING_PATH), "accounting"),
    }


def accounting_rows_by_path(accounting: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = accounting.get("rows")
    if not isinstance(rows, list):
        raise RmsnormInputFusedAdapterGateError("accounting rows must be list")
    by_path: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_dict = require_dict(row, "accounting row")
        path = row_dict.get("evidence_relative_path")
        if not isinstance(path, str) or not path:
            raise RmsnormInputFusedAdapterGateError("accounting row path must be non-empty string")
        if path in by_path:
            raise RmsnormInputFusedAdapterGateError(f"duplicate accounting row path: {path}")
        by_path[path] = row_dict
    expected = {variant["accounting_relative_path"] for variant in EXPECTED_VARIANTS.values()}
    if set(by_path) != expected:
        raise RmsnormInputFusedAdapterGateError(
            f"accounting row path drift: got {sorted(by_path)}, expected {sorted(expected)}"
        )
    return by_path


def variant_payload(name: str, context: dict[str, Any], rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    expected = EXPECTED_VARIANTS[name]
    try:
        context_prefix = VARIANT_CONTEXT_PREFIX[name]
    except KeyError as err:
        raise RmsnormInputFusedAdapterGateError(f"missing context prefix for variant: {name}") from err
    input_payload = context[f"{context_prefix}_input"]
    envelope = context[f"{context_prefix}_envelope"]
    row = rows[expected["accounting_relative_path"]]
    accounting = require_dict(row.get("local_binary_accounting"), f"{name} local accounting")
    groups = require_typed_groups(accounting.get("grouped_reconstruction"), f"{name} groups")
    typed_size = require_int(accounting.get("component_sum_bytes"), f"{name} typed bytes")
    proof_json_size = require_int(row.get("proof_json_size_bytes"), f"{name} proof JSON bytes")

    if input_payload.get("adapter_mode") != expected["adapter_mode"]:
        raise RmsnormInputFusedAdapterGateError(f"{name} adapter mode drift")
    if input_payload.get("adapter_status") != expected["adapter_status"]:
        raise RmsnormInputFusedAdapterGateError(f"{name} adapter status drift")
    if input_payload.get("adapter_value_columns") != expected["adapter_value_columns"]:
        raise RmsnormInputFusedAdapterGateError(f"{name} adapter value column drift")
    if input_payload.get("adapter_trace_cells") != expected["adapter_trace_cells"]:
        raise RmsnormInputFusedAdapterGateError(f"{name} adapter trace cell drift")
    if envelope.get("proof_backend_version") != expected["proof_backend_version"]:
        raise RmsnormInputFusedAdapterGateError(f"{name} backend version drift")
    if proof_json_size != expected["proof_json_size_bytes"]:
        raise RmsnormInputFusedAdapterGateError(f"{name} proof JSON size drift")
    if typed_size != expected["typed_size_estimate_bytes"]:
        raise RmsnormInputFusedAdapterGateError(f"{name} typed size drift")
    if accounting.get("record_stream_sha256") != expected["record_stream_sha256"]:
        raise RmsnormInputFusedAdapterGateError(f"{name} accounting record stream drift")
    proof_sha256 = require_sha256_hex(row.get("proof_sha256"), f"{name} proof_sha256")
    envelope_sha256 = require_sha256_hex(row.get("envelope_sha256"), f"{name} envelope_sha256")

    return {
        "name": name,
        "input_path": str(expected["input_path"].relative_to(ROOT)),
        "envelope_path": str(expected["envelope_path"].relative_to(ROOT)),
        "adapter_mode": expected["adapter_mode"],
        "adapter_status": expected["adapter_status"],
        "adapter_value_columns": expected["adapter_value_columns"],
        "adapter_trace_cells": expected["adapter_trace_cells"],
        "proof_backend_version": expected["proof_backend_version"],
        "proof_json_size_bytes": proof_json_size,
        "typed_size_estimate_bytes": typed_size,
        "typed_groups": groups,
        "record_stream_sha256": accounting["record_stream_sha256"],
        "proof_sha256": proof_sha256,
        "envelope_sha256": envelope_sha256,
    }


def build_payload(context: dict[str, Any] | None = None, *, include_mutations: bool = True) -> dict[str, Any]:
    if context is None:
        context = build_context()
    rows = accounting_rows_by_path(context["accounting"])
    compact = variant_payload("compact_selector", context, rows)
    fused = variant_payload("rmsnorm_input_fused", context, rows)

    fused_minus_compact = {
        key: require_int(fused["typed_groups"].get(key), f"fused group {key}")
        - require_int(compact["typed_groups"].get(key), f"compact group {key}")
        for key in EXPECTED_GROUP_DELTAS_FUSED_MINUS_COMPACT
    }
    if fused_minus_compact != EXPECTED_GROUP_DELTAS_FUSED_MINUS_COMPACT:
        raise RmsnormInputFusedAdapterGateError("typed group delta drift")

    summary = {
        "compact_typed_bytes": compact["typed_size_estimate_bytes"],
        "fused_typed_bytes": fused["typed_size_estimate_bytes"],
        "fused_typed_delta_vs_compact_bytes": fused["typed_size_estimate_bytes"]
        - compact["typed_size_estimate_bytes"],
        "fused_typed_delta_vs_two_proof_frontier_bytes": fused["typed_size_estimate_bytes"]
        - TWO_PROOF_FRONTIER_TYPED_BYTES,
        "compact_adapter_trace_cells": compact["adapter_trace_cells"],
        "fused_adapter_trace_cells": fused["adapter_trace_cells"],
        "fused_json_delta_vs_compact_bytes": fused["proof_json_size_bytes"] - compact["proof_json_size_bytes"],
        "fused_group_deltas_vs_compact": fused_minus_compact,
    }
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "claim_boundary": CLAIM_BOUNDARY,
        "variants": {
            "compact_selector": compact,
            "rmsnorm_input_fused": fused,
        },
        "comparisons": {
            "fused_vs_compact": {
                "typed_delta_bytes": summary["fused_typed_delta_vs_compact_bytes"],
                "proof_size_improvement_claimed": False,
            },
            "fused_vs_two_proof_frontier": {
                "frontier_typed_bytes": TWO_PROOF_FRONTIER_TYPED_BYTES,
                "frontier_json_bytes": TWO_PROOF_FRONTIER_JSON_BYTES,
                "typed_delta_bytes": summary["fused_typed_delta_vs_two_proof_frontier_bytes"],
                "frontier_win_claimed": False,
            },
            "fused_vs_nanozk_reported_row": {
                "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
                "workload_matched": False,
                "nanozk_win_claimed": False,
            },
        },
        "summary": summary,
        "interpretation": {
            "human_read": (
                "The RMSNorm-input fused adapter removes all adapter base trace cells and verifies, "
                "but it is 616 typed bytes larger than the compact adapter and 728 typed bytes above "
                "the current two-proof frontier. The saving from fewer queried values is outweighed by "
                "FRI and trace decommitment growth."
            ),
            "next_attack": (
                "Do not keep shrinking adapter cells in isolation; target opening/decommitment geometry "
                "or fuse the boundary into an existing component without adding a worse transcript shape."
            ),
        },
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    refresh_payload_commitment(payload)
    if include_mutations:
        payload["mutation_result"] = mutation_result(payload, context=context)
        refresh_payload_commitment(payload)
    return payload


def validate_payload(payload: dict[str, Any], *, context: dict[str, Any] | None = None) -> None:
    if context is None:
        context = build_context()
    summary = require_dict(payload.get("summary"), "summary")
    comparisons = require_dict(payload.get("comparisons"), "comparisons")
    fused_vs_compact = require_dict(comparisons.get("fused_vs_compact"), "fused_vs_compact")
    fused_vs_frontier = require_dict(
        comparisons.get("fused_vs_two_proof_frontier"),
        "fused_vs_two_proof_frontier",
    )
    fused_vs_nanozk = require_dict(
        comparisons.get("fused_vs_nanozk_reported_row"),
        "fused_vs_nanozk_reported_row",
    )
    fused_typed_bytes = require_int(summary.get("fused_typed_bytes"), "summary fused_typed_bytes")
    compact_typed_bytes = require_int(summary.get("compact_typed_bytes"), "summary compact_typed_bytes")
    if fused_typed_bytes <= compact_typed_bytes:
        raise RmsnormInputFusedAdapterGateError("fused proof-size win is not supported")
    if fused_typed_bytes <= TWO_PROOF_FRONTIER_TYPED_BYTES:
        raise RmsnormInputFusedAdapterGateError("two-proof frontier win is not supported")
    if require_bool(fused_vs_compact.get("proof_size_improvement_claimed"), "compact claim"):
        raise RmsnormInputFusedAdapterGateError("compact win overclaim")
    if require_bool(fused_vs_frontier.get("frontier_win_claimed"), "frontier claim"):
        raise RmsnormInputFusedAdapterGateError("frontier win overclaim")
    if require_bool(fused_vs_nanozk.get("nanozk_win_claimed"), "NANOZK claim"):
        raise RmsnormInputFusedAdapterGateError("NANOZK win overclaim")

    has_mutation_result = "mutation_result" in payload
    provided_mutation_result = payload.get("mutation_result")
    actual = copy.deepcopy(payload)
    actual.pop("mutation_result", None)
    actual.pop("payload_commitment", None)
    expected_payload = build_payload(context, include_mutations=False)
    expected_core = copy.deepcopy(expected_payload)
    expected_core.pop("payload_commitment", None)
    if actual != expected_core:
        raise RmsnormInputFusedAdapterGateError("payload body drift")
    if has_mutation_result and provided_mutation_result != mutation_result(expected_payload, context=context):
        raise RmsnormInputFusedAdapterGateError("mutation result drift")
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise RmsnormInputFusedAdapterGateError("payload commitment drift")


def mutation_result(payload: dict[str, Any], *, context: dict[str, Any] | None = None) -> dict[str, Any]:
    if context is None:
        context = build_context()
    cases = []
    for name in MUTATION_NAMES:
        candidate = copy.deepcopy(payload)
        candidate.pop("mutation_result", None)
        if name == "fused_typed_bytes_drift":
            candidate["summary"]["fused_typed_bytes"] -= 1
        elif name == "compact_typed_bytes_drift":
            candidate["summary"]["compact_typed_bytes"] += 1
        elif name == "fused_mode_relabeling":
            candidate["variants"]["rmsnorm_input_fused"]["adapter_mode"] = "compact_base_referenced_fixed_v1"
        elif name == "zero_adapter_trace_cells_drift":
            candidate["variants"]["rmsnorm_input_fused"]["adapter_trace_cells"] = 128
        elif name == "frontier_win_overclaim":
            candidate["comparisons"]["fused_vs_two_proof_frontier"]["frontier_win_claimed"] = True
        elif name == "compact_win_overclaim":
            candidate["comparisons"]["fused_vs_compact"]["proof_size_improvement_claimed"] = True
        elif name == "nanozk_overclaim":
            candidate["comparisons"]["fused_vs_nanozk_reported_row"]["nanozk_win_claimed"] = True
        elif name == "payload_commitment_drift":
            candidate["payload_commitment"] = "blake2b-256:" + "00" * 32
        else:
            raise AssertionError(name)
        if name != "payload_commitment_drift":
            refresh_payload_commitment(candidate)
        rejected = False
        try:
            validate_payload(candidate, context=context)
        except RmsnormInputFusedAdapterGateError:
            rejected = True
        cases.append({"name": name, "rejected": rejected})
    return {
        "mutation_count": len(cases),
        "rejected_count": sum(1 for case in cases if case["rejected"]),
        "cases": cases,
    }


def write_outputs(payload: dict[str, Any], json_path: pathlib.Path | None, tsv_path: pathlib.Path | None) -> None:
    if json_path is not None:
        write_text_atomically(json_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    if tsv_path is not None:
        row = {column: payload["summary"].get(column, payload.get(column, "")) for column in TSV_COLUMNS}
        row["decision"] = payload["decision"]
        row["result"] = payload["result"]
        group_deltas = require_dict(
            payload["summary"].get("fused_group_deltas_vs_compact"),
            "fused_group_deltas_vs_compact",
        )
        for key in EXPECTED_TYPED_GROUP_KEYS:
            row[f"fused_group_delta_{key}_bytes"] = require_int(group_deltas.get(key), f"group delta {key}")
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(
            buffer,
            fieldnames=TSV_COLUMNS,
            dialect="excel-tab",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerow(row)
        write_text_atomically(tsv_path, buffer.getvalue())


def write_text_atomically(path: pathlib.Path, text: str) -> None:
    if path.is_symlink():
        raise RmsnormInputFusedAdapterGateError(f"refusing to overwrite symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp: pathlib.Path | None = None
    try:
        fd, tmp_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            text=True,
        )
        tmp = pathlib.Path(tmp_name)
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except OSError as err:
        if tmp is not None:
            with contextlib.suppress(OSError):
                tmp.unlink()
        raise RmsnormInputFusedAdapterGateError(f"failed to write {path}: {err}") from err


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json", type=pathlib.Path, default=None)
    parser.add_argument("--write-tsv", type=pathlib.Path, default=None)
    args = parser.parse_args()
    payload = build_payload()
    validate_payload(payload)
    write_outputs(payload, args.write_json, args.write_tsv)
    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "decision": payload["decision"],
                "result": payload["result"],
                "fused_typed_bytes": payload["summary"]["fused_typed_bytes"],
                "fused_typed_delta_vs_compact_bytes": payload["summary"][
                    "fused_typed_delta_vs_compact_bytes"
                ],
                "fused_typed_delta_vs_two_proof_frontier_bytes": payload["summary"][
                    "fused_typed_delta_vs_two_proof_frontier_bytes"
                ],
                "mutation_rejections": payload["mutation_result"]["rejected_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
