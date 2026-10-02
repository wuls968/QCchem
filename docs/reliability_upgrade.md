# Correctness and reliability upgrade

This upgrade addresses the 2026-10-02 audit of the current main-line checkout.
It does not incorporate the separate QCIR development branch.

## Exact molecular results

Molecular exact solvers, exact baselines, and excited-state spectra now select
both `(N_alpha, N_beta)` and total spin `S(S+1)`, with `S=(multiplicity-1)/2`.
Mapped number/spin operators use the same parity and Z2 reduction as the
Hamiltonian. Unrestricted orbital overlaps are retained when constructing spin
operators. Cavity spectra constrain electrons while retaining photon states;
lattice-field models retain their existing field-specific treatment.

`exact_baseline.sector` records particle counts, multiplicity, spin, and the
available dimension. A Z2-tapered spectrum belongs to that selected Z2 sector;
it is not the union of all symmetry sectors. Unavailable requested states are
reported explicitly. Old result bundles are not recomputed automatically.
Charged/open-shell results generated before this fix should be rerun before
using their previous exact-validation claims.

The shared spectrum API defaults to 16 qubits and 512 MiB for matrix/workspace
estimates. It rejects large allocations before constructing a matrix and uses a
bounded dense path for requests near the full dimension. These are conservative
estimates, not an operating-system memory reservation. Reduce the active space
if a guard rejects a calculation.

## Configuration and output safety

Unknown keys in the main execution sections, incorrect boolean/integer types,
non-finite numeric values, unsupported execution kinds, invalid shots/precision,
noise probabilities, and negative state indices are rejected before execution.
Supported coordinate units are `angstrom` and `bohr`. Plugin-specific dictionaries
and advanced method options retain their existing parser contracts.

For a nonempty run output directory, `run.overwrite: true` stages the new run in
`.NAME.pending-<id>` beside the existing directory. A failed run preserves the old
directory and leaves failed staging artifacts for diagnosis. A completed run
moves the previous bundle to `NAME.backup-<id>` before publishing the new bundle.
These backups and failed staging artifacts consume additional disk space and are
not deleted automatically. Aggregate workflow overwrites also retain backups.
Use a fresh output directory to keep all run identities separate.

JSON results use a temporary sibling file, flush/fsync, and atomic replacement.
Runtime collection includes all four energy constants used by local execution:
electronic reduction, nuclear repulsion, external-charge nuclear interaction,
and boundary embedding. Optional collected exports stay inside their bundle.

## Custom workflows

Step IDs accept 1-128 letters, digits, underscores, or hyphens, beginning with a
letter or digit. Absolute IDs, traversal, separators, and symlinked output paths
are rejected. `context.output_path()` constrains plugin output paths to the step
folder. Installed Python plugins remain trusted code, not sandboxed programs.

