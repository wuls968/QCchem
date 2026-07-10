# Release-History Guidance Coherence Design

## Overview

The downloaded-history verifier already validates the retained run list, summary
status, totals, status maps, current evidence, and AI provenance. It still
trusts two core fields that are derived solely from `runs`: the operator-facing
`recommended_action` and `first_failure`. A tampered passed-history summary can
therefore preserve correct counts while showing a misleading next action or a
spurious first failure.

## Requirements

- MUST derive `recommended_action` from the verified summary status using the
  release-history generator's exact mapping.
- MUST derive `first_failure` from the retained run order using the generator's
  existing first non-passed run rule.
- MUST reject a missing or divergent core guidance field with a named downloaded
  artifact verification failure.
- MUST keep the release-history schema version and release promotion policy
  unchanged.
- MUST not reconstruct filesystem-only metadata, browser evidence, or evidence
  internal to a retained run beyond its already archived record.

## Design

Extend `_verify_release_history_structural_coherence` with two small local
reducers mirroring `qcchem.cli.main._release_history_summary`. The action reducer
returns `review_release_history` for `passed`, `collect_release_evidence` for
`empty`, and `inspect_release_history_failures` otherwise. The first-failure
reducer scans retained runs in their archived order, skips passed runs, and
returns the same label, status, reason, path, and original failure payload used
by the history generator.

`recommended_action` and `first_failure` are core release-history fields, not
the additive projections covered by the previous compatibility groups. Their
absence is therefore invalid rather than legacy-compatible. The verifier report
adds compact `guidance_validation` metadata alongside the existing structural
states. A mismatch remains an artifact-verification failure even if the
diagnostics manifest independently reports a digest mismatch.

## Error Handling

- A missing or incorrect action produces
  `release_history_summary_recommended_action_mismatch` with expected and
  actual values.
- A missing or incorrect first failure produces
  `release_history_summary_first_failure_mismatch` with expected and actual
  values.
- Valid current summaries report `guidance_validation: verified`.
- Invalid runs/current labels continue to report the existing invalid coherence
  state; guidance is `not_checked` because no deterministic retained run can be
  selected safely.

## Validation

- Extend the nominal downloaded-diagnostics test with
  `guidance_validation: verified`.
- Parameterize wrong action and spurious first-failure mutations; assert the
  semantic failure and manifest digest failure.
- Refresh the manifest after each mutation in an independent test to prove that
  semantic validation rejects a self-consistent-but-misleading artifact.
- Run focused tests, release-audit integration/unit suites, release audit,
  Workbench smoke, the full test suite, and all three CI Python versions.

## Scope Boundaries

- No schema version bump, generator output change, or changes to retained
  history directories.
- No shared generator extraction in this increment; duplicated reducers remain
  short and intentionally mirror the generator's stable semantics.
- No automated real-browser Workbench coverage.
