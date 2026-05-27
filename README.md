<p align="center">
  <img src="qcchem/workbench/assets/qcchem-logo.png" alt="QCchem logo" width="560">
</p>

# QCchem

QCchem is a research workflow scaffold for quantum chemistry experiments built on
Qiskit, Qiskit Nature, PySCF, and local artifact-first workflows. It is not a
single VQE demo. The project is organized around repeatable runs, benchmark
suites, studies, scans, runtime probes, release audits, and a local visual
workbench that all speak the same evidence language.

The current branch is the `Trust-First Release` line for `0.1.0a1`. The release
goal is not to maximize feature count. It is to make every public surface answer
the same questions:

- What claim is being made?
- What baseline is it compared against?
- How large is the error?
- Which trust tier applies?
- What should a careful researcher do next?

## Install

Use an isolated Python environment with Python 3.10 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Optional extras:

```bash
python -m pip install -e ".[ui]"       # Dash workbench
python -m pip install -e ".[runtime]"  # IBM Runtime helpers
python -m pip install -e ".[ai]"       # AI workspace provider adapter
```

## License

QCchem is distributed under the MIT License. See [LICENSE](LICENSE).

## Quick Start

Run a validated H2 example:

```bash
qcchem run -c configs/h2.yaml -o artifacts/h2_local
```

Inspect a config without running it:

```bash
qcchem inspect -c configs/lih_active_vqe.yaml
```

Run from a mainstream molecular structure file:

```bash
qcchem run -c examples/h2_from_xyz.yaml -o artifacts/h2_from_xyz_local
```

Structure-file configs use `molecule.structure_file` plus optional
`molecule.structure_format`. QCchem currently supports XYZ, PDB, MOL/SDF
V2000, and MOL2 without adding RDKit/ASE as required dependencies. The parser
records raw file SHA-256, normalized-geometry SHA-256, resolved path, selected
record/model, and atom count in run provenance; inline `molecule.geometry`
remains supported, but it cannot be mixed with `structure_file` in the same
config.

Run the local Trust-First release gate:

```bash
qcchem release audit \
  -c configs/release/trust_first_audit.yaml \
  -o artifacts/release_audit
```

Validate the executable Gamma-only PBC/PBC-QMMM path:

```bash
qcchem validation pbc-qmmm --profile smoke -o artifacts/pbc_qmmm_validation_smoke
```

The smoke profile runs plain Gamma-only PBC, PBC-QM/MM Ewald, and non-Gamma
k-point rejection cases, then writes `pbc_qmmm_validation.json`,
`pbc_qmmm_validation.md`, and `metrics.csv`. The full profile also exercises
VQE/twolocal, active-space, compression, LR-ACE, and TC-QSCI routing on the same
Gamma-only PBC surface. PBC v1 is deliberately conservative: closed-shell RHF,
fully periodic 3D cells, matching molecule/cell units, neutral full QM/MM cells,
and no runtime submission or uniform-background neutralization.

Evaluate a benchmark acceptance artifact:

```bash
qcchem benchmark accept artifacts/benchmark_suite_v1/benchmark_result.json
```

Build the artifact-driven workbench index:

```bash
qcchem artifacts index artifacts
```

Validate an artifact as an evidence capsule:

```bash
qcchem artifacts capsule artifacts/h2 -o artifacts/capsule_smoke/h2
```

Plan a research objective without running calculations:

```bash
qcchem objective plan \
  -c configs/objectives/h2_local_validation.yaml \
  -o artifacts/objectives/h2_local_validation_plan
```

Compile a claim against best evidence:

```bash
qcchem claim check \
  --claim-file examples/claims/hardware_overclaim.txt \
  --target artifacts/hardware_calibration_suite_v1 \
  -o artifacts/claim_reviews/hardware_overclaim
```

Review an exploratory promotion gate:

```bash
qcchem promote exploratory \
  --artifact artifacts/h2_lr_ace/result.json \
  --target validated_algorithm_candidate \
  -o artifacts/promotion/h2_lr_ace
```

Run an artifact-only campaign:

```bash
qcchem campaign run -c configs/campaign/trust_loop_mini.yaml
```

Run the finite-cutoff lattice-QED sparse exact H2 example:

```bash
qcchem exploratory run \
  -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml \
  -o artifacts/h2_4site_lattice_qed_sparse_exact
```

