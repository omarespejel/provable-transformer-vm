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
    prove_zkai_attention_kv_native_d64_four_head_seq32_bounded_softmax_table_envelope,
    prove_zkai_attention_kv_native_d64_four_head_seq32_fused_softmax_table_envelope,
    prove_zkai_attention_kv_native_d64_four_head_seq32_softmax_table_lookup_envelope,
    prove_zkai_attention_kv_native_d64_four_head_seq64_bounded_softmax_table_envelope,
    prove_zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_envelope,
    prove_zkai_attention_kv_native_d64_four_head_seq64_softmax_table_lookup_envelope,
    prove_zkai_attention_kv_native_d64_two_head_seq32_bounded_softmax_table_envelope,
    prove_zkai_attention_kv_native_d64_two_head_seq32_fused_softmax_table_envelope,
    prove_zkai_attention_kv_native_d64_two_head_seq32_softmax_table_lookup_envelope,
    prove_zkai_attention_kv_native_d64_two_head_seq64_bounded_softmax_table_envelope,
    prove_zkai_attention_kv_native_d64_two_head_seq64_fused_softmax_table_envelope,
    prove_zkai_attention_kv_native_d64_two_head_seq64_softmax_table_lookup_envelope,
    verify_zkai_attention_kv_native_d64_four_head_seq32_bounded_softmax_table_envelope,
    verify_zkai_attention_kv_native_d64_four_head_seq32_fused_softmax_table_envelope,
    verify_zkai_attention_kv_native_d64_four_head_seq32_softmax_table_lookup_envelope,
    verify_zkai_attention_kv_native_d64_four_head_seq64_bounded_softmax_table_envelope,
    verify_zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_envelope,
    verify_zkai_attention_kv_native_d64_four_head_seq64_softmax_table_lookup_envelope,
    verify_zkai_attention_kv_native_d64_two_head_seq32_bounded_softmax_table_envelope,
    verify_zkai_attention_kv_native_d64_two_head_seq32_fused_softmax_table_envelope,
    verify_zkai_attention_kv_native_d64_two_head_seq32_softmax_table_lookup_envelope,
    verify_zkai_attention_kv_native_d64_two_head_seq64_bounded_softmax_table_envelope,
    verify_zkai_attention_kv_native_d64_two_head_seq64_fused_softmax_table_envelope,
    verify_zkai_attention_kv_native_d64_two_head_seq64_softmax_table_lookup_envelope,
    zkai_attention_kv_native_d64_four_head_seq32_bounded_softmax_table_envelope_from_json_slice,
    zkai_attention_kv_native_d64_four_head_seq32_bounded_softmax_table_input_from_json_str,
    zkai_attention_kv_native_d64_four_head_seq32_fused_softmax_table_envelope_from_json_slice,
    zkai_attention_kv_native_d64_four_head_seq32_fused_softmax_table_source_input_from_json_str,
    zkai_attention_kv_native_d64_four_head_seq32_softmax_table_lookup_envelope_from_json_slice,
    zkai_attention_kv_native_d64_four_head_seq32_softmax_table_lookup_source_input_from_json_str,
    zkai_attention_kv_native_d64_four_head_seq64_bounded_softmax_table_envelope_from_json_slice,
    zkai_attention_kv_native_d64_four_head_seq64_bounded_softmax_table_input_from_json_str,
    zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_envelope_from_json_slice,
    zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_source_input_from_json_str,
    zkai_attention_kv_native_d64_four_head_seq64_softmax_table_lookup_envelope_from_json_slice,
    zkai_attention_kv_native_d64_four_head_seq64_softmax_table_lookup_source_input_from_json_str,
    zkai_attention_kv_native_d64_two_head_seq32_bounded_softmax_table_envelope_from_json_slice,
    zkai_attention_kv_native_d64_two_head_seq32_bounded_softmax_table_input_from_json_str,
    zkai_attention_kv_native_d64_two_head_seq32_fused_softmax_table_envelope_from_json_slice,
    zkai_attention_kv_native_d64_two_head_seq32_fused_softmax_table_source_input_from_json_str,
    zkai_attention_kv_native_d64_two_head_seq32_softmax_table_lookup_envelope_from_json_slice,
    zkai_attention_kv_native_d64_two_head_seq32_softmax_table_lookup_source_input_from_json_str,
    zkai_attention_kv_native_d64_two_head_seq64_bounded_softmax_table_envelope_from_json_slice,
    zkai_attention_kv_native_d64_two_head_seq64_bounded_softmax_table_input_from_json_str,
    zkai_attention_kv_native_d64_two_head_seq64_fused_softmax_table_envelope_from_json_slice,
    zkai_attention_kv_native_d64_two_head_seq64_fused_softmax_table_source_input_from_json_str,
    zkai_attention_kv_native_d64_two_head_seq64_softmax_table_lookup_envelope_from_json_slice,
    zkai_attention_kv_native_d64_two_head_seq64_softmax_table_lookup_source_input_from_json_str,
    ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ32_BOUNDED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ32_BOUNDED_SOFTMAX_TABLE_MAX_INPUT_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ32_FUSED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ32_SOFTMAX_TABLE_LOOKUP_MAX_ENVELOPE_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ64_BOUNDED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ64_BOUNDED_SOFTMAX_TABLE_MAX_INPUT_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ64_FUSED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ64_SOFTMAX_TABLE_LOOKUP_MAX_ENVELOPE_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D64_TWO_HEAD_SEQ32_BOUNDED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D64_TWO_HEAD_SEQ32_BOUNDED_SOFTMAX_TABLE_MAX_INPUT_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D64_TWO_HEAD_SEQ32_FUSED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D64_TWO_HEAD_SEQ32_SOFTMAX_TABLE_LOOKUP_MAX_ENVELOPE_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D64_TWO_HEAD_SEQ64_BOUNDED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D64_TWO_HEAD_SEQ64_BOUNDED_SOFTMAX_TABLE_MAX_INPUT_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D64_TWO_HEAD_SEQ64_FUSED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
    ZKAI_ATTENTION_KV_NATIVE_D64_TWO_HEAD_SEQ64_SOFTMAX_TABLE_LOOKUP_MAX_ENVELOPE_JSON_BYTES,
};

