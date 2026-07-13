import copy
import json
import tempfile
import unittest

from scripts import zkai_stwo_ai_boundary_pressure_inventory_gate as gate


class StwoAiBoundaryPressureInventoryGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = gate.build_payload()

    def test_records_read_only_no_fork_decision(self) -> None:
        gate.validate_payload(self.payload)
        self.assertEqual(self.payload["schema"], gate.SCHEMA)
        self.assertEqual(self.payload["decision"], gate.DECISION)
        self.assertEqual(self.payload["fork_status"], gate.FORK_STATUS)
        self.assertEqual(self.payload["aggregate"]["profiles_checked"], 11)
        self.assertEqual(self.payload["aggregate"]["total_saving_bytes"], 223958)
        self.assertEqual(self.payload["aggregate"]["total_opening_saving_bytes"], 209155)
        self.assertEqual(self.payload["aggregate"]["total_opening_saving_share"], 0.933903)
        self.assertEqual(self.payload["aggregate"]["largest_profile_id"], "d64_four_head_seq64")
        self.assertIn("not a Stwo fork", self.payload["non_claims"])
        self.assertIn("delete FRI proof or decommitment witness material inside a valid proof", self.payload["unsafe_actions"])
        self.assertEqual(self.payload["mutations_checked"], len(gate.MUTATION_NAMES))
        self.assertEqual(self.payload["mutations_rejected"], len(gate.MUTATION_NAMES))
        self.assertTrue(self.payload["all_mutations_rejected"])

    def test_d64_decision_gate_has_opening_dominated_pressure(self) -> None:
        d64 = self.payload["aggregate"]["d64_four_head_seq64"]
        self.assertEqual(d64["total_saving_bytes"], 39282)
        self.assertEqual(d64["opening_saving_bytes"], 37827)
        self.assertEqual(d64["fri_saving_bytes"], 27012)
        self.assertEqual(d64["decommitment_saving_bytes"], 10815)
        self.assertEqual(d64["query_saving_bytes"], 850)
        self.assertEqual(d64["source_opening_surface_bytes"], 45896)
        self.assertEqual(d64["sidecar_opening_surface_bytes"], 40721)
        self.assertEqual(d64["fused_opening_surface_bytes"], 48790)
        self.assertEqual(d64["fused_opening_minus_source_opening_bytes"], 2894)
        self.assertEqual(d64["sidecar_opening_absorption_share"], 0.928931)

        rows = {row["profile_id"]: row for row in self.payload["pressure_rows"]}
        row = rows["d64_four_head_seq64"]
        self.assertEqual(row["first_action"], gate.FIRST_ACTION)
        self.assertEqual(row["opening_saving_share"], 0.96296)
        self.assertEqual(row["fork_status"], gate.FORK_STATUS)

    def test_query_policy_evidence_blocks_unsound_query_choice(self) -> None:
        evidence = self.payload["source_evidence"]
        self.assertEqual(evidence["query_hook_decision"], gate.EXPECTED_QUERY_HOOK_DECISION)
        self.assertEqual(evidence["query_preview_decision"], gate.EXPECTED_QUERY_PREVIEW_DECISION)
        self.assertEqual(evidence["query_preview_result"], gate.EXPECTED_QUERY_PREVIEW_RESULT)
        actions = {row["action"]: row for row in self.payload["action_queue"]}
        self.assertEqual(actions["route_level_layout_policy"]["status"], "START_NOW")
        self.assertEqual(actions["upstream_stwo_patch_or_small_fork"]["status"], "FOLLOWUP_ONLY_IF_API_WALL_CONFIRMED")
        self.assertEqual(actions["actual_independent_stwo_ai_fork"]["status"], "NO_GO_NOW")

    def test_mutations_reject(self) -> None:
        for name in gate.MUTATION_NAMES:
            with self.subTest(name=name):
                mutated = gate.mutate_payload(self.payload, name)
                with self.assertRaises(gate.StwoAiBoundaryPressureInventoryError):
                    gate.validate_payload(mutated, require_mutations=False)

    def test_tsv_round_trip(self) -> None:
        tsv = gate.to_tsv(self.payload)
        self.assertIn("d64_four_head_seq64", tsv)
        self.assertIn("ROUTE_LEVEL_LAYOUT_POLICY_AND_PROOF_SECTION_PROFILER_HARDENING", tsv)
        self.assertIn(gate.FORK_STATUS, tsv)

    def test_write_outputs_round_trip(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-stwo-ai-pressure-") as tmp:
            tmp_path = gate.pathlib.Path(tmp)
            json_path = tmp_path / "inventory.json"
            tsv_path = tmp_path / "inventory.tsv"
            gate.write_outputs(self.payload, json_path, tsv_path)
            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            gate.validate_payload(loaded)
            self.assertEqual(tsv_path.read_text(encoding="utf-8"), gate.to_tsv(self.payload))

    def test_output_paths_reject_same_path_and_escape(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-stwo-ai-pressure-") as tmp:
            same = gate.pathlib.Path(tmp) / "same"
            with self.assertRaisesRegex(gate.StwoAiBoundaryPressureInventoryError, "must differ"):
                gate.write_outputs(self.payload, same, same)
        with tempfile.TemporaryDirectory() as tmp:
            outside = gate.pathlib.Path(tmp) / "outside.json"
            with self.assertRaisesRegex(gate.StwoAiBoundaryPressureInventoryError, "inside evidence dir"):
                gate.write_outputs(self.payload, outside, gate.TSV_OUT)

    def test_commitment_rejects_body_drift(self) -> None:
        mutated = copy.deepcopy(self.payload)
        mutated["pressure_rows"][0]["total_saving_bytes"] += 1
        with self.assertRaises(gate.StwoAiBoundaryPressureInventoryError):
            gate.validate_payload(mutated)


if __name__ == "__main__":
    unittest.main()
