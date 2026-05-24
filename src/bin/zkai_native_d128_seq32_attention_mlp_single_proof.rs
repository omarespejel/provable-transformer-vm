use std::process::ExitCode;

#[cfg(feature = "stwo-backend")]
use std::ffi::OsString;
#[cfg(feature = "stwo-backend")]
use std::fs;
#[cfg(feature = "stwo-backend")]
use std::io::ErrorKind;
#[cfg(feature = "stwo-backend")]
use std::io::{Read, Write};
#[cfg(all(feature = "stwo-backend", unix))]
use std::os::unix::fs::OpenOptionsExt;
#[cfg(feature = "stwo-backend")]
use std::path::{Path, PathBuf};

#[cfg(feature = "stwo-backend")]
use llm_provable_computer::stwo_backend::{
    build_zkai_native_d128_seq32_attention_mlp_single_proof_input,
    build_zkai_native_d128_seq32_attention_mlp_single_proof_input_with_adapter_mode,
    build_zkai_native_d128_seq32_attention_mlp_single_proof_input_with_adapter_mode_and_attempt_profile,
    prove_zkai_native_d128_seq32_attention_mlp_single_proof_envelope,
    sample_zkai_native_d128_seq32_attention_mlp_openings,
    verify_zkai_native_d128_seq32_attention_mlp_single_proof_envelope,
    zkai_attention_kv_native_d128_two_head_seq32_fused_softmax_table_source_input_from_json_str,
    zkai_d128_rmsnorm_mlp_fused_input_from_json_str,
    zkai_native_d128_seq32_attention_mlp_single_proof_envelope_from_json_slice,
    zkai_native_d128_seq32_attention_mlp_single_proof_input_from_json_str,
    ZkAiNativeD128Seq32AttentionMlpAdapterMode,
    ZkAiNativeD128Seq32AttentionMlpAttemptPolicyProfile,
    ZKAI_ATTENTION_KV_NATIVE_D128_TWO_HEAD_SEQ32_BOUNDED_SOFTMAX_TABLE_MAX_INPUT_JSON_BYTES,
    ZKAI_D128_RMSNORM_MLP_FUSED_MAX_JSON_BYTES,
    ZKAI_NATIVE_D128_SEQ32_ATTENTION_MLP_OPENING_SAMPLER_MAX_JSON_BYTES,
    ZKAI_NATIVE_D128_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_ENVELOPE_JSON_BYTES,
    ZKAI_NATIVE_D128_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_INPUT_JSON_BYTES,
};

#[cfg(feature = "stwo-backend")]
const DETERMINISTIC_TEMP_ATTEMPTS: usize = 16;

#[cfg(feature = "stwo-backend")]
fn main() -> ExitCode {
    match run() {
        Ok(summary) => {
            println!("{summary}");
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("{error}");
            ExitCode::from(2)
        }
    }
}

#[cfg(not(feature = "stwo-backend"))]
fn main() -> ExitCode {
    eprintln!("zkai_native_d128_seq32_attention_mlp_single_proof requires --features stwo-backend");
    ExitCode::from(2)
}

#[cfg(feature = "stwo-backend")]
fn run() -> Result<String, String> {
    run_with_args(std::env::args_os().skip(1))
}

