import copy
import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "scripts" / "zkai_stwo_query_preview_split_prototype_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location(
        "stwo_query_preview_split_prototype_gate",
        GATE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StwoQueryPreviewSplitPrototypeGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()
        try:
            cls.payload = cls.gate.build_payload()
        except cls.gate.hook_gate.BoundedStwoQueryPolicyHookGateError as err:
            if "Stwo 2.2.0 source is not available" in str(err):
                raise unittest.SkipTest(str(err)) from err
            raise

    def route(self, route_id):
        return self.gate.route(self.payload, route_id)

    def test_payload_records_preview_split_narrow_no_go(self):
        self.assertEqual(
            self.payload["decision"],
            "NARROW_CLAIM_QUERY_PREVIEW_SPLIT_IS_API_FEASIBLE_NOT_SOUND_LABEL_POLICY",
        )
        self.assertEqual(
            self.payload["result"],
            "NO_GO_SOUND_QUERY_GEOMETRY_CONTROL_WITHOUT_GRINDING_OR_POLICY_COMMITMENT",
        )
        assessment = self.payload["preview_split_assessment"]
        self.assertTrue(assessment["api_preview_split_feasible"])
        self.assertFalse(assessment["sound_label_policy_feasible_now"])
        self.assertFalse(assessment["regenerate_proof_size_frontier_now"])
        self.assertEqual(assessment["proof_size_delta_typed_bytes"], 0)

    def test_source_audit_pins_existing_stwo_query_flow(self):
        markers = self.payload["source_audit"]["stwo_markers"]
        self.assertTrue(markers["fri_decommit_draws_queries_from_channel"])
        self.assertTrue(markers["fri_decommit_uses_decommit_on_queries"])
        self.assertTrue(markers["fri_decommit_on_queries_is_public"])
        self.assertTrue(markers["pcs_trace_decommit_uses_query_positions"])
        self.assertTrue(markers["verifier_samples_query_positions_from_channel"])

    def test_core_query_markers_pin_transcript_derived_queries(self):
        markers = self.payload["source_audit"]["core_query_markers"]
        self.assertTrue(markers["draw_queries_is_public"])
        self.assertTrue(markers["draw_queries_reads_transcript_words"])
        self.assertTrue(markers["draw_queries_masks_domain"])
        self.assertTrue(markers["queries_new_sorts_and_dedups"])

    def test_stage_order_keeps_preview_after_commitments_before_decommitments(self):
        stages = {item["stage_id"]: item for item in self.payload["stage_order"]}
        self.assertEqual(stages["trace_commitments"]["relative_to_query_preview"], "before")
        self.assertEqual(
            stages["fri_commitment_and_pow_mix"]["relative_to_query_preview"],
            "before",
        )
        self.assertEqual(stages["canonical_query_draw"]["relative_to_query_preview"], "preview_point")
        self.assertEqual(stages["fri_decommit_on_queries"]["relative_to_query_preview"], "after")
        self.assertEqual(stages["trace_tree_decommit"]["relative_to_query_preview"], "after")
        self.assertFalse(stages["trace_commitments"]["can_change_after_preview"])

    def test_preview_only_route_is_feasible_but_not_label_control(self):
        preview = self.route("preview_only_split")
        self.assertEqual(preview["status"], "FEASIBLE_API_PATCH")
        self.assertTrue(preview["requires_prover_patch"])
        self.assertFalse(preview["requires_verifier_patch"])
        self.assertFalse(preview["external_query_choice"])
        self.assertTrue(preview["preview_before_fri_decommit"])
        self.assertTrue(preview["preview_before_trace_decommit"])
        self.assertFalse(preview["can_change_committed_trace_after_preview"])
        self.assertFalse(preview["can_claim_probe_b_control"])

    def test_policy_override_and_grinding_routes_are_bounded(self):
        policy = self.route("policy_commitment_mix")
        override = self.route("external_query_override")
        grinding = self.route("transcript_grinding_search")
        self.assertTrue(policy["requires_verifier_patch"])
        self.assertFalse(policy["external_query_choice"])
        self.assertEqual(override["status"], "REJECTED_UNSOUND")
        self.assertTrue(override["external_query_choice"])
        self.assertTrue(override["requires_security_budget"])
        self.assertTrue(grinding["requires_security_budget"])
        self.assertFalse(grinding["can_claim_probe_b_control"])

    def test_current_metric_anchor_is_derived_from_previous_gate(self):
        self.assertEqual(
            self.payload["current_metric_anchor"],
            self.gate.hook_gate.predecommit_metric_anchor(),
        )
        anchor = self.payload["current_metric_anchor"]
        self.assertEqual(anchor["selected_row"], "adjacent_label_probe_b")
        self.assertEqual(anchor["typed_bytes"], 37_532)
        self.assertEqual(anchor["matched_two_proof_frontier_typed_bytes"], 47_188)
        self.assertEqual(anchor["saving_vs_two_proof_frontier_typed_bytes"], 9_656)

    def test_forbidden_policy_inputs_remain_forbidden(self):
        forbidden = self.payload["forbidden_policy_inputs"]
        self.assertTrue(forbidden["final_envelope_json"])
        self.assertTrue(forbidden["final_proof_bytes"])
        self.assertTrue(forbidden["post_decommitment_aux_as_selector"])
        self.assertTrue(forbidden["unbounded_abort_and_retry"])

    def test_source_artifacts_include_core_queries_digest(self):
        artifact = self.gate.find_source_artifact(self.payload, "stwo_2_2_core_queries")
        self.assertEqual(artifact["sha256"], self.gate.EXPECTED_CORE_QUERIES_SHA256)
        self.assertEqual(
            artifact["path"],
            "stwo-2.2.0/src/core/queries.rs",
        )

    def test_all_mutations_rejected(self):
        mutation = self.payload["mutation_result"]
        self.assertTrue(mutation["all_mutations_rejected"])
        self.assertEqual(mutation["mutations_rejected"], len(self.gate.MUTATION_NAMES))
        self.assertEqual(mutation["mutation_names"], list(self.gate.MUTATION_NAMES))

    def test_validate_mutation_result_rejects_malformed_case(self):
        bad_result = copy.deepcopy(self.payload["mutation_result"])
        bad_result["cases"][0] = "not-a-mutation-case"
        with self.assertRaisesRegex(
            self.gate.StwoQueryPreviewSplitPrototypeGateError,
            "mutation case schema drift",
        ):
            self.gate.validate_mutation_result(bad_result)

    def test_missing_route_and_artifact_helpers_reject(self):
        with self.assertRaisesRegex(
            self.gate.StwoQueryPreviewSplitPrototypeGateError,
            "route missing",
        ):
            self.gate.route(self.payload, "missing-route")
        with self.assertRaisesRegex(
            self.gate.StwoQueryPreviewSplitPrototypeGateError,
            "source artifact missing",
        ):
            self.gate.find_source_artifact(self.payload, "missing-artifact")

    def test_pinned_unittest_count_matches_loaded_suite(self):
        count = unittest.TestLoader().loadTestsFromTestCase(type(self)).countTestCases()
        self.assertEqual(count, self.gate.EXPECTED_UNITTEST_STEP_COUNT)
        self.assertEqual(count, self.payload["reproducibility_metadata"]["unittest_step_count"])

    def test_committed_evidence_contains_integrity_fields(self):
        evidence = json.loads(self.gate.JSON_OUT.read_text())
        self.assertEqual(evidence["payload_commitment"], self.payload["payload_commitment"])
        self.assertEqual(evidence["mutation_result"], self.payload["mutation_result"])
        self.gate.validate_payload(evidence)

    def test_payload_commitment_and_tsv_are_stable(self):
        payload_a = self.gate.build_payload()
        payload_b = self.gate.build_payload()
        self.assertEqual(payload_a["payload_commitment"], self.gate.payload_commitment(payload_a))
        self.assertEqual(payload_a["payload_commitment"], payload_b["payload_commitment"])
        tsv = self.gate.render_tsv(payload_a)
        self.assertEqual(tsv, self.gate.render_tsv(payload_b))
        self.assertIn("preview_only_split\tFEASIBLE_API_PATCH", tsv)
        self.assertIn("external_query_override\tREJECTED_UNSOUND", tsv)

    def test_writes_paired_json_and_tsv_outputs(self):
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmp:
            tmp_path = pathlib.Path(tmp)
            json_path = tmp_path / "out.json"
            tsv_path = tmp_path / "out.tsv"
            self.gate.write_outputs(json_path, tsv_path, self.payload)
            loaded = json.loads(json_path.read_text())
            self.assertEqual(loaded["payload_commitment"], self.payload["payload_commitment"])
            lines = tsv_path.read_text().splitlines()
            self.assertEqual(lines[0], "\t".join(self.gate.TSV_COLUMNS))
            self.assertEqual(len(lines), 1 + len(self.payload["prototype_routes"]))

    def test_base_payload_rejects_overclaim(self):
        item = self.gate.build_payload_without_mutations()
        item["preview_split_assessment"]["sound_label_policy_feasible_now"] = True
        with self.assertRaisesRegex(
            self.gate.StwoQueryPreviewSplitPrototypeGateError,
            "base payload drift",
        ):
            self.gate.validate_base_payload(item)

    def test_payload_commitment_drift_rejects(self):
        item = copy.deepcopy(self.payload)
        item["payload_commitment"] = "blake2b-256:" + ("0" * 64)
        with self.assertRaisesRegex(
            self.gate.StwoQueryPreviewSplitPrototypeGateError,
            "payload commitment drift",
        ):
            self.gate.validate_payload(item)


if __name__ == "__main__":
    unittest.main()
