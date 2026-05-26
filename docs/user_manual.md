# QCchem User Manual

This manual covers the everyday QCchem workflow: install, run, inspect outputs,
work with aggregate studies, and understand release boundaries.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Optional extras:

```bash
python -m pip install -e ".[ui]"
python -m pip install -e ".[runtime]"
python -m pip install -e ".[ai]"
```

## Single Run Workflow

Run from a YAML config:

```bash
qcchem run -c configs/h2.yaml -o artifacts/h2_local
```

Inspect before running:

```bash
qcchem inspect -c configs/lih_active_vqe.yaml
```

Use an XYZ/PDB/MOL/SDF/MOL2 structure file instead of inline YAML geometry:

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
`basis` stay in the YAML config. QCchem records the structure file path, parser,
atom count, selected first record/model, raw file SHA-256, and normalized
geometry SHA-256 in `result.json`, `report.md`, and QCSchema extras when that
export is enabled. Do not set both `molecule.geometry` and
`molecule.structure_file` in the same config.

Regenerate a report from an existing result:

```bash
qcchem report artifacts/h2/result.json
```

Expected run outputs:

- `result.json`: structured result payload.
- `report.md`: human-readable report.
- `resolved_config.yaml`: fully resolved config snapshot.
- `run.log`: execution log.
- `exact_result.json`: exact baseline when available.
- `quantum_evidence.json`: full quantum evidence sidecar with Pauli terms when
  they are materialized, measurement groups/counts when available, trajectory,
  state diagnostics, resource metrics, error budgets, and sparse/projected
  validation metadata for finite-cutoff field-model runs.
- `runtime_submission.json`: runtime sidecar when runtime submission is attempted.
- `calibration.json` and `calibration_report.md`: empirical execution calibration
  when available.

## Aggregate Workflows

Benchmark suite:

```bash
qcchem benchmark run \
  -c benchmarks/benchmark_suite_v1.yaml \
  -o artifacts/benchmark_suite_v1_local
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

VQE scan workflows use chemical continuity by default. The first scan point uses
the configured `solver.initial_point`, the second point uses the previous VQE
`optimal_parameters`, and later points use a `linear_predictor` over the two
previous optimized parameter vectors. The run artifact records
`variational_result.initial_point_provenance`, and scan tables include whether
the candidate was reused, `candidate_source`, `effective_strategy`, predictor
history, evaluations, parameter count, and any fallback reason.

Study workflows keep continuity off by default because many studies compare
different basis sets, active spaces, mappings, or ansatz shapes. Enable it only
for ordered sweeps where the YAML run order is chemically meaningful:

```yaml
study:
  continuity:
    enabled: true
    mode: previous_optimal
    on_parameter_mismatch: fallback
```

If the previous optimum has a different parameter count from the current ansatz,
QCchem does not pad or truncate parameters. It falls back to the run's configured
`solver.initial_point` and records the mismatch in provenance.

Aggregate reports should be read as evidence summaries first, then as detailed
case lists.

## Runtime Collection

If a real Runtime job was submitted and local waiting was interrupted, collect
the result later:

```bash
qcchem runtime collect artifacts/h2_runtime_hardware_probe_puccd_layout
```

This reads `runtime_submission.json`, polls provider state when available, and
merges returned metadata back into `result.json` and `report.md`.

## Hardware Optimization

Preview first:

```bash
qcchem hardware optimize \
  -c configs/h2_hardware_precision_push.yaml \
  -o artifacts/h2_hardware_precision_push_preview \
  --preview
```

Real submission is intentionally guarded. Do not use submit mode unless the
budget and backend target have been reviewed at action time.

Runtime-capable `run`, `exploratory run`, `benchmark run`, and hardware
optimization paths accept `--confirm-runtime-budget`, but only the exact
confirmation phrase expected by the configured runtime path unlocks real
submission. Setting `submit_real_job: true` in YAML is not sufficient by itself.

QFT dynamics runtime previews and micro runs should keep tight limits:

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

Use these fields to prevent the default time-grid/observable product from
turning into a large Runtime batch. Real QFT micro jobs should remain small
enough to inspect error bars, residuals, and usage before any larger run.

## Exploratory Workflows

Use `qcchem exploratory run` when the config uses an exploratory solver or model.

QFT finite-cutoff lattice-QED:

```bash
qcchem exploratory run \
  -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml
