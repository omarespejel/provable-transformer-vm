use std::collections::BTreeSet;

use blake2::digest::{Update, VariableOutput};
use blake2::Blake2bVar;
use serde::{Deserialize, Serialize};
use stwo::core::air::{Component, Components};
use stwo::core::channel::{Blake2sM31Channel, Channel};
use stwo::core::fields::m31::BaseField;
use stwo::core::fields::qm31::SecureField;
use stwo::core::pcs::{CommitmentSchemeVerifier, PcsConfig};
use stwo::core::poly::circle::CanonicCoset;
use stwo::core::proof::StarkProof;
use stwo::core::vcs_lifted::blake2_merkle::{Blake2sM31MerkleChannel, Blake2sM31MerkleHasher};
use stwo::core::verifier::verify;
use stwo::core::ColumnVec;
use stwo::prover::backend::simd::column::BaseColumn;
use stwo::prover::backend::simd::SimdBackend;
use stwo::prover::poly::circle::{CircleEvaluation, PolyOps};
use stwo::prover::poly::{BitReversedOrder, NaturalOrder};
use stwo::prover::{prove, CommitmentSchemeProver, ComponentProver};
use stwo_constraint_framework::preprocessed_columns::PreProcessedColumnId;
use stwo_constraint_framework::{
    EvalAtRow, FrameworkComponent, FrameworkEval, TraceLocationAllocator,
};

use crate::error::{Result, VmError};
use crate::proof::StarkProofBackend;

use super::attention_kv_native_two_head_seq32_bounded_softmax_table_proof::ZkAiAttentionKvNativeTwoHeadSeq32BoundedSoftmaxTableProofInput;
use super::attention_kv_native_two_head_seq32_fused_softmax_table_proof::{
    zkai_attention_kv_native_two_head_seq32_fused_softmax_table_base_trace,
    zkai_attention_kv_native_two_head_seq32_fused_softmax_table_component_with_allocator,
    zkai_attention_kv_native_two_head_seq32_fused_softmax_table_interaction_trace,
    zkai_attention_kv_native_two_head_seq32_fused_softmax_table_preprocessed_column_ids,
    zkai_attention_kv_native_two_head_seq32_fused_softmax_table_preprocessed_trace,
    zkai_attention_kv_native_two_head_seq32_fused_softmax_table_summary,
    zkai_attention_kv_native_two_head_seq32_fused_softmax_table_validate_source_input,
    AttentionKvTwoHeadSeq32FusedSoftmaxTableRelation,
    ZkAiAttentionKvNativeTwoHeadSeq32FusedSoftmaxTableSummary,
    ZKAI_ATTENTION_KV_NATIVE_TWO_HEAD_SEQ32_FUSED_SOFTMAX_TABLE_PROOF_VERSION,
};
use super::d128_native_activation_swiglu_proof::{
    zkai_d128_activation_swiglu_component_with_allocator,
    zkai_d128_activation_swiglu_preprocessed_column_ids, zkai_d128_activation_swiglu_trace,
};
use super::d128_native_down_projection_proof::{
    zkai_d128_down_projection_component_with_allocator,
    zkai_d128_down_projection_preprocessed_column_ids, zkai_d128_down_projection_trace,
};
use super::d128_native_gate_value_projection_proof::{
    zkai_d128_gate_value_projection_component_with_allocator,
    zkai_d128_gate_value_projection_preprocessed_column_ids, zkai_d128_gate_value_projection_rows,
    zkai_d128_gate_value_projection_trace,
};
use super::d128_native_residual_add_proof::{
    zkai_d128_residual_add_component_with_allocator,
    zkai_d128_residual_add_preprocessed_column_ids, zkai_d128_residual_add_trace,
};
use super::d128_native_rmsnorm_mlp_fused_proof::{
    zkai_d128_rmsnorm_mlp_fused_validate_input, ZkAiD128RmsnormMlpFusedInput,
    ZKAI_D128_RMSNORM_MLP_FUSED_PROOF_VERSION,
};
use super::d128_native_rmsnorm_public_row_proof::{
    zkai_d128_rmsnorm_public_row_component_with_optional_input_adapter_allocator,
    zkai_d128_rmsnorm_public_row_preprocessed_column_ids, zkai_d128_rmsnorm_public_row_trace,
    ZkAiD128RmsnormInputAdapterBinding,
};
use super::d128_native_rmsnorm_to_projection_bridge_proof::{
    zkai_d128_rmsnorm_to_projection_bridge_component_with_allocator,
    zkai_d128_rmsnorm_to_projection_bridge_preprocessed_column_ids,
    zkai_d128_rmsnorm_to_projection_bridge_trace,
};
use super::{publication_v1_pcs_config, publication_v1_pcs_config_matches};

pub const ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_INPUT_SCHEMA: &str =
    "zkai-native-seq32-attention-mlp-single-proof-object-input-v1";
pub const ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_INPUT_DECISION: &str =
    "GO_INPUT_FOR_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_OBJECT_PROBE";
pub const ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_BACKEND_VERSION: &str =
    "stwo-native-seq32-attention-mlp-single-proof-object-native-adapter-v1";
pub const ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_PROOF_VERSION: &str =
    "stwo-native-seq32-attention-mlp-single-proof-object-native-adapter-payload-v1";
pub const ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_STATEMENT_VERSION: &str =
    "zkai-native-seq32-attention-mlp-single-proof-object-native-adapter-statement-v1";
pub const ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_SEMANTIC_SCOPE: &str =
    "two_head_seq32_attention_softmax_table_attention_to_d128_adapter_and_seq32_derived_d128_rmsnorm_mlp_surfaces_in_one_native_stwo_proof_object";
pub const ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_DECISION: &str =
    "GO_SINGLE_NATIVE_STWO_PROOF_OBJECT_WITH_NATIVE_SEQ32_ATTENTION_TO_D128_ADAPTER_AIR";
pub const ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_ROUTE_ID: &str =
    "native_stwo_two_head_seq32_attention_softmax_table_plus_seq32_derived_d128_rmsnorm_mlp_single_proof_object_probe";
pub const ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_TARGET_ID: &str =
    "attention-kv-two-head-seq32-fused-softmax-table-plus-seq32-derived-d128-rmsnorm-mlp-v1";
pub const ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_VERIFIER_DOMAIN: &str =
    "ptvm:zkai:native-seq32-attention-mlp-single-proof-object:v1";
pub const ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_INPUT_JSON_BYTES: usize = 8_388_608;
pub const ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_PROOF_BYTES: usize = 2_097_152;
pub const ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_ENVELOPE_JSON_BYTES: usize = 10_485_760;

const ATTENTION_LOG_SIZE: u32 = 11;
const ADAPTER_LOG_SIZE: u32 = 7;
const ADAPTER_WIDTH: usize = 128;
const ADAPTER_VALUE_COLUMNS: usize = 9;
const ADAPTER_REMAINDER_BIT_COLUMNS: usize = 3;
const ADAPTER_TRACE_COLUMNS: usize = ADAPTER_VALUE_COLUMNS + ADAPTER_REMAINDER_BIT_COLUMNS;
const ADAPTER_TRACE_CELLS: usize = ADAPTER_WIDTH * ADAPTER_TRACE_COLUMNS;
const ADAPTER_COMPACT_BASE_VALUE_COLUMNS: usize = 5;
const ADAPTER_COMPACT_BASE_TRACE_COLUMNS: usize =
    ADAPTER_COMPACT_BASE_VALUE_COLUMNS + ADAPTER_REMAINDER_BIT_COLUMNS;
const ADAPTER_COMPACT_BASE_TRACE_CELLS: usize = ADAPTER_WIDTH * ADAPTER_COMPACT_BASE_TRACE_COLUMNS;
const ADAPTER_PREPROCESSED_OUTPUT_ANCHOR_BASE_VALUE_COLUMNS: usize = 1;
const ADAPTER_PREPROCESSED_OUTPUT_ANCHOR_BASE_TRACE_COLUMNS: usize =
    ADAPTER_PREPROCESSED_OUTPUT_ANCHOR_BASE_VALUE_COLUMNS;
const ADAPTER_PREPROCESSED_OUTPUT_ANCHOR_BASE_TRACE_CELLS: usize =
    ADAPTER_WIDTH * ADAPTER_PREPROCESSED_OUTPUT_ANCHOR_BASE_TRACE_COLUMNS;
const ADAPTER_RMSNORM_INPUT_FUSED_BASE_VALUE_COLUMNS: usize = 0;
const ADAPTER_RMSNORM_INPUT_FUSED_BASE_TRACE_CELLS: usize = 0;
const ATTENTION_ROWS: usize = 64;
const ATTENTION_WIDTH: usize = 8;
const ATTENTION_FLAT_CELLS: usize = ATTENTION_ROWS * ATTENTION_WIDTH;
const ADAPTER_PRIMARY_COEFF: i64 = 9;
const ADAPTER_MIX_COEFF: i64 = 5;
const ADAPTER_DENOMINATOR: i64 = 8;
const M31_MODULUS: i64 = (1i64 << 31) - 1;
const EXPECTED_TRACE_COMMITMENT_TREES: usize = 3;
const EXPECTED_PROOF_COMMITMENTS: usize = 4;
const SINGLE_PCS_LIFTING_LOG_SIZE: u32 = 19;
const CURRENT_TWO_PROOF_FRONTIER_TYPED_BYTES: usize = 47_188;
const CURRENT_ATTENTION_FUSED_TYPED_BYTES: usize = 22_916;
const CURRENT_DERIVED_MLP_FUSED_TYPED_BYTES: usize = 24_272;
const NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES: usize = 6_900;
const SOURCE_ATTENTION_OUTPUTS_COMMITMENT: &str =
    "blake2b-256:893d7caa9d9ce54e43508c4890209805f24a7cba43d0951592e812de1dbcfd69";
const SEQ32_DERIVED_D128_INPUT_ACTIVATION_COMMITMENT: &str =
    "blake2b-256:f1145a876ece5ad4154ce254ae284d3c2f673d76db0ff74a7a48bf9e4cfa8223";
const SEQ32_DERIVED_D128_INPUT_PROOF_VERSION: &str = "zkai-seq32-derived-d128-input-gate-v1";
const SEQ32_DERIVED_D128_INPUT_STATEMENT_COMMITMENT: &str =
    "blake2b-256:03267fbc084726c1249fbd6025cc3ec3fdc30214f7c75693810c5b72188ace55";
const STATEMENT_DOMAIN: &str = "ptvm:zkai:native-seq32-attention-mlp-single-proof-statement:v1";
const PUBLIC_INSTANCE_DOMAIN: &str =
    "ptvm:zkai:native-seq32-attention-mlp-single-proof-public-instance:v1";
const PROOF_NATIVE_PARAMETER_DOMAIN: &str =
    "ptvm:zkai:native-seq32-attention-mlp-single-proof-native-parameter:v1";

const EXPECTED_ADAPTER_STATUS: &str = "NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER";
const EXPECTED_COMPACT_ADAPTER_STATUS: &str =
    "NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER_COMPACT_BASE_REFERENCED_FIXED_COLUMNS";
const EXPECTED_PREPROCESSED_OUTPUT_ANCHOR_ADAPTER_STATUS: &str =
    "NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER_PREPROCESSED_FIXED_COLUMNS_WITH_OUTPUT_ANCHOR";
const EXPECTED_RMSNORM_INPUT_FUSED_ADAPTER_STATUS: &str =
    "NATIVE_AIR_PROVEN_ATTENTION_OUTPUT_TO_D128_INPUT_ADAPTER_FUSED_INTO_RMSNORM_INPUT_COMPONENT";
const ADAPTER_COLUMN_IDS: [&str; ADAPTER_TRACE_COLUMNS] = [
    "zkai/native-attention-mlp/adapter/row-index",
    "zkai/native-attention-mlp/adapter/primary-source-index",
    "zkai/native-attention-mlp/adapter/mix-source-index",
    "zkai/native-attention-mlp/adapter/primary-q8",
    "zkai/native-attention-mlp/adapter/mix-q8",
    "zkai/native-attention-mlp/adapter/bias-q8",
    "zkai/native-attention-mlp/adapter/numerator-q8",
    "zkai/native-attention-mlp/adapter/output-q8",
    "zkai/native-attention-mlp/adapter/floor-remainder-q8",
    "zkai/native-attention-mlp/adapter/floor-remainder-bit-0",
    "zkai/native-attention-mlp/adapter/floor-remainder-bit-1",
    "zkai/native-attention-mlp/adapter/floor-remainder-bit-2",
];
const DUPLICATE_ADAPTER_BACKEND_VERSION: &str =
    ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_BACKEND_VERSION;
const DUPLICATE_SELECTOR_ADAPTER_BACKEND_VERSION: &str =
    "stwo-native-seq32-attention-mlp-single-proof-object-duplicate-adapter-selector-v1";
const COMPACT_ADAPTER_BACKEND_VERSION: &str =
    "stwo-native-seq32-attention-mlp-single-proof-object-compact-adapter-selector-v1";
const PREPROCESSED_OUTPUT_ANCHOR_ADAPTER_BACKEND_VERSION: &str =
    "stwo-native-seq32-attention-mlp-single-proof-object-preprocessed-output-anchor-adapter-v1";
const RMSNORM_INPUT_FUSED_ADAPTER_BACKEND_VERSION: &str =
    "stwo-native-seq32-attention-mlp-single-proof-object-rmsnorm-input-fused-adapter-v1";
const RMSNORM_INPUT_FUSED_ADJACENT_ADAPTER_BACKEND_VERSION: &str =
    "stwo-native-seq32-attention-mlp-single-proof-object-rmsnorm-input-fused-adjacent-fixed-v1";
const RMSNORM_INPUT_FUSED_POST_TAIL_ADAPTER_BACKEND_VERSION: &str =
    "stwo-native-seq32-attention-mlp-single-proof-object-rmsnorm-input-fused-post-tail-fixed-v1";
