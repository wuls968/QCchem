# QCchem Qwen Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the mature parts of the qwen QCchem branch into the main QCchem codebase, while preserving experimental algorithms behind an explicit exploratory boundary with consistent schema, artifact, report, CLI, and test behavior.

**Architecture:** Keep the current QCchem run/study/benchmark/scan architecture intact. Add only a thin exploratory boundary at the schema, CLI, workflow, and reporting layers; merge mature utilities like chemical-accuracy checks, reduction planning, and safe policy resolution into the existing core path; migrate solver and mitigation experiments into `qcchem/exploratory/` so they can evolve without contaminating the validated path.

**Tech Stack:** Python, Qiskit, Qiskit Nature, primitives V2, PySCF, pytest, JSON/YAML, optional HDF5, existing QCchem CLI/reporting stack

---

## File Map

### Core files to modify

- Modify: `/Users/a0000/QCchem/qcchem/core/specs.py`
  Add exploratory gating fields plus safe reduction/policy spec fields.
- Modify: `/Users/a0000/QCchem/qcchem/core/results.py`
  Add module-origin, capability-tier, verification-notes, scientific-risk metadata, and reduction/policy result sections.
- Modify: `/Users/a0000/QCchem/qcchem/core/__init__.py`
  Export new spec/result models.
- Modify: `/Users/a0000/QCchem/qcchem/io/config.py`
  Parse new exploratory / policy / reduction fields safely from YAML.
- Modify: `/Users/a0000/QCchem/qcchem/workflow/runner.py`
  Enforce gating, attach reduction plan / policy / chemical accuracy summaries, and keep validated path behavior stable.
- Modify: `/Users/a0000/QCchem/qcchem/reporting/markdown.py`
  Add validation-boundary sections and mixed-scope reporting.
- Modify: `/Users/a0000/QCchem/qcchem/reporting/aggregate.py`
  Separate validated and exploratory summaries in aggregate reports.
- Modify: `/Users/a0000/QCchem/qcchem/cli/main.py`
  Add `qcchem exploratory ...` entrypoints and safe rejection from standard commands.

### New core files to create

- Create: `/Users/a0000/QCchem/qcchem/core/chemical_accuracy.py`
  Unified chemical-accuracy helper aligned with `BenchmarkSummary`.
- Create: `/Users/a0000/QCchem/qcchem/chem/reduction_planner.py`
  Safe reduction recommendation layer built on existing active-space audit.
- Create: `/Users/a0000/QCchem/qcchem/backends/policy_engine.py`
  Safe preset resolution layer that never overrides explicit user settings.

### New exploratory package files to create

- Create: `/Users/a0000/QCchem/qcchem/exploratory/__init__.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/solvers/__init__.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/solvers/registry.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/solvers/adapt_vqe.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/solvers/vqd.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/solvers/qse.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/solvers/iqpe.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/solvers/folded_spectrum.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/mitigation/__init__.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/mitigation/readout.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/mitigation/zne.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/mitigation/cdr.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/mitigation/symmetry_verify.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/benchmarks/__init__.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/benchmarks/suite_definitions.py`

### Tests to create

- Create: `/Users/a0000/QCchem/tests/unit/test_qwen_integration_spec_v09.py`
- Create: `/Users/a0000/QCchem/tests/integration/test_qwen_core_integration_v09.py`
- Create: `/Users/a0000/QCchem/tests/integration/test_exploratory_cli_v09.py`
- Create: `/Users/a0000/QCchem/tests/exploratory/test_exploratory_solvers_v09.py`
- Create: `/Users/a0000/QCchem/tests/exploratory/test_exploratory_mitigation_v09.py`

### Docs to update

- Modify: `/Users/a0000/QCchem/README.md`
- Modify: `/Users/a0000/QCchem/docs/architecture.md`
- Modify: `/Users/a0000/QCchem/docs/roadmap.md`
- Modify: `/Users/a0000/QCchem/docs/handoff.md`
- Modify: `/Users/a0000/QCchem/docs/verified_scope.md`

---

### Task 1: Add schema and config gating for exploratory boundaries

