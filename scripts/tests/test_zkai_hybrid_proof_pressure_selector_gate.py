import json
import tempfile
import unittest
from copy import deepcopy

from scripts import zkai_hybrid_proof_pressure_selector_gate as gate


class HybridProofPressureSelectorGateTest(unittest.TestCase):
    def test_build_payload_records_selector_inventory(self) -> None:
        payload = gate.build_payload()
        self.assertEqual(payload["schema"], gate.SCHEMA)
        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertEqual(payload["result"], gate.RESULT)
        self.assertEqual(payload["summary"]["selector_row_count"], 8)
        self.assertEqual(payload["summary"]["attack_next_count"], 2)
        self.assertEqual(payload["summary"]["no_go_now_count"], 2)
        self.assertEqual(payload["summary"]["proof_size_comparable_rows"], 0)
        self.assertEqual(payload["summary"]["claim_audit_proof_size_comparable_rows"], 0)
        self.assertEqual(payload["summary"]["stwo_two_proof_frontier_typed_bytes"], 40_700)
        self.assertEqual(payload["summary"]["nanozk_paper_reported_bytes"], 6_900)
        self.assertEqual(payload["summary"]["gap_to_nanozk_paper_reported_bytes"], 33_800)
        self.assertEqual(payload["summary"]["gkr_tiny_gemm_proof_bytes"], 11_645)
        self.assertEqual(payload["summary"]["gkr_tiny_gemm_vs_stwo_dense_substitute_ratio"], "0.515813")
        self.assertEqual(payload["summary"]["gkr_tiny_gemm_vs_stwo_frontier_ratio"], "0.286118")
        self.assertEqual(payload["mutation_count"], 12)
        self.assertEqual(payload["mutations_rejected"], 12)

    def test_selector_rows_keep_good_and_bad_routes_explicit(self) -> None:
        rows = {row["route_id"]: row for row in gate.build_payload()["selector_rows"]}
        self.assertEqual(rows["local_stwo_two_proof_frontier"]["ratio_vs_nanozk_context"], "5.898551")
        self.assertEqual(rows["gkr_dense_linear_scaling_candidate"]["selector_decision"], "ATTACK_NEXT_UNMATCHED_DENSE_LINEAR_SCALING")
        self.assertEqual(rows["gkr_dense_linear_scaling_candidate"]["ratio_vs_nanozk_context"], "1.687681")
        self.assertEqual(rows["gkr_residual_add_no_go_now"]["selector_decision"], "NO_GO_NOW_TINY_RESIDUAL_SHAPE_HEAVIER")
        self.assertEqual(rows["gkr_residual_add_no_go_now"]["ratio_vs_stwo_frontier"], "1.377248")
        self.assertEqual(rows["gkr_layernorm_no_go_now"]["selector_decision"], "NO_GO_NOW_TINY_NORM_SHAPE_HEAVIER")
        self.assertEqual(rows["native_d128_block_object_blocker"]["selector_decision"], "ATTACK_NEXT_NATIVE_BLOCK_OBJECT")
        self.assertEqual(rows["tablero_statement_boundary_guardrail"]["ratio_vs_stwo_frontier"], "NA")
        self.assertFalse(any(row["proof_size_comparable"] for row in rows.values()))
        for row in rows.values():
            self.assertTrue(set(gate.NON_CLAIMS).issubset(set(row["non_claims"])))

    def test_mutation_inventory_is_strict(self) -> None:
        payload = gate.build_payload()
        self.assertEqual([result["name"] for result in payload["mutation_results"]], [name for name, _ in gate.MUTATIONS])
        self.assertTrue(all(result["accepted"] is False for result in payload["mutation_results"]))

    def test_rejects_gkr_dense_promoted_to_matched_native(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_gkr_dense_promoted(payload)
        with self.assertRaisesRegex(gate.HybridSelectorError, "GKR fixture promoted"):
            gate.validate_payload(payload, final=False)

    def test_rejects_statement_boundary_ratio(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_statement_boundary_ratio(payload)
        with self.assertRaisesRegex(gate.HybridSelectorError, "statement artifact promoted"):
            gate.validate_payload(payload, final=False)

    def test_rejects_any_route_comparable(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_any_route_comparable(payload)
        with self.assertRaisesRegex(gate.HybridSelectorError, "proof-size comparability overclaim"):
            gate.validate_payload(payload, final=False)

    def test_rejects_nanozk_paper_context_promoted(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_nanozk_matched(payload)
        with self.assertRaisesRegex(gate.HybridSelectorError, "NANOZK paper context promoted"):
            gate.validate_payload(payload, final=False)

    def test_rejects_missing_route_non_claim(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_remove_row_non_claim(payload)
        with self.assertRaisesRegex(gate.HybridSelectorError, "missing non-claims"):
            gate.validate_payload(payload, final=False)

    def test_rejects_no_attack_next_route(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_remove_attack_next(payload)
        with self.assertRaisesRegex(gate.HybridSelectorError, "no attack-next"):
            gate.validate_payload(payload, final=False)

    def test_rejects_no_no_go_now_route(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_remove_no_go_now(payload)
        with self.assertRaisesRegex(gate.HybridSelectorError, "no no-go-now"):
            gate.validate_payload(payload, final=False)

    def test_rejects_claim_audit_comparable_drift(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_claim_audit_comparable(payload)
        with self.assertRaisesRegex(gate.HybridSelectorError, "claim audit proof comparable rows drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_summary_route_drift(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_summary_attack_route_drift(payload)
        with self.assertRaisesRegex(gate.HybridSelectorError, "attack-next routes drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_stwo_frontier_drift(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_stwo_frontier_drift(payload)
        with self.assertRaisesRegex(gate.HybridSelectorError, "summary frontier drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_selector_semantic_drift_even_when_summary_is_unchanged(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        payload["selector_rows"][0]["next_action"] = "quietly_promote_unchecked_route"
        with self.assertRaisesRegex(gate.HybridSelectorError, "canonical selector row drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_tablero_pressure_drift_even_when_type_is_valid(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        rows = {row["route_id"]: row for row in payload["selector_rows"]}
        rows["tablero_statement_boundary_guardrail"]["primary_pressure"] += 1
        with self.assertRaisesRegex(gate.HybridSelectorError, "canonical selector row drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_source_artifact_digest_drift(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_source_artifact_digest(payload)
        with self.assertRaisesRegex(gate.HybridSelectorError, "source artifact descriptor drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_source_artifact_path_outside_allowlist(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        payload["source_artifacts"][0]["path"] = "docs/engineering/evidence/not-a-source.json"
        with self.assertRaisesRegex(gate.HybridSelectorError, "source artifact path outside allowlist"):
            gate.validate_payload(payload, final=False)

    def test_rejects_duplicate_source_artifact_path(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        payload["source_artifacts"][1] = dict(payload["source_artifacts"][0])
        with self.assertRaisesRegex(gate.HybridSelectorError, "duplicate source artifact path"):
            gate.validate_payload(payload, final=False)

    def test_rejects_validation_command_drift(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        payload["validation_commands"] = payload["validation_commands"][:-1]
        with self.assertRaisesRegex(gate.HybridSelectorError, "validation command inventory drift"):
            gate.validate_payload(payload, final=False)

    def test_payload_commitment_rejects_drift(self) -> None:
        payload = gate.build_payload()
        gate.mutate_payload_commitment(payload)
        with self.assertRaisesRegex(gate.HybridSelectorError, "payload commitment drift"):
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

    def test_write_outputs_creates_nested_evidence_directory(self) -> None:
        payload = gate.build_payload()
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix="tmp-hybrid-selector-test-") as temp_dir:
            nested_dir = gate.pathlib.Path(temp_dir)
            json_path = nested_dir / "selector.json"
            tsv_path = nested_dir / "selector.tsv"
            gate.write_outputs(payload, json_path, tsv_path)
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8")), payload)
            self.assertTrue(tsv_path.exists())

    def test_rejects_source_overwrite(self) -> None:
        with self.assertRaisesRegex(gate.HybridSelectorError, "source artifact"):
            gate.write_outputs(gate.build_payload(), gate.CLAIM_AUDIT, None)

    def test_rejects_wrong_output_suffix(self) -> None:
        payload = gate.build_payload()
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".txt", delete=False) as handle:
            path = gate.pathlib.Path(handle.name)
        try:
            with self.assertRaisesRegex(gate.HybridSelectorError, "JSON output"):
                gate.write_outputs(payload, path, None)
        finally:
            path.unlink(missing_ok=True)

    def test_rejects_mutation_inventory_drift(self) -> None:
        payload = gate.build_payload()
        payload["mutation_results"] = deepcopy(payload["mutation_results"])
        payload["mutation_results"].pop()
        payload["mutation_count"] -= 1
        payload["mutations_rejected"] -= 1
        payload["payload_commitment"] = gate.commitment({key: value for key, value in payload.items() if key != "payload_commitment"})
        with self.assertRaisesRegex(gate.HybridSelectorError, "mutation inventory drift"):
            gate.validate_payload(payload)

    def test_rejects_non_dict_mutation_inventory_entry(self) -> None:
        payload = gate.build_payload()
        payload["mutation_results"] = deepcopy(payload["mutation_results"])
        payload["mutation_results"][-1] = "not-a-dict"
        payload["payload_commitment"] = gate.commitment({key: value for key, value in payload.items() if key != "payload_commitment"})
        with self.assertRaisesRegex(gate.HybridSelectorError, "mutation inventory drift"):
            gate.validate_payload(payload)


if __name__ == "__main__":
    unittest.main()
