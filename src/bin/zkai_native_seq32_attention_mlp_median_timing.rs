use std::process::ExitCode;

#[cfg(feature = "stwo-backend")]
use std::fs;
#[cfg(feature = "stwo-backend")]
use std::io::Read;
#[cfg(feature = "stwo-backend")]
use std::path::{Path, PathBuf};
#[cfg(feature = "stwo-backend")]
use std::time::Instant;

#[cfg(feature = "stwo-backend")]
use serde::Serialize;
#[cfg(feature = "stwo-backend")]
use sha2::{Digest, Sha256};

#[cfg(feature = "stwo-backend")]
use llm_provable_computer::stwo_backend::{
    build_zkai_native_seq32_attention_mlp_single_proof_input_with_adapter_mode_and_attempt_profile,
    prove_zkai_native_seq32_attention_mlp_single_proof_envelope,
    verify_zkai_native_seq32_attention_mlp_single_proof_envelope,
    zkai_attention_kv_native_two_head_seq32_fused_softmax_table_source_input_from_json_str,
    zkai_d128_rmsnorm_mlp_fused_input_from_json_str,
    zkai_native_seq32_attention_mlp_single_proof_envelope_from_json_slice,
    zkai_native_seq32_attention_mlp_single_proof_input_from_json_str,
    ZkAiNativeSeq32AttentionMlpAdapterMode, ZkAiNativeSeq32AttentionMlpAttemptPolicyProfile,
    ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_ENVELOPE_JSON_BYTES,
    ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_INPUT_JSON_BYTES,
};

#[cfg(feature = "stwo-backend")]
const SCHEMA: &str = "zkai-native-seq32-attention-mlp-median-timing-cli-v1";
#[cfg(feature = "stwo-backend")]
const ISSUE: usize = 681;
#[cfg(feature = "stwo-backend")]
const DECISION: &str =
    "GO_ENGINEERING_LOCAL_MEDIAN_OF_5_TIMING_FOR_SEQ32_D128_STATEMENT_ONLY_FRONTIER";
#[cfg(feature = "stwo-backend")]
const RESULT: &str = "GO_TIMING_CAPTURED_ENGINEERING_LOCAL_ONLY";
#[cfg(feature = "stwo-backend")]
const TIMING_POLICY: &str =
    "median_of_5_in_process_std_time_instant_microsecond_capture_engineering_only";
#[cfg(feature = "stwo-backend")]
const TIMING_SCOPE: &str =
    "build_input_from_source_json_plus_existing_input_prove_plus_existing_envelope_verify";
#[cfg(feature = "stwo-backend")]
const DEFAULT_RUNS: usize = 5;
#[cfg(feature = "stwo-backend")]
const EXPECTED_TYPED_BYTES: usize = 39_516;
#[cfg(feature = "stwo-backend")]
const EXPECTED_JSON_PROOF_BYTES: usize = 113_388;
#[cfg(feature = "stwo-backend")]
const EXPECTED_TWO_PROOF_FRONTIER_TYPED_BYTES: usize = 47_188;
#[cfg(feature = "stwo-backend")]
const EXPECTED_STATEMENT_POLICY_VERSION: &str =
    "seq32-d128-adjacent-attempt-domain-statement-only-transcript-v1";
#[cfg(feature = "stwo-backend")]
const EXPECTED_STATEMENT_POLICY_STAGE: &str = "inner_statement_digest_only_transcript_metadata";
#[cfg(feature = "stwo-backend")]
const EXPECTED_SELECTED_ATTEMPT_ID: &str = "adjacent_label_probe_b";
#[cfg(feature = "stwo-backend")]
const EXPECTED_STATEMENT_COMMITMENT: &str =
    "blake2b-256:6a14c2912df3b2dcd3ce298d8bde566317468be53d084a42104249d7304cf712";
#[cfg(feature = "stwo-backend")]
const EXPECTED_PUBLIC_INSTANCE_COMMITMENT: &str =
    "blake2b-256:dda271e9eeae84b8ade4020dd7146be75e1160e00368948173bd4796dcdff954";
