# Release-History Markdown Coherence Design

## Overview

`release_history_summary.md` is the reviewer-facing handoff generated from the
machine-readable JSON summary. Downloaded-artifact validation currently checks
only its heading and reference to `release_history_summary.json`. A tampered
Markdown handoff can therefore display an incorrect status, action, count, or
first-failure summary while the verified JSON remains correct and the manifest
is refreshed to match the altered file.

## Requirements

- MUST verify the generated handoff's top-level schema, status, recommended
  action, run counts, and first-failure summary against the parsed JSON summary.
- MUST reject missing, duplicated, or divergent core top-level Markdown fields
  with named downloaded-artifact verification failures.
- MUST allow extra reviewer notes after the generated top-level block.
- MUST keep JSON as the authoritative machine-readable source and leave schema
  versions, generator output, and release promotion policy unchanged.
- MUST not claim that this text-level check replaces the manual real-browser
  Workbench checklist.

## Design

Extend `_verify_release_history_markdown` to receive the parsed summary once it
is readable. It will isolate the generated top-level block before `## Status
Counts`, parse each required `- field: \`value\`` entry exactly once, and compare
the values with deterministic local renderers for the JSON summary. Required
fields are `schema_version`, `status`, `recommended_action`, `run_count`,
`passed_runs`, `failed_runs`, `incomplete_runs`, and `first_failure`.

The check does not compare the full document. This preserves the reviewer note
section and avoids duplicating the complete Markdown generator in the verifier.
`first_failure` compares its stable label/reason/path prefix, while JSON
continues to validate the full nested failure payload. The handoff report adds
`markdown_core_validation: verified`, `inconsistent`, or `not_checked`.

## Error Handling

- Missing or duplicated core field lines produce
  `release_history_markdown_core_field_invalid` with the field name.
- A divergent displayed value produces
  `release_history_markdown_core_field_mismatch` with expected and actual
  values.
- Unreadable JSON keeps the existing heading/reference checks and reports
  `markdown_core_validation: not_checked` because no authoritative summary is
  available for comparison.

## Validation

- Assert `markdown_core_validation: verified` for the nominal downloaded
  diagnostics fixture.
- Tamper Markdown status, action, and first-failure text without refreshing its
  manifest record; assert the semantic failure and digest failure.
- Refresh the Markdown manifest record after an action-text mutation and prove
  semantic validation still rejects the handoff.
- Add an appended reviewer note to a valid handoff and prove it remains
  accepted after refreshing the manifest record.
- Run focused tests, release-audit integration/unit suites, release audit,
  Workbench smoke, the full suite, and the Python 3.10/3.11/3.12 CI matrix.

## Scope Boundaries

- No full-document byte comparison and no generated Markdown rewrite.
- No per-run Markdown field parser in this increment.
- No browser automation, external fetch, or retained-history mutation.
