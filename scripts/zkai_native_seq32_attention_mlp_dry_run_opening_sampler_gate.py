#!/usr/bin/env python3.10
"""Gate a dry-run query/opening sampler for seq32 attention+MLP labels."""

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
from typing import Any


if sys.version_info < (3, 10):
    raise RuntimeError(
        "zkai_native_seq32_attention_mlp_dry_run_opening_sampler_gate requires Python 3.10+"
    )

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
RUST_SOURCE_PATH = ROOT / "src" / "stwo_backend" / "native_seq32_attention_mlp_single_proof.rs"
CLI_SOURCE_PATH = ROOT / "src" / "bin" / "zkai_native_seq32_attention_mlp_single_proof.rs"
PREPROVE_EVIDENCE_PATH = (
    EVIDENCE_DIR
    / "zkai-native-seq32-attention-mlp-preprove-opening-bucket-predictor-2026-05.json"
)
JSON_OUT = (
    EVIDENCE_DIR
    / "zkai-native-seq32-attention-mlp-dry-run-opening-sampler-2026-05.json"
)
TSV_OUT = (
    EVIDENCE_DIR
    / "zkai-native-seq32-attention-mlp-dry-run-opening-sampler-2026-05.tsv"
)

SCHEMA = "zkai-native-seq32-attention-mlp-dry-run-opening-sampler-gate-v1"
DECISION = "GO_QUERY_LOCATION_SAMPLER_PREDICTS_CHECKED_ADJACENT_OPENING_BUCKETS"
RESULT = (
    "QUERY_LOCATION_GEOMETRY_PREDICTS_PROBE_B_AND_SEED_BUCKETS_WITHOUT_FINAL_PROOF_BYTES"
)
CLAIM_BOUNDARY = (
    "SAMPLER_USES_PROVER_INTERNAL_QUERY_LOCATIONS_ONLY;"
    "FINAL_ACCOUNTING_JOIN_USED_ONLY_FOR_EVALUATION;"
    "NO_ENVELOPE_JSON_NO_PROOF_BYTES_NO_GROUPED_ACCOUNTING_NO_RECORD_STREAMS_IN_PREDICTOR;"
    "NOT_A_PRODUCTION_LABEL_POLICY_NOT_A_NANOZK_COMPARISON"
)
ISSUE_HINT = "https://github.com/omarespejel/provable-transformer-vm/issues/697"
PAYLOAD_DOMAIN = "ptvm:zkai:native-seq32-attention-mlp-dry-run-opening-sampler:v1"

MAX_SOURCE_ARTIFACT_BYTES = 768 * 1024
MAX_SAMPLER_JSON_BYTES = 64 * 1024
MAX_PREPROVE_EVIDENCE_BYTES = 2 * 1024 * 1024
DETERMINISTIC_TEMP_ATTEMPTS = 16

EXPECTED_RUST_SOURCE_SHA256 = "7818c25b034da111cddd090783ea6bc66fd0c4dc2c67f95e3281899d0235344b"
EXPECTED_CLI_SOURCE_SHA256 = "ea68996b62dd763255e20479672bf7a392494a710c87eb2c0da84482873b4b52"
EXPECTED_PREPROVE_EVIDENCE_SHA256 = "98bcd9b9a574aa934c4ad571ae78aa1d738f0fb720488cb992be88609a8b785b"

SAMPLER_SCHEMA = "zkai-native-seq32-attention-mlp-dry-run-opening-sampler-v1"
SAMPLER_DECISION = "GO_PROVER_INTERNAL_QUERY_OPENING_SAMPLER_BEFORE_FINAL_PROOF_SERIALIZATION"
SAMPLER_BOUNDARY = (
    "PROVER_INTERNAL_EXTENDED_AUX_QUERY_LOCATIONS_ONLY;"
    "NO_ENVELOPE_JSON_NO_PROOF_BYTES_NO_GROUPED_ACCOUNTING_NO_RECORD_STREAMS"
)
EXPECTED_FRI_QUERIES = 3
BEST_BUCKET_VARIANT_ID = "adjacent_label_probe_b"
BEST_BUCKET_PATH_OPENING_BYTES = 16_560
DISTINCT_FINAL_PATH_OPENING_BUCKETS = 5

