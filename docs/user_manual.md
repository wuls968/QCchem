# QCchem User Manual

This manual is the operational guide for QCchem users. It explains how to run
local calculations, validate artifacts, inspect evidence, use Research OS
analysis commands, open the Workbench, and keep release language conservative.

Use the README for quick orientation. Use this manual when you need the exact
command sequence or the meaning of an artifact field.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Install optional extras only when needed:

```bash
python -m pip install -e ".[ui]"       # qcchem workbench serve
python -m pip install -e ".[runtime]"  # IBM Runtime submit/collect helpers
python -m pip install -e ".[ai]"       # AI workspace provider adapter
```

Use local output directories such as `artifacts/h2_local` while experimenting.
Curated artifacts under `artifacts/` are release evidence and should not be
rewritten casually.

## Command Cheat Sheet

| Goal | Command |
| --- | --- |
| Run one calculation | `qcchem run -c configs/h2.yaml -o artifacts/h2_local` |
| Inspect a config | `qcchem inspect -c configs/lih_active_vqe.yaml` |
| Regenerate a report | `qcchem report artifacts/h2/result.json` |
| Preview active-space selection | `qcchem active-space recommend -c configs/lih_active_space_trusted_score.yaml -o artifacts/lih_active_space_recommendation.json --emit-yaml-patch` |
| Validate PBC/PBC-QMMM | `qcchem validation pbc-qmmm --profile smoke -o artifacts/pbc_qmmm_validation_smoke` |
| Run a benchmark suite | `qcchem benchmark run -c benchmarks/benchmark_suite_v1.yaml -o artifacts/benchmark_suite_v1_local` |
| Evaluate benchmark acceptance | `qcchem benchmark accept artifacts/benchmark_suite_v1/benchmark_result.json` |
| Run a study | `qcchem study run -c configs/studies/mini_comparison.yaml -o artifacts/mini_comparison_study_local` |
| Run a scan | `qcchem scan run -c configs/scans/h2_short_scan.yaml -o artifacts/h2_short_scan_local` |
| Run a custom workflow | `qcchem workflow run -c examples/workflows/h2_trust_first_workflow.yaml` |
| Index artifacts | `qcchem artifacts index artifacts` |
| Build an evidence capsule | `qcchem artifacts capsule artifacts/h2 -o artifacts/capsule_smoke/h2` |
| Plan a research objective | `qcchem objective plan -c configs/objectives/h2_local_validation.yaml -o artifacts/objectives/h2_local_validation_plan` |
| Check claim language | `qcchem claim check --claim-file examples/claims/hardware_overclaim.txt --target artifacts/hardware_calibration_suite_v1 -o artifacts/claim_reviews/hardware_overclaim` |
| Review exploratory promotion | `qcchem promote exploratory --artifact artifacts/h2_lr_ace/result.json --target validated_algorithm_candidate -o artifacts/promotion/h2_lr_ace` |
| Collect a Runtime result | `qcchem runtime collect artifacts/h2_runtime_hardware_probe_puccd_layout` |
| Serve the Workbench | `qcchem workbench serve` |
| Smoke-test Workbench routes | `qcchem workbench smoke --docs docs/workbench.md -o artifacts/workbench_smoke.json` |
| Run release audit | `qcchem release audit -c configs/release/trust_first_audit.yaml -o artifacts/release_audit` |
| Summarize release status | `qcchem release status --audit-dir artifacts/release_audit --strict` |
| Verify downloaded release diagnostics | `qcchem release verify-artifacts --artifact-dir <downloaded-artifacts>` |
| Collect post-CI release evidence | `qcchem release collect-evidence --artifact-dir <downloaded-artifacts>` |
| Check release sidecars | `qcchem release acceptance-status -c configs/release/trust_first_audit.yaml --strict` |
| Plan release sidecar repairs | `qcchem release acceptance-status -c configs/release/trust_first_audit.yaml --strict --repair-plan` |
| Preview release sidecar refresh | `qcchem release accept-artifact -c configs/release/trust_first_audit.yaml --name h2_local_validated_anchor --dry-run` |
| Refresh release sidecar | `qcchem release accept-artifact -c configs/release/trust_first_audit.yaml --name h2_local_validated_anchor --overwrite` |

