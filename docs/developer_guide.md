# QCchem Developer Guide

This guide captures the release-hardening practices for QCchem contributors.

## Working Tree Hygiene

Generated local outputs should not be committed unless they are curated release
fixtures. The following are intentionally ignored:

- `.superpowers/`
- `artifacts/lr_ace_local_molecule_sweep_*/`
- `artifacts/release_audit/`
- `artifacts/**/preview_local/`

When running tests, make sure tracked curated artifacts are not rewritten:

```bash
git diff --name-only -- artifacts/lih_active_vqe
```

The command should print nothing.

## Test Layers

Targeted release checks:

```bash
python -m pytest tests/integration/test_qwen_core_integration_v09.py -q
python -m pytest tests/unit/test_release_audit_v23.py -q
python -m pytest tests/integration/test_release_audit_workflow_v23.py -q
python -m pytest tests/integration/test_lattice_qed_workflow_v20.py tests/integration/test_lattice_qed_dynamics_workflow_v21.py tests/integration/test_lattice_qed_sparse_engine_workflow_v22.py -q
python -m pytest tests/unit/test_lattice_qed_sparse_engine_v22.py tests/unit/test_lattice_qed_sector_first_builder.py tests/unit/test_field_model_qft_benchmark_configs.py -q
python -m pytest tests/integration/test_lr_ace_workflow_v19.py tests/integration/test_tc_qsci_workflow.py -q
```

Default suite:

```bash
python -m pytest -q
```

`pyproject.toml` excludes tests marked `slow` from the default gate. Slow tests
are exploratory stress checks, not deleted coverage. Run them explicitly when
validating long LR-ACE/adaptive or other stress surfaces:

```bash
python -m pytest -m slow -q
```

Static/hygiene checks:

```bash
python -m compileall -q qcchem
git diff --check
git status --short
```

CUDA-Q/MKL-Q optional backend checks:

```bash
PYTHONPATH=/Users/a0000/.cudaq-mklq /opt/anaconda3/bin/python3 -m pytest tests/unit/test_cudaq_backend.py -q
PYTHONPATH=/Users/a0000/.cudaq-mklq /opt/anaconda3/bin/python3 -m pytest tests/integration/test_cudaq_mklq_workflow.py -q
PYTHONPATH=/Users/a0000/.cudaq-mklq /opt/anaconda3/bin/python3 -m qcchem.cli.main run -c configs/h2_cudaq_mklq_cpu.yaml -o /tmp/qcchem-mklq-cpu-smoke
```

The local MKL-Q prefix currently targets CPython 3.12 on this Mac. Treat
`mklq-metal` as experimental mixed Metal/CPU smoke evidence and keep
`hardware_verified` false unless a real Runtime/QPU result is collected through
the runtime sidecar path.

## Warning Policy

Known dependency deprecations from Qiskit and Qiskit Aer are filtered in
`pyproject.toml` so the test summary stays readable. Do not blanket-ignore all
warnings. Add filters only when the warning is external, understood, and noisy
enough to hide project failures.

Current filtered warnings cover:

- `DAGCircuit.duration`
- `DAGCircuit.unit`
- `Instruction.condition`
- `qiskit.providers.models`
- `NLocal`

## Artifact Isolation In Tests

Tests that call `run_from_config` or `run_spec` should pass a `tmp_path` output
directory unless the test is intentionally reading a curated fixture.

Preferred:

```python
result = run_from_config(
    REPO_ROOT / "configs" / "h2.yaml",
    output_dir=tmp_path / "h2",
)
```

Avoid:

```python
result = run_from_config(REPO_ROOT / "configs" / "h2.yaml")
```

The second form writes to the config's default artifact directory and can dirty
the repository.

## Public Compatibility Rules

Keep these entrypoints stable unless a migration is explicitly planned:

- `qcchem run`
- `qcchem exploratory run`
- `qcchem release audit`
- `run_from_config`
- `run_spec`
- existing `result.json` field names

Custom workflow compatibility:

- Keep `qcchem workflow validate/run/report/plugins/template` additive and
  backward-compatible within workflow `version: "1"`.
- Keep the `qcchem.workflow_steps` entry point group stable for plugin authors.
- A workflow plugin should expose a class with `describe()`, `validate()`, and
  `run()`; `plan_next()` is optional and may only return step definitions that
  the central runner validates before execution.
- Do not let plugin code bypass runtime or hardware confirmation gates. Installed
  plugins are trusted local Python code, but QCchem artifacts must still record
  package metadata, step outputs, workflow limits, and provenance.
- Tests for new workflow steps should cover YAML loading, reference resolution,
  CLI execution, artifact bundle creation, and failure policy behavior.

New result sections should be additive and nullable where practical.

## Exploratory Boundary Rules

QFT, LR-ACE, and TC-QSCI may produce normal artifacts, reports, and workbench
views. They must remain behind the exploratory boundary unless a dedicated
validation plan adds stronger acceptance criteria.

Do not promote an exploratory algorithm by changing docs alone. Promotion
requires tests, release audit changes, benchmark evidence, and a clear public
scope statement.

For finite-cutoff lattice-QED sparse exact work:

- Keep the solver boundary separate from output/report changes. Most trust fixes
  should live in result structure, `quantum_evidence`, reports, and tests.
- Preserve the three-layer accuracy contract:
  `finite_model_exactness`, `continuum_chemistry_accuracy`, and
  `hardware_accuracy`.
- If `pauli_materialization=skipped`, emit `pauli_terms_available: false` and an
  empty Pauli-term list. Do not create an identity Pauli term to satisfy an old
  schema path.
- Measurement group counts and shot-cost estimates on sparse projected paths
  must be labeled as sparse/exploratory estimates unless a hardware-ready
  materialized operator path exists.
- New QFT evidence fields should be additive and nullable, and tests should
  cover `result.json`, `quantum_evidence.json`, and `report.md` together.

## Release Checklist

Before declaring a release candidate:

```bash
python -m compileall -q qcchem
python -m pytest -q
qcchem release audit -c configs/release/trust_first_audit.yaml -o artifacts/release_audit
git diff --check
git diff --name-only -- artifacts/lih_active_vqe
```

Then inspect:

- `artifacts/release_audit/release_readiness.md`
- `docs/verified_scope.md`
- `docs/release_showcase.md`
- `README.md`

For the visual release gate, also run the Workbench browser smoke checklist in
`docs/workbench.md`. The required direct routes are `/overview`,
`/result-confidence`, `/benchmarks`, `/hardware-campaign`, and
`/ai-workspace`; each route must show its own shell `Active route` label and a
clean browser console.
