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
    prove_zkai_attention_kv_native_d256_two_head_seq32_bounded_softmax_table_envelope,
    prove_zkai_attention_kv_native_d256_two_head_seq32_fused_softmax_table_envelope,
    prove_zkai_attention_kv_native_d256_two_head_seq32_softmax_table_lookup_envelope,
    verify_zkai_attention_kv_native_d256_two_head_seq32_bounded_softmax_table_envelope,
    verify_zkai_attention_kv_native_d256_two_head_seq32_fused_softmax_table_envelope,
    verify_zkai_attention_kv_native_d256_two_head_seq32_softmax_table_lookup_envelope,
    zkai_attention_kv_native_d256_two_head_seq32_bounded_softmax_table_envelope_from_json_slice,
    zkai_attention_kv_native_d256_two_head_seq32_bounded_softmax_table_input_from_json_str,
    zkai_attention_kv_native_d256_two_head_seq32_fused_softmax_table_envelope_from_json_slice,
    zkai_attention_kv_native_d256_two_head_seq32_fused_softmax_table_source_input_from_json_str,
    zkai_attention_kv_native_d256_two_head_seq32_softmax_table_lookup_envelope_from_json_slice,
    zkai_attention_kv_native_d256_two_head_seq32_softmax_table_lookup_source_input_from_json_str,
    ZKAI_ATTENTION_KV_NATIVE_D256_TWO_HEAD_SEQ32_BOUNDED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D256_TWO_HEAD_SEQ32_BOUNDED_SOFTMAX_TABLE_MAX_INPUT_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D256_TWO_HEAD_SEQ32_FUSED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D256_TWO_HEAD_SEQ32_SOFTMAX_TABLE_LOOKUP_MAX_ENVELOPE_JSON_BYTES,
};

#[cfg(feature = "stwo-backend")]
const SCHEMA: &str = "zkai-attention-kv-d256-two-head-seq32-median-timing-cli-v1";
#[cfg(feature = "stwo-backend")]
const ISSUE: usize = 715;
#[cfg(feature = "stwo-backend")]
const DECISION: &str = "GO_D256_TWO_HEAD_SEQ32_ENGINEERING_LOCAL_MEDIAN_OF_5_TIMING_CAPTURED";
#[cfg(feature = "stwo-backend")]
const TIMING_POLICY: &str =
    "median_of_5_in_process_std_time_instant_microsecond_capture_engineering_only";
#[cfg(feature = "stwo-backend")]
const TIMING_SCOPE: &str =
    "existing_typed_source_input_prove_functions_plus_existing_typed_envelope_verify_functions";
#[cfg(feature = "stwo-backend")]
const DEFAULT_RUNS: usize = 5;
#[cfg(feature = "stwo-backend")]
const SOURCE_INPUT_PATH: &str =
    "zkai-attention-kv-stwo-native-d256-two-head-seq32-bounded-softmax-table-proof-2026-05.json";
#[cfg(feature = "stwo-backend")]
const SOURCE_ENVELOPE_PATH: &str =
    "zkai-attention-kv-stwo-native-d256-two-head-seq32-bounded-softmax-table-proof-2026-05.envelope.json";
#[cfg(feature = "stwo-backend")]
const SIDECAR_ENVELOPE_PATH: &str =
    "zkai-attention-kv-stwo-native-d256-two-head-seq32-softmax-table-logup-sidecar-proof-2026-05.envelope.json";
#[cfg(feature = "stwo-backend")]
const FUSED_ENVELOPE_PATH: &str =
    "zkai-attention-kv-stwo-native-d256-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json";
