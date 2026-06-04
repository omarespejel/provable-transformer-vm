import copy
import json
import pathlib
import tempfile
import unittest

from scripts import zkai_stwo_ai_d64_four_head_seq64_chunk4_policy_gate as gate


class D64Chunk4PolicyGateTests(unittest.TestCase):
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
        with self.assertRaises(gate.D64Chunk4PolicyGateError) as ctx:
            gate.validate_payload(payload, allow_missing_mutation_summary=True)
        self.assertIn(message, str(ctx.exception))

    def test_records_d64_chunk4_policy_win_without_fork_promotion(self):
        payload = self.payload
        gate.validate_payload(payload)
        self.assertEqual(payload["schema"], gate.SCHEMA)
        self.assertEqual(payload["issue"], 757)
        self.assertEqual(payload["source_surface_issue"], 715)
        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertEqual(payload["fork_status"], gate.FORK_STATUS)
        self.assertIn("not a Stwo fork", payload["non_claims"])
        self.assertIn(gate.NATIVE_VERIFY_COMMAND, payload["validation_commands"])

        result = payload["result"]
        self.assertEqual(result["layout_policy"], "chunk4")
        self.assertEqual(result["baseline_proof_size_bytes"], 276503)
        self.assertEqual(result["chunk4_proof_size_bytes"], 274692)
        self.assertEqual(result["saving_vs_baseline_bytes"], 1811)
        self.assertEqual(result["source_plus_sidecar_raw_proof_bytes"], 315785)
        self.assertEqual(result["saving_vs_split_bytes"], 41093)
        self.assertEqual(result["chunk4_vs_baseline_ratio"], "0.993450")
        self.assertEqual(result["chunk4_vs_split_ratio"], "0.869870")
        self.assertEqual(result["bucket_delta_vs_baseline_bytes"]["opening_bucket_bytes"], -1866)
        self.assertEqual(result["section_delta_vs_baseline_bytes"]["fri_proof"], -1374)
        self.assertEqual(result["section_delta_vs_baseline_bytes"]["decommitments"], -492)
        self.assertEqual(result["bucket_delta_vs_baseline_bytes"]["query_bucket_bytes"], 53)

    def test_source_input_is_policy_bound_and_chunked(self):
        source_input = gate.read_json(gate.CHUNK4_INPUT, gate.MAX_INPUT_BYTES, "chunk4 input")
        gate.validate_source_input(source_input)
        self.assertEqual(source_input["layout_policy"], "chunk4")
        self.assertEqual(source_input["statement_commitment"], gate.SOURCE_STATEMENT_COMMITMENT)
        self.assertEqual(
            [step["head_index"] for step in source_input["input_steps"][:16]],
            [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3],
        )
        self.assertEqual(
            [step["token_position"] for step in source_input["input_steps"][:16]],
            [2, 3, 4, 5] * 4,
        )

    def test_declared_mutations_reject(self):
        self.assertEqual([case["name"] for case in self.payload["mutation_cases"]], list(gate.EXPECTED_MUTATION_NAMES))
        self.assertEqual(self.payload["mutations_checked"], gate.EXPECTED_MUTATION_COUNT)
        self.assertEqual(self.payload["mutations_rejected"], gate.EXPECTED_MUTATION_COUNT)
        self.assertTrue(self.payload["all_mutations_rejected"])
        self.assertTrue(all(case["rejected"] is True for case in self.payload["mutation_cases"]))

    def test_rejects_overclaims_and_metric_smuggling(self):
        payload = self.strip_mutation_summary(self.payload)
        payload["fork_status"] = "GO_FORK_STWO_NOW"
        self.assert_rejects(payload, "fork_status drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["result"]["layout_policy"] = "choose_after_queries"
        self.assert_rejects(payload, "result row drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["result"]["chunk4_proof_size_bytes"] = 1
        self.assert_rejects(payload, "result row drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["validation_commands"].remove(gate.NATIVE_VERIFY_COMMAND)
        self.assert_rejects(payload, "validation_commands drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["non_claims"].remove("not a Stwo fork")
        self.assert_rejects(payload, "non_claims drift")

    def test_tsv_and_markdown_summarize_result(self):
        tsv = gate.to_tsv(self.payload)
        self.assertIn("d64_four_head_seq64", tsv)
        self.assertIn("274692", tsv)
        self.assertIn("41093", tsv)
        self.assertIn(gate.SOURCE_STATEMENT_COMMITMENT, tsv)

        md = gate.to_markdown(self.payload)
        self.assertIn("Stwo-AI D64 Chunk4 Layout Policy Gate", md)
        self.assertIn("`chunk4` is now a verifier-bound d64 route-layout policy", md)
        self.assertIn("`1811` bytes", md)
        self.assertIn("`41093` bytes", md)
        self.assertIn("not a Stwo fork", md)

    def test_checked_outputs_match_generator(self):
        self.assertEqual(json.dumps(self.payload, indent=2, sort_keys=True) + "\n", gate.JSON_OUT.read_text(encoding="utf-8"))
        self.assertEqual(gate.to_tsv(self.payload, validated=True), gate.TSV_OUT.read_text(encoding="utf-8"))
        self.assertEqual(gate.to_markdown(self.payload, validated=True), gate.MD_OUT.read_text(encoding="utf-8"))

    def test_serializers_validate_untrusted_payloads(self):
        payload = self.strip_mutation_summary(self.payload)
        payload["decision"] = "GO_STWO_AI_FORK_BREAKTHROUGH"
        with self.assertRaisesRegex(gate.D64Chunk4PolicyGateError, "decision drift"):
            gate.to_tsv(payload)
        with self.assertRaisesRegex(gate.D64Chunk4PolicyGateError, "decision drift"):
            gate.to_markdown(payload)

    def test_write_paths_are_constrained(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            with self.assertRaisesRegex(gate.D64Chunk4PolicyGateError, "evidence output path"):
                gate.write_outputs(self.payload, tmp_path / "out.json", gate.TSV_OUT, gate.MD_OUT)
            with self.assertRaisesRegex(gate.D64Chunk4PolicyGateError, "evidence output path"):
                gate.write_outputs(self.payload, gate.JSON_OUT, tmp_path / "out.tsv", gate.MD_OUT)
            with self.assertRaisesRegex(gate.D64Chunk4PolicyGateError, "markdown output path"):
                gate.write_outputs(self.payload, gate.JSON_OUT, gate.TSV_OUT, tmp_path / "out.md")


if __name__ == "__main__":
    unittest.main()
