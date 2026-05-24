from __future__ import annotations

import copy
import tempfile
import unittest

from scripts import zkai_native_d128_seq32_attention_derived_mlp_single_proof_gate as gate


class NativeD128Seq32AttentionDerivedMlpSingleProofGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = gate.build_payload()
        cls.mutations = gate.run_mutations(cls.payload)

    def test_payload_validates(self) -> None:
        gate.validate_payload(copy.deepcopy(self.payload))

    def test_metrics_are_pinned(self) -> None:
        summary = self.payload["summary"]
        self.assertEqual(summary["single_proof_json_bytes"], 503_567)
        self.assertEqual(summary["split_proof_json_bytes"], 522_480)
        self.assertEqual(summary["proof_json_saving_bytes"], 18_913)
        self.assertEqual(summary["single_typed_bytes"], 204_564)
        self.assertEqual(summary["split_typed_bytes"], 209_732)
        self.assertEqual(summary["typed_saving_bytes"], 5_168)
        self.assertEqual(summary["proof_json_ratio"], "0.963801")
        self.assertEqual(summary["typed_ratio"], "0.975359")

    def test_route_is_model_faithful_d128_attention_derived(self) -> None:
        route = self.payload["route"]
        self.assertEqual(route["adapter_mode"], gate.ADAPTER_MODE)
        self.assertEqual(route["target_id"], gate.TARGET_ID)
        self.assertEqual(route["statement_commitment"], gate.STATEMENT_COMMITMENT)
        self.assertEqual(route["mlp_input_activation_commitment"], gate.MLP_INPUT_ACTIVATION_COMMITMENT)
        self.assertNotIn("not enforcing d128 MLP input derivation from attention outputs", self.payload["non_claims"])

    def test_mutations_are_rejected(self) -> None:
        self.assertEqual(len(self.mutations), len(gate.mutation_cases()))
        self.assertTrue(all(result["rejected"] for result in self.mutations))

    def test_source_artifact_drift_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.payload)
        candidate["source_artifacts"][0]["sha256"] = "0" * 64
        candidate["payload_commitment"] = gate.payload_commitment(candidate)
        with self.assertRaises(gate.NativeD128Seq32AttentionDerivedMlpSingleProofGateError):
            gate.validate_payload(candidate)

    def test_output_path_guard_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR) as tmpdir:
            target = gate.pathlib.Path(tmpdir) / "target.json"
            target.write_text("{}", encoding="utf-8")
            link = gate.pathlib.Path(tmpdir) / "link.json"
            link.symlink_to(target)
            with self.assertRaisesRegex(gate.NativeD128Seq32AttentionDerivedMlpSingleProofGateError, "symlink"):
                gate.atomic_write_text(link, "{}\n")


if __name__ == "__main__":
    unittest.main()
