#!/usr/bin/env python3.10
"""Gate expanded seq32 attention+MLP label probes against the adjacent frontier."""

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
from collections.abc import Callable
from typing import Any


if sys.version_info < (3, 10):
    raise RuntimeError(
        "zkai_native_seq32_attention_mlp_expanded_label_probe_gate requires Python 3.10+"
    )

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
RUST_SOURCE_PATH = ROOT / "src" / "stwo_backend" / "native_seq32_attention_mlp_single_proof.rs"
CLI_SOURCE_PATH = ROOT / "src" / "bin" / "zkai_native_seq32_attention_mlp_single_proof.rs"
ACCOUNTING_PATH = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-expanded-label-probe-accounting-2026-05.json"
JSON_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-expanded-label-probe-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-seq32-attention-mlp-expanded-label-probe-2026-05.tsv"

SCHEMA = "zkai-native-seq32-attention-mlp-expanded-label-probe-gate-v1"
DECISION = "NO_GO_EXPANDED_LABEL_PROBES_DO_NOT_BEAT_ADJACENT_PROBE_B_FRONTIER"
RESULT = "FOUR_NEW_PROBES_VERIFY_BUT_BEST_NEW_ROW_IS_40476_TYPED_BYTES_VS_37532_FRONTIER"
CLAIM_BOUNDARY = (
    "BOUNDED_SOURCE_EXPOSED_LABEL_PROBE_SWEEP_OVER_EXISTING_SEQ32_NATIVE_PROOF_OBJECT;"
    "COMPARES_ONLY_LOCAL_TYPED_AND_JSON_PROOF_BYTES;"
    "NOT_A_NEW_FRONTIER_NOT_A_NANOZK_WIN_NOT_A_PRODUCTION_LABEL_POLICY"
)
PAYLOAD_DOMAIN = "ptvm:zkai:native-seq32-attention-mlp-expanded-label-probe:v1"
ISSUE_HINT = "bounded-expanded-seq32-label-probe-sweep"
DETERMINISTIC_TEMP_ATTEMPTS = 8

EXPECTED_RUST_SOURCE_SHA256 = "3d740bda9a3f301edea7a10dc1b9f58878d1a0f067397eecb5ed50465e4b7d95"
EXPECTED_CLI_SOURCE_SHA256 = "abd34cbc64a04e234ccf2c3e951629f57243eb7e1795b1c448d340bb7111095d"
EXPECTED_ACCOUNTING_SHA256 = "d17b7838ddcb4c77c8d346ceb89fcac1c7985b0bbf7b2679fe2a1daaca2c30f4"

CURRENT_CHAMPION_TYPED_BYTES = 42_068
CURRENT_TWO_PROOF_FRONTIER_TYPED_BYTES = 47_188
ADJACENT_PROBE_B_FRONTIER_TYPED_BYTES = 37_532
ADJACENT_PROBE_B_FRONTIER_JSON_BYTES = 106_317
NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES = 6_900

PATH_OPENING_GROUPS = ("fri_decommitments", "fri_samples", "trace_decommitments")
VALUE_GROUPS = ("oods_samples", "queries_values")

