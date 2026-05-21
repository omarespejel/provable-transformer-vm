import copy
import json
import tempfile
import unittest

from scripts import zkai_proof_pressure_wide_grid_selector_gate as gate


class ProofPressureWideGridSelectorGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = gate.build_payload()

    def evidence_tempdir(self):
        return tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-wide-grid-selector-test-")

    def test_records_wide_grid_as_falsification_target_not_result(self):
        payload = self.payload
        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertIn("NO_D64_D128_D256_ATTENTION_PROOF_ROWS_YET", payload["claim_boundary"])
        requested = payload["requested_grid_signal"]
        self.assertEqual(requested["requested_widths"], [64, 128, 256])
        self.assertEqual(requested["requested_cell_count"], 18)
        self.assertEqual(requested["source_backed_requested_cell_count"], 0)
        self.assertEqual(requested["missing_requested_widths"], [64, 128, 256])
        self.assertEqual(requested["selector_status"], "NO_D64_D128_D256_ATTENTION_ROUTE_ROWS_YET")

    def test_binds_current_route_matrix_signal(self):
        current = self.payload["current_signal"]
        self.assertEqual(current["checked_attention_route_rows"], 14)
        self.assertEqual(current["checked_widths"], [8, 16, 32])
        self.assertEqual(current["raw_saving_bytes_total"], 266325)
        d32_sequence = current["d32_two_head_seq8_to_seq32"]
        self.assertEqual(d32_sequence["lookup_claim_growth"], 11.384615)
        self.assertEqual(d32_sequence["trace_row_growth"], 16.0)
        self.assertEqual(d32_sequence["fused_raw_proof_growth"], 1.193955)
        width_pressure = current["d8_to_d32_two_head_seq32_width_pressure"]
        self.assertEqual(width_pressure["lookup_claim_growth"], 1.0)
        self.assertEqual(width_pressure["fused_raw_proof_growth"], 2.263739)
        accounting = current["accounting_triplet_signal"]
        self.assertEqual(accounting["attention_typed_savings_bytes_total"], 51288)
        self.assertEqual(accounting["attention_json_bytes_total"], 629466)
        self.assertEqual(accounting["attention_raw_proof_savings_bytes_total"], 266325)
        self.assertEqual(accounting["binary_raw_available_rows"], 2)
        self.assertEqual(accounting["binary_raw_missing_rows"], 10)
        self.assertEqual(accounting["current_best_inner_policy_bound_row"]["typed_bytes"], 39516)

    def test_selects_d64_two_head_seq32_first(self):
        candidates = self.payload["candidate_order"]
        self.assertEqual([row["profile_id"] for row in candidates], [
            "d64_h2_seq32",
            "d64_h1_seq8",
            "d64_h2_seq16",
            "d128_h2_seq32",
            "d256_h2_seq32",
        ])
        first = candidates[0]
        self.assertEqual(first["selector_status"], "FIRST_FALSIFICATION_ROW")
        self.assertIn("extends the current d32 two-head seq32", first["why_this_row"])

    def test_all_declared_mutations_reject(self):
        mutation = self.payload["mutation_result"]
        self.assertEqual(len(gate.MUTATION_NAMES), 13)
        self.assertTrue(mutation["all_mutations_rejected"])
        self.assertEqual(mutation["mutations_checked"], 13)
        self.assertEqual(mutation["mutations_rejected"], 13)
        self.assertEqual(len(mutation["mutation_names"]), 13)
        self.assertEqual(mutation["mutation_names"], list(gate.MUTATION_NAMES))

    def test_current_signal_rejects_non_go_match_status(self):
        sources, _ = gate.load_sources()
        route_matrix = copy.deepcopy(sources["route_matrix"])
        route_matrix["route_rows"][0]["matched_source_sidecar_status"] = "NO_GO_PLACEHOLDER"
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "current route row count drift"):
            gate.build_current_signal(route_matrix, sources["fuller_grid"])

    def test_validate_rejects_wide_row_smuggling(self):
        payload = copy.deepcopy(self.payload)
        payload["requested_grid_signal"]["source_backed_requested_cell_count"] = 1
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "wide row smuggling"):
            gate.validate_payload(payload)

    def test_validate_rejects_payload_commitment_drift(self):
        payload = copy.deepcopy(self.payload)
        payload["payload_commitment"] = "blake2b-256:" + "0" * 64
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "payload commitment drift"):
            gate.validate_payload(payload)

    def test_write_json_and_tsv_round_trip(self):
        with self.evidence_tempdir() as tmp:
            tmp_path = gate.pathlib.Path(tmp)
            json_path = tmp_path / "wide-grid.json"
            tsv_path = tmp_path / "wide-grid.tsv"
            gate.write_json(json_path, self.payload)
            gate.write_tsv(tsv_path, self.payload)
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8"))["schema"], gate.SCHEMA)
            tsv = tsv_path.read_text(encoding="utf-8")
            self.assertIn("d64_h2_seq32", tsv)
            self.assertIn("FIRST_FALSIFICATION_ROW", tsv)

    def test_write_outputs_reject_absolute_outside_evidence_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "stay inside evidence dir"):
                gate.write_json(gate.pathlib.Path(tmp) / "wide-grid.json", self.payload)

    def test_write_outputs_reject_relative_parent_traversal(self):
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "stay inside evidence dir"):
            gate.write_tsv(gate.pathlib.Path("docs/engineering/evidence/../wide-grid.tsv"), self.payload)

    def test_write_outputs_reject_symlink_escape_inside_evidence_dir(self):
        with self.evidence_tempdir() as evidence_tmp, tempfile.TemporaryDirectory() as outside_tmp:
            link_path = gate.pathlib.Path(evidence_tmp) / "escape"
            link_path.symlink_to(gate.pathlib.Path(outside_tmp), target_is_directory=True)
            with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "symlink components"):
                gate.write_json(link_path / "wide-grid.json", self.payload)

    def test_output_path_rejects_symlinked_evidence_root(self):
        original_evidence_dir = gate.EVIDENCE_DIR
        with tempfile.TemporaryDirectory() as outside_tmp:
            link_path = original_evidence_dir.parent / ".tmp-wide-grid-selector-root-link"
            link_path.unlink(missing_ok=True)
            link_path.symlink_to(gate.pathlib.Path(outside_tmp), target_is_directory=True)
            gate.EVIDENCE_DIR = link_path
            try:
                with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "symlink components"):
                    gate.checked_output_path(link_path / "wide-grid.json")
            finally:
                gate.EVIDENCE_DIR = original_evidence_dir
                link_path.unlink(missing_ok=True)

    def test_output_path_rejects_symlinked_evidence_ancestor(self):
        original_root = gate.ROOT
        original_evidence_dir = gate.EVIDENCE_DIR
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = gate.pathlib.Path(tmp)
            fake_root = tmp_path / "repo"
            real_docs = tmp_path / "real-docs"
            (real_docs / "engineering" / "evidence").mkdir(parents=True)
            fake_root.mkdir()
            (fake_root / "docs").symlink_to(real_docs, target_is_directory=True)
            gate.ROOT = fake_root
            gate.EVIDENCE_DIR = fake_root / "docs" / "engineering" / "evidence"
            try:
                with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "symlink components"):
                    gate.checked_output_path(gate.EVIDENCE_DIR / "wide-grid.json")
            finally:
                gate.ROOT = original_root
                gate.EVIDENCE_DIR = original_evidence_dir


if __name__ == "__main__":
    unittest.main()
