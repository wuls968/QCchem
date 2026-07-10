# Release-History Markdown Run Coherence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject reviewer-facing retained-run Markdown rows that disagree with the verified JSON run conclusions.

**Architecture:** Parse only the generated row prefix inside `## Retained Runs`, compare each JSON run's label/status/verification/Workbench status, and preserve all optional row details plus notes after `## Review Notes`.

**Tech Stack:** Python 3.10+, pytest, JSON release artifacts, Trust-First release CLI.

## Global Constraints

- Keep release-history JSON and Markdown generator unchanged.
- Validate only label, `status`, `verification`, and `workbench` for each run.
- Reject missing, duplicate, extra, and divergent conclusion rows.
- Keep optional row details and post-section reviewer notes outside verification scope.

---

### Task 1: Add failing per-run Markdown contract tests

**Files:**
- Modify: `tests/integration/test_release_audit_workflow_v23.py:750-1100`

- [ ] **Step 1: Assert nominal run validation**

Add:

```python
assert history_handoff["markdown_runs_validation"] == "verified"
```

to the nominal downloaded-diagnostics test.

- [ ] **Step 2: Add tampered row cases**

Mutate the `current` row without refreshing the Markdown manifest record:

```python
[
    ("status", "status=`failed`"),
    ("verification", "verification=`failed`"),
    ("workbench", "workbench=`failed`"),
]
```

Assert exit code `2`, `release_history_markdown_run_mismatch`, and
`diagnostics_manifest_sha256_mismatch`.

- [ ] **Step 3: Add semantic-only and note tests**

Refresh the Markdown record after a `verification` mutation and assert semantic
rejection without digest mismatch. Append a reviewer note after `## Review
Notes`, refresh the record, and assert `markdown_runs_validation == "verified"`.

- [ ] **Step 4: Confirm RED**

Run:

```bash
python -m pytest tests/integration/test_release_audit_workflow_v23.py -k "markdown_run or accepts_downloaded_diagnostics" -q
```

Expected: new report and semantic assertions fail before the verifier parses
retained-run rows.

### Task 2: Implement conclusion-row verification

**Files:**
- Modify: `qcchem/workflow/release_status.py:883-1040`

- [ ] **Step 1: Isolate and parse the retained-run section**

Split Markdown between `\n## Retained Runs` and `\n## Review Notes`. For each
line beginning `- \``, parse the label and the prefix values in this order:

```python
status=`...`; verification=`...`; workbench=`...`;
```

- [ ] **Step 2: Compare JSON conclusions**

For every run dict in `summary["runs"]`, require exactly one row with matching
label. Compare `run["status"]`,
`run["release_artifact_verification"]["status"]`, and
`run["workbench_smoke"]["status"]` against parsed values. Fail invalid
row/label cardinality with `release_history_markdown_run_invalid`; fail values
with `release_history_markdown_run_mismatch` including label and field.

- [ ] **Step 3: Publish report state**

Set `entry["markdown_runs_validation"]` to `verified`, `inconsistent`, or
`not_checked` when Markdown or JSON is unavailable.

- [ ] **Step 4: Confirm GREEN**

Rerun Task 1's command. Expected: nominal, digest-tampered,
semantic-only, and note cases pass.

### Task 3: Document, validate, and publish

**Files:**
- Modify: `README.md:160-175`
- Modify: `docs/release_audit.md:315-330`
- Modify: `docs/user_manual.md:730-745`

- [ ] **Step 1: Document retained-run conclusion checks**

Describe that per-run release, verification, and Workbench conclusions in the
generated Markdown are checked against JSON; optional details and reviewer notes
remain informational.

- [ ] **Step 2: Run regressions**

```bash
git diff --check
python -m pytest tests/integration/test_release_audit_workflow_v23.py -q
python -m pytest tests/unit/test_release_audit_v23.py -q
python -m qcchem.cli.main release audit -c configs/release/trust_first_audit.yaml -o /tmp/qcchem-history-run-markdown-audit
python -m qcchem.cli.main workbench smoke --docs docs/workbench.md
python -m pytest tests -q
```

- [ ] **Step 3: Review and publish**

Commit with `git commit -m "feat: verify release history markdown runs"`, push
`master`, and wait for Python 3.10/3.11/3.12 CI.
