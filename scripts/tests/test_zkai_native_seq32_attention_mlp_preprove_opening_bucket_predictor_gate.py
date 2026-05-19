import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "scripts" / "zkai_native_seq32_attention_mlp_preprove_opening_bucket_predictor_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location("preprove_opening_bucket_predictor_gate", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PreproveOpeningBucketPredictorGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()
        cls.payload = cls.gate.build_payload()

    def preprove_row(self, variant_id):
        for row in self.payload["preprove_inventory_rows"]:
            if row["variant_id"] == variant_id:
                return row
        self.fail(f"missing preprove row {variant_id}")

    def final_row(self, variant_id):
        for row in self.payload["final_accounting_join_rows"]:
            if row["variant_id"] == variant_id:
                return row
        self.fail(f"missing final row {variant_id}")

    def test_payload_records_no_go_predictor_boundary(self):
        assessment = self.payload["predictor_assessment"]
        self.assertEqual(
            self.payload["decision"],
            "NO_GO_SOURCE_VISIBLE_PREPROVE_INVENTORY_DOES_NOT_PREDICT_PROBE_B_BUCKET",
        )
        self.assertFalse(assessment["source_exposed_bucket_predictor"])
        self.assertEqual(assessment["unique_preprove_structural_signatures"], 1)
        self.assertEqual(assessment["distinct_final_path_opening_buckets"], 5)
        self.assertEqual(assessment["best_bucket_variant_id"], "adjacent_label_probe_b")
        self.assertEqual(assessment["best_bucket_path_opening_bytes"], 16_560)
        self.assertEqual(assessment["best_pre_registered_seed_id"], "adjacent_seed_02")
        self.assertEqual(assessment["gap_vs_best_seed_path_opening_bytes"], 2_736)
        self.assertEqual(assessment["value_bytes_constant"], 20_924)

    def test_preprove_rows_do_not_leak_final_accounting(self):
        forbidden = {
            "typed_bytes",
            "json_proof_bytes",
            "path_opening_bytes",
            "value_bytes",
            "groups",
            "record_stream_sha256",
            "envelope_sha256",
            "proof_sha256",
        }
        for row in self.payload["preprove_inventory_rows"]:
            self.assertFalse(forbidden.intersection(row))
            self.assertEqual(
                row["source_visible_scope"],
                "input_json_before_prove_no_envelope_no_accounting_no_proof_bytes",
            )

    def test_all_rows_share_structural_signature_but_final_buckets_diverge(self):
        structural_signatures = {
            row["structural_signature"] for row in self.payload["preprove_inventory_rows"]
        }
        final_buckets = {
            row["path_opening_bytes"] for row in self.payload["final_accounting_join_rows"]
        }
        self.assertEqual(len(structural_signatures), 1)
        self.assertEqual(len(self.payload["preprove_inventory_rows"]), 9)
        self.assertEqual(len(final_buckets), 5)
        self.assertEqual(max(final_buckets) - min(final_buckets), 4_624)

    def test_row_identity_hashes_are_unique_but_rejected_as_predictors(self):
        signatures = {
            row["row_identity_signature"] for row in self.payload["preprove_inventory_rows"]
        }
        self.assertEqual(len(signatures), len(self.payload["preprove_inventory_rows"]))
        self.assertTrue(self.payload["predictor_assessment"]["row_identity_signatures_unique"])
        rejected = [
            row
            for row in self.payload["predictor_assessment"]["candidate_predictors"]
            if row["candidate"] == "adapter_mode_or_statement_commitment_lookup"
        ]
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["status"], "REJECTED_AS_POST_HOC_ROW_IDENTITY_LOOKUP")
        self.assertFalse(self.payload["preprove_inventory_policy"]["row_identity_hashes_are_predictors"])

    def test_final_join_rows_pin_expected_buckets(self):
        self.assertEqual(self.final_row("fixed_adjacent_layout")["path_opening_bytes"], 21_184)
        self.assertEqual(self.final_row("adjacent_label_probe_a")["path_opening_bytes"], 19_360)
        self.assertEqual(self.final_row("adjacent_label_probe_b")["path_opening_bytes"], 16_560)
        self.assertEqual(self.final_row("adjacent_seed_02")["path_opening_bytes"], 19_296)
        self.assertEqual(self.final_row("adjacent_seed_05")["path_opening_bytes"], 19_360)
        self.assertEqual(
            {row["value_bytes"] for row in self.payload["final_accounting_join_rows"]},
            {20_924},
        )

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
                self.gate.PreproveOpeningBucketPredictorGateError,
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

    def test_rejects_source_predictor_promotion(self):
        item = json.loads(json.dumps(self.payload))
        item["predictor_assessment"]["source_exposed_bucket_predictor"] = True
        item["payload_commitment"] = self.gate.payload_commitment(item)
        with self.assertRaisesRegex(
            self.gate.PreproveOpeningBucketPredictorGateError,
            "predictor_assessment drift",
        ):
            self.gate.validate_payload(item)

    def test_rejects_final_accounting_leak_in_preprove_row(self):
        item = json.loads(json.dumps(self.payload))
        self.row_from(item["preprove_inventory_rows"], "adjacent_label_probe_b")[
            "path_opening_bytes"
        ] = 16_560
        item["payload_commitment"] = self.gate.payload_commitment(item)
        with self.assertRaisesRegex(
            self.gate.PreproveOpeningBucketPredictorGateError,
            "preprove_inventory_rows drift",
        ):
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
            self.assertEqual(len(lines), 1 + len(self.payload["preprove_inventory_rows"]))
            self.assertEqual(lines[0], "\t".join(self.gate.TSV_COLUMNS))
            final_by_variant = {
                row["variant_id"]: row for row in self.payload["final_accounting_join_rows"]
            }
            for line in lines[1:]:
                columns = dict(zip(self.gate.TSV_COLUMNS, line.split("\t"), strict=True))
                variant_id = columns["variant_id"]
                self.assertIn(variant_id, final_by_variant)
                self.assertEqual(
                    columns["final_typed_bytes"],
                    str(final_by_variant[variant_id]["typed_bytes"]),
                )

    def test_rejects_output_paths_outside_evidence_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            with self.assertRaisesRegex(
                self.gate.PreproveOpeningBucketPredictorGateError,
                "inside evidence dir",
            ):
                self.gate.write_outputs(tmp_path / "out.json", tmp_path / "out.tsv", self.payload)

    def test_rejects_symlink_output_path(self):
        with (
            tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmp,
            tempfile.TemporaryDirectory() as outside_tmp,
        ):
            tmp_path = pathlib.Path(tmp)
            outside = pathlib.Path(outside_tmp) / "outside.json"
            outside.write_text("{}")
            symlink_path = tmp_path / "out.json"
            symlink_path.symlink_to(outside)
            with self.assertRaisesRegex(
                self.gate.PreproveOpeningBucketPredictorGateError,
                "symlink",
            ):
                self.gate.write_outputs(symlink_path, tmp_path / "out.tsv", self.payload)

    def test_rejects_symlinked_output_parent(self):
        with (
            tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmp,
            tempfile.TemporaryDirectory() as outside_tmp,
        ):
            tmp_path = pathlib.Path(tmp)
            outside = pathlib.Path(outside_tmp)
            linkdir = tmp_path / "linkdir"
            linkdir.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(
                self.gate.PreproveOpeningBucketPredictorGateError,
                "traverse symlinks",
            ):
                self.gate.write_outputs(linkdir / "out.json", tmp_path / "out.tsv", self.payload)

    def test_rejects_directory_output_target(self):
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmp:
            tmp_path = pathlib.Path(tmp)
            directory_target = tmp_path / "out.json"
            directory_target.mkdir()
            with self.assertRaisesRegex(
                self.gate.PreproveOpeningBucketPredictorGateError,
                "non-symlink file",
            ):
                self.gate.write_outputs(directory_target, tmp_path / "out.tsv", self.payload)

    @staticmethod
    def row_from(rows, variant_id):
        for row in rows:
            if row["variant_id"] == variant_id:
                return row
        raise AssertionError(f"missing row {variant_id}")


if __name__ == "__main__":
    unittest.main()