**Files:**
- Create: `/Users/a0000/QCchem/tests/unit/test_qwen_integration_spec_v09.py`
- Modify: `/Users/a0000/QCchem/qcchem/core/specs.py`
- Modify: `/Users/a0000/QCchem/qcchem/core/results.py`
- Modify: `/Users/a0000/QCchem/qcchem/core/__init__.py`
- Modify: `/Users/a0000/QCchem/qcchem/io/config.py`

- [ ] **Step 1: Write the failing spec/config tests**

```python
from pathlib import Path

import yaml

from qcchem.io.config import load_run_spec


def test_run_spec_parses_exploratory_gate(tmp_path: Path) -> None:
    config = {
        "molecule": {
            "name": "H2",
            "geometry": [
                {"symbol": "H", "coords": [0.0, 0.0, 0.0]},
                {"symbol": "H", "coords": [0.0, 0.0, 0.74]},
            ],
        },
        "solver": {
            "kind": "vqd",
            "experimental": True,
        },
        "policy": {
            "name": "benchmark",
            "allow_exploratory": True,
        },
        "exploratory": {
            "enabled": True,
            "modules": ["solvers.vqd"],
            "notes": ["manual opt-in"],
        },
    }
    path = tmp_path / "exploratory.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")

    spec = load_run_spec(path)

    assert spec.solver.experimental is True
    assert spec.policy.allow_exploratory is True
    assert spec.exploratory.enabled is True
    assert spec.exploratory.modules == ["solvers.vqd"]


def test_run_result_defaults_keep_core_origin() -> None:
    from qcchem.core.results import RunResult

    assert "module_origin" in RunResult.__dataclass_fields__
    assert "capability_tier" in RunResult.__dataclass_fields__
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/unit/test_qwen_integration_spec_v09.py -q`

Expected: FAIL with missing `experimental`, `allow_exploratory`, `exploratory`, `module_origin`, or `capability_tier` fields.

- [ ] **Step 3: Add minimal schema/config support**

```python
@dataclass(slots=True)
class ExploratorySpec:
    enabled: bool = False
    modules: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SolverSpec:
    kind: str = "vqe"
    optimizer: OptimizerSpec = field(default_factory=OptimizerSpec)
    ansatz: AnsatzSpec = field(default_factory=AnsatzSpec)
    initial_point: str | list[float] = "zeros"
    experimental: bool = False


@dataclass(slots=True)
class PolicySpec:
    name: str = "benchmark"
    allow_exploratory: bool = False


@dataclass(slots=True)
class RunSpec:
    ...
    exploratory: ExploratorySpec = field(default_factory=ExploratorySpec)
```

```python
@dataclass(slots=True)
class RunResult:
    ...
    module_origin: str = "core"
    capability_tier: str = "validated"
    verification_notes: list[str] = field(default_factory=list)
    scientific_risk_notes: list[str] = field(default_factory=list)
```

- [ ] **Step 4: Re-run the unit test**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/unit/test_qwen_integration_spec_v09.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/a0000/QCchem
git add tests/unit/test_qwen_integration_spec_v09.py qcchem/core/specs.py qcchem/core/results.py qcchem/core/__init__.py qcchem/io/config.py
git commit -m "feat: add exploratory schema boundary"
```

### Task 2: Integrate chemical accuracy, reduction planner, and safe policy resolution into the core path

**Files:**
- Create: `/Users/a0000/QCchem/tests/integration/test_qwen_core_integration_v09.py`
- Create: `/Users/a0000/QCchem/qcchem/core/chemical_accuracy.py`
- Create: `/Users/a0000/QCchem/qcchem/chem/reduction_planner.py`
- Create: `/Users/a0000/QCchem/qcchem/backends/policy_engine.py`
- Modify: `/Users/a0000/QCchem/qcchem/core/results.py`
- Modify: `/Users/a0000/QCchem/qcchem/core/__init__.py`
- Modify: `/Users/a0000/QCchem/qcchem/workflow/runner.py`
- Modify: `/Users/a0000/QCchem/qcchem/reporting/markdown.py`

- [ ] **Step 1: Write the failing integration tests**

```python
from pathlib import Path