#[cfg(feature = "stwo-backend")]
const EXPECTED_SOURCE_PROOF_BYTES: usize = 816_627;
#[cfg(feature = "stwo-backend")]
const EXPECTED_SIDECAR_PROOF_BYTES: usize = 34_914;
#[cfg(feature = "stwo-backend")]
const EXPECTED_FUSED_PROOF_BYTES: usize = 821_398;
#[cfg(feature = "stwo-backend")]
const EXPECTED_SOURCE_PLUS_SIDECAR_PROOF_BYTES: usize = 851_541;
#[cfg(feature = "stwo-backend")]
const EXPECTED_LOOKUP_CLAIMS: usize = 1_184;
#[cfg(feature = "stwo-backend")]
const EXPECTED_TRACE_ROWS: usize = 2_048;
#[cfg(feature = "stwo-backend")]
const EXPECTED_STATEMENT_COMMITMENT: &str =
    "blake2b-256:be89d181dd43a0dce9f47d1165533945c7334e71e5b185a99e3a4565044f1864";
#[cfg(feature = "stwo-backend")]
const NON_CLAIMS: &[&str] = &[
    "not a public benchmark",
    "not an external-system timing comparison",
    "not hardware-normalized performance evidence",
    "not production throughput evidence",
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
        eprintln!(
            "zkai_attention_kv_d256_two_head_seq32_median_timing requires --features stwo-backend"
        );
        ExitCode::from(2)
    }
}

#[cfg(feature = "stwo-backend")]
#[derive(Debug)]
struct Config {
    evidence_dir: PathBuf,
    runs: usize,
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

    let evidence_dir = fs::canonicalize(&config.evidence_dir).map_err(|error| {
        format!(
            "failed to canonicalize evidence dir {}: {error}",
            config.evidence_dir.display()
        )
    })?;
    let source_input_path = contained_evidence_file(&evidence_dir, SOURCE_INPUT_PATH)?;
    let source_envelope_path = contained_evidence_file(&evidence_dir, SOURCE_ENVELOPE_PATH)?;
    let sidecar_envelope_path = contained_evidence_file(&evidence_dir, SIDECAR_ENVELOPE_PATH)?;
    let fused_envelope_path = contained_evidence_file(&evidence_dir, FUSED_ENVELOPE_PATH)?;

    let source_input_raw = read_bounded_utf8(
        &source_input_path,
        ZKAI_ATTENTION_KV_NATIVE_D256_TWO_HEAD_SEQ32_BOUNDED_SOFTMAX_TABLE_MAX_INPUT_JSON_BYTES,
        "d256 source input",
    )?;
    let source_envelope_raw = read_bounded_bytes(
        &source_envelope_path,
        ZKAI_ATTENTION_KV_NATIVE_D256_TWO_HEAD_SEQ32_BOUNDED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
        "d256 source envelope",
    )?;
    let sidecar_envelope_raw = read_bounded_bytes(
        &sidecar_envelope_path,
        ZKAI_ATTENTION_KV_NATIVE_D256_TWO_HEAD_SEQ32_SOFTMAX_TABLE_LOOKUP_MAX_ENVELOPE_JSON_BYTES,
        "d256 sidecar envelope",
    )?;
    let fused_envelope_raw = read_bounded_bytes(
        &fused_envelope_path,
        ZKAI_ATTENTION_KV_NATIVE_D256_TWO_HEAD_SEQ32_FUSED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
        "d256 fused envelope",
    )?;

    let source_input =
        zkai_attention_kv_native_d256_two_head_seq32_bounded_softmax_table_input_from_json_str(
            &source_input_raw,
        )
        .map_err(|error| error.to_string())?;
    let sidecar_input =
        zkai_attention_kv_native_d256_two_head_seq32_softmax_table_lookup_source_input_from_json_str(
            &source_input_raw,
        )
        .map_err(|error| error.to_string())?;
    let fused_input =
        zkai_attention_kv_native_d256_two_head_seq32_fused_softmax_table_source_input_from_json_str(
            &source_input_raw,
        )
        .map_err(|error| error.to_string())?;
    let source_envelope =
        zkai_attention_kv_native_d256_two_head_seq32_bounded_softmax_table_envelope_from_json_slice(
            &source_envelope_raw,
        )
        .map_err(|error| error.to_string())?;
    let sidecar_envelope =
        zkai_attention_kv_native_d256_two_head_seq32_softmax_table_lookup_envelope_from_json_slice(
            &sidecar_envelope_raw,
        )
        .map_err(|error| error.to_string())?;
    let fused_envelope =
        zkai_attention_kv_native_d256_two_head_seq32_fused_softmax_table_envelope_from_json_slice(
            &fused_envelope_raw,
        )
        .map_err(|error| error.to_string())?;

