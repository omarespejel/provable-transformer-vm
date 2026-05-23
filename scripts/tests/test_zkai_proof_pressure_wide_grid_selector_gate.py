import copy
import json
import tempfile
import unittest

from scripts import zkai_proof_pressure_wide_grid_selector_gate as gate


class ProofPressureWideGridSelectorGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = gate.build_payload()
        cls.expected_source_artifacts = cls.payload["source_artifacts"]

    def evidence_tempdir(self):
        return tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-wide-grid-selector-test-")

    def symlink_or_skip(self, link_path, target_path):
        try:
            link_path.symlink_to(target_path, target_is_directory=True)
        except (OSError, NotImplementedError) as err:
            self.skipTest(f"symlink creation unavailable: {err}")

    def test_records_wide_grid_as_falsification_target_not_result(self):
        payload = self.payload
        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertIn("D128_HAS_SINGLE_HEAD_TWO_TWO_HEAD_ROWS_AND_TWO_FOUR_HEAD_ROWS", payload["claim_boundary"])
        requested = payload["requested_grid_signal"]
        self.assertEqual(requested["requested_widths"], [64, 128, 256])
        self.assertEqual(requested["requested_head_counts"], [1, 2, 4])
        self.assertEqual(requested["requested_sequences"], [16, 32, 64])
        self.assertEqual(requested["requested_cell_count"], 27)
        self.assertEqual(requested["source_backed_requested_cell_count"], 12)
        self.assertEqual(requested["missing_requested_cell_count"], 15)
        self.assertEqual(
            requested["source_backed_requested_profile_ids"],
            [
                "d64_h1_seq16",
                "d64_h2_seq16",
                "d64_h2_seq32",
                "d64_h2_seq64",
                "d64_h4_seq16",
                "d64_h4_seq32",
                "d64_h4_seq64",
                "d128_h1_seq16",
                "d128_h2_seq32",
                "d128_h2_seq64",
                "d128_h4_seq32",
                "d128_h4_seq64",
            ],
        )
        self.assertEqual(requested["fully_missing_requested_widths"], [256])
        self.assertEqual(requested["selector_status"], "PARTIAL_D64_AND_FIVE_D128_SOURCE_BACKED_D256_MISSING")
        status_by_id = {row["profile_id"]: row["selector_status"] for row in requested["requested_rows"]}
        self.assertEqual(status_by_id["d64_h2_seq16"], "SOURCE_BACKED_ATTENTION_ROUTE_ROW")
        self.assertEqual(status_by_id["d64_h2_seq32"], "SOURCE_BACKED_ATTENTION_ROUTE_ROW")
        self.assertEqual(status_by_id["d64_h2_seq64"], "SOURCE_BACKED_ATTENTION_ROUTE_ROW")
        self.assertEqual(status_by_id["d64_h4_seq16"], "SOURCE_BACKED_ATTENTION_ROUTE_ROW")
        self.assertEqual(status_by_id["d64_h4_seq32"], "SOURCE_BACKED_ATTENTION_ROUTE_ROW")
        self.assertEqual(status_by_id["d64_h4_seq64"], "SOURCE_BACKED_ATTENTION_ROUTE_ROW")
        self.assertEqual(status_by_id["d64_h1_seq16"], "SOURCE_BACKED_ATTENTION_ROUTE_ROW")
        self.assertEqual(status_by_id["d128_h1_seq16"], "SOURCE_BACKED_ATTENTION_ROUTE_ROW")
        self.assertEqual(status_by_id["d128_h2_seq32"], "SOURCE_BACKED_ATTENTION_ROUTE_ROW")
        self.assertEqual(status_by_id["d128_h2_seq64"], "SOURCE_BACKED_ATTENTION_ROUTE_ROW")
        self.assertEqual(status_by_id["d128_h4_seq32"], "SOURCE_BACKED_ATTENTION_ROUTE_ROW")
        self.assertEqual(status_by_id["d128_h4_seq64"], "SOURCE_BACKED_ATTENTION_ROUTE_ROW")

    def test_binds_current_route_matrix_signal(self):
        current = self.payload["current_signal"]
        self.assertEqual(current["checked_attention_route_rows"], 29)
        self.assertEqual(current["checked_widths"], [8, 16, 32, 64, 128])
        self.assertEqual(current["checked_sequences"], [8, 16, 32, 64])
        self.assertEqual(current["raw_fused_bytes_total"], 5576234)
        self.assertEqual(current["raw_split_bytes_total"], 6312974)
        self.assertEqual(current["raw_saving_bytes_total"], 736740)
        self.assertEqual(
            current["checked_requested_profile_ids"],
            [
                "d64_h1_seq16",
                "d64_h2_seq16",
                "d64_h2_seq32",
                "d64_h2_seq64",
                "d64_h4_seq16",
                "d64_h4_seq32",
                "d64_h4_seq64",
                "d128_h1_seq16",
                "d128_h2_seq32",
                "d128_h2_seq64",
                "d128_h4_seq32",
                "d128_h4_seq64",
            ],
        )
        self.assertEqual(current["fully_missing_requested_widths"], [256])
        d32_sequence = current["d32_two_head_seq8_to_seq32"]
        self.assertEqual(d32_sequence["lookup_claim_growth"], 11.384615)
        self.assertEqual(d32_sequence["trace_row_growth"], 16.0)
        self.assertEqual(d32_sequence["fused_raw_proof_growth"], 1.193955)
        width_pressure = current["d8_to_d32_two_head_seq32_width_pressure"]
        self.assertEqual(width_pressure["lookup_claim_growth"], 1.0)
        self.assertEqual(width_pressure["fused_raw_proof_growth"], 2.263739)
        d64_sequence = current["d64_two_head_seq16_to_seq32"]
        self.assertEqual(d64_sequence["lookup_claim_growth"], 3.52381)
        self.assertEqual(d64_sequence["trace_row_growth"], 4.0)
        self.assertEqual(d64_sequence["fused_raw_proof_growth"], 1.061856)
        self.assertEqual(d64_sequence["split_raw_proof_growth"], 1.106226)
        self.assertEqual(d64_sequence["saving_growth"], 1.656782)
        d64_two_head_seq64 = current["d64_two_head_seq32_to_seq64"]
        self.assertEqual(d64_two_head_seq64["lookup_claim_growth"], 3.72973)
        self.assertEqual(d64_two_head_seq64["trace_row_growth"], 4.0)
        self.assertEqual(d64_two_head_seq64["source_raw_proof_growth"], 1.063132)
        self.assertEqual(d64_two_head_seq64["sidecar_raw_proof_growth"], 1.169423)
        self.assertEqual(d64_two_head_seq64["fused_raw_proof_growth"], 1.076519)
        self.assertEqual(d64_two_head_seq64["split_raw_proof_growth"], 1.076702)
        self.assertEqual(d64_two_head_seq64["saving_growth"], 1.07816)
        d64_head_seq16 = current["d64_two_to_four_head_seq16"]
        self.assertEqual(d64_head_seq16["lookup_claim_growth"], 2.0)
        self.assertEqual(d64_head_seq16["trace_row_growth"], 2.0)
        self.assertEqual(d64_head_seq16["source_raw_proof_growth"], 1.009983)
        self.assertEqual(d64_head_seq16["sidecar_raw_proof_growth"], 1.0243)
        self.assertEqual(d64_head_seq16["fused_raw_proof_growth"], 0.996193)
        self.assertEqual(d64_head_seq16["split_raw_proof_growth"], 1.011485)
        self.assertEqual(d64_head_seq16["saving_growth"], 1.201238)
        d64_single_head_seq16 = current["d64_single_to_four_head_seq16"]
        self.assertEqual(d64_single_head_seq16["lookup_claim_growth"], 4.0)
        self.assertEqual(d64_single_head_seq16["trace_row_growth"], 4.0)
        self.assertEqual(d64_single_head_seq16["source_raw_proof_growth"], 1.00681)
        self.assertEqual(d64_single_head_seq16["sidecar_raw_proof_growth"], 1.206185)
        self.assertEqual(d64_single_head_seq16["fused_raw_proof_growth"], 0.999457)
        self.assertEqual(d64_single_head_seq16["split_raw_proof_growth"], 1.024806)
        self.assertEqual(d64_single_head_seq16["saving_growth"], 1.386727)
        d128_single_head_seq16 = current["d64_to_d128_single_head_seq16_width_anchor"]
        self.assertEqual(d128_single_head_seq16["lookup_claim_growth"], 1.0)
        self.assertEqual(d128_single_head_seq16["trace_row_growth"], 1.0)
        self.assertEqual(d128_single_head_seq16["source_raw_proof_growth"], 1.617272)
        self.assertEqual(d128_single_head_seq16["sidecar_raw_proof_growth"], 1.004007)
        self.assertEqual(d128_single_head_seq16["fused_raw_proof_growth"], 1.599924)
        self.assertEqual(d128_single_head_seq16["split_raw_proof_growth"], 1.561918)
        self.assertEqual(d128_single_head_seq16["saving_growth"], 1.019279)
        d64_head = current["d64_two_to_four_head_seq32"]
        self.assertEqual(d64_head["lookup_claim_growth"], 2.0)
        self.assertEqual(d64_head["trace_row_growth"], 2.0)
        self.assertEqual(d64_head["source_raw_proof_growth"], 1.021886)
        self.assertEqual(d64_head["fused_raw_proof_growth"], 1.010393)
        self.assertEqual(d64_head["sidecar_raw_proof_growth"], 0.938104)
        self.assertEqual(d64_head["split_raw_proof_growth"], 1.011189)
        self.assertEqual(d64_head["saving_growth"], 1.017522)
        d64_four_head_seq64 = current["d64_four_head_seq32_to_seq64"]
        self.assertEqual(d64_four_head_seq64["lookup_claim_growth"], 3.72973)
        self.assertEqual(d64_four_head_seq64["trace_row_growth"], 4.0)
        self.assertEqual(d64_four_head_seq64["source_raw_proof_growth"], 1.072766)
        self.assertEqual(d64_four_head_seq64["sidecar_raw_proof_growth"], 1.263566)
        self.assertEqual(d64_four_head_seq64["fused_raw_proof_growth"], 1.080558)
        self.assertEqual(d64_four_head_seq64["split_raw_proof_growth"], 1.095365)
        self.assertEqual(d64_four_head_seq64["saving_growth"], 1.212295)
        d128_width = current["d64_to_d128_two_head_seq32_width_frontier"]
        self.assertEqual(d128_width["lookup_claim_growth"], 1.0)
        self.assertEqual(d128_width["trace_row_growth"], 1.0)
        self.assertEqual(d128_width["source_raw_proof_growth"], 1.782318)
        self.assertEqual(d128_width["sidecar_raw_proof_growth"], 0.961813)
        self.assertEqual(d128_width["fused_raw_proof_growth"], 1.760615)
        self.assertEqual(d128_width["split_raw_proof_growth"], 1.677561)
        self.assertEqual(d128_width["saving_growth"], 1.017051)
        d128_sequence = current["d128_two_head_seq32_to_seq64"]
        self.assertEqual(d128_sequence["lookup_claim_growth"], 3.72973)
        self.assertEqual(d128_sequence["trace_row_growth"], 4.0)
        self.assertEqual(d128_sequence["source_raw_proof_growth"], 1.075591)
        self.assertEqual(d128_sequence["sidecar_raw_proof_growth"], 1.297172)
        self.assertEqual(d128_sequence["fused_raw_proof_growth"], 1.080697)
        self.assertEqual(d128_sequence["split_raw_proof_growth"], 1.091811)
        self.assertEqual(d128_sequence["saving_growth"], 1.244813)
        d128_head = current["d128_two_to_four_head_seq32"]
        self.assertEqual(d128_head["lookup_claim_growth"], 2.0)
        self.assertEqual(d128_head["trace_row_growth"], 2.0)
        self.assertEqual(d128_head["source_raw_proof_growth"], 1.045444)
        self.assertEqual(d128_head["sidecar_raw_proof_growth"], 1.186061)
        self.assertEqual(d128_head["fused_raw_proof_growth"], 1.044276)
        self.assertEqual(d128_head["split_raw_proof_growth"], 1.055738)
        self.assertEqual(d128_head["saving_growth"], 1.213536)
        d128_seq64_width = current["d64_to_d128_two_head_seq64_width_frontier"]
        self.assertEqual(d128_seq64_width["lookup_claim_growth"], 1.0)
        self.assertEqual(d128_seq64_width["trace_row_growth"], 1.0)
        self.assertEqual(d128_seq64_width["source_raw_proof_growth"], 1.803206)
        self.assertEqual(d128_seq64_width["sidecar_raw_proof_growth"], 1.066883)
        self.assertEqual(d128_seq64_width["fused_raw_proof_growth"], 1.767448)
        self.assertEqual(d128_seq64_width["split_raw_proof_growth"], 1.701101)
        self.assertEqual(d128_seq64_width["saving_growth"], 1.174259)
        accounting = current["accounting_triplet_signal"]
        self.assertEqual(accounting["attention_typed_rows"], 10)
        self.assertEqual(accounting["attention_typed_bytes_total"], 234296)
        self.assertEqual(accounting["attention_typed_savings_bytes_total"], 51288)
        self.assertEqual(accounting["attention_json_bytes_total"], 629466)
        self.assertEqual(accounting["attention_raw_proof_savings_bytes_total"], 736740)
        self.assertEqual(accounting["binary_raw_available_rows"], 2)
        self.assertEqual(accounting["binary_raw_missing_rows"], 10)
        self.assertEqual(accounting["current_best_inner_policy_bound_row"]["typed_bytes"], 39516)

    def test_selects_next_width_targets_after_d128_four_head_seq64_landed(self):
        candidates = self.payload["candidate_order"]
        self.assertEqual([row["profile_id"] for row in candidates], ["d256_h2_seq32"])
        first = candidates[0]
        self.assertEqual(first["selector_status"], "NEXT_WIDTH_STRESS_TEST_AFTER_D128_FOUR_HEAD_SEQ64_GO")
        self.assertIn("harder width point", first["why_this_row"])

    def test_all_declared_mutations_reject(self):
        mutation = self.payload["mutation_result"]
        self.assertTrue(mutation["all_mutations_rejected"])
        self.assertEqual(mutation["mutations_checked"], len(gate.MUTATION_NAMES))
        self.assertEqual(mutation["mutations_rejected"], len(gate.MUTATION_NAMES))
        self.assertEqual(len(mutation["mutation_names"]), len(gate.MUTATION_NAMES))
        self.assertEqual(mutation["mutation_names"], list(gate.MUTATION_NAMES))

    def test_current_signal_rejects_non_go_match_status(self):
        sources, _ = gate.load_sources()
        route_matrix = copy.deepcopy(sources["route_matrix"])
        route_matrix["route_rows"][0]["matched_source_sidecar_status"] = "NO_GO_PLACEHOLDER"
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "current route row count drift"):
            gate.build_current_signal(route_matrix, sources["fuller_grid"])

    def test_validate_rejects_wide_row_smuggling(self):
        payload = copy.deepcopy(self.payload)
        payload["requested_grid_signal"]["source_backed_requested_cell_count"] = 13
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "wide row smuggling"):
            gate.validate_payload(payload, self.expected_source_artifacts)

    def test_validate_rejects_requested_selector_status_drift(self):
        payload = copy.deepcopy(self.payload)
        payload["requested_grid_signal"]["selector_status"] = "DRIFTED_STATUS"
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "requested selector status drift"):
            gate.validate_payload(payload, self.expected_source_artifacts)

    def test_validate_rejects_requested_source_id_drift(self):
        payload = copy.deepcopy(self.payload)
        payload["requested_grid_signal"]["source_backed_requested_profile_ids"] = [
            "d64_h1_seq16",
            "d64_h2_seq16",
            "d64_h2_seq32",
            "d64_h2_seq64",
            "d64_h4_seq16",
            "d64_h4_seq32",
        ]
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "source-backed requested profile IDs drift"):
            gate.validate_payload(payload, self.expected_source_artifacts)

    def test_validate_rejects_requested_row_status_drift(self):
        payload = copy.deepcopy(self.payload)
        payload["requested_grid_signal"]["requested_rows"][0]["selector_status"] = "MISSING_SOURCE_BACKED_ATTENTION_ROUTE_ROW"
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "requested row status drift"):
            gate.validate_payload(payload, self.expected_source_artifacts)

    def test_validate_rejects_candidate_text_drift(self):
        payload = copy.deepcopy(self.payload)
        payload["candidate_order"][0]["why_this_row"] = "drifted narrative"
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "candidate order drift"):
            gate.validate_payload(payload, self.expected_source_artifacts)

    def test_validate_rejects_payload_commitment_drift(self):
        payload = copy.deepcopy(self.payload)
        payload["payload_commitment"] = "blake2b-256:" + "0" * 64
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "payload commitment drift"):
            gate.validate_payload(payload, self.expected_source_artifacts)

    def test_write_json_rejects_source_artifact_drift_against_independent_baseline(self):
        payload = copy.deepcopy(self.payload)
        payload["source_artifacts"][0]["sha256"] = "0" * 64
        with self.evidence_tempdir() as tmp:
            with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "source artifact drift"):
                gate.write_json(gate.pathlib.Path(tmp) / "wide-grid.json", payload, self.expected_source_artifacts)

    def test_validate_rejects_accounting_total_drift(self):
        payload = copy.deepcopy(self.payload)
        payload["current_signal"]["accounting_triplet_signal"]["attention_typed_bytes_total"] = 0
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "accounting typed total drift"):
            gate.validate_payload(payload, self.expected_source_artifacts)

    def test_validate_rejects_raw_total_drift(self):
        payload = copy.deepcopy(self.payload)
        payload["current_signal"]["raw_fused_bytes_total"] = 0
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "raw fused total drift"):
            gate.validate_payload(payload, self.expected_source_artifacts)

    def test_current_signal_rejects_missing_required_field(self):
        sources, _ = gate.load_sources()
        route_matrix = copy.deepcopy(sources["route_matrix"])
        del route_matrix["route_rows"][0]["fused_saves_vs_source_plus_sidecar_bytes"]
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "route matrix signal field missing"):
            gate.build_current_signal(route_matrix, sources["fuller_grid"])

    def test_current_signal_rejects_wrong_typed_route_field(self):
        sources, _ = gate.load_sources()
        route_matrix = copy.deepcopy(sources["route_matrix"])
        route_matrix["route_rows"][0]["fused_saves_vs_source_plus_sidecar_bytes"] = None
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "route matrix signal field type drift"):
            gate.build_current_signal(route_matrix, sources["fuller_grid"])

    def test_accounting_signal_rejects_missing_required_field(self):
        sources, _ = gate.load_sources()
        claim_pack = copy.deepcopy(sources["claim_pack"])
        del claim_pack["fused_vs_split_rows"][0]["typed_bytes"]
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "accounting field missing"):
            gate.build_accounting_triplet_signal(claim_pack)

    def test_write_json_and_tsv_round_trip(self):
        with self.evidence_tempdir() as tmp:
            tmp_path = gate.pathlib.Path(tmp)
            json_path = tmp_path / "wide-grid.json"
            tsv_path = tmp_path / "wide-grid.tsv"
            gate.write_json(json_path, self.payload, self.expected_source_artifacts)
            gate.write_tsv(tsv_path, self.payload, self.expected_source_artifacts)
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8"))["schema"], gate.SCHEMA)
            tsv = tsv_path.read_text(encoding="utf-8")
            self.assertIn("d256_h2_seq32", tsv)
            self.assertIn("NEXT_WIDTH_STRESS_TEST_AFTER_D128_FOUR_HEAD_SEQ64_GO", tsv)

    def test_write_outputs_reject_absolute_outside_evidence_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "stay inside evidence dir"):
                gate.write_json(gate.pathlib.Path(tmp) / "wide-grid.json", self.payload, self.expected_source_artifacts)

    def test_write_outputs_reject_relative_parent_traversal(self):
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "stay inside evidence dir"):
            gate.write_tsv(
                gate.pathlib.Path("docs/engineering/evidence/../wide-grid.tsv"),
                self.payload,
                self.expected_source_artifacts,
            )

    def test_write_outputs_reject_missing_parent_directory(self):
        with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "parent directory must exist"):
            gate.write_json(
                gate.EVIDENCE_DIR / ".tmp-wide-grid-selector-missing" / "wide-grid.json",
                self.payload,
                self.expected_source_artifacts,
            )

    def test_write_outputs_reject_symlink_escape_inside_evidence_dir(self):
        with self.evidence_tempdir() as evidence_tmp, tempfile.TemporaryDirectory() as outside_tmp:
            link_path = gate.pathlib.Path(evidence_tmp) / "escape"
            self.symlink_or_skip(link_path, gate.pathlib.Path(outside_tmp))
            with self.assertRaisesRegex(gate.ProofPressureWideGridSelectorError, "symlink components"):
                gate.write_json(link_path / "wide-grid.json", self.payload, self.expected_source_artifacts)

    def test_output_path_rejects_symlinked_evidence_root(self):
        original_evidence_dir = gate.EVIDENCE_DIR
        with tempfile.TemporaryDirectory() as outside_tmp:
            link_path = original_evidence_dir.parent / ".tmp-wide-grid-selector-root-link"
            link_path.unlink(missing_ok=True)
            self.symlink_or_skip(link_path, gate.pathlib.Path(outside_tmp))
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
            self.symlink_or_skip(fake_root / "docs", real_docs)
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