EXPECTED_ROWS = (
    {
        "variant_id": "current_duplicate_base_champion",
        "path": "zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json",
        "adapter_mode": "duplicate_base_preprocessed_v1",
        "family": "champion",
        "policy_status": "baseline_champion",
        "typed_bytes": 42_068,
        "json_proof_bytes": 121_996,
    },
    {
        "variant_id": "fixed_adjacent_layout",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_fixed_v1",
        "family": "adjacent",
        "policy_status": "rejected_existing_inflating_label",
        "typed_bytes": 42_156,
        "json_proof_bytes": 122_688,
    },
    {
        "variant_id": "adjacent_label_probe_a",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_a_v1",
        "family": "adjacent",
        "policy_status": "accepted_existing_label",
        "typed_bytes": 40_332,
        "json_proof_bytes": 116_321,
    },
    {
        "variant_id": "adjacent_label_probe_b",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_b_v1",
        "family": "adjacent",
        "policy_status": "current_frontier",
        "typed_bytes": 37_532,
        "json_proof_bytes": 106_317,
    },
    {
        "variant_id": "fixed_label_probe_a",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-fused-label-probe-a-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_fixed_label_probe_a_v1",
        "family": "fixed",
        "policy_status": "new_probe_rejected_not_better_than_frontier",
        "typed_bytes": 42_156,
        "json_proof_bytes": 122_655,
    },
    {
        "variant_id": "fixed_label_probe_b",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-fused-label-probe-b-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_fixed_label_probe_b_v1",
        "family": "fixed",
        "policy_status": "new_probe_beats_champion_but_not_frontier",
        "typed_bytes": 40_476,
        "json_proof_bytes": 116_661,
    },
    {
        "variant_id": "post_tail_label_probe_a",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-post-tail-label-probe-a-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_post_tail_label_probe_a_v1",
        "family": "post_tail",
        "policy_status": "new_probe_rejected_not_better_than_frontier",
        "typed_bytes": 42_156,
        "json_proof_bytes": 122_418,
    },
    {
        "variant_id": "post_tail_label_probe_b",
        "path": "zkai-native-seq32-attention-mlp-rmsnorm-post-tail-label-probe-b-2026-05.envelope.json",
        "adapter_mode": "rmsnorm_input_fused_post_tail_label_probe_b_v1",
        "family": "post_tail",
        "policy_status": "new_probe_rejected_not_better_than_frontier",
        "typed_bytes": 41_564,
        "json_proof_bytes": 120_368,
    },
)

VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-label-probe-a docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-fused-label-probe-a-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-label-probe-b docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-fused-label-probe-b-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-post-tail-label-probe-a docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-label-probe-a-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-post-tail-label-probe-b docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-label-probe-b-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-fused-label-probe-a-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-fused-label-probe-b-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-label-probe-a-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-label-probe-b-2026-05.envelope.json > docs/engineering/evidence/zkai-native-seq32-attention-mlp-expanded-label-probe-accounting-2026-05.json",
    "python3.10 scripts/zkai_native_seq32_attention_mlp_expanded_label_probe_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-expanded-label-probe-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-expanded-label-probe-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_expanded_label_probe_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_expanded_label_probe_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_expanded_label_probe_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend rmsnorm_input_adjacent_label --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
)

NON_CLAIMS = (
    "not a new proof-size frontier beyond the 37,532 typed-byte adjacent probe B row",
    "not a production label-selection policy",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not a full transformer block proof",
    "not exact real-valued Softmax",
    "not timing evidence",
    "not production-ready zkML",
)

MUTATION_NAMES = (
    "decision_drift",
    "claim_boundary_overclaim",
    "accounting_digest_drift",
    "frontier_promotion",
    "new_probe_typed_drift",
    "adapter_mode_relabeling",
    "path_opening_mechanism_drift",
    "validation_command_drift",
    "removed_non_claim",
    "payload_commitment_drift",
)


class ExpandedLabelProbeGateError(Exception):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def payload_commitment(payload: dict[str, Any]) -> str:
    item = copy.deepcopy(payload)
    item.pop("payload_commitment", None)
    raw = json.dumps(item, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.blake2b(PAYLOAD_DOMAIN.encode() + b"\0" + raw, digest_size=32).hexdigest()
    return f"blake2b-256:{digest}"


def read_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())


def source_artifact(path: pathlib.Path, artifact_id: str, expected_sha: str) -> dict[str, Any]:
    raw = path.read_bytes()
    digest = sha256_bytes(raw)
    if digest != expected_sha:
        raise ExpandedLabelProbeGateError(f"{artifact_id} source digest drift")
    return {
        "id": artifact_id,
        "path": str(path.relative_to(ROOT)),
        "sha256": digest,
        "size_bytes": len(raw),
    }


