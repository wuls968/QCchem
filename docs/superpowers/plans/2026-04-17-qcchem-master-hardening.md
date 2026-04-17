# QCchem Master Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the QCchem master branch by improving repository hygiene, making runtime calibration budget-aware, and producing one more meaningful real-hardware convergence artifact.

**Architecture:** Keep the existing QCchem architecture intact and focus on strengthening the current run and benchmark paths. Add narrow improvements around runtime submission policy, calibration reporting, and repository hygiene utilities rather than introducing new algorithm families or new top-level abstractions.

**Tech Stack:** Python, Qiskit, Qiskit Nature, Qiskit IBM Runtime, pytest, YAML, Markdown reporting.

---

### Task 1: Add failing tests for budget-aware runtime calibration and repo hygiene

**Files:**
- Modify: `/Users/a0000/QCchem/tests/unit/test_hardware_calibration_v10.py`
- Modify: `/Users/a0000/QCchem/tests/integration/test_hardware_dashboard_v10.py`
- Modify: `/Users/a0000/QCchem/tests/unit/test_config.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_runtime_submission_summary_exposes_budget_metadata():
    ...

def test_hardware_dashboard_reports_budget_and_precision_outcome(tmp_path):
    ...

def test_runtime_budget_config_parses_from_yaml(tmp_path):
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/unit/test_hardware_calibration_v10.py tests/integration/test_hardware_dashboard_v10.py tests/unit/test_config.py -q`
Expected: FAIL because runtime budget metadata and dashboard fields do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add config parsing and result fields only as needed to satisfy the tests.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/unit/test_hardware_calibration_v10.py tests/integration/test_hardware_dashboard_v10.py tests/unit/test_config.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C /Users/a0000/QCchem add tests/unit/test_hardware_calibration_v10.py tests/integration/test_hardware_dashboard_v10.py tests/unit/test_config.py
git -C /Users/a0000/QCchem commit -m "test: add runtime budget calibration coverage"
```

### Task 2: Implement budget-aware runtime calibration and reporting

**Files:**
- Modify: `/Users/a0000/QCchem/qcchem/core/specs.py`
- Modify: `/Users/a0000/QCchem/qcchem/core/results.py`
- Modify: `/Users/a0000/QCchem/qcchem/io/config.py`
- Modify: `/Users/a0000/QCchem/qcchem/backends/runtime_submission.py`
- Modify: `/Users/a0000/QCchem/qcchem/workflow/calibration.py`
- Modify: `/Users/a0000/QCchem/qcchem/workflow/benchmark.py`
- Modify: `/Users/a0000/QCchem/qcchem/reporting/markdown.py`
- Modify: `/Users/a0000/QCchem/qcchem/reporting/aggregate.py`

- [ ] **Step 1: Write the failing runtime budget test if still missing**

```python
assert summary.options_snapshot["max_execution_seconds"] == 300
assert summary.options_snapshot["budget_strategy"] == "tight_calibration"
```

- [ ] **Step 2: Run targeted tests to verify failure**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/unit/test_hardware_calibration_v10.py::test_runtime_submission_summary_exposes_budget_metadata -q`
Expected: FAIL on missing runtime budget keys.

- [ ] **Step 3: Write minimal implementation**

```python
@dataclass(slots=True)
class RuntimeOptionsSpec:
    ...
    max_execution_seconds: float | None = None
    max_budgeted_shots: int | None = None
    calibration_strategy: str = "default"
```

```python
options_snapshot = {
    "precision_target": ...,
    "max_execution_seconds": spec.runtime.max_execution_seconds,
    "max_budgeted_shots": spec.runtime.max_budgeted_shots,
    "budget_strategy": spec.runtime.calibration_strategy,
}
```

