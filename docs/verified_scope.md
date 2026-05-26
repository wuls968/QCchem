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
- exact finite-cutoff real-time dynamics curves, and
- guarded runtime-batch preview metadata.

Boundary: QFT evidence is finite-cutoff lattice-QED evidence only. It is not a
continuum chemistry accuracy claim.

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
- required release terms in README, verified scope, release showcase, and release
  audit docs.

Run:

```bash
qcchem release audit \
  -c configs/release/trust_first_audit.yaml \
  -o artifacts/release_audit
```