def accounting_rows_by_path() -> dict[str, dict[str, Any]]:
    raw = ACCOUNTING_PATH.read_bytes()
    digest = sha256_bytes(raw)
    if digest != EXPECTED_ACCOUNTING_SHA256:
        raise ExpandedLabelProbeGateError("accounting digest drift")
    data = json.loads(raw)
    if data.get("schema") != "zkai-stwo-local-binary-proof-accounting-cli-v1":
        raise ExpandedLabelProbeGateError("accounting schema drift")
    rows: dict[str, dict[str, Any]] = {}
    for row in data.get("rows", []):
        path = row.get("evidence_relative_path")
        if not isinstance(path, str):
            raise ExpandedLabelProbeGateError("accounting row path missing")
        if path in rows:
            raise ExpandedLabelProbeGateError(f"duplicate accounting path: {path}")
        rows[path] = row
    return rows


def proof_row(expected: dict[str, Any], accounting_row: dict[str, Any]) -> dict[str, Any]:
    envelope_path = EVIDENCE_DIR / expected["path"]
    raw = envelope_path.read_bytes()
    envelope = json.loads(raw)
    proof = envelope.get("proof")
    if not isinstance(proof, list):
        raise ExpandedLabelProbeGateError(f"{expected['variant_id']} proof field missing")
    envelope_input = envelope.get("input")
    if not isinstance(envelope_input, dict):
        raise ExpandedLabelProbeGateError(f"{expected['variant_id']} envelope input missing")
    accounting = accounting_row.get("local_binary_accounting")
    if not isinstance(accounting, dict):
        raise ExpandedLabelProbeGateError(f"{expected['variant_id']} accounting missing")
    groups = accounting.get("grouped_reconstruction")
    if not isinstance(groups, dict):
        raise ExpandedLabelProbeGateError(f"{expected['variant_id']} grouped accounting missing")

    proof_len = len(proof)
    typed_bytes = accounting.get("typed_size_estimate_bytes")
    if envelope_input.get("adapter_mode") != expected["adapter_mode"]:
        raise ExpandedLabelProbeGateError(f"{expected['variant_id']} adapter mode drift")
    if typed_bytes != expected["typed_bytes"]:
        raise ExpandedLabelProbeGateError(f"{expected['variant_id']} typed bytes drift")
    if proof_len != expected["json_proof_bytes"]:
        raise ExpandedLabelProbeGateError(f"{expected['variant_id']} JSON proof bytes drift")
    if accounting_row.get("proof_json_size_bytes") != proof_len:
        raise ExpandedLabelProbeGateError(f"{expected['variant_id']} accounting proof length drift")
    if accounting_row.get("envelope_sha256") != sha256_bytes(raw):
        raise ExpandedLabelProbeGateError(f"{expected['variant_id']} envelope digest drift")
    proof_bytes = bytes(int(value) for value in proof)
    if accounting_row.get("proof_sha256") != sha256_bytes(proof_bytes):
        raise ExpandedLabelProbeGateError(f"{expected['variant_id']} proof digest drift")

    path_opening_bytes = sum(int(groups[name]) for name in PATH_OPENING_GROUPS)
    value_bytes = sum(int(groups[name]) for name in VALUE_GROUPS)
    return {
        "variant_id": expected["variant_id"],
        "family": expected["family"],
        "policy_status": expected["policy_status"],
        "adapter_mode": expected["adapter_mode"],
        "path": expected["path"],
        "proof_backend_version": accounting_row["envelope_metadata"]["proof_backend_version"],
        "typed_bytes": typed_bytes,
        "json_proof_bytes": proof_len,
        "path_opening_bytes": path_opening_bytes,
        "value_bytes": value_bytes,
        "typed_delta_vs_current_champion": typed_bytes - CURRENT_CHAMPION_TYPED_BYTES,
        "typed_delta_vs_adjacent_probe_b": typed_bytes - ADJACENT_PROBE_B_FRONTIER_TYPED_BYTES,
        "json_delta_vs_adjacent_probe_b": proof_len - ADJACENT_PROBE_B_FRONTIER_JSON_BYTES,
        "envelope_sha256": accounting_row["envelope_sha256"],
        "proof_sha256": accounting_row["proof_sha256"],
        "record_stream_sha256": accounting["record_stream_sha256"],
    }