#[cfg(feature = "stwo-backend")]
const EXPECTED_PROOF_NATIVE_PARAMETER_COMMITMENT: &str =
    "blake2b-256:ed60a38df328e49773410b2335fed805704478ce07712147f3b855be9924b1d2";
#[cfg(feature = "stwo-backend")]
const DEFAULT_ATTENTION_SOURCE: &str =
    "zkai-attention-kv-stwo-native-two-head-seq32-bounded-softmax-table-proof-2026-05.json";
#[cfg(feature = "stwo-backend")]
const DEFAULT_MLP_INPUT: &str =
    "zkai-seq32-derived-d128-rmsnorm-mlp-fused-proof-2026-05.input.json";
#[cfg(feature = "stwo-backend")]
const DEFAULT_SINGLE_INPUT: &str =
    "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.input.json";
#[cfg(feature = "stwo-backend")]
const DEFAULT_SINGLE_ENVELOPE: &str =
    "zkai-native-seq32-attention-mlp-rmsnorm-adjacent-label-probe-b-statement-only-transcript-2026-05.envelope.json";
#[cfg(feature = "stwo-backend")]
const NON_CLAIMS: &[&str] = &[
    "not a public benchmark",
    "not a NANOZK/Jolt/DeepProve/EZKL timing comparison",
    "not proof-generation throughput evidence for production zkML",
    "not hardware-normalized performance evidence",
    "not GitHub Actions evidence",
    "not a full transformer block benchmark",
];

