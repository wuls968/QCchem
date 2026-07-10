# Release-History Coherence Verifier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Detect downloaded retained-history summaries that diverge from their copied current release evidence or declared AI provenance aggregates without treating unavailable AI context as a release failure.

**Architecture:** `qcchem.workflow.release_status` remains the read-only downloaded-diagnostics verifier. It will add focused helpers that locate the `current` history run, compare the release status and normalized AI snapshot with copied current evidence, and recompute declared AI aggregate maps. The helpers append failures to the existing verifier report and expose compact verification metadata in the existing history-handoff entry.

**Tech Stack:** Python 3.10+, pytest, JSON artifact verification, Trust-First release CLI.

## Global Constraints

- Keep `qcchem.release_history_summary.v0.1-alpha` unchanged; all verifier output fields are additive.
- Use `normalize_ai_delivery_review_summary` as the only AI snapshot validation boundary.
- `not_available` AI snapshots are valid informational evidence when both sides normalize identically.
- Preserve readability of historical summaries that omit both additive AI aggregate maps.
- Fail only declared coherence divergence; do not make AI review availability a release eligibility gate.
- Keep diagnostics-manifest digest failures independent of semantic coherence failures.

---

### Task 1: Define the verifier contract with failing downloaded-artifact tests

**Files:**
- Modify: `tests/integration/test_release_audit_workflow_v23.py:734-780`
- Modify: `tests/integration/test_release_audit_workflow_v23.py:1928-1980`

**Interfaces:**
- Consumes: `_write_downloaded_release_diagnostics_artifact(tmp_path)` and `main(["release", "verify-artifacts", ...])`.
- Produces: observable report fields and failure reasons for history/current coherence.

- [x] **Step 1: Add passing current-run coherence assertions**

Extend `test_release_verify_artifacts_cli_accepts_downloaded_diagnostics`:

```python
assert history_handoff["current_run_label"] == "current"
assert history_handoff["current_run_status"] == "passed"
assert history_handoff["current_ai_workspace_delivery_status"] == "available"
assert history_handoff["current_ai_workspace_delivery_source_status"] == "not_available"
assert history_handoff["ai_workspace_delivery_validation"] == "verified"
```

- [x] **Step 2: Add explicit corruption tests**

For a copied `release_history_summary.json`, mutate one field per test before
calling `verify-artifacts`, then assert exit code `2` and the named failure:

```python
summary["runs"] = []
assert "release_history_current_run_missing" in failure_reasons

summary["runs"][0]["status"] = "failed"
assert "release_history_current_run_status_mismatch" in failure_reasons

summary["runs"][0]["ai_workspace_delivery"]["review_event_count"] = 0
assert "release_history_current_ai_workspace_delivery_mismatch" in failure_reasons

summary["ai_workspace_delivery_status_counts"] = {"not_available": 1}
assert "release_history_ai_workspace_delivery_status_counts_mismatch" in failure_reasons
```

Keep the diagnostics-manifest mismatch assertion separate from the semantic
failure reason because mutating downloaded JSON intentionally invalidates its
recorded digest.

- [x] **Step 3: Add legacy compatibility coverage**

Remove both AI aggregate map fields and every run's `ai_workspace_delivery`
field from the copied history JSON. Verify that the history entry reports:

```python
assert history_handoff["ai_workspace_delivery_validation"] == "legacy_not_available"
```

The fixture's current evidence may contain AI context; the verifier must not
fail merely because an older summary predates the additive projection.

- [x] **Step 4: Run focused tests and confirm RED**

Run:

```bash
python -m pytest tests/integration/test_release_audit_workflow_v23.py::test_release_verify_artifacts_cli_accepts_downloaded_diagnostics tests/integration/test_release_audit_workflow_v23.py -k "release_history and (verify_artifacts or coherence)" -q
```

Expected: the new passing assertions and corruption tests fail because the
existing verifier only validates independent files.

### Task 2: Implement current-evidence and AI aggregate coherence verification

**Files:**
- Modify: `qcchem/workflow/release_status.py:1-20`
- Modify: `qcchem/workflow/release_status.py:770-910`

