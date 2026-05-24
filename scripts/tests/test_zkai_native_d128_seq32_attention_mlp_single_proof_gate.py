import copy
import os
import tempfile
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
        self.assertEqual(summary["single_proof_json_bytes"], 504_518)
        self.assertEqual(summary["split_proof_json_bytes"], 520_399)
        self.assertEqual(summary["proof_json_saving_bytes"], 15_881)
        self.assertEqual(summary["proof_json_ratio"], "0.969483")

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

    def test_source_artifact_drift_rejected_even_with_recomputed_commitment(self) -> None:
        candidate = copy.deepcopy(self.payload)
        candidate["source_artifacts"][0]["sha256"] = "0" * 64
        candidate["payload_commitment"] = gate.payload_commitment(candidate)
        with self.assertRaises(gate.NativeD128Seq32SingleProofGateError):
            gate.validate_payload(candidate)

    def test_bounded_repo_read_accepts_exact_cap_and_rejects_over_cap(self) -> None:
        handle = tempfile.NamedTemporaryFile(prefix=".codex-gate-cap-", dir=gate.ROOT, delete=False)
        try:
            with handle:
                handle.write(b"abcd")
            self.assertEqual(gate.read_repo_file(gate.ROOT / handle.name, "test artifact", max_bytes=4), b"abcd")
            with self.assertRaises(gate.NativeD128Seq32SingleProofGateError):
                gate.read_repo_file(gate.ROOT / handle.name, "test artifact", max_bytes=3)
        finally:
            os.unlink(gate.ROOT / handle.name)

    def test_resource_caps_are_pinned_close_to_artifact_sizes(self) -> None:
        resource = self.payload["resource_limit_analysis"]
        self.assertEqual(resource["max_single_input_json_bytes"], 32 * 1024 * 1024)
        self.assertEqual(resource["max_single_envelope_json_bytes"], 32 * 1024 * 1024)
        self.assertGreater(resource["single_input_headroom_bytes"], 0)
        self.assertGreater(resource["single_envelope_headroom_bytes"], 0)
        self.assertIn("bounded-read", resource["parsing_model"])

    def test_validation_commands_include_full_gate(self) -> None:
        self.assertEqual(self.payload["validation_commands"][-2:], ["just gate-fast", "just gate"])


if __name__ == "__main__":
    unittest.main()
