# Release-History Markdown Run Coherence Design

## Overview

The retained-run rows in `release_history_summary.md` are compact reviewer
summaries of the JSON `runs` list. Top-level handoff fields are now checked, but
a modified row can still misstate an individual run's release outcome,
artifact-verification outcome, or Workbench outcome after its manifest digest is
refreshed.

## Requirements

- MUST validate each retained Markdown run row's label, `status`,
  `verification`, and `workbench` values against the corresponding JSON run.
- MUST reject missing, duplicate, extra, or divergent conclusion rows with named
  downloaded-artifact verification failures.
- MUST preserve compatibility for optional per-run detail fields and reviewer
  notes outside `## Retained Runs`.
- MUST not change JSON schemas, Markdown generation, release policy, or manual
  browser-review boundaries.

## Design

The verifier will isolate the text between `## Retained Runs` and `## Review
Notes`. It will parse one generated-row prefix per JSON run using the stable
``- `<label>`: status=`...`; verification=`...`; workbench=`...`;`` shape. It
will compare only these four conclusion fields. The verifier does not parse the
remaining detailed columns, which remain informative projections backed by the
JSON and referenced evidence files.

The report adds `markdown_runs_validation` with `verified`, `inconsistent`, or
`not_checked`. Invalid or duplicate row prefixes fail with
`release_history_markdown_run_invalid`; divergent values fail with
`release_history_markdown_run_mismatch` and identify the label and field.

## Validation

- Assert nominal run-row validation is `verified`.
- Tamper `status`, `verification`, and `workbench` independently and assert
  semantic plus digest failures.
- Refresh the Markdown digest for one mutation and assert semantic rejection.
- Append a reviewer note after `## Review Notes` and assert acceptance.
- Run release integration/unit suites, release audit, Workbench smoke, full
  tests, and GitHub Actions before publication.

## Scope Boundaries

- No exact full-row or full-document comparison.
- No parser for matrix counts, baselines, AI fields, or free-text failure detail.
- No retained evidence mutation or browser automation.