#[cfg(feature = "stwo-backend")]
fn run_with_args<I>(args: I) -> Result<String, String>
where
    I: IntoIterator<Item = OsString>,
{
    let mut args = args.into_iter().collect::<Vec<_>>();
    if args.is_empty() {
        return Err(usage());
    }
    let mode = args.remove(0).to_string_lossy().to_string();
    if let Some((adapter_mode, attempt_profile)) = build_input_attempt_profile_mode(mode.as_str()) {
        return build_input_with_adapter_mode_and_attempt_profile(
            args,
            adapter_mode,
            Some(attempt_profile),
        );
    }
    if let Some(adapter_mode) = build_input_adapter_mode(mode.as_str()) {
        return build_input_with_adapter_mode_and_attempt_profile(args, adapter_mode, None);
    }
    match mode.as_str() {
        "prove" => {
            if args.len() != 2 {
                return Err("usage: prove <single-input.json> <envelope.json>".to_string());
            }
            let input_path = PathBuf::from(&args[0]);
            let envelope_path = PathBuf::from(&args[1]);
            let input_raw = read_bounded_utf8(
                &input_path,
                ZKAI_NATIVE_D128_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_INPUT_JSON_BYTES,
                "d128 seq32 native single proof input JSON",
            )?;
            let input =
                zkai_native_d128_seq32_attention_mlp_single_proof_input_from_json_str(&input_raw)
                    .map_err(|error| error.to_string())?;
            let envelope = prove_zkai_native_d128_seq32_attention_mlp_single_proof_envelope(&input)
                .map_err(|error| error.to_string())?;
            let bytes = pretty_json_bytes_with_trailing_newline(
                &envelope,
                ZKAI_NATIVE_D128_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_ENVELOPE_JSON_BYTES,
                "d128 seq32 native single proof envelope JSON",
            )?;
            atomic_write_file(
                &envelope_path,
                &bytes,
                "d128 seq32 native single proof envelope",
            )?;
            Ok(serde_json::json!({
                "schema": "zkai-native-d128-seq32-attention-mlp-single-proof-cli-summary-v1",
                "mode": "prove",
                "envelope_path": envelope_path.display().to_string(),
                "envelope_size_bytes": bytes.len(),
                "proof_size_bytes": envelope.proof.len(),
                "statement_commitment": envelope.input.statement_commitment,
                "public_instance_commitment": envelope.input.public_instance_commitment,
                "adapter_mode": envelope.input.adapter_mode,
                "adapter_status": envelope.input.adapter_status,
                "adapter_trace_cells": envelope.input.adapter_trace_cells,
                "pcs_lifting_log_size": envelope.input.pcs_lifting_log_size,
                "current_two_proof_frontier_typed_bytes": envelope.input.current_two_proof_frontier_typed_bytes,
            })
            .to_string())
        }
        "verify" => {
            if args.len() != 1 {
                return Err("usage: verify <envelope.json>".to_string());
            }
            let envelope_path = PathBuf::from(&args[0]);
            let envelope_bytes = read_bounded_bytes(
                &envelope_path,
                ZKAI_NATIVE_D128_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_ENVELOPE_JSON_BYTES,
                "d128 seq32 native single proof envelope JSON",
            )?;
            let envelope =
                zkai_native_d128_seq32_attention_mlp_single_proof_envelope_from_json_slice(
                    &envelope_bytes,
                )
                .map_err(|error| error.to_string())?;
            let verified =
                verify_zkai_native_d128_seq32_attention_mlp_single_proof_envelope(&envelope)
                    .map_err(|error| error.to_string())?;
            Ok(serde_json::json!({
                "schema": "zkai-native-d128-seq32-attention-mlp-single-proof-cli-summary-v1",
                "mode": "verify",
                "envelope_path": envelope_path.display().to_string(),
                "proof_size_bytes": envelope.proof.len(),
                "verified": verified,
                "adapter_mode": envelope.input.adapter_mode,
                "adapter_status": envelope.input.adapter_status,
                "adapter_trace_cells": envelope.input.adapter_trace_cells,
                "pcs_lifting_log_size": envelope.input.pcs_lifting_log_size,
            })
            .to_string())
        }
        "sample-openings" => {
            if args.len() != 2 {
                return Err("usage: sample-openings <single-input.json> <sampler.json>".to_string());
            }
            let input_path = PathBuf::from(&args[0]);
            let sampler_path = PathBuf::from(&args[1]);
            let input_raw = read_bounded_utf8(
                &input_path,
                ZKAI_NATIVE_D128_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_INPUT_JSON_BYTES,
                "d128 seq32 native single proof input JSON",
            )?;
            let input =
                zkai_native_d128_seq32_attention_mlp_single_proof_input_from_json_str(&input_raw)
                    .map_err(|error| error.to_string())?;
            let sampler = sample_zkai_native_d128_seq32_attention_mlp_openings(&input)
                .map_err(|error| error.to_string())?;
            let bytes = pretty_json_bytes_with_trailing_newline(
                &sampler,
                ZKAI_NATIVE_D128_SEQ32_ATTENTION_MLP_OPENING_SAMPLER_MAX_JSON_BYTES,
                "d128 seq32 native single proof opening sampler JSON",
            )?;
            atomic_write_file(
                &sampler_path,
                &bytes,
                "d128 seq32 native single proof opening sampler",
            )?;
            Ok(serde_json::json!({
                "schema": "zkai-native-d128-seq32-attention-mlp-single-proof-cli-summary-v1",
                "mode": "sample-openings",
                "sampler_path": sampler_path.display().to_string(),
                "sampler_size_bytes": bytes.len(),
                "statement_commitment": sampler.statement_commitment,
                "public_instance_commitment": sampler.public_instance_commitment,
                "adapter_mode": sampler.adapter_mode,
                "adapter_status": sampler.adapter_status,
                "expected_fri_queries": sampler.expected_fri_queries,
                "unique_query_count": sampler.unique_query_count,
                "duplicate_query_count": sampler.duplicate_query_count,
                "query_location_digest": sampler.query_location_digest,
            })
            .to_string())
        }
        _ => Err(format!("unknown mode: {mode}\n{}", usage())),
    }
}

