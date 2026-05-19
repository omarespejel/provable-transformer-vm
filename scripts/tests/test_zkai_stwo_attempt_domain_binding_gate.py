from __future__ import annotations

import copy
import csv
import importlib.util
import io
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "scripts" / "zkai_stwo_attempt_domain_binding_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location("zkai_stwo_attempt_domain_binding_gate", GATE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StwoAttemptDomainBindingGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gate = load_gate()
        cls.payload = cls.gate.build_payload()

    def test_binds_two_probe_domain_without_inner_transcript_overclaim(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        summary = payload["binding_summary"]
        envelope = payload["verifier_facing_attempt_envelope"]
        self.assertEqual(
            payload["decision"],
            "GO_TYPED_OUTER_ENVELOPE_BINDS_TWO_PROBE_ATTEMPT_DOMAIN_TO_EXISTING_PROOF_ROW",
        )
        self.assertEqual(envelope["attempt_domain"], ["adjacent_label_probe_a", "adjacent_label_probe_b"])
        self.assertEqual(envelope["selected_attempt_id"], "adjacent_label_probe_b")
        self.assertEqual(envelope["selected_attempt_index"], 1)
        self.assertEqual(envelope["attempt_budget"], 2)
        self.assertEqual(envelope["security_loss_bits"], "1.000000")
        self.assertTrue(summary["outer_envelope_binds_attempt_domain"])
        self.assertTrue(summary["outer_envelope_binds_selected_proof_hashes"])
        self.assertFalse(summary["inner_stwo_transcript_binds_attempt_domain"])
        self.assertFalse(summary["proof_object_regenerated"])
        self.assertFalse(summary["new_frontier_claimed"])
        self.gate.validate_payload(payload)

    def test_selected_proof_artifact_is_probe_b_and_saves_against_local_frontier(self) -> None:
        proof = self.__class__.payload["verifier_facing_attempt_envelope"]["bound_proof_artifact"]
        self.assertEqual(proof["variant_id"], "adjacent_label_probe_b")
        self.assertEqual(proof["typed_bytes"], 37_532)
        self.assertEqual(proof["proof_json_bytes"], 106_317)
        self.assertEqual(proof["path_opening_bytes"], 16_560)
        self.assertEqual(proof["typed_saving_vs_single_proof_champion"], 4_536)
        self.assertEqual(proof["typed_saving_vs_matched_two_proof_frontier"], 9_656)
        self.assertEqual(
            proof["proof_sha256"],
            "4a5dc66d63ee3ddd3acad65e88c42259fb925ee31768a3fdecdb528722630845",
        )

    def test_source_artifacts_bind_builder_and_budget_payloads(self) -> None:
        artifacts = {row["id"]: row for row in self.__class__.payload["source_artifacts"]}
        builder = artifacts["generated_proof_object_builder"]
        budget = artifacts["query_grinding_budget"]
        self.assertEqual(builder["sha256"], self.gate.EXPECTED_BUILDER_SHA256)
        self.assertEqual(builder["payload_commitment"], self.gate.EXPECTED_BUILDER_COMMITMENT)
        self.assertEqual(budget["sha256"], self.gate.EXPECTED_BUDGET_SHA256)
        self.assertEqual(budget["payload_commitment"], self.gate.EXPECTED_BUDGET_COMMITMENT)

    def test_mutation_inventory_is_exact(self) -> None:
        result = self.__class__.payload["mutation_result"]
        self.assertTrue(result["all_mutations_rejected"])
        self.assertEqual(result["mutations_rejected"], len(self.gate.MUTATION_NAMES))
        self.assertEqual(tuple(result["mutation_names"]), self.gate.MUTATION_NAMES)
        self.assertEqual(tuple(case["name"] for case in result["cases"]), self.gate.MUTATION_NAMES)
        self.assertEqual(
            tuple(case["error"] for case in result["cases"]),
            tuple(self.gate.EXPECTED_MUTATION_ERRORS[name] for name in self.gate.MUTATION_NAMES),
        )

    def test_rejects_attempt_and_claim_drift(self) -> None:
        cases = [
            (
                lambda payload: payload["verifier_facing_attempt_envelope"].update(
                    {"attempt_domain": ["adjacent_label_probe_b", "adjacent_label_probe_a"]}
                ),
                "attempt domain drift",
            ),
            (
                lambda payload: payload["verifier_facing_attempt_envelope"].update(
                    {"selected_attempt_id": "adjacent_label_probe_a"}
                ),
                "selected attempt drift",
            ),
            (lambda payload: payload["binding_summary"].update({"new_frontier_claimed": True}), "binding summary drift"),
            (lambda payload: payload.update({"claim_boundary": payload["claim_boundary"] + ";NANOZK_WIN"}), "claim_boundary drift"),
        ]
        for mutate, error in cases:
            with self.subTest(error=error):
                payload = copy.deepcopy(self.__class__.payload)
                mutate(payload)
                payload["payload_commitment"] = self.gate.payload_commitment(payload)
                with self.assertRaisesRegex(self.gate.AttemptDomainBindingGateError, error):
                    self.gate.validate_payload(payload)

    def test_render_tsv_records_attempt_domain_and_artifact_hashes(self) -> None:
        text = self.gate.render_tsv(self.__class__.payload)
        rows = list(csv.DictReader(io.StringIO(text), delimiter="\t"))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["selected_attempt_id"], "adjacent_label_probe_b")
        self.assertEqual(row["attempt_domain"], "adjacent_label_probe_a,adjacent_label_probe_b")
        self.assertEqual(row["typed_bytes"], "37532")
        self.assertEqual(row["security_loss_bits"], "1.000000")
        self.assertEqual(row["inner_stwo_transcript_binds_attempt_domain"], "False")
        self.assertIn("selected_proof_hash_drift=rejected:selected proof artifact drift", row["mutation_outcomes"])

    def test_write_outputs_records_json_and_tsv_inside_evidence_tree(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            json_out = tmp / "attempt-domain.json"
            tsv_out = tmp / "attempt-domain.tsv"
            self.gate.write_outputs(self.__class__.payload, json_out, tsv_out)
            self.assertIn("GO_TYPED_OUTER_ENVELOPE_BINDS_TWO_PROBE_ATTEMPT_DOMAIN", json_out.read_text(encoding="utf-8"))
            self.assertIn("adjacent_label_probe_b\tadjacent_label_probe_a,adjacent_label_probe_b", tsv_out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
