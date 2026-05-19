import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = (
    ROOT
    / "scripts"
    / "zkai_native_seq32_attention_mlp_dry_run_opening_sampler_gate.py"
)


def load_gate():
    spec = importlib.util.spec_from_file_location("dry_run_opening_sampler_gate", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DryRunOpeningSamplerGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()
        cls.payload = cls.gate.build_payload()

    def row(self, variant_id):
        for row in self.payload["sampler_rows"]:
            if row["variant_id"] == variant_id:
                return row
        self.fail(f"missing row {variant_id}")

    def test_payload_records_query_location_go_boundary(self):
        self.assertEqual(
            self.payload["decision"],
            "GO_QUERY_LOCATION_SAMPLER_PREDICTS_CHECKED_ADJACENT_OPENING_BUCKETS",
        )
        policy = self.payload["predictor_policy"]
        self.assertTrue(policy["prediction_all_correct"])
        self.assertFalse(policy["row_identity_fields_are_predictors"])
        self.assertFalse(policy["final_accounting_is_predictor_input"])
        self.assertEqual(policy["best_predicted_variant_id"], "adjacent_label_probe_b")
        self.assertEqual(policy["best_predicted_path_opening_bytes"], 16_560)
        self.assertEqual(policy["distinct_final_path_opening_buckets"], 5)

    def test_probe_b_tight_query_cluster_is_the_smallest_bucket(self):
        probe_b = self.row("adjacent_label_probe_b")
        self.assertEqual(probe_b["sorted_unique_query_locations"], [427295, 433264, 443913])
        self.assertEqual(probe_b["predictor_features"]["query_location_span"], 16_618)
        self.assertEqual(probe_b["prediction_rule"], "tight_three_query_cluster")
        self.assertEqual(probe_b["predicted_path_opening_bytes"], 16_560)
        self.assertEqual(probe_b["final_path_opening_bytes"], 16_560)
        self.assertTrue(probe_b["prediction_correct"])

    def test_predictor_uses_only_query_geometry(self):
        predictor_keys = set(self.payload["predictor_policy"]["predictor_feature_keys"])
        self.assertEqual(
            predictor_keys,
            {"unique_query_count", "query_location_span", "min_pairwise_query_gap"},
        )
        self.assertFalse(predictor_keys.intersection(self.gate.FORBIDDEN_PREDICTOR_KEYS))
        for row in self.payload["sampler_rows"]:
            self.assertEqual(set(row["predictor_features"]), predictor_keys)
            self.assertNotIn("path_opening_bytes", row["predictor_features"])
            self.assertNotIn("statement_commitment", row["predictor_features"])

    def test_all_mutations_rejected(self):
        mutation = self.payload["mutation_result"]
        self.assertTrue(mutation["all_mutations_rejected"])
        self.assertEqual(mutation["mutations_rejected"], len(self.gate.MUTATION_NAMES))
        self.assertEqual(mutation["mutation_names"], list(self.gate.MUTATION_NAMES))

    def test_rejects_row_identity_promotion(self):
        item = self.gate.build_payload_without_mutations()
        item["predictor_policy"]["predictor_feature_keys"].append("statement_commitment")
        with self.assertRaisesRegex(
            self.gate.DryRunOpeningSamplerGateError,
            "base payload drift",
        ):
            self.gate.validate_base_payload(item)

    def test_rejects_final_accounting_leak_to_predictor(self):
        item = self.gate.build_payload_without_mutations()
        item["sampler_rows"][1]["predictor_features"]["path_opening_bytes"] = 16_560
        with self.assertRaisesRegex(
            self.gate.DryRunOpeningSamplerGateError,
            "base payload drift",
        ):
            self.gate.validate_base_payload(item)

    def test_payload_commitment_and_tsv_are_stable(self):
        payload_a = self.gate.build_payload()
        payload_b = self.gate.build_payload()
        self.assertEqual(payload_a["payload_commitment"], self.gate.payload_commitment(payload_a))
        self.assertEqual(payload_a["payload_commitment"], payload_b["payload_commitment"])
        self.assertEqual(self.gate.render_tsv(payload_a), self.gate.render_tsv(payload_b))

    def test_writes_paired_json_and_tsv_outputs(self):
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmp:
            tmp_path = pathlib.Path(tmp)
            json_path = tmp_path / "out.json"
            tsv_path = tmp_path / "out.tsv"
            self.gate.write_outputs(json_path, tsv_path, self.payload)
            loaded = json.loads(json_path.read_text())
            self.assertEqual(loaded["payload_commitment"], self.payload["payload_commitment"])
            lines = tsv_path.read_text().splitlines()
            self.assertEqual(len(lines), 1 + len(self.payload["sampler_rows"]))
            self.assertEqual(lines[0], "\t".join(self.gate.TSV_COLUMNS))
            rows_by_variant = {row["variant_id"]: row for row in self.payload["sampler_rows"]}
            for line in lines[1:]:
                columns = dict(zip(self.gate.TSV_COLUMNS, line.split("\t"), strict=True))
                row = rows_by_variant[columns["variant_id"]]
                self.assertEqual(columns["adapter_mode"], row["adapter_mode"])
                self.assertEqual(
                    columns["query_location_span"],
                    str(row["predictor_features"]["query_location_span"]),
                )
                self.assertEqual(
                    columns["predicted_path_opening_bytes"],
                    str(row["predicted_path_opening_bytes"]),
                )
                self.assertEqual(
                    columns["final_path_opening_bytes"],
                    str(row["final_path_opening_bytes"]),
                )
                self.assertEqual(columns["prediction_correct"], "true")

    def test_rejects_output_paths_outside_evidence_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                self.gate.DryRunOpeningSamplerGateError,
                "output path must stay under evidence directory",
            ):
                self.gate.write_outputs(
                    pathlib.Path(tmp) / "out.json",
                    pathlib.Path(tmp) / "out.tsv",
                    self.payload,
                )


if __name__ == "__main__":
    unittest.main()
