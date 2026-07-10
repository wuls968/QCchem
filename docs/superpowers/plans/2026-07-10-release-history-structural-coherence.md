# Release-History Structural Coherence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify that downloaded retained-history counters and non-AI status maps are structurally consistent with their retained run records.

**Architecture:** Extend the existing read-only history coherence verifier in `qcchem.workflow.release_status`. Shared local helpers will reproduce the release-history generator's deterministic outcome/status-map reductions. The verifier will compare declared values only when their complete compatibility group is present, preserve all-omitted groups as legacy, and record compact validation states on the existing handoff entry.

**Tech Stack:** Python 3.10+, pytest, JSON release artifacts, Trust-First release CLI.

## Global Constraints

- Keep `qcchem.release_history_summary.v0.1-alpha` unchanged; verifier report fields are additive.
- Reproduce `qcchem.cli.main._release_history_summary` status/count semantics exactly.
- Require `run_count` to equal `len(runs)` whenever a summary is readable.
- Treat all-absent outcome or status-map groups as legacy, but reject partial groups.
- Do not validate `skipped_non_directory_count` or real-browser evidence from downloaded artifacts.
- Keep AI provenance validation separate and preserve its `not_available` semantics.

---

### Task 1: Add failing structural coherence contract tests

**Files:**
- Modify: `tests/integration/test_release_audit_workflow_v23.py:760-1010`

**Interfaces:**
- Consumes: `_write_downloaded_release_diagnostics_artifact(tmp_path)`, `_refresh_diagnostics_manifest_file_record(...)`, and `main(["release", "verify-artifacts", ...])`.
- Produces: expected report metadata and named structural failure reasons.

- [ ] **Step 1: Assert the normal report's structural validation**

Add to `test_release_verify_artifacts_cli_accepts_downloaded_diagnostics`:

```python
assert history_handoff["structural_validation"] == "verified"
assert history_handoff["outcome_counts_validation"] == "verified"
assert history_handoff["status_maps_validation"] == "verified"
```

- [ ] **Step 2: Add parameterized tamper cases**

Add a dedicated parameterized test that mutates the copied
`release_history_summary.json`, does not refresh the manifest, and asserts exit
code `2`, the semantic failure, and the independent digest failure:

```python
summary["status"] = "failed"
assert "release_history_summary_status_mismatch" in failure_reasons

summary["run_count"] = 2
assert "release_history_summary_run_count_mismatch" in failure_reasons

summary["passed_run_count"] = 0
assert "release_history_summary_outcome_counts_mismatch" in failure_reasons

summary["matrix_delta_status_counts"] = {"not_available": 1}
assert "release_history_summary_status_map_mismatch" in failure_reasons

summary.pop("workbench_smoke_status_counts")
assert "release_history_summary_status_maps_incomplete" in failure_reasons
```

- [ ] **Step 3: Add legacy group compatibility coverage**

Remove all three outcome counters and all four non-AI status maps, refresh the
history-summary manifest record, then assert:

```python
assert exit_code == 0
assert history_handoff["structural_validation"] == "legacy_not_available"
assert history_handoff["outcome_counts_validation"] == "legacy_not_available"
assert history_handoff["status_maps_validation"] == "legacy_not_available"
```

Add a partial-outcome test that removes only `failed_run_count` and asserts
`release_history_summary_outcome_counts_incomplete`.

- [ ] **Step 4: Run focused tests and confirm RED**

Run:

```bash
python -m pytest tests/integration/test_release_audit_workflow_v23.py::test_release_verify_artifacts_cli_accepts_downloaded_diagnostics tests/integration/test_release_audit_workflow_v23.py -k "release_history and (structural or verify_artifacts)" -q
```

Expected: new structural report assertions and semantic failure assertions fail
because the current verifier does not recompute non-AI fields.

### Task 2: Implement structural status, counter, and map verification

**Files:**
- Modify: `qcchem/workflow/release_status.py:16-24`
- Modify: `qcchem/workflow/release_status.py:972-1125`

**Interfaces:**
- Consumes: the validated `runs: list[dict[str, object]]` from
  `_verify_release_history_coherence`.
- Produces: `_verify_release_history_structural_coherence(...) -> None` and
  handoff entry fields `structural_validation`, `outcome_counts_validation`,
  and `status_maps_validation`.

