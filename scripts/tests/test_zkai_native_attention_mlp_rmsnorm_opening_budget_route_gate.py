import copy
import csv
import io
import pathlib
import tempfile
import unittest
from unittest import mock

from scripts import zkai_native_attention_mlp_rmsnorm_opening_budget_route_gate as gate


class RmsnormOpeningBudgetRouteGateTest(unittest.TestCase):
    def test_payload_pins_worst_label_opening_budget(self) -> None:
        payload = gate.build_payload()
        summary = payload["summary"]

        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertEqual(payload["result"], gate.RESULT)
        self.assertEqual(summary["worst_label_required_reduction_to_beat_frontier_bytes"], 1_401)
        self.assertEqual(summary["worst_label_path_opening_overhang_vs_compact_bytes"], 1_680)
        self.assertEqual(summary["required_share_of_worst_label_path_opening_overhang"], 0.833929)
        self.assertEqual(summary["full_worst_label_path_opening_removal_modeled_typed_bytes"], 40_420)
        self.assertEqual(summary["full_worst_label_path_opening_removal_frontier_margin_bytes"], 280)
        self.assertEqual(summary["strict_margin_after_required_reduction_bytes"], 279)
        self.assertEqual(summary["rmsnorm_value_saving_vs_compact_bytes"], 392)

    def test_route_candidates_separate_cherry_pick_from_policy_target(self) -> None:
        payload = gate.build_payload()
        candidates = payload["route_candidates"]

        self.assertTrue(candidates["single_best_label"]["cherry_pick_risk"])
        self.assertFalse(candidates["single_best_label"]["policy_sufficient_if_full_path_opening_removed"])
        self.assertEqual(candidates["single_best_label"]["required_reduction_to_beat_frontier_bytes"], 137)
        self.assertFalse(candidates["canonical_overhang_only"]["policy_sufficient_if_full_path_opening_removed"])
        self.assertEqual(candidates["canonical_overhang_only"]["path_opening_overhang_vs_compact_bytes"], 1_008)
        self.assertTrue(
            candidates["worst_label_path_opening_to_compact"][
                "policy_sufficient_if_full_path_opening_removed"
            ]
        )
        self.assertEqual(
            candidates["worst_label_path_opening_to_compact"][
                "required_share_of_path_opening_overhang"
            ],
            0.833929,
        )

    def test_route_budget_explains_why_opening_attack_is_alive_but_not_claimed(self) -> None:
        payload = gate.build_payload()
        budget = payload["route_budget"]

        self.assertFalse(budget["canonical_overhang_sufficient_under_worst_label_policy"])
        self.assertFalse(budget["current_promotion_allowed"])
        self.assertEqual(budget["worst_label_path_opening_overhang_vs_compact_bytes"], 1_680)
        self.assertEqual(budget["modeled_typed_after_full_worst_label_path_opening_removal"], 40_420)
        self.assertEqual(
            budget["modeled_frontier_margin_after_full_worst_label_path_opening_removal_bytes"],
            280,
        )
        self.assertFalse(payload["issue_scope"]["closes_issue"])
        self.assertFalse(payload["issue_scope"]["satisfies_issue_go_gate"])

    def test_mutations_are_rejected(self) -> None:
        payload = gate.build_payload()
        result = payload["mutation_result"]

        self.assertEqual(result["mutation_count"], len(gate.EXPECTED_MUTATION_NAMES))
        self.assertEqual(result["rejected_count"], len(gate.EXPECTED_MUTATION_NAMES))
        self.assertEqual([case["name"] for case in result["cases"]], list(gate.EXPECTED_MUTATION_NAMES))
        self.assertTrue(all(case["rejected"] for case in result["cases"]))

    def test_frontier_overclaim_is_rejected(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["frontier"]["frontier_win_claimed"] = True
        gate.refresh_payload_commitment(mutated)

        with self.assertRaisesRegex(gate.OpeningBudgetRouteError, "frontier overclaim"):
            gate.validate_payload(mutated)

    def test_nanozk_workload_overclaim_is_rejected(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["frontier"]["nanozk_workload_matched"] = True
        gate.refresh_payload_commitment(mutated)

        with self.assertRaisesRegex(gate.OpeningBudgetRouteError, "NANOZK workload"):
            gate.validate_payload(mutated)

    def test_source_artifact_drift_is_rejected(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["source_artifacts"][0]["sha256"] = "00" * 32
        gate.refresh_payload_commitment(mutated)

        with self.assertRaisesRegex(gate.OpeningBudgetRouteError, "source artifact drift"):
            gate.validate_payload(mutated)

    def test_worst_label_required_reduction_drift_is_rejected(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["route_budget"]["worst_label_required_reduction_to_beat_frontier_bytes"] = 137
        gate.refresh_payload_commitment(mutated)

        with self.assertRaisesRegex(gate.OpeningBudgetRouteError, "route budget drift"):
            gate.validate_payload(mutated)

    def test_single_label_policy_overclaim_is_rejected(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["route_candidates"]["single_best_label"][
            "policy_sufficient_if_full_path_opening_removed"
        ] = True
        gate.refresh_payload_commitment(mutated)

        with self.assertRaisesRegex(gate.OpeningBudgetRouteError, "policy sufficiency drift"):
            gate.validate_payload(mutated)

    def test_route_status_drift_is_rejected(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["route_candidates"]["worst_label_path_opening_to_compact"]["route_status"] = "UNREVIEWED_STATUS"
        gate.refresh_payload_commitment(mutated)

        with self.assertRaisesRegex(gate.OpeningBudgetRouteError, "route status not allowed"):
            gate.validate_payload(mutated)

    def test_route_source_variant_drift_is_rejected(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["route_candidates"]["worst_label_path_opening_to_compact"]["source_variant"] = "label_probe_a"
        gate.refresh_payload_commitment(mutated)

        with self.assertRaisesRegex(gate.OpeningBudgetRouteError, "source variant drift"):
            gate.validate_payload(mutated)

    def test_route_margin_drift_is_rejected(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["route_candidates"]["worst_label_path_opening_to_compact"][
            "modeled_frontier_margin_after_full_path_opening_removal_bytes"
        ] = 0
        gate.refresh_payload_commitment(mutated)

        with self.assertRaisesRegex(gate.OpeningBudgetRouteError, "modeled margin drift"):
            gate.validate_payload(mutated)

    def test_issue_scope_overclaim_is_rejected(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["issue_scope"]["satisfies_issue_go_gate"] = True
        gate.refresh_payload_commitment(mutated)

        with self.assertRaisesRegex(gate.OpeningBudgetRouteError, "issue scope drift"):
            gate.validate_payload(mutated)

    def test_zero_worst_label_overhang_fails_closed(self) -> None:
        original_variant = gate.variant

        def variant_with_zero_worst_overhang(sensitivity_payload, name):
            item = copy.deepcopy(original_variant(sensitivity_payload, name))
            if name == "label_probe_b":
                item["path_opening_bytes"] = 19_504
            return item

        with mock.patch.object(gate, "variant", side_effect=variant_with_zero_worst_overhang):
            with self.assertRaisesRegex(gate.OpeningBudgetRouteError, "overhang must be positive"):
                gate.build_payload()

    def test_payload_commitment_rejects_drift(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["summary"]["full_worst_label_path_opening_removal_frontier_margin_bytes"] = 0
        gate.refresh_payload_commitment(mutated)

        with self.assertRaisesRegex(gate.OpeningBudgetRouteError, "summary drift"):
            gate.validate_payload(mutated)

    def test_mutation_result_rejects_extra_keys(self) -> None:
        payload = gate.build_payload()
        mutated = copy.deepcopy(payload["mutation_result"])
        mutated["unchecked"] = True

        with self.assertRaisesRegex(gate.OpeningBudgetRouteError, "mutation result key drift"):
            gate.validate_mutation_result(mutated)

    def test_tsv_uses_route_order(self) -> None:
        payload = gate.build_payload()
        rows = list(csv.DictReader(io.StringIO(gate.tsv_text(payload)), dialect="excel-tab"))

        self.assertEqual([row["route_candidate"] for row in rows], list(gate.ROUTE_CANDIDATE_ORDER))
        self.assertEqual(rows[2]["route_candidate"], "worst_label_path_opening_to_compact")
        self.assertEqual(rows[2]["required_reduction_to_beat_frontier_bytes"], "1401")
        self.assertEqual(rows[2]["required_share_of_path_opening_overhang"], "0.833929")

    def test_write_outputs_rejects_invalid_payload(self) -> None:
        payload = gate.build_payload()
        payload["frontier"]["frontier_win_claimed"] = True
        gate.refresh_payload_commitment(payload)

        with self.assertRaisesRegex(gate.OpeningBudgetRouteError, "frontier overclaim"):
            gate.write_outputs(payload, gate.JSON_OUT, None)

    def test_write_outputs_rejects_duplicate_destinations(self) -> None:
        payload = gate.build_payload()

        with self.assertRaisesRegex(gate.OpeningBudgetRouteError, "duplicate output destination"):
            gate.write_outputs(payload, gate.JSON_OUT, gate.JSON_OUT.with_suffix(".json"))

    def test_write_outputs_rejects_wrong_suffix(self) -> None:
        payload = gate.build_payload()

        with self.assertRaisesRegex(gate.OpeningBudgetRouteError, "suffix"):
            gate.write_outputs(payload, gate.JSON_OUT.with_suffix(".txt"), None)

    def test_write_outputs_rejects_outside_evidence_dir(self) -> None:
        payload = gate.build_payload()
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(gate.OpeningBudgetRouteError, "evidence dir"):
                gate.write_outputs(payload, pathlib.Path(tmpdir) / "route.json", None)


if __name__ == "__main__":
    unittest.main()
