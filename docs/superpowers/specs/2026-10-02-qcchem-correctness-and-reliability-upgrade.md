# Spec: QCchem correctness and reliability upgrade

## Overview

Resolve the nine findings reproduced by the 2026-10-02 audit of checkout
`616b8e5`. Preserve existing results and use the installed scientific environment.
Changes are confined to this checkout; the separate QCIR branch and dirty main
checkout are outside this implementation.

## Requirements

- Molecular exact solvers, excited-state spectra, and exact baselines must use
  the configured particle and total-spin sector, including reduced mappings.
- Exact diagonalization must handle requests near the matrix dimension and
  reject allocations exceeding explicit resource limits before materialization.
- Workflow identifiers and plugin output paths must stay inside their output
  root, including symlink and direct Python API cases.
- Runtime collection must use the same energy constants as local execution.
- Invalid configurations must fail before any existing output is changed.
  Explicit overwrite must retain the previous bundle if the new run fails.
- Workflow deadlines must be checked around steps, retries, and loops; a timed
  out workflow must never be accepted. Document cooperative interruption limits.
- Workbench pages must share a real selected artifact and must not substitute
  demo geometry or orbital energies for missing scientific data.
- Molecular viewers must initialize after route changes and show load failures.
- Add environment diagnostics and regression tests without installing tools or
  changing provider credentials, core dependencies, or existing result bundles.

## Design

Use a shared exact-sector contract built from mapped number and spin operators.
Retain eigenvectors in the original mapped space for property evaluation. Apply
the contract to molecular electrons while leaving lattice-field spectra in their
own Hilbert space. Keep explicit memory/qubit guards for dense and sparse paths.

Centralize run validation and energy composition. Use sibling staging directories
for overwrite runs; publish only completed bundles and retain old bundles under
unique backup names. Failed staging outputs remain inspectable. Constrain output
paths at both parsing and execution boundaries.

Use monotonic deadline checks during custom workflows, persist failure evidence,
and ensure aborts override permissive acceptance settings. This release uses
cooperative deadlines; it does not claim to terminate arbitrary plugin code.

Build Workbench geometry and orbital views from result/resolved-configuration
artifacts, rank eligible artifacts deterministically, and use an explicit
unavailable state when required data is absent. Observe viewer DOM mounts and
report rendering errors visibly.

## Validation

- Independent FCI checks for charged/open-shell molecules; particle/spin checks
  on ground and excited states; Jordan-Wigner, Bravyi-Kitaev, parity, and tapering.
- Small matrix full-spectrum and resource rejection checks.
- Absolute/traversal/symlink workflow-output regression tests.
- Local versus collected-runtime energy reconciliation with external constants.
- Invalid configuration and failed-overwrite preservation tests.
- Deadline tests covering long steps, retries, loops, and optional steps.
- Artifact-backed Workbench component checks and an actual browser render.
- Relevant module tests, lint, full normal test suite, CLI and packaging smoke.

## Open Questions

- Hardware/provider acceptance remains dependent on authorized remote jobs.
- Cross-process resume/cancel and QCIR integration require separate scientific
  contracts and are not claimed by this reliability upgrade.
