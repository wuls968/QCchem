# QCchem Hardware Calibration and Minimal Real Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two high-value real-hardware chemistry examples plus a unified hardware calibration dashboard so QCchem can compare exact, ideal, sampled, and runtime-backed execution using artifact-first provenance.

**Architecture:** Keep the existing QCchem run and benchmark pipeline intact. Extend the existing result schema, calibration helpers, runtime submission summary, and aggregate reports so hardware evidence becomes a first-class view instead of a sidecar. Use one tiny baseline chemistry case (`H2`) and one QCchem-differentiated low-rank case (`LiH active-space compressed`) to generate reproducible runtime artifacts and feed a single hardware dashboard.

**Tech Stack:** Python, Qiskit, Qiskit Nature, qiskit-ibm-runtime, primitives V2, PySCF, pytest, YAML/JSON/HDF5 exports, existing QCchem CLI/report stack

---

## File Map

### Core/runtime/result files to modify

- Modify: `/Users/a0000/QCchem/qcchem/core/results.py`
  Add explicit hardware-evidence fields and ensure calibration/runtime summaries can represent measured runtime runs cleanly.
- Modify: `/Users/a0000/QCchem/qcchem/workflow/runner.py`
  Compute hardware-verified flags, wire measured runtime data into calibration, and keep exact/ideal/local sampled paths consistent.
- Modify: `/Users/a0000/QCchem/qcchem/workflow/calibration.py`
  Build calibration summaries from both local sampled runs and remote runtime returns.
- Modify: `/Users/a0000/QCchem/qcchem/workflow/benchmark.py`
  Aggregate hardware dashboard metrics and serialize a hardware calibration summary artifact.
- Modify: `/Users/a0000/QCchem/qcchem/backends/runtime_submission.py`
  Normalize returned runtime metadata and expose enough information for dashboard comparisons.
- Modify: `/Users/a0000/QCchem/qcchem/reporting/markdown.py`
  Add `Hardware Execution` and `Calibration Summary` sections to run reports.
- Modify: `/Users/a0000/QCchem/qcchem/reporting/aggregate.py`
  Generate a dedicated hardware calibration report that compares ideal, sampled, and runtime paths.
- Modify: `/Users/a0000/QCchem/qcchem/io/exports.py`
  Include hardware metadata in `qcschema.json` extras and `result.h5`.

### Configs and benchmark definitions to create/modify

- Create: `/Users/a0000/QCchem/configs/h2_runtime_hardware_probe.yaml`
- Create: `/Users/a0000/QCchem/configs/lih_active_runtime_hardware_probe_v2.yaml`
- Modify: `/Users/a0000/QCchem/benchmarks/low_rank_suite_v1.yaml`
  Add hardware comparison case references only if they are produced successfully.
- Create: `/Users/a0000/QCchem/benchmarks/hardware_calibration_suite_v1.yaml`

### Artifact/report output paths expected

- Create at runtime: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe/`
- Create at runtime: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe_v2/`
- Create at runtime: `/Users/a0000/QCchem/artifacts/hardware_calibration_suite_v1/`

### Tests to create or extend

- Create: `/Users/a0000/QCchem/tests/unit/test_hardware_calibration_v10.py`
- Create: `/Users/a0000/QCchem/tests/integration/test_hardware_dashboard_v10.py`
- Modify: `/Users/a0000/QCchem/tests/integration/test_low_rank_calibration_v08.py`

### Docs to update

- Modify: `/Users/a0000/QCchem/README.md`
- Modify: `/Users/a0000/QCchem/docs/architecture.md`
- Modify: `/Users/a0000/QCchem/docs/roadmap.md`
- Modify: `/Users/a0000/QCchem/docs/handoff.md`
- Modify: `/Users/a0000/QCchem/docs/verified_scope.md`

---

### Task 1: Add hardware-evidence fields and calibration logic

**Files:**
- Create: `/Users/a0000/QCchem/tests/unit/test_hardware_calibration_v10.py`
- Modify: `/Users/a0000/QCchem/qcchem/core/results.py`
- Modify: `/Users/a0000/QCchem/qcchem/workflow/calibration.py`

