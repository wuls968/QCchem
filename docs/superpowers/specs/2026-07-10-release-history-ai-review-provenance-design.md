# Release-History AI Review Provenance Design

## Overview

Retained post-CI release-history runs currently preserve verifier, matrix, and
Workbench evidence, but omit the already-normalized AI delivery review summary
from each `release_evidence_summary.json`. This design makes that frozen,
informational review context visible in machine-readable history summaries,
reviewer-facing Markdown, and Workbench retained-run drilldowns.

## Requirements

- MUST preserve a compact normalized `ai_workspace_delivery` object for every
  readable retained run.
- MUST use `normalize_ai_delivery_review_summary` as the one validation and
  normalization boundary.
- MUST expose per-run `status`, `source_status`, `review_event_count`,
  `review_provenance_log`, and `latest_review_event` when validated context is
  available.
- MUST make malformed, missing, or non-object AI context `not_available` with
  `release_gate: informational_only` without changing retained-run or
  release-history pass/fail status.
- MUST add top-level status and source-status count maps without summing review
  events across runs, because history snapshots can repeat the same event.
- MUST surface the compact fields in CLI text, exported Markdown, Workbench
  smoke JSON, and the Overview retained-run table.
- MUST retain `qcchem.release_history_summary.v0.1-alpha`; the new fields are
  additive.

## Design

`qcchem.cli.main._release_history_run_summary` reads the retained evidence
summary and feeds `payload["ai_workspace_delivery"]` through the shared
normalizer. The resulting compact object is embedded as
`run["ai_workspace_delivery"]`. The existing history count helper adds one
map for AI summary status and one map for `source_status`; missing source status
is reported as `not_available`.

CLI stdout and the Markdown export show the per-run AI status, source status,
event count, and provenance path. The Markdown also lists both aggregate count
maps. These fields describe evidence provenance only; they are not consulted by
strict exit status or `first_failure` selection.

Workbench uses the generated history JSON as its source of truth. Its smoke
summary reduces each retained run to the same bounded fields and passes the two
aggregate maps through. Overview renders the per-run status, source, event
count, and provenance path alongside the existing verifier, smoke, and matrix
fields.

## Error Handling

- Missing, malformed, or structurally inconsistent AI context normalizes to
  `{status: not_available, release_gate: informational_only}`.
- The fallback does not add an entry to release-history failures, does not
  modify a retained run's `status`, and does not alter `--strict` behavior for
  an otherwise passed history.
- Existing retained summaries without the new additive keys remain readable by
  Workbench and render their AI review fields as `not_available`.

## Validation

- Extend the retained-history integration test with a verified AI review
  fixture and assert JSON, CLI, and Markdown output.
- Add a malformed retained AI review fixture and assert that the run and
  history stay `passed` while its AI status is `not_available`.
- Extend Workbench smoke and Overview fixtures to assert the bounded fields and
  aggregate count maps.
- Run the focused integration tests, release-audit unit tests, release audit,
  Workbench smoke, and the default suite before publishing.

## Scope Boundaries

- No raw AI ticket payloads, queues, or unbounded provenance logs are copied
  into release history.
- No release-gate policy, schema version, external download behavior, or AI
  provider integration changes.
