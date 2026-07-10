# Release-History Guidance Coherence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject downloaded release-history summaries whose operator guidance is inconsistent with their retained run records.

**Architecture:** Extend the existing structural coherence verifier in `qcchem.workflow.release_status` with two deterministic reducers that reproduce the generator's action and first-failure semantics. Treat both fields as mandatory core guidance fields, report one compact guidance validation state, and keep digest validation independent.

**Tech Stack:** Python 3.10+, pytest, JSON release artifacts, Trust-First release CLI.

## Global Constraints

- Keep `qcchem.release_history_summary.v0.1-alpha` unchanged.
- Reproduce `qcchem.cli.main._release_history_summary` guidance semantics exactly.
- `recommended_action` and `first_failure` are core fields; missing values are invalid, not legacy-compatible.
- Preserve all current counter/map/AI compatibility behavior.
- Do not validate filesystem-only metadata or manual browser evidence.

---

### Task 1: Add failing guidance coherence contract tests

**Files:**
- Modify: `tests/integration/test_release_audit_workflow_v23.py:750-1020`

**Interfaces:**
- Consumes: `_write_downloaded_release_diagnostics_artifact(tmp_path)`,
  `_refresh_diagnostics_manifest_file_record(...)`, and `main(["release",
  "verify-artifacts", ...])`.
- Produces: expected `guidance_validation` metadata and named failure reasons.

- [ ] **Step 1: Assert nominal guidance validation**

Add to `test_release_verify_artifacts_cli_accepts_downloaded_diagnostics`:

```python
assert history_handoff["guidance_validation"] == "verified"
```

- [ ] **Step 2: Add tampered guidance tests**

Add a parameterized test that mutates the copied history summary without
refreshing its diagnostics manifest record:

```python
[
    ("recommended_action", "release_history_summary_recommended_action_mismatch"),
    ("first_failure", "release_history_summary_first_failure_mismatch"),
]
```

For `recommended_action`, assign `"collect_release_evidence"`. For
`first_failure`, assign:

```python
{"label": "current", "status": "passed", "reason": "spurious", "path": "none", "failure": None}
```

After `verify-artifacts`, assert exit code `2`, the expected semantic failure,
and `diagnostics_manifest_sha256_mismatch`.

- [ ] **Step 3: Prove semantic rejection with refreshed digest**

Write one focused test that changes `recommended_action`, refreshes the copied
summary manifest record, and asserts:

```python
assert exit_code == 2
assert "release_history_summary_recommended_action_mismatch" in failure_reasons
assert "diagnostics_manifest_sha256_mismatch" not in failure_reasons
```

- [ ] **Step 4: Run tests and confirm RED**

Run:

```bash
python -m pytest tests/integration/test_release_audit_workflow_v23.py -k "guidance or accepts_downloaded_diagnostics" -q
```

Expected: the nominal field assertion and semantic failure assertions fail
because the verifier has no guidance reducer.

### Task 2: Implement deterministic guidance verification

**Files:**
- Modify: `qcchem/workflow/release_status.py:1000-1190`

**Interfaces:**
- Consumes: validated `runs: list[dict[str, object]]` and the summary status
  inside `_verify_release_history_structural_coherence(...)`.
- Produces: `_release_history_recommended_action(status) -> str`,
  `_release_history_first_failure(runs) -> dict[str, object] | None`, and
  `entry["guidance_validation"]`.

- [ ] **Step 1: Add the exact local reducers**

Add these helpers adjacent to the existing structural reducers:

```python
def _release_history_recommended_action(status: str) -> str:
    if status == "passed":
        return "review_release_history"
    if status == "empty":
        return "collect_release_evidence"
    return "inspect_release_history_failures"


def _release_history_first_failure(runs: list[dict[str, object]]) -> dict[str, object] | None:
    for run in runs:
        if run.get("status") == "passed":
            continue
        failure = run.get("first_failure") if isinstance(run.get("first_failure"), dict) else None
        return {
            "label": run.get("label"),
            "status": run.get("status"),
            "reason": failure.get("reason") if failure is not None else "release_history_run_not_passed",
            "path": failure.get("path") if failure is not None else run.get("summary_path"),
            "failure": failure,
        }
    return None
```

- [ ] **Step 2: Compare core guidance fields**

At the end of `_verify_release_history_structural_coherence`, compare the
summary action against `_release_history_recommended_action(expected_status)`
and `summary["first_failure"]` against `_release_history_first_failure(runs)`.
For each divergence, append one failure through
`_release_history_coherence_failure(...)` with the specified reason and
expected/actual details. Set `guidance_validation` to `verified` only when both
fields agree; otherwise set it to `inconsistent` and make
`structural_validation` `inconsistent`.

- [ ] **Step 3: Mark invalid retained-run shapes as unchecked**

In each early return for invalid runs, missing `current`, or duplicate
`current`, add:

```python
entry["guidance_validation"] = "not_checked"
```

- [ ] **Step 4: Run focused tests and confirm GREEN**

Run the Task 1 command again.

Expected: the nominal, digest-tampered, and refreshed-digest semantic cases
pass with the expected report metadata and failure reasons.

### Task 3: Document and publish the guidance contract

**Files:**
- Modify: `README.md:155-170`
- Modify: `docs/release_audit.md:310-325`
- Modify: `docs/user_manual.md:724-740`

**Interfaces:**
- Consumes: verifier report metadata and failure reasons.
- Produces: operator-facing documentation that distinguishes integrity checks
  from the manual browser checklist.

- [ ] **Step 1: Document derived guidance verification**

Add a concise statement that `verify-artifacts` recomputes history action and
first failure from retained runs; a missing or divergent value fails
verification even when the manifest digest is refreshed. Retain the manual
real-browser boundary.

- [ ] **Step 2: Run release regressions**

Run:

```bash
git diff --check
python -m pytest tests/integration/test_release_audit_workflow_v23.py -q
python -m pytest tests/unit/test_release_audit_v23.py -q
python -m qcchem.cli.main release audit -c configs/release/trust_first_audit.yaml -o /tmp/qcchem-history-guidance-audit
python -m qcchem.cli.main workbench smoke --docs docs/workbench.md
```

Expected: both test modules pass, release audit reports `86 passed, 0 failed`,
and Workbench smoke reports six routes and fourteen pages passed.

- [ ] **Step 3: Run the full suite, review, and publish**

Run:

```bash
python -m pytest tests -q
git diff --check
git diff --stat
git status --short --branch
```

Stage only the design, plan, source, tests, and documentation for this
increment. Commit with:

```bash
git commit -m "feat: verify release history guidance"
```

Push `master`, wait for the Python 3.10/3.11/3.12 GitHub Actions matrix, and
report the remaining manual real-browser-checklist boundary.
