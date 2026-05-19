#!/usr/bin/env python3.10
"""Gate the pre-decommitment opening-policy boundary for seq32 attention+MLP."""

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
    raise RuntimeError(
        "zkai_native_seq32_attention_mlp_predecommit_opening_policy_gate requires Python 3.10+"
    )

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import zkai_native_seq32_attention_mlp_dry_run_opening_sampler_gate as sampler_gate


EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
JSON_OUT = (
    EVIDENCE_DIR
    / "zkai-native-seq32-attention-mlp-predecommit-opening-policy-2026-05.json"
)
TSV_OUT = (
    EVIDENCE_DIR
    / "zkai-native-seq32-attention-mlp-predecommit-opening-policy-2026-05.tsv"
)

SCHEMA = "zkai-native-seq32-attention-mlp-predecommit-opening-policy-gate-v1"
DECISION = "NARROW_CLAIM_CURRENT_STWO_WRAPPER_EXPOSES_QUERY_GEOMETRY_AFTER_PROVE_EX"
RESULT = (
    "POST_TRANSCRIPT_QUERY_GEOMETRY_SELECTS_PROBE_B_BUT_TRUE_PREDECOMMIT_CONTROL_REQUIRES_API_HOOK"
)
CLAIM_BOUNDARY = (
    "POLICY_INPUTS_USE_RAW_OPENING_SAMPLER_QUERY_GEOMETRY_ONLY;"
    "FINAL_ACCOUNTING_JOIN_USED_ONLY_FOR_EVALUATION;"
    "CURRENT_REPO_SAMPLER_CALLS_PROVE_SINGLE_EXTENDED_AND_READS_EXTENDED_AUX_AFTER_PROVE_EX;"
    "NO_TRUE_PREDECOMMIT_POLICY_CLAIM_NO_PRODUCTION_LABEL_POLICY_NO_NANOZK_COMPARISON"
)
ISSUE_HINT = "https://github.com/omarespejel/provable-transformer-vm/issues/700"
PAYLOAD_DOMAIN = "ptvm:zkai:native-seq32-attention-mlp-predecommit-opening-policy:v1"

EXPECTED_RUST_SOURCE_SHA256 = sampler_gate.EXPECTED_RUST_SOURCE_SHA256
EXPECTED_CLI_SOURCE_SHA256 = sampler_gate.EXPECTED_CLI_SOURCE_SHA256
EXPECTED_PREPROVE_EVIDENCE_SHA256 = sampler_gate.EXPECTED_PREPROVE_EVIDENCE_SHA256
EXPECTED_DRY_RUN_EVIDENCE_SHA256 = (
    "ea6e3e7f97b689d02c6c67e96436a6d10d1251be24d424b8eeaa3b15bb71f018"
)

BEST_VARIANT_ID = "adjacent_label_probe_b"
BEST_TYPED_BYTES = 37_532
BEST_PATH_OPENING_BYTES = 16_560
CURRENT_CHAMPION_TYPED_BYTES = 42_068
BEST_PRE_REGISTERED_SEED_ID = "adjacent_seed_02"
BEST_PRE_REGISTERED_SEED_TYPED_BYTES = 40_268
EXPECTED_SUPPORTED_LABEL_WORST_TYPED_BYTES = 40_332
EXPECTED_CANDIDATE_SAVING_VS_CHAMPION = 4_536
EXPECTED_CANDIDATE_SAVING_SHARE_VS_CHAMPION = "10.7825%"
EXPECTED_CANDIDATE_SAVING_VS_BEST_SEED = 2_736
EXPECTED_POLICY_ROW_COUNT = len(sampler_gate.VARIANTS)
EXPECTED_UNITTEST_STEP_COUNT = 15
EXPECTED_LOCAL_RELEASE_GATE_STEP_COUNT = 14