#[cfg(feature = "stwo-backend")]
fn build_input_attempt_profile_mode(
    mode: &str,
) -> Option<(
    ZkAiNativeD128Seq32AttentionMlpAdapterMode,
    ZkAiNativeD128Seq32AttentionMlpAttemptPolicyProfile,
)> {
    match mode {
        "build-input-rmsnorm-fused-adjacent-label-probe-a-compact-transcript" => Some((
            ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentLabelProbeA,
            ZkAiNativeD128Seq32AttentionMlpAttemptPolicyProfile::CompactTranscriptV1,
        )),
        "build-input-rmsnorm-fused-adjacent-label-probe-b-compact-transcript" => Some((
            ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentLabelProbeB,
            ZkAiNativeD128Seq32AttentionMlpAttemptPolicyProfile::CompactTranscriptV1,
        )),
        "build-input-rmsnorm-fused-adjacent-label-probe-a-statement-only-transcript" => Some((
            ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentLabelProbeA,
            ZkAiNativeD128Seq32AttentionMlpAttemptPolicyProfile::StatementOnlyTranscriptV1,
        )),
        "build-input-rmsnorm-fused-adjacent-label-probe-b-statement-only-transcript" => Some((
            ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentLabelProbeB,
            ZkAiNativeD128Seq32AttentionMlpAttemptPolicyProfile::StatementOnlyTranscriptV1,
        )),
        _ => None,
    }
}

#[cfg(feature = "stwo-backend")]
fn build_input_adapter_mode(mode: &str) -> Option<ZkAiNativeD128Seq32AttentionMlpAdapterMode> {
    match mode {
        "build-input" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::DuplicateBasePreprocessed)
        }
        "build-input-model-faithful" => Some(
            ZkAiNativeD128Seq32AttentionMlpAdapterMode::D128AttentionDerivedDuplicateBasePreprocessed,
        ),
        "build-input-compact" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::CompactBaseReferencedFixed)
        }
        "build-input-preprocessed-anchor" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::PreprocessedOutputAnchorFixed)
        }
        "build-input-rmsnorm-fused" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedFixed)
        }
        "build-input-rmsnorm-fused-label-probe-a" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedLabelProbeA)
        }
        "build-input-rmsnorm-fused-label-probe-b" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedLabelProbeB)
        }
        "build-input-rmsnorm-fused-adjacent" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentFixed)
        }
        "build-input-rmsnorm-fused-adjacent-label-probe-a" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentLabelProbeA)
        }
        "build-input-rmsnorm-fused-adjacent-label-probe-b" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentLabelProbeB)
        }
        "build-input-rmsnorm-fused-adjacent-seed-00" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentSeed00)
        }
        "build-input-rmsnorm-fused-adjacent-seed-01" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentSeed01)
        }
        "build-input-rmsnorm-fused-adjacent-seed-02" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentSeed02)
        }
        "build-input-rmsnorm-fused-adjacent-seed-03" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentSeed03)
        }
        "build-input-rmsnorm-fused-adjacent-seed-04" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentSeed04)
        }
        "build-input-rmsnorm-fused-adjacent-seed-05" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentSeed05)
        }
        "build-input-rmsnorm-fused-post-tail" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailFixed)
        }
        "build-input-rmsnorm-fused-post-tail-label-probe-a" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailLabelProbeA)
        }
        "build-input-rmsnorm-fused-post-tail-label-probe-b" => {
            Some(ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailLabelProbeB)
        }
        _ => None,
    }
}

