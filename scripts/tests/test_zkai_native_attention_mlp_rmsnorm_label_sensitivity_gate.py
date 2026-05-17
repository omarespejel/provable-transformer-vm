import copy
import pathlib
import tempfile
import unittest
from unittest import mock

from scripts import zkai_native_attention_mlp_rmsnorm_label_sensitivity_gate as gate


class RmsnormLabelSensitivityGateTest(unittest.TestCase):
    def test_payload_pins_label_only_span_without_frontier_promotion(self) -> None:
        payload = gate.build_payload()
        summary = payload["summary"]
        self.assertEqual(summary["canonical_rmsnorm_input_fused_typed_bytes"], 41_428)
        self.assertEqual(summary["best_label_probe"], "label_probe_a")
        self.assertEqual(summary["best_label_probe_typed_bytes"], 40_836)
        self.assertEqual(summary["best_label_probe_delta_vs_frontier_bytes"], 136)
        self.assertEqual(summary["best_label_probe_delta_vs_compact_bytes"], 24)
        self.assertEqual(summary["best_label_probe_reduction_vs_canonical_bytes"], 592)
        self.assertEqual(summary["label_only_typed_span_bytes"], 1_264)
        self.assertTrue(summary["label_only_span_exceeds_required_frontier_reduction"])
        self.assertFalse(payload["frontier"]["frontier_win_claimed"])
        self.assertFalse(payload["frontier"]["nanozk_win_claimed"])
        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertEqual(payload["result"], gate.RESULT)
        self.assertEqual(payload["issue"], gate.ISSUE)
        self.assertEqual(payload["claim_boundary"], gate.CLAIM_BOUNDARY)
        self.assertEqual(payload["proof_backend_version"], gate.PROOF_BACKEND_VERSION)
        self.assertEqual(payload["proof_schema_version"], gate.PROOF_SCHEMA_VERSION)
        self.assertEqual(payload["interpretation"], gate.INTERPRETATION)
        self.assertEqual(payload["non_claims"], list(gate.NON_CLAIMS))
        self.assertEqual(payload["validation_commands"], list(gate.VALIDATION_COMMANDS))
        self.assertEqual(
            payload["source_artifacts"],
            [
                {
                    "name": "baseline_accounting",
                    "path": str(gate.BASE_ACCOUNTING_PATH.relative_to(gate.ROOT)),
                    "sha256": gate.EXPECTED_SOURCE_SHA256["baseline_accounting"],
                },
                {
                    "name": "label_probe_accounting",
                    "path": str(gate.LABEL_ACCOUNTING_PATH.relative_to(gate.ROOT)),
                    "sha256": gate.EXPECTED_SOURCE_SHA256["label_probe_accounting"],
                },
            ],
        )

    def test_label_probes_preserve_direct_value_bytes(self) -> None:
        payload = gate.build_payload()
        canonical = payload["variants"]["rmsnorm_input_fused"]
        for name in ("label_probe_a", "label_probe_b"):
            with self.subTest(name=name):
                probe = payload["variants"][name]
                self.assertEqual(probe["value_bytes"], canonical["value_bytes"])
                self.assertEqual(probe["value_delta_vs_canonical"], 0)
                self.assertNotEqual(
                    probe["path_opening_delta_vs_canonical"],
                    0,
                    "label-only movement should be path/opening movement",
                )

    def test_best_label_probe_still_does_not_beat_compact_or_frontier(self) -> None:
        payload = gate.build_payload()
        compact = payload["variants"]["compact_selector"]
        probe = payload["variants"]["label_probe_a"]
        self.assertGreater(probe["typed_bytes"], compact["typed_bytes"])
        self.assertGreater(
            probe["typed_bytes"],
            payload["frontier"]["two_proof_frontier_typed_bytes"],
        )

    def test_mutations_reject_overclaim_and_metric_drift(self) -> None:
        payload = gate.build_payload()
        result = payload["mutation_result"]
        self.assertEqual(result["mutation_count"], len(gate.EXPECTED_MUTATION_NAMES))
        self.assertEqual(result["rejected_count"], len(gate.EXPECTED_MUTATION_NAMES))
        self.assertEqual(
            [case["name"] for case in result["cases"]],
            list(gate.EXPECTED_MUTATION_NAMES),
        )
        self.assertTrue(all(case["rejected"] for case in result["cases"]))

    def test_payload_commitment_rejects_mutation(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["summary"]["label_only_typed_span_bytes"] = 1_263
        gate.refresh_payload_commitment(mutated)
        with self.assertRaises(gate.RmsnormLabelSensitivityError):
            gate.validate_payload(mutated)

    def test_validate_payload_recomputes_variant_deltas(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["variants"]["label_probe_a"]["typed_delta_vs_canonical"] = 0
        gate.refresh_payload_commitment(mutated)
        with self.assertRaises(gate.RmsnormLabelSensitivityError):
            gate.validate_payload(mutated)

    def test_validate_payload_rejects_misleading_summary_label(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["summary"]["best_label_probe"] = "label_probe_b"
        gate.refresh_payload_commitment(mutated)
        with self.assertRaises(gate.RmsnormLabelSensitivityError):
            gate.validate_payload(mutated)

    def test_validate_payload_rejects_decision_metadata_drift(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["decision"] = "GO_FRONTIER_PROMOTION"
        gate.refresh_payload_commitment(mutated)
        with self.assertRaises(gate.RmsnormLabelSensitivityError):
            gate.validate_payload(mutated)

    def test_validate_payload_reports_frontier_overclaim(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["frontier"]["frontier_win_claimed"] = True
        gate.refresh_payload_commitment(mutated)
        with self.assertRaisesRegex(gate.RmsnormLabelSensitivityError, "frontier overclaim"):
            gate.validate_payload(mutated)

    def test_validate_payload_rejects_mutation_result_drift(self) -> None:
        payload = gate.build_payload()
        mutated = copy.deepcopy(payload)
        mutated["mutation_result"]["cases"][0]["rejected"] = False
        gate.refresh_payload_commitment(mutated)
        with self.assertRaises(gate.RmsnormLabelSensitivityError):
            gate.validate_payload(mutated)

    def test_validate_payload_rejects_unexpected_summary_key(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["summary"]["unchecked_frontier_win"] = True
        gate.refresh_payload_commitment(mutated)
        with self.assertRaises(gate.RmsnormLabelSensitivityError):
            gate.validate_payload(mutated)

    def test_path_opening_bytes_rejects_missing_group(self) -> None:
        groups = dict(gate.EXPECTED_VARIANTS["label_probe_a"]["groups"])
        groups.pop("fri_decommitments")
        with self.assertRaises(gate.RmsnormLabelSensitivityError):
            gate.path_opening_bytes(groups)

    def test_accounting_row_lookup_rejects_duplicates(self) -> None:
        accounting, _ = gate.read_json(gate.LABEL_ACCOUNTING_PATH, "label accounting")
        path = gate.EXPECTED_VARIANTS["label_probe_a"]["path"]
        row = gate.row_by_path(accounting, path)
        duplicate_accounting = {"rows": [row, copy.deepcopy(row)]}
        with self.assertRaises(gate.RmsnormLabelSensitivityError):
            gate.row_by_path(duplicate_accounting, path)

    def test_tsv_has_canonical_and_probe_rows(self) -> None:
        payload = gate.build_payload()
        text = gate.tsv_text(payload)
        self.assertIn("rmsnorm_input_fused\t41428\t0\t728", text)
        self.assertIn("label_probe_a\t40836\t-592\t136", text)
        self.assertIn("label_probe_b\t42100\t672\t1400", text)

    def test_output_path_rejects_outside_evidence_dir(self) -> None:
        with self.assertRaises(gate.RmsnormLabelSensitivityError):
            gate.require_output_path(pathlib.Path("/tmp/not-evidence.json"))

    def test_output_path_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            target = tmp / "target.json"
            target.write_text("{}", encoding="utf-8")
            link = tmp / f"tmp-label-sensitivity-{target.name}"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            with mock.patch.object(gate, "EVIDENCE_DIR", tmp):
                with self.assertRaises(gate.RmsnormLabelSensitivityError):
                    gate.require_output_path(link)

    def test_output_path_rejects_dangling_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = pathlib.Path(tmpdir)
            link = tmp / "dangling.json"
            try:
                link.symlink_to(tmp / "missing.json")
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            with mock.patch.object(gate, "EVIDENCE_DIR", tmp):
                with self.assertRaises(gate.RmsnormLabelSensitivityError):
                    gate.require_output_path(link)

    def test_output_path_rejects_missing_evidence_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            evidence = root / "docs" / "engineering" / "evidence"
            with mock.patch.object(gate, "ROOT", root), mock.patch.object(gate, "EVIDENCE_DIR", evidence):
                with self.assertRaises(gate.RmsnormLabelSensitivityError):
                    gate.require_output_path(evidence / "out.json")

    def test_output_path_rejects_symlinked_evidence_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir) / "root"
            target = pathlib.Path(tmpdir) / "target"
            root.mkdir()
            target.mkdir()
            evidence = root / "docs" / "engineering" / "evidence"
            evidence.parent.mkdir(parents=True)
            try:
                evidence.symlink_to(target, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            with mock.patch.object(gate, "ROOT", root), mock.patch.object(gate, "EVIDENCE_DIR", evidence):
                with self.assertRaises(gate.RmsnormLabelSensitivityError):
                    gate.require_output_path(evidence / "out.json")

    def test_write_text_atomically_uses_exclusive_temp_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = pathlib.Path(tmpdir)
            evidence = root / "docs" / "engineering" / "evidence"
            evidence.mkdir(parents=True)
            output = evidence / "out.json"
            real_open = gate.os.open
            temp_flags = []

            def spy_open(path, flags, *args, **kwargs):
                if pathlib.Path(path).name.startswith(".out.json."):
                    temp_flags.append(flags)
                return real_open(path, flags, *args, **kwargs)

            with (
                mock.patch.object(gate, "ROOT", root),
                mock.patch.object(gate, "EVIDENCE_DIR", evidence),
                mock.patch.object(gate.os, "open", side_effect=spy_open),
            ):
                gate.write_text_atomically(output, "{}\n")
            self.assertEqual(output.read_text(encoding="utf-8"), "{}\n")
            self.assertTrue(temp_flags)
            self.assertTrue(temp_flags[0] & gate.os.O_EXCL)

    def test_read_json_rejects_source_digest_drift(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        self.assertIn("source_artifacts", payload)
        with mock.patch.dict(
            gate.EXPECTED_SOURCE_SHA256,
            {"label_probe_accounting": "00" * 32},
            clear=False,
        ):
            with self.assertRaises(gate.RmsnormLabelSensitivityError):
                gate.build_payload(include_mutations=False)

    def test_read_regular_file_requires_no_follow_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir) / "payload.json"
            path.write_text("{}", encoding="utf-8")
            with mock.patch.object(gate.os, "O_NOFOLLOW", 0, create=True):
                with self.assertRaises(gate.RmsnormLabelSensitivityError):
                    gate.read_regular_file(path, "payload")


if __name__ == "__main__":
    unittest.main()