SOURCE_MARKERS = {
    "sampler_calls_full_extended_proof": "let extended = prove_single_extended(input)?;",
    "sampler_reads_extended_aux_query_locations": "extended.aux.unsorted_query_locations",
    "prove_single_extended_delegates_to_stwo_prove_ex": "prove_ex::<SimdBackend, Blake2sM31MerkleChannel>",
    "sampler_boundary_names_extended_aux_not_predecommit_hook": (
        "PROVER_INTERNAL_EXTENDED_AUX_QUERY_LOCATIONS_ONLY"
    ),
}
CLI_MARKERS = {
    "cli_exposes_sample_openings_command": '"sample-openings"',
    "cli_writes_sampler_after_sample_openings": "sample_zkai_native_seq32_attention_mlp_openings",
}
POLICY_FEATURE_KEYS = sampler_gate.PREDICTOR_FEATURE_KEYS
FORBIDDEN_POLICY_INPUT_KEYS = sampler_gate.FORBIDDEN_PREDICTOR_KEYS | {
    "final_path_opening_bytes",
    "final_typed_bytes",
    "final_json_proof_bytes",
    "envelope_path",
}
TSV_COLUMNS = (
    "variant_id",
    "adapter_mode",
    "policy_stage",
    "query_location_span",
    "min_pairwise_query_gap",
    "selected_without_final_accounting",
    "predicted_path_opening_bytes",
    "final_path_opening_bytes",
    "final_typed_bytes",
    "api_control_status",
)
VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_native_seq32_attention_mlp_predecommit_opening_policy_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-predecommit-opening-policy-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-predecommit-opening-policy-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_predecommit_opening_policy_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_predecommit_opening_policy_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_predecommit_opening_policy_gate",
    "git diff --check",
    "just gate-fast",
    "just gate",
)
NON_CLAIMS = (
    "not a true pre-decommitment selector in the current Stwo wrapper",
    "not a production label-selection policy",
    "not a new proof-size frontier beyond the existing adjacent probe-B row",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not a full transformer block proof",
    "not exact real-valued Softmax",
    "not timing evidence",
    "not production-ready zkML",
)
INTERPRETATION = {
    "human_read": (
        "The useful signal survives: the tight query cluster selects the 37,532 typed-byte "
        "probe-B row without using final accounting as an input. The limiting fact is where "
        "that signal appears. In the current wrapper, query locations are read from the "
        "ExtendedStarkProof after prove_ex, so this is post-transcript/pre-accounting "
        "selection, not true pre-decommitment control."
    ),
    "mechanism_read": (
        "Probe B is still the smallest checked adjacent row because its query span is only "
        "16,618 and its path-opening bucket is 16,560 typed bytes. To convert that into a "
        "real policy, Stwo needs a hook that separates query drawing from Merkle/FRI "
        "decommitment or accepts an externally pinned query policy."
    ),
    "next_experiment": (
        "Prototype a bounded Stwo query-policy hook or a local fork that exposes draw_queries "
        "before decommitment, then regenerate the seq32+d128 boundary under a committed query "
        "policy and re-run the same source-binding and mutation gates."
    ),
}
MUTATION_NAMES = (
    "decision_drift",
    "result_overclaim",
    "claim_boundary_predecommit_overclaim",
    "rust_source_digest_drift",
    "cli_source_digest_drift",
    "dry_run_digest_drift",
    "source_marker_erasure",
    "predecommit_available_flip",
    "policy_final_accounting_leak",
    "row_identity_promoted_to_policy",
    "selected_variant_drift",
    "candidate_saving_drift",
    "candidate_path_opening_drift",
    "required_hook_erasure",
    "evaluation_row_removed",
    "validation_command_removed",
    "non_claim_removed",
    "payload_commitment_drift",
)


class PredecommitOpeningPolicyGateError(Exception):
    pass


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
        raise PredecommitOpeningPolicyGateError(f"non-canonical JSON value: {err}") from err


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


def sha256_repo_file(path: pathlib.Path, label: str, max_bytes: int) -> str:
    raw = sampler_gate.read_bounded_repo_file(path, label, max_bytes)
    return sampler_gate.sha256_bytes(raw)


def read_source_text(path: pathlib.Path, label: str) -> str:
    raw = sampler_gate.read_bounded_repo_file(
        path,
        label,
        sampler_gate.MAX_SOURCE_ARTIFACT_BYTES,
    )
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as err:
        raise PredecommitOpeningPolicyGateError(f"{label} is not UTF-8") from err