#[cfg(feature = "stwo-backend")]
fn build_input_with_adapter_mode_and_attempt_profile(
    args: Vec<std::ffi::OsString>,
    adapter_mode: ZkAiNativeD128Seq32AttentionMlpAdapterMode,
    attempt_profile: Option<ZkAiNativeD128Seq32AttentionMlpAttemptPolicyProfile>,
) -> Result<String, String> {
    if args.len() != 3 {
        return Err(usage());
    }
    let attention_path = PathBuf::from(&args[0]);
    let mlp_path = PathBuf::from(&args[1]);
    let output_path = PathBuf::from(&args[2]);
    let attention_raw = read_bounded_utf8(
        &attention_path,
        ZKAI_ATTENTION_KV_NATIVE_D128_TWO_HEAD_SEQ32_BOUNDED_SOFTMAX_TABLE_MAX_INPUT_JSON_BYTES,
        "seq32 attention source input JSON",
    )?;
    let attention =
        zkai_attention_kv_native_d128_two_head_seq32_fused_softmax_table_source_input_from_json_str(
            &attention_raw,
        )
        .map_err(|error| error.to_string())?;
    let mlp_raw = read_bounded_utf8(
        &mlp_path,
        ZKAI_D128_RMSNORM_MLP_FUSED_MAX_JSON_BYTES,
        "seq32-derived d128 RMSNorm-MLP fused input JSON",
    )?;
    let mlp = zkai_d128_rmsnorm_mlp_fused_input_from_json_str(&mlp_raw)
        .map_err(|error| error.to_string())?;
    let input = if adapter_mode
        == ZkAiNativeD128Seq32AttentionMlpAdapterMode::DuplicateBasePreprocessed
        && attempt_profile.is_none()
    {
        build_zkai_native_d128_seq32_attention_mlp_single_proof_input(attention, mlp)
            .map_err(|error| error.to_string())?
    } else if let Some(attempt_profile) = attempt_profile {
        build_zkai_native_d128_seq32_attention_mlp_single_proof_input_with_adapter_mode_and_attempt_profile(
            attention,
            mlp,
            adapter_mode,
            attempt_profile,
        )
        .map_err(|error| error.to_string())?
    } else {
        build_zkai_native_d128_seq32_attention_mlp_single_proof_input_with_adapter_mode(
            attention,
            mlp,
            adapter_mode,
        )
        .map_err(|error| error.to_string())?
    };
    let bytes = pretty_json_bytes_with_trailing_newline(
        &input,
        ZKAI_NATIVE_D128_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_INPUT_JSON_BYTES,
        "d128 seq32 native single proof input JSON",
    )?;
    atomic_write_file(&output_path, &bytes, "d128 seq32 native single proof input")?;
    Ok(serde_json::json!({
        "schema": "zkai-native-d128-seq32-attention-mlp-single-proof-cli-summary-v1",
        "mode": "build-input",
        "input_path": output_path.display().to_string(),
        "input_size_bytes": bytes.len(),
        "statement_commitment": input.statement_commitment,
        "public_instance_commitment": input.public_instance_commitment,
        "adapter_mode": input.adapter_mode,
        "adapter_status": input.adapter_status,
        "adapter_trace_cells": input.adapter_trace_cells,
        "pcs_lifting_log_size": input.pcs_lifting_log_size,
        "current_two_proof_frontier_typed_bytes": input.current_two_proof_frontier_typed_bytes,
    })
    .to_string())
}

