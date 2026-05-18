from __future__ import annotations

import copy
import importlib.util
import os
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "scripts" / "zkai_native_seq32_attention_mlp_adapter_variant_selector_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location(
        "zkai_native_seq32_attention_mlp_adapter_variant_selector_gate", GATE_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NativeSeq32AdapterVariantSelectorGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gate = load_gate()
        cls.payload = cls.gate.payload_with_mutations()

    def test_pins_no_go_and_best_near_miss(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        summary = payload["summary"]
        self.assertEqual(payload["decision"], self.gate.DECISION)
        self.assertEqual(summary["current_champion_typed_bytes"], 42_068)
        self.assertEqual(summary["best_variant_id"], "rmsnorm_adjacent_layout")
        self.assertEqual(summary["best_variant_typed_bytes"], 42_156)
        self.assertEqual(summary["best_variant_gap_typed_bytes"], 88)
        self.assertEqual(summary["zero_base_variant_count"], 3)
        self.gate.validate_payload(payload)

    def test_zero_base_does_not_imply_smaller_proof(self) -> None:
        variants = self.__class__.payload["variants"]
        zero_base = [row for row in variants if row["adapter_trace_cells"] == 0]
        self.assertEqual(len(zero_base), 3)
        self.assertTrue(all(row["typed_bytes"] > self.gate.CURRENT_CHAMPION_TYPED_BYTES for row in zero_base))

    def test_records_opening_geometry_blocker(self) -> None:
        summary = self.__class__.payload["summary"]
        self.assertEqual(summary["best_variant_opening_overhang_bytes"], 576)
        self.assertEqual(summary["best_variant_oods_queries_saving_bytes"], 504)
        self.assertEqual(summary["best_variant_fri_sample_overhang_bytes"], 16)

    def test_mutation_inventory_is_exact(self) -> None:
        result = self.__class__.payload["mutation_result"]
        self.assertTrue(result["all_mutations_rejected"])
        self.assertEqual(result["mutations_rejected"], len(self.gate.MUTATION_NAMES))
        self.assertEqual(tuple(result["mutation_names"]), self.gate.MUTATION_NAMES)
        self.assertEqual(tuple(case["name"] for case in result["cases"]), self.gate.MUTATION_NAMES)

    def test_rejects_best_variant_gap_erasure(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["summary"]["best_variant_gap_typed_bytes"] = 0
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(self.gate.NativeSeq32AdapterVariantSelectorGateError, "summary drift"):
            self.gate.validate_payload(payload)

    def test_rejects_variant_metric_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["variants"][4]["typed_bytes"] = 42_000
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(self.gate.NativeSeq32AdapterVariantSelectorGateError, "variant summary drift"):
            self.gate.validate_payload(payload)

    def test_rejects_variant_metadata_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["variants"][4]["proof_sha256"] = "0" * 64
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(self.gate.NativeSeq32AdapterVariantSelectorGateError, "variant metadata drift"):
            self.gate.validate_payload(payload)

    def test_rejects_overclaim_boundary(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["claim_boundary"] = payload["claim_boundary"] + ";NANOZK_WIN"
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(self.gate.NativeSeq32AdapterVariantSelectorGateError, "claim_boundary drift"):
            self.gate.validate_payload(payload)

    def test_rejects_source_digest_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["source_artifacts"][0]["sha256"] = "0" * 64
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.NativeSeq32AdapterVariantSelectorGateError,
            "source artifact digest drift",
        ):
            self.gate.validate_payload(payload)

    def test_rejects_source_path_traversal(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["source_artifacts"][0]["path"] = "../outside.json"
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.NativeSeq32AdapterVariantSelectorGateError,
            "source artifact inventory drift",
        ):
            self.gate.validate_payload(payload)

    def test_rejects_payload_commitment_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["payload_commitment"] = "blake2b-256:" + "0" * 64
        with self.assertRaisesRegex(
            self.gate.NativeSeq32AdapterVariantSelectorGateError,
            "payload commitment drift",
        ):
            self.gate.validate_payload(payload)

    def test_atomic_write_rejects_path_outside_evidence_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            outside = pathlib.Path(tmpdir) / "outside.json"
            with self.assertRaisesRegex(
                self.gate.NativeSeq32AdapterVariantSelectorGateError,
                "output path escapes evidence dir",
            ):
                self.gate.atomic_write_text(outside, "{}\n")
            self.assertFalse(outside.exists())

    def test_atomic_write_skips_stale_temp_slot(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            output = tmp / "out.json"
            stale = tmp / ".out.json.tmp.0"
            stale.write_text("stale\n", encoding="utf-8")
            self.gate.atomic_write_text(output, "fresh\n")
            self.assertEqual(output.read_text(encoding="utf-8"), "fresh\n")
            self.assertEqual(stale.read_text(encoding="utf-8"), "stale\n")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_read_repo_file_rejects_symlink_leaf(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            target = tmp / "target.json"
            link = tmp / "link.json"
            target.write_text("{}", encoding="utf-8")
            os.symlink(target, link)
            with self.assertRaisesRegex(
                self.gate.NativeSeq32AdapterVariantSelectorGateError,
                "must not traverse symlinks",
            ):
                self.gate.read_repo_file(link, "symlink leaf")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_atomic_write_rejects_symlink_parent(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            real_parent = tmp / "real"
            link_parent = tmp / "link-parent"
            real_parent.mkdir()
            os.symlink(real_parent, link_parent)
            with self.assertRaisesRegex(
                self.gate.NativeSeq32AdapterVariantSelectorGateError,
                "output path must not traverse symlinks",
            ):
                self.gate.atomic_write_text(link_parent / "out.json", "{}\n")
            self.assertFalse((real_parent / "out.json").exists())


if __name__ == "__main__":
    unittest.main()
