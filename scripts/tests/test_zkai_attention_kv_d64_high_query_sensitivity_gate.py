import copy
import unittest

from scripts import zkai_attention_kv_d64_high_query_sensitivity_gate as gate


class D64HighQuerySensitivityGateTests(unittest.TestCase):
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
        with self.assertRaises(gate.D64HighQuerySensitivityGateError) as ctx:
            gate.validate_payload(payload, allow_missing_mutation_summary=True)
        self.assertIn(message, str(ctx.exception))

    def row(self, query_count):
        for row in self.payload["rows"]:
            if row["fri_query_count"] == query_count:
                return row
        self.fail(f"missing query row {query_count}")

    def test_records_d64_high_query_sensitivity_without_promoting_security_claim(self):
        gate.validate_payload(self.payload)
        self.assertEqual(self.payload["schema"], gate.SCHEMA)
        self.assertEqual(self.payload["issue"], 769)
        self.assertEqual(self.payload["decision"], gate.DECISION)
        self.assertEqual(self.payload["surface"], gate.SURFACE)
        self.assertIn("not production-security parameter evidence", self.payload["non_claims"])
        self.assertIn("not a change to the publication/default q3 backend configuration", self.payload["non_claims"])

    def test_rejects_non_object_payload(self):
        self.assert_rejects([{"schema": gate.SCHEMA}], "payload must be a JSON object")

    def test_q3_q6_q12_rows_keep_fused_smaller_than_split(self):
        q3 = self.row(3)
        self.assertEqual(q3["source_plus_sidecar_raw_proof_bytes"], 315_785)
        self.assertEqual(q3["fused_proof_size_bytes"], 276_503)
        self.assertEqual(q3["fused_saves_vs_source_plus_sidecar_bytes"], 39_282)
        self.assertEqual(q3["fused_to_split_ratio"], 0.875605)

        q6 = self.row(6)
        self.assertEqual(q6["source_plus_sidecar_raw_proof_bytes"], 453_733)
        self.assertEqual(q6["fused_proof_size_bytes"], 390_437)
        self.assertEqual(q6["fused_saves_vs_source_plus_sidecar_bytes"], 63_296)
        self.assertEqual(q6["fused_to_split_ratio"], 0.860499)

        q12 = self.row(12)
        self.assertEqual(q12["source_plus_sidecar_raw_proof_bytes"], 727_747)
        self.assertEqual(q12["fused_proof_size_bytes"], 612_237)
        self.assertEqual(q12["fused_saves_vs_source_plus_sidecar_bytes"], 115_510)
        self.assertEqual(q12["fused_to_split_ratio"], 0.841277)

    def test_growth_metrics_and_patch_scope_are_explicit(self):
        aggregate = self.payload["aggregate"]
        self.assertEqual(aggregate["query_counts_checked"], [3, 6, 12])
        self.assertEqual(aggregate["q12_saving_bytes"], 115_510)
        self.assertEqual(aggregate["q12_saving_growth_vs_q3"], 2.940533)
        self.assertEqual(aggregate["q12_fused_growth_vs_q3"], 2.214215)
        self.assertEqual(aggregate["q12_split_growth_vs_q3"], 2.304565)
        self.assertFalse(aggregate["q12_requires_resource_limit_retune"])

        patches = self.payload["query_count_patches"]
        self.assertEqual(patches["q6"][0]["to"], "FriConfig::new(0, 1, 6, 1)")
        self.assertEqual(patches["q12"][0]["to"], "FriConfig::new(0, 1, 12, 1)")
        self.assertEqual(self.payload["build_environment"]["rustflags"], "-C debuginfo=0")

    def test_artifacts_are_hash_and_config_pinned(self):
        q12 = self.row(12)
        self.assertEqual(
            q12["artifacts"]["fused"]["sha256"],
            "d8b6cc7d993011948f1e532e9c11db6b8ebb52f425287c8ddb92008673f41a2e",
        )
        self.assertEqual(q12["proof_config"]["fri_config"]["n_queries"], 12)
        self.assertEqual(q12["proof_config"]["fri_config"]["log_blowup_factor"], 1)
        self.assertEqual(q12["proof_config"]["pow_bits"], 10)

    def test_declared_mutations_reject(self):
        self.assertEqual([item["name"] for item in self.payload["mutation_cases"]], list(gate.MUTATION_NAMES))
        self.assertEqual(self.payload["mutations_checked"], len(gate.MUTATION_NAMES))
        self.assertEqual(self.payload["mutations_rejected"], len(gate.MUTATION_NAMES))
        self.assertTrue(self.payload["all_mutations_rejected"])
        self.assertTrue(all(item["rejected"] is True for item in self.payload["mutation_cases"]))

    def test_rejects_overclaims_and_metric_drift(self):
        payload = self.strip_mutation_summary(self.payload)
        payload["decision"] = "GO_PRODUCTION_SECURITY_HIGH_QUERY_RESULT"
        self.assert_rejects(payload, "decision drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["claim_boundary"] = "HEADLINE_D64_D128_HIGH_QUERY_PROOF_SIZE_WIN"
        self.assert_rejects(payload, "claim boundary drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["query_count_patches"]["q12"][0]["to"] = "FriConfig::new(0, 1, 16, 1)"
        payload["payload_commitment"] = gate.payload_commitment(payload)
        self.assert_rejects(payload, "query-count patch drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["rows"][2]["proof_config"]["fri_config"]["n_queries"] = 11
        self.assert_rejects(payload, "q12 proof config drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["rows"][2]["artifacts"]["fused"]["path"] = payload["rows"][0]["artifacts"]["fused"]["path"]
        payload["payload_commitment"] = gate.payload_commitment(payload)
        self.assert_rejects(payload, "q12 artifact block drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["payload_commitment"] = "blake2b-256:" + "00" * 32
        self.assert_rejects(payload, "payload commitment drift")


if __name__ == "__main__":
    unittest.main()