const EXPECTED_NON_CLAIMS: &[&str] = &[
    "not proof-size savings",
    "not a full transformer block",
    "not a NANOZK proof-size win",
    "not a matched external zkML benchmark",
    "not exact real-valued Softmax",
    "not full autoregressive inference",
    "not recursion or proof-carrying data",
    "not timing evidence",
    "not production-ready zkML",
];
const EXPECTED_PROOF_VERIFIER_HARDENING: &[&str] = &[
    "attention source input validated before proof construction",
    "attention fused summary recomputed before relation draw",
    "attention LogUp interaction trace committed in the same proof object",
    "attention output commitment pinned to the statement-bound d128 adapter source",
    "native adapter AIR proves fixed public projection from two-head seq32 attention outputs to d128 RMSNorm input rows",
    "native adapter AIR proves quotient/remainder semantics for every d128 adapter coordinate",
    "native adapter AIR remainder bits are boolean-constrained inside the same proof object",
    "d128 RMSNorm-MLP fused input validated before proof construction",
    "d128 MLP input activation commitment pinned to the approved attention-derived vector",
    "d128 residual source anchors pinned to the approved attention-derived input statement",
    "combined preprocessed column IDs checked for uniqueness",
    "combined preprocessed trace column count checked before committing",
    "combined base trace binds attention rows and six MLP component traces",
    "statement/public-instance/native-parameter commitments recomputed before proof verification",
    "fixed publication-v1 PCS verifier profile before commitment-root recomputation",
    "commitment-vector length check before commitment indexing",
    "bounded proof bytes before JSON deserialization",
];
const EXPECTED_VALIDATION_COMMANDS: &[&str] = &[
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json > docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-binary-accounting-2026-05.json",
    "python3 scripts/zkai_native_seq32_attention_mlp_single_proof_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.tsv",
    "python3 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_single_proof_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend native_seq32_attention_mlp_single_proof --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
];
const EXPECTED_SEQ32_ADAPTER_VARIANT_SELECTOR_VALIDATION_COMMANDS: &[&str] = &[
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-compact docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-compact-adapter-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-compact-adapter-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-compact-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-compact-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-preprocessed-anchor docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-adjacent docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- build-input-rmsnorm-fused-post-tail docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.input.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- prove docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.input.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_native_seq32_attention_mlp_single_proof -- verify docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.envelope.json",
    "cargo +nightly-2025-07-14 run --locked --features stwo-backend --bin zkai_stwo_proof_binary_accounting -- --evidence-dir docs/engineering/evidence docs/engineering/evidence/zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-compact-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json docs/engineering/evidence/zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.envelope.json > docs/engineering/evidence/zkai-native-seq32-attention-mlp-adapter-variant-selector-accounting-2026-05.json",
    "python3.10 scripts/zkai_native_seq32_attention_mlp_adapter_variant_selector_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-adapter-variant-selector-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-adapter-variant-selector-2026-05.tsv",
    "python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_adapter_variant_selector_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_adapter_variant_selector_gate.py",
    "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_adapter_variant_selector_gate",
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend native_seq32_attention_mlp_single_proof --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
];
const EXPECTED_EXPERIMENTAL_ADAPTER_MODE_VALIDATION_COMMANDS: &[&str] = &[
    "cargo +nightly-2025-07-14 test --locked --features stwo-backend native_seq32_attention_mlp_single_proof --lib",
    "git diff --check",
    "just gate-fast",
    "just gate",
];
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ZkAiNativeSeq32AttentionMlpAdapterMode {
    #[serde(rename = "duplicate_base_preprocessed_v1")]
    DuplicateBasePreprocessed,
    #[serde(rename = "duplicate_base_preprocessed_selector_v1")]
    DuplicateBasePreprocessedSelector,
    #[serde(rename = "compact_base_referenced_fixed_v1")]
    CompactBaseReferencedFixed,
    #[serde(rename = "preprocessed_output_anchor_fixed_v1")]
    PreprocessedOutputAnchorFixed,
    #[serde(rename = "rmsnorm_input_fused_fixed_v1")]
    RmsnormInputFusedFixed,
    #[serde(rename = "rmsnorm_input_fused_adjacent_fixed_v1")]
    RmsnormInputFusedAdjacentFixed,
    #[serde(rename = "rmsnorm_input_fused_adjacent_label_probe_a_v1")]
    RmsnormInputFusedAdjacentLabelProbeA,
    #[serde(rename = "rmsnorm_input_fused_adjacent_label_probe_b_v1")]
    RmsnormInputFusedAdjacentLabelProbeB,
    #[serde(rename = "rmsnorm_input_fused_post_tail_fixed_v1")]
    RmsnormInputFusedPostTailFixed,
    #[serde(rename = "rmsnorm_input_fused_post_tail_label_probe_a_v1")]
    RmsnormInputFusedPostTailLabelProbeA,
    #[serde(rename = "rmsnorm_input_fused_post_tail_label_probe_b_v1")]
    RmsnormInputFusedPostTailLabelProbeB,
    #[serde(rename = "rmsnorm_input_fused_fixed_label_probe_a_v1")]
    RmsnormInputFusedLabelProbeA,
    #[serde(rename = "rmsnorm_input_fused_fixed_label_probe_b_v1")]
    RmsnormInputFusedLabelProbeB,
}

impl Default for ZkAiNativeSeq32AttentionMlpAdapterMode {
    fn default() -> Self {
        Self::DuplicateBasePreprocessed
    }
}

impl ZkAiNativeSeq32AttentionMlpAdapterMode {
    fn adapter_status(self) -> &'static str {
        match self {
            Self::DuplicateBasePreprocessed | Self::DuplicateBasePreprocessedSelector => {
                EXPECTED_ADAPTER_STATUS
            }
            Self::CompactBaseReferencedFixed => EXPECTED_COMPACT_ADAPTER_STATUS,
            Self::PreprocessedOutputAnchorFixed => {
                EXPECTED_PREPROCESSED_OUTPUT_ANCHOR_ADAPTER_STATUS
            }
            Self::RmsnormInputFusedFixed
            | Self::RmsnormInputFusedAdjacentFixed
            | Self::RmsnormInputFusedAdjacentLabelProbeA
            | Self::RmsnormInputFusedAdjacentLabelProbeB
            | Self::RmsnormInputFusedPostTailFixed
            | Self::RmsnormInputFusedPostTailLabelProbeA
            | Self::RmsnormInputFusedPostTailLabelProbeB
            | Self::RmsnormInputFusedLabelProbeA
            | Self::RmsnormInputFusedLabelProbeB => EXPECTED_RMSNORM_INPUT_FUSED_ADAPTER_STATUS,
        }
    }

    fn backend_version(self) -> &'static str {
        match self {
            Self::DuplicateBasePreprocessed => DUPLICATE_ADAPTER_BACKEND_VERSION,
            Self::DuplicateBasePreprocessedSelector => DUPLICATE_SELECTOR_ADAPTER_BACKEND_VERSION,
            Self::CompactBaseReferencedFixed => COMPACT_ADAPTER_BACKEND_VERSION,
            Self::PreprocessedOutputAnchorFixed => {
                PREPROCESSED_OUTPUT_ANCHOR_ADAPTER_BACKEND_VERSION
            }
            Self::RmsnormInputFusedFixed
            | Self::RmsnormInputFusedLabelProbeA
            | Self::RmsnormInputFusedLabelProbeB => RMSNORM_INPUT_FUSED_ADAPTER_BACKEND_VERSION,
            Self::RmsnormInputFusedAdjacentFixed
            | Self::RmsnormInputFusedAdjacentLabelProbeA
            | Self::RmsnormInputFusedAdjacentLabelProbeB => {
                RMSNORM_INPUT_FUSED_ADJACENT_ADAPTER_BACKEND_VERSION
            }
            Self::RmsnormInputFusedPostTailFixed
            | Self::RmsnormInputFusedPostTailLabelProbeA
            | Self::RmsnormInputFusedPostTailLabelProbeB => {
                RMSNORM_INPUT_FUSED_POST_TAIL_ADAPTER_BACKEND_VERSION
            }
        }
    }

    fn base_value_columns(self) -> usize {
        match self {
            Self::DuplicateBasePreprocessed | Self::DuplicateBasePreprocessedSelector => {
                ADAPTER_VALUE_COLUMNS
            }
            Self::CompactBaseReferencedFixed => ADAPTER_COMPACT_BASE_VALUE_COLUMNS,
            Self::PreprocessedOutputAnchorFixed => {
                ADAPTER_PREPROCESSED_OUTPUT_ANCHOR_BASE_VALUE_COLUMNS
            }
            Self::RmsnormInputFusedFixed
            | Self::RmsnormInputFusedAdjacentFixed
            | Self::RmsnormInputFusedAdjacentLabelProbeA
            | Self::RmsnormInputFusedAdjacentLabelProbeB
            | Self::RmsnormInputFusedPostTailFixed
            | Self::RmsnormInputFusedPostTailLabelProbeA
            | Self::RmsnormInputFusedPostTailLabelProbeB
            | Self::RmsnormInputFusedLabelProbeA
            | Self::RmsnormInputFusedLabelProbeB => ADAPTER_RMSNORM_INPUT_FUSED_BASE_VALUE_COLUMNS,
        }
    }

    fn base_trace_cells(self) -> usize {
        match self {
            Self::DuplicateBasePreprocessed | Self::DuplicateBasePreprocessedSelector => {
                ADAPTER_TRACE_CELLS
            }
            Self::CompactBaseReferencedFixed => ADAPTER_COMPACT_BASE_TRACE_CELLS,
            Self::PreprocessedOutputAnchorFixed => {
                ADAPTER_PREPROCESSED_OUTPUT_ANCHOR_BASE_TRACE_CELLS
            }
            Self::RmsnormInputFusedFixed
            | Self::RmsnormInputFusedAdjacentFixed
            | Self::RmsnormInputFusedAdjacentLabelProbeA
            | Self::RmsnormInputFusedAdjacentLabelProbeB
            | Self::RmsnormInputFusedPostTailFixed
            | Self::RmsnormInputFusedPostTailLabelProbeA
            | Self::RmsnormInputFusedPostTailLabelProbeB
            | Self::RmsnormInputFusedLabelProbeA
            | Self::RmsnormInputFusedLabelProbeB => ADAPTER_RMSNORM_INPUT_FUSED_BASE_TRACE_CELLS,
        }
    }

    fn validation_commands(self) -> &'static [&'static str] {
        match self {
            Self::DuplicateBasePreprocessed => EXPECTED_VALIDATION_COMMANDS,
            Self::CompactBaseReferencedFixed
            | Self::PreprocessedOutputAnchorFixed
            | Self::RmsnormInputFusedFixed
            | Self::RmsnormInputFusedAdjacentFixed
            | Self::RmsnormInputFusedPostTailFixed => {
                EXPECTED_SEQ32_ADAPTER_VARIANT_SELECTOR_VALIDATION_COMMANDS
            }
            Self::DuplicateBasePreprocessedSelector
            | Self::RmsnormInputFusedLabelProbeA
            | Self::RmsnormInputFusedLabelProbeB
            | Self::RmsnormInputFusedAdjacentLabelProbeA
            | Self::RmsnormInputFusedAdjacentLabelProbeB
            | Self::RmsnormInputFusedPostTailLabelProbeA
            | Self::RmsnormInputFusedPostTailLabelProbeB => {
                EXPECTED_EXPERIMENTAL_ADAPTER_MODE_VALIDATION_COMMANDS
            }
        }
    }

    fn uses_compact_base_trace(self) -> bool {
        self == Self::CompactBaseReferencedFixed
    }

    fn uses_preprocessed_output_anchor_trace(self) -> bool {
        self == Self::PreprocessedOutputAnchorFixed
    }

    fn uses_rmsnorm_input_fused_adapter(self) -> bool {
        matches!(
            self,
            Self::RmsnormInputFusedFixed
                | Self::RmsnormInputFusedAdjacentFixed
                | Self::RmsnormInputFusedAdjacentLabelProbeA
                | Self::RmsnormInputFusedAdjacentLabelProbeB
                | Self::RmsnormInputFusedPostTailFixed
                | Self::RmsnormInputFusedPostTailLabelProbeA
                | Self::RmsnormInputFusedPostTailLabelProbeB
                | Self::RmsnormInputFusedLabelProbeA
                | Self::RmsnormInputFusedLabelProbeB
        )
    }

    fn uses_rmsnorm_adjacent_preprocessed_layout(self) -> bool {
        matches!(
            self,
            Self::RmsnormInputFusedAdjacentFixed
                | Self::RmsnormInputFusedAdjacentLabelProbeA
                | Self::RmsnormInputFusedAdjacentLabelProbeB
        )
    }

    fn uses_rmsnorm_post_tail_preprocessed_layout(self) -> bool {
        matches!(
            self,
            Self::RmsnormInputFusedPostTailFixed
                | Self::RmsnormInputFusedPostTailLabelProbeA
                | Self::RmsnormInputFusedPostTailLabelProbeB
        )
    }
}

#[derive(Debug, Clone)]
struct D128AttentionAdapterEval {
    log_size: u32,
    adapter_mode: ZkAiNativeSeq32AttentionMlpAdapterMode,
    preprocessed_column_ids: [PreProcessedColumnId; ADAPTER_TRACE_COLUMNS],
}

impl FrameworkEval for D128AttentionAdapterEval {
    fn log_size(&self) -> u32 {
        self.log_size
    }

    fn max_constraint_log_degree_bound(&self) -> u32 {
        self.log_size.saturating_add(1)
    }