**Interfaces:**
- Consumes: `normalize_ai_delivery_review_summary(value: object) -> dict[str, Any]`.
- Produces: `_verify_release_history_coherence(...) -> None` and additive
  fields on `release_history_handoffs` report entries.

- [x] **Step 1: Add deterministic compact helpers**

Add a lazy wrapper beside existing release-status helpers:

```python
def normalize_ai_delivery_review_summary(*args: object, **kwargs: object) -> dict[str, Any]:
    from qcchem.workflow.ai_delivery_summary import normalize_ai_delivery_review_summary as normalize
    return normalize(*args, **kwargs)
```

Add helpers that derive deterministic maps from a `runs` list:

```python
def _release_history_ai_source_status_counts(runs: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for run in runs:
        summary = run.get("ai_workspace_delivery") if isinstance(run.get("ai_workspace_delivery"), dict) else {}
        source_status = summary.get("source_status")
        key = source_status.strip() if isinstance(source_status, str) else ""
        key = key or "not_available"
        counts[key] = counts.get(key, 0) + 1
    return {key: counts[key] for key in sorted(counts)}
```

- [x] **Step 2: Verify the current run against copied evidence**

After `_verify_release_history_current_evidence` returns a mapping, invoke a
helper that requires exactly one dictionary run with `label == "current"`. Add
failures with these exact reasons:

```python
"release_history_runs_invalid"
"release_history_current_run_missing"
"release_history_current_run_duplicate"
"release_history_current_run_status_mismatch"
"release_history_current_ai_workspace_delivery_mismatch"
```

Compare AI snapshots only when the summary declares the additive AI map fields.
When neither map exists, set `entry["ai_workspace_delivery_validation"]` to
`"legacy_not_available"`; otherwise set it to `"verified"` after all checks.

- [x] **Step 3: Verify declared aggregate maps**

When either map exists, require both mappings and compare them with values
recomputed from the retained run list. Add failure reasons:

```python
"release_history_ai_workspace_delivery_aggregate_maps_incomplete"
"release_history_ai_workspace_delivery_status_counts_mismatch"
"release_history_ai_workspace_delivery_source_status_counts_mismatch"
```

Store the current run's compact status and normalized AI status/source status in
the report entry without copying raw events or provenance records.

- [x] **Step 4: Run focused tests and confirm GREEN**

Run the Task 1 command again.

Expected: all nominal, divergence, and legacy cases pass with explicit failure
reasons where applicable.

### Task 3: Document and validate the downloaded-diagnostics trust boundary

**Files:**
- Modify: `README.md:134-175`
- Modify: `docs/release_audit.md:249-285`
- Modify: `docs/user_manual.md:684-710`

**Interfaces:**
- Consumes: the verifier report's retained-history coherence fields.
- Produces: concise user-facing explanation that digest integrity and semantic
  coherence are both checked after download.

- [x] **Step 1: Document coherence semantics**

State that `release verify-artifacts` cross-checks the retained `current` run
against copied current evidence and, when present, validates AI provenance
aggregate maps. State that `not_available` context is informational while a
declared mismatch fails verification; older summaries without additive fields
remain readable.

- [x] **Step 2: Run targeted and release-facing regressions**

Run:

```bash
git diff --check
python -m pytest tests/integration/test_release_audit_workflow_v23.py -q
python -m pytest tests/unit/test_release_audit_v23.py -q
python -m qcchem.cli.main release audit -c configs/release/trust_first_audit.yaml -o /tmp/qcchem-history-coherence-audit
python -m qcchem.cli.main workbench smoke --docs docs/workbench.md
```

Expected: integration and unit tests pass; audit reports `86 passed, 0 failed`;
Workbench smoke reports six routes and fourteen pages passed.

- [x] **Step 3: Run the full suite and review before publishing**

Run:

```bash
python -m pytest tests -q
git diff --check
git diff --stat
git status --short --branch
```

Stage only this feature's design, plan, source, tests, and docs. Commit with:

```bash
git commit -m "feat: verify release history coherence"
```

Push `master`, wait for the three-version GitHub Actions matrix, and report the
remote CI conclusion plus the remaining real-browser checklist boundary.