#[cfg(feature = "stwo-backend")]
fn usage() -> String {
    "usage: zkai_native_d128_seq32_attention_mlp_single_proof \
build-input|build-input-model-faithful|build-input-compact|build-input-preprocessed-anchor|build-input-rmsnorm-fused|build-input-rmsnorm-fused-label-probe-a|build-input-rmsnorm-fused-label-probe-b|build-input-rmsnorm-fused-adjacent|build-input-rmsnorm-fused-adjacent-label-probe-a|build-input-rmsnorm-fused-adjacent-label-probe-b|build-input-rmsnorm-fused-adjacent-label-probe-a-compact-transcript|build-input-rmsnorm-fused-adjacent-label-probe-b-compact-transcript|build-input-rmsnorm-fused-adjacent-label-probe-a-statement-only-transcript|build-input-rmsnorm-fused-adjacent-label-probe-b-statement-only-transcript|build-input-rmsnorm-fused-adjacent-seed-00|build-input-rmsnorm-fused-adjacent-seed-01|build-input-rmsnorm-fused-adjacent-seed-02|build-input-rmsnorm-fused-adjacent-seed-03|build-input-rmsnorm-fused-adjacent-seed-04|build-input-rmsnorm-fused-adjacent-seed-05|build-input-rmsnorm-fused-post-tail|build-input-rmsnorm-fused-post-tail-label-probe-a|build-input-rmsnorm-fused-post-tail-label-probe-b \
<attention-source.json> <mlp-input.json> <single-input.json> | prove <single-input.json> <envelope.json> | verify <envelope.json> | sample-openings <single-input.json> <sampler.json>"
        .to_string()
}

#[cfg(feature = "stwo-backend")]
fn read_bounded_utf8(path: &Path, max_bytes: usize, label: &str) -> Result<String, String> {
    let bytes = read_bounded_bytes(path, max_bytes, label)?;
    String::from_utf8(bytes).map_err(|error| {
        format!(
            "failed to decode {label} {} as UTF-8: {error}",
            path.display()
        )
    })
}

#[cfg(feature = "stwo-backend")]
fn read_bounded_bytes(path: &Path, max_bytes: usize, label: &str) -> Result<Vec<u8>, String> {
    let mut open_options = fs::OpenOptions::new();
    open_options.read(true);
    #[cfg(unix)]
    {
        open_options.custom_flags(libc::O_NOFOLLOW);
    }
    let mut file = open_options
        .open(path)
        .map_err(|error| format!("failed to open {label} {}: {error}", path.display()))?;
    let metadata = file
        .metadata()
        .map_err(|error| format!("failed to stat opened {label} {}: {error}", path.display()))?;
    if !metadata.is_file() {
        return Err(format!("{label} {} is not a regular file", path.display()));
    }
    if metadata.len() > max_bytes as u64 {
        return Err(format!(
            "{label} exceeds max size: got {} bytes, limit {max_bytes} bytes",
            metadata.len()
        ));
    }
    let mut raw = Vec::new();
    std::io::Read::by_ref(&mut file)
        .take(max_bytes.saturating_add(1) as u64)
        .read_to_end(&mut raw)
        .map_err(|error| format!("failed to read {label} {}: {error}", path.display()))?;
    if raw.len() > max_bytes {
        return Err(format!(
            "{label} exceeds max size: got more than {max_bytes} bytes, limit {max_bytes} bytes"
        ));
    }
    Ok(raw)
}

#[cfg(feature = "stwo-backend")]
fn pretty_json_bytes_with_trailing_newline<T: serde::Serialize>(
    value: &T,
    max_bytes: usize,
    label: &str,
) -> Result<Vec<u8>, String> {
    let mut bytes = serde_json::to_vec_pretty(value)
        .map_err(|error| format!("failed to encode {label}: {error}"))?;
    bytes.push(b'\n');
    if bytes.len() > max_bytes {
        return Err(format!(
            "{label} exceeds max size after serialization: got {}, limit {}",
            bytes.len(),
            max_bytes
        ));
    }
    Ok(bytes)
}

