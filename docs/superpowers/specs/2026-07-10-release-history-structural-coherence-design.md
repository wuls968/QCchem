# Release-History Structural Coherence Design

## Overview

The downloaded-diagnostics verifier now binds the retained `current` run to its
copied evidence and validates AI provenance maps. It still trusts the remaining
top-level release-history counters and status maps without recomputing them
from the retained `runs` list. A malformed summary can therefore declare an
inaccurate run count, outcome count, or matrix/verifier/Workbench status map
while retaining a readable schema and a valid current run.

## Requirements

- MUST recompute the release-history summary status from the retained run list.
- MUST require `run_count` to equal the number of retained run records.
- MUST recompute `passed_run_count`, `failed_run_count`, and
  `incomplete_run_count` when those outcome counters are declared.
- MUST recompute `run_status_counts`, `matrix_delta_status_counts`,
  `release_artifact_verification_status_counts`, and
  `workbench_smoke_status_counts` when the complete map group is declared.
- MUST reject partial declaration of an outcome-counter group or status-map
  group because it is ambiguous, not legacy.
- MUST preserve compatibility for historical summaries that omit an entire
  additive group, reporting that group as `legacy_not_available` rather than
  failing solely for absence.
- MUST not attempt to reconstruct `skipped_non_directory_count`, filesystem
  ordering, or browser-console evidence from downloaded artifacts.
- MUST not alter release-history schema version or promotion/gating policy.

## Design

`qcchem.workflow.release_status._verify_release_history_coherence` already
rejects malformed `runs` and identifies `current`. This change adds a compact
structural validator operating on the same validated run list. It derives the
overall history status exactly as `qcchem.cli.main._release_history_summary`:
`empty` for no runs, `passed` if all runs pass, `failed` if any run fails, and
`incomplete` otherwise.

The validator compares `run_count` with `len(runs)`. It treats the three outcome
counters as one compatibility group: all present means recompute and compare;
all absent means `legacy_not_available`; any subset is a failure. It treats the
four non-AI status maps the same way. Each map uses the generator's existing
rule: use `run[key]["status"]` for nested evidence dictionaries, otherwise use
the direct run value, falling back to `not_available`.

The verifier report adds `structural_validation` plus compact expected/actual
metadata only on divergence. It does not duplicate per-run payloads. AI maps
remain governed by the existing dedicated validator, so the two checks do not
change the meaning of `not_available` AI provenance.

## Error Handling

- An inaccurate total status produces `release_history_summary_status_mismatch`.
- An inaccurate run count produces `release_history_summary_run_count_mismatch`.
- Partial outcome counters produce
  `release_history_summary_outcome_counts_incomplete`; mismatched values produce
  `release_history_summary_outcome_counts_mismatch`.
- Partial status maps produce
  `release_history_summary_status_maps_incomplete`; individual mismatches use
  `release_history_summary_status_map_mismatch` with the affected field.
- Omitted complete groups record `legacy_not_available` and remain readable.

## Validation

- Extend downloaded-diagnostics tests for a coherent current release-history
  report with `structural_validation: verified`.
- Add tamper cases for total status, run count, outcome count, each status-map
  group, and partial groups; assert named semantic failures even when the
  manifest digest also fails.
- Add legacy cases that refresh the fixture manifest and demonstrate missing
  complete groups do not fail verification.
- Run focused tests, release-audit integration/unit suites, default tests,
  release audit, Workbench smoke, and GitHub Actions before publication.

## Scope Boundaries

- No changes to the release-history generator or output schema.
- No browser server, Playwright dependency, screenshot artifact, or manual
  browser checklist automation in this increment.
- No scientific result or runtime submission policy changes.
