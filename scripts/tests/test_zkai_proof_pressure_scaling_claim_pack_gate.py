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
        self.assertEqual(summary["proof_size_comparable_external_rows"], 0)
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

    def test_fused_vs_split_rows_are_local_and_positive(self) -> None:
        rows = {row["row_id"]: row for row in self.payload["fused_vs_split_rows"]}
        attention_rows = [row for row in rows.values() if row["category"] == "attention_fused_vs_split"]

        self.assertEqual(len(attention_rows), 10)
        self.assertTrue(all(row["typed_saving_bytes"] > 0 for row in attention_rows))

        seq32 = rows["d8_two_head_seq32"]
        self.assertEqual(seq32["matched_frontier_typed_bytes"], 31712)
        self.assertEqual(seq32["typed_bytes"], 22916)
        self.assertEqual(seq32["typed_saving_bytes"], 8796)
        self.assertEqual(seq32["comparison_status"], "LOCAL_MATCHED_ATTENTION_SOURCE_PLUS_SIDECAR")

        native = rows["seq32_d128_native_single_proof"]
        self.assertEqual(native["typed_bytes"], 42068)
        self.assertEqual(native["matched_frontier_typed_bytes"], 47188)
        self.assertEqual(native["typed_saving_bytes"], 5120)

        statement = rows["seq32_d128_statement_only_probe_b"]
        self.assertEqual(statement["typed_bytes"], 39516)
        self.assertEqual(statement["matched_frontier_typed_bytes"], 47188)
        self.assertEqual(statement["typed_saving_bytes"], 7672)

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
        self.assertGreaterEqual(len(artifacts), 12)
        for artifact in artifacts:
            path = gate.ROOT / artifact["path"]
            self.assertTrue(path.is_file(), path)
            raw = path.read_bytes()
            self.assertEqual(gate.sha256(raw), artifact["sha256"])
            self.assertEqual(len(raw), artifact["size_bytes"])

        payload = self.strip_mutation_summary(self.payload)
        payload["source_artifacts"][0]["sha256"] = "0" * 64
        self.assert_rejects(payload, "source digest drift")

    def test_write_outputs_round_trip(self) -> None:
        gate.validate_payload(self.payload)
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR) as tmp:
            root = pathlib.Path(tmp)
            json_path = root / "claim.json"
            tsv_path = root / "claim.tsv"

            with self.assertRaisesRegex(gate.ProofPressureScalingClaimPackError, "output path must be"):
                gate.write_outputs(self.payload, json_path.relative_to(gate.ROOT), tsv_path.relative_to(gate.ROOT))

        gate.write_outputs(
            self.payload,
            gate.JSON_OUT.relative_to(gate.ROOT),
            gate.TSV_OUT.relative_to(gate.ROOT),
        )
        loaded = json.loads(gate.JSON_OUT.read_text(encoding="utf-8"))
        self.assertEqual(loaded, self.payload)
        self.assertIn("seq32_d128_statement_only_probe_b", gate.TSV_OUT.read_text(encoding="utf-8"))

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


if __name__ == "__main__":
    unittest.main()
