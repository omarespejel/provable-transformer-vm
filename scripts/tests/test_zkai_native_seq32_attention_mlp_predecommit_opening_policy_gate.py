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
        self.assertEqual(mutation["mutations_rejected"], self.gate.EXPECTED_MUTATION_COUNT)
        self.assertEqual(mutation["mutation_names"], list(self.gate.MUTATION_NAMES))

    def test_rejects_predecommit_overclaim(self):
        item = self.gate.build_payload_without_mutations()
        item["api_stage_audit"]["predecommit_control_available"] = True
        with self.assertRaisesRegex(
            self.gate.PredecommitOpeningPolicyGateError,
            "base payload drift",
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


if __name__ == "__main__":
    unittest.main()
