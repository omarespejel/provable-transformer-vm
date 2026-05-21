from __future__ import annotations

import copy
import json
import pathlib
import tempfile
import unittest

from scripts import zkai_proof_pressure_scaling_claim_pack_gate as gate


class ProofPressureScalingClaimPackGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload_base = gate.build_payload()

    def setUp(self) -> None:
        self.payload = copy.deepcopy(self.payload_base)

    def strip_mutation_summary(self, payload: dict) -> dict:
        payload = copy.deepcopy(payload)
        for key in ("mutation_results", "mutations_checked", "mutations_rejected", "all_mutations_rejected"):
            payload.pop(key, None)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        return payload

    def assert_rejects(self, payload: dict, message: str) -> None:
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.ProofPressureScalingClaimPackError, message):
            gate.validate_payload(payload, check_mutations=False)

    def test_records_current_scale_signal_without_full_grid_overclaim(self) -> None:
        gate.validate_payload(self.payload)
        signal = self.payload["scale_signal"]
        route_signal = self.payload["route_matrix_signal"]
        summary = self.payload["summary"]

        self.assertEqual(self.payload["schema"], gate.SCHEMA)
        self.assertEqual(self.payload["issue"], gate.ISSUE)
        self.assertEqual(self.payload["decision"], gate.DECISION)
        self.assertIn("NOT_D64_D128_D256_FULL_GRID", self.payload["claim_boundary"])
        self.assertIn("not a d64/d128/d256 attention grid", self.payload["non_claims"])
        self.assertEqual(signal["profiles_checked"], 10)
        self.assertEqual(signal["axes_checked"]["widths"], [8, 16])
        self.assertEqual(signal["axes_checked"]["head_counts"], [1, 2, 4, 8, 16])
        self.assertEqual(signal["axes_checked"]["steps_per_head"], [8, 16, 32])
        self.assertIn("d64/d128/d256", signal["missing_axes"][0])
        self.assertEqual(route_signal["profiles_checked"], 14)
        self.assertEqual(route_signal["matched_comparator_profiles"], 14)
        self.assertEqual(route_signal["widths"], [8, 16, 32])
        self.assertEqual(route_signal["raw_proof_savings_bytes_total"], 266325)
        self.assertEqual(route_signal["d32_two_head_sequence_ladder"]["seq32_raw_saving_bytes"], 26326)
        self.assertEqual(summary["proof_size_comparable_external_rows"], 0)
        self.assertEqual(summary["attention_route_rows_checked"], 14)
        self.assertEqual(summary["attention_raw_proof_savings_bytes_total"], 266325)
        self.assertEqual(summary["open_followup_count"], 3)

    def test_binds_lookup_growth_and_bytes_per_lookup_signal(self) -> None:
        seq32 = self.payload["scale_signal"]["seq32_vs_d8_single_head"]

        self.assertEqual(seq32["lookup_claim_growth"], "22.769231")
        self.assertEqual(seq32["typed_byte_growth"], "1.264401")
        self.assertEqual(seq32["baseline_typed_bytes_per_lookup_claim"], "348.538462")
        self.assertEqual(seq32["seq32_typed_bytes_per_lookup_claim"], "19.354730")
        self.assertEqual(seq32["seq32_lookup_claims"], 1184)
        self.assertEqual(seq32["seq32_fused_typed_bytes"], 22916)
        self.assertEqual(seq32["seq32_split_typed_bytes"], 31712)
        self.assertEqual(seq32["seq32_fused_saving_bytes"], 8796)

    def test_binds_14_row_route_matrix_and_d32_seq32_raw_signal(self) -> None:
        route_signal = self.payload["route_matrix_signal"]
        ladder = route_signal["d32_two_head_sequence_ladder"]

        self.assertEqual(route_signal["total_lookup_claims"], 5300)
        self.assertEqual(route_signal["total_trace_rows"], 8000)
        self.assertEqual(route_signal["fused_raw_proof_bytes_total"], 1145173)
        self.assertEqual(route_signal["source_plus_sidecar_raw_proof_bytes_total"], 1411498)
        self.assertEqual(ladder["profile_ids"], ["d32_two_head_seq8", "d32_two_head_seq16", "d32_two_head_seq32"])
        self.assertEqual(ladder["seq32_lookup_claims"], 1184)
        self.assertEqual(ladder["seq32_fused_raw_proof_bytes"], 150147)
        self.assertEqual(ladder["seq32_source_plus_sidecar_raw_proof_bytes"], 176473)
        self.assertEqual(ladder["seq8_to_seq32_lookup_claim_growth"], "11.384615")
        self.assertEqual(ladder["seq8_to_seq32_trace_row_growth"], "16.000000")
        self.assertEqual(ladder["seq8_to_seq32_fused_raw_proof_growth"], "1.193955")
        self.assertEqual(ladder["seq16_to_seq32_lookup_claim_growth"], "3.523810")
        self.assertEqual(ladder["seq16_to_seq32_trace_row_growth"], "4.000000")
        self.assertEqual(ladder["seq16_to_seq32_fused_raw_proof_growth"], "1.132817")

    def test_fused_vs_split_rows_are_local_and_positive(self) -> None:
        rows = {row["row_id"]: row for row in self.payload["fused_vs_split_rows"]}
        attention_rows = [row for row in rows.values() if row["category"] == "attention_fused_vs_split"]

        self.assertEqual(len(attention_rows), 10)
        self.assertTrue(all(row["typed_saving_bytes"] > 0 for row in attention_rows))

        seq32 = rows["d8_two_head_seq32"]
        self.assertEqual(seq32["matched_frontier_typed_bytes"], 31712)
        self.assertEqual(seq32["typed_bytes"], 22916)
        self.assertEqual(seq32["typed_saving_bytes"], 8796)
        self.assertIsNone(seq32["binary_raw_bytes"])
        self.assertEqual(seq32["binary_raw_status"], gate.ATTENTION_BINARY_RAW_STATUS)
        self.assertEqual(seq32["comparison_status"], "LOCAL_MATCHED_ATTENTION_SOURCE_PLUS_SIDECAR")

        native = rows["seq32_d128_native_single_proof"]
        self.assertEqual(native["typed_bytes"], 42068)
        self.assertEqual(native["matched_frontier_typed_bytes"], 47188)
        self.assertEqual(native["typed_saving_bytes"], 5120)
        self.assertEqual(native["binary_raw_bytes"], 1084)
        self.assertEqual(native["binary_raw_status"], gate.LOCAL_RECORD_STREAM_STATUS)

        statement = rows["seq32_d128_statement_only_probe_b"]
        self.assertEqual(statement["typed_bytes"], 39516)
        self.assertEqual(statement["matched_frontier_typed_bytes"], 47188)
        self.assertEqual(statement["typed_saving_bytes"], 7672)
        self.assertEqual(statement["binary_raw_bytes"], 1084)
        self.assertEqual(statement["binary_raw_status"], gate.LOCAL_RECORD_STREAM_STATUS)

    def test_external_rows_are_not_proof_size_comparable(self) -> None:
        rows = {row["system"]: row for row in self.payload["external_baseline_status"]}

        self.assertEqual(set(rows), {"EZKL", "d64 external adapter surface", "Jolt Atlas", "NANOZK"})
        for row in rows.values():
            self.assertEqual(row["comparison_status"], "NOT_PROOF_SIZE_COMPARABLE")
        self.assertEqual(rows["EZKL"]["mutations_rejected"], 7)
        self.assertEqual(rows["NANOZK"]["paper_reported_d128_row_bytes"], 6900)

    def test_accounting_status_keeps_binary_guardrail(self) -> None:
        accounting = self.payload["accounting_status"]

        self.assertEqual(
            accounting["status"],
            "GO_LOCAL_TYPED_ACCOUNTING_PRESENT_NO_GO_UPSTREAM_BINARY_SERIALIZATION_CLAIM",
        )
        self.assertEqual(accounting["local_binary_accounting_artifact_count"], 4)
        self.assertIn(
            "NOT_UPSTREAM_STWO_SERIALIZATION_LOCAL_ACCOUNTING_RECORD_STREAM_ONLY",
            accounting["upstream_stwo_serialization_statuses"],
        )

    def test_all_declared_mutations_reject(self) -> None:
        self.assertEqual(self.payload["mutations_checked"], len(gate.MUTATION_NAMES))
        self.assertEqual(self.payload["mutations_rejected"], len(gate.MUTATION_NAMES))
        self.assertTrue(self.payload["all_mutations_rejected"])
        self.assertEqual([item["name"] for item in self.payload["mutation_results"]], list(gate.MUTATION_NAMES))
        self.assertTrue(all(item["rejected"] for item in self.payload["mutation_results"]))

        base = self.strip_mutation_summary(self.payload)
        for name, mutated in gate.mutation_cases(base):
            with self.assertRaises(gate.ProofPressureScalingClaimPackError, msg=name):
                gate.validate_payload(mutated, check_mutations=False)

    def test_rejects_metric_and_claim_drift_even_with_refreshed_commitment(self) -> None:
        payload = self.strip_mutation_summary(self.payload)
        payload["scale_signal"]["seq32_vs_d8_single_head"]["lookup_claim_growth"] = "1.000000"
        self.assert_rejects(payload, "lookup growth drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["route_matrix_signal"]["profiles_checked"] = 13
        self.assert_rejects(payload, "route matrix profile count drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["route_matrix_signal"]["d32_two_head_sequence_ladder"]["seq32_raw_saving_bytes"] = 26325
        self.assert_rejects(payload, "d32 seq32 raw saving drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["fused_vs_split_rows"][0]["typed_saving_bytes"] = 0
        self.assert_rejects(payload, "row typed saving arithmetic drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["external_baseline_status"][0]["comparison_status"] = "PROOF_SIZE_COMPARABLE"
        self.assert_rejects(payload, "external baseline marked comparable")

        payload = self.strip_mutation_summary(self.payload)
        payload["claim_boundary"] = payload["claim_boundary"].replace("NOT_NANOZK_WIN", "NANOZK_WIN")
        self.assert_rejects(payload, "claim boundary drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["non_claims"].remove("not a NANOZK proof-size win")
        self.assert_rejects(payload, "non-claims drift")

    def test_source_artifacts_are_bound_by_path_digest_and_size(self) -> None:
        artifacts = self.payload["source_artifacts"]
        self.assertEqual(tuple(artifact["id"] for artifact in artifacts), gate.EXPECTED_SOURCE_ARTIFACT_IDS)
        for artifact in artifacts:
            path = gate.ROOT / artifact["path"]
            self.assertTrue(path.is_file(), path)
            raw = path.read_bytes()
            self.assertEqual(gate.sha256(raw), artifact["sha256"])
            self.assertEqual(len(raw), artifact["size_bytes"])

        payload = self.strip_mutation_summary(self.payload)
        payload["source_artifacts"][0]["sha256"] = "0" * 64
        self.assert_rejects(payload, "source digest drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["source_artifacts"] = payload["source_artifacts"][1:]
        self.assert_rejects(payload, "source artifact id drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["source_artifacts"].append(copy.deepcopy(payload["source_artifacts"][0]))
        payload["source_artifacts"][-1]["id"] = "unexpected_extra_artifact"
        self.assert_rejects(payload, "source artifact id drift")

    def test_write_outputs_round_trip(self) -> None:
        gate.validate_payload(self.payload)
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR) as tmp:
            root = pathlib.Path(tmp)
            json_path = root / "claim.json"
            tsv_path = root / "claim.tsv"

            with self.assertRaisesRegex(gate.ProofPressureScalingClaimPackError, "output path must be"):
                gate.write_outputs(self.payload, json_path.relative_to(gate.ROOT), tsv_path.relative_to(gate.ROOT))

        original_json = gate.JSON_OUT.read_bytes() if gate.JSON_OUT.exists() else None
        original_tsv = gate.TSV_OUT.read_bytes() if gate.TSV_OUT.exists() else None
        try:
            gate.write_outputs(
                self.payload,
                gate.JSON_OUT.relative_to(gate.ROOT),
                gate.TSV_OUT.relative_to(gate.ROOT),
            )
            loaded = json.loads(gate.JSON_OUT.read_text(encoding="utf-8"))
            self.assertEqual(loaded, self.payload)
            self.assertIn("seq32_d128_statement_only_probe_b", gate.TSV_OUT.read_text(encoding="utf-8"))
        finally:
            if original_json is None:
                gate.JSON_OUT.unlink(missing_ok=True)
            else:
                gate.JSON_OUT.write_bytes(original_json)
            if original_tsv is None:
                gate.TSV_OUT.unlink(missing_ok=True)
            else:
                gate.TSV_OUT.write_bytes(original_tsv)

    def test_output_path_rejects_absolute_and_symlink_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(gate.ProofPressureScalingClaimPackError, "repo-relative"):
                gate.write_outputs(self.payload, pathlib.Path(tmp) / "x.json", gate.TSV_OUT.relative_to(gate.ROOT))

        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / "target.json"
            target.write_text("{}", encoding="utf-8")
            link = gate.JSON_OUT.with_name(f"{gate.JSON_OUT.name}.link-test")
            link.unlink(missing_ok=True)
            try:
                try:
                    link.symlink_to(target)
                except OSError as err:
                    self.skipTest(f"symlink creation is unavailable: {err}")
                with self.assertRaisesRegex(gate.ProofPressureScalingClaimPackError, "output path must be"):
                    gate.write_outputs(self.payload, link.relative_to(gate.ROOT), gate.TSV_OUT.relative_to(gate.ROOT))
            finally:
                link.unlink(missing_ok=True)

        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR) as tmp:
            target_dir = pathlib.Path(tmp) / "outside"
            target_dir.mkdir()
            link = gate.EVIDENCE_DIR / "claim-pack-parent-link-test"
            link.unlink(missing_ok=True)
            try:
                try:
                    link.symlink_to(target_dir, target_is_directory=True)
                except OSError as err:
                    self.skipTest(f"directory symlink creation is unavailable: {err}")
                with self.assertRaisesRegex(gate.ProofPressureScalingClaimPackError, "symlink components"):
                    gate._assert_no_symlink_components_for_output(link / "out.json", "output path")
            finally:
                link.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
