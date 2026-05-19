import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "scripts" / "zkai_native_seq32_attention_mlp_adjacent_label_seed_sweep_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location("adjacent_label_seed_sweep_gate", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AdjacentLabelSeedSweepGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()
        cls.payload = cls.gate.build_payload()

    def row(self, variant_id):
        for row in self.payload["proof_object_rows"]:
            if row["variant_id"] == variant_id:
                return row
        self.fail(f"missing row {variant_id}")

    def test_records_seed_sweep_no_go(self):
        summary = self.payload["frontier_summary"]
        self.assertEqual(
            self.payload["decision"],
            "NO_GO_PRE_REGISTERED_ADJACENT_SEEDS_DO_NOT_BEAT_FRONTIER",
        )
        self.assertFalse(summary["seed_promotable"])
        self.assertEqual(summary["best_seed_id"], "adjacent_seed_02")
        self.assertEqual(summary["best_seed_typed_bytes"], 40_268)
        self.assertEqual(summary["best_seed_gap_vs_adjacent_probe_b_typed_bytes"], 2_736)

    def test_seed_inventory_is_pre_registered_and_complete(self):
        seed_policy = self.payload["seed_policy"]
        self.assertTrue(seed_policy["pre_registered"])
        self.assertEqual(seed_policy["seed_ids"], list(self.gate.PRE_REGISTERED_SEED_IDS))
        seed_rows = [
            row["variant_id"]
            for row in self.payload["proof_object_rows"]
            if row["family"] == "pre_registered_seed"
        ]
        self.assertEqual(seed_rows, list(self.gate.PRE_REGISTERED_SEED_IDS))

    def test_seed_distribution_keeps_frontier_as_existing_probe_b(self):
        summary = self.payload["frontier_summary"]
        self.assertEqual(self.row("adjacent_label_probe_b")["typed_bytes"], 37_532)
        self.assertEqual(summary["seed_min_typed_bytes"], 40_268)
        self.assertEqual(summary["seed_median_typed_bytes"], 41_484)
        self.assertEqual(summary["seed_worst_typed_bytes"], 42_156)
        self.assertEqual(summary["seed_span_typed_bytes"], 1_888)

    def test_shape_classes_record_transcript_buckets(self):
        classes = self.payload["shape_classes"]
        self.assertEqual(len(classes), 4)
        class_members = [tuple(item["variant_ids"]) for item in classes]
        self.assertIn(("adjacent_seed_03", "adjacent_seed_04"), class_members)
        self.assertIn(("adjacent_seed_00", "adjacent_seed_01"), class_members)
        self.assertIn(("adjacent_seed_05",), class_members)
        self.assertIn(("adjacent_seed_02",), class_members)

    def test_mutation_suite_rejects_all_cases(self):
        mutation = self.payload["mutation_result"]
        self.assertTrue(mutation["all_mutations_rejected"])
        self.assertEqual(mutation["mutations_rejected"], len(self.gate.MUTATION_NAMES))
        self.assertEqual(mutation["mutation_names"], list(self.gate.MUTATION_NAMES))

    def test_mutation_inventory_guard_is_not_assert_only(self):
        original_names = self.gate.MUTATION_NAMES
        self.gate.MUTATION_NAMES = ("unexpected_mutation_inventory",)
        try:
            with self.assertRaisesRegex(
                self.gate.AdjacentSeedSweepGateError,
                "mutation function inventory drift",
            ):
                self.gate.ensure_mutation_inventory()
        finally:
            self.gate.MUTATION_NAMES = original_names

    def test_payload_commitment_is_stable(self):
        self.assertEqual(
            self.payload["payload_commitment"],
            self.gate.payload_commitment(self.payload),
        )

    def test_rejects_frontier_promotion(self):
        item = json.loads(json.dumps(self.payload))
        item["frontier_summary"]["seed_promotable"] = True
        item["payload_commitment"] = self.gate.payload_commitment(item)
        with self.assertRaisesRegex(self.gate.AdjacentSeedSweepGateError, "frontier_summary drift"):
            self.gate.validate_payload(item)

    def test_rejects_seed_erasure(self):
        item = json.loads(json.dumps(self.payload))
        item["seed_policy"]["seed_ids"].pop()
        item["payload_commitment"] = self.gate.payload_commitment(item)
        with self.assertRaisesRegex(self.gate.AdjacentSeedSweepGateError, "seed_policy drift"):
            self.gate.validate_payload(item)

    def test_rejects_adapter_relabeling(self):
        item = json.loads(json.dumps(self.payload))
        self.row_from(item, "adjacent_seed_02")["adapter_mode"] = (
            "rmsnorm_input_fused_adjacent_label_probe_b_v1"
        )
        item["payload_commitment"] = self.gate.payload_commitment(item)
        with self.assertRaisesRegex(self.gate.AdjacentSeedSweepGateError, "proof_object_rows drift"):
            self.gate.validate_payload(item)

    def test_rejects_removed_non_claim(self):
        item = json.loads(json.dumps(self.payload))
        item["non_claims"].remove("not a NANOZK proof-size win")
        item["payload_commitment"] = self.gate.payload_commitment(item)
        with self.assertRaisesRegex(self.gate.AdjacentSeedSweepGateError, "non_claims drift"):
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
            self.assertIn("record_stream_sha256", lines[0])

    def test_rejects_output_paths_outside_evidence_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            with self.assertRaisesRegex(
                self.gate.AdjacentSeedSweepGateError,
                "output path escapes evidence dir",
            ):
                self.gate.write_outputs(tmp_path / "out.json", tmp_path / "out.tsv", self.payload)

    def test_rejects_non_regular_repo_file_before_reading(self):
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmp:
            directory_path = pathlib.Path(tmp) / "not-a-file"
            directory_path.mkdir()
            with self.assertRaisesRegex(
                self.gate.AdjacentSeedSweepGateError,
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
