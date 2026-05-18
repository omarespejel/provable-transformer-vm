import json
import tempfile
import unittest
from copy import deepcopy

from scripts import zkai_larger_native_block_boundary_amortization_budget_gate as gate


class LargerNativeBlockBoundaryAmortizationBudgetGateTest(unittest.TestCase):
    def test_build_payload_pins_local_frontier_budget(self) -> None:
        payload = gate.build_payload()
        self.assertEqual(payload["schema"], gate.SCHEMA)
        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertEqual(payload["result"], gate.RESULT)
        self.assertEqual(payload["summary"]["selected_next_route"], gate.SELECTED_NEXT_ROUTE)
        self.assertEqual(payload["summary"]["strict_native_single_typed_bytes"], 41_932)
        self.assertEqual(payload["summary"]["two_proof_frontier_typed_bytes"], 40_700)
        self.assertEqual(payload["summary"]["strict_native_delta_vs_frontier_typed_bytes"], 1_232)
        self.assertEqual(payload["summary"]["strict_native_reduction_to_beat_frontier_bytes"], 1_233)
        self.assertEqual(payload["summary"]["strict_native_share_of_mlp_fusion_saving_to_beat_frontier"], "0.038359")
        self.assertEqual(payload["summary"]["four_percent_transfer_model_typed_bytes"], 40_646)
        self.assertEqual(payload["summary"]["four_percent_transfer_model_margin_vs_frontier_bytes"], 54)
        self.assertEqual(payload["summary"]["strict_native_reduction_to_beat_nanozk_context_bytes"], 35_033)
        self.assertEqual(payload["summary"]["strict_native_share_of_mlp_fusion_saving_to_beat_nanozk_context"], "1.089877")
        self.assertEqual(payload["summary"]["proof_size_comparable_rows"], 0)
        self.assertEqual(payload["mutation_count"], 13)
        self.assertEqual(payload["mutations_rejected"], 13)

    def test_build_payload_is_deterministic(self) -> None:
        self.assertEqual(gate.build_payload(), gate.build_payload())

    def test_budget_rows_are_ordered_and_guarded(self) -> None:
        payload = gate.build_payload()
        rows = {row["row_id"]: row for row in payload["budget_rows"]}
        self.assertEqual(list(rows), list(gate.EXPECTED_ROW_IDS))
        self.assertEqual(rows["strict_native_single_vs_two_proof_frontier"]["status"], "ATTACK_NEXT_LOCAL_FRONTIER")
        self.assertEqual(rows["strict_native_single_vs_two_proof_frontier"]["reduction_to_beat_reference_bytes"], 1_233)
        self.assertEqual(rows["strict_native_single_vs_two_proof_frontier"]["share_of_mlp_fusion_saving_to_beat_reference"], "0.038359")
        self.assertEqual(rows["gkr_width_preserving_vs_two_proof_frontier"]["status"], "PARK_CURRENT_GKR")
        self.assertEqual(rows["gkr_width_preserving_vs_two_proof_frontier"]["share_of_mlp_fusion_saving_to_beat_reference"], "0.915847")
        self.assertEqual(rows["strict_native_single_vs_nanozk_context"]["status"], "BLOCKED_NOT_MATCHED")
        self.assertEqual(rows["strict_native_single_vs_nanozk_context"]["share_of_mlp_fusion_saving_to_beat_reference"], "1.089877")
        self.assertFalse(any(row["proof_size_comparable_to_nanozk"] for row in rows.values()))

    def test_source_numbers_are_pinned(self) -> None:
        sources = gate.load_sources()
        gate.validate_source_numbers(sources)
        sources["native_single"] = dict(sources["native_single"])
        sources["native_single"]["summary"] = dict(sources["native_single"]["summary"])
        sources["native_single"]["summary"]["single_proof_typed_bytes"] = 40_700
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "single typed drift"):
            gate.validate_source_numbers(sources)

    def test_source_ratio_type_drift_rejected(self) -> None:
        sources = gate.load_sources()
        sources["mlp_fused"] = dict(sources["mlp_fused"])
        sources["mlp_fused"]["aggregate"] = dict(sources["mlp_fused"]["aggregate"])
        sources["mlp_fused"]["aggregate"]["typed_saving_ratio_vs_separate"] = "0.564167"
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "MLP saving ratio must be a number"):
            gate.validate_source_numbers(sources)

    def test_load_source_artifact_normalizes_missing_file(self) -> None:
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "unable to read source artifact"):
            gate.load_source_artifact(gate.EVIDENCE_DIR / "missing-amortization-budget-source.json")

    def test_load_source_artifact_normalizes_json_parse_failure(self) -> None:
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".json", delete=False) as handle:
            path = gate.pathlib.Path(handle.name)
            handle.write(b"{")
        try:
            with self.assertRaisesRegex(gate.AmortizationBudgetError, "invalid JSON source artifact"):
                gate.load_source_artifact(path)
        finally:
            path.unlink(missing_ok=True)

    def test_mutation_inventory_is_strict(self) -> None:
        payload = gate.build_payload()
        self.assertEqual([row["name"] for row in payload["mutation_results"]], [name for name, _ in gate.MUTATIONS])
        self.assertTrue(all(row["rejected"] for row in payload["mutation_results"]))

    def test_rejects_nanozk_comparable_overclaim(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_promote_nanozk_comparable(payload)
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "NANOZK proof-size comparability overclaim"):
            gate.validate_payload(payload, final=False)

    def test_rejects_selected_route_drift(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_selected_route_to_local_reorder(payload)
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "selected next route drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_strict_frontier_gap_erasure(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_strict_frontier_gap_erased(payload)
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "strict beat frontier drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_four_percent_projection_erasure(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_four_percent_projection_erased(payload)
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "four percent margin drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_mlp_saving_inflation(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_mlp_saving_inflated(payload)
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "MLP saving drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_nanozk_gap_erasure(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_nanozk_gap_erased(payload)
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "strict_native_single_vs_nanozk_context reduction to beat drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_compact_preprocessed_promotion(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_compact_preprocessed_promoted(payload)
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "NANOZK proof-size comparability overclaim"):
            gate.validate_payload(payload, final=False)

    def test_rejects_gkr_unparked(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_gkr_unparked(payload)
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "GKR row status drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_interpretation_overclaim(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_interpretation_overclaim(payload)
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "NANOZK interpretation drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_malformed_budget_row(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        payload["budget_rows"][0] = "not-an-object"
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "budget row must be an object"):
            gate.validate_payload(payload, final=False)

    def test_rejects_budget_row_key_inventory_drift(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        payload["budget_rows"][0] = dict(payload["budget_rows"][0])
        payload["budget_rows"][0].pop("status")
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "budget row key inventory drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_computed_delta_drift(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        payload["budget_rows"][0]["delta_vs_reference_typed_bytes"] = 0
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "strict_native_single_vs_two_proof_frontier delta drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_source_descriptor_drift(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_source_descriptor_drift(payload)
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "source artifact descriptor drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_source_descriptor_key_inventory_drift(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        payload["source_artifacts"][0] = dict(payload["source_artifacts"][0])
        payload["source_artifacts"][0].pop("schema")
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "source artifact row key inventory drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_source_descriptor_sha_format_drift(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        payload["source_artifacts"][0] = dict(payload["source_artifacts"][0])
        payload["source_artifacts"][0]["sha256"] = "not-a-sha"
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "source artifact sha256 format drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_non_claim_erasure(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_remove_non_claim(payload)
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "payload missing non-claims"):
            gate.validate_payload(payload, final=False)

    def test_rejects_validation_command_drift(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_validation_command_drift(payload)
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "validation command inventory drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_payload_commitment_drift(self) -> None:
        payload = gate.build_payload()
        gate.mutate_payload_commitment(payload)
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "payload commitment drift"):
            gate.validate_payload(payload)

    def test_rejects_mutation_inventory_drift(self) -> None:
        payload = gate.build_payload()
        payload["mutation_results"] = deepcopy(payload["mutation_results"])
        payload["mutation_results"].pop()
        payload["mutation_count"] -= 1
        payload["mutations_rejected"] -= 1
        payload["payload_commitment"] = gate.commitment({key: value for key, value in payload.items() if key != "payload_commitment"})
        with self.assertRaisesRegex(gate.AmortizationBudgetError, "mutation inventory drift"):
            gate.validate_payload(payload)

    def test_tsv_shape(self) -> None:
        text = gate.tsv_text(gate.build_payload())
        self.assertEqual(text.splitlines()[0].split("\t"), list(gate.ROW_COLUMNS))
        self.assertIn("strict_native_single_vs_two_proof_frontier\tATTACK_NEXT_LOCAL_FRONTIER", text)
        self.assertIn("compact_preprocessed_vs_nanozk_context\tMECHANISM_LEAD_NOT_COMPARABLE", text)

    def test_write_outputs_round_trips(self) -> None:
        payload = gate.build_payload()
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".json", delete=False) as json_handle:
            json_path = gate.pathlib.Path(json_handle.name)
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".tsv", delete=False) as tsv_handle:
            tsv_path = gate.pathlib.Path(tsv_handle.name)
        try:
            gate.write_outputs(payload, json_path, tsv_path)
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8")), payload)
            self.assertTrue(tsv_path.read_text(encoding="utf-8").startswith("\t".join(gate.ROW_COLUMNS)))
        finally:
            json_path.unlink(missing_ok=True)
            tsv_path.unlink(missing_ok=True)

    def test_write_outputs_rejects_outside_evidence_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(gate.AmortizationBudgetError, "evidence dir"):
                gate.write_outputs(gate.build_payload(), gate.pathlib.Path(tmpdir) / "payload.json", None)

    def test_write_outputs_rejects_symlink_in_path(self) -> None:
        payload = gate.build_payload()
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix="tmp-amortization-symlink-") as tmpdir:
            tmp_path = gate.pathlib.Path(tmpdir)
            target = tmp_path / "target.json"
            target.write_text("{}", encoding="utf-8")
            link = tmp_path / "link.json"
            link.symlink_to(target)
            with self.assertRaisesRegex(gate.AmortizationBudgetError, "symlink"):
                gate.write_outputs(payload, link, None)

    def test_write_outputs_rejects_symlink_parent(self) -> None:
        payload = gate.build_payload()
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix="tmp-amortization-parent-target-") as target_dir:
            target_path = gate.pathlib.Path(target_dir)
            link_dir = target_path.with_name(f"{target_path.name}-link")
            try:
                link_dir.symlink_to(target_path, target_is_directory=True)
                with self.assertRaisesRegex(gate.AmortizationBudgetError, "symlink"):
                    gate.write_outputs(payload, link_dir / "payload.json", None)
            finally:
                link_dir.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