    validate_static_target(
        source_input.statement_commitment.as_str(),
        source_input.score_row_count,
        source_input.trace_row_count,
        source_envelope.proof.len(),
        sidecar_envelope.proof.len(),
        fused_envelope.proof.len(),
        fused_envelope
            .fused_summary
            .source_plus_sidecar_raw_proof_bytes,
    )?;

    let mut generated_source_proof_bytes = Vec::with_capacity(config.runs);
    let source_prove_row = timed_row("source_prove_existing_input_us", config.runs, || {
        let envelope =
            prove_zkai_attention_kv_native_d256_two_head_seq32_bounded_softmax_table_envelope(
                &source_input,
            )
            .map_err(|error| error.to_string())?;
        generated_source_proof_bytes.push(envelope.proof.len());
        validate_proof_len(
            "source generated proof",
            envelope.proof.len(),
            EXPECTED_SOURCE_PROOF_BYTES,
        )
    })?;

    let mut generated_sidecar_proof_bytes = Vec::with_capacity(config.runs);
    let sidecar_prove_row = timed_row("sidecar_prove_existing_input_us", config.runs, || {
        let envelope =
            prove_zkai_attention_kv_native_d256_two_head_seq32_softmax_table_lookup_envelope(
                &sidecar_input,
            )
            .map_err(|error| error.to_string())?;
        generated_sidecar_proof_bytes.push(envelope.proof.len());
        validate_proof_len(
            "sidecar generated proof",
            envelope.proof.len(),
            EXPECTED_SIDECAR_PROOF_BYTES,
        )
    })?;

    let mut generated_fused_proof_bytes = Vec::with_capacity(config.runs);
    let fused_prove_row = timed_row("fused_prove_existing_input_us", config.runs, || {
        let envelope =
            prove_zkai_attention_kv_native_d256_two_head_seq32_fused_softmax_table_envelope(
                &fused_input,
            )
            .map_err(|error| error.to_string())?;
        generated_fused_proof_bytes.push(envelope.proof.len());
        validate_proof_len(
            "fused generated proof",
            envelope.proof.len(),
            EXPECTED_FUSED_PROOF_BYTES,
        )
    })?;

    let source_verify_row = timed_row("source_verify_existing_envelope_us", config.runs, || {
        require_verified(
            verify_zkai_attention_kv_native_d256_two_head_seq32_bounded_softmax_table_envelope(
                &source_envelope,
            ),
            "source verifier",
        )
    })?;
    let sidecar_verify_row = timed_row("sidecar_verify_existing_envelope_us", config.runs, || {
        require_verified(
            verify_zkai_attention_kv_native_d256_two_head_seq32_softmax_table_lookup_envelope(
                &sidecar_envelope,
            ),
            "sidecar verifier",
        )
    })?;
    let fused_verify_row = timed_row("fused_verify_existing_envelope_us", config.runs, || {
        require_verified(
            verify_zkai_attention_kv_native_d256_two_head_seq32_fused_softmax_table_envelope(
                &fused_envelope,
            ),
            "fused verifier",
        )
    })?;

    let split_prove_median = source_prove_row
        .median_us
        .checked_add(sidecar_prove_row.median_us)
        .ok_or("split prove median overflow")?;
    let split_verify_median = source_verify_row
        .median_us
        .checked_add(sidecar_verify_row.median_us)
        .ok_or("split verify median overflow")?;

