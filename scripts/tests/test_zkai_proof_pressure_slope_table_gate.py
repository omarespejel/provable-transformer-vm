import csv
import json
import tempfile
import unittest

from scripts import zkai_proof_pressure_slope_table_gate as gate


class ProofPressureSlopeTableGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = gate.build_payload()

    def test_records_sequence_head_and_width_slope_without_overclaim(self) -> None:
        gate.validate_payload(self.payload)
        self.assertEqual(self.payload["schema"], gate.SCHEMA)
        self.assertEqual(self.payload["issue"], 715)
        self.assertIn("NOT_FULL_BLOCK", self.payload["claim_boundary"])
        self.assertIn("not a claim that width scaling is free", self.payload["non_claims"])
        self.assertEqual(self.payload["summary"]["row_count"], 8)
        self.assertEqual(self.payload["summary"]["sequence_fused_proof_growth_min"], 1.06491)
        self.assertEqual(self.payload["summary"]["sequence_fused_proof_growth_max"], 1.080697)
        self.assertEqual(self.payload["summary"]["head_axis_d64_seq16_fused_proof_growth"], 0.999457)
        self.assertEqual(self.payload["summary"]["d256_width_saving_bytes"], 30143)
        self.assertEqual(self.payload["summary"]["d256_width_fused_prove_ratio"], 1.154002)
        self.assertEqual(self.payload["summary"]["d256_width_fused_verify_ratio"], 1.198076)
        self.assertIn("scoped_d128_seq32_transformer_block_boundary_preflight", self.payload["summary"]["recommended_next_gate"])

    def test_binds_key_rows(self) -> None:
        rows = {row["row_id"]: row for row in self.payload["rows"]}
        head = rows["d64_h1_to_h4_seq16_head_axis"]
        self.assertEqual(head["lookup_growth"], 4.0)
        self.assertEqual(head["trace_growth"], 4.0)
        self.assertEqual(head["fused_proof_growth"], 0.999457)
        self.assertEqual(head["target_saving_bytes"], 23089)

        d128_seq = rows["d128_h4_seq32_to_seq64_sequence_axis"]
        self.assertEqual(d128_seq["lookup_growth"], 3.72973)
        self.assertEqual(d128_seq["trace_growth"], 4.0)
        self.assertEqual(d128_seq["fused_proof_growth"], 1.06491)
        self.assertEqual(d128_seq["target_saving_bytes"], 43816)

        d256 = rows["d128_to_d256_h2_seq32_width_axis"]
        self.assertEqual(d256["lookup_growth"], 1.0)
        self.assertEqual(d256["trace_growth"], 1.0)
        self.assertEqual(d256["width_growth"], 2.0)
        self.assertEqual(d256["fused_proof_growth"], 1.842162)
        self.assertEqual(d256["saving_growth"], 0.930684)
        self.assertEqual(d256["target_fused_to_split_ratio"], 0.964602)

    def test_individual_mutations_reject(self) -> None:
        for name in gate.MUTATION_NAMES:
            mutated = gate.mutate_payload(self.payload, name)
            with self.assertRaises(gate.ProofPressureSlopeTableError, msg=name):
                gate.validate_payload(mutated, require_mutations=False)

    def test_write_outputs_round_trip(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-slope-table-test-") as tmp:
            tmp_path = gate.pathlib.Path(tmp)
            json_path = tmp_path / "slope.json"
            tsv_path = tmp_path / "slope.tsv"
            gate.write_json(json_path, self.payload)
            gate.write_tsv(tsv_path, self.payload)
            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            gate.validate_payload(loaded)
            with tsv_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual(len(rows), 8)
        with tempfile.TemporaryDirectory(dir=gate.DOCS_DIR, prefix=".tmp-slope-table-test-") as tmp:
            md_path = gate.pathlib.Path(tmp) / "slope.md"
            gate.write_md(md_path, self.payload)
            markdown = md_path.read_text(encoding="utf-8")
            self.assertIn("width growth is a cost center", markdown)
            self.assertIn("d128 to d256 h2 seq32 width axis", markdown)
            self.assertIn("Go: sequence-axis proof-size signal, with timing caveat", markdown)
            self.assertIn("Caution: width saving weakens and timing is not a speed win", markdown)

    def test_output_paths_reject_aliasing_and_escape(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-slope-table-test-") as tmp:
            same = gate.pathlib.Path(tmp) / "same"
            with self.assertRaisesRegex(gate.ProofPressureSlopeTableError, "different files"):
                gate.reject_same_output_paths((same, same, gate.pathlib.Path(tmp) / "other.md"))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(gate.ProofPressureSlopeTableError, "inside"):
                gate.write_json(gate.pathlib.Path(tmp) / "escape.json", self.payload)


if __name__ == "__main__":
    unittest.main()
