# EZKL Artifact-Binding Audit - 2026-05-18

Issue: `#677`

Status: `EXECUTABLE_MUTATION_PASS_DONE_NARROW_CLAIM`

This note records a bounded Tablero-style audit pass against `zkonduit/ezkl`.

Target snapshot:

- repository: `https://github.com/zkonduit/ezkl`
- default branch: `main`
- latest checked commit: `e196b111c1ba`
- latest checked release: `v23.0.5`
- installed Python package: `ezkl==23.0.5`
- archived: `false`
- security policy: `.github/SECURITY.md` asks serious vulnerabilities to be
  reported privately to maintainers rather than through public issues or PRs.

## Audit Question

Can an EZKL proof artifact be relabeled at the application-statement layer
without changing what the official verifier actually checks?

This is not an attempt to break Halo2, KZG, or EZKL soundness. The question is
where EZKL's artifact boundary ends and where a Tablero-style typed statement
envelope would start.

## Source-Level Result

No core verifier soundness issue is claimed from this pass.

The source shape looks disciplined:

- `verify` loads `settings.json`, `vk.key`, SRS, and `proof.json`;
- `verify_commitment` loads the `Snark` proof object and verifying key;
- `verify_proof_circuit` passes `snark.instances` and `snark.proof` to Halo2
  verification;
- `GraphSettings` carries run args, visibility policy, instance shapes, input
  scales, and output scales;
- EZKL has explicit security notes for public commitments and quantization
  backdoors.

The most plausible Tablero surface is not the proof core. It is app-facing
metadata and claim presentation around the proof object.

## Stale Official Fixture Check

Release-pinned `tests/assets` were downloaded from `v23.0.5`:

```text
proof.json      b00dae6a2df133f8e660eb5fb691b02a7d86c5797f7b669871860cb7711314ca
settings.json   da675f3ce41be4d82e785188eef3d3a100d1db63e9453726c3569334cea981f2
vk.key          a4e075d9e29f29131510f1dbcc837887573ca3cb001bf0023cfa127469e48aec
kzg             7fe160fdf0725d7f86af953bde64f1acffa63bc178e625dcebe7de91fe42f615
```

The official verifier did not accept that bundle:

```text
Artifact version is 0.0.0, skipping version check
Using 3 columns for range-check.
RuntimeError: Failed to run verify: [halo2] The constraint system is not satisfied
```

Because the baseline failed, no mutation claim is made from this stale fixture.

## Fresh Baseline

To avoid stale-fixture drift, the executable mutation pass generated a fresh
proof from EZKL's release-pinned `examples/onnx/1l_relu` artifacts using
`ezkl==23.0.5`.

Fresh artifact snapshot:

```text
network.onnx             1c8c9f4fb788d088e7b518852ef46e6eab93c0c09af211276959bef146ec8ec2
input.json               b9557e9e386ab939bedd457003ca5130caa96b370c4d9e59a2e3768447182c2c
settings.json            21c507dbfd1899102bcfb2de6782f5f0237d3ded021b1f8d466595fb2ecc3f35
model.compiled           c45ad63198018c2ed2767eec9d3ca38b7dbd6244b2546474dadd54020498f155
witness.json             54da1969ba14a0238d0d2567303b45adb6b391b6d78be70abe42087feccd4086
srs_17                   5d6773af907eb8f8d5f69b903171ed87dcc8dbf3c90d28e254282f49a4da3091
test.vk                  da758e8562dff7552f317b2ae507e06f19414884f91ce31952570f34343cd810
test.pk                  fca282168042c17a186b1925b8dc55362b144fc395d86987d4779dcb396ab48e
proof.json               f54a3e5a65aad20913ad48ba476d5cb6263138d9defde110ed8d9f0ecb1aacd0
```

Observed proof shape:

```text
proof JSON bytes: 17,606
settings JSON bytes: 1,216
vk bytes: 263,431
instance columns: 1
instance lengths: [3]
raw proof bytes in JSON array: 3,072
pretty_public_inputs present: true
baseline official verify: true
```

## Mutation Results

The mutation pass used the official Python verifier:

```python
ezkl.verify(proof_path, settings_path, vk_path, srs_path)
```

Result summary:

| Mutation | Official verifier result | Interpretation |
|---|---:|---|
| Baseline fresh proof | accept | Valid baseline. |
| Change `pretty_public_inputs` only | accept | Human-readable display metadata is not proof-bound. |
| Change `version` only | accept | Provenance metadata is not proof-bound. |
| Change `timestamp` only | accept | Provenance metadata is not proof-bound. |
| Change `hex_proof` nibble only | accept | Verifier uses the proof byte array, not this display/compat field. |
| Change `instances[0][0]` with valid 64-hex field | reject | Public instance values are proof-bound. |
| Change `instances[0][1]` with valid 64-hex field | reject | Public instance values are proof-bound. |
| Change first byte in `proof` array | reject | Proof bytes are checked. |
| Change first byte in `vk.key` | reject | Verifying key bytes are checked. |
| Change `run_args.logrows` from `17` to `16` | reject | This verifier-critical setting is checked. |
| Empty `required_range_checks` | reject | Range-check table material is verifier-critical. |
| Change `model_instance_shapes` to `[[1, 2]]` | accept | App-facing settings metadata can drift. |
| Change `model_instance_shapes` to `[[9, 9]]` | accept | App-facing settings metadata can drift. |
| Change `model_output_scales` to `[0]` | accept | Display/decoding scale can drift. |
| Change `model_input_scales` to `[0]` | accept | Display/decoding scale can drift. |
| Empty `required_lookups` | accept | This settings field is not checked for this proof. |
| Change `total_assignments` to `1` | accept | Accounting metadata can drift. |
| Change `input_visibility` from `Private` to `Public` | accept | Visibility labels can drift at the settings layer. |
| Change `output_visibility` from `Public` to `Private` | accept | Visibility labels can drift at the settings layer. |
| Change `param_visibility` from `Private` to `Fixed` | accept | Visibility labels can drift at the settings layer. |
| Use lowercase visibility labels | reject | Malformed settings are rejected by parsing. |

