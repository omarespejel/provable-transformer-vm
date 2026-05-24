import csv
import copy
import json
import re
import tempfile
import unittest

from scripts import zkai_minimal_d128_block_boundary_wrapper_gate as gate


class MinimalD128BlockBoundaryWrapperGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = gate.build_payload()

    def test_builds_minimal_wrapper_around_model_faithful_boundary(self) -> None:
        gate.validate_payload(self.payload)
        self.assertEqual(self.payload["schema"], gate.SCHEMA)
        self.assertEqual(self.payload["issue"], 715)
        self.assertEqual(self.payload["decision"], gate.DECISION)
        self.assertEqual(self.payload["result"], gate.RESULT)
        self.assertEqual(self.payload["boundary_statement_commitment"], gate.EXPECTED_BOUNDARY_STATEMENT_COMMITMENT)
        self.assertEqual(self.payload["payload_commitment"], gate.EXPECTED_PAYLOAD_COMMITMENT)
        self.assertIn("MINIMAL_D128_BLOCK_BOUNDARY_WRAPPER", self.payload["claim_boundary"])
        self.assertIn("NOT_NEW_PROOF_OBJECT", self.payload["claim_boundary"])
        self.assertIn("not a new native proof object", self.payload["non_claims"])
        self.assertIn("not a full transformer block proof", self.payload["non_claims"])
        self.assertEqual(self.payload["mutations_checked"], len(gate.MUTATIONS))
        self.assertTrue(self.payload["all_mutations_rejected"])

    def test_pins_proof_size_anchor_without_counting_wrapper_as_proof_bytes(self) -> None:
        summary = self.payload["summary"]
        self.assertEqual(summary["underlying_single_proof_json_bytes"], 503_567)
        self.assertEqual(summary["matched_split_proof_json_bytes"], 522_480)
        self.assertEqual(summary["proof_json_saving_bytes"], 18_913)
        self.assertEqual(summary["proof_json_ratio"], "0.963801")
        self.assertEqual(summary["underlying_single_typed_bytes"], 204_564)
        self.assertEqual(summary["matched_split_typed_bytes"], 209_732)
        self.assertEqual(summary["typed_saving_bytes"], 5_168)
        self.assertEqual(summary["typed_ratio"], "0.975359")
        self.assertEqual(summary["wrapper_proof_byte_delta"], 0)
        self.assertEqual(summary["proof_size_comparable_external_rows"], 0)
        self.assertEqual(
            summary["split_component_proof_json_bytes"],
            {
                "attention_fused_softmax_logup_proof": 445_888,
                "attention_derived_d128_rmsnorm_mlp_proof": 76_592,
            },
        )
        self.assertEqual(
            summary["split_component_typed_bytes"],
            {
                "attention_fused_softmax_logup_proof": 184_900,
                "attention_derived_d128_rmsnorm_mlp_proof": 24_832,
            },
        )

    def test_binds_stwo_verifier_domain_and_target(self) -> None:
        proof = self.payload["boundary_statement"]["proof_binding"]
        self.assertEqual(proof["proof_backend"], "stwo")
        self.assertEqual(
            proof["verifier_domain"],
            "ptvm:zkai:native-d128-seq32-attention-mlp-single-proof-object:v1",
        )
        self.assertEqual(
            proof["target_id"],
            "attention-kv-d128-two-head-seq32-fused-softmax-table-plus-d128-attention-derived-d128-rmsnorm-mlp-v1",
        )
        self.assertEqual(proof["envelope_sha256"], gate.EXPECTED_SINGLE["envelope_sha256"])
        self.assertEqual(proof["proof_sha256"], gate.EXPECTED_SINGLE["proof_sha256"])
        self.assertEqual(proof["record_stream_sha256"], gate.EXPECTED_SINGLE["record_stream_sha256"])

    def test_binds_block_statement_chain_commitments(self) -> None:
        block = self.payload["boundary_statement"]["block_statement_binding"]
        self.assertEqual(block["block_statement_commitment"], gate.EXPECTED_BLOCK["block_statement_commitment"])
        self.assertEqual(
            block["source_attention_outputs_commitment"],
            gate.EXPECTED_BLOCK["source_attention_outputs_commitment"],
        )
        self.assertEqual(
            block["derived_input_activation_commitment"],
            gate.EXPECTED_BLOCK["derived_input_activation_commitment"],
        )
        self.assertEqual(
            block["derived_output_activation_commitment"],
            gate.EXPECTED_BLOCK["derived_output_activation_commitment"],
        )
        self.assertEqual(block["accounted_relation_rows"], 199_553)
        self.assertEqual(block["edge_count"], 11)

    def test_records_split_frontier_components(self) -> None:
        split = self.payload["boundary_statement"]["split_frontier"]
        self.assertEqual(split["proof_count"], 2)
        self.assertEqual(split["components"], list(gate.EXPECTED_SPLIT_COMPONENTS))
        self.assertEqual(sum(component["proof_json_size_bytes"] for component in split["components"]), 522_480)
        self.assertEqual(sum(component["typed_bytes"] for component in split["components"]), 209_732)
        self.assertTrue(split["components"][0]["contains_logup"])
        self.assertFalse(split["components"][1]["contains_logup"])
        self.assertTrue(all(component["target_id"] for component in split["components"]))
        self.assertTrue(all(component["verifier_domain"] for component in split["components"]))
        self.assertIsNone(split["components"][1]["source_target_id"])
        self.assertIsNone(split["components"][1]["source_verifier_domain"])

    def test_source_artifacts_are_pinned(self) -> None:
        artifact_ids = [artifact["id"] for artifact in self.payload["source_artifacts"]]
        self.assertEqual(len(artifact_ids), len(set(artifact_ids)))
        self.assertEqual(artifact_ids, list(gate.EXPECTED_SOURCES))
        sources = {artifact["id"]: artifact for artifact in self.payload["source_artifacts"]}
        for source_id, expected in gate.EXPECTED_SOURCES.items():
            self.assertEqual(sources[source_id]["path"], expected["path"].relative_to(gate.ROOT).as_posix())
            self.assertEqual(sources[source_id]["schema"], expected["schema"])
            self.assertEqual(sources[source_id]["decision"], expected["decision"])
            self.assertEqual(sources[source_id]["result"], expected["result"])
            self.assertEqual(sources[source_id]["payload_commitment"], expected["payload_commitment"])
            self.assertEqual(sources[source_id]["sha256"], expected["sha256"])
            self.assertEqual(sources[source_id]["bytes"], expected["bytes"])

    def test_rows_keep_wrapper_as_statement_metadata_not_proof(self) -> None:
        rows = {row["row_id"]: row for row in self.payload["rows"]}
        self.assertEqual(rows["model_faithful_proof_boundary"]["status"], "CURRENT_PROOF_OBJECT_BOUND")
        self.assertEqual(rows["model_faithful_proof_boundary"]["proof_json_bytes"], 503_567)
        self.assertEqual(rows["model_faithful_proof_boundary"]["typed_bytes"], 204_564)
        self.assertEqual(rows["model_faithful_proof_boundary"]["saving_bytes"], 18_913)
        self.assertEqual(rows["attention_derived_block_statement_boundary"]["typed_bytes"], 199_553)
        self.assertEqual(rows["minimal_wrapper_boundary"]["proof_json_bytes"], 0)
        self.assertEqual(rows["minimal_wrapper_boundary"]["split_reference_bytes"], 0)
        self.assertEqual(rows["minimal_wrapper_boundary"]["saving_bytes"], 0)
        self.assertEqual(
            rows["minimal_wrapper_boundary"]["typed_bytes"],
            len(gate.canonical_json_bytes(self.payload["boundary_statement"])),
        )
        self.assertEqual(rows["minimal_wrapper_boundary"]["commitment"], self.payload["boundary_statement_commitment"])

    def test_malformed_source_rows_reject_with_gate_error(self) -> None:
        sources, _descriptors = gate.load_sources()
        missing_summary = copy.deepcopy(sources)
        missing_summary["model_faithful_single"].pop("summary")
        with self.assertRaisesRegex(gate.MinimalD128BlockBoundaryWrapperError, "model faithful single summary"):
            gate.build_boundary_statement(missing_summary)

        missing_local = copy.deepcopy(sources)
        missing_local["model_faithful_single_accounting"]["rows"][0].pop("local_binary_accounting")
        with self.assertRaisesRegex(gate.MinimalD128BlockBoundaryWrapperError, "single local accounting"):
            gate.build_boundary_statement(missing_local)

        missing_block = copy.deepcopy(sources)
        missing_block["attention_derived_block_statement_chain"]["summary"].pop("edge_count")
        with self.assertRaisesRegex(gate.MinimalD128BlockBoundaryWrapperError, "block summary edge_count"):
            gate.build_boundary_statement(missing_block)

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
            with self.assertRaises(gate.MinimalD128BlockBoundaryWrapperError, msg=name):
                gate.validate_payload(candidate, require_mutations=False)

    def test_final_payload_requires_mutation_evidence(self) -> None:
        missing = copy.deepcopy(self.payload)
        missing.pop("mutation_results")
        missing.pop("mutations_checked")
        missing.pop("mutations_rejected")
        missing.pop("all_mutations_rejected")
        missing["payload_commitment"] = gate.payload_commitment(missing)
        with self.assertRaisesRegex(gate.MinimalD128BlockBoundaryWrapperError, "mutation results missing"):
            gate.validate_payload(missing)

        blank_error = copy.deepcopy(self.payload)
        blank_error["mutation_results"][0]["error"] = ""
        blank_error["payload_commitment"] = gate.payload_commitment(blank_error)
        with self.assertRaisesRegex(gate.MinimalD128BlockBoundaryWrapperError, "mutation error missing"):
            gate.validate_payload(blank_error)

    def test_malformed_payload_shapes_reject(self) -> None:
        malformed = copy.deepcopy(self.payload)
        malformed["rows"].append(None)
        malformed["payload_commitment"] = gate.payload_commitment(malformed)
        with self.assertRaisesRegex(gate.MinimalD128BlockBoundaryWrapperError, "row count drift"):
            gate.validate_payload(malformed)

        malformed = copy.deepcopy(self.payload)
        malformed["rows"][0] = None
        malformed["payload_commitment"] = gate.payload_commitment(malformed)
        with self.assertRaisesRegex(gate.MinimalD128BlockBoundaryWrapperError, "row 0 must be an object"):
            gate.validate_payload(malformed)

        malformed = copy.deepcopy(self.payload)
        malformed["non_claims"] = None
        malformed["payload_commitment"] = gate.payload_commitment(malformed)
        with self.assertRaisesRegex(gate.MinimalD128BlockBoundaryWrapperError, "non-claims drift"):
            gate.validate_payload(malformed)

        malformed = copy.deepcopy(self.payload)
        malformed["validation_commands"][0] = None
        malformed["payload_commitment"] = gate.payload_commitment(malformed)
        with self.assertRaisesRegex(gate.MinimalD128BlockBoundaryWrapperError, "validation commands drift"):
            gate.validate_payload(malformed)

    def test_non_finite_json_rejects_with_gate_error(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-minimal-d128-wrapper-") as tmp:
            path = gate.pathlib.Path(tmp) / "bad.json"
            path.write_text('{"schema": NaN}\n', encoding="utf-8")
            with self.assertRaisesRegex(
                gate.MinimalD128BlockBoundaryWrapperError,
                "non-finite JSON constant",
            ):
                gate.read_json(path, "bad source")

            duplicate = gate.pathlib.Path(tmp) / "duplicate.json"
            duplicate.write_text('{"schema": "one", "schema": "two"}\n', encoding="utf-8")
            with self.assertRaisesRegex(gate.MinimalD128BlockBoundaryWrapperError, "duplicate JSON key"):
                gate.read_json(duplicate, "duplicate source")

        with self.assertRaisesRegex(
            gate.MinimalD128BlockBoundaryWrapperError,
            "non-canonical JSON value",
        ):
            gate.payload_commitment({"bad": float("nan")})

    def test_write_outputs_round_trip(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-minimal-d128-wrapper-") as tmp:
            tmp_path = gate.pathlib.Path(tmp)
            json_path = tmp_path / "wrapper.json"
            tsv_path = tmp_path / "wrapper.tsv"
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
            self.assertEqual(rows[-1]["proof_json_bytes"], "0")
            self.assertEqual(rows[-1]["saving_bytes"], "0")

        with tempfile.TemporaryDirectory(dir=gate.DOCS_DIR, prefix=".tmp-minimal-d128-wrapper-") as tmp:
            md_path = gate.pathlib.Path(tmp) / "wrapper.md"
            gate.write_md(md_path, self.payload)
            markdown = md_path.read_text(encoding="utf-8")
            self.assertIn("Minimal D128 Block-Boundary Wrapper", markdown)
            self.assertIn("not a new native proof object", markdown)
            self.assertIn("Wrapper proof-byte delta: `0`", markdown)
            self.assertIn("Block statement commitment", markdown)

    def test_output_paths_reject_aliasing_and_escape(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-minimal-d128-wrapper-") as tmp:
            same = gate.pathlib.Path(tmp) / "same"
            with self.assertRaisesRegex(gate.MinimalD128BlockBoundaryWrapperError, "different files"):
                gate.checked_output_paths(same, same, gate.MD_OUT)

        with tempfile.TemporaryDirectory() as tmp:
            outside = gate.pathlib.Path(tmp)
            for writer, path in (
                (gate.write_json, outside / "escape.json"),
                (gate.write_tsv, outside / "escape.tsv"),
                (gate.write_md, outside / "escape.md"),
            ):
                with self.assertRaisesRegex(gate.MinimalD128BlockBoundaryWrapperError, "inside"):
                    writer(path, self.payload)

        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-minimal-d128-wrapper-") as tmp:
            with tempfile.TemporaryDirectory() as outside_tmp:
                link = gate.pathlib.Path(tmp) / "linked-outside"
                gate.os.symlink(outside_tmp, link, target_is_directory=True)
                with self.assertRaisesRegex(gate.MinimalD128BlockBoundaryWrapperError, "inside"):
                    gate.write_json(link / "escape.json", self.payload)

        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-minimal-d128-wrapper-") as tmp:
            link = gate.pathlib.Path(tmp) / "dangling.json"
            gate.os.symlink(gate.pathlib.Path(tmp) / "missing-target.json", link)
            with self.assertRaisesRegex(gate.MinimalD128BlockBoundaryWrapperError, "symlink"):
                gate.write_json(link, self.payload)

        for writer, path in (
            (gate.write_json, gate.EVIDENCE_DIR),
            (gate.write_tsv, gate.EVIDENCE_DIR),
            (gate.write_md, gate.DOCS_DIR),
        ):
            with self.assertRaisesRegex(gate.MinimalD128BlockBoundaryWrapperError, "file"):
                writer(path, self.payload)


if __name__ == "__main__":
    unittest.main()