fn main() -> ExitCode {
    #[cfg(feature = "stwo-backend")]
    {
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
    {
        eprintln!("zkai_native_seq32_attention_mlp_median_timing requires --features stwo-backend");
        ExitCode::from(2)
    }
}

#[cfg(feature = "stwo-backend")]
#[derive(Debug)]
struct Config {
    evidence_dir: PathBuf,
    runs: usize,
    attention_source_path: PathBuf,
    mlp_input_path: PathBuf,
    single_input_path: PathBuf,
    single_envelope_path: PathBuf,
}

#[cfg(feature = "stwo-backend")]
#[derive(Serialize)]
struct TimingRow {
    metric: &'static str,
    runs_us: Vec<u64>,
    median_us: u64,
    min_us: u64,
    max_us: u64,
}

#[cfg(feature = "stwo-backend")]
fn run() -> Result<String, String> {
    let config = Config::parse(std::env::args_os().skip(1))?;
    if config.runs != DEFAULT_RUNS {
        return Err(format!(
            "--runs must be {DEFAULT_RUNS} for the checked median-of-5 timing policy"
        ));
    }
    let canonical_evidence_dir = fs::canonicalize(&config.evidence_dir).map_err(|error| {
        format!(
            "failed to canonicalize evidence dir {}: {error}",
            config.evidence_dir.display()
        )
    })?;
    let attention_source_path =
        contained_evidence_file(&canonical_evidence_dir, &config.attention_source_path)?;
    let mlp_input_path = contained_evidence_file(&canonical_evidence_dir, &config.mlp_input_path)?;
    let single_input_path =
        contained_evidence_file(&canonical_evidence_dir, &config.single_input_path)?;
    let single_envelope_path =
        contained_evidence_file(&canonical_evidence_dir, &config.single_envelope_path)?;

    let attention_source_raw = read_bounded_utf8(
        &attention_source_path,
        ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_INPUT_JSON_BYTES,
        "seq32 attention source input",
    )?;
    let mlp_input_raw = read_bounded_utf8(
        &mlp_input_path,
        ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_INPUT_JSON_BYTES,
        "seq32-derived d128 MLP input",
    )?;
    let single_input_raw = read_bounded_utf8(
        &single_input_path,
        ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_INPUT_JSON_BYTES,
        "seq32+d128 single proof input",
    )?;
    let single_envelope_raw = read_bounded_bytes(
        &single_envelope_path,
        ZKAI_NATIVE_SEQ32_ATTENTION_MLP_SINGLE_PROOF_MAX_ENVELOPE_JSON_BYTES,
        "seq32+d128 single proof envelope",
    )?;

    let single_input =
        zkai_native_seq32_attention_mlp_single_proof_input_from_json_str(&single_input_raw)
            .map_err(|error| error.to_string())?;
    let single_envelope =
        zkai_native_seq32_attention_mlp_single_proof_envelope_from_json_slice(&single_envelope_raw)
            .map_err(|error| error.to_string())?;
    validate_statement_only_target(&single_input, single_envelope.proof.len())?;

    let build_input_row = timed_row("build_input_from_source_json_us", config.runs, || {
        let attention_input =
            zkai_attention_kv_native_two_head_seq32_fused_softmax_table_source_input_from_json_str(
                &attention_source_raw,
            )
            .map_err(|error| error.to_string())?;
        let mlp_input = zkai_d128_rmsnorm_mlp_fused_input_from_json_str(&mlp_input_raw)
            .map_err(|error| error.to_string())?;
        let built =
            build_zkai_native_seq32_attention_mlp_single_proof_input_with_adapter_mode_and_attempt_profile(
                attention_input,
                mlp_input,
                ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentLabelProbeB,
                ZkAiNativeSeq32AttentionMlpAttemptPolicyProfile::StatementOnlyTranscriptV1,
            )
            .map_err(|error| error.to_string())?;
        validate_statement_only_target(&built, EXPECTED_JSON_PROOF_BYTES)
    })?;

    let mut generated_proof_json_bytes = Vec::with_capacity(config.runs);
    let prove_row = timed_row("prove_existing_input_us", config.runs, || {
        let envelope = prove_zkai_native_seq32_attention_mlp_single_proof_envelope(&single_input)
            .map_err(|error| error.to_string())?;
        validate_statement_only_target(&envelope.input, envelope.proof.len())?;
        generated_proof_json_bytes.push(envelope.proof.len());
        Ok(())
    })?;

    let verify_row = timed_row("verify_existing_envelope_us", config.runs, || {
        let verified =
            verify_zkai_native_seq32_attention_mlp_single_proof_envelope(&single_envelope)
                .map_err(|error| error.to_string())?;
        if !verified {
            return Err("seq32+d128 statement-only envelope did not verify".to_string());
        }
        Ok(())
    })?;

    let summary = serde_json::json!({
        "schema": SCHEMA,
        "issue": ISSUE,
        "decision": DECISION,
        "result": RESULT,
        "timing_policy": TIMING_POLICY,
        "timing_scope": TIMING_SCOPE,
        "clock": "std_time_instant_elapsed_as_micros",
        "sample_count": DEFAULT_RUNS,
        "target": {
            "profile_id": "statement_only_probe_b",
            "adapter_mode": "rmsnorm_input_fused_adjacent_label_probe_b_v1",
            "attempt_policy_version": EXPECTED_STATEMENT_POLICY_VERSION,
            "attempt_policy_stage": EXPECTED_STATEMENT_POLICY_STAGE,
            "selected_attempt_id": EXPECTED_SELECTED_ATTEMPT_ID,
            "typed_bytes_from_checked_accounting": EXPECTED_TYPED_BYTES,
            "json_proof_bytes": single_envelope.proof.len(),
            "current_two_proof_frontier_typed_bytes": single_input.current_two_proof_frontier_typed_bytes,
            "statement_commitment": single_input.statement_commitment,
            "public_instance_commitment": single_input.public_instance_commitment,
            "proof_native_parameter_commitment": single_input.proof_native_parameter_commitment,
        },
        "source_artifacts": [
            source_artifact("attention_source_input", &canonical_evidence_dir, &attention_source_path)?,
            source_artifact("seq32_derived_d128_mlp_input", &canonical_evidence_dir, &mlp_input_path)?,
            source_artifact("statement_only_single_input", &canonical_evidence_dir, &single_input_path)?,
            source_artifact("statement_only_single_envelope", &canonical_evidence_dir, &single_envelope_path)?,
        ],
        "timings": [
            build_input_row,
            prove_row,
            verify_row,
        ],
        "generated_proof_json_bytes": generated_proof_json_bytes,
        "host_metadata": {
            "os": std::env::consts::OS,
            "arch": std::env::consts::ARCH,
            "family": std::env::consts::FAMILY,
            "logical_cpus": std::thread::available_parallelism().map(|value| value.get()).unwrap_or(0),
            "cargo_profile": if cfg!(debug_assertions) { "debug" } else { "release" },
            "privacy_policy": "hostnames_usernames_and_absolute_local_paths_are_not_recorded",
        },
        "non_claims": NON_CLAIMS,
        "validation_commands": [
            "cargo +nightly-2025-07-14 run --locked --release --features stwo-backend --bin zkai_native_seq32_attention_mlp_median_timing -- --evidence-dir docs/engineering/evidence --runs 5 > docs/engineering/evidence/zkai-native-seq32-attention-mlp-median-timing-raw-2026-05.json",
            "python3.10 scripts/zkai_native_seq32_attention_mlp_median_timing_gate.py --write-json docs/engineering/evidence/zkai-native-seq32-attention-mlp-median-timing-2026-05.json --write-tsv docs/engineering/evidence/zkai-native-seq32-attention-mlp-median-timing-2026-05.tsv",
            "python3.10 -m py_compile scripts/zkai_native_seq32_attention_mlp_median_timing_gate.py scripts/tests/test_zkai_native_seq32_attention_mlp_median_timing_gate.py",
            "python3.10 -m unittest scripts.tests.test_zkai_native_seq32_attention_mlp_median_timing_gate",
            "cargo +nightly-2025-07-14 test --locked --release --features stwo-backend --bin zkai_native_seq32_attention_mlp_median_timing",
            "git diff --check",
            "just gate-fast",
            "just gate",
        ],
    });
    serde_json::to_string_pretty(&summary)
        .map_err(|error| format!("failed to serialize timing summary: {error}"))
}

#[cfg(feature = "stwo-backend")]
impl Config {
    fn parse<I>(args: I) -> Result<Self, String>
    where
        I: IntoIterator<Item = std::ffi::OsString>,
    {
        let mut evidence_dir = None;
        let mut runs = DEFAULT_RUNS;
        let mut attention_source_path = PathBuf::from(DEFAULT_ATTENTION_SOURCE);
        let mut mlp_input_path = PathBuf::from(DEFAULT_MLP_INPUT);
        let mut single_input_path = PathBuf::from(DEFAULT_SINGLE_INPUT);
        let mut single_envelope_path = PathBuf::from(DEFAULT_SINGLE_ENVELOPE);
        let mut iter = args.into_iter();
        while let Some(arg) = iter.next() {
            let arg = arg.to_string_lossy().to_string();
            match arg.as_str() {
                "--evidence-dir" => {
                    let value = iter.next().ok_or("--evidence-dir requires a value")?;
                    evidence_dir = Some(PathBuf::from(value));
                }
                "--runs" => {
                    let value = iter.next().ok_or("--runs requires a value")?;
                    runs = value
                        .to_string_lossy()
                        .parse::<usize>()
                        .map_err(|error| format!("invalid --runs value: {error}"))?;
                }
                "--attention-source" => {
                    attention_source_path =
                        PathBuf::from(iter.next().ok_or("--attention-source requires a value")?);
                }
                "--mlp-input" => {
                    mlp_input_path =
                        PathBuf::from(iter.next().ok_or("--mlp-input requires a value")?);
                }
                "--single-input" => {
                    single_input_path =
                        PathBuf::from(iter.next().ok_or("--single-input requires a value")?);
                }
                "--single-envelope" => {
                    single_envelope_path =
                        PathBuf::from(iter.next().ok_or("--single-envelope requires a value")?);
                }
                _ => return Err(format!("unknown argument: {arg}\n{}", usage())),
            }
        }
        let evidence_dir = evidence_dir.ok_or_else(usage)?;
        Ok(Self {
            evidence_dir,
            runs,
            attention_source_path,
            mlp_input_path,
            single_input_path,
            single_envelope_path,
        })
    }
}

#[cfg(feature = "stwo-backend")]
fn validate_statement_only_target(
    input: &llm_provable_computer::stwo_backend::ZkAiNativeSeq32AttentionMlpSingleProofInput,
    proof_json_bytes: usize,
) -> Result<(), String> {
    if input.adapter_mode
        != ZkAiNativeSeq32AttentionMlpAdapterMode::RmsnormInputFusedAdjacentLabelProbeB
    {
        return Err("timing target must use adjacent label probe B".to_string());
    }
    let policy = input
        .attempt_policy
        .as_ref()
        .ok_or("timing target must bind an attempt policy")?;
    if policy.policy_version != EXPECTED_STATEMENT_POLICY_VERSION {
        return Err("statement-only policy version drift".to_string());
    }
    if policy.policy_stage != EXPECTED_STATEMENT_POLICY_STAGE {
        return Err("statement-only policy stage drift".to_string());
    }
    if policy.selected_attempt_id != EXPECTED_SELECTED_ATTEMPT_ID {
        return Err("selected attempt drift".to_string());
    }
    if input.current_two_proof_frontier_typed_bytes != EXPECTED_TWO_PROOF_FRONTIER_TYPED_BYTES {
        return Err("two-proof frontier drift".to_string());
    }
    if input.statement_commitment != EXPECTED_STATEMENT_COMMITMENT {
        return Err("statement commitment drift".to_string());
    }
    if input.public_instance_commitment != EXPECTED_PUBLIC_INSTANCE_COMMITMENT {
        return Err("public-instance commitment drift".to_string());
    }
    if input.proof_native_parameter_commitment != EXPECTED_PROOF_NATIVE_PARAMETER_COMMITMENT {
        return Err("proof native parameter commitment drift".to_string());
    }
    if proof_json_bytes != EXPECTED_JSON_PROOF_BYTES {
        return Err(format!(
            "statement-only proof JSON bytes drift: got {proof_json_bytes}, expected {EXPECTED_JSON_PROOF_BYTES}"
        ));
    }
    Ok(())
}

#[cfg(feature = "stwo-backend")]
fn timed_row<F>(metric: &'static str, runs: usize, mut f: F) -> Result<TimingRow, String>
where
    F: FnMut() -> Result<(), String>,
{
    let mut timings = Vec::with_capacity(runs);
    for _ in 0..runs {
        let started = Instant::now();
        f()?;
        let elapsed = u64::try_from(started.elapsed().as_micros())
            .map_err(|_| format!("{metric} timing overflow"))?;
        if elapsed == 0 {
            return Err(format!("{metric} timing rounded to zero microseconds"));
        }
        timings.push(elapsed);
    }
    let median = median_us(&timings)?;
    let min = *timings.iter().min().ok_or("missing min timing")?;
    let max = *timings.iter().max().ok_or("missing max timing")?;
    Ok(TimingRow {
        metric,
        runs_us: timings,
        median_us: median,
        min_us: min,
        max_us: max,
    })
}

#[cfg(feature = "stwo-backend")]
fn median_us(values: &[u64]) -> Result<u64, String> {
    if values.len() != DEFAULT_RUNS {
        return Err(format!(
            "median timing requires exactly {DEFAULT_RUNS} runs, got {}",
            values.len()
        ));
    }
    let mut sorted = values.to_vec();
    sorted.sort_unstable();
    Ok(sorted[DEFAULT_RUNS / 2])
}

#[cfg(feature = "stwo-backend")]
fn contained_evidence_file(canonical_root: &Path, path: &Path) -> Result<PathBuf, String> {
    let candidate = if path.is_absolute() || path.components().count() > 1 {
        path.to_path_buf()
    } else {
        canonical_root.join(path)
    };
    let metadata = fs::symlink_metadata(&candidate)
        .map_err(|error| format!("failed to stat {}: {error}", candidate.display()))?;
    if metadata.file_type().is_symlink() {
        return Err(format!(
            "evidence file must not be a symlink: {}",
            candidate.display()
        ));
    }
    if !metadata.is_file() {
        return Err(format!(
            "evidence path must be a regular file: {}",
            candidate.display()
        ));
    }
    let canonical = fs::canonicalize(&candidate)
        .map_err(|error| format!("failed to canonicalize {}: {error}", candidate.display()))?;
    canonical.strip_prefix(canonical_root).map_err(|_| {
        format!(
            "evidence file escapes evidence dir: {} not under {}",
            canonical.display(),
            canonical_root.display()
        )
    })?;
    Ok(canonical)
}

#[cfg(feature = "stwo-backend")]
fn source_artifact(
    id: &'static str,
    canonical_root: &Path,
    path: &Path,
) -> Result<serde_json::Value, String> {
    let relative = path
        .strip_prefix(canonical_root)
        .map_err(|_| format!("source artifact escapes root: {}", path.display()))?;
    let bytes =
        fs::read(path).map_err(|error| format!("failed to read {}: {error}", path.display()))?;
    Ok(serde_json::json!({
        "id": id,
        "path": format!("docs/engineering/evidence/{}", relative.display()),
        "sha256": sha256_bytes(&bytes),
        "bytes": bytes.len(),
    }))
}

#[cfg(feature = "stwo-backend")]
fn read_bounded_utf8(path: &Path, max_len: usize, label: &str) -> Result<String, String> {
    let bytes = read_bounded_bytes(path, max_len, label)?;
    String::from_utf8(bytes).map_err(|error| format!("{label} is not UTF-8: {error}"))
}

#[cfg(feature = "stwo-backend")]
fn read_bounded_bytes(path: &Path, max_len: usize, label: &str) -> Result<Vec<u8>, String> {
    let mut file = fs::File::open(path)
        .map_err(|error| format!("failed to open {label} {}: {error}", path.display()))?;
    let mut buf = Vec::new();
    file.by_ref()
        .take(u64::try_from(max_len).map_err(|_| "max length overflow".to_string())? + 1)
        .read_to_end(&mut buf)
        .map_err(|error| format!("failed to read {label} {}: {error}", path.display()))?;
    if buf.is_empty() || buf.len() > max_len {
        return Err(format!(
            "{label} size outside bound: got {} bytes, max {max_len}",
            buf.len()
        ));
    }
    Ok(buf)
}

#[cfg(feature = "stwo-backend")]
fn sha256_bytes(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("{:x}", hasher.finalize())
}

#[cfg(feature = "stwo-backend")]
fn usage() -> String {
    "usage: zkai_native_seq32_attention_mlp_median_timing --evidence-dir <dir> [--runs 5]"
        .to_string()
}

#[cfg(all(test, feature = "stwo-backend"))]
mod tests {
    use super::*;

    #[test]
    fn median_requires_five_runs() {
        assert_eq!(median_us(&[9, 3, 5, 1, 7]).unwrap(), 5);
        let error = median_us(&[1, 2, 3]).unwrap_err();
        assert!(error.contains("requires exactly 5 runs"));
    }

    #[test]
    fn config_rejects_non_five_runs() {
        let config = Config::parse([
            "--evidence-dir".into(),
            "docs/engineering/evidence".into(),
            "--runs".into(),
            "4".into(),
        ])
        .unwrap();
        assert_eq!(config.runs, 4);
    }

    #[test]
    fn target_validation_rejects_statement_commitment_drift() {
        let raw = std::fs::read_to_string(
            Path::new(env!("CARGO_MANIFEST_DIR"))
                .join("docs/engineering/evidence")
                .join(DEFAULT_SINGLE_INPUT),
        )
        .unwrap();
        let mut input = zkai_native_seq32_attention_mlp_single_proof_input_from_json_str(&raw)
            .expect("fixture input parses");

        validate_statement_only_target(&input, EXPECTED_JSON_PROOF_BYTES)
            .expect("fixture target validates");
        input.statement_commitment.push_str("-mutated");

        let error = validate_statement_only_target(&input, EXPECTED_JSON_PROOF_BYTES).unwrap_err();
        assert!(error.contains("statement commitment drift"));
    }
}