Runtime-capable commands accept `--confirm-runtime-budget`, but real submission
only unlocks when the configured confirmation phrase is supplied at action time.
Setting `submit_real_job: true` in YAML is not sufficient by itself.

## Run Single Calculations

Run from a YAML config:

```bash
qcchem run -c configs/h2.yaml -o artifacts/h2_local
```

Use dedicated artifact directories for outputs. QCchem refuses root/home paths,
the repository root, top-level `artifacts/`, or source-tree paths outside
`artifacts/` before it creates or replaces outputs.
Relative `run.output_dir` values are resolved under the workspace that owns the
config file. If you run a standalone YAML outside the checkout, its `artifacts/`
directory is created beside that YAML unless you pass `-o`.

Inspect before running:

```bash
qcchem inspect -c configs/lih_active_vqe.yaml
```

Regenerate a report from an existing result:

```bash
qcchem report artifacts/h2/result.json
```

### Structure Files

Use `molecule.structure_file` when coordinates live in XYZ, PDB, MOL/SDF V2000,
or MOL2:

```yaml
molecule:
  name: H2-from-xyz
  structure_file: examples/structures/h2.xyz
  structure_format: xyz
  charge: 0
  multiplicity: 1
  basis: sto3g
```

```bash
qcchem run -c examples/h2_from_xyz.yaml -o artifacts/h2_from_xyz_local
```

File coordinates are interpreted as angstrom. `charge`, `multiplicity`, and
`basis` stay in YAML. QCchem records the parser, resolved path, atom count,
selected first record/model, raw file SHA-256, and normalized geometry SHA-256
in run provenance. Do not set both `molecule.geometry` and
`molecule.structure_file` in one config.

## Validate PBC And PBC-QMMM

Run the smoke profile:

```bash
qcchem validation pbc-qmmm --profile smoke -o artifacts/pbc_qmmm_validation_smoke
```

The smoke profile runs:

- `configs/pbc_h2_gamma.yaml`
- `configs/pbc_h2_qmmm.yaml`
- a non-Gamma rejection fixture

It writes `pbc_qmmm_validation.json`, `pbc_qmmm_validation.md`, and
`metrics.csv`. The full profile also exercises VQE/twolocal, active-space,
compression, LR-ACE, and TC-QSCI routing on the Gamma-only PBC Hamiltonian.

Validated v1 scope:

- Gamma-only/supercell electronic structure.
- Fixed-charge PBC-QM/MM Ewald electrostatics.
- Closed-shell RHF, fully periodic 3D cells, matching molecule/cell units.
- Neutral full QM/MM cells with `neutralization: reject`.
- Reports, QCSchema extras, HDF5 exports, artifact indexing, and Workbench
  model propagation.

Out of scope:

- Non-Gamma mapped quantum algorithms.
- Forces, stress, cell optimization, PME dynamics, polarization, MM relaxation.
- Mixed periodic axes, open-shell/UHF mapping, runtime submission.
- Charged full QM/MM cells or uniform-background neutralization.

## Run Aggregate Workflows

Benchmark suite:

```bash
qcchem benchmark run \
  -c benchmarks/benchmark_suite_v1.yaml \
  -o artifacts/benchmark_suite_v1_local
```

For suites that mix quick gates and slow diagnostics, select a tagged subset:

```bash
qcchem benchmark run \
  -c benchmarks/lr_ace_flagship_suite_v1.yaml \
  --include-tag fast \
  -o artifacts/lr_ace_flagship_fast
```

Study:

```bash
qcchem study run \
  -c configs/studies/mini_comparison.yaml \
  -o artifacts/mini_comparison_study_local
```

Scan:

```bash
qcchem scan run \
  -c configs/scans/h2_short_scan.yaml \
  -o artifacts/h2_short_scan_local
```

Aggregate workflows preserve underlying run artifacts and add suite-level JSON,
Markdown reports, tables, registries, and acceptance summaries. Read aggregate
reports as best-evidence summaries first, then drill into individual case
artifacts. Existing non-empty aggregate output directories are rejected by
default; rerun with `--overwrite` only when you intentionally want to replace
that output bundle. Output paths with existing symlink components are rejected
before replacement so overwrite runs cannot follow a link into another directory.