VARIANTS = (
    {
        "variant_id": "adjacent_label_probe_a",
        "sampler_path": "docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-a-2026-05-opening-sampler-2026-05.json",
        "sampler_sha256": "e5789e6876e13a68542aadad1a8b2649b2d31bc1c08843b595818eb031c170b8",
        "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_a_v1",
    },
    {
        "variant_id": "adjacent_label_probe_b",
        "sampler_path": "docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05-opening-sampler-2026-05.json",
        "sampler_sha256": "5421f80d39bf80c3301d4f65f412fb9bb6d8f9b333577b7f305b02912dda6252",
        "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_b_v1",
    },
    {
        "variant_id": "fixed_adjacent_layout",
        "sampler_path": "docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05-opening-sampler-2026-05.json",
        "sampler_sha256": "6fd4527aa1e62a22e96f413b252677aae3c778b10823cce96cb6a879df8337d4",
        "adapter_mode": "rmsnorm_input_fused_adjacent_fixed_v1",
    },
    {
        "variant_id": "adjacent_seed_00",
        "sampler_path": "docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-00-2026-05-opening-sampler-2026-05.json",
        "sampler_sha256": "6a99c0a0eb1f57ee96ac629e09e6e98d84a621dcf3b7d7492bd19e07b09ce226",
        "adapter_mode": "rmsnorm_input_fused_adjacent_seed_00_v1",
    },
    {
        "variant_id": "adjacent_seed_01",
        "sampler_path": "docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-01-2026-05-opening-sampler-2026-05.json",
        "sampler_sha256": "bb2005983a1d783eb80b12e9b988a493ae3e1247f6e086a9d32d2e75bdaed375",
        "adapter_mode": "rmsnorm_input_fused_adjacent_seed_01_v1",
    },
    {
        "variant_id": "adjacent_seed_02",
        "sampler_path": "docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-02-2026-05-opening-sampler-2026-05.json",
        "sampler_sha256": "747708f9c6f28af8f7383e15fef6a2f8fa48745a64dc9f3f8930012ee02082d4",
        "adapter_mode": "rmsnorm_input_fused_adjacent_seed_02_v1",
    },
    {
        "variant_id": "adjacent_seed_03",
        "sampler_path": "docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-03-2026-05-opening-sampler-2026-05.json",
        "sampler_sha256": "9edc1870d6aa63e04ea703cc3ea0824bc27acf8bcade1e08ddcc929e366c9b1b",
        "adapter_mode": "rmsnorm_input_fused_adjacent_seed_03_v1",
    },
    {
        "variant_id": "adjacent_seed_04",
        "sampler_path": "docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-04-2026-05-opening-sampler-2026-05.json",
        "sampler_sha256": "0016d0f425f5ed79c14c847ae32bbd54b317a1d1149137b55eb2fbbb4c56050b",
        "adapter_mode": "rmsnorm_input_fused_adjacent_seed_04_v1",
    },
    {
        "variant_id": "adjacent_seed_05",
        "sampler_path": "docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-seed-05-2026-05-opening-sampler-2026-05.json",
        "sampler_sha256": "967f5bffb6a7d35ecdcb059444851d194d9e03dbd80a38f3ec8ddc9c3260230e",
        "adapter_mode": "rmsnorm_input_fused_adjacent_seed_05_v1",
    },
)

