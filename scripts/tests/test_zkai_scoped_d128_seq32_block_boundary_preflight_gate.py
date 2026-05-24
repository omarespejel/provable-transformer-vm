import csv
import copy
import json
import re
import tempfile
import unittest

from scripts import zkai_scoped_d128_seq32_block_boundary_preflight_gate as gate


class ScopedD128Seq32BlockBoundaryPreflightGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = gate.build_payload()

    def test_records_scoped_boundary_decision_without_overclaim(self) -> None:
        gate.validate_payload(self.payload)
        self.assertEqual(self.payload["schema"], gate.SCHEMA)
        self.assertEqual(self.payload["issue"], 715)
        self.assertIn("NOT_FULL_BLOCK", self.payload["claim_boundary"])
        self.assertEqual(self.payload["decision"], gate.DECISION)
        self.assertEqual(self.payload["result"], gate.RESULT)
        self.assertEqual(self.payload["summary"]["primary_next_gate"], gate.PRIMARY_NEXT_GATE)
        self.assertEqual(self.payload["summary"]["stress_gate"], gate.STRESS_GATE)
        self.assertEqual(self.payload["summary"]["recommended_action"], gate.RECOMMENDED_ACTION)
        self.assertEqual(self.payload["summary"]["proof_size_comparable_external_rows"], 0)
        self.assertIn("not a full transformer block proof", self.payload["non_claims"])
        self.assertIn("not a NANOZK proof-size win", self.payload["non_claims"])
        self.assertEqual(self.payload["mutations_checked"], len(gate.MUTATION_NAMES))
        self.assertTrue(self.payload["all_mutations_rejected"])

    def test_binds_current_champion_attention_mlp_and_slope_numbers(self) -> None:
        summary = self.payload["summary"]
        self.assertEqual(summary["existing_seq32_d128_single_typed_bytes"], 42068)
        self.assertEqual(summary["existing_seq32_d128_frontier_typed_bytes"], 47188)
        self.assertEqual(summary["existing_seq32_d128_typed_saving_bytes"], 5120)
        self.assertEqual(summary["existing_seq32_d128_typed_ratio"], 0.891498)
        self.assertEqual(summary["d128_attention_lookup_claims"], 1184)
        self.assertEqual(summary["d128_attention_trace_rows"], 2048)
        self.assertEqual(summary["d128_attention_fused_proof_bytes"], 445888)
        self.assertEqual(summary["d128_attention_split_raw_proof_bytes"], 478276)
        self.assertEqual(summary["d128_attention_saving_bytes"], 32388)
        self.assertEqual(summary["d128_mlp_fused_typed_bytes"], 24272)
        self.assertEqual(summary["d128_mlp_separate_typed_bytes"], 54336)
        self.assertEqual(summary["d128_mlp_typed_saving_bytes"], 30064)
        self.assertEqual(summary["d128_mlp_adapter_mismatches"], 0)
        self.assertEqual(summary["d128_sequence_lookup_growth"], 3.72973)
        self.assertEqual(summary["d128_sequence_trace_growth"], 4.0)
        self.assertEqual(summary["d128_sequence_fused_proof_growth"], 1.080697)
        self.assertEqual(summary["d256_width_fused_proof_growth"], 1.842162)
        self.assertEqual(summary["d256_width_fused_ratio"], 0.964602)

        rows = {row["row_id"]: row for row in self.payload["rows"]}
        self.assertEqual(rows["existing_seq32_d128_single_proof_champion"]["saving_bytes"], 5120)
        self.assertEqual(rows["d128_two_head_seq32_attention_route"]["ratio"], 0.932282)
        self.assertEqual(rows["seq32_derived_d128_mlp_surface"]["adapter_mismatches"], 0)
        self.assertEqual(rows["d128_two_head_seq32_sequence_slope"]["saving_bytes"], 40317)
        self.assertEqual(rows["width_axis_caution"]["status"], "CAUTION_DO_NOT_JUMP_TO_D256_SEQ64_AS_PRIMARY_GATE")
        self.assertEqual(rows["next_scoped_boundary_gate"]["action"], gate.RECOMMENDED_ACTION)

    def test_source_artifacts_are_pinned(self) -> None:
        sources = {artifact["id"]: artifact for artifact in self.payload["source_artifacts"]}
        self.assertEqual(tuple(sources), tuple(gate.EXPECTED_SOURCE_DESCRIPTORS))
        for source_id, expected in gate.EXPECTED_SOURCE_DESCRIPTORS.items():
            self.assertEqual(sources[source_id]["path"], expected["path"].relative_to(gate.ROOT).as_posix())
            self.assertEqual(sources[source_id]["schema"], expected["schema"])
            self.assertEqual(sources[source_id]["decision"], expected["decision"])
            self.assertEqual(sources[source_id]["sha256"], expected["sha256"])
            self.assertEqual(sources[source_id]["bytes"], expected["bytes"])

    def test_individual_mutations_reject(self) -> None:
        for name in gate.MUTATION_NAMES:
            mutated = gate.mutate_payload(self.payload, name)
            with self.assertRaises(gate.ScopedBlockPreflightError, msg=name):
                gate.validate_payload(mutated, require_mutations=False)

    def test_malformed_string_lists_reject_with_gate_error(self) -> None:
        malformed_cases = (
            ("go gate[0]", ("go_gate", 0, None)),
            ("no-go gate[0]", ("no_go_gate", 0, 42)),
            ("non claims[0]", ("non_claims", 0, False)),
            ("validation commands[0]", ("validation_commands", 0, None)),
        )
        for pattern, (field, index, value) in malformed_cases:
            malformed = copy.deepcopy(self.payload)
            malformed[field][index] = value
            with self.assertRaisesRegex(gate.ScopedBlockPreflightError, re.escape(pattern)):
                gate.validate_payload(malformed, require_mutations=False)

    def test_write_outputs_round_trip(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-scoped-d128-preflight-test-") as tmp:
            tmp_path = gate.pathlib.Path(tmp)
            json_path = tmp_path / "preflight.json"
            tsv_path = tmp_path / "preflight.tsv"
            gate.write_json(json_path, self.payload)
            gate.write_tsv(tsv_path, self.payload)
            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            gate.validate_payload(loaded)
            with tsv_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual(len(rows), len(gate.ROW_IDS))
            self.assertEqual(rows[-1]["action"], gate.RECOMMENDED_ACTION)
        with tempfile.TemporaryDirectory(dir=gate.DOCS_DIR, prefix=".tmp-scoped-d128-preflight-test-") as tmp:
            md_path = gate.pathlib.Path(tmp) / "preflight.md"
            gate.write_md(md_path, self.payload)
            markdown = md_path.read_text(encoding="utf-8")
            self.assertIn("Scoped D128 Seq32 Block Boundary Preflight", markdown)
            self.assertIn("attack the scoped `d128 seq32`", markdown)
            self.assertIn("d256 stays a stress test", markdown)
            self.assertIn("not a full transformer block proof", markdown)

    def test_output_paths_reject_aliasing_and_escape(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=".tmp-scoped-d128-preflight-test-") as tmp:
            same = gate.pathlib.Path(tmp) / "same"
            with self.assertRaisesRegex(gate.ScopedBlockPreflightError, "different files"):
                gate.reject_same_output_paths((same, same, gate.pathlib.Path(tmp) / "other.md"))
            with self.assertRaisesRegex(gate.ScopedBlockPreflightError, "different files"):
                gate.checked_output_paths(same, same, gate.MD_OUT)
        with tempfile.TemporaryDirectory() as tmp:
            outside = gate.pathlib.Path(tmp)
            for writer, path in (
                (gate.write_json, outside / "escape.json"),
                (gate.write_tsv, outside / "escape.tsv"),
                (gate.write_md, outside / "escape.md"),
            ):
                with self.assertRaisesRegex(gate.ScopedBlockPreflightError, "inside"):
                    writer(path, self.payload)
        traversal_cases = (
            (gate.write_json, gate.EVIDENCE_DIR.relative_to(gate.ROOT) / ".." / "escape.json"),
            (gate.write_tsv, gate.EVIDENCE_DIR.relative_to(gate.ROOT) / ".." / "escape.tsv"),
            (gate.write_md, gate.DOCS_DIR.relative_to(gate.ROOT) / ".." / "escape.md"),
        )
        for writer, path in traversal_cases:
            with self.assertRaisesRegex(gate.ScopedBlockPreflightError, "inside"):
                writer(path, self.payload)
        for writer, path in (
            (gate.write_json, gate.EVIDENCE_DIR),
            (gate.write_tsv, gate.EVIDENCE_DIR),
            (gate.write_md, gate.DOCS_DIR),
        ):
            with self.assertRaisesRegex(gate.ScopedBlockPreflightError, "file"):
                writer(path, self.payload)


if __name__ == "__main__":
    unittest.main()
