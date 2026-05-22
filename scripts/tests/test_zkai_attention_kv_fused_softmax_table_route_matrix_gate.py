import copy
import csv
import json
import tempfile
import unittest
from unittest import mock

from scripts import zkai_attention_kv_fused_softmax_table_route_matrix_gate as gate


class AttentionKvFusedSoftmaxTableRouteMatrixGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = gate.build_result()

    def test_records_controlled_axis_matrix_with_matched_eight_head_comparator(self):
        result = self.result
        self.assertEqual(result["decision"], gate.DECISION)
        self.assertEqual(result["route_id"], gate.ROUTE_ID)
        self.assertEqual(result["profiles_checked"], 19)
        self.assertEqual(result["matched_comparator_profiles"], 19)
        self.assertEqual(result["no_comparator_profiles"], [])
        self.assertIn("NOT_REAL_VALUED_SOFTMAX", result["claim_boundary"])
        self.assertIn("MATCHED_SOURCE_PLUS_SIDECAR_COMPARATORS", result["claim_boundary"])
        self.assertEqual(result["mutations_checked"], len(gate.EXPECTED_MUTATION_NAMES))
        self.assertEqual(result["mutations_rejected"], len(gate.EXPECTED_MUTATION_NAMES))

    def test_route_rows_match_expected_dimensions_and_existing_gate_metrics(self):
        rows = {row["profile_id"]: row for row in self.result["route_rows"]}

        self.assertEqual(rows["d8_single_head_seq8"]["lookup_claims"], 52)
        self.assertEqual(rows["d8_single_head_seq8"]["trace_rows"], 64)
        self.assertEqual(rows["d8_single_head_seq8"]["fused_proof_size_bytes"], 47698)
        self.assertEqual(rows["d8_single_head_seq8"]["fused_to_source_plus_sidecar_ratio"], 0.802497)

        self.assertEqual(rows["d16_single_head_seq8"]["key_width"], 16)
        self.assertEqual(rows["d16_single_head_seq8"]["lookup_claims"], 52)
        self.assertEqual(rows["d16_single_head_seq8"]["fused_proof_size_bytes"], 64503)
        self.assertEqual(rows["d16_single_head_seq8"]["fused_to_source_plus_sidecar_ratio"], 0.860487)

        self.assertEqual(rows["d32_single_head_seq8"]["axis_role"], "width_axis_extension")
        self.assertEqual(rows["d32_single_head_seq8"]["key_width"], 32)
        self.assertEqual(rows["d32_single_head_seq8"]["lookup_claims"], 52)
        self.assertEqual(rows["d32_single_head_seq8"]["trace_rows"], 64)
        self.assertEqual(rows["d32_single_head_seq8"]["source_proof_size_bytes"], 101120)
        self.assertEqual(rows["d32_single_head_seq8"]["sidecar_proof_size_bytes"], 15562)
        self.assertEqual(rows["d32_single_head_seq8"]["source_plus_sidecar_raw_proof_bytes"], 116682)
        self.assertEqual(rows["d32_single_head_seq8"]["fused_proof_size_bytes"], 107261)
        self.assertEqual(rows["d32_single_head_seq8"]["fused_to_source_plus_sidecar_ratio"], 0.919259)

        self.assertEqual(rows["d8_two_head_seq8"]["head_count"], 2)
        self.assertEqual(rows["d8_two_head_seq8"]["lookup_claims"], 104)
        self.assertEqual(rows["d8_two_head_seq8"]["fused_proof_size_bytes"], 49508)
        self.assertEqual(rows["d8_four_head_seq8"]["head_count"], 4)
        self.assertEqual(rows["d8_four_head_seq8"]["lookup_claims"], 208)
        self.assertEqual(rows["d8_four_head_seq8"]["fused_to_source_plus_sidecar_ratio"], 0.717412)

        self.assertEqual(rows["d8_eight_head_seq8"]["head_count"], 8)
        self.assertEqual(rows["d8_eight_head_seq8"]["lookup_claims"], 416)
        self.assertEqual(rows["d8_eight_head_seq8"]["source_plus_sidecar_raw_proof_bytes"], 74086)
        self.assertEqual(rows["d8_eight_head_seq8"]["sidecar_proof_size_bytes"], 21694)
        self.assertEqual(rows["d8_eight_head_seq8"]["fused_proof_size_bytes"], 59375)
        self.assertEqual(rows["d8_eight_head_seq8"]["fused_to_source_plus_sidecar_ratio"], 0.801433)
        self.assertEqual(rows["d8_eight_head_seq8"]["matched_source_sidecar_status"], gate.MATCHED_COMPARATOR_STATUS)

        self.assertEqual(rows["d8_sixteen_head_seq8"]["head_count"], 16)
        self.assertEqual(rows["d8_sixteen_head_seq8"]["lookup_claims"], 832)
        self.assertEqual(rows["d8_sixteen_head_seq8"]["source_plus_sidecar_raw_proof_bytes"], 88711)
        self.assertEqual(rows["d8_sixteen_head_seq8"]["sidecar_proof_size_bytes"], 28062)
        self.assertEqual(rows["d8_sixteen_head_seq8"]["fused_proof_size_bytes"], 65006)
        self.assertEqual(rows["d8_sixteen_head_seq8"]["fused_to_source_plus_sidecar_ratio"], 0.732784)
        self.assertEqual(rows["d8_sixteen_head_seq8"]["matched_source_sidecar_status"], gate.MATCHED_COMPARATOR_STATUS)

        self.assertEqual(rows["d8_two_head_seq16"]["steps_per_head"], 16)
        self.assertEqual(rows["d8_two_head_seq16"]["lookup_claims"], 336)
        self.assertEqual(rows["d8_two_head_seq16"]["fused_proof_size_bytes"], 60502)
        self.assertEqual(rows["d8_two_head_seq16"]["source_plus_sidecar_raw_proof_bytes"], 79444)

        self.assertEqual(rows["d8_two_head_seq32"]["axis_role"], "sequence_axis_extension")
        self.assertEqual(rows["d8_two_head_seq32"]["steps_per_head"], 32)
        self.assertEqual(rows["d8_two_head_seq32"]["lookup_claims"], 1184)
        self.assertEqual(rows["d8_two_head_seq32"]["trace_rows"], 2048)
        self.assertEqual(rows["d8_two_head_seq32"]["source_proof_size_bytes"], 62983)
        self.assertEqual(rows["d8_two_head_seq32"]["sidecar_proof_size_bytes"], 35029)
        self.assertEqual(rows["d8_two_head_seq32"]["source_plus_sidecar_raw_proof_bytes"], 98012)
        self.assertEqual(rows["d8_two_head_seq32"]["fused_proof_size_bytes"], 66327)
        self.assertEqual(rows["d8_two_head_seq32"]["fused_to_source_plus_sidecar_ratio"], 0.676723)

        self.assertEqual(rows["d16_two_head_seq8"]["axis_role"], "combined_width_head_axis")
        self.assertEqual(rows["d16_two_head_seq8"]["key_width"], 16)
        self.assertEqual(rows["d16_two_head_seq8"]["head_count"], 2)
        self.assertEqual(rows["d16_two_head_seq8"]["lookup_claims"], 104)
        self.assertEqual(rows["d16_two_head_seq8"]["trace_rows"], 128)
        self.assertEqual(rows["d16_two_head_seq8"]["source_proof_size_bytes"], 73508)
        self.assertEqual(rows["d16_two_head_seq8"]["sidecar_proof_size_bytes"], 18088)
        self.assertEqual(rows["d16_two_head_seq8"]["source_plus_sidecar_raw_proof_bytes"], 91596)
        self.assertEqual(rows["d16_two_head_seq8"]["fused_proof_size_bytes"], 78211)
        self.assertEqual(rows["d16_two_head_seq8"]["fused_to_source_plus_sidecar_ratio"], 0.853869)

        self.assertEqual(rows["d32_two_head_seq8"]["axis_role"], "combined_width_head_axis_extension")
        self.assertEqual(rows["d32_two_head_seq8"]["key_width"], 32)
        self.assertEqual(rows["d32_two_head_seq8"]["head_count"], 2)
        self.assertEqual(rows["d32_two_head_seq8"]["lookup_claims"], 104)
        self.assertEqual(rows["d32_two_head_seq8"]["trace_rows"], 128)
        self.assertEqual(rows["d32_two_head_seq8"]["source_proof_size_bytes"], 123926)
        self.assertEqual(rows["d32_two_head_seq8"]["sidecar_proof_size_bytes"], 18137)
        self.assertEqual(rows["d32_two_head_seq8"]["source_plus_sidecar_raw_proof_bytes"], 142063)
        self.assertEqual(rows["d32_two_head_seq8"]["fused_proof_size_bytes"], 125756)
        self.assertEqual(rows["d32_two_head_seq8"]["fused_to_source_plus_sidecar_ratio"], 0.885213)

        self.assertEqual(rows["d16_two_head_seq16"]["axis_role"], "combined_width_head_sequence_axis")
        self.assertEqual(rows["d16_two_head_seq16"]["key_width"], 16)
        self.assertEqual(rows["d16_two_head_seq16"]["head_count"], 2)
        self.assertEqual(rows["d16_two_head_seq16"]["steps_per_head"], 16)
        self.assertEqual(rows["d16_two_head_seq16"]["lookup_claims"], 336)
        self.assertEqual(rows["d16_two_head_seq16"]["trace_rows"], 512)
        self.assertEqual(rows["d16_two_head_seq16"]["source_proof_size_bytes"], 83330)
        self.assertEqual(rows["d16_two_head_seq16"]["sidecar_proof_size_bytes"], 24828)
        self.assertEqual(rows["d16_two_head_seq16"]["source_plus_sidecar_raw_proof_bytes"], 108158)
        self.assertEqual(rows["d16_two_head_seq16"]["fused_proof_size_bytes"], 84868)
        self.assertEqual(rows["d16_two_head_seq16"]["fused_to_source_plus_sidecar_ratio"], 0.784667)

        self.assertEqual(rows["d16_two_head_seq32"]["axis_role"], "combined_width_head_sequence_axis_lower_seq32_extension")
        self.assertEqual(rows["d16_two_head_seq32"]["key_width"], 16)
        self.assertEqual(rows["d16_two_head_seq32"]["head_count"], 2)
        self.assertEqual(rows["d16_two_head_seq32"]["steps_per_head"], 32)
        self.assertEqual(rows["d16_two_head_seq32"]["lookup_claims"], 1184)
        self.assertEqual(rows["d16_two_head_seq32"]["trace_rows"], 2048)
        self.assertEqual(rows["d16_two_head_seq32"]["source_proof_size_bytes"], 90754)
        self.assertEqual(rows["d16_two_head_seq32"]["sidecar_proof_size_bytes"], 36453)
        self.assertEqual(rows["d16_two_head_seq32"]["source_plus_sidecar_raw_proof_bytes"], 127207)
        self.assertEqual(rows["d16_two_head_seq32"]["fused_proof_size_bytes"], 92363)
        self.assertEqual(rows["d16_two_head_seq32"]["fused_over_source_proof_bytes"], 1609)
        self.assertEqual(rows["d16_two_head_seq32"]["fused_saves_vs_source_plus_sidecar_bytes"], 34844)
        self.assertEqual(rows["d16_two_head_seq32"]["fused_to_source_plus_sidecar_ratio"], 0.726084)

        self.assertEqual(rows["d32_two_head_seq16"]["axis_role"], "combined_width_head_sequence_axis_extension")
        self.assertEqual(rows["d32_two_head_seq16"]["key_width"], 32)
        self.assertEqual(rows["d32_two_head_seq16"]["head_count"], 2)
        self.assertEqual(rows["d32_two_head_seq16"]["steps_per_head"], 16)
        self.assertEqual(rows["d32_two_head_seq16"]["lookup_claims"], 336)
        self.assertEqual(rows["d32_two_head_seq16"]["trace_rows"], 512)
        self.assertEqual(rows["d32_two_head_seq16"]["source_proof_size_bytes"], 135063)
        self.assertEqual(rows["d32_two_head_seq16"]["sidecar_proof_size_bytes"], 27075)
        self.assertEqual(rows["d32_two_head_seq16"]["source_plus_sidecar_raw_proof_bytes"], 162138)
        self.assertEqual(rows["d32_two_head_seq16"]["fused_proof_size_bytes"], 132543)
        self.assertEqual(rows["d32_two_head_seq16"]["fused_over_source_proof_bytes"], -2520)
        self.assertEqual(rows["d32_two_head_seq16"]["fused_saves_vs_source_plus_sidecar_bytes"], 29595)
        self.assertEqual(rows["d32_two_head_seq16"]["fused_to_source_plus_sidecar_ratio"], 0.81747)

        self.assertEqual(rows["d32_four_head_seq16"]["axis_role"], "combined_width_head_sequence_crossing_extension")
        self.assertEqual(rows["d32_four_head_seq16"]["key_width"], 32)
        self.assertEqual(rows["d32_four_head_seq16"]["head_count"], 4)
        self.assertEqual(rows["d32_four_head_seq16"]["steps_per_head"], 16)
        self.assertEqual(rows["d32_four_head_seq16"]["lookup_claims"], 672)
        self.assertEqual(rows["d32_four_head_seq16"]["trace_rows"], 1024)
        self.assertEqual(rows["d32_four_head_seq16"]["source_proof_size_bytes"], 139755)
        self.assertEqual(rows["d32_four_head_seq16"]["sidecar_proof_size_bytes"], 30263)
        self.assertEqual(rows["d32_four_head_seq16"]["source_plus_sidecar_raw_proof_bytes"], 170018)
        self.assertEqual(rows["d32_four_head_seq16"]["fused_proof_size_bytes"], 142334)
        self.assertEqual(rows["d32_four_head_seq16"]["fused_over_source_proof_bytes"], 2579)
        self.assertEqual(rows["d32_four_head_seq16"]["fused_saves_vs_source_plus_sidecar_bytes"], 27684)
        self.assertEqual(rows["d32_four_head_seq16"]["fused_to_source_plus_sidecar_ratio"], 0.83717)

        self.assertEqual(rows["d32_two_head_seq32"]["axis_role"], "combined_width_head_sequence_axis_seq32_extension")
        self.assertEqual(rows["d32_two_head_seq32"]["key_width"], 32)
        self.assertEqual(rows["d32_two_head_seq32"]["head_count"], 2)
        self.assertEqual(rows["d32_two_head_seq32"]["steps_per_head"], 32)
        self.assertEqual(rows["d32_two_head_seq32"]["lookup_claims"], 1184)
        self.assertEqual(rows["d32_two_head_seq32"]["trace_rows"], 2048)
        self.assertEqual(rows["d32_two_head_seq32"]["source_proof_size_bytes"], 145497)
        self.assertEqual(rows["d32_two_head_seq32"]["sidecar_proof_size_bytes"], 30976)
        self.assertEqual(rows["d32_two_head_seq32"]["source_plus_sidecar_raw_proof_bytes"], 176473)
        self.assertEqual(rows["d32_two_head_seq32"]["fused_proof_size_bytes"], 150147)
        self.assertEqual(rows["d32_two_head_seq32"]["fused_over_source_proof_bytes"], 4650)
        self.assertEqual(rows["d32_two_head_seq32"]["fused_saves_vs_source_plus_sidecar_bytes"], 26326)
        self.assertEqual(rows["d32_two_head_seq32"]["fused_to_source_plus_sidecar_ratio"], 0.850821)

        self.assertEqual(rows["d32_four_head_seq32"]["axis_role"], "combined_width_head_sequence_axis_seq32_head_extension")
        self.assertEqual(rows["d32_four_head_seq32"]["key_width"], 32)
        self.assertEqual(rows["d32_four_head_seq32"]["head_count"], 4)
        self.assertEqual(rows["d32_four_head_seq32"]["steps_per_head"], 32)
        self.assertEqual(rows["d32_four_head_seq32"]["lookup_claims"], 2368)
        self.assertEqual(rows["d32_four_head_seq32"]["trace_rows"], 4096)
        self.assertEqual(rows["d32_four_head_seq32"]["source_proof_size_bytes"], 151309)
        self.assertEqual(rows["d32_four_head_seq32"]["sidecar_proof_size_bytes"], 41628)
        self.assertEqual(rows["d32_four_head_seq32"]["source_plus_sidecar_raw_proof_bytes"], 192937)
        self.assertEqual(rows["d32_four_head_seq32"]["fused_proof_size_bytes"], 154670)
        self.assertEqual(rows["d32_four_head_seq32"]["fused_over_source_proof_bytes"], 3361)
        self.assertEqual(rows["d32_four_head_seq32"]["fused_saves_vs_source_plus_sidecar_bytes"], 38267)
        self.assertEqual(rows["d32_four_head_seq32"]["fused_to_source_plus_sidecar_ratio"], 0.801661)

        self.assertEqual(rows["d64_two_head_seq16"]["axis_role"], "combined_width_head_sequence_axis_d64_seq16_falsification")
        self.assertEqual(rows["d64_two_head_seq16"]["key_width"], 64)
        self.assertEqual(rows["d64_two_head_seq16"]["head_count"], 2)
        self.assertEqual(rows["d64_two_head_seq16"]["steps_per_head"], 16)
        self.assertEqual(rows["d64_two_head_seq16"]["lookup_claims"], 336)
        self.assertEqual(rows["d64_two_head_seq16"]["trace_rows"], 512)
        self.assertEqual(rows["d64_two_head_seq16"]["source_proof_size_bytes"], 230688)
        self.assertEqual(rows["d64_two_head_seq16"]["sidecar_proof_size_bytes"], 27037)
        self.assertEqual(rows["d64_two_head_seq16"]["source_plus_sidecar_raw_proof_bytes"], 257725)
        self.assertEqual(rows["d64_two_head_seq16"]["fused_proof_size_bytes"], 238504)
        self.assertEqual(rows["d64_two_head_seq16"]["fused_over_source_proof_bytes"], 7816)
        self.assertEqual(rows["d64_two_head_seq16"]["fused_saves_vs_source_plus_sidecar_bytes"], 19221)
        self.assertEqual(rows["d64_two_head_seq16"]["fused_to_source_plus_sidecar_ratio"], 0.925421)

        self.assertEqual(rows["d64_two_head_seq32"]["axis_role"], "combined_width_head_sequence_axis_d64_seq32_falsification")
        self.assertEqual(rows["d64_two_head_seq32"]["key_width"], 64)
        self.assertEqual(rows["d64_two_head_seq32"]["head_count"], 2)
        self.assertEqual(rows["d64_two_head_seq32"]["steps_per_head"], 32)
        self.assertEqual(rows["d64_two_head_seq32"]["lookup_claims"], 1184)
        self.assertEqual(rows["d64_two_head_seq32"]["trace_rows"], 2048)
        self.assertEqual(rows["d64_two_head_seq32"]["source_proof_size_bytes"], 248702)
        self.assertEqual(rows["d64_two_head_seq32"]["sidecar_proof_size_bytes"], 36400)
        self.assertEqual(rows["d64_two_head_seq32"]["source_plus_sidecar_raw_proof_bytes"], 285102)
        self.assertEqual(rows["d64_two_head_seq32"]["fused_proof_size_bytes"], 253257)
        self.assertEqual(rows["d64_two_head_seq32"]["fused_over_source_proof_bytes"], 4555)
        self.assertEqual(rows["d64_two_head_seq32"]["fused_saves_vs_source_plus_sidecar_bytes"], 31845)
        self.assertEqual(rows["d64_two_head_seq32"]["fused_to_source_plus_sidecar_ratio"], 0.888303)

    def test_axis_summary_separates_width_head_and_sequence_effects(self):
        summary = self.result["axis_summary"]
        self.assertEqual(summary["width_axis_d8_to_d16"]["key_width_ratio"], 2.0)
        self.assertEqual(summary["width_axis_d8_to_d16"]["lookup_claim_ratio"], 1.0)
        self.assertEqual(summary["width_axis_d8_to_d16"]["fused_proof_size_ratio"], 1.352321)

        width = summary["width_axis_single_head_seq8"]
        self.assertEqual(width["profile_ids"], ["d8_single_head_seq8", "d16_single_head_seq8", "d32_single_head_seq8"])
        self.assertEqual(width["key_widths"], [8, 16, 32])
        self.assertEqual(width["lookup_claims"], [52, 52, 52])
        self.assertEqual(width["trace_rows"], [64, 64, 64])
        self.assertEqual(width["fused_proof_size_bytes"], [47698, 64503, 107261])
        self.assertEqual(width["source_plus_sidecar_raw_proof_bytes"], [59437, 74961, 116682])
        self.assertEqual(width["fused_to_source_plus_sidecar_ratios"], [0.802497, 0.860487, 0.919259])
        self.assertEqual(width["d16_to_d32_key_width_ratio"], 2.0)
        self.assertEqual(width["d16_to_d32_fused_proof_size_ratio"], 1.662884)
        self.assertEqual(width["d16_to_d32_source_plus_sidecar_ratio"], 1.556569)
        self.assertEqual(width["d8_to_d32_key_width_ratio"], 4.0)
        self.assertEqual(width["d8_to_d32_fused_proof_size_ratio"], 2.248753)

        head = summary["head_axis_d8_seq8"]
        self.assertEqual(head["head_counts"], [1, 2, 4, 8, 16])
        self.assertEqual(head["lookup_claim_ratio_1_to_16"], 16.0)
        self.assertEqual(head["lookup_claim_ratio_8_to_16"], 2.0)
        self.assertEqual(head["fused_proof_ratio_1_to_16"], 1.362866)
        self.assertEqual(head["fused_proof_ratio_8_to_16"], 1.094838)
        self.assertEqual(head["matched_comparator_head_counts"], [1, 2, 4, 8, 16])
        self.assertEqual(
            head["matched_fused_to_source_plus_sidecar_ratios"],
            [0.802497, 0.759232, 0.717412, 0.801433, 0.732784],
        )
        self.assertEqual(head["eight_head_comparator_status"], gate.MATCHED_COMPARATOR_STATUS)
        self.assertEqual(head["sixteen_head_comparator_status"], gate.MATCHED_COMPARATOR_STATUS)

        sequence = summary["sequence_axis_two_head_d8"]
        self.assertEqual(sequence["profile_ids"], ["d8_two_head_seq8", "d8_two_head_seq16", "d8_two_head_seq32"])
        self.assertEqual(sequence["steps_per_head"], [8, 16, 32])
        self.assertEqual(sequence["lookup_claims"], [104, 336, 1184])
        self.assertEqual(sequence["trace_rows"], [128, 512, 2048])
        self.assertEqual(sequence["fused_proof_size_bytes"], [49508, 60502, 66327])
        self.assertEqual(sequence["source_plus_sidecar_raw_proof_bytes"], [65208, 79444, 98012])
        self.assertEqual(sequence["fused_to_source_plus_sidecar_ratios"], [0.759232, 0.761568, 0.676723])
        self.assertEqual(sequence["seq8_to_seq16_steps_ratio"], 2.0)
        self.assertEqual(sequence["seq8_to_seq16_lookup_claim_ratio"], 3.230769)
        self.assertEqual(sequence["seq8_to_seq16_trace_row_ratio"], 4.0)
        self.assertEqual(sequence["seq8_to_seq16_fused_proof_size_ratio"], 1.222065)
        self.assertEqual(sequence["seq16_to_seq32_steps_ratio"], 2.0)
        self.assertEqual(sequence["seq16_to_seq32_lookup_claim_ratio"], 3.52381)
        self.assertEqual(sequence["seq16_to_seq32_trace_row_ratio"], 4.0)
        self.assertEqual(sequence["seq16_to_seq32_fused_proof_size_ratio"], 1.096278)

        combined = summary["combined_width_head_axis_seq8"]
        self.assertEqual(combined["profile_id"], "d16_two_head_seq8")
        self.assertEqual(combined["key_width"], 16)
        self.assertEqual(combined["head_count"], 2)
        self.assertEqual(combined["lookup_claims"], 104)
        self.assertEqual(combined["trace_rows"], 128)
        self.assertEqual(combined["vs_d16_single_head_lookup_claim_ratio"], 2.0)
        self.assertEqual(combined["vs_d16_single_head_trace_row_ratio"], 2.0)
        self.assertEqual(combined["vs_d16_single_head_fused_proof_size_ratio"], 1.212517)
        self.assertEqual(combined["vs_d8_two_head_lookup_claim_ratio"], 1.0)
        self.assertEqual(combined["vs_d8_two_head_trace_row_ratio"], 1.0)
        self.assertEqual(combined["vs_d8_two_head_fused_proof_size_ratio"], 1.579765)

        combined_ext = summary["combined_width_head_axis_seq8_extension"]
        self.assertEqual(combined_ext["profile_id"], "d32_two_head_seq8")
        self.assertEqual(combined_ext["key_width"], 32)
        self.assertEqual(combined_ext["head_count"], 2)
        self.assertEqual(combined_ext["lookup_claims"], 104)
        self.assertEqual(combined_ext["trace_rows"], 128)
        self.assertEqual(combined_ext["fused_proof_size_bytes"], 125756)
        self.assertEqual(combined_ext["source_plus_sidecar_raw_proof_bytes"], 142063)
        self.assertEqual(combined_ext["vs_d32_single_head_lookup_claim_ratio"], 2.0)
        self.assertEqual(combined_ext["vs_d32_single_head_trace_row_ratio"], 2.0)
        self.assertEqual(combined_ext["vs_d32_single_head_fused_proof_size_ratio"], 1.17243)
        self.assertEqual(combined_ext["vs_d16_two_head_key_width_ratio"], 2.0)
        self.assertEqual(combined_ext["vs_d16_two_head_lookup_claim_ratio"], 1.0)
        self.assertEqual(combined_ext["vs_d16_two_head_trace_row_ratio"], 1.0)
        self.assertEqual(combined_ext["vs_d16_two_head_fused_proof_size_ratio"], 1.607907)
        self.assertEqual(combined_ext["matched_comparator_status"], gate.MATCHED_COMPARATOR_STATUS)

        all_axes = summary["combined_width_head_sequence_axis"]
        self.assertEqual(all_axes["profile_id"], "d16_two_head_seq16")
        self.assertEqual(all_axes["key_width"], 16)
        self.assertEqual(all_axes["head_count"], 2)
        self.assertEqual(all_axes["steps_per_head"], 16)
        self.assertEqual(all_axes["lookup_claims"], 336)
        self.assertEqual(all_axes["trace_rows"], 512)
        self.assertEqual(all_axes["fused_proof_size_bytes"], 84868)
        self.assertEqual(all_axes["source_plus_sidecar_raw_proof_bytes"], 108158)
        self.assertEqual(all_axes["vs_d16_two_head_seq8_steps_ratio"], 2.0)
        self.assertEqual(all_axes["vs_d16_two_head_seq8_lookup_claim_ratio"], 3.230769)
        self.assertEqual(all_axes["vs_d16_two_head_seq8_trace_row_ratio"], 4.0)
        self.assertEqual(all_axes["vs_d16_two_head_seq8_fused_proof_size_ratio"], 1.085116)
        self.assertEqual(all_axes["vs_d8_two_head_seq16_key_width_ratio"], 2.0)
        self.assertEqual(all_axes["vs_d8_two_head_seq16_lookup_claim_ratio"], 1.0)
        self.assertEqual(all_axes["vs_d8_two_head_seq16_trace_row_ratio"], 1.0)
        self.assertEqual(all_axes["vs_d8_two_head_seq16_fused_proof_size_ratio"], 1.40273)
        self.assertEqual(all_axes["matched_comparator_status"], gate.MATCHED_COMPARATOR_STATUS)

        d16_seq32 = summary["combined_width_head_sequence_axis_lower_seq32_extension"]
        self.assertEqual(d16_seq32["profile_ids"], ["d16_two_head_seq8", "d16_two_head_seq16", "d16_two_head_seq32"])
        self.assertEqual(d16_seq32["steps_per_head"], [8, 16, 32])
        self.assertEqual(d16_seq32["lookup_claims"], [104, 336, 1184])
        self.assertEqual(d16_seq32["trace_rows"], [128, 512, 2048])
        self.assertEqual(d16_seq32["fused_proof_size_bytes"], [78211, 84868, 92363])
        self.assertEqual(d16_seq32["source_plus_sidecar_raw_proof_bytes"], [91596, 108158, 127207])
        self.assertEqual(d16_seq32["fused_to_source_plus_sidecar_ratios"], [0.853869, 0.784667, 0.726084])
        self.assertEqual(d16_seq32["seq16_to_seq32_lookup_claim_ratio"], 3.52381)
        self.assertEqual(d16_seq32["seq16_to_seq32_trace_row_ratio"], 4.0)
        self.assertEqual(d16_seq32["seq16_to_seq32_fused_proof_size_ratio"], 1.088314)
        self.assertEqual(d16_seq32["seq16_to_seq32_source_plus_sidecar_ratio"], 1.176122)
        self.assertEqual(d16_seq32["seq16_to_seq32_savings_ratio"], 1.496093)

        d8_to_d16_seq32 = summary["combined_width_head_sequence_axis_d8_to_d16_seq32_width_check"]
        self.assertEqual(d8_to_d16_seq32["profile_ids"], ["d8_two_head_seq32", "d16_two_head_seq32"])
        self.assertEqual(d8_to_d16_seq32["key_widths"], [8, 16])
        self.assertEqual(d8_to_d16_seq32["lookup_claims"], [1184, 1184])
        self.assertEqual(d8_to_d16_seq32["trace_rows"], [2048, 2048])
        self.assertEqual(d8_to_d16_seq32["d8_to_d16_fused_proof_size_ratio"], 1.39254)
        self.assertEqual(d8_to_d16_seq32["d8_to_d16_source_plus_sidecar_ratio"], 1.297872)
        self.assertEqual(d8_to_d16_seq32["d8_to_d16_savings_ratio"], 1.0997)

        d16_to_d32_seq32 = summary["combined_width_head_sequence_axis_d16_to_d32_seq32_width_check"]
        self.assertEqual(d16_to_d32_seq32["profile_ids"], ["d16_two_head_seq32", "d32_two_head_seq32"])
        self.assertEqual(d16_to_d32_seq32["key_widths"], [16, 32])
        self.assertEqual(d16_to_d32_seq32["lookup_claims"], [1184, 1184])
        self.assertEqual(d16_to_d32_seq32["trace_rows"], [2048, 2048])
        self.assertEqual(d16_to_d32_seq32["d16_to_d32_fused_proof_size_ratio"], 1.625618)
        self.assertEqual(d16_to_d32_seq32["d16_to_d32_source_plus_sidecar_ratio"], 1.38729)
        self.assertEqual(d16_to_d32_seq32["d16_to_d32_savings_ratio"], 0.755539)

        all_axes_ext = summary["combined_width_head_sequence_axis_extension"]
        self.assertEqual(all_axes_ext["profile_id"], "d32_two_head_seq16")
        self.assertEqual(all_axes_ext["key_width"], 32)
        self.assertEqual(all_axes_ext["head_count"], 2)
        self.assertEqual(all_axes_ext["steps_per_head"], 16)
        self.assertEqual(all_axes_ext["lookup_claims"], 336)
        self.assertEqual(all_axes_ext["trace_rows"], 512)
        self.assertEqual(all_axes_ext["fused_proof_size_bytes"], 132543)
        self.assertEqual(all_axes_ext["source_plus_sidecar_raw_proof_bytes"], 162138)
        self.assertEqual(all_axes_ext["fused_to_source_plus_sidecar_ratio"], 0.81747)
        self.assertEqual(all_axes_ext["fused_over_source_proof_bytes"], -2520)
        self.assertEqual(all_axes_ext["fused_saves_vs_source_plus_sidecar_bytes"], 29595)
        self.assertEqual(all_axes_ext["vs_d32_two_head_seq8_steps_ratio"], 2.0)
        self.assertEqual(all_axes_ext["vs_d32_two_head_seq8_lookup_claim_ratio"], 3.230769)
        self.assertEqual(all_axes_ext["vs_d32_two_head_seq8_trace_row_ratio"], 4.0)
        self.assertEqual(all_axes_ext["vs_d32_two_head_seq8_fused_proof_size_ratio"], 1.05397)
        self.assertEqual(all_axes_ext["vs_d32_two_head_seq8_source_plus_sidecar_ratio"], 1.141311)
        self.assertEqual(all_axes_ext["vs_d16_two_head_seq16_key_width_ratio"], 2.0)
        self.assertEqual(all_axes_ext["vs_d16_two_head_seq16_lookup_claim_ratio"], 1.0)
        self.assertEqual(all_axes_ext["vs_d16_two_head_seq16_trace_row_ratio"], 1.0)
        self.assertEqual(all_axes_ext["vs_d16_two_head_seq16_fused_proof_size_ratio"], 1.561755)
        self.assertEqual(all_axes_ext["matched_comparator_status"], gate.MATCHED_COMPARATOR_STATUS)

        d32_head_ext = summary["combined_width_head_sequence_axis_d32_head_extension"]
        self.assertEqual(d32_head_ext["profile_ids"], ["d32_two_head_seq16", "d32_four_head_seq16"])
        self.assertEqual(d32_head_ext["head_counts"], [2, 4])
        self.assertEqual(d32_head_ext["lookup_claims"], [336, 672])
        self.assertEqual(d32_head_ext["trace_rows"], [512, 1024])
        self.assertEqual(d32_head_ext["fused_proof_size_bytes"], [132543, 142334])
        self.assertEqual(d32_head_ext["source_plus_sidecar_raw_proof_bytes"], [162138, 170018])
        self.assertEqual(d32_head_ext["fused_to_source_plus_sidecar_ratios"], [0.81747, 0.83717])
        self.assertEqual(d32_head_ext["two_to_four_head_count_ratio"], 2.0)
        self.assertEqual(d32_head_ext["two_to_four_lookup_claim_ratio"], 2.0)
        self.assertEqual(d32_head_ext["two_to_four_trace_row_ratio"], 2.0)
        self.assertEqual(d32_head_ext["two_to_four_fused_proof_size_ratio"], 1.07387)
        self.assertEqual(d32_head_ext["two_to_four_source_plus_sidecar_ratio"], 1.048601)
        self.assertEqual(d32_head_ext["two_to_four_savings_ratio"], 0.935428)
        self.assertEqual(d32_head_ext["matched_comparator_status"], gate.MATCHED_COMPARATOR_STATUS)

        all_axes_seq32 = summary["combined_width_head_sequence_axis_seq32_extension"]
        self.assertEqual(all_axes_seq32["profile_ids"], ["d32_two_head_seq8", "d32_two_head_seq16", "d32_two_head_seq32"])
        self.assertEqual(all_axes_seq32["steps_per_head"], [8, 16, 32])
        self.assertEqual(all_axes_seq32["lookup_claims"], [104, 336, 1184])
        self.assertEqual(all_axes_seq32["trace_rows"], [128, 512, 2048])
        self.assertEqual(all_axes_seq32["fused_proof_size_bytes"], [125756, 132543, 150147])
        self.assertEqual(all_axes_seq32["source_plus_sidecar_raw_proof_bytes"], [142063, 162138, 176473])
        self.assertEqual(all_axes_seq32["fused_to_source_plus_sidecar_ratios"], [0.885213, 0.81747, 0.850821])
        self.assertEqual(all_axes_seq32["seq16_to_seq32_lookup_claim_ratio"], 3.52381)
        self.assertEqual(all_axes_seq32["seq16_to_seq32_trace_row_ratio"], 4.0)
        self.assertEqual(all_axes_seq32["seq16_to_seq32_fused_proof_size_ratio"], 1.132817)
        self.assertEqual(all_axes_seq32["seq16_to_seq32_source_plus_sidecar_ratio"], 1.088412)
        self.assertEqual(all_axes_seq32["seq16_to_seq32_savings_ratio"], 0.889542)

        d32_seq32_head = summary["combined_width_head_sequence_axis_d32_seq32_head_extension"]
        self.assertEqual(d32_seq32_head["profile_ids"], ["d32_two_head_seq32", "d32_four_head_seq32"])
        self.assertEqual(d32_seq32_head["head_counts"], [2, 4])
        self.assertEqual(d32_seq32_head["lookup_claims"], [1184, 2368])
        self.assertEqual(d32_seq32_head["trace_rows"], [2048, 4096])
        self.assertEqual(d32_seq32_head["fused_proof_size_bytes"], [150147, 154670])
        self.assertEqual(d32_seq32_head["source_plus_sidecar_raw_proof_bytes"], [176473, 192937])
        self.assertEqual(d32_seq32_head["fused_to_source_plus_sidecar_ratios"], [0.850821, 0.801661])
        self.assertEqual(d32_seq32_head["two_to_four_head_count_ratio"], 2.0)
        self.assertEqual(d32_seq32_head["two_to_four_lookup_claim_ratio"], 2.0)
        self.assertEqual(d32_seq32_head["two_to_four_trace_row_ratio"], 2.0)
        self.assertEqual(d32_seq32_head["two_to_four_source_proof_size_ratio"], 1.039946)
        self.assertEqual(d32_seq32_head["two_to_four_fused_proof_size_ratio"], 1.030124)
        self.assertEqual(d32_seq32_head["two_to_four_source_plus_sidecar_ratio"], 1.093295)
        self.assertEqual(d32_seq32_head["two_to_four_savings_ratio"], 1.453582)

        d64_seq32 = summary["combined_width_head_sequence_axis_d64_seq32_falsification"]
        self.assertEqual(d64_seq32["profile_ids"], ["d32_two_head_seq32", "d64_two_head_seq32"])
        self.assertEqual(d64_seq32["key_widths"], [32, 64])
        self.assertEqual(d64_seq32["lookup_claims"], [1184, 1184])
        self.assertEqual(d64_seq32["trace_rows"], [2048, 2048])
        self.assertEqual(d64_seq32["fused_proof_size_bytes"], [150147, 253257])
        self.assertEqual(d64_seq32["source_plus_sidecar_raw_proof_bytes"], [176473, 285102])
        self.assertEqual(d64_seq32["fused_to_source_plus_sidecar_ratios"], [0.850821, 0.888303])
        self.assertEqual(d64_seq32["d32_to_d64_key_width_ratio"], 2.0)
        self.assertEqual(d64_seq32["d32_to_d64_lookup_claim_ratio"], 1.0)
        self.assertEqual(d64_seq32["d32_to_d64_trace_row_ratio"], 1.0)
        self.assertEqual(d64_seq32["d32_to_d64_source_proof_size_ratio"], 1.709327)
        self.assertEqual(d64_seq32["d32_to_d64_fused_proof_size_ratio"], 1.686727)
        self.assertEqual(d64_seq32["d32_to_d64_source_plus_sidecar_ratio"], 1.615556)
        self.assertEqual(d64_seq32["d32_to_d64_savings_ratio"], 1.209641)
        self.assertEqual(d64_seq32["matched_comparator_status"], gate.MATCHED_COMPARATOR_STATUS)

        d64_seq16 = summary["combined_width_head_sequence_axis_d64_seq16_falsification"]
        self.assertEqual(d64_seq16["profile_ids"], ["d32_two_head_seq16", "d64_two_head_seq16"])
        self.assertEqual(d64_seq16["key_widths"], [32, 64])
        self.assertEqual(d64_seq16["lookup_claims"], [336, 336])
        self.assertEqual(d64_seq16["trace_rows"], [512, 512])
        self.assertEqual(d64_seq16["fused_proof_size_bytes"], [132543, 238504])
        self.assertEqual(d64_seq16["source_plus_sidecar_raw_proof_bytes"], [162138, 257725])
        self.assertEqual(d64_seq16["fused_to_source_plus_sidecar_ratios"], [0.81747, 0.925421])
        self.assertEqual(d64_seq16["d32_to_d64_key_width_ratio"], 2.0)
        self.assertEqual(d64_seq16["d32_to_d64_lookup_claim_ratio"], 1.0)
        self.assertEqual(d64_seq16["d32_to_d64_trace_row_ratio"], 1.0)
        self.assertEqual(d64_seq16["d32_to_d64_source_proof_size_ratio"], 1.708003)
        self.assertEqual(d64_seq16["d32_to_d64_fused_proof_size_ratio"], 1.799446)
        self.assertEqual(d64_seq16["d32_to_d64_source_plus_sidecar_ratio"], 1.589541)
        self.assertEqual(d64_seq16["d32_to_d64_savings_ratio"], 0.649468)

        d64_sequence = summary["combined_width_head_sequence_axis_d64_sequence_extension"]
        self.assertEqual(d64_sequence["profile_ids"], ["d64_two_head_seq16", "d64_two_head_seq32"])
        self.assertEqual(d64_sequence["steps_per_head"], [16, 32])
        self.assertEqual(d64_sequence["lookup_claims"], [336, 1184])
        self.assertEqual(d64_sequence["trace_rows"], [512, 2048])
        self.assertEqual(d64_sequence["fused_proof_size_bytes"], [238504, 253257])
        self.assertEqual(d64_sequence["source_plus_sidecar_raw_proof_bytes"], [257725, 285102])
        self.assertEqual(d64_sequence["fused_to_source_plus_sidecar_ratios"], [0.925421, 0.888303])
        self.assertEqual(d64_sequence["seq16_to_seq32_lookup_claim_ratio"], 3.52381)
        self.assertEqual(d64_sequence["seq16_to_seq32_trace_row_ratio"], 4.0)
        self.assertEqual(d64_sequence["seq16_to_seq32_source_proof_size_ratio"], 1.078088)
        self.assertEqual(d64_sequence["seq16_to_seq32_fused_proof_size_ratio"], 1.061856)
        self.assertEqual(d64_sequence["seq16_to_seq32_source_plus_sidecar_ratio"], 1.106226)
        self.assertEqual(d64_sequence["seq16_to_seq32_savings_ratio"], 1.656782)

    def test_aggregate_metrics_are_checked(self):
        metrics = self.result["aggregate_metrics"]
        self.assertEqual(metrics["total_lookup_claims"], 11044)
        self.assertEqual(metrics["total_trace_rows"], 17728)
        self.assertEqual(metrics["total_fused_proof_size_bytes"], 2026301)
        self.assertEqual(metrics["max_fused_proof_size_bytes"], 253257)
        self.assertEqual(metrics["matched_source_plus_sidecar_raw_proof_bytes_total"], 2444487)
        self.assertEqual(metrics["matched_fused_proof_size_bytes_total"], 2026301)
        self.assertEqual(metrics["matched_fused_savings_bytes_total"], 418186)
        self.assertEqual(metrics["min_matched_fused_to_source_plus_sidecar_ratio"], 0.676723)
        self.assertEqual(metrics["max_matched_fused_to_source_plus_sidecar_ratio"], 0.925421)

    def test_declared_mutations_reject(self):
        self.assertEqual([item["name"] for item in self.result["mutation_results"]], list(gate.EXPECTED_MUTATION_NAMES))
        self.assertTrue(all(item["rejected"] is True for item in self.result["mutation_results"]))

    def test_validate_rejects_metric_smuggling_and_overclaims(self):
        bad = copy.deepcopy(self.result)
        bad["route_rows"][4]["source_plus_sidecar_raw_proof_bytes"] = 1
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "source-plus-sidecar sum drift"):
            gate.validate_result(bad)

        bad = copy.deepcopy(self.result)
        bad["axis_summary"]["head_axis_d8_seq8"]["fused_proof_ratio_1_to_16"] = 16.0
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "axis summary drift"):
            gate.validate_result(bad)

        bad = copy.deepcopy(self.result)
        bad["claim_boundary"] = "GO_REAL_VALUED_SOFTMAX_PUBLIC_BENCHMARK"
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "result drift for claim_boundary"):
            gate.validate_result(bad)

        bad = copy.deepcopy(self.result)
        bad["route_rows"][0]["label"] = "different label"
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "label drift"):
            gate.validate_result(bad)

        bad = copy.deepcopy(self.result)
        bad["route_rows"][0]["decision"] = "GO_DIFFERENT_GATE"
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "decision drift"):
            gate.validate_result(bad)

        bad = copy.deepcopy(self.result)
        bad["route_rows"][0]["evidence_json"] = "other.json"
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "evidence path drift"):
            gate.validate_result(bad)

        bad = copy.deepcopy(self.result)
        seq32 = next(row for row in bad["route_rows"] if row["profile_id"] == "d8_two_head_seq32")
        seq32["lookup_claims"] -= 1
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "d8_two_head_seq32 lookup/score row drift"):
            gate.validate_result(bad)

    def test_source_dimensions_rejects_malformed_dimensions_with_gate_errors(self):
        base = {
            "score_rows": [
                {
                    "head_index": 0,
                    "step_index": 0,
                    "candidate_index": 0,
                    "key": [1, 2],
                    "value": [3, 4],
                },
                {"head_index": 0, "step_index": 0, "candidate_index": 1, "key": [1, 2], "value": [3, 4]},
                {"head_index": 0, "step_index": 0, "candidate_index": 2, "key": [1, 2], "value": [3, 4]},
            ],
            "trace_rows": 8,
        }
        self.assertEqual(gate.source_dimensions(base)["key_width"], 2)

        bad = copy.deepcopy(base)
        bad["score_rows"][0].pop("key")
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "source key_width missing"):
            gate.source_dimensions(bad)

        bad = copy.deepcopy(base)
        bad["score_rows"][0].pop("value")
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "source value_width missing"):
            gate.source_dimensions(bad)

        bad = copy.deepcopy(base)
        bad.pop("trace_rows")
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "source trace_rows missing"):
            gate.source_dimensions(bad)

        bad = copy.deepcopy(base)
        bad["score_rows"][0].pop("step_index")
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "source step_index missing"):
            gate.source_dimensions(bad)

        bad = copy.deepcopy(base)
        bad["key_width"] = "not-an-int"
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "source dimensions must be integer-like"):
            gate.source_dimensions(bad)

        bad = copy.deepcopy(base)
        bad["key_width"] = "+-1"
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "source dimensions must be integer-like"):
            gate.source_dimensions(bad)

        bad = copy.deepcopy(base)
        bad["key_width"] = 8.5
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "source dimensions must be integer-like"):
            gate.source_dimensions(bad)

        bad = copy.deepcopy(base)
        bad["key_width"] = True
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "source dimensions must be integer-like"):
            gate.source_dimensions(bad)

        good = copy.deepcopy(base)
        good["key_width"] = "2"
        good["value_width"] = 2.0
        self.assertEqual(gate.source_dimensions(good)["value_width"], 2)

        bad = copy.deepcopy(base)
        bad["key_width"] = -1
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "source dimensions must be positive"):
            gate.source_dimensions(bad)

    def test_source_dimensions_rejects_head_step_grid_drift(self):
        source = {
            "score_rows": [
                {
                    "head_index": head_index,
                    "step_index": step_index,
                    "candidate_index": candidate_index,
                    "key": [1, 2],
                    "value": [3, 4],
                }
                for head_index in (0, 1)
                for step_index in (0, 1)
                for candidate_index in range(step_index + 3)
            ],
            "trace_rows": 8,
        }
        self.assertEqual(gate.source_dimensions(source)["head_count"], 2)

        bad = copy.deepcopy(source)
        for row in bad["score_rows"]:
            if row["head_index"] == 1 and row["step_index"] == 1:
                row["head_index"] = 0
                row["step_index"] = 0
                row["candidate_index"] += 3
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "source head/step grid incomplete"):
            gate.source_dimensions(bad)

        bad = copy.deepcopy(source)
        for row in bad["score_rows"]:
            row["head_index"] += 1
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "source head_index grid drift"):
            gate.source_dimensions(bad)

        bad = copy.deepcopy(source)
        for row in bad["score_rows"]:
            row["step_index"] += 1
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "source step_index grid drift"):
            gate.source_dimensions(bad)

        bad = copy.deepcopy(source)
        bad["score_rows"][0]["candidate_index"] = 1
        with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "source duplicate candidate row"):
            gate.source_dimensions(bad)

    def test_mutator_failures_are_gate_failures_not_rejections(self):
        def broken_mutator(_result):
            raise RuntimeError("boom")

        with mock.patch.object(gate, "mutation_cases", return_value=(("broken_mutator", broken_mutator),)):
            with self.assertRaisesRegex(gate.FusedSoftmaxTableRouteMatrixGateError, "mutation mutator failed"):
                gate.build_result()

    def test_write_json_and_tsv_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = gate.pathlib.Path(tmp)
            json_path = tmp_path / "route-matrix.json"
            tsv_path = tmp_path / "route-matrix.tsv"
            gate.write_json(json_path, self.result)
            gate.write_tsv(tsv_path, self.result)
            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            gate.validate_result(loaded)
            with tsv_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual(len(rows), 19)
            self.assertEqual(rows[0]["profile_id"], "d8_single_head_seq8")
            self.assertEqual(rows[2]["profile_id"], "d32_single_head_seq8")
            self.assertEqual(rows[2]["source_plus_sidecar_raw_proof_bytes"], "116682")
            self.assertEqual(rows[2]["fused_to_source_plus_sidecar_ratio"], "0.919259")
            self.assertEqual(rows[5]["profile_id"], "d8_eight_head_seq8")
            self.assertEqual(rows[5]["source_plus_sidecar_raw_proof_bytes"], "74086")
            self.assertEqual(rows[5]["fused_to_source_plus_sidecar_ratio"], "0.801433")
            self.assertEqual(rows[6]["profile_id"], "d8_sixteen_head_seq8")
            self.assertEqual(rows[6]["source_plus_sidecar_raw_proof_bytes"], "88711")
            self.assertEqual(rows[6]["fused_to_source_plus_sidecar_ratio"], "0.732784")
            self.assertEqual(rows[8]["profile_id"], "d8_two_head_seq32")
            self.assertEqual(rows[8]["source_plus_sidecar_raw_proof_bytes"], "98012")
            self.assertEqual(rows[8]["fused_to_source_plus_sidecar_ratio"], "0.676723")
            self.assertEqual(rows[9]["profile_id"], "d16_two_head_seq8")
            self.assertEqual(rows[9]["source_plus_sidecar_raw_proof_bytes"], "91596")
            self.assertEqual(rows[9]["fused_to_source_plus_sidecar_ratio"], "0.853869")
            self.assertEqual(rows[10]["profile_id"], "d32_two_head_seq8")
            self.assertEqual(rows[10]["source_plus_sidecar_raw_proof_bytes"], "142063")
            self.assertEqual(rows[10]["fused_to_source_plus_sidecar_ratio"], "0.885213")
            self.assertEqual(rows[11]["profile_id"], "d16_two_head_seq16")
            self.assertEqual(rows[11]["source_plus_sidecar_raw_proof_bytes"], "108158")
            self.assertEqual(rows[11]["fused_to_source_plus_sidecar_ratio"], "0.784667")
            self.assertEqual(rows[12]["profile_id"], "d16_two_head_seq32")
            self.assertEqual(rows[12]["source_plus_sidecar_raw_proof_bytes"], "127207")
            self.assertEqual(rows[12]["fused_to_source_plus_sidecar_ratio"], "0.726084")
            self.assertEqual(rows[13]["profile_id"], "d32_two_head_seq16")
            self.assertEqual(rows[13]["source_plus_sidecar_raw_proof_bytes"], "162138")
            self.assertEqual(rows[13]["fused_to_source_plus_sidecar_ratio"], "0.81747")
            self.assertEqual(rows[14]["profile_id"], "d32_four_head_seq16")
            self.assertEqual(rows[14]["source_plus_sidecar_raw_proof_bytes"], "170018")
            self.assertEqual(rows[14]["fused_to_source_plus_sidecar_ratio"], "0.83717")
            self.assertEqual(rows[15]["profile_id"], "d32_two_head_seq32")
            self.assertEqual(rows[15]["source_plus_sidecar_raw_proof_bytes"], "176473")
            self.assertEqual(rows[15]["fused_to_source_plus_sidecar_ratio"], "0.850821")
            self.assertEqual(rows[16]["profile_id"], "d32_four_head_seq32")
            self.assertEqual(rows[16]["source_plus_sidecar_raw_proof_bytes"], "192937")
            self.assertEqual(rows[16]["fused_to_source_plus_sidecar_ratio"], "0.801661")
            self.assertEqual(rows[17]["profile_id"], "d64_two_head_seq16")
            self.assertEqual(rows[17]["source_plus_sidecar_raw_proof_bytes"], "257725")
            self.assertEqual(rows[17]["fused_to_source_plus_sidecar_ratio"], "0.925421")
            self.assertEqual(rows[18]["profile_id"], "d64_two_head_seq32")
            self.assertEqual(rows[18]["source_plus_sidecar_raw_proof_bytes"], "285102")
            self.assertEqual(rows[18]["fused_to_source_plus_sidecar_ratio"], "0.888303")


if __name__ == "__main__":
    unittest.main()
