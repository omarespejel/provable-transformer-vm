import copy
import unittest

from scripts import zkai_native_attention_mlp_rmsnorm_input_fused_adapter_gate as gate


class RmsnormInputFusedAdapterGateTests(unittest.TestCase):
    def test_payload_validates_and_rejects_mutations(self) -> None:
        context = gate.build_context()
        payload = gate.build_payload(context)
        gate.validate_payload(payload, context=context)
        self.assertEqual(payload["summary"]["fused_typed_bytes"], 41_428)
        self.assertEqual(payload["summary"]["fused_typed_delta_vs_compact_bytes"], 616)
        self.assertEqual(payload["summary"]["fused_typed_delta_vs_two_proof_frontier_bytes"], 728)
        self.assertEqual(payload["summary"]["fused_adapter_trace_cells"], 0)
        cases = payload["mutation_result"]["cases"]
        self.assertEqual([case["name"] for case in cases], list(gate.MUTATION_NAMES))
        self.assertTrue(all(case["rejected"] for case in cases))

    def test_frontier_overclaim_is_rejected(self) -> None:
        context = gate.build_context()
        expected = gate.build_payload(context)
        candidate = copy.deepcopy(expected)
        candidate["comparisons"]["fused_vs_two_proof_frontier"]["frontier_win_claimed"] = True
        candidate["payload_commitment"] = expected["payload_commitment"]
        with self.assertRaises(gate.RmsnormInputFusedAdapterGateError):
            gate.validate_payload(candidate, context=context)

    def test_compact_win_overclaim_is_rejected(self) -> None:
        context = gate.build_context()
        expected = gate.build_payload(context)
        candidate = copy.deepcopy(expected)
        candidate["comparisons"]["fused_vs_compact"]["proof_size_improvement_claimed"] = True
        candidate["payload_commitment"] = expected["payload_commitment"]
        with self.assertRaises(gate.RmsnormInputFusedAdapterGateError):
            gate.validate_payload(candidate, context=context)

    def test_duplicate_accounting_row_path_is_rejected(self) -> None:
        context = gate.build_context()
        accounting = copy.deepcopy(context["accounting"])
        accounting["rows"][1]["evidence_relative_path"] = accounting["rows"][0][
            "evidence_relative_path"
        ]

        with self.assertRaisesRegex(gate.RmsnormInputFusedAdapterGateError, "duplicate accounting row path"):
            gate.accounting_rows_by_path(accounting)

    def test_missing_accounting_row_is_rejected(self) -> None:
        context = gate.build_context()
        accounting = copy.deepcopy(context["accounting"])
        accounting["rows"].pop()

        with self.assertRaisesRegex(gate.RmsnormInputFusedAdapterGateError, "accounting row path drift"):
            gate.accounting_rows_by_path(accounting)


if __name__ == "__main__":
    unittest.main()