PREDICTOR_FEATURE_KEYS = (
    "unique_query_count",
    "query_location_span",
    "min_pairwise_query_gap",
)
FORBIDDEN_PREDICTOR_KEYS = {
    "variant_id",
    "adapter_mode",
    "statement_commitment",
    "public_instance_commitment",
    "proof_native_parameter_commitment",
    "path_opening_bytes",
    "typed_bytes",
    "json_proof_bytes",
    "groups",
    "record_stream_sha256",
    "envelope_sha256",
    "proof_sha256",
}
TSV_COLUMNS = (
    "variant_id",
    "adapter_mode",
    "query_location_span",
    "min_pairwise_query_gap",
    "prediction_rule",
    "predicted_path_opening_bytes",
    "final_path_opening_bytes",
    "prediction_correct",
    "sampler_sha256",
    "query_location_digest",
)
VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend native_seq32_attention_mlp_single_proof --lib",
    "cargo +nightly-2025-07-14 build --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof",
    'for input in docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent*2026-05.input.json; do output="${input%.input.json}-opening-sampler-2026-05.json"; target/debug/zkai_native_seq32_attention_mlp_single_proof sample-openings "$input" "$output"; done',
    "python3.10 scripts/zkai_native_seq32_attention_mlp_dry_run_opening_sampler_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-dry-run-opening-sampler-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-dry-run-opening-sampler-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_dry_run_opening_sampler_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_dry_run_opening_sampler_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_dry_run_opening_sampler_gate",
    "git diff --check",
    "just gate-fast",
    "just gate",
)
NON_CLAIMS = (
    "not a production label-selection policy",
    "not a new proof-size frontier",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not a full transformer block proof",
    "not exact real-valued Softmax",
    "not timing evidence",
    "not production-ready zkML",
)
INTERPRETATION = {
    "human_read": (
        "The source-visible inventory was blind, but prover-internal query locations expose "
        "a checked mechanism for this small adjacent-label inventory. Probe B lands in the "
        "tightest three-query cluster and in the smallest final path-opening bucket."
    ),
    "mechanism_read": (
        "The predictor uses only query-location geometry from the Stwo extended proof auxiliary "
        "data. Final proof-size accounting is joined after prediction only to score the result."
    ),
    "next_experiment": (
        "Move from this checked inventory rule to a true pre-decommitment sampler or multi-run "
        "layout policy before promoting any production label-selection claim."
    ),
}
MUTATION_NAMES = (
    "decision_drift",
    "result_overclaim",
    "rust_source_digest_drift",
    "cli_source_digest_drift",
    "preprove_digest_drift",
    "sampler_digest_drift",
    "sampler_row_removed",
    "query_location_erasure",
    "row_identity_promoted_to_predictor",
    "final_accounting_leak_to_predictor",
    "probe_b_prediction_drift",
    "prediction_rule_threshold_drift",
    "validation_command_removed",
    "non_claim_removed",
    "payload_commitment_drift",
)


class DryRunOpeningSamplerGateError(Exception):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    except (TypeError, ValueError) as err:
        raise DryRunOpeningSamplerGateError(f"non-canonical JSON value: {err}") from err


def blake2b_commitment(domain: str, value: Any) -> str:
    digest = hashlib.blake2b(
        domain.encode() + b"\0" + canonical_json_bytes(value),
        digest_size=32,
    ).hexdigest()
    return f"blake2b-256:{digest}"


def payload_commitment(payload: dict[str, Any]) -> str:
    item = copy.deepcopy(payload)
    item.pop("payload_commitment", None)
    return blake2b_commitment(PAYLOAD_DOMAIN, item)


def read_bounded_repo_file(path: pathlib.Path, label: str, max_bytes: int) -> bytes:
    root = ROOT.resolve()
    candidate = pathlib.Path(os.path.abspath(path if path.is_absolute() else ROOT / path))
    try:
        relative = candidate.relative_to(root)
    except ValueError as err:
        raise DryRunOpeningSamplerGateError(f"{label} escapes repo root") from err
    if not relative.parts:
        raise DryRunOpeningSamplerGateError(f"{label} must name a repo file")
    try:
        current_fd = os.open(
            root,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as err:
        raise DryRunOpeningSamplerGateError("failed to open repo root") from err
    fd: int | None = None
    try:
        for part in relative.parts[:-1]:
            try:
                next_fd = os.open(
                    part,
                    os.O_RDONLY
                    | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=current_fd,
                )
            except FileNotFoundError as err:
                raise DryRunOpeningSamplerGateError(f"{label} missing: {relative}") from err
            except OSError as err:
                raise DryRunOpeningSamplerGateError(
                    f"{label} must not traverse symlinks or non-directories"
                ) from err
            os.close(current_fd)
            current_fd = next_fd
        try:
            fd = os.open(
                relative.parts[-1],
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=current_fd,
            )
        except FileNotFoundError as err:
            raise DryRunOpeningSamplerGateError(f"{label} missing: {relative}") from err
        except OSError as err:
            raise DryRunOpeningSamplerGateError(f"{label} must not be a symlink") from err
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode):
            raise DryRunOpeningSamplerGateError(f"{label} must be a regular file")
        if opened.st_size > max_bytes:
            raise DryRunOpeningSamplerGateError(
                f"{label} exceeds max size: {opened.st_size} > {max_bytes}"
            )
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, 64 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise DryRunOpeningSamplerGateError(f"{label} exceeds max size while reading")
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        if fd is not None:
            os.close(fd)
        os.close(current_fd)


def read_json(path: pathlib.Path, label: str, max_bytes: int) -> Any:
    raw = read_bounded_repo_file(path, label, max_bytes)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as err:
        raise DryRunOpeningSamplerGateError(f"{label} is not valid JSON: {err}") from err


