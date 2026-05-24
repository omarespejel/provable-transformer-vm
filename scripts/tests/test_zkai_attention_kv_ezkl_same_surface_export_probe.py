from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "zkai_attention_kv_ezkl_same_surface_export_probe.py"
SPEC = importlib.util.spec_from_file_location("zkai_attention_kv_ezkl_same_surface_export_probe", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"failed to load EZKL same-surface export probe from {SCRIPT_PATH}")
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


class ZkAIAttentionKVEzklSameSurfaceExportProbeTests(unittest.TestCase):
    def test_probe_records_source_shape_without_proof_claim(self) -> None:
        payload = PROBE.build_probe()
        PROBE.validate_probe(payload)

        self.assertEqual(payload["decision"], PROBE.DECISION)
        shape = payload["source_shape"]
        self.assertEqual(shape["head_count"], 2)
        self.assertEqual(shape["sequence_length"], 32)
        self.assertEqual(shape["key_width"], 64)
        self.assertEqual(shape["value_width"], 64)
        self.assertEqual(shape["score_row_count"], 1184)
        self.assertEqual(shape["trace_row_count"], 2048)
        self.assertEqual(shape["attention_output_shape"], [64, 64])
        self.assertEqual(shape["weight_policy"], PROBE.SOURCE_WEIGHT_POLICY)
        self.assertEqual(shape["semantics"], PROBE.SOURCE_SEMANTICS)

    def test_candidate_matrix_blocks_direct_vanilla_onnx_claim(self) -> None:
        payload = PROBE.build_probe()
        rows = {row["candidate_adapter"]: row for row in payload["candidate_adapters"]}

        direct = rows["vanilla_onnx_ezkl_direct_export"]
        self.assertEqual(direct["gate"], "NO_GO_SAME_SURFACE_TODAY")
        self.assertEqual(direct["same_surface_claim"], "NO_GO")
        self.assertFalse(direct["proof_generated"])

        custom = rows["custom_integer_table_ezkl_export_probe"]
        self.assertEqual(custom["gate"], "IMPLEMENT_PROBE_NEXT")
        self.assertEqual(custom["same_surface_claim"], "NOT_CHECKED")
        self.assertFalse(custom["proof_generated"])

    def test_rows_for_tsv_are_stable(self) -> None:
        payload = PROBE.build_probe()
        rows = PROBE.rows_for_tsv(payload)

        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["candidate_adapter"], "vanilla_onnx_ezkl_direct_export")
        self.assertEqual(rows[0]["proof_generated"], "false")
        self.assertEqual(rows[1]["candidate_adapter"], "custom_integer_table_ezkl_export_probe")

    def test_source_shape_validation_rejects_mutated_policy(self) -> None:
        source = PROBE.load_source(PROBE.DEFAULT_SOURCE)
        source["weight_policy"] = "float_softmax"

        with self.assertRaisesRegex(PROBE.SameSurfaceExportProbeError, "source scalar drift"):
            PROBE.source_shape(source, PROBE.DEFAULT_SOURCE)

    def test_source_shape_validation_rejects_score_row_count_drift(self) -> None:
        source = PROBE.load_source(PROBE.DEFAULT_SOURCE)
        source["score_row_count"] = source["score_row_count"] + 1

        with self.assertRaisesRegex(PROBE.SameSurfaceExportProbeError, "source scalar drift"):
            PROBE.source_shape(source, PROBE.DEFAULT_SOURCE)

    def test_source_shape_validation_rejects_output_width_drift(self) -> None:
        source = PROBE.load_source(PROBE.DEFAULT_SOURCE)
        source["attention_outputs"] = copy.deepcopy(source["attention_outputs"])
        source["attention_outputs"][0] = source["attention_outputs"][0][:-1]

        with self.assertRaisesRegex(PROBE.SameSurfaceExportProbeError, "attention_outputs width drift"):
            PROBE.source_shape(source, PROBE.DEFAULT_SOURCE)

    def test_validation_rejects_candidate_overclaim(self) -> None:
        payload = PROBE.build_probe()
        payload["candidate_adapters"][0]["proof_generated"] = True
        payload["candidate_matrix_commitment"] = PROBE.blake2b_commitment(
            payload["candidate_adapters"],
            "ptvm:zkai:attention-kv-ezkl-same-surface-candidates:v1",
        )

        with self.assertRaisesRegex(PROBE.SameSurfaceExportProbeError, "candidate adapter matrix drift"):
            PROBE.validate_probe(payload)

    def test_validation_rejects_non_claim_drift(self) -> None:
        payload = PROBE.build_probe()
        payload["non_claims"][0] = "now a proof-generation benchmark"

        with self.assertRaisesRegex(PROBE.SameSurfaceExportProbeError, "non-claims drift"):
            PROBE.validate_probe(payload)

    def test_write_outputs_round_trips_probe_note_and_tsv(self) -> None:
        payload = PROBE.build_probe()
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = pathlib.Path(raw_tmp)
            out_dir = tmp / "out"
            note = tmp / "note.md"
            PROBE.write_outputs(payload, out_dir, note, PROBE.DEFAULT_SOURCE)

            written = json.loads((out_dir / "probe.json").read_text(encoding="utf-8"))
            self.assertEqual(written["schema"], PROBE.SCHEMA)
            self.assertIn("vanilla_onnx_ezkl_direct_export", (out_dir / "adapter_matrix.tsv").read_text())
            self.assertIn("attention_output_shape", (out_dir / "source_shape.tsv").read_text())
            self.assertIn("NO_GO_DIRECT_SAME_SURFACE_BASELINE", note.read_text(encoding="utf-8"))

    def test_render_note_names_prior_probe(self) -> None:
        payload = PROBE.build_probe()
        note = PROBE.render_note(payload)

        self.assertIn("zkai-d64-external-adapter-surface-probe-2026-05-01.md", note)
        self.assertIn("not yet an external baseline row", note)


if __name__ == "__main__":
    unittest.main()