- [ ] **Step 1: Write the failing unit tests**

```python
from qcchem.core.results import CalibrationSummary, RunResult
from qcchem.workflow.calibration import build_calibration_summary


def test_run_result_exposes_hardware_evidence_fields() -> None:
    assert "hardware_verified" in RunResult.__dataclass_fields__
    assert "hardware_evidence_tier" in RunResult.__dataclass_fields__


def test_calibration_summary_can_use_runtime_measured_values() -> None:
    summary = build_calibration_summary(
        measurement=None,
        sampled_result=None,
        benchmark=None,
        measured_wall_time_seconds=12.5,
        measured_shot_usage=4096,
        precision_target=0.1,
        achieved_error=0.02,
        estimated_measurement_cost=8000.0,
    )
    assert isinstance(summary, CalibrationSummary)
    assert summary.measured_wall_time_seconds == 12.5
    assert summary.measured_shot_usage == 4096
    assert summary.precision_target == 0.1
    assert summary.achieved_error == 0.02
```

- [ ] **Step 2: Run the unit tests to verify they fail**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/unit/test_hardware_calibration_v10.py -q`

Expected: FAIL because `RunResult` lacks the new hardware fields and `build_calibration_summary` does not yet accept explicit measured runtime values.

- [ ] **Step 3: Implement the minimal schema and calibration changes**

```python
@dataclass(slots=True)
class RunResult:
    ...
    hardware_verified: bool = False
    hardware_evidence_tier: str | None = None
```

```python
def build_calibration_summary(
    *,
    measurement,
    sampled_result,
    benchmark,
    measured_wall_time_seconds: float,
    measured_shot_usage: float | None = None,
    precision_target: float | None = None,
    achieved_error: float | None = None,
    estimated_measurement_cost: float | None = None,
) -> CalibrationSummary | None:
    ...
    return CalibrationSummary(
        available=True,
        measured_wall_time_seconds=float(measured_wall_time_seconds),
        measured_shot_usage=measured_shot_usage,
        precision_target=precision_target or derived_precision,
        achieved_error=achieved_error or derived_error,
        estimated_measurement_cost=estimated_measurement_cost or derived_cost,
        estimated_vs_measured_cost=estimated_ratio,
        reference_target=derived_target,
        notes=notes,
    )
```

- [ ] **Step 4: Re-run the unit tests**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/unit/test_hardware_calibration_v10.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/a0000/QCchem
git add tests/unit/test_hardware_calibration_v10.py qcchem/core/results.py qcchem/workflow/calibration.py
git commit -m "feat: add hardware calibration fields"
```

### Task 2: Add run-level hardware reporting and dashboard aggregation

**Files:**
- Create: `/Users/a0000/QCchem/tests/integration/test_hardware_dashboard_v10.py`
- Modify: `/Users/a0000/QCchem/qcchem/workflow/runner.py`
- Modify: `/Users/a0000/QCchem/qcchem/workflow/benchmark.py`
- Modify: `/Users/a0000/QCchem/qcchem/reporting/markdown.py`
- Modify: `/Users/a0000/QCchem/qcchem/reporting/aggregate.py`

- [ ] **Step 1: Write the failing integration tests**

```python
from pathlib import Path

from qcchem.reporting.aggregate import write_hardware_calibration_report
from qcchem.workflow.runner import run_from_config


def test_hardware_run_report_mentions_hardware_sections(tmp_path: Path) -> None:
    result = run_from_config(
        Path("/Users/a0000/QCchem/configs/lih_active_shot_runtime_ready_compressed.yaml"),
        output_dir=tmp_path / "lih_runtime_preview",
    )
    report_text = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "Hardware Execution" in report_text
    assert "Calibration Summary" in report_text


def test_hardware_dashboard_serializes_summary(tmp_path: Path) -> None:
    dashboard = {
        "cases": [
            {
                "name": "h2_runtime_probe",
                "estimated_measurement_cost": 8000,
                "measured_shot_usage": 4096,
                "measured_wall_time_seconds": 15.0,
                "achieved_error": 0.03,
                "hardware_verified": True,
            }
        ]
    }
    output = tmp_path / "hardware_dashboard.md"
    write_hardware_calibration_report(dashboard, output)
    text = output.read_text(encoding="utf-8")
    assert "estimated vs measured cost" in text.lower()
    assert "h2_runtime_probe" in text
```

