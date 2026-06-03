import copy
import json
import os
import pathlib
import tempfile
import unittest

from scripts import zkai_stwo_ai_two_head_seq32_layout_schedule_sweep_gate as gate


class LayoutScheduleSweepGateTests(unittest.TestCase):
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
        with self.assertRaises(gate.LayoutScheduleSweepGateError) as ctx:
            gate.validate_payload(payload, allow_missing_mutation_summary=True)
        self.assertIn(message, str(ctx.exception))

    def row(self, schedule_id):
        return gate.find_row(self.payload["variant_rows"], schedule_id)

    def test_records_chunk4_as_small_layout_win_without_fork_promotion(self):
        payload = self.payload
        gate.validate_payload(payload)

        self.assertEqual(payload["schema"], gate.SCHEMA)
        self.assertEqual(payload["issue"], 757)
        self.assertEqual(payload["source_surface_issue"], 537)
        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertEqual(payload["fork_status"], gate.FORK_STATUS)
        self.assertEqual(payload["promotion_status"], gate.PROMOTION_STATUS)
        self.assertIn("not a Stwo fork", payload["non_claims"])
        self.assertIn(gate.NATIVE_VERIFY_COMMAND, payload["validation_commands"])

        aggregate = payload["aggregate"]
        self.assertEqual(aggregate["baseline_proof_size_bytes"], 66327)
        self.assertEqual(aggregate["variants_checked"], 7)
        self.assertEqual(aggregate["best_schedule_id"], "chunk4")
        self.assertEqual(aggregate["best_proof_size_bytes"], 65998)
        self.assertEqual(aggregate["best_saves_vs_baseline_bytes"], 329)
        self.assertEqual(aggregate["best_opening_delta_vs_baseline_bytes"], -395)
        self.assertEqual(aggregate["best_fri_delta_vs_baseline_bytes"], -353)
        self.assertEqual(aggregate["best_decommitment_delta_vs_baseline_bytes"], -42)
        self.assertEqual(aggregate["best_query_delta_vs_baseline_bytes"], 80)
        self.assertEqual(aggregate["worst_schedule_id"], "chunk8")
        self.assertEqual(aggregate["worst_proof_delta_vs_baseline_bytes"], 4050)
        self.assertEqual(payload["baseline_artifact"]["proof_backend"], "stwo")

    def test_variant_rows_bind_same_workload_and_statement_commitments(self):
        chunk4 = self.row("chunk4")
        self.assertEqual(chunk4["proof_backend"], "stwo")
        self.assertEqual(chunk4["proof_size_bytes"], 65998)
        self.assertEqual(chunk4["saves_vs_baseline_bytes"], 329)
        self.assertEqual(chunk4["proof_delta_vs_baseline_bytes"], -329)
        self.assertEqual(chunk4["bucket_delta_vs_baseline_bytes"]["opening_bucket_bytes"], -395)
        self.assertEqual(chunk4["section_delta_vs_baseline_bytes"]["fri_proof"], -353)
        self.assertEqual(chunk4["section_delta_vs_baseline_bytes"]["decommitments"], -42)
        self.assertEqual(chunk4["bucket_delta_vs_baseline_bytes"]["query_bucket_bytes"], 80)
        self.assertEqual(
            chunk4["statement_commitment"],
            "blake2b-256:b1d5550c3bb5401b2198db8e8693e04a1f34e949d9b2502cb5ee5bbe26321ab7",
        )
        self.assertEqual(chunk4["same_workload"]["lookup_claims"], 1184)
        self.assertEqual(chunk4["same_workload"]["trace_rows"], 2048)

        head_blocked = self.row("head_blocked")
        self.assertEqual(head_blocked["proof_delta_vs_baseline_bytes"], 2544)
        self.assertGreater(head_blocked["bucket_delta_vs_baseline_bytes"]["opening_bucket_bytes"], 0)

    def test_declared_mutations_reject(self):
        self.assertEqual([item["name"] for item in self.payload["mutation_cases"]], list(gate.EXPECTED_MUTATION_NAMES))
        self.assertEqual(self.payload["mutations_checked"], gate.EXPECTED_MUTATION_COUNT)
        self.assertEqual(self.payload["mutations_rejected"], gate.EXPECTED_MUTATION_COUNT)
        self.assertTrue(self.payload["all_mutations_rejected"])
        self.assertTrue(all(item["rejected"] is True for item in self.payload["mutation_cases"]))

    def test_rejects_overclaims_and_metric_smuggling(self):
        payload = self.strip_mutation_summary(self.payload)
        payload["fork_status"] = "GO_FORK_STWO_NOW"
        self.assert_rejects(payload, "fork_status drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["promotion_status"] = "GO_PROMOTE_TO_D64_NOW"
        self.assert_rejects(payload, "promotion_status drift")

        payload = self.strip_mutation_summary(self.payload)
        gate.find_row(payload["variant_rows"], "chunk4")["proof_size_bytes"] = 1
        self.assert_rejects(payload, "variant row drift")

        payload = self.strip_mutation_summary(self.payload)
        gate.find_row(payload["variant_rows"], "chunk4")["proof_backend"] = "forked-stwo"
        self.assert_rejects(payload, "proof_backend drift")

        payload = self.strip_mutation_summary(self.payload)
        gate.find_row(payload["variant_rows"], "chunk4")["statement_commitment"] = "blake2b-256:" + "aa" * 32
        self.assert_rejects(payload, "variant row drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["validation_commands"].remove(gate.NATIVE_VERIFY_COMMAND)
        self.assert_rejects(payload, "validation_commands drift")

        payload = self.strip_mutation_summary(self.payload)
        payload["non_claims"].remove("not a Stwo fork")
        self.assert_rejects(payload, "non_claims drift")

    def test_tsv_and_markdown_summarize_result(self):
        tsv = gate.to_tsv(self.payload)
        self.assertIn("chunk4", tsv)
        self.assertIn("65998", tsv)
        self.assertIn("four-row deterministic source chunks", tsv)

        md = gate.to_markdown(self.payload)
        self.assertIn("Stwo-AI Two-Head Seq32 Layout Schedule Sweep", md)
        self.assertIn("`chunk4` is the first checked route-layout win", md)
        self.assertIn("`329` bytes", md)
        self.assertIn("Proof backend: `stwo`", md)
        self.assertIn("not a Stwo fork", md)

    def test_checked_outputs_match_generator(self):
        self.assertEqual(
            json.dumps(self.payload, indent=2, sort_keys=True) + "\n",
            gate.JSON_OUT.read_text(encoding="utf-8"),
        )
        self.assertEqual(gate.to_tsv(self.payload, validated=True), gate.TSV_OUT.read_text(encoding="utf-8"))
        self.assertEqual(gate.to_markdown(self.payload, validated=True), gate.MD_OUT.read_text(encoding="utf-8"))

    def test_serializers_still_validate_untrusted_payloads(self):
        payload = self.strip_mutation_summary(self.payload)
        payload["decision"] = "GO_STWO_AI_FORK_BREAKTHROUGH"
        with self.assertRaisesRegex(gate.LayoutScheduleSweepGateError, "decision drift"):
            gate.to_tsv(payload)
        with self.assertRaisesRegex(gate.LayoutScheduleSweepGateError, "decision drift"):
            gate.to_markdown(payload)

    def test_relative_output_paths_resolve_from_repo_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous_cwd = pathlib.Path.cwd()
            try:
                os.chdir(tmp)
                evidence_path = gate.require_evidence_output_path(
                    pathlib.Path("docs/engineering/evidence/zkai-stwo-ai-two-head-seq32-layout-schedule-sweep-2026-06.json")
                )
                docs_path = gate.require_docs_output_path(
                    pathlib.Path("docs/engineering/zkai-stwo-ai-two-head-seq32-layout-schedule-sweep-2026-06-04.md")
                )
            finally:
                os.chdir(previous_cwd)
        self.assertEqual(evidence_path, gate.JSON_OUT.resolve())
        self.assertEqual(docs_path, gate.MD_OUT.resolve())

    def test_write_paths_are_constrained(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            with self.assertRaisesRegex(gate.LayoutScheduleSweepGateError, "evidence output path"):
                gate.write_outputs(self.payload, tmp_path / "out.json", gate.TSV_OUT, gate.MD_OUT)
            with self.assertRaisesRegex(gate.LayoutScheduleSweepGateError, "evidence output path"):
                gate.write_outputs(self.payload, gate.JSON_OUT, tmp_path / "out.tsv", gate.MD_OUT)
            with self.assertRaisesRegex(gate.LayoutScheduleSweepGateError, "markdown output path"):
                gate.write_outputs(self.payload, gate.JSON_OUT, gate.TSV_OUT, tmp_path / "out.md")

    def test_missing_artifact_uses_gate_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = pathlib.Path(tmp) / "missing.json"
            with self.assertRaisesRegex(gate.LayoutScheduleSweepGateError, "missing artifact: missing.json"):
                gate.sha256_file(missing)


if __name__ == "__main__":
    unittest.main()
