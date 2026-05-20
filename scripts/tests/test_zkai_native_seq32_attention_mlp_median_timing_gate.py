import copy
import unittest

from scripts import zkai_native_seq32_attention_mlp_median_timing_gate as gate


class Seq32AttentionMlpMedianTimingGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = gate.build_payload()

    def test_payload_validates(self):
        gate.validate_payload(copy.deepcopy(self.payload))
        self.assertEqual(self.payload["schema"], gate.SCHEMA)
        self.assertEqual(self.payload["decision"], gate.DECISION)
        self.assertEqual(self.payload["result"], gate.RESULT)

    def test_target_is_statement_only_frontier(self):
        target = self.payload["target"]
        self.assertEqual(target["profile_id"], "statement_only_probe_b")
        self.assertEqual(target["typed_bytes"], 39_516)
        self.assertEqual(target["json_proof_bytes"], 113_388)
        self.assertEqual(target["matched_two_proof_frontier_typed_bytes"], 47_188)

    def test_timing_rows_are_median_of_five(self):
        rows = {row["metric"]: row for row in self.payload["timing_rows"]}
        self.assertEqual(tuple(rows), gate.EXPECTED_TIMING_METRICS)
        for row in rows.values():
            self.assertEqual(len(row["runs_us"]), 5)
            self.assertGreater(row["median_us"], 0)
            self.assertEqual(row["median_us"], sorted(row["runs_us"])[2])
            self.assertEqual(row["min_us"], min(row["runs_us"]))
            self.assertEqual(row["max_us"], max(row["runs_us"]))

    def test_non_claims_block_public_benchmark_framing(self):
        for non_claim in gate.NON_CLAIMS:
            self.assertIn(non_claim, self.payload["non_claims"])
        self.assertIn("NO_EXTERNAL_SYSTEM_COMPARISON", self.payload["claim_boundary"])
        self.assertIn("NO_PUBLIC_BENCHMARK", self.payload["claim_boundary"])

    def test_source_artifacts_are_pinned(self):
        sources = {source["id"]: source for source in self.payload["source_artifacts"]}
        self.assertIn("raw_timing_json", sources)
        self.assertIn("statement_only_gate_json", sources)
        self.assertIn("timing_rust_source", sources)
        self.assertIn("native_proof_rust_source", sources)
        for source in sources.values():
            self.assertRegex(source["sha256"], r"^[0-9a-f]{64}$")
            self.assertGreater(source["bytes"], 0)

    def test_mutation_inventory_is_rejected(self):
        result = self.payload["mutation_result"]
        self.assertTrue(result["all_rejected"])
        self.assertEqual(result["rejected_count"], len(gate.mutation_inventory(self.payload)))
        self.assertIn("claim_boundary_public_benchmark", result["rejected_mutations"])
        self.assertIn("timing_policy_relabeling", result["rejected_mutations"])
        self.assertIn("source_digest_relabeling", result["rejected_mutations"])

    def test_missing_public_benchmark_non_claim_rejected(self):
        candidate = copy.deepcopy(self.payload)
        candidate["non_claims"].remove("not a public benchmark")
        candidate["payload_commitment"] = gate.payload_commitment(candidate)
        with self.assertRaises(gate.Seq32TimingGateError):
            gate.validate_payload(candidate, check_mutations=False)

    def test_host_metadata_privacy_boundary_rejected(self):
        candidate = copy.deepcopy(self.payload)
        candidate["host_metadata_policy"]["excluded"] = []
        candidate["payload_commitment"] = gate.payload_commitment(candidate)
        with self.assertRaises(gate.Seq32TimingGateError):
            gate.validate_payload(candidate, check_mutations=False)


if __name__ == "__main__":
    unittest.main()
