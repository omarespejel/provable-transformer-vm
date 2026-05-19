import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = (
    ROOT
    / "scripts"
    / "zkai_native_seq32_attention_mlp_predecommit_opening_policy_gate.py"
)


def load_gate():
    spec = importlib.util.spec_from_file_location("predecommit_opening_policy_gate", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PredecommitOpeningPolicyGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()
        cls.payload = cls.gate.build_payload()

    def row(self, variant_id):
        for row in self.payload["policy_rows"]:
            if row["variant_id"] == variant_id:
                return row
        self.fail(f"missing policy row {variant_id}")

    def evaluated_row(self, variant_id):
        for row in self.payload["evaluation_rows"]:
            if row["variant_id"] == variant_id:
                return row
        self.fail(f"missing evaluation row {variant_id}")

    def test_payload_records_narrow_claim_not_true_predecommit_go(self):
        self.assertEqual(
            self.payload["decision"],
            "NARROW_CLAIM_CURRENT_STWO_WRAPPER_EXPOSES_QUERY_GEOMETRY_AFTER_PROVE_EX",
        )
        api = self.payload["api_stage_audit"]
        self.assertFalse(api["predecommit_control_available"])
        self.assertTrue(api["post_transcript_pre_accounting_policy_available"])
        self.assertEqual(
            api["current_api_control_status"],
            "NO_TRUE_PREDECOMMIT_CONTROL_HOOK_IN_CURRENT_WRAPPER",
        )
        self.assertFalse(self.payload["evaluation"]["true_predecommit_go_gate_satisfied"])

    def test_policy_selects_probe_b_without_final_accounting_inputs(self):
        policy = self.payload["policy_input"]
        self.assertFalse(policy["uses_final_accounting_as_input"])
        self.assertFalse(policy["uses_row_identity_as_input"])
        self.assertFalse(policy["uses_envelope_or_proof_bytes_as_input"])
        self.assertEqual(
            set(policy["policy_feature_keys"]),
            {"unique_query_count", "query_location_span", "min_pairwise_query_gap"},
        )
        probe_b = self.row("adjacent_label_probe_b")
        self.assertTrue(probe_b["selected_without_final_accounting"])
        self.assertEqual(probe_b["predicted_path_opening_bytes"], 16_560)
        self.assertEqual(probe_b["policy_input_features"]["query_location_span"], 16_618)
        self.assertEqual(probe_b["policy_input_features"]["min_pairwise_query_gap"], 5_969)

    def test_final_evaluation_is_recorded_only_after_selection(self):
        evaluation = self.payload["evaluation"]
        self.assertEqual(evaluation["selected_variant_id"], "adjacent_label_probe_b")
        self.assertEqual(evaluation["selected_final_typed_bytes"], 37_532)
        self.assertEqual(evaluation["selected_final_path_opening_bytes"], 16_560)
        self.assertEqual(evaluation["saving_vs_current_champion_typed_bytes"], 4_536)
        self.assertEqual(evaluation["saving_vs_current_champion_share"], "10.7825%")
        self.assertEqual(evaluation["saving_vs_best_pre_registered_seed_typed_bytes"], 2_736)
        self.assertEqual(self.evaluated_row("adjacent_label_probe_b")["final_value_bytes"], 20_924)
        self.assertEqual(
            self.evaluated_row("adjacent_label_probe_b")["final_path_opening_bytes"],
            self.gate.BEST_PATH_OPENING_BYTES,
        )

    def test_reproducibility_metadata_records_backend_and_counts(self):
        metadata = self.payload["reproducibility_metadata"]
        self.assertEqual(
            metadata["selected_backend_version"],
            "stwo-native-seq32-attention-mlp-single-proof-object-rmsnorm-input-fused-adjacent-fixed-v1",
        )
        self.assertEqual(metadata["policy_row_count"], 9)
        self.assertEqual(metadata["fri_query_count_per_row"], 3)
        self.assertEqual(metadata["mutation_step_count"], len(self.gate.MUTATION_NAMES))
        self.assertEqual(metadata["unittest_step_count"], self.gate.EXPECTED_UNITTEST_STEP_COUNT)
        self.assertEqual(metadata["local_release_gate_step_count"], 14)

    def test_pinned_unittest_count_matches_loaded_suite(self):
        count = unittest.TestLoader().loadTestsFromTestCase(type(self)).countTestCases()
        self.assertEqual(count, self.gate.EXPECTED_UNITTEST_STEP_COUNT)
        self.assertEqual(count, self.payload["reproducibility_metadata"]["unittest_step_count"])

    def test_source_stage_markers_are_pinned(self):
        markers = self.payload["api_stage_audit"]["source_markers"]
        self.assertTrue(markers["sampler_calls_full_extended_proof"])
        self.assertTrue(markers["sampler_reads_extended_aux_query_locations"])
        self.assertTrue(markers["prove_single_extended_delegates_to_stwo_prove_ex"])
        self.assertTrue(markers["sampler_boundary_names_extended_aux_not_predecommit_hook"])
        self.assertIn("split query drawing", self.payload["api_stage_audit"]["required_hook"])

    def test_all_mutations_rejected(self):
        mutation = self.payload["mutation_result"]
        self.assertTrue(mutation["all_mutations_rejected"])
        self.assertEqual(mutation["mutations_rejected"], len(self.gate.MUTATION_NAMES))
        self.assertEqual(mutation["mutation_names"], list(self.gate.MUTATION_NAMES))

    def test_committed_evidence_contains_integrity_fields(self):
        evidence = json.loads(self.gate.JSON_OUT.read_text())
        self.assertEqual(evidence["payload_commitment"], self.payload["payload_commitment"])
        self.assertEqual(evidence["mutation_result"], self.payload["mutation_result"])
        self.gate.validate_payload(evidence)

    def test_rejects_predecommit_overclaim(self):
        item = self.gate.build_payload_without_mutations()
        item["api_stage_audit"]["predecommit_control_available"] = True
        with self.assertRaisesRegex(
            self.gate.PredecommitOpeningPolicyGateError,
            "base payload drift",
        ):
            self.gate.validate_base_payload(item)

    def test_rejects_selected_path_opening_drift(self):
        item = self.gate.build_payload_without_mutations()
        self.evaluated_row_from(item, "adjacent_label_probe_b")[
            "final_path_opening_bytes"
        ] = 19_296
        with self.assertRaisesRegex(
            self.gate.PredecommitOpeningPolicyGateError,
            "path-opening drift",
        ):
            self.gate.validate_base_payload(item)

    def test_rejects_final_accounting_as_policy_input(self):
        item = self.gate.build_payload_without_mutations()
        item["policy_input"]["uses_final_accounting_as_input"] = True
        with self.assertRaisesRegex(
            self.gate.PredecommitOpeningPolicyGateError,
            "base payload drift",
        ):
            self.gate.validate_base_payload(item)

    def test_payload_commitment_and_tsv_are_stable(self):
        payload_a = self.gate.build_payload()
        payload_b = self.gate.build_payload()
        self.assertEqual(payload_a["payload_commitment"], self.gate.payload_commitment(payload_a))
        self.assertEqual(payload_a["payload_commitment"], payload_b["payload_commitment"])
        tsv = self.gate.render_tsv(payload_a)
        self.assertEqual(tsv, self.gate.render_tsv(payload_b))
        self.assertIn(
            "adjacent_label_probe_b\trmsnorm_input_fused_adjacent_label_probe_b_v1",
            tsv,
        )
        self.assertIn("\ttrue\t16560\t16560\t37532\t", tsv)

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
            self.assertEqual(len(lines), 1 + len(self.payload["policy_rows"]))

    def evaluated_row_from(self, payload, variant_id):
        for row in payload["evaluation_rows"]:
            if row["variant_id"] == variant_id:
                return row
        self.fail(f"missing evaluation row {variant_id}")


if __name__ == "__main__":
    unittest.main()
