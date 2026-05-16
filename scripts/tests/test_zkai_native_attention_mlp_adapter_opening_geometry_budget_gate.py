import csv
import copy
import io
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from scripts import zkai_native_attention_mlp_adapter_opening_geometry_budget_gate as gate


class AdapterOpeningGeometryBudgetGateTests(unittest.TestCase):
    def test_payload_validates_and_pins_best_attack(self) -> None:
        context = gate.build_context()
        payload = gate.build_payload(context)
        gate.validate_payload(payload, context=context)

        summary = payload["summary"]
        self.assertEqual(summary["best_current_one_proof_variant"], "compact_selector")
        self.assertEqual(summary["best_current_one_proof_typed_bytes"], 40_812)
        self.assertEqual(summary["best_current_one_proof_delta_to_frontier_bytes"], 112)
        self.assertEqual(summary["best_semantic_fusion_attack"], "rmsnorm_input_fused")
        self.assertEqual(summary["best_semantic_fusion_delta_to_frontier_bytes"], 728)
        self.assertEqual(summary["best_semantic_fusion_reduction_to_beat_frontier_bytes"], 729)
        self.assertEqual(summary["best_semantic_fusion_path_opening_overhang_bytes"], 1_008)
        self.assertEqual(summary["best_semantic_fusion_opening_removal_fraction_to_beat_frontier"], 0.723214)
        self.assertEqual(
            [item["proof_size_bytes"] for item in payload["recorded_verifier_outputs"]],
            [124_585, 116_091, 119_360, 118_378, 119_790],
        )
        self.assertTrue(all(item["verified"] for item in payload["recorded_verifier_outputs"]))

    def test_mutations_are_present_and_rejected(self) -> None:
        payload = gate.build_payload()
        cases = payload["mutation_result"]["cases"]
        self.assertEqual([case["name"] for case in cases], list(gate.MUTATION_NAMES))
        self.assertEqual(payload["mutation_result"]["rejected_count"], len(gate.MUTATION_NAMES))
        self.assertTrue(all(case["rejected"] for case in cases))

    def test_recorded_verifier_outputs_are_deep_copied(self) -> None:
        payload = gate.build_payload()
        payload["recorded_verifier_outputs"][0]["verified"] = False

        self.assertTrue(gate.RECORDED_VERIFIER_OUTPUTS[0]["verified"])
        with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "payload body drift"):
            gate.validate_payload(payload)

    def test_two_proof_frontier_overclaim_is_rejected(self) -> None:
        context = gate.build_context()
        payload = gate.build_payload(context)
        candidate = copy.deepcopy(payload)
        candidate["frontier"]["two_proof_frontier_win_claimed"] = True
        gate.refresh_payload_commitment(candidate)

        with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "two-proof frontier"):
            gate.validate_payload(candidate, context=context)

    def test_nanozk_overclaim_is_rejected(self) -> None:
        context = gate.build_context()
        payload = gate.build_payload(context)
        candidate = copy.deepcopy(payload)
        candidate["frontier"]["nanozk_win_claimed"] = True
        gate.refresh_payload_commitment(candidate)

        with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "NANOZK"):
            gate.validate_payload(candidate, context=context)

    def test_nanozk_workload_match_drift_is_rejected(self) -> None:
        context = gate.build_context()
        payload = gate.build_payload(context)
        candidate = copy.deepcopy(payload)
        candidate["frontier"]["nanozk_workload_matched"] = True
        gate.refresh_payload_commitment(candidate)

        with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "NANOZK workload"):
            gate.validate_payload(candidate, context=context)

    def test_empty_semantic_attack_set_is_rejected_cleanly(self) -> None:
        expected_variants = copy.deepcopy(gate.EXPECTED_VARIANTS)
        for variant in expected_variants.values():
            variant["semantic_fusion_attack"] = False

        with mock.patch.object(gate, "EXPECTED_VARIANTS", expected_variants):
            with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "no viable semantic-fusion"):
                gate.build_payload()

    def test_source_gate_commitment_drift_is_rejected(self) -> None:
        context = gate.build_context()
        artifact = context["source_gate_artifacts"]["rmsnorm_input_fused"]["payload"]
        artifact["payload_commitment"] = "blake2b-256:" + "00" * 32

        with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "source gate payload_commitment"):
            gate.build_payload(context)

    def test_source_gate_raw_digest_drift_is_rejected(self) -> None:
        context = gate.build_context()
        context["source_gate_artifacts"]["rmsnorm_input_fused"]["sha256"] = "0" * 64

        with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "raw digest drift"):
            gate.build_payload(context)

    def test_accounting_raw_digest_drift_is_rejected(self) -> None:
        context = gate.build_context()
        context["accounting_sources"]["rmsnorm_input_fused"]["sha256"] = "0" * 64

        with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "accounting raw digest drift"):
            gate.build_payload(context)

    def test_malformed_typed_groups_are_rejected(self) -> None:
        context = gate.build_context()
        rows = context["accounting_sources"]["rmsnorm_input_fused"]["payload"]["rows"]
        rows[0]["local_binary_accounting"]["grouped_reconstruction"]["unexpected"] = 1

        with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "key drift"):
            gate.build_payload(context)

    def test_cross_source_accounting_drift_is_rejected(self) -> None:
        context = gate.build_context()
        rows = context["accounting_sources"]["preprocessed_output_anchor"]["payload"]["rows"]
        compact_row = next(
            row
            for row in rows
            if row["evidence_relative_path"]
            == "zkai-native-attention-mlp-source-backed-compact-adapter-2026-05.envelope.json"
        )
        compact_row["local_binary_accounting"]["component_sum_bytes"] += 1

        with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "cross-source accounting drift"):
            gate.build_payload(context)

    def test_duplicate_accounting_row_is_rejected(self) -> None:
        context = gate.build_context()
        rows = context["accounting_sources"]["source_backed_selector"]["payload"]["rows"]
        rows[1]["evidence_relative_path"] = rows[0]["evidence_relative_path"]

        with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "duplicate accounting row"):
            gate.build_payload(context)

    def test_mutation_result_drift_is_rejected(self) -> None:
        context = gate.build_context()
        payload = gate.build_payload(context)
        candidate = copy.deepcopy(payload)
        candidate["mutation_result"]["cases"][0]["rejected"] = False
        gate.refresh_payload_commitment(candidate)

        with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "mutation result drift"):
            gate.validate_payload(candidate, context=context)

    def test_write_outputs_rejects_paths_outside_evidence_dir(self) -> None:
        payload = gate.build_payload()
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = pathlib.Path(tmpdir) / "budget.json"
            with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "inside"):
                gate.write_outputs(payload, json_path, None)

    def test_write_outputs_rejects_wrong_suffix(self) -> None:
        payload = gate.build_payload()
        with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "suffix"):
            gate.write_outputs(payload, gate.EVIDENCE_DIR / "budget.txt", None)

    def test_write_outputs_rejects_invalid_payload_before_writing(self) -> None:
        payload = gate.build_payload()
        payload["summary"]["best_current_one_proof_typed_bytes"] += 1
        gate.refresh_payload_commitment(payload)

        with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "summary drift"):
            gate.write_outputs(payload, gate.JSON_OUT, None)

    def test_tsv_rows_use_canonical_order(self) -> None:
        payload = gate.build_payload()
        variant_names = list(payload["variants"])
        payload["variants"] = {name: payload["variants"][name] for name in reversed(variant_names)}

        rows = list(csv.DictReader(io.StringIO(gate.build_tsv_text(payload)), dialect="excel-tab"))

        self.assertEqual([row["variant"] for row in rows], sorted(variant_names))

    def test_output_path_resolution_is_repo_relative(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = pathlib.Path.cwd()
            os.chdir(tmpdir)
            try:
                path = pathlib.Path(
                    "docs/engineering/evidence/"
                    "zkai-native-attention-mlp-adapter-opening-geometry-budget-2026-05.json"
                )
                resolved = gate.require_output_path(path, ".json")
            finally:
                os.chdir(original_cwd)

        self.assertEqual(resolved, gate.JSON_OUT)

    def test_output_path_rejects_symlinked_evidence_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = pathlib.Path(tmpdir)
            target = directory / "outside"
            evidence = directory / "evidence"
            target.mkdir()
            try:
                os.symlink(target, evidence)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")

            with mock.patch.object(gate, "EVIDENCE_DIR", evidence):
                with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "symlinked evidence"):
                    gate.require_output_path(evidence / "budget.json", ".json")

    def test_text_outputs_are_written_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = pathlib.Path(tmpdir) / "budget.json"
            tsv_path = pathlib.Path(tmpdir) / "budget.tsv"
            gate.write_text_atomically(json_path, "{}\n")
            gate.write_text_atomically(tsv_path, "variant\n")

            self.assertTrue(json_path.exists())
            self.assertTrue(tsv_path.exists())
            tsv_text = tsv_path.read_text(encoding="utf-8")
            self.assertEqual(tsv_text, "variant\n")
            self.assertFalse(any(path.name.endswith(".tmp") for path in pathlib.Path(tmpdir).iterdir()))

    def test_symlink_output_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = pathlib.Path(tmpdir)
            target = directory / "target.json"
            symlink = directory / "budget.json"
            target.write_text("{}", encoding="utf-8")
            try:
                os.symlink(target, symlink)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")

            with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "symlink"):
                gate.write_text_atomically(symlink, "{}\n")

    def test_read_json_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = pathlib.Path(tmpdir)
            target = directory / "target.json"
            symlink = directory / "source.json"
            target.write_text("{}", encoding="utf-8")
            try:
                os.symlink(target, symlink)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")

            with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "symlink"):
                gate.read_json_and_raw(symlink)

    def test_read_json_fails_closed_without_o_nofollow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "source.json"
            path.write_text("{}", encoding="utf-8")

            with mock.patch.object(gate.os, "O_NOFOLLOW", None):
                with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "O_NOFOLLOW"):
                    gate.read_json_and_raw(path)

    def test_fsync_parent_dir_uses_o_directory_when_available(self) -> None:
        directory_flag = getattr(os, "O_DIRECTORY", 0)
        if not isinstance(directory_flag, int) or directory_flag == 0:
            self.skipTest("O_DIRECTORY unavailable")

        calls = []
        real_open = os.open

        def recording_open(path: pathlib.Path, flags: int, *args: object, **kwargs: object) -> int:
            calls.append(flags)
            return real_open(path, flags, *args, **kwargs)

        with mock.patch.object(gate.os, "open", side_effect=recording_open):
            gate.fsync_parent_dir(gate.JSON_OUT)

        self.assertTrue(calls)
        self.assertTrue(calls[-1] & directory_flag)

    def test_read_json_wraps_invalid_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "invalid.json"
            path.write_bytes(b"\xff")

            with self.assertRaisesRegex(gate.AdapterOpeningGeometryBudgetError, "failed to parse"):
                gate.read_json_and_raw(path)


if __name__ == "__main__":
    unittest.main()