def source_stage_audit() -> dict[str, Any]:
    rust_source = read_source_text(sampler_gate.RUST_SOURCE_PATH, "rust source")
    cli_source = read_source_text(sampler_gate.CLI_SOURCE_PATH, "cli source")
    marker_results = {
        name: marker in rust_source for name, marker in SOURCE_MARKERS.items()
    }
    marker_results.update({name: marker in cli_source for name, marker in CLI_MARKERS.items()})
    missing = [name for name, present in marker_results.items() if not present]
    if missing:
        raise PredecommitOpeningPolicyGateError(f"source stage marker drift: {missing}")
    return {
        "query_geometry_available_stage": "after_prove_single_extended_returns_extended_stark_proof",
        "current_api_control_status": "NO_TRUE_PREDECOMMIT_CONTROL_HOOK_IN_CURRENT_WRAPPER",
        "predecommit_control_available": False,
        "post_transcript_pre_accounting_policy_available": True,
        "source_markers": marker_results,
        "required_hook": (
            "split query drawing from Merkle/FRI decommitment or accept a committed external "
            "query policy before decommitment"
        ),
    }


def build_policy_rows_without_final_accounting() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in sampler_gate.VARIANTS:
        sampler = sampler_gate.read_json(
            ROOT / spec["sampler_path"],
            spec["variant_id"],
            sampler_gate.MAX_SAMPLER_JSON_BYTES,
        )
        sampler_gate.validate_sampler_document(sampler, spec)
        features = sampler_gate.query_features(sampler["sorted_unique_query_locations"])
        predicted, rule = sampler_gate.predict_path_opening_bucket(features)
        feature_subset = {key: features[key] for key in POLICY_FEATURE_KEYS}
        leaked = FORBIDDEN_POLICY_INPUT_KEYS.intersection(feature_subset)
        if leaked:
            raise PredecommitOpeningPolicyGateError(
                f"{spec['variant_id']} policy features leak forbidden keys: {sorted(leaked)}"
            )
        rows.append(
            {
                "variant_id": spec["variant_id"],
                "adapter_mode": sampler["adapter_mode"],
                "proof_backend_version": sampler["proof_backend_version"],
                "sampler_path": spec["sampler_path"],
                "sampler_sha256": spec["sampler_sha256"],
                "query_location_digest": sampler["query_location_digest"],
                "policy_input_features": feature_subset,
                "prediction_rule": rule,
                "predicted_path_opening_bytes": predicted,
            }
        )
    best_predicted = min(row["predicted_path_opening_bytes"] for row in rows)
    selected = [row for row in rows if row["predicted_path_opening_bytes"] == best_predicted]
    if len(selected) != 1:
        raise PredecommitOpeningPolicyGateError("policy selection is not unique")
    for row in rows:
        row["selected_without_final_accounting"] = row["variant_id"] == selected[0]["variant_id"]
    return rows


