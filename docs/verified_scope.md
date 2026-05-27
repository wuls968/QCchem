# QCchem Verified Scope

This document defines what QCchem currently verifies, what remains exploratory,
and which words must not be over-interpreted in release-facing reports.

## Trust-First Release Semantics

QCchem `0.1.0a1` uses the Evidence Core as its public contract. A release-facing
artifact should lead with:

- `best evidence`
- `trust tier`
- `baseline strength`
- `chemical accuracy status`
- `runtime evidence status`
- `recommended next action`
- `hardware verification boundary`
- `exploratory boundary`
- `release audit`

The central object is `evidence_summary`. It records identity, primary claim,
baseline, error metric, local chemistry status, runtime status, trust tier, and
next action before any detailed payload sections.

## Validated Surface

The validated surface currently includes:

- Evidence Summary for run artifacts, study aggregates, benchmark cases,
  benchmark suites, scan points, scan aggregates, hardware campaign aggregates,
  and AI-facing summaries.
- H2 exact and statevector ground-state workflows.
- LiH exact and LiH active-space VQE benchmark workflows.
- H2O active-space exact workflow.
- Active-space, freeze-core, remove-virtual, and active-space auto
  recommendation provenance.
- Trusted active-space recommendation preview with PySCF orbital diagnostics,
  rule-scored candidates, confidence, warnings, resource-budget rejections, and
  reportable provenance. This is a classical preprocessing aid, not a
  standalone chemistry validation claim.
- Reduction audit fields: original/reduced system size, transformer list,
  selected/frozen/removed orbitals, Hamiltonian constants, and energy formula.
- Modified-Cholesky compression-aware execution.
- Compressed exact and ideal low-rank measurement planning.
- PySCF NEVPT2 classical-reference correction task.
- Benchmark Suite v1, low-rank benchmark suite, study aggregation, and 1D H2
  bond scan workflows.
- Exact-spectrum excited-state mini baseline.
- Dipole moment exact-expectation property path.
- Runtime sidecar persistence and `qcchem runtime collect` rehydration path.
- Hardware calibration dashboard artifact/report path.
- H2 hardware optimization preview and guarded submit/collect mechanics.
- Workbench startup summary, page inventory, default route, and artifact
  inventory rooted at repository `artifacts/`.
- Evidence Console v2 shared language for overview, runtime monitoring,
  hardware campaign, and AI Workspace surfaces.
- CLI-first AI agent task interface and JSON summary path.
- Trust-First release audit through `qcchem release audit` and
  `configs/release/trust_first_audit.yaml`.
- Research Objective planning/status, Evidence Capsule validation, Claim
  Compiler review, and Promotion Gate review as local analysis-only workflow
  surfaces.
- Gamma-only PBC and PBC-QM/MM Ewald execution through reports, QCSchema extras,
  artifact index, workbench data/view models, and
  `qcchem validation pbc-qmmm`.

## Hardware-Verified Boundary

`hardware_verified` means:

- a real runtime submission happened,
- runtime provenance was persisted,
- a provider result was retrieved or a sidecar can be collected later, and
- the artifact can be grouped with real hardware/runtime evidence.

It does not mean:

- chemical accuracy was achieved,
- the remote chemistry workflow is publication-grade, or
- the result will reproduce on another backend, time window, or shot budget.

Hardware-derived chemistry quality is expressed separately with
`runtime_evidence_status`, `runtime_chemical_accuracy`, and
`recommended_action`.

Current hardware evidence supports the plumbing and budget-ledger loop more
strongly than the chemistry claim. The H2 hardware precision campaign submitted
and collected two controlled Runtime jobs:

- `parity_puccd_layout`: depth `22`, 2Q gates `4`, runtime error
  approximately `0.0182535 Ha`.
- `jw_puccd_layout_baseline`: depth `149`, 2Q gates `42`, runtime error
  approximately `0.0477009 Ha`.

This validates submission, sidecar, collect, and budget tracking. It does not
promote the chemistry result to `validated`.

## Exploratory Surface

Exploratory assets produce real artifacts and reports, but their claims remain
outside the validated release surface.

### QFT / Lattice-QED

QFT assets include:

- compact U(1) finite-cutoff lattice-QED Hamiltonian construction,
- Gauss-law generators and commutator audits,
- sparse projected physical-sector engine for small grids,
- sector-first projected sparse construction and basis hashing,
- sparse exact validation fields such as `eigen_residual_norm`,
  `relative_eigen_residual`, `ground_state_gap`, `lowest_eigenvalues`, and
  `projected_matrix_sha256`,
- lattice-QED observables including site density, link electric flux,
  electric-energy by link, onsite/hopping energy breakdowns, Gauss-law residuals,
  and dominant physical-sector configurations,
- exact finite-cutoff real-time dynamics curves, and
- guarded runtime-batch preview metadata.
- independent field evidence sidecars for registry, Hamiltonian sectors,
  observables, dynamics, constraints, resources, and error budgets.