- [ ] **Step 4: Run targeted tests to verify pass**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/unit/test_hardware_calibration_v10.py tests/integration/test_hardware_dashboard_v10.py tests/unit/test_config.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C /Users/a0000/QCchem add qcchem/core/specs.py qcchem/core/results.py qcchem/io/config.py qcchem/backends/runtime_submission.py qcchem/workflow/calibration.py qcchem/workflow/benchmark.py qcchem/reporting/markdown.py qcchem/reporting/aggregate.py
git -C /Users/a0000/QCchem commit -m "feat: add budget-aware runtime calibration reporting"
```

### Task 3: Add repository hygiene support without disturbing existing artifacts

**Files:**
- Modify: `/Users/a0000/QCchem/.gitignore`
- Create: `/Users/a0000/QCchem/scripts/artifact_index.py`
- Modify: `/Users/a0000/QCchem/README.md`

- [ ] **Step 1: Write the failing test**

```python
def test_artifact_indexer_discovers_result_json_files(tmp_path):
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/unit/test_platform_v03.py -q`
Expected: FAIL because the artifact indexer does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
def build_artifact_index(root: Path) -> dict[str, object]:
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/unit/test_platform_v03.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git -C /Users/a0000/QCchem add .gitignore scripts/artifact_index.py README.md
git -C /Users/a0000/QCchem commit -m "feat: add artifact indexing and repo hygiene support"
```

### Task 4: Run one tighter real-hardware H2 calibration and refresh hardware dashboard artifacts

**Files:**
- Modify: `/Users/a0000/QCchem/configs/h2_runtime_hardware_probe.yaml`
- Modify: `/Users/a0000/QCchem/benchmarks/hardware_calibration_suite_v1.yaml`
- Update generated artifacts under `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe/`
- Update generated artifacts under `/Users/a0000/QCchem/artifacts/hardware_calibration_suite_v1/`

- [ ] **Step 1: Write the failing test or assertion**

```python
assert payload["runtime_submission"]["options_snapshot"]["precision_target"] <= 0.05
```

- [ ] **Step 2: Run targeted verification to confirm current config does not meet the stricter target**

Run: `python - <<'PY'\nimport yaml\nfrom pathlib import Path\ncfg = yaml.safe_load(Path('/Users/a0000/QCchem/configs/h2_runtime_hardware_probe.yaml').read_text())\nprint(cfg['backend']['runtime']['precision_target'])\nPY`
Expected: prints a value larger than the new target.

- [ ] **Step 3: Update the config and execute the real run**

Run:

```bash
cd /Users/a0000/QCchem
conda run -n qiskit python -m qcchem.cli.main run -c configs/h2_runtime_hardware_probe.yaml
conda run -n qiskit python -m qcchem.cli.main benchmark report artifacts/hardware_calibration_suite_v1/hardware_calibration_summary.json
```

- [ ] **Step 4: Verify artifact outputs**

Run:

```bash
python - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path('/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe/runtime_submission.json').read_text())
print(payload['submitted'], payload['succeeded'], payload['options_snapshot'])
PY
```

Expected: `True True` and tighter runtime precision metadata than the previous probe.

- [ ] **Step 5: Commit**

```bash
git -C /Users/a0000/QCchem add configs/h2_runtime_hardware_probe.yaml benchmarks/hardware_calibration_suite_v1.yaml artifacts/h2_runtime_hardware_probe artifacts/hardware_calibration_suite_v1
git -C /Users/a0000/QCchem commit -m "feat: tighten H2 hardware calibration probe"
```

### Task 5: Final verification and handoff

**Files:**
- Modify: `/Users/a0000/QCchem/docs/handoff.md`
- Modify: `/Users/a0000/QCchem/docs/verified_scope.md`

- [ ] **Step 1: Update documentation**

Document the new budget-aware runtime metadata, artifact indexing support, and the new hardware calibration outcome.

- [ ] **Step 2: Run focused verification**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/unit/test_hardware_calibration_v10.py tests/integration/test_hardware_dashboard_v10.py tests/unit/test_config.py tests/unit/test_platform_v03.py -q`
Expected: PASS

- [ ] **Step 3: Run full verification**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest -q`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git -C /Users/a0000/QCchem add docs/handoff.md docs/verified_scope.md
git -C /Users/a0000/QCchem commit -m "docs: refresh hardening and hardware calibration handoff"
```
