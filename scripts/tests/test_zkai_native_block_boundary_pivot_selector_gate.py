import json
import tempfile
import unittest
from copy import deepcopy

from scripts import zkai_native_block_boundary_pivot_selector_gate as gate


class NativeBlockBoundaryPivotSelectorGateTest(unittest.TestCase):
    def test_build_payload_selects_larger_boundary(self) -> None:
        payload = gate.build_payload()
        self.assertEqual(payload["schema"], gate.SCHEMA)
        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertEqual(payload["result"], gate.RESULT)
        self.assertEqual(payload["summary"]["selected_next_route"], "larger_native_block_boundary")
        self.assertEqual(payload["summary"]["attack_next_count"], 1)
        self.assertEqual(payload["summary"]["park_now_count"], 2)
        self.assertEqual(payload["summary"]["proof_size_comparable_rows"], 0)
        self.assertEqual(payload["summary"]["strict_native_adapter_typed_bytes"], 41_932)
        self.assertEqual(payload["summary"]["strict_native_adapter_gap_bytes"], 1_232)
        self.assertEqual(payload["summary"]["compact_selector_typed_bytes"], 40_812)
        self.assertEqual(payload["summary"]["compact_selector_gap_bytes"], 112)
        self.assertEqual(payload["summary"]["post_tail_typed_bytes"], 42_724)
        self.assertEqual(payload["summary"]["post_tail_label_span_bytes"], 1_216)
        self.assertEqual(payload["summary"]["gkr_smallest_width_preserving_bytes"], 70_138)
        self.assertEqual(payload["summary"]["mlp_fusion_typed_saving_bytes"], 32_144)
        self.assertEqual(payload["summary"]["compact_preprocessed_typed_bytes"], 6_264)
        self.assertEqual(payload["mutation_count"], 12)
        self.assertEqual(payload["mutations_rejected"], 12)

    def test_build_payload_is_deterministic(self) -> None:
        payload_1 = gate.build_payload()
        payload_2 = gate.build_payload()
        self.assertEqual(payload_1, payload_2)

    def test_route_statuses_are_explicit(self) -> None:
        rows = {row["route_id"]: row for row in gate.build_payload()["routes"]}
        self.assertEqual(rows["larger_native_block_boundary"]["selector_status"], "ATTACK_NEXT")
        self.assertEqual(rows["sub_kilobyte_adapter_reorder"]["selector_status"], "PARK_NOW")
        self.assertEqual(rows["current_gkr_projection_sidecar"]["selector_status"], "PARK_NOW")
        self.assertEqual(rows["compact_preprocessed_public_rows"]["selector_status"], "USE_SELECTIVELY")
        self.assertEqual(rows["comparison_claim_guardrail"]["selector_status"], "GUARDRAIL")
        self.assertFalse(any(row["proof_size_comparable_to_nanozk"] for row in rows.values()))

    def test_source_numbers_are_pinned(self) -> None:
        sources = gate.load_sources()
        gate.validate_source_numbers(sources)
        sources["post_tail"] = dict(sources["post_tail"])
        sources["post_tail"]["post_tail_canonical_typed_bytes"] = 40_699
        with self.assertRaisesRegex(gate.PivotSelectorError, "post-tail typed bytes drift"):
            gate.validate_source_numbers(sources)

    def test_rejects_source_ratio_type_drift(self) -> None:
        sources = gate.load_sources()
        sources["mlp_fused"] = dict(sources["mlp_fused"])
        sources["mlp_fused"]["aggregate"] = dict(sources["mlp_fused"]["aggregate"])
        sources["mlp_fused"]["aggregate"]["typed_saving_ratio_vs_separate"] = "0.564167"
        with self.assertRaisesRegex(gate.PivotSelectorError, "MLP saving ratio must be a number"):
            gate.validate_source_numbers(sources)

    def test_mutation_inventory_is_strict(self) -> None:
        payload = gate.build_payload()
        self.assertEqual([row["name"] for row in payload["mutation_results"]], [name for name, _ in gate.MUTATIONS])
        self.assertTrue(all(row["rejected"] for row in payload["mutation_results"]))

    def test_rejects_nanozk_comparable_overclaim(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_promote_nanozk(payload)
        with self.assertRaisesRegex(gate.PivotSelectorError, "NANOZK proof-size comparability overclaim"):
            gate.validate_payload(payload, final=False)

    def test_rejects_next_route_drift(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_next_route_to_post_tail(payload)
        with self.assertRaisesRegex(gate.PivotSelectorError, "selected next route drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_gkr_unparked(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_unpark_gkr(payload)
        with self.assertRaisesRegex(gate.PivotSelectorError, "GKR status drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_mlp_saving_erasure(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_mlp_saving_erased(payload)
        with self.assertRaisesRegex(gate.PivotSelectorError, "MLP saving drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_summary_field_drift(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        payload["summary"]["post_tail_typed_bytes"] = 40_000
        with self.assertRaisesRegex(gate.PivotSelectorError, "post-tail typed drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_non_claim_erasure(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_remove_non_claim(payload)
        with self.assertRaisesRegex(gate.PivotSelectorError, "payload missing non-claims"):
            gate.validate_payload(payload, final=False)

    def test_rejects_source_path_drift(self) -> None:
        payload = gate.base_payload(gate.load_sources())
        gate.mutate_source_path_drift(payload)
        with self.assertRaisesRegex(gate.PivotSelectorError, "source artifact paths drift"):
            gate.validate_payload(payload, final=False)

    def test_rejects_payload_commitment_drift(self) -> None:
        payload = gate.build_payload()
        gate.mutate_payload_commitment(payload)
        with self.assertRaisesRegex(gate.PivotSelectorError, "payload commitment drift"):
            gate.validate_payload(payload)

    def test_rejects_mutation_inventory_drift(self) -> None:
        payload = gate.build_payload()
        payload["mutation_results"] = deepcopy(payload["mutation_results"])
        payload["mutation_results"].pop()
        payload["mutation_count"] -= 1
        payload["mutations_rejected"] -= 1
        payload["payload_commitment"] = gate.commitment({key: value for key, value in payload.items() if key != "payload_commitment"})
        with self.assertRaisesRegex(gate.PivotSelectorError, "mutation inventory drift"):
            gate.validate_payload(payload)

    def test_tsv_shape(self) -> None:
        text = gate.tsv_text(gate.build_payload())
        self.assertEqual(text.splitlines()[0].split("\t"), list(gate.ROW_COLUMNS))
        self.assertIn("larger_native_block_boundary\tATTACK_NEXT", text)
        self.assertIn("current_gkr_projection_sidecar\tPARK_NOW", text)

    def test_write_outputs_round_trips(self) -> None:
        payload = gate.build_payload()
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".json", delete=False) as json_handle:
            json_path = gate.pathlib.Path(json_handle.name)
        with tempfile.NamedTemporaryFile(dir=gate.EVIDENCE_DIR, suffix=".tsv", delete=False) as tsv_handle:
            tsv_path = gate.pathlib.Path(tsv_handle.name)
        try:
            gate.write_outputs(payload, json_path, tsv_path)
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8")), payload)
            self.assertTrue(tsv_path.read_text(encoding="utf-8").startswith("\t".join(gate.ROW_COLUMNS)))
        finally:
            json_path.unlink(missing_ok=True)
            tsv_path.unlink(missing_ok=True)

    def test_write_outputs_rejects_outside_evidence_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(gate.PivotSelectorError, "evidence dir"):
                gate.write_outputs(gate.build_payload(), gate.pathlib.Path(tmpdir) / "x.json", None)

    def test_write_outputs_rejects_symlink_in_path(self) -> None:
        payload = gate.build_payload()
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix="tmp-pivot-symlink-") as tmpdir:
            tmp_path = gate.pathlib.Path(tmpdir)
            target = tmp_path / "target.json"
            target.write_text("{}", encoding="utf-8")
            link = tmp_path / "link.json"
            link.symlink_to(target)
            with self.assertRaisesRegex(gate.PivotSelectorError, "symlink"):
                gate.write_outputs(payload, link, None)

    def test_write_outputs_rejects_symlink_parent(self) -> None:
        payload = gate.build_payload()
        with tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix="tmp-pivot-parent-target-") as target_dir:
            target_path = gate.pathlib.Path(target_dir)
            link_dir = target_path.with_name(f"{target_path.name}-link")
            try:
                link_dir.symlink_to(target_path, target_is_directory=True)
                with self.assertRaisesRegex(gate.PivotSelectorError, "symlink"):
                    gate.write_outputs(payload, link_dir / "payload.json", None)
            finally:
                link_dir.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
