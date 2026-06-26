#!/usr/bin/env python3.10
"""Gate a small higher-FRI-query sensitivity slice for proof-pressure paper work.

The paper headline stays on the fixed q=3 Stwo configuration. This gate records
one deliberately small sensitivity slice on the same d8 single-head bounded
attention surface, with q=6 and q=12 scratch reruns. It is engineering evidence,
not a production-security claim and not a headline d64/d128 rerun.
"""

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


if sys.version_info < (3, 10):
    raise RuntimeError("zkai_attention_kv_high_query_sensitivity_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
HIGH_QUERY_DIR = EVIDENCE_DIR / "high-query"
JSON_OUT = EVIDENCE_DIR / "zkai-attention-kv-d8-high-query-sensitivity-2026-06.json"
TSV_OUT = EVIDENCE_DIR / "zkai-attention-kv-d8-high-query-sensitivity-2026-06.tsv"
MD_OUT = ROOT / "docs" / "engineering" / "zkai-attention-kv-d8-high-query-sensitivity-2026-06-26.md"

SCHEMA = "zkai-attention-kv-d8-high-query-sensitivity-v1"
ISSUE = 765
DATE = "2026-06-26"
DECISION = "GO_SMALL_SURFACE_HIGH_QUERY_SENSITIVITY_WITH_RESOURCE_LIMIT_CAVEAT"
CLAIM_BOUNDARY = (
    "SMALL_D8_SINGLE_HEAD_SEQ8_HIGHER_FRI_QUERY_SENSITIVITY_FOR_SPLIT_VS_FUSED_PROOF_BYTES;"
    "NOT_HEADLINE_D64_D128_MEASUREMENT;NOT_PRODUCTION_SECURITY;NOT_TIMING;NOT_SYSTEM_COMPARISON"
)
SURFACE = "d8_single_head_seq8_bounded_softmax_table_attention"
BACKEND = "unmodified_stwo_2_2_0_with_scratch_pcs_config_patch"
TOOLCHAIN = "cargo +nightly-2025-07-14 --locked --features stwo-backend"
PAYLOAD_DOMAIN = "ptvm:zkai:attention-kv-d8-high-query-sensitivity:v1"

PROOF_SECTION_KEYS = (
    "config",
    "commitments",
    "sampled_values",
    "decommitments",
    "queried_values",
    "proof_of_work",
    "fri_proof",
)
ROLES = ("source", "sidecar", "fused")
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
EXPECTED_ROWS = {
    3: {
        "paths": {
            "source": EVIDENCE_DIR / "zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.envelope.json",
            "sidecar": EVIDENCE_DIR / "zkai-attention-kv-stwo-native-d8-softmax-table-logup-sidecar-proof-2026-05.envelope.json",
            "fused": EVIDENCE_DIR / "zkai-attention-kv-stwo-native-d8-fused-softmax-table-proof-2026-05.envelope.json",
        },
        "sha256": {
            "source": "1f3ee47d47d9e3df61704d23dff5eaf55c57d02ca140e42ba32cb330b3de2564",
            "sidecar": "955c501e6211d31483052b8cfedc0ae3946bc29f30087fe6aba2df0afc78c349",
            "fused": "2e0e9c17db31077e067d26aa5e18fc0dbcf2ab04a91431325d75988a796b2e07",
        },
        "proof_size_bytes": {"source": 44_692, "sidecar": 14_745, "fused": 47_698},
        "resource_limit_status": "checked_default_artifact",
    },
    6: {
        "paths": {
            "source": HIGH_QUERY_DIR / "zkai-attention-kv-d8-q6-source-proof-2026-06.envelope.json",
            "sidecar": HIGH_QUERY_DIR / "zkai-attention-kv-d8-q6-sidecar-proof-2026-06.envelope.json",
            "fused": HIGH_QUERY_DIR / "zkai-attention-kv-d8-q6-fused-proof-2026-06.envelope.json",
        },
        "sha256": {
            "source": "5130188ee66f77c6ec574cd262bdf3dfdcf3517e09c5e1da7d0d89e3bd378835",
            "sidecar": "054a903fe2c360bef356a0bc115807dcfcdcbc342a76d551a4ec4024f3f805f5",
            "fused": "a260ae5863d1ae77526fa291784996f7244e2f22bcf57eda6eab7d3cf0f4bf1a",
        },
        "proof_size_bytes": {"source": 60_828, "sidecar": 21_287, "fused": 62_889},
        "resource_limit_status": "verified_with_query_count_patch_only",
    },
    12: {
        "paths": {
            "source": HIGH_QUERY_DIR / "zkai-attention-kv-d8-q12-source-proof-2026-06.envelope.json",
            "sidecar": HIGH_QUERY_DIR / "zkai-attention-kv-d8-q12-sidecar-proof-2026-06.envelope.json",
            "fused": HIGH_QUERY_DIR / "zkai-attention-kv-d8-q12-fused-proof-2026-06.envelope.json",
        },
        "sha256": {
            "source": "d5b0e6512ae784eeaa5baefd80e37e708624bd26e4e0cbe8dcad4e3341a8ffe3",
            "sidecar": "b2f91bd48e434478df9456f10f28fbf8c6ba4113e4497e815f29cf8783eadaa4",
            "fused": "6d449b33979369cfd6f6970fa5baa940d21753c8112610c77aa4158fd31887ea",
        },
        "proof_size_bytes": {"source": 84_266, "sidecar": 27_164, "fused": 85_900},
        "resource_limit_status": "verified_after_scratch_source_proof_limit_raise",
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
        },
        {
            "path": "src/stwo_backend/attention_kv_native_d8_bounded_softmax_table_proof.rs",
            "from": "ZKAI_ATTENTION_KV_NATIVE_D8_BOUNDED_SOFTMAX_TABLE_MAX_PROOF_BYTES = 65_536",
            "to": "ZKAI_ATTENTION_KV_NATIVE_D8_BOUNDED_SOFTMAX_TABLE_MAX_PROOF_BYTES = 262_144",
            "reason": "q12 source proof is 84266 bytes, above the default d8 source proof ceiling",
        },
    ],
}
VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_attention_kv_high_query_sensitivity_gate.py --write-json docs/engineering/evidence/zkai-attention-kv-d8-high-query-sensitivity-2026-06.json --write-tsv docs/engineering/evidence/zkai-attention-kv-d8-high-query-sensitivity-2026-06.tsv --write-md docs/engineering/zkai-attention-kv-d8-high-query-sensitivity-2026-06-26.md",
    "python3.10 -m py_compile scripts/zkai_attention_kv_high_query_sensitivity_gate.py scripts/tests/test_zkai_attention_kv_high_query_sensitivity_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_attention_kv_high_query_sensitivity_gate",
    "git diff --check",
)
HIGH_QUERY_SOURCE_INPUT = "docs/engineering/evidence/zkai-attention-kv-stwo-native-d8-bounded-softmax-table-proof-2026-05.json"
HIGH_QUERY_CARGO_RUN = "cargo +nightly-2025-07-14 run --locked --features stwo-backend"
HIGH_QUERY_ROLE_BINS = {
    "source": "zkai_attention_kv_native_d8_bounded_softmax_table_proof",
    "sidecar": "zkai_attention_kv_native_d8_softmax_table_lookup_proof",
    "fused": "zkai_attention_kv_native_d8_fused_softmax_table_proof",
}
NON_CLAIMS = (
    "not a headline d64 or d128 high-query rerun",
    "not production-security parameter evidence",
    "not a proving-time or verifier-time claim",
    "not exact real-valued Softmax",
    "not full transformer inference",
    "not a comparison with external zkML systems",
    "not evidence that higher query count always improves fused-to-split ratio",
    "not a permanent Stwo-AI backend change",
)
MUTATION_NAMES = (
    "decision_overclaim",
    "claim_boundary_overclaim",
    "missing_non_claim",
    "q6_size_drift",
    "q12_size_drift",
    "q12_limit_caveat_removed",
    "q6_query_count_drift",
    "q12_query_count_drift",
    "payload_commitment_drift",
)


class HighQuerySensitivityGateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    except (TypeError, ValueError) as err:
        raise HighQuerySensitivityGateError(f"non-canonical JSON value: {err}") from err


def blake2b_commitment(domain: str, value: Any) -> str:
    digest = hashlib.blake2b(domain.encode() + b"\0" + canonical_json_bytes(value), digest_size=32).hexdigest()
    return f"blake2b-256:{digest}"


def payload_commitment(payload: dict[str, Any]) -> str:
    item = copy.deepcopy(payload)
    item.pop("payload_commitment", None)
    item.pop("mutation_cases", None)
    item.pop("mutations_checked", None)
    item.pop("mutations_rejected", None)
    item.pop("all_mutations_rejected", None)
    return blake2b_commitment(PAYLOAD_DOMAIN, item)


def sha256_file(path: pathlib.Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as err:
        raise HighQuerySensitivityGateError(f"missing evidence file: {path}") from err


def load_proof_envelope(path: pathlib.Path) -> tuple[dict[str, Any], int, int]:
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise HighQuerySensitivityGateError(f"invalid envelope {path}: {err}") from err
    proof_raw = envelope.get("proof")
    if not isinstance(proof_raw, list) or not proof_raw:
        raise HighQuerySensitivityGateError(f"{path}: proof byte array missing")
    proof = bytearray()
    for index, value in enumerate(proof_raw):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 255:
            raise HighQuerySensitivityGateError(f"{path}: proof byte {index} invalid")
        proof.append(value)
    try:
        proof_json = json.loads(bytes(proof).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        raise HighQuerySensitivityGateError(f"{path}: proof JSON invalid: {err}") from err
    stark_proof = proof_json.get("stark_proof")
    if not isinstance(stark_proof, dict) or set(stark_proof) != set(PROOF_SECTION_KEYS):
        raise HighQuerySensitivityGateError(f"{path}: stark proof section drift")
    return stark_proof, len(proof), path.stat().st_size


def proof_artifact(query_count: int, role: str) -> dict[str, Any]:
    expected = EXPECTED_ROWS[query_count]
    path = expected["paths"][role]
    actual_sha = sha256_file(path)
    if actual_sha != expected["sha256"][role]:
        raise HighQuerySensitivityGateError(f"q{query_count} {role} artifact sha256 drift")
    stark_proof, proof_size, envelope_size = load_proof_envelope(path)
    expected_size = expected["proof_size_bytes"][role]
    if proof_size != expected_size:
        raise HighQuerySensitivityGateError(f"q{query_count} {role} proof size drift")
    config = stark_proof["config"]
    fri_config = config.get("fri_config")
    if config.get("pow_bits") != 10 or not isinstance(fri_config, dict):
        raise HighQuerySensitivityGateError(f"q{query_count} {role} config drift")
    if (
        fri_config.get("log_blowup_factor") != 1
        or fri_config.get("log_last_layer_degree_bound") != 0
        or fri_config.get("n_queries") != query_count
        or fri_config.get("fold_step") != 1
        or config.get("lifting_log_size") is not None
    ):
        raise HighQuerySensitivityGateError(f"q{query_count} {role} FRI config drift")
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
        raise HighQuerySensitivityGateError(f"q{query_count} fused does not beat split")
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


def high_query_reproduction_commands(query_count: int) -> list[str]:
    commands = []
    for role in ROLES:
        envelope_path = EXPECTED_ROWS[query_count]["paths"][role].relative_to(ROOT).as_posix()
        bin_name = HIGH_QUERY_ROLE_BINS[role]
        commands.append(
            f"{HIGH_QUERY_CARGO_RUN} --bin {bin_name} -- prove {HIGH_QUERY_SOURCE_INPUT} {envelope_path}"
        )
        commands.append(f"{HIGH_QUERY_CARGO_RUN} --bin {bin_name} -- verify {envelope_path}")
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
        "q12_split_growth_vs_q3": rows[2]["split_growth_vs_q3"],
        "q12_fused_growth_vs_q3": rows[2]["fused_growth_vs_q3"],
        "q12_requires_resource_limit_retune": True,
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
        "scratch_patches": PATCHES,
        "rows": rows,
        "aggregate": aggregate,
        "interpretation": (
            "On this small d8 surface, q6 and q12 preserve the fused proof-size win. "
            "The absolute saving grows from 11739 bytes at q3 to 19226 at q6 and 25530 at q12. "
            "The q12 source proof also exceeds the current default d8 source proof byte ceiling, so "
            "higher-query experiments need explicit resource-limit retuning before promotion."
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
    payload: dict[str, Any],
    *,
    allow_missing_mutation_summary: bool = False,
    expected_rows: list[dict[str, Any]] | None = None,
    expected_aggregate: dict[str, Any] | None = None,
) -> None:
    if payload.get("schema") != SCHEMA:
        raise HighQuerySensitivityGateError("schema drift")
    if payload.get("decision") != DECISION:
        raise HighQuerySensitivityGateError("decision drift")
    if payload.get("claim_boundary") != CLAIM_BOUNDARY:
        raise HighQuerySensitivityGateError("claim boundary drift")
    if tuple(payload.get("non_claims", ())) != NON_CLAIMS:
        raise HighQuerySensitivityGateError("non-claims drift")
    rows = payload.get("rows")
    if not isinstance(rows, list) or [row.get("fri_query_count") for row in rows] != [3, 6, 12]:
        raise HighQuerySensitivityGateError("query row drift")
    if (expected_rows is None) != (expected_aggregate is None):
        raise HighQuerySensitivityGateError("expected row cache drift")
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
                raise HighQuerySensitivityGateError(f"q{expected['fri_query_count']} {field} drift")
        if actual.get("proof_config") != expected["proof_config"]:
            raise HighQuerySensitivityGateError(f"q{expected['fri_query_count']} proof config drift")
    aggregate = payload.get("aggregate")
    if not isinstance(aggregate, dict) or aggregate != expected_aggregate:
        raise HighQuerySensitivityGateError("aggregate drift")
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise HighQuerySensitivityGateError("payload commitment drift")
    if not allow_missing_mutation_summary:
        if payload.get("mutations_checked") != len(MUTATION_NAMES):
            raise HighQuerySensitivityGateError("mutation count drift")
        if payload.get("mutations_rejected") != len(MUTATION_NAMES) or not payload.get("all_mutations_rejected"):
            raise HighQuerySensitivityGateError("mutation rejection drift")


def run_mutations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    mutations: list[tuple[str, Any]] = []

    def add(name: str, mutator: Any) -> None:
        mutations.append((name, mutator))

    add("decision_overclaim", lambda p: p.__setitem__("decision", "GO_PRODUCTION_SECURITY_HIGH_QUERY_RESULT"))
    add("claim_boundary_overclaim", lambda p: p.__setitem__("claim_boundary", "HEADLINE_D64_D128_HIGH_QUERY_PROOF_SIZE_WIN"))
    add("missing_non_claim", lambda p: p["non_claims"].remove("not production-security parameter evidence"))
    add("q6_size_drift", lambda p: p["rows"][1].__setitem__("fused_proof_size_bytes", p["rows"][1]["fused_proof_size_bytes"] - 1))
    add("q12_size_drift", lambda p: p["rows"][2].__setitem__("source_plus_sidecar_raw_proof_bytes", p["rows"][2]["source_plus_sidecar_raw_proof_bytes"] - 1))
    add("q12_limit_caveat_removed", lambda p: p["rows"][2].__setitem__("resource_limit_status", "verified_with_query_count_patch_only"))
    add("q6_query_count_drift", lambda p: p["rows"][1]["proof_config"]["fri_config"].__setitem__("n_queries", 7))
    add("q12_query_count_drift", lambda p: p["rows"][2]["proof_config"]["fri_config"].__setitem__("n_queries", 11))
    add("payload_commitment_drift", lambda p: p.__setitem__("payload_commitment", "blake2b-256:" + "00" * 32))

    if tuple(name for name, _ in mutations) != MUTATION_NAMES:
        raise HighQuerySensitivityGateError("mutation name drift")
    expected_rows, expected_aggregate = expected_rows_and_aggregate()
    results = []
    for name, mutator in mutations:
        candidate = copy.deepcopy(payload)
        for key in ("mutation_cases", "mutations_checked", "mutations_rejected", "all_mutations_rejected"):
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
        except HighQuerySensitivityGateError as err:
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
        "# d8 High-Query Sensitivity",
        "",
        f"- Issue: `#{ISSUE}`",
        f"- Decision: `{DECISION}`",
        f"- Surface: `{SURFACE}`",
        f"- Backend: `{BACKEND}`",
        "",
        "## Result",
        "",
        "This is a small higher-query sensitivity slice, not a new headline row. It reruns the d8 single-head seq8 bounded Softmax-table attention surface with higher FRI query counts and the same split-versus-fused comparator.",
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
            "The q12 run is useful but should stay engineering-scoped: the source proof exceeded the current default d8 source proof byte ceiling and verified only after a scratch resource-limit retune.",
            "",
            "## Reproduction",
            "",
            "Use a throwaway worktree. Do not change the publication branch's default `publication_v1_pcs_config`.",
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
            "",
            "src/stwo_backend/attention_kv_native_d8_bounded_softmax_table_proof.rs:",
            "ZKAI_ATTENTION_KV_NATIVE_D8_BOUNDED_SOFTMAX_TABLE_MAX_PROOF_BYTES = 65_536",
            "->",
            "ZKAI_ATTENTION_KV_NATIVE_D8_BOUNDED_SOFTMAX_TABLE_MAX_PROOF_BYTES = 262_144",
            "```",
            "",
            "After applying the q6 patch, run:",
            "",
            "```bash",
            *high_query_reproduction_commands(6),
            "```",
            "",
            "After applying the q12 patch, run:",
            "",
            "```bash",
            *high_query_reproduction_commands(12),
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