Machine-readable local result files:

```text
external_repos/ezkl-fresh-1l-relu/mutation-results.json
  9006ba97aa290550b9a85b55edd43bd59c5ea35e2403d347da9bd142589efb98

external_repos/ezkl-fresh-1l-relu/mutation-results-strict.json
  ba22d6fd1e81f78fdc073908be3fc88177904271b64d1a8e661f91b435fc3d9a

external_repos/ezkl-fresh-1l-relu/mutation-results-visibility.json
  200add663ab6777f00f12db3d60e2d1153bb24dfb6233679bda13310fe2fa0e3
```

## Tablero Interpretation

EZKL core verification did the important cryptographic job in this pass:

- mutated public instances were rejected;
- mutated proof bytes were rejected;
- mutated verifying key bytes were rejected;
- malformed settings were rejected;
- some verifier-critical settings were rejected.

The application-statement gap is narrower and more useful:

The official verifier can accept the same proof while app-facing metadata in
`settings.json` and display metadata in `proof.json` drift. That includes shape,
scale, visibility, display outputs, version, timestamp, and accounting fields
for this checked baseline.

That is not automatically an EZKL vulnerability. It becomes a vulnerability only
if a downstream verifier wrapper, UI, registry, contract, or API treats those
mutable fields as the accepted application statement instead of deriving or
binding the statement separately.

Tablero's value would be to make that boundary explicit:

- bind model hash or compiled-circuit hash;
- bind `settings.json` digest, or split settings into verifier-critical,
  app-statement-critical, and display-only classes;
- bind `vk.key` digest;
- bind proof digest;
- bind public input/output schema and display decoding;
- bind visibility policy when it matters to the claim;
- mark fields like `pretty_public_inputs`, `timestamp`, `version`,
  `total_assignments`, and `hex_proof` as either bound statement fields or
  display-only fields.

## Claim Boundary

Supported narrow claim:

> In a fresh `ezkl==23.0.5` proof generated from the official `1l_relu` example,
> the official verifier rejects mutations to proof-critical material but accepts
> relabeling of several app-facing metadata fields. A Tablero-style statement
> envelope would prevent downstream software from confusing mutable metadata
> with the verified statement.

Unsupported claims:

- not a claim that EZKL verification is broken;
- not a claim that Halo2/KZG soundness is broken;
- not a claim that the official EZKL CLI or docs present mutated display fields
  as authoritative;
- not a claim against an official production verifier wrapper;
- not a proof-size or performance comparison;
- not a private-disclosure-worthy finding unless an official or production app
  surface is shown to rely on the mutable metadata as the accepted statement.

## Reproduction Commands

From the workspace root that contains `external_repos/`:

```bash
external_repos/ezkl-audit-venv/bin/python - <<'PY'
import ezkl, pathlib
base = pathlib.Path("external_repos/ezkl-fresh-1l-relu")
res = ezkl.verify(
    str(base / "proof.json"),
    str(base / "settings.json"),
    str(base / "test.vk"),
    str(base / "srs_17"),
)
print(res)
PY
```

Expected baseline output:

```text
True
```

Regenerate the baseline:

```bash
external_repos/ezkl-audit-venv/bin/python - <<'PY'
import ezkl, pathlib
base = pathlib.Path("external_repos/ezkl-fresh-1l-relu")
run_args = ezkl.PyRunArgs()
run_args.input_visibility = "private"
run_args.output_visibility = "public"
run_args.param_visibility = "private"
run_args.logrows = 17
run_args.input_scale = 7
run_args.param_scale = 7
run_args.scale_rebase_multiplier = 1
ezkl.gen_settings(str(base / "network.onnx"), str(base / "settings.json"), py_run_args=run_args)
ezkl.compile_circuit(str(base / "network.onnx"), str(base / "model.compiled"), str(base / "settings.json"))
ezkl.gen_srs(str(base / "srs_17"), 17)
ezkl.setup(str(base / "model.compiled"), str(base / "test.vk"), str(base / "test.pk"), str(base / "srs_17"))
ezkl.gen_witness(str(base / "input.json"), str(base / "model.compiled"), str(base / "witness.json"))
ezkl.prove(str(base / "witness.json"), str(base / "model.compiled"), str(base / "test.pk"), str(base / "proof.json"), srs_path=str(base / "srs_17"))
print(ezkl.verify(str(base / "proof.json"), str(base / "settings.json"), str(base / "test.vk"), str(base / "srs_17")))
PY
```

## Current Recommendation

Keep EZKL as a lower-severity but high-signal Tablero target:

- best case: find an official or downstream wrapper that presents mutable
  metadata as authoritative, then disclose privately;
- likely case: EZKL core is fine and Tablero learns how to wrap EZKL artifacts
  cleanly;
- bad case: only our wrapper is confused, which still improves our own
  statement-boundary discipline.
