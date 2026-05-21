import copy
import json
import tempfile
import unittest

from scripts import zkai_attention_kv_d64_two_head_seq32_fused_softmax_table_native_gate as gate


class AttentionKvD64TwoHeadSeq32FusedSoftmaxTableNativeGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_input = gate.read_bounded_json(gate.SOURCE_INPUT_JSON, gate.MAX_SOURCE_INPUT_JSON_BYTES, "source input")
        cls.source_envelope, cls.source_raw = gate.read_sized_envelope(
            gate.SOURCE_ENVELOPE_JSON,
            gate.MAX_SOURCE_ENVELOPE_JSON_BYTES,
            gate.SOURCE_ENVELOPE_SIZE_BYTES,
            "source envelope",
        )
        cls.sidecar_envelope, cls.sidecar_raw = gate.read_sized_envelope(
            gate.SIDECAR_ENVELOPE_JSON,
            gate.MAX_SIDECAR_ENVELOPE_JSON_BYTES,
            gate.SIDECAR_ENVELOPE_SIZE_BYTES,
            "sidecar envelope",
        )
        cls.fused_envelope, cls.fused_raw = gate.read_sized_envelope(
            gate.FUSED_ENVELOPE_JSON,
            gate.MAX_FUSED_ENVELOPE_JSON_BYTES,
            gate.FUSED_ENVELOPE_SIZE_BYTES,
            "fused envelope",
        )
        cls.payload = gate.run_gate()

    def evidence_tempdir(self, prefix=".tmp-d64-seq32-fused-test-"):
        return tempfile.TemporaryDirectory(dir=gate.EVIDENCE_DIR, prefix=prefix)

    def test_gate_records_fused_go_and_byte_delta(self):
        payload = self.payload
        self.assertEqual(payload["decision"], gate.DECISION)
        self.assertEqual(payload["fusion_status"], gate.FUSION_STATUS)
        self.assertEqual(payload["lookup_claims"], 1184)
        self.assertEqual(payload["table_rows"], 9)
        self.assertEqual(payload["source_head_count"], 2)
        self.assertEqual(payload["source_proof_size_bytes"], 248702)
        self.assertEqual(payload["sidecar_proof_size_bytes"], 36400)
        self.assertEqual(payload["source_plus_sidecar_raw_proof_bytes"], 285102)
        self.assertEqual(payload["fused_proof_size_bytes"], 253257)
        self.assertEqual(payload["fused_over_source_proof_bytes"], 4555)
        self.assertEqual(payload["fused_saves_vs_source_plus_sidecar_bytes"], 31845)
        self.assertLess(payload["fused_to_source_plus_sidecar_ratio"], 0.89)
        self.assertTrue(payload["fused_envelope_commitment"].startswith("blake2b-256:"))
        self.assertTrue(payload["fused_proof_commitment"].startswith("blake2b-256:"))
        self.assertEqual(payload["mutations_checked"], len(gate.EXPECTED_MUTATION_NAMES))
        self.assertEqual(payload["mutations_rejected"], len(gate.EXPECTED_MUTATION_NAMES))

    def test_fused_envelope_commitment_binds_raw_envelope_bytes(self):
        compact = json.dumps(self.fused_envelope, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        pretty = json.dumps(self.fused_envelope, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
        self.assertNotEqual(compact, pretty)
        compact_envelope_commitment, compact_proof_commitment = gate.fused_artifact_commitments(
            self.fused_envelope, envelope_bytes=compact
        )
        pretty_envelope_commitment, pretty_proof_commitment = gate.fused_artifact_commitments(
            self.fused_envelope, envelope_bytes=pretty
        )
        self.assertNotEqual(compact_envelope_commitment, pretty_envelope_commitment)
        self.assertEqual(compact_proof_commitment, pretty_proof_commitment)

    def test_fused_envelope_commitment_rejects_bytes_dict_split_brain(self):
        mutated = copy.deepcopy(self.fused_envelope)
        mutated["decision"] = "GO_RELABELED_FUSED"
        mutated_raw = json.dumps(mutated, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
        with self.assertRaisesRegex(
            gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
            "fused envelope commitment bytes/dict split-brain drift",
        ):
            gate.fused_artifact_commitments(self.fused_envelope, envelope_bytes=mutated_raw)

    def test_fused_envelope_commitment_rejects_int_bool_split_brain(self):
        envelope = {"lookup_claims": 1, "proof": []}
        bool_drift_raw = b'{"lookup_claims":true,"proof":[]}'
        self.assertEqual(json.loads(bool_drift_raw), envelope)
        with self.assertRaisesRegex(
            gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
            "fused envelope commitment bytes/dict split-brain drift",
        ):
            gate.fused_artifact_commitments(envelope, envelope_bytes=bool_drift_raw)

    def test_fused_summary_counts_table_multiplicities(self):
        summary = self.fused_envelope["fused_summary"]
        self.assertEqual(summary, gate.expected_summary(self.source_input))
        self.assertEqual(sum(row["multiplicity"] for row in summary["table_multiplicities"]), 1184)
        self.assertEqual(summary["table_multiplicities"][-1]["gap"], 8)
        self.assertEqual(summary["table_multiplicities"][-1]["multiplicity"], 1107)

    def test_all_declared_mutations_reject(self):
        for name, mutated, run_native in gate.mutation_cases(self.fused_envelope):
            with self.assertRaises(gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError, msg=name):
                gate.validate_fused_envelope(mutated, self.source_input, run_native=run_native)

    def test_rejects_sidecar_or_source_proof_injection(self):
        for key in ("sidecar_proof", "source_proof"):
            mutated = copy.deepcopy(self.fused_envelope)
            mutated[key] = []
            with self.assertRaisesRegex(gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError, "unknown fused envelope field"):
                gate.validate_fused_envelope(mutated, self.source_input, run_native=False)

    def test_rejects_source_input_split_brain(self):
        mutated = copy.deepcopy(self.fused_envelope)
        mutated["source_input"]["score_rows"][0]["attention_weight"] = 255
        with self.assertRaisesRegex(gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError, "source input split-brain"):
            gate.validate_fused_envelope(mutated, self.source_input, run_native=False)

    def same_digit_mutation(self, value):
        return gate.same_digit_int_mutation(value, "test proof byte")

    def test_native_verifier_rejects_same_size_tampered_proof_payload(self):
        envelope = copy.deepcopy(self.fused_envelope)
        proof_payload = json.loads(bytes(envelope["proof"]).decode("utf-8"))
        commitments = proof_payload["stark_proof"]["commitments"]
        commitments[0][0] = self.same_digit_mutation(commitments[0][0])
        proof_bytes = json.dumps(proof_payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.assertEqual(len(proof_bytes), len(envelope["proof"]))
        envelope["proof"] = list(proof_bytes)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
            json.dump(envelope, tmp, indent=2)
            tmp_path = gate.pathlib.Path(tmp.name)
        try:
            with self.assertRaisesRegex(
                gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
                "native fused verifier rejected",
            ):
                gate.verify_fused_envelope_bytes_with_native_cli(tmp_path.read_bytes(), str(tmp_path))
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_source_artifact_validation_rejects_same_size_source_proof_tamper(self):
        source_envelope = copy.deepcopy(self.source_envelope)
        gate.mutate_same_size_stark_proof_commitment(source_envelope)
        source_raw = json.dumps(source_envelope, indent=2, ensure_ascii=False).encode("utf-8")
        self.assertEqual(len(source_raw), len(self.source_raw))
        with self.assertRaisesRegex(
            gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
            "native source verifier rejected artifact",
        ):
            gate.validate_source_artifacts(
                self.source_input,
                source_envelope,
                self.sidecar_envelope,
                source_envelope_bytes=source_raw,
                sidecar_envelope_bytes=self.sidecar_raw,
            )

    def test_source_artifact_validation_rejects_same_size_sidecar_proof_tamper(self):
        sidecar_envelope = copy.deepcopy(self.sidecar_envelope)
        gate.mutate_same_size_stark_proof_commitment(sidecar_envelope)
        sidecar_raw = json.dumps(sidecar_envelope, indent=2, ensure_ascii=False).encode("utf-8")
        self.assertEqual(len(sidecar_raw), len(self.sidecar_raw))
        with self.assertRaisesRegex(
            gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
            "native sidecar verifier rejected artifact",
        ):
            gate.validate_source_artifacts(
                self.source_input,
                self.source_envelope,
                sidecar_envelope,
                source_envelope_bytes=self.source_raw,
                sidecar_envelope_bytes=sidecar_raw,
            )

    def test_native_verifier_cache_still_checks_expected_summary(self):
        expected = {
            "mode": "verify",
            "verified": True,
            "proof_size_bytes": gate.SOURCE_PROOF_SIZE_BYTES,
            "envelope_size_bytes": len(self.source_raw),
            "statement_commitment": gate.SOURCE_STATEMENT_COMMITMENT,
            "score_row_count": gate.SOURCE_SCORE_ROWS,
            "trace_row_count": gate.SOURCE_TRACE_ROWS,
        }
        gate.verify_envelope_bytes_with_native_cli(
            self.source_raw,
            "source cache seed",
            max_bytes=gate.MAX_SOURCE_ENVELOPE_JSON_BYTES,
            binary="zkai_attention_kv_native_d64_two_head_seq32_bounded_softmax_table_proof",
            expected_summary=expected,
        )
        wrong_expected = copy.deepcopy(expected)
        wrong_expected["proof_size_bytes"] = gate.SOURCE_PROOF_SIZE_BYTES + 1
        with self.assertRaisesRegex(
            gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
            "native source cache replay verifier summary drift for proof_size_bytes",
        ):
            gate.verify_envelope_bytes_with_native_cli(
                self.source_raw,
                "source cache replay",
                max_bytes=gate.MAX_SOURCE_ENVELOPE_JSON_BYTES,
                binary="zkai_attention_kv_native_d64_two_head_seq32_bounded_softmax_table_proof",
                expected_summary=wrong_expected,
            )

    def test_source_artifact_validation_rejects_unknown_source_or_sidecar_fields(self):
        source_envelope = copy.deepcopy(self.source_envelope)
        source_envelope["unexpected"] = "claim smuggling"
        source_raw = json.dumps(source_envelope, indent=2, ensure_ascii=False).encode("utf-8")
        with self.assertRaisesRegex(
            gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
            "source envelope field set drift",
        ):
            gate.validate_source_artifacts(
                self.source_input,
                source_envelope,
                self.sidecar_envelope,
                source_envelope_bytes=source_raw,
                sidecar_envelope_bytes=self.sidecar_raw,
            )

        sidecar_envelope = copy.deepcopy(self.sidecar_envelope)
        sidecar_envelope["unexpected"] = "claim smuggling"
        sidecar_raw = json.dumps(sidecar_envelope, indent=2, ensure_ascii=False).encode("utf-8")
        with self.assertRaisesRegex(
            gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
            "sidecar envelope field set drift",
        ):
            gate.validate_source_artifacts(
                self.source_input,
                self.source_envelope,
                sidecar_envelope,
                source_envelope_bytes=self.source_raw,
                sidecar_envelope_bytes=sidecar_raw,
            )

    def test_source_artifact_validation_rejects_unknown_lookup_summary_fields(self):
        sidecar_envelope = copy.deepcopy(self.sidecar_envelope)
        sidecar_envelope["lookup_summary"]["unexpected_metric"] = 1
        sidecar_raw = json.dumps(sidecar_envelope, indent=2, ensure_ascii=False).encode("utf-8")
        with self.assertRaisesRegex(
            gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
            "sidecar lookup summary field set drift",
        ):
            gate.validate_source_artifacts(
                self.source_input,
                self.source_envelope,
                sidecar_envelope,
                source_envelope_bytes=self.source_raw,
                sidecar_envelope_bytes=sidecar_raw,
            )

    def test_source_artifact_validation_binds_envelope_bytes_to_dicts(self):
        source_envelope = copy.deepcopy(self.source_envelope)
        source_envelope["decision"] = "GO_RELABELED_SOURCE"
        with self.assertRaisesRegex(
            gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
            "source envelope bytes/dict split-brain drift",
        ):
            gate.validate_source_artifacts(
                self.source_input,
                source_envelope,
                self.sidecar_envelope,
                source_envelope_bytes=self.source_raw,
                sidecar_envelope_bytes=self.sidecar_raw,
            )

        sidecar_envelope = copy.deepcopy(self.sidecar_envelope)
        sidecar_envelope["decision"] = "GO_RELABELED_SIDECAR"
        with self.assertRaisesRegex(
            gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
            "sidecar envelope bytes/dict split-brain drift",
        ):
            gate.validate_source_artifacts(
                self.source_input,
                self.source_envelope,
                sidecar_envelope,
                source_envelope_bytes=self.source_raw,
                sidecar_envelope_bytes=self.sidecar_raw,
            )

    def test_mutation_collection_does_not_swallow_runtime_bugs(self):
        original_validate = gate.validate_fused_envelope

        def raise_runtime_bug(*args, **kwargs):
            raise RuntimeError("synthetic validator bug")

        gate.validate_fused_envelope = raise_runtime_bug
        try:
            with self.assertRaisesRegex(RuntimeError, "synthetic validator bug"):
                gate.evaluate_mutation_results(self.fused_envelope, self.source_input)
        finally:
            gate.validate_fused_envelope = original_validate

    def test_gate_checks_source_sidecar_and_fused_envelope_byte_sizes(self):
        cases = (
            ("source envelope", gate.SOURCE_ENVELOPE_JSON, gate.SOURCE_ENVELOPE_SIZE_BYTES),
            ("sidecar envelope", gate.SIDECAR_ENVELOPE_JSON, gate.SIDECAR_ENVELOPE_SIZE_BYTES),
            ("fused envelope", gate.FUSED_ENVELOPE_JSON, gate.FUSED_ENVELOPE_SIZE_BYTES),
        )
        for label, path, expected_size in cases:
            raw = path.read_bytes()
            self.assertEqual(len(raw), expected_size)
            with self.assertRaisesRegex(gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError, f"{label} size drift"):
                gate.expect_artifact_size(raw + b" ", expected_size, label)

    def test_write_json_and_tsv_round_trip(self):
        with self.evidence_tempdir() as tmp_dir:
            tmp_path = gate.pathlib.Path(tmp_dir)
            json_path = tmp_path / "gate.json"
            tsv_path = tmp_path / "gate.tsv"
            gate.write_json(json_path, self.payload)
            gate.write_tsv(tsv_path, self.payload)
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8"))["decision"], gate.DECISION)
            self.assertIn(gate.DECISION, tsv_path.read_text(encoding="utf-8"))
            self.assertIn("253257", tsv_path.read_text(encoding="utf-8"))

    def test_write_json_rejects_metric_drift(self):
        payload = copy.deepcopy(self.payload)
        payload["fused_proof_size_bytes"] += 1
        with self.evidence_tempdir() as tmp:
            with self.assertRaisesRegex(
                gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
                "result drift for fused_proof_size_bytes",
            ):
                gate.write_json(gate.pathlib.Path(tmp) / "bad.json", payload)

    def test_write_json_rejects_published_identity_drift(self):
        payload = copy.deepcopy(self.payload)
        payload["route_id"] = "different-route"
        with self.evidence_tempdir() as tmp:
            with self.assertRaisesRegex(
                gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
                "result drift for route_id",
            ):
                gate.write_json(gate.pathlib.Path(tmp) / "bad.json", payload)

    def test_write_json_rejects_mutation_result_shape_drift(self):
        payload = copy.deepcopy(self.payload)
        payload["mutation_results"][0]["rejected"] = False
        with self.evidence_tempdir() as tmp:
            with self.assertRaisesRegex(
                gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
                "mutation result rejection drift",
            ):
                gate.write_json(gate.pathlib.Path(tmp) / "bad.json", payload)

    def test_write_json_rejects_unknown_result_key(self):
        payload = copy.deepcopy(self.payload)
        payload["unexpected"] = "claim smuggling"
        with self.evidence_tempdir() as tmp:
            with self.assertRaisesRegex(
                gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
                "unknown result keys",
            ):
                gate.write_json(gate.pathlib.Path(tmp) / "bad.json", payload)

    def test_validate_result_rejects_non_object_payload(self):
        with self.assertRaisesRegex(
            gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
            "result must be an object",
        ):
            gate.validate_result([])

    def test_validate_result_rejects_extra_mutation_result_key(self):
        payload = copy.deepcopy(self.payload)
        payload["mutation_results"][0]["unexpected"] = "claim smuggling"
        with self.assertRaisesRegex(
            gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
            "mutation result schema drift",
        ):
            gate.validate_result(payload)

    def test_write_json_failure_preserves_existing_artifact(self):
        with self.evidence_tempdir() as tmp:
            path = gate.pathlib.Path(tmp) / "gate.json"
            gate.write_json(path, self.payload)
            original = path.read_text(encoding="utf-8")
            payload = copy.deepcopy(self.payload)
            payload["route_id"] = "different-route"
            with self.assertRaisesRegex(
                gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
                "result drift for route_id",
            ):
                gate.write_json(path, payload)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    @unittest.skipUnless(hasattr(gate.pathlib.Path, "symlink_to"), "symlink support required")
    def test_write_outputs_reject_leaf_symlink(self):
        with self.evidence_tempdir(prefix=".tmp-d64-seq32-fused-leaf-symlink-") as tmp:
            tmp_path = gate.pathlib.Path(tmp)
            target = tmp_path / "target.json"
            link = tmp_path / "gate.json"
            target.write_text("{}", encoding="utf-8")
            try:
                link.symlink_to(target)
            except OSError as err:
                self.skipTest(f"symlink creation unavailable: {err}")
            with self.assertRaisesRegex(
                gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
                "symlink components",
            ):
                gate.write_json(link, self.payload)

    @unittest.skipUnless(hasattr(gate.pathlib.Path, "symlink_to"), "symlink support required")
    def test_write_outputs_reject_parent_symlink(self):
        with self.evidence_tempdir(prefix=".tmp-d64-seq32-fused-symlink-") as tmp:
            tmp_path = gate.pathlib.Path(tmp)
            real_parent = tmp_path / "real-parent"
            real_parent.mkdir()
            link_parent = tmp_path / "linked-parent"
            try:
                link_parent.symlink_to(real_parent, target_is_directory=True)
            except OSError as err:
                self.skipTest(f"directory symlink creation unavailable: {err}")
            with self.assertRaisesRegex(
                gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
                "symlink components",
            ):
                gate.write_tsv(link_parent / "gate.tsv", self.payload)

    def test_write_outputs_reject_absolute_outside_evidence_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
                "stay inside evidence dir",
            ):
                gate.write_json(gate.pathlib.Path(tmp) / "gate.json", self.payload)

    def test_write_outputs_reject_relative_parent_traversal(self):
        with self.assertRaisesRegex(
            gate.AttentionKvD64TwoHeadSeq32FusedSoftmaxTableGateError,
            "stay inside evidence dir",
        ):
            gate.write_tsv(gate.pathlib.Path("docs/engineering/evidence/../gate.tsv"), self.payload)


if __name__ == "__main__":
    unittest.main()