#[cfg(feature = "stwo-backend")]
fn atomic_write_file(path: &Path, bytes: &[u8], label: &str) -> Result<(), String> {
    reject_symlinked_ancestors(path, label)?;
    if let Some(parent) = path
        .parent()
        .filter(|parent| !parent.as_os_str().is_empty())
    {
        ensure_directory_without_symlinks(parent, label)?;
        reject_symlinked_ancestors(path, label)?;
    }
    let metadata = fs::symlink_metadata(path).ok();
    if metadata
        .as_ref()
        .is_some_and(|meta| meta.file_type().is_symlink())
    {
        return Err(format!(
            "refusing to overwrite symlink for {label}: {}",
            path.display()
        ));
    }
    let parent = path
        .parent()
        .filter(|parent| !parent.as_os_str().is_empty())
        .unwrap_or_else(|| Path::new("."));
    let file_name = path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| {
            format!(
                "{label} output path has no UTF-8 file name: {}",
                path.display()
            )
        })?;
    for attempt in 0..DETERMINISTIC_TEMP_ATTEMPTS {
        let tmp_path = parent.join(format!(".{file_name}.tmp.{attempt}"));
        reject_symlinked_ancestors(&tmp_path, label)?;
        if !write_new_file(&tmp_path, bytes)? {
            continue;
        }
        return publish_temp_file(&tmp_path, path, label);
    }
    Err(format!(
        "deterministic temp file collision for {label}: all {} slots occupied under {}",
        DETERMINISTIC_TEMP_ATTEMPTS,
        parent.display()
    ))
}

#[cfg(feature = "stwo-backend")]
fn write_new_file(path: &Path, bytes: &[u8]) -> Result<bool, String> {
    let mut options = fs::OpenOptions::new();
    options.write(true).create_new(true);
    #[cfg(unix)]
    {
        options.mode(0o600);
    }
    let mut file = match options.open(path) {
        Ok(file) => file,
        Err(error) if error.kind() == ErrorKind::AlreadyExists => {
            return Ok(false);
        }
        Err(error) => {
            return Err(format!(
                "failed to create temp file {}: {error}",
                path.display()
            ));
        }
    };
    file.write_all(bytes)
        .map_err(|error| format!("failed to write temp file {}: {error}", path.display()))?;
    file.sync_all()
        .map_err(|error| format!("failed to sync temp file {}: {error}", path.display()))?;
    Ok(true)
}

#[cfg(feature = "stwo-backend")]
fn reject_symlinked_ancestors(path: &Path, label: &str) -> Result<(), String> {
    #[cfg(not(unix))]
    {
        let _ = path;
        let _ = label;
        Ok(())
    }
    #[cfg(unix)]
    {
        for ancestor in path.ancestors().skip(1) {
            if ancestor.as_os_str().is_empty() {
                continue;
            }
            match fs::symlink_metadata(ancestor) {
                Ok(metadata) if metadata.file_type().is_symlink() => {
                    return Err(format!(
                        "refusing symlinked parent for {label}: {}",
                        ancestor.display()
                    ));
                }
                Ok(_) => {}
                Err(error) if error.kind() == ErrorKind::NotFound => {}
                Err(error) => {
                    return Err(format!(
                        "failed to inspect parent {} for {label}: {error}",
                        ancestor.display()
                    ));
                }
            }
        }
        Ok(())
    }
}

#[cfg(feature = "stwo-backend")]
fn ensure_directory_without_symlinks(path: &Path, label: &str) -> Result<(), String> {
    if path.as_os_str().is_empty() {
        return Ok(());
    }
    let mut current = PathBuf::new();
    for component in path.components() {
        match component {
            std::path::Component::RootDir => current.push(component.as_os_str()),
            std::path::Component::CurDir => {
                if current.as_os_str().is_empty() {
                    current.push(".");
                }
            }
            std::path::Component::Normal(part) => {
                current.push(part);
                ensure_existing_or_created_dir(&current, label)?;
            }
            std::path::Component::ParentDir => {
                return Err(format!(
                    "refusing parent-directory component in {label} path: {}",
                    path.display()
                ));
            }
            std::path::Component::Prefix(_) => {
                return Err(format!(
                    "unsupported path prefix for {label}: {}",
                    path.display()
                ));
            }
        }
    }
    Ok(())
}