VQE scan workflows use chemical continuity by default. The first point uses the
configured `solver.initial_point`, the second uses the previous VQE optimum, and
later points use a `linear_predictor` over the two previous optimized parameter
vectors. Scan tables record candidate reuse, source, effective strategy,
predictor history, evaluations, parameter count, and fallback reason.

Study workflows keep continuity off by default because many studies compare
different basis sets, active spaces, mappings, or ansatz shapes. Enable it only
for ordered sweeps where YAML run order is chemically meaningful:

```yaml
study:
  continuity:
    enabled: true
    mode: previous_optimal
    on_parameter_mismatch: fallback
```

QCchem does not pad or truncate parameters when ansatz parameter counts differ.
It falls back to the configured initial point and records the mismatch.

## Custom Workflows

Create, validate, and run a YAML-first workflow:

```bash
qcchem workflow template -o examples/workflows/local_workflow.yaml
qcchem workflow validate -c examples/workflows/h2_trust_first_workflow.yaml
qcchem workflow run -c examples/workflows/h2_trust_first_workflow.yaml
qcchem workflow report artifacts/workflows/h2_trust_first_workflow/workflow_result.json
qcchem workflow plugins
```

Workflow outputs live under the configured `workflow.output_root` and include
`workflow_result.json`, `workflow_report.md`, `workflow_graph.json`,
`step_outputs/`, `provenance.jsonl`, and `registry.json`.

`workflow run` refuses to replace an existing non-empty output directory by
default. Use `--overwrite` only for a deliberate rerun of that workflow bundle.
Symlinked output paths are rejected before replacement for the same data-loss
reason.

Installed Python plugins are discovered through the `qcchem.workflow_steps`
entry point group. Treat installed plugins as trusted local code, but keep real
runtime or hardware submission behind the existing QCchem confirmation gates.

## Preview Active-Space Recommendations

Preview a trusted active-space recommendation without running the quantum solver:

```bash
qcchem active-space recommend \
  -c configs/lih_active_space_trusted_score.yaml \
  -o artifacts/lih_active_space_trusted_score_recommendation.json \
  --emit-yaml-patch
```

Active-space auto selection supports:

- `frontier_orbitals`: the legacy contiguous HOMO/LUMO window heuristic.
- `trusted_orbital_score`: a PySCF-backed rule scorer with orbital energies,
  SCF occupations, optional MP2 natural-occupation diagnostics, candidate
  scores, confidence, resource-budget rejections, warnings, and provenance
  under `active_space_metadata.recommendation`.

Treat this as auditable classical preprocessing. It is not a standalone
chemistry validation claim.

## Use Research OS Analysis Commands

Use Research Objectives for a claim, required evidence, candidate configs,
promotion policy, and next action:

```bash
qcchem objective init \
  --name h2-local-validation \
  --claim "H2/STO-3G local statevector energy is validated against exact baseline" \
  -o configs/objectives/h2_local_validation_draft.yaml

qcchem objective plan \
  -c configs/objectives/h2_local_validation.yaml \
  -o artifacts/objectives/h2_local_validation_plan

qcchem objective status \
  -c configs/objectives/h2_local_validation.yaml \
  -o artifacts/objectives/h2_local_validation_status
```

Use Evidence Capsules before treating an artifact as best evidence:

```bash
qcchem artifacts capsule artifacts/h2 -o artifacts/capsule_smoke/h2
```

Use the Claim Compiler to detect overclaim language:

```bash
qcchem claim check \
  --claim-file examples/claims/hardware_overclaim.txt \
  --target artifacts/hardware_calibration_suite_v1 \
  -o artifacts/claim_reviews/hardware_overclaim
```

Use the Promotion Gate before using candidate or validated language for QFT,
LR-ACE, TC-QSCI, or any other exploratory boundary artifact:

```bash
qcchem promote exploratory \
  --artifact artifacts/h2_lr_ace/result.json \
  --target validated_algorithm_candidate \
  -o artifacts/promotion/h2_lr_ace
```

