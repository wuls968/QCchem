# QCchem Agent Interface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a CLI-first AI agent interface plus a formal hardware runtime campaign report without rewriting QCchem’s existing workflows.

**Architecture:** Reuse existing run/benchmark/runtime-collect workflows and wrap them in a small agent-task schema and orchestration layer. Generate a human-readable hardware report and a machine-readable campaign summary from the existing hardware calibration suite.

**Tech Stack:** Python, dataclasses, existing QCchem CLI/workflow modules, YAML, JSON, pytest

---

### Task 1: Add failing tests for the agent interface

**Files:**
- Create: `/Users/a0000/QCchem/tests/integration/test_agent_interface_v13.py`
- Modify: `/Users/a0000/QCchem/tests/integration/test_cli_entrypoint.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_validate_agent_task_reports_valid_config(): ...
def test_run_agent_task_executes_runtime_collect_task(): ...
def test_agent_summarize_writes_campaign_summary(): ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/integration/test_agent_interface_v13.py tests/integration/test_cli_entrypoint.py -q`
Expected: FAIL because `agent` subcommands and workflow modules do not exist yet.

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_agent_interface_v13.py tests/integration/test_cli_entrypoint.py
git commit -m "test: add failing agent interface coverage"
```

### Task 2: Implement agent task parsing and execution

**Files:**
- Create: `/Users/a0000/QCchem/qcchem/io/agent_config.py`
- Create: `/Users/a0000/QCchem/qcchem/workflow/agent.py`
- Modify: `/Users/a0000/QCchem/qcchem/workflow/__init__.py`
- Modify: `/Users/a0000/QCchem/qcchem/cli/main.py`

- [ ] **Step 1: Write minimal parsing/execution code**

```python
@dataclass(slots=True)
class AgentTaskSpec:
    ...
```

- [ ] **Step 2: Add CLI plumbing for**

```text
qcchem agent validate-task
qcchem agent run-task
qcchem agent summarize
```

- [ ] **Step 3: Run the focused tests**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/integration/test_agent_interface_v13.py tests/integration/test_cli_entrypoint.py -q`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add qcchem/io/agent_config.py qcchem/workflow/agent.py qcchem/workflow/__init__.py qcchem/cli/main.py tests/integration/test_agent_interface_v13.py tests/integration/test_cli_entrypoint.py
git commit -m "feat: add CLI-first agent task interface"
```

### Task 3: Add hardware campaign report generation

**Files:**
- Create: `/Users/a0000/QCchem/qcchem/reporting/hardware_campaign.py`
- Create: `/Users/a0000/QCchem/docs/hardware_runtime_campaign_report.md`
- Create: `/Users/a0000/QCchem/artifacts/hardware_calibration_suite_v1/hardware_runtime_campaign_summary.json`
- Modify: `/Users/a0000/QCchem/qcchem/reporting/__init__.py`
- Modify: `/Users/a0000/QCchem/qcchem/workflow/agent.py`

- [ ] **Step 1: Write failing tests for summary generation**

```python
def test_build_hardware_campaign_summary_picks_best_case(): ...
```

- [ ] **Step 2: Implement summary builder and markdown report writer**

- [ ] **Step 3: Generate the real hardware campaign report from current artifacts**

- [ ] **Step 4: Run focused tests**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/integration/test_agent_interface_v13.py tests/integration/test_hardware_dashboard_v10.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add qcchem/reporting/hardware_campaign.py qcchem/reporting/__init__.py qcchem/workflow/agent.py docs/hardware_runtime_campaign_report.md artifacts/hardware_calibration_suite_v1/hardware_runtime_campaign_summary.json
git commit -m "feat: add hardware runtime campaign reporting"
```

### Task 4: Add agent examples and docs

**Files:**
- Create: `/Users/a0000/QCchem/examples/agents/runtime_collect_h2.yaml`
- Create: `/Users/a0000/QCchem/examples/agents/hardware_campaign_summary.yaml`
- Create: `/Users/a0000/QCchem/examples/agents/benchmark_h2_lih.yaml`
- Create: `/Users/a0000/QCchem/docs/agent_interface.md`
- Modify: `/Users/a0000/QCchem/README.md`
- Modify: `/Users/a0000/QCchem/docs/handoff.md`
- Modify: `/Users/a0000/QCchem/docs/architecture.md`
- Modify: `/Users/a0000/QCchem/docs/verified_scope.md`

- [ ] **Step 1: Add example task files**

- [ ] **Step 2: Document agent usage**

- [ ] **Step 3: Update README and project docs**

- [ ] **Step 4: Commit**

```bash
git add examples/agents docs/agent_interface.md README.md docs/handoff.md docs/architecture.md docs/verified_scope.md
git commit -m "docs: add agent interface usage and examples"
```

### Task 5: Full verification

**Files:**
- Verify only

- [ ] **Step 1: Run the full test suite**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest -q`
Expected: PASS

- [ ] **Step 2: Smoke test agent commands**

Run:

```bash
cd /Users/a0000/QCchem
conda run -n qiskit python -m qcchem.cli.main agent validate-task examples/agents/runtime_collect_h2.yaml
conda run -n qiskit python -m qcchem.cli.main agent summarize artifacts/hardware_calibration_suite_v1
```

Expected: PASS with summary output and artifact/report paths

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: verify agent interface and hardware report"
```