#[cfg(feature = "stwo-backend")]
fn ensure_existing_or_created_dir(path: &Path, label: &str) -> Result<(), String> {
    match fs::symlink_metadata(path) {
        Ok(metadata) if metadata.file_type().is_symlink() => Err(format!(
            "refusing symlinked directory for {label}: {}",
            path.display()
        )),
        Ok(metadata) if metadata.is_dir() => Ok(()),
        Ok(_) => Err(format!(
            "refusing non-directory parent for {label}: {}",
            path.display()
        )),
        Err(error) if error.kind() == ErrorKind::NotFound => {
            match fs::create_dir(path) {
                Ok(()) => {}
                Err(create_error) if create_error.kind() == ErrorKind::AlreadyExists => {}
                Err(create_error) => {
                    return Err(format!(
                        "failed to create directory {} for {label}: {create_error}",
                        path.display()
                    ));
                }
            }
            match fs::symlink_metadata(path) {
                Ok(metadata) if metadata.file_type().is_symlink() => Err(format!(
                    "refusing symlinked directory for {label}: {}",
                    path.display()
                )),
                Ok(metadata) if metadata.is_dir() => Ok(()),
                Ok(_) => Err(format!(
                    "refusing non-directory parent for {label}: {}",
                    path.display()
                )),
                Err(stat_error) => Err(format!(
                    "failed to inspect created directory {} for {label}: {stat_error}",
                    path.display()
                )),
            }
        }
        Err(error) => Err(format!(
            "failed to inspect parent directory {} for {label}: {error}",
            path.display()
        )),
    }
}

#[cfg(feature = "stwo-backend")]
fn publish_temp_file(tmp_path: &Path, path: &Path, label: &str) -> Result<(), String> {
    match fs::rename(tmp_path, path) {
        Ok(()) => Ok(()),
        Err(first_error)
            if matches!(
                first_error.kind(),
                ErrorKind::AlreadyExists | ErrorKind::PermissionDenied
            ) =>
        {
            match existing_non_symlink_destination(path, label) {
                Ok(true) => {
                    if let Err(remove_error) = fs::remove_file(path) {
                        let _ = fs::remove_file(tmp_path);
                        return Err(format!(
                            "failed to replace existing {label} {} after publish error {first_error}: {remove_error}",
                            path.display()
                        ));
                    }
                }
                Ok(false) => {}
                Err(error) => {
                    let _ = fs::remove_file(tmp_path);
                    return Err(error);
                }
            }
            if let Err(second_error) = fs::rename(tmp_path, path) {
                let _ = fs::remove_file(tmp_path);
                return Err(format!(
                    "failed to publish replacement {label} {} after handling existing destination: {second_error}",
                    path.display()
                ));
            }
            Ok(())
        }
        Err(error) => {
            let _ = fs::remove_file(tmp_path);
            Err(format!(
                "failed to move {} to {}: {error}",
                tmp_path.display(),
                path.display()
            ))
        }
    }
}

#[cfg(feature = "stwo-backend")]
fn existing_non_symlink_destination(path: &Path, label: &str) -> Result<bool, String> {
    match fs::symlink_metadata(path) {
        Ok(metadata) if metadata.file_type().is_symlink() => Err(format!(
            "refusing to overwrite symlink for {label}: {}",
            path.display()
        )),
        Ok(metadata) if metadata.is_file() => Ok(true),
        Ok(_) => Err(format!(
            "refusing to replace non-file destination for {label}: {}",
            path.display()
        )),
        Err(error) if error.kind() == ErrorKind::NotFound => Ok(false),
        Err(error) => Err(format!(
            "failed to inspect destination {} for {label}: {error}",
            path.display()
        )),
    }
}

#[cfg(all(test, feature = "stwo-backend"))]
mod tests {
    use super::*;
    #[cfg(unix)]
    use std::os::unix::fs::symlink;

    fn tempdir() -> tempfile::TempDir {
        tempfile::Builder::new()
            .prefix("zkai-seq32-single-proof-cli-test-")
            .tempdir_in(std::env::current_dir().expect("current dir"))
            .expect("tempdir")
    }

