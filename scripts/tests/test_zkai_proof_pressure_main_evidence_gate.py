import csv
import json
import tempfile
import unittest

from scripts import zkai_proof_pressure_main_evidence_gate as gate


class ProofPressureMainEvidenceGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = gate.build_payload()

    def test_records_size_signal_with_timing_caveat(self) -> None:
        gate.validate_payload(self.payload)
        self.assertEqual(self.payload["decision"], gate.DECISION)
        self.assertIn("TIMING_IS_ENGINEERING_LOCAL", self.payload["claim_boundary"])
        self.assertEqual(self.payload["summary"]["row_count"], 5)
        rows = {row["row_id"]: row for row in self.payload["rows"]}
        h2 = rows["d64_h2_seq32_to_seq64"]
        self.assertEqual(h2["lookup_growth"], 3.72973)
        self.assertEqual(h2["trace_growth"], 4.0)
        self.assertEqual(h2["fused_proof_growth"], 1.076519)
        self.assertGreater(h2["fused_prove_growth"], 3.0)
        h4 = rows["d64_h4_seq32_to_seq64"]
        self.assertEqual(h4["saving_bytes"], 39282)
        self.assertEqual(h4["fused_to_split_ratio"], 0.875605)
        d256 = rows["d128_to_d256_h2_seq32_width_stress"]
        self.assertEqual(d256["saving_bytes"], 30143)
        self.assertGreater(d256["d256_fused_to_split_prove_ratio"], 1.0)

    def test_write_outputs_round_trip(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-main-evidence-test-") as tmp:
            tmp_path = gate.pathlib.Path(tmp)
            json_path = tmp_path / "evidence.json"
            tsv_path = tmp_path / "evidence.tsv"
            svg_path = tmp_path / "evidence.svg"
            gate.write_json(json_path, self.payload)
            gate.write_tsv(tsv_path, self.payload)
            gate.write_svg(svg_path, self.payload)
            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            gate.validate_payload(loaded)
            with tsv_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual(len(rows), 5)
            svg = svg_path.read_text(encoding="utf-8")
            self.assertIn("Work grows fast", svg)
            self.assertIn("d64 two head seq32", svg)

    def test_validate_rejects_overclaim_shapes(self) -> None:
        payload = json.loads(json.dumps(self.payload))
        payload["rows"].append({"row_id": "fake"})
        with self.assertRaisesRegex(gate.ProofPressureMainEvidenceError, "row smuggling"):
            gate.validate_payload(payload)

        payload = json.loads(json.dumps(self.payload))
        payload["non_claims"].remove("not a public proving-speed benchmark")
        with self.assertRaisesRegex(gate.ProofPressureMainEvidenceError, "non-claims"):
            gate.validate_payload(payload)


if __name__ == "__main__":
    unittest.main()
