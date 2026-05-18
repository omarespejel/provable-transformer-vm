import copy
import os
import tempfile
import unittest
from pathlib import Path

from scripts import zkai_larger_native_boundary_source_compatibility_gate as gate


class LargerNativeBoundarySourceCompatibilityGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = gate.build_context()
        cls.payload = gate.build_payload(cls.context)

    def fresh_payload(self) -> dict:
        return copy.deepcopy(self.payload)

    def unique_evidence_path(self, prefix: str, suffix: str) -> Path:
        fd, name = tempfile.mkstemp(dir=gate.EVIDENCE_DIR, prefix=prefix, suffix=suffix)
        os.close(fd)
        path = Path(name)
        path.unlink()
        self.addCleanup(path.unlink, missing_ok=True)
        return path

    def test_payload_records_seq32_value_incompatibility(self) -> None:
        payload = self.fresh_payload()
        gate.validate_payload(payload)
        summary = payload["summary"]
        self.assertEqual(summary["d8_adapter_mismatches"], 0)
        self.assertEqual(summary["d8_adapter_matches"], 128)
        self.assertEqual(summary["seq32_adapter_mismatches"], 113)
        self.assertEqual(summary["seq32_adapter_matches"], 15)
        self.assertEqual(summary["seq32_mismatch_share"], 0.882812)
        self.assertEqual(summary["seq32_attention_flat_cells"], 512)
        self.assertEqual(summary["mlp_rmsnorm_input_rows"], 128)
        self.assertEqual(len(summary["first_seq32_mismatches"]), 10)

    def test_selector_context_is_pinned(self) -> None:
        selector = self.fresh_payload()["selector_context"]
        self.assertEqual(selector["selected_route"], "two_head_seq32_fused_attention")
        self.assertEqual(selector["selected_lookup_claims"], 1184)
        self.assertEqual(selector["selected_attention_typed_bytes"], 22916)
        self.assertEqual(selector["selected_mlp_typed_bytes"], 22576)
        self.assertEqual(selector["matched_two_proof_frontier_typed_bytes"], 45492)

    def test_interpretation_stays_no_go(self) -> None:
        interpretation = self.fresh_payload()["interpretation"]
        self.assertIs(interpretation["native_larger_boundary_proof_object_exists"], False)
        self.assertIs(interpretation["adapter_value_binding_preserved"], False)
        self.assertIn("regenerate", interpretation["next_experiment"])

    def test_source_artifacts_are_pinned_by_path_and_digest(self) -> None:
        artifacts = self.fresh_payload()["source_artifacts"]
        self.assertEqual(
            [artifact["id"] for artifact in artifacts],
            [
                "d8_attention_control",
                "two_head_seq32_attention_candidate",
                "attention_derived_d128_mlp_input",
                "larger_native_boundary_selector",
            ],
        )
        for artifact in artifacts:
            self.assertTrue(artifact["path"].startswith("docs/engineering/evidence/"))
            self.assertEqual(len(artifact["sha256"]), 64)

    def test_all_mutations_reject(self) -> None:
        payload = self.fresh_payload()
        cases = payload["mutation_result"]["cases"]
        self.assertEqual(payload["mutation_inventory"]["cases"], list(gate.MUTATION_NAMES))
        self.assertEqual([case["name"] for case in cases], list(gate.MUTATION_NAMES))
        self.assertEqual(len(cases), len(gate.MUTATION_NAMES))
        self.assertTrue(all(case["rejected"] for case in cases))
        for case in cases:
            self.assertEqual(case["reason"], gate.EXPECTED_MUTATION_REASONS[case["name"]])

    def test_promoting_go_rejects(self) -> None:
        payload = self.fresh_payload()
        payload["decision"] = "GO_NATIVE_LARGER_BOUNDARY_PROOF_OBJECT_READY"
        gate.refresh_payload_commitments(payload)
        with self.assertRaisesRegex(gate.LargerNativeBoundaryCompatibilityError, "decision drift"):
            gate.validate_payload(payload)

    def test_payload_commitment_drift_rejects(self) -> None:
        payload = self.fresh_payload()
        payload["payload_commitment"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(gate.LargerNativeBoundaryCompatibilityError, "payload commitment drift"):
            gate.validate_payload(payload)

    def test_to_tsv_validates_payload(self) -> None:
        tsv = gate.to_tsv(self.fresh_payload())
        expected = (
            "decision\tresult\td8_adapter_mismatches\tseq32_adapter_mismatches\tseq32_adapter_matches\t"
            "mismatch_share\tselected_lookup_claims\tselected_attention_typed_bytes\t"
            "matched_two_proof_frontier_typed_bytes\n"
            "NO_GO_CURRENT_D128_MLP_INPUT_NOT_VALUE_COMPATIBLE_WITH_TWO_HEAD_SEQ32_ATTENTION\t"
            "REGENERATE_SEQ32_DERIVED_D128_MLP_SURFACE_BEFORE_NATIVE_PROOF_OBJECT\t"
            "0\t113\t15\t0.882812\t1184\t22916\t45492\n"
        )
        self.assertEqual(tsv, expected)

    def test_written_payload_validates(self) -> None:
        handle = tempfile.NamedTemporaryFile(
            dir=gate.EVIDENCE_DIR,
            prefix=".tmp-larger-boundary-compat-",
            suffix=".json",
            delete=False,
        )
        path = Path(handle.name)
        handle.close()
        try:
            gate.write_json(path, self.fresh_payload())
            loaded = gate.read_json_and_raw(path, "written payload")[0]
            gate.validate_payload(loaded)
        finally:
            path.unlink(missing_ok=True)

    def test_write_json_validates_before_writing(self) -> None:
        payload = self.fresh_payload()
        payload["decision"] = "GO_BAD"
        gate.refresh_payload_commitments(payload)
        path = self.unique_evidence_path(".tmp-larger-boundary-compat-invalid-", ".json")
        with self.assertRaisesRegex(gate.LargerNativeBoundaryCompatibilityError, "decision drift"):
            gate.write_json(path, payload)
        self.assertFalse(path.exists())

    def test_relative_output_path_is_repo_root_anchored(self) -> None:
        target = self.unique_evidence_path(".tmp-larger-boundary-compat-root-anchored-", ".json")
        relative = target.relative_to(gate.ROOT)
        cwd = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                os.chdir(tmp)
                gate.write_json(relative, self.fresh_payload())
        finally:
            os.chdir(cwd)
        try:
            self.assertTrue(target.exists())
            loaded = gate.read_json_and_raw(target, "root-anchored output")[0]
            gate.validate_payload(loaded)
        finally:
            target.unlink(missing_ok=True)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_json_output_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-compat-json-symlink-") as tmp:
            temp_dir = Path(tmp)
            target = temp_dir / "target.json"
            link = temp_dir / "out.json"
            target.write_text("{}", encoding="utf-8")
            try:
                link.symlink_to(target)
            except OSError as err:
                self.skipTest(f"symlink creation unavailable: {err}")
            with self.assertRaisesRegex(gate.LargerNativeBoundaryCompatibilityError, "symlink"):
                gate.write_json(link, self.fresh_payload())

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_tsv_output_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-compat-tsv-symlink-") as tmp:
            temp_dir = Path(tmp)
            target = temp_dir / "target.tsv"
            link = temp_dir / "out.tsv"
            target.write_text("", encoding="utf-8")
            try:
                link.symlink_to(target)
            except OSError as err:
                self.skipTest(f"symlink creation unavailable: {err}")
            with self.assertRaisesRegex(gate.LargerNativeBoundaryCompatibilityError, "symlink"):
                gate.write_tsv(link, self.fresh_payload())

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_json_output_rejects_dangling_symlink(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-compat-json-dangling-symlink-") as tmp:
            temp_dir = Path(tmp)
            target = temp_dir / "missing-target.json"
            link = temp_dir / "out.json"
            try:
                link.symlink_to(target)
            except OSError as err:
                self.skipTest(f"symlink creation unavailable: {err}")
            self.assertFalse(link.exists())
            self.assertTrue(link.is_symlink())
            with self.assertRaisesRegex(gate.LargerNativeBoundaryCompatibilityError, "symlink"):
                gate.write_json(link, self.fresh_payload())

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_tsv_output_rejects_dangling_symlink(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-compat-tsv-dangling-symlink-") as tmp:
            temp_dir = Path(tmp)
            target = temp_dir / "missing-target.tsv"
            link = temp_dir / "out.tsv"
            try:
                link.symlink_to(target)
            except OSError as err:
                self.skipTest(f"symlink creation unavailable: {err}")
            self.assertFalse(link.exists())
            self.assertTrue(link.is_symlink())
            with self.assertRaisesRegex(gate.LargerNativeBoundaryCompatibilityError, "symlink"):
                gate.write_tsv(link, self.fresh_payload())

    def test_json_output_path_escape_rejects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp) / "compat.json"
            with self.assertRaisesRegex(gate.LargerNativeBoundaryCompatibilityError, "escapes evidence directory"):
                gate.write_json(outside, self.fresh_payload())

    def test_tsv_output_path_escape_rejects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp) / "compat.tsv"
            with self.assertRaisesRegex(gate.LargerNativeBoundaryCompatibilityError, "escapes evidence directory"):
                gate.write_tsv(outside, self.fresh_payload())


if __name__ == "__main__":
    unittest.main()
