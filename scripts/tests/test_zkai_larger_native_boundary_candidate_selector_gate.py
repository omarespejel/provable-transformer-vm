import copy
import json
import pathlib
import tempfile
import unittest

from scripts import zkai_larger_native_boundary_candidate_selector_gate as gate


class LargerNativeBoundaryCandidateSelectorGateTests(unittest.TestCase):
    def payload(self):
        return gate.finalize_payload(gate.build_payload())

    def test_payload_selects_two_head_seq32(self):
        payload = self.payload()
        self.assertEqual(
            payload["decision"],
            "GO_SELECT_TWO_HEAD_SEQ32_LARGER_NATIVE_BOUNDARY_IMPLEMENTATION_CANDIDATE",
        )
        self.assertEqual(payload["summary"]["selected_candidate"], "two_head_seq32_fused_attention")
        self.assertEqual(payload["summary"]["selected_attention_typed_bytes"], 22_916)
        self.assertEqual(payload["summary"]["selected_lookup_claims"], 1_184)
        self.assertEqual(
            payload["summary"]["selected_matched_two_proof_frontier_typed_bytes"],
            45_492,
        )

    def test_d8_baseline_matches_current_frontier(self):
        payload = self.payload()
        d8 = payload["candidates"][0]
        self.assertEqual(d8["candidate_id"], "d8_fused_attention")
        self.assertEqual(d8["attention_typed_bytes"], 18_124)
        self.assertEqual(d8["lookup_claims"], 52)
        self.assertEqual(d8["matched_two_proof_frontier_typed_bytes"], 40_700)
        self.assertEqual(d8["typed_bytes_per_lookup_claim"], "348.538462")

    def test_selected_candidate_has_best_work_amortization_signal(self):
        payload = self.payload()
        selected = payload["candidates"][-1]
        self.assertEqual(selected["candidate_id"], "two_head_seq32_fused_attention")
        self.assertEqual(selected["typed_bytes_per_lookup_claim"], "19.354730")
        self.assertEqual(selected["fused_to_source_plus_sidecar_ratio"], "0.676723")
        self.assertEqual(selected["fused_saves_vs_source_plus_sidecar_json_bytes"], 31_685)
        self.assertEqual(
            payload["summary"]["selected_bytes_per_lookup_improvement_vs_d8"],
            "18.007922",
        )

    def test_candidate_order_is_pinned(self):
        payload = self.payload()
        self.assertEqual(
            [row["candidate_id"] for row in payload["candidates"]],
            list(gate.EXPECTED_CANDIDATES),
        )

    def test_source_artifacts_are_pinned_to_real_files(self):
        payload = self.payload()
        self.assertEqual(len(payload["source_artifacts"]), 6)
        for artifact in payload["source_artifacts"]:
            path = gate.ROOT / artifact["path"]
            raw = path.read_bytes()
            self.assertEqual(artifact["sha256"], gate.digest(raw))
            self.assertEqual(artifact["size_bytes"], len(raw))

    def test_non_claim_inventory_is_exact(self):
        payload = self.payload()
        self.assertEqual(tuple(payload["non_claims"]), gate.NON_CLAIMS)

    def test_validation_command_inventory_is_exact(self):
        payload = self.payload()
        self.assertEqual(tuple(payload["validation_commands"]), gate.VALIDATION_COMMANDS)

    def test_payload_commitment_is_stable(self):
        payload = self.payload()
        self.assertEqual(payload["payload_commitment"], gate.payload_commitment(payload))

    def test_tsv_contains_candidate_rows(self):
        payload = self.payload()
        text = gate.tsv_bytes(payload).decode("utf-8")
        lines = text.strip().splitlines()
        self.assertEqual(len(lines), 6)
        self.assertIn("candidate_id\tstatus\tattention_typed_bytes", lines[0])
        self.assertIn("two_head_seq32_fused_attention\tATTACK_NEXT_LARGER_NATIVE_BOUNDARY", text)

    def test_all_mutations_reject(self):
        payload = gate.build_payload()
        results = gate.run_mutations(payload)
        self.assertEqual([item["name"] for item in results], list(gate.MUTATION_NAMES))
        self.assertTrue(all(item["rejected"] for item in results))

    def test_rejects_selected_candidate_drift(self):
        payload = self.payload()
        payload["summary"]["selected_candidate"] = "d16_fused_attention"
        gate.refresh_payload_commitment(payload)
        with self.assertRaisesRegex(gate.LargerNativeBoundaryCandidateSelectorError, "summary drift"):
            gate.validate_payload(payload)

    def test_rejects_nanozk_overclaim(self):
        payload = self.payload()
        payload["claim_boundary"] += "_NANOZK_WIN"
        gate.refresh_payload_commitment(payload)
        with self.assertRaisesRegex(gate.LargerNativeBoundaryCandidateSelectorError, "claim_boundary drift"):
            gate.validate_payload(payload)

    def test_rejects_non_claim_addition(self):
        payload = self.payload()
        payload["non_claims"].append("not reviewed")
        gate.refresh_payload_commitment(payload)
        with self.assertRaisesRegex(
            gate.LargerNativeBoundaryCandidateSelectorError,
            "non-claim inventory drift",
        ):
            gate.validate_payload(payload)

    def test_rejects_validation_command_drift(self):
        payload = self.payload()
        payload["validation_commands"].pop(0)
        gate.refresh_payload_commitment(payload)
        with self.assertRaisesRegex(
            gate.LargerNativeBoundaryCandidateSelectorError,
            "validation command inventory drift",
        ):
            gate.validate_payload(payload)

    def test_rejects_payload_commitment_drift(self):
        payload = self.payload()
        payload["payload_commitment"] = "blake2b-256:" + "0" * 64
        with self.assertRaisesRegex(
            gate.LargerNativeBoundaryCandidateSelectorError,
            "payload commitment drift",
        ):
            gate.validate_payload(payload)

    def test_rejects_mutation_result_drift(self):
        payload = self.payload()
        payload["mutation_result"]["cases"][0]["rejected"] = False
        payload["mutation_result"]["all_mutations_rejected"] = False
        payload["mutation_result"]["mutations_rejected"] -= 1
        gate.refresh_payload_commitment(payload)
        with self.assertRaisesRegex(
            gate.LargerNativeBoundaryCandidateSelectorError,
            "mutation rejected count drift|mutation rejection drift|mutation case rejection drift",
        ):
            gate.validate_payload(payload)

    def test_write_bytes_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / "target"
            target.write_text("x")
            link = pathlib.Path(tmp) / "link"
            link.symlink_to(target)
            with self.assertRaisesRegex(
                gate.LargerNativeBoundaryCandidateSelectorError,
                "refusing to write symlink",
            ):
                gate.write_bytes(link, b"no")

    def test_accounting_row_removal_rejects(self):
        payload = self.payload()
        payload["candidates"] = copy.deepcopy(payload["candidates"][:-1])
        gate.refresh_payload_commitment(payload)
        with self.assertRaisesRegex(
            gate.LargerNativeBoundaryCandidateSelectorError,
            "candidate row count drift",
        ):
            gate.validate_payload(payload)


if __name__ == "__main__":
    unittest.main()
