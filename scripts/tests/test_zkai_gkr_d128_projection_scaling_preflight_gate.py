import json
import tempfile
import unittest
from copy import deepcopy

from scripts import zkai_gkr_d128_projection_scaling_preflight_gate as gate


class GkrD128ProjectionScalingPreflightGateTest(unittest.TestCase):
    def test_build_payload_records_no_go_preflight(self) -> None:
        payload = gate.build_payload()
        self.assertEqual(payload["schema"], gate.SCHEMA)
        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertEqual(payload["result"], gate.RESULT)
        self.assertEqual(payload["summary"]["local_stwo_d128_gate_value_typed_bytes"], 16_360)
        self.assertEqual(payload["summary"]["local_stwo_dense_substitute_typed_bytes"], 22_576)
        self.assertEqual(payload["summary"]["local_stwo_two_proof_frontier_typed_bytes"], 40_700)
        self.assertEqual(payload["summary"]["nanozk_paper_reported_d128_block_proof_bytes"], 6_900)
        self.assertEqual(payload["summary"]["jstprove_tiny_gemm_scalar_proof_bytes"], 11_645)
        self.assertEqual(payload["summary"]["jstprove_dim2_width_preserving_gemm_proof_bytes"], 71_040)
        self.assertEqual(payload["summary"]["jstprove_dim4_width_preserving_gemm_proof_bytes"], 70_138)
        self.assertEqual(payload["summary"]["smallest_width_preserving_gkr_proof_bytes"], 70_138)
        self.assertEqual(payload["summary"]["tiny_scalar_vs_stwo_gate_value_ratio"], "0.711797")
        self.assertEqual(payload["summary"]["smallest_width_preserving_vs_stwo_gate_value_ratio"], "4.287164")
        self.assertEqual(payload["summary"]["smallest_width_preserving_vs_nanozk_context_ratio"], "10.164928")
        self.assertEqual(payload["summary"]["width_gap_from_largest_checked_gkr_dim_to_d128"], 32)
        self.assertEqual(payload["summary"]["proof_size_comparable_rows"], 0)
        self.assertEqual(payload["mutation_count"], 8)
        self.assertEqual(payload["mutations_rejected"], 8)

    def test_rows_keep_tiny_signal_and_width_preserving_no_go_separate(self) -> None:
        rows = {row["row_id"]: row for row in gate.build_payload()["rows"]}
        self.assertEqual(rows["local_stwo_d128_gate_value_projection"]["primary_value"], 16_360)
        self.assertEqual(rows["local_stwo_d128_rmsnorm_mlp_substitute"]["primary_value"], 22_576)
        self.assertEqual(rows["jstprove_tiny_gemm_scalar"]["primary_value"], 11_645)
        self.assertEqual(rows["jstprove_tiny_gemm_scalar"]["recommendation"], "do_not_promote_tiny_scalar_signal_to_d128_projection")
        self.assertIn("not d128", " ".join(rows["jstprove_tiny_gemm_scalar"]["non_claims"]))
        self.assertEqual(rows["jstprove_width_preserving_gemm_dim_1"]["primary_value"], 11_726)
        self.assertEqual(rows["jstprove_width_preserving_gemm_dim_2"]["primary_value"], 71_040)
        self.assertEqual(rows["jstprove_width_preserving_gemm_dim_4"]["primary_value"], 70_138)
        self.assertEqual(
            rows["jstprove_width_preserving_gemm_dim_4"]["recommendation"],
            "no_go_now_for_jstprove_d128_projection_scaling",
        )
        self.assertEqual(rows["tablero_statement_boundary_guardrail"]["ratio_vs_stwo_gate_value"], "NA")
        self.assertEqual(rows["hybrid_selector_prior_attack_next"]["ratio_vs_stwo_gate_value"], "NA")
        self.assertFalse(any(row["matched_workload"] for row in rows.values()))
        self.assertFalse(any(row["proof_size_comparable"] for row in rows.values()))

    def test_mutation_inventory_is_strict(self) -> None:
        payload = gate.build_payload()
        self.assertEqual([result["name"] for result in payload["mutation_results"]], [name for name, _ in gate.MUTATIONS])
        self.assertTrue(all(result["rejected"] is True for result in payload["mutation_results"]))

    def test_rejects_tiny_gemm_promoted_to_matched_workload(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_promote_tiny_gemm(payload)
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, "matched workload overclaim"):
            gate.validate_payload(payload, final=False)

    def test_rejects_width_preserving_comparability_overclaim(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_promote_dim4_comparable(payload)
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, "proof-size comparability overclaim"):
            gate.validate_payload(payload, final=False)

    def test_rejects_width_preserving_byte_smuggling(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_width_preserving_bytes(payload)
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, "rows drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_recommendation_overclaim(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_recommendation(payload)
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, "summary recommendation drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_global_non_claim_removal(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_remove_non_claim(payload)
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, "global non-claims drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_width_preserving_row_non_claim_removal(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_remove_width_preserving_non_claim(payload)
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, "row-specific non-claim inventory drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_malformed_row_non_claim_with_domain_error(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_malformed_row_non_claim(payload)
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, "non-claim entries must be strings"):
            gate.validate_payload(payload, final=False)

    def test_rejects_source_digest_drift(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_source_digest(payload)
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, "source_artifacts drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_tiny_row_without_d128_non_claim(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        rows = {row["row_id"]: row for row in payload["rows"]}
        rows["jstprove_tiny_gemm_scalar"]["non_claims"] = [
            claim for claim in rows["jstprove_tiny_gemm_scalar"]["non_claims"] if "not d128" not in claim
        ]
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, "row-specific non-claim inventory drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_duplicate_fixture_source_rows(self) -> None:
        parsed, raws = gate.load_sources()
        parsed = deepcopy(parsed)
        results = parsed["shape"]["results"]
        results.append(deepcopy(results[0]))
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, "duplicate fixture: tiny_gemm"):
            gate.base_payload((parsed, raws))

    def test_rejects_duplicate_dimension_source_rows(self) -> None:
        parsed, raws = gate.load_sources()
        parsed = deepcopy(parsed)
        sweep = parsed["shape"]["dimension_sweep"]
        sweep.append(deepcopy(sweep[0]))
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, "duplicate dimension: 1"):
            gate.base_payload((parsed, raws))

    def test_rejects_duplicate_component_source_rows(self) -> None:
        parsed, raws = gate.load_sources()
        parsed = deepcopy(parsed)
        components = parsed["minimal"]["component_rows"]
        components.append(deepcopy(components[1]))
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, "duplicate component: rmsnorm_mlp_residual_substitute"):
            gate.base_payload((parsed, raws))

    def test_rejects_malformed_fixture_source_rows(self) -> None:
        parsed, raws = gate.load_sources()
        parsed = deepcopy(parsed)
        parsed["shape"]["results"].append("not an object")
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, r"shape results row \d+ must be an object"):
            gate.base_payload((parsed, raws))

    def test_rejects_malformed_dimension_source_rows(self) -> None:
        parsed, raws = gate.load_sources()
        parsed = deepcopy(parsed)
        parsed["shape"]["dimension_sweep"].append("not an object")
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, "dimension sweep row 3 must be an object"):
            gate.base_payload((parsed, raws))

    def test_rejects_malformed_component_source_rows(self) -> None:
        parsed, raws = gate.load_sources()
        parsed = deepcopy(parsed)
        parsed["minimal"]["component_rows"].append("not an object")
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, r"component row \d+ must be an object"):
            gate.base_payload((parsed, raws))

    def test_rejects_mutation_inventory_drift(self) -> None:
        payload = gate.build_payload()
        payload["mutation_results"] = deepcopy(payload["mutation_results"])
        payload["mutation_results"].pop()
        payload["mutation_count"] -= 1
        payload["mutations_rejected"] -= 1
        payload["payload_commitment"] = gate.commitment(payload)
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, "mutation result drift"):
            gate.validate_payload(payload)

    def test_payload_commitment_rejects_drift(self) -> None:
        payload = gate.build_payload()
        payload["payload_commitment"] = "blake2b-256:" + "0" * 64
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, "payload commitment drift"):
            gate.validate_payload(payload)

    def test_tsv_columns_are_stable(self) -> None:
        self.assertEqual(gate.tsv_text(gate.build_payload()).splitlines()[0].split("\t"), list(gate.ROW_COLUMNS))

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

    def test_rejects_output_source_overwrite(self) -> None:
        with self.assertRaisesRegex(gate.GkrProjectionPreflightError, "source artifact"):
            gate.write_outputs(gate.build_payload(), gate.JSTPROVE_SHAPE_PROBE, None)

    def test_rejects_wrong_output_suffix(self) -> None:
        payload = gate.build_payload()
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".txt", delete=False) as handle:
            path = gate.pathlib.Path(handle.name)
        try:
            with self.assertRaisesRegex(gate.GkrProjectionPreflightError, "JSON output"):
                gate.write_outputs(payload, path, None)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
