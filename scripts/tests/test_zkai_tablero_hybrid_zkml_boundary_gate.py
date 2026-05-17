import copy
import json
import tempfile
import unittest

from scripts import zkai_tablero_hybrid_zkml_boundary_gate as gate


class TableroHybridZkmlBoundaryGateTest(unittest.TestCase):
    def test_build_payload_records_typed_boundary_inventory(self) -> None:
        payload = gate.build_payload()
        self.assertEqual(payload["schema"], gate.SCHEMA)
        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertEqual(payload["typed_statement_schema"]["schema"], gate.BOUNDARY_SCHEMA)
        self.assertEqual(payload["summary"]["boundary_example_count"], 5)
        self.assertEqual(payload["summary"]["object_class_count"], 5)
        self.assertEqual(payload["summary"]["native_equivalent_rows"], 1)
        self.assertEqual(payload["summary"]["non_native_equivalent_rows"], 4)
        self.assertEqual(payload["summary"]["jstprove_statement_envelope_mutations_rejected"], 13)
        self.assertEqual(payload["summary"]["jstprove_statement_envelope_mutation_count"], 13)
        self.assertFalse(payload["summary"]["jolt_atlas_local_reproduced"])
        self.assertFalse(payload["summary"]["jolt_atlas_proof_size_available"])
        self.assertEqual(payload["summary"]["tablero_role"], "typed_statement_boundary_not_external_verifier")
        self.assertEqual(payload["mutation_count"], 10)
        self.assertEqual(payload["mutations_rejected"], 10)

    def test_boundary_examples_keep_object_classes_separate(self) -> None:
        rows = {row["statement_id"]: row for row in gate.build_payload()["boundary_examples"]}
        self.assertTrue(rows["stwo_two_proof_frontier_boundary"]["native_proof_equivalent"])
        self.assertEqual(rows["stwo_two_proof_frontier_boundary"]["primary_value"], 40_700)
        self.assertFalse(rows["compact_statement_chain_boundary"]["native_proof_equivalent"])
        self.assertEqual(rows["compact_statement_chain_boundary"]["primary_value"], 199_553)
        self.assertEqual(rows["jstprove_statement_envelope_boundary"]["primary_value"], 13)
        self.assertEqual(rows["gkr_dense_sidecar_boundary"]["primary_value"], 11_645)
        self.assertEqual(
            rows["jolt_atlas_self_attention_source_boundary"]["primary_value"],
            "cargo run --release --package jolt-atlas-core --example transformer",
        )

    def test_all_boundary_examples_have_required_fields_and_commitments(self) -> None:
        payload = gate.build_payload()
        expected = set(gate.REQUIRED_BINDING_FIELDS) | {"primary_metric", "primary_value", "statement_commitment"}
        for row in payload["boundary_examples"]:
            self.assertEqual(set(row), expected)
            self.assertEqual(row["statement_commitment"], gate.statement_commitment(row))
            for field in ("model_binding", "input_binding", "output_binding", "proof_object_binding"):
                self.assertEqual(set(row[field]), set(gate.BINDING_OBJECT_FIELDS))
                self.assertTrue(row[field]["commitment"].startswith("blake2b-256:"))

    def test_rejects_compact_statement_as_native(self) -> None:
        payload = gate.build_payload()
        gate.promote_compact_statement_as_native(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.TableroHybridBoundaryError, "native proof equivalence overclaim"):
            gate.validate_payload(payload)

    def test_rejects_missing_model_binding(self) -> None:
        payload = gate.build_payload()
        gate.remove_model_binding(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.TableroHybridBoundaryError, "field drift"):
            gate.validate_payload(payload)

    def test_rejects_missing_approximation_policy(self) -> None:
        payload = gate.build_payload()
        gate.erase_approximation_policy(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.TableroHybridBoundaryError, "approximation policy missing"):
            gate.validate_payload(payload)

    def test_rejects_backend_version_drift(self) -> None:
        payload = gate.build_payload()
        gate.mutate_backend_version(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.TableroHybridBoundaryError, "statement commitment drift"):
            gate.validate_payload(payload)

    def test_rejects_atlas_marked_local(self) -> None:
        payload = gate.build_payload()
        gate.mark_atlas_local(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.TableroHybridBoundaryError, "external source marked local"):
            gate.validate_payload(payload)

    def test_rejects_statement_commitment_drift(self) -> None:
        payload = gate.build_payload()
        gate.mutate_statement_commitment(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.TableroHybridBoundaryError, "statement commitment drift"):
            gate.validate_payload(payload)

    def test_rejects_unavailable_binding_field_removal(self) -> None:
        payload = gate.build_payload()
        gate.remove_unavailable_output_binding(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.TableroHybridBoundaryError, "output_binding field drift"):
            gate.validate_payload(payload)

    def test_rejects_atlas_proof_size_overclaim(self) -> None:
        payload = gate.build_payload()
        gate.promote_atlas_proof_size(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.TableroHybridBoundaryError, "Jolt Atlas proof-size overclaim"):
            gate.validate_payload(payload)

    def test_rejects_typed_schema_field_removal(self) -> None:
        payload = gate.build_payload()
        gate.remove_schema_field(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.TableroHybridBoundaryError, "typed schema required-field drift"):
            gate.validate_payload(payload)

    def test_rejects_global_non_claim_removal(self) -> None:
        payload = gate.build_payload()
        gate.remove_global_non_claim(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.TableroHybridBoundaryError, "Tablero non-claim drift"):
            gate.validate_payload(payload)

    def test_payload_commitment_rejects_drift(self) -> None:
        payload = gate.build_payload()
        payload["payload_commitment"] = "blake2b-256:" + "0" * 64
        with self.assertRaisesRegex(gate.TableroHybridBoundaryError, "payload commitment drift"):
            gate.validate_payload(payload)

    def test_mutation_inventory_is_strict(self) -> None:
        payload = gate.build_payload()
        payload["mutation_results"] = copy.deepcopy(payload["mutation_results"])
        payload["mutation_results"].pop()
        payload["mutation_count"] -= 1
        payload["mutations_rejected"] -= 1
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.TableroHybridBoundaryError, "mutation"):
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
        with self.assertRaisesRegex(gate.TableroHybridBoundaryError, "source artifact"):
            gate.write_outputs(gate.build_payload(), gate.MINIMAL_BENCHMARK, None)

    def test_rejects_wrong_output_suffix(self) -> None:
        payload = gate.build_payload()
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".txt", delete=False) as handle:
            path = gate.pathlib.Path(handle.name)
        try:
            with self.assertRaisesRegex(gate.TableroHybridBoundaryError, "JSON output"):
                gate.write_outputs(payload, path, None)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
