# QCchem Release Showcase

This is the repeatable demo path for the `Trust-First Release`. The path is
designed to show QCchem as an evidence-first research console rather than a
collection of unrelated quantum chemistry demos.

## Setup

Install the project and optional UI extras:

```bash
python -m pip install -e ".[dev,ui]"
```

Start the local workbench:

```bash
qcchem workbench serve
```

Before a release demo, run:

```bash
qcchem release audit \
  -c configs/release/trust_first_audit.yaml \
  -o artifacts/release_audit
```

The release audit reads local docs, configs, and artifacts only. It performs no
runtime submission.

## Showcase Order

1. Overview
2. Result Confidence
3. Benchmarks
4. Hardware Campaign
5. AI Workspace
6. Exploratory Appendix

## 1. Overview

Route: `/overview`

Use this page to answer:

- What is the current `best evidence`?
- Which case is most worth advancing?
- What is the largest trust gap?
- What is the recommended next action?

The page should lead with the Evidence Summary, not raw algorithm settings.

## 2. Result Confidence

Route: `/result-confidence`

Use this page to answer:

- What is the primary scientific claim?
- What is the primary baseline?
- What is the primary error metric?
- Which `trust tier` applies?
- Does `hardware_verified` mean chemistry validation here?

Keep the distinction between local chemical accuracy and runtime-derived
accuracy explicit.

## 3. Benchmarks

Route: `/benchmarks`

Use this page to answer:

- How does the result sit inside the benchmark suite?
- Which cases are validated, exploratory, unstable, or failed?
- Which baseline is strongest?
- Which case should not receive more budget yet?

The benchmark story should show comparison quality before implementation detail.

## 4. Hardware Campaign

Route: `/hardware-campaign`

Use this page to answer:

- Has the real runtime path been verified?
- Which hardware result is the best recovered evidence?
- How far is it from chemical accuracy?
- Is the right action to continue, pause, collect, or analyze bias?

The release line is conservative: hardware verification is runtime evidence,
not automatic chemistry validation.

## 5. AI Workspace

Route: `/ai-workspace`

Use this page to answer:

- Which analysis ticket should happen next?
- What is pending, accepted, returned, or blocked?
- Which artifacts ground the request?
- What output should be reviewed by a human?

The default AI role is conservative evidence interpretation. It should explain
boundaries before proposing execution.

## 6. Exploratory Appendix

The appendix is optional and must not promote exploratory research assets into
the validated release path.

QFT / finite-cutoff lattice-QED:

```bash
qcchem exploratory run \
  -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml

qcchem exploratory run \
  -c configs/exploratory/h2_4site_lattice_qed_sparse_dynamics.yaml
```

Boundary: sparse projected physical-sector, Gauss-law, and finite-cutoff audit
evidence only. No continuum chemistry claim.

For sparse exact artifacts, show the report's `Trust Boundary Summary / 可信边界摘要`
and `Chemical Accuracy Frame` before discussing energy values. The expected
reading is:

- `finite_model_exactness`: finite Hamiltonian internal exactness.
- `continuum_chemistry_accuracy`: `not_claimed` unless convergence evidence is
  attached.
- `hardware_accuracy`: `unavailable` unless a real Runtime/shot-based result was
  submitted and collected.
- `pauli_terms_available`: `false` when Pauli materialization was skipped; the
  sidecar should show sparse validation metadata instead of a fake Pauli
  Hamiltonian.

Optional QFT benchmark appendix:

```bash
qcchem benchmark run -c benchmarks/field_model_qft_smoke_v2.yaml
qcchem benchmark run -c benchmarks/field_model_qft_cutoff_grid_convergence_v1.yaml
qcchem benchmark run -c benchmarks/field_model_qft_dynamics_resource_v1.yaml
```

These suites are exploratory finite-model/resource evidence. They should not be
used as a continuum chemistry validation slide.

LR-ACE:

```bash
qcchem exploratory run -c configs/exploratory/h2_lr_ace.yaml
qcchem exploratory run -c configs/exploratory/lih_active_lr_ace.yaml
```

Boundary: local exact-baseline gates and runtime probes are exploratory algorithm
evidence, not publication-grade method validation.

TC-QSCI:

```bash
qcchem exploratory run -c configs/exploratory/h2_tc_qsci.yaml
qcchem exploratory run -c configs/exploratory/lih_active_tc_qsci.yaml
```

Boundary: TC-kicked sampling and determinant subspace diagonalization remain
isolated exploratory evidence.

## Curated Artifacts

The release-grade artifact set is:

- `artifacts/h2/result.json`
- `artifacts/lih_auto_compressed_nevpt2/result.json`
- `artifacts/lih_active_exact_compressed_cholesky/result.json`
- `artifacts/benchmark_suite_v1/benchmark_result.json`
- `artifacts/mini_comparison_study/study_result.json`
- `artifacts/h2_short_scan/scan_result.json`
- `artifacts/hardware_calibration_suite_v1/hardware_calibration_summary.json`
- `examples/ai_workspace/tickets/analysis_h2_campaign.json`

Generated local demo outputs should go under a separate output directory and
should not overwrite curated artifacts during testing.

## Release Language

Use the same vocabulary across README, reports, workbench, AI tickets, and
handoff notes:

- `best evidence`
- `trust tier`
- `baseline strength`
- `chemical accuracy status`
- `runtime evidence status`
- `recommended next action`
- `hardware verification boundary`
- `exploratory boundary`
- `release audit`