These commands are local analysis paths. They preserve trust tier, baseline
strength, chemical accuracy status, runtime evidence status, hardware
verification boundary, and recommended next action. They do not submit hardware
jobs or promote exploratory artifacts automatically.

## Use Runtime And Hardware Paths

If a real Runtime job was submitted and local waiting was interrupted, collect
the result later:

```bash
qcchem runtime collect artifacts/h2_runtime_hardware_probe_puccd_layout
```

This reads `runtime_submission.json`, polls provider state when available, and
merges returned metadata back into `result.json` and `report.md`.

Preview hardware optimization before any real submission:

```bash
qcchem hardware optimize \
  -c configs/h2_hardware_precision_push.yaml \
  -o artifacts/h2_hardware_precision_push_preview \
  --preview
```

Real submission requires explicit runtime-budget confirmation and should remain
small enough to inspect error bars, residuals, usage, and bias before spending
more budget.

For QFT dynamics runtime previews and micro runs, keep tight limits:

```yaml
problem:
  qft:
    dynamics:
      runtime:
        time_point_indices: [0, 10]
        observable_names: [particle_number, total_gauss_violation]
        max_pub_count: 4
        max_total_pub_shots: 2048
        max_logical_depth: 200
```

## Run Exploratory Workflows

Use `qcchem exploratory run` when the config uses an exploratory solver or
field model.

QFT finite-cutoff lattice-QED:

```bash
qcchem exploratory run \
  -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml
```

LR-ACE legacy exploratory probe:

```bash
qcchem exploratory run -c configs/exploratory/h2_lr_ace.yaml
```

TC-QSCI:

```bash
qcchem exploratory run -c configs/exploratory/h2_tc_qsci.yaml
```

Exploratory artifacts are reproducible research evidence. They are not
validated chemistry claims unless a later release explicitly moves them through
the required validation gate.

## Read Artifacts

Expected single-run files:

- `result.json`: structured result payload.
- `report.md`: human-readable report.
- `resolved_config.yaml`: fully resolved config snapshot.
- `run.log`: execution log.
- `exact_result.json`: exact baseline when available.
- `quantum_evidence.json`: detailed quantum evidence sidecar.
- `runtime_submission.json`: runtime sidecar when submission is attempted.
- `calibration.json` and `calibration_report.md`: empirical calibration when
  available.

Field-model runs may also write:

- `field_model_registry.json`
- `field_hamiltonian.json`
- `field_observables.json`
- `field_dynamics.json`
- `field_constraints.json`
- `field_resources.json`
- `field_error_budget.json`

Start with these `result.json` fields:

- `schema_version`
- `problem`
- `mapping`
- `backend`
- `energy`
- `chemical_accuracy`
- `runtime_chemical_accuracy`
- `evidence_summary`
- `quantum_evidence`
- `field_evidence`
- `pbc`
- `pbc_qmmm`

For Trust-First review, read:

- `evidence_summary.primary_scientific_claim`
- `evidence_summary.primary_baseline`
- `evidence_summary.primary_error_metric`
- `evidence_summary.trust_tier`
- `evidence_summary.recommended_action`

Use `quantum_evidence.json` for:

- Pauli Hamiltonian decomposition and per-term energy contributions.
- Measurement grouping, shots, bitstring counts, and count digests.
- VQE trajectory and final-state dominant configurations.
- Hamiltonian variance, particle/spin/Z2/QFT constraint checks.
- Circuit resources, measurement cost, and error budgets.
- Sparse exact validation and lattice-QED observables when Pauli
  materialization is skipped.

Local `shot_estimator` runs default to QCchem's Python statevector/Pauli shot
sampler rather than native Aer C++ execution, so `shots`, seeds, repetitions,
and uncertainty estimates remain reproducible in long pytest or notebook
sessions. The Aer-compatible parallelism fields
(`max_parallel_threads=1`, `max_parallel_experiments=1`,
`max_parallel_shots=1`) remain bounded in metadata and config handling for
native-Aer opt-in paths.

