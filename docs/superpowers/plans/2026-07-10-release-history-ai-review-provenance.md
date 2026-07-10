# Release-History AI Review Provenance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve normalized, informational AI delivery-review provenance in every retained release-history run and expose it consistently to CLI, Markdown, and Workbench reviewers.

**Architecture:** The release-history CLI will reuse the existing shared AI review normalizer when converting retained `release_evidence_summary.json` files into compact run records. It will add additive aggregate status maps and renderer fields without changing history pass/fail logic. Workbench will pass through bounded fields from the generated history summary and render them in the existing retained-run table.

**Tech Stack:** Python 3.10+, pytest, JSON artifacts, Dash Workbench, Markdown handoff generation.

## Global Constraints

- Keep `qcchem.release_history_summary.v0.1-alpha` unchanged; all fields are additive.
- Reuse `normalize_ai_delivery_review_summary`; do not duplicate AI summary validation.
- Treat every AI review context as `informational_only`; no missing or invalid context may affect history status, `first_failure`, or `--strict` exit status.
- Do not aggregate review event counts across retained runs because snapshots can repeat events.
- Preserve current output ordering and existing status fields.

---

### Task 1: Lock the retained-history contract with failing integration tests

**Files:**
- Modify: `tests/integration/test_release_audit_workflow_v23.py:1455-1555`
- Modify: `tests/integration/test_workbench_app_v14.py:840-1020`
- Modify: `tests/integration/test_workbench_app_v14.py:1589-1675`

**Interfaces:**
- Consumes: `_ai_workspace_delivery_summary_fixture()` and `qcchem.cli.main.main()`.
- Produces: assertions for the additive `ai_workspace_delivery_status_counts`, `ai_workspace_delivery_source_status_counts`, and compact per-run fields.

- [ ] **Step 1: Add the retained-history CLI/Markdown expectations**

In `test_release_history_summarize_lists_retained_runs_and_baselines`, add assertions for both status maps, the per-run snapshot, and emitted text:

```python
assert summary["ai_workspace_delivery_status_counts"] == {"available": 2}
assert summary["ai_workspace_delivery_source_status_counts"] == {"consistent": 2}
assert runs["run-001"]["ai_workspace_delivery"]["review_event_count"] == 1
assert runs["run-001"]["ai_workspace_delivery"]["review_provenance_log"] == (
    "artifacts/ai_workspace/provenance/ai_provenance.jsonl"
)
assert "ai_review=available" in stdout
```

Add a focused malformed retained-run case by replacing one saved run's
`ai_workspace_delivery` with `{"review_status_counts": {"accepted": "one"}}`,
then assert:

```python
assert summary["status"] == "passed"
assert runs["run-002"]["status"] == "passed"
assert runs["run-002"]["ai_workspace_delivery"] == {
    "status": "not_available",
    "release_gate": "informational_only",
}
```

- [ ] **Step 2: Add Workbench consumer expectations**

Extend the Overview and smoke fixtures with the additive top-level maps and a
valid per-run `ai_workspace_delivery`. Assert that smoke returns bounded
`ai_review_status`, `ai_review_source_status`, `ai_review_event_count`, and
`ai_review_provenance_log`, and that Overview text includes:

```python
assert "ai_review=available" in page_text
assert "review_events=1" in page_text
assert "review_source=consistent" in page_text
assert "artifacts/ai_workspace/provenance/ai_provenance.jsonl" in page_text
```

- [ ] **Step 3: Run the focused tests and confirm RED**

Run:

```bash
python -m pytest tests/integration/test_release_audit_workflow_v23.py::test_release_history_summarize_lists_retained_runs_and_baselines tests/integration/test_workbench_app_v14.py::test_overview_page_surfaces_release_verification tests/integration/test_workbench_app_v14.py::test_workbench_smoke_docs_can_check_release_history_run_drilldown -q
```

Expected: FAIL because release-history output and Workbench summaries do not yet expose the asserted AI provenance fields.

### Task 2: Implement the compact history snapshot and consumers

**Files:**
- Modify: `qcchem/cli/main.py:2527-2943`
- Modify: `qcchem/workbench/smoke.py:215-310`
- Modify: `qcchem/workbench/pages/overview.py:273-302`

**Interfaces:**
- Consumes: `normalize_ai_delivery_review_summary(value: object) -> dict[str, Any]`.
- Produces: `run["ai_workspace_delivery"]`, top-level `ai_workspace_delivery_status_counts`, top-level `ai_workspace_delivery_source_status_counts`, and bounded Workbench-derived field names.

- [ ] **Step 1: Add the minimal CLI snapshot and aggregate helpers**

