from __future__ import annotations

import copy
import csv
import importlib.util
import io
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "scripts" / "zkai_stwo_inner_attempt_domain_statement_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location("zkai_stwo_inner_attempt_domain_statement_gate", GATE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StwoInnerAttemptDomainStatementGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gate = load_gate()
        cls.payload = cls.gate.build_payload()

    def test_regenerated_attempt_rows_bind_policy_inside_statement(self) -> None:
        payload = copy.deepcopy(self.__class__.payload)
        rows = {row["variant_id"]: row for row in payload["attempt_rows"]}
        self.assertEqual(set(rows), {"adjacent_label_probe_a", "adjacent_label_probe_b"})
        for variant_id, row in rows.items():
            policy = row["attempt_policy"]
            self.assertEqual(policy["attempt_domain"], ["adjacent_label_probe_a", "adjacent_label_probe_b"])
            self.assertEqual(policy["attempt_budget"], 2)
            self.assertEqual(policy["security_loss_bits"], "1.000000")
            self.assertEqual(policy["policy_stage"], "inner_statement_transcript_metadata")
            self.assertEqual(policy["selected_attempt_id"], variant_id)
            self.assertTrue(row["statement_commitment"].startswith("blake2b-256:"))
            self.assertEqual(row["typed_bytes"], 40_892)
        self.gate.validate_payload(payload)

    def test_summary_is_correctness_upgrade_not_new_frontier(self) -> None:
        summary = self.__class__.payload["binding_summary"]
        self.assertTrue(summary["inner_stwo_statement_binds_attempt_domain"])
        self.assertTrue(summary["inner_stwo_transcript_binds_attempt_domain"])
        self.assertTrue(summary["proof_object_regenerated"])
        self.assertFalse(summary["new_frontier_claimed"])
        self.assertEqual(summary["best_inner_attempt_id"], "adjacent_label_probe_b")
        self.assertEqual(summary["best_inner_attempt_typed_bytes"], 40_892)
        self.assertEqual(summary["best_inner_attempt_json_bytes"], 118_042)
        self.assertEqual(summary["typed_cost_vs_legacy_wrapper_b"], 3_360)
        self.assertEqual(summary["typed_saving_vs_single_proof_champion"], 1_176)
        self.assertEqual(summary["typed_saving_vs_matched_two_proof_frontier"], 6_296)
        self.assertEqual(summary["json_cost_vs_legacy_wrapper_b"], 11_725)
        self.assertEqual(summary["json_saving_vs_matched_two_proof_frontier"], 22_796)
        self.assertEqual(summary["nanozk_comparable_external_rows"], 0)

    def test_source_artifacts_pin_code_and_accounting(self) -> None:
        artifacts = {row["id"]: row for row in self.__class__.payload["source_artifacts"]}
        self.assertEqual(
            artifacts["rust_native_seq32_attention_mlp_source"]["sha256"],
            self.gate.EXPECTED_RUST_SOURCE_SHA256,
        )
        self.assertEqual(
            artifacts["cli_native_seq32_attention_mlp_source"]["sha256"],
            self.gate.EXPECTED_CLI_SOURCE_SHA256,
        )
        self.assertEqual(
            artifacts["inner_attempt_domain_accounting"]["sha256"],
            self.gate.EXPECTED_ACCOUNTING_SHA256,
        )

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

    def test_rejects_policy_and_claim_drift(self) -> None:
        cases = [
            (
                lambda payload: payload["attempt_rows"][1]["attempt_policy"].update(
                    {"attempt_domain": ["adjacent_label_probe_b", "adjacent_label_probe_a"]}
                ),
                "attempt row drift",
            ),
            (
                lambda payload: payload["attempt_rows"][1]["attempt_policy"].update(
                    {"selected_attempt_id": "adjacent_label_probe_a"}
                ),
                "attempt row drift",
            ),
            (
                lambda payload: payload["binding_summary"].update({"typed_cost_vs_legacy_wrapper_b": 0}),
                "binding summary drift",
            ),
            (
                lambda payload: payload.update({"claim_boundary": payload["claim_boundary"] + ";NANOZK_WIN"}),
                "claim_boundary drift",
            ),
        ]
        for mutate, error in cases:
            with self.subTest(error=error):
                payload = copy.deepcopy(self.__class__.payload)
                mutate(payload)
                payload["payload_commitment"] = self.gate.payload_commitment(payload)
                with self.assertRaisesRegex(self.gate.InnerAttemptDomainStatementGateError, error):
                    self.gate.validate_payload(payload)

    def test_render_tsv_records_cost_and_savings(self) -> None:
        text = self.gate.render_tsv(self.__class__.payload)
        rows = list(csv.DictReader(io.StringIO(text), delimiter="\t"))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["best_inner_attempt_id"], "adjacent_label_probe_b")
        self.assertEqual(row["typed_bytes"], "40892")
        self.assertEqual(row["typed_cost_vs_legacy_wrapper_b"], "3360")
        self.assertEqual(row["typed_saving_vs_single_proof_champion"], "1176")
        self.assertEqual(row["typed_saving_vs_matched_two_proof_frontier"], "6296")
        self.assertEqual(row["inner_stwo_transcript_binds_attempt_domain"], "True")
        self.assertIn(
            "attempt_policy_removed=rejected:attempt row field drift: missing attempt_policy",
            row["mutation_outcomes"],
        )

    def test_write_outputs_records_json_and_tsv(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.gate.EVIDENCE_DIR) as tmpdir:
            tmp = pathlib.Path(tmpdir)
            json_out = tmp / "inner-attempt.json"
            tsv_out = tmp / "inner-attempt.tsv"
            self.gate.write_text_if_requested(
                str(json_out),
                self.gate.json.dumps(self.__class__.payload, indent=2, sort_keys=True) + "\n",
            )
            self.gate.write_text_if_requested(str(tsv_out), self.gate.render_tsv(self.__class__.payload))
            self.assertIn("GO_REGENERATED_SEQ32_D128_STWO_PROOFS", json_out.read_text(encoding="utf-8"))
            self.assertIn("adjacent_label_probe_b\t40892", tsv_out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
