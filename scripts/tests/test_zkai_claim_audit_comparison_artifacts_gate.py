import json
import tempfile
import unittest
from copy import deepcopy

from scripts import zkai_claim_audit_comparison_artifacts_gate as gate


class ClaimAuditComparisonArtifactsGateTest(unittest.TestCase):
    def test_build_payload_records_comparison_audit_inventory(self) -> None:
        payload = gate.build_payload()
        self.assertEqual(payload["schema"], gate.SCHEMA)
        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertEqual(payload["result"], gate.RESULT)
        self.assertEqual(payload["summary"]["audit_row_count"], 13)
        self.assertEqual(payload["summary"]["object_class_count"], 10)
        self.assertEqual(payload["summary"]["proof_size_comparable_rows"], 0)
        self.assertEqual(payload["summary"]["stwo_two_proof_frontier_typed_bytes"], 40_700)
        self.assertEqual(payload["summary"]["nanozk_paper_reported_bytes"], 6_900)
        self.assertEqual(payload["summary"]["gkr_tiny_gemm_proof_bytes"], 11_645)
        self.assertEqual(payload["summary"]["gkr_tiny_residual_add_proof_bytes"], 56_054)
        self.assertEqual(payload["summary"]["gkr_tiny_layernorm_proof_bytes"], 52_080)
        self.assertEqual(payload["summary"]["worst_label_required_reduction_bytes"], 1_401)
        self.assertEqual(payload["mutation_count"], 13)
        self.assertEqual(payload["mutations_rejected"], 13)

    def test_audit_rows_keep_object_classes_and_reproduction_status_explicit(self) -> None:
        rows = gate.build_payload()["audit_rows"]
        self.assertEqual(len({row["row_id"] for row in rows}), len(rows))
        by_id = {row["row_id"]: row for row in rows}
        self.assertFalse(by_id["nanozk_paper_reported_context"]["locally_reproduced"])
        self.assertFalse(by_id["nanozk_paper_reported_context"]["proof_size_comparable"])
        self.assertFalse(by_id["jolt_atlas_self_attention_reproduction_target"]["locally_reproduced"])
        self.assertFalse(by_id["jolt_atlas_self_attention_reproduction_target"]["proof_size_comparable"])
        self.assertFalse(by_id["tablero_compact_statement_boundary"]["native_proof_equivalent"])
        self.assertFalse(by_id["tablero_compact_statement_boundary"]["proof_size_comparable"])
        self.assertFalse(by_id["gkr_tiny_gemm_sidecar"]["matched_workload"])
        self.assertFalse(by_id["gkr_tiny_gemm_sidecar"]["proof_size_comparable"])
        self.assertIn("single best label rejected", by_id["rmsnorm_single_best_label_rejected"]["proof_size_policy"])

    def test_mutation_inventory_is_strict(self) -> None:
        payload = gate.build_payload()
        mutation_names = [result["name"] for result in payload["mutation_results"]]
        self.assertEqual(mutation_names, [name for name, _ in gate.MUTATIONS])
        self.assertTrue(all(result["accepted"] is False for result in payload["mutation_results"]))

    def test_rejects_compact_statement_promoted_to_native(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_compact_statement_as_native(payload)
        with self.assertRaisesRegex(gate.ClaimAuditError, "compact statement promoted"):
            gate.validate_payload(payload, final=False)

    def test_rejects_paper_reported_nanozk_marked_local(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_nanozk_marked_local(payload)
        with self.assertRaisesRegex(gate.ClaimAuditError, "paper-reported row promoted"):
            gate.validate_payload(payload, final=False)

    def test_rejects_jolt_proof_size_comparable_without_local_run(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_jolt_proof_size_comparable(payload)
        with self.assertRaisesRegex(gate.ClaimAuditError, "external lookup row promoted"):
            gate.validate_payload(payload, final=False)

    def test_rejects_gkr_fixture_promoted_to_matched_d128(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_gkr_matched_d128(payload)
        with self.assertRaisesRegex(gate.ClaimAuditError, "GKR fixture promoted"):
            gate.validate_payload(payload, final=False)

    def test_rejects_missing_object_class(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_missing_object_class(payload)
        with self.assertRaisesRegex(gate.ClaimAuditError, "row field drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_missing_timing_policy(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_missing_timing_policy(payload)
        with self.assertRaisesRegex(gate.ClaimAuditError, "timing policy"):
            gate.validate_payload(payload, final=False)

    def test_rejects_single_best_label_promotion(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_single_best_label_promoted(payload)
        with self.assertRaisesRegex(gate.ClaimAuditError, "favorable-label policy drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_required_non_claim_removal(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_remove_nanozk_non_claim(payload)
        with self.assertRaisesRegex(gate.ClaimAuditError, "global non-claim drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_external_native_equivalence(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_external_native_equivalence(payload)
        with self.assertRaisesRegex(gate.ClaimAuditError, "native equivalence overclaim"):
            gate.validate_payload(payload, final=False)

    def test_rejects_source_artifact_digest_drift(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_source_artifact_digest(payload)
        with self.assertRaisesRegex(gate.ClaimAuditError, "source artifact file digest drift"):
            gate.validate_payload(payload, final=False)

    def test_payload_commitment_rejects_drift(self) -> None:
        payload = gate.build_payload()
        payload["payload_commitment"] = "blake2b-256:" + "0" * 64
        with self.assertRaisesRegex(gate.ClaimAuditError, "payload commitment drift"):
            gate.validate_payload(payload)

    def test_tsv_columns_are_stable(self) -> None:
        self.assertEqual(gate.tsv_text(gate.build_payload()).splitlines()[0].split("\t"), list(gate.ROW_COLUMNS))

    def test_write_outputs_round_trips(self) -> None:
        payload = gate.build_payload()
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".json", delete=False) as json_handle:
            json_path = gate.pathlib.Path(json_handle.name)
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".tsv", delete=False) as tsv_handle:
            tsv_path = gate.pathlib.Path(tsv_handle.name)
        try:
            gate.write_outputs(payload, json_path, tsv_path)
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8")), payload)
            self.assertTrue(tsv_path.read_text(encoding="utf-8").startswith("\t".join(gate.ROW_COLUMNS)))
        finally:
            json_path.unlink(missing_ok=True)
            tsv_path.unlink(missing_ok=True)

    def test_rejects_output_source_overwrite(self) -> None:
        with self.assertRaisesRegex(gate.ClaimAuditError, "source artifact"):
            gate.write_outputs(gate.build_payload(), gate.MINIMAL_BENCHMARK, None)

    def test_rejects_wrong_output_suffix(self) -> None:
        payload = gate.build_payload()
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".txt", delete=False) as handle:
            path = gate.pathlib.Path(handle.name)
        try:
            with self.assertRaisesRegex(gate.ClaimAuditError, "JSON output"):
                gate.write_outputs(payload, path, None)
        finally:
            path.unlink(missing_ok=True)

    def test_rejects_mutation_inventory_drift(self) -> None:
        payload = gate.build_payload()
        payload["mutation_results"] = deepcopy(payload["mutation_results"])
        payload["mutation_results"].pop()
        payload["mutation_count"] -= 1
        payload["mutations_rejected"] -= 1
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.ClaimAuditError, "mutation inventory drift"):
            gate.validate_payload(payload)


if __name__ == "__main__":
    unittest.main()
