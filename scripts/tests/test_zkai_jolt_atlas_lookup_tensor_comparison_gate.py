import copy
import json
import tempfile
import unittest

from scripts import zkai_jolt_atlas_lookup_tensor_comparison_gate as gate


class JoltAtlasLookupTensorComparisonGateTest(unittest.TestCase):
    def test_build_payload_records_honest_source_backed_status(self) -> None:
        payload = gate.build_payload()
        self.assertEqual(payload["schema"], gate.SCHEMA)
        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertEqual(payload["summary"]["comparison_rows"], 8)
        self.assertEqual(payload["summary"]["local_rows"], 3)
        self.assertEqual(payload["summary"]["external_rows"], 5)
        self.assertFalse(payload["summary"]["atlas_local_reproduced"])
        self.assertFalse(payload["summary"]["atlas_proof_size_available"])
        self.assertFalse(payload["summary"]["matched_atlas_workload"])
        self.assertEqual(payload["summary"]["atlas_repo_head_commit"], gate.JOLT_ATLAS_REPO_HEAD)
        self.assertEqual(payload["summary"]["jolt_core_repo_head_commit"], gate.JOLT_CORE_REPO_HEAD)
        self.assertEqual(payload["summary"]["local_stwo_two_proof_frontier_typed_bytes"], 40_700)
        self.assertEqual(payload["summary"]["local_stwo_attention_lookup_typed_savings_bytes"], 51_288)
        self.assertEqual(payload["summary"]["local_gkr_tiny_gemm_proof_bytes"], 11_645)
        self.assertEqual(payload["summary"]["gkr_tiny_gemm_ratio_vs_stwo_two_proof_frontier"], "0.286118")
        self.assertEqual(payload["summary"]["atlas_readme_gpt2_proof_seconds"], "14.889")
        self.assertEqual(payload["summary"]["atlas_readme_nanogpt_proof_seconds"], "2.288")
        self.assertEqual(payload["mutation_count"], 8)
        self.assertEqual(payload["mutations_rejected"], 8)

    def test_rows_keep_object_classes_and_reproduction_statuses_separate(self) -> None:
        rows = {row["row_id"]: row for row in gate.build_payload()["rows"]}
        self.assertEqual(rows["local_stwo_attention_lookup_grid"]["primary_value"], 51_288)
        self.assertEqual(rows["local_stwo_minimal_block_frontier"]["primary_value"], 40_700)
        self.assertEqual(rows["local_gkr_dense_sidecar_tiny_gemm"]["primary_value"], 11_645)
        self.assertEqual(rows["jolt_core_zkvm_context"]["primary_value"], gate.JOLT_CORE_REPO_HEAD)
        self.assertEqual(rows["jolt_atlas_paper_architecture"]["source_status"], "paper_reported_not_locally_reproduced")
        self.assertEqual(rows["jolt_atlas_repo_gpt2_readme"]["primary_value"], "14.889")
        self.assertEqual(rows["jolt_atlas_repo_nanogpt_readme"]["primary_value"], "2.288")
        self.assertEqual(
            rows["jolt_atlas_repo_self_attention_example"]["primary_value"],
            "cargo run --release --package jolt-atlas-core --example transformer",
        )

    def test_rejects_atlas_reproduction_overclaim(self) -> None:
        payload = gate.build_payload()
        gate.promote_atlas_reproduced(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.JoltAtlasComparisonError, "reproduction overclaim"):
            gate.validate_payload(payload)

    def test_rejects_stwo_beats_atlas_overclaim(self) -> None:
        payload = gate.build_payload()
        gate.promote_stwo_beats_atlas(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.JoltAtlasComparisonError, "comparison overclaim"):
            gate.validate_payload(payload)

    def test_rejects_atlas_proof_size_overclaim(self) -> None:
        payload = gate.build_payload()
        gate.promote_atlas_proof_size(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.JoltAtlasComparisonError, "proof-size availability overclaim"):
            gate.validate_payload(payload)

    def test_rejects_external_row_marked_local(self) -> None:
        payload = gate.build_payload()
        gate.mark_jolt_row_local(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.JoltAtlasComparisonError, "external reproduction overclaim"):
            gate.validate_payload(payload)

    def test_rejects_repo_head_drift(self) -> None:
        payload = gate.build_payload()
        gate.mutate_atlas_repo_head(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.JoltAtlasComparisonError, "Atlas repo head drift"):
            gate.validate_payload(payload)

    def test_rejects_primary_source_removal(self) -> None:
        payload = gate.build_payload()
        gate.remove_primary_source(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.JoltAtlasComparisonError, "primary source inventory drift"):
            gate.validate_payload(payload)

    def test_rejects_object_class_collapse(self) -> None:
        payload = gate.build_payload()
        gate.collapse_object_class(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.JoltAtlasComparisonError, "object-class drift"):
            gate.validate_payload(payload)

    def test_rejects_non_claim_removal(self) -> None:
        payload = gate.build_payload()
        gate.remove_non_claim(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.JoltAtlasComparisonError, "proof-size non-claim drift"):
            gate.validate_payload(payload)

    def test_payload_commitment_rejects_drift(self) -> None:
        payload = gate.build_payload()
        payload["payload_commitment"] = "blake2b-256:" + "0" * 64
        with self.assertRaisesRegex(gate.JoltAtlasComparisonError, "commitment"):
            gate.validate_payload(payload)

    def test_mutation_inventory_is_strict(self) -> None:
        payload = gate.build_payload()
        payload["mutation_results"] = copy.deepcopy(payload["mutation_results"])
        payload["mutation_results"].pop()
        payload["mutation_count"] -= 1
        payload["mutations_rejected"] -= 1
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.JoltAtlasComparisonError, "mutation"):
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
        with self.assertRaisesRegex(gate.JoltAtlasComparisonError, "source artifact"):
            gate.write_outputs(gate.build_payload(), gate.MINIMAL_BENCHMARK, None)

    def test_rejects_wrong_output_suffix(self) -> None:
        payload = gate.build_payload()
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".txt", delete=False) as handle:
            path = gate.pathlib.Path(handle.name)
        try:
            with self.assertRaisesRegex(gate.JoltAtlasComparisonError, "JSON output"):
                gate.write_outputs(payload, path, None)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