def build_rows() -> list[dict[str, Any]]:
    accounting = accounting_rows_by_path()
    rows = []
    for expected in EXPECTED_ROWS:
        row = accounting.get(expected["path"])
        if row is None:
            raise ExpandedLabelProbeGateError(f"missing accounting row: {expected['path']}")
        rows.append(proof_row(expected, row))
    return rows


def build_payload_without_mutations() -> dict[str, Any]:
    rows = build_rows()
    new_rows = [row for row in rows if row["policy_status"].startswith("new_probe")]
    best_new = min(new_rows, key=lambda row: row["typed_bytes"])
    adjacent_frontier = next(row for row in rows if row["variant_id"] == "adjacent_label_probe_b")
    if adjacent_frontier["typed_bytes"] != ADJACENT_PROBE_B_FRONTIER_TYPED_BYTES:
        raise ExpandedLabelProbeGateError("adjacent frontier drift")
    if best_new["typed_bytes"] <= adjacent_frontier["typed_bytes"]:
        raise ExpandedLabelProbeGateError("new probe unexpectedly beats adjacent frontier")
    if best_new["typed_bytes"] >= CURRENT_CHAMPION_TYPED_BYTES:
        raise ExpandedLabelProbeGateError("best new probe no longer beats champion")

    payload = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "issue_hint": ISSUE_HINT,
        "source_artifacts": [
            source_artifact(RUST_SOURCE_PATH, "rust_native_seq32_attention_mlp_source", EXPECTED_RUST_SOURCE_SHA256),
            source_artifact(CLI_SOURCE_PATH, "cli_native_seq32_attention_mlp_source", EXPECTED_CLI_SOURCE_SHA256),
            source_artifact(ACCOUNTING_PATH, "expanded_label_probe_accounting", EXPECTED_ACCOUNTING_SHA256),
        ],
        "probe_policy": {
            "scope": "bounded_existing_rust_modes_exposed_through_cli",
            "new_probe_count": len(new_rows),
            "new_probe_ids": [row["variant_id"] for row in new_rows],
            "promotion_rule": "a new probe must verify and beat the 37,532 typed-byte adjacent probe B frontier before it can replace the frontier",
            "manual_override_allowed": False,
        },
        "proof_object_rows": rows,
        "frontier_summary": {
            "current_champion_typed_bytes": CURRENT_CHAMPION_TYPED_BYTES,
            "current_two_proof_frontier_typed_bytes": CURRENT_TWO_PROOF_FRONTIER_TYPED_BYTES,
            "adjacent_probe_b_frontier_typed_bytes": ADJACENT_PROBE_B_FRONTIER_TYPED_BYTES,
            "adjacent_probe_b_frontier_json_bytes": ADJACENT_PROBE_B_FRONTIER_JSON_BYTES,
            "best_new_probe_id": best_new["variant_id"],
            "best_new_probe_typed_bytes": best_new["typed_bytes"],
            "best_new_probe_json_bytes": best_new["json_proof_bytes"],
            "best_new_probe_saving_vs_champion_typed_bytes": CURRENT_CHAMPION_TYPED_BYTES - best_new["typed_bytes"],
            "best_new_probe_gap_vs_adjacent_probe_b_typed_bytes": best_new["typed_bytes"] - ADJACENT_PROBE_B_FRONTIER_TYPED_BYTES,
            "new_probe_promotable": False,
            "nanozk_reported_d128_block_proof_bytes": NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
            "proof_size_comparable_external_rows": 0,
        },
        "interpretation": {
            "human_read": "The expanded probes verified, but none beat the existing adjacent probe B frontier.",
            "mechanism_read": "Fixed-label B still beats the old duplicate-base champion, so transcript labels matter, but layout also matters: adjacent B keeps the best path-opening shape.",
            "next_experiment": "If this path continues, use a pre-registered adjacent-only label-seed sweep and report every seed, not just the best one.",
        },
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
        "mutation_result": {"all_mutations_rejected": True, "mutations_rejected": 0, "cases": []},
    }
    return payload