    #[test]
    fn build_input_command_routing_maps_adapter_modes() {
        let cases = [
            (
                "build-input",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::DuplicateBasePreprocessed,
            ),
            (
                "build-input-compact",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::CompactBaseReferencedFixed,
            ),
            (
                "build-input-preprocessed-anchor",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::PreprocessedOutputAnchorFixed,
            ),
            (
                "build-input-rmsnorm-fused",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedFixed,
            ),
            (
                "build-input-rmsnorm-fused-label-probe-a",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedLabelProbeA,
            ),
            (
                "build-input-rmsnorm-fused-label-probe-b",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedLabelProbeB,
            ),
            (
                "build-input-rmsnorm-fused-adjacent",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentFixed,
            ),
            (
                "build-input-rmsnorm-fused-adjacent-label-probe-a",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentLabelProbeA,
            ),
            (
                "build-input-rmsnorm-fused-adjacent-label-probe-b",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentLabelProbeB,
            ),
            (
                "build-input-rmsnorm-fused-adjacent-seed-00",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentSeed00,
            ),
            (
                "build-input-rmsnorm-fused-adjacent-seed-01",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentSeed01,
            ),
            (
                "build-input-rmsnorm-fused-adjacent-seed-02",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentSeed02,
            ),
            (
                "build-input-rmsnorm-fused-adjacent-seed-03",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentSeed03,
            ),
            (
                "build-input-rmsnorm-fused-adjacent-seed-04",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentSeed04,
            ),
            (
                "build-input-rmsnorm-fused-adjacent-seed-05",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentSeed05,
            ),
            (
                "build-input-rmsnorm-fused-post-tail",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailFixed,
            ),
            (
                "build-input-rmsnorm-fused-post-tail-label-probe-a",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailLabelProbeA,
            ),
            (
                "build-input-rmsnorm-fused-post-tail-label-probe-b",
                ZkAiNativeD128Seq32AttentionMlpAdapterMode::RmsnormInputFusedPostTailLabelProbeB,
            ),
        ];
        for (command, expected) in cases {
            assert_eq!(build_input_adapter_mode(command), Some(expected));
        }
        assert_eq!(
            build_input_adapter_mode("build-input-rmsnorm-fused-typo"),
            None
        );
    }

    #[test]
    fn sample_openings_command_rejects_wrong_arg_count() {
        let error = run_with_args([
            OsString::from("sample-openings"),
            OsString::from("only-input.json"),
        ])
        .expect_err("sample-openings requires input and output paths");
        assert_eq!(
            error,
            "usage: sample-openings <single-input.json> <sampler.json>"
        );
    }

    #[test]
    fn atomic_write_file_creates_nested_directory_without_symlink() {
        let tmp = tempdir();
        let output = tmp.path().join("nested").join("out.json");
        atomic_write_file(&output, b"{\"ok\":true}\n", "test output").expect("atomic write");
        let contents = fs::read_to_string(output).expect("read output");
        assert_eq!(contents, "{\"ok\":true}\n");
    }

    #[test]
    fn atomic_write_file_skips_stale_temp_slot() {
        let tmp = tempdir();
        let output = tmp.path().join("out.json");
        let stale = tmp.path().join(".out.json.tmp.0");
        fs::write(&stale, b"stale\n").expect("stale temp");
        atomic_write_file(&output, b"fresh\n", "test output").expect("atomic write");
        let contents = fs::read_to_string(&output).expect("read output");
        assert_eq!(contents, "fresh\n");
        let stale_contents = fs::read_to_string(&stale).expect("read stale temp");
        assert_eq!(stale_contents, "stale\n");
        assert!(!tmp.path().join(".out.json.tmp.1").exists());
    }

    #[cfg(unix)]
    #[test]
    fn atomic_write_file_rejects_symlink_target() {
        let tmp = tempdir();
        let target = tmp.path().join("target.json");
        fs::write(&target, b"target").expect("target");
        let link = tmp.path().join("link.json");
        symlink(&target, &link).expect("symlink");
        let error =
            atomic_write_file(&link, b"{}", "test output").expect_err("symlink must reject");
        assert!(error.contains("symlink"));
    }

    #[cfg(unix)]
    #[test]
    fn atomic_write_file_rejects_symlink_parent() {
        let tmp = tempdir();
        let real_parent = tmp.path().join("real");
        fs::create_dir(&real_parent).expect("real parent");
        let link_parent = tmp.path().join("link-parent");
        symlink(&real_parent, &link_parent).expect("symlink parent");
        let output = link_parent.join("out.json");
        let error = atomic_write_file(&output, b"{}", "test output")
            .expect_err("symlinked parent must reject");
        assert!(error.contains("symlink"));
        assert!(!real_parent.join("out.json").exists());
    }
}
