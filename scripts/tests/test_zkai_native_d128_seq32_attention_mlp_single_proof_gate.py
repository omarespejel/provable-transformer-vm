import copy
import unittest

from scripts import zkai_native_d128_seq32_attention_mlp_single_proof_gate as gate


class NativeD128Seq32AttentionMlpSingleProofGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = gate.build_payload()

    def test_payload_validates(self) -> None:
        gate.validate_payload(self.payload)

    def test_mutations_are_rejected(self) -> None:
        results = gate.run_mutations(self.payload)
        self.assertEqual(len(results), len(gate.mutation_cases()))
        self.assertTrue(all(result["rejected"] for result in results))

    def test_proof_json_saving_is_pinned(self) -> None:
        summary = self.payload["summary"]
        self.assertEqual(summary["single_proof_json_bytes"], 503_004)
        self.assertEqual(summary["split_proof_json_bytes"], 520_399)
        self.assertEqual(summary["proof_json_saving_bytes"], 17_395)
        self.assertEqual(summary["proof_json_ratio"], "0.966574")

    def test_typed_saving_is_pinned(self) -> None:
        summary = self.payload["summary"]
        self.assertEqual(summary["single_typed_bytes"], 204_564)
        self.assertEqual(summary["split_typed_bytes"], 209_172)
        self.assertEqual(summary["typed_saving_bytes"], 4_608)
        self.assertEqual(summary["typed_ratio"], "0.977970")

    def test_external_overclaim_rejected(self) -> None:
        candidate = copy.deepcopy(self.payload)
        candidate["summary"]["proof_size_comparable_external_rows"] = 1
        with self.assertRaises(gate.NativeD128Seq32SingleProofGateError):
            gate.validate_payload(candidate)

    def test_non_claim_removal_rejected(self) -> None:
        candidate = copy.deepcopy(self.payload)
        candidate["non_claims"] = candidate["non_claims"][:-1]
        with self.assertRaises(gate.NativeD128Seq32SingleProofGateError):
            gate.validate_payload(candidate)


if __name__ == "__main__":
    unittest.main()