    fn evaluate<E: EvalAtRow>(&self, mut eval: E) -> E {
        let row_index_public =
            eval.get_preprocessed_column(self.preprocessed_column_ids[0].clone());
        let primary_source_index_public =
            eval.get_preprocessed_column(self.preprocessed_column_ids[1].clone());
        let mix_source_index_public =
            eval.get_preprocessed_column(self.preprocessed_column_ids[2].clone());
        let primary_q8_public =
            eval.get_preprocessed_column(self.preprocessed_column_ids[3].clone());
        let mix_q8_public = eval.get_preprocessed_column(self.preprocessed_column_ids[4].clone());
        let bias_q8 = eval.get_preprocessed_column(self.preprocessed_column_ids[5].clone());
        let numerator_q8_public =
            eval.get_preprocessed_column(self.preprocessed_column_ids[6].clone());
        let output_q8_public =
            eval.get_preprocessed_column(self.preprocessed_column_ids[7].clone());
        let floor_remainder_q8_public =
            eval.get_preprocessed_column(self.preprocessed_column_ids[8].clone());
        let bit_0_public = eval.get_preprocessed_column(self.preprocessed_column_ids[9].clone());
        let bit_1_public = eval.get_preprocessed_column(self.preprocessed_column_ids[10].clone());
        let bit_2_public = eval.get_preprocessed_column(self.preprocessed_column_ids[11].clone());

        let primary_q8;
        let mix_q8;
        let numerator_q8;
        let output_q8;
        let floor_remainder_q8;
        let remainder_bit_0;
        let remainder_bit_1;
        let remainder_bit_2;

        if self.adapter_mode.uses_preprocessed_output_anchor_trace() {
            primary_q8 = primary_q8_public;
            mix_q8 = mix_q8_public;
            numerator_q8 = numerator_q8_public;
            output_q8 = eval.next_trace_mask();
            floor_remainder_q8 = floor_remainder_q8_public;
            remainder_bit_0 = bit_0_public;
            remainder_bit_1 = bit_1_public;
            remainder_bit_2 = bit_2_public;

            let _ = (
                row_index_public,
                primary_source_index_public,
                mix_source_index_public,
            );
            eval.add_constraint(output_q8.clone() - output_q8_public);
        } else if !self.adapter_mode.uses_compact_base_trace() {
            let row_index = eval.next_trace_mask();
            let primary_source_index = eval.next_trace_mask();
            let mix_source_index = eval.next_trace_mask();
            primary_q8 = eval.next_trace_mask();
            mix_q8 = eval.next_trace_mask();
            let bias_q8_trace = eval.next_trace_mask();
            numerator_q8 = eval.next_trace_mask();
            output_q8 = eval.next_trace_mask();
            floor_remainder_q8 = eval.next_trace_mask();
            remainder_bit_0 = eval.next_trace_mask();
            remainder_bit_1 = eval.next_trace_mask();
            remainder_bit_2 = eval.next_trace_mask();

            eval.add_constraint(row_index - row_index_public);
            eval.add_constraint(primary_source_index - primary_source_index_public);
            eval.add_constraint(mix_source_index - mix_source_index_public);
            eval.add_constraint(primary_q8.clone() - primary_q8_public);
            eval.add_constraint(mix_q8.clone() - mix_q8_public);
            eval.add_constraint(bias_q8_trace - bias_q8.clone());
            eval.add_constraint(numerator_q8.clone() - numerator_q8_public);
            eval.add_constraint(output_q8.clone() - output_q8_public);
            eval.add_constraint(floor_remainder_q8.clone() - floor_remainder_q8_public);
            eval.add_constraint(remainder_bit_0.clone() - bit_0_public);
            eval.add_constraint(remainder_bit_1.clone() - bit_1_public);
            eval.add_constraint(remainder_bit_2.clone() - bit_2_public);
        } else {
            primary_q8 = eval.next_trace_mask();
            mix_q8 = eval.next_trace_mask();
            numerator_q8 = eval.next_trace_mask();
            output_q8 = eval.next_trace_mask();
            floor_remainder_q8 = eval.next_trace_mask();
            remainder_bit_0 = eval.next_trace_mask();
            remainder_bit_1 = eval.next_trace_mask();
            remainder_bit_2 = eval.next_trace_mask();

            let _ = (
                row_index_public,
                primary_source_index_public,
                mix_source_index_public,
            );
            eval.add_constraint(primary_q8.clone() - primary_q8_public);
            eval.add_constraint(mix_q8.clone() - mix_q8_public);
            eval.add_constraint(numerator_q8.clone() - numerator_q8_public);
            eval.add_constraint(output_q8.clone() - output_q8_public);
            eval.add_constraint(floor_remainder_q8.clone() - floor_remainder_q8_public);
            eval.add_constraint(remainder_bit_0.clone() - bit_0_public);
            eval.add_constraint(remainder_bit_1.clone() - bit_1_public);
            eval.add_constraint(remainder_bit_2.clone() - bit_2_public);
        }

        let one = E::F::from(BaseField::from(1u32));
        for bit in [&remainder_bit_0, &remainder_bit_1, &remainder_bit_2] {
            eval.add_constraint(bit.clone() * (bit.clone() - one.clone()));
        }
        eval.add_constraint(
            numerator_q8.clone()
                - E::F::from(BaseField::from(ADAPTER_PRIMARY_COEFF as u32)) * primary_q8
                - E::F::from(BaseField::from(ADAPTER_MIX_COEFF as u32)) * mix_q8
                - bias_q8,
        );
        eval.add_constraint(
            numerator_q8
                - E::F::from(BaseField::from(ADAPTER_DENOMINATOR as u32)) * output_q8
                - floor_remainder_q8.clone(),
        );
        eval.add_constraint(
            floor_remainder_q8
                - remainder_bit_0
                - E::F::from(BaseField::from(2u32)) * remainder_bit_1
                - E::F::from(BaseField::from(4u32)) * remainder_bit_2,
        );
        eval
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct D128AttentionAdapterRow {
    row_index: usize,
    primary_source_index: usize,
    mix_source_index: usize,
    primary_q8: i64,
    mix_q8: i64,
    bias_q8: i64,
    numerator_q8: i64,
    output_q8: i64,
    floor_remainder_q8: i64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ZkAiNativeSeq32AttentionMlpSingleProofInput {
    pub schema: String,
    pub decision: String,
    pub route_id: String,
    pub target_id: String,
    pub verifier_domain: String,
    pub attention_proof_version: String,
    pub mlp_proof_version: String,
    pub attention_statement_commitment: String,
    pub attention_public_instance_commitment: String,
    pub attention_outputs_commitment: String,
    pub attention_score_row_commitment: String,
    pub attention_weight_table_commitment: String,
    pub attention_lookup_claims: usize,
    pub attention_table_rows: usize,
    pub mlp_statement_commitment: String,
    pub mlp_public_instance_commitment: String,
    pub mlp_input_activation_commitment: String,
    pub mlp_output_activation_commitment: String,
    pub mlp_row_count: usize,
    #[serde(default)]
    pub adapter_mode: ZkAiNativeSeq32AttentionMlpAdapterMode,
    pub adapter_status: String,
    pub adapter_row_count: usize,
    pub adapter_value_columns: usize,
    pub adapter_remainder_bit_columns: usize,
    pub adapter_trace_cells: usize,
    pub pcs_lifting_log_size: u32,
    pub current_two_proof_frontier_typed_bytes: usize,
    pub current_attention_fused_typed_bytes: usize,
    pub current_derived_mlp_fused_typed_bytes: usize,
    pub nanozk_reported_d128_block_proof_bytes: usize,
    pub statement_commitment: String,
    pub public_instance_commitment: String,
    pub proof_native_parameter_commitment: String,
    pub attention_source_input: ZkAiAttentionKvNativeTwoHeadSeq32BoundedSoftmaxTableProofInput,
    pub mlp_input: ZkAiD128RmsnormMlpFusedInput,
    pub non_claims: Vec<String>,
    pub proof_verifier_hardening: Vec<String>,
    pub validation_commands: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ZkAiNativeSeq32AttentionMlpSingleProofEnvelope {
    pub proof_backend: StarkProofBackend,
    pub proof_backend_version: String,
    pub proof_schema_version: String,
    pub statement_version: String,
    pub semantic_scope: String,
    pub decision: String,
    pub target_id: String,
    pub verifier_domain: String,
    pub input: ZkAiNativeSeq32AttentionMlpSingleProofInput,
    pub proof: Vec<u8>,
}

#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct NativeSeq32AttentionMlpSingleProofPayload {
    stark_proof: StarkProof<Blake2sM31MerkleHasher>,
}

pub fn build_zkai_native_seq32_attention_mlp_single_proof_input(
    attention_source_input: ZkAiAttentionKvNativeTwoHeadSeq32BoundedSoftmaxTableProofInput,
    mlp_input: ZkAiD128RmsnormMlpFusedInput,
) -> Result<ZkAiNativeSeq32AttentionMlpSingleProofInput> {
    build_zkai_native_seq32_attention_mlp_single_proof_input_with_adapter_mode(
        attention_source_input,
        mlp_input,
        ZkAiNativeSeq32AttentionMlpAdapterMode::DuplicateBasePreprocessed,
    )
}

pub fn build_zkai_native_seq32_attention_mlp_single_proof_input_with_adapter_mode(
    attention_source_input: ZkAiAttentionKvNativeTwoHeadSeq32BoundedSoftmaxTableProofInput,
    mlp_input: ZkAiD128RmsnormMlpFusedInput,
    adapter_mode: ZkAiNativeSeq32AttentionMlpAdapterMode,
) -> Result<ZkAiNativeSeq32AttentionMlpSingleProofInput> {
    zkai_attention_kv_native_two_head_seq32_fused_softmax_table_validate_source_input(
        &attention_source_input,
    )?;
    zkai_d128_rmsnorm_mlp_fused_validate_input(&mlp_input)?;
    let attention_summary = zkai_attention_kv_native_two_head_seq32_fused_softmax_table_summary(
        &attention_source_input,
    )?;
    let pcs_lifting_log_size = single_pcs_config(adapter_mode)?
        .lifting_log_size
        .ok_or_else(|| {
            single_error("single proof PCS config must pin an explicit lifting log size")
        })?;
    let mut input = ZkAiNativeSeq32AttentionMlpSingleProofInput {
        schema: ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_INPUT_SCHEMA.to_string(),
        decision: ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_INPUT_DECISION.to_string(),
        route_id: ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_ROUTE_ID.to_string(),
        target_id: ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_TARGET_ID.to_string(),
        verifier_domain: ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_VERIFIER_DOMAIN.to_string(),
        attention_proof_version:
            ZKAI_ATTENTION_KV_NATIVE_TWO_HEAD_SEQ32_FUSED_SOFTMAX_TABLE_PROOF_VERSION.to_string(),
        mlp_proof_version: ZKAI_D128_RMSNORM_MLP_FUSED_PROOF_VERSION.to_string(),
        attention_statement_commitment: attention_source_input.statement_commitment.clone(),
        attention_public_instance_commitment: attention_source_input
            .public_instance_commitment
            .clone(),
        attention_outputs_commitment: attention_source_input.outputs_commitment.clone(),
        attention_score_row_commitment: attention_source_input.score_row_commitment.clone(),
        attention_weight_table_commitment: attention_source_input.weight_table_commitment.clone(),
        attention_lookup_claims: attention_summary.lookup_claims,
        attention_table_rows: attention_summary.table_rows,
        mlp_statement_commitment: mlp_input.statement_commitment.clone(),
        mlp_public_instance_commitment: mlp_input.public_instance_commitment.clone(),
        mlp_input_activation_commitment: mlp_input.input_activation_commitment.clone(),
        mlp_output_activation_commitment: mlp_input.output_activation_commitment.clone(),
        mlp_row_count: mlp_input.rmsnorm_row_count
            + mlp_input.projection_bridge_row_count
            + mlp_input.gate_value_row_count
            + mlp_input.activation_row_count
            + mlp_input.down_projection_row_count
            + mlp_input.residual_add_row_count,
        adapter_mode,
        adapter_status: adapter_mode.adapter_status().to_string(),
        adapter_row_count: ADAPTER_WIDTH,
        adapter_value_columns: adapter_mode.base_value_columns(),
        adapter_remainder_bit_columns: ADAPTER_REMAINDER_BIT_COLUMNS,
        adapter_trace_cells: adapter_mode.base_trace_cells(),
        pcs_lifting_log_size,
        current_two_proof_frontier_typed_bytes: CURRENT_TWO_PROOF_FRONTIER_TYPED_BYTES,
        current_attention_fused_typed_bytes: CURRENT_ATTENTION_FUSED_TYPED_BYTES,
        current_derived_mlp_fused_typed_bytes: CURRENT_DERIVED_MLP_FUSED_TYPED_BYTES,
        nanozk_reported_d128_block_proof_bytes: NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
        statement_commitment: String::new(),
        public_instance_commitment: String::new(),
        proof_native_parameter_commitment: String::new(),
        attention_source_input,
        mlp_input,
        non_claims: EXPECTED_NON_CLAIMS
            .iter()
            .map(|value| value.to_string())
            .collect(),
        proof_verifier_hardening: EXPECTED_PROOF_VERIFIER_HARDENING
            .iter()
            .map(|value| value.to_string())
            .collect(),
        validation_commands: adapter_mode
            .validation_commands()
            .iter()
            .map(|value| value.to_string())
            .collect(),
    };
    input.statement_commitment = statement_commitment(&input)?;
    input.public_instance_commitment = public_instance_commitment(&input.statement_commitment)?;
    input.proof_native_parameter_commitment =
        proof_native_parameter_commitment(&input.statement_commitment, input.adapter_mode)?;
    validate_single_input(&input)?;
    Ok(input)
}

pub fn zkai_native_seq32_attention_mlp_single_proof_input_from_json_str(
    raw_json: &str,
) -> Result<ZkAiNativeSeq32AttentionMlpSingleProofInput> {
    if raw_json.len() > ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_INPUT_JSON_BYTES {
        return Err(single_error(format!(
            "input JSON exceeds max size: got {} bytes, limit {} bytes",
            raw_json.len(),
            ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_INPUT_JSON_BYTES
        )));
    }
    let input: ZkAiNativeSeq32AttentionMlpSingleProofInput = serde_json::from_str(raw_json)
        .map_err(|error| VmError::Serialization(error.to_string()))?;
    validate_single_input(&input)?;
    Ok(input)
}

pub fn zkai_native_seq32_attention_mlp_single_proof_envelope_from_json_slice(
    raw_json: &[u8],
) -> Result<ZkAiNativeSeq32AttentionMlpSingleProofEnvelope> {
    if raw_json.len() > ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_ENVELOPE_JSON_BYTES {
        return Err(single_error(format!(
            "envelope JSON exceeds max size: got {} bytes, limit {} bytes",
            raw_json.len(),
            ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_ENVELOPE_JSON_BYTES
        )));
    }
    let envelope: ZkAiNativeSeq32AttentionMlpSingleProofEnvelope = serde_json::from_slice(raw_json)
        .map_err(|error| VmError::Serialization(error.to_string()))?;
    validate_single_envelope(&envelope)?;
    Ok(envelope)
}

pub fn prove_zkai_native_seq32_attention_mlp_single_proof_envelope(
    input: &ZkAiNativeSeq32AttentionMlpSingleProofInput,
) -> Result<ZkAiNativeSeq32AttentionMlpSingleProofEnvelope> {
    validate_single_input(input)?;
    let proof = prove_single_proof(input)?;
    if proof.len() > ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_PROOF_BYTES {
        return Err(single_error(format!(
            "proof bytes exceed bounded prover limit: got {}, max {}",
            proof.len(),
            ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_PROOF_BYTES
        )));
    }
    Ok(ZkAiNativeSeq32AttentionMlpSingleProofEnvelope {
        proof_backend: StarkProofBackend::Stwo,
        proof_backend_version: input.adapter_mode.backend_version().to_string(),
        proof_schema_version: ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_PROOF_VERSION
            .to_string(),
        statement_version: ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_STATEMENT_VERSION
            .to_string(),
        semantic_scope: ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_SEMANTIC_SCOPE.to_string(),
        decision: ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_DECISION.to_string(),
        target_id: ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_TARGET_ID.to_string(),
        verifier_domain: ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_VERIFIER_DOMAIN.to_string(),
        input: input.clone(),
        proof,
    })
}

pub fn verify_zkai_native_seq32_attention_mlp_single_proof_envelope(
    envelope: &ZkAiNativeSeq32AttentionMlpSingleProofEnvelope,
) -> Result<bool> {
    validate_single_envelope(envelope)?;
    verify_single_proof(&envelope.input, &envelope.proof)
}

fn validate_single_envelope(
    envelope: &ZkAiNativeSeq32AttentionMlpSingleProofEnvelope,
) -> Result<()> {
    validate_single_input(&envelope.input)?;
    if envelope.proof_backend != StarkProofBackend::Stwo {
        return Err(single_error("proof backend is not Stwo"));
    }
    expect_eq(
        &envelope.proof_backend_version,
        envelope.input.adapter_mode.backend_version(),
        "proof backend version",
    )?;
    expect_eq(
        &envelope.proof_schema_version,
        ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_PROOF_VERSION,
        "proof schema version",
    )?;
    expect_eq(
        &envelope.statement_version,
        ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_STATEMENT_VERSION,
        "statement version",
    )?;
    expect_eq(
        &envelope.semantic_scope,
        ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_SEMANTIC_SCOPE,
        "semantic scope",
    )?;
    expect_eq(
        &envelope.decision,
        ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_DECISION,
        "decision",
    )?;
    expect_eq(
        &envelope.target_id,
        ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_TARGET_ID,
        "target id",
    )?;
    expect_eq(
        &envelope.verifier_domain,
        ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_VERIFIER_DOMAIN,
        "verifier domain",
    )?;
    if envelope.proof.is_empty()
        || envelope.proof.len() > ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_PROOF_BYTES
    {
        return Err(single_error("proof byte length outside bounded cap"));
    }
    Ok(())
}

fn validate_single_input(input: &ZkAiNativeSeq32AttentionMlpSingleProofInput) -> Result<()> {
    expect_eq(
        &input.schema,
        ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_INPUT_SCHEMA,
        "schema",
    )?;
    expect_eq(
        &input.decision,
        ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_INPUT_DECISION,
        "input decision",
    )?;
    expect_eq(
        &input.route_id,
        ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_ROUTE_ID,
        "route id",
    )?;
    expect_eq(
        &input.target_id,
        ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_TARGET_ID,
        "target id",
    )?;
    expect_eq(
        &input.verifier_domain,
        ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_VERIFIER_DOMAIN,
        "verifier domain",
    )?;
    expect_eq(
        &input.attention_proof_version,
        ZKAI_ATTENTION_KV_NATIVE_TWO_HEAD_SEQ32_FUSED_SOFTMAX_TABLE_PROOF_VERSION,
        "attention proof version",
    )?;
    expect_eq(
        &input.mlp_proof_version,
        ZKAI_D128_RMSNORM_MLP_FUSED_PROOF_VERSION,
        "MLP proof version",
    )?;
    zkai_attention_kv_native_two_head_seq32_fused_softmax_table_validate_source_input(
        &input.attention_source_input,
    )?;
    zkai_d128_rmsnorm_mlp_fused_validate_input(&input.mlp_input)?;
    let attention_summary = zkai_attention_kv_native_two_head_seq32_fused_softmax_table_summary(
        &input.attention_source_input,
    )?;
    expect_attention_summary(input, &attention_summary)?;
    expect_eq(
        &input.attention_outputs_commitment,
        SOURCE_ATTENTION_OUTPUTS_COMMITMENT,
        "attention output commitment route pin",
    )?;
    expect_eq(
        &input.attention_outputs_commitment,
        &input.attention_source_input.outputs_commitment,
        "attention output commitment source",
    )?;
    expect_eq(
        &input.mlp_input_activation_commitment,
        SEQ32_DERIVED_D128_INPUT_ACTIVATION_COMMITMENT,
        "MLP input activation commitment route pin",
    )?;
    expect_eq(
        &input.mlp_input_activation_commitment,
        &input.mlp_input.input_activation_commitment,
        "MLP input activation commitment",
    )?;
    expect_eq(
        &input
            .mlp_input
            .residual_add_input
            .source_rmsnorm_proof_version,
        SEQ32_DERIVED_D128_INPUT_PROOF_VERSION,
        "MLP residual source proof version",
    )?;
    expect_eq(
        &input
            .mlp_input
            .residual_add_input
            .source_rmsnorm_statement_commitment,
        SEQ32_DERIVED_D128_INPUT_STATEMENT_COMMITMENT,
        "MLP residual source statement commitment",
    )?;
    expect_eq(
        &input.mlp_statement_commitment,
        &input.mlp_input.statement_commitment,
        "MLP statement commitment",
    )?;
    expect_eq(
        &input.mlp_public_instance_commitment,
        &input.mlp_input.public_instance_commitment,
        "MLP public instance commitment",
    )?;
    expect_eq(
        &input.mlp_output_activation_commitment,
        &input.mlp_input.output_activation_commitment,
        "MLP output activation commitment",
    )?;
    expect_usize(
        input.mlp_row_count,
        input.mlp_input.rmsnorm_row_count
            + input.mlp_input.projection_bridge_row_count
            + input.mlp_input.gate_value_row_count
            + input.mlp_input.activation_row_count
            + input.mlp_input.down_projection_row_count
            + input.mlp_input.residual_add_row_count,
        "MLP row count",
    )?;
    expect_eq(
        &input.adapter_status,
        input.adapter_mode.adapter_status(),
        "adapter status",
    )?;
    let adapter_rows = attention_adapter_rows(input)?;
    expect_usize(
        input.adapter_row_count,
        adapter_rows.len(),
        "adapter row count",
    )?;
    expect_usize(
        input.adapter_value_columns,
        input.adapter_mode.base_value_columns(),
        "adapter value columns",
    )?;
    expect_usize(
        input.adapter_remainder_bit_columns,
        ADAPTER_REMAINDER_BIT_COLUMNS,
        "adapter remainder bit columns",
    )?;
    expect_usize(
        input.adapter_trace_cells,
        input.adapter_mode.base_trace_cells(),
        "adapter trace cells",
    )?;
    let expected_lifting_log_size = single_pcs_config(input.adapter_mode)?
        .lifting_log_size
        .ok_or_else(|| {
            single_error("single proof PCS config must pin an explicit lifting log size")
        })?;
    expect_usize(
        input.pcs_lifting_log_size as usize,
        expected_lifting_log_size as usize,
        "PCS lifting log size",
    )?;
    expect_usize(
        input.current_two_proof_frontier_typed_bytes,
        CURRENT_TWO_PROOF_FRONTIER_TYPED_BYTES,
        "current two-proof frontier typed bytes",
    )?;
    expect_usize(
        input.current_attention_fused_typed_bytes,
        CURRENT_ATTENTION_FUSED_TYPED_BYTES,
        "current attention fused typed bytes",
    )?;
    expect_usize(
        input.current_derived_mlp_fused_typed_bytes,
        CURRENT_DERIVED_MLP_FUSED_TYPED_BYTES,
        "current derived MLP fused typed bytes",
    )?;
    expect_usize(
        input.nanozk_reported_d128_block_proof_bytes,
        NANOZK_REPORTED_D128_BLOCK_PROOF_BYTES,
        "NANOZK reported d128 block proof bytes",
    )?;
    expect_vec_eq(&input.non_claims, EXPECTED_NON_CLAIMS, "non-claims")?;
    expect_vec_eq(
        &input.proof_verifier_hardening,
        EXPECTED_PROOF_VERIFIER_HARDENING,
        "proof verifier hardening",
    )?;
    expect_vec_eq(
        &input.validation_commands,
        input.adapter_mode.validation_commands(),
        "validation commands",
    )?;
    expect_eq(
        &input.statement_commitment,
        &statement_commitment(input)?,
        "statement commitment",
    )?;
    expect_eq(
        &input.public_instance_commitment,
        &public_instance_commitment(&input.statement_commitment)?,
        "public instance commitment",
    )?;
    expect_eq(
        &input.proof_native_parameter_commitment,
        &proof_native_parameter_commitment(&input.statement_commitment, input.adapter_mode)?,
        "proof-native parameter commitment",
    )?;
    let ids = combined_preprocessed_column_ids(input.adapter_mode)?;
    if ids.is_empty() {
        return Err(single_error("combined preprocessed column IDs are empty"));
    }
    Ok(())
}

fn expect_attention_summary(
    input: &ZkAiNativeSeq32AttentionMlpSingleProofInput,
    summary: &ZkAiAttentionKvNativeTwoHeadSeq32FusedSoftmaxTableSummary,
) -> Result<()> {
    expect_eq(
        &input.attention_statement_commitment,
        &input.attention_source_input.statement_commitment,
        "attention statement commitment source",
    )?;
    expect_eq(
        &input.attention_statement_commitment,
        &summary.source_statement_commitment,
        "attention statement commitment summary",
    )?;
    expect_eq(
        &input.attention_public_instance_commitment,
        &input.attention_source_input.public_instance_commitment,
        "attention public instance commitment source",
    )?;
    expect_eq(
        &input.attention_public_instance_commitment,
        &summary.source_public_instance_commitment,
        "attention public instance commitment summary",
    )?;
    expect_eq(
        &input.attention_score_row_commitment,
        &input.attention_source_input.score_row_commitment,
        "attention score row commitment source",
    )?;
    expect_eq(
        &input.attention_score_row_commitment,
        &summary.source_score_row_commitment,
        "attention score row commitment summary",
    )?;
    expect_eq(
        &input.attention_weight_table_commitment,
        &input.attention_source_input.weight_table_commitment,
        "attention weight table commitment source",
    )?;
    expect_eq(
        &input.attention_weight_table_commitment,
        &summary.source_weight_table_commitment,
        "attention weight table commitment summary",
    )?;
    expect_usize(
        input.attention_lookup_claims,
        summary.lookup_claims,
        "attention lookup claims",
    )?;
    expect_usize(
        input.attention_table_rows,
        summary.table_rows,
        "attention table rows",
    )
}

fn prove_single_proof(input: &ZkAiNativeSeq32AttentionMlpSingleProofInput) -> Result<Vec<u8>> {
    let attention_summary = zkai_attention_kv_native_two_head_seq32_fused_softmax_table_summary(
        &input.attention_source_input,
    )?;
    let attention_preprocessed =
        zkai_attention_kv_native_two_head_seq32_fused_softmax_table_preprocessed_trace(
            &input.attention_source_input,
            &attention_summary,
        )?;
    let attention_base = zkai_attention_kv_native_two_head_seq32_fused_softmax_table_base_trace(
        &input.attention_source_input,
    )?;
    let preprocessed_ids = combined_preprocessed_column_ids(input.adapter_mode)?;
    let mut allocator = TraceLocationAllocator::new_with_preprocessed_columns(&preprocessed_ids);
    let attention_placeholder =
        zkai_attention_kv_native_two_head_seq32_fused_softmax_table_component_with_allocator(
            &mut allocator,
            AttentionKvTwoHeadSeq32FusedSoftmaxTableRelation::dummy(),
        );
    let adapter_component = if input.adapter_mode.uses_rmsnorm_input_fused_adapter() {
        None
    } else {
        Some(zkai_native_attention_mlp_adapter_component_with_allocator(
            &mut allocator,
            input.adapter_mode,
        ))
    };
    let rmsnorm_component =
        zkai_d128_rmsnorm_public_row_component_with_optional_input_adapter_allocator(
            &mut allocator,
            input
                .adapter_mode
                .uses_rmsnorm_input_fused_adapter()
                .then(rmsnorm_input_adapter_binding),
        );
    let bridge_component =
        zkai_d128_rmsnorm_to_projection_bridge_component_with_allocator(&mut allocator);
    let gate_value_component =
        zkai_d128_gate_value_projection_component_with_allocator(&mut allocator);
    let activation_component = zkai_d128_activation_swiglu_component_with_allocator(&mut allocator);
    let down_projection_component =
        zkai_d128_down_projection_component_with_allocator(&mut allocator);
    let residual_add_component = zkai_d128_residual_add_component_with_allocator(&mut allocator);
    let max_constraint_log_degree_bound = attention_placeholder
        .max_constraint_log_degree_bound()
        .max(rmsnorm_component.max_constraint_log_degree_bound())
        .max(bridge_component.max_constraint_log_degree_bound())
        .max(gate_value_component.max_constraint_log_degree_bound())
        .max(activation_component.max_constraint_log_degree_bound())
        .max(down_projection_component.max_constraint_log_degree_bound())
        .max(residual_add_component.max_constraint_log_degree_bound());
    let max_constraint_log_degree_bound = if let Some(adapter_component) = &adapter_component {
        max_constraint_log_degree_bound.max(adapter_component.max_constraint_log_degree_bound())
    } else {
        max_constraint_log_degree_bound
    };
    let config = single_pcs_config(input.adapter_mode)?;
    let twiddles = SimdBackend::precompute_twiddles(
        CanonicCoset::new(
            max_constraint_log_degree_bound + config.fri_config.log_blowup_factor + 1,
        )
        .circle_domain()
        .half_coset,
    );
    let channel = &mut Blake2sM31Channel::default();
    let mut commitment_scheme =
        CommitmentSchemeProver::<SimdBackend, Blake2sM31MerkleChannel>::new(config, &twiddles);
    commitment_scheme.set_store_polynomials_coefficients();

    let preprocessed_trace = combined_preprocessed_trace(input, attention_preprocessed)?;
    if preprocessed_trace.len() != preprocessed_ids.len() {
        return Err(single_error(format!(
            "combined preprocessed trace column count drift: got {}, expected {}",
            preprocessed_trace.len(),
            preprocessed_ids.len()
        )));
    }
    let base_trace = combined_base_trace(input, attention_base.clone())?;
    let sizes = combined_column_log_sizes(&preprocessed_ids, input.adapter_mode);
    ensure_trace_shape("preprocessed", &preprocessed_trace, &sizes[0])?;
    ensure_trace_shape("base", &base_trace, &sizes[1])?;

    let mut tree_builder = commitment_scheme.tree_builder();
    tree_builder.extend_evals(preprocessed_trace.clone());
    tree_builder.commit(channel);

    let mut tree_builder = commitment_scheme.tree_builder();
    tree_builder.extend_evals(base_trace);
    tree_builder.commit(channel);

    mix_single_statement(channel, input, &attention_summary);
    let lookup_elements = AttentionKvTwoHeadSeq32FusedSoftmaxTableRelation::draw(channel);
    let (interaction_trace, claimed_sum) =
        zkai_attention_kv_native_two_head_seq32_fused_softmax_table_interaction_trace(
            ATTENTION_LOG_SIZE,
            &attention_base,
            &preprocessed_trace
                [..zkai_attention_kv_native_two_head_seq32_fused_softmax_table_preprocessed_column_ids().len()]
                .to_vec(),
            &lookup_elements,
        )?;
    if claimed_sum != SecureField::from(BaseField::from(0u32)) {
        return Err(single_error(
            "attention Softmax-table LogUp expected zero claimed sum in combined proof",
        ));
    }
    ensure_trace_shape("interaction", &interaction_trace, &sizes[2])?;
    let mut tree_builder = commitment_scheme.tree_builder();
    tree_builder.extend_evals(interaction_trace);
    tree_builder.commit(channel);

    let mut allocator = TraceLocationAllocator::new_with_preprocessed_columns(&preprocessed_ids);
    let attention_component =
        zkai_attention_kv_native_two_head_seq32_fused_softmax_table_component_with_allocator(
            &mut allocator,
            lookup_elements,
        );
    let adapter_component = if input.adapter_mode.uses_rmsnorm_input_fused_adapter() {
        None
    } else {
        Some(zkai_native_attention_mlp_adapter_component_with_allocator(
            &mut allocator,
            input.adapter_mode,
        ))
    };
    let rmsnorm_component =
        zkai_d128_rmsnorm_public_row_component_with_optional_input_adapter_allocator(
            &mut allocator,
            input
                .adapter_mode
                .uses_rmsnorm_input_fused_adapter()
                .then(rmsnorm_input_adapter_binding),
        );
    let bridge_component =
        zkai_d128_rmsnorm_to_projection_bridge_component_with_allocator(&mut allocator);
    let gate_value_component =
        zkai_d128_gate_value_projection_component_with_allocator(&mut allocator);
    let activation_component = zkai_d128_activation_swiglu_component_with_allocator(&mut allocator);
    let down_projection_component =
        zkai_d128_down_projection_component_with_allocator(&mut allocator);
    let residual_add_component = zkai_d128_residual_add_component_with_allocator(&mut allocator);
    let mut components: Vec<&dyn ComponentProver<SimdBackend>> = vec![&attention_component];
    if let Some(adapter_component) = &adapter_component {
        components.push(adapter_component);
    }
    components.extend([
        &rmsnorm_component as &dyn ComponentProver<SimdBackend>,
        &bridge_component,
        &gate_value_component,
        &activation_component,
        &down_projection_component,
        &residual_add_component,
    ]);
    let stark_proof =
        prove::<SimdBackend, Blake2sM31MerkleChannel>(&components, channel, commitment_scheme)
            .map_err(|error| {
                single_error(format!("native attention plus MLP proving failed: {error}"))
            })?;
    serde_json::to_vec(&NativeSeq32AttentionMlpSingleProofPayload { stark_proof })
        .map_err(|error| VmError::Serialization(error.to_string()))
}

fn verify_single_proof(
    input: &ZkAiNativeSeq32AttentionMlpSingleProofInput,
    proof: &[u8],
) -> Result<bool> {
    if proof.is_empty()
        || proof.len() > ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_PROOF_BYTES
    {
        return Err(single_error("proof byte length outside bounded cap"));
    }
    let payload: NativeSeq32AttentionMlpSingleProofPayload =
        serde_json::from_slice(proof).map_err(|error| VmError::Serialization(error.to_string()))?;
    let stark_proof = payload.stark_proof;
    let config = validate_pcs_config(stark_proof.config, input.adapter_mode)?;
    let preprocessed_ids = combined_preprocessed_column_ids(input.adapter_mode)?;
    let sizes = combined_column_log_sizes(&preprocessed_ids, input.adapter_mode);
    if sizes.len() != EXPECTED_TRACE_COMMITMENT_TREES {
        return Err(single_error(format!(
            "combined trace commitment tree count drift: got {}, expected {}",
            sizes.len(),
            EXPECTED_TRACE_COMMITMENT_TREES
        )));
    }
    if stark_proof.commitments.len() != EXPECTED_PROOF_COMMITMENTS {
        return Err(single_error(format!(
            "proof commitment count mismatch: got {}, expected exactly {}",
            stark_proof.commitments.len(),
            EXPECTED_PROOF_COMMITMENTS
        )));
    }
    let expected_roots = single_commitment_roots(input, config)?;
    if expected_roots.len() != EXPECTED_TRACE_COMMITMENT_TREES {
        return Err(single_error(format!(
            "expected root count drift: got {}, expected {}",
            expected_roots.len(),
            EXPECTED_TRACE_COMMITMENT_TREES
        )));
    }
    for index in 0..EXPECTED_TRACE_COMMITMENT_TREES {
        if stark_proof.commitments[index] != expected_roots[index] {
            return Err(single_error(format!(
                "proof commitment {index} does not match recomputed combined rows"
            )));
        }
    }

    let attention_summary = zkai_attention_kv_native_two_head_seq32_fused_softmax_table_summary(
        &input.attention_source_input,
    )?;
    let channel = &mut Blake2sM31Channel::default();
    let commitment_scheme = &mut CommitmentSchemeVerifier::<Blake2sM31MerkleChannel>::new(config);
    commitment_scheme.commit(stark_proof.commitments[0], &sizes[0], channel);
    commitment_scheme.commit(stark_proof.commitments[1], &sizes[1], channel);
    mix_single_statement(channel, input, &attention_summary);
    let lookup_elements = AttentionKvTwoHeadSeq32FusedSoftmaxTableRelation::draw(channel);
    let component_boxes =
        combined_component_boxes(&preprocessed_ids, input.adapter_mode, lookup_elements);
    let components = component_boxes
        .iter()
        .map(|component| component.as_ref() as &dyn Component)
        .collect::<Vec<_>>();
    commitment_scheme.commit(stark_proof.commitments[2], &sizes[2], channel);
    verify(&components, channel, commitment_scheme, stark_proof)
        .map(|_| true)
        .map_err(|error| single_error(format!("native attention plus MLP proof rejected: {error}")))
}

fn single_commitment_roots(
    input: &ZkAiNativeSeq32AttentionMlpSingleProofInput,
    config: PcsConfig,
) -> Result<
    stwo::core::pcs::TreeVec<
        <Blake2sM31MerkleHasher as stwo::core::vcs_lifted::merkle_hasher::MerkleHasherLifted>::Hash,
    >,
> {
    let attention_summary = zkai_attention_kv_native_two_head_seq32_fused_softmax_table_summary(
        &input.attention_source_input,
    )?;
    let attention_preprocessed =
        zkai_attention_kv_native_two_head_seq32_fused_softmax_table_preprocessed_trace(
            &input.attention_source_input,
            &attention_summary,
        )?;
    let attention_base = zkai_attention_kv_native_two_head_seq32_fused_softmax_table_base_trace(
        &input.attention_source_input,
    )?;
    let preprocessed_ids = combined_preprocessed_column_ids(input.adapter_mode)?;
    let sizes = combined_column_log_sizes(&preprocessed_ids, input.adapter_mode);
    let max_constraint_log_degree_bound =
        combined_max_constraint_log_degree_bound(&preprocessed_ids, input.adapter_mode);
    let twiddles = SimdBackend::precompute_twiddles(
        CanonicCoset::new(
            max_constraint_log_degree_bound + config.fri_config.log_blowup_factor + 1,
        )
        .circle_domain()
        .half_coset,
    );
    let channel = &mut Blake2sM31Channel::default();
    let mut commitment_scheme =
        CommitmentSchemeProver::<SimdBackend, Blake2sM31MerkleChannel>::new(config, &twiddles);
    commitment_scheme.set_store_polynomials_coefficients();
    let preprocessed_trace = combined_preprocessed_trace(input, attention_preprocessed)?;
    if preprocessed_trace.len() != preprocessed_ids.len() {
        return Err(single_error(format!(
            "combined preprocessed trace column count drift: got {}, expected {}",
            preprocessed_trace.len(),
            preprocessed_ids.len()
        )));
    }
    let base_trace = combined_base_trace(input, attention_base.clone())?;
    ensure_trace_shape("preprocessed", &preprocessed_trace, &sizes[0])?;
    ensure_trace_shape("base", &base_trace, &sizes[1])?;
    let mut tree_builder = commitment_scheme.tree_builder();
    tree_builder.extend_evals(preprocessed_trace.clone());
    tree_builder.commit(channel);

    let mut tree_builder = commitment_scheme.tree_builder();
    tree_builder.extend_evals(base_trace);
    tree_builder.commit(channel);

    mix_single_statement(channel, input, &attention_summary);
    let lookup_elements = AttentionKvTwoHeadSeq32FusedSoftmaxTableRelation::draw(channel);
    let attention_preprocessed_len =
        zkai_attention_kv_native_two_head_seq32_fused_softmax_table_preprocessed_column_ids().len();
    let attention_preprocessed_trace = preprocessed_trace[..attention_preprocessed_len].to_vec();
    let (interaction_trace, claimed_sum) =
        zkai_attention_kv_native_two_head_seq32_fused_softmax_table_interaction_trace(
            ATTENTION_LOG_SIZE,
            &attention_base,
            &attention_preprocessed_trace,
            &lookup_elements,
        )?;
    if claimed_sum != SecureField::from(BaseField::from(0u32)) {
        return Err(single_error(
            "attention Softmax-table LogUp expected zero claimed sum in combined proof",
        ));
    }
    ensure_trace_shape("interaction", &interaction_trace, &sizes[2])?;
    let mut tree_builder = commitment_scheme.tree_builder();
    tree_builder.extend_evals(interaction_trace);
    tree_builder.commit(channel);
    if commitment_scheme.roots().len() != sizes.len() {
        return Err(single_error(
            "commitment root count does not match component sizes",
        ));
    }
    Ok(commitment_scheme.roots())
}

fn ensure_trace_shape(
    label: &str,
    trace: &ColumnVec<CircleEvaluation<SimdBackend, BaseField, BitReversedOrder>>,
    log_sizes: &ColumnVec<u32>,
) -> Result<()> {
    if trace.len() != log_sizes.len() {
        return Err(single_error(format!(
            "{label} trace column count mismatch: got {}, expected {}",
            trace.len(),
            log_sizes.len()
        )));
    }
    for (index, (column, expected_log_size)) in trace.iter().zip(log_sizes).enumerate() {
        let actual_log_size = column.domain.log_size();
        if actual_log_size != *expected_log_size {
            return Err(single_error(format!(
                "{label} trace column {index} log-size mismatch: got {actual_log_size}, expected {expected_log_size}"
            )));
        }
    }
    Ok(())
}

fn combined_preprocessed_trace(
    input: &ZkAiNativeSeq32AttentionMlpSingleProofInput,
    mut attention_preprocessed: ColumnVec<
        CircleEvaluation<SimdBackend, BaseField, BitReversedOrder>,
    >,
) -> Result<ColumnVec<CircleEvaluation<SimdBackend, BaseField, BitReversedOrder>>> {
    if input
        .adapter_mode
        .uses_rmsnorm_adjacent_preprocessed_layout()
    {
        attention_preprocessed.extend(zkai_d128_rmsnorm_public_row_trace(
            &input.mlp_input.rmsnorm_input,
        ));
        attention_preprocessed.extend(adapter_rmsnorm_input_fused_preprocessed_trace(input)?);
        attention_preprocessed.extend(mlp_tail_trace(input)?);
        return Ok(attention_preprocessed);
    }
    if input
        .adapter_mode
        .uses_rmsnorm_post_tail_preprocessed_layout()
    {
        attention_preprocessed.extend(zkai_d128_rmsnorm_public_row_trace(
            &input.mlp_input.rmsnorm_input,
        ));
        attention_preprocessed.extend(mlp_tail_trace(input)?);
        attention_preprocessed.extend(adapter_rmsnorm_input_fused_preprocessed_trace(input)?);
        return Ok(attention_preprocessed);
    }
    if input.adapter_mode.uses_rmsnorm_input_fused_adapter() {
        attention_preprocessed.extend(adapter_rmsnorm_input_fused_preprocessed_trace(input)?);
    } else {
        attention_preprocessed.extend(adapter_trace(input)?);
    }
    attention_preprocessed.extend(mlp_trace(input)?);
    Ok(attention_preprocessed)
}

fn combined_base_trace(
    input: &ZkAiNativeSeq32AttentionMlpSingleProofInput,
    mut attention_base: ColumnVec<CircleEvaluation<SimdBackend, BaseField, BitReversedOrder>>,
) -> Result<ColumnVec<CircleEvaluation<SimdBackend, BaseField, BitReversedOrder>>> {
    match input.adapter_mode {
        ZkAiNativeSeq32AttentionMlpAdapterMode::DuplicateBasePreprocessed
        | ZkAiNativeSeq32AttentionMlpAdapterMode::DuplicateBasePreprocessedSelector => {
            attention_base.extend(adapter_trace(input)?);
        }
        ZkAiNativeSeq32AttentionMlpAdapterMode::CompactBaseReferencedFixed => {
            attention_base.extend(adapter_compact_base_trace(input)?);
        }
        ZkAiNativeSeq32AttentionMlpAdapterMode::PreprocessedOutputAnchorFixed => {
            attention_base.extend(adapter_preprocessed_output_anchor_base_trace(input)?);
        }
        ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedFixed
        | ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentFixed
        | ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentLabelProbeA
        | ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentLabelProbeB
        | ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailFixed
        | ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailLabelProbeA
        | ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailLabelProbeB
        | ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedLabelProbeA
        | ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedLabelProbeB => {}
    }
    attention_base.extend(mlp_trace(input)?);
    Ok(attention_base)
}

fn zkai_native_attention_mlp_adapter_component_with_allocator(
    allocator: &mut TraceLocationAllocator,
    adapter_mode: ZkAiNativeSeq32AttentionMlpAdapterMode,
) -> FrameworkComponent<D128AttentionAdapterEval> {
    FrameworkComponent::new(
        allocator,
        D128AttentionAdapterEval {
            log_size: ADAPTER_LOG_SIZE,
            adapter_mode,
            preprocessed_column_ids: adapter_preprocessed_column_id_array(),
        },
        SecureField::from(BaseField::from(0u32)),
    )
}

fn adapter_preprocessed_column_id_array() -> [PreProcessedColumnId; ADAPTER_TRACE_COLUMNS] {
    ADAPTER_COLUMN_IDS.map(preprocessed_column_id)
}

fn adapter_preprocessed_column_ids() -> Vec<PreProcessedColumnId> {
    adapter_preprocessed_column_id_array().into()
}

fn adapter_rmsnorm_input_fused_preprocessed_column_ids() -> Vec<PreProcessedColumnId> {
    [
        ADAPTER_COLUMN_IDS[3],
        ADAPTER_COLUMN_IDS[4],
        ADAPTER_COLUMN_IDS[5],
        ADAPTER_COLUMN_IDS[9],
        ADAPTER_COLUMN_IDS[10],
        ADAPTER_COLUMN_IDS[11],
    ]
    .map(preprocessed_column_id)
    .into()
}

fn rmsnorm_input_adapter_binding() -> ZkAiD128RmsnormInputAdapterBinding {
    let ids = adapter_preprocessed_column_id_array();
    ZkAiD128RmsnormInputAdapterBinding {
        primary_q8_column_id: ids[3].clone(),
        mix_q8_column_id: ids[4].clone(),
        bias_q8_column_id: ids[5].clone(),
        remainder_bit_column_ids: [ids[9].clone(), ids[10].clone(), ids[11].clone()],
        primary_coeff: ADAPTER_PRIMARY_COEFF as u32,
        mix_coeff: ADAPTER_MIX_COEFF as u32,
        denominator: ADAPTER_DENOMINATOR as u32,
    }
}

fn adapter_rmsnorm_input_fused_preprocessed_trace(
    input: &ZkAiNativeSeq32AttentionMlpSingleProofInput,
) -> Result<ColumnVec<CircleEvaluation<SimdBackend, BaseField, BitReversedOrder>>> {
    let domain = CanonicCoset::new(ADAPTER_LOG_SIZE).circle_domain();
    let rows = attention_adapter_rows(input)?;
    let columns: Vec<Vec<BaseField>> = vec![
        rows.iter().map(|row| field_i64(row.primary_q8)).collect(),
        rows.iter().map(|row| field_i64(row.mix_q8)).collect(),
        rows.iter().map(|row| field_i64(row.bias_q8)).collect(),
        rows.iter()
            .map(|row| field_usize((row.floor_remainder_q8 & 1) as usize))
            .collect(),
        rows.iter()
            .map(|row| field_usize(((row.floor_remainder_q8 >> 1) & 1) as usize))
            .collect(),
        rows.iter()
            .map(|row| field_usize(((row.floor_remainder_q8 >> 2) & 1) as usize))
            .collect(),
    ];
    Ok(columns
        .into_iter()
        .map(|column| {
            CircleEvaluation::<SimdBackend, BaseField, NaturalOrder>::new(
                domain,
                BaseColumn::from_iter(column),
            )
            .bit_reverse()
        })
        .collect())
}

fn adapter_trace(
    input: &ZkAiNativeSeq32AttentionMlpSingleProofInput,
) -> Result<ColumnVec<CircleEvaluation<SimdBackend, BaseField, BitReversedOrder>>> {
    let domain = CanonicCoset::new(ADAPTER_LOG_SIZE).circle_domain();
    let rows = attention_adapter_rows(input)?;
    let columns: Vec<Vec<BaseField>> = vec![
        rows.iter().map(|row| field_usize(row.row_index)).collect(),
        rows.iter()
            .map(|row| field_usize(row.primary_source_index))
            .collect(),
        rows.iter()
            .map(|row| field_usize(row.mix_source_index))
            .collect(),
        rows.iter().map(|row| field_i64(row.primary_q8)).collect(),
        rows.iter().map(|row| field_i64(row.mix_q8)).collect(),
        rows.iter().map(|row| field_i64(row.bias_q8)).collect(),
        rows.iter().map(|row| field_i64(row.numerator_q8)).collect(),
        rows.iter().map(|row| field_i64(row.output_q8)).collect(),
        rows.iter()
            .map(|row| field_i64(row.floor_remainder_q8))
            .collect(),
        rows.iter()
            .map(|row| field_usize((row.floor_remainder_q8 & 1) as usize))
            .collect(),
        rows.iter()
            .map(|row| field_usize(((row.floor_remainder_q8 >> 1) & 1) as usize))
            .collect(),
        rows.iter()
            .map(|row| field_usize(((row.floor_remainder_q8 >> 2) & 1) as usize))
            .collect(),
    ];
    Ok(columns
        .into_iter()
        .map(|column| {
            CircleEvaluation::<SimdBackend, BaseField, NaturalOrder>::new(
                domain,
                BaseColumn::from_iter(column),
            )
            .bit_reverse()
        })
        .collect())
}

fn adapter_compact_base_trace(
    input: &ZkAiNativeSeq32AttentionMlpSingleProofInput,
) -> Result<ColumnVec<CircleEvaluation<SimdBackend, BaseField, BitReversedOrder>>> {
    let domain = CanonicCoset::new(ADAPTER_LOG_SIZE).circle_domain();
    let rows = attention_adapter_rows(input)?;
    let columns: Vec<Vec<BaseField>> = vec![
        rows.iter().map(|row| field_i64(row.primary_q8)).collect(),
        rows.iter().map(|row| field_i64(row.mix_q8)).collect(),
        rows.iter().map(|row| field_i64(row.numerator_q8)).collect(),
        rows.iter().map(|row| field_i64(row.output_q8)).collect(),
        rows.iter()
            .map(|row| field_i64(row.floor_remainder_q8))
            .collect(),
        rows.iter()
            .map(|row| field_usize((row.floor_remainder_q8 & 1) as usize))
            .collect(),
        rows.iter()
            .map(|row| field_usize(((row.floor_remainder_q8 >> 1) & 1) as usize))
            .collect(),
        rows.iter()
            .map(|row| field_usize(((row.floor_remainder_q8 >> 2) & 1) as usize))
            .collect(),
    ];
    Ok(columns
        .into_iter()
        .map(|column| {
            CircleEvaluation::<SimdBackend, BaseField, NaturalOrder>::new(
                domain,
                BaseColumn::from_iter(column),
            )
            .bit_reverse()
        })
        .collect())
}

fn adapter_preprocessed_output_anchor_base_trace(
    input: &ZkAiNativeSeq32AttentionMlpSingleProofInput,
) -> Result<ColumnVec<CircleEvaluation<SimdBackend, BaseField, BitReversedOrder>>> {
    let domain = CanonicCoset::new(ADAPTER_LOG_SIZE).circle_domain();
    let rows = attention_adapter_rows(input)?;
    let columns: Vec<Vec<BaseField>> =
        vec![rows.iter().map(|row| field_i64(row.output_q8)).collect()];
    Ok(columns
        .into_iter()
        .map(|column| {
            CircleEvaluation::<SimdBackend, BaseField, NaturalOrder>::new(
                domain,
                BaseColumn::from_iter(column),
            )
            .bit_reverse()
        })
        .collect())
}

fn attention_adapter_rows(
    input: &ZkAiNativeSeq32AttentionMlpSingleProofInput,
) -> Result<Vec<D128AttentionAdapterRow>> {
    if input.attention_source_input.attention_outputs.len() != ATTENTION_ROWS {
        return Err(single_error("adapter attention output row count drift"));
    }
    let mut flat = Vec::with_capacity(ATTENTION_FLAT_CELLS);
    for row in &input.attention_source_input.attention_outputs {
        if row.len() != ATTENTION_WIDTH {
            return Err(single_error("adapter attention output width drift"));
        }
        flat.extend(row.iter().copied());
    }
    if flat.len() != ATTENTION_FLAT_CELLS {
        return Err(single_error("adapter attention flat cell count drift"));
    }
    let mlp_input_values = input
        .mlp_input
        .rmsnorm_input
        .rows
        .iter()
        .map(|row| row.input_q8)
        .collect::<Vec<_>>();
    if mlp_input_values.len() != ADAPTER_WIDTH {
        return Err(single_error("adapter MLP input width drift"));
    }
    let mut rows = Vec::with_capacity(ADAPTER_WIDTH);
    for row_index in 0..ADAPTER_WIDTH {
        let primary_source_index = row_index % ATTENTION_FLAT_CELLS;
        let mix_source_index = (17 * row_index + 11) % ATTENTION_FLAT_CELLS;
        let primary_q8 = flat[primary_source_index];
        let mix_q8 = flat[mix_source_index];
        let bias_q8 = adapter_bias_q8(row_index);
        let numerator_q8 =
            ADAPTER_PRIMARY_COEFF * primary_q8 + ADAPTER_MIX_COEFF * mix_q8 + bias_q8;
        let output_q8 = numerator_q8.div_euclid(ADAPTER_DENOMINATOR);
        let floor_remainder_q8 = numerator_q8.rem_euclid(ADAPTER_DENOMINATOR);
        if floor_remainder_q8 < 0 || floor_remainder_q8 >= ADAPTER_DENOMINATOR {
            return Err(single_error("adapter floor remainder range drift"));
        }
        if output_q8 != mlp_input_values[row_index] {
            return Err(single_error(
                "native adapter output does not match d128 RMSNorm input row",
            ));
        }
        rows.push(D128AttentionAdapterRow {
            row_index,
            primary_source_index,
            mix_source_index,
            primary_q8,
            mix_q8,
            bias_q8,
            numerator_q8,
            output_q8,
            floor_remainder_q8,
        });
    }
    Ok(rows)
}

fn adapter_bias_q8(index: usize) -> i64 {
    ((7 * index + 3) % 9) as i64 - 4
}

fn mlp_trace(
    input: &ZkAiNativeSeq32AttentionMlpSingleProofInput,
) -> Result<ColumnVec<CircleEvaluation<SimdBackend, BaseField, BitReversedOrder>>> {
    let mut trace = zkai_d128_rmsnorm_public_row_trace(&input.mlp_input.rmsnorm_input);
    trace.extend(mlp_tail_trace(input)?);
    Ok(trace)
}

fn mlp_tail_trace(
    input: &ZkAiNativeSeq32AttentionMlpSingleProofInput,
) -> Result<ColumnVec<CircleEvaluation<SimdBackend, BaseField, BitReversedOrder>>> {
    let gate_rows = zkai_d128_gate_value_projection_rows(&input.mlp_input.gate_value_input)?;
    let mut trace =
        zkai_d128_rmsnorm_to_projection_bridge_trace(&input.mlp_input.projection_bridge_input);
    trace.extend(zkai_d128_gate_value_projection_trace(&gate_rows)?);
    trace.extend(zkai_d128_activation_swiglu_trace(
        &input.mlp_input.activation_input,
    )?);
    trace.extend(zkai_d128_down_projection_trace(
        &input.mlp_input.down_projection_input,
    )?);
    trace.extend(zkai_d128_residual_add_trace(
        &input.mlp_input.residual_add_input,
    ));
    Ok(trace)
}

fn combined_preprocessed_column_ids(
    adapter_mode: ZkAiNativeSeq32AttentionMlpAdapterMode,
) -> Result<Vec<PreProcessedColumnId>> {
    let mut ids =
        zkai_attention_kv_native_two_head_seq32_fused_softmax_table_preprocessed_column_ids();
    if adapter_mode.uses_rmsnorm_adjacent_preprocessed_layout() {
        ids.extend(zkai_d128_rmsnorm_public_row_preprocessed_column_ids());
        ids.extend(adapter_rmsnorm_input_fused_preprocessed_column_ids());
        ids.extend(mlp_tail_preprocessed_column_ids());
        return ensure_unique_preprocessed_ids(ids);
    }
    if adapter_mode.uses_rmsnorm_post_tail_preprocessed_layout() {
        ids.extend(zkai_d128_rmsnorm_public_row_preprocessed_column_ids());
        ids.extend(mlp_tail_preprocessed_column_ids());
        ids.extend(adapter_rmsnorm_input_fused_preprocessed_column_ids());
        return ensure_unique_preprocessed_ids(ids);
    }
    if adapter_mode.uses_rmsnorm_input_fused_adapter() {
        ids.extend(adapter_rmsnorm_input_fused_preprocessed_column_ids());
    } else {
        ids.extend(adapter_preprocessed_column_ids());
    }
    ids.extend(zkai_d128_rmsnorm_public_row_preprocessed_column_ids());
    ids.extend(zkai_d128_rmsnorm_to_projection_bridge_preprocessed_column_ids());
    ids.extend(zkai_d128_gate_value_projection_preprocessed_column_ids());
    ids.extend(zkai_d128_activation_swiglu_preprocessed_column_ids());
    ids.extend(zkai_d128_down_projection_preprocessed_column_ids());
    ids.extend(zkai_d128_residual_add_preprocessed_column_ids());
    ensure_unique_preprocessed_ids(ids)
}

fn mlp_tail_preprocessed_column_ids() -> Vec<PreProcessedColumnId> {
    let mut ids = zkai_d128_rmsnorm_to_projection_bridge_preprocessed_column_ids();
    ids.extend(zkai_d128_gate_value_projection_preprocessed_column_ids());
    ids.extend(zkai_d128_activation_swiglu_preprocessed_column_ids());
    ids.extend(zkai_d128_down_projection_preprocessed_column_ids());
    ids.extend(zkai_d128_residual_add_preprocessed_column_ids());
    ids
}

fn ensure_unique_preprocessed_ids(
    ids: Vec<PreProcessedColumnId>,
) -> Result<Vec<PreProcessedColumnId>> {
    let mut seen = BTreeSet::new();
    for id in &ids {
        if !seen.insert(id.id.clone()) {
            return Err(single_error(format!(
                "duplicate combined preprocessed column id: {}",
                id.id
            )));
        }
    }
    Ok(ids)
}

fn combined_max_constraint_log_degree_bound(
    preprocessed_ids: &[PreProcessedColumnId],
    adapter_mode: ZkAiNativeSeq32AttentionMlpAdapterMode,
) -> u32 {
    combined_component_boxes(
        preprocessed_ids,
        adapter_mode,
        AttentionKvTwoHeadSeq32FusedSoftmaxTableRelation::dummy(),
    )
    .iter()
    .map(|component| component.max_constraint_log_degree_bound())
    .max()
    .unwrap_or(0)
}

fn combined_column_log_sizes(
    preprocessed_ids: &[PreProcessedColumnId],
    adapter_mode: ZkAiNativeSeq32AttentionMlpAdapterMode,
) -> stwo::core::pcs::TreeVec<ColumnVec<u32>> {
    let component_boxes = combined_component_boxes(
        preprocessed_ids,
        adapter_mode,
        AttentionKvTwoHeadSeq32FusedSoftmaxTableRelation::dummy(),
    );
    let components = component_boxes
        .iter()
        .map(|component| component.as_ref() as &dyn Component)
        .collect::<Vec<_>>();
    Components {
        components,
        n_preprocessed_columns: preprocessed_ids.len(),
    }
    .column_log_sizes()
}

fn combined_component_boxes(
    preprocessed_ids: &[PreProcessedColumnId],
    adapter_mode: ZkAiNativeSeq32AttentionMlpAdapterMode,
    lookup_elements: AttentionKvTwoHeadSeq32FusedSoftmaxTableRelation,
) -> Vec<Box<dyn Component>> {
    let mut allocator = TraceLocationAllocator::new_with_preprocessed_columns(preprocessed_ids);
    let attention_component = Box::new(
        zkai_attention_kv_native_two_head_seq32_fused_softmax_table_component_with_allocator(
            &mut allocator,
            lookup_elements,
        ),
    );
    let adapter_component = if adapter_mode.uses_rmsnorm_input_fused_adapter() {
        None
    } else {
        Some(
            Box::new(zkai_native_attention_mlp_adapter_component_with_allocator(
                &mut allocator,
                adapter_mode,
            )) as Box<dyn Component>,
        )
    };
    let rmsnorm_component = Box::new(
        zkai_d128_rmsnorm_public_row_component_with_optional_input_adapter_allocator(
            &mut allocator,
            adapter_mode
                .uses_rmsnorm_input_fused_adapter()
                .then(rmsnorm_input_adapter_binding),
        ),
    );
    let bridge_component =
        Box::new(zkai_d128_rmsnorm_to_projection_bridge_component_with_allocator(&mut allocator));
    let gate_value_component = Box::new(zkai_d128_gate_value_projection_component_with_allocator(
        &mut allocator,
    ));
    let activation_component = Box::new(zkai_d128_activation_swiglu_component_with_allocator(
        &mut allocator,
    ));
    let down_projection_component = Box::new(zkai_d128_down_projection_component_with_allocator(
        &mut allocator,
    ));
    let residual_add_component = Box::new(zkai_d128_residual_add_component_with_allocator(
        &mut allocator,
    ));
    let mut components = vec![attention_component as Box<dyn Component>];
    if let Some(adapter_component) = adapter_component {
        components.push(adapter_component);
    }
    components.extend([
        rmsnorm_component as Box<dyn Component>,
        bridge_component as Box<dyn Component>,
        gate_value_component as Box<dyn Component>,
        activation_component as Box<dyn Component>,
        down_projection_component as Box<dyn Component>,
        residual_add_component as Box<dyn Component>,
    ]);
    components
}

fn validate_pcs_config(
    actual: PcsConfig,
    adapter_mode: ZkAiNativeSeq32AttentionMlpAdapterMode,
) -> Result<PcsConfig> {
    let expected = single_pcs_config(adapter_mode)?;
    if actual.pow_bits != expected.pow_bits
        || actual.fri_config.log_blowup_factor != expected.fri_config.log_blowup_factor
        || actual.fri_config.n_queries != expected.fri_config.n_queries
        || actual.fri_config.log_last_layer_degree_bound
            != expected.fri_config.log_last_layer_degree_bound
        || actual.fri_config.fold_step != expected.fri_config.fold_step
        || actual.lifting_log_size != expected.lifting_log_size
    {
        return Err(single_error(
            "PCS config does not match publication-v1 profile with route-specific explicit lifting log size",
        ));
    }
    Ok(expected)
}

fn single_pcs_config(adapter_mode: ZkAiNativeSeq32AttentionMlpAdapterMode) -> Result<PcsConfig> {
    let preprocessed_ids = combined_preprocessed_column_ids(adapter_mode)?;
    let max_constraint_log_degree_bound =
        combined_max_constraint_log_degree_bound(&preprocessed_ids, adapter_mode);
    let mut config = publication_v1_pcs_config();
    let derived_lifting_log_size =
        max_constraint_log_degree_bound + config.fri_config.log_blowup_factor;
    if derived_lifting_log_size != SINGLE_PCS_LIFTING_LOG_SIZE {
        return Err(single_error(format!(
            "single proof PCS lifting log size drift: derived {derived_lifting_log_size}, expected {SINGLE_PCS_LIFTING_LOG_SIZE}"
        )));
    }
    config.lifting_log_size = Some(SINGLE_PCS_LIFTING_LOG_SIZE);
    if publication_v1_pcs_config_matches(&config) {
        return Err(single_error(
            "single proof PCS config unexpectedly matches publication-v1 default",
        ));
    }
    Ok(config)
}

fn mix_single_statement(
    channel: &mut Blake2sM31Channel,
    input: &ZkAiNativeSeq32AttentionMlpSingleProofInput,
    attention_summary: &ZkAiAttentionKvNativeTwoHeadSeq32FusedSoftmaxTableSummary,
) {
    channel.mix_u64(input.attention_lookup_claims as u64);
    channel.mix_u64(input.attention_table_rows as u64);
    channel.mix_u64(input.adapter_row_count as u64);
    channel.mix_u64(input.adapter_trace_cells as u64);
    channel.mix_u64(input.mlp_row_count as u64);
    channel.mix_u64(input.current_two_proof_frontier_typed_bytes as u64);
    channel.mix_u64(input.current_attention_fused_typed_bytes as u64);
    channel.mix_u64(input.current_derived_mlp_fused_typed_bytes as u64);
    channel.mix_u64(input.nanozk_reported_d128_block_proof_bytes as u64);
    channel.mix_u64(input.pcs_lifting_log_size as u64);
    mix_commitment(channel, &input.statement_commitment);
    mix_commitment(channel, &input.attention_statement_commitment);
    mix_commitment(channel, &input.attention_outputs_commitment);
    mix_commitment(channel, &input.mlp_statement_commitment);
    mix_commitment(channel, &input.mlp_input_activation_commitment);
    for entry in &attention_summary.table_multiplicities {
        channel.mix_u64(entry.gap as u64);
        channel.mix_u64(entry.weight.rem_euclid((1i64 << 31) - 1) as u64);
        channel.mix_u64(entry.multiplicity as u64);
    }
}

fn mix_commitment(channel: &mut Blake2sM31Channel, commitment: &str) {
    for chunk in commitment.as_bytes().chunks(8) {
        let mut bytes = [0u8; 8];
        bytes[..chunk.len()].copy_from_slice(chunk);
        channel.mix_u64(u64::from_le_bytes(bytes));
    }
}

fn statement_commitment(input: &ZkAiNativeSeq32AttentionMlpSingleProofInput) -> Result<String> {
    let mut payload = serde_json::json!({
        "adapter_status": input.adapter_status,
        "adapter_row_count": input.adapter_row_count,
        "adapter_trace_cells": input.adapter_trace_cells,
        "adapter_value_columns": input.adapter_value_columns,
        "adapter_remainder_bit_columns": input.adapter_remainder_bit_columns,
        "attention_lookup_claims": input.attention_lookup_claims,
        "attention_outputs_commitment": input.attention_outputs_commitment,
        "attention_proof_version": input.attention_proof_version,
        "attention_public_instance_commitment": input.attention_public_instance_commitment,
        "attention_score_row_commitment": input.attention_score_row_commitment,
        "attention_statement_commitment": input.attention_statement_commitment,
        "attention_table_rows": input.attention_table_rows,
        "attention_weight_table_commitment": input.attention_weight_table_commitment,
        "current_attention_fused_typed_bytes": input.current_attention_fused_typed_bytes,
        "current_derived_mlp_fused_typed_bytes": input.current_derived_mlp_fused_typed_bytes,
        "current_two_proof_frontier_typed_bytes": input.current_two_proof_frontier_typed_bytes,
        "mlp_input_activation_commitment": input.mlp_input_activation_commitment,
        "mlp_output_activation_commitment": input.mlp_output_activation_commitment,
        "mlp_proof_version": input.mlp_proof_version,
        "mlp_public_instance_commitment": input.mlp_public_instance_commitment,
        "mlp_row_count": input.mlp_row_count,
        "mlp_statement_commitment": input.mlp_statement_commitment,
        "nanozk_reported_d128_block_proof_bytes": input.nanozk_reported_d128_block_proof_bytes,
        "operation": "native_seq32_attention_mlp_single_proof_object_probe",
        "pcs_lifting_log_size": input.pcs_lifting_log_size,
        "route_id": input.route_id,
        "target_id": input.target_id,
        "verifier_domain": input.verifier_domain,
    });
    if input.adapter_mode != ZkAiNativeSeq32AttentionMlpAdapterMode::DuplicateBasePreprocessed {
        payload["adapter_mode"] = serde_json::to_value(input.adapter_mode).map_err(|error| {
            VmError::Serialization(format!("failed to serialize adapter mode: {error}"))
        })?;
    }
    let bytes =
        serde_json::to_vec(&payload).map_err(|error| VmError::Serialization(error.to_string()))?;
    Ok(blake2b_commitment_bytes(&bytes, STATEMENT_DOMAIN))
}

fn public_instance_commitment(statement: &str) -> Result<String> {
    let payload = serde_json::json!({
        "operation": "native_seq32_attention_mlp_single_proof_object_probe",
        "route_id": ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_ROUTE_ID,
        "statement_commitment": statement,
    });
    let bytes =
        serde_json::to_vec(&payload).map_err(|error| VmError::Serialization(error.to_string()))?;
    Ok(blake2b_commitment_bytes(&bytes, PUBLIC_INSTANCE_DOMAIN))
}

fn proof_native_parameter_commitment(
    statement: &str,
    adapter_mode: ZkAiNativeSeq32AttentionMlpAdapterMode,
) -> Result<String> {
    let pcs_lifting_log_size = single_pcs_config(adapter_mode)?
        .lifting_log_size
        .ok_or_else(|| {
            single_error("single proof PCS config must pin an explicit lifting log size")
        })?;
    let payload = serde_json::json!({
        "kind": "native-attention-mlp-single-proof-native-parameter-v1",
        "pcs_lifting_log_size": pcs_lifting_log_size,
        "pcs_profile": "publication_v1_with_explicit_lifting_log_size",
        "statement_commitment": statement,
        "trace_commitment_trees": EXPECTED_TRACE_COMMITMENT_TREES,
    });
    let bytes =
        serde_json::to_vec(&payload).map_err(|error| VmError::Serialization(error.to_string()))?;
    Ok(blake2b_commitment_bytes(
        &bytes,
        PROOF_NATIVE_PARAMETER_DOMAIN,
    ))
}

fn blake2b_commitment_bytes(bytes: &[u8], domain: &str) -> String {
    let mut hasher = Blake2bVar::new(32).expect("valid blake2b output length");
    hasher.update(domain.as_bytes());
    hasher.update(&[0]);
    hasher.update(bytes);
    let mut out = [0u8; 32];
    hasher
        .finalize_variable(&mut out)
        .expect("blake2b output length is fixed");
    format!(
        "blake2b-256:{}",
        out.iter()
            .map(|byte| format!("{byte:02x}"))
            .collect::<String>()
    )
}

fn preprocessed_column_id(id: &str) -> PreProcessedColumnId {
    PreProcessedColumnId { id: id.to_string() }
}

fn field_usize(value: usize) -> BaseField {
    BaseField::from(u32::try_from(value).expect("field_usize: value out of u32 range"))
}

fn field_i64(value: i64) -> BaseField {
    BaseField::from(value.rem_euclid(M31_MODULUS) as u32)
}

fn expect_eq(actual: &str, expected: &str, label: &str) -> Result<()> {
    if actual != expected {
        return Err(single_error(format!(
            "{label} mismatch: got `{actual}`, expected `{expected}`"
        )));
    }
    Ok(())
}

fn expect_usize(actual: usize, expected: usize, label: &str) -> Result<()> {
    if actual != expected {
        return Err(single_error(format!(
            "{label} mismatch: got {actual}, expected {expected}"
        )));
    }
    Ok(())
}

fn expect_vec_eq(actual: &[String], expected: &[&str], label: &str) -> Result<()> {
    let expected_strings = expected
        .iter()
        .map(|value| value.to_string())
        .collect::<Vec<_>>();
    if actual != expected_strings {
        return Err(single_error(format!("{label} drift")));
    }
    Ok(())
}

fn single_error(message: impl Into<String>) -> VmError {
    VmError::UnsupportedProof(format!(
        "native attention plus MLP single proof object: {}",
        message.into()
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::stwo_backend::{
        zkai_attention_kv_native_two_head_seq32_fused_softmax_table_source_input_from_json_str,
        zkai_d128_rmsnorm_mlp_fused_input_from_json_str,
    };

    fn fixture_input() -> ZkAiNativeSeq32AttentionMlpSingleProofInput {
        fixture_input_with_mode(ZkAiNativeSeq32AttentionMlpAdapterMode::DuplicateBasePreprocessed)
    }

    fn fixture_input_with_mode(
        adapter_mode: ZkAiNativeSeq32AttentionMlpAdapterMode,
    ) -> ZkAiNativeSeq32AttentionMlpSingleProofInput {
        let attention = zkai_attention_kv_native_two_head_seq32_fused_softmax_table_source_input_from_json_str(
            include_str!(
                "../../docs/engineering/evidence/zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json"
            ),
        )
        .expect("attention source");
        let mlp = zkai_d128_rmsnorm_mlp_fused_input_from_json_str(include_str!(
            "../../docs/engineering/evidence/zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json"
        ))
        .expect("MLP input");
        build_zkai_native_seq32_attention_mlp_single_proof_input_with_adapter_mode(
            attention,
            mlp,
            adapter_mode,
        )
        .expect("single input")
    }

    #[test]
    fn single_proof_input_validates_statement_bound_route() {
        let input = fixture_input();
        assert_eq!(
            input.attention_outputs_commitment,
            SOURCE_ATTENTION_OUTPUTS_COMMITMENT
        );
        assert_eq!(
            input.mlp_input_activation_commitment,
            SEQ32_DERIVED_D128_INPUT_ACTIVATION_COMMITMENT
        );
        assert_eq!(input.adapter_status, EXPECTED_ADAPTER_STATUS);
        assert_eq!(
            input.adapter_mode,
            ZkAiNativeSeq32AttentionMlpAdapterMode::DuplicateBasePreprocessed
        );
        assert_eq!(input.adapter_row_count, ADAPTER_WIDTH);
        assert_eq!(input.adapter_trace_cells, ADAPTER_TRACE_CELLS);
        assert_eq!(
            input.current_two_proof_frontier_typed_bytes,
            CURRENT_TWO_PROOF_FRONTIER_TYPED_BYTES
        );
        validate_single_input(&input).expect("input validates");
    }

    #[test]
    fn compact_adapter_input_references_fixed_columns_and_validates() {
        let input = fixture_input_with_mode(
            ZkAiNativeSeq32AttentionMlpAdapterMode::CompactBaseReferencedFixed,
        );
        assert_eq!(
            input.adapter_mode,
            ZkAiNativeSeq32AttentionMlpAdapterMode::CompactBaseReferencedFixed
        );
        assert_eq!(input.adapter_status, EXPECTED_COMPACT_ADAPTER_STATUS);
        assert_eq!(
            input.adapter_value_columns,
            ADAPTER_COMPACT_BASE_VALUE_COLUMNS
        );
        assert_eq!(input.adapter_trace_cells, ADAPTER_COMPACT_BASE_TRACE_CELLS);
        validate_single_input(&input).expect("compact input validates");

        let preprocessed = adapter_trace(&input).expect("adapter preprocessed");
        let compact = adapter_compact_base_trace(&input).expect("compact base");
        assert_eq!(preprocessed.len(), ADAPTER_TRACE_COLUMNS);
        assert_eq!(compact.len(), ADAPTER_COMPACT_BASE_TRACE_COLUMNS);
    }

    #[test]
    fn compact_adapter_round_trip_verifies_and_rejects_relabeling() {
        let input = fixture_input_with_mode(
            ZkAiNativeSeq32AttentionMlpAdapterMode::CompactBaseReferencedFixed,
        );
        let envelope = prove_zkai_native_seq32_attention_mlp_single_proof_envelope(&input)
            .expect("compact prove");
        assert!(
            verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&envelope)
                .expect("compact verify")
        );

        let mut proof_tampered = envelope.clone();
        proof_tampered.proof[0] ^= 1;
        let proof_tamper_result =
            verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&proof_tampered);
        assert!(matches!(proof_tamper_result, Ok(false) | Err(_)));

        let mut relabeled = envelope;
        relabeled.input.adapter_mode =
            ZkAiNativeSeq32AttentionMlpAdapterMode::DuplicateBasePreprocessedSelector;
        assert!(verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&relabeled).is_err());
    }

    #[test]
    fn preprocessed_output_anchor_adapter_input_uses_one_base_column_and_validates() {
        let input = fixture_input_with_mode(
            ZkAiNativeSeq32AttentionMlpAdapterMode::PreprocessedOutputAnchorFixed,
        );
        assert_eq!(
            input.adapter_mode,
            ZkAiNativeSeq32AttentionMlpAdapterMode::PreprocessedOutputAnchorFixed
        );
        assert_eq!(
            input.adapter_status,
            EXPECTED_PREPROCESSED_OUTPUT_ANCHOR_ADAPTER_STATUS
        );
        assert_eq!(
            input.adapter_value_columns,
            ADAPTER_PREPROCESSED_OUTPUT_ANCHOR_BASE_VALUE_COLUMNS
        );
        assert_eq!(
            input.adapter_trace_cells,
            ADAPTER_PREPROCESSED_OUTPUT_ANCHOR_BASE_TRACE_CELLS
        );
        validate_single_input(&input).expect("preprocessed output-anchor input validates");

        let preprocessed = adapter_trace(&input).expect("adapter preprocessed");
        let output_anchor =
            adapter_preprocessed_output_anchor_base_trace(&input).expect("output anchor base");
        let attention_summary =
            zkai_attention_kv_native_two_head_seq32_fused_softmax_table_summary(
                &input.attention_source_input,
            )
            .expect("attention summary");
        let attention_base =
            zkai_attention_kv_native_two_head_seq32_fused_softmax_table_base_trace(
                &input.attention_source_input,
            )
            .expect("attention base");
        let attention_base_len = attention_base.len();
        let base = combined_base_trace(&input, attention_base).expect("combined base");
        let mlp = mlp_trace(&input).expect("MLP trace");
        assert_eq!(preprocessed.len(), ADAPTER_TRACE_COLUMNS);
        assert_eq!(
            output_anchor.len(),
            ADAPTER_PREPROCESSED_OUTPUT_ANCHOR_BASE_TRACE_COLUMNS
        );
        assert_eq!(
            base.len(),
            attention_base_len + output_anchor.len() + mlp.len()
        );
        assert_eq!(attention_summary.table_rows, input.attention_table_rows);
    }

    #[test]
    fn preprocessed_output_anchor_adapter_round_trip_verifies_and_rejects_relabeling() {
        let input = fixture_input_with_mode(
            ZkAiNativeSeq32AttentionMlpAdapterMode::PreprocessedOutputAnchorFixed,
        );
        let envelope = prove_zkai_native_seq32_attention_mlp_single_proof_envelope(&input)
            .expect("preprocessed output-anchor prove");
        assert!(
            verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&envelope)
                .expect("preprocessed output-anchor verify")
        );

        let mut proof_tampered = envelope.clone();
        proof_tampered.proof[0] ^= 1;
        let proof_tamper_result =
            verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&proof_tampered);
        assert!(matches!(proof_tamper_result, Ok(false) | Err(_)));

        let mut relabeled = envelope;
        relabeled.input.adapter_mode =
            ZkAiNativeSeq32AttentionMlpAdapterMode::CompactBaseReferencedFixed;
        assert!(verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&relabeled).is_err());
    }

    #[test]
    fn rmsnorm_input_fused_adapter_input_uses_no_adapter_base_columns_and_validates() {
        let input =
            fixture_input_with_mode(ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedFixed);
        assert_eq!(
            input.adapter_mode,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedFixed
        );
        assert_eq!(
            input.adapter_status,
            EXPECTED_RMSNORM_INPUT_FUSED_ADAPTER_STATUS
        );
        assert_eq!(
            input.adapter_value_columns,
            ADAPTER_RMSNORM_INPUT_FUSED_BASE_VALUE_COLUMNS
        );
        assert_eq!(
            input.adapter_trace_cells,
            ADAPTER_RMSNORM_INPUT_FUSED_BASE_TRACE_CELLS
        );
        validate_single_input(&input).expect("RMSNorm-input fused adapter input validates");

        let attention_base =
            zkai_attention_kv_native_two_head_seq32_fused_softmax_table_base_trace(
                &input.attention_source_input,
            )
            .expect("attention base");
        let attention_base_len = attention_base.len();
        let base = combined_base_trace(&input, attention_base).expect("combined base");
        let mlp = mlp_trace(&input).expect("MLP trace");
        assert_eq!(base.len(), attention_base_len + mlp.len());
    }

    #[test]
    fn rmsnorm_input_fused_adapter_round_trip_verifies_and_rejects_relabeling() {
        let input =
            fixture_input_with_mode(ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedFixed);
        let envelope = prove_zkai_native_seq32_attention_mlp_single_proof_envelope(&input)
            .expect("fused prove");
        assert!(
            verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&envelope)
                .expect("fused verify")
        );

        let mut proof_tampered = envelope.clone();
        proof_tampered.proof[0] ^= 1;
        let proof_tamper_result =
            verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&proof_tampered);
        assert!(matches!(proof_tamper_result, Ok(false) | Err(_)));

        let mut relabeled = envelope;
        relabeled.input.adapter_mode =
            ZkAiNativeSeq32AttentionMlpAdapterMode::PreprocessedOutputAnchorFixed;
        assert!(verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&relabeled).is_err());
    }

    #[test]
    fn rmsnorm_input_adjacent_layout_keeps_zero_adapter_base_and_reorders_fixed_columns() {
        let input = fixture_input_with_mode(
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentFixed,
        );
        assert_eq!(
            input.adapter_mode,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentFixed
        );
        assert_eq!(input.adapter_trace_cells, 0);
        validate_single_input(&input).expect("adjacent layout input validates");

        let ids =
            combined_preprocessed_column_ids(input.adapter_mode).expect("adjacent layout ids");
        let attention_count =
            zkai_attention_kv_native_two_head_seq32_fused_softmax_table_preprocessed_column_ids()
                .len();
        let rmsnorm_count = zkai_d128_rmsnorm_public_row_preprocessed_column_ids().len();
        let adapter_ids = adapter_rmsnorm_input_fused_preprocessed_column_ids();
        let adjacent_slice = &ids
            [attention_count + rmsnorm_count..attention_count + rmsnorm_count + adapter_ids.len()];
        assert_eq!(adjacent_slice, adapter_ids.as_slice());
    }

    #[test]
    fn rmsnorm_input_post_tail_layout_keeps_zero_adapter_base_and_moves_fixed_columns_after_tail() {
        let input = fixture_input_with_mode(
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailFixed,
        );
        assert_eq!(
            input.adapter_mode,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailFixed
        );
        assert_eq!(input.adapter_trace_cells, 0);
        validate_single_input(&input).expect("post-tail layout input validates");

        let ids = combined_preprocessed_column_ids(input.adapter_mode).expect("post-tail ids");
        let attention_count =
            zkai_attention_kv_native_two_head_seq32_fused_softmax_table_preprocessed_column_ids()
                .len();
        let rmsnorm_count = zkai_d128_rmsnorm_public_row_preprocessed_column_ids().len();
        let tail_count = mlp_tail_preprocessed_column_ids().len();
        let adapter_ids = adapter_rmsnorm_input_fused_preprocessed_column_ids();
        let adapter_start = attention_count + rmsnorm_count + tail_count;
        let post_tail_slice = &ids[adapter_start..adapter_start + adapter_ids.len()];
        assert_eq!(post_tail_slice, adapter_ids.as_slice());
    }

    #[test]
    fn rmsnorm_input_adjacent_adapter_round_trip_verifies_and_rejects_relabeling() {
        let input = fixture_input_with_mode(
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentFixed,
        );
        validate_single_input(&input).expect("adjacent layout input validates");

        let envelope = prove_zkai_native_seq32_attention_mlp_single_proof_envelope(&input)
            .expect("adjacent layout prove");
        assert!(
            verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&envelope)
                .expect("adjacent layout verify")
        );

        let mut proof_tampered = envelope.clone();
        proof_tampered.proof[0] ^= 1;
        let proof_tamper_result =
            verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&proof_tampered);
        assert!(matches!(proof_tamper_result, Ok(false) | Err(_)));

        let mut relabeled = envelope;
        relabeled.input.adapter_mode =
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedFixed;
        assert!(verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&relabeled).is_err());
    }

    #[test]
    fn rmsnorm_input_post_tail_adapter_round_trip_verifies_and_rejects_relabeling() {
        let input = fixture_input_with_mode(
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailFixed,
        );
        validate_single_input(&input).expect("post-tail layout input validates");

        let envelope = prove_zkai_native_seq32_attention_mlp_single_proof_envelope(&input)
            .expect("post-tail layout prove");
        assert!(
            verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&envelope)
                .expect("post-tail layout verify")
        );

        let mut proof_tampered = envelope.clone();
        proof_tampered.proof[0] ^= 1;
        let proof_tamper_result =
            verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&proof_tampered);
        assert!(matches!(proof_tamper_result, Ok(false) | Err(_)));

        let mut relabeled = envelope;
        relabeled.input.adapter_mode =
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentFixed;
        assert!(verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&relabeled).is_err());
    }

    #[test]
    fn rmsnorm_input_post_tail_label_probes_preserve_constraints_but_change_statement() {
        let canonical = fixture_input_with_mode(
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailFixed,
        );
        for mode in [
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailLabelProbeA,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailLabelProbeB,
        ] {
            let input = fixture_input_with_mode(mode);
            assert_eq!(input.adapter_status, canonical.adapter_status);
            assert_eq!(input.adapter_value_columns, canonical.adapter_value_columns);
            assert_eq!(input.adapter_trace_cells, canonical.adapter_trace_cells);
            assert_ne!(input.statement_commitment, canonical.statement_commitment);
            validate_single_input(&input).expect("post-tail label probe input validates");
        }
    }

    #[test]
    fn rmsnorm_input_fused_label_probes_preserve_constraints_but_change_statement() {
        let canonical =
            fixture_input_with_mode(ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedFixed);
        for mode in [
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedLabelProbeA,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedLabelProbeB,
        ] {
            let input = fixture_input_with_mode(mode);
            assert_eq!(input.adapter_status, canonical.adapter_status);
            assert_eq!(input.adapter_value_columns, canonical.adapter_value_columns);
            assert_eq!(input.adapter_trace_cells, canonical.adapter_trace_cells);
            assert_ne!(input.statement_commitment, canonical.statement_commitment);
            validate_single_input(&input).expect("label probe input validates");
        }
    }

    #[test]
    fn rmsnorm_input_fused_label_probe_rejects_relabeling() {
        let mut relabeled = fixture_input_with_mode(
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedLabelProbeA,
        );
        relabeled.adapter_mode = ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedFixed;
        assert!(validate_single_input(&relabeled).is_err());

        let mut cross_labeled = fixture_input_with_mode(
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedLabelProbeB,
        );
        cross_labeled.adapter_mode =
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedLabelProbeA;
        assert!(validate_single_input(&cross_labeled).is_err());
    }

    #[test]
    fn rmsnorm_input_fused_label_probe_round_trip_verifies_and_rejects_tamper() {
        let input = fixture_input_with_mode(
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedLabelProbeA,
        );
        let envelope = prove_zkai_native_seq32_attention_mlp_single_proof_envelope(&input)
            .expect("label probe prove");
        assert!(
            verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&envelope)
                .expect("label probe verify")
        );

        let mut proof_tampered = envelope.clone();
        proof_tampered.proof[0] ^= 1;
        let proof_tamper_result =
            verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&proof_tampered);
        assert!(matches!(proof_tamper_result, Ok(false) | Err(_)));

        let mut relabeled = envelope;
        relabeled.input.adapter_mode =
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedFixed;
        assert!(verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&relabeled).is_err());
    }

    #[test]
    fn legacy_json_without_adapter_mode_defaults_to_duplicate() {
        let input = fixture_input();
        let mut value = serde_json::to_value(&input).expect("input JSON value");
        value
            .as_object_mut()
            .expect("input object")
            .remove("adapter_mode");
        let raw = serde_json::to_string(&value).expect("input JSON string");
        let parsed = zkai_native_seq32_attention_mlp_single_proof_input_from_json_str(&raw)
            .expect("parse input");
        assert_eq!(
            parsed.adapter_mode,
            ZkAiNativeSeq32AttentionMlpAdapterMode::DuplicateBasePreprocessed
        );
        validate_single_input(&parsed).expect("legacy input validates");
    }

    #[test]
    fn single_proof_input_rejects_attention_output_commitment_drift() {
        let mut input = fixture_input();
        input.attention_outputs_commitment =
            "blake2b-256:1111111111111111111111111111111111111111111111111111111111111111"
                .to_string();
        input.statement_commitment = statement_commitment(&input).expect("statement");
        input.public_instance_commitment =
            public_instance_commitment(&input.statement_commitment).expect("public instance");
        input.proof_native_parameter_commitment =
            proof_native_parameter_commitment(&input.statement_commitment, input.adapter_mode)
                .expect("params");
        assert!(validate_single_input(&input).is_err());
    }

    #[test]
    fn single_proof_input_rejects_mlp_input_activation_drift() {
        let mut input = fixture_input();
        input.mlp_input_activation_commitment =
            "blake2b-256:2222222222222222222222222222222222222222222222222222222222222222"
                .to_string();
        input.statement_commitment = statement_commitment(&input).expect("statement");
        input.public_instance_commitment =
            public_instance_commitment(&input.statement_commitment).expect("public instance");
        input.proof_native_parameter_commitment =
            proof_native_parameter_commitment(&input.statement_commitment, input.adapter_mode)
                .expect("params");
        assert!(validate_single_input(&input).is_err());
    }

    #[test]
    fn single_proof_input_rejects_adapter_output_drift() {
        let mut input = fixture_input();
        input.mlp_input.rmsnorm_input.rows[0].input_q8 += 1;
        assert!(validate_single_input(&input).is_err());
    }

    #[test]
    fn combined_preprocessed_columns_are_unique() {
        for mode in [
            ZkAiNativeSeq32AttentionMlpAdapterMode::DuplicateBasePreprocessed,
            ZkAiNativeSeq32AttentionMlpAdapterMode::DuplicateBasePreprocessedSelector,
            ZkAiNativeSeq32AttentionMlpAdapterMode::CompactBaseReferencedFixed,
            ZkAiNativeSeq32AttentionMlpAdapterMode::PreprocessedOutputAnchorFixed,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedFixed,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedLabelProbeA,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedLabelProbeB,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentFixed,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentLabelProbeA,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentLabelProbeB,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailFixed,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailLabelProbeA,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailLabelProbeB,
        ] {
            let ids = combined_preprocessed_column_ids(mode).expect("ids");
            let unique = ids.iter().map(|id| id.id.clone()).collect::<BTreeSet<_>>();
            assert_eq!(ids.len(), unique.len());
        }
    }

    #[test]
    fn adapter_variant_validation_commands_are_self_contained_for_checked_modes() {
        let commands = EXPECTED_SEQ32_ADAPTER_VARIANT_SELECTOR_VALIDATION_COMMANDS;
        for needle in [
            "zkai-native-seq32-attention-mlp-single-proof-2026-05.envelope.json",
            "zkai-native-seq32-attention-mlp-compact-adapter-2026-05.envelope.json",
            "zkai-native-seq32-attention-mlp-output-anchor-adapter-2026-05.envelope.json",
            "zkai-native-seq32-attention-mlp-rmsnorm-input-fused-adapter-2026-05.envelope.json",
            "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-layout-2026-05.envelope.json",
            "zkai-native-seq32-attention-mlp-rmsnorm-post-tail-layout-2026-05.envelope.json",
            "zkai-native-seq32-attention-mlp-adapter-variant-selector-accounting-2026-05.json",
        ] {
            assert!(commands.iter().any(|command| command.contains(needle)));
        }
        for mode in [
            ZkAiNativeSeq32AttentionMlpAdapterMode::CompactBaseReferencedFixed,
            ZkAiNativeSeq32AttentionMlpAdapterMode::PreprocessedOutputAnchorFixed,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedFixed,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentFixed,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailFixed,
        ] {
            assert_eq!(mode.validation_commands(), commands);
        }
        for mode in [
            ZkAiNativeSeq32AttentionMlpAdapterMode::DuplicateBasePreprocessedSelector,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedLabelProbeA,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedLabelProbeB,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentLabelProbeA,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentLabelProbeB,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailLabelProbeA,
            ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailLabelProbeB,
        ] {
            assert_eq!(
                mode.validation_commands(),
                EXPECTED_EXPERIMENTAL_ADAPTER_MODE_VALIDATION_COMMANDS
            );
        }
    }

    #[test]
    fn single_proof_round_trip_verifies_and_rejects_tamper() {
        let input = fixture_input();
        assert_eq!(
            input.statement_commitment,
            statement_commitment(&input).expect("statement")
        );
        assert_eq!(
            input.public_instance_commitment,
            public_instance_commitment(&input.statement_commitment).expect("public instance")
        );
        assert_eq!(
            input.proof_native_parameter_commitment,
            proof_native_parameter_commitment(&input.statement_commitment, input.adapter_mode)
                .expect("params")
        );
        validate_single_input(&input).expect("input validates");

        let envelope =
            prove_zkai_native_seq32_attention_mlp_single_proof_envelope(&input).expect("prove");
        assert!(
            verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&envelope)
                .expect("verify")
        );

        let mut proof_tampered = envelope.clone();
        proof_tampered.proof[0] ^= 1;
        let proof_tamper_result =
            verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&proof_tampered);
        assert!(matches!(proof_tamper_result, Ok(false) | Err(_)));

        let mut public_input_tampered = envelope;
        public_input_tampered.input.public_instance_commitment =
            "blake2b-256:3333333333333333333333333333333333333333333333333333333333333333"
                .to_string();
        assert!(
            verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&public_input_tampered)
                .is_err()
        );
    }
}
