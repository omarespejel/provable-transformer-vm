#!/usr/bin/env python3.10
"""Gate the d128 seq32 attention-derived MLP single proof result."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import os
import pathlib
import stat
import sys
import tempfile
from typing import Any, Callable


if sys.version_info < (3, 10):
    raise RuntimeError("zkai_native_d128_seq32_attention_derived_mlp_single_proof_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"

INPUT_PATH = EVIDENCE_DIR / "zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05.input.json"
ENVELOPE_PATH = EVIDENCE_DIR / "zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05.envelope.json"
SINGLE_ACCOUNTING_PATH = (
    EVIDENCE_DIR / "zkai-native-d128-seq32-attention-derived-mlp-single-proof-binary-accounting-2026-05.json"
)
SPLIT_ACCOUNTING_PATH = (
    EVIDENCE_DIR / "zkai-native-d128-seq32-attention-derived-mlp-split-frontier-binary-accounting-2026-05.json"
)
MLP_SURFACE_PATH = EVIDENCE_DIR / "zkai-d128-attention-derived-d128-native-mlp-surface-2026-05.json"

JSON_OUT = EVIDENCE_DIR / "zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05.tsv"
MD_OUT = ROOT / "docs" / "engineering" / "zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05-24.md"

SCHEMA = "zkai-native-d128-seq32-attention-derived-mlp-single-proof-gate-v1"
DECISION = "GO_D128_SEQ32_ATTENTION_DERIVED_MLP_SINGLE_PROOF_BEATS_MATCHED_SPLIT_FRONTIER"
RESULT = "D128_ATTENTION_DERIVED_SINGLE_PROOF_SAVES_18913_JSON_AND_5168_TYPED_BYTES"
PAYLOAD_DOMAIN = "ptvm:zkai:native-d128-seq32-attention-derived-mlp-single-proof-gate:v1"
ISSUE = 715

ADAPTER_MODE = "d128_attention_derived_duplicate_base_preprocessed_v1"
TARGET_ID = "attention-kv-d128-two-head-seq32-fused-softmax-table-plus-d128-attention-derived-d128-rmsnorm-mlp-v1"
SEMANTIC_SCOPE = (
    "d128_two_head_seq32_attention_softmax_table_public_adapter_and_d128_attention_derived_d128_"
    "rmsnorm_mlp_surfaces_in_one_native_stwo_proof_object"
)
STATEMENT_COMMITMENT = "blake2b-256:9e8a8be8deaa111526e38f501bcf2ccc8ee15e045e3cbd3638ebaf34535ce8ef"
PUBLIC_INSTANCE_COMMITMENT = "blake2b-256:85b257741d49fe8684992efccfb1db72e7eed81366da3d90de0e70c1893b04e5"
MLP_INPUT_ACTIVATION_COMMITMENT = "blake2b-256:086f65c7f1a79ef3ba1b56a51479bff381ef21efb49b6a5fa7b06156191d07ca"

SINGLE_PROOF_JSON_BYTES = 503_567
SINGLE_TYPED_BYTES = 204_564
SINGLE_ENVELOPE_JSON_BYTES = 25_401_065
SINGLE_INPUT_JSON_BYTES = 18_751_390
MAX_SINGLE_INPUT_JSON_BYTES = 32 * 1024 * 1024
MAX_SINGLE_ENVELOPE_JSON_BYTES = 32 * 1024 * 1024
MAX_ACCOUNTING_JSON_BYTES = 1 * 1024 * 1024
MAX_MLP_SURFACE_JSON_BYTES = 1 * 1024 * 1024
SPLIT_PROOF_JSON_BYTES = 522_480
SPLIT_TYPED_BYTES = 209_732
PROOF_JSON_SAVING_BYTES = 18_913
TYPED_SAVING_BYTES = 5_168
PROOF_JSON_RATIO = "0.963801"
TYPED_RATIO = "0.975359"

NON_CLAIMS = (
    "not a full transformer block proof",
    "not proving a learned attention-to-MLP projection",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not exact real-valued Softmax",
    "not full autoregressive inference",
    "not timing evidence",
    "not production-ready zkML",
)

VALIDATION_COMMANDS = (
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_d128_seq32_attention_mlp_single_proof -- build-input-model-faithful docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-d128-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_d128_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05.input.json docs/engineering/evidence/zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_d128_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05.envelope.json > docs/engineering/evidence/zkai-native-d128-seq32-attention-derived-mlp-single-proof-binary-accounting-2026-05.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-attention-kv-stwo-native-d128-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json docs/engineering/evidence/zkai-d128-attention-derived-d128-rmsnorm-mlp-fused-proof-2026-05.envelope.json > docs/engineering/evidence/zkai-native-d128-seq32-attention-derived-mlp-split-frontier-binary-accounting-2026-05.json",
    "python3.10 scripts/zkai_native_d128_seq32_attention_derived_mlp_single_proof_gate.py --write-json docs/engineering/evidence/zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05.tsv --write-md docs/engineering/zkai-native-d128-seq32-attention-derived-mlp-single-proof-2026-05-24.md",
    "python3.10 -m py_compile scripts/zkai_native_d128_seq32_attention_derived_mlp_single_proof_gate.py scripts/tests/test_zkai_native_d128_seq32_attention_derived_mlp_single_proof_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_native_d128_seq32_attention_derived_mlp_single_proof_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend native_d128_seq32_attention_mlp_single_proof --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
)


class NativeD128Seq32AttentionDerivedMlpSingleProofGateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    digest = hashlib.blake2b(digest_size=32)
    digest.update(PAYLOAD_DOMAIN.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(material))
    return "blake2b-256:" + digest.hexdigest()


def read_repo_file(path: pathlib.Path, label: str, max_bytes: int | None = None) -> bytes:
    root = ROOT.resolve()
    candidate = pathlib.Path(os.path.abspath(path if path.is_absolute() else ROOT / path))
    try:
        relative = candidate.relative_to(root)
    except ValueError as err:
        raise NativeD128Seq32AttentionDerivedMlpSingleProofGateError(f"{label} escapes repo root: {path}") from err
    current = root
    try:
        for part in relative.parts:
            current = current / part
            if stat.S_ISLNK(current.lstat().st_mode):
                raise NativeD128Seq32AttentionDerivedMlpSingleProofGateError(f"{label} must not traverse symlinks")
        fd = os.open(candidate, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            file_stat = os.fstat(fd)
            if not stat.S_ISREG(file_stat.st_mode):
                raise NativeD128Seq32AttentionDerivedMlpSingleProofGateError(f"{label} must be a regular file")
            if max_bytes is not None and file_stat.st_size > max_bytes:
                raise NativeD128Seq32AttentionDerivedMlpSingleProofGateError(
                    f"{label} exceeds max size: got {file_stat.st_size} bytes, limit {max_bytes} bytes"
                )
            with os.fdopen(fd, "rb") as handle:
                fd = None
                raw = handle.read() if max_bytes is None else handle.read(max_bytes + 1)
                if max_bytes is not None and len(raw) > max_bytes:
                    raise NativeD128Seq32AttentionDerivedMlpSingleProofGateError(
                        f"{label} exceeds max size: got more than {max_bytes} bytes, limit {max_bytes} bytes"
                    )
                return raw
        finally:
            if fd is not None:
                os.close(fd)
    except OSError as err:
        raise NativeD128Seq32AttentionDerivedMlpSingleProofGateError(f"failed to read {label}: {err}") from err


def read_json(path: pathlib.Path, label: str, max_bytes: int | None = None) -> tuple[dict[str, Any], bytes]:
    raw = read_repo_file(path, label, max_bytes)
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as err:
        raise NativeD128Seq32AttentionDerivedMlpSingleProofGateError(f"{label} is not valid JSON: {err}") from err
    if not isinstance(value, dict):
        raise NativeD128Seq32AttentionDerivedMlpSingleProofGateError(f"{label} must be a JSON object")
    return value, raw


def source_artifact_from_payload(artifact_id: str, path: pathlib.Path, payload: dict[str, Any], raw: bytes) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "path": path.relative_to(ROOT).as_posix(),
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "payload_sha256": hashlib.sha256(canonical_json_bytes(payload)).hexdigest(),
    }


SourceArtifactSpec = tuple[str, pathlib.Path, str, int | None]
LoadedSourceArtifact = tuple[dict[str, Any], bytes]


def source_artifact_specs() -> tuple[SourceArtifactSpec, ...]:
    return (
        ("single_input", INPUT_PATH, "single proof input", MAX_SINGLE_INPUT_JSON_BYTES),
        ("single_envelope", ENVELOPE_PATH, "single proof envelope", MAX_SINGLE_ENVELOPE_JSON_BYTES),
        ("single_accounting", SINGLE_ACCOUNTING_PATH, "single proof accounting", MAX_ACCOUNTING_JSON_BYTES),
        ("split_accounting", SPLIT_ACCOUNTING_PATH, "split frontier accounting", MAX_ACCOUNTING_JSON_BYTES),
        ("mlp_surface_gate", MLP_SURFACE_PATH, "attention-derived MLP surface gate", MAX_MLP_SURFACE_JSON_BYTES),
    )


def load_source_artifacts() -> tuple[dict[str, LoadedSourceArtifact], list[dict[str, Any]]]:
    loaded: dict[str, LoadedSourceArtifact] = {}
    artifacts = []
    for artifact_id, path, label, max_bytes in source_artifact_specs():
        payload, raw = read_json(path, label, max_bytes)
        loaded[artifact_id] = (payload, raw)
        artifacts.append(source_artifact_from_payload(artifact_id, path, payload, raw))
    return loaded, artifacts


def require(condition: bool, message: str) -> None:
    if not condition:
        raise NativeD128Seq32AttentionDerivedMlpSingleProofGateError(message)


def accounting_typed_bytes(accounting: dict[str, Any]) -> int:
    rows = accounting.get("rows")
    require(isinstance(rows, list) and len(rows) > 0, "accounting rows missing")
    return sum(int(row["local_binary_accounting"]["component_sum_bytes"]) for row in rows)


def build_payload() -> dict[str, Any]:
    loaded, source_artifacts = load_source_artifacts()
    input_payload, input_raw = loaded["single_input"]
    envelope_payload, envelope_raw = loaded["single_envelope"]
    single_accounting, _single_accounting_raw = loaded["single_accounting"]
    split_accounting, _split_accounting_raw = loaded["split_accounting"]
    mlp_surface, _mlp_surface_raw = loaded["mlp_surface_gate"]

    proof_json_bytes = len(envelope_payload["proof"])
    single_typed_bytes = accounting_typed_bytes(single_accounting)
    split_typed_bytes = accounting_typed_bytes(split_accounting)
    payload = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "issue": ISSUE,
        "route": {
            "adapter_mode": input_payload["adapter_mode"],
            "target_id": input_payload["target_id"],
            "semantic_scope": envelope_payload["semantic_scope"],
            "statement_commitment": input_payload["statement_commitment"],
            "public_instance_commitment": input_payload["public_instance_commitment"],
            "mlp_input_activation_commitment": input_payload["mlp_input_activation_commitment"],
        },
        "summary": {
            "single_proof_json_bytes": proof_json_bytes,
            "single_typed_bytes": single_typed_bytes,
            "single_envelope_json_bytes": len(envelope_raw),
            "single_input_json_bytes": len(input_raw),
            "split_proof_json_bytes": input_payload["current_two_proof_frontier_typed_bytes"],
            "split_typed_bytes": split_typed_bytes,
            "proof_json_saving_bytes": input_payload["current_two_proof_frontier_typed_bytes"] - proof_json_bytes,
            "typed_saving_bytes": split_typed_bytes - single_typed_bytes,
            "proof_json_ratio": f"{proof_json_bytes / input_payload['current_two_proof_frontier_typed_bytes']:.6f}",
            "typed_ratio": f"{single_typed_bytes / split_typed_bytes:.6f}",
            "proof_size_comparable_external_rows": 0,
            "nanozk_comparison_claim": False,
        },
        "mlp_surface_summary": {
            "fused_proof_json_bytes": mlp_surface["summary"]["fused_proof_json_bytes"],
            "fused_typed_bytes": mlp_surface["summary"]["fused_typed_bytes"],
            "separate_component_json_bytes": mlp_surface["summary"]["separate_component_json_bytes"],
            "separate_component_typed_bytes": mlp_surface["summary"]["separate_component_typed_bytes"],
        },
        "non_claims": list(NON_CLAIMS),
        "source_artifacts": source_artifacts,
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> None:
    require(payload.get("schema") == SCHEMA, "schema drift")
    require(payload.get("decision") == DECISION, "decision drift")
    require(payload.get("result") == RESULT, "result drift")
    route = payload.get("route")
    require(isinstance(route, dict), "route missing")
    require(route.get("adapter_mode") == ADAPTER_MODE, "adapter mode drift")
    require(route.get("target_id") == TARGET_ID, "target id drift")
    require(route.get("semantic_scope") == SEMANTIC_SCOPE, "semantic scope drift")
    require(route.get("statement_commitment") == STATEMENT_COMMITMENT, "statement commitment drift")
    require(route.get("public_instance_commitment") == PUBLIC_INSTANCE_COMMITMENT, "public instance drift")
    require(route.get("mlp_input_activation_commitment") == MLP_INPUT_ACTIVATION_COMMITMENT, "MLP input drift")

    summary = payload.get("summary")
    require(isinstance(summary, dict), "summary missing")
    expected_summary = {
        "single_proof_json_bytes": SINGLE_PROOF_JSON_BYTES,
        "single_typed_bytes": SINGLE_TYPED_BYTES,
        "single_envelope_json_bytes": SINGLE_ENVELOPE_JSON_BYTES,
        "single_input_json_bytes": SINGLE_INPUT_JSON_BYTES,
        "split_proof_json_bytes": SPLIT_PROOF_JSON_BYTES,
        "split_typed_bytes": SPLIT_TYPED_BYTES,
        "proof_json_saving_bytes": PROOF_JSON_SAVING_BYTES,
        "typed_saving_bytes": TYPED_SAVING_BYTES,
        "proof_json_ratio": PROOF_JSON_RATIO,
        "typed_ratio": TYPED_RATIO,
        "proof_size_comparable_external_rows": 0,
        "nanozk_comparison_claim": False,
    }
    for key, expected in expected_summary.items():
        require(summary.get(key) == expected, f"summary metric drift: {key}")
    require(payload.get("non_claims") == list(NON_CLAIMS), "non-claims drift")
    require(
        "not enforcing d128 MLP input derivation from attention outputs" not in payload["non_claims"],
        "legacy non-derivation caveat leaked into model-faithful route",
    )
    _loaded, expected_artifacts = load_source_artifacts()
    require(payload.get("source_artifacts") == expected_artifacts, "source artifact digest drift")
    require(payload.get("validation_commands") == list(VALIDATION_COMMANDS), "validation command drift")
    require(payload.get("payload_commitment") == payload_commitment(payload), "payload commitment drift")


Mutation = tuple[str, Callable[[dict[str, Any]], None]]


def mutation_cases() -> tuple[Mutation, ...]:
    return (
        ("proof_json_bytes", lambda p: p["summary"].__setitem__("single_proof_json_bytes", SINGLE_PROOF_JSON_BYTES + 1)),
        ("typed_bytes", lambda p: p["summary"].__setitem__("single_typed_bytes", SINGLE_TYPED_BYTES + 1)),
        ("target_id", lambda p: p["route"].__setitem__("target_id", TARGET_ID + "-mutated")),
        ("old_non_claim", lambda p: p["non_claims"].append("not enforcing d128 MLP input derivation from attention outputs")),
        ("external_overclaim", lambda p: p["summary"].__setitem__("nanozk_comparison_claim", True)),
        ("source_artifact_sha", lambda p: p["source_artifacts"][0].__setitem__("sha256", "0" * 64)),
        ("validation_command", lambda p: p["validation_commands"].append("echo unsafe")),
    )


def run_mutations(payload: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    base = build_payload() if payload is None else payload
    results = []
    for name, mutate in mutation_cases():
        candidate = copy.deepcopy(base)
        mutate(candidate)
        candidate["payload_commitment"] = payload_commitment(candidate)
        try:
            validate_payload(candidate)
        except NativeD128Seq32AttentionDerivedMlpSingleProofGateError as err:
            results.append({"name": name, "rejected": True, "error": str(err)})
        else:
            results.append({"name": name, "rejected": False, "error": None})
    return results


def atomic_write_text(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.is_symlink():
        raise NativeD128Seq32AttentionDerivedMlpSingleProofGateError(f"refusing to write through symlink: {path}")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        tmp_path = pathlib.Path(handle.name)
        handle.write(text)
    os.replace(tmp_path, path)


def write_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_tsv(path: pathlib.Path, payload: dict[str, Any]) -> None:
    columns = (
        "decision",
        "result",
        "single_proof_json_bytes",
        "split_proof_json_bytes",
        "proof_json_saving_bytes",
        "single_typed_bytes",
        "split_typed_bytes",
        "typed_saving_bytes",
        "proof_json_ratio",
        "typed_ratio",
        "statement_commitment",
        "target_id",
    )
    row = {
        "decision": payload["decision"],
        "result": payload["result"],
        "statement_commitment": payload["route"]["statement_commitment"],
        "target_id": payload["route"]["target_id"],
        **payload["summary"],
    }
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerow({column: row[column] for column in columns})
    atomic_write_text(path, buffer.getvalue())


def write_md(path: pathlib.Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    route = payload["route"]
    lines = [
        "# d128 seq32 attention-derived MLP single proof",
        "",
        f"- Decision: `{payload['decision']}`",
        f"- Target: `{route['target_id']}`",
        f"- Statement: `{route['statement_commitment']}`",
        f"- Public instance: `{route['public_instance_commitment']}`",
        f"- Proof JSON bytes: `{summary['single_proof_json_bytes']}` versus `{summary['split_proof_json_bytes']}` split",
        f"- Typed bytes: `{summary['single_typed_bytes']}` versus `{summary['split_typed_bytes']}` split",
        f"- Saving: `{summary['proof_json_saving_bytes']}` proof JSON bytes and `{summary['typed_saving_bytes']}` typed bytes",
        "",
        "This is still a scoped transformer surface, not a full block proof or an external zkML comparison.",
        "",
    ]
    atomic_write_text(path, "\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-json", type=pathlib.Path)
    parser.add_argument("--write-tsv", type=pathlib.Path)
    parser.add_argument("--write-md", type=pathlib.Path)
    args = parser.parse_args()

    payload = build_payload()
    mutations = run_mutations(payload)
    if not all(result["rejected"] for result in mutations):
        raise NativeD128Seq32AttentionDerivedMlpSingleProofGateError("mutation gate failed")
    payload["mutation_results"] = mutations
    payload["payload_commitment"] = payload_commitment(payload)
    validate_payload(payload)

    if args.write_json:
        write_json(args.write_json, payload)
    if args.write_tsv:
        write_tsv(args.write_tsv, payload)
    if args.write_md:
        write_md(args.write_md, payload)
    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "decision": DECISION,
                "result": RESULT,
                "proof_json_saving_bytes": PROOF_JSON_SAVING_BYTES,
                "typed_saving_bytes": TYPED_SAVING_BYTES,
                "mutations_rejected": len(mutations),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