- [ ] **Step 2: Run the integration tests to verify they fail**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/integration/test_hardware_dashboard_v10.py -q`

Expected: FAIL because the new report sections and hardware dashboard writer do not exist yet.

- [ ] **Step 3: Implement minimal reporting and aggregation support**

```python
def _hardware_execution_lines(result: RunResult) -> list[str]:
    if result.runtime_submission is None:
        return []
    return [
        "## Hardware Execution",
        f"- Submitted: `{result.runtime_submission.submitted}`",
        f"- Succeeded: `{result.runtime_submission.succeeded}`",
        f"- Backend: `{result.runtime_submission.backend_name}`",
        f"- Job ID: `{result.runtime_submission.job_id}`",
    ]
```

```python
def write_hardware_calibration_report(summary: dict[str, object], output_path: Path) -> None:
    lines = [
        "# Hardware Calibration Dashboard",
        "",
        "| Case | Estimated Cost | Measured Cost | Wall Time (s) | Achieved Error | Hardware Verified |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for case in summary["cases"]:
        lines.append(
            f"| {case['name']} | {case['estimated_measurement_cost']} | "
            f"{case['measured_shot_usage']} | {case['measured_wall_time_seconds']} | "
            f"{case['achieved_error']} | {case['hardware_verified']} |"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Re-run the integration tests**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/integration/test_hardware_dashboard_v10.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/a0000/QCchem
git add tests/integration/test_hardware_dashboard_v10.py qcchem/workflow/runner.py qcchem/workflow/benchmark.py qcchem/reporting/markdown.py qcchem/reporting/aggregate.py
git commit -m "feat: add hardware dashboard reporting"
```

### Task 3: Add controlled hardware configs and local preflight checks

**Files:**
- Create: `/Users/a0000/QCchem/configs/h2_runtime_hardware_probe.yaml`
- Create: `/Users/a0000/QCchem/configs/lih_active_runtime_hardware_probe_v2.yaml`
- Modify: `/Users/a0000/QCchem/tests/integration/test_low_rank_calibration_v08.py`

- [ ] **Step 1: Write the failing config-level tests**

```python
from pathlib import Path

from qcchem.io.config import load_run_spec


def test_h2_hardware_probe_config_has_runtime_submission_enabled() -> None:
    spec = load_run_spec(Path("/Users/a0000/QCchem/configs/h2_runtime_hardware_probe.yaml"))
    assert spec.backend.runtime.enabled is True
    assert spec.backend.runtime.options["submit_real_job"] is True


def test_lih_hardware_probe_v2_config_uses_compression() -> None:
    spec = load_run_spec(Path("/Users/a0000/QCchem/configs/lih_active_runtime_hardware_probe_v2.yaml"))
    assert spec.problem.compression.enabled is True
    assert spec.problem.measurement.strategy == "low_rank_commuting"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/integration/test_low_rank_calibration_v08.py -q`

Expected: FAIL because the new config files do not exist and the current tests do not cover them.

- [ ] **Step 3: Add the minimal configs**

```yaml
molecule:
  name: H2-runtime-hardware-probe
  geometry:
    - symbol: H
      coords: [0.0, 0.0, 0.0]
    - symbol: H
      coords: [0.0, 0.0, 0.74]
  charge: 0
  multiplicity: 1
  basis: sto3g

backend:
  kind: shot_estimator
  shots: 512
  repetitions: 1
  runtime:
    enabled: true
    runtime_ready: true
    session_ready: true
    options:
      backend_name: ibm_fez
      submit_real_job: true
      wait_for_result: true
```

```yaml
problem:
  freeze_core: true
  active_space:
    selection_mode: manual
    num_electrons: 2
    num_spatial_orbitals: 2
    active_orbitals: [1, 2]
  compression:
    enabled: true
    method: modified_cholesky
    threshold: 1.0e-3
    max_rank: 2
    execution_enabled: true
  measurement:
    strategy: low_rank_commuting
    runtime_precision_target: 0.15
```

- [ ] **Step 4: Re-run the config tests**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/integration/test_low_rank_calibration_v08.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/a0000/QCchem
git add configs/h2_runtime_hardware_probe.yaml configs/lih_active_runtime_hardware_probe_v2.yaml tests/integration/test_low_rank_calibration_v08.py
git commit -m "feat: add hardware probe configs"
```

### Task 4: Run the H2 hardware probe with a strict budget gate

**Files:**
- Runtime output: `/Users/a0000/QCchem/artifacts/h2_runtime_hardware_probe/`

- [ ] **Step 1: Dry-run locally without a remote submit**

```bash
cd /Users/a0000/QCchem
python - <<'PY'
from pathlib import Path
import yaml

path = Path("configs/h2_runtime_hardware_probe.yaml")
data = yaml.safe_load(path.read_text())
data["backend"]["runtime"]["options"]["submit_real_job"] = False
preview = Path("configs/.tmp_h2_runtime_preview.yaml")
preview.write_text(yaml.safe_dump(data), encoding="utf-8")
print(preview)
PY
```

- [ ] **Step 2: Run the local preview to verify the workflow and artifact shape**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m qcchem.cli.main run -c configs/.tmp_h2_runtime_preview.yaml`

Expected: PASS with a local artifact and a `runtime_submission` section showing submission disabled rather than a hard failure.

- [ ] **Step 3: Submit the real H2 hardware job**

```bash
cd /Users/a0000/QCchem
conda run -n qiskit python -m qcchem.cli.main run -c configs/h2_runtime_hardware_probe.yaml
```

- [ ] **Step 4: Verify the hardware artifact contents**

Run: `cd /Users/a0000/QCchem && python3 - <<'PY'
from pathlib import Path
import json

result = json.loads(Path("artifacts/h2_runtime_hardware_probe/result.json").read_text())
assert result["runtime_submission"]["submitted"] is True
assert result["runtime_submission"]["job_id"]
assert "calibration" in result
print(result["runtime_submission"]["job_id"])
PY`

Expected: PASS and print a non-empty job id.

- [ ] **Step 5: Commit config/report-side changes only**

```bash
cd /Users/a0000/QCchem
git add configs/h2_runtime_hardware_probe.yaml
git commit -m "feat: add h2 hardware probe workflow"
```

### Task 5: Run the LiH active-space compressed hardware probe and build the dashboard

**Files:**
- Runtime output: `/Users/a0000/QCchem/artifacts/lih_active_runtime_hardware_probe_v2/`
- Create: `/Users/a0000/QCchem/benchmarks/hardware_calibration_suite_v1.yaml`

- [ ] **Step 1: Add the failing dashboard benchmark test**

```python
from pathlib import Path
import json


def test_hardware_suite_summary_can_be_written(tmp_path: Path) -> None:
    summary_path = tmp_path / "hardware_calibration_summary.json"
    payload = {
        "cases": [
            {"name": "h2_runtime_probe", "hardware_verified": True},
            {"name": "lih_runtime_probe", "hardware_verified": False},
        ]
    }
    summary_path.write_text(json.dumps(payload), encoding="utf-8")
    loaded = json.loads(summary_path.read_text())
    assert len(loaded["cases"]) == 2
```

- [ ] **Step 2: Run the test to verify it fails in context**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/integration/test_hardware_dashboard_v10.py -q`

Expected: FAIL until the benchmark writer persists the summary and report in the expected location.

- [ ] **Step 3: Submit the real LiH hardware probe**

```bash
cd /Users/a0000/QCchem
conda run -n qiskit python -m qcchem.cli.main run -c configs/lih_active_runtime_hardware_probe_v2.yaml
```

- [ ] **Step 4: Generate the hardware suite summary and report**

```bash
cd /Users/a0000/QCchem
conda run -n qiskit python - <<'PY'
from pathlib import Path
from qcchem.workflow.benchmark import build_hardware_calibration_suite

build_hardware_calibration_suite(
    [
        Path("artifacts/h2_runtime_hardware_probe/result.json"),
        Path("artifacts/lih_active_runtime_hardware_probe_v2/result.json"),
    ],
    output_root=Path("artifacts/hardware_calibration_suite_v1"),
)
PY
```

- [ ] **Step 5: Verify the suite artifacts**

Run: `cd /Users/a0000/QCchem && python3 - <<'PY'
from pathlib import Path
for name in [
    "artifacts/hardware_calibration_suite_v1/hardware_calibration_summary.json",
    "artifacts/hardware_calibration_suite_v1/hardware_calibration_report.md",
]:
    path = Path(name)
    assert path.exists(), name
    print(name)
PY`

Expected: PASS and print both files.

- [ ] **Step 6: Commit the benchmark wiring**

```bash
cd /Users/a0000/QCchem
git add benchmarks/hardware_calibration_suite_v1.yaml qcchem/workflow/benchmark.py
git commit -m "feat: add hardware calibration dashboard"
```

### Task 6: Update docs, exports, and run the full verification pass

**Files:**
- Modify: `/Users/a0000/QCchem/qcchem/io/exports.py`
- Modify: `/Users/a0000/QCchem/README.md`
- Modify: `/Users/a0000/QCchem/docs/architecture.md`
- Modify: `/Users/a0000/QCchem/docs/roadmap.md`
- Modify: `/Users/a0000/QCchem/docs/handoff.md`
- Modify: `/Users/a0000/QCchem/docs/verified_scope.md`

- [ ] **Step 1: Write the failing documentation/export tests**

```python
from pathlib import Path


def test_verified_scope_mentions_hardware_verified_boundary() -> None:
    text = Path("/Users/a0000/QCchem/docs/verified_scope.md").read_text(encoding="utf-8")
    assert "hardware-verified" in text


def test_readme_mentions_h2_and_lih_hardware_probes() -> None:
    text = Path("/Users/a0000/QCchem/README.md").read_text(encoding="utf-8")
    assert "h2_runtime_hardware_probe" in text
    assert "lih_active_runtime_hardware_probe_v2" in text
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/integration/test_hardware_dashboard_v10.py tests/unit/test_hardware_calibration_v10.py -q`

Expected: FAIL until the docs and export paths mention the new hardware scope and files.

- [ ] **Step 3: Update docs and exports**

```python
extras["hardware_execution"] = {
    "hardware_verified": result.hardware_verified,
    "hardware_evidence_tier": result.hardware_evidence_tier,
    "runtime_submission": to_primitive(result.runtime_submission),
    "calibration": to_primitive(result.calibration),
}
```

```markdown
## Hardware-Verified Scope

- `h2_runtime_hardware_probe`
- `lih_active_runtime_hardware_probe_v2`
- `hardware_calibration_suite_v1`
```

- [ ] **Step 4: Run the focused verification suite**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/unit/test_hardware_calibration_v10.py tests/integration/test_hardware_dashboard_v10.py tests/integration/test_low_rank_calibration_v08.py -q`

Expected: PASS

- [ ] **Step 5: Run the full regression suite**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/a0000/QCchem
git add qcchem/io/exports.py README.md docs/architecture.md docs/roadmap.md docs/handoff.md docs/verified_scope.md
git commit -m "docs: add hardware verification scope"
```

---

## Hardware Execution Guardrails

- Always run the local preview path before each new real-runtime submission.
- Prefer `ibm_fez` first only if queue remains zero or near zero; otherwise choose the least queued open backend.
- Stop after the first successful artifact for each target case unless the result is clearly malformed.
- Use at most one reserve rerun for `H2` and one reserve rerun for `LiH`.
- Do not spend runtime minutes on exploratory solvers in this phase.

## Self-Review

- Spec coverage:
  - `H2 hardware probe`: covered in Task 4
  - `LiH active-space compressed hardware probe`: covered in Task 5
  - `hardware calibration/dashboard`: covered in Tasks 1, 2, 5, and 6
  - docs and boundary updates: covered in Task 6
- Placeholder scan:
  - No `TODO`, `TBD`, or “implement later” placeholders remain.
- Type consistency:
  - `hardware_verified`, `hardware_evidence_tier`, and calibration fields use the same names throughout the plan.