from qcchem.workflow.runner import run_from_config


def test_run_result_contains_policy_and_reduction_plan() -> None:
    result = run_from_config(Path("/Users/a0000/QCchem/configs/lih_active_vqe.yaml"))

    assert result.policy_engine is not None
    assert result.reduction_plan is not None
    assert result.chemical_accuracy is not None
    assert result.policy_engine.policy_name == "benchmark"


def test_report_mentions_validation_boundary_and_chemical_accuracy(tmp_path: Path) -> None:
    result = run_from_config(Path("/Users/a0000/QCchem/configs/h2.yaml"), output_dir=tmp_path / "h2_core")
    report_text = result.artifacts.report_markdown.read_text(encoding="utf-8")

    assert "Validation Boundary" in report_text
    assert "Chemical Accuracy" in report_text
```

- [ ] **Step 2: Run the integration test to verify it fails**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/integration/test_qwen_core_integration_v09.py -q`

Expected: FAIL because `policy_engine`, `reduction_plan`, or `chemical_accuracy` sections do not yet exist.

- [ ] **Step 3: Implement safe core integrations**

```python
def check_chemical_accuracy(
    computed_energy: float,
    reference_energy: float | None,
    *,
    threshold_hartree: float = 1.6e-3,
    statistical_error: float | None = None,
) -> ChemicalAccuracyReport:
    absolute_error = None if reference_energy is None else abs(computed_energy - reference_energy)
    meets = None if absolute_error is None else absolute_error <= threshold_hartree
    return ChemicalAccuracyReport(
        meets_chemical_accuracy=meets,
        absolute_error_hartree=absolute_error,
        threshold_hartree=threshold_hartree,
        statistical_error=statistical_error,
    )
```

```python
def resolve_policy(spec: RunSpec) -> PolicyEngineResult:
    preset = POLICY_PRESETS.get(spec.policy.name, {})
    resolved = _spec_to_dict(spec)
    overrides_applied: list[str] = []
    for key, value in preset.items():
        if _path_is_unset(spec, key):
            _set_nested_value(resolved, key, value)
            overrides_applied.append(key)
    return PolicyEngineResult(
        policy_name=spec.policy.name,
        resolved_policy=resolved,
        overrides_applied=overrides_applied,
        presets_used=[spec.policy.name] if spec.policy.name in POLICY_PRESETS else [],
    )
```

```python
reduction_plan = build_reduction_plan(...)
chemical_accuracy = check_chemical_accuracy(
    total_energy,
    exact_baseline.total_energy if exact_baseline.available else None,
    statistical_error=sampled_result.standard_error if sampled_result else None,
)
```

- [ ] **Step 4: Re-run the targeted integration tests**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/integration/test_qwen_core_integration_v09.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/a0000/QCchem
git add tests/integration/test_qwen_core_integration_v09.py qcchem/core/chemical_accuracy.py qcchem/chem/reduction_planner.py qcchem/backends/policy_engine.py qcchem/core/results.py qcchem/core/__init__.py qcchem/workflow/runner.py qcchem/reporting/markdown.py
git commit -m "feat: integrate qwen core planning utilities"
```

### Task 3: Add exploratory package scaffolding and CLI gating

**Files:**
- Create: `/Users/a0000/QCchem/tests/integration/test_exploratory_cli_v09.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/__init__.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/solvers/__init__.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/mitigation/__init__.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/benchmarks/__init__.py`
- Modify: `/Users/a0000/QCchem/qcchem/cli/main.py`
- Modify: `/Users/a0000/QCchem/qcchem/workflow/runner.py`

- [ ] **Step 1: Write the failing CLI gating tests**

```python
from pathlib import Path

from qcchem.cli.main import main


