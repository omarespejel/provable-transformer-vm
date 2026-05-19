import copy
import importlib.util
import json
import os
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "scripts" / "zkai_bounded_stwo_query_policy_hook_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location("bounded_stwo_query_policy_hook_gate", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BoundedStwoQueryPolicyHookGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()
        try:
            cls.payload = cls.gate.build_payload()
        except cls.gate.BoundedStwoQueryPolicyHookGateError as err:
            if "Stwo 2.2.0 source is not available" in str(err):
                raise unittest.SkipTest(str(err)) from err
            raise

    def design(self, hook_id):
        for design in self.payload["hook_designs"]:
            if design["hook_id"] == hook_id:
                return design
        self.fail(f"missing hook design {hook_id}")

    def test_payload_records_narrow_no_go_not_proof_size_frontier(self):
        self.assertEqual(
            self.payload["decision"],
            "NARROW_CLAIM_STWO_2_2_COUPLES_QUERY_DRAW_AND_DECOMMITMENT",
        )
        self.assertEqual(
            self.payload["result"],
            "NO_GO_REPO_LOCAL_QUERY_POLICY_HOOK_WITHOUT_STWO_PROVER_VERIFIER_API_PATCH",
        )
        assessment = self.payload["bounded_hook_assessment"]
        self.assertFalse(assessment["repo_local_hook_available"])
        self.assertFalse(assessment["true_predecommit_query_policy_available"])
        self.assertTrue(assessment["needs_matched_prover_verifier_patch"])
        self.assertFalse(assessment["go_gate_satisfied"])
        self.assertEqual(assessment["proof_size_delta_typed_bytes"], 0)

    def test_source_audit_pins_stwo_query_draw_and_verifier_sampling(self):
        markers = self.payload["source_audit"]["stwo_markers"]
        self.assertTrue(markers["fri_decommit_draws_queries_from_channel"])
        self.assertTrue(markers["fri_decommit_uses_decommit_on_queries"])
        self.assertTrue(markers["pcs_decommit_calls_fri_prover_decommit_channel"])
        self.assertTrue(markers["pcs_trace_decommit_uses_query_positions"])
        self.assertTrue(markers["verifier_samples_query_positions_from_channel"])
        self.assertTrue(markers["fri_verifier_draws_queries_from_channel"])

    def test_repo_wrapper_still_only_sees_extended_aux_after_prove_ex(self):
        markers = self.payload["source_audit"]["repo_markers"]
        self.assertTrue(markers["sampler_calls_full_extended_proof"])
        self.assertTrue(markers["sampler_reads_extended_aux_query_locations"])
        self.assertTrue(markers["prove_single_extended_delegates_to_stwo_prove_ex"])
        self.assertTrue(markers["sampler_boundary_names_extended_aux_only"])
        self.assertIn(
            "ExtendedStarkProof aux",
            self.payload["source_audit"]["current_stage_boundary"],
        )

    def test_external_policy_markers_are_absent_in_current_sources(self):
        absent = self.payload["source_audit"]["external_policy_markers_absent"]
        self.assertEqual(
            set(absent),
            {
                "prove_ex_with_query_policy",
                "decommit_with_query_policy",
                "external_query_policy",
                "query_policy_commitment",
            },
        )
        self.assertTrue(all(absent.values()))

    def test_hook_designs_are_bounded_and_do_not_claim_current_probe_b_control(self):
        preview = self.design("query_preview_split")
        policy = self.design("policy_commitment_mix")
        rejected = self.design("external_query_override")
        self.assertTrue(preview["requires_stwo_prover_patch"])
        self.assertFalse(preview["requires_stwo_verifier_patch"])
        self.assertFalse(preview["allows_external_query_choice"])
        self.assertTrue(policy["requires_stwo_verifier_patch"])
        self.assertTrue(policy["preserves_fiat_shamir_if_transcript_bound"])
        self.assertTrue(rejected["allows_external_query_choice"])
        self.assertFalse(rejected["preserves_fiat_shamir_if_transcript_bound"])
        for design in self.payload["hook_designs"]:
            self.assertFalse(design["can_claim_current_probe_b_control"])
            self.assertEqual(design["proof_size_delta_typed_bytes"], 0)

    def test_current_metric_anchor_preserves_recent_numbers_without_promoting_them(self):
        anchor = self.payload["current_metric_anchor"]
        self.assertEqual(anchor["selected_row"], "adjacent_label_probe_b")
        self.assertEqual(anchor["typed_bytes"], 37_532)
        self.assertEqual(anchor["path_opening_bytes"], 16_560)
        self.assertEqual(anchor["query_span"], 16_618)
        self.assertEqual(anchor["min_pairwise_query_gap"], 5_969)
        self.assertEqual(anchor["matched_two_proof_frontier_typed_bytes"], 47_188)
        self.assertEqual(anchor["saving_vs_two_proof_frontier_typed_bytes"], 9_656)

    def test_current_metric_anchor_is_derived_from_predecommit_tsv(self):
        self.assertEqual(
            self.payload["current_metric_anchor"],
            self.gate.predecommit_metric_anchor(),
        )

    def test_forbidden_policy_inputs_remain_forbidden(self):
        forbidden = self.payload["forbidden_policy_inputs"]
        self.assertTrue(forbidden["final_envelope_json"])
        self.assertTrue(forbidden["final_proof_bytes"])
        self.assertTrue(forbidden["grouped_accounting"])
        self.assertTrue(forbidden["record_streams"])
        self.assertTrue(forbidden["final_path_opening_bytes"])
        self.assertTrue(forbidden["post_decommitment_aux_as_selector"])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_read_external_file_rejects_symlink(self):
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmp:
            tmp_path = pathlib.Path(tmp)
            target = tmp_path / "target.rs"
            target.write_text("fn main() {}\n")
            link = tmp_path / "link.rs"
            os.symlink(target, link)
            with self.assertRaisesRegex(
                self.gate.BoundedStwoQueryPolicyHookGateError,
                "must not traverse symlink",
            ):
                self.gate.read_external_file(link, "symlink source", 1024)

    def test_stwo_source_root_expands_env_vars_and_user(self):
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmp:
            tmp_path = pathlib.Path(tmp)
            source_root = tmp_path / "stwo-source"
            for rel in self.gate.STWO_FILES.values():
                path = source_root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("// fixture\n", encoding="utf-8")
            old_env = os.environ.get("STWO_SOURCE_ROOT")
            old_fixture_root = os.environ.get("PTVM_STWO_FIXTURE_ROOT")
            old_home = os.environ.get("HOME")
            try:
                os.environ["PTVM_STWO_FIXTURE_ROOT"] = str(tmp_path)
                os.environ["STWO_SOURCE_ROOT"] = "$PTVM_STWO_FIXTURE_ROOT/stwo-source"
                self.assertEqual(self.gate.find_stwo_source_root(), source_root)
                os.environ["HOME"] = str(tmp_path)
                os.environ["STWO_SOURCE_ROOT"] = "~/stwo-source"
                self.assertEqual(self.gate.find_stwo_source_root(), source_root)
            finally:
                if old_env is None:
                    os.environ.pop("STWO_SOURCE_ROOT", None)
                else:
                    os.environ["STWO_SOURCE_ROOT"] = old_env
                if old_fixture_root is None:
                    os.environ.pop("PTVM_STWO_FIXTURE_ROOT", None)
                else:
                    os.environ["PTVM_STWO_FIXTURE_ROOT"] = old_fixture_root
                if old_home is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = old_home

    def test_all_mutations_rejected(self):
        mutation = self.payload["mutation_result"]
        self.assertTrue(mutation["all_mutations_rejected"])
        self.assertEqual(mutation["mutations_rejected"], len(self.gate.MUTATION_NAMES))
        self.assertEqual(mutation["mutation_names"], list(self.gate.MUTATION_NAMES))

    def test_source_artifact_lookup_rejects_missing_id(self):
        with self.assertRaisesRegex(
            self.gate.BoundedStwoQueryPolicyHookGateError,
            "source artifact missing",
        ):
            self.gate.find_source_artifact(self.payload, "missing-artifact-id")

    def test_validate_mutation_result_rejects_malformed_case(self):
        bad_result = copy.deepcopy(self.payload["mutation_result"])
        bad_result["cases"][0] = "not-a-mutation-case"
        with self.assertRaisesRegex(
            self.gate.BoundedStwoQueryPolicyHookGateError,
            "mutation case schema drift",
        ):
            self.gate.validate_mutation_result(bad_result)

    def test_pinned_unittest_count_matches_loaded_suite(self):
        count = unittest.TestLoader().loadTestsFromTestCase(type(self)).countTestCases()
        self.assertEqual(count, self.gate.EXPECTED_UNITTEST_STEP_COUNT)
        self.assertEqual(count, self.payload["reproducibility_metadata"]["unittest_step_count"])

    def test_committed_evidence_contains_integrity_fields(self):
        evidence = json.loads(self.gate.JSON_OUT.read_text())
        self.assertEqual(evidence["payload_commitment"], self.payload["payload_commitment"])
        self.assertEqual(evidence["mutation_result"], self.payload["mutation_result"])
        self.gate.validate_payload(evidence)

    def test_rejects_current_control_overclaim(self):
        item = self.gate.build_payload_without_mutations()
        item["bounded_hook_assessment"]["repo_local_hook_available"] = True
        with self.assertRaisesRegex(
            self.gate.BoundedStwoQueryPolicyHookGateError,
            "base payload drift",
        ):
            self.gate.validate_base_payload(item)

    def test_payload_commitment_and_tsv_are_stable(self):
        payload_a = self.gate.build_payload()
        payload_b = self.gate.build_payload()
        self.assertEqual(payload_a["payload_commitment"], self.gate.payload_commitment(payload_a))
        self.assertEqual(payload_a["payload_commitment"], payload_b["payload_commitment"])
        tsv = self.gate.render_tsv(payload_a)
        self.assertEqual(tsv, self.gate.render_tsv(payload_b))
        self.assertIn("query_preview_split\t", tsv)
        self.assertIn("external_query_override\tREJECTED_UNSOUND", tsv)

    def test_writes_paired_json_and_tsv_outputs(self):
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmp:
            tmp_path = pathlib.Path(tmp)
            json_path = tmp_path / "out.json"
            tsv_path = tmp_path / "out.tsv"
            self.gate.write_outputs(json_path, tsv_path, self.payload)
            loaded = json.loads(json_path.read_text())
            self.assertEqual(loaded["payload_commitment"], self.payload["payload_commitment"])
            lines = tsv_path.read_text().splitlines()
            self.assertEqual(lines[0], "\t".join(self.gate.TSV_COLUMNS))
            self.assertEqual(len(lines), 1 + len(self.payload["hook_designs"]))


if __name__ == "__main__":
    unittest.main()