    let summary = serde_json::json!({
        "schema": SCHEMA,
        "issue": ISSUE,
        "decision": DECISION,
        "timing_policy": TIMING_POLICY,
        "timing_scope": TIMING_SCOPE,
        "clock": "std_time_instant_elapsed_as_micros",
        "sample_count": DEFAULT_RUNS,
        "target": {
            "profile_id": "d256_two_head_seq32",
            "key_width": 256,
            "value_width": 256,
            "head_count": 2,
            "steps_per_head": 32,
            "source_proof_bytes": EXPECTED_SOURCE_PROOF_BYTES,
            "sidecar_proof_bytes": EXPECTED_SIDECAR_PROOF_BYTES,
            "source_plus_sidecar_raw_proof_bytes": EXPECTED_SOURCE_PLUS_SIDECAR_PROOF_BYTES,
            "fused_proof_bytes": EXPECTED_FUSED_PROOF_BYTES,
            "lookup_claims": EXPECTED_LOOKUP_CLAIMS,
            "trace_rows": EXPECTED_TRACE_ROWS,
            "statement_commitment": EXPECTED_STATEMENT_COMMITMENT,
        },
        "source_artifacts": [
            source_artifact("source_input", &evidence_dir, &source_input_path)?,
            source_artifact("source_envelope", &evidence_dir, &source_envelope_path)?,
            source_artifact("sidecar_envelope", &evidence_dir, &sidecar_envelope_path)?,
            source_artifact("fused_envelope", &evidence_dir, &fused_envelope_path)?,
        ],
        "timings": [
            source_prove_row,
            sidecar_prove_row,
            fused_prove_row,
            source_verify_row,
            sidecar_verify_row,
            fused_verify_row,
        ],
        "comparisons": {
            "source_plus_sidecar_prove_median_us": split_prove_median,
            "fused_prove_median_us": fused_prove_row.median_us,
            "fused_minus_source_plus_sidecar_prove_median_us": fused_prove_row.median_us as i128 - split_prove_median as i128,
            "fused_to_source_plus_sidecar_prove_median_ratio": round6(fused_prove_row.median_us as f64 / split_prove_median as f64),
            "source_plus_sidecar_verify_median_us": split_verify_median,
            "fused_verify_median_us": fused_verify_row.median_us,
            "fused_minus_source_plus_sidecar_verify_median_us": fused_verify_row.median_us as i128 - split_verify_median as i128,
            "fused_to_source_plus_sidecar_verify_median_ratio": round6(fused_verify_row.median_us as f64 / split_verify_median as f64),
        },
        "generated_proof_bytes": {
            "source_runs": generated_source_proof_bytes,
            "sidecar_runs": generated_sidecar_proof_bytes,
            "fused_runs": generated_fused_proof_bytes,
        },
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
            "cargo +nightly-2025-07-14 run --locked --release --features stwo-backend --bin zkai_attention_kv_d256_two_head_seq32_median_timing -- --evidence-dir docs/engineering/evidence --runs 5 > docs/engineering/evidence/zkai-attention-kv-d256-two-head-seq32-median-timing-raw-2026-05.json",
            "cargo +nightly-2025-07-14 test --locked --release --features stwo-backend --bin zkai_attention_kv_d256_two_head_seq32_median_timing",
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
        let mut args = args.into_iter();
        while let Some(arg) = args.next() {
            let arg = arg.to_string_lossy().to_string();
            match arg.as_str() {
                "--evidence-dir" => {
                    evidence_dir = Some(PathBuf::from(
                        args.next().ok_or("--evidence-dir requires a value")?,
                    ));
                }
                "--runs" => {
                    runs = args
                        .next()
                        .ok_or("--runs requires a value")?
                        .to_string_lossy()
                        .parse::<usize>()
                        .map_err(|error| format!("invalid --runs value: {error}"))?;
                }
                "--help" | "-h" => return Err(usage()),
                _ => return Err(format!("unknown argument: {arg}\n{}", usage())),
            }
        }
        Ok(Self {
            evidence_dir: evidence_dir.ok_or_else(usage)?,
            runs,
        })
    }
}

#[cfg(feature = "stwo-backend")]
fn usage() -> String {
    "usage: zkai_attention_kv_d256_two_head_seq32_median_timing --evidence-dir <dir> [--runs 5]"
        .to_string()
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
fn validate_static_target(
    statement_commitment: &str,
    lookup_claims: usize,
    trace_rows: usize,
    source_proof_bytes: usize,
    sidecar_proof_bytes: usize,
    fused_proof_bytes: usize,
    source_plus_sidecar_proof_bytes: usize,
) -> Result<(), String> {
    if statement_commitment != EXPECTED_STATEMENT_COMMITMENT {
        return Err("d256 statement commitment drift".to_string());
    }
    if lookup_claims != EXPECTED_LOOKUP_CLAIMS {
        return Err("d256 lookup-claim count drift".to_string());
    }
    if trace_rows != EXPECTED_TRACE_ROWS {
        return Err("d256 trace-row count drift".to_string());
    }
    validate_proof_len(
        "source envelope proof",
        source_proof_bytes,
        EXPECTED_SOURCE_PROOF_BYTES,
    )?;
    validate_proof_len(
        "sidecar envelope proof",
        sidecar_proof_bytes,
        EXPECTED_SIDECAR_PROOF_BYTES,
    )?;
    validate_proof_len(
        "fused envelope proof",
        fused_proof_bytes,
        EXPECTED_FUSED_PROOF_BYTES,
    )?;
    validate_proof_len(
        "split comparator proof bytes",
        source_plus_sidecar_proof_bytes,
        EXPECTED_SOURCE_PLUS_SIDECAR_PROOF_BYTES,
    )?;
    Ok(())
}

#[cfg(feature = "stwo-backend")]
fn validate_proof_len(label: &str, got: usize, expected: usize) -> Result<(), String> {
    if got != expected {
        return Err(format!("{label} drift: got {got}, expected {expected}"));
    }
    Ok(())
}

#[cfg(feature = "stwo-backend")]
fn require_verified<E: std::fmt::Display>(
    verified: Result<bool, E>,
    label: &str,
) -> Result<(), String> {
    match verified {
        Ok(true) => Ok(()),
        Ok(false) => Err(format!("{label} returned false")),
        Err(error) => Err(format!("{label} errored: {error}")),
    }
}

#[cfg(feature = "stwo-backend")]
fn contained_evidence_file(canonical_root: &Path, relative_path: &str) -> Result<PathBuf, String> {
    if relative_path.starts_with('/') || relative_path.contains("..") {
        return Err(format!(
            "evidence path must be relative and contained: {relative_path}"
        ));
    }
    let path = canonical_root.join(relative_path);
    let metadata = fs::symlink_metadata(&path)
        .map_err(|error| format!("failed to stat evidence file {}: {error}", path.display()))?;
    if metadata.file_type().is_symlink() {
        return Err(format!(
            "evidence file must not be a symlink: {}",
            path.display()
        ));
    }
    if !metadata.is_file() {
        return Err(format!(
            "evidence path must be a regular file: {}",
            path.display()
        ));
    }
    let canonical = fs::canonicalize(&path)
        .map_err(|error| format!("failed to canonicalize {}: {error}", path.display()))?;
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
fn round6(value: f64) -> f64 {
    (value * 1_000_000.0).round() / 1_000_000.0
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
    fn config_rejects_unknown_argument() {
        let error = Config::parse(["--bad".into()]).unwrap_err();
        assert!(error.contains("unknown argument"));
    }
}
