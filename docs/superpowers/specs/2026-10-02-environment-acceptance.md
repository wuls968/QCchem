# QCchem environment acceptance

## Goal

Validate the upgraded chemistry and recovery paths against existing interpreters,
native CUDA-Q/MKL-Q installations, and retrievable IBM Runtime evidence. Record
executed checks separately from unavailable platforms and provider submissions.

## Requirements

- Reuse existing environments; do not install or upgrade dependencies.
- Keep source checkouts, original computation bundles, credentials, and saved
  checkpoint-compatible wheels unchanged.
- Run real H2 simulator estimates and compare with the physical exact baseline;
  CPU, experimental Metal, NVIDIA GPU, and QPU evidence remain separate.
- Query existing Runtime jobs without submitting or charging for a new job.
  Recollection writes only into a new copy of an original artifact.
- Check cross-platform CI against upstream support. PySCF requires WSL on Windows;
  a Windows control-layer test must not claim native Windows chemistry support.
- Fix demonstrated compatibility failures with focused regression coverage.

## Design

Preserve an environment/source receipt for each interpreter. Use bounded native
integration checks and unique test/output directories. Package any compatibility
fix in an isolated wheel and validate that installed package as well as the source.
CI uses available platform runners and retains diagnostic artifacts on failure.

Native sampling exposed a missing-uncertainty fallback that used unitless
`1/sqrt(shots)` as an energy standard deviation. Retain missing error bars as
`null`; empirical uncertainty is available only from repeated evaluations.
Chemical accuracy uses the post-optimization sampled mean, consistently with
benchmark error. The optimization trajectory energy remains unchanged.

Windows mandatory locking blocks readers of byte zero. Reserve this existing
exclusion byte as whitespace and read owner JSON from byte one on Windows;
keep the same lock range so older owners still exclude new writers.

Real Python 3.12/SciPy 1.13 process cancellation exposed a Fortran COBYLA/f2py
abort. Capture callback exceptions only on legacy COBYLA, stop further estimates,
then re-raise the original exception after native unwinding. Never commit the
unwind placeholder values or a completed outcome. Keep existing dependencies.

## Validation

Run target-specific H2 checks, independent exact-energy comparisons, process
recovery checks, related unit tests, Ruff, and diff review. Expand to the default
suite when code changes justify it. Retain failed attempts and original artifacts.

## Open gates

No current Linux/WSL/NVIDIA GPU execution has been verified. Lab SSH closed the
initial read-only connection. GPUHome uses credentials held by KSH; this round
does not extract them. Real QPU resubmission still requires the engine's explicit
budget confirmation. Provider read-back may be blocked by account/network state.
