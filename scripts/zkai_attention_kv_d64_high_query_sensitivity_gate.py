#!/usr/bin/env python3.10
"""Gate d64 four-head seq64 higher-FRI-query sensitivity evidence.

This is engineering evidence for issue #769. It extends the small d8
high-query slice to the paper-relevant d64 four-head seq64 surface, while
keeping the publication/default backend on the q=3 Stwo configuration.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import pathlib
import sys
from typing import Any


if sys.version_info < (3, 10):
    raise RuntimeError("zkai_attention_kv_d64_high_query_sensitivity_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
HIGH_QUERY_DIR = EVIDENCE_DIR / "high-query"
JSON_OUT = EVIDENCE_DIR / "zkai-attention-kv-d64-high-query-sensitivity-2026-06.json"
TSV_OUT = EVIDENCE_DIR / "zkai-attention-kv-d64-high-query-sensitivity-2026-06.tsv"
MD_OUT = ROOT / "docs" / "engineering" / "zkai-attention-kv-d64-high-query-sensitivity-2026-06.md"

SCHEMA = "zkai-attention-kv-d64-high-query-sensitivity-v1"
DATE = "2026-06-26"
ISSUE = 769
DECISION = "GO_D64_H4_SEQ64_HIGH_QUERY_SENSITIVITY_Q6_Q12"
SURFACE = "d64_four_head_seq64_bounded_softmax_table_attention"
BACKEND = "unmodified_stwo_2_2_0_with_explicit_query_count_patch"
TOOLCHAIN = "cargo +nightly-2025-07-14 --locked --features stwo-backend"
PAYLOAD_DOMAIN = "ptvm:zkai:attention-kv-d64-high-query-sensitivity:v1"
CLAIM_BOUNDARY = (
    "D64_FOUR_HEAD_SEQ64_HIGHER_FRI_QUERY_SENSITIVITY_FOR_SPLIT_VS_FUSED_PROOF_BYTES;"
    "ENGINEERING_EVIDENCE;NOT_PRODUCTION_SECURITY;NOT_TIMING;NOT_SYSTEM_COMPARISON"
)

ROLES = ("source", "sidecar", "fused")
PROOF_SECTION_KEYS = (
    "config",
    "commitments",
    "sampled_values",
    "decommitments",
    "queried_values",
    "proof_of_work",
    "fri_proof",
)
TSV_COLUMNS = (
    "fri_query_count",
    "source_proof_size_bytes",
    "sidecar_proof_size_bytes",
    "source_plus_sidecar_raw_proof_bytes",
    "fused_proof_size_bytes",
    "fused_saves_vs_source_plus_sidecar_bytes",
    "fused_to_split_ratio",
    "fused_growth_vs_q3",
    "split_growth_vs_q3",
    "resource_limit_status",
)

SOURCE_INPUT = (
    "docs/engineering/evidence/"
    "zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.json"
)
CARGO_RUN = "CARGO_INCREMENTAL=0 RUSTFLAGS='-C debuginfo=0' cargo +nightly-2025-07-14 run --locked --features stwo-backend"
ROLE_BINS = {
    "source": "zkai_attention_kv_native_d64_four_head_seq64_bounded_softmax_table_proof",
    "sidecar": "zkai_attention_kv_native_d64_four_head_seq64_softmax_table_lookup_proof",
    "fused": "zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_proof",
}

EXPECTED_ROWS: dict[int, dict[str, Any]] = {
    3: {
        "paths": {
            "source": EVIDENCE_DIR
            / "zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.envelope.json",
            "sidecar": EVIDENCE_DIR
            / "zkai-attention-kv-stwo-native-d64-four-head-seq64-softmax-table-logup-sidecar-proof-2026-05.envelope.json",
            "fused": EVIDENCE_DIR
            / "zkai-attention-kv-stwo-native-d64-four-head-seq64-fused-softmax-table-proof-2026-05.envelope.json",
        },
        "sha256": {
            "source": "955de60217be05dd5bf61d51990f6f553050feb87c9051be22cc53869071fcca",
            "sidecar": "64cb8b285340eed5e5dcb059fcdb2adb5f1952a2ddea999b8065899c98f1a835",
            "fused": "641bcd4c8b29ad8098b47a4ec293b6972913ad0ceee9548229a219bd3bea7000",
        },
        "proof_size_bytes": {"source": 272_638, "sidecar": 43_147, "fused": 276_503},
        "resource_limit_status": "checked_default_artifact",
    },
    6: {
        "paths": {
            "source": HIGH_QUERY_DIR / "zkai-attention-kv-d64-four-head-seq64-q6-source-proof-2026-06.envelope.json",
            "sidecar": HIGH_QUERY_DIR / "zkai-attention-kv-d64-four-head-seq64-q6-sidecar-proof-2026-06.envelope.json",
            "fused": HIGH_QUERY_DIR / "zkai-attention-kv-d64-four-head-seq64-q6-fused-proof-2026-06.envelope.json",
        },
        "sha256": {
            "source": "4ce332c04eca0e8749e32e2ff1318deb2f4f520a219cc937e23feb76843c3e60",
            "sidecar": "260b849e2aa7bd9e907b75c8988fad3fb3af2cd203d9dc9a52159deb3a5918cb",
            "fused": "7eb2c70fcae2bfe5d449498b3a62ddd637473a0a6b1176d4cbabd7ff0e1ad3d5",
        },
        "proof_size_bytes": {"source": 387_078, "sidecar": 66_655, "fused": 390_437},
        "resource_limit_status": "verified_with_query_count_patch_and_reduced_build_output",
    },
    12: {
        "paths": {
            "source": HIGH_QUERY_DIR / "zkai-attention-kv-d64-four-head-seq64-q12-source-proof-2026-06.envelope.json",
            "sidecar": HIGH_QUERY_DIR / "zkai-attention-kv-d64-four-head-seq64-q12-sidecar-proof-2026-06.envelope.json",
            "fused": HIGH_QUERY_DIR / "zkai-attention-kv-d64-four-head-seq64-q12-fused-proof-2026-06.envelope.json",
        },
        "sha256": {
            "source": "cd7a2ec0257fe717684ab5965121db9c02c7c9cf1e9ee659af50a8a7eef740da",
            "sidecar": "741bc1ffbb527ddcc5c62f4d6a797f6a9ae0c622a637dbdd9c0069d8663b2113",
            "fused": "d8b6cc7d993011948f1e532e9c11db6b8ebb52f425287c8ddb92008673f41a2e",
        },
        "proof_size_bytes": {"source": 601_616, "sidecar": 126_131, "fused": 612_237},
        "resource_limit_status": "verified_with_query_count_patch_and_reduced_build_output",
    },
}

PATCHES = {
    "q6": [
        {
            "path": "src/stwo_backend/mod.rs",
            "from": "FriConfig::new(0, 1, 3, 1)",
            "to": "FriConfig::new(0, 1, 6, 1)",
            "reason": "raise FRI query count while keeping blowup, fold step, and PoW fixed",
        }
    ],
    "q12": [
        {
            "path": "src/stwo_backend/mod.rs",
            "from": "FriConfig::new(0, 1, 3, 1)",
            "to": "FriConfig::new(0, 1, 12, 1)",
            "reason": "raise FRI query count while keeping blowup, fold step, and PoW fixed",
        }
    ],
}

VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_attention_kv_d64_high_query_sensitivity_gate.py "
    "--write-json docs/engineering/evidence/zkai-attention-kv-d64-high-query-sensitivity-2026-06.json "
    "--write-tsv docs/engineering/evidence/zkai-attention-kv-d64-high-query-sensitivity-2026-06.tsv "
    "--write-md docs/engineering/zkai-attention-kv-d64-high-query-sensitivity-2026-06.md",
    "python3.10 -m py_compile scripts/zkai_attention_kv_d64_high_query_sensitivity_gate.py "
    "scripts/tests/test_zkai_attention_kv_d64_high_query_sensitivity_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_attention_kv_d64_high_query_sensitivity_gate",
    "git diff --check",
)

NON_CLAIMS = (
    "not production-security parameter evidence",
    "not a proving-time or verifier-time claim",
    "not exact real-valued Softmax",
    "not full transformer inference",
    "not a comparison with external zkML systems",
    "not evidence that higher query count always improves fused-to-split ratio",
    "not a permanent Stwo-AI backend change",
    "not a change to the publication/default q3 backend configuration",
)

MUTATION_NAMES = (
    "decision_overclaim",
    "claim_boundary_overclaim",
    "missing_non_claim",
    "query_count_patch_drift",
    "q6_fused_size_drift",
    "q12_split_size_drift",
    "q12_config_query_drift",
    "q12_artifact_hash_drift",
    "stale_artifact_relabel",
    "payload_commitment_drift",
)
PAYLOAD_CORE_KEYS = frozenset(
    {
        "schema",
        "date",
        "issue",
        "decision",
        "claim_boundary",
        "surface",
        "backend",
        "toolchain",
        "fixed_fields",
        "build_environment",
        "query_count_patches",
        "rows",
        "aggregate",
        "interpretation",
        "validation_commands",
        "non_claims",
        "payload_commitment",
    }
)
PAYLOAD_MUTATION_SUMMARY_KEYS = frozenset(
    {
        "mutation_cases",
        "mutations_checked",
        "mutations_rejected",
        "all_mutations_rejected",
    }
)


class D64HighQuerySensitivityGateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    except (TypeError, ValueError) as err:
        raise D64HighQuerySensitivityGateError(f"non-canonical JSON value: {err}") from err


def blake2b_commitment(domain: str, value: Any) -> str:
    digest = hashlib.blake2b(domain.encode() + b"\0" + canonical_json_bytes(value), digest_size=32).hexdigest()
    return f"blake2b-256:{digest}"


def payload_commitment(payload: dict[str, Any]) -> str:
    item = copy.deepcopy(payload)
    item.pop("payload_commitment", None)
    for key in PAYLOAD_MUTATION_SUMMARY_KEYS:
        item.pop(key, None)
    return blake2b_commitment(PAYLOAD_DOMAIN, item)


def sha256_file(path: pathlib.Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as err:
        raise D64HighQuerySensitivityGateError(f"missing evidence file: {path}") from err


def load_proof_envelope(path: pathlib.Path) -> tuple[dict[str, Any], int, int]:
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise D64HighQuerySensitivityGateError(f"invalid envelope {path}: {err}") from err
    proof_raw = envelope.get("proof")
    if not isinstance(proof_raw, list) or not proof_raw:
        raise D64HighQuerySensitivityGateError(f"{path}: proof byte array missing")
    proof = bytearray()
    for index, value in enumerate(proof_raw):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 255:
            raise D64HighQuerySensitivityGateError(f"{path}: proof byte {index} invalid")
        proof.append(value)
    try:
        proof_json = json.loads(bytes(proof).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        raise D64HighQuerySensitivityGateError(f"{path}: proof JSON invalid: {err}") from err
    stark_proof = proof_json.get("stark_proof")
    if not isinstance(stark_proof, dict) or set(stark_proof) != set(PROOF_SECTION_KEYS):
        raise D64HighQuerySensitivityGateError(f"{path}: stark proof section drift")
    return stark_proof, len(proof), path.stat().st_size


def proof_artifact(query_count: int, role: str) -> dict[str, Any]:
    expected = EXPECTED_ROWS[query_count]
    path = expected["paths"][role]
    actual_sha = sha256_file(path)
    if actual_sha != expected["sha256"][role]:
        raise D64HighQuerySensitivityGateError(f"q{query_count} {role} artifact sha256 drift")
    stark_proof, proof_size, envelope_size = load_proof_envelope(path)
    expected_size = expected["proof_size_bytes"][role]
    if proof_size != expected_size:
        raise D64HighQuerySensitivityGateError(f"q{query_count} {role} proof size drift")
    config = stark_proof["config"]
    fri_config = config.get("fri_config")
    if config.get("pow_bits") != 10 or not isinstance(fri_config, dict):
        raise D64HighQuerySensitivityGateError(f"q{query_count} {role} config drift")
    if (
        fri_config.get("log_blowup_factor") != 1
        or fri_config.get("log_last_layer_degree_bound") != 0
        or fri_config.get("n_queries") != query_count
        or fri_config.get("fold_step") != 1
        or config.get("lifting_log_size") is not None
    ):
        raise D64HighQuerySensitivityGateError(f"q{query_count} {role} FRI config drift")
    section_bytes = {key: len(canonical_json_bytes(stark_proof[key])) for key in PROOF_SECTION_KEYS}
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": actual_sha,
        "proof_size_bytes": proof_size,
        "envelope_size_bytes": envelope_size,
        "proof_config": config,
        "section_bytes": section_bytes,
    }


def build_row(query_count: int, q3_split: int, q3_fused: int) -> dict[str, Any]:
    artifacts = {role: proof_artifact(query_count, role) for role in ROLES}
    source = artifacts["source"]["proof_size_bytes"]
    sidecar = artifacts["sidecar"]["proof_size_bytes"]
    fused = artifacts["fused"]["proof_size_bytes"]
    split = source + sidecar
    saving = split - fused
    if saving <= 0:
        raise D64HighQuerySensitivityGateError(f"q{query_count} fused does not beat split")
    return {
        "fri_query_count": query_count,
        "proof_config": artifacts["fused"]["proof_config"],
        "artifacts": artifacts,
        "source_proof_size_bytes": source,
        "sidecar_proof_size_bytes": sidecar,
        "source_plus_sidecar_raw_proof_bytes": split,
        "fused_proof_size_bytes": fused,
        "fused_saves_vs_source_plus_sidecar_bytes": saving,
        "fused_to_split_ratio": round(fused / split, 6),
        "split_growth_vs_q3": round(split / q3_split, 6),
        "fused_growth_vs_q3": round(fused / q3_fused, 6),
        "resource_limit_status": EXPECTED_ROWS[query_count]["resource_limit_status"],
    }


def reproduction_commands(query_count: int) -> list[str]:
    commands = []
    for role in ROLES:
        envelope_path = EXPECTED_ROWS[query_count]["paths"][role].relative_to(ROOT).as_posix()
        bin_name = ROLE_BINS[role]
        commands.append(f"{CARGO_RUN} --bin {bin_name} -- prove {SOURCE_INPUT} {envelope_path}")
        commands.append(f"{CARGO_RUN} --bin {bin_name} -- verify {envelope_path}")
    return commands


def expected_rows_and_aggregate() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    q3_expected = EXPECTED_ROWS[3]["proof_size_bytes"]
    q3_split = q3_expected["source"] + q3_expected["sidecar"]
    q3_fused = q3_expected["fused"]
    rows = [build_row(query_count, q3_split, q3_fused) for query_count in (3, 6, 12)]
    aggregate = {
        "surface": SURFACE,
        "query_counts_checked": [row["fri_query_count"] for row in rows],
        "q3_fused_to_split_ratio": rows[0]["fused_to_split_ratio"],
        "q6_fused_to_split_ratio": rows[1]["fused_to_split_ratio"],
        "q12_fused_to_split_ratio": rows[2]["fused_to_split_ratio"],
        "q3_saving_bytes": rows[0]["fused_saves_vs_source_plus_sidecar_bytes"],
        "q6_saving_bytes": rows[1]["fused_saves_vs_source_plus_sidecar_bytes"],
        "q12_saving_bytes": rows[2]["fused_saves_vs_source_plus_sidecar_bytes"],
        "q6_split_growth_vs_q3": rows[1]["split_growth_vs_q3"],
        "q6_fused_growth_vs_q3": rows[1]["fused_growth_vs_q3"],
        "q12_split_growth_vs_q3": rows[2]["split_growth_vs_q3"],
        "q12_fused_growth_vs_q3": rows[2]["fused_growth_vs_q3"],
        "q12_saving_growth_vs_q3": round(rows[2]["fused_saves_vs_source_plus_sidecar_bytes"] / rows[0]["fused_saves_vs_source_plus_sidecar_bytes"], 6),
        "q12_requires_resource_limit_retune": False,
    }
    return rows, aggregate


def build_payload() -> dict[str, Any]:
    rows, aggregate = expected_rows_and_aggregate()
    payload = {
        "schema": SCHEMA,
        "date": DATE,
        "issue": ISSUE,
        "decision": DECISION,
        "claim_boundary": CLAIM_BOUNDARY,
        "surface": SURFACE,
        "backend": BACKEND,
        "toolchain": TOOLCHAIN,
        "fixed_fields": {
            "pow_bits": 10,
            "fri_log_blowup": 1,
            "fri_blowup_factor": 2,
            "fri_fold_step": 1,
            "fri_log_last_layer_degree_bound": 0,
        },
        "build_environment": {
            "cargo_incremental": "0",
            "rustflags": "-C debuginfo=0",
            "reason": "reduce local build output on a disk-constrained machine; proof config is still decoded from artifacts",
        },
        "query_count_patches": copy.deepcopy(PATCHES),
        "rows": rows,
        "aggregate": aggregate,
        "interpretation": (
            "On the d64 four-head seq64 surface, q6 and q12 preserve the fused proof-size win. "
            "The absolute saving grows from 39282 bytes at q3 to 63296 bytes at q6 and 115510 bytes at q12. "
            "The q12 fused/split ratio is 0.841277x under the same fixed PoW, blowup, fold-step, and query-count-only patch discipline. "
            "This is engineering evidence for boundary-selection robustness under higher FRI query count, not a production-security or timing claim."
        ),
        "validation_commands": list(VALIDATION_COMMANDS),
        "non_claims": list(NON_CLAIMS),
    }
    payload["payload_commitment"] = payload_commitment(payload)
    mutation_cases = run_mutations(payload)
    payload["mutation_cases"] = mutation_cases
    payload["mutations_checked"] = len(mutation_cases)
    payload["mutations_rejected"] = sum(1 for item in mutation_cases if item["rejected"])
    payload["all_mutations_rejected"] = payload["mutations_checked"] == payload["mutations_rejected"]
    return payload


def validate_payload(
    payload: Any,
    *,
    allow_missing_mutation_summary: bool = False,
    expected_rows: list[dict[str, Any]] | None = None,
    expected_aggregate: dict[str, Any] | None = None,
) -> None:
    if not isinstance(payload, dict):
        raise D64HighQuerySensitivityGateError("payload must be a JSON object")
    actual_keys = set(payload)
    allowed_keys = PAYLOAD_CORE_KEYS | PAYLOAD_MUTATION_SUMMARY_KEYS
    if "scratch_patches" in payload:
        raise D64HighQuerySensitivityGateError("legacy scratch_patches field")
    if not actual_keys <= allowed_keys or not PAYLOAD_CORE_KEYS <= actual_keys:
        raise D64HighQuerySensitivityGateError("top-level key drift")
    if not allow_missing_mutation_summary and not PAYLOAD_MUTATION_SUMMARY_KEYS <= actual_keys:
        raise D64HighQuerySensitivityGateError("mutation summary drift")
    if payload.get("schema") != SCHEMA:
        raise D64HighQuerySensitivityGateError("schema drift")
    if payload.get("decision") != DECISION:
        raise D64HighQuerySensitivityGateError("decision drift")
    if payload.get("claim_boundary") != CLAIM_BOUNDARY:
        raise D64HighQuerySensitivityGateError("claim boundary drift")
    if tuple(payload.get("non_claims", ())) != NON_CLAIMS:
        raise D64HighQuerySensitivityGateError("non-claims drift")
    if payload.get("query_count_patches") != PATCHES:
        raise D64HighQuerySensitivityGateError("query-count patch drift")
    rows = payload.get("rows")
    if not isinstance(rows, list) or [row.get("fri_query_count") for row in rows] != [3, 6, 12]:
        raise D64HighQuerySensitivityGateError("query row drift")
    if (expected_rows is None) != (expected_aggregate is None):
        raise D64HighQuerySensitivityGateError("expected row cache drift")
    if expected_rows is None or expected_aggregate is None:
        expected_rows, expected_aggregate = expected_rows_and_aggregate()
    for actual, expected in zip(rows, expected_rows):
        fields = (
            "source_proof_size_bytes",
            "sidecar_proof_size_bytes",
            "source_plus_sidecar_raw_proof_bytes",
            "fused_proof_size_bytes",
            "fused_saves_vs_source_plus_sidecar_bytes",
            "fused_to_split_ratio",
            "split_growth_vs_q3",
            "fused_growth_vs_q3",
            "resource_limit_status",
        )
        for field in fields:
            if actual.get(field) != expected[field]:
                raise D64HighQuerySensitivityGateError(f"q{expected['fri_query_count']} {field} drift")
        if actual.get("proof_config") != expected["proof_config"]:
            raise D64HighQuerySensitivityGateError(f"q{expected['fri_query_count']} proof config drift")
        if actual.get("artifacts") != expected["artifacts"]:
            raise D64HighQuerySensitivityGateError(f"q{expected['fri_query_count']} artifact block drift")
    aggregate = payload.get("aggregate")
    if not isinstance(aggregate, dict) or aggregate != expected_aggregate:
        raise D64HighQuerySensitivityGateError("aggregate drift")
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise D64HighQuerySensitivityGateError("payload commitment drift")
    if not allow_missing_mutation_summary:
        if payload.get("mutations_checked") != len(MUTATION_NAMES):
            raise D64HighQuerySensitivityGateError("mutation count drift")
        if payload.get("mutations_rejected") != len(MUTATION_NAMES) or not payload.get("all_mutations_rejected"):
            raise D64HighQuerySensitivityGateError("mutation rejection drift")


def run_mutations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    mutations: list[tuple[str, Any]] = []

    def add(name: str, mutator: Any) -> None:
        mutations.append((name, mutator))

    add("decision_overclaim", lambda p: p.__setitem__("decision", "GO_PRODUCTION_SECURITY_HIGH_QUERY_RESULT"))
    add("claim_boundary_overclaim", lambda p: p.__setitem__("claim_boundary", "HEADLINE_D64_D128_HIGH_QUERY_PROOF_SIZE_WIN"))
    add("missing_non_claim", lambda p: p["non_claims"].remove("not production-security parameter evidence"))
    add("query_count_patch_drift", lambda p: p["query_count_patches"]["q12"][0].__setitem__("to", "FriConfig::new(0, 1, 16, 1)"))
    add("q6_fused_size_drift", lambda p: p["rows"][1].__setitem__("fused_proof_size_bytes", p["rows"][1]["fused_proof_size_bytes"] - 1))
    add("q12_split_size_drift", lambda p: p["rows"][2].__setitem__("source_plus_sidecar_raw_proof_bytes", p["rows"][2]["source_plus_sidecar_raw_proof_bytes"] - 1))
    add("q12_config_query_drift", lambda p: p["rows"][2]["proof_config"]["fri_config"].__setitem__("n_queries", 11))
    add("q12_artifact_hash_drift", lambda p: p["rows"][2]["artifacts"]["fused"].__setitem__("sha256", "0" * 64))
    add("stale_artifact_relabel", lambda p: p["rows"][2]["artifacts"]["fused"].__setitem__("path", p["rows"][0]["artifacts"]["fused"]["path"]))
    add("payload_commitment_drift", lambda p: p.__setitem__("payload_commitment", "blake2b-256:" + "00" * 32))

    if tuple(name for name, _ in mutations) != MUTATION_NAMES:
        raise D64HighQuerySensitivityGateError("mutation name drift")
    expected_rows, expected_aggregate = expected_rows_and_aggregate()
    results = []
    for name, mutator in mutations:
        candidate = copy.deepcopy(payload)
        for key in PAYLOAD_MUTATION_SUMMARY_KEYS:
            candidate.pop(key, None)
        rejected = False
        error = ""
        try:
            mutator(candidate)
            validate_payload(
                candidate,
                allow_missing_mutation_summary=True,
                expected_rows=expected_rows,
                expected_aggregate=expected_aggregate,
            )
        except D64HighQuerySensitivityGateError as err:
            rejected = True
            error = str(err)
        results.append({"name": name, "rejected": rejected, "error": error})
    return results


def write_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_tsv(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TSV_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in payload["rows"]:
            writer.writerow({field: row[field] for field in TSV_COLUMNS})


def write_md(path: pathlib.Path, payload: dict[str, Any]) -> None:
    rows = payload["rows"]
    lines = [
        "# d64 High-Query Sensitivity",
        "",
        f"- Issue: `#{ISSUE}`",
        f"- Decision: `{DECISION}`",
        f"- Surface: `{SURFACE}`",
        f"- Backend: `{BACKEND}`",
        "",
        "## Result",
        "",
        "This is a larger-surface higher-query sensitivity slice, not a production-security claim. It reruns the d64 four-head seq64 bounded Softmax-table attention surface with higher FRI query counts and the same split-versus-fused comparator.",
        "",
        "| FRI queries | split proof bytes | fused proof bytes | saving | fused/split | fused growth vs q3 | split growth vs q3 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {fri_query_count} | {source_plus_sidecar_raw_proof_bytes} | {fused_proof_size_bytes} | {fused_saves_vs_source_plus_sidecar_bytes} | {fused_to_split_ratio:.6f} | {fused_growth_vs_q3:.6f} | {split_growth_vs_q3:.6f} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            payload["interpretation"],
            "",
            "The important signal is not that q12 is a production-security profile. It is that increasing FRI query count on the existing d64 four-head seq64 surface did not erase the fused proof-size win. The absolute saving grew because the split path pays duplicated source and sidecar proof plumbing.",
            "",
            "## Reproduction",
            "",
            "Use a throwaway worktree. Do not commit the temporary query-count patch to the publication branch.",
            "",
            "For q6, patch:",
            "",
            "```text",
            "src/stwo_backend/mod.rs:",
            "FriConfig::new(0, 1, 3, 1) -> FriConfig::new(0, 1, 6, 1)",
            "```",
            "",
            "For q12, patch:",
            "",
            "```text",
            "src/stwo_backend/mod.rs:",
            "FriConfig::new(0, 1, 3, 1) -> FriConfig::new(0, 1, 12, 1)",
            "```",
            "",
            "After applying the q6 patch, run:",
            "",
            "```bash",
            *reproduction_commands(6),
            "```",
            "",
            "After applying the q12 patch, run:",
            "",
            "```bash",
            *reproduction_commands(12),
            "```",
            "",
            "The checked envelopes are stored under `docs/engineering/evidence/high-query/` and this gate parses their proof configs, byte sizes, and hashes.",
            "",
            "## Non-Claims",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in NON_CLAIMS)
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    parser.add_argument("--write-md", type=pathlib.Path)
    args = parser.parse_args()

    payload = build_payload()
    validate_payload(payload)
    if args.write_json:
        write_json(args.write_json, payload)
    if args.write_tsv:
        write_tsv(args.write_tsv, payload)
    if args.write_md:
        write_md(args.write_md, payload)
    if not (args.write_json or args.write_tsv or args.write_md):
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
