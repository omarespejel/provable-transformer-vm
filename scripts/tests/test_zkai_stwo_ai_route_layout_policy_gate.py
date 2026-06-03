import copy
import pathlib
import tempfile
import unittest

from scripts import zkai_stwo_ai_route_layout_policy_gate as gate


class StwoAiRouteLayoutPolicyGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload_base = gate.build_payload()

    def setUp(self) -> None:
        self.payload = copy.deepcopy(self.payload_base)

    def strip_mutation_summary(self, payload):
        payload = copy.deepcopy(payload)
        for key in ("mutation_cases", "mutations_checked", "mutations_rejected", "all_mutations_rejected"):
            payload.pop(key, None)
        return payload

    def assert_rejects(self, payload, message):
        with self.assertRaises(gate.StwoAiRouteLayoutPolicyGateError) as ctx:
            gate.validate_payload(payload, allow_missing_mutation_summary=True)
        self.assertIn(message, str(ctx.exception))

    def row(self, profile_id):
        return gate.find_row(self.payload["policy_metric_rows"], profile_id)

    def test_records_route_layout_selector_without_fork_promotion(self):
        payload = self.payload
        gate.validate_payload(payload)

        self.assertEqual(payload["schema"], gate.SCHEMA)
        self.assertEqual(payload["issue"], 757)
        self.assertEqual(payload["source_issue"], 531)
        self.assertEqual(payload["route_matrix_issue"], 505)
        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertEqual(payload["fork_status"], gate.FORK_STATUS)
        self.assertEqual(payload["next_policy_status"], gate.NEXT_POLICY_STATUS)
        self.assertEqual(payload["prover_policy"], gate.PROVER_POLICY)
        self.assertEqual(payload["profile_ids"], list(gate.EXPECTED_PROFILE_IDS))
        self.assertIn("not a Stwo fork", payload["non_claims"])

        aggregate = payload["aggregate"]
        self.assertEqual(aggregate["profiles_checked"], 11)
        self.assertEqual(aggregate["total_fused_saves_vs_source_plus_sidecar_bytes"], 223958)
        self.assertEqual(aggregate["total_opening_bucket_savings_bytes"], 209155)
        self.assertEqual(aggregate["total_opening_savings_share"], 0.933903)
        self.assertEqual(aggregate["largest_savings_profile_id"], "d64_four_head_seq64")
        self.assertEqual(aggregate["lowest_cost_sequence_profile_id"], "d8_two_head_seq32")

        selector = payload["selector"]
        self.assertEqual(selector["headline_pressure_anchor_profile_id"], "d64_four_head_seq64")
        self.assertEqual(selector["headline_pressure_anchor_savings_bytes"], 39282)
        self.assertEqual(selector["fast_sequence_target_profile_id"], "d8_two_head_seq32")
        self.assertEqual(selector["fast_sequence_target_fused_proof_size_bytes"], 66327)
        self.assertEqual(selector["fast_sequence_target_savings_bytes"], 31685)
        self.assertEqual(selector["fast_sequence_target_opening_savings_share"], 0.953227)
        self.assertEqual(selector["fast_sequence_target_sidecar_absorption_share"], 0.926899)
        self.assertEqual(selector["absorption_sanity_profile_id"], "d16_two_head_seq16")
        self.assertEqual(selector["head_axis_fallback_profile_id"], "d8_four_head_seq8")

    def test_policy_rows_bind_mechanism_to_fast_target_and_d64_anchor(self):
        fast = self.row("d8_two_head_seq32")
        self.assertEqual(fast["policy_role"], "fast_sequence_iteration_target")
        self.assertEqual(fast["steps_per_head"], 32)
        self.assertEqual(fast["lookup_claims"], 1184)
        self.assertEqual(fast["trace_rows"], 2048)
        self.assertEqual(fast["fused_proof_size_bytes"], 66327)
        self.assertEqual(fast["source_plus_sidecar_raw_proof_bytes"], 98012)
        self.assertEqual(fast["fused_saves_vs_source_plus_sidecar_bytes"], 31685)
        self.assertEqual(fast["opening_bucket_savings_bytes"], 30203)
        self.assertEqual(fast["query_bucket_savings_bytes"], 846)
        self.assertEqual(fast["fused_opening_minus_source_opening_bytes"], 2382)

        d64 = self.row("d64_four_head_seq64")
        self.assertEqual(d64["policy_role"], "headline_pressure_anchor")
        self.assertEqual(d64["key_width"], 64)
        self.assertEqual(d64["head_count"], 4)
        self.assertEqual(d64["steps_per_head"], 64)
        self.assertEqual(d64["lookup_claims"], 8832)
        self.assertEqual(d64["trace_rows"], 16384)
        self.assertEqual(d64["fused_proof_size_bytes"], 276503)
        self.assertEqual(d64["source_plus_sidecar_raw_proof_bytes"], 315785)
        self.assertEqual(d64["fused_saves_vs_source_plus_sidecar_bytes"], 39282)
        self.assertEqual(d64["opening_bucket_savings_bytes"], 37827)
        self.assertEqual(d64["opening_savings_share"], 0.96296)
        self.assertEqual(d64["query_bucket_savings_bytes"], 850)

        fallback = self.row("d8_four_head_seq8")
        self.assertEqual(fallback["policy_role"], "head_axis_fallback")
        self.assertEqual(fallback["fused_opening_minus_source_opening_bytes"], -392)
        self.assertEqual(fallback["sidecar_opening_absorption_share"], 1.020258)

    def test_policy_plan_keeps_safe_next_action(self):
        plan = self.payload["policy_plan"]
        self.assertEqual(plan["immediate_target"], "d8_two_head_seq32")
        self.assertEqual(plan["pressure_anchor"], "d64_four_head_seq64")
        self.assertEqual(plan["promote_after_fast_target_go"], "d64_four_head_seq64")
        self.assertIn("verifier-bound deterministic route-layout policy", plan["go_gate"])
        self.assertIn("post-query selection", plan["no_go_gate"])
        self.assertIn("public-API wall", plan["fork_trigger"])
        self.assertIn("choosing labels after transcript queries are sampled", plan["unsafe_actions_rejected"])

    def test_declared_mutations_reject(self):
        self.assertEqual([item["name"] for item in self.payload["mutation_cases"]], list(gate.EXPECTED_MUTATION_NAMES))
        self.assertEqual(self.payload["mutations_checked"], gate.EXPECTED_MUTATION_COUNT)
        self.assertEqual(self.payload["mutations_rejected"], gate.EXPECTED_MUTATION_COUNT)
        self.assertTrue(self.payload["all_mutations_rejected"])
        self.assertTrue(all(item["rejected"] is True for item in self.payload["mutation_cases"]))

    def test_rejects_overclaims_and_metric_smuggling(self):
        payload = self.strip_mutation_summary(self.payload)
        payload["decision"] = "GO_NEW_PROOF_SIZE_FRONTIER"
        self.assert_rejects(payload, "decision drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["fork_status"] = "GO_FORK_STWO_NOW"
        self.assert_rejects(payload, "fork_status drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["security_policy"] = "choose_layout_after_query_draw"
        self.assert_rejects(payload, "security_policy drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["source_artifacts"]["section_delta_sha256"] = "00" * 32
        self.assert_rejects(payload, "source artifact digest drift")

        payload = self.strip_mutation_summary(self.payload)
        gate.find_row(payload["policy_metric_rows"], "d8_two_head_seq32")["query_bucket_savings_bytes"] += 1
        self.assert_rejects(payload, "policy metric row drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["selector"]["fast_sequence_target_profile_id"] = "d64_four_head_seq64"
        self.assert_rejects(payload, "selector drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["policy_plan"]["unsafe_actions_rejected"].pop(0)
        self.assert_rejects(payload, "policy plan drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["non_claims"].remove("not a Stwo fork")
        self.assert_rejects(payload, "non_claims drift")

    def test_tsv_and_markdown_summarize_selector(self):
        tsv = gate.to_tsv(self.payload)
        self.assertIn("d8_two_head_seq32", tsv)
        self.assertIn("fast_sequence_iteration_target", tsv)
        self.assertIn("d64_four_head_seq64", tsv)
        self.assertIn("headline_pressure_anchor", tsv)

        md = gate.to_markdown(self.payload)
        self.assertIn("Stwo-AI Route-Layout Policy Selector", md)
        self.assertIn("The next Stwo-AI step is not a fork.", md)
        self.assertIn("`d8_two_head_seq32`", md)
        self.assertIn("`d64_four_head_seq64`", md)

    def test_write_paths_are_constrained(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            with self.assertRaisesRegex(gate.StwoAiRouteLayoutPolicyGateError, "evidence output path"):
                gate.write_outputs(self.payload, tmp_path / "out.json", gate.TSV_OUT, gate.MD_OUT)
            with self.assertRaisesRegex(gate.StwoAiRouteLayoutPolicyGateError, "evidence output path"):
                gate.write_outputs(self.payload, gate.JSON_OUT, tmp_path / "out.tsv", gate.MD_OUT)
            with self.assertRaisesRegex(gate.StwoAiRouteLayoutPolicyGateError, "markdown output path"):
                gate.write_outputs(self.payload, gate.JSON_OUT, gate.TSV_OUT, tmp_path / "out.md")


if __name__ == "__main__":
    unittest.main()
