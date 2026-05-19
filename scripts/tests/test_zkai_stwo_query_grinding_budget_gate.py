import copy
import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "scripts" / "zkai_stwo_query_grinding_budget_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location("stwo_query_grinding_budget_gate", GATE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StwoQueryGrindingBudgetGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()
        try:
            cls.payload = cls.gate.build_payload()
        except cls.gate.hook_gate.BoundedStwoQueryPolicyHookGateError as err:
            if "Stwo 2.2.0 source is not available" in str(err):
                raise unittest.SkipTest(str(err)) from err
            raise

    def policy(self, policy_id):
        return self.gate.policy_row(self.payload, policy_id)

    def test_payload_records_mechanism_go_not_frontier(self):
        self.assertEqual(
            self.payload["decision"],
            "NARROW_CLAIM_SMALL_VERIFIER_BOUND_RETRY_BUDGET_CAN_RECOVER_PROBE_B_INVENTORY",
        )
        self.assertEqual(self.payload["result"], "GO_MECHANISM_LEAD_NOT_PROOF_SIZE_FRONTIER")
        self.assertEqual(self.payload["issue"], self.gate.ISSUE_HINT)
        self.assertFalse(self.payload["budget_rule"]["absolute_soundness_claim"])

    def test_inventory_is_loaded_from_pinned_predecommit_tsv(self):
        inventory = self.payload["inventory"]
        self.assertEqual(inventory["row_count"], 9)
        self.assertEqual(inventory["source_path"], str(self.gate.INVENTORY_TSV.relative_to(self.gate.ROOT)))
        self.assertTrue(inventory["commitment"].startswith("blake2b-256:"))
        self.assertEqual(len(inventory["rows"]), 9)
        header = self.gate.INVENTORY_TSV.read_text(encoding="utf-8").splitlines()[0].split("\t")
        self.assertEqual(tuple(header), self.gate.REQUIRED_INVENTORY_COLUMNS)
        selected_ids = [row["variant_id"] for row in inventory["rows"] if row["selected_without_final_accounting"]]
        self.assertEqual(selected_ids, ["adjacent_label_probe_b"])
        self.assertTrue(
            all(row["policy_stage"] == self.gate.EXPECTED_POLICY_STAGE for row in inventory["rows"])
        )
        self.assertTrue(
            all(row["api_control_status"] == self.gate.EXPECTED_API_CONTROL_STATUS for row in inventory["rows"])
        )

    def test_baseline_and_champion_metrics_are_pinned(self):
        self.assertEqual(self.payload["baseline"]["variant_id"], "fixed_adjacent_layout")
        self.assertEqual(self.payload["baseline"]["final_typed_bytes"], 42_156)
        self.assertEqual(self.payload["champion"]["variant_id"], "adjacent_label_probe_b")
        self.assertEqual(self.payload["champion"]["final_typed_bytes"], 37_532)
        self.assertEqual(self.payload["champion"]["final_path_opening_bytes"], 16_560)

    def test_two_probe_budget_recovers_champion_with_one_bit_loss(self):
        row = self.policy("two_probe_budget_2")
        self.assertEqual(row["status"], "MECHANISM_GO_REQUIRES_VERIFIER_BOUND_ATTEMPT_DOMAIN")
        self.assertEqual(row["attempt_budget"], 2)
        self.assertEqual(row["security_loss_bits"], "1.000000")
        self.assertEqual(row["best_variant_id"], "adjacent_label_probe_b")
        self.assertEqual(row["best_typed_bytes"], 37_532)
        self.assertEqual(row["improvement_vs_fixed_typed_bytes"], 4_624)
        self.assertEqual(row["improvement_vs_champion_typed_bytes"], 0)
        self.assertTrue(row["requires_verifier_bound_attempt_domain"])
        self.assertFalse(row["claims_new_frontier"])

    def test_seed_only_budget_is_no_go(self):
        row = self.policy("seed_only_budget_6")
        self.assertEqual(row["status"], "NO_GO_SEED_ONLY_DOES_NOT_RECOVER_CHAMPION")
        self.assertEqual(row["attempt_budget"], 6)
        self.assertEqual(row["security_loss_bits"], "2.584963")
        self.assertEqual(row["best_variant_id"], "adjacent_seed_02")
        self.assertEqual(row["best_typed_bytes"], 40_268)
        self.assertEqual(row["improvement_vs_champion_typed_bytes"], -2_736)

    def test_all_inventory_budget_is_unneeded_extra_grinding(self):
        row = self.policy("all_inventory_budget_9")
        self.assertEqual(row["status"], "NO_GO_UNNEEDED_EXTRA_GRINDING")
        self.assertEqual(row["attempt_budget"], 9)
        self.assertEqual(row["security_loss_bits"], "3.169925")
        self.assertEqual(row["best_variant_id"], "adjacent_label_probe_b")
        self.assertEqual(row["improvement_vs_champion_typed_bytes"], 0)

    def test_unbounded_retry_is_rejected(self):
        row = self.policy("unbounded_abort_and_retry")
        self.assertEqual(row["status"], "REJECTED_UNBOUNDED_SECURITY_LOSS")
        self.assertIsNone(row["attempt_budget"])
        self.assertTrue(row["requires_verifier_bound_attempt_domain"])
        self.assertFalse(row["claims_new_frontier"])

    def test_budget_rule_records_relative_not_absolute_security(self):
        rule = self.payload["budget_rule"]
        self.assertEqual(rule["security_loss_bits_formula"], "log2(attempt_budget)")
        self.assertEqual(rule["paper_prototype_max_loss_bits"], "2.000000")
        self.assertTrue(rule["verifier_must_bind_attempt_domain"])
        self.assertTrue(rule["verifier_must_reject_attempts_outside_domain"])
        self.assertFalse(rule["absolute_soundness_claim"])

    def test_forbidden_policy_inputs_remain_forbidden(self):
        forbidden = self.payload["forbidden_policy_inputs"]
        self.assertTrue(forbidden["final_envelope_json"])
        self.assertTrue(forbidden["final_proof_bytes"])
        self.assertTrue(forbidden["post_decommitment_accounting"])
        self.assertTrue(forbidden["unbounded_retry_count"])
        self.assertTrue(forbidden["uncommitted_attempt_domain"])

    def test_loss_bits_helper_is_exact_for_budget_points(self):
        self.assertEqual(self.gate.loss_bits(1), "0.000000")
        self.assertEqual(self.gate.loss_bits(2), "1.000000")
        self.assertEqual(self.gate.loss_bits(4), "2.000000")
        self.assertEqual(self.gate.loss_bits(9), "3.169925")
        with self.assertRaisesRegex(self.gate.StwoQueryGrindingBudgetGateError, "positive"):
            self.gate.loss_bits(0)

    def test_find_variant_and_policy_helpers_reject_missing_values(self):
        with self.assertRaisesRegex(self.gate.StwoQueryGrindingBudgetGateError, "variant missing"):
            self.gate.find_variant(self.payload["inventory"]["rows"], "missing")
        with self.assertRaisesRegex(self.gate.StwoQueryGrindingBudgetGateError, "policy missing"):
            self.gate.policy_row(self.payload, "missing")

    def test_all_mutations_rejected(self):
        mutation = self.payload["mutation_result"]
        self.assertTrue(mutation["all_mutations_rejected"])
        self.assertEqual(mutation["mutations_rejected"], len(self.gate.MUTATION_NAMES))
        self.assertEqual(mutation["mutation_names"], list(self.gate.MUTATION_NAMES))

    def test_validate_mutation_result_rejects_malformed_case(self):
        bad_result = copy.deepcopy(self.payload["mutation_result"])
        bad_result["cases"][0] = "not-a-mutation-case"
        with self.assertRaisesRegex(
            self.gate.StwoQueryGrindingBudgetGateError,
            "mutation case schema drift",
        ):
            self.gate.validate_mutation_result(bad_result)

    def test_pinned_unittest_count_matches_loaded_suite(self):
        count = unittest.TestLoader().loadTestsFromTestCase(type(self)).countTestCases()
        self.assertEqual(count, self.gate.EXPECTED_UNITTEST_STEP_COUNT)
        self.assertEqual(count, self.payload["reproducibility_metadata"]["unittest_step_count"])

    def test_committed_evidence_contains_integrity_fields(self):
        evidence = json.loads(self.gate.JSON_OUT.read_text(encoding="utf-8"))
        self.assertEqual(evidence["payload_commitment"], self.payload["payload_commitment"])
        self.assertEqual(evidence["mutation_result"], self.payload["mutation_result"])
        self.gate.validate_payload(evidence)

    def test_payload_commitment_and_tsv_are_stable(self):
        payload_a = self.gate.build_payload()
        payload_b = self.gate.build_payload()
        self.assertEqual(payload_a["payload_commitment"], self.gate.payload_commitment(payload_a))
        self.assertEqual(payload_a["payload_commitment"], payload_b["payload_commitment"])
        tsv = self.gate.render_tsv(payload_a)
        self.assertEqual(tsv, self.gate.render_tsv(payload_b))
        self.assertIn("two_probe_budget_2\tMECHANISM_GO", tsv)
        self.assertIn("unbounded_abort_and_retry\tREJECTED_UNBOUNDED_SECURITY_LOSS", tsv)

    def test_writes_paired_json_and_tsv_outputs(self):
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmp:
            tmp_path = pathlib.Path(tmp)
            json_path = tmp_path / "out.json"
            tsv_path = tmp_path / "out.tsv"
            self.gate.write_outputs(json_path, tsv_path, self.payload)
            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["payload_commitment"], self.payload["payload_commitment"])
            lines = tsv_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], "\t".join(self.gate.TSV_COLUMNS))
            self.assertEqual(len(lines), 1 + len(self.payload["policy_rows"]))

    def test_payload_commitment_drift_rejects(self):
        item = copy.deepcopy(self.payload)
        item["payload_commitment"] = "blake2b-256:" + ("0" * 64)
        with self.assertRaisesRegex(
            self.gate.StwoQueryGrindingBudgetGateError,
            "payload commitment drift",
        ):
            self.gate.validate_payload(item)


if __name__ == "__main__":
    unittest.main()
