# AI Review Release Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve AI delivery review provenance in release evidence handoffs and surface the same review context on Workbench Overview without changing release pass/fail semantics.

**Architecture:** Reuse the existing `ai_workspace_delivery` object emitted by Workbench smoke. CI-side handoff copies the supplied smoke context; post-download collection reads only manifest-verified downloaded CI smoke paths and requires matrix copies to agree. A shared domain validator labels valid context `informational_only`, rejects malformed input, and feeds both release handoff and Overview. Overview prefers the frozen release copy and falls back to the current local AI Workspace summary.

**Tech Stack:** Python 3.10+, Dash, pytest, JSON/JSONL, Markdown.

## Global Constraints

- AI delivery review provenance is informational and MUST NOT change release evidence status.
- Reuse `build_delivery_handoff_summary()`; do not add another JSONL parser.
- Missing or malformed optional AI review context must render as `not_available`, not raise.
- Do not change the AI Workspace delivery or provenance schemas.

---

### Task 1: Preserve AI review context in release evidence

**Files:**
- Modify: `tests/integration/test_release_audit_workflow_v23.py`
- Modify: `qcchem/cli/main.py`
- Create: `qcchem/workflow/ai_delivery_summary.py`
- Modify: `qcchem/workflow/release_status.py`
- Modify: `docs/release_audit.md`
- Modify: `docs/user_manual.md`

**Interfaces:**
- Consumes: Workbench smoke field `ai_workspace_delivery: dict[str, object]`.
- Produces: release summary field `ai_workspace_delivery` with `release_gate="informational_only"` and a Markdown `AI Delivery Review Provenance` section.

- [x] **Step 1: Write failing release handoff assertions**

Extend `_write_workbench_smoke()` with an event-present fixture and assert both local and downloaded collection paths preserve it:

```python
"ai_workspace_delivery": {
    "available": True,
    "delivery_count": 1,
    "review_status_counts": {"accepted": 1},
    "review_event_count": 1,
    "latest_review_event": {
        "event_id": "evt-review-001",
        "timestamp": "2026-07-10T00:00:00+00:00",
        "delivery_id": "delivery-001",
        "review_status": "accepted",
        "reviewed_by": "release-reviewer",
        "review_source": "workbench",
        "ticket_link_status": "updated",
    },
    "review_provenance_log": "artifacts/ai_workspace/provenance/ai_provenance.jsonl",
},
```

Expected assertions:

```python
assert summary["ai_workspace_delivery"]["release_gate"] == "informational_only"
assert summary["ai_workspace_delivery"]["review_event_count"] == 1
assert "## AI Delivery Review Provenance" in handoff
assert "- review_event_count: `1`" in handoff
assert "- release_gate: `informational_only`" in handoff
```

- [x] **Step 2: Run tests to verify the new contract fails**

Run:

```bash
python -m pytest tests/integration/test_release_audit_workflow_v23.py::test_release_evidence_handoff_cli_writes_local_ci_handoff tests/integration/test_release_audit_workflow_v23.py::test_release_collect_evidence_cli_writes_verifier_and_workbench_handoff -q
```

Expected: FAIL because `ai_workspace_delivery` is absent from the release summary and handoff.

- [x] **Step 3: Add one normalization helper and propagate the field**

Add a helper near the release handoff formatters:

```python
def _release_ai_workspace_delivery_summary(workbench_summary: dict[str, object]) -> dict[str, object]:
    raw = workbench_summary.get("ai_workspace_delivery")
    if not isinstance(raw, dict):
        return {"status": "not_available", "release_gate": "informational_only"}
    return {"status": "available", "release_gate": "informational_only", **raw}
```

Use it in `_local_release_evidence_summary()` and `_release_evidence_summary()`. In `_release_evidence_handoff_markdown()`, render availability, delivery/review counts, review-status counts, latest event metadata, provenance path, and the informational gate label.

- [x] **Step 4: Run the focused release tests**

Run the Step 2 command again.

Expected: `2 passed` and both collection modes keep status `passed`.

- [x] **Step 5: Document the release contract**

Update `docs/release_audit.md` to state that release summary JSON and Markdown carry the compact AI delivery review context, and that it is explicitly non-gating.

### Task 2: Surface frozen or live AI review provenance on Overview

**Files:**
- Modify: `tests/integration/test_workbench_app_v14.py`
- Modify: `qcchem/workbench/pages/overview.py`
- Modify: `docs/workbench.md`

**Interfaces:**
- Consumes: `release_evidence_handoff["ai_workspace_delivery"]` when available, otherwise `build_delivery_handoff_summary(list_delivery_records(root), workspace_root_path=root)`.
- Produces: Overview status card `AI delivery review provenance` with source, delivery count, review-event count, latest review, and provenance path.

- [x] **Step 1: Write a failing Overview component-tree assertion**

