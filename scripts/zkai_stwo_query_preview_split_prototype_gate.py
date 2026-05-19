#!/usr/bin/env python3.10
"""Gate the Stwo query-preview split prototype boundary for seq32 attention+MLP."""

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
    raise RuntimeError("zkai_stwo_query_preview_split_prototype_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import zkai_bounded_stwo_query_policy_hook_gate as hook_gate
from scripts import zkai_native_seq32_attention_mlp_dry_run_opening_sampler_gate as sampler_gate


EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
JSON_OUT = EVIDENCE_DIR / "zkai-stwo-query-preview-split-prototype-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-stwo-query-preview-split-prototype-2026-05.tsv"

SCHEMA = "zkai-stwo-query-preview-split-prototype-gate-v1"
DECISION = "NARROW_CLAIM_QUERY_PREVIEW_SPLIT_IS_API_FEASIBLE_NOT_SOUND_LABEL_POLICY"
RESULT = "NO_GO_SOUND_QUERY_GEOMETRY_CONTROL_WITHOUT_GRINDING_OR_POLICY_COMMITMENT"
ISSUE_HINT = "https://github.com/omarespejel/provable-transformer-vm/issues/704"
PAYLOAD_DOMAIN = "ptvm:zkai:stwo-query-preview-split-prototype:v1"

STWO_VERSION = hook_gate.STWO_VERSION
MAX_STWO_SOURCE_BYTES = hook_gate.MAX_STWO_SOURCE_BYTES
CORE_QUERIES_RELATIVE_PATH = "src/core/queries.rs"
EXPECTED_CORE_QUERIES_SHA256 = (
    "fd978cad026f3b684844503c543dfe3cb4fbf003108f92ecf945807c5d92e633"
)

QUERY_SOURCE_MARKERS = {
    "draw_queries_is_public": "pub fn draw_queries(",
    "draw_queries_reads_transcript_words": "let random_words = channel.draw_u32s();",
    "draw_queries_masks_domain": "let query_mask = (1 << log_domain_size) - 1;",
    "queries_new_sorts_and_dedups": "BTreeSet::from_iter(raw_positions.iter())",
}

EXPECTED_UNITTEST_STEP_COUNT = 18
TSV_COLUMNS = (
    "route_id",
    "status",
    "requires_prover_patch",
    "requires_verifier_patch",
    "external_query_choice",
    "preview_before_fri_decommit",
    "preview_before_trace_decommit",
    "can_change_committed_trace_after_preview",
    "can_claim_probe_b_control",
    "requires_security_budget",
)
VALIDATION_COMMANDS = (
    "python3.10 scripts/zkai_stwo_query_preview_split_prototype_gate.py --write-json docs/engineering/evidence/zkai-stwo-query-preview-split-prototype-2026-05.json --write-tsv docs/engineering/evidence/zkai-stwo-query-preview-split-prototype-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_stwo_query_preview_split_prototype_gate.py scripts/tests/test_zkai_stwo_query_preview_split_prototype_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_stwo_query_preview_split_prototype_gate",
    "git diff --check",
    "just gate-fast",
    "just gate",
)
NON_CLAIMS = (
    "not a new proof-size frontier",
    "not a regenerated seq32+d128 proof under a new Stwo API",
    "not a production label-selection policy",
    "not a sound post-query label chooser",
    "not an external query override",
    "not a NANOZK proof-size comparison",
    "not a full transformer block proof",
    "not timing evidence",
    "not production-ready zkML",
)
MUTATION_NAMES = (
    "decision_overclaim",
    "result_overclaim",
    "preview_claims_label_control",
    "external_query_override_allowed",
    "stage_order_flip",
    "committed_trace_mutable_after_preview",
    "proof_size_frontier_claimed",
    "metric_anchor_drift",
    "core_query_source_digest_drift",
    "core_query_marker_erasure",
    "verifier_marker_erasure",
    "policy_reads_final_bytes",
    "transcript_grinding_without_budget",
    "policy_commitment_verifier_patch_removed",
    "validation_command_removed",
    "non_claim_removed",
    "source_artifact_digest_drift",
    "payload_commitment_drift",
)


class StwoQueryPreviewSplitPrototypeGateError(Exception):
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
        raise StwoQueryPreviewSplitPrototypeGateError(
            f"non-canonical JSON value: {err}"
        ) from err


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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_text_bytes(raw: bytes, label: str) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as err:
        raise StwoQueryPreviewSplitPrototypeGateError(f"{label} is not UTF-8") from err


def stwo_core_queries_artifact(stwo_root: pathlib.Path) -> dict[str, Any]:
    raw = hook_gate.read_external_file(
        stwo_root / CORE_QUERIES_RELATIVE_PATH,
        "stwo core queries source",
        MAX_STWO_SOURCE_BYTES,
    )
    digest = sha256_bytes(raw)
    if digest != EXPECTED_CORE_QUERIES_SHA256:
        raise StwoQueryPreviewSplitPrototypeGateError("stwo core queries digest drift")
    return {
        "id": "stwo_2_2_core_queries",
        "crate": "stwo",
        "version": STWO_VERSION,
        "path": f"stwo-{STWO_VERSION}/{CORE_QUERIES_RELATIVE_PATH}",
        "sha256": digest,
        "size_bytes": len(raw),
    }


def source_artifacts(stwo_root: pathlib.Path) -> list[dict[str, Any]]:
    artifacts = hook_gate.source_artifacts(stwo_root)
    artifacts.append(stwo_core_queries_artifact(stwo_root))
    return artifacts


def core_query_markers(stwo_root: pathlib.Path) -> dict[str, bool]:
    raw = hook_gate.read_external_file(
        stwo_root / CORE_QUERIES_RELATIVE_PATH,
        "stwo core queries source",
        MAX_STWO_SOURCE_BYTES,
    )
    text = read_text_bytes(raw, "stwo core queries source")
    markers = {name: marker in text for name, marker in QUERY_SOURCE_MARKERS.items()}
    missing = [name for name, present in markers.items() if not present]
    if missing:
        raise StwoQueryPreviewSplitPrototypeGateError(
            f"core query source marker drift: {missing}"
        )
    return markers


def source_audit(stwo_root: pathlib.Path) -> dict[str, Any]:
    audit = hook_gate.audit_source_markers(stwo_root)
    audit["core_query_markers"] = core_query_markers(stwo_root)
    audit["preview_split_source_read"] = (
        "FriProver::decommit already factors canonical query drawing from "
        "decommit_on_queries; a prover-side API can expose the drawn Queries before "
        "calling decommit_on_queries, while the verifier keeps sampling the same "
        "positions from the Fiat-Shamir transcript."
    )
    return audit


def stage_order() -> list[dict[str, Any]]:
    return [
        {
            "stage_id": "trace_commitments",
            "relative_to_query_preview": "before",
            "transcript_bound": True,
            "can_change_after_preview": False,
            "source_fact": "commitment_scheme trees are already committed before FRI queries are drawn",
        },
        {
            "stage_id": "fri_commitment_and_pow_mix",
            "relative_to_query_preview": "before",
            "transcript_bound": True,
            "can_change_after_preview": False,
            "source_fact": "FRI commit and proof_of_work are mixed before FriProver::decommit draws queries",
        },
        {
            "stage_id": "canonical_query_draw",
            "relative_to_query_preview": "preview_point",
            "transcript_bound": True,
            "can_change_after_preview": False,
            "source_fact": "draw_queries(channel, first_layer_log_size, n_queries) is transcript-derived",
        },
        {
            "stage_id": "fri_decommit_on_queries",
            "relative_to_query_preview": "after",
            "transcript_bound": True,
            "can_change_after_preview": False,
            "source_fact": "decommit_on_queries consumes the same canonical Queries",
        },
        {
            "stage_id": "trace_tree_decommit",
            "relative_to_query_preview": "after",
            "transcript_bound": True,
            "can_change_after_preview": False,
            "source_fact": "tree.decommit(query_positions) uses verifier-replayed query positions",
        },
    ]


def prototype_routes() -> list[dict[str, Any]]:
    return [
        {
            "route_id": "preview_only_split",
            "status": "FEASIBLE_API_PATCH",
            "requires_prover_patch": True,
            "requires_verifier_patch": False,
            "external_query_choice": False,
            "preview_before_fri_decommit": True,
            "preview_before_trace_decommit": True,
            "can_change_committed_trace_after_preview": False,
            "can_claim_probe_b_control": False,
            "requires_security_budget": False,
            "interpretation": (
                "Expose transcript-drawn queries after PoW mix and before FRI/tree "
                "decommitments. This can support measurement or bounded early abort, but "
                "does not justify choosing labels after seeing the queries."
            ),
        },
        {
            "route_id": "policy_commitment_mix",
            "status": "FOLLOWUP_MATCHED_TRANSCRIPT_PATCH",
            "requires_prover_patch": True,
            "requires_verifier_patch": True,
            "external_query_choice": False,
            "preview_before_fri_decommit": True,
            "preview_before_trace_decommit": True,
            "can_change_committed_trace_after_preview": False,
            "can_claim_probe_b_control": False,
            "requires_security_budget": False,
            "interpretation": (
                "Bind a deterministic policy commitment into prover and verifier transcript "
                "before canonical query draw. It can make policy semantics explicit, but still "
                "cannot read final proof bytes or post-decommitment accounting."
            ),
        },
        {
            "route_id": "external_query_override",
            "status": "REJECTED_UNSOUND",
            "requires_prover_patch": True,
            "requires_verifier_patch": True,
            "external_query_choice": True,
            "preview_before_fri_decommit": True,
            "preview_before_trace_decommit": True,
            "can_change_committed_trace_after_preview": False,
            "can_claim_probe_b_control": False,
            "requires_security_budget": True,
            "interpretation": (
                "Letting the prover choose FRI query locations directly breaks the "
                "Fiat-Shamir verifier story unless the verifier derives the same positions "
                "from a bound policy."
            ),
        },
        {
            "route_id": "transcript_grinding_search",
            "status": "FOLLOWUP_SECURITY_BUDGET_REQUIRED",
            "requires_prover_patch": False,
            "requires_verifier_patch": True,
            "external_query_choice": False,
            "preview_before_fri_decommit": True,
            "preview_before_trace_decommit": True,
            "can_change_committed_trace_after_preview": False,
            "can_claim_probe_b_control": False,
            "requires_security_budget": True,
            "interpretation": (
                "Abort-and-retry after seeing canonical queries is transcript grinding. "
                "It may be a research lever only with explicit soundness-loss accounting, "
                "bounded attempts, and verifier-visible constraints."
            ),
        },
    ]


def build_payload_without_mutations() -> dict[str, Any]:
    stwo_root = hook_gate.find_stwo_source_root()
    metric_anchor = hook_gate.predecommit_metric_anchor()
    return {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE_HINT,
        "current_metric_anchor": metric_anchor,
        "source_audit": source_audit(stwo_root),
        "stage_order": stage_order(),
        "prototype_routes": prototype_routes(),
        "preview_split_assessment": {
            "api_preview_split_feasible": True,
            "sound_label_policy_feasible_now": False,
            "regenerate_proof_size_frontier_now": False,
            "proof_size_delta_typed_bytes": 0,
            "cannot_change_committed_trace_or_layout_after_preview": True,
            "followup_needed": (
                "security-budgeted transcript grinding or a verifier-bound deterministic "
                "policy commitment"
            ),
        },
        "forbidden_policy_inputs": {
            "final_envelope_json": True,
            "final_proof_bytes": True,
            "grouped_accounting": True,
            "record_streams": True,
            "final_path_opening_bytes": True,
            "post_decommitment_aux_as_selector": True,
            "unbounded_abort_and_retry": True,
        },
        "interpretation": {
            "human_read": (
                "The Stwo split is useful, but not in the naive way. We can expose canonical "
                "queries before expensive decommitment, which is a real API seam. We cannot "
                "then change labels or layouts after seeing those queries without turning the "
                "experiment into transcript grinding."
            ),
            "why_it_matters": (
                "This keeps the breakthrough path honest. The current 37,532 typed-byte "
                "champion and 20.4628% saving over the two-proof frontier remain an opening "
                "geometry signal, but the next paper-grade claim needs either a deterministic "
                "precommitted policy or explicit security-budgeted grinding."
            ),
            "next_experiment": (
                "Prototype the preview-only Stwo API first for early measurement, then test a "
                "bounded transcript-grinding or policy-commitment route before regenerating "
                "proof-size frontiers."
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


def route(payload: dict[str, Any], route_id: str) -> dict[str, Any]:
    for item in payload.get("prototype_routes", []):
        if item.get("route_id") == route_id:
            return item
    raise StwoQueryPreviewSplitPrototypeGateError(f"route missing: {route_id}")


def find_source_artifact(item: dict[str, Any], artifact_id: str) -> dict[str, Any]:
    for artifact in item.get("source_artifacts", []):
        if artifact.get("id") == artifact_id:
            return artifact
    raise StwoQueryPreviewSplitPrototypeGateError(f"source artifact missing: {artifact_id}")


def validate_base_payload(payload: dict[str, Any]) -> None:
    expected = build_payload_without_mutations()
    if payload != expected:
        raise StwoQueryPreviewSplitPrototypeGateError("base payload drift")
    if payload["decision"] != DECISION or payload["result"] != RESULT:
        raise StwoQueryPreviewSplitPrototypeGateError("claim boundary drift")
    metric = payload["current_metric_anchor"]
    if metric != hook_gate.predecommit_metric_anchor():
        raise StwoQueryPreviewSplitPrototypeGateError("metric anchor drift")
    assessment = payload["preview_split_assessment"]
    if not assessment["api_preview_split_feasible"]:
        raise StwoQueryPreviewSplitPrototypeGateError("preview split feasibility drift")
    if assessment["sound_label_policy_feasible_now"]:
        raise StwoQueryPreviewSplitPrototypeGateError("sound label policy overclaim")
    if assessment["regenerate_proof_size_frontier_now"]:
        raise StwoQueryPreviewSplitPrototypeGateError("proof-size frontier overclaim")
    if assessment["proof_size_delta_typed_bytes"] != 0:
        raise StwoQueryPreviewSplitPrototypeGateError("proof-size delta drift")
    preview = route(payload, "preview_only_split")
    if not preview["preview_before_fri_decommit"] or not preview["preview_before_trace_decommit"]:
        raise StwoQueryPreviewSplitPrototypeGateError("preview timing drift")
    if preview["can_change_committed_trace_after_preview"]:
        raise StwoQueryPreviewSplitPrototypeGateError("committed trace mutability overclaim")
    if preview["can_claim_probe_b_control"]:
        raise StwoQueryPreviewSplitPrototypeGateError("probe-b control overclaim")
    external = route(payload, "external_query_override")
    if external["status"] != "REJECTED_UNSOUND":
        raise StwoQueryPreviewSplitPrototypeGateError("external query override not rejected")
    grinding = route(payload, "transcript_grinding_search")
    if not grinding["requires_security_budget"]:
        raise StwoQueryPreviewSplitPrototypeGateError("missing grinding security budget")
    policy = route(payload, "policy_commitment_mix")
    if not policy["requires_verifier_patch"]:
        raise StwoQueryPreviewSplitPrototypeGateError("policy verifier patch requirement drift")
    if payload["validation_commands"] != list(VALIDATION_COMMANDS):
        raise StwoQueryPreviewSplitPrototypeGateError("validation command drift")
    if payload["non_claims"] != list(NON_CLAIMS):
        raise StwoQueryPreviewSplitPrototypeGateError("non-claim drift")
    if payload["reproducibility_metadata"]["mutation_step_count"] != len(MUTATION_NAMES):
        raise StwoQueryPreviewSplitPrototypeGateError("mutation count drift")


def validate_payload(payload: dict[str, Any]) -> None:
    item = copy.deepcopy(payload)
    supplied_commitment = item.pop("payload_commitment", None)
    mutation_result = item.pop("mutation_result", None)
    validate_base_payload(item)
    if supplied_commitment != payload_commitment(payload):
        raise StwoQueryPreviewSplitPrototypeGateError("payload commitment drift")
    expected_mutation = run_mutations(item)
    if mutation_result != expected_mutation:
        raise StwoQueryPreviewSplitPrototypeGateError("mutation result drift")
    validate_mutation_result(mutation_result)


def validate_mutation_result(mutation_result: Any) -> None:
    if not isinstance(mutation_result, dict):
        raise StwoQueryPreviewSplitPrototypeGateError("mutation result missing")
    if mutation_result.get("mutation_names") != list(MUTATION_NAMES):
        raise StwoQueryPreviewSplitPrototypeGateError("mutation names drift")
    cases = mutation_result.get("cases")
    if not isinstance(cases, list) or len(cases) != len(MUTATION_NAMES):
        raise StwoQueryPreviewSplitPrototypeGateError("mutation case count drift")
    for case in cases:
        if not isinstance(case, dict):
            raise StwoQueryPreviewSplitPrototypeGateError("mutation case schema drift")
        if (
            not isinstance(case.get("name"), str)
            or not isinstance(case.get("rejected"), bool)
            or not isinstance(case.get("error"), str)
        ):
            raise StwoQueryPreviewSplitPrototypeGateError("mutation case schema drift")
    rejected_names = [case["name"] for case in cases if case["rejected"]]
    if rejected_names != list(MUTATION_NAMES):
        raise StwoQueryPreviewSplitPrototypeGateError("mutation rejection drift")
    if mutation_result.get("mutations_rejected") != len(MUTATION_NAMES):
        raise StwoQueryPreviewSplitPrototypeGateError("mutation rejected count drift")
    if mutation_result.get("all_mutations_rejected") is not True:
        raise StwoQueryPreviewSplitPrototypeGateError("mutation all-rejected drift")


def mutate_payload(name: str, item: dict[str, Any]) -> None:
    if name == "decision_overclaim":
        item["decision"] = "GO_QUERY_GEOMETRY_CONTROL"
    elif name == "result_overclaim":
        item["result"] = "BEATS_NANOZK_WITH_QUERY_PREVIEW"
    elif name == "preview_claims_label_control":
        route(item, "preview_only_split")["can_claim_probe_b_control"] = True
    elif name == "external_query_override_allowed":
        route(item, "external_query_override")["status"] = "FEASIBLE_API_PATCH"
    elif name == "stage_order_flip":
        item["stage_order"][0]["relative_to_query_preview"] = "after"
    elif name == "committed_trace_mutable_after_preview":
        route(item, "preview_only_split")["can_change_committed_trace_after_preview"] = True
    elif name == "proof_size_frontier_claimed":
        item["preview_split_assessment"]["regenerate_proof_size_frontier_now"] = True
    elif name == "metric_anchor_drift":
        item["current_metric_anchor"]["typed_bytes"] = 36_000
    elif name == "core_query_source_digest_drift":
        find_source_artifact(item, "stwo_2_2_core_queries")["sha256"] = "0" * 64
    elif name == "core_query_marker_erasure":
        item["source_audit"]["core_query_markers"]["draw_queries_reads_transcript_words"] = False
    elif name == "verifier_marker_erasure":
        item["source_audit"]["stwo_markers"]["verifier_samples_query_positions_from_channel"] = (
            False
        )
    elif name == "policy_reads_final_bytes":
        item["forbidden_policy_inputs"]["final_proof_bytes"] = False
    elif name == "transcript_grinding_without_budget":
        route(item, "transcript_grinding_search")["requires_security_budget"] = False
    elif name == "policy_commitment_verifier_patch_removed":
        route(item, "policy_commitment_mix")["requires_verifier_patch"] = False
    elif name == "validation_command_removed":
        item["validation_commands"].pop()
    elif name == "non_claim_removed":
        item["non_claims"].remove("not a NANOZK proof-size comparison")
    elif name == "source_artifact_digest_drift":
        find_source_artifact(item, "stwo_2_2_prover_fri")["sha256"] = "1" * 64
    elif name == "payload_commitment_drift":
        item["payload_commitment"] = "blake2b-256:" + ("0" * 64)
    else:
        raise StwoQueryPreviewSplitPrototypeGateError(f"unknown mutation: {name}")


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
        except (StwoQueryPreviewSplitPrototypeGateError, hook_gate.BoundedStwoQueryPolicyHookGateError) as err:
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
    for item in payload["prototype_routes"]:
        writer.writerow(
            {
                "route_id": item["route_id"],
                "status": item["status"],
                "requires_prover_patch": str(item["requires_prover_patch"]).lower(),
                "requires_verifier_patch": str(item["requires_verifier_patch"]).lower(),
                "external_query_choice": str(item["external_query_choice"]).lower(),
                "preview_before_fri_decommit": str(item["preview_before_fri_decommit"]).lower(),
                "preview_before_trace_decommit": str(
                    item["preview_before_trace_decommit"]
                ).lower(),
                "can_change_committed_trace_after_preview": str(
                    item["can_change_committed_trace_after_preview"]
                ).lower(),
                "can_claim_probe_b_control": str(item["can_claim_probe_b_control"]).lower(),
                "requires_security_budget": str(item["requires_security_budget"]).lower(),
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
        raise StwoQueryPreviewSplitPrototypeGateError(str(err)) from err


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
            raise StwoQueryPreviewSplitPrototypeGateError(
                "--write-json and --write-tsv must be paired"
            )
        write_outputs(args.write_json, args.write_tsv, payload)
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        StwoQueryPreviewSplitPrototypeGateError,
        hook_gate.BoundedStwoQueryPolicyHookGateError,
    ) as err:
        print(f"error: {err}", file=sys.stderr)
        raise SystemExit(2) from None