#[cfg(feature = "stwo-backend")]
const SCHEMA: &str = "zkai-attention-kv-d64-sequence-median-timing-cli-v1";
#[cfg(feature = "stwo-backend")]
const ISSUE: usize = 715;
#[cfg(feature = "stwo-backend")]
const DECISION: &str = "GO_D64_SEQUENCE_ENGINEERING_LOCAL_MEDIAN_OF_5_TIMING_CAPTURED";
#[cfg(feature = "stwo-backend")]
const TIMING_POLICY: &str =
    "median_of_5_in_process_std_time_instant_microsecond_capture_engineering_only";
#[cfg(feature = "stwo-backend")]
const TIMING_SCOPE: &str =
    "existing_typed_source_input_prove_functions_plus_existing_typed_envelope_verify_functions";
#[cfg(feature = "stwo-backend")]
const DEFAULT_RUNS: usize = 5;
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
        eprintln!("zkai_attention_kv_d64_sequence_median_timing requires --features stwo-backend");
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
#[derive(Clone, Serialize)]
struct TimingRow {
    metric: &'static str,
    runs_us: Vec<u64>,
    median_us: u64,
    min_us: u64,
    max_us: u64,
}

#[cfg(feature = "stwo-backend")]
#[derive(Clone, Serialize)]
struct TimingComparisons {
    source_plus_sidecar_prove_median_us: u64,
    fused_prove_median_us: u64,
    fused_minus_source_plus_sidecar_prove_median_us: i128,
    fused_to_source_plus_sidecar_prove_median_ratio: f64,
    source_plus_sidecar_verify_median_us: u64,
    fused_verify_median_us: u64,
    fused_minus_source_plus_sidecar_verify_median_us: i128,
    fused_to_source_plus_sidecar_verify_median_ratio: f64,
}

#[cfg(feature = "stwo-backend")]
#[derive(Clone, Serialize)]
struct GeneratedProofBytes {
    source_runs: Vec<usize>,
    sidecar_runs: Vec<usize>,
    fused_runs: Vec<usize>,
}

#[cfg(feature = "stwo-backend")]
#[derive(Clone, Serialize)]
struct ProfileTimingSummary {
    profile_id: &'static str,
    key_width: usize,
    value_width: usize,
    head_count: usize,
    steps_per_head: usize,
    source_proof_bytes: usize,
    sidecar_proof_bytes: usize,
    source_plus_sidecar_raw_proof_bytes: usize,
    fused_proof_bytes: usize,
    fused_saves_vs_source_plus_sidecar_bytes: usize,
    fused_to_source_plus_sidecar_ratio: f64,
    lookup_claims: usize,
    trace_rows: usize,
    statement_commitment: &'static str,
    source_artifacts: Vec<serde_json::Value>,
    timings: Vec<TimingRow>,
    comparisons: TimingComparisons,
    generated_proof_bytes: GeneratedProofBytes,
}

