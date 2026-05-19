#!/usr/bin/env python3.10
"""Gate bounded transcript-grinding budgets for Stwo query geometry."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import math
import pathlib
import sys
from typing import Any


if sys.version_info < (3, 10):
    raise RuntimeError("zkai_stwo_query_grinding_budget_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import zkai_stwo_query_preview_split_prototype_gate as preview_gate
from scripts import zkai_bounded_stwo_query_policy_hook_gate as hook_gate
from scripts import zkai_native_seq32_attention_mlp_dry_run_opening_sampler_gate as sampler_gate


EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"
JSON_OUT = EVIDENCE_DIR / "zkai-stwo-query-grinding-budget-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-stwo-query-grinding-budget-2026-05.tsv"

SCHEMA = "zkai-stwo-query-grinding-budget-gate-v1"
DECISION = "NARROW_CLAIM_SMALL_VERIFIER_BOUND_RETRY_BUDGET_CAN_RECOVER_PROBE_B_INVENTORY"
RESULT = "GO_MECHANISM_LEAD_NOT_PROOF_SIZE_FRONTIER"
ISSUE_HINT = "https://github.com/omarespejel/provable-transformer-vm/issues/706"
PAYLOAD_DOMAIN = "ptvm:zkai:stwo-query-grinding-budget:v1"

INVENTORY_TSV = hook_gate.PREDECOMMIT_TSV_PATH
BASELINE_VARIANT_ID = "fixed_adjacent_layout"
CHAMPION_VARIANT_ID = "adjacent_label_probe_b"
EXPECTED_INVENTORY_COUNT = 9
EXPECTED_UNITTEST_STEP_COUNT = 18
MAX_PAPER_PROTOTYPE_LOSS_BITS = "2.000000"
EXPECTED_POLICY_STAGE = "post_transcript_pre_accounting_not_true_predecommit"
EXPECTED_API_CONTROL_STATUS = "NO_TRUE_PREDECOMMIT_CONTROL_HOOK_IN_CURRENT_WRAPPER"
EXPECTED_INVENTORY_COMMITMENT = (
    "blake2b-256:6b58d3f30c5a0b0e5d1aa78890f72c5830d973f3b3795bc1917fc0253266c37e"
)
EXPECTED_PAYLOAD_COMMITMENT = (
    "blake2b-256:139ebaf55f70c771cf1d1f9f6fb8a132bc2215118e46a6ca4dbd2d6da4e0aea6"
)

TSV_COLUMNS = (
    "policy_id",
    "status",
    "attempt_budget",
    "security_loss_bits",
    "best_variant_id",
    "best_typed_bytes",
    "improvement_vs_fixed_typed_bytes",
    "improvement_vs_champion_typed_bytes",
    "requires_verifier_bound_attempt_domain",
    "claims_new_frontier",
)
REQUIRED_INVENTORY_COLUMNS = (
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
    "python3.10 scripts/zkai_stwo_query_grinding_budget_gate.py --write-json docs/engineering/evidence/zkai-stwo-query-grinding-budget-2026-05.json --write-tsv docs/engineering/evidence/zkai-stwo-query-grinding-budget-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_stwo_query_grinding_budget_gate.py scripts/tests/test_zkai_stwo_query_grinding_budget_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_stwo_query_grinding_budget_gate",
    "git diff --check",
    "just gate-fast",
    "just gate",
)
NON_CLAIMS = (
    "not a new proof-size frontier",
    "not regenerated proof objects under a grinding API",
    "not an absolute soundness claim",
    "not a verifier implementation",
    "not a production query policy",
    "not a NANOZK proof-size comparison",
    "not a full transformer block proof",
    "not timing evidence",
)
MUTATION_NAMES = (
    "decision_overclaim",
    "result_overclaim",
    "inventory_count_drift",
    "inventory_commitment_drift",
    "inventory_trust_field_drift",
    "baseline_metric_drift",
    "champion_metric_drift",
    "two_probe_claims_new_frontier",
    "two_probe_security_loss_understated",
    "two_probe_verifier_bound_removed",
    "seed_only_promoted",
    "all_inventory_promoted",
    "unbounded_policy_allowed",
    "final_envelope_json_allowed",
    "final_proof_bytes_allowed",
    "post_decommitment_accounting_allowed",
    "unbounded_retry_count_allowed",
    "uncommitted_attempt_domain_allowed",
    "max_loss_bits_drift",
    "validation_command_removed",
    "non_claim_removed",
    "payload_commitment_drift",
)


class StwoQueryGrindingBudgetGateError(Exception):
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
        raise StwoQueryGrindingBudgetGateError(f"non-canonical JSON value: {err}") from err


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


def parse_int(row: dict[str, str], field: str) -> int:
    try:
        value = int(row[field])
    except (KeyError, TypeError, ValueError) as err:
        raise StwoQueryGrindingBudgetGateError(f"inventory field {field} is invalid") from err
    if value < 0:
        raise StwoQueryGrindingBudgetGateError(f"inventory field {field} is negative: {value}")
    return value


def parse_text(row: dict[str, str], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or value == "":
        raise StwoQueryGrindingBudgetGateError(f"inventory field {field} is invalid")
    return value


def parse_bool_token(row: dict[str, str], field: str) -> bool:
    value = parse_text(row, field)
    if value == "true":
        return True
    if value == "false":
        return False
    raise StwoQueryGrindingBudgetGateError(f"inventory field {field} is invalid")


def load_inventory() -> list[dict[str, Any]]:
    raw = hook_gate.read_repo_file(INVENTORY_TSV, "predecommit inventory TSV", hook_gate.MAX_EVIDENCE_BYTES)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as err:
        raise StwoQueryGrindingBudgetGateError("predecommit inventory TSV is not UTF-8") from err
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    if tuple(reader.fieldnames or ()) != REQUIRED_INVENTORY_COLUMNS:
        raise StwoQueryGrindingBudgetGateError("inventory header drift")
    rows = list(reader)
    if len(rows) != EXPECTED_INVENTORY_COUNT:
        raise StwoQueryGrindingBudgetGateError("inventory row count drift")
    inventory = []
    for row in rows:
        policy_stage = parse_text(row, "policy_stage")
        if policy_stage != EXPECTED_POLICY_STAGE:
            raise StwoQueryGrindingBudgetGateError("inventory policy stage drift")
        api_control_status = parse_text(row, "api_control_status")
        if api_control_status != EXPECTED_API_CONTROL_STATUS:
            raise StwoQueryGrindingBudgetGateError("inventory API control status drift")
        predicted_path_opening_bytes = parse_int(row, "predicted_path_opening_bytes")
        final_path_opening_bytes = parse_int(row, "final_path_opening_bytes")
        if predicted_path_opening_bytes != final_path_opening_bytes:
            raise StwoQueryGrindingBudgetGateError("inventory predicted path-opening drift")
        inventory.append(
            {
                "variant_id": parse_text(row, "variant_id"),
                "adapter_mode": parse_text(row, "adapter_mode"),
                "policy_stage": policy_stage,
                "query_location_span": parse_int(row, "query_location_span"),
                "min_pairwise_query_gap": parse_int(row, "min_pairwise_query_gap"),
                "selected_without_final_accounting": parse_bool_token(row, "selected_without_final_accounting"),
                "predicted_path_opening_bytes": predicted_path_opening_bytes,
                "final_path_opening_bytes": final_path_opening_bytes,
                "final_typed_bytes": parse_int(row, "final_typed_bytes"),
                "api_control_status": api_control_status,
            }
        )
    selected_ids = [row["variant_id"] for row in inventory if row["selected_without_final_accounting"]]
    if selected_ids != [CHAMPION_VARIANT_ID]:
        raise StwoQueryGrindingBudgetGateError("inventory selected-without-final-accounting drift")
    return inventory


def find_variant(inventory: list[dict[str, Any]], variant_id: str) -> dict[str, Any]:
    matches = [row for row in inventory if row["variant_id"] == variant_id]
    if len(matches) != 1:
        raise StwoQueryGrindingBudgetGateError(f"variant missing: {variant_id}")
    return matches[0]


def best_variant(inventory: list[dict[str, Any]], variant_ids: tuple[str, ...]) -> dict[str, Any]:
    rows = [find_variant(inventory, variant_id) for variant_id in variant_ids]
    return min(rows, key=lambda row: (row["final_typed_bytes"], row["query_location_span"], row["variant_id"]))


def loss_bits(attempt_budget: int) -> str:
    if attempt_budget <= 0:
        raise StwoQueryGrindingBudgetGateError("attempt budget must be positive")
    return f"{math.log2(attempt_budget):.6f}"


def classify_policy(policy_id: str, best: dict[str, Any], attempt_budget: int) -> str:
    if policy_id == "fixed_layout_budget_1":
        return "BASELINE_NO_GRINDING"
    if policy_id == "two_probe_budget_2":
        if attempt_budget == 2 and best["variant_id"] == CHAMPION_VARIANT_ID:
            return "MECHANISM_GO_REQUIRES_VERIFIER_BOUND_ATTEMPT_DOMAIN"
        return "NO_GO_TWO_PROBE_DOES_NOT_RECOVER_CHAMPION"
    if policy_id == "seed_only_budget_6":
        if best["variant_id"] == CHAMPION_VARIANT_ID:
            return "NO_GO_SEED_ONLY_RECOVERS_CHAMPION_BUT_SPENDS_EXTRA_BUDGET"
        return "NO_GO_SEED_ONLY_DOES_NOT_RECOVER_CHAMPION"
    if policy_id == "all_inventory_budget_9":
        if best["variant_id"] == CHAMPION_VARIANT_ID:
            return "NO_GO_UNNEEDED_EXTRA_GRINDING"
        return "NO_GO_ALL_INVENTORY_DOES_NOT_RECOVER_CHAMPION"
    raise StwoQueryGrindingBudgetGateError(f"unknown policy: {policy_id}")


def policy(inventory: list[dict[str, Any]], policy_id: str, variant_ids: tuple[str, ...]) -> dict[str, Any]:
    baseline = find_variant(inventory, BASELINE_VARIANT_ID)
    champion = find_variant(inventory, CHAMPION_VARIANT_ID)
    best = best_variant(inventory, variant_ids)
    attempt_budget = len(variant_ids)
    status = classify_policy(policy_id, best, attempt_budget)
    return {
        "policy_id": policy_id,
        "status": status,
        "allowed_variant_ids": list(variant_ids),
        "attempt_budget": attempt_budget,
        "security_loss_bits": loss_bits(attempt_budget),
        "best_variant_id": best["variant_id"],
        "best_typed_bytes": best["final_typed_bytes"],
        "best_path_opening_bytes": best["final_path_opening_bytes"],
        "improvement_vs_fixed_typed_bytes": baseline["final_typed_bytes"] - best["final_typed_bytes"],
        "improvement_vs_champion_typed_bytes": champion["final_typed_bytes"] - best["final_typed_bytes"],
        "requires_verifier_bound_attempt_domain": attempt_budget > 1,
        "claims_new_frontier": False,
    }


def policies(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        policy(
            inventory,
            "fixed_layout_budget_1",
            ("fixed_adjacent_layout",),
        ),
        policy(
            inventory,
            "two_probe_budget_2",
            ("adjacent_label_probe_a", "adjacent_label_probe_b"),
        ),
        policy(
            inventory,
            "seed_only_budget_6",
            (
                "adjacent_seed_00",
                "adjacent_seed_01",
                "adjacent_seed_02",
                "adjacent_seed_03",
                "adjacent_seed_04",
                "adjacent_seed_05",
            ),
        ),
        policy(
            inventory,
            "all_inventory_budget_9",
            tuple(row["variant_id"] for row in inventory),
        ),
        {
            "policy_id": "unbounded_abort_and_retry",
            "status": "REJECTED_UNBOUNDED_SECURITY_LOSS",
            "allowed_variant_ids": [],
            "attempt_budget": None,
            "security_loss_bits": None,
            "best_variant_id": None,
            "best_typed_bytes": None,
            "best_path_opening_bytes": None,
            "improvement_vs_fixed_typed_bytes": None,
            "improvement_vs_champion_typed_bytes": None,
            "requires_verifier_bound_attempt_domain": True,
            "claims_new_frontier": False,
        },
    ]


def build_payload_without_mutations() -> dict[str, Any]:
    preview_payload = preview_gate.build_payload_without_mutations()
    inventory = load_inventory()
    baseline = find_variant(inventory, BASELINE_VARIANT_ID)
    champion = find_variant(inventory, CHAMPION_VARIANT_ID)
    policy_rows = policies(inventory)
    return {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE_HINT,
        "parent_issue": preview_payload["issue"],
        "inventory": {
            "source_path": str(INVENTORY_TSV.relative_to(ROOT)),
            "row_count": len(inventory),
            "commitment": blake2b_commitment("ptvm:zkai:grinding-inventory:v1", inventory),
            "rows": inventory,
        },
        "baseline": baseline,
        "champion": champion,
        "policy_rows": policy_rows,
        "budget_rule": {
            "relative_security_loss": "attempt_budget multiplies Fiat-Shamir search space",
            "security_loss_bits_formula": "log2(attempt_budget)",
            "paper_prototype_max_loss_bits": MAX_PAPER_PROTOTYPE_LOSS_BITS,
            "verifier_must_bind_attempt_domain": True,
            "verifier_must_reject_attempts_outside_domain": True,
            "absolute_soundness_claim": False,
        },
        "forbidden_policy_inputs": {
            "final_envelope_json": True,
            "final_proof_bytes": True,
            "post_decommitment_accounting": True,
            "unbounded_retry_count": True,
            "uncommitted_attempt_domain": True,
        },
        "interpretation": {
            "human_read": (
                "The small controlled signal is real: a two-attempt probe policy recovers "
                "the existing probe-B row from the checked inventory with one bit of relative "
                "Fiat-Shamir grinding loss. It does not improve the current champion and does "
                "not become a frontier until regenerated proofs enforce the attempt domain."
            ),
            "why_it_matters": (
                "This turns query geometry from post-hoc label selection into a bounded "
                "proof-system policy question. The next implementation should bind the "
                "attempt domain in the verifier-facing statement before claiming size wins."
            ),
            "next_experiment": (
                "Prototype a verifier-bound attempt-domain metadata path and regenerate the "
                "seq32+d128 proof for the two-probe policy."
            ),
        },
        "validation_commands": list(VALIDATION_COMMANDS),
        "non_claims": list(NON_CLAIMS),
        "reproducibility_metadata": {
            "mutation_step_count": len(MUTATION_NAMES),
            "unittest_step_count": EXPECTED_UNITTEST_STEP_COUNT,
            "local_release_gate_step_count": 14,
        },
    }


def policy_row(payload: dict[str, Any], policy_id: str) -> dict[str, Any]:
    for row in payload.get("policy_rows", []):
        if row.get("policy_id") == policy_id:
            return row
    raise StwoQueryGrindingBudgetGateError(f"policy missing: {policy_id}")


def validate_base_payload(payload: dict[str, Any]) -> None:
    expected = build_payload_without_mutations()
    if payload != expected:
        raise StwoQueryGrindingBudgetGateError("base payload drift")
    if payload["decision"] != DECISION or payload["result"] != RESULT:
        raise StwoQueryGrindingBudgetGateError("claim boundary drift")
    if payload["inventory"]["row_count"] != EXPECTED_INVENTORY_COUNT:
        raise StwoQueryGrindingBudgetGateError("inventory count drift")
    if payload["inventory"]["commitment"] != EXPECTED_INVENTORY_COMMITMENT:
        raise StwoQueryGrindingBudgetGateError("published inventory commitment drift")
    baseline = payload["baseline"]
    champion = payload["champion"]
    if baseline["variant_id"] != BASELINE_VARIANT_ID or baseline["final_typed_bytes"] != 42_156:
        raise StwoQueryGrindingBudgetGateError("baseline metric drift")
    if champion["variant_id"] != CHAMPION_VARIANT_ID or champion["final_typed_bytes"] != 37_532:
        raise StwoQueryGrindingBudgetGateError("champion metric drift")
    two_probe = policy_row(payload, "two_probe_budget_2")
    if two_probe["security_loss_bits"] != "1.000000":
        raise StwoQueryGrindingBudgetGateError("two-probe security loss drift")
    if not two_probe["requires_verifier_bound_attempt_domain"]:
        raise StwoQueryGrindingBudgetGateError("two-probe verifier-bound domain missing")
    if two_probe["claims_new_frontier"]:
        raise StwoQueryGrindingBudgetGateError("two-probe frontier overclaim")
    if two_probe["improvement_vs_fixed_typed_bytes"] != 4_624:
        raise StwoQueryGrindingBudgetGateError("two-probe improvement drift")
    if two_probe["improvement_vs_champion_typed_bytes"] != 0:
        raise StwoQueryGrindingBudgetGateError("champion improvement overclaim")
    seed_only = policy_row(payload, "seed_only_budget_6")
    if not seed_only["status"].startswith("NO_GO"):
        raise StwoQueryGrindingBudgetGateError("seed-only promotion drift")
    all_inventory = policy_row(payload, "all_inventory_budget_9")
    if all_inventory["status"] != "NO_GO_UNNEEDED_EXTRA_GRINDING":
        raise StwoQueryGrindingBudgetGateError("all-inventory promotion drift")
    unbounded = policy_row(payload, "unbounded_abort_and_retry")
    if unbounded["status"] != "REJECTED_UNBOUNDED_SECURITY_LOSS":
        raise StwoQueryGrindingBudgetGateError("unbounded retry not rejected")
    for policy_item in payload["policy_rows"]:
        if policy_item["claims_new_frontier"]:
            raise StwoQueryGrindingBudgetGateError("policy row frontier overclaim")
        if (
            policy_item["status"].startswith("MECHANISM_GO")
            and policy_item["requires_verifier_bound_attempt_domain"] is not True
        ):
            raise StwoQueryGrindingBudgetGateError("mechanism policy missing verifier-bound domain")
    for field, forbidden in payload["forbidden_policy_inputs"].items():
        if forbidden is not True:
            raise StwoQueryGrindingBudgetGateError(f"forbidden policy input allowed: {field}")
    if payload["budget_rule"]["paper_prototype_max_loss_bits"] != MAX_PAPER_PROTOTYPE_LOSS_BITS:
        raise StwoQueryGrindingBudgetGateError("max loss-bit drift")
    if payload["validation_commands"] != list(VALIDATION_COMMANDS):
        raise StwoQueryGrindingBudgetGateError("validation command drift")
    if payload["non_claims"] != list(NON_CLAIMS):
        raise StwoQueryGrindingBudgetGateError("non-claim drift")


def validate_payload(payload: dict[str, Any]) -> None:
    item = copy.deepcopy(payload)
    supplied_commitment = item.pop("payload_commitment", None)
    mutation_result = item.pop("mutation_result", None)
    validate_base_payload(item)
    if supplied_commitment != payload_commitment(payload):
        raise StwoQueryGrindingBudgetGateError("payload commitment drift")
    if supplied_commitment != EXPECTED_PAYLOAD_COMMITMENT:
        raise StwoQueryGrindingBudgetGateError("published payload commitment drift")
    expected_mutation = run_mutations(item)
    if mutation_result != expected_mutation:
        raise StwoQueryGrindingBudgetGateError("mutation result drift")
    validate_mutation_result(mutation_result)


def validate_mutation_result(mutation_result: Any) -> None:
    if not isinstance(mutation_result, dict):
        raise StwoQueryGrindingBudgetGateError("mutation result missing")
    if mutation_result.get("mutation_names") != list(MUTATION_NAMES):
        raise StwoQueryGrindingBudgetGateError("mutation names drift")
    cases = mutation_result.get("cases")
    if not isinstance(cases, list) or len(cases) != len(MUTATION_NAMES):
        raise StwoQueryGrindingBudgetGateError("mutation case count drift")
    for case in cases:
        if not isinstance(case, dict):
            raise StwoQueryGrindingBudgetGateError("mutation case schema drift")
        if (
            not isinstance(case.get("name"), str)
            or not isinstance(case.get("rejected"), bool)
            or not isinstance(case.get("error"), str)
        ):
            raise StwoQueryGrindingBudgetGateError("mutation case schema drift")
    if [case["name"] for case in cases if case["rejected"]] != list(MUTATION_NAMES):
        raise StwoQueryGrindingBudgetGateError("mutation rejection drift")
    if mutation_result.get("mutations_rejected") != len(MUTATION_NAMES):
        raise StwoQueryGrindingBudgetGateError("mutation rejected count drift")
    if mutation_result.get("all_mutations_rejected") is not True:
        raise StwoQueryGrindingBudgetGateError("mutation all-rejected drift")


def mutate_payload(name: str, item: dict[str, Any]) -> None:
    if name == "decision_overclaim":
        item["decision"] = "GO_GRINDING_BREAKTHROUGH"
    elif name == "result_overclaim":
        item["result"] = "NEW_PROOF_SIZE_FRONTIER"
    elif name == "inventory_count_drift":
        item["inventory"]["row_count"] = 8
    elif name == "inventory_commitment_drift":
        item["inventory"]["commitment"] = "blake2b-256:" + ("0" * 64)
    elif name == "inventory_trust_field_drift":
        item["inventory"]["rows"][0]["api_control_status"] = "POST_DECOMMITMENT_CONTROL_ALLOWED"
    elif name == "baseline_metric_drift":
        item["baseline"]["final_typed_bytes"] = 41_000
    elif name == "champion_metric_drift":
        item["champion"]["final_typed_bytes"] = 36_000
    elif name == "two_probe_claims_new_frontier":
        policy_row(item, "two_probe_budget_2")["claims_new_frontier"] = True
    elif name == "two_probe_security_loss_understated":
        policy_row(item, "two_probe_budget_2")["security_loss_bits"] = "0.000000"
    elif name == "two_probe_verifier_bound_removed":
        policy_row(item, "two_probe_budget_2")["requires_verifier_bound_attempt_domain"] = False
    elif name == "seed_only_promoted":
        policy_row(item, "seed_only_budget_6")["status"] = "GO"
    elif name == "all_inventory_promoted":
        policy_row(item, "all_inventory_budget_9")["status"] = "GO"
    elif name == "unbounded_policy_allowed":
        policy_row(item, "unbounded_abort_and_retry")["status"] = "GO"
    elif name == "final_envelope_json_allowed":
        item["forbidden_policy_inputs"]["final_envelope_json"] = False
    elif name == "final_proof_bytes_allowed":
        item["forbidden_policy_inputs"]["final_proof_bytes"] = False
    elif name == "post_decommitment_accounting_allowed":
        item["forbidden_policy_inputs"]["post_decommitment_accounting"] = False
    elif name == "unbounded_retry_count_allowed":
        item["forbidden_policy_inputs"]["unbounded_retry_count"] = False
    elif name == "uncommitted_attempt_domain_allowed":
        item["forbidden_policy_inputs"]["uncommitted_attempt_domain"] = False
    elif name == "max_loss_bits_drift":
        item["budget_rule"]["paper_prototype_max_loss_bits"] = "8.000000"
    elif name == "validation_command_removed":
        item["validation_commands"].pop()
    elif name == "non_claim_removed":
        item["non_claims"].remove("not a new proof-size frontier")
    elif name == "payload_commitment_drift":
        item["payload_commitment"] = "blake2b-256:" + ("0" * 64)
    else:
        raise StwoQueryGrindingBudgetGateError(f"unknown mutation: {name}")


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
        except (StwoQueryGrindingBudgetGateError, preview_gate.StwoQueryPreviewSplitPrototypeGateError, hook_gate.BoundedStwoQueryPolicyHookGateError) as err:
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
    for row in payload["policy_rows"]:
        writer.writerow({column: row[column] for column in TSV_COLUMNS})
    return output.getvalue()


def write_outputs(json_path: pathlib.Path, tsv_path: pathlib.Path, payload: dict[str, Any]) -> None:
    validate_payload(payload)
    json_data = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True).encode() + b"\n"
    tsv_data = render_tsv(payload).encode()
    try:
        sampler_gate.atomic_write_pair(json_path, json_data, tsv_path, tsv_data)
    except sampler_gate.DryRunOpeningSamplerGateError as err:
        raise StwoQueryGrindingBudgetGateError(str(err)) from err


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
            raise StwoQueryGrindingBudgetGateError("--write-json and --write-tsv must be paired")
        write_outputs(args.write_json, args.write_tsv, payload)
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        StwoQueryGrindingBudgetGateError,
        preview_gate.StwoQueryPreviewSplitPrototypeGateError,
        hook_gate.BoundedStwoQueryPolicyHookGateError,
    ) as err:
        print(f"error: {err}", file=sys.stderr)
        raise SystemExit(2) from None
