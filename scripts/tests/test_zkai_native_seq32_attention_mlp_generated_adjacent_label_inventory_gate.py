from __future__ import annotations

import copy
import csv
import importlib.util
import io
import os
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = (
    ROOT
    / "scripts"
    / "zkai_native_seq32_attention_mlp_generated_adjacent_label_inventory_gate.py"
)


def load_gate():
    spec = importlib.util.spec_from_file_location(
        "zkai_native_seq32_attention_mlp_generated_adjacent_label_inventory_gate",
        GATE_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NativeSeq32GeneratedAdjacentLabelInventoryGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gate = load_gate()
        cls.payload = cls.gate.payload_with_mutations()

    def test_pins_generated_supported_policy_without_promoting_full_inventory(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        summary = payload["policy_summary"]
        self.assertEqual(
            payload["decision"],
            "GO_GENERATED_SUPPORTED_ADJACENT_LABELS_BEAT_CURRENT_CHAMPION_WITH_FULL_INVENTORY_NO_GO",
        )
        self.assertEqual(
            payload["result"],
            "NINE_LABEL_SOURCE_INVENTORY_ACCEPTS_PROBE_A_B_AND_REJECTS_FIXED_PLUS_SEEDS",
        )
        self.assertFalse(summary["full_generated_inventory_promotable_vs_current_champion"])
        self.assertEqual(summary["generated_label_count"], 9)
        self.assertEqual(summary["accepted_label_count"], 2)
        self.assertEqual(summary["rejected_label_count"], 7)
        self.assertEqual(summary["full_generated_worst_label_id"], "fixed_adjacent_layout")
        self.assertEqual(summary["full_generated_worst_typed_bytes"], 42_156)
        self.assertEqual(summary["full_generated_miss_vs_champion_typed_bytes"], 88)
        self.assertEqual(summary["worst_accepted_label_id"], "adjacent_label_probe_a")
        self.assertEqual(summary["worst_accepted_typed_bytes"], 40_332)
        self.assertEqual(summary["worst_accepted_saving_typed_bytes"], 1_736)
        self.assertEqual(summary["best_accepted_label_id"], "adjacent_label_probe_b")
        self.assertEqual(summary["best_accepted_typed_bytes"], 37_532)
        self.assertEqual(summary["best_accepted_saving_typed_bytes"], 4_536)
        self.assertEqual(summary["proof_size_comparable_external_rows"], 0)
        self.gate.validate_payload(payload)

    def test_generates_adapter_modes_and_cli_commands_from_source(self) -> None:
        policy = self.__class__.payload["generator_policy"]
        self.assertEqual(
            tuple(policy["generated_adapter_modes"]),
            self.gate.EXPECTED_ADJACENT_MODES,
        )
        self.assertEqual(
            tuple(policy["generated_cli_commands"]),
            self.gate.EXPECTED_CLI_COMMANDS,
        )
        self.assertEqual(
            tuple(policy["generated_label_ids"]),
            (
                "fixed_adjacent_layout",
                "adjacent_label_probe_a",
                "adjacent_label_probe_b",
                "adjacent_seed_00",
                "adjacent_seed_01",
                "adjacent_seed_02",
                "adjacent_seed_03",
                "adjacent_seed_04",
                "adjacent_seed_05",
            ),
        )
        self.assertEqual(
            tuple(policy["accepted_label_ids"]),
            ("adjacent_label_probe_a", "adjacent_label_probe_b"),
        )
        self.assertEqual(
            tuple(policy["rejected_label_ids"]),
            (
                "fixed_adjacent_layout",
                "adjacent_seed_00",
                "adjacent_seed_01",
                "adjacent_seed_02",
                "adjacent_seed_03",
                "adjacent_seed_04",
                "adjacent_seed_05",
            ),
        )
        self.assertFalse(policy["manual_override_allowed"])

    def test_generated_label_rows_pin_policy_status_and_accounting(self) -> None:
        rows = {row["variant_id"]: row for row in self.__class__.payload["generated_label_inventory"]}
        fixed = rows["fixed_adjacent_layout"]
        probe_a = rows["adjacent_label_probe_a"]
        probe_b = rows["adjacent_label_probe_b"]
        seed_02 = rows["adjacent_seed_02"]
        self.assertEqual(fixed["policy_status"], "rejected_inflating_label")
        self.assertEqual(fixed["path_opening_delta_vs_champion"], 592)
        self.assertTrue(fixed["proof_accounting_pinned"])
        self.assertEqual(probe_a["policy_status"], "supported_label")
        self.assertEqual(probe_a["typed_delta_vs_champion"], -1_736)
        self.assertEqual(probe_a["path_opening_delta_vs_champion"], -1_232)
        self.assertEqual(probe_a["value_bytes"], 20_924)
        self.assertEqual(probe_b["policy_status"], "supported_label")
        self.assertEqual(probe_b["typed_delta_vs_champion"], -4_536)
        self.assertEqual(probe_b["path_opening_delta_vs_champion"], -4_032)
        self.assertEqual(probe_b["value_bytes"], 20_924)
        self.assertEqual(seed_02["policy_status"], "rejected_unpromoted_seed_label")
        self.assertEqual(seed_02["typed_delta_vs_champion"], -1_800)
        self.assertEqual(seed_02["path_opening_delta_vs_champion"], -1_296)

    def test_rejects_unseen_and_cross_family_labels(self) -> None:
        rejected = self.__class__.payload["rejected_unseen_labels"]
        self.assertEqual(
            rejected[0]["adapter_mode"],
            "rmsnorm_input_fused_adjacent_label_probe_c_v1",
        )
        self.assertIn("absent from the pinned Rust enum", rejected[0]["reason"])
        self.assertEqual(
            rejected[1]["adapter_mode"],
            "rmsnorm_input_fused_post_tail_label_probe_a_v1",
        )
        self.assertIn("post-tail family", rejected[1]["reason"])

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

    def test_rejects_manual_override_or_generator_rule_drift(self) -> None:
        cases = [
            ("manual_override_allowed", True),
            ("source_rule", "manual list"),
        ]
        for field, value in cases:
            with self.subTest(field=field):
                payload = copy.deepcopy(self.__class__.payload)
                payload["generator_policy"][field] = value
                payload["payload_commitment"] = self.gate.payload_commitment(payload)
                with self.assertRaisesRegex(
                    self.gate.GeneratedAdjacentLabelInventoryGateError,
                    "generator policy drift",
                ):
                    self.gate.validate_payload(payload)

    def test_rejects_fixed_label_promotion_or_accepted_label_drift(self) -> None:
        cases = [
            (0, "policy_status", "supported_label"),
            (1, "value_bytes", self.gate.CURRENT_CHAMPION_VALUE_BYTES),
            (1, "typed_bytes", self.gate.CURRENT_CHAMPION_TYPED_BYTES),
            (2, "proof_accounting_pinned", False),
        ]
        for row_index, field, value in cases:
            with self.subTest(field=field):
                payload = copy.deepcopy(self.__class__.payload)
                payload["generated_label_inventory"][row_index][field] = value
                payload["payload_commitment"] = self.gate.payload_commitment(payload)
                with self.assertRaisesRegex(
                    self.gate.GeneratedAdjacentLabelInventoryGateError,
                    "generated label inventory drift",
                ):
                    self.gate.validate_payload(payload)

    def test_rejects_source_artifact_drift_even_with_recomputed_commitment(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["source_artifacts"][0]["sha256"] = "0" * 64
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.GeneratedAdjacentLabelInventoryGateError,
            "source artifact drift",
        ):
            self.gate.validate_payload(payload)

    def test_load_source_policy_rechecks_raw_digest(self) -> None:
        original = self.gate.deterministic_gate.load_source_policy
        source, raw = original()

        def drifted_source_policy():
            return source, raw + b"\n"

        self.gate.deterministic_gate.load_source_policy = drifted_source_policy
        try:
            with self.assertRaisesRegex(
                self.gate.GeneratedAdjacentLabelInventoryGateError,
                "source policy digest drift",
            ):
                self.gate.load_source_policy()
        finally:
            self.gate.deterministic_gate.load_source_policy = original

    def test_rejects_unseen_label_acceptance(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["rejected_unseen_labels"][0]["reason"] = "accepted"
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.GeneratedAdjacentLabelInventoryGateError,
            "rejected unseen label drift",
        ):
            self.gate.validate_payload(payload)

    def test_rejects_nanozk_overclaim(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["claim_boundary"] = payload["claim_boundary"] + ";NANOZK_WIN"
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with self.assertRaisesRegex(
            self.gate.GeneratedAdjacentLabelInventoryGateError,
            "claim_boundary drift",
        ):
            self.gate.validate_payload(payload)

    def test_render_tsv_records_generated_policy(self) -> None:
        text = self.gate.render_tsv(self.__class__.payload)
        self.assertTrue(text.startswith("variant_id\tadapter_mode\tcli_command\t"))
        rows = list(csv.DictReader(io.StringIO(text), delimiter="\t"))
        self.assertEqual(len(rows), 9)
        fixed = rows[0]
        probe_b = rows[2]
        seed_02 = rows[5]
        self.assertEqual(fixed["variant_id"], "fixed_adjacent_layout")
        self.assertEqual(fixed["policy_status"], "rejected_inflating_label")
        self.assertEqual(fixed["typed_bytes"], "42156")
        self.assertEqual(fixed["typed_delta_vs_champion"], "88")
        self.assertEqual(fixed["proof_accounting_pinned"], "True")
        self.assertEqual(probe_b["variant_id"], "adjacent_label_probe_b")
        self.assertEqual(probe_b["policy_status"], "supported_label")
        self.assertEqual(probe_b["typed_bytes"], "37532")
        self.assertEqual(probe_b["typed_delta_vs_champion"], "-4536")
        self.assertEqual(seed_02["variant_id"], "adjacent_seed_02")
        self.assertEqual(seed_02["policy_status"], "rejected_unpromoted_seed_label")
        self.assertEqual(seed_02["typed_bytes"], "40268")

    def test_render_tsv_records_audit_pins(self) -> None:
        rows = list(csv.DictReader(io.StringIO(self.gate.render_tsv(self.__class__.payload)), delimiter="\t"))
        row = rows[1]
        self.assertEqual(row["payload_commitment"], self.__class__.payload["payload_commitment"])
        self.assertIn(
            "rust_native_seq32_attention_mlp_source=7818c25b034da111cddd090783ea6bc66fd0c4dc2c67f95e3281899d0235344b",
            row["source_artifact_digest_pins"],
        )
        self.assertIn(
            "deterministic_adjacent_label_policy=blake2b-256:cb60558f8b274ffa44d51de3367a34759b408b5c1dd3427583d3031ef9017fdd",
            row["source_artifact_payload_commitments"],
        )
        self.assertEqual(
            row["accepted_label_ids"],
            "adjacent_label_probe_a,adjacent_label_probe_b",
        )
        self.assertIn("adjacent_seed_02", row["rejected_label_ids"])
        self.assertIn(
            "rmsnorm_input_fused_adjacent_label_probe_c_v1",
            row["rejected_unseen_adapter_modes"],
        )
        self.assertIn("decision_drift=rejected:decision drift", row["mutation_outcomes"])
        self.assertIn("payload_commitment_drift=rejected:payload commitment drift", row["mutation_outcomes"])

    def test_write_outputs_records_json_and_tsv_inside_evidence_tree(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            json_out = tmp / "generated.json"
            tsv_out = tmp / "generated.tsv"
            self.gate.write_outputs(self.__class__.payload, json_out, tsv_out)
            self.assertIn(
                "GO_GENERATED_SUPPORTED_ADJACENT_LABELS_BEAT_CURRENT_CHAMPION",
                json_out.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "adjacent_label_probe_a\trmsnorm_input_fused_adjacent_label_probe_a_v1",
                tsv_out.read_text(encoding="utf-8"),
            )

    def test_write_outputs_rejects_invalid_payload_without_artifacts(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["policy_summary"]["worst_accepted_saving_typed_bytes"] = 0
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            bad_json = tmp / "bad.json"
            bad_tsv = tmp / "bad.tsv"
            with self.assertRaisesRegex(
                self.gate.GeneratedAdjacentLabelInventoryGateError,
                "policy summary drift",
            ):
                self.gate.write_outputs(payload, bad_json, bad_tsv)
            self.assertFalse(bad_json.exists())
            self.assertFalse(bad_tsv.exists())

    def test_write_outputs_rejects_path_outside_evidence_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            outside = pathlib.Path(tmpdir) / "outside.json"
            with self.assertRaisesRegex(
                self.gate.GeneratedAdjacentLabelInventoryGateError,
                "output path escapes evidence dir",
            ):
                self.gate.write_outputs(self.__class__.payload, outside, None)
            self.assertFalse(outside.exists())

    def test_write_outputs_wraps_raw_writer_exceptions(self) -> None:
        original = self.gate.source_gate.atomic_write_text

        def fail_writer(_path: pathlib.Path, _text: str) -> None:
            raise OSError("disk full")

        self.gate.source_gate.atomic_write_text = fail_writer
        try:
            with self.assertRaisesRegex(
                self.gate.GeneratedAdjacentLabelInventoryGateError,
                "failed to write output: disk full",
            ):
                self.gate.write_outputs(self.__class__.payload, self.gate.JSON_OUT, None)
        finally:
            self.gate.source_gate.atomic_write_text = original

    def test_write_outputs_rolls_back_paired_publish_if_second_final_fails(self) -> None:
        original = self.gate.source_gate.atomic_write_text
        calls = 0
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            json_out = tmp / "generated.json"
            tsv_out = tmp / "generated.tsv"

            def fail_fourth_write(path: pathlib.Path, text: str) -> None:
                nonlocal calls
                calls += 1
                if calls == 4:
                    raise OSError("second final publish failed")
                original(path, text)

            self.gate.source_gate.atomic_write_text = fail_fourth_write
            try:
                with self.assertRaisesRegex(
                    self.gate.GeneratedAdjacentLabelInventoryGateError,
                    "failed to write output: second final publish failed",
                ):
                    self.gate.write_outputs(self.__class__.payload, json_out, tsv_out)
            finally:
                self.gate.source_gate.atomic_write_text = original
            self.assertFalse(json_out.exists())
            self.assertFalse(tsv_out.exists())
            self.assertEqual(list(tmp.glob(".*.paired-stage.*")), [])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_write_outputs_rejects_symlink_parent(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            real_parent = tmp / "real"
            link_parent = tmp / "link-parent"
            real_parent.mkdir()
            os.symlink(real_parent, link_parent)
            with self.assertRaisesRegex(
                self.gate.GeneratedAdjacentLabelInventoryGateError,
                "output path must not traverse symlinks",
            ):
                self.gate.write_outputs(
                    self.__class__.payload,
                    link_parent / "out.json",
                    None,
                )

    def test_source_decoders_raise_gate_error_for_invalid_utf8(self) -> None:
        with self.assertRaisesRegex(
            self.gate.GeneratedAdjacentLabelInventoryGateError,
            "rust native seq32 attention mlp source must be UTF-8",
        ):
            self.gate.rust_adjacent_adapter_modes(b"\xff")
        with self.assertRaisesRegex(
            self.gate.GeneratedAdjacentLabelInventoryGateError,
            "cli native seq32 attention mlp source must be UTF-8",
        ):
            self.gate.cli_adjacent_commands(b"\xff", {})


if __name__ == "__main__":
    unittest.main()