CUDA-Q/MKL-Q execution is optional and uses the `cudaq` Python API at runtime;
QCchem does not vendor `/Users/a0000/Documents/MKL-Q`. Use:

- `backend.kind: cudaq_statevector` for deterministic observe-style estimates.
- `backend.kind: cudaq_sample` with `backend.shots` for shot-based repeated
  sampling and `sampled_result` artifacts.
- `backend.runtime.options.target: mklq-cpu` by default, or explicit
  `mklq-metal`, `qpp-cpu`, or `nvidia`.

`mklq-metal` is recorded as experimental mixed Metal/CPU smoke evidence. Local
CUDA-Q/MKL-Q simulator paths keep `hardware_verified == false`; reports and
`result.json` store the CUDA-Q version, module path, target, available targets,
GPU count, and evidence tier in `backend.metadata`.

Use field sidecars for finite-cutoff QFT and cavity evidence:

- Lattice-QED grid, matter/gauge qubits, U(1) link cutoff, Gauss-law
  generators, physical-sector hash, Wilson/electric observables, and Trotter
  diagnostics.
- Pauli-Fierz cavity-QED photon occupation, dipole expectation,
  electron-photon coupling, dipole self energy, polaritonic composition, photon
  leakage, and photon-cutoff inputs.
- Sector-level field-Hamiltonian energy closure against the solver
  Hamiltonian.

Scalar, fermion, and generic gauge-field placeholder registry entries are schema
only and are not scientific evidence.

## Interpret Trust Boundaries

`hardware_verified` means runtime provenance exists: submission metadata, job
identity when available, retrieved result status, and sidecar merge history. It
does not mean chemical accuracy was achieved.

QFT sparse exact artifacts split accuracy into:

- `finite_model_exactness`: internal exactness for the configured finite grid,
  cutoff, and softening Hamiltonian.
- `continuum_chemistry_accuracy`: `not_claimed` unless convergence evidence is
  attached.
- `hardware_accuracy`: `unavailable` unless a Runtime or shot-based backend
  result has been submitted and collected.

When `qft_model.engine.pauli_materialization` is `skipped`, the quantum evidence
sidecar records `pauli_terms_available: false` and leaves
`hamiltonian.pauli_terms` empty. Read `sparse_exact_validation` instead:

- `eigen_residual_norm`
- `relative_eigen_residual`
- `ground_state_gap`
- `lowest_eigenvalues`
- `projected_matrix_dimension`
- `projected_hamiltonian_nnz`
- `physical_sector_dimension`
- `basis_hash`
- `projected_matrix_sha256`

LR-ACE flagship artifacts are gated method evidence, not blanket method
validation. Legacy LR-ACE configs remain exploratory unless a release gate says
otherwise.

TC-QSCI records determinant selection, symmetry-sector checks, CAST sampling
provenance, low-rank resource estimates, QPE resource estimates, and error
budget fields. It remains exploratory.

## Workbench

Start:

```bash
qcchem workbench serve
```

The server reads `./artifacts` from the current working directory when present.
When launching an installed wheel from outside the checkout, pass the evidence
root explicitly:

```bash
qcchem workbench serve --artifact-root /path/to/QCchem/artifacts
```

Missing explicit artifact roots are rejected instead of silently rendering
sample fallback data.

Default route:

```text
http://127.0.0.1:8050/overview
```

Read release-demo pages in this order:

1. Overview
2. Result Confidence
3. Benchmarks
4. Hardware Campaign
5. AI Workspace
6. Workflow Studio

The Workbench should lead with best evidence, trust tier, baseline strength,
chemical accuracy status, runtime evidence status, hardware verification
boundary, exploratory boundary, and recommended next action before raw algorithm
settings.

Before release handoff, run the component-tree smoke gate:

```bash
qcchem workbench smoke --docs docs/workbench.md -o artifacts/workbench_smoke.json
```

Outside the checkout, include `--artifact-root /path/to/QCchem/artifacts` so the
smoke gate renders the same evidence root as the browser server.
Missing explicit artifact roots are rejected with exit code `2`.