In `_release_history_incomplete_run_summary`, add the shared normalizer fallback:

```python
"ai_workspace_delivery": normalize_ai_delivery_review_summary(None),
```

In `_release_history_run_summary`, normalize only the retained summary value:

```python
ai_workspace_delivery = normalize_ai_delivery_review_summary(payload.get("ai_workspace_delivery"))
```

and add it unchanged to the returned run mapping. Add a source-status count
helper that maps a missing or blank `source_status` to `not_available` without
changing `_release_history_status_counts`:

```python
def _release_history_ai_delivery_source_status_counts(runs: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for run in runs:
        ai_summary = _release_history_dict(run.get("ai_workspace_delivery"))
        source_status = ai_summary.get("source_status")
        status = str(source_status).strip() if isinstance(source_status, str) else ""
        status = status or "not_available"
        counts[status] = counts.get(status, 0) + 1
    return {name: counts[name] for name in sorted(counts)}
```

Add the two additive maps to `_release_history_summary`. Extend
`_print_release_history_summary` and `_release_history_markdown` to include
AI status and counts. Per-run Markdown must include `ai_review`,
`ai_review_source`, `ai_review_events`, `ai_review_provenance`, and the
latest event ID when one exists.

- [ ] **Step 2: Pass bounded fields through Workbench smoke**

In `qcchem/workbench/smoke.py`, extract only the fixed-size fields from each
run:

```python
ai_workspace_delivery = (
    run.get("ai_workspace_delivery")
    if isinstance(run.get("ai_workspace_delivery"), dict)
    else {}
)
```

Return `ai_review_status`, `ai_review_source_status`,
`ai_review_event_count`, and `ai_review_provenance_log` from
`_release_history_run_summary`. In `_release_history_summary`, preserve the
two top-level maps with `{}` defaults for legacy JSON.

- [ ] **Step 3: Render exactly the same context in Overview**

In `_release_history_run_rows`, read `run["ai_workspace_delivery"]` defensively
and append this bounded text before the existing source breadcrumb:

```python
f"ai_review={ai_workspace_delivery.get('status', 'not_available')}; "
f"review_source={ai_workspace_delivery.get('source_status', 'not_available')}; "
f"review_events={ai_workspace_delivery.get('review_event_count', 'n/a')}; "
f"review_provenance={ai_workspace_delivery.get('review_provenance_log', 'not_available')}; "
```

Do not add a new Overview card; the retained-run record is the reviewer’s
appropriate provenance location.

- [ ] **Step 4: Run the focused tests and confirm GREEN**

Run the Task 1 command again.

Expected: PASS, including the malformed-context case retaining a passed
history status.

### Task 3: Document, review, and validate the release-facing behavior

**Files:**
- Modify: `README.md:140-175`
- Modify: `docs/release_audit.md:250-325`
- Modify: `docs/workbench.md:210-245`
- Modify: `docs/user_manual.md:720-770`

**Interfaces:**
- Consumes: the additive history JSON and Markdown fields from Task 2.
- Produces: user documentation that distinguishes informational AI provenance
  from release gating.

- [ ] **Step 1: Document the retained history fields and boundary**

In all four existing release-history descriptions, state that each retained run
includes its frozen AI review status, source status, review-event count, latest
review metadata, and provenance-log path. State explicitly that unavailable or
malformed AI review evidence is `not_available` and does not change release
history pass/fail status.

- [ ] **Step 2: Run static and targeted regression checks**

Run:

```bash
git diff --check
python -m pytest tests/integration/test_release_audit_workflow_v23.py tests/integration/test_workbench_app_v14.py -q
python -m pytest tests/unit/test_release_audit_v23.py -q
```

Expected: all selected tests pass and `git diff --check` prints no whitespace
errors.

- [ ] **Step 3: Run release and Workbench evidence gates**

Run:

```bash
python -m qcchem.cli.main release audit -c configs/release/trust_first_audit.yaml -o /tmp/qcchem-release-history-ai-audit
python -m qcchem.cli.main workbench smoke --docs docs/workbench.md
python -m pytest tests -q
```

Expected: release audit reports `86/0`, Workbench smoke reports all documented
routes and pages passed, and the default test suite is green.

- [ ] **Step 4: Review and publish**

Inspect `git diff --check`, `git diff --stat`, and `git status --short`; stage
only this feature’s source, tests, docs, and plan. Commit with:

```bash
git commit -m "feat: retain ai review provenance in release history"
```

Push `master`, inspect the new GitHub Actions run with `gh run view`, and
report any remaining browser-checklist limitation separately from component-tree
smoke evidence.