def build_payload() -> dict[str, Any]:
    payload = build_payload_without_mutations()
    payload["mutation_result"] = mutation_result(payload)
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload)
    return payload


def mutation_functions() -> tuple[tuple[str, Callable[[dict[str, Any]], None]], ...]:
    return (
        ("decision_drift", lambda item: item.update({"decision": "GO"})),
        ("claim_boundary_overclaim", lambda item: item.update({"claim_boundary": item["claim_boundary"] + ";NANOZK_WIN"})),
        ("accounting_digest_drift", lambda item: item["source_artifacts"][2].update({"sha256": "0" * 64})),
        ("frontier_promotion", lambda item: item["frontier_summary"].update({"new_probe_promotable": True})),
        ("new_probe_typed_drift", lambda item: _row(item, "fixed_label_probe_b").update({"typed_bytes": 37_000})),
        ("adapter_mode_relabeling", lambda item: _row(item, "fixed_label_probe_b").update({"adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_b_v1"})),
        ("path_opening_mechanism_drift", lambda item: _row(item, "fixed_label_probe_b").update({"path_opening_bytes": 1})),
        ("validation_command_drift", lambda item: item["validation_commands"].append("echo unchecked")),
        ("removed_non_claim", lambda item: item["non_claims"].remove("not a NANOZK proof-size win")),
        ("payload_commitment_drift", lambda item: item.update({"payload_commitment": "blake2b-256:" + "0" * 64})),
    )


def _row(payload: dict[str, Any], variant_id: str) -> dict[str, Any]:
    for row in payload["proof_object_rows"]:
        if row["variant_id"] == variant_id:
            return row
    raise ExpandedLabelProbeGateError(f"missing row: {variant_id}")


def mutation_result(payload: dict[str, Any]) -> dict[str, Any]:
    cases = []
    for name, mutate in mutation_functions():
        item = copy.deepcopy(payload)
        item.pop("payload_commitment", None)
        item["mutation_result"] = {"all_mutations_rejected": True, "mutations_rejected": 0, "cases": []}
        mutate(item)
        if name != "payload_commitment_drift":
            item["payload_commitment"] = payload_commitment(item)
        try:
            validate_payload_core(item)
            if item.get("payload_commitment") != payload_commitment(item):
                raise ExpandedLabelProbeGateError("payload commitment drift")
        except ExpandedLabelProbeGateError as error:
            cases.append({"name": name, "rejected": True, "error": str(error)})
        else:
            cases.append({"name": name, "rejected": False, "error": ""})
    return {
        "all_mutations_rejected": all(case["rejected"] for case in cases),
        "mutations_rejected": sum(1 for case in cases if case["rejected"]),
        "mutation_names": list(MUTATION_NAMES),
        "cases": cases,
    }


def validate_payload(payload: dict[str, Any]) -> None:
    validate_payload_core(payload)
    mutation = payload.get("mutation_result")
    if not isinstance(mutation, dict):
        raise ExpandedLabelProbeGateError("mutation_result missing")
    if mutation.get("mutation_names") != list(MUTATION_NAMES):
        raise ExpandedLabelProbeGateError("mutation inventory drift")
    if mutation.get("mutations_rejected") != len(MUTATION_NAMES) or not mutation.get("all_mutations_rejected"):
        raise ExpandedLabelProbeGateError("mutation rejection drift")
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise ExpandedLabelProbeGateError("payload commitment drift")


def validate_payload_core(payload: dict[str, Any]) -> None:
    expected = build_payload_without_mutations()
    for key, value in {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "claim_boundary": CLAIM_BOUNDARY,
        "issue_hint": ISSUE_HINT,
    }.items():
        if payload.get(key) != value:
            raise ExpandedLabelProbeGateError(f"{key} drift")
    if "NANOZK_WIN" in str(payload.get("claim_boundary")).split(";"):
        raise ExpandedLabelProbeGateError("claim_boundary drift")
    for key in ("source_artifacts", "probe_policy", "proof_object_rows", "frontier_summary", "interpretation", "non_claims", "validation_commands"):
        if payload.get(key) != expected[key]:
            raise ExpandedLabelProbeGateError(f"{key} drift")


