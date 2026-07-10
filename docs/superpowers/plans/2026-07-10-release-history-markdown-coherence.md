# Release-History Markdown Coherence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject downloaded release-history Markdown handoffs whose core reviewer-facing values diverge from the verified JSON summary.

**Architecture:** Extend the existing Markdown verifier with a small top-level-block parser. Compare exact scalar fields and the stable first-failure prefix against the parsed JSON, while allowing content after `## Status Counts` to carry reviewer notes.

**Tech Stack:** Python 3.10+, pytest, JSON release artifacts, Trust-First release CLI.

## Global Constraints

- Keep `qcchem.release_history_summary.v0.1-alpha` and the Markdown generator unchanged.
- JSON remains authoritative; Markdown is a checked reviewer-facing projection.
- Reject missing, duplicate, and divergent core Markdown fields.
- Permit appended reviewer notes outside the generated top-level block.
- Do not validate per-run Markdown rows or browser evidence in this increment.

---

### Task 1: Add failing Markdown coherence contract tests

**Files:**
- Modify: `tests/integration/test_release_audit_workflow_v23.py:750-1080`

**Interfaces:**
- Consumes: `_write_downloaded_release_diagnostics_artifact`,
  `_refresh_diagnostics_manifest_file_record`, and `release verify-artifacts`.
- Produces: expected `markdown_core_validation` report metadata and named
  Markdown semantic failures.

- [ ] **Step 1: Assert nominal Markdown validation**

Add:

```python
assert history_handoff["markdown_core_validation"] == "verified"
```

to `test_release_verify_artifacts_cli_accepts_downloaded_diagnostics`.

- [ ] **Step 2: Add Markdown tamper cases**

Create a parameterized test that mutates the copied
`release_history_summary.md` without refreshing its manifest record:

```python
[
    ("status", "- status: `failed`", "release_history_markdown_core_field_mismatch"),
    ("recommended_action", "- recommended_action: `collect_release_evidence`", "release_history_markdown_core_field_mismatch"),
    ("first_failure", "- first_failure: `label=current spurious`", "release_history_markdown_core_field_mismatch"),
]
```

Assert exit code `2`, expected semantic reason, and
`diagnostics_manifest_sha256_mismatch`.

- [ ] **Step 3: Add semantic-only and note compatibility tests**

Replace the action line, refresh the Markdown manifest record, and assert a
semantic failure without a digest mismatch. In a separate test append
`\nReviewer note: retained evidence manually reviewed.\n`, refresh the record,
and assert exit code `0` with `markdown_core_validation == "verified"`.

- [ ] **Step 4: Confirm RED**

Run:

```bash
python -m pytest tests/integration/test_release_audit_workflow_v23.py -k "markdown_core or accepts_downloaded_diagnostics" -q
```

Expected: new report assertion and semantic failure assertions fail because the
current verifier only checks heading and summary-file reference.

### Task 2: Parse and verify the generated Markdown top block

**Files:**
- Modify: `qcchem/workflow/release_status.py:790-970`

**Interfaces:**
- Consumes: parsed `summary: dict[str, object]`, Markdown text, and summary path.
- Produces: `_verify_release_history_markdown(..., summary=...)` and
  `entry["markdown_core_validation"]`.

- [ ] **Step 1: Pass readable JSON to the Markdown verifier**

Change the readable-summary call to:

```python
_verify_release_history_markdown(
    markdown_path,
    summary_path=summary_path,
    summary=summary,
    entry=entry,
    failures=failures,
)
```

For unreadable JSON, call it without a summary and set
`markdown_core_validation` to `not_checked` after basic file/heading/reference
checks.

- [ ] **Step 2: Add field parser and expected-value renderers**

Split Markdown at `\n## Status Counts` and parse lines matching
`- <field>: \`<value>\``. Require exactly one line for each core field:

```python
(
    ("schema_version", str(summary.get("schema_version"))),
    ("status", str(summary.get("status"))),
    ("recommended_action", str(summary.get("recommended_action"))),
    ("run_count", str(summary.get("run_count"))),
    ("passed_runs", str(summary.get("passed_run_count"))),
    ("failed_runs", str(summary.get("failed_run_count"))),
    ("incomplete_runs", str(summary.get("incomplete_run_count"))),
)
```

Render `first_failure` as `none` or its stable
`label=<label> <reason> path=<path>` prefix. Do not compare its optional detail
suffix because JSON already verifies the full nested failure object.

- [ ] **Step 3: Record named core-field failures**

For missing/duplicate entries append
`release_history_markdown_core_field_invalid` with `field` and count. For a
different value append `release_history_markdown_core_field_mismatch` with
`field`, expected, and actual. Set `markdown_core_validation` to `verified` or
`inconsistent` after all checks.

- [ ] **Step 4: Confirm GREEN**

Rerun the Task 1 command. Expected: all nominal, tampered, refreshed-digest,
and appended-note cases pass.

### Task 3: Document, validate, and publish

**Files:**
- Modify: `README.md:155-175`
- Modify: `docs/release_audit.md:310-335`
- Modify: `docs/user_manual.md:724-745`

- [ ] **Step 1: Document Markdown projection verification**

State that core handoff values are checked against the verified JSON while
reviewer notes remain allowed; this is separate from manual real-browser review.

- [ ] **Step 2: Run regressions**

```bash
git diff --check
python -m pytest tests/integration/test_release_audit_workflow_v23.py -q
python -m pytest tests/unit/test_release_audit_v23.py -q
python -m qcchem.cli.main release audit -c configs/release/trust_first_audit.yaml -o /tmp/qcchem-history-markdown-audit
python -m qcchem.cli.main workbench smoke --docs docs/workbench.md
python -m pytest tests -q
```

Expected: tests pass, release audit reports `86 passed, 0 failed`, and
Workbench smoke reports six routes and fourteen pages passed.

- [ ] **Step 3: Review and publish**

Run `git diff --check`, review the staged diff, then commit:

```bash
git commit -m "feat: verify release history markdown"
```

Push `master` and wait for the Python 3.10/3.11/3.12 GitHub Actions matrix.