Open the local workbench when UI dependencies are installed:

```bash
qcchem workbench serve
```

## Development

Install the full development extras and run the same checks used by CI:

```bash
python -m pip install -e ".[dev,ui,ai,runtime]"
python -m compileall qcchem
python -m pytest
```

GitHub Actions runs these checks on push and pull request for Python 3.10,
3.11, and 3.12. The CI workflow does not require OpenAI, IBM Quantum, or other
runtime secrets; real hardware submission stays behind explicit local
confirmation.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution rules, evidence
boundaries, and PR expectations.

## Citation And Security

If you use QCchem in research, cite the software metadata in
[CITATION.cff](CITATION.cff). Security guidance and secret-handling rules are in
[SECURITY.md](SECURITY.md).

## Branding

The QCchem logo and app icon are committed under
`qcchem/workbench/assets/`. The editable Canva design and asset notes are
tracked in [docs/branding.md](docs/branding.md).

## Core Concepts

### Evidence Summary

Every release-facing run or aggregate artifact should expose an
`evidence_summary` with these fields:

- `result_identity`
- `primary_scientific_claim`
- `primary_baseline`
- `primary_error_metric`
- `chemical_accuracy_status`
- `runtime_evidence_status`
- `trust_tier`
- `recommended_action`

This summary is the first object consumed by reports, the workbench, release
audit, and AI tooling.

### Quantum And Field Evidence

Every run writes `quantum_evidence.json` for Pauli execution evidence. Field
model runs additionally write a separate field-evidence artifact family:
`field_model_registry.json`, `field_hamiltonian.json`,
`field_observables.json`, `field_dynamics.json`, `field_constraints.json`,
`field_resources.json`, and `field_error_budget.json`.

These field sidecars are authoritative for finite-cutoff lattice-QED and
Pauli-Fierz cavity-QED observables, constraints, cutoff metadata, sector energy
closure, and field-model error budgets. Placeholder registry entries for scalar,
fermion, and generic gauge fields are schema-only and must not be used as
scientific evidence.

### Trust Tiers

QCchem uses strict categories instead of a single blended score:

- `validated`: local evidence is inside the defended chemistry scope.
- `exploratory`: the artifact is real and reproducible, but the algorithmic or
  modeling claim is not part of the validated release surface.
- `unstable`: the workflow is implemented but known to be noisy, statistically
  weak, or not yet suitable for promotion.
- `hardware_verified`: a real runtime result was submitted and retrieved. This
  does not automatically mean the chemistry claim is validated.

### Hardware Boundary

`hardware_verified` means runtime provenance exists: submission metadata, job
identity when available, retrieved result status, and sidecar merge history. It
does not mean publication-grade chemistry accuracy. Hardware-derived chemistry
accuracy is reported separately as `runtime_evidence_status` and, when present,
`runtime_chemical_accuracy`.

### Research OS Loop

The Trust-First Quantum Chemistry Research OS prototype adds four local analysis
objects:

- `research objective`: records the claim, required evidence, candidate configs,
  promotion policy, and recommended next action.
- `evidence capsule`: validates result/report/config/log/sidecar completeness,
  provenance, trust tier, and boundary warnings.
- `claim compiler`: labels claims as supported, partially supported,
  unsupported, or overclaimed and gives a safe rewrite.
- `promotion gate`: blocks QFT, LR-ACE, and TC-QSCI exploratory artifacts from
  direct validated language unless the required studies exist.

These commands are analysis-only. They do not submit hardware jobs, spend IBM
Runtime budget, read secrets, or mutate curated artifact trust tiers.

## Supported Workflows

### Single Runs

```bash
qcchem run -c configs/h2.yaml -o artifacts/h2
qcchem run -c configs/lih_active_vqe.yaml -o artifacts/lih_active_vqe_local
qcchem report artifacts/h2/result.json
```

Single-run artifacts include `result.json`, `report.md`,
`resolved_config.yaml`, `run.log`, and usually `exact_result.json`.
Field-model runs add the seven `field_*.json` sidecars listed above.
Runtime-facing runs also carry `hardware_error_diagnostic`, which separates
local solver error from runtime-derived error and names the next measurement.

### Benchmarks, Studies, And Scans

