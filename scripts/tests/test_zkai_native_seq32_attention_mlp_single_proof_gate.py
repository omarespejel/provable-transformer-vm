from __future__ import annotations

import copy
import importlib.util
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "scripts" / "zkai_native_seq32_attention_mlp_single_proof_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location(
        "zkai_native_seq32_attention_mlp_single_proof_gate", GATE_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NativeSeq32AttentionMlpSingleProofGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gate = load_gate()
        cls.payload = cls.gate.payload_with_mutations()

    def test_pins_native_boundary_saving(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        summary = payload["summary"]
        self.assertEqual(summary["native_single_proof_typed_bytes"], self.gate.SINGLE_TYPED_BYTES)
        self.assertEqual(summary["matched_two_proof_frontier_typed_bytes"], self.gate.FRONTIER_TYPED_BYTES)
        self.assertEqual(summary["typed_saving_vs_matched_frontier_bytes"], self.gate.TYPED_SAVING_BYTES)
        self.assertEqual(summary["native_single_proof_json_bytes"], self.gate.SINGLE_PROOF_JSON_BYTES)
        self.assertEqual(summary["json_saving_vs_matched_frontier_bytes"], self.gate.PROOF_JSON_SAVING_BYTES)
        self.assertEqual(summary["proof_size_comparable_external_rows"], 0)
        self.gate.validate_payload(payload)

    def test_rejects_erased_typed_saving(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["summary"]["typed_saving_vs_matched_frontier_bytes"] = 0
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(self.gate.NativeSeq32AttentionMlpSingleProofGateError, "summary drift"):
            self.gate.validate_payload(payload)

    def test_rejects_nanozk_overclaim(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["claim_boundary"] = payload["claim_boundary"] + "_NANOZK_WIN"
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(self.gate.NativeSeq32AttentionMlpSingleProofGateError, "claim_boundary drift"):
            self.gate.validate_payload(payload)

    def test_rejects_issue_hint_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["issue_hint"] = "different-issue"
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(self.gate.NativeSeq32AttentionMlpSingleProofGateError, "issue_hint drift"):
            self.gate.validate_payload(payload)

    def test_rejects_external_comparison_flag(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["summary"]["proof_size_comparable_external_rows"] = 1
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(self.gate.NativeSeq32AttentionMlpSingleProofGateError, "summary drift"):
            self.gate.validate_payload(payload)

    def test_rejects_source_digest_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["source_artifacts"][0]["sha256"] = "0" * 64
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.NativeSeq32AttentionMlpSingleProofGateError,
            "source artifact digest drift",
        ):
            self.gate.validate_payload(payload)

    def test_rejects_source_path_traversal(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["source_artifacts"][0]["path"] = "../outside.json"
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.NativeSeq32AttentionMlpSingleProofGateError,
            "source artifact inventory drift",
        ):
            self.gate.validate_payload(payload)

    def test_rejects_valid_in_repo_source_path_swap(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        raw = self.gate.read_repo_file(self.gate.SINGLE_ACCOUNTING, "valid path swap")
        payload["source_artifacts"][0]["path"] = str(self.gate.SINGLE_ACCOUNTING.relative_to(self.gate.ROOT))
        payload["source_artifacts"][0]["sha256"] = self.gate.sha256(raw)
        payload["source_artifacts"][0]["size_bytes"] = len(raw)
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.NativeSeq32AttentionMlpSingleProofGateError,
            "source artifact inventory drift",
        ):
            self.gate.validate_payload(payload)

    def test_mutation_inventory_is_exact(self) -> None:
        result = self.__class__.payload["mutation_result"]
        self.assertTrue(result["all_mutations_rejected"])
        self.assertEqual(result["mutations_rejected"], len(self.gate.MUTATION_NAMES))
        self.assertEqual(tuple(result["mutation_names"]), self.gate.MUTATION_NAMES)
        self.assertEqual(tuple(case["name"] for case in result["cases"]), self.gate.MUTATION_NAMES)

    def test_rejects_mutation_case_name_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["mutation_result"]["cases"][0]["name"] = "different"
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.NativeSeq32AttentionMlpSingleProofGateError,
            "mutation result drift",
        ):
            self.gate.validate_payload(payload)

    def test_rejects_mutation_case_verdict_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["mutation_result"]["cases"][0]["rejected"] = False
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.NativeSeq32AttentionMlpSingleProofGateError,
            "mutation result drift",
        ):
            self.gate.validate_payload(payload)

    def test_atomic_write_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            target = tmp / "target.json"
            target.write_text("{}", encoding="utf-8")
            link = tmp / "link.json"
            link.symlink_to(target)
            with self.assertRaisesRegex(self.gate.NativeSeq32AttentionMlpSingleProofGateError, "symlink"):
                self.gate.atomic_write_text(link, "{}\n")

    def test_atomic_write_rejects_symlink_parent(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            real_parent = tmp / "real"
            real_parent.mkdir()
            link_parent = tmp / "link-parent"
            link_parent.symlink_to(real_parent, target_is_directory=True)
            output = link_parent / "out.json"
            with self.assertRaisesRegex(self.gate.NativeSeq32AttentionMlpSingleProofGateError, "symlink"):
                self.gate.atomic_write_text(output, "{}\n")
            self.assertFalse((real_parent / "out.json").exists())

    def test_atomic_write_skips_stale_temp_slot(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            output = tmp / "out.json"
            stale = tmp / ".out.json.tmp.0"
            stale.write_text("stale\n", encoding="utf-8")
            self.gate.atomic_write_text(output, "fresh\n")
            self.assertEqual(output.read_text(encoding="utf-8"), "fresh\n")
            self.assertEqual(stale.read_text(encoding="utf-8"), "stale\n")
            self.assertFalse((tmp / ".out.json.tmp.1").exists())

    def test_atomic_write_rejects_path_outside_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            outside = pathlib.Path(tmpdir) / "outside.json"
            with self.assertRaisesRegex(
                self.gate.NativeSeq32AttentionMlpSingleProofGateError,
                "output path escapes evidence dir",
            ):
                self.gate.atomic_write_text(outside, "{}\n")
            self.assertFalse(outside.exists())


if __name__ == "__main__":
    unittest.main()
