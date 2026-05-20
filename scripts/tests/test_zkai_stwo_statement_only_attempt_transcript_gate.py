from __future__ import annotations

import copy
import csv
import importlib.util
import io
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "scripts" / "zkai_stwo_statement_only_attempt_transcript_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location("zkai_stwo_statement_only_attempt_transcript_gate", GATE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StwoStatementOnlyAttemptTranscriptGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gate = load_gate()
        cls.payload = cls.gate.build_payload()

    def test_statement_only_probe_b_is_current_inner_policy_bound_frontier(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        summary = payload["binding_summary"]
        self.assertEqual(summary["best_profile_id"], "statement_only_probe_b")
        self.assertEqual(summary["best_variant_id"], "adjacent_label_probe_b")
        self.assertEqual(summary["best_typed_bytes"], 39_516)
        self.assertEqual(summary["best_json_bytes"], 113_388)
        self.assertEqual(summary["best_typed_saving_vs_full_policy_b"], 1_376)
        self.assertEqual(summary["best_typed_saving_vs_previous_single_proof_champion"], 2_552)
        self.assertEqual(summary["best_typed_saving_vs_matched_two_proof_frontier"], 7_672)
        self.assertEqual(summary["best_typed_cost_vs_legacy_wrapper_b"], 1_984)
        self.assertTrue(summary["inner_policy_bound_frontier_claimed"])
        self.assertFalse(summary["legacy_wrapper_frontier_claimed"])
        self.assertEqual(summary["nanozk_comparable_external_rows"], 0)
        self.gate.validate_payload(payload)

    def test_profile_rows_preserve_attempt_policy_boundary(self) -> None:
        rows = {row["profile_id"]: row for row in self.__class__.payload["profile_rows"]}
        self.assertEqual(
            set(rows),
            {
                "full_policy_field_mix_probe_b",
                "compact_policy_mix_probe_b",
                "statement_only_probe_a",
                "statement_only_probe_b",
            },
        )
        statement_b = rows["statement_only_probe_b"]
        self.assertEqual(statement_b["policy_version"], self.gate.STATEMENT_ONLY_POLICY_VERSION)
        self.assertEqual(statement_b["policy_stage"], self.gate.STATEMENT_ONLY_POLICY_STAGE)
        self.assertEqual(statement_b["selected_attempt_id"], "adjacent_label_probe_b")
        self.assertEqual(statement_b["selected_attempt_index"], 1)
        self.assertEqual(statement_b["typed_delta_vs_full_policy_b"], -1_376)
        self.assertEqual(statement_b["typed_saving_vs_matched_two_proof_frontier"], 7_672)
        self.assertTrue(statement_b["statement_commitment"].startswith("blake2b-256:"))
        self.assertTrue(statement_b["public_instance_commitment"].startswith("blake2b-256:"))

    def test_payload_commitment_and_mutation_inventory_are_exact(self) -> None:
        payload = self.__class__.payload
        self.assertEqual(payload["payload_commitment"], self.gate.EXPECTED_PAYLOAD_COMMITMENT)
        self.assertEqual(payload["payload_commitment"], self.gate.payload_commitment(payload))
        mutation = payload["mutation_result"]
        self.assertEqual(mutation["accepted"], 0)
        self.assertEqual(mutation["rejected"], len(self.gate.MUTATION_NAMES))
        self.assertEqual(set(mutation["outcomes"]), set(self.gate.MUTATION_NAMES))
        self.assertTrue(all(value == "rejected" for value in mutation["outcomes"].values()))

    def test_mutation_outcome_drift_rejected(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        first_name = self.gate.MUTATION_NAMES[0]
        payload["mutation_result"]["outcomes"][first_name] = "accepted"
        with self.assertRaisesRegex(self.gate.StatementOnlyAttemptTranscriptGateError, "mutation outcome drift"):
            self.gate.validate_payload(payload, check_commitment=False)

    def test_rejects_claim_and_artifact_drift(self) -> None:
        cases = [
            (
                lambda payload: payload.update({"claim_boundary": payload["claim_boundary"] + ";NANOZK_WIN"}),
                "claim_boundary drift",
            ),
            (
                lambda payload: payload["source_artifacts"][0].update({"sha256": "00"}),
                "source artifact drift",
            ),
            (
                lambda payload: payload["profile_rows"][3].update({"policy_version": self.gate.FULL_POLICY_VERSION}),
                "profile row drift",
            ),
            (
                lambda payload: payload["binding_summary"].update({"legacy_wrapper_frontier_claimed": True}),
                "binding summary drift",
            ),
            (
                lambda payload: payload["non_claims"].remove("not a NANOZK proof-size comparison"),
                "non_claims drift",
            ),
        ]
        for mutate, error in cases:
            with self.subTest(error=error):
                payload = copy.deepcopy(self.__class__.payload)
                mutate(payload)
                with self.assertRaisesRegex(self.gate.StatementOnlyAttemptTranscriptGateError, error):
                    self.gate.validate_payload(payload, check_commitment=False)

    def test_payload_commitment_rejects_drift(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        payload["payload_commitment"] = "blake2b-256:00"
        with self.assertRaisesRegex(self.gate.StatementOnlyAttemptTranscriptGateError, "payload commitment drift"):
            self.gate.validate_payload(payload)

    def test_writes_json_and_tsv_under_evidence_dir(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            json_path = tmp / "statement-only.json"
            tsv_path = tmp / "statement-only.tsv"
            self.gate.write_json(json_path, self.__class__.payload)
            self.gate.write_tsv(tsv_path, self.__class__.payload)
            self.assertIn(self.gate.DECISION, json_path.read_text(encoding="utf-8"))
            rows = list(csv.DictReader(io.StringIO(tsv_path.read_text(encoding="utf-8")), delimiter="\t"))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["best_profile_id"], "statement_only_probe_b")
            self.assertEqual(rows[0]["typed_bytes"], "39516")
            self.assertEqual(rows[0]["typed_saving_vs_full_policy_b"], "1376")
            self.assertIn("nanozk_overclaim", rows[0]["mutation_outcomes"])

    def test_rejects_output_path_outside_evidence_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(
                self.gate.StatementOnlyAttemptTranscriptGateError,
                "output path must stay under evidence directory",
            ):
                self.gate.write_json(pathlib.Path(tmpdir) / "out.json", self.__class__.payload)


if __name__ == "__main__":
    unittest.main()