```bash
qcchem benchmark run -c benchmarks/benchmark_suite_v1.yaml -o artifacts/benchmark_suite_v1
qcchem study run -c configs/studies/mini_comparison.yaml -o artifacts/mini_comparison_study
qcchem scan run -c configs/scans/h2_short_scan.yaml -o artifacts/h2_short_scan
```

These aggregate workflows preserve the underlying run artifacts while adding
suite-level JSON, Markdown, tables, and registry files.
Benchmark suites can additionally write `acceptance_summary.json`; this is the
machine-readable gate used by campaigns and release audits to decide whether the
evidence loop is accepted.

### Runtime Collection

QCchem writes `runtime_submission.json` as soon as a real runtime job id is
available. If local waiting is interrupted, collect the result later:

```bash
qcchem runtime collect artifacts/h2_runtime_hardware_probe_puccd_layout
```

### Hardware Optimization Preview

Hardware optimization is guarded by preview and confirmation flows:

```bash
qcchem hardware optimize \
  -c configs/h2_hardware_precision_push.yaml \
  -o artifacts/h2_hardware_precision_push_preview \
  --preview
```

Real submission requires explicit runtime-budget confirmation and remains
separate from chemistry validation.

## Exploratory Research Assets

The release keeps exploratory research assets isolated. They can produce normal
artifacts and reports, but they must not be promoted into validated chemistry
claims by default.

### QFT / Lattice-QED

QFT assets model compact U(1) finite-cutoff lattice-QED Hamiltonians, Gauss-law
audits, sparse physical-sector projection, and small real-time dynamics.

```bash
qcchem exploratory run \
  -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml

qcchem exploratory run \
  -c configs/exploratory/h2_4site_lattice_qed_sparse_dynamics.yaml
```

Boundary: these artifacts validate finite-cutoff model consistency and
physical-sector audit only. They do not claim continuum-limit chemistry
accuracy, and they do not claim quantum hardware execution unless a real
Runtime/shot-based result is submitted and collected.

Sparse projected exact runs expose this boundary explicitly:

- `chemical_accuracy.finite_model_exactness`: whether the configured finite
  grid/cutoff/softening Hamiltonian passed its internal exact gate.
- `chemical_accuracy.continuum_chemistry_accuracy`: `not_claimed` until grid,
  cutoff, and softening convergence evidence exists.
- `chemical_accuracy.hardware_accuracy`: `unavailable` until a real Runtime or
  shot-based backend result exists.
- `quantum_evidence.hamiltonian.pauli_terms_available`: `false` when
  `pauli_materialization=skipped`; QCchem does not write a fake zero identity
  Pauli Hamiltonian in that case.
- `quantum_evidence.sparse_exact_validation`: projected dimension, NNZ, basis
  hash, eigen residuals, gap, lowest eigenvalues, and projected matrix SHA-256.
- `qft_model.observables`: site density, link electric flux, electric energy by
  link, onsite/hopping energy breakdowns, Gauss-law residuals, and dominant
  physical-sector configurations.

QFT benchmark suites are available for smoke, cutoff/grid convergence,
dynamics/resource checks, and guarded hardware micro previews:

```bash
qcchem benchmark run -c benchmarks/field_model_qft_smoke_v2.yaml
qcchem benchmark run -c benchmarks/field_model_qft_cutoff_grid_convergence_v1.yaml
qcchem benchmark run -c benchmarks/field_model_qft_dynamics_resource_v1.yaml
```

Real QFT Runtime micro jobs remain budget-gated. A config setting such as
`submit_real_job: true` is not sufficient by itself; submission also requires an
explicit runtime-budget confirmation phrase at action time.

### LR-ACE

LR-ACE, the Low-Rank Adaptive Chemistry Eigensolver, is QCchem's flagship
low-rank-factor-informed variational method. Use the core LR-ACE configs for
trust-first local runs whose artifacts can be promoted only when exact-baseline,
local accuracy, and compression gates pass.

```bash
qcchem run -c configs/lr_ace/h2_flagship.yaml
qcchem run -c configs/lr_ace/lih_active_flagship.yaml
qcchem benchmark run -c benchmarks/lr_ace_flagship_suite_v1.yaml -o artifacts/lr_ace_flagship_suite_v1
```