The JSON summary is local diagnostic output. It is intentionally ignored by git
and includes route labels, registered routes, failed checks, and bounded text
excerpts for CI triage. When a `release_artifact_verification.json` report is
indexed under the selected artifact root, the same smoke JSON also records its
status, source path, matrix artifact counts, and failure count.

## Release Audit

Run:

```bash
qcchem release audit \
  -c configs/release/trust_first_audit.yaml \
  -o artifacts/release_audit
```

Outputs:

- `release_readiness.json`
- `release_readiness.md`
- `release_handoff.json`
- `release_handoff.md`
- `release_diagnostics_manifest.json` in CI, written before diagnostic upload
- `release_evidence/release_evidence_summary.json` in CI, written before diagnostic upload
- `release_evidence/release_evidence_handoff.md` in CI, written before diagnostic upload
- `release_history_summary.json` in CI, written before diagnostic upload
- `release_history_summary.md` in CI, written before diagnostic upload

Release audit reads local source files, docs, configs, and curated artifacts. It
performs no runtime submission and should not mutate curated artifacts. On
failure, read `release_handoff.md` first for the compact run/artifact entrypoint,
then `release_readiness.md` for failed check names and recommended actions.
The CLI prints both generated paths; in GitHub Actions it also prints the exact
`qcchem-release-diagnostics-*` artifact name, artifact listing API URL, and
diagnostics manifest path.
After running the audit, use `qcchem release status --audit-dir
artifacts/release_audit --strict` to read those existing outputs and print a
compact status summary without rerunning the audit. The status command also
fails if the existing readiness or handoff JSON uses an unexpected
`schema_version`, or if required current-schema fields are missing or have the
wrong type, which protects scripts from consuming stale or partial audit bundles.
It also checks that the handoff status, counts, sidecar state, and diagnostics
manifest schema still agree with the readiness JSON before reporting the bundle
as current. CI applies that same validator to both the source-tree and
installed-wheel release bundles. CI diagnostic artifacts include that compact
status JSON, `release_diagnostics_manifest.json` with uploaded-path size and
SHA-256 summaries, the `acceptance-status` sidecar-freshness JSON with its own
`schema_features`, a pre-upload `release_evidence_handoff.md` /
`release_evidence_summary.json` pair, and a single-run
`release_history_summary.json` / `release_history_summary.md` retained-history
handoff for each Python matrix; CI validates the acceptance-status artifact
before upload so the reported counts and repair plan stay consistent with the
item list.

The CI-side reviewer handoff is generated with:

```bash
qcchem release evidence-handoff \
  --audit-dir artifacts/release_audit \
  --workbench-smoke artifacts/workbench_smoke.json \
  --acceptance-status /tmp/qcchem-release-acceptance-status.json \
  --output-dir artifacts/release_evidence
```

It uses `collection_mode: ci_diagnostics_handoff` and intentionally records
downloaded artifact digest verification as `not_run`.

After downloading `qcchem-release-diagnostics-*` artifacts from CI, collect the
offline release evidence handoff:

```bash
qcchem release collect-evidence \
  --artifact-dir /tmp/qcchem-ci-artifacts \
  --docs docs/workbench.md
```

This writes `release_artifact_verification.json`, `release_matrix_summary.json`,
`workbench_smoke.json`, `release_evidence_summary.json`, and reviewer-facing
`release_evidence_handoff.md` under the downloaded artifact directory. The
handoff includes a per-matrix artifact section with release-status count,
manifest digest/file counts, sidecar freshness, failure count, first failure,
and matrix-baseline delta for each `qcchem-release-diagnostics-*` bundle. Use
`--baseline-summary <previous-release_matrix_summary.json>` to compare the
current downloaded matrix set against an earlier collection. Use
`--history-root <history-dir> --history-label <run-id>` when retained evidence
is stored as one directory per run; the collector writes into
`<history-dir>/<run-id>`, refuses to overwrite a non-empty retained run
directory, defaults automatic baseline search to that history root, skips the
current output directory, picks the newest prior `release_matrix_summary.json`,
and records the history path plus baseline selection details in the JSON and
Markdown handoffs. Use `--baseline-search-root <history-dir>` when you already
picked `--output-dir` manually. An explicit `--baseline-summary` takes
precedence. The Markdown
handoff writes inactive or unavailable fields as `not_applicable`,
`not_available`, `not_provided`, or `none` instead of placeholder `None` text.

