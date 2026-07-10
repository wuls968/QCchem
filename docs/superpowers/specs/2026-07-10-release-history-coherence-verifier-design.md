# Release-History Coherence Verifier Design

## Overview

Downloaded release diagnostics already verify individual file digests, schemas,
and passed statuses. The retained `release_history_summary.json` is not yet
checked against its copied `release_history/current/release_evidence_summary.json`.
This leaves a cross-artifact coherence gap: a structurally valid history summary
can describe a different current release evidence payload, or can carry
inconsistent AI review aggregate counts.

## Requirements

- MUST verify that a readable retained history summary has a `current` run when
  its current release evidence file is present.
- MUST verify that the current run's release status matches the copied current
  release evidence status.
- MUST compare current-run AI delivery review context only after both values
  pass `normalize_ai_delivery_review_summary`.
- MUST recompute AI delivery review status and source-status count maps for
  summaries that declare those additive fields.
- MUST report declared-but-inconsistent provenance as a verifier failure.
- MUST accept `not_available` AI context as an informational state when both
  current evidence and retained history normalize to that state.
- MUST remain compatible with retained summaries that predate the additive AI
  fields; those summaries receive an explicit legacy validation status rather
  than a failure solely for absent fields.
- MUST not change the release-history schema version or make AI review
  availability a release eligibility requirement.

## Design

`qcchem.workflow.release_status._verify_release_history_handoff` will validate
the summary and copied current evidence together after their existing
independent schema/status checks. A small internal helper will read the `runs`
array, locate the single `label == "current"` entry, and emit a precise failure
when it is missing, duplicated, or not an object.

For a valid current run, the verifier compares `current_run["status"]` with the
copied evidence status. It passes both AI objects through the shared normalizer
and compares normalized output; malformed values therefore become the same
explicit `not_available` fallback rather than a synthetic release failure.

When either AI aggregate map appears in the summary, the verifier recomputes it
from all retained run snapshots. It requires both maps to be present together,
to contain non-negative integer values, and to exactly match the deterministic
recomputed maps. The source map treats a missing or blank source as
`not_available`, matching the history CLI contract. A summary with neither map
is marked `legacy_not_available` and remains readable for historical reviews.

The verifier records compact current-run and AI validation fields in each
`release_history_handoffs` report entry. The existing top-level pass/fail policy
is unchanged: only coherence divergence becomes a failure; an unavailable AI
review snapshot does not.

## Error Handling

- Missing, non-list, or malformed `runs` produces an explicit summary-contract
  failure instead of a traceback.
- Zero or multiple `current` labels produce distinct failures.
- A declared AI map with invalid counts or mismatch produces a precise failure
  containing the expected and actual maps.
- Older summaries that omit both AI maps do not fail merely due to age.

## Validation

- Extend downloaded-diagnostics integration tests for the verified current run
  and the normalized AI snapshot.
- Add corruption cases for a missing current run, status divergence, normalized
  AI divergence, and aggregate-map divergence.
- Add a legacy-summary case proving that omitted additive AI fields remain
  readable.
- Run focused integration tests, release-audit unit tests, the default suite,
  release audit, Workbench smoke, and the GitHub Actions matrix before publish.

## Scope Boundaries

- No new remote trust service, signature scheme, or diagnostics-manifest format.
- No raw AI ticket payloads or provenance-log contents are copied into the
  verifier report.
- No change to scientific claims, artifact acceptance policy, or runtime
  submission behavior.
