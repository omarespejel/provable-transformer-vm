import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "scripts" / "zkai_native_seq32_attention_mlp_expanded_label_probe_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location("expanded_label_probe_gate", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ExpandedLabelProbeGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()
        cls.payload = cls.gate.build_payload()

    def row(self, variant_id):
        for row in self.payload["proof_object_rows"]:
            if row["variant_id"] == variant_id:
                return row
        self.fail(f"missing row {variant_id}")

    def test_records_no_go_without_promoting_new_probe(self):
        summary = self.payload["frontier_summary"]
        self.assertEqual(
            self.payload["decision"],
            "NO_GO_EXPANDED_LABEL_PROBES_DO_NOT_BEAT_ADJACENT_PROBE_B_FRONTIER",
        )
        self.assertFalse(summary["new_probe_promotable"])
        self.assertEqual(summary["best_new_probe_id"], "fixed_label_probe_b")
        self.assertEqual(summary["best_new_probe_typed_bytes"], 40_476)
        self.assertEqual(summary["best_new_probe_gap_vs_adjacent_probe_b_typed_bytes"], 2_944)

    def test_adjacent_probe_b_remains_frontier(self):
        adjacent_b = self.row("adjacent_label_probe_b")
        self.assertEqual(adjacent_b["typed_bytes"], 37_532)
        self.assertEqual(adjacent_b["json_proof_bytes"], 106_317)
        self.assertEqual(adjacent_b["policy_status"], "current_frontier")

    def test_new_probe_rows_are_bound_to_expected_modes(self):
        expected_modes = {
            "fixed_label_probe_a": "rmsnorm_input_fused_fixed_label_probe_a_v1",
            "fixed_label_probe_b": "rmsnorm_input_fused_fixed_label_probe_b_v1",
            "post_tail_label_probe_a": "rmsnorm_input_fused_post_tail_label_probe_a_v1",
            "post_tail_label_probe_b": "rmsnorm_input_fused_post_tail_label_probe_b_v1",
        }
        for variant_id, mode in expected_modes.items():
            row = self.row(variant_id)
            self.assertEqual(row["adapter_mode"], mode)
            self.assertTrue(row["envelope_sha256"])
            self.assertTrue(row["proof_sha256"])

    def test_path_opening_explains_fixed_label_b_limit(self):
        adjacent_b = self.row("adjacent_label_probe_b")
        fixed_b = self.row("fixed_label_probe_b")
        self.assertEqual(fixed_b["value_bytes"], adjacent_b["value_bytes"])
        self.assertGreater(fixed_b["path_opening_bytes"], adjacent_b["path_opening_bytes"])
        self.assertEqual(fixed_b["typed_delta_vs_adjacent_probe_b"], 2_944)

    def test_mutation_suite_rejects_all_cases(self):
        mutation = self.payload["mutation_result"]
        self.assertTrue(mutation["all_mutations_rejected"])
        self.assertEqual(mutation["mutations_rejected"], len(self.gate.MUTATION_NAMES))
        self.assertEqual(mutation["mutation_names"], list(self.gate.MUTATION_NAMES))

    def test_mutation_function_order_matches_inventory(self):
        self.assertEqual(self.gate.mutation_function_names(), self.gate.MUTATION_NAMES)

    def test_payload_commitment_is_stable(self):
        self.assertEqual(
            self.payload["payload_commitment"],
            self.gate.payload_commitment(self.payload),
        )

    def test_rejects_frontier_promotion(self):
        item = json.loads(json.dumps(self.payload))
        item["frontier_summary"]["new_probe_promotable"] = True
        item["payload_commitment"] = self.gate.payload_commitment(item)
        with self.assertRaisesRegex(self.gate.ExpandedLabelProbeGateError, "frontier_summary drift"):
            self.gate.validate_payload(item)

    def test_rejects_adapter_relabeling(self):
        item = json.loads(json.dumps(self.payload))
        self.row_from(item, "fixed_label_probe_b")["adapter_mode"] = (
            "rmsnorm_input_fused_adjacent_label_probe_b_v1"
        )
        item["payload_commitment"] = self.gate.payload_commitment(item)
        with self.assertRaisesRegex(self.gate.ExpandedLabelProbeGateError, "proof_object_rows drift"):
            self.gate.validate_payload(item)

    def test_rejects_removed_non_claim(self):
        item = json.loads(json.dumps(self.payload))
        item["non_claims"].remove("not a NANOZK proof-size win")
        item["payload_commitment"] = self.gate.payload_commitment(item)
        with self.assertRaisesRegex(self.gate.ExpandedLabelProbeGateError, "non_claims drift"):
            self.gate.validate_payload(item)

    def test_writes_paired_json_and_tsv_outputs(self):
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmp:
            tmp_path = pathlib.Path(tmp)
            json_path = tmp_path / "out.json"
            tsv_path = tmp_path / "out.tsv"
            self.gate.write_outputs(json_path, tsv_path, self.payload)
            loaded = json.loads(json_path.read_text())
            self.assertEqual(loaded["payload_commitment"], self.payload["payload_commitment"])
            lines = tsv_path.read_text().splitlines()
            self.assertEqual(len(lines), 1 + len(self.payload["proof_object_rows"]))
            self.assertIn("payload_commitment", lines[0])

    def test_rejects_output_paths_outside_evidence_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            with self.assertRaisesRegex(
                self.gate.ExpandedLabelProbeGateError,
                "output path escapes evidence dir",
            ):
                self.gate.write_outputs(tmp_path / "out.json", tmp_path / "out.tsv", self.payload)

    def test_rejects_oversized_repo_file_before_json_load(self):
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmp:
            too_large = pathlib.Path(tmp) / "too-large.json"
            too_large.write_bytes(b"{}")
            with self.assertRaisesRegex(
                self.gate.ExpandedLabelProbeGateError,
                "oversized test exceeds max size",
            ):
                self.gate.read_bounded_repo_file(too_large, "oversized test", 1)

    def test_rejects_non_regular_repo_file_before_reading(self):
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmp:
            directory_path = pathlib.Path(tmp) / "not-a-file"
            directory_path.mkdir()
            with self.assertRaisesRegex(
                self.gate.ExpandedLabelProbeGateError,
                "regular file",
            ):
                self.gate.read_bounded_repo_file(directory_path, "directory test", 1024)

    @staticmethod
    def row_from(payload, variant_id):
        for row in payload["proof_object_rows"]:
            if row["variant_id"] == variant_id:
                return row
        raise AssertionError(f"missing row {variant_id}")


if __name__ == "__main__":
    unittest.main()
