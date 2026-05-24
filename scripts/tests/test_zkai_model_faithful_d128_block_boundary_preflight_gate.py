import csv
import copy
import json
import re
import tempfile
import unittest

from scripts import zkai_model_faithful_d128_block_boundary_preflight_gate as gate


class ModelFaithfulD128BlockBoundaryPreflightGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = gate.build_payload()

    def test_records_model_faithful_boundary_as_next_anchor(self) -> None:
        gate.validate_payload(self.payload)
        self.assertEqual(self.payload["schema"], gate.SCHEMA)
        self.assertEqual(self.payload["issue"], 715)
        self.assertEqual(self.payload["decision"], gate.DECISION)
        self.assertEqual(self.payload["result"], gate.RESULT)
        self.assertEqual(self.payload["primary_next_gate"], gate.PRIMARY_NEXT_GATE)
        self.assertEqual(self.payload["fallback_gate"], gate.FALLBACK_GATE)
        self.assertEqual(self.payload["recommended_action"], gate.RECOMMENDED_ACTION)
        self.assertIn("MODEL_FAITHFUL_D128", self.payload["claim_boundary"])
        self.assertIn("NOT_FULL_BLOCK", self.payload["claim_boundary"])
        self.assertIn("not a full transformer block proof", self.payload["non_claims"])
        self.assertIn("not a matched external zkML comparison", self.payload["non_claims"])
        self.assertEqual(self.payload["mutations_checked"], len(gate.MUTATIONS))
        self.assertTrue(self.payload["all_mutations_rejected"])

    def test_pins_current_and_previous_boundary_metrics(self) -> None:
        summary = self.payload["summary"]
        self.assertEqual(summary["previous_colocated_single_proof_json_bytes"], 504_518)
        self.assertEqual(summary["previous_colocated_split_proof_json_bytes"], 520_399)
        self.assertEqual(summary["previous_colocated_proof_json_saving_bytes"], 15_881)
        self.assertEqual(summary["previous_colocated_typed_bytes"], 204_564)
        self.assertEqual(summary["previous_colocated_typed_saving_bytes"], 4_608)

        self.assertEqual(summary["model_faithful_single_proof_json_bytes"], 503_567)
        self.assertEqual(summary["model_faithful_split_proof_json_bytes"], 522_480)
        self.assertEqual(summary["model_faithful_proof_json_saving_bytes"], 18_913)
        self.assertEqual(summary["model_faithful_typed_bytes"], 204_564)
        self.assertEqual(summary["model_faithful_split_typed_bytes"], 209_732)
        self.assertEqual(summary["model_faithful_typed_saving_bytes"], 5_168)
        self.assertEqual(summary["model_faithful_json_delta_vs_colocated_bytes"], -951)
        self.assertEqual(summary["model_faithful_typed_delta_vs_colocated_bytes"], 0)
        self.assertEqual(summary["model_faithful_typed_saving_delta_vs_colocated_bytes"], 560)
        self.assertTrue(summary["legacy_non_derivation_caveat_removed"])

    def test_rows_keep_seq64_as_fallback_not_primary(self) -> None:
        rows = {row["row_id"]: row for row in self.payload["rows"]}
        self.assertEqual(rows["previous_colocated_d128_boundary"]["status"], "BASELINE_SUPERSEDED_BY_MODEL_FAITHFUL_BINDING")
        self.assertEqual(rows["model_faithful_d128_boundary"]["status"], "CURRENT_CLAIM_ANCHOR_GO")
        self.assertEqual(rows["model_faithful_d128_boundary"]["typed_saving_bytes"], 5_168)
        self.assertEqual(rows["attention_derived_mlp_surface"]["adapter_mismatches"], 0)
        self.assertEqual(rows["attention_derived_mlp_surface"]["saving_bytes"], 32_144)
        self.assertEqual(rows["d128_sequence_stress_context"]["lookup_growth"], 3.72973)
        self.assertEqual(rows["d128_sequence_stress_context"]["trace_growth"], 4.0)
        self.assertEqual(rows["d128_sequence_stress_context"]["fused_proof_growth"], 1.080697)
        self.assertTrue(rows["d128_sequence_stress_context"]["action"].startswith("run_d128_h2_seq64_if"))
        self.assertEqual(rows["next_block_boundary_gate"]["action"], gate.RECOMMENDED_ACTION)

    def test_source_artifacts_are_pinned(self) -> None:
        sources = {artifact["id"]: artifact for artifact in self.payload["source_artifacts"]}
        self.assertEqual(tuple(sources), tuple(gate.EXPECTED_SOURCES))
        for source_id, expected in gate.EXPECTED_SOURCES.items():
            self.assertEqual(sources[source_id]["path"], expected["path"].relative_to(gate.ROOT).as_posix())
            self.assertEqual(sources[source_id]["schema"], expected["schema"])
            self.assertEqual(sources[source_id]["decision"], expected["decision"])
            self.assertEqual(sources[source_id]["result"], expected["result"])
            self.assertEqual(sources[source_id]["sha256"], expected["sha256"])
            self.assertEqual(sources[source_id]["bytes"], expected["bytes"])

    def test_malformed_source_rows_reject_with_gate_error(self) -> None:
        sources, _descriptors = gate.load_sources()
        missing_summary = copy.deepcopy(sources)
        missing_summary["model_faithful_single"].pop("summary")
        with self.assertRaisesRegex(
            gate.ModelFaithfulD128BlockBoundaryPreflightError,
            "model faithful summary",
        ):
            gate.build_rows(missing_summary)

        missing_metric = copy.deepcopy(sources)
        missing_metric["previous_colocated_single"]["summary"].pop("single_proof_json_bytes")
        with self.assertRaisesRegex(
            gate.ModelFaithfulD128BlockBoundaryPreflightError,
            "previous single proof JSON bytes",
        ):
            gate.build_rows(missing_metric)

    def test_individual_mutations_reject(self) -> None:
        for name, mutate in gate.MUTATIONS:
            candidate = copy.deepcopy(self.payload)
            candidate.pop("mutation_results", None)
            candidate.pop("mutations_checked", None)
            candidate.pop("mutations_rejected", None)
            candidate.pop("all_mutations_rejected", None)
            mutate(candidate)
            if name != "payload_commitment_drift":
                candidate["payload_commitment"] = gate.payload_commitment(candidate)
            with self.assertRaises(gate.ModelFaithfulD128BlockBoundaryPreflightError, msg=name):
                gate.validate_payload(candidate, require_mutations=False)

    def test_final_payload_requires_mutation_evidence(self) -> None:
        missing = copy.deepcopy(self.payload)
        missing.pop("mutation_results")
        missing.pop("mutations_checked")
        missing.pop("mutations_rejected")
        missing.pop("all_mutations_rejected")
        missing["payload_commitment"] = gate.payload_commitment(missing)
        with self.assertRaisesRegex(
            gate.ModelFaithfulD128BlockBoundaryPreflightError,
            "mutation results missing",
        ):
            gate.validate_payload(missing)

        blank_error = copy.deepcopy(self.payload)
        blank_error["mutation_results"][0]["error"] = ""
        blank_error["payload_commitment"] = gate.payload_commitment(blank_error)
        with self.assertRaisesRegex(
            gate.ModelFaithfulD128BlockBoundaryPreflightError,
            "mutation error missing",
        ):
            gate.validate_payload(blank_error)

    def test_malformed_rows_reject_with_gate_error(self) -> None:
        malformed = copy.deepcopy(self.payload)
        malformed["rows"].append(None)
        malformed["payload_commitment"] = gate.payload_commitment(malformed)
        with self.assertRaisesRegex(
            gate.ModelFaithfulD128BlockBoundaryPreflightError,
            "row count drift",
        ):
            gate.validate_payload(malformed)

        malformed = copy.deepcopy(self.payload)
        malformed["rows"][0] = None
        malformed["payload_commitment"] = gate.payload_commitment(malformed)
        with self.assertRaisesRegex(
            gate.ModelFaithfulD128BlockBoundaryPreflightError,
            "row 0 must be an object",
        ):
            gate.validate_payload(malformed)

    def test_malformed_lists_reject_with_gate_error(self) -> None:
        malformed_cases = (
            ("non-claims drift", ("non_claims", None, None)),
            ("non-claims drift", ("non_claims", None, 1)),
            ("non-claims drift", ("non_claims", 0, None)),
            ("validation commands drift", ("validation_commands", 0, None)),
            ("GO gate drift", ("go_gate", 0, None)),
            ("NO-GO gate drift", ("no_go_gate", 0, None)),
        )
        for pattern, (field, index, value) in malformed_cases:
            malformed = copy.deepcopy(self.payload)
            if index is None:
                malformed[field] = value
            else:
                malformed[field][index] = value
            malformed["payload_commitment"] = gate.payload_commitment(malformed)
            with self.assertRaisesRegex(gate.ModelFaithfulD128BlockBoundaryPreflightError, re.escape(pattern)):
                gate.validate_payload(malformed)

    def test_non_finite_json_rejects_with_gate_error(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-model-faithful-block-preflight-") as tmp:
            path = gate.pathlib.Path(tmp) / "bad.json"
            path.write_text('{"schema": NaN}\n', encoding="utf-8")
            with self.assertRaisesRegex(
                gate.ModelFaithfulD128BlockBoundaryPreflightError,
                "non-finite JSON constant",
            ):
                gate.read_json(path, "bad source")

        with self.assertRaisesRegex(
            gate.ModelFaithfulD128BlockBoundaryPreflightError,
            "non-canonical JSON value",
        ):
            gate.payload_commitment({"bad": float("nan")})

    def test_write_outputs_round_trip(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-model-faithful-block-preflight-") as tmp:
            tmp_path = gate.pathlib.Path(tmp)
            json_path = tmp_path / "preflight.json"
            tsv_path = tmp_path / "preflight.tsv"
            gate.write_json(json_path, self.payload)
            gate.write_tsv(tsv_path, self.payload)
            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            gate.validate_payload(loaded)
            with tsv_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            tsv_text = tsv_path.read_text(encoding="utf-8")
            self.assertNotIn("\tNone\t", tsv_text)
            self.assertNotIn("\tNone\n", tsv_text)
            self.assertEqual(len(rows), len(gate.ROW_IDS))
            self.assertEqual(rows[-1]["action"], gate.RECOMMENDED_ACTION)
            self.assertEqual(rows[-1]["single_or_fused_bytes"], "")

        with tempfile.TemporaryDirectory(dir=gate.DOCS_DIR, prefix=".tmp-model-faithful-block-preflight-") as tmp:
            md_path = gate.pathlib.Path(tmp) / "preflight.md"
            gate.write_md(md_path, self.payload)
            markdown = md_path.read_text(encoding="utf-8")
            self.assertIn("Model-Faithful D128 Block-Boundary Preflight", markdown)
            self.assertIn("model-faithful d128 attention-derived MLP", markdown)
            self.assertIn("typed bytes stayed flat", markdown)
            self.assertIn("not a full transformer block proof", markdown)

    def test_output_paths_reject_aliasing_and_escape(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-model-faithful-block-preflight-") as tmp:
            same = gate.pathlib.Path(tmp) / "same"
            with self.assertRaisesRegex(gate.ModelFaithfulD128BlockBoundaryPreflightError, "different files"):
                gate.checked_output_paths(same, same, gate.MD_OUT)

        with tempfile.TemporaryDirectory() as tmp:
            outside = gate.pathlib.Path(tmp)
            for writer, path in (
                (gate.write_json, outside / "escape.json"),
                (gate.write_tsv, outside / "escape.tsv"),
                (gate.write_md, outside / "escape.md"),
            ):
                with self.assertRaisesRegex(gate.ModelFaithfulD128BlockBoundaryPreflightError, "inside"):
                    writer(path, self.payload)

        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-model-faithful-block-preflight-") as tmp:
            with tempfile.TemporaryDirectory() as outside_tmp:
                link = gate.pathlib.Path(tmp) / "linked-outside"
                gate.os.symlink(outside_tmp, link, target_is_directory=True)
                with self.assertRaisesRegex(gate.ModelFaithfulD128BlockBoundaryPreflightError, "inside"):
                    gate.write_json(link / "escape.json", self.payload)

        for writer, path in (
            (gate.write_json, gate.EVIDENCE_DIR),
            (gate.write_tsv, gate.EVIDENCE_DIR),
            (gate.write_md, gate.DOCS_DIR),
        ):
            with self.assertRaisesRegex(gate.ModelFaithfulD128BlockBoundaryPreflightError, "file"):
                writer(path, self.payload)


if __name__ == "__main__":
    unittest.main()