LR-ACE flagship artifacts record `method_role`, `profile`, and
`validation_gate` under `variational_result.ansatz.lr_ace`, plus
`lr_ace_trust_label` in Evidence Summary. Legacy exploratory LR-ACE configs
remain available for boundary-preserving probes:

```bash
qcchem exploratory run -c configs/exploratory/h2_lr_ace.yaml
qcchem exploratory run -c configs/exploratory/lih_active_lr_ace.yaml
```

Boundary: LR-ACE flagship means default recommended method surface, not a blanket
publication-grade claim. Each run must still pass the trust-first validation
gate before it is reported as validated chemistry.

### TC-QSCI

TC-kicked QSCI is an exploratory determinant-selection workflow. It uses CAST-QC
Hamiltonians only to generate sampling dynamics, then diagonalizes selected
determinants with the physical Hamiltonian.

```bash
qcchem exploratory run -c configs/exploratory/h2_tc_qsci.yaml
qcchem exploratory run -c configs/exploratory/lih_active_tc_qsci.yaml
```

Boundary: TC-QSCI records determinant selection, symmetry-sector checks, CAST
provenance, low-rank resource estimates, QPE resource estimates, and error
budget fields. It is isolated exploratory evidence, not validated production
QSCI.

## AI Workspace

AI Workspace adds a floating research copilot shell to the local workbench and a
dedicated task hub at `/ai-workspace`. The copilot is evidence-aware and
ticket-mediated: free-form requests become structured tickets, accepted tickets
run through QCchem workflows, and delivery records stay linked to persisted
artifacts.

Useful commands:

```bash
qcchem ai draft-ticket \
  --provider examples/ai_workspace/provider.openai-compatible.yaml \
  --request "Compare the H2 hardware campaign evidence." \
  --linked-artifacts artifacts/hardware_calibration_suite_v1

qcchem ai run-ticket examples/ai_workspace/tickets/analysis_h2_campaign.json
```

The default AI posture is conservative. It should summarize Evidence Summary
fields, explain hardware and exploratory boundaries, and propose reviewable next
actions before queueing execution.

## Public Interfaces Added In 0.1.0a1

Config additions:

- `problem.qft`: finite-cutoff lattice-QED model, grid, gauge, constraint,
  engine, and dynamics settings.
- `solver.lr_ace_adaptive`: adaptive LR-ACE candidate schedule and local gate
  settings.
- `tc_qsci`: CAST model, initial state, kick, selection, and resource-estimation
  settings.
- `release_audit`: manifest-driven local release readiness checks.

Result additions:

- `qft_model`
- `qft_dynamics`
- `tc_qsci_result`
- `determinant_selection`
- `symmetry_sector`
- `cast_hamiltonian`
- `low_rank_resource_estimate`
- `qpe_resource_estimate`
- `error_budget`

CLI addition:

```bash
qcchem release audit -c configs/release/trust_first_audit.yaml
```

## Documentation Map

- `docs/user_manual.md`: installation, commands, recipes, and artifact reading.
- `docs/developer_guide.md`: test strategy, warning policy, generated artifact
  hygiene, and release checks.
- `docs/verified_scope.md`: validated, exploratory, unstable, and hardware
  boundaries.
- `docs/release_showcase.md`: repeatable demo path for the release.
- `docs/release_audit.md`: release audit manifest and output contract.
- `docs/tc_qsci.md`: TC-kicked QSCI exploratory workflow details.
- `docs/workbench.md`: local visual workbench guide.
- `docs/ai_workspace.md`: AI workspace ticket and provider flow.

## Verification

Fast targeted checks:

```bash
python -m pytest tests/unit/test_release_audit_v23.py -q
python -m pytest tests/integration/test_qwen_core_integration_v09.py -q
```

Full release check:

```bash
python -m pytest -q
git diff --check
git diff --name-only -- artifacts/lih_active_vqe
```

The final command should print nothing. Tests must not rewrite tracked curated
artifacts.

## Current Limitations

- Some property tasks remain `placeholder_only`; they are represented in schema
  but not validated chemistry.
- Readout mitigation, ZNE, and PEC are still metadata hooks unless explicitly
  implemented by an exploratory workflow.
- Real hardware evidence currently validates runtime plumbing more strongly than
  chemistry accuracy.
- QFT, LR-ACE, and TC-QSCI are deliberately behind the exploratory boundary.
