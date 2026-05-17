import copy
import tempfile
import unittest

from scripts import zkai_native_attention_mlp_rmsnorm_adjacent_layout_gate as gate


class RmsnormAdjacentLayoutGateTest(unittest.TestCase):
    def test_build_payload_records_no_go_and_layout_saving(self) -> None:
        payload = gate.build_payload()
        self.assertEqual(
            payload["decision"],
            "NO_GO_WORST_LABEL_FRONTIER_PROMOTION_BUT_GO_LAYOUT_LEVER",
        )
        self.assertEqual(payload["adjacent_canonical_typed_bytes"], 40_948)
        self.assertEqual(payload["adjacent_canonical_saving_vs_canonical_typed_bytes"], 480)
        self.assertEqual(payload["adjacent_canonical_delta_vs_frontier_typed_bytes"], 248)
        self.assertEqual(payload["adjacent_worst_label_typed_bytes"], 42_724)
        self.assertEqual(payload["adjacent_worst_label_delta_vs_frontier_typed_bytes"], 2_024)
        self.assertEqual(payload["adjacent_label_span_typed_bytes"], 1_776)
        self.assertEqual(len(payload["mutation_results"]), 12)
        self.assertTrue(all(entry["rejected"] for entry in payload["mutation_results"]))

    def test_payload_rejects_frontier_overclaim(self) -> None:
        payload = gate.build_payload()
        payload["decision"] = "GO_FRONTIER_PROMOTION"
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaises(gate.AdjacentLayoutGateError):
            gate.validate_payload(payload)

    def test_payload_rejects_worst_label_erasure(self) -> None:
        payload = gate.build_payload()
        payload["adjacent_worst_label_typed_bytes"] = 40_699
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaises(gate.AdjacentLayoutGateError):
            gate.validate_payload(payload)

    def test_payload_rejects_group_drift(self) -> None:
        payload = gate.build_payload()
        payload["variants"]["adjacent_layout"]["typed_groups"]["fri_decommitments"] = 0
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaises(gate.AdjacentLayoutGateError):
            gate.validate_payload(payload)

    def test_payload_rejects_top_level_summary_drift(self) -> None:
        for key, value in (
            ("compact_selector_typed_bytes", 1),
            ("canonical_rmsnorm_input_fused_typed_bytes", 1),
            ("adjacent_canonical_typed_bytes", 1),
            ("source_accounting_path", "docs/engineering/evidence/other.json"),
        ):
            with self.subTest(key=key):
                payload = gate.build_payload()
                payload[key] = value
                payload["payload_commitment"] = gate.payload_commitment(payload)
                with self.assertRaises(gate.AdjacentLayoutGateError):
                    gate.validate_payload(payload)

    def test_payload_rejects_non_claim_erasure(self) -> None:
        payload = gate.build_payload()
        payload["non_claims"] = []
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaises(gate.AdjacentLayoutGateError):
            gate.validate_payload(payload)

    def test_payload_rejects_partial_non_claim_erasure(self) -> None:
        payload = gate.build_payload()
        payload["non_claims"] = [
            "not a proof-size win",
            "does not close issue 644",
        ]
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaises(gate.AdjacentLayoutGateError):
            gate.validate_payload(payload)

    def test_payload_rejects_non_claim_type_drift(self) -> None:
        payload = gate.build_payload()
        payload["non_claims"] = None
        payload["payload_commitment"] = gate.payload_commitment(payload)
        with self.assertRaises(gate.AdjacentLayoutGateError):
            gate.validate_payload(payload)

    def test_payload_rejects_commitment_drift(self) -> None:
        payload = gate.build_payload()
        payload["payload_commitment"] = "blake2b-256:" + "0" * 64
        with self.assertRaises(gate.AdjacentLayoutGateError):
            gate.validate_payload(payload)

    def test_mutation_inventory_is_exact(self) -> None:
        payload = gate.build_payload()
        mutations = copy.deepcopy(payload["mutation_results"])
        mutations.append({"name": "extra", "rejected": True, "reason": "extra"})
        with self.assertRaises(gate.AdjacentLayoutGateError):
            gate.validate_mutation_results(mutations)

    def test_mutation_inventory_rejects_non_object_entries(self) -> None:
        payload = gate.build_payload()
        mutations = copy.deepcopy(payload["mutation_results"])
        mutations[-1] = "not an object"
        with self.assertRaises(gate.AdjacentLayoutGateError):
            gate.validate_mutation_results(mutations)

    def test_payload_can_validate_without_mutation_inventory(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        self.assertEqual(payload["mutation_results"], [])
        gate.validate_payload(payload, require_mutations=False)
        with self.assertRaises(gate.AdjacentLayoutGateError):
            gate.validate_payload(payload)

    def test_read_input_bytes_rejects_oversized_artifact(self) -> None:
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".json", delete=False) as handle:
            path = gate.pathlib.Path(handle.name)
            handle.truncate(gate.MAX_INPUT_JSON_BYTES + 1)
        try:
            with self.assertRaises(gate.AdjacentLayoutGateError):
                gate.read_input_bytes(path)
        finally:
            path.unlink(missing_ok=True)

    def test_tsv_includes_adjacent_bad_label(self) -> None:
        payload = gate.build_payload()
        text = gate.tsv_text(payload)
        self.assertIn("adjacent_label_probe_b\t42724\t2024\t21808", text)
        self.assertIn("no_go_worst_label", text)

    def test_write_outputs_rejects_non_evidence_path(self) -> None:
        payload = gate.build_payload()
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(gate.AdjacentLayoutGateError):
                gate.write_outputs(payload, gate.pathlib.Path(tmpdir) / "payload.json", None)


if __name__ == "__main__":
    unittest.main()
