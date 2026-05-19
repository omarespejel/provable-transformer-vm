#!/usr/bin/env python3.10
"""Gate the bounded Stwo query-policy hook boundary for seq32 attention+MLP."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import os
import pathlib
import sys
from typing import Any


if sys.version_info < (3, 10):
    raise RuntimeError("zkai_bounded_stwo_query_policy_hook_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import zkai_native_seq32_attention_mlp_predecommit_opening_policy_gate as pre_gate
from scripts import zkai_native_seq32_attention_mlp_dry_run_opening_sampler_gate as sampler_gate


EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
JSON_OUT = EVIDENCE_DIR / "zkai-bounded-stwo-query-policy-hook-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-bounded-stwo-query-policy-hook-2026-05.tsv"

SCHEMA = "zkai-bounded-stwo-query-policy-hook-gate-v1"
DECISION = "NARROW_CLAIM_STWO_2_2_COUPLES_QUERY_DRAW_AND_DECOMMITMENT"
RESULT = "NO_GO_REPO_LOCAL_QUERY_POLICY_HOOK_WITHOUT_STWO_PROVER_VERIFIER_API_PATCH"
CLAIM_BOUNDARY = (
    "CURRENT_STWO_2_2_PROVER_DRAWS_QUERIES_INSIDE_FRI_DECOMMIT;"
    "CURRENT_STWO_2_2_VERIFIER_SAMPLES_QUERIES_FROM_TRANSCRIPT;"
    "REPO_WRAPPER_ONLY_SEES_QUERY_LOCATIONS_AFTER_PROVE_EX_EXTENDED_AUX;"
    "NO_EXTERNAL_QUERY_POLICY_WITHOUT_MATCHED_PROVER_VERIFIER_TRANSCRIPT_PATCH;"
    "NO_PROOF_SIZE_CHANGE_NO_NANOZK_COMPARISON"
)
ISSUE_HINT = "https://github.com/omarespejel/provable-transformer-vm/issues/701"
PAYLOAD_DOMAIN = "ptvm:zkai:bounded-stwo-query-policy-hook:v1"

STWO_VERSION = "2.2.0"
MAX_STWO_SOURCE_BYTES = 768 * 1024
MAX_REPO_SOURCE_BYTES = 768 * 1024
MAX_EVIDENCE_BYTES = 2 * 1024 * 1024

RUST_SOURCE_PATH = ROOT / "src" / "stwo_backend" / "native_seq32_attention_mlp_single_proof.rs"
CLI_SOURCE_PATH = ROOT / "src" / "bin" / "zkai_native_seq32_attention_mlp_single_proof.rs"
PREDECOMMIT_EVIDENCE_PATH = pre_gate.JSON_OUT
PREDECOMMIT_TSV_PATH = pre_gate.TSV_OUT

EXPECTED_RUST_SOURCE_SHA256 = pre_gate.EXPECTED_RUST_SOURCE_SHA256
EXPECTED_CLI_SOURCE_SHA256 = pre_gate.EXPECTED_CLI_SOURCE_SHA256
EXPECTED_PREDECOMMIT_EVIDENCE_SHA256 = (
    "07d711adf35a960f64c2cb644ba0e912b0d167698f2c4597d1294075eaa36084"
)
EXPECTED_PREDECOMMIT_TSV_SHA256 = (
    "9d27db58076a846b5cdfa15b5f8e74cdcd703cf41292c03f33f867a75e531a81"
)

EXPECTED_STWO_SOURCE_SHA256 = {
    "prover_mod": "1a26ddc000bbda77ad8a36bf5f152a4f79947f784c9f31236164cc644d8f7bd5",
    "prover_pcs_mod": "214158108b0381079e9cd96c7020eaf7e36fbb0ca3cdfefdcaa5b03ba5d9ce99",
    "prover_fri": "475d667b19f5914cd11e65fc9f7230151029ae73d86e7241b7e9abc031023171",
    "core_pcs_verifier": "797c32b03c3c4348c9b995bdccc30a9600cce085bafbce3bb9e7e49067dbabf6",
    "core_fri": "27af206dae322e9c60d6a44f6de3b01422d9c0a90089bf9009636c8e16dd95ce",
}
STWO_FILES = {
    "prover_mod": "src/prover/mod.rs",
    "prover_pcs_mod": "src/prover/pcs/mod.rs",
    "prover_fri": "src/prover/fri.rs",
    "core_pcs_verifier": "src/core/pcs/verifier.rs",
    "core_fri": "src/core/fri.rs",
}

REPO_SOURCE_MARKERS = {
    "sampler_calls_full_extended_proof": "let extended = prove_single_extended(input)?;",
    "sampler_reads_extended_aux_query_locations": "extended.aux.unsorted_query_locations",
    "prove_single_extended_delegates_to_stwo_prove_ex": (
        "prove_ex::<SimdBackend, Blake2sM31MerkleChannel>"
    ),
    "sampler_boundary_names_extended_aux_only": (
        "PROVER_INTERNAL_EXTENDED_AUX_QUERY_LOCATIONS_ONLY"
    ),
}
STWO_SOURCE_MARKERS = {
    "prove_ex_calls_commitment_scheme_prove_values": (
        "let commitment_scheme_proof = commitment_scheme.prove_values(sample_points, channel);"
    ),
    "pcs_commits_fri_before_pow": (
        "FriProver::<B, MC>::commit(channel, self.config.fri_config, &quotients, self.twiddles)"
    ),
    "pcs_decommit_calls_fri_prover_decommit_channel": "fri_prover.decommit(channel)",
    "pcs_trace_decommit_uses_query_positions": "tree.decommit(query_positions)",
    "fri_decommit_draws_queries_from_channel": (
        "draw_queries(channel, first_layer_log_size, self.config.n_queries)"
    ),
    "fri_decommit_uses_decommit_on_queries": "let fri_proof = self.decommit_on_queries(&queries);",
    "fri_decommit_on_queries_is_public": "pub fn decommit_on_queries(self, queries: &Queries)",
    "verifier_samples_query_positions_from_channel": (
        "let query_positions = fri_verifier.sample_query_positions(channel);"
    ),
    "fri_verifier_draws_queries_from_channel": (
        "draw_queries(channel, first_layer_log_size, self.config.n_queries)"
    ),
}
ABSENT_EXTERNAL_POLICY_MARKERS = (
    "prove_ex_with_query_policy",
    "decommit_with_query_policy",
    "external_query_policy",
    "query_policy_commitment",
)

CURRENT_CHAMPION_TYPED_BYTES = 37_532
CURRENT_CHAMPION_PATH_OPENING_BYTES = 16_560
MATCHED_TWO_PROOF_FRONTIER_TYPED_BYTES = 47_188
SAVING_VS_TWO_PROOF_FRONTIER = 9_656
SAVING_SHARE_VS_TWO_PROOF_FRONTIER = "20.4637%"
QUERY_SPAN = 16_618
MIN_PAIRWISE_QUERY_GAP = 5_969
EXPECTED_UNITTEST_STEP_COUNT = 14

TSV_COLUMNS = (
    "hook_id",
    "status",
    "requires_stwo_prover_patch",
    "requires_stwo_verifier_patch",
    "allows_external_query_choice",
    "preserves_fiat_shamir_if_transcript_bound",
    "can_claim_current_probe_b_control",
    "proof_size_delta_typed_bytes",
)
VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_bounded_stwo_query_policy_hook_gate.py --write-json docs/engineering/evidence/zkai-bounded-stwo-query-policy-hook-2026-05.json --write-tsv docs/engineering/evidence/zkai-bounded-stwo-query-policy-hook-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_bounded_stwo_query_policy_hook_gate.py scripts/tests/test_zkai_bounded_stwo_query_policy_hook_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_bounded_stwo_query_policy_hook_gate",
    "git diff --check",
    "just gate-fast",
    "just gate",
)
NON_CLAIMS = (
    "not a new proof-size frontier",
    "not a proof regeneration under a true pre-decommitment query policy",
    "not an external query override in current Stwo",
    "not a production label-selection policy",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not a full transformer block proof",
    "not exact real-valued Softmax",
    "not timing evidence",
    "not production-ready zkML",
)
MUTATION_NAMES = (
    "decision_overclaim",
    "result_overclaim",
    "claim_boundary_overclaim",
    "stwo_source_digest_drift",
    "repo_source_digest_drift",
    "predecommit_evidence_digest_drift",
    "source_marker_erasure",
    "verifier_marker_erasure",
    "external_policy_absence_flip",
    "hook_claims_current_control",
    "query_policy_reads_final_bytes",
    "query_policy_commitment_unbound",
    "champion_metric_drift",
    "proof_size_delta_claim_drift",
    "validation_command_removed",
    "non_claim_removed",
    "payload_commitment_drift",
)


class BoundedStwoQueryPolicyHookGateError(Exception):
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
        raise BoundedStwoQueryPolicyHookGateError(f"non-canonical JSON value: {err}") from err


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


def read_repo_file(path: pathlib.Path, label: str, max_bytes: int) -> bytes:
    try:
        return sampler_gate.read_bounded_repo_file(path, label, max_bytes)
    except sampler_gate.DryRunOpeningSamplerGateError as err:
        raise BoundedStwoQueryPolicyHookGateError(str(err)) from err


def read_text_bytes(raw: bytes, label: str) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as err:
        raise BoundedStwoQueryPolicyHookGateError(f"{label} is not UTF-8") from err


def find_stwo_source_root() -> pathlib.Path:
    cargo_home = pathlib.Path(os.environ.get("CARGO_HOME", pathlib.Path.home() / ".cargo"))
    registry_src = cargo_home / "registry" / "src"
    candidates = sorted(registry_src.glob(f"*/stwo-{STWO_VERSION}"))
    for candidate in candidates:
        if all((candidate / rel).is_file() for rel in STWO_FILES.values()):
            return candidate
    raise BoundedStwoQueryPolicyHookGateError(
        f"Stwo {STWO_VERSION} source is not available under {registry_src}; run cargo fetch"
    )


def read_external_file(path: pathlib.Path, label: str, max_bytes: int) -> bytes:
    resolved = path.resolve()
    if resolved.is_symlink():
        raise BoundedStwoQueryPolicyHookGateError(f"{label} must not be a symlink")
    if not resolved.is_file():
        raise BoundedStwoQueryPolicyHookGateError(f"{label} missing: {resolved}")
    size = resolved.stat().st_size
    if size > max_bytes:
        raise BoundedStwoQueryPolicyHookGateError(f"{label} exceeds max size: {size}")
    return resolved.read_bytes()


def repo_artifact(path: pathlib.Path, artifact_id: str, expected_sha256: str) -> dict[str, Any]:
    raw = read_repo_file(path, artifact_id, MAX_REPO_SOURCE_BYTES)
    digest = sha256_bytes(raw)
    if digest != expected_sha256:
        raise BoundedStwoQueryPolicyHookGateError(f"{artifact_id} digest drift")
    return {
        "id": artifact_id,
        "path": str(path.relative_to(ROOT)),
        "sha256": digest,
        "size_bytes": len(raw),
    }


def evidence_artifact(path: pathlib.Path, artifact_id: str, expected_sha256: str) -> dict[str, Any]:
    raw = read_repo_file(path, artifact_id, MAX_EVIDENCE_BYTES)
    digest = sha256_bytes(raw)
    if digest != expected_sha256:
        raise BoundedStwoQueryPolicyHookGateError(f"{artifact_id} digest drift")
    return {
        "id": artifact_id,
        "path": str(path.relative_to(ROOT)),
        "sha256": digest,
        "size_bytes": len(raw),
    }


def stwo_artifact(
    stwo_root: pathlib.Path,
    key: str,
    relative_path: str,
    expected_sha256: str,
) -> dict[str, Any]:
    full_path = stwo_root / relative_path
    raw = read_external_file(full_path, f"stwo {key}", MAX_STWO_SOURCE_BYTES)
    digest = sha256_bytes(raw)
    if digest != expected_sha256:
        raise BoundedStwoQueryPolicyHookGateError(f"stwo {key} digest drift")
    return {
        "id": f"stwo_2_2_{key}",
        "crate": "stwo",
        "version": STWO_VERSION,
        "path": f"stwo-{STWO_VERSION}/{relative_path}",
        "sha256": digest,
        "size_bytes": len(raw),
    }


def source_artifacts(stwo_root: pathlib.Path) -> list[dict[str, Any]]:
    artifacts = [
        repo_artifact(
            RUST_SOURCE_PATH,
            "rust_native_seq32_attention_mlp_source",
            EXPECTED_RUST_SOURCE_SHA256,
        ),
        repo_artifact(
            CLI_SOURCE_PATH,
            "cli_native_seq32_attention_mlp_source",
            EXPECTED_CLI_SOURCE_SHA256,
        ),
        evidence_artifact(
            PREDECOMMIT_EVIDENCE_PATH,
            "predecommit_opening_policy_evidence",
            EXPECTED_PREDECOMMIT_EVIDENCE_SHA256,
        ),
        evidence_artifact(
            PREDECOMMIT_TSV_PATH,
            "predecommit_opening_policy_tsv",
            EXPECTED_PREDECOMMIT_TSV_SHA256,
        ),
    ]
    for key, relative_path in STWO_FILES.items():
        artifacts.append(
            stwo_artifact(stwo_root, key, relative_path, EXPECTED_STWO_SOURCE_SHA256[key])
        )
    return artifacts


def source_texts(stwo_root: pathlib.Path) -> dict[str, str]:
    texts = {
        "repo_rust": read_text_bytes(
            read_repo_file(RUST_SOURCE_PATH, "rust source", MAX_REPO_SOURCE_BYTES),
            "rust source",
        ),
        "repo_cli": read_text_bytes(
            read_repo_file(CLI_SOURCE_PATH, "cli source", MAX_REPO_SOURCE_BYTES),
            "cli source",
        ),
    }
    for key, relative_path in STWO_FILES.items():
        texts[f"stwo_{key}"] = read_text_bytes(
            read_external_file(stwo_root / relative_path, f"stwo {key}", MAX_STWO_SOURCE_BYTES),
            f"stwo {key}",
        )
    return texts


def audit_source_markers(stwo_root: pathlib.Path) -> dict[str, Any]:
    texts = source_texts(stwo_root)
    repo_markers = {
        name: marker in texts["repo_rust"] or marker in texts["repo_cli"]
        for name, marker in REPO_SOURCE_MARKERS.items()
    }
    stwo_markers = {
        "prove_ex_calls_commitment_scheme_prove_values": (
            STWO_SOURCE_MARKERS["prove_ex_calls_commitment_scheme_prove_values"]
            in texts["stwo_prover_mod"]
        ),
        "pcs_commits_fri_before_pow": (
            STWO_SOURCE_MARKERS["pcs_commits_fri_before_pow"] in texts["stwo_prover_pcs_mod"]
        ),
        "pcs_decommit_calls_fri_prover_decommit_channel": (
            STWO_SOURCE_MARKERS["pcs_decommit_calls_fri_prover_decommit_channel"]
            in texts["stwo_prover_pcs_mod"]
        ),
        "pcs_trace_decommit_uses_query_positions": (
            STWO_SOURCE_MARKERS["pcs_trace_decommit_uses_query_positions"]
            in texts["stwo_prover_pcs_mod"]
        ),
        "fri_decommit_draws_queries_from_channel": (
            STWO_SOURCE_MARKERS["fri_decommit_draws_queries_from_channel"]
            in texts["stwo_prover_fri"]
        ),
        "fri_decommit_uses_decommit_on_queries": (
            STWO_SOURCE_MARKERS["fri_decommit_uses_decommit_on_queries"]
            in texts["stwo_prover_fri"]
        ),
        "fri_decommit_on_queries_is_public": (
            STWO_SOURCE_MARKERS["fri_decommit_on_queries_is_public"] in texts["stwo_prover_fri"]
        ),
        "verifier_samples_query_positions_from_channel": (
            STWO_SOURCE_MARKERS["verifier_samples_query_positions_from_channel"]
            in texts["stwo_core_pcs_verifier"]
        ),
        "fri_verifier_draws_queries_from_channel": (
            STWO_SOURCE_MARKERS["fri_verifier_draws_queries_from_channel"]
            in texts["stwo_core_fri"]
        ),
    }
    all_source = "\n".join(texts.values())
    absent_policy_markers = {
        marker: marker not in all_source for marker in ABSENT_EXTERNAL_POLICY_MARKERS
    }
    missing = [name for name, present in {**repo_markers, **stwo_markers}.items() if not present]
    if missing:
        raise BoundedStwoQueryPolicyHookGateError(f"source marker drift: {missing}")
    unexpected = [name for name, absent in absent_policy_markers.items() if not absent]
    if unexpected:
        raise BoundedStwoQueryPolicyHookGateError(
            f"external query-policy marker appeared unexpectedly: {unexpected}"
        )
    return {
        "stwo_version": STWO_VERSION,
        "repo_markers": repo_markers,
        "stwo_markers": stwo_markers,
        "external_policy_markers_absent": absent_policy_markers,
        "current_stage_boundary": (
            "repo wrapper observes query locations only after Stwo prove_ex returns "
            "ExtendedStarkProof aux"
        ),
        "current_stwo_query_boundary": (
            "Stwo prover draws FRI queries inside FriProver::decommit(channel), then uses those "
            "positions for FRI and trace Merkle decommitments; verifier redraws positions from "
            "the transcript channel"
        ),
    }


def hook_designs() -> list[dict[str, Any]]:
    return [
        {
            "hook_id": "query_preview_split",
            "status": "SOUND_API_CANDIDATE_NOT_PRESENT_IN_CURRENT_STWO_2_2",
            "requires_stwo_prover_patch": True,
            "requires_stwo_verifier_patch": False,
            "allows_external_query_choice": False,
            "preserves_fiat_shamir_if_transcript_bound": True,
            "can_claim_current_probe_b_control": False,
            "proof_size_delta_typed_bytes": 0,
            "description": (
                "Split canonical query drawing from decommitment so the prover can observe "
                "Fiat-Shamir queries before Merkle/FRI decommitment while still using the same "
                "drawn queries."
            ),
        },
        {
            "hook_id": "policy_commitment_mix",
            "status": "SOUND_API_CANDIDATE_REQUIRES_MATCHED_PROVER_VERIFIER_TRANSCRIPT_PATCH",
            "requires_stwo_prover_patch": True,
            "requires_stwo_verifier_patch": True,
            "allows_external_query_choice": False,
            "preserves_fiat_shamir_if_transcript_bound": True,
            "can_claim_current_probe_b_control": False,
            "proof_size_delta_typed_bytes": 0,
            "description": (
                "Mix a policy commitment into the prover and verifier transcript before canonical "
                "query sampling; the policy cannot read final proof bytes or decommitment sizes."
            ),
        },
        {
            "hook_id": "external_query_override",
            "status": "REJECTED_UNSOUND_WITHOUT_VERIFIER_AND_TRANSCRIPT_BINDING",
            "requires_stwo_prover_patch": True,
            "requires_stwo_verifier_patch": True,
            "allows_external_query_choice": True,
            "preserves_fiat_shamir_if_transcript_bound": False,
            "can_claim_current_probe_b_control": False,
            "proof_size_delta_typed_bytes": 0,
            "description": (
                "Directly overriding FRI query locations is rejected unless the verifier derives "
                "the same positions from a bound transcript policy."
            ),
        },
    ]


def build_payload_without_mutations() -> dict[str, Any]:
    stwo_root = find_stwo_source_root()
    audit = audit_source_markers(stwo_root)
    return {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE_HINT,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_metric_anchor": {
            "selected_row": "adjacent_label_probe_b",
            "typed_bytes": CURRENT_CHAMPION_TYPED_BYTES,
            "path_opening_bytes": CURRENT_CHAMPION_PATH_OPENING_BYTES,
            "query_span": QUERY_SPAN,
            "min_pairwise_query_gap": MIN_PAIRWISE_QUERY_GAP,
            "matched_two_proof_frontier_typed_bytes": MATCHED_TWO_PROOF_FRONTIER_TYPED_BYTES,
            "saving_vs_two_proof_frontier_typed_bytes": SAVING_VS_TWO_PROOF_FRONTIER,
            "saving_vs_two_proof_frontier_share": SAVING_SHARE_VS_TWO_PROOF_FRONTIER,
        },
        "source_audit": audit,
        "bounded_hook_assessment": {
            "repo_local_hook_available": False,
            "true_predecommit_query_policy_available": False,
            "needs_matched_prover_verifier_patch": True,
            "can_regenerate_smaller_proof_in_this_pr": False,
            "proof_size_changed_by_this_gate": False,
            "proof_size_delta_typed_bytes": 0,
            "go_gate_satisfied": False,
            "no_go_reason": (
                "current Stwo API couples query drawing with decommitment and the verifier "
                "samples query positions from the same transcript; a repo-local wrapper cannot "
                "inject a sound external policy"
            ),
        },
        "forbidden_policy_inputs": {
            "final_envelope_json": True,
            "final_proof_bytes": True,
            "grouped_accounting": True,
            "record_streams": True,
            "final_path_opening_bytes": True,
            "post_decommitment_aux_as_selector": True,
        },
        "hook_designs": hook_designs(),
        "interpretation": {
            "human_read": (
                "The opening-geometry signal is real, but the mechanism is currently exposed "
                "too late. Stwo draws the FRI queries inside decommitment, and the verifier "
                "redraws them from the transcript. So the next serious step is a small Stwo API "
                "hook, not more wrapper-side label guessing."
            ),
            "why_it_matters": (
                "This keeps the paper path honest: the proof-size win remains 37,532 typed "
                "bytes for the selected row, but true pre-decommitment control needs a "
                "transcript-bound prover/verifier interface."
            ),
            "next_experiment": (
                "Prototype a query-preview split or policy-commitment mix in a bounded Stwo fork, "
                "then regenerate the seq32+d128 boundary and rerun proof verification, source "
                "binding, statement binding, and mutation gates."
            ),
        },
        "source_artifacts": source_artifacts(stwo_root),
        "validation_commands": list(VALIDATION_COMMANDS),
        "non_claims": list(NON_CLAIMS),
        "reproducibility_metadata": {
            "stwo_version": STWO_VERSION,
            "cargo_dependency": "stwo = 2.2.0",
            "mutation_step_count": len(MUTATION_NAMES),
            "unittest_step_count": EXPECTED_UNITTEST_STEP_COUNT,
            "local_release_gate_step_count": 14,
        },
    }


def validate_base_payload(payload: dict[str, Any]) -> None:
    expected = build_payload_without_mutations()
    if payload != expected:
        raise BoundedStwoQueryPolicyHookGateError("base payload drift")
    assessment = payload["bounded_hook_assessment"]
    if assessment["repo_local_hook_available"]:
        raise BoundedStwoQueryPolicyHookGateError("repo-local hook overclaim")
    if assessment["true_predecommit_query_policy_available"]:
        raise BoundedStwoQueryPolicyHookGateError("true predecommit policy overclaim")
    if not assessment["needs_matched_prover_verifier_patch"]:
        raise BoundedStwoQueryPolicyHookGateError("missing prover/verifier patch requirement")
    if assessment["proof_size_delta_typed_bytes"] != 0:
        raise BoundedStwoQueryPolicyHookGateError("proof-size delta claim drift")
    metric = payload["current_metric_anchor"]
    if metric["typed_bytes"] != CURRENT_CHAMPION_TYPED_BYTES:
        raise BoundedStwoQueryPolicyHookGateError("champion typed-byte drift")
    if metric["path_opening_bytes"] != CURRENT_CHAMPION_PATH_OPENING_BYTES:
        raise BoundedStwoQueryPolicyHookGateError("champion path-opening drift")
    if payload["reproducibility_metadata"]["mutation_step_count"] != len(MUTATION_NAMES):
        raise BoundedStwoQueryPolicyHookGateError("mutation count drift")


def validate_payload(payload: dict[str, Any]) -> None:
    item = copy.deepcopy(payload)
    supplied_commitment = item.pop("payload_commitment", None)
    mutation_result = item.pop("mutation_result", None)
    validate_base_payload(item)
    if supplied_commitment != payload_commitment(payload):
        raise BoundedStwoQueryPolicyHookGateError("payload commitment drift")
    expected_mutation = run_mutations(item)
    if mutation_result != expected_mutation:
        raise BoundedStwoQueryPolicyHookGateError("mutation result drift")
    validate_mutation_result(mutation_result)


def validate_mutation_result(mutation_result: Any) -> None:
    if not isinstance(mutation_result, dict):
        raise BoundedStwoQueryPolicyHookGateError("mutation result missing")
    if mutation_result.get("mutation_names") != list(MUTATION_NAMES):
        raise BoundedStwoQueryPolicyHookGateError("mutation names drift")
    cases = mutation_result.get("cases")
    if not isinstance(cases, list) or len(cases) != len(MUTATION_NAMES):
        raise BoundedStwoQueryPolicyHookGateError("mutation case count drift")
    for case in cases:
        if not isinstance(case, dict):
            raise BoundedStwoQueryPolicyHookGateError("mutation case schema drift")
        if (
            not isinstance(case.get("name"), str)
            or not isinstance(case.get("rejected"), bool)
            or not isinstance(case.get("error"), str)
        ):
            raise BoundedStwoQueryPolicyHookGateError("mutation case schema drift")
    rejected_names = [case.get("name") for case in cases if case.get("rejected") is True]
    if rejected_names != list(MUTATION_NAMES):
        raise BoundedStwoQueryPolicyHookGateError("mutation rejection drift")
    if mutation_result.get("mutations_rejected") != len(MUTATION_NAMES):
        raise BoundedStwoQueryPolicyHookGateError("mutation rejected count drift")
    if mutation_result.get("all_mutations_rejected") is not True:
        raise BoundedStwoQueryPolicyHookGateError("mutation all-rejected drift")


def mutate_payload(name: str, item: dict[str, Any]) -> None:
    if name == "decision_overclaim":
        item["decision"] = "GO_TRUE_STWO_QUERY_POLICY_HOOK"
    elif name == "result_overclaim":
        item["result"] = "QUERY_POLICY_BEATS_NANOZK"
    elif name == "claim_boundary_overclaim":
        item["claim_boundary"] = item["claim_boundary"].replace(
            "NO_EXTERNAL_QUERY_POLICY_WITHOUT_MATCHED_PROVER_VERIFIER_TRANSCRIPT_PATCH;",
            "",
        )
    elif name == "stwo_source_digest_drift":
        item["source_artifacts"][4]["sha256"] = "0" * 64
    elif name == "repo_source_digest_drift":
        item["source_artifacts"][0]["sha256"] = "1" * 64
    elif name == "predecommit_evidence_digest_drift":
        item["source_artifacts"][2]["sha256"] = "2" * 64
    elif name == "source_marker_erasure":
        item["source_audit"]["stwo_markers"]["fri_decommit_draws_queries_from_channel"] = False
    elif name == "verifier_marker_erasure":
        item["source_audit"]["stwo_markers"]["verifier_samples_query_positions_from_channel"] = (
            False
        )
    elif name == "external_policy_absence_flip":
        item["source_audit"]["external_policy_markers_absent"]["query_policy_commitment"] = False
    elif name == "hook_claims_current_control":
        item["bounded_hook_assessment"]["true_predecommit_query_policy_available"] = True
    elif name == "query_policy_reads_final_bytes":
        item["forbidden_policy_inputs"]["final_proof_bytes"] = False
    elif name == "query_policy_commitment_unbound":
        item["bounded_hook_assessment"]["needs_matched_prover_verifier_patch"] = False
    elif name == "champion_metric_drift":
        item["current_metric_anchor"]["typed_bytes"] = 36_000
    elif name == "proof_size_delta_claim_drift":
        item["bounded_hook_assessment"]["proof_size_delta_typed_bytes"] = -512
    elif name == "validation_command_removed":
        item["validation_commands"].pop()
    elif name == "non_claim_removed":
        item["non_claims"].remove("not a new proof-size frontier")
    elif name == "payload_commitment_drift":
        item["payload_commitment"] = "blake2b-256:" + ("0" * 64)
    else:
        raise BoundedStwoQueryPolicyHookGateError(f"unknown mutation: {name}")


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
        except BoundedStwoQueryPolicyHookGateError as err:
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
    for design in payload["hook_designs"]:
        writer.writerow(
            {
                "hook_id": design["hook_id"],
                "status": design["status"],
                "requires_stwo_prover_patch": str(
                    design["requires_stwo_prover_patch"]
                ).lower(),
                "requires_stwo_verifier_patch": str(
                    design["requires_stwo_verifier_patch"]
                ).lower(),
                "allows_external_query_choice": str(
                    design["allows_external_query_choice"]
                ).lower(),
                "preserves_fiat_shamir_if_transcript_bound": str(
                    design["preserves_fiat_shamir_if_transcript_bound"]
                ).lower(),
                "can_claim_current_probe_b_control": str(
                    design["can_claim_current_probe_b_control"]
                ).lower(),
                "proof_size_delta_typed_bytes": design["proof_size_delta_typed_bytes"],
            }
        )
    return output.getvalue()


def write_outputs(json_path: pathlib.Path, tsv_path: pathlib.Path, payload: dict[str, Any]) -> None:
    validate_payload(payload)
    json_data = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True).encode() + b"\n"
    tsv_data = render_tsv(payload).encode()
    try:
        sampler_gate.atomic_write_pair(json_path, json_data, tsv_path, tsv_data)
    except sampler_gate.DryRunOpeningSamplerGateError as err:
        raise BoundedStwoQueryPolicyHookGateError(str(err)) from err


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
            raise BoundedStwoQueryPolicyHookGateError("--write-json and --write-tsv must be paired")
        write_outputs(args.write_json, args.write_tsv, payload)
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BoundedStwoQueryPolicyHookGateError as err:
        print(f"error: {err}", file=sys.stderr)
        raise SystemExit(2) from None
