from __future__ import annotations

import copy
import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "scripts" / "zkai_seq32_value_compatible_boundary_frontier_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location(
        "zkai_seq32_value_compatible_boundary_frontier_gate", GATE_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Seq32ValueCompatibleBoundaryFrontierGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gate = load_gate()
        cls.payload = cls.gate.payload_with_mutations()

    def test_pins_value_compatible_frontier(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        summary = payload["summary"]
        self.assertEqual(
            summary["value_compatible_two_proof_frontier_typed_bytes"],
            self.gate.FRONTIER_TYPED_BYTES,
        )
        self.assertEqual(summary["selected_attention_typed_bytes"], self.gate.SEQ32_ATTENTION_TYPED_BYTES)
        self.assertEqual(summary["seq32_derived_mlp_typed_bytes"], self.gate.SEQ32_MLP_TYPED_BYTES)
        self.assertEqual(summary["seq32_derived_mlp_adapter_mismatches"], 0)
        self.assertEqual(
            summary["frontier_typed_increase_after_value_fix_bytes"],
            self.gate.FRONTIER_TYPED_BYTES - self.gate.STALE_SELECTOR_FRONTIER_TYPED_BYTES,
        )
        self.gate.validate_payload(payload)

    def test_rejects_stale_selector_frontier(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["summary"]["value_compatible_two_proof_frontier_typed_bytes"] = (
            self.gate.STALE_SELECTOR_FRONTIER_TYPED_BYTES
        )
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.Seq32ValueCompatibleBoundaryFrontierError,
            "summary drift",
        ):
            self.gate.validate_payload(payload)

    def test_rejects_nanozk_overclaim(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["claim_boundary"] = payload["claim_boundary"] + "_NANOZK_WIN"
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(self.gate.Seq32ValueCompatibleBoundaryFrontierError, "claim_boundary drift"):
            self.gate.validate_payload(payload)

    def test_rejects_source_digest_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["source_artifacts"][0]["sha256"] = "0" * 64
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.Seq32ValueCompatibleBoundaryFrontierError,
            "source artifact digest drift",
        ):
            self.gate.validate_payload(payload)

    def test_rejects_source_path_traversal(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["source_artifacts"][0]["path"] = "../outside.json"
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.Seq32ValueCompatibleBoundaryFrontierError,
            "source artifact path traversal",
        ):
            self.gate.validate_payload(payload)

    def test_mutation_inventory_is_exact(self) -> None:
        result = self.__class__.payload["mutation_result"]
        self.assertTrue(result["all_mutations_rejected"])
        self.assertEqual(result["mutations_rejected"], len(self.gate.MUTATION_NAMES))
        self.assertEqual(tuple(result["mutation_names"]), self.gate.MUTATION_NAMES)

    def test_atomic_write_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            target = tmp / "target.json"
            target.write_text("{}", encoding="utf-8")
            link = tmp / "link.json"
            link.symlink_to(target)
            with self.assertRaisesRegex(self.gate.Seq32ValueCompatibleBoundaryFrontierError, "symlink"):
                self.gate.atomic_write_text(link, "{}\n")


if __name__ == "__main__":
    unittest.main()
