import copy
import hashlib
import json
import os
import tempfile
import types
import unittest
from unittest import mock

from scripts import zkai_minimal_transformer_block_benchmark_gate as gate


class MinimalTransformerBlockBenchmarkGateTest(unittest.TestCase):
    def test_build_payload_records_contract_and_missing_native_block(self) -> None:
        payload = gate.build_payload()
        self.assertEqual(payload["schema"], gate.SCHEMA)
        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertEqual(payload["result"], gate.RESULT)
        self.assertEqual(payload["summary"]["component_count"], 10)
        self.assertEqual(payload["summary"]["proof_component_count"], 2)
        self.assertTrue(payload["summary"]["missing_native_block_proof_object"])
        self.assertEqual(payload["summary"]["two_proof_frontier_typed_bytes"], 40_700)
        self.assertEqual(payload["summary"]["adjacent_worst_label_gap_typed_bytes"], 2_024)
        self.assertEqual(payload["summary"]["gap_to_nanozk_from_two_proof_frontier_typed_bytes"], 33_800)
        self.assertEqual(
            payload["summary"]["adjacent_worst_label_gap_typed_bytes"],
            payload["summary"]["adjacent_worst_label_typed_bytes"]
            - payload["summary"]["two_proof_frontier_typed_bytes"],
        )
        self.assertEqual(
            payload["summary"]["gap_to_nanozk_from_two_proof_frontier_typed_bytes"],
            payload["summary"]["two_proof_frontier_typed_bytes"]
            - payload["summary"]["nanozk_reported_d128_block_proof_bytes"],
        )
        self.assertEqual(payload["summary"]["statement_chain_rows"], 199_553)
        self.assertEqual(payload["summary"]["external_statement_receipt_proof_bytes"], 807)
        self.assertEqual(payload["mutation_count"], 14)
        self.assertEqual(payload["mutations_rejected"], 14)
        self.assertTrue(all(entry["rejected"] for entry in payload["mutation_results"]))

    def test_spec_makes_approximations_and_statement_bindings_explicit(self) -> None:
        spec = gate.build_payload()["benchmark_spec"]
        self.assertEqual(spec["model_width"], 128)
        self.assertEqual(spec["attention_source_width"], 8)
        self.assertEqual(spec["ffn_width"], 512)
        self.assertIn("RMSNorm substitute for LayerNorm", spec["component_contract"])
        self.assertIn("not exact real-valued Softmax", spec["approximation_policy"]["attention"])
        self.assertIn("not exact LayerNorm", spec["approximation_policy"]["normalization"])
        self.assertIn("not exact GELU", spec["approximation_policy"]["activation"])
        self.assertIn("proof_commitment_or_receipt_commitment", spec["public_statement_bindings"])

    def test_rows_classify_object_classes_without_external_overclaim(self) -> None:
        rows = {row["component"]: row for row in gate.build_payload()["component_rows"]}
        self.assertEqual(rows["attention_boundary_and_softmax_lookup"]["object_class"], "local_native_stwo_proof_component")
        self.assertEqual(rows["two_proof_frontier"]["object_class"], "local_two_proof_target")
        self.assertEqual(rows["typed_public_statement_chain"]["object_class"], "local_statement_artifact")
        self.assertEqual(rows["external_statement_receipt"]["object_class"], "external_snark_statement_receipt")
        self.assertEqual(rows["native_full_block_proof_object"]["object_class"], "missing_native_proof_object")
        self.assertIsNone(rows["native_full_block_proof_object"]["primary_value"])
        self.assertEqual(rows["nanozk_context_row"]["comparability"], "CONTEXT_ONLY_NOT_LOCAL_REPRODUCTION_NOT_MATCHED_WORKLOAD")
        self.assertEqual(
            rows["nanozk_context_row"]["evidence_path"],
            "docs/engineering/evidence/zkai-d128-attention-mlp-boundary-frontier-2026-05.json",
        )
        self.assertEqual(rows["gkr_hyrax_sidecar_lane"]["local_status"], "FOLLOWUP_ISSUE_650_NOT_IMPLEMENTED")
        self.assertEqual(rows["jolt_atlas_lookup_tensor_lane"]["local_status"], "FOLLOWUP_ISSUE_651_NOT_IMPLEMENTED")

    def test_rejects_component_omission(self) -> None:
        payload = gate.build_payload()
        payload["component_rows"] = [
            row for row in payload["component_rows"] if row["component"] != "attention_boundary_and_softmax_lookup"
        ]
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaises(gate.MinimalBlockBenchmarkError):
            gate.validate_payload(payload)

    def test_accepts_component_rows_reordered_by_stable_component_key(self) -> None:
        payload = gate.build_payload()
        payload["component_rows"] = list(reversed(payload["component_rows"]))
        payload["payload_commitment"] = gate.payload_commitment(payload)
        gate.validate_payload(payload)

    def test_rejects_duplicate_component_rows(self) -> None:
        payload = gate.build_payload()
        payload["component_rows"][-1] = copy.deepcopy(payload["component_rows"][0])
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.MinimalBlockBenchmarkError, "duplicate component"):
            gate.validate_payload(payload)

    def test_rejects_native_block_proof_promotion(self) -> None:
        payload = gate.build_payload()
        rows = {row["component"]: row for row in payload["component_rows"]}
        native = rows["native_full_block_proof_object"]
        native["object_class"] = "local_native_stwo_proof_object"
        native["primary_value"] = 6_900
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaises(gate.MinimalBlockBenchmarkError):
            gate.validate_payload(payload)

    def test_rejects_false_nanozk_comparability(self) -> None:
        payload = gate.build_payload()
        rows = {row["component"]: row for row in payload["component_rows"]}
        rows["nanozk_context_row"]["comparability"] = "MATCHED_EXTERNAL_BENCHMARK"
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaises(gate.MinimalBlockBenchmarkError):
            gate.validate_payload(payload)

    def test_rejects_approximation_policy_removal(self) -> None:
        payload = gate.build_payload()
        payload["benchmark_spec"]["approximation_policy"] = {}
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaises(gate.MinimalBlockBenchmarkError):
            gate.validate_payload(payload)

    def test_rejects_statement_binding_removal(self) -> None:
        payload = gate.build_payload()
        payload["benchmark_spec"]["public_statement_bindings"] = []
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaises(gate.MinimalBlockBenchmarkError):
            gate.validate_payload(payload)

    def test_rejects_source_digest_drift(self) -> None:
        payload = gate.build_payload()
        target = next(
            artifact
            for artifact in payload["source_artifacts"]
            if artifact["path"] == str(gate.ONE_BLOCK_SURFACE.relative_to(gate.ROOT))
        )
        target["file_sha256"] = "0" * 64
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaises(gate.MinimalBlockBenchmarkError):
            gate.validate_payload(payload)

    def test_rejects_missing_native_block_row_with_domain_error(self) -> None:
        payload = gate.build_payload()
        payload["component_rows"] = [
            row for row in payload["component_rows"] if row["component"] != "native_full_block_proof_object"
        ]
        payload["component_rows"].append(
            {
                "component": "native_full_block_placeholder",
                "object_class": "missing_native_proof_object",
                "local_status": "NO_GO_NATIVE_BLOCK_PROOF_OBJECT_MISSING",
                "proof_system": "Stwo/STARK",
                "evidence_path": "",
                "primary_metric": "native_block_proof_bytes",
                "primary_value": None,
                "comparability": "REQUIRED_BEFORE_NANOZK_OR_JOLT_PROOF_SIZE_COMPARISON",
                "claim_boundary": "placeholder",
            }
        )
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.MinimalBlockBenchmarkError, "native_full_block_proof_object"):
            gate.validate_payload(payload)

    def test_rejects_malformed_component_row_with_domain_error(self) -> None:
        payload = gate.build_payload()
        payload["component_rows"][0] = {"object_class": "local_native_stwo_proof_component"}
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.MinimalBlockBenchmarkError, "component row"):
            gate.validate_payload(payload)

    def test_rejects_non_object_component_row_with_domain_error(self) -> None:
        payload = gate.build_payload()
        payload["component_rows"][0] = "native_full_block_proof_object"
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.MinimalBlockBenchmarkError, "component row"):
            gate.validate_payload(payload)

    def test_rejects_non_claim_removal(self) -> None:
        payload = gate.build_payload()
        payload["non_claims"].remove("not a NANOZK proof-size win")
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaises(gate.MinimalBlockBenchmarkError):
            gate.validate_payload(payload)

    def test_rejects_mutation_result_type_drift(self) -> None:
        payload = gate.build_payload()
        payload["mutation_results"] = copy.deepcopy(payload["mutation_results"])
        payload["mutation_results"][-1] = "not an object"
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaises(gate.MinimalBlockBenchmarkError):
            gate.validate_payload(payload)

    def test_tsv_contains_object_class_rows(self) -> None:
        text = gate.tsv_text(gate.build_payload())
        self.assertIn("native_full_block_proof_object\tmissing_native_proof_object", text)
        self.assertIn("nanozk_context_row\tpaper_reported_external_context", text)
        self.assertIn("gkr_hyrax_sidecar_lane\tfollowup_hypothesis", text)

    def test_source_descriptor_uses_supplied_snapshot_bytes(self) -> None:
        payload = {"schema": "unit-test", "decision": "GO"}
        raw = b'{"schema":"unit-test","decision":"GO"}'
        with mock.patch.object(gate, "read_source_bytes", side_effect=AssertionError("unexpected reread")):
            descriptor = gate.source_descriptor(gate.ONE_BLOCK_SURFACE, payload, raw)
        self.assertEqual(descriptor["file_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(descriptor["payload_sha256"], hashlib.sha256(gate.canonical_json_bytes(payload)).hexdigest())

    def test_write_outputs_round_trips(self) -> None:
        payload = gate.build_payload()
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".json", delete=False) as json_handle:
            json_path = gate.pathlib.Path(json_handle.name)
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".tsv", delete=False) as tsv_handle:
            tsv_path = gate.pathlib.Path(tsv_handle.name)
        try:
            gate.write_outputs(payload, json_path, tsv_path)
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8")), payload)
            self.assertTrue(tsv_path.read_text(encoding="utf-8").startswith("\t".join(gate.TSV_COLUMNS)))
        finally:
            json_path.unlink(missing_ok=True)
            tsv_path.unlink(missing_ok=True)

    def test_write_outputs_rejects_symlink_path(self) -> None:
        payload = gate.build_payload()
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".json", delete=False) as handle:
            target = gate.pathlib.Path(handle.name)
        link = target.with_name(f"{target.name}.link.json")
        try:
            link.symlink_to(target)
            with self.assertRaises(gate.MinimalBlockBenchmarkError):
                gate.write_outputs(payload, link, None)
        finally:
            link.unlink(missing_ok=True)
            target.unlink(missing_ok=True)

    def test_write_outputs_resolves_repo_relative_path_from_root(self) -> None:
        payload = gate.build_payload()
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".json", delete=False) as handle:
            path = gate.pathlib.Path(handle.name)
        path.unlink()
        relative = path.relative_to(gate.ROOT)
        previous_cwd = os.getcwd()
        try:
            os.chdir(gate.ROOT / "scripts")
            gate.write_outputs(payload, relative, None)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), payload)
        finally:
            os.chdir(previous_cwd)
            path.unlink(missing_ok=True)

    def test_write_outputs_rejects_wrong_suffixes(self) -> None:
        payload = gate.build_payload()
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".tsv", delete=False) as handle:
            wrong_json_path = gate.pathlib.Path(handle.name)
        try:
            with self.assertRaisesRegex(gate.MinimalBlockBenchmarkError, "JSON output"):
                gate.write_outputs(payload, wrong_json_path, None)
        finally:
            wrong_json_path.unlink(missing_ok=True)

    def test_write_outputs_rejects_colliding_targets(self) -> None:
        payload = gate.build_payload()
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".json", delete=False) as handle:
            path = gate.pathlib.Path(handle.name)
        try:
            with self.assertRaisesRegex(gate.MinimalBlockBenchmarkError, "collide"):
                gate.write_outputs(payload, path, path)
        finally:
            path.unlink(missing_ok=True)

    def test_write_outputs_rejects_source_artifact_overwrite(self) -> None:
        payload = gate.build_payload()
        source = gate.ROOT / payload["source_artifacts"][0]["path"]
        with self.assertRaisesRegex(gate.MinimalBlockBenchmarkError, "source artifact"):
            gate.write_outputs(payload, source, None)

    def test_write_outputs_rejects_canonical_source_overwrite_even_if_payload_hides_it(self) -> None:
        payload = gate.build_payload()
        payload["source_artifacts"] = []
        with self.assertRaisesRegex(gate.MinimalBlockBenchmarkError, "source artifact"):
            gate.write_outputs(payload, gate.ONE_BLOCK_SURFACE, None)

    def test_read_source_bytes_rejects_in_place_rewrite_drift(self) -> None:
        original_fstat = gate.os.fstat
        calls = 0

        def drifting_fstat(fd: int) -> types.SimpleNamespace:
            nonlocal calls
            calls += 1
            current = original_fstat(fd)
            return types.SimpleNamespace(
                st_dev=current.st_dev,
                st_ino=current.st_ino,
                st_mode=current.st_mode,
                st_size=current.st_size,
                st_mtime_ns=current.st_mtime_ns + (1 if calls >= 2 else 0),
                st_ctime_ns=current.st_ctime_ns,
            )

        with mock.patch.object(gate.os, "fstat", side_effect=drifting_fstat):
            with self.assertRaises(gate.MinimalBlockBenchmarkError):
                gate.read_source_bytes(gate.ONE_BLOCK_SURFACE)


if __name__ == "__main__":
    unittest.main()