def test_standard_run_rejects_exploratory_config(tmp_path: Path) -> None:
    config = tmp_path / "exploratory.yaml"
    config.write_text(
        '''
        molecule:
          name: H2
          geometry:
            - {symbol: H, coords: [0.0, 0.0, 0.0]}
            - {symbol: H, coords: [0.0, 0.0, 0.74]}
        solver:
          kind: vqd
          experimental: true
        ''',
        encoding="utf-8",
    )

    exit_code = main(["run", "-c", str(config)])
    assert exit_code == 2


def test_exploratory_command_accepts_experimental_solver(tmp_path: Path) -> None:
    from qcchem.cli.main import _build_parser

    parser = _build_parser()
    args = parser.parse_args(["exploratory", "run", "-c", "dummy.yaml"])
    assert args.command == "exploratory"
```

- [ ] **Step 2: Run the CLI test to verify it fails**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/integration/test_exploratory_cli_v09.py -q`

Expected: FAIL because the CLI has no exploratory command group and standard run does not reject exploratory configs.

- [ ] **Step 3: Add scaffolding and gating**

```python
def _ensure_exploratory_allowed(spec: RunSpec, *, exploratory_command: bool) -> None:
    requested = spec.solver.experimental or spec.exploratory.enabled
    if requested and not (exploratory_command or spec.policy.allow_exploratory):
        raise ValueError(
            "Exploratory modules require qcchem exploratory ... or policy.allow_exploratory=true"
        )
```

```python
exploratory_parser = subparsers.add_parser("exploratory", help="Exploratory workflow commands.")
exploratory_subparsers = exploratory_parser.add_subparsers(dest="exploratory_command", required=True)
exploratory_run = exploratory_subparsers.add_parser("run", help="Run an exploratory QCchem calculation.")
exploratory_run.add_argument("-c", "--config", type=Path, required=True)
exploratory_run.add_argument("-o", "--output-dir", type=Path)
```

- [ ] **Step 4: Re-run the targeted CLI tests**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/integration/test_exploratory_cli_v09.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/a0000/QCchem
git add tests/integration/test_exploratory_cli_v09.py qcchem/exploratory/__init__.py qcchem/exploratory/solvers/__init__.py qcchem/exploratory/mitigation/__init__.py qcchem/exploratory/benchmarks/__init__.py qcchem/cli/main.py qcchem/workflow/runner.py
git commit -m "feat: add exploratory boundary and cli"
```

### Task 4: Migrate exploratory solver skeletons into isolated modules

**Files:**
- Create: `/Users/a0000/QCchem/tests/exploratory/test_exploratory_solvers_v09.py`
- Create: `/Users/a0000/QCchem/configs/exploratory/h2_vqd.yaml`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/solvers/registry.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/solvers/adapt_vqe.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/solvers/vqd.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/solvers/qse.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/solvers/iqpe.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/solvers/folded_spectrum.py`
- Modify: `/Users/a0000/QCchem/qcchem/workflow/runner.py`

- [ ] **Step 1: Write the failing exploratory solver smoke tests**

```python
from qcchem.exploratory.solvers.registry import get_exploratory_solver


def test_vqd_solver_is_registered_as_exploratory() -> None:
    solver_cls, metadata = get_exploratory_solver("vqd")
    assert solver_cls is not None
    assert metadata["module_origin"] == "exploratory"
    assert metadata["capability_tier"] == "exploratory"


def test_exploratory_solver_metadata_contains_scientific_risk_notes() -> None:
    _, metadata = get_exploratory_solver("qse")
    assert metadata["scientific_risk_notes"]
```