`max_wall_time_seconds` uses a monotonic cooperative deadline around validation,
execution, retries, planning, and loop iterations. An overrun always produces a
failed, unaccepted workflow, including optional steps and permissive acceptance
settings. It does not forcibly interrupt a running external program or arbitrary
plugin function. Plugins can check `context.metadata['deadline_monotonic']` while
working. Each finished/failed step persists `step_outputs/ID/step_result.json`.
Step result files alone are not sufficient for recovery.
The follow-up recovery upgrade adds an atomic `workflow_checkpoint.json`, an
OS-held execution lock, and `workflow status/cancel/resume`. Completed steps are
reused only after configuration/software/file checks; uncertain or failed steps
require explicit `--retry-step` flags. Original partial outputs and previous
result sidecars are retained. Cancellation is cooperative and session-bound.
See [Custom workflows](custom_workflows.md#recovery-and-cancellation) for the
commands, whole-step recovery limits, and runtime/provider boundary.

## Inner computation recovery

Individual calculations write `run_checkpoint.json`. Core VQE also writes
`vqe_checkpoint.json` before each backend call and after each returned estimate.
Scans write `scan_checkpoint.json` with completed point manifests and variational
continuity records. These files are additive; original inputs/results are retained.

Use a separate, empty destination when recovering:

```bash
python -m qcchem.cli.main run -c configs/h2.yaml -o artifacts/h2-resumed --resume-from artifacts/h2-partial
python -m qcchem.cli.main scan run -c configs/scans/h2_short_scan.yaml -o artifacts/scan-resumed --resume-from artifacts/scan-partial
```

VQE starts SciPy with the original initial point/options and feeds back the saved
objective values. Each requested parameter vector must match its recorded vector
exactly. A mismatch stops recovery before any new estimate. It does not serialize
SciPy's internal state or restart optimization from a new warm guess. Original
budget, logical evaluation indices, energies, uncertainty, shots, and seeds are
retained. The TNC adapter now maps the configured budget to SciPy's `maxfun` option;
other methods keep their existing `maxiter` semantics. SciPy may raise an
undersized COBYLA budget to its initialization minimum, as in ordinary runs.

Recovery supports local `statevector` and `shot_estimator`/`aer_shot_estimator`.
Shot recovery requires `backend.seed`; its evaluation counter is restored so the
first new estimate receives the next original seed. An interrupted local call
without a committed estimate is recomputed with its original seed. A completed
optimizer checkpoint bypasses optimization, while downstream postprocessing and
exports run again. Runtime must be disabled; CUDA-Q and remote/provider recovery
are not supported here. Source, dependency versions, inputs, Hamiltonian, and
circuit must match. Rebuilt SCF coefficients may differ by machine roundoff:
the L1 difference must be at most `1e-12` Hartree, after which the original
checkpoint Hamiltonian is reused for optimization and downstream evidence. The
observed bound is recorded in recovery provenance. Larger differences or changed
Pauli bases reject recovery. Legacy bundles without these checkpoints require a new run.

Scan recovery reuses original completed point directories and their predictor
history. Keep those original bundles: the new aggregate references them rather
than copying or moving scientific data. An interrupted VQE point uses its inner
checkpoint; an incomplete exact/reference point starts over locally. File hashes
and directory membership are verified before and after reuse. Stable adjacent
computation locks exclude cooperating run/scan writers, including overwrite.
Hashes detect accidental changes, not deliberate forgery of untrusted artifacts.

Workflow `run_config`/`scan` plugins pass `context.check_control()` into these
loops. Cancellation and deadlines are observed before a new estimate/point and
after returned evidence is committed. A native SCF, eigensolver, or backend call
already running must return before cancellation is observed. No PID signalling
or provider cancellation is performed. Standalone Ctrl-C returns CLI status 130
and retains partial bundles; machine/process death is recovered from the last
atomic checkpoint. Source changes require a new run, not checkpoint migration.

SciPy versions before 1.16 use Fortran COBYLA. Exceptions crossing its f2py
objective callback can abort CPython in some supported environments. QCchem
captures the first callback failure, performs no further backend estimates, and
re-raises the original exception after the native optimizer returns. Placeholder
callback values used during that unwind are not stored as estimates or accepted
as an optimizer outcome. Newer Python COBYLA and other optimizer paths keep
their usual exception propagation. Optional COBYQA requires SciPy 1.14 or newer.

## Workbench

Overview, structure, reduction, mapping, runtime, confidence, and method pages
select real artifact data consistently. Selection prefers complete evidence and
provenance, then recency; historical hard-coded artifact names have no priority.
Geometry comes from the result or its resolved configuration. Orbital ladders
use stored SCF orbital energies, with explicit Hartree-to-eV conversion. Missing
geometry, orbital energies, or hardware estimates show an unavailable state;
simulator errors are never substituted for hardware errors.
Studies and Scans select real aggregates from the configured artifact root and
offer an explicit Demo choice. Scan checkpoints expose committed points as
incomplete evidence. Missing energies/errors remain unavailable; charts mark
the lowest sampled energy without claiming convergence. Bond-distance scans
record their parameter unit in the final result and checkpoint.
Benchmark/hardware fallbacks remain explicitly labeled `Demo data`.

Workflow Studio offers session-bound cooperative cancellation and reviewed
background recovery over the existing workflow engine. The review shares the
engine's read-only preflight and records the checkpoint digest and known input
manifest. The worker rechecks both before executing. Local request checks and
server-owned catalog paths bound these actions to a local workstation. See
[Workbench workflow controls](workbench.md#workflow-controls) for the complete
flow and preserved request/log/receipt files.

3Dmol.js 2.5.5 is bundled locally with its license, and viewer mounts are observed
after route changes. No network download is required to render the molecule.
The default ball-and-stick style keeps atoms visible even without inferred bonds;
linear molecules along the viewing axis receive a side view.
The pinned distribution came from the [3Dmol project](https://github.com/3dmol/3Dmol.js)
and its npm package. Distribution SHA-256:
`f7cc78921ae72e7623e89cdd111434f58c2efddd2ffda1cd212644b406fb8016`.

## Environment diagnostics

Native CUDA-Q `ObserveResult` may not report an energy uncertainty. Such sampled
estimates retain `null` uncertainty rather than substituting `1/sqrt(shots)`;
Hamiltonian coefficients and measurement covariances determine energy error bars.
Repeated post-optimization samples provide an empirical mean standard error.
One sample without a backend error bar has no standard error or confidence
interval. Stored intervals use the existing 95% normal approximation; small
repeat counts do not establish convergence or reliable coverage. Chemical
accuracy and benchmark error both compare the post-optimization sample mean
with the exact baseline. The optimization-stage energy remains in `energy`.

Process locks reserve the first byte for exclusion. Owner metadata starts at the
next byte so Windows mandatory locks do not prevent status readers from seeing
an active owner. Checkpoint and control helpers import independently of Qiskit,
PySCF, and Dash; public configuration loaders are resolved on demand. Native CI
covers macOS/Linux science and process recovery, with
a separate Windows control test. PySCF chemistry on Windows requires
[WSL](https://pyscf.org/user/install.html). Configuration of CI is not evidence
that its remote jobs have run.

Use the interpreter that owns the scientific dependencies:

```bash
/opt/anaconda3/envs/qiskit/bin/python -m qcchem.cli.main doctor --json
```

`qcchem doctor` reports the imported source, installed distribution version,
Python executable, dependency versions/minimums, optional features, thread
settings, and separate shell/interpreter Conda environments. It does not install
packages, inspect credentials, contact providers, or certify GPU/hardware jobs.
A source/installed-version mismatch is reported without modifying the environment.

## Validation commands

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest tests/integration/test_exact_physical_sector.py tests/unit/test_reliability_upgrade.py -q
python -m pytest tests -q -W error::scipy.sparse._base.SparseEfficiencyWarning
ruff check qcchem tests
python -m qcchem.cli.main doctor --json
python -m qcchem.cli.main workbench serve --artifact-root /path/to/new/run/artifacts
```

Independent PySCF FCI tests cover H2+, singlet H2, and triplet H2 across four
mapping/reduction combinations, including particle and spin checks on every
returned eigenvector. Hardware Runtime collection tests use a provider fixture;
they do not prove a real provider job. Normal tests exclude slow/stress markers.