- [ ] **Step 1: Define deterministic history field groups and reducers**

Add exact field tuples:

```python
RELEASE_HISTORY_OUTCOME_COUNT_FIELDS = (
    "passed_run_count",
    "failed_run_count",
    "incomplete_run_count",
)
RELEASE_HISTORY_STATUS_MAP_FIELDS = (
    ("run_status_counts", "status"),
    ("matrix_delta_status_counts", "release_matrix_delta"),
    ("release_artifact_verification_status_counts", "release_artifact_verification"),
    ("workbench_smoke_status_counts", "workbench_smoke"),
)
```

Implement `_release_history_status_counts(runs, key)` with the generator's
direct-or-nested `status` fallback to `not_available`, and
`_release_history_derived_status(runs)` with the `empty/passed/failed/incomplete`
decision order from `qcchem.cli.main._release_history_summary`.

- [ ] **Step 2: Verify status, run count, and outcome group**

Invoke structural verification after a valid current run is found. Compare
summary `status` and `run_count` with derived values. For outcome counters,
determine group state from presence of all three fields:

```python
if not present_fields:
    entry["outcome_counts_validation"] = "legacy_not_available"
elif len(present_fields) != len(RELEASE_HISTORY_OUTCOME_COUNT_FIELDS):
    # append release_history_summary_outcome_counts_incomplete
else:
    # compare expected and actual dictionaries
```

Use failure reasons `release_history_summary_status_mismatch`,
`release_history_summary_run_count_mismatch`, and
`release_history_summary_outcome_counts_mismatch`.

- [ ] **Step 3: Verify all-or-none non-AI status maps**

Apply the same group-state rule to the four map fields. For a complete group,
compare every actual map with its reducer output and append:

```python
{
    "reason": "release_history_summary_status_map_mismatch",
    "field": field,
    "expected": expected,
    "actual": actual,
}
```

For a partial group, append `release_history_summary_status_maps_incomplete`
with present/missing field lists. Set `status_maps_validation` to `verified`,
`legacy_not_available`, or `inconsistent` accordingly. Set overall
`structural_validation` to `verified` only when both groups verify, to
`legacy_not_available` when both are legacy, to `partially_legacy` when one is
legacy and the other verifies, and to `inconsistent` after any structural
failure.

- [ ] **Step 4: Run focused tests and confirm GREEN**

Run the Task 1 command again.

Expected: nominal, tampered, partial, and legacy cases pass with the intended
report fields and named failures.

### Task 3: Document and validate the strengthened downloaded-history contract

**Files:**
- Modify: `README.md:150-165`
- Modify: `docs/release_audit.md:306-320`
- Modify: `docs/user_manual.md:724-738`

**Interfaces:**
- Consumes: structural validation metadata from the verifier report.
- Produces: accurate operator guidance distinguishing semantic history checks
  from manifest digests and manual browser review.

- [ ] **Step 1: Document structural coherence and legacy behavior**

State that `verify-artifacts` recomputes retained run totals, outcome counts,
and non-AI status maps when declared. Explain all-absent legacy groups remain
readable, while partial or mismatched declarations fail verification. Keep the
manual real-browser checklist explicitly outside this verifier's scope.

- [ ] **Step 2: Run focused release regressions**

Run:

```bash
git diff --check
python -m pytest tests/integration/test_release_audit_workflow_v23.py -q
python -m pytest tests/unit/test_release_audit_v23.py -q
python -m qcchem.cli.main release audit -c configs/release/trust_first_audit.yaml -o /tmp/qcchem-history-structural-audit
python -m qcchem.cli.main workbench smoke --docs docs/workbench.md
```

Expected: integration and unit tests pass; the audit reports `86 passed, 0 failed`;
Workbench smoke reports all six routes and fourteen pages passed.

- [ ] **Step 3: Run the full suite, review, and publish**

Run:

```bash
python -m pytest tests -q
git diff --check
git diff --stat
git status --short --branch
```

Stage only this feature's design, plan, source, tests, and docs. Commit with:

```bash
git commit -m "feat: verify release history structure"
```

Push `master`, wait for the GitHub Actions Python 3.10/3.11/3.12 matrix, and
report the remaining manual browser-checklist boundary.