#[cfg(feature = "stwo-backend")]
macro_rules! capture_profile {
    (
        $config:expr,
        $evidence_dir:expr,
        profile_id = $profile_id:literal,
        key_width = $key_width:literal,
        head_count = $head_count:literal,
        steps_per_head = $steps_per_head:literal,
        source_input_path = $source_input_path:literal,
        source_envelope_path = $source_envelope_path:literal,
        sidecar_envelope_path = $sidecar_envelope_path:literal,
        fused_envelope_path = $fused_envelope_path:literal,
        expected_source_proof_bytes = $expected_source_proof_bytes:literal,
        expected_sidecar_proof_bytes = $expected_sidecar_proof_bytes:literal,
        expected_fused_proof_bytes = $expected_fused_proof_bytes:literal,
        expected_source_plus_sidecar_proof_bytes = $expected_source_plus_sidecar_proof_bytes:literal,
        expected_lookup_claims = $expected_lookup_claims:literal,
        expected_trace_rows = $expected_trace_rows:literal,
        expected_statement_commitment = $expected_statement_commitment:literal,
        max_input_bytes = $max_input_bytes:ident,
        max_source_envelope_bytes = $max_source_envelope_bytes:ident,
        max_sidecar_envelope_bytes = $max_sidecar_envelope_bytes:ident,
        max_fused_envelope_bytes = $max_fused_envelope_bytes:ident,
        parse_source_input = $parse_source_input:ident,
        parse_sidecar_input = $parse_sidecar_input:ident,
        parse_fused_input = $parse_fused_input:ident,
        parse_source_envelope = $parse_source_envelope:ident,
        parse_sidecar_envelope = $parse_sidecar_envelope:ident,
        parse_fused_envelope = $parse_fused_envelope:ident,
        prove_source = $prove_source:ident,
        prove_sidecar = $prove_sidecar:ident,
        prove_fused = $prove_fused:ident,
        verify_source = $verify_source:ident,
        verify_sidecar = $verify_sidecar:ident,
        verify_fused = $verify_fused:ident $(,)?
    ) => {{
        let source_input_path = contained_evidence_file($evidence_dir, $source_input_path)?;
        let source_envelope_path = contained_evidence_file($evidence_dir, $source_envelope_path)?;
        let sidecar_envelope_path = contained_evidence_file($evidence_dir, $sidecar_envelope_path)?;
        let fused_envelope_path = contained_evidence_file($evidence_dir, $fused_envelope_path)?;

        let source_input_raw =
            read_bounded_utf8(&source_input_path, $max_input_bytes, $profile_id)?;
        let source_envelope_raw = read_bounded_bytes(
            &source_envelope_path,
            $max_source_envelope_bytes,
            $profile_id,
        )?;
        let sidecar_envelope_raw = read_bounded_bytes(
            &sidecar_envelope_path,
            $max_sidecar_envelope_bytes,
            $profile_id,
        )?;
        let fused_envelope_raw =
            read_bounded_bytes(&fused_envelope_path, $max_fused_envelope_bytes, $profile_id)?;

        let source_input =
            $parse_source_input(&source_input_raw).map_err(|error| error.to_string())?;
        let sidecar_input =
            $parse_sidecar_input(&source_input_raw).map_err(|error| error.to_string())?;
        let fused_input =
            $parse_fused_input(&source_input_raw).map_err(|error| error.to_string())?;
        let source_envelope =
            $parse_source_envelope(&source_envelope_raw).map_err(|error| error.to_string())?;
        let sidecar_envelope =
            $parse_sidecar_envelope(&sidecar_envelope_raw).map_err(|error| error.to_string())?;
        let fused_envelope =
            $parse_fused_envelope(&fused_envelope_raw).map_err(|error| error.to_string())?;

        validate_profile_target(
            $profile_id,
            source_input.statement_commitment.as_str(),
            source_input.score_row_count,
            source_input.trace_row_count,
            source_envelope.proof.len(),
            sidecar_envelope.proof.len(),
            fused_envelope.proof.len(),
            fused_envelope
                .fused_summary
                .source_plus_sidecar_raw_proof_bytes,
            $expected_statement_commitment,
            $expected_lookup_claims,
            $expected_trace_rows,
            $expected_source_proof_bytes,
            $expected_sidecar_proof_bytes,
            $expected_fused_proof_bytes,
            $expected_source_plus_sidecar_proof_bytes,
        )?;

        let mut generated_source_proof_bytes = Vec::with_capacity($config.runs);
        let source_prove_row = timed_row("source_prove_existing_input_us", $config.runs, || {
            let envelope = $prove_source(&source_input).map_err(|error| error.to_string())?;
            generated_source_proof_bytes.push(envelope.proof.len());
            validate_proof_len(
                $profile_id,
                "source generated proof",
                envelope.proof.len(),
                $expected_source_proof_bytes,
            )
        })?;

        let mut generated_sidecar_proof_bytes = Vec::with_capacity($config.runs);
        let sidecar_prove_row = timed_row("sidecar_prove_existing_input_us", $config.runs, || {
            let envelope = $prove_sidecar(&sidecar_input).map_err(|error| error.to_string())?;
            generated_sidecar_proof_bytes.push(envelope.proof.len());
            validate_proof_len(
                $profile_id,
                "sidecar generated proof",
                envelope.proof.len(),
                $expected_sidecar_proof_bytes,
            )
        })?;

        let mut generated_fused_proof_bytes = Vec::with_capacity($config.runs);
        let fused_prove_row = timed_row("fused_prove_existing_input_us", $config.runs, || {
            let envelope = $prove_fused(&fused_input).map_err(|error| error.to_string())?;
            generated_fused_proof_bytes.push(envelope.proof.len());
            validate_proof_len(
                $profile_id,
                "fused generated proof",
                envelope.proof.len(),
                $expected_fused_proof_bytes,
            )
        })?;

        let source_verify_row =
            timed_row("source_verify_existing_envelope_us", $config.runs, || {
                require_verified($verify_source(&source_envelope), "source verifier")
            })?;
        let sidecar_verify_row =
            timed_row("sidecar_verify_existing_envelope_us", $config.runs, || {
                require_verified($verify_sidecar(&sidecar_envelope), "sidecar verifier")
            })?;
        let fused_verify_row =
            timed_row("fused_verify_existing_envelope_us", $config.runs, || {
                require_verified($verify_fused(&fused_envelope), "fused verifier")
            })?;

        let split_prove_median = source_prove_row
            .median_us
            .checked_add(sidecar_prove_row.median_us)
            .ok_or_else(|| format!("{} split prove median overflow", $profile_id))?;
        let split_verify_median = source_verify_row
            .median_us
            .checked_add(sidecar_verify_row.median_us)
            .ok_or_else(|| format!("{} split verify median overflow", $profile_id))?;
        let comparisons = TimingComparisons {
            source_plus_sidecar_prove_median_us: split_prove_median,
            fused_prove_median_us: fused_prove_row.median_us,
            fused_minus_source_plus_sidecar_prove_median_us: fused_prove_row.median_us as i128
                - split_prove_median as i128,
            fused_to_source_plus_sidecar_prove_median_ratio: round6(
                fused_prove_row.median_us as f64 / split_prove_median as f64,
            ),
            source_plus_sidecar_verify_median_us: split_verify_median,
            fused_verify_median_us: fused_verify_row.median_us,
            fused_minus_source_plus_sidecar_verify_median_us: fused_verify_row.median_us as i128
                - split_verify_median as i128,
            fused_to_source_plus_sidecar_verify_median_ratio: round6(
                fused_verify_row.median_us as f64 / split_verify_median as f64,
            ),
        };
        let fused_saving = $expected_source_plus_sidecar_proof_bytes - $expected_fused_proof_bytes;
        ProfileTimingSummary {
            profile_id: $profile_id,
            key_width: $key_width,
            value_width: $key_width,
            head_count: $head_count,
            steps_per_head: $steps_per_head,
            source_proof_bytes: $expected_source_proof_bytes,
            sidecar_proof_bytes: $expected_sidecar_proof_bytes,
            source_plus_sidecar_raw_proof_bytes: $expected_source_plus_sidecar_proof_bytes,
            fused_proof_bytes: $expected_fused_proof_bytes,
            fused_saves_vs_source_plus_sidecar_bytes: fused_saving,
            fused_to_source_plus_sidecar_ratio: round6(
                $expected_fused_proof_bytes as f64
                    / $expected_source_plus_sidecar_proof_bytes as f64,
            ),
            lookup_claims: $expected_lookup_claims,
            trace_rows: $expected_trace_rows,
            statement_commitment: $expected_statement_commitment,
            source_artifacts: vec![
                source_artifact(
                    "source_input",
                    $source_input_path,
                    source_input_raw.as_bytes(),
                ),
                source_artifact(
                    "source_envelope",
                    $source_envelope_path,
                    &source_envelope_raw,
                ),
                source_artifact(
                    "sidecar_envelope",
                    $sidecar_envelope_path,
                    &sidecar_envelope_raw,
                ),
                source_artifact("fused_envelope", $fused_envelope_path, &fused_envelope_raw),
            ],
            timings: vec![
                source_prove_row,
                sidecar_prove_row,
                fused_prove_row,
                source_verify_row,
                sidecar_verify_row,
                fused_verify_row,
            ],
            comparisons,
            generated_proof_bytes: GeneratedProofBytes {
                source_runs: generated_source_proof_bytes,
                sidecar_runs: generated_sidecar_proof_bytes,
                fused_runs: generated_fused_proof_bytes,
            },
        }
    }};
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

    let profiles = vec![
        capture_profile!(
            config,
            &evidence_dir,
            profile_id = "d64_two_head_seq32",
            key_width = 64,
            head_count = 2,
            steps_per_head = 32,
            source_input_path = "zkai-attention-kv-stwo-native-d64-two-head-seq32-bounded-softmax-table-proof-2026-05.json",
            source_envelope_path = "zkai-attention-kv-stwo-native-d64-two-head-seq32-bounded-softmax-table-proof-2026-05.envelope.json",
            sidecar_envelope_path = "zkai-attention-kv-stwo-native-d64-two-head-seq32-softmax-table-logup-sidecar-proof-2026-05.envelope.json",
            fused_envelope_path = "zkai-attention-kv-stwo-native-d64-two-head-seq32-fused-softmax-table-proof-2026-05.envelope.json",
            expected_source_proof_bytes = 248_702,
            expected_sidecar_proof_bytes = 36_400,
            expected_fused_proof_bytes = 253_257,
            expected_source_plus_sidecar_proof_bytes = 285_102,
            expected_lookup_claims = 1_184,
            expected_trace_rows = 2_048,
            expected_statement_commitment = "blake2b-256:e8b693ec2447a681ced82ab852a909d71bdf546db53b260cec8eb5f399c0990b",
            max_input_bytes = ZKAI_ATTENTION_KV_NATIVE_D64_TWO_HEAD_SEQ32_BOUNDED_SOFTMAX_TABLE_MAX_INPUT_JSON_BYTES,
            max_source_envelope_bytes = ZKAI_ATTENTION_KV_NATIVE_D64_TWO_HEAD_SEQ32_BOUNDED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
            max_sidecar_envelope_bytes = ZKAI_ATTENTION_KV_NATIVE_D64_TWO_HEAD_SEQ32_SOFTMAX_TABLE_LOOKUP_MAX_ENVELOPE_JSON_BYTES,
            max_fused_envelope_bytes = ZKAI_ATTENTION_KV_NATIVE_D64_TWO_HEAD_SEQ32_FUSED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
            parse_source_input = zkai_attention_kv_native_d64_two_head_seq32_bounded_softmax_table_input_from_json_str,
            parse_sidecar_input = zkai_attention_kv_native_d64_two_head_seq32_softmax_table_lookup_source_input_from_json_str,
            parse_fused_input = zkai_attention_kv_native_d64_two_head_seq32_fused_softmax_table_source_input_from_json_str,
            parse_source_envelope = zkai_attention_kv_native_d64_two_head_seq32_bounded_softmax_table_envelope_from_json_slice,
            parse_sidecar_envelope = zkai_attention_kv_native_d64_two_head_seq32_softmax_table_lookup_envelope_from_json_slice,
            parse_fused_envelope = zkai_attention_kv_native_d64_two_head_seq32_fused_softmax_table_envelope_from_json_slice,
            prove_source = prove_zkai_attention_kv_native_d64_two_head_seq32_bounded_softmax_table_envelope,
            prove_sidecar = prove_zkai_attention_kv_native_d64_two_head_seq32_softmax_table_lookup_envelope,
            prove_fused = prove_zkai_attention_kv_native_d64_two_head_seq32_fused_softmax_table_envelope,
            verify_source = verify_zkai_attention_kv_native_d64_two_head_seq32_bounded_softmax_table_envelope,
            verify_sidecar = verify_zkai_attention_kv_native_d64_two_head_seq32_softmax_table_lookup_envelope,
            verify_fused = verify_zkai_attention_kv_native_d64_two_head_seq32_fused_softmax_table_envelope,
        ),
        capture_profile!(
            config,
            &evidence_dir,
            profile_id = "d64_two_head_seq64",
            key_width = 64,
            head_count = 2,
            steps_per_head = 64,
            source_input_path = "zkai-attention-kv-stwo-native-d64-two-head-seq64-bounded-softmax-table-proof-2026-05.json",
            source_envelope_path = "zkai-attention-kv-stwo-native-d64-two-head-seq64-bounded-softmax-table-proof-2026-05.envelope.json",
            sidecar_envelope_path = "zkai-attention-kv-stwo-native-d64-two-head-seq64-softmax-table-logup-sidecar-proof-2026-05.envelope.json",
            fused_envelope_path = "zkai-attention-kv-stwo-native-d64-two-head-seq64-fused-softmax-table-proof-2026-05.envelope.json",
            expected_source_proof_bytes = 264_403,
            expected_sidecar_proof_bytes = 42_567,
            expected_fused_proof_bytes = 272_636,
            expected_source_plus_sidecar_proof_bytes = 306_970,
            expected_lookup_claims = 4_416,
            expected_trace_rows = 8_192,
            expected_statement_commitment = "blake2b-256:cfa3e6a544faaf8f4aeb0801418836153dbe19e140936e99d65ab795a9fd9e70",
            max_input_bytes = ZKAI_ATTENTION_KV_NATIVE_D64_TWO_HEAD_SEQ64_BOUNDED_SOFTMAX_TABLE_MAX_INPUT_JSON_BYTES,
            max_source_envelope_bytes = ZKAI_ATTENTION_KV_NATIVE_D64_TWO_HEAD_SEQ64_BOUNDED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
            max_sidecar_envelope_bytes = ZKAI_ATTENTION_KV_NATIVE_D64_TWO_HEAD_SEQ64_SOFTMAX_TABLE_LOOKUP_MAX_ENVELOPE_JSON_BYTES,
            max_fused_envelope_bytes = ZKAI_ATTENTION_KV_NATIVE_D64_TWO_HEAD_SEQ64_FUSED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
            parse_source_input = zkai_attention_kv_native_d64_two_head_seq64_bounded_softmax_table_input_from_json_str,
            parse_sidecar_input = zkai_attention_kv_native_d64_two_head_seq64_softmax_table_lookup_source_input_from_json_str,
            parse_fused_input = zkai_attention_kv_native_d64_two_head_seq64_fused_softmax_table_source_input_from_json_str,
            parse_source_envelope = zkai_attention_kv_native_d64_two_head_seq64_bounded_softmax_table_envelope_from_json_slice,
            parse_sidecar_envelope = zkai_attention_kv_native_d64_two_head_seq64_softmax_table_lookup_envelope_from_json_slice,
            parse_fused_envelope = zkai_attention_kv_native_d64_two_head_seq64_fused_softmax_table_envelope_from_json_slice,
            prove_source = prove_zkai_attention_kv_native_d64_two_head_seq64_bounded_softmax_table_envelope,
            prove_sidecar = prove_zkai_attention_kv_native_d64_two_head_seq64_softmax_table_lookup_envelope,
            prove_fused = prove_zkai_attention_kv_native_d64_two_head_seq64_fused_softmax_table_envelope,
            verify_source = verify_zkai_attention_kv_native_d64_two_head_seq64_bounded_softmax_table_envelope,
            verify_sidecar = verify_zkai_attention_kv_native_d64_two_head_seq64_softmax_table_lookup_envelope,
            verify_fused = verify_zkai_attention_kv_native_d64_two_head_seq64_fused_softmax_table_envelope,
        ),
        capture_profile!(
            config,
            &evidence_dir,
            profile_id = "d64_four_head_seq32",
            key_width = 64,
            head_count = 4,
            steps_per_head = 32,
            source_input_path = "zkai-attention-kv-stwo-native-d64-four-head-seq32-bounded-softmax-table-proof-2026-05.json",
            source_envelope_path = "zkai-attention-kv-stwo-native-d64-four-head-seq32-bounded-softmax-table-proof-2026-05.envelope.json",
            sidecar_envelope_path = "zkai-attention-kv-stwo-native-d64-four-head-seq32-softmax-table-logup-sidecar-proof-2026-05.envelope.json",
            fused_envelope_path = "zkai-attention-kv-stwo-native-d64-four-head-seq32-fused-softmax-table-proof-2026-05.envelope.json",
            expected_source_proof_bytes = 254_145,
            expected_sidecar_proof_bytes = 34_147,
            expected_fused_proof_bytes = 255_889,
            expected_source_plus_sidecar_proof_bytes = 288_292,
            expected_lookup_claims = 2_368,
            expected_trace_rows = 4_096,
            expected_statement_commitment = "blake2b-256:c808ebf201c3371d6598812755963d28ce64005c8b09161ccfbdeae101f346a3",
            max_input_bytes = ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ32_BOUNDED_SOFTMAX_TABLE_MAX_INPUT_JSON_BYTES,
            max_source_envelope_bytes = ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ32_BOUNDED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
            max_sidecar_envelope_bytes = ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ32_SOFTMAX_TABLE_LOOKUP_MAX_ENVELOPE_JSON_BYTES,
            max_fused_envelope_bytes = ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ32_FUSED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
            parse_source_input = zkai_attention_kv_native_d64_four_head_seq32_bounded_softmax_table_input_from_json_str,
            parse_sidecar_input = zkai_attention_kv_native_d64_four_head_seq32_softmax_table_lookup_source_input_from_json_str,
            parse_fused_input = zkai_attention_kv_native_d64_four_head_seq32_fused_softmax_table_source_input_from_json_str,
            parse_source_envelope = zkai_attention_kv_native_d64_four_head_seq32_bounded_softmax_table_envelope_from_json_slice,
            parse_sidecar_envelope = zkai_attention_kv_native_d64_four_head_seq32_softmax_table_lookup_envelope_from_json_slice,
            parse_fused_envelope = zkai_attention_kv_native_d64_four_head_seq32_fused_softmax_table_envelope_from_json_slice,
            prove_source = prove_zkai_attention_kv_native_d64_four_head_seq32_bounded_softmax_table_envelope,
            prove_sidecar = prove_zkai_attention_kv_native_d64_four_head_seq32_softmax_table_lookup_envelope,
            prove_fused = prove_zkai_attention_kv_native_d64_four_head_seq32_fused_softmax_table_envelope,
            verify_source = verify_zkai_attention_kv_native_d64_four_head_seq32_bounded_softmax_table_envelope,
            verify_sidecar = verify_zkai_attention_kv_native_d64_four_head_seq32_softmax_table_lookup_envelope,
            verify_fused = verify_zkai_attention_kv_native_d64_four_head_seq32_fused_softmax_table_envelope,
        ),
        capture_profile!(
            config,
            &evidence_dir,
            profile_id = "d64_four_head_seq64",
            key_width = 64,
            head_count = 4,
            steps_per_head = 64,
            source_input_path = "zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.json",
            source_envelope_path = "zkai-attention-kv-stwo-native-d64-four-head-seq64-bounded-softmax-table-proof-2026-05.envelope.json",
            sidecar_envelope_path = "zkai-attention-kv-stwo-native-d64-four-head-seq64-softmax-table-logup-sidecar-proof-2026-05.envelope.json",
            fused_envelope_path = "zkai-attention-kv-stwo-native-d64-four-head-seq64-fused-softmax-table-proof-2026-05.envelope.json",
            expected_source_proof_bytes = 272_638,
            expected_sidecar_proof_bytes = 43_147,
            expected_fused_proof_bytes = 276_503,
            expected_source_plus_sidecar_proof_bytes = 315_785,
            expected_lookup_claims = 8_832,
            expected_trace_rows = 16_384,
            expected_statement_commitment = "blake2b-256:c4118c9f0b1b07ce8474121a63717b1a410e86bdcc155d57a4c9765e4255c333",
            max_input_bytes = ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ64_BOUNDED_SOFTMAX_TABLE_MAX_INPUT_JSON_BYTES,
            max_source_envelope_bytes = ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ64_BOUNDED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
            max_sidecar_envelope_bytes = ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ64_SOFTMAX_TABLE_LOOKUP_MAX_ENVELOPE_JSON_BYTES,
            max_fused_envelope_bytes = ZKAI_ATTENTION_KV_NATIVE_D64_FOUR_HEAD_SEQ64_FUSED_SOFTMAX_TABLE_MAX_ENVELOPE_JSON_BYTES,
            parse_source_input = zkai_attention_kv_native_d64_four_head_seq64_bounded_softmax_table_input_from_json_str,
            parse_sidecar_input = zkai_attention_kv_native_d64_four_head_seq64_softmax_table_lookup_source_input_from_json_str,
            parse_fused_input = zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_source_input_from_json_str,
            parse_source_envelope = zkai_attention_kv_native_d64_four_head_seq64_bounded_softmax_table_envelope_from_json_slice,
            parse_sidecar_envelope = zkai_attention_kv_native_d64_four_head_seq64_softmax_table_lookup_envelope_from_json_slice,
            parse_fused_envelope = zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_envelope_from_json_slice,
            prove_source = prove_zkai_attention_kv_native_d64_four_head_seq64_bounded_softmax_table_envelope,
            prove_sidecar = prove_zkai_attention_kv_native_d64_four_head_seq64_softmax_table_lookup_envelope,
            prove_fused = prove_zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_envelope,
            verify_source = verify_zkai_attention_kv_native_d64_four_head_seq64_bounded_softmax_table_envelope,
            verify_sidecar = verify_zkai_attention_kv_native_d64_four_head_seq64_softmax_table_lookup_envelope,
            verify_fused = verify_zkai_attention_kv_native_d64_four_head_seq64_fused_softmax_table_envelope,
        ),
    ];

    let summary = serde_json::json!({
        "schema": SCHEMA,
        "issue": ISSUE,
        "decision": DECISION,
        "timing_policy": TIMING_POLICY,
        "timing_scope": TIMING_SCOPE,
        "clock": "std_time_instant_elapsed_as_micros",
        "sample_count": DEFAULT_RUNS,
        "profiles": profiles,
        "sequence_growth": [
            sequence_growth(
                profile_by_id(&profiles, "d64_two_head_seq32")?,
                profile_by_id(&profiles, "d64_two_head_seq64")?,
            ),
            sequence_growth(
                profile_by_id(&profiles, "d64_four_head_seq32")?,
                profile_by_id(&profiles, "d64_four_head_seq64")?,
            ),
        ],
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
            "cargo +nightly-2025-07-14 run --locked --release --features stwo-backend --bin zkai_attention_kv_d64_sequence_median_timing -- --evidence-dir docs/engineering/evidence --runs 5 > docs/engineering/evidence/zkai-attention-kv-d64-sequence-median-timing-raw-2026-05.json",
            "cargo +nightly-2025-07-14 test --locked --release --features stwo-backend --bin zkai_attention_kv_d64_sequence_median_timing",
        ],
    });

    serde_json::to_string_pretty(&summary)
        .map_err(|error| format!("failed to serialize timing summary: {error}"))
}

