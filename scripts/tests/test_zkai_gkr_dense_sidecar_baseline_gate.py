import copy
import json
import tempfile
import unittest

from scripts import zkai_gkr_dense_sidecar_baseline_gate as gate


class GkrDenseSidecarBaselineGateTest(unittest.TestCase):
    def test_build_payload_records_honest_frontier(self) -> None:
        payload = gate.build_payload()
        self.assertEqual(payload["schema"], gate.SCHEMA)
        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertFalse(payload["summary"]["matched_d128_dense_layer_comparison"])
        self.assertEqual(payload["summary"]["local_stwo_dense_typed_bytes"], 22_576)
        self.assertEqual(payload["summary"]["jstprove_tiny_gemm_proof_bytes"], 11_645)
        self.assertEqual(payload["summary"]["jstprove_tiny_gemm_ratio_vs_stwo_dense_typed"], "0.515813")
        self.assertEqual(payload["summary"]["jstprove_residual_add_proof_bytes"], 56_054)
        self.assertEqual(payload["summary"]["jstprove_layernorm_proof_bytes"], 52_080)
        self.assertEqual(payload["summary"]["comparison_rows"], 10)
        self.assertEqual(payload["mutation_count"], 6)
        self.assertEqual(payload["mutations_rejected"], 6)

    def test_rows_include_go_and_no_go_gkr_shapes(self) -> None:
        rows = {row["row_id"]: row for row in gate.build_payload()["rows"]}
        self.assertEqual(rows["local_stwo_dense_substitute"]["primary_value"], 22_576)
        self.assertEqual(rows["tiny_gemm"]["status"], "GO")
        self.assertEqual(rows["tiny_gemm_add"]["primary_value"], 36_449)
        self.assertEqual(rows["tiny_gemm_residual_add"]["primary_value"], 56_054)
        self.assertEqual(rows["tiny_gemm_layernorm"]["primary_value"], 52_080)
        self.assertEqual(rows["tiny_gemm_relu"]["primary_metric"], "range_check_capacity")
        self.assertEqual(rows["tiny_gemm_softmax"]["primary_metric"], "unconstrained_backend_op")
        self.assertEqual(rows["tiny_matmul_residual_add"]["primary_metric"], "unsupported_witness_op")
        self.assertEqual(rows["jstprove_statement_envelope_binding"]["primary_value"], 13)

    def test_rejects_matched_comparison_overclaim(self) -> None:
        payload = gate.build_payload()
        gate.promote_matched_comparison(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.GkrDenseBaselineError, "matched comparison"):
            gate.validate_payload(payload)

    def test_rejects_gkr_replacement_overclaim(self) -> None:
        payload = gate.build_payload()
        gate.promote_gkr_replacement(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.GkrDenseBaselineError, "summary"):
            gate.validate_payload(payload)

    def test_rejects_row_comparability_overclaim(self) -> None:
        payload = gate.build_payload()
        gate.promote_row_comparability(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.GkrDenseBaselineError, "rows"):
            gate.validate_payload(payload)

    def test_rejects_no_go_removal(self) -> None:
        payload = gate.build_payload()
        gate.remove_softmax_no_go(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.GkrDenseBaselineError, "rows"):
            gate.validate_payload(payload)

    def test_rejects_non_claim_removal(self) -> None:
        payload = gate.build_payload()
        gate.remove_non_claim(payload)
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.GkrDenseBaselineError, "non_claims"):
            gate.validate_payload(payload)

    def test_payload_commitment_rejects_drift(self) -> None:
        payload = gate.build_payload()
        payload["payload_commitment"] = "blake2b-256:" + "0" * 64
        with self.assertRaisesRegex(gate.GkrDenseBaselineError, "commitment"):
            gate.validate_payload(payload)

    def test_mutation_inventory_is_strict(self) -> None:
        payload = gate.build_payload()
        payload["mutation_results"] = copy.deepcopy(payload["mutation_results"])
        payload["mutation_results"].pop()
        payload["mutation_count"] -= 1
        payload["mutations_rejected"] -= 1
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaisesRegex(gate.GkrDenseBaselineError, "mutation"):
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
        with self.assertRaisesRegex(gate.GkrDenseBaselineError, "source artifact"):
            gate.write_outputs(gate.build_payload(), gate.MINIMAL_BENCHMARK, None)

    def test_rejects_wrong_output_suffix(self) -> None:
        payload = gate.build_payload()
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".txt", delete=False) as handle:
            path = gate.pathlib.Path(handle.name)
        try:
            with self.assertRaisesRegex(gate.GkrDenseBaselineError, "JSON output"):
                gate.write_outputs(payload, path, None)
        finally:
            path.unlink(missing_ok=True)

    def test_rejects_missing_summary_row_with_gate_error(self) -> None:
        payload = gate.build_payload()
        rows = [row for row in payload["rows"] if row["row_id"] != "tiny_gemm"]
        with self.assertRaisesRegex(gate.GkrDenseBaselineError, "missing summary row: tiny_gemm"):
            gate.build_summary(rows, gate.load_sources())

    def test_rejects_shape_count_drift(self) -> None:
        sources = gate.load_sources()
        rows = gate.build_rows(sources)
        sources["shape"] = copy.deepcopy(sources["shape"])
        del sources["shape"]["conclusion"]["go_count"]
        with self.assertRaisesRegex(gate.GkrDenseBaselineError, "shape go_count"):
            gate.build_summary(rows, sources)

    def test_rejects_shape_count_mismatch(self) -> None:
        sources = gate.load_sources()
        rows = gate.build_rows(sources)
        sources["shape"] = copy.deepcopy(sources["shape"])
        sources["shape"]["conclusion"]["go_count"] += 1
        with self.assertRaisesRegex(gate.GkrDenseBaselineError, "fixture counts drift"):
            gate.build_summary(rows, sources)


if __name__ == "__main__":
    unittest.main()