def source_artifact(
    path: pathlib.Path,
    artifact_id: str,
    expected_sha256: str,
    max_bytes: int = MAX_SOURCE_ARTIFACT_BYTES,
) -> dict[str, Any]:
    raw = read_bounded_repo_file(path, artifact_id, max_bytes)
    digest = sha256_bytes(raw)
    if digest != expected_sha256:
        raise DryRunOpeningSamplerGateError(f"{artifact_id} source digest drift")
    return {
        "id": artifact_id,
        "path": str(path.relative_to(ROOT)),
        "sha256": digest,
        "size_bytes": len(raw),
    }


def sampler_artifact(spec: dict[str, str]) -> dict[str, Any]:
    path = ROOT / spec["sampler_path"]
    raw = read_bounded_repo_file(path, spec["variant_id"], MAX_SAMPLER_JSON_BYTES)
    digest = sha256_bytes(raw)
    if digest != spec["sampler_sha256"]:
        raise DryRunOpeningSamplerGateError(f"{spec['variant_id']} sampler digest drift")
    return {
        "id": f"{spec['variant_id']}_opening_sampler",
        "path": spec["sampler_path"],
        "sha256": digest,
        "size_bytes": len(raw),
    }


def final_rows_by_variant() -> dict[str, dict[str, Any]]:
    raw = read_bounded_repo_file(
        PREPROVE_EVIDENCE_PATH, "preprove evidence", MAX_PREPROVE_EVIDENCE_BYTES
    )
    digest = sha256_bytes(raw)
    if digest != EXPECTED_PREPROVE_EVIDENCE_SHA256:
        raise DryRunOpeningSamplerGateError("preprove evidence digest drift")
    payload = json.loads(raw)
    return {row["variant_id"]: row for row in payload["final_accounting_join_rows"]}


def query_features(sorted_queries: list[int]) -> dict[str, int]:
    if len(sorted_queries) != EXPECTED_FRI_QUERIES:
        raise DryRunOpeningSamplerGateError("unexpected query count")
    pairwise = [
        sorted_queries[1] - sorted_queries[0],
        sorted_queries[2] - sorted_queries[1],
        sorted_queries[2] - sorted_queries[0],
    ]
    return {
        "unique_query_count": len(sorted_queries),
        "query_location_span": sorted_queries[-1] - sorted_queries[0],
        "min_pairwise_query_gap": min(pairwise),
        "max_pairwise_query_gap": max(pairwise),
    }


def predict_path_opening_bucket(features: dict[str, int]) -> tuple[int, str]:
    span = features["query_location_span"]
    min_gap = features["min_pairwise_query_gap"]
    if span <= 20_000:
        return 16_560, "tight_three_query_cluster"
    if span <= 90_000:
        return 19_296, "medium_span_without_tight_pair"
    if min_gap <= 20_000:
        return 19_360, "one_tight_pair_inside_wider_span"
    if span <= 200_000:
        return 20_512, "medium_wide_span_without_tight_pair"
    return 21_184, "wide_query_span"


def build_sampler_rows() -> list[dict[str, Any]]:
    final_rows = final_rows_by_variant()
    rows = []
    for spec in VARIANTS:
        sampler = read_json(ROOT / spec["sampler_path"], spec["variant_id"], MAX_SAMPLER_JSON_BYTES)
        validate_sampler_document(sampler, spec)
        features = query_features(sampler["sorted_unique_query_locations"])
        predicted, rule = predict_path_opening_bucket(features)
        final = final_rows[spec["variant_id"]]
        row = {
            "variant_id": spec["variant_id"],
            "adapter_mode": sampler["adapter_mode"],
            "sampler_path": spec["sampler_path"],
            "sampler_sha256": spec["sampler_sha256"],
            "query_location_digest": sampler["query_location_digest"],
            "commitment_roots_digest": sampler["commitment_roots_digest"],
            "sorted_unique_query_locations": sampler["sorted_unique_query_locations"],
            "predictor_features": {key: features[key] for key in PREDICTOR_FEATURE_KEYS},
            "prediction_rule": rule,
            "predicted_path_opening_bytes": predicted,
            "final_path_opening_bytes": final["path_opening_bytes"],
            "final_value_bytes": final["value_bytes"],
            "prediction_correct": predicted == final["path_opening_bytes"],
        }
        rows.append(row)
    return rows


