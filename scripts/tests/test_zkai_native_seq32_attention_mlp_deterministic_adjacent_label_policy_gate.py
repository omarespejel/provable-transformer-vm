from __future__ import annotations

import copy
import importlib.util
import os
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = (
    ROOT
    / "scripts"
    / "zkai_native_seq32_attention_mlp_deterministic_adjacent_label_policy_gate.py"
)


def load_gate():
    spec = importlib.util.spec_from_file_location(
        "zkai_native_seq32_attention_mlp_deterministic_adjacent_label_policy_gate",
        GATE_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NativeSeq32DeterministicAdjacentLabelPolicyGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gate = load_gate()
        cls.payload = cls.gate.payload_with_mutations()

    def test_pins_supported_label_policy_go_without_promoting_full_inventory(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        summary = payload["policy_summary"]
        self.assertEqual(
            payload["decision"],
            "GO_SUPPORTED_ADJACENT_LABEL_POLICY_BEATS_CURRENT_CHAMPION",
        )
        self.assertEqual(
            payload["result"],
            "WORST_SUPPORTED_ADJACENT_LABEL_SAVES_1736_TYPED_BYTES_VS_42068_CHAMPION",
        )
        self.assertFalse(
            payload["full_inventory_policy"][
                "full_inventory_promotable_vs_current_champion"
            ]
        )
        self.assertEqual(summary["full_inventory_worst_label_id"], "fixed_adjacent_layout")
        self.assertEqual(summary["full_inventory_worst_typed_bytes"], 42_156)
        self.assertEqual(summary["full_inventory_miss_vs_champion_typed_bytes"], 88)
        self.assertEqual(summary["worst_supported_label_id"], "adjacent_label_probe_a")
        self.assertEqual(summary["worst_supported_typed_bytes"], 40_332)
        self.assertEqual(summary["worst_supported_saving_typed_bytes"], 1_736)
        self.assertEqual(summary["best_supported_label_id"], "adjacent_label_probe_b")
        self.assertEqual(summary["best_supported_typed_bytes"], 37_532)
        self.assertEqual(summary["best_supported_saving_typed_bytes"], 4_536)
        self.assertEqual(summary["proof_size_comparable_external_rows"], 0)
        self.gate.validate_payload(payload)

    def test_label_inventory_rejects_fixed_label_and_supports_both_probes(self) -> None:
        rows = {row["variant_id"]: row for row in self.__class__.payload["label_inventory"]}
        self.assertEqual(rows["current_duplicate_base"]["policy_status"], "comparison_champion")
        self.assertEqual(
            rows["fixed_adjacent_layout"]["policy_status"],
            "rejected_inflating_label",
        )
        self.assertEqual(
            rows["fixed_adjacent_layout"]["status_reason"],
            "path-opening bytes are not below the current champion",
        )
        self.assertEqual(rows["adjacent_label_probe_a"]["policy_status"], "supported_label")
        self.assertEqual(rows["adjacent_label_probe_b"]["policy_status"], "supported_label")
        self.assertEqual(rows["fixed_adjacent_layout"]["value_bytes"], 20_924)
        self.assertEqual(rows["adjacent_label_probe_a"]["value_bytes"], 20_924)
        self.assertEqual(rows["adjacent_label_probe_b"]["value_bytes"], 20_924)
        self.assertEqual(rows["fixed_adjacent_layout"]["path_opening_delta_vs_champion"], 592)
        self.assertEqual(rows["adjacent_label_probe_a"]["path_opening_delta_vs_champion"], -1_232)
        self.assertEqual(rows["adjacent_label_probe_b"]["path_opening_delta_vs_champion"], -4_032)

    def test_mutation_inventory_is_exact(self) -> None:
        result = self.__class__.payload["mutation_result"]
        self.assertTrue(result["all_mutations_rejected"])
        self.assertEqual(result["mutations_rejected"], len(self.gate.MUTATION_NAMES))
        self.assertEqual(tuple(result["mutation_names"]), self.gate.MUTATION_NAMES)
        self.assertEqual(
            tuple(case["name"] for case in result["cases"]),
            self.gate.MUTATION_NAMES,
        )
        self.assertEqual(
            tuple(case["error"] for case in result["cases"]),
            tuple(
                self.gate.EXPECTED_MUTATION_ERRORS[name]
                for name in self.gate.MUTATION_NAMES
            ),
        )

    def test_rejects_full_inventory_overclaim(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["full_inventory_policy"][
            "full_inventory_promotable_vs_current_champion"
        ] = True
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.DeterministicAdjacentLabelPolicyGateError,
            "full inventory overclaim",
        ):
            self.gate.validate_payload(payload)

    def test_rejects_fixed_label_supported_relabeling(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["label_inventory"][1]["policy_status"] = "supported_label"
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.DeterministicAdjacentLabelPolicyGateError,
            "label inventory drift",
        ):
            self.gate.validate_payload(payload)

    def test_rejects_support_criteria_erasure(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["deterministic_policy"]["support_criteria"] = []
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.DeterministicAdjacentLabelPolicyGateError,
            "deterministic policy drift",
        ):
            self.gate.validate_payload(payload)

    def test_rejects_source_artifact_digest_relabeling(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["source_artifacts"][0]["sha256"] = "0" * 64
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.DeterministicAdjacentLabelPolicyGateError,
            "source artifact drift",
        ):
            self.gate.validate_payload(payload)

    def test_rejects_nanozk_or_external_proof_size_overclaim(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["claim_boundary"] = payload["claim_boundary"] + ";NANOZK_WIN"
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.DeterministicAdjacentLabelPolicyGateError,
            "claim_boundary drift",
        ):
            self.gate.validate_payload(payload)

    def test_rejects_final_policy_overclaim(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["non_claims"].remove("not a final production label-selection policy")
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.DeterministicAdjacentLabelPolicyGateError,
            "non_claims drift",
        ):
            self.gate.validate_payload(payload)

    def test_rejects_unknown_policy_field(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["deterministic_policy"]["unchecked"] = True
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.DeterministicAdjacentLabelPolicyGateError,
            "deterministic policy field drift: unexpected unchecked",
        ):
            self.gate.validate_payload(payload)

    def test_rejects_label_inventory_order_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["label_inventory"].reverse()
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.DeterministicAdjacentLabelPolicyGateError,
            "label inventory order drift",
        ):
            self.gate.validate_payload(payload)

    def test_rejects_label_inventory_metadata_drift(self) -> None:
        cases = [
            (2, "adapter_mode", "relabelled"),
            (3, "proof_json_bytes", 1),
            (1, "status_reason", "supported"),
            (0, "value_bytes", self.gate.ADJACENT_VALUE_BYTES),
        ]
        for row_index, field, value in cases:
            with self.subTest(field=field):
                payload = copy.deepcopy(self.__class__.payload)
                payload["label_inventory"][row_index][field] = value
                payload["payload_commitment"] = self.gate.payload_commitment(payload)
                with self.assertRaisesRegex(
                    self.gate.DeterministicAdjacentLabelPolicyGateError,
                    "label inventory drift",
                ):
                    self.gate.validate_payload(payload)

    def test_rejects_payload_commitment_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["payload_commitment"] = "blake2b-256:" + "0" * 64
        with self.assertRaisesRegex(
            self.gate.DeterministicAdjacentLabelPolicyGateError,
            "payload commitment drift",
        ):
            self.gate.validate_payload(payload)

    def test_render_tsv_records_policy_statuses(self) -> None:
        text = self.gate.render_tsv(self.__class__.payload)
        self.assertTrue(text.startswith("variant_id\tpolicy_status\ttyped_bytes\t"))
        self.assertIn(
            "fixed_adjacent_layout\trejected_inflating_label\t42156\t88\t21184\t592\t20924\t",
            text,
        )
        self.assertIn(
            "adjacent_label_probe_b\tsupported_label\t37532\t-4536\t16560\t-4032\t20924\t",
            text,
        )

    def test_write_outputs_records_json_and_tsv_inside_evidence_tree(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            json_out = tmp / "deterministic.json"
            tsv_out = tmp / "deterministic.tsv"
            self.gate.write_outputs(self.__class__.payload, json_out, tsv_out)
            self.assertIn(
                "GO_SUPPORTED_ADJACENT_LABEL_POLICY_BEATS_CURRENT_CHAMPION",
                json_out.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "adjacent_label_probe_a\tsupported_label",
                tsv_out.read_text(encoding="utf-8"),
            )

    def test_write_outputs_rejects_invalid_payload(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["policy_summary"]["worst_supported_saving_typed_bytes"] = 0
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            bad_json = tmp / "bad.json"
            bad_tsv = tmp / "bad.tsv"
            with self.assertRaisesRegex(
                self.gate.DeterministicAdjacentLabelPolicyGateError,
                "policy summary drift",
            ):
                self.gate.write_outputs(payload, bad_json, bad_tsv)
            self.assertFalse(bad_json.exists())
            self.assertFalse(bad_tsv.exists())

    def test_write_outputs_rejects_path_outside_evidence_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            outside = pathlib.Path(tmpdir) / "outside.json"
            with self.assertRaisesRegex(
                self.gate.source_gate.AdjacentLabelPolicyGateError,
                "output path escapes evidence dir",
            ):
                self.gate.write_outputs(self.__class__.payload, outside, None)
            self.assertFalse(outside.exists())

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_write_outputs_rejects_symlink_parent(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            real_parent = tmp / "real"
            link_parent = tmp / "link-parent"
            real_parent.mkdir()
            os.symlink(real_parent, link_parent)
            with self.assertRaisesRegex(
                self.gate.source_gate.AdjacentLabelPolicyGateError,
                "output path must not traverse symlinks",
            ):
                self.gate.write_outputs(
                    self.__class__.payload,
                    link_parent / "out.json",
                    None,
                )
            self.assertFalse((real_parent / "out.json").exists())


if __name__ == "__main__":
    unittest.main()