def render_tsv(payload: dict[str, Any]) -> str:
    fieldnames = [
        "variant_id",
        "family",
        "policy_status",
        "adapter_mode",
        "typed_bytes",
        "json_proof_bytes",
        "typed_delta_vs_current_champion",
        "typed_delta_vs_adjacent_probe_b",
        "path_opening_bytes",
        "value_bytes",
        "payload_commitment",
        "decision",
        "result",
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in payload["proof_object_rows"]:
        writer.writerow({key: row.get(key, payload.get(key, "")) for key in fieldnames})
    return output.getvalue()


def require_output_path(path: pathlib.Path) -> pathlib.Path:
    target = pathlib.Path(os.path.abspath(path if path.is_absolute() else ROOT / path))
    evidence_root = EVIDENCE_DIR.resolve()
    try:
        relative = target.relative_to(evidence_root)
    except ValueError as err:
        raise ExpandedLabelProbeGateError("output path escapes evidence dir") from err
    current = evidence_root
    for part in relative.parent.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except OSError as err:
            raise ExpandedLabelProbeGateError(f"output parent must exist: {current}") from err
        if stat.S_ISLNK(mode):
            raise ExpandedLabelProbeGateError("output path must not traverse symlinks")
        if not stat.S_ISDIR(mode):
            raise ExpandedLabelProbeGateError(f"output parent must be directory: {current}")
    if target.is_symlink() or (target.exists() and target.is_dir()):
        raise ExpandedLabelProbeGateError("output path must be a non-symlink file")
    return target


def atomic_write(path: pathlib.Path, text: str) -> None:
    target = require_output_path(path)
    parent_fd = os.open(
        target.parent,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        for attempt in range(DETERMINISTIC_TEMP_ATTEMPTS):
            tmp_name = f".{target.name}.tmp.{attempt}"
            tmp_created = False
            fd: int | None = None
            try:
                fd = os.open(
                    tmp_name,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=parent_fd,
                )
            except FileExistsError:
                continue
            try:
                tmp_created = True
                try:
                    handle = os.fdopen(fd, "w", encoding="utf-8", newline="")
                except Exception:
                    os.close(fd)
                    fd = None
                    raise
                fd = None
                with handle:
                    handle.write(text)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(tmp_name, target.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
                os.fsync(parent_fd)
                return
            except Exception:
                if fd is not None:
                    os.close(fd)
                if tmp_created:
                    try:
                        os.unlink(tmp_name, dir_fd=parent_fd)
                    except FileNotFoundError:
                        pass
                raise
        raise ExpandedLabelProbeGateError("could not create deterministic temp output")
    finally:
        os.close(parent_fd)


def write_outputs(json_path: pathlib.Path, tsv_path: pathlib.Path, payload: dict[str, Any]) -> None:
    atomic_write(json_path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    atomic_write(tsv_path, render_tsv(payload))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    args = parser.parse_args()
    if bool(args.write_json) != bool(args.write_tsv):
        raise SystemExit("--write-json and --write-tsv must be provided together")
    payload = build_payload()
    if args.write_json and args.write_tsv:
        write_outputs(args.write_json, args.write_tsv, payload)
    print(json.dumps({
        "decision": payload["decision"],
        "best_new_probe_id": payload["frontier_summary"]["best_new_probe_id"],
        "best_new_probe_typed_bytes": payload["frontier_summary"]["best_new_probe_typed_bytes"],
        "new_probe_gap_vs_adjacent_probe_b_typed_bytes": payload["frontier_summary"]["best_new_probe_gap_vs_adjacent_probe_b_typed_bytes"],
        "mutations_rejected": payload["mutation_result"]["mutations_rejected"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