def validate_sampler_document(sampler: dict[str, Any], spec: dict[str, str]) -> None:
    expected = {
        "schema": SAMPLER_SCHEMA,
        "decision": SAMPLER_DECISION,
        "sampler_boundary": SAMPLER_BOUNDARY,
        "adapter_mode": spec["adapter_mode"],
        "expected_fri_queries": EXPECTED_FRI_QUERIES,
        "unsorted_query_count": EXPECTED_FRI_QUERIES,
        "unique_query_count": EXPECTED_FRI_QUERIES,
        "duplicate_query_count": 0,
    }
    for key, value in expected.items():
        if sampler.get(key) != value:
            raise DryRunOpeningSamplerGateError(f"{spec['variant_id']} sampler {key} drift")
    if len(sampler.get("sorted_unique_query_locations", [])) != EXPECTED_FRI_QUERIES:
        raise DryRunOpeningSamplerGateError(f"{spec['variant_id']} sorted query count drift")
    forbidden = FORBIDDEN_PREDICTOR_KEYS.intersection(sampler.get("predictor_features", {}))
    if forbidden:
        raise DryRunOpeningSamplerGateError(
            f"{spec['variant_id']} sampler predictor leaks forbidden keys: {sorted(forbidden)}"
        )
    for forbidden_key in ("path_opening_bytes", "typed_bytes", "json_proof_bytes", "groups"):
        if forbidden_key in sampler:
            raise DryRunOpeningSamplerGateError(
                f"{spec['variant_id']} sampler leaks final accounting field {forbidden_key}"
            )


def build_payload_without_mutations() -> dict[str, Any]:
    rows = build_sampler_rows()
    final_buckets = sorted({row["final_path_opening_bytes"] for row in rows})
    predicted_buckets = sorted({row["predicted_path_opening_bytes"] for row in rows})
    best_rows = [
        row for row in rows if row["predicted_path_opening_bytes"] == min(predicted_buckets)
    ]
    source_artifacts = [
        source_artifact(
            RUST_SOURCE_PATH,
            "rust_native_seq32_attention_mlp_source",
            EXPECTED_RUST_SOURCE_SHA256,
        ),
        source_artifact(
            CLI_SOURCE_PATH,
            "cli_native_seq32_attention_mlp_source",
            EXPECTED_CLI_SOURCE_SHA256,
        ),
        source_artifact(
            PREPROVE_EVIDENCE_PATH,
            "preprove_opening_bucket_predictor_evidence",
            EXPECTED_PREPROVE_EVIDENCE_SHA256,
            MAX_PREPROVE_EVIDENCE_BYTES,
        ),
    ]
    source_artifacts.extend(sampler_artifact(spec) for spec in VARIANTS)
    return {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE_HINT,
        "claim_boundary": CLAIM_BOUNDARY,
        "sampler_rows": rows,
        "predictor_policy": {
            "predictor_feature_keys": list(PREDICTOR_FEATURE_KEYS),
            "forbidden_predictor_keys": sorted(FORBIDDEN_PREDICTOR_KEYS),
            "row_identity_fields_are_predictors": False,
            "final_accounting_is_predictor_input": False,
            "prediction_all_correct": all(row["prediction_correct"] for row in rows),
            "distinct_final_path_opening_buckets": len(final_buckets),
            "distinct_predicted_path_opening_buckets": len(predicted_buckets),
            "best_predicted_variant_id": best_rows[0]["variant_id"],
            "best_predicted_path_opening_bytes": best_rows[0][
                "predicted_path_opening_bytes"
            ],
            "best_final_variant_id": BEST_BUCKET_VARIANT_ID,
            "best_final_path_opening_bytes": BEST_BUCKET_PATH_OPENING_BYTES,
        },
        "interpretation": INTERPRETATION,
        "source_artifacts": source_artifacts,
        "validation_commands": list(VALIDATION_COMMANDS),
        "non_claims": list(NON_CLAIMS),
    }


