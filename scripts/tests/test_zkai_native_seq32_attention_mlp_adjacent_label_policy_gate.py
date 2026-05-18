from __future__ import annotations

import copy
import importlib.util
import os
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "scripts" / "zkai_native_seq32_attention_mlp_adjacent_label_policy_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location(
        "zkai_native_seq32_attention_mlp_adjacent_label_policy_gate", GATE_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NativeSeq32AdjacentLabelPolicyGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gate = load_gate()
        cls.payload = cls.gate.payload_with_mutations()

    def test_pins_checked_label_probe_go(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        summary = payload["summary"]
        self.assertEqual(payload["decision"], self.gate.DECISION)
        self.assertEqual(summary["current_champion_typed_bytes"], 42_068)
        self.assertEqual(summary["fixed_adjacent_typed_delta_vs_champion"], 88)
        self.assertEqual(summary["worst_probe_id"], "adjacent_label_probe_a")
        self.assertEqual(summary["worst_probe_typed_bytes"], 40_332)
        self.assertEqual(summary["worst_probe_saving_typed_bytes"], 1_736)
        self.assertEqual(summary["worst_probe_saving_share"], "0.041267")
        self.assertEqual(summary["best_probe_id"], "adjacent_label_probe_b")
        self.assertEqual(summary["best_probe_typed_bytes"], 37_532)
        self.assertEqual(summary["best_probe_saving_typed_bytes"], 4_536)
        self.assertEqual(summary["best_probe_saving_share"], "0.107825")
        self.assertEqual(summary["proof_size_comparable_external_rows"], 0)
        self.gate.validate_payload(payload)

    def test_direct_value_bytes_stay_stable_but_path_openings_move(self) -> None:
        rows = {row["variant_id"]: row for row in self.__class__.payload["variants"]}
        fixed = rows["fixed_adjacent_layout"]
        probe_a = rows["adjacent_label_probe_a"]
        probe_b = rows["adjacent_label_probe_b"]
        self.assertEqual(fixed["value_bytes"], 20_924)
        self.assertEqual(probe_a["value_bytes"], fixed["value_bytes"])
        self.assertEqual(probe_b["value_bytes"], fixed["value_bytes"])
        self.assertEqual(probe_a["path_opening_bytes"], 19_360)
        self.assertEqual(probe_b["path_opening_bytes"], 16_560)
        self.assertEqual(probe_b["path_opening_delta_vs_champion"], -4_032)

    def test_mutation_inventory_is_exact(self) -> None:
        result = self.__class__.payload["mutation_result"]
        self.assertTrue(result["all_mutations_rejected"])
        self.assertEqual(result["mutations_rejected"], len(self.gate.MUTATION_NAMES))
        self.assertEqual(tuple(result["mutation_names"]), self.gate.MUTATION_NAMES)
        self.assertEqual(tuple(case["name"] for case in result["cases"]), self.gate.MUTATION_NAMES)

    def test_rejects_summary_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["summary"]["best_probe_saving_typed_bytes"] = 0
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(self.gate.AdjacentLabelPolicyGateError, "summary drift"):
            self.gate.validate_payload(payload)

    def test_rejects_variant_value_group_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["variants"][2]["grouped"]["queries_values"] = 9_000
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(self.gate.AdjacentLabelPolicyGateError, "variant metadata drift"):
            self.gate.validate_payload(payload)

    def test_rejects_computed_path_opening_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["variants"][3]["path_opening_bytes"] = 16_000
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(self.gate.AdjacentLabelPolicyGateError, "variant path-opening bytes drift"):
            self.gate.validate_payload(payload)

    def test_accounting_helpers_raise_gate_errors_for_missing_groups(self) -> None:
        with self.assertRaisesRegex(self.gate.AdjacentLabelPolicyGateError, "local accounting must be object"):
            self.gate.grouped({})
        with self.assertRaisesRegex(self.gate.AdjacentLabelPolicyGateError, "missing accounting group"):
            self.gate.path_opening_bytes({"fri_decommitments": 1, "fri_samples": 1})
        with self.assertRaisesRegex(self.gate.AdjacentLabelPolicyGateError, "accounting group must be int"):
            self.gate.value_bytes({"oods_samples": True, "queries_values": 1})

    def test_rejects_source_artifact_path_relabeling(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["source_artifacts"][0]["path"] = "docs/engineering/evidence/other.json"
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(self.gate.AdjacentLabelPolicyGateError, "source artifact inventory drift"):
            self.gate.validate_payload(payload)

    def test_rejects_overclaim_boundary(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["claim_boundary"] = payload["claim_boundary"] + ";NANOZK_WIN"
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(self.gate.AdjacentLabelPolicyGateError, "claim_boundary drift"):
            self.gate.validate_payload(payload)

    def test_rejects_payload_commitment_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["payload_commitment"] = "blake2b-256:" + "0" * 64
        with self.assertRaisesRegex(self.gate.AdjacentLabelPolicyGateError, "payload commitment drift"):
            self.gate.validate_payload(payload)

    def test_render_tsv_records_each_variant(self) -> None:
        text = self.gate.render_tsv(self.__class__.payload)
        self.assertTrue(text.startswith("variant_id\ttyped_bytes\tproof_json_bytes\t"))
        self.assertIn("current_duplicate_base\t42068\t121996\t0\t0\t20592\t0\t21428\t0\n", text)
        self.assertIn("adjacent_label_probe_b\t37532\t106317\t-4536\t-15679\t16560\t-4032\t20924\t-504\n", text)

    def test_atomic_write_rejects_path_outside_evidence_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            outside = pathlib.Path(tmpdir) / "outside.json"
            with self.assertRaisesRegex(self.gate.AdjacentLabelPolicyGateError, "output path escapes evidence dir"):
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
            with self.assertRaisesRegex(self.gate.AdjacentLabelPolicyGateError, "must not traverse symlinks"):
                self.gate.read_repo_file(link, "symlink leaf")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_atomic_write_rejects_symlink_parent(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            real_parent = tmp / "real"
            link_parent = tmp / "link-parent"
            real_parent.mkdir()
            os.symlink(real_parent, link_parent)
            with self.assertRaisesRegex(self.gate.AdjacentLabelPolicyGateError, "output path must not traverse symlinks"):
                self.gate.atomic_write_text(link_parent / "out.json", "{}\n")
            self.assertFalse((real_parent / "out.json").exists())


if __name__ == "__main__":
    unittest.main()