- [ ] **Step 2: Run the exploratory solver tests to verify they fail**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/exploratory/test_exploratory_solvers_v09.py -q`

Expected: FAIL because the exploratory solver registry does not yet exist.

- [ ] **Step 3: Implement isolated solver registry and skeleton wrappers**

```python
EXPLORATORY_SOLVERS = {
    "adapt_vqe": {
        "loader": "qcchem.exploratory.solvers.adapt_vqe:build_solver",
        "module_origin": "exploratory",
        "capability_tier": "exploratory",
        "scientific_risk_notes": [
            "Adaptive excitation pool is not part of the validated QCchem benchmark path."
        ],
    },
    "vqd": {
        "loader": "qcchem.exploratory.solvers.vqd:build_solver",
        "module_origin": "exploratory",
        "capability_tier": "exploratory",
        "scientific_risk_notes": [
            "Overlap penalty and excited-state accuracy remain exploratory."
        ],
    },
    "qse": {
        "loader": "qcchem.exploratory.solvers.qse:build_solver",
        "module_origin": "exploratory",
        "capability_tier": "exploratory",
        "scientific_risk_notes": [
            "Subspace construction is retained as exploratory until matrix elements are re-validated."
        ],
    },
}
```

```python
class ExploratoryVQDSolver(BaseSolver):
    def solve(self, operator):
        outcome = self._delegate.solve(operator)
        outcome.metadata.setdefault("module_origin", "exploratory")
        outcome.metadata.setdefault("validation_scope", "exploratory excited-state skeleton")
        outcome.metadata.setdefault(
            "scientific_risk_notes",
            ["Do not treat this as a validated excited-state benchmark."],
        )
        return outcome
```

- [ ] **Step 4: Re-run the exploratory solver tests**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/exploratory/test_exploratory_solvers_v09.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/a0000/QCchem
git add tests/exploratory/test_exploratory_solvers_v09.py configs/exploratory/h2_vqd.yaml qcchem/exploratory/solvers/registry.py qcchem/exploratory/solvers/adapt_vqe.py qcchem/exploratory/solvers/vqd.py qcchem/exploratory/solvers/qse.py qcchem/exploratory/solvers/iqpe.py qcchem/exploratory/solvers/folded_spectrum.py qcchem/workflow/runner.py
git commit -m "feat: isolate exploratory solver skeletons"
```

### Task 5: Migrate exploratory mitigation and benchmark definitions with explicit risk labeling

**Files:**
- Create: `/Users/a0000/QCchem/tests/exploratory/test_exploratory_mitigation_v09.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/mitigation/readout.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/mitigation/zne.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/mitigation/cdr.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/mitigation/symmetry_verify.py`
- Create: `/Users/a0000/QCchem/qcchem/exploratory/benchmarks/suite_definitions.py`
- Modify: `/Users/a0000/QCchem/qcchem/reporting/aggregate.py`

- [ ] **Step 1: Write the failing exploratory mitigation/benchmark tests**

```python
from qcchem.exploratory.benchmarks.suite_definitions import EXPLORATORY_SUITES


def test_exploratory_benchmark_suites_are_not_validated() -> None:
    assert EXPLORATORY_SUITES["spectroscopy_v1"]["scope"] == "exploratory"
    assert EXPLORATORY_SUITES["strong_correlation_v1"]["scope"] == "exploratory"


def test_exploratory_mitigation_metadata_declares_risk() -> None:
    from qcchem.exploratory.mitigation.readout import READOUT_EXPLORATORY_METADATA

    assert READOUT_EXPLORATORY_METADATA["module_origin"] == "exploratory"
    assert READOUT_EXPLORATORY_METADATA["scientific_risk_notes"]
```

- [ ] **Step 2: Run the exploratory mitigation test to verify it fails**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/exploratory/test_exploratory_mitigation_v09.py -q`

Expected: FAIL because the exploratory mitigation package and suite definitions do not exist.

- [ ] **Step 3: Implement exploratory mitigation metadata and suite separation**

```python
READOUT_EXPLORATORY_METADATA = {
    "module_origin": "exploratory",
    "capability_tier": "exploratory",
    "validation_scope": "general observable readout correction",
    "scientific_risk_notes": [
        "Current implementation is not validated for arbitrary non-diagonal observables."
    ],
}
```

```python
EXPLORATORY_SUITES = {
    "spectroscopy_v1": {
        "scope": "exploratory",
        "description": "Exploratory spectroscopy cases kept outside the validated benchmark suite.",
        "default_status": "exploratory",
    },
    "strong_correlation_v1": {
        "scope": "exploratory",
        "description": "Exploratory strong-correlation stress cases.",
        "default_status": "exploratory",
    },
}
```

- [ ] **Step 4: Re-run the exploratory mitigation tests**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/exploratory/test_exploratory_mitigation_v09.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/a0000/QCchem
git add tests/exploratory/test_exploratory_mitigation_v09.py qcchem/exploratory/mitigation/readout.py qcchem/exploratory/mitigation/zne.py qcchem/exploratory/mitigation/cdr.py qcchem/exploratory/mitigation/symmetry_verify.py qcchem/exploratory/benchmarks/suite_definitions.py qcchem/reporting/aggregate.py
git commit -m "feat: separate exploratory mitigation and benchmark suites"
```

