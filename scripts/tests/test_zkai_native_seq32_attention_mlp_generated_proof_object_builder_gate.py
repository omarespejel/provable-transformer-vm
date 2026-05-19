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
    / "zkai_native_seq32_attention_mlp_generated_proof_object_builder_gate.py"
)


def load_gate():
    spec = importlib.util.spec_from_file_location(
        "zkai_native_seq32_attention_mlp_generated_proof_object_builder_gate",
        GATE_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NativeSeq32GeneratedProofObjectBuilderGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gate = load_gate()
        cls.payload = cls.gate.payload_with_mutations()

    def test_pins_source_generated_proof_object_frontier_without_new_claim(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        summary = payload["frontier_summary"]
        self.assertEqual(
            payload["decision"],
            "GO_SOURCE_GENERATED_PROOF_OBJECT_ROWS_REPRODUCE_CURRENT_ADJACENT_FRONTIER",
        )
        self.assertEqual(summary["generated_proof_object_row_count"], 9)
        self.assertEqual(summary["accepted_row_count"], 2)
        self.assertEqual(summary["rejected_row_count"], 7)
        self.assertEqual(summary["fixed_adjacent_typed_bytes"], 42_156)
        self.assertEqual(summary["fixed_adjacent_miss_vs_champion_typed_bytes"], 88)
        self.assertEqual(summary["worst_accepted_label_id"], "adjacent_label_probe_a")
        self.assertEqual(summary["worst_accepted_typed_bytes"], 40_332)
        self.assertEqual(summary["worst_accepted_saving_typed_bytes"], 1_736)
        self.assertEqual(summary["best_accepted_label_id"], "adjacent_label_probe_b")
        self.assertEqual(summary["best_accepted_typed_bytes"], 37_532)
        self.assertEqual(summary["best_accepted_saving_typed_bytes"], 4_536)
        self.assertEqual(summary["best_accepted_saving_share"], "0.107825")
        self.assertFalse(summary["new_frontier_claimed"])
        self.assertEqual(summary["proof_size_comparable_external_rows"], 0)
        self.gate.validate_payload(payload)

    def test_rows_bind_generated_labels_to_accounting_and_envelopes(self) -> None:
        rows = {row["variant_id"]: row for row in self.__class__.payload["proof_object_rows"]}
        fixed = rows["fixed_adjacent_layout"]
        probe_a = rows["adjacent_label_probe_a"]
        probe_b = rows["adjacent_label_probe_b"]
        seed_02 = rows["adjacent_seed_02"]
        self.assertEqual(fixed["policy_status"], "rejected_inflating_label")
        self.assertEqual(fixed["typed_saving_vs_champion"], -88)
        self.assertEqual(fixed["proof_len_bytes"], 122_688)
        self.assertEqual(fixed["path_opening_bytes"], 21_184)
        self.assertEqual(fixed["proof_sha256"], "f1a495236e06cb3bb76e7f7cb900b9b96eb203809f791d28238fc948514126ed")
        self.assertEqual(probe_a["policy_status"], "supported_label")
        self.assertEqual(probe_a["typed_bytes"], 40_332)
        self.assertEqual(probe_a["typed_saving_vs_champion"], 1_736)
        self.assertEqual(probe_a["proof_json_bytes"], probe_a["proof_len_bytes"])
        self.assertEqual(probe_a["record_stream_sha256"], "ab9c27d7b780f81ec8f8f562997392362c18c9ddc6315d1db303520e3fd7e682")
        self.assertEqual(probe_b["policy_status"], "supported_label")
        self.assertEqual(probe_b["typed_bytes"], 37_532)
        self.assertEqual(probe_b["typed_saving_vs_champion"], 4_536)
        self.assertEqual(probe_b["proof_json_bytes"], 106_317)
        self.assertEqual(probe_b["path_opening_bytes"], 16_560)
        self.assertEqual(probe_b["value_bytes"], 20_924)
        self.assertEqual(seed_02["policy_status"], "rejected_unpromoted_seed_label")
        self.assertEqual(seed_02["typed_bytes"], 40_268)
        self.assertEqual(seed_02["path_opening_bytes"], 19_296)

    def test_source_artifacts_pin_generated_inventory_and_accounting(self) -> None:
        artifacts = {row["id"]: row for row in self.__class__.payload["source_artifacts"]}
        inventory = artifacts["generated_adjacent_label_inventory"]
        accounting = artifacts["adjacent_label_seed_sweep_accounting"]
        self.assertEqual(inventory["sha256"], self.gate.EXPECTED_GENERATED_INVENTORY_SHA256)
        self.assertEqual(inventory["payload_commitment"], self.gate.EXPECTED_GENERATED_INVENTORY_COMMITMENT)
        self.assertEqual(accounting["sha256"], self.gate.EXPECTED_ACCOUNTING_SHA256)
        self.assertIsNone(accounting["payload_commitment"])

    def test_builder_policy_is_generated_and_manual_override_is_forbidden(self) -> None:
        policy = self.__class__.payload["builder_policy"]
        self.assertFalse(policy["manual_override_allowed"])
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
        self.assertIn("fixed_adjacent_layout", policy["rejected_label_ids"])
        self.assertIn("adjacent_seed_02", policy["rejected_label_ids"])
        self.assertEqual(
            policy["row_join_key"],
            "generated_label_inventory.path == accounting.evidence_relative_path",
        )

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

    def test_rejects_source_artifact_or_manual_policy_drift(self) -> None:
        cases = [
            (lambda p: p["source_artifacts"][0].update({"sha256": "0" * 64}), "source artifact drift"),
            (lambda p: p["builder_policy"].update({"manual_override_allowed": True}), "builder policy drift"),
        ]
        for mutate, error in cases:
            with self.subTest(error=error):
                payload = copy.deepcopy(self.__class__.payload)
                mutate(payload)
                payload["payload_commitment"] = self.gate.payload_commitment(payload)
                with self.assertRaisesRegex(self.gate.GeneratedProofObjectBuilderGateError, error):
                    self.gate.validate_payload(payload)

    def test_rejects_proof_object_row_drift(self) -> None:
        cases = [
            ("path", "other.envelope.json"),
            ("proof_sha256", "1" * 64),
            ("envelope_sha256", "2" * 64),
            ("record_stream_sha256", "3" * 64),
            ("proof_len_bytes", 1),
            ("typed_bytes", self.gate.CURRENT_CHAMPION_TYPED_BYTES),
            ("proof_backend_version", "wrong"),
        ]
        for field, value in cases:
            with self.subTest(field=field):
                payload = copy.deepcopy(self.__class__.payload)
                payload["proof_object_rows"][1][field] = value
                payload["payload_commitment"] = self.gate.payload_commitment(payload)
                with self.assertRaisesRegex(
                    self.gate.GeneratedProofObjectBuilderGateError,
                    "proof object row drift",
                ):
                    self.gate.validate_payload(payload)

    def test_load_generated_inventory_rechecks_rebuilt_source_payload(self) -> None:
        original = self.gate.inventory_gate.build_payload
        rebuilt = original()
        rebuilt["decision"] = "NO_GO"

        def drifted_inventory_payload():
            return rebuilt

        self.gate.inventory_gate.build_payload = drifted_inventory_payload
        try:
            with self.assertRaisesRegex(
                self.gate.GeneratedProofObjectBuilderGateError,
                "generated inventory rebuild drift",
            ):
                self.gate.load_generated_inventory()
        finally:
            self.gate.inventory_gate.build_payload = original

    def test_rejects_duplicate_generated_or_accounting_join_keys(self) -> None:
        generated = {
            "generated_label_inventory": [
                {"variant_id": "duplicate"},
                {"variant_id": "duplicate"},
            ]
        }
        accounting = {
            "rows": [
                {"evidence_relative_path": "same.envelope.json"},
                {"evidence_relative_path": "same.envelope.json"},
            ]
        }
        with self.assertRaisesRegex(
            self.gate.GeneratedProofObjectBuilderGateError,
            "generated label inventory duplicate variant_id",
        ):
            self.gate.generated_rows_by_id(generated)
        with self.assertRaisesRegex(
            self.gate.GeneratedProofObjectBuilderGateError,
            "accounting rows duplicate evidence_relative_path",
        ):
            self.gate.accounting_rows_by_path(accounting)

    def test_frontier_summary_rejects_missing_required_partitions(self) -> None:
        rows = copy.deepcopy(self.__class__.payload["proof_object_rows"])
        for row in rows:
            row["policy_status"] = "rejected_inflating_label"
        with self.assertRaisesRegex(
            self.gate.GeneratedProofObjectBuilderGateError,
            "frontier summary drift",
        ):
            self.gate.build_frontier_summary(rows)
        rows = [
            row
            for row in self.__class__.payload["proof_object_rows"]
            if row["variant_id"] != "fixed_adjacent_layout"
        ]
        with self.assertRaisesRegex(
            self.gate.GeneratedProofObjectBuilderGateError,
            "frontier summary drift",
        ):
            self.gate.build_frontier_summary(rows)

    def test_envelope_metadata_rejects_missing_or_mismatched_fields(self) -> None:
        metadata = {
            "proof_backend": "stwo",
            "proof_backend_version": "version",
        }
        with self.assertRaisesRegex(
            self.gate.GeneratedProofObjectBuilderGateError,
            "envelope proof_backend_version must be non-empty string",
        ):
            self.gate.envelope_metadata_fields({"proof_backend": "stwo"}, metadata)
        with self.assertRaisesRegex(
            self.gate.GeneratedProofObjectBuilderGateError,
            "envelope metadata drift",
        ):
            self.gate.envelope_metadata_fields(
                {"proof_backend": "stwo", "proof_backend_version": "other"},
                metadata,
            )

    def test_render_tsv_records_proof_object_rows_and_audit_pins(self) -> None:
        text = self.gate.render_tsv(self.__class__.payload)
        self.assertTrue(text.startswith("variant_id\tadapter_mode\tcli_command\t"))
        rows = list(csv.DictReader(io.StringIO(text), delimiter="\t"))
        self.assertEqual(len(rows), 9)
        fixed = rows[0]
        probe_b = rows[2]
        seed_02 = rows[5]
        self.assertEqual(fixed["variant_id"], "fixed_adjacent_layout")
        self.assertEqual(fixed["typed_saving_vs_champion"], "-88")
        self.assertEqual(probe_b["variant_id"], "adjacent_label_probe_b")
        self.assertEqual(probe_b["typed_bytes"], "37532")
        self.assertEqual(probe_b["proof_len_bytes"], "106317")
        self.assertEqual(seed_02["variant_id"], "adjacent_seed_02")
        self.assertEqual(seed_02["policy_status"], "rejected_unpromoted_seed_label")
        self.assertIn(
            f"generated_adjacent_label_inventory={self.gate.EXPECTED_GENERATED_INVENTORY_SHA256}",
            probe_b["source_artifact_digest_pins"],
        )
        self.assertIn(
            "accounting_digest_drift=rejected:source artifact drift",
            probe_b["mutation_outcomes"],
        )

    def test_write_outputs_records_json_and_tsv_inside_evidence_tree(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            json_out = tmp / "builder.json"
            tsv_out = tmp / "builder.tsv"
            self.gate.write_outputs(self.__class__.payload, json_out, tsv_out)
            self.assertIn(
                "GO_SOURCE_GENERATED_PROOF_OBJECT_ROWS_REPRODUCE_CURRENT_ADJACENT_FRONTIER",
                json_out.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "adjacent_label_probe_b\trmsnorm_input_fused_adjacent_label_probe_b_v1",
                tsv_out.read_text(encoding="utf-8"),
            )

    def test_write_outputs_rejects_invalid_payload_without_artifacts(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["frontier_summary"]["best_accepted_typed_bytes"] = self.gate.CURRENT_CHAMPION_TYPED_BYTES
        payload["payload_commitment"] = self.gate.payload_commitment(payload)
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            bad_json = tmp / "bad.json"
            bad_tsv = tmp / "bad.tsv"
            with self.assertRaisesRegex(
                self.gate.GeneratedProofObjectBuilderGateError,
                "frontier summary drift",
            ):
                self.gate.write_outputs(payload, bad_json, bad_tsv)
            self.assertFalse(bad_json.exists())
            self.assertFalse(bad_tsv.exists())

    def test_write_outputs_rejects_path_outside_evidence_dir(self) -> None:
        with tempfile.TemporaryDirectory() as outside_dir, tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            outside = pathlib.Path(outside_dir) / "outside.json"
            tsv_out = pathlib.Path(tmpdir) / "inside.tsv"
            with self.assertRaisesRegex(
                self.gate.GeneratedProofObjectBuilderGateError,
                "output path escapes evidence dir",
            ):
                self.gate.write_outputs(self.__class__.payload, outside, tsv_out)
            self.assertFalse(outside.exists())
            self.assertFalse(tsv_out.exists())

    def test_write_outputs_requires_paired_json_and_tsv_paths(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            json_out = pathlib.Path(tmpdir) / "builder.json"
            with self.assertRaisesRegex(
                self.gate.GeneratedProofObjectBuilderGateError,
                "paired JSON/TSV output paths required",
            ):
                self.gate.write_outputs(self.__class__.payload, json_out, None)
            self.assertFalse(json_out.exists())

    def test_write_outputs_wraps_raw_writer_exceptions(self) -> None:
        original = self.gate.inventory_gate.source_gate.atomic_write_text

        def fail_writer(_path: pathlib.Path, _text: str) -> None:
            raise OSError("disk full")

        self.gate.inventory_gate.source_gate.atomic_write_text = fail_writer
        try:
            with self.assertRaisesRegex(
                self.gate.GeneratedProofObjectBuilderGateError,
                "failed to write output: disk full",
            ):
                self.gate.write_outputs(self.__class__.payload, self.gate.JSON_OUT, self.gate.TSV_OUT)
        finally:
            self.gate.inventory_gate.source_gate.atomic_write_text = original

    def test_write_outputs_rolls_back_paired_publish_if_second_final_fails(self) -> None:
        original = self.gate.inventory_gate.source_gate.atomic_write_text
        calls = 0
        final_publish_calls = 0
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            json_out = tmp / "builder.json"
            tsv_out = tmp / "builder.tsv"

            def fail_second_final_publish(path: pathlib.Path, text: str) -> None:
                nonlocal calls, final_publish_calls
                calls += 1
                if path in {json_out, tsv_out}:
                    final_publish_calls += 1
                    if final_publish_calls == 2:
                        raise OSError("second final publish failed")
                original(path, text)

            self.gate.inventory_gate.source_gate.atomic_write_text = fail_second_final_publish
            try:
                with self.assertRaisesRegex(
                    self.gate.GeneratedProofObjectBuilderGateError,
                    "failed to write output: second final publish failed",
                ):
                    self.gate.write_outputs(self.__class__.payload, json_out, tsv_out)
            finally:
                self.gate.inventory_gate.source_gate.atomic_write_text = original
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
                self.gate.GeneratedProofObjectBuilderGateError,
                "output path must not traverse symlinks",
            ):
                self.gate.write_outputs(
                    self.__class__.payload,
                    link_parent / "out.json",
                    link_parent / "out.tsv",
                )


if __name__ == "__main__":
    unittest.main()