```

Sparse projected exact lattice-QED runs are finite-model checks, not continuum
chemistry claims. Read these fields first:

- `chemical_accuracy.finite_model_exactness`: internal exactness for the
  configured finite grid/cutoff/softening Hamiltonian.
- `chemical_accuracy.continuum_chemistry_accuracy`: `not_claimed` unless a
  convergence scan is attached.
- `chemical_accuracy.hardware_accuracy`: `unavailable` unless a Runtime or
  shot-based backend result has been submitted and collected.
- `qft_model.sparse_exact_validation`: `eigen_residual_norm`,
  `relative_eigen_residual`, `ground_state_gap`, `lowest_eigenvalues`,
  `projected_matrix_dimension`, `projected_hamiltonian_nnz`,
  `physical_sector_dimension`, `basis_hash`, and `projected_matrix_sha256`.
- `qft_model.observables`: site density, link electric flux, electric energy by
  link, onsite energy by site, hopping energy by link,
  Gauss-law residual by site, and dominant physical-sector configurations.

When `qft_model.engine.pauli_materialization` is `skipped`, the quantum
evidence sidecar records `pauli_terms_available: false` and leaves
`hamiltonian.pauli_terms` empty. Measurement groups and shot cost in this path
are sparse/exploratory estimates; they are not hardware measurement budgets.

LR-ACE:

```bash
qcchem exploratory run -c configs/exploratory/h2_lr_ace.yaml
```

TC-QSCI:

```bash
qcchem exploratory run -c configs/exploratory/h2_tc_qsci.yaml
```

Exploratory artifacts are reproducible research evidence, but they are not
validated chemistry claims.

## Reading `result.json`

Start with:

- `schema_version`
- `problem`
- `mapping`
- `backend`
- `energy`
- `benchmark`
- `chemical_accuracy`
- `runtime_chemical_accuracy`
- `evidence_summary`
- `quantum_evidence`

`chemical_accuracy` may contain separate trust layers. For lattice-QED sparse
exact artifacts, do not treat `absolute_error_hartree: 0` as continuum chemistry
accuracy. The authoritative interpretation is:

- `finite_model_exactness`: finite Hamiltonian internal exactness.
- `continuum_chemistry_accuracy`: continuum chemistry claim status.
- `hardware_accuracy`: Runtime/shot-based hardware claim status.

For Trust-First review, the most important fields are:

- `evidence_summary.primary_scientific_claim`
- `evidence_summary.primary_baseline`
- `evidence_summary.primary_error_metric`
- `evidence_summary.trust_tier`
- `evidence_summary.recommended_action`

The compact `quantum_evidence` field points to `quantum_evidence.json` and
summarizes the detailed evidence layer. Use the sidecar when you need to audit:

- Pauli Hamiltonian decomposition and per-term energy contributions when Pauli
  terms are available.
- Measurement grouping, shots, bitstring counts, and count digests.
- VQE evaluation trajectory and final-state dominant configurations.
- Hamiltonian variance, particle/spin/Z2/QFT constraint checks.
- Circuit resources, measurement cost, and ansatz/shot/compression/hardware
  error budget.
- Sparse exact validation and lattice-QED observables for projected QFT runs
  where Pauli materialization was intentionally skipped.

Mapping resources now separate the executed Hamiltonian from its untapered
baseline:

- `mapping.num_qubits` and `mapping.qubit_term_count` describe the executed
  qubit Hamiltonian.
- `mapping.raw_num_qubits` and `mapping.raw_qubit_term_count` describe the
  pre-Z2-tapering Hamiltonian.
- `mapping.symmetry_tapered_qubits`, `mapping.z2_symmetry_count`, and
  `mapping.z2_tapering_values` record the Z2 tapering sector and savings.
- `problem.point_group_metadata` and
  `reduction_audit.point_group_metadata` record PySCF point-group irreps.
  Point-group `audit` mode records symmetry only; `irrep_filter` is the
  explicit model-reduction mode.

For exploratory assets, also inspect:

- `qft_model`
- `qft_dynamics`
- `tc_qsci_result`
- `determinant_selection`
- `cast_hamiltonian`
- `low_rank_resource_estimate`
- `qpe_resource_estimate`
- `error_budget`

## Workbench

Start:

```bash
qcchem workbench serve
```

Default route:

```text
http://127.0.0.1:8050/overview
```

Read pages in this order for release demos:

1. Overview
2. Result Confidence
3. Benchmarks
4. Hardware Campaign
5. AI Workspace

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

The audit performs no runtime submission and should not mutate curated artifacts.
