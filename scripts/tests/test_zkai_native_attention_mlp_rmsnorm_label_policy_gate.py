import copy
import csv
import io
import pathlib
import tempfile
import unittest
from unittest import mock

from scripts import zkai_native_attention_mlp_rmsnorm_label_policy_gate as gate


class RmsnormLabelPolicyGateTest(unittest.TestCase):
    def test_payload_pins_worst_label_policy(self) -> None:
        payload = gate.build_payload()
        summary = payload["summary"]

        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertEqual(payload["result"], gate.RESULT)
        self.assertEqual(summary["best_observed_label"], "label_probe_a")
        self.assertEqual(summary["best_observed_label_typed_bytes"], 40_836)
        self.assertEqual(summary["single_best_label_reduction_to_beat_frontier_bytes"], 137)
        self.assertEqual(summary["canonical_label_reduction_to_beat_frontier_bytes"], 729)
        self.assertEqual(summary["mean_two_label_probes_reduction_to_beat_frontier_bytes"], 769)
        self.assertEqual(summary["worst_label_inventory"], "label_probe_b")
        self.assertEqual(summary["worst_label_inventory_typed_bytes"], 42_100)
        self.assertEqual(summary["worst_label_inventory_delta_vs_frontier_bytes"], 1_400)
        self.assertEqual(summary["worst_label_inventory_reduction_to_beat_frontier_bytes"], 1_401)
        self.assertEqual(summary["worst_label_inventory_reduction_to_beat_compact_selector_bytes"], 1_289)
        self.assertEqual(summary["label_span_typed_bytes"], 1_264)
        self.assertTrue(summary["value_delta_preserved_across_labels"])

    def test_policy_candidates_show_cherry_pick_gap(self) -> None:
        payload = gate.build_payload()
        candidates = payload["policy_candidates"]

        self.assertEqual(candidates["single_best_label"]["typed_bytes"], 40_836)
        self.assertTrue(candidates["single_best_label"]["cherry_pick_risk"])
        self.assertEqual(candidates["single_best_label"]["reduction_to_beat_frontier_bytes"], 137)
        self.assertEqual(candidates["worst_label_inventory"]["typed_bytes"], 42_100)
        self.assertFalse(candidates["worst_label_inventory"]["cherry_pick_risk"])
        self.assertEqual(candidates["worst_label_inventory"]["reduction_to_beat_frontier_bytes"], 1_401)
        self.assertFalse(candidates["worst_label_inventory"]["frontier_promotable"])

    def test_label_inventory_preserves_value_bytes(self) -> None:
        payload = gate.build_payload()
        inventory = {item["name"]: item for item in payload["label_inventory"]}
        canonical_value = inventory["rmsnorm_input_fused"]["value_bytes"]

        for name in ("label_probe_a", "label_probe_b"):
            with self.subTest(name=name):
                self.assertEqual(inventory[name]["value_bytes"], canonical_value)
                self.assertEqual(inventory[name]["value_delta_vs_canonical"], 0)

    def test_mutations_are_rejected(self) -> None:
        payload = gate.build_payload()
        result = payload["mutation_result"]

        self.assertEqual(result["mutation_count"], len(gate.EXPECTED_MUTATION_NAMES))
        self.assertEqual(result["rejected_count"], len(gate.EXPECTED_MUTATION_NAMES))
        self.assertEqual([case["name"] for case in result["cases"]], list(gate.EXPECTED_MUTATION_NAMES))
        self.assertTrue(all(case["rejected"] for case in result["cases"]))

    def test_frontier_overclaim_is_rejected(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["frontier"]["frontier_win_claimed"] = True
        gate.refresh_payload_commitment(mutated)

        with self.assertRaisesRegex(gate.LabelPolicyError, "frontier overclaim"):
            gate.validate_payload(mutated)

    def test_policy_reduction_drift_is_rejected(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["promotion_policy"]["required_reduction_to_beat_frontier_bytes"] = 137
        gate.refresh_payload_commitment(mutated)

        with self.assertRaisesRegex(gate.LabelPolicyError, "policy frontier reduction"):
            gate.validate_payload(mutated)

    def test_candidate_missing_worst_label_is_rejected(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["policy_candidates"].pop("worst_label_inventory")
        gate.refresh_payload_commitment(mutated)

        with self.assertRaisesRegex(gate.LabelPolicyError, "policy candidates key drift"):
            gate.validate_payload(mutated)

    def test_source_artifact_drift_is_rejected(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["source_artifacts"][0]["sha256"] = "00" * 32
        gate.refresh_payload_commitment(mutated)

        with self.assertRaisesRegex(gate.LabelPolicyError, "source artifact drift"):
            gate.validate_payload(mutated)

    def test_source_artifact_path_is_posix_stable(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        path = payload["source_artifacts"][0]["path"]

        self.assertEqual(path, gate.LABEL_SENSITIVITY_RELATIVE_PATH)
        self.assertNotIn("\\", path)

    def test_mutation_result_rejects_extra_keys(self) -> None:
        payload = gate.build_payload()
        mutated = copy.deepcopy(payload["mutation_result"])
        mutated["unchecked"] = True

        with self.assertRaisesRegex(gate.LabelPolicyError, "mutation result key drift"):
            gate.validate_mutation_result(mutated)

    def test_inventory_byte_drift_is_rejected(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["label_inventory"][0]["typed_bytes"] += 1
        gate.refresh_payload_commitment(mutated)

        with self.assertRaisesRegex(
            gate.LabelPolicyError, "inventory byte drift: typed_bytes expected=41428 got=41429"
        ):
            gate.validate_payload(mutated)

    def test_payload_commitment_rejects_drift(self) -> None:
        payload = gate.build_payload(include_mutations=False)
        mutated = copy.deepcopy(payload)
        mutated["summary"]["label_span_typed_bytes"] = 0
        gate.refresh_payload_commitment(mutated)

        with self.assertRaisesRegex(gate.LabelPolicyError, "summary drift"):
            gate.validate_payload(mutated)

    def test_tsv_uses_policy_order(self) -> None:
        payload = gate.build_payload()
        text = gate.tsv_text(payload)
        rows = list(csv.DictReader(io.StringIO(text), dialect="excel-tab"))

        self.assertEqual([row["policy_candidate"] for row in rows], list(gate.POLICY_CANDIDATE_ORDER))
        self.assertEqual(rows[-1]["policy_candidate"], "worst_label_inventory")
        self.assertEqual(rows[-1]["reduction_to_beat_frontier_bytes"], "1401")

    def test_write_outputs_rejects_invalid_payload(self) -> None:
        payload = gate.build_payload()
        payload["promotion_policy"]["multi_label_frontier_promotable"] = True
        gate.refresh_payload_commitment(payload)

        with self.assertRaisesRegex(gate.LabelPolicyError, "multi-label frontier"):
            gate.write_outputs(payload, gate.JSON_OUT, None)

    def test_write_outputs_rejects_duplicate_destinations(self) -> None:
        payload = gate.build_payload()

        with self.assertRaisesRegex(gate.LabelPolicyError, "duplicate output destination"):
            gate.write_outputs(payload, gate.JSON_OUT, gate.JSON_OUT)

    def test_write_outputs_rejects_relative_absolute_duplicate_destinations(self) -> None:
        payload = gate.build_payload()
        relative = pathlib.Path("docs/engineering/evidence/rmsnorm-label-policy-collision.tmp")
        absolute = gate.ROOT / relative

        with self.assertRaisesRegex(gate.LabelPolicyError, "duplicate output destination"):
            gate.write_outputs(payload, relative, absolute)

    def test_write_outputs_stages_pair_before_replacing_targets(self) -> None:
        payload = gate.build_payload()
        json_path = gate.EVIDENCE_DIR / "rmsnorm-label-policy-atomic-json.tmp"
        tsv_path = gate.EVIDENCE_DIR / "rmsnorm-label-policy-atomic-tsv.tmp"
        original_writer = gate.sensitivity_gate.write_text_atomically
        writes = []

        try:
            original_writer(json_path, "old-json\n")
            original_writer(tsv_path, "old-tsv\n")

            def fail_second_write(path: pathlib.Path, text: str) -> None:
                writes.append(path)
                if len(writes) == 2:
                    raise gate.sensitivity_gate.RmsnormLabelSensitivityError("forced second write")
                original_writer(path, text)

            with mock.patch.object(
                gate.sensitivity_gate, "write_text_atomically", side_effect=fail_second_write
            ):
                with self.assertRaisesRegex(gate.LabelPolicyError, "forced second write"):
                    gate.write_outputs(payload, json_path, tsv_path)

            self.assertEqual(json_path.read_text(), "old-json\n")
            self.assertEqual(tsv_path.read_text(), "old-tsv\n")
        finally:
            json_path.unlink(missing_ok=True)
            tsv_path.unlink(missing_ok=True)

    def test_write_outputs_fsyncs_directory_after_pair_publish(self) -> None:
        payload = gate.build_payload()
        json_path = gate.EVIDENCE_DIR / "rmsnorm-label-policy-fsync-json.tmp"
        tsv_path = gate.EVIDENCE_DIR / "rmsnorm-label-policy-fsync-tsv.tmp"

        try:
            with mock.patch.object(
                gate.sensitivity_gate,
                "fsync_dir_fd",
                wraps=gate.sensitivity_gate.fsync_dir_fd,
            ) as fsync_dir:
                gate.write_outputs(payload, json_path, tsv_path)

            self.assertGreaterEqual(fsync_dir.call_count, 3)
            self.assertTrue(
                any(len(call.args) > 1 and call.args[1] == gate.EVIDENCE_DIR for call in fsync_dir.mock_calls)
            )
        finally:
            json_path.unlink(missing_ok=True)
            tsv_path.unlink(missing_ok=True)

    def test_write_outputs_rejects_outside_evidence_dir(self) -> None:
        payload = gate.build_payload()
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(gate.LabelPolicyError, "evidence dir"):
                gate.write_outputs(payload, pathlib.Path(tmpdir) / "policy.json", None)


if __name__ == "__main__":
    unittest.main()
