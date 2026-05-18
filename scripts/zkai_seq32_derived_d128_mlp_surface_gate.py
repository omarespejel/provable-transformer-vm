#!/usr/bin/env python3.10
"""Build and gate the seq32-derived d128 MLP surface.

This is a source-compatible successor to the d8 attention-derived d128 MLP
surface. It keeps the old artifacts intact and writes a separate seq32-derived
artifact family.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import sys
import tempfile
from typing import Any, Callable


if sys.version_info < (3, 10):
    raise RuntimeError("zkai_seq32_derived_d128_mlp_surface_gate requires Python 3.10+")

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "docs" / "engineering" / "evidence"

SEQ32_ATTENTION_JSON = (
    EVIDENCE_DIR / "zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json"
)
SEQ32_INPUT_JSON = EVIDENCE_DIR / "zkai-seq32-derived-d128-input-2026-05.json"
SEQ32_INPUT_TSV = EVIDENCE_DIR / "zkai-seq32-derived-d128-input-2026-05.tsv"
SEQ32_RMSNORM_JSON = EVIDENCE_DIR / "zkai-seq32-derived-d128-rmsnorm-public-row-2026-05.json"
SEQ32_RMSNORM_TSV = EVIDENCE_DIR / "zkai-seq32-derived-d128-rmsnorm-public-row-2026-05.tsv"
SEQ32_RMSNORM_PROOF_ENVELOPE = (
    EVIDENCE_DIR / "zkai-seq32-derived-d128-native-rmsnorm-public-row-proof-2026-05.envelope.json"
)
SEQ32_BRIDGE_JSON = (
    EVIDENCE_DIR / "zkai-seq32-derived-d128-native-rmsnorm-to-projection-bridge-proof-2026-05.json"
)
SEQ32_BRIDGE_TSV = (
    EVIDENCE_DIR / "zkai-seq32-derived-d128-native-rmsnorm-to-projection-bridge-proof-2026-05.tsv"
)
SEQ32_BRIDGE_ENVELOPE = (
    EVIDENCE_DIR / "zkai-seq32-derived-d128-native-rmsnorm-to-projection-bridge-proof-2026-05.envelope.json"
)
SEQ32_GATE_VALUE_JSON = (
    EVIDENCE_DIR / "zkai-seq32-derived-d128-native-gate-value-projection-proof-2026-05.json"
)
SEQ32_GATE_VALUE_TSV = (
    EVIDENCE_DIR / "zkai-seq32-derived-d128-native-gate-value-projection-proof-2026-05.tsv"
)
SEQ32_GATE_VALUE_ENVELOPE = (
    EVIDENCE_DIR / "zkai-seq32-derived-d128-native-gate-value-projection-proof-2026-05.envelope.json"
)
SEQ32_ACTIVATION_JSON = EVIDENCE_DIR / "zkai-seq32-derived-d128-native-activation-swiglu-proof-2026-05.json"
SEQ32_ACTIVATION_TSV = EVIDENCE_DIR / "zkai-seq32-derived-d128-native-activation-swiglu-proof-2026-05.tsv"
SEQ32_ACTIVATION_ENVELOPE = (
    EVIDENCE_DIR / "zkai-seq32-derived-d128-native-activation-swiglu-proof-2026-05.envelope.json"
)
SEQ32_DOWN_JSON = EVIDENCE_DIR / "zkai-seq32-derived-d128-native-down-projection-proof-2026-05.json"
SEQ32_DOWN_TSV = EVIDENCE_DIR / "zkai-seq32-derived-d128-native-down-projection-proof-2026-05.tsv"
SEQ32_DOWN_ENVELOPE = EVIDENCE_DIR / "zkai-seq32-derived-d128-native-down-projection-proof-2026-05.envelope.json"
SEQ32_RESIDUAL_JSON = EVIDENCE_DIR / "zkai-seq32-derived-d128-native-residual-add-proof-2026-05.json"
SEQ32_RESIDUAL_TSV = EVIDENCE_DIR / "zkai-seq32-derived-d128-native-residual-add-proof-2026-05.tsv"
SEQ32_RESIDUAL_ENVELOPE = EVIDENCE_DIR / "zkai-seq32-derived-d128-native-residual-add-proof-2026-05.envelope.json"
SEQ32_FUSED_INPUT_JSON = EVIDENCE_DIR / "zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json"
SEQ32_FUSED_ENVELOPE = EVIDENCE_DIR / "zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.envelope.json"
SEQ32_BINARY_ACCOUNTING_JSON = (
    EVIDENCE_DIR / "zkai-seq32-derived-d128-rmsnorm-mlp-fused-binary-accounting-2026-05.json"
)
JSON_OUT = EVIDENCE_DIR / "zkai-seq32-derived-d128-native-mlp-surface-2026-05.json"
TSV_OUT = EVIDENCE_DIR / "zkai-seq32-derived-d128-native-mlp-surface-2026-05.tsv"

COMPAT_PATH = ROOT / "scripts" / "zkai_larger_native_boundary_source_compatibility_gate.py"
RMSWRAP_PATH = ROOT / "scripts" / "zkai_attention_derived_d128_rmsnorm_public_row_gate.py"
BRIDGE_PATH = ROOT / "scripts" / "zkai_d128_rmsnorm_to_projection_bridge_input.py"
GATE_VALUE_PATH = ROOT / "scripts" / "zkai_d128_gate_value_projection_proof_input.py"
ACTIVATION_PATH = ROOT / "scripts" / "zkai_d128_activation_swiglu_proof_input.py"
DOWN_PATH = ROOT / "scripts" / "zkai_d128_down_projection_proof_input.py"
RESIDUAL_PATH = ROOT / "scripts" / "zkai_d128_residual_add_proof_input.py"

SCHEMA = "zkai-seq32-derived-d128-native-mlp-surface-gate-v1"
INPUT_SCHEMA = "zkai-seq32-derived-d128-input-gate-v1"
INPUT_DECISION = "GO_SEQ32_DERIVED_D128_INPUT_FIXTURE"
INPUT_RESULT = "GO_VALUE_CONNECTED_SEQ32_DERIVED_D128_INPUT_ARTIFACT"
DECISION = "GO_SEQ32_DERIVED_D128_MLP_SURFACE_INPUTS_READY_FOR_NATIVE_PROOF"
RESULT = "SEQ32_DERIVED_D128_MLP_SURFACE_REGENERATED_FROM_VALUE_COMPATIBLE_ATTENTION_OUTPUTS"
PAYLOAD_DOMAIN = "ptvm:zkai:seq32-derived-d128-mlp-surface:v1"

WIDTH = 128
EXPECTED_SEQ32_ATTENTION = {
    "schema": "zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-air-proof-input-v1",
    "decision": "GO_INPUT_FOR_STWO_NATIVE_ATTENTION_KV_TWO_HEAD_SEQ32_BOUNDED_SOFTMAX_TABLE_AIR_PROOF",
    "head_count": 2,
    "sequence_length": 32,
    "value_width": 8,
    "trace_row_count": 2048,
    "score_row_count": 1184,
    "outputs_commitment": "blake2b-256:893d7caa9d9ce54e43508c4890209805f24a7cba43d0951592e812de1dbcfd69",
    "statement_commitment": "blake2b-256:03267fbc084726c1249fbd6025cc3ec3fdc30214f7c75693810c5b72188ace55",
}

SEQ32_SOURCE_ATTENTION_STATEMENT = "blake2b-256:03267fbc084726c1249fbd6025cc3ec3fdc30214f7c75693810c5b72188ace55"
SEQ32_SOURCE_OUTPUTS = "blake2b-256:893d7caa9d9ce54e43508c4890209805f24a7cba43d0951592e812de1dbcfd69"
SEQ32_INPUT_ACTIVATION = "blake2b-256:f1145a876ece5ad4154ce254ae284d3c2f673d76db0ff74a7a48bf9e4cfa8223"
SEQ32_RMS_STMT = "blake2b-256:bfe0e37bd0830057018212ada60c1c3c6378d343fb97f0fb14a607b699b49d48"
SEQ32_RMS_PUB = "blake2b-256:ee8af8fb5bc69c8d0b965a156d2da636ba31cf848075ca663ee88e461cef8ecd"
SEQ32_RMS_PNP = "blake2b-256:9b100459335ec0b56e5dc72ef619f733fa0508fc168dc6a985c8cad17657df6a"
SEQ32_RMS_OUT = "blake2b-256:bee594cd2dd38e8e2d6eed98f41f74c756b18b44aab2840e79ec84e9ef9c0964"
SEQ32_BRIDGE_STMT = "blake2b-256:218a95a49c5038438f940f2bbbf72a502995c15120bace15b0baa823251b3288"
SEQ32_BRIDGE_PUB = "blake2b-256:9a0d9ab8a1dbf40cfac92554460941b4aab954417349e2412baa5d0ba714a680"
SEQ32_PROJECTION_INPUT = "blake2b-256:de110b5c13a34e16c97b08499cd076354944f4ef9ea721950ac462a53773e2cf"
SEQ32_GATE_VALUE_STMT = "blake2b-256:3b2122aa86c92194194b3a322321cb119f720c1657f629ebcb5835f153b95003"
SEQ32_GATE_VALUE_PUB = "blake2b-256:6fc1b1a31765cc0e4797ef65042d4e43bfb23f55a679a17bbbc65e3b949d7e6c"
SEQ32_GATE_OUT = "blake2b-256:3cfd9113f1ce6139d0181ea847a620b815e5a23a35a8355ec9dc5fba789ce669"
SEQ32_VALUE_OUT = "blake2b-256:b225b2b1a2a395bd12467970012d8ce10e106e888e5cfea66187b0039f3422d6"
SEQ32_GATE_VALUE_OUT = "blake2b-256:fd196bfda6f2e30012487fdc45e8a91cdcc8aa75bd8481f02318a3ef6a532d0c"
SEQ32_ACT_STMT = "blake2b-256:dea8ba820803d368c260a267fbb5c93584bade42b5200b6deb28fffaa37cb441"
SEQ32_ACT_PUB = "blake2b-256:ce264c51e6a568a1b632a60bc3c640ae395ceffb41b9c3f0a01aebae03687efc"
SEQ32_HIDDEN = "blake2b-256:0fdb6968a15701bafe8362bce37359677ab521863556952984bf7c0b9d540344"
SEQ32_DOWN_STMT = "blake2b-256:4b8ae8318c0a74ba251265527e3aa25ad62df16a57b5714b285a41b5708c76d3"
SEQ32_DOWN_PUB = "blake2b-256:74e827de64a586efe23692f7d4503e19187804525add71e23809a8482b8c3da3"
SEQ32_RESD = "blake2b-256:89af7b3b0f22f7f590d945ba659afa3fc0ef6d67cd982e31f87e1cf825f05efd"
SEQ32_DOWN_ROW = "blake2b-256:9961f7bffbcd959cf684b1656a597d07061bf107bd067955cd5f8bf8133e6ae3"
SEQ32_REMD_SHA = "90815085e4a5fbfa3bdf3cdc6a38c23a9b55f7a27bd127a78092a004974e7907"
SEQ32_RES_STMT = "blake2b-256:b775ed46ff4e4ff043a4c886667a9771bb71859a3ee9e7ed19d9925cc27dcf94"
SEQ32_RES_PUB = "blake2b-256:1454ebcfb035a3883f08b8aa2449d7c085f538857cd4700a80f687907e566424"
SEQ32_OUT_ACT = "blake2b-256:864505937d7fe562b549dacdb2143e2c8290c2757978a3dd4b2ebbf0a4696b98"
SEQ32_RES_ROW = "blake2b-256:eb0e783dd6b048c14f38ba6cef33f7f7ea40cb4604b375288986c45eafae93f3"
SEQ32_RES_PNP = "blake2b-256:96bbdb8923fb0c3984a531f31c0b22a13b256a24253669a48366f979e5e74044"

SEQ32_BRIDGE_COMMANDS = [
    "python3.10 scripts/zkai_seq32_derived_d128_mlp_surface_gate.py --write-inputs",
    "python3.10 -m unittest scripts.tests.test_zkai_seq32_derived_d128_mlp_surface_gate",
    "cargo +nightly-2025-07-14 test d128_native_rmsnorm_to_projection_bridge_proof --lib --features stwo-backend",
    "just gate-fast",
    "just gate",
]
SEQ32_GATE_VALUE_COMMANDS = [
    "python3.10 scripts/zkai_seq32_derived_d128_mlp_surface_gate.py --write-inputs",
    "python3.10 -m unittest scripts.tests.test_zkai_seq32_derived_d128_mlp_surface_gate",
    "cargo +nightly-2025-07-14 test d128_native_gate_value_projection_proof --lib --features stwo-backend",
    "just gate-fast",
    "just gate",
]
SEQ32_ACTIVATION_COMMANDS = [
    "python3.10 scripts/zkai_seq32_derived_d128_mlp_surface_gate.py --write-inputs",
    "python3.10 -m unittest scripts.tests.test_zkai_seq32_derived_d128_mlp_surface_gate",
    "cargo +nightly-2025-07-14 test d128_native_activation_swiglu_proof --lib --features stwo-backend",
    "just gate-fast",
    "just gate",
]
SEQ32_DOWN_COMMANDS = [
    "python3.10 scripts/zkai_seq32_derived_d128_mlp_surface_gate.py --write-inputs",
    "python3.10 -m unittest scripts.tests.test_zkai_seq32_derived_d128_mlp_surface_gate",
    "cargo +nightly-2025-07-14 test d128_native_down_projection_proof --lib --features stwo-backend",
    "just gate-fast",
    "just gate",
]
SEQ32_RESIDUAL_COMMANDS = [
    "python3.10 scripts/zkai_seq32_derived_d128_mlp_surface_gate.py --write-inputs",
    "python3.10 -m unittest scripts.tests.test_zkai_seq32_derived_d128_mlp_surface_gate",
    "cargo +nightly-2025-07-14 test d128_native_residual_add_proof --lib --features stwo-backend",
    "just gate-fast",
    "just gate",
]
VALIDATION_COMMANDS = [
    "python3.10 scripts/zkai_seq32_derived_d128_mlp_surface_gate.py --write-inputs --write-json docs/engineering/evidence/zkai-seq32-derived-d128-native-mlp-surface-2026-05.json --write-tsv docs/engineering/evidence/zkai-seq32-derived-d128-native-mlp-surface-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_seq32_derived_d128_mlp_surface_gate.py scripts/tests/test_zkai_seq32_derived_d128_mlp_surface_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_seq32_derived_d128_mlp_surface_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend d128_native_rmsnorm_mlp_fused_proof --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
]
SEQ32_FUSED_COMMANDS = [
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_d128_rmsnorm_mlp_fused_proof -- build-input docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-public-row-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-native-rmsnorm-to-projection-bridge-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-native-gate-value-projection-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-native-activation-swiglu-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-native-down-projection-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-native-residual-add-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_d128_rmsnorm_mlp_fused_proof -- prove docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_d128_rmsnorm_mlp_fused_proof -- verify docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.envelope.json",
    "python3.10 scripts/zkai_seq32_derived_d128_mlp_surface_gate.py --write-inputs --write-json docs/engineering/evidence/zkai-seq32-derived-d128-native-mlp-surface-2026-05.json --write-tsv docs/engineering/evidence/zkai-seq32-derived-d128-native-mlp-surface-2026-05.tsv",
    "python3.10 -m unittest scripts.tests.test_zkai_seq32_derived_d128_mlp_surface_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend d128_native_rmsnorm_mlp_fused_proof --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
]

EXPECTED_FUSED_JSON_BYTES = 74511
EXPECTED_FUSED_TYPED_BYTES = 24272
EXPECTED_SEPARATE_JSON_BYTES = 181194
EXPECTED_SEPARATE_TYPED_BYTES = 54336
EXPECTED_JSON_SAVING_BYTES = 106683
EXPECTED_TYPED_SAVING_BYTES = 30064
EXPECTED_FUSED_JSON_RATIO = 0.411222
EXPECTED_FUSED_TYPED_RATIO = 0.446702

NON_CLAIMS = [
    "not a full transformer block proof",
    "not attention plus MLP in one native proof object",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not timing evidence",
    "not production-ready zkML",
]

TSV_COLUMNS = (
    "decision",
    "result",
    "seq32_adapter_mismatches",
    "input_activation_commitment",
    "rmsnorm_statement_commitment",
    "fused_proof_json_bytes",
    "fused_typed_bytes",
    "separate_component_json_bytes",
    "separate_component_typed_bytes",
    "json_saving_bytes",
    "typed_saving_bytes",
    "source_attention_statement_commitment",
)


class Seq32DerivedD128MlpSurfaceError(ValueError):
    pass


def _load_module(path: pathlib.Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise Seq32DerivedD128MlpSurfaceError(f"failed to load helper module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


COMPAT = _load_module(COMPAT_PATH, "zkai_larger_native_boundary_source_compatibility_gate")
RMSWRAP = _load_module(RMSWRAP_PATH, "zkai_attention_derived_d128_rmsnorm_public_row_gate")
BRIDGE = _load_module(BRIDGE_PATH, "zkai_d128_rmsnorm_to_projection_bridge_input")
GATE_VALUE = _load_module(GATE_VALUE_PATH, "zkai_d128_gate_value_projection_proof_input")
ACTIVATION = _load_module(ACTIVATION_PATH, "zkai_d128_activation_swiglu_proof_input")
DOWN = _load_module(DOWN_PATH, "zkai_d128_down_projection_proof_input")
RESIDUAL = _load_module(RESIDUAL_PATH, "zkai_d128_residual_add_proof_input")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode(
        "utf-8"
    )


def pretty_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def blake2b_commitment(value: Any, domain: str) -> str:
    digest = hashlib.blake2b(digest_size=32)
    digest.update(domain.encode("utf-8"))
    digest.update(b"\0")
    digest.update(canonical_json_bytes(value))
    return f"blake2b-256:{digest.hexdigest()}"


def payload_commitment(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "payload_commitment"}
    return blake2b_commitment(material, PAYLOAD_DOMAIN)


def _dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise Seq32DerivedD128MlpSurfaceError(f"{label} must be object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise Seq32DerivedD128MlpSurfaceError(f"{label} must be list")
    return value


def _int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise Seq32DerivedD128MlpSurfaceError(f"{label} must be integer")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise Seq32DerivedD128MlpSurfaceError(f"{label} must be non-empty string")
    return value


def read_json(path: pathlib.Path, label: str) -> tuple[dict[str, Any], bytes]:
    candidate = path if path.is_absolute() else ROOT / path
    if candidate.is_symlink():
        raise Seq32DerivedD128MlpSurfaceError(f"{label} must not be a symlink: {path}")
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as err:
        raise Seq32DerivedD128MlpSurfaceError(f"{label} escapes repository: {path}") from err
    try:
        raw = resolved.read_bytes()
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as err:
        raise Seq32DerivedD128MlpSurfaceError(f"failed to read {label}: {err}") from err
    return _dict(payload, label), raw


def source_artifact(artifact_id: str, path: pathlib.Path, payload: Any, raw: bytes) -> dict[str, Any]:
    return {
        "id": artifact_id,
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "payload_sha256": hashlib.sha256(canonical_json_bytes(payload)).hexdigest(),
    }


def assert_expected_attention(attention: dict[str, Any]) -> None:
    for field, expected in EXPECTED_SEQ32_ATTENTION.items():
        if attention.get(field) != expected:
            raise Seq32DerivedD128MlpSurfaceError(f"seq32 attention field drift: {field}")


def derive_seq32_projection(attention: dict[str, Any]) -> tuple[list[dict[str, int]], list[int]]:
    assert_expected_attention(attention)
    flat = COMPAT.flat_attention_outputs(attention, "seq32_attention")
    if len(flat) != 512:
        raise Seq32DerivedD128MlpSurfaceError("seq32 attention flat cell count drift")
    projection = COMPAT.adapter_projection(flat, WIDTH)
    values = [row["output_q8"] for row in projection]
    if BRIDGE.sequence_commitment(values, BRIDGE.SOURCE_INPUT_ACTIVATION_DOMAIN) != SEQ32_INPUT_ACTIVATION:
        raise Seq32DerivedD128MlpSurfaceError("seq32 input activation commitment drift")
    return projection, values


def build_seq32_input_payload() -> dict[str, Any]:
    attention, raw = read_json(SEQ32_ATTENTION_JSON, "seq32 attention source")
    projection, values = derive_seq32_projection(attention)
    payload = {
        "schema": INPUT_SCHEMA,
        "decision": INPUT_DECISION,
        "result": INPUT_RESULT,
        "source_artifacts": [source_artifact("two_head_seq32_fused_attention", SEQ32_ATTENTION_JSON, attention, raw)],
        "adapter_policy": {
            "id": "fixed_public_two_source_q8_projection_v1",
            "primary_coeff": COMPAT.ADAPTER_PRIMARY_COEFF,
            "mix_coeff": COMPAT.ADAPTER_MIX_COEFF,
            "denominator": COMPAT.ADAPTER_DENOMINATOR,
            "target_rows": WIDTH,
            "source_flat_cells": 512,
        },
        "derived_input": {
            "width": WIDTH,
            "source_attention_statement_commitment": attention["statement_commitment"],
            "source_attention_outputs_commitment": attention["outputs_commitment"],
            "input_activation_commitment": SEQ32_INPUT_ACTIVATION,
            "values_q8": values,
            "adapter_rows": projection,
        },
        "summary": {
            "min_q8": min(values),
            "max_q8": max(values),
            "sum_q8": sum(values),
            "adapter_mismatches_against_self": 0,
        },
        "non_claims": [
            "not a learned model projection",
            "not a full transformer block proof",
            "not a NANOZK benchmark",
            "not proof-size evidence",
        ],
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    payload["payload_commitment"] = payload_commitment(payload)
    validate_seq32_input_payload(payload)
    return payload


def validate_seq32_input_payload(payload: Any) -> None:
    payload = _dict(payload, "seq32 input payload")
    expected_fields = {
        "schema",
        "decision",
        "result",
        "source_artifacts",
        "adapter_policy",
        "derived_input",
        "summary",
        "non_claims",
        "validation_commands",
        "payload_commitment",
    }
    if set(payload) != expected_fields:
        raise Seq32DerivedD128MlpSurfaceError("seq32 input field set drift")
    constants = {
        "schema": INPUT_SCHEMA,
        "decision": INPUT_DECISION,
        "result": INPUT_RESULT,
        "non_claims": payload["non_claims"],
        "validation_commands": VALIDATION_COMMANDS,
    }
    for field, expected in constants.items():
        if payload.get(field) != expected:
            raise Seq32DerivedD128MlpSurfaceError(f"seq32 input field drift: {field}")
    if payload["payload_commitment"] != payload_commitment(payload):
        raise Seq32DerivedD128MlpSurfaceError("seq32 input payload commitment drift")
    derived = _dict(payload.get("derived_input"), "derived input")
    values = [_int(value, f"derived_input.values_q8[{index}]") for index, value in enumerate(_list(derived.get("values_q8"), "values"))]
    if len(values) != WIDTH:
        raise Seq32DerivedD128MlpSurfaceError("seq32 input width drift")
    if derived.get("source_attention_statement_commitment") != SEQ32_SOURCE_ATTENTION_STATEMENT:
        raise Seq32DerivedD128MlpSurfaceError("seq32 source attention statement drift")
    if derived.get("source_attention_outputs_commitment") != SEQ32_SOURCE_OUTPUTS:
        raise Seq32DerivedD128MlpSurfaceError("seq32 source attention outputs drift")
    if BRIDGE.sequence_commitment(values, BRIDGE.SOURCE_INPUT_ACTIVATION_DOMAIN) != derived.get(
        "input_activation_commitment"
    ):
        raise Seq32DerivedD128MlpSurfaceError("seq32 derived values commitment drift")
    if derived.get("input_activation_commitment") != SEQ32_INPUT_ACTIVATION:
        raise Seq32DerivedD128MlpSurfaceError("seq32 input activation commitment drift")
    rows = _list(derived.get("adapter_rows"), "adapter rows")
    if len(rows) != WIDTH:
        raise Seq32DerivedD128MlpSurfaceError("seq32 adapter row count drift")
    for index, row_value in enumerate(rows):
        row = _dict(row_value, f"adapter row {index}")
        if _int(row.get("row_index"), "row_index") != index:
            raise Seq32DerivedD128MlpSurfaceError("seq32 adapter row index drift")
        if _int(row.get("output_q8"), "output_q8") != values[index]:
            raise Seq32DerivedD128MlpSurfaceError("seq32 adapter output drift")


def build_rmsnorm_wrapper(values: list[int]) -> dict[str, Any]:
    rmsnorm_payload = RMSWRAP.build_rmsnorm_payload_for_input(values)
    if rmsnorm_payload["statement_commitment"] != SEQ32_RMS_STMT:
        raise Seq32DerivedD128MlpSurfaceError("seq32 RMSNorm statement drift")
    payload = {
        "schema": RMSWRAP.SCHEMA,
        "decision": RMSWRAP.DECISION,
        "result": "GO_SEQ32_DERIVED_D128_RMSNORM_PUBLIC_ROW_INPUT",
        "claim_boundary": "CHECKED_D128_RMSNORM_PUBLIC_ROW_INPUT_CONSUMES_SEQ32_DERIVED_D128_VECTOR_NOT_FULL_BLOCK",
        "source_artifacts": [
            {
                "id": "seq32_derived_d128_input",
                "path": SEQ32_INPUT_JSON.relative_to(ROOT).as_posix(),
            }
        ],
        "source_summary": {
            "source_attention_statement_commitment": SEQ32_SOURCE_ATTENTION_STATEMENT,
            "source_attention_outputs_commitment": SEQ32_SOURCE_OUTPUTS,
            "derived_input_activation_commitment": SEQ32_INPUT_ACTIVATION,
            "seq32_adapter_mismatch_count": 0,
        },
        "rmsnorm_public_row_payload": rmsnorm_payload,
        "summary": {
            "row_count": WIDTH,
            "rms_q8": rmsnorm_payload["rms_q8"],
            "input_min_q8": min(values),
            "input_max_q8": max(values),
            "input_sum_q8": sum(values),
        },
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    payload["payload_commitment"] = payload_commitment(payload)
    return payload


def _add_bridge_anchor(module: Any, rmsnorm_payload: dict[str, Any]) -> None:
    module.APPROVED_SOURCE_ANCHORS.add((SEQ32_RMS_STMT, SEQ32_RMS_PUB, SEQ32_RMS_PNP, SEQ32_RMS_OUT))
    module.SOURCE_PAYLOAD_COMMANDS[(SEQ32_RMS_STMT, SEQ32_RMS_PUB, SEQ32_RMS_OUT)] = list(SEQ32_BRIDGE_COMMANDS)
    module.ALLOWED_VALIDATION_COMMANDS = tuple(list(module.ALLOWED_VALIDATION_COMMANDS) + [SEQ32_BRIDGE_COMMANDS])
    if rmsnorm_payload["statement_commitment"] != SEQ32_RMS_STMT:
        raise Seq32DerivedD128MlpSurfaceError("cannot add bridge anchor for non-seq32 RMSNorm payload")


def _add_gate_value_anchor(module: Any) -> None:
    anchor = {
        "kind": "seq32_derived",
        "statement_commitment": SEQ32_BRIDGE_STMT,
        "public_instance_commitment": SEQ32_BRIDGE_PUB,
        "projection_input_row_commitment": SEQ32_PROJECTION_INPUT,
        "validation_commands": list(SEQ32_GATE_VALUE_COMMANDS),
    }
    module.SOURCE_BRIDGE_ANCHORS = tuple(list(module.SOURCE_BRIDGE_ANCHORS) + [anchor])


def _add_activation_anchor(module: Any) -> None:
    anchor = {
        "kind": "seq32_derived",
        "statement_commitment": SEQ32_GATE_VALUE_STMT,
        "public_instance_commitment": SEQ32_GATE_VALUE_PUB,
        "gate_projection_output_commitment": SEQ32_GATE_OUT,
        "value_projection_output_commitment": SEQ32_VALUE_OUT,
        "gate_value_projection_output_commitment": SEQ32_GATE_VALUE_OUT,
        "validation_commands": list(SEQ32_ACTIVATION_COMMANDS),
    }
    module.SOURCE_GATE_VALUE_ANCHORS = tuple(list(module.SOURCE_GATE_VALUE_ANCHORS) + [anchor])


def _add_down_anchor(module: Any, placeholder: bool = False) -> dict[str, str | list[str]]:
    anchor: dict[str, str | list[str]] = {
        "kind": "seq32_derived",
        "statement_commitment": SEQ32_ACT_STMT,
        "public_instance_commitment": SEQ32_ACT_PUB,
        "hidden_activation_commitment": SEQ32_HIDDEN,
        "residual_delta_commitment": "TO_BE_FILLED" if placeholder else SEQ32_RESD,
        "residual_delta_remainder_sha256": "TO_BE_FILLED" if placeholder else SEQ32_REMD_SHA,
        "down_projection_mul_row_commitment": "TO_BE_FILLED" if placeholder else SEQ32_DOWN_ROW,
        "public_instance_commitment_out": "TO_BE_FILLED" if placeholder else SEQ32_DOWN_PUB,
        "statement_commitment_out": "TO_BE_FILLED" if placeholder else SEQ32_DOWN_STMT,
        "validation_commands": list(SEQ32_DOWN_COMMANDS),
    }
    module.SOURCE_ACTIVATION_ANCHORS = tuple(list(module.SOURCE_ACTIVATION_ANCHORS) + [anchor])
    return anchor


def patch_generation_anchors(rmsnorm_payload: dict[str, Any]) -> dict[str, Any]:
    _add_bridge_anchor(BRIDGE, rmsnorm_payload)
    for module in (GATE_VALUE, ACTIVATION.GATE_VALUE, DOWN.ACTIVATION_SWIGLU.GATE_VALUE, RESIDUAL.DOWN_PROJECTION.ACTIVATION_SWIGLU.GATE_VALUE):
        _add_gate_value_anchor(module)
    for module in (ACTIVATION, DOWN.ACTIVATION_SWIGLU, RESIDUAL.DOWN_PROJECTION.ACTIVATION_SWIGLU):
        _add_activation_anchor(module)
    down_anchor = _add_down_anchor(DOWN, placeholder=True)
    _add_down_anchor(RESIDUAL.DOWN_PROJECTION, placeholder=True)
    return down_anchor


def build_component_payloads() -> dict[str, dict[str, Any]]:
    seq32_input = build_seq32_input_payload()
    values = list(seq32_input["derived_input"]["values_q8"])
    rmsnorm_wrapper = build_rmsnorm_wrapper(values)
    rmsnorm_payload = rmsnorm_wrapper["rmsnorm_public_row_payload"]
    down_anchor = patch_generation_anchors(rmsnorm_payload)
    bridge_payload = BRIDGE.build_payload(rmsnorm_payload, validation_commands=list(SEQ32_BRIDGE_COMMANDS))
    gate_payload = GATE_VALUE.build_payload(bridge_payload)
    activation_payload = ACTIVATION.build_payload(gate_payload)
    down_payload = DOWN.build_payload(activation_payload)
    down_anchor.update(
        {
            "residual_delta_commitment": down_payload["residual_delta_commitment"],
            "residual_delta_remainder_sha256": SEQ32_REMD_SHA,
            "down_projection_mul_row_commitment": down_payload["down_projection_mul_row_commitment"],
            "public_instance_commitment_out": down_payload["public_instance_commitment"],
            "statement_commitment_out": down_payload["statement_commitment"],
        }
    )
    if down_payload["statement_commitment"] != SEQ32_DOWN_STMT:
        raise Seq32DerivedD128MlpSurfaceError("seq32 down-projection statement drift")
    rows = RESIDUAL.build_rows(values, down_payload["residual_delta_q8"])
    output_q8 = [row["output_q8"] for row in rows]
    residual_payload = {
        "schema": RESIDUAL.SCHEMA,
        "decision": RESIDUAL.DECISION,
        "target_id": RESIDUAL.TARGET_ID,
        "required_backend_version": RESIDUAL.REQUIRED_BACKEND_VERSION,
        "verifier_domain": RESIDUAL.VERIFIER_DOMAIN,
        "width": RESIDUAL.WIDTH,
        "row_count": RESIDUAL.WIDTH,
        "source_rmsnorm_proof_version": INPUT_SCHEMA,
        "source_rmsnorm_statement_commitment": SEQ32_SOURCE_ATTENTION_STATEMENT,
        "source_down_projection_proof_version": RESIDUAL.SOURCE_DOWN_PROJECTION_PROOF_VERSION,
        "source_down_projection_statement_commitment": down_payload["statement_commitment"],
        "source_down_projection_public_instance_commitment": down_payload["public_instance_commitment"],
        "range_policy": RESIDUAL.RANGE_POLICY,
        "input_activation_commitment": SEQ32_INPUT_ACTIVATION,
        "residual_delta_commitment": down_payload["residual_delta_commitment"],
        "residual_delta_scale_divisor": down_payload["residual_delta_scale_divisor"],
        "residual_delta_remainder_sha256": SEQ32_REMD_SHA,
        "output_activation_commitment": RESIDUAL.sequence_commitment(output_q8, RESIDUAL.OUTPUT_ACTIVATION_DOMAIN, [RESIDUAL.WIDTH]),
        "residual_add_row_commitment": RESIDUAL.rows_commitment(rows),
        "proof_native_parameter_commitment": RESIDUAL.proof_native_parameter_commitment(down_payload["statement_commitment"]),
        "public_instance_commitment": "",
        "statement_commitment": "",
        "input_q8": values,
        "residual_delta_q8": down_payload["residual_delta_q8"],
        "residual_delta_remainder_q8": down_payload["residual_delta_remainder_q8"],
        "output_q8": output_q8,
        "rows": rows,
        "non_claims": list(RESIDUAL.NON_CLAIMS),
        "proof_verifier_hardening": list(RESIDUAL.PROOF_VERIFIER_HARDENING),
        "next_backend_step": RESIDUAL.NEXT_BACKEND_STEP,
        "validation_commands": list(SEQ32_RESIDUAL_COMMANDS),
    }
    statement = RESIDUAL.statement_commitment(residual_payload)
    residual_payload["statement_commitment"] = statement
    residual_payload["public_instance_commitment"] = RESIDUAL.public_instance_commitment(statement)
    if residual_payload["statement_commitment"] != SEQ32_RES_STMT:
        raise Seq32DerivedD128MlpSurfaceError("seq32 residual-add statement drift")
    return {
        "seq32_input": seq32_input,
        "rmsnorm_wrapper": rmsnorm_wrapper,
        "bridge": bridge_payload,
        "gate_value": gate_payload,
        "activation": activation_payload,
        "down": down_payload,
        "residual": residual_payload,
    }


def _assert_output_path(path: pathlib.Path) -> pathlib.Path:
    candidate = path if path.is_absolute() else ROOT / path
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as err:
        raise Seq32DerivedD128MlpSurfaceError(f"output path escapes repository: {path}") from err
    if candidate.is_symlink():
        raise Seq32DerivedD128MlpSurfaceError(f"output path must not be a symlink: {path}")
    if resolved.exists() and resolved.is_dir():
        raise Seq32DerivedD128MlpSurfaceError(f"output path must not be a directory: {path}")
    return resolved


def atomic_write_text(path: pathlib.Path, text: str) -> None:
    resolved = _assert_output_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{resolved.name}.", suffix=".tmp", dir=resolved.parent)
    tmp_path = pathlib.Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, resolved)
    except BaseException:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise


def tsv_text(rows: list[dict[str, Any]], columns: tuple[str, ...]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(columns), delimiter="\t", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def write_inputs(payloads: dict[str, dict[str, Any]] | None = None) -> None:
    payloads = build_component_payloads() if payloads is None else payloads
    atomic_write_text(SEQ32_INPUT_JSON, pretty_json(payloads["seq32_input"]))
    atomic_write_text(
        SEQ32_INPUT_TSV,
        tsv_text(
            [
                {
                    "schema": INPUT_SCHEMA,
                    "decision": INPUT_DECISION,
                    "input_activation_commitment": SEQ32_INPUT_ACTIVATION,
                    "source_attention_statement_commitment": SEQ32_SOURCE_ATTENTION_STATEMENT,
                    "min_q8": payloads["seq32_input"]["summary"]["min_q8"],
                    "max_q8": payloads["seq32_input"]["summary"]["max_q8"],
                    "sum_q8": payloads["seq32_input"]["summary"]["sum_q8"],
                }
            ],
            (
                "schema",
                "decision",
                "input_activation_commitment",
                "source_attention_statement_commitment",
                "min_q8",
                "max_q8",
                "sum_q8",
            ),
        ),
    )
    atomic_write_text(SEQ32_RMSNORM_JSON, pretty_json(payloads["rmsnorm_wrapper"]))
    atomic_write_text(
        SEQ32_RMSNORM_TSV,
        tsv_text(
            [
                {
                    "schema": RMSWRAP.SCHEMA,
                    "decision": RMSWRAP.DECISION,
                    "input_activation_commitment": SEQ32_INPUT_ACTIVATION,
                    "statement_commitment": SEQ32_RMS_STMT,
                    "rmsnorm_output_row_commitment": SEQ32_RMS_OUT,
                }
            ],
            (
                "schema",
                "decision",
                "input_activation_commitment",
                "statement_commitment",
                "rmsnorm_output_row_commitment",
            ),
        ),
    )
    BRIDGE.write_outputs(payloads["bridge"], SEQ32_BRIDGE_JSON, SEQ32_BRIDGE_TSV)
    GATE_VALUE.write_outputs(payloads["gate_value"], SEQ32_GATE_VALUE_JSON, SEQ32_GATE_VALUE_TSV)
    ACTIVATION.write_outputs(payloads["activation"], SEQ32_ACTIVATION_JSON, SEQ32_ACTIVATION_TSV)
    DOWN.write_outputs(payloads["down"], SEQ32_DOWN_JSON, SEQ32_DOWN_TSV)
    atomic_write_text(SEQ32_RESIDUAL_JSON, pretty_json(payloads["residual"]))
    residual = payloads["residual"]
    atomic_write_text(
        SEQ32_RESIDUAL_TSV,
        tsv_text(
            [
                {
                    "target_id": residual["target_id"],
                    "decision": residual["decision"],
                    "width": residual["width"],
                    "row_count": residual["row_count"],
                    "source_rmsnorm_proof_version": residual["source_rmsnorm_proof_version"],
                    "source_down_projection_proof_version": residual["source_down_projection_proof_version"],
                    "input_activation_commitment": residual["input_activation_commitment"],
                    "residual_delta_commitment": residual["residual_delta_commitment"],
                    "residual_delta_scale_divisor": residual["residual_delta_scale_divisor"],
                    "residual_delta_remainder_sha256": residual["residual_delta_remainder_sha256"],
                    "output_activation_commitment": residual["output_activation_commitment"],
                    "residual_add_row_commitment": residual["residual_add_row_commitment"],
                    "range_policy": residual["range_policy"],
                    "residual_min": min(residual["residual_delta_q8"]),
                    "residual_max": max(residual["residual_delta_q8"]),
                    "output_min": min(residual["output_q8"]),
                    "output_max": max(residual["output_q8"]),
                    "residual_delta_relabels_full_output": str(
                        residual["residual_delta_commitment"] == residual["output_activation_commitment"]
                    ).lower(),
                    "input_relabels_output": str(
                        residual["input_activation_commitment"] == residual["output_activation_commitment"]
                    ).lower(),
                    "non_claims": json.dumps(residual["non_claims"], separators=(",", ":"), sort_keys=True),
                    "next_backend_step": residual["next_backend_step"],
                }
            ],
            RESIDUAL.TSV_COLUMNS,
        ),
    )


def proof_json_bytes(path: pathlib.Path) -> int:
    payload, _raw = read_json(path, path.name)
    proof = _list(payload.get("proof"), f"{path.name}.proof")
    return len(proof)


def accounting_typed_bytes(path: pathlib.Path, evidence_name: str) -> int | None:
    if not path.exists():
        return None
    payload, _raw = read_json(path, path.name)
    for row_value in _list(payload.get("rows"), "accounting rows"):
        row = _dict(row_value, "accounting row")
        if row.get("evidence_relative_path") == evidence_name:
            local = _dict(row.get("local_binary_accounting"), "local accounting")
            return _int(local.get("component_sum_bytes"), "component_sum_bytes")
    return None


def accounting_row(path: pathlib.Path, evidence_name: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload, _raw = read_json(path, path.name)
    for row_value in _list(payload.get("rows"), "accounting rows"):
        row = _dict(row_value, "accounting row")
        if row.get("evidence_relative_path") == evidence_name:
            return row
    return None


def summary_source_artifacts() -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for artifact_id, path, label in (
        ("seq32_attention_source", SEQ32_ATTENTION_JSON, "seq32 attention source"),
        ("seq32_derived_input", SEQ32_INPUT_JSON, "seq32 derived input"),
        ("seq32_derived_rmsnorm_wrapper", SEQ32_RMSNORM_JSON, "seq32 derived RMSNorm wrapper"),
    ):
        payload, raw = read_json(path, label)
        artifacts.append(source_artifact(artifact_id, path, payload, raw))
    return artifacts


def build_summary_payload() -> dict[str, Any]:
    payloads = build_component_payloads()
    accounting_rows = [
        accounting_row(SEQ32_BINARY_ACCOUNTING_JSON, path.name)
        for path in (
            SEQ32_FUSED_ENVELOPE,
            SEQ32_RMSNORM_PROOF_ENVELOPE,
            SEQ32_BRIDGE_ENVELOPE,
            SEQ32_GATE_VALUE_ENVELOPE,
            SEQ32_ACTIVATION_ENVELOPE,
            SEQ32_DOWN_ENVELOPE,
            SEQ32_RESIDUAL_ENVELOPE,
        )
    ]
    fused_row = accounting_rows[0]
    component_rows = [row for row in accounting_rows[1:] if row is not None]
    if fused_row is None or len(component_rows) != 6:
        raise Seq32DerivedD128MlpSurfaceError("seq32 fused accounting row set incomplete")
    fused_json_bytes = fused_row["proof_json_size_bytes"] if fused_row is not None else None
    fused_typed_bytes = (
        fused_row["local_binary_accounting"]["component_sum_bytes"] if fused_row is not None else None
    )
    separate_json_bytes = sum(row["proof_json_size_bytes"] for row in component_rows) if len(component_rows) == 6 else None
    separate_typed_bytes = (
        sum(row["local_binary_accounting"]["component_sum_bytes"] for row in component_rows)
        if len(component_rows) == 6
        else None
    )
    typed_saving_bytes = (
        separate_typed_bytes - fused_typed_bytes
        if separate_typed_bytes is not None and fused_typed_bytes is not None
        else None
    )
    json_saving_bytes = (
        separate_json_bytes - fused_json_bytes
        if separate_json_bytes is not None and fused_json_bytes is not None
        else None
    )
    payload = {
        "schema": SCHEMA,
        "decision": DECISION,
        "result": RESULT,
        "source_artifacts": summary_source_artifacts(),
        "summary": {
            "seq32_adapter_mismatches": 0,
            "input_activation_commitment": SEQ32_INPUT_ACTIVATION,
            "rmsnorm_statement_commitment": SEQ32_RMS_STMT,
            "bridge_statement_commitment": SEQ32_BRIDGE_STMT,
            "gate_value_statement_commitment": SEQ32_GATE_VALUE_STMT,
            "activation_statement_commitment": SEQ32_ACT_STMT,
            "down_statement_commitment": SEQ32_DOWN_STMT,
            "residual_statement_commitment": SEQ32_RES_STMT,
            "fused_proof_json_bytes": fused_json_bytes,
            "fused_typed_bytes": fused_typed_bytes,
            "separate_component_json_bytes": separate_json_bytes,
            "separate_component_typed_bytes": separate_typed_bytes,
            "json_saving_bytes": json_saving_bytes,
            "typed_saving_bytes": typed_saving_bytes,
            "fused_json_ratio": round(fused_json_bytes / separate_json_bytes, 6)
            if fused_json_bytes is not None and separate_json_bytes
            else None,
            "fused_typed_ratio": round(fused_typed_bytes / separate_typed_bytes, 6)
            if fused_typed_bytes is not None and separate_typed_bytes
            else None,
        },
        "interpretation": {
            "value_compatible_with_two_head_seq32_attention": True,
            "native_mlp_surface_regenerated": True,
            "native_larger_attention_mlp_boundary_exists": False,
            "nanozk_comparison_claim": False,
        },
        "non_claims": list(NON_CLAIMS),
        "validation_commands": list(VALIDATION_COMMANDS),
    }
    payload["payload_commitment"] = payload_commitment(payload)
    validate_summary_payload(payload, payloads)
    return payload


def validate_summary_payload(payload: Any, payloads: dict[str, dict[str, Any]] | None = None) -> None:
    payload = _dict(payload, "summary payload")
    if payload.get("schema") != SCHEMA:
        raise Seq32DerivedD128MlpSurfaceError("summary schema drift")
    if payload.get("decision") != DECISION:
        raise Seq32DerivedD128MlpSurfaceError("summary decision drift")
    if payload.get("result") != RESULT:
        raise Seq32DerivedD128MlpSurfaceError("summary result drift")
    if payload.get("non_claims") != NON_CLAIMS:
        raise Seq32DerivedD128MlpSurfaceError("summary non-claims drift")
    if payload.get("validation_commands") != VALIDATION_COMMANDS:
        raise Seq32DerivedD128MlpSurfaceError("summary validation commands drift")
    if payload.get("payload_commitment") != payload_commitment(payload):
        raise Seq32DerivedD128MlpSurfaceError("summary payload commitment drift")
    source_artifacts = _list(payload.get("source_artifacts"), "summary source artifacts")
    expected_source_ids = [
        "seq32_attention_source",
        "seq32_derived_input",
        "seq32_derived_rmsnorm_wrapper",
    ]
    if [artifact.get("id") for artifact in source_artifacts] != expected_source_ids:
        raise Seq32DerivedD128MlpSurfaceError("summary source artifact id drift")
    for artifact in source_artifacts:
        artifact_obj = _dict(artifact, "summary source artifact")
        for field in ("path", "sha256", "payload_sha256"):
            _string(artifact_obj.get(field), f"summary source artifact {field}")
    if source_artifacts != summary_source_artifacts():
        raise Seq32DerivedD128MlpSurfaceError("summary source artifact digest drift")
    summary = _dict(payload.get("summary"), "summary")
    if summary.get("seq32_adapter_mismatches") != 0:
        raise Seq32DerivedD128MlpSurfaceError("seq32 adapter mismatch drift")
    if summary.get("input_activation_commitment") != SEQ32_INPUT_ACTIVATION:
        raise Seq32DerivedD128MlpSurfaceError("summary input activation drift")
    expected_numbers = {
        "fused_proof_json_bytes": EXPECTED_FUSED_JSON_BYTES,
        "fused_typed_bytes": EXPECTED_FUSED_TYPED_BYTES,
        "separate_component_json_bytes": EXPECTED_SEPARATE_JSON_BYTES,
        "separate_component_typed_bytes": EXPECTED_SEPARATE_TYPED_BYTES,
        "json_saving_bytes": EXPECTED_JSON_SAVING_BYTES,
        "typed_saving_bytes": EXPECTED_TYPED_SAVING_BYTES,
        "fused_json_ratio": EXPECTED_FUSED_JSON_RATIO,
        "fused_typed_ratio": EXPECTED_FUSED_TYPED_RATIO,
    }
    for field, expected in expected_numbers.items():
        if summary.get(field) != expected:
            raise Seq32DerivedD128MlpSurfaceError(f"summary metric drift: {field}")
    interpretation = _dict(payload.get("interpretation"), "interpretation")
    if interpretation.get("native_larger_attention_mlp_boundary_exists") is not False:
        raise Seq32DerivedD128MlpSurfaceError("larger-boundary overclaim drift")
    if interpretation.get("nanozk_comparison_claim") is not False:
        raise Seq32DerivedD128MlpSurfaceError("NANOZK overclaim drift")
    if payloads is not None and payloads["residual"]["statement_commitment"] != SEQ32_RES_STMT:
        raise Seq32DerivedD128MlpSurfaceError("residual payload statement drift")


def write_summary(json_path: pathlib.Path | None, tsv_path: pathlib.Path | None) -> None:
    payload = build_summary_payload()
    if json_path is not None:
        atomic_write_text(json_path, pretty_json(payload))
    if tsv_path is not None:
        summary = payload["summary"]
        atomic_write_text(
            tsv_path,
            tsv_text(
                [
                    {
                        "decision": payload["decision"],
                        "result": payload["result"],
                        "seq32_adapter_mismatches": summary["seq32_adapter_mismatches"],
                        "input_activation_commitment": summary["input_activation_commitment"],
                        "rmsnorm_statement_commitment": summary["rmsnorm_statement_commitment"],
                        "fused_proof_json_bytes": summary["fused_proof_json_bytes"],
                        "fused_typed_bytes": summary["fused_typed_bytes"],
                        "separate_component_json_bytes": summary["separate_component_json_bytes"],
                        "separate_component_typed_bytes": summary["separate_component_typed_bytes"],
                        "json_saving_bytes": summary["json_saving_bytes"],
                        "typed_saving_bytes": summary["typed_saving_bytes"],
                        "source_attention_statement_commitment": SEQ32_SOURCE_ATTENTION_STATEMENT,
                    }
                ],
                TSV_COLUMNS,
            ),
        )


def mutation_inventory() -> list[tuple[str, Callable[[dict[str, Any]], None]]]:
    return [
        ("decision_promoted_to_overclaim", lambda payload: payload.__setitem__("decision", "GO_FULL_TRANSFORMER_BLOCK")),
        (
            "seq32_mismatch_drift",
            lambda payload: payload["summary"].__setitem__("seq32_adapter_mismatches", 1),
        ),
        (
            "native_larger_boundary_overclaim",
            lambda payload: payload["interpretation"].__setitem__("native_larger_attention_mlp_boundary_exists", True),
        ),
        (
            "typed_saving_metric_drift",
            lambda payload: payload["summary"].__setitem__("typed_saving_bytes", EXPECTED_TYPED_SAVING_BYTES - 1),
        ),
        (
            "source_artifact_digest_drift",
            lambda payload: payload["source_artifacts"][0].__setitem__("sha256", "0" * 64),
        ),
        (
            "nanozk_overclaim",
            lambda payload: payload["interpretation"].__setitem__("nanozk_comparison_claim", True),
        ),
        (
            "payload_commitment_drift",
            lambda payload: payload.__setitem__("payload_commitment", "blake2b-256:" + "00" * 32),
        ),
    ]


def run_mutations() -> dict[str, Any]:
    baseline = build_summary_payload()
    cases = []
    for name, mutate in mutation_inventory():
        candidate = copy.deepcopy(baseline)
        mutate(candidate)
        try:
            validate_summary_payload(candidate)
        except Exception as err:  # noqa: BLE001 - record rejection reason.
            cases.append({"name": name, "rejected": True, "reason": str(err)})
        else:
            cases.append({"name": name, "rejected": False, "reason": "accepted"})
    return {
        "case_count": len(cases),
        "all_mutations_rejected": all(case["rejected"] for case in cases),
        "cases": cases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-inputs", action="store_true")
    parser.add_argument("--write-json", type=pathlib.Path, default=None)
    parser.add_argument("--write-tsv", type=pathlib.Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payloads = build_component_payloads()
    if args.write_inputs:
        write_inputs(payloads)
    if args.write_json or args.write_tsv:
        write_summary(args.write_json, args.write_tsv)
    mutation_result = run_mutations()
    if not mutation_result["all_mutations_rejected"]:
        raise Seq32DerivedD128MlpSurfaceError("mutation inventory accepted an invalid payload")
    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "decision": DECISION,
                "seq32_adapter_mismatches": 0,
                "input_activation_commitment": SEQ32_INPUT_ACTIVATION,
                "residual_statement_commitment": SEQ32_RES_STMT,
                "mutations_rejected": mutation_result["case_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