Boundary: QFT evidence is finite-cutoff lattice-QED evidence only. The sparse
exact path splits accuracy into `finite_model_exactness`,
`continuum_chemistry_accuracy`, and `hardware_accuracy`. A passed finite-model
exactness gate does not claim continuum chemistry accuracy; that layer remains
`not_claimed` until grid/cutoff/softening convergence evidence exists. Hardware
accuracy remains `unavailable` unless a real Runtime/shot-based backend result is
submitted and collected.

When `pauli_materialization=skipped`, `quantum_evidence.json` must report
`pauli_terms_available: false` and leave `hamiltonian.pauli_terms` empty. It
must not present a zero-coefficient identity Pauli term as the Hamiltonian.
Measurement group counts and shot-cost values on that path are
sparse/exploratory estimates, not real hardware measurement costs.

### Pauli-Fierz Cavity-QED

Cavity-QED assets include:

- finite photon-cutoff Pauli-Fierz Hamiltonian construction,
- photon occupation, dipole expectation, electron-photon coupling, dipole self
  energy, polaritonic composition, and photon-subspace leakage observables,
- photon-cutoff inputs for convergence campaigns, and
- independent field evidence sidecars aligned with the QFT artifact family.

Boundary: cavity-QED evidence is exact or variational only for the configured
electron-photon Hamiltonian and photon cutoff. It is not an external
cavity-QED benchmark validation.

### Field-Model Placeholders

The scalar-field, fermion-field, and generic gauge-field registry entries are
schema placeholders. They exist so future field-model plugins can share the same
artifact contract, but they do not implement Hamiltonian construction or solver
evidence and must not be used as scientific claims.

### PBC / PBC-QMMM

QCchem v1 supports Gamma-only/supercell periodic electronic structure through
`qcchem.pbc.pyscf_adapter` and fixed-charge PBC-QM/MM electrostatics through
`qcchem.pbc.ewald`. The validated slice checks plain PBC, PBC-QM/MM Ewald,
non-Gamma k-point rejection, VQE/twolocal, active-space, compression, LR-ACE,
TC-QSCI routing, reports, QCSchema/HDF5 exports, artifact indexing, and
workbench models.

Boundary: non-Gamma k-point mapped quantum algorithms, forces, stress, cell
optimization, PME dynamics, polarization, MM relaxation, and covalent PBC-QM/MM
boundary embedding are not claimed in v1. The implementation also rejects mixed
molecule/cell units, reduced-dimensional PBC flags, open-shell/UHF mapping,
runtime submission, charged full QM/MM cells, and uniform-background
neutralization.

### LR-ACE

LR-ACE flagship assets include:

- H2 local exact-baseline gate with 2 qubits and 1 parameter,
- LiH active-space local exact-baseline gate with 2 qubits and compact
  parameter counts,
- adaptive local gate examples for H2O active space, H3+, and H4 chain, and
- retrieved H2 Runtime probes with best runtime error near, but above, the
  chemical-accuracy threshold.

Boundary: LR-ACE flagship is the recommended QCchem method surface when its
trust-first validation gate passes. Legacy exploratory LR-ACE assets remain
inside the exploratory boundary, and runtime retrieval alone does not validate
LR-ACE as a general publication-grade algorithm.

### TC-QSCI

TC-kicked QSCI assets include:

- determinant selection,
- symmetry-sector audit,
- CAST-QC sampling provenance,
- low-rank resource summaries,
- QPE resource summaries, and
- error budget fields.

Boundary: CAST Hamiltonians guide sampling only. The selected subspace is
diagonalized with the physical Hamiltonian, and the entire workflow remains
exploratory.

## Unstable Surface

The unstable surface includes:

- H2 shot VQE.
- H2 noisy local execution.
- H2 noisy comparison benchmark.
- H2 shot scaling benchmark.
- Hardware-ready shot paths before real collection.
- LiH low-rank runtime-ready sampled path.

Unstable artifacts are useful for engineering and design pressure. They should
not be used as release claims without a stronger evidence gate.

## Placeholder Surface

The following are schema or metadata hooks unless a specific workflow states
otherwise:

- readout mitigation,
- zero-noise extrapolation,
- probabilistic error cancellation,
- several property names outside the validated exact-expectation path, and
- generic embedding/fragment solver plugins.

Placeholder sections should be explicit in reports and must not be promoted by
release audit.

## Release Audit Coverage

The release audit checks local source files, docs, configs, and curated
artifacts. It performs no runtime submission. The default manifest verifies:

- `pyproject.toml` release version,
- required Evidence Summary fields in curated artifacts,
- conservative runtime/hardware boundary language,
- QFT, LR-ACE, and TC-QSCI exploratory boundary classification, and
- required release terms in README, verified scope, release showcase, release
  audit docs, and Research OS docs.

The Research OS checks are deliberately local: evidence capsule, claim compiler,
promotion gate, and research objective artifacts may be reviewed by the audit,
but the audit does not run calculations, submit hardware, or rewrite curated
artifacts.

Release audit must protect the lattice-QED trust boundary language:
`finite_model_exactness`, `continuum_chemistry_accuracy`, `hardware_accuracy`,
`pauli_materialization`, `pauli_terms_available`, and `sparse_exact_validation`
are evidence-boundary terms, not cosmetic report fields.

Run:

```bash
qcchem release audit \
  -c configs/release/trust_first_audit.yaml \
  -o artifacts/release_audit
```