When the artifacts are still in GitHub Actions, fetch and retain them in one
step:

```bash
qcchem release fetch-ci-evidence \
  --run-id 28834488613 \
  --repo wuls968/QCchem \
  --history-root /tmp/qcchem-release-history
```

This requires the GitHub CLI `gh`. It downloads the run artifacts into an empty
`--download-dir`, or into a generated `/tmp` directory when `--download-dir` is
omitted, then runs the retained `collect-evidence` flow with the run id as the
default `--history-label`. The retained summary and Markdown handoff carry the
same release history handoff verifier count and status reported by
`verify-artifacts`.

To inspect retained runs later, use:

```bash
qcchem release history summarize \
  --history-root /tmp/qcchem-release-history \
  -o /tmp/qcchem-release-history-summary.json
```

This read-only command prints each retained run with release evidence status,
matrix delta status, selected baseline mode, downloaded-artifact verifier
status, release history handoff count, and Workbench smoke status. The optional
JSON output preserves those fields plus first failures and compact status
counts. Add `--strict` when any failed or incomplete retained run should make
the command exit with code `2`.
To write a reviewer-facing Markdown handoff from the same history, use:

```bash
qcchem release history export-markdown \
  --history-summary /tmp/qcchem-release-history-summary.json \
  -o /tmp/qcchem-release-history-summary.md
```

The export can also read `--history-root` directly. It writes only the requested
Markdown path and includes retained run counts, status-count summaries,
selected baselines, matrix-delta counts, verifier status, release history
handoff counts, Workbench smoke status, and first failures.

Use the
lower-level verifier directly when you only need the artifact-integrity check:

```bash
qcchem release verify-artifacts \
  --artifact-dir /tmp/qcchem-ci-artifacts \
  -o /tmp/release_artifact_verification.json
```

This command revalidates release status bundles, sidecar freshness reports,
release history handoff JSON/Markdown/current evidence, diagnostics manifest
counts, and each uploaded file's recorded size and SHA-256.
It exits with code `2` when the downloaded artifact set is missing required
release evidence or no longer matches the manifest.
If you write the report as `release_artifact_verification.json` under an
artifact root, `qcchem artifacts index` classifies it as
`release_artifact_verification`, and the Workbench startup inventory exposes its
count and featured path. The Workbench Overview page also shows the latest
indexed release verification status, matrix artifact counts, and retained
history handoff count when present. The Workbench smoke JSON mirrors that count
in its compact `release_verification` summary. When
`release_matrix_summary.json` is kept under the same artifact root, the index
classifies it as `release_matrix_summary`, startup inventory exposes its count
and featured path, and Overview shows the baseline matrix-artifact count plus
failed count. When a retained-history overview is written as
`release_history_summary.json` under the artifact root, the index classifies it
as `release_history_summary`, startup inventory exposes its count and featured
path, and Overview shows retained run counts plus matrix-delta status counts.
When the retained-history Markdown is kept as `release_history_summary.md` or
`release_history_handoff.md` next to that JSON, the index classifies it as
`release_history_handoff`, startup inventory exposes its count and featured
path, and Overview shows the Markdown path while reading status/count fields from
the sibling JSON.
When
`release_evidence_handoff.md` is kept next to `release_evidence_summary.json`,
the index classifies the Markdown report as `release_evidence_handoff`, and the
Overview page shows the handoff status, recommended action, first failure,
matrix artifact counts, matrix delta status, and path.

Before publishing release-facing docs, also run:

```bash
git diff --check
git diff --name-only -- .github artifacts README.md docs configs qcchem tests pyproject.toml
git status --short --untracked-files=all -- .github artifacts README.md docs configs qcchem tests pyproject.toml
```

The last two commands should print nothing except intentionally ignored local
outputs such as `artifacts/artifact_index.json`,
`artifacts/workbench_smoke.json`, `artifacts/release_audit/`, and
`artifacts/release_evidence/`.