def validate_base_payload(payload: dict[str, Any]) -> None:
    expected = build_payload_without_mutations()
    if payload != expected:
        raise DryRunOpeningSamplerGateError("base payload drift")
    rows = payload["sampler_rows"]
    if len(rows) != len(VARIANTS):
        raise DryRunOpeningSamplerGateError("sampler row count drift")
    if not all(row["prediction_correct"] for row in rows):
        raise DryRunOpeningSamplerGateError("not all sampler predictions are correct")
    best = payload["predictor_policy"]
    if best["best_predicted_variant_id"] != BEST_BUCKET_VARIANT_ID:
        raise DryRunOpeningSamplerGateError("best predicted variant drift")
    if best["best_predicted_path_opening_bytes"] != BEST_BUCKET_PATH_OPENING_BYTES:
        raise DryRunOpeningSamplerGateError("best predicted bucket drift")
    if best["distinct_final_path_opening_buckets"] != DISTINCT_FINAL_PATH_OPENING_BUCKETS:
        raise DryRunOpeningSamplerGateError("final bucket count drift")
    leaked = FORBIDDEN_PREDICTOR_KEYS.intersection(best["predictor_feature_keys"])
    if leaked:
        raise DryRunOpeningSamplerGateError(f"predictor keys leak forbidden fields: {sorted(leaked)}")


def validate_payload(payload: dict[str, Any]) -> None:
    item = copy.deepcopy(payload)
    supplied_commitment = item.pop("payload_commitment", None)
    mutation_result = item.pop("mutation_result", None)
    validate_base_payload(item)
    if supplied_commitment != payload_commitment(payload):
        raise DryRunOpeningSamplerGateError("payload commitment drift")
    expected_mutation = run_mutations(item)
    if mutation_result != expected_mutation:
        raise DryRunOpeningSamplerGateError("mutation result drift")


def mutate_payload(name: str, item: dict[str, Any]) -> None:
    if name == "decision_drift":
        item["decision"] = "NO_GO"
    elif name == "result_overclaim":
        item["result"] = "PRODUCTION_LABEL_POLICY_DISCOVERED"
    elif name == "rust_source_digest_drift":
        item["source_artifacts"][0]["sha256"] = "0" * 64
    elif name == "cli_source_digest_drift":
        item["source_artifacts"][1]["sha256"] = "1" * 64
    elif name == "preprove_digest_drift":
        item["source_artifacts"][2]["sha256"] = "2" * 64
    elif name == "sampler_digest_drift":
        item["source_artifacts"][3]["sha256"] = "3" * 64
    elif name == "sampler_row_removed":
        item["sampler_rows"].pop()
    elif name == "query_location_erasure":
        item["sampler_rows"][1]["sorted_unique_query_locations"] = []
    elif name == "row_identity_promoted_to_predictor":
        item["predictor_policy"]["predictor_feature_keys"].append("statement_commitment")
    elif name == "final_accounting_leak_to_predictor":
        item["sampler_rows"][1]["predictor_features"]["path_opening_bytes"] = 16_560
    elif name == "probe_b_prediction_drift":
        item["sampler_rows"][1]["predicted_path_opening_bytes"] = 19_360
    elif name == "prediction_rule_threshold_drift":
        item["sampler_rows"][1]["prediction_rule"] = "row_identity_lookup"
    elif name == "validation_command_removed":
        item["validation_commands"].pop()
    elif name == "non_claim_removed":
        item["non_claims"].remove("not a NANOZK proof-size win")
    elif name == "payload_commitment_drift":
        item["payload_commitment"] = "blake2b-256:" + ("0" * 64)
    else:
        raise DryRunOpeningSamplerGateError(f"unknown mutation: {name}")


def run_mutations(base_payload: dict[str, Any]) -> dict[str, Any]:
    cases = []
    for name in MUTATION_NAMES:
        item = copy.deepcopy(base_payload)
        mutate_payload(name, item)
        rejected = False
        error = ""
        try:
            if name == "payload_commitment_drift":
                validate_payload(item)
            else:
                validate_base_payload(item)
        except DryRunOpeningSamplerGateError as err:
            rejected = True
            error = str(err)
        cases.append({"name": name, "rejected": rejected, "error": error})
    rejected_count = sum(1 for case in cases if case["rejected"])
    return {
        "all_mutations_rejected": rejected_count == len(MUTATION_NAMES),
        "mutations_rejected": rejected_count,
        "mutation_names": list(MUTATION_NAMES),
        "cases": cases,
    }


def build_payload() -> dict[str, Any]:
    payload = build_payload_without_mutations()
    payload["mutation_result"] = run_mutations(payload)
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload)
    return payload


