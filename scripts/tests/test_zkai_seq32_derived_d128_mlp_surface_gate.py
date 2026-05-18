from __future__ import annotations

import copy
import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "scripts" / "zkai_seq32_derived_d128_mlp_surface_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location("zkai_seq32_derived_d128_mlp_surface_gate", GATE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Seq32DerivedD128MlpSurfaceGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gate = load_gate()
        cls.seq32_input_payload = cls.gate.build_seq32_input_payload()
        cls.component_payloads = cls.gate.build_component_payloads()
        cls.summary_payload = cls.gate.build_summary_payload()
        cls.mutation_result = cls.gate.run_mutations()

    def setUp(self) -> None:
        self.gate = self.__class__.gate

    def test_builds_value_compatible_seq32_input(self) -> None:
        payload = copy.deepcopy(self.__class__.seq32_input_payload)
        self.assertEqual(payload["schema"], self.gate.INPUT_SCHEMA)
        self.assertEqual(payload["derived_input"]["input_activation_commitment"], self.gate.SEQ32_INPUT_ACTIVATION)
        self.assertEqual(payload["summary"]["adapter_mismatches_against_self"], 0)
        self.assertEqual(len(payload["derived_input"]["values_q8"]), self.gate.WIDTH)
        self.gate.validate_seq32_input_payload(payload)

    def test_component_payloads_pin_seq32_commitments(self) -> None:
        payloads = self.__class__.component_payloads
        self.assertEqual(payloads["rmsnorm_wrapper"]["rmsnorm_public_row_payload"]["statement_commitment"], self.gate.SEQ32_RMS_STMT)
        self.assertEqual(payloads["bridge"]["statement_commitment"], self.gate.SEQ32_BRIDGE_STMT)
        self.assertEqual(payloads["gate_value"]["statement_commitment"], self.gate.SEQ32_GATE_VALUE_STMT)
        self.assertEqual(payloads["activation"]["statement_commitment"], self.gate.SEQ32_ACT_STMT)
        self.assertEqual(payloads["down"]["statement_commitment"], self.gate.SEQ32_DOWN_STMT)
        self.assertEqual(payloads["residual"]["statement_commitment"], self.gate.SEQ32_RES_STMT)

    def test_rejects_d8_attention_fallback(self) -> None:
        d8, _raw = self.gate.read_json(self.gate.COMPAT.D8_ATTENTION_PATH, "d8 attention fallback")
        with self.assertRaisesRegex(self.gate.Seq32DerivedD128MlpSurfaceError, "seq32 attention field drift"):
            self.gate.derive_seq32_projection(d8)

    def test_rejects_source_commitment_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.seq32_input_payload)
        payload["derived_input"]["source_attention_statement_commitment"] = "blake2b-256:" + "11" * 32
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(self.gate.Seq32DerivedD128MlpSurfaceError, "source attention statement drift"):
            self.gate.validate_seq32_input_payload(payload)

    def test_seq32_input_rejects_non_claim_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.seq32_input_payload)
        payload["non_claims"][0] = "claims a learned model projection"
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(self.gate.Seq32DerivedD128MlpSurfaceError, "seq32 input field drift: non_claims"):
            self.gate.validate_seq32_input_payload(payload)

    def test_anchor_patching_is_idempotent(self) -> None:
        def count_dict_anchors(anchors, statement):
            return sum(
                1
                for anchor in anchors
                if isinstance(anchor, dict)
                and anchor.get("kind") == "seq32_derived"
                and anchor.get("statement_commitment") == statement
            )

        self.assertEqual(
            sum(list(commands) == self.gate.SEQ32_BRIDGE_COMMANDS for commands in self.gate.BRIDGE.ALLOWED_VALIDATION_COMMANDS),
            1,
        )
        self.assertEqual(count_dict_anchors(self.gate.GATE_VALUE.SOURCE_BRIDGE_ANCHORS, self.gate.SEQ32_BRIDGE_STMT), 1)
        self.assertEqual(
            count_dict_anchors(self.gate.ACTIVATION.SOURCE_GATE_VALUE_ANCHORS, self.gate.SEQ32_GATE_VALUE_STMT),
            1,
        )
        self.assertEqual(count_dict_anchors(self.gate.DOWN.SOURCE_ACTIVATION_ANCHORS, self.gate.SEQ32_ACT_STMT), 1)
        self.assertEqual(
            count_dict_anchors(self.gate.RESIDUAL.DOWN_PROJECTION.SOURCE_ACTIVATION_ANCHORS, self.gate.SEQ32_ACT_STMT),
            1,
        )

    def test_rejects_overclaim_mutations(self) -> None:
        result = self.__class__.mutation_result
        self.assertTrue(result["all_mutations_rejected"])
        self.assertEqual(result["case_count"], self.gate.EXPECTED_MUTATION_CASE_COUNT)

    def test_output_path_guard_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            target = tmp / "target.json"
            target.write_text("{}", encoding="utf-8")
            link = tmp / "link.json"
            link.symlink_to(target)
            with self.assertRaisesRegex(self.gate.Seq32DerivedD128MlpSurfaceError, "symlink"):
                self.gate.atomic_write_text(link, "{}\n")

    def test_summary_rejects_nanozk_overclaim(self) -> None:
        payload = copy.deepcopy(self.__class__.summary_payload)
        candidate = copy.deepcopy(payload)
        candidate["interpretation"]["nanozk_comparison_claim"] = True
        candidate["payload_commitment"] = self.gate.payload_commitment(candidate)
        with self.assertRaisesRegex(self.gate.Seq32DerivedD128MlpSurfaceError, "NANOZK overclaim"):
            self.gate.validate_summary_payload(candidate)

    def test_summary_pins_proof_accounting(self) -> None:
        payload = copy.deepcopy(self.__class__.summary_payload)
        summary = payload["summary"]
        self.assertEqual(summary["fused_typed_bytes"], self.gate.EXPECTED_FUSED_TYPED_BYTES)
        self.assertEqual(summary["separate_component_typed_bytes"], self.gate.EXPECTED_SEPARATE_TYPED_BYTES)
        self.assertEqual(summary["typed_saving_bytes"], self.gate.EXPECTED_TYPED_SAVING_BYTES)
        candidate = copy.deepcopy(payload)
        candidate["summary"]["fused_typed_bytes"] += 1
        candidate["payload_commitment"] = self.gate.payload_commitment(candidate)
        with self.assertRaisesRegex(self.gate.Seq32DerivedD128MlpSurfaceError, "summary metric drift"):
            self.gate.validate_summary_payload(candidate)

    def test_summary_pins_source_artifact_digests(self) -> None:
        payload = copy.deepcopy(self.__class__.summary_payload)
        candidate = copy.deepcopy(payload)
        candidate["source_artifacts"][0]["sha256"] = "0" * 64
        candidate["payload_commitment"] = self.gate.payload_commitment(candidate)
        with self.assertRaisesRegex(self.gate.Seq32DerivedD128MlpSurfaceError, "source artifact digest drift"):
            self.gate.validate_summary_payload(candidate)


if __name__ == "__main__":
    unittest.main()