Add `ai_workspace_delivery` to the release summary fixture in `test_overview_page_surfaces_release_verification()` and assert:

```python
assert "AI delivery review provenance" in page_text
assert "1 review event" in page_text
assert "delivery-001 accepted via workbench" in page_text
assert "artifacts/ai_workspace/provenance/ai_provenance.jsonl" in page_text
```

- [x] **Step 2: Run the Overview test and verify failure**

Run:

```bash
python -m pytest tests/integration/test_workbench_app_v14.py::test_overview_page_surfaces_release_verification -q
```

Expected: FAIL because Overview has no AI review provenance card.

- [x] **Step 3: Implement the Overview summary resolver and card**

Add a small helper that prefers an available release snapshot and otherwise reads the current local AI workspace with the existing summary builder. Render a status card with bounded one-line detail and informational tone.

```python
release_ai_delivery = release_evidence_handoff.get("ai_workspace_delivery")
if isinstance(release_ai_delivery, dict) and release_ai_delivery.get("status") == "available":
    ai_delivery = release_ai_delivery
    ai_delivery_source = "release evidence handoff"
else:
    root = workspace_root(Path.cwd(), create=False)
    ai_delivery = build_delivery_handoff_summary(
        list_delivery_records(root),
        workspace_root_path=root,
    )
    ai_delivery_source = "current workspace"
```

- [x] **Step 4: Run the Overview and Workbench smoke tests**

Run:

```bash
python -m pytest tests/integration/test_workbench_app_v14.py::test_overview_page_surfaces_release_verification tests/integration/test_workbench_app_v14.py::test_workbench_smoke_summary_records_ai_workspace_delivery_handoff -q
```

Expected: `2 passed`.

- [x] **Step 5: Document the Overview behavior**

Update `docs/workbench.md` so the Overview and release handoff sections describe the frozen release copy, live fallback, and informational-only semantics.

### Review Remediation

- [x] Read AI review context from downloaded `workbench_smoke.json` paths exposed by the verified diagnostics manifest instead of synthesizing it under the output root.
- [x] Require multiple downloaded matrix smoke snapshots to be identical; report missing, unreadable, invalid, or divergent context as non-gating `not_available`.
- [x] Move nested count/event validation into `qcchem.workflow.ai_delivery_summary.normalize_ai_delivery_review_summary()`.
- [x] Apply the shared validator to frozen and live Overview snapshots so malformed archived context falls back to the current workspace.
- [x] Add an end-to-end regression proving malformed AI context leaves release `status`, `first_failure`, and `failures` unchanged.
- [x] Cover malformed nested downloaded context and divergent multi-matrix smoke snapshots explicitly.

### Task 3: Validate and publish

**Files:**
- Review all files modified in Tasks 1-2.

**Interfaces:**
- Consumes: the completed implementation and test suite.
- Produces: a clean, pushed `master` commit with local and remote release evidence.

- [x] **Step 1: Run lint and focused integration tests**

```bash
python -m ruff check qcchem/cli/main.py qcchem/workflow/ai_delivery_summary.py qcchem/workflow/release_status.py qcchem/workbench/pages/overview.py tests/integration/test_release_audit_workflow_v23.py tests/integration/test_workbench_app_v14.py
python -m pytest tests/integration/test_release_audit_workflow_v23.py tests/integration/test_workbench_app_v14.py -q
```

- [x] **Step 2: Run release-facing gates**

```bash
python -m qcchem.cli.main workbench smoke --docs docs/workbench.md -o /tmp/qcchem_workbench_smoke_ai_review_release.json
python -m qcchem.cli.main release audit -c configs/release/trust_first_audit.yaml -o /tmp/qcchem_release_audit_ai_review_release
python -m compileall -q qcchem
python -m pytest -q
git diff --check
```

Expected: all commands pass; release audit has zero failures; full default pytest is green.

- [x] **Step 3: Review the diff and verify non-gating behavior**

Confirm release status calculations still depend only on verifier, Workbench smoke, and matrix delta. Confirm AI review fields are copied and rendered but never added to `failures`.

- [x] **Step 4: Commit, push, and watch CI**

```bash
git add docs/superpowers/plans/2026-07-10-ai-review-release-handoff.md qcchem/cli/main.py qcchem/workflow/ai_delivery_summary.py qcchem/workflow/release_status.py qcchem/workbench/pages/overview.py tests/integration/test_release_audit_workflow_v23.py tests/integration/test_workbench_app_v14.py docs/release_audit.md docs/user_manual.md docs/workbench.md
git commit -m "feat: surface ai review provenance in release handoff"
git push origin master
run_id=$(gh run list --repo wuls968/QCchem --branch master --limit 1 --json databaseId --jq '.[0].databaseId')
gh run watch "$run_id" --repo wuls968/QCchem --exit-status
```

Expected: push succeeds and all supported Python jobs pass.
