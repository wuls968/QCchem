# VQE and scan checkpoints

## Goal

Observe workflow cancellation and deadlines at VQE evaluation and scan point
boundaries, retain expensive completed work, and resume without overwriting the
original artifacts or resetting the optimizer budget.

## Requirements and design

- Explicit `run/scan run --resume-from OLD_ROOT -o NEW_ROOT` writes a fresh bundle.
- Atomic, integrity-checked checkpoints bind inputs, source, dependencies,
  Hamiltonian, circuit, seeds, optimizer options, and evaluation evidence.
- VQE reconstructs SciPy progress by replaying stored objective values from the
  original initial point. Every requested parameter vector must match exactly
  before any new backend call. This is checked replay, not serialized SciPy state.
- Restore the local sampler evaluation counter; retain original shots, seeds,
  trajectory indices, and total optimization budget. Unseeded shot sampling and
  remote/runtime submission are excluded from recovery in this version.
- Preserve original Hamiltonian coefficients. Rebuilt SCF coefficients must have
  the same Pauli basis and an L1 difference no greater than 1e-12 Hartree; report
  that bound in provenance and use the original operator in all downstream work.
- Save a pending evaluation before calling the backend and commit its evidence
  before checking cancellation. A killed local evaluation may be recomputed with
  its original seed; completed evaluations are never resampled.
- Scans commit completed point summaries, continuity records, and file manifests.
  Resume reuses those bundles and their predictor history. An interrupted VQE
  point uses its own checkpoint; incomplete exact points restart locally.
- Cooperating run/scan processes share stable OS locks. Recovery checks source
  manifests before and after use. No provider cancellation or PID signalling.
- Built-in workflow `run_config` and `scan` steps pass the existing control callback
  and automatically find the prior partial bundle on explicitly approved retry
  when the step uses its default artifact directory. Loop retries remain whole
  loop retries and do not gain inner resume semantics.

## Validation

Compare uninterrupted and resumed VQE parameter/energy/seed trajectories for
deterministic and seeded shot sampling; reject changed inputs, circuit,
implementation, corrupted checkpoints, replay divergence, and concurrent writes.
Exercise cooperative cancellation and process death, scan point reuse and
predictor continuity, real H2 workflow recovery, CLI behavior, the normal test
suite, static checks, and an isolated wheel smoke test.

## Limits and open questions

Native SCF, eigensolver, backend evaluation, and provider calls are not forcibly
interrupted. A running call returns before cooperative cancellation is observed.
Cross-version/source checkpoint migration and CUDA-Q recovery are deferred. No
dependency installation, commit, push, or cleanup is part of this change.
