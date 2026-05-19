import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "scripts" / "zkai_native_seq32_attention_mlp_adjacent_probe_b_bucket_attribution_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location("adjacent_probe_b_bucket_attribution_gate", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AdjacentProbeBBucketAttributionGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()
        cls.payload = cls.gate.build_payload()

    def row(self, variant_id):
        for row in self.payload["proof_object_rows"]:
            if row["variant_id"] == variant_id:
                return row
        self.fail(f"missing row {variant_id}")

    def comparison(self, variant_id):
        for row in self.payload["comparisons_vs_probe_b"]:
            if row["variant_id"] == variant_id:
                return row
        self.fail(f"missing comparison {variant_id}")

    def test_records_narrow_attribution_not_frontier_claim(self):
        bucket = self.payload["bucket_attribution"]
        self.assertEqual(
            self.payload["decision"],
            "NARROW_CLAIM_PATH_OPENING_BUCKET_ATTRIBUTED_NO_SOURCE_PREDICTOR",
        )
        self.assertEqual(bucket["frontier_variant_id"], "adjacent_label_probe_b")
        self.assertEqual(bucket["frontier_typed_bytes"], 37_532)
        self.assertFalse(bucket["source_exposed_bucket_predictor"])
        self.assertEqual(
            bucket["prediction_status"],
            "NO_GO_SOURCE_EXPOSED_BUCKET_PREDICTOR_ABSENT",
        )

    def test_best_seed_gap_is_entirely_path_opening(self):
        bucket = self.payload["bucket_attribution"]
        self.assertEqual(bucket["best_seed_id"], "adjacent_seed_02")
        self.assertEqual(bucket["best_seed_gap_typed_bytes"], 2_736)
        self.assertEqual(bucket["best_seed_gap_path_opening_bytes"], 2_736)
        self.assertEqual(bucket["best_seed_gap_value_bytes"], 0)
        self.assertEqual(
            bucket["best_seed_group_gap_bytes"],
            {
                "fixed_overhead": 0,
                "fri_decommitments": 2_016,
                "fri_samples": 80,
                "oods_samples": 0,
                "queries_values": 0,
                "trace_decommitments": 640,
            },
        )

    def test_compared_rows_have_same_value_bytes(self):
        values = {row["variant_id"]: row["value_bytes"] for row in self.payload["proof_object_rows"]}
        self.assertEqual(set(values.values()), {20_924})
        self.assertTrue(self.payload["bucket_attribution"]["all_compared_rows_have_same_value_bytes"])

    def test_comparison_deltas_are_pinned(self):
        seed_02 = self.comparison("adjacent_seed_02")
        seed_05 = self.comparison("adjacent_seed_05")
        fixed = self.comparison("fixed_adjacent_layout")
        self.assertEqual(seed_02["path_opening_delta_vs_probe_b"], 2_736)
        self.assertEqual(seed_05["path_opening_delta_vs_probe_b"], 2_800)
        self.assertEqual(fixed["path_opening_delta_vs_probe_b"], 4_624)
        self.assertEqual(seed_02["value_delta_vs_probe_b"], 0)
        self.assertEqual(seed_05["value_delta_vs_probe_b"], 0)
        self.assertEqual(fixed["value_delta_vs_probe_b"], 0)

    def test_record_streams_remain_bound_to_rows(self):
        streams = {row["variant_id"]: row["record_stream_sha256"] for row in self.payload["proof_object_rows"]}
        self.assertEqual(len(set(streams.values())), len(streams))
        for digest in streams.values():
            self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_non_claims_reject_nanozk_win(self):
        self.assertIn("not a NANOZK proof-size win", self.payload["non_claims"])
        self.assertEqual(
            self.payload["bucket_attribution"]["proof_size_comparable_external_rows"],
            0,
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
                self.gate.AdjacentProbeBBucketAttributionGateError,
                "mutation function inventory drift",
            ):
                self.gate.ensure_mutation_inventory()
        finally:
            self.gate.MUTATION_NAMES = original_names

    def test_best_seed_lookup_has_controlled_missing_row_error(self):
        original_comparison_rows = self.gate.comparison_rows

        def missing_seed_02(rows):
            return [row for row in original_comparison_rows(rows) if row["variant_id"] != "adjacent_seed_02"]

        self.gate.comparison_rows = missing_seed_02
        try:
            with self.assertRaisesRegex(
                self.gate.AdjacentProbeBBucketAttributionGateError,
                "adjacent_seed_02 comparison row missing",
            ):
                self.gate.build_payload_without_mutations()
        finally:
            self.gate.comparison_rows = original_comparison_rows

    def test_payload_commitment_is_stable(self):
        self.assertEqual(
            self.payload["payload_commitment"],
            self.gate.payload_commitment(self.payload),
        )

    def test_rejects_predictor_promotion(self):
        item = json.loads(json.dumps(self.payload))
        item["bucket_attribution"]["source_exposed_bucket_predictor"] = True
        item["payload_commitment"] = self.gate.payload_commitment(item)
        with self.assertRaisesRegex(
            self.gate.AdjacentProbeBBucketAttributionGateError,
            "bucket_attribution drift",
        ):
            self.gate.validate_payload(item)

    def test_rejects_value_byte_drift(self):
        item = json.loads(json.dumps(self.payload))
        self.row_from(item, "adjacent_seed_02")["value_bytes"] = 20_000
        item["payload_commitment"] = self.gate.payload_commitment(item)
        with self.assertRaisesRegex(
            self.gate.AdjacentProbeBBucketAttributionGateError,
            "proof_object_rows drift",
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
            self.assertEqual(len(lines), 1 + len(self.payload["comparisons_vs_probe_b"]))
            self.assertEqual(
                lines[0],
                "\t".join(
                    [
                        "variant_id",
                        "typed_delta_vs_probe_b",
                        "json_delta_vs_probe_b",
                        "path_opening_delta_vs_probe_b",
                        "value_delta_vs_probe_b",
                        "fri_decommitments_delta",
                        "fri_samples_delta",
                        "trace_decommitments_delta",
                        "payload_commitment",
                        "decision",
                        "result",
                    ]
                ),
            )
            expected_rows = []
            for row in self.payload["comparisons_vs_probe_b"]:
                group_deltas = row["group_deltas_vs_probe_b"]
                expected_rows.append(
                    "\t".join(
                        str(value)
                        for value in [
                            row["variant_id"],
                            row["typed_delta_vs_probe_b"],
                            row["json_delta_vs_probe_b"],
                            row["path_opening_delta_vs_probe_b"],
                            row["value_delta_vs_probe_b"],
                            group_deltas["fri_decommitments"],
                            group_deltas["fri_samples"],
                            group_deltas["trace_decommitments"],
                            self.payload["payload_commitment"],
                            self.payload["decision"],
                            self.payload["result"],
                        ]
                    )
                )
            self.assertEqual(lines[1:], expected_rows)

    def test_rejects_output_paths_outside_evidence_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            with self.assertRaisesRegex(
                self.gate.AdjacentProbeBBucketAttributionGateError,
                "output path escapes evidence dir",
            ):
                self.gate.write_outputs(tmp_path / "out.json", tmp_path / "out.tsv", self.payload)

    def test_rejects_non_regular_repo_file_before_reading(self):
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmp:
            directory_path = pathlib.Path(tmp) / "not-a-file"
            directory_path.mkdir()
            with self.assertRaisesRegex(
                self.gate.AdjacentProbeBBucketAttributionGateError,
                "regular file",
            ):
                self.gate.read_bounded_repo_file(directory_path, "directory test", 1024)

    def test_rejects_symlink_repo_file_before_reading(self):
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmp, tempfile.TemporaryDirectory() as outside_tmp:
            tmp_path = pathlib.Path(tmp)
            outside = pathlib.Path(outside_tmp) / "outside.txt"
            outside.write_text("outside")
            symlink_path = tmp_path / "link"
            symlink_path.symlink_to(outside)
            with self.assertRaisesRegex(
                self.gate.AdjacentProbeBBucketAttributionGateError,
                "symlink",
            ):
                self.gate.read_bounded_repo_file(symlink_path, "symlink test", 1024)

    def test_rejects_malformed_accounting_rows_shape(self):
        original_read_json_object = self.gate.read_json_object

        def fake_read_json_object(path, label, max_bytes):
            data, raw = original_read_json_object(path, label, max_bytes)
            if path == self.gate.ACCOUNTING_PATH:
                data = dict(data)
                data["rows"] = {}
            return data, raw

        self.gate.read_json_object = fake_read_json_object
        try:
            with self.assertRaisesRegex(
                self.gate.AdjacentProbeBBucketAttributionGateError,
                "accounting rows must be a JSON array",
            ):
                self.gate.accounting_rows_by_path()
        finally:
            self.gate.read_json_object = original_read_json_object

    def test_rejects_malformed_accounting_row_object(self):
        original_read_json_object = self.gate.read_json_object

        def fake_read_json_object(path, label, max_bytes):
            data, raw = original_read_json_object(path, label, max_bytes)
            if path == self.gate.ACCOUNTING_PATH:
                data = dict(data)
                data["rows"] = ["bad-row"]
            return data, raw

        self.gate.read_json_object = fake_read_json_object
        try:
            with self.assertRaisesRegex(
                self.gate.AdjacentProbeBBucketAttributionGateError,
                "accounting row must be a JSON object",
            ):
                self.gate.accounting_rows_by_path()
        finally:
            self.gate.read_json_object = original_read_json_object

    def test_rejects_invalid_proof_byte_with_gate_error(self):
        original_read_json_object = self.gate.read_json_object

        def fake_read_json_object(path, label, max_bytes):
            data, raw = original_read_json_object(path, label, max_bytes)
            if label == "adjacent_label_probe_b envelope":
                data = json.loads(json.dumps(data))
                data["proof"][0] = 300
            return data, raw

        self.gate.read_json_object = fake_read_json_object
        try:
            with self.assertRaisesRegex(
                self.gate.AdjacentProbeBBucketAttributionGateError,
                "proof byte 0 invalid",
            ):
                self.gate.build_rows()
        finally:
            self.gate.read_json_object = original_read_json_object

    def test_rejects_missing_envelope_metadata_with_gate_error(self):
        accounting = self.gate.accounting_rows_by_path()
        row = json.loads(
            json.dumps(
                accounting[
                    "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-2026-05.envelope.json"
                ]
            )
        )
        row.pop("envelope_metadata")
        with self.assertRaisesRegex(
            self.gate.AdjacentProbeBBucketAttributionGateError,
            "envelope metadata missing",
        ):
            self.gate.proof_row(self.gate.EXPECTED_ROWS[0], row)

    @staticmethod
    def row_from(payload, variant_id):
        for row in payload["proof_object_rows"]:
            if row["variant_id"] == variant_id:
                return row
        raise AssertionError(f"missing row {variant_id}")


if __name__ == "__main__":
    unittest.main()