def evaluate_rows(policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    final_rows = sampler_gate.final_rows_by_variant()
    evaluated: list[dict[str, Any]] = []
    for row in policy_rows:
        final = final_rows[row["variant_id"]]
        evaluated.append(
            {
                **row,
                "final_path_opening_bytes": final["path_opening_bytes"],
                "final_typed_bytes": final["typed_bytes"],
                "final_json_proof_bytes": final["json_proof_bytes"],
                "final_value_bytes": final["value_bytes"],
            }
        )
    return evaluated


def source_artifacts() -> list[dict[str, Any]]:
    dry_run_path = sampler_gate.JSON_OUT
    dry_run_sha = sha256_repo_file(
        dry_run_path,
        "dry-run opening sampler evidence",
        sampler_gate.MAX_PREPROVE_EVIDENCE_BYTES,
    )
    if dry_run_sha != EXPECTED_DRY_RUN_EVIDENCE_SHA256:
        raise PredecommitOpeningPolicyGateError("dry-run evidence digest drift")
    return [
        sampler_gate.source_artifact(
            sampler_gate.RUST_SOURCE_PATH,
            "rust_native_seq32_attention_mlp_source",
            EXPECTED_RUST_SOURCE_SHA256,
        ),
        sampler_gate.source_artifact(
            sampler_gate.CLI_SOURCE_PATH,
            "cli_native_seq32_attention_mlp_source",
            EXPECTED_CLI_SOURCE_SHA256,
        ),
        sampler_gate.source_artifact(
            sampler_gate.PREPROVE_EVIDENCE_PATH,
            "preprove_opening_bucket_predictor_evidence",
            EXPECTED_PREPROVE_EVIDENCE_SHA256,
            sampler_gate.MAX_PREPROVE_EVIDENCE_BYTES,
        ),
        {
            "id": "dry_run_opening_sampler_evidence",
            "path": str(dry_run_path.relative_to(ROOT)),
            "sha256": dry_run_sha,
            "size_bytes": len(
                sampler_gate.read_bounded_repo_file(
                    dry_run_path,
                    "dry-run opening sampler evidence",
                    sampler_gate.MAX_PREPROVE_EVIDENCE_BYTES,
                )
            ),
        },
    ]


def build_payload_without_mutations() -> dict[str, Any]:
    policy_rows = build_policy_rows_without_final_accounting()
    evaluated_rows = evaluate_rows(policy_rows)
    selected = next(row for row in evaluated_rows if row["selected_without_final_accounting"])
    if selected["variant_id"] != BEST_VARIANT_ID:
        raise PredecommitOpeningPolicyGateError("selected variant drift")
    if selected["final_path_opening_bytes"] != BEST_PATH_OPENING_BYTES:
        raise PredecommitOpeningPolicyGateError("path-opening drift")
    if selected["final_typed_bytes"] != BEST_TYPED_BYTES:
        raise PredecommitOpeningPolicyGateError("typed-byte drift")
    saving_vs_champion = CURRENT_CHAMPION_TYPED_BYTES - selected["final_typed_bytes"]
    saving_vs_seed = BEST_PRE_REGISTERED_SEED_TYPED_BYTES - selected["final_typed_bytes"]
    if saving_vs_champion != EXPECTED_CANDIDATE_SAVING_VS_CHAMPION:
        raise PredecommitOpeningPolicyGateError("candidate saving vs champion drift")
    if saving_vs_seed != EXPECTED_CANDIDATE_SAVING_VS_BEST_SEED:
        raise PredecommitOpeningPolicyGateError("candidate saving vs best seed drift")
    return {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE_HINT,
        "claim_boundary": CLAIM_BOUNDARY,
        "api_stage_audit": source_stage_audit(),
        "policy_input": {
            "policy_stage": "post_transcript_pre_accounting_not_true_predecommit",
            "policy_feature_keys": list(POLICY_FEATURE_KEYS),
            "forbidden_policy_input_keys": sorted(FORBIDDEN_POLICY_INPUT_KEYS),
            "uses_final_accounting_as_input": False,
            "uses_row_identity_as_input": False,
            "uses_envelope_or_proof_bytes_as_input": False,
        },
        "policy_rows": policy_rows,
        "evaluation_rows": evaluated_rows,
        "evaluation": {
            "selected_variant_id": selected["variant_id"],
            "selected_final_typed_bytes": selected["final_typed_bytes"],
            "selected_final_path_opening_bytes": selected["final_path_opening_bytes"],
            "current_champion_typed_bytes": CURRENT_CHAMPION_TYPED_BYTES,
            "saving_vs_current_champion_typed_bytes": saving_vs_champion,
            "saving_vs_current_champion_share": EXPECTED_CANDIDATE_SAVING_SHARE_VS_CHAMPION,
            "best_pre_registered_seed_id": BEST_PRE_REGISTERED_SEED_ID,
            "best_pre_registered_seed_typed_bytes": BEST_PRE_REGISTERED_SEED_TYPED_BYTES,
            "saving_vs_best_pre_registered_seed_typed_bytes": saving_vs_seed,
            "worst_supported_label_typed_bytes": EXPECTED_SUPPORTED_LABEL_WORST_TYPED_BYTES,
            "true_predecommit_go_gate_satisfied": False,
            "narrow_claim_reason": (
                "candidate selection is query-geometry based, but query geometry is exposed "
                "after prove_ex in the current wrapper"
            ),
        },
        "reproducibility_metadata": {
            "selected_backend_version": selected["proof_backend_version"],
            "selected_adapter_mode": selected["adapter_mode"],
            "rust_source_sha256": EXPECTED_RUST_SOURCE_SHA256,
            "cli_source_sha256": EXPECTED_CLI_SOURCE_SHA256,
            "preprove_evidence_sha256": EXPECTED_PREPROVE_EVIDENCE_SHA256,
            "dry_run_evidence_sha256": EXPECTED_DRY_RUN_EVIDENCE_SHA256,
            "policy_row_count": len(policy_rows),
            "fri_query_count_per_row": sampler_gate.EXPECTED_FRI_QUERIES,
            "mutation_step_count": len(MUTATION_NAMES),
            "unittest_step_count": EXPECTED_UNITTEST_STEP_COUNT,
            "local_release_gate_step_count": EXPECTED_LOCAL_RELEASE_GATE_STEP_COUNT,
        },
        "interpretation": INTERPRETATION,
        "source_artifacts": source_artifacts(),
        "validation_commands": list(VALIDATION_COMMANDS),
        "non_claims": list(NON_CLAIMS),
    }


def validate_base_payload(payload: dict[str, Any]) -> None:
    enforce_selected_candidate(payload)
    expected = build_payload_without_mutations()
    if payload != expected:
        raise PredecommitOpeningPolicyGateError("base payload drift")
    api = payload["api_stage_audit"]
    if api["predecommit_control_available"]:
        raise PredecommitOpeningPolicyGateError("predecommit control overclaim")
    if not api["post_transcript_pre_accounting_policy_available"]:
        raise PredecommitOpeningPolicyGateError("post-transcript policy availability drift")
    policy = payload["policy_input"]
    if policy["uses_final_accounting_as_input"]:
        raise PredecommitOpeningPolicyGateError("policy leaks final accounting")
    if policy["uses_row_identity_as_input"]:
        raise PredecommitOpeningPolicyGateError("policy uses row identity")
    if FORBIDDEN_POLICY_INPUT_KEYS.intersection(policy["policy_feature_keys"]):
        raise PredecommitOpeningPolicyGateError("policy feature keys leak forbidden fields")
    selected = payload["evaluation"]["selected_variant_id"]
    if selected != BEST_VARIANT_ID:
        raise PredecommitOpeningPolicyGateError("selected variant drift")
    if payload["evaluation"]["true_predecommit_go_gate_satisfied"]:
        raise PredecommitOpeningPolicyGateError("true predecommit GO overclaim")
    metadata = payload["reproducibility_metadata"]
    if metadata["policy_row_count"] != EXPECTED_POLICY_ROW_COUNT:
        raise PredecommitOpeningPolicyGateError("policy row count drift")
    if metadata["mutation_step_count"] != len(MUTATION_NAMES):
        raise PredecommitOpeningPolicyGateError("mutation step count drift")


def enforce_selected_candidate(payload: dict[str, Any]) -> None:
    evaluation = payload.get("evaluation", {})
    selected_variant_id = evaluation.get("selected_variant_id")
    rows = payload.get("evaluation_rows", [])
    selected_rows = [row for row in rows if row.get("variant_id") == selected_variant_id]
    if len(selected_rows) != 1:
        raise PredecommitOpeningPolicyGateError("selected evaluation row drift")
    selected = selected_rows[0]
    if selected.get("final_path_opening_bytes") != BEST_PATH_OPENING_BYTES:
        raise PredecommitOpeningPolicyGateError("path-opening drift")
    if selected.get("final_typed_bytes") != BEST_TYPED_BYTES:
        raise PredecommitOpeningPolicyGateError("typed-byte drift")


def validate_payload(payload: dict[str, Any]) -> None:
    item = copy.deepcopy(payload)
    supplied_commitment = item.pop("payload_commitment", None)
    mutation_result = item.pop("mutation_result", None)
    validate_base_payload(item)
    if supplied_commitment != payload_commitment(payload):
        raise PredecommitOpeningPolicyGateError("payload commitment drift")
    expected_mutation = run_mutations(item)
    if mutation_result != expected_mutation:
        raise PredecommitOpeningPolicyGateError("mutation result drift")
    validate_mutation_result(mutation_result)


def validate_mutation_result(mutation_result: Any) -> None:
    if not isinstance(mutation_result, dict):
        raise PredecommitOpeningPolicyGateError("mutation result missing")
    if mutation_result.get("mutation_names") != list(MUTATION_NAMES):
        raise PredecommitOpeningPolicyGateError("mutation names drift")
    cases = mutation_result.get("cases")
    if not isinstance(cases, list) or len(cases) != len(MUTATION_NAMES):
        raise PredecommitOpeningPolicyGateError("mutation case count drift")
    for case in cases:
        if not isinstance(case, dict):
            raise PredecommitOpeningPolicyGateError("mutation case schema drift")
        if (
            not isinstance(case.get("name"), str)
            or not isinstance(case.get("rejected"), bool)
            or not isinstance(case.get("error"), str)
        ):
            raise PredecommitOpeningPolicyGateError("mutation case schema drift")
    rejected_names = [case.get("name") for case in cases if case.get("rejected") is True]
    if rejected_names != list(MUTATION_NAMES):
        raise PredecommitOpeningPolicyGateError("mutation rejection drift")
    if mutation_result.get("mutations_rejected") != len(MUTATION_NAMES):
        raise PredecommitOpeningPolicyGateError("mutation rejected count drift")
    if mutation_result.get("all_mutations_rejected") is not True:
        raise PredecommitOpeningPolicyGateError("mutation all-rejected drift")


def mutate_payload(name: str, item: dict[str, Any]) -> None:
    if name == "decision_drift":
        item["decision"] = "GO_TRUE_PREDECOMMIT_POLICY"
    elif name == "result_overclaim":
        item["result"] = "TRUE_PREDECOMMIT_POLICY_BEATS_NANOZK"
    elif name == "claim_boundary_predecommit_overclaim":
        item["claim_boundary"] = item["claim_boundary"].replace("NO_TRUE_PREDECOMMIT_POLICY_CLAIM_", "")
    elif name == "rust_source_digest_drift":
        item["source_artifacts"][0]["sha256"] = "0" * 64
    elif name == "cli_source_digest_drift":
        item["source_artifacts"][1]["sha256"] = "1" * 64
    elif name == "dry_run_digest_drift":
        item["source_artifacts"][3]["sha256"] = "2" * 64
    elif name == "source_marker_erasure":
        item["api_stage_audit"]["source_markers"]["sampler_calls_full_extended_proof"] = False
    elif name == "predecommit_available_flip":
        item["api_stage_audit"]["predecommit_control_available"] = True
    elif name == "policy_final_accounting_leak":
        item["policy_rows"][1]["policy_input_features"]["final_typed_bytes"] = 37_532
    elif name == "row_identity_promoted_to_policy":
        item["policy_input"]["policy_feature_keys"].append("statement_commitment")
    elif name == "selected_variant_drift":
        item["evaluation"]["selected_variant_id"] = "adjacent_seed_02"
    elif name == "candidate_saving_drift":
        item["evaluation"]["saving_vs_current_champion_typed_bytes"] = 6_900
    elif name == "candidate_path_opening_drift":
        for row in item["evaluation_rows"]:
            if row["variant_id"] == BEST_VARIANT_ID:
                row["final_path_opening_bytes"] = 19_296
                break
    elif name == "required_hook_erasure":
        item["api_stage_audit"]["required_hook"] = ""
    elif name == "evaluation_row_removed":
        item["evaluation_rows"].pop()
    elif name == "validation_command_removed":
        item["validation_commands"].pop()
    elif name == "non_claim_removed":
        item["non_claims"].remove("not a true pre-decommitment selector in the current Stwo wrapper")
    elif name == "payload_commitment_drift":
        item["payload_commitment"] = "blake2b-256:" + ("0" * 64)
    else:
        raise PredecommitOpeningPolicyGateError(f"unknown mutation: {name}")


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
        except PredecommitOpeningPolicyGateError as err:
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
    rows_by_variant = {row["variant_id"]: row for row in payload["evaluation_rows"]}
    for row in payload["policy_rows"]:
        evaluated = rows_by_variant[row["variant_id"]]
        writer.writerow(
            {
                "variant_id": row["variant_id"],
                "adapter_mode": row["adapter_mode"],
                "policy_stage": payload["policy_input"]["policy_stage"],
                "query_location_span": row["policy_input_features"]["query_location_span"],
                "min_pairwise_query_gap": row["policy_input_features"]["min_pairwise_query_gap"],
                "selected_without_final_accounting": str(
                    row["selected_without_final_accounting"]
                ).lower(),
                "predicted_path_opening_bytes": row["predicted_path_opening_bytes"],
                "final_path_opening_bytes": evaluated["final_path_opening_bytes"],
                "final_typed_bytes": evaluated["final_typed_bytes"],
                "api_control_status": payload["api_stage_audit"]["current_api_control_status"],
            }
        )
    return output.getvalue()


def write_outputs(json_path: pathlib.Path, tsv_path: pathlib.Path, payload: dict[str, Any]) -> None:
    validate_payload(payload)
    json_data = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True).encode() + b"\n"
    tsv_data = render_tsv(payload).encode()
    sampler_gate.atomic_write_pair(json_path, json_data, tsv_path, tsv_data)


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
            raise PredecommitOpeningPolicyGateError("--write-json and --write-tsv must be paired")
        write_outputs(args.write_json, args.write_tsv, payload)
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PredecommitOpeningPolicyGateError as err:
        print(f"error: {err}", file=sys.stderr)
        raise SystemExit(2) from None