def render_tsv(payload: dict[str, Any]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in payload["sampler_rows"]:
        writer.writerow(
            {
                "variant_id": row["variant_id"],
                "adapter_mode": row["adapter_mode"],
                "query_location_span": row["predictor_features"]["query_location_span"],
                "min_pairwise_query_gap": row["predictor_features"]["min_pairwise_query_gap"],
                "prediction_rule": row["prediction_rule"],
                "predicted_path_opening_bytes": row["predicted_path_opening_bytes"],
                "final_path_opening_bytes": row["final_path_opening_bytes"],
                "prediction_correct": str(row["prediction_correct"]).lower(),
                "sampler_sha256": row["sampler_sha256"],
                "query_location_digest": row["query_location_digest"],
            }
        )
    return output.getvalue()


def require_output_path(path: pathlib.Path) -> pathlib.Path:
    target = pathlib.Path(os.path.abspath(path if path.is_absolute() else ROOT / path))
    evidence = EVIDENCE_DIR.resolve()
    try:
        relative = target.relative_to(evidence)
    except ValueError as err:
        raise DryRunOpeningSamplerGateError("output path must stay under evidence directory") from err
    current = evidence
    for part in relative.parent.parts:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except OSError as err:
            raise DryRunOpeningSamplerGateError(f"output parent must exist: {current}") from err
        if stat.S_ISLNK(mode):
            raise DryRunOpeningSamplerGateError("output path must not traverse symlinks")
        if not stat.S_ISDIR(mode):
            raise DryRunOpeningSamplerGateError(f"output parent must be directory: {current}")
    if target.is_symlink() or (target.exists() and target.is_dir()):
        raise DryRunOpeningSamplerGateError("output path must be a non-symlink file")
    return target


def open_output_parent_fd(target: pathlib.Path) -> int:
    evidence = EVIDENCE_DIR.resolve()
    try:
        relative = target.relative_to(evidence)
    except ValueError as err:
        raise DryRunOpeningSamplerGateError("output path must stay under evidence directory") from err
    try:
        current_fd = os.open(
            evidence,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as err:
        raise DryRunOpeningSamplerGateError("failed to open evidence directory") from err
    try:
        for part in relative.parent.parts:
            try:
                next_fd = os.open(
                    part,
                    os.O_RDONLY
                    | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=current_fd,
                )
            except FileNotFoundError as err:
                raise DryRunOpeningSamplerGateError(f"output parent must exist: {target.parent}") from err
            except OSError as err:
                raise DryRunOpeningSamplerGateError(
                    "output path must not traverse symlinks or non-directories"
                ) from err
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except Exception:
        os.close(current_fd)
        raise


def write_temp_output(parent_fd: int, target_name: str, data: bytes) -> str:
    for attempt in range(DETERMINISTIC_TEMP_ATTEMPTS):
        tmp_name = f".{target_name}.tmp.{attempt}"
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
        except OSError as err:
            raise DryRunOpeningSamplerGateError(f"failed to create temp output: {tmp_name}") from err
        try:
            tmp_created = True
            try:
                handle = os.fdopen(fd, "wb")
            except Exception:
                os.close(fd)
                fd = None
                raise
            fd = None
            with handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            tmp_created = False
            return tmp_name
        except OSError as err:
            raise DryRunOpeningSamplerGateError(f"failed to write temp output: {tmp_name}") from err
        finally:
            if tmp_created:
                try:
                    os.unlink(tmp_name, dir_fd=parent_fd)
                except OSError:
                    pass
            if fd is not None:
                os.close(fd)
    raise DryRunOpeningSamplerGateError(
        f"deterministic temp file collision for {target_name} after "
        f"{DETERMINISTIC_TEMP_ATTEMPTS} attempts"
    )


def fsync_parent_dir(parent_fd: int, context: str) -> None:
    try:
        os.fsync(parent_fd)
    except OSError as err:
        raise DryRunOpeningSamplerGateError(f"failed to fsync {context}") from err


def backup_existing_output(parent_fd: int, target_name: str) -> str | None:
    for attempt in range(DETERMINISTIC_TEMP_ATTEMPTS):
        backup_name = f".{target_name}.bak.{attempt}"
        try:
            os.link(
                target_name,
                backup_name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
                follow_symlinks=False,
            )
            return backup_name
        except FileNotFoundError:
            return None
        except FileExistsError:
            continue
        except OSError as err:
            raise DryRunOpeningSamplerGateError(f"failed to back up output: {target_name}") from err
    raise DryRunOpeningSamplerGateError(
        f"deterministic backup file collision for {target_name} after "
        f"{DETERMINISTIC_TEMP_ATTEMPTS} attempts"
    )


def restore_output_backup(
    parent_fd: int,
    target_name: str,
    backup_name: str | None,
    remove_partial: bool,
) -> None:
    if remove_partial or backup_name is not None:
        try:
            os.unlink(target_name, dir_fd=parent_fd)
        except FileNotFoundError:
            pass
        except OSError as err:
            raise DryRunOpeningSamplerGateError(
                f"failed to remove partial output: {target_name}"
            ) from err
    if backup_name is not None:
        try:
            os.replace(backup_name, target_name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        except OSError as err:
            raise DryRunOpeningSamplerGateError(f"failed to restore output: {target_name}") from err


def atomic_write(path: pathlib.Path, data: bytes) -> None:
    target = require_output_path(path)
    parent_fd = open_output_parent_fd(target)
    tmp_name: str | None = None
    try:
        tmp_name = write_temp_output(parent_fd, target.name, data)
        os.replace(tmp_name, target.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        tmp_name = None
        fsync_parent_dir(parent_fd, "single output publish")
    except OSError as err:
        raise DryRunOpeningSamplerGateError(f"failed to write output: {target}") from err
    finally:
        if tmp_name is not None:
            try:
                os.unlink(tmp_name, dir_fd=parent_fd)
            except OSError:
                pass
        os.close(parent_fd)


def atomic_write_pair(
    json_path: pathlib.Path,
    json_data: bytes,
    tsv_path: pathlib.Path,
    tsv_data: bytes,
) -> None:
    json_target = require_output_path(json_path)
    tsv_target = require_output_path(tsv_path)
    if json_target == tsv_target:
        raise DryRunOpeningSamplerGateError("paired output paths must be distinct files")
    if json_target.parent != tsv_target.parent:
        raise DryRunOpeningSamplerGateError("paired output paths must share one parent directory")
    parent_fd = open_output_parent_fd(json_target)
    json_tmp: str | None = None
    tsv_tmp: str | None = None
    json_backup: str | None = None
    tsv_backup: str | None = None
    json_published = False
    tsv_published = False
    try:
        json_tmp = write_temp_output(parent_fd, json_target.name, json_data)
        tsv_tmp = write_temp_output(parent_fd, tsv_target.name, tsv_data)
        json_backup = backup_existing_output(parent_fd, json_target.name)
        tsv_backup = backup_existing_output(parent_fd, tsv_target.name)
        os.replace(json_tmp, json_target.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        json_tmp = None
        json_published = True
        os.replace(tsv_tmp, tsv_target.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        tsv_tmp = None
        tsv_published = True
        for backup_name in (json_backup, tsv_backup):
            if backup_name is not None:
                os.unlink(backup_name, dir_fd=parent_fd)
        json_backup = None
        tsv_backup = None
        fsync_parent_dir(parent_fd, "paired output publish")
    except DryRunOpeningSamplerGateError:
        restore_output_backup(parent_fd, json_target.name, json_backup, json_published)
        restore_output_backup(parent_fd, tsv_target.name, tsv_backup, tsv_published)
        fsync_parent_dir(parent_fd, "paired output rollback")
        raise
    except OSError as err:
        restore_output_backup(parent_fd, json_target.name, json_backup, json_published)
        restore_output_backup(parent_fd, tsv_target.name, tsv_backup, tsv_published)
        fsync_parent_dir(parent_fd, "paired output rollback")
        raise DryRunOpeningSamplerGateError("failed to publish paired outputs") from err
    finally:
        for tmp_name in (json_tmp, tsv_tmp):
            if tmp_name is not None:
                try:
                    os.unlink(tmp_name, dir_fd=parent_fd)
                except OSError:
                    pass
        for backup_name in (json_backup, tsv_backup):
            if backup_name is not None:
                try:
                    os.unlink(backup_name, dir_fd=parent_fd)
                except OSError:
                    pass
        os.close(parent_fd)


def write_outputs(json_path: pathlib.Path, tsv_path: pathlib.Path, payload: dict[str, Any]) -> None:
    validate_payload(payload)
    json_data = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True).encode() + b"\n"
    tsv_data = render_tsv(payload).encode()
    atomic_write_pair(
        json_path,
        json_data,
        tsv_path,
        tsv_data,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_payload()
    if args.write_json or args.write_tsv:
        if not args.write_json or not args.write_tsv:
            raise DryRunOpeningSamplerGateError("--write-json and --write-tsv must be paired")
        write_outputs(args.write_json, args.write_tsv, payload)
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DryRunOpeningSamplerGateError as err:
        print(f"error: {err}", file=sys.stderr)
        raise SystemExit(2)