#[cfg(feature = "stwo-backend")]
fn profile_by_id<'a>(
    profiles: &'a [ProfileTimingSummary],
    profile_id: &str,
) -> Result<&'a ProfileTimingSummary, String> {
    profiles
        .iter()
        .find(|profile| profile.profile_id == profile_id)
        .ok_or_else(|| format!("missing timing profile: {profile_id}"))
}

#[cfg(feature = "stwo-backend")]
fn sequence_growth(from: &ProfileTimingSummary, to: &ProfileTimingSummary) -> serde_json::Value {
    serde_json::json!({
        "from_profile_id": from.profile_id,
        "to_profile_id": to.profile_id,
        "head_count": to.head_count,
        "from_steps_per_head": from.steps_per_head,
        "to_steps_per_head": to.steps_per_head,
        "lookup_claim_growth": round6(to.lookup_claims as f64 / from.lookup_claims as f64),
        "trace_row_growth": round6(to.trace_rows as f64 / from.trace_rows as f64),
        "fused_raw_proof_growth": round6(to.fused_proof_bytes as f64 / from.fused_proof_bytes as f64),
        "split_raw_proof_growth": round6(
            to.source_plus_sidecar_raw_proof_bytes as f64 / from.source_plus_sidecar_raw_proof_bytes as f64
        ),
        "fused_prove_median_growth": round6(
            to.comparisons.fused_prove_median_us as f64 / from.comparisons.fused_prove_median_us as f64
        ),
        "split_prove_median_growth": round6(
            to.comparisons.source_plus_sidecar_prove_median_us as f64
                / from.comparisons.source_plus_sidecar_prove_median_us as f64
        ),
        "fused_verify_median_growth": round6(
            to.comparisons.fused_verify_median_us as f64 / from.comparisons.fused_verify_median_us as f64
        ),
        "split_verify_median_growth": round6(
            to.comparisons.source_plus_sidecar_verify_median_us as f64
                / from.comparisons.source_plus_sidecar_verify_median_us as f64
        ),
    })
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
    "usage: zkai_attention_kv_d64_sequence_median_timing --evidence-dir <dir> [--runs 5]"
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
#[allow(clippy::too_many_arguments)]
fn validate_profile_target(
    profile_id: &str,
    statement_commitment: &str,
    lookup_claims: usize,
    trace_rows: usize,
    source_proof_bytes: usize,
    sidecar_proof_bytes: usize,
    fused_proof_bytes: usize,
    source_plus_sidecar_proof_bytes: usize,
    expected_statement_commitment: &str,
    expected_lookup_claims: usize,
    expected_trace_rows: usize,
    expected_source_proof_bytes: usize,
    expected_sidecar_proof_bytes: usize,
    expected_fused_proof_bytes: usize,
    expected_source_plus_sidecar_proof_bytes: usize,
) -> Result<(), String> {
    if statement_commitment != expected_statement_commitment {
        return Err(format!("{profile_id} statement commitment drift"));
    }
    if lookup_claims != expected_lookup_claims {
        return Err(format!("{profile_id} lookup-claim count drift"));
    }
    if trace_rows != expected_trace_rows {
        return Err(format!("{profile_id} trace-row count drift"));
    }
    validate_proof_len(
        profile_id,
        "source envelope proof",
        source_proof_bytes,
        expected_source_proof_bytes,
    )?;
    validate_proof_len(
        profile_id,
        "sidecar envelope proof",
        sidecar_proof_bytes,
        expected_sidecar_proof_bytes,
    )?;
    validate_proof_len(
        profile_id,
        "fused envelope proof",
        fused_proof_bytes,
        expected_fused_proof_bytes,
    )?;
    validate_proof_len(
        profile_id,
        "split comparator proof bytes",
        source_plus_sidecar_proof_bytes,
        expected_source_plus_sidecar_proof_bytes,
    )?;
    Ok(())
}

#[cfg(feature = "stwo-backend")]
fn validate_proof_len(
    profile_id: &str,
    label: &str,
    got: usize,
    expected: usize,
) -> Result<(), String> {
    if got != expected {
        return Err(format!(
            "{profile_id} {label} drift: got {got}, expected {expected}"
        ));
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
fn source_artifact(id: &'static str, relative_path: &str, bytes: &[u8]) -> serde_json::Value {
    serde_json::json!({
        "id": id,
        "path": format!("docs/engineering/evidence/{relative_path}"),
        "sha256": sha256_bytes(bytes),
        "bytes": bytes.len(),
    })
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

    #[test]
    fn sequence_growth_keeps_work_and_time_axes_separate() {
        let mut from = fixture_profile("from", 1_000, 2_000, 10_000, 20_000);
        let mut to = fixture_profile("to", 4_000, 8_000, 11_000, 50_000);
        from.comparisons.fused_prove_median_us = 100;
        from.comparisons.source_plus_sidecar_prove_median_us = 200;
        from.comparisons.fused_verify_median_us = 300;
        from.comparisons.source_plus_sidecar_verify_median_us = 400;
        to.comparisons.fused_prove_median_us = 250;
        to.comparisons.source_plus_sidecar_prove_median_us = 600;
        to.comparisons.fused_verify_median_us = 900;
        to.comparisons.source_plus_sidecar_verify_median_us = 1_000;
        let growth = sequence_growth(&from, &to);
        assert_eq!(growth["lookup_claim_growth"], 4.0);
        assert_eq!(growth["trace_row_growth"], 4.0);
        assert_eq!(growth["fused_raw_proof_growth"], 1.1);
        assert_eq!(growth["fused_prove_median_growth"], 2.5);
    }

    #[test]
    fn source_artifact_uses_pre_read_bytes_without_disk_reopen() {
        let artifact = source_artifact("fixture", "nested/input.json", b"{\"ok\":true}");
        assert_eq!(artifact["id"], "fixture");
        assert_eq!(
            artifact["path"],
            "docs/engineering/evidence/nested/input.json"
        );
        assert_eq!(artifact["bytes"], 11);
        assert_eq!(
            artifact["sha256"],
            "4062edaf750fb8074e7e83e0c9028c94e32468a8b6f1614774328ef045150f93"
        );
    }

    fn fixture_profile(
        profile_id: &'static str,
        lookup_claims: usize,
        trace_rows: usize,
        fused_proof_bytes: usize,
        split_proof_bytes: usize,
    ) -> ProfileTimingSummary {
        ProfileTimingSummary {
            profile_id,
            key_width: 64,
            value_width: 64,
            head_count: 2,
            steps_per_head: 32,
            source_proof_bytes: split_proof_bytes - 1,
            sidecar_proof_bytes: 1,
            source_plus_sidecar_raw_proof_bytes: split_proof_bytes,
            fused_proof_bytes,
            fused_saves_vs_source_plus_sidecar_bytes: split_proof_bytes - fused_proof_bytes,
            fused_to_source_plus_sidecar_ratio: round6(
                fused_proof_bytes as f64 / split_proof_bytes as f64,
            ),
            lookup_claims,
            trace_rows,
            statement_commitment: "blake2b-256:test",
            source_artifacts: vec![],
            timings: vec![],
            comparisons: TimingComparisons {
                source_plus_sidecar_prove_median_us: 1,
                fused_prove_median_us: 1,
                fused_minus_source_plus_sidecar_prove_median_us: 0,
                fused_to_source_plus_sidecar_prove_median_ratio: 1.0,
                source_plus_sidecar_verify_median_us: 1,
                fused_verify_median_us: 1,
                fused_minus_source_plus_sidecar_verify_median_us: 0,
                fused_to_source_plus_sidecar_verify_median_ratio: 1.0,
            },
            generated_proof_bytes: GeneratedProofBytes {
                source_runs: vec![],
                sidecar_runs: vec![],
                fused_runs: vec![],
            },
        }
    }
}