### Task 6: Update reports, docs, and full-suite verification for mixed validated/exploratory scope

**Files:**
- Modify: `/Users/a0000/QCchem/qcchem/reporting/markdown.py`
- Modify: `/Users/a0000/QCchem/qcchem/reporting/aggregate.py`
- Modify: `/Users/a0000/QCchem/README.md`
- Modify: `/Users/a0000/QCchem/docs/architecture.md`
- Modify: `/Users/a0000/QCchem/docs/roadmap.md`
- Modify: `/Users/a0000/QCchem/docs/handoff.md`
- Modify: `/Users/a0000/QCchem/docs/verified_scope.md`

- [ ] **Step 1: Write the failing mixed-scope report test**

```python
from pathlib import Path

from qcchem.workflow.runner import run_from_config


def test_exploratory_report_declares_boundary(tmp_path: Path) -> None:
    config = tmp_path / "exploratory.yaml"
    config.write_text(
        '''
        molecule:
          name: H2
          geometry:
            - {symbol: H, coords: [0.0, 0.0, 0.0]}
            - {symbol: H, coords: [0.0, 0.0, 0.74]}
        solver:
          kind: vqd
          experimental: true
        policy:
          name: benchmark
          allow_exploratory: true
        exploratory:
          enabled: true
          modules: ["solvers.vqd"]
        ''',
        encoding="utf-8",
    )
    result = run_from_config(config, output_dir=tmp_path / "exploratory_report")
    text = result.artifacts.report_markdown.read_text(encoding="utf-8")
    assert "Validation Boundary" in text
    assert "Module Origin" in text
```

- [ ] **Step 2: Run the report test to verify it fails**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest tests/integration/test_qwen_core_integration_v09.py tests/integration/test_exploratory_cli_v09.py tests/exploratory/test_exploratory_solvers_v09.py tests/exploratory/test_exploratory_mitigation_v09.py -q`

Expected: FAIL with missing mixed-scope reporting text or missing exploratory boundary handling.

- [ ] **Step 3: Implement report and doc updates**

```python
lines.extend([
    "## Validation Boundary",
    f"- Capability tier: `{result.capability_tier}`",
    f"- Module origin: `{result.module_origin}`",
])
for note in result.verification_notes:
    lines.append(f"- Verification note: {note}")
for note in result.scientific_risk_notes:
    lines.append(f"- Scientific risk: {note}")
```

```markdown
## Validated vs Exploratory

- Validated QCchem paths remain the default for `qcchem run`, study, benchmark, and scan.
- Exploratory algorithms are opt-in via `qcchem exploratory ...` or explicit config gating.
- Exploratory artifacts are retained for research iteration but are excluded from validated benchmark summaries by default.
```

- [ ] **Step 4: Run the full verification set**

Run: `cd /Users/a0000/QCchem && conda run -n qiskit python -m pytest -q`

Expected: PASS with the existing validated suite still green and the new exploratory tests green.

- [ ] **Step 5: Commit**

```bash
cd /Users/a0000/QCchem
git add qcchem/reporting/markdown.py qcchem/reporting/aggregate.py README.md docs/architecture.md docs/roadmap.md docs/handoff.md docs/verified_scope.md
git add tests/unit/test_qwen_integration_spec_v09.py tests/integration/test_qwen_core_integration_v09.py tests/integration/test_exploratory_cli_v09.py tests/exploratory/test_exploratory_solvers_v09.py tests/exploratory/test_exploratory_mitigation_v09.py
git commit -m "docs: clarify validated and exploratory integration scope"
```
