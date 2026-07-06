# QCchem Developer Guide

This guide captures the release-hardening practices for QCchem contributors.

## Working Tree Hygiene

Generated local outputs should not be committed unless they are curated release
fixtures. The following are intentionally ignored:

- `.superpowers/`
- `artifacts/workflows/`
- `artifacts/artifact_index.json`
- `artifacts/workbench_smoke.json`
- `artifacts/lr_ace_local_molecule_sweep_*/`
- `artifacts/release_audit/`
- `artifacts/**/preview_local/`

When running tests, make sure curated release files are not rewritten or left as
untracked files:

```bash
git ls-files -ci --exclude-standard
git diff --name-only -- .github artifacts README.md docs configs qcchem tests pyproject.toml
git status --short --untracked-files=all -- .github artifacts README.md docs configs qcchem tests pyproject.toml
```

The tracked-ignored probe should print nothing. If it prints paths, a generated
or ignored file is still in the Git index and should be removed from tracking.
The diff and status probes should print nothing, except for intentionally
ignored local outputs such as `artifacts/artifact_index.json`,
`artifacts/workbench_smoke.json`, `artifacts/release_audit/`, and
`artifacts/workflows/`.

Release acceptance sidecars are not scratch output. When a path is listed in
`configs/release/trust_first_audit.yaml`, its sibling `acceptance_summary.json`
must remain trackable release evidence:

```bash
git check-ignore --no-index -q artifacts/release_audit/release_readiness.json
git check-ignore --no-index -q artifacts/release_audit/release_handoff.json
git check-ignore --no-index -q artifacts/release_audit/release_status.json
git check-ignore --no-index -q artifacts/artifact_index.json
git check-ignore --no-index -q artifacts/workbench_smoke.json
git check-ignore --no-index -q artifacts/workflows/research_os_review_workflow/workflow_result.json
git check-ignore --no-index -q artifacts/lr_ace_flagship_suite_v1/preview_local/benchmark_result.json
git check-ignore --no-index -q .playwright-cli/probe.yml
git ls-files --error-unmatch artifacts/h2/acceptance_summary.json
```

The first eight commands should succeed because those paths are generated local
outputs. A release sidecar such as `artifacts/h2/acceptance_summary.json` should
not match `.gitignore`; `git ls-files --error-unmatch` should find it.
Sidecars using `schema_version:
qcchem.release_artifact_acceptance.v0.1-alpha` must also be listed by the
release manifest through their sibling artifact path. Historical
`qcchem.benchmark_acceptance.v0.1-alpha` sidecars may remain with older
benchmark evidence, but they cannot satisfy `required` or
`acceptance_required` manifest entries. New release-artifact sidecars should not
float outside `configs/release/trust_first_audit.yaml`.

Refresh a manifest-bound release sidecar with the explicit writer command:

```bash
qcchem release acceptance-status \
  -c configs/release/trust_first_audit.yaml \
  --strict \
  --repair-plan
```

```bash
qcchem release accept-artifact \
  -c configs/release/trust_first_audit.yaml \
  --name h2_local_validated_anchor \
  --dry-run
```

```bash
qcchem release accept-artifact \
  -c configs/release/trust_first_audit.yaml \
  --name h2_local_validated_anchor \
  --overwrite
```

`acceptance-status` is read-only and can fail a gate with `--strict` when a
manifest sidecar is missing, stale, unreadable, or blocked. Add `--repair-plan`
to print the preview and refresh commands for every non-fresh sidecar; status
JSON also includes `repair_plan` and `repair_plan_count`.
`accept-artifact --dry-run` previews the same manifest-bound payload and current
sidecar status without writing. `accept-artifact` without `--dry-run` writes the
sibling `acceptance_summary.json`, refreshes `artifact_sha256`, derives trust
tier and runtime evidence status from the same release-readable evidence summary
used by `qcchem release audit`, and preserves existing `release_boundaries` on
overwrite unless `--boundary` is supplied. It refuses to replace an existing
sidecar unless `--overwrite` is explicit.

CI runs `qcchem release acceptance-status --strict --repair-plan` after the
Trust-First release audit, so a regenerated curated artifact must have its
manifest-bound sidecar refreshed before the release branch can pass and CI logs
show the preview/refresh commands. The JSON output carries `schema_features` and
is validated before it is written; CI also probes the saved artifact for schema
feature and semantic-invariant drift before upload.
Use `qcchem release status --audit-dir artifacts/release_audit --strict` after a
local audit when a script needs the compact handoff state without rerunning the
audit. The status command rejects unexpected `release_readiness.json` and
`release_handoff.json` schema versions, and it rejects current-schema bundles
with missing or mistyped required status fields. It also rejects handoff bundles
whose status, action, counts, provenance, or sidecar state no longer match the
readiness JSON before treating the bundle as current. CI calls the same
`qcchem.workflow.release_status` validator for the source-tree audit bundle and
the installed-wheel audit bundle before uploading diagnostics.
Add `-o artifacts/release_audit/release_status.json` only for local or CI
handoff bundles; that file is generated output and should stay ignored.

Artifact indexes preserve both release-sidecar presence and parse status:
`has_acceptance_summary` reports embedded acceptance data or a sibling
`acceptance_summary.json`, while `acceptance_summary_readable` and
`acceptance_summary_error` distinguish a valid sidecar from malformed release
evidence that needs repair. Default artifact-root scans skip ignored
`preview_local` regeneration outputs and report the skipped count through
`skipped_generated_artifacts`; explicitly indexing a preview directory still
indexes that directory for debugging. Missing or non-directory artifact roots
return an empty index with `artifact_root_exists`, `artifact_root_is_dir`, and
`index_error` populated instead of being confused with a successful inventory.

Manifest `acceptance_commands` should be executable recipes, but benchmark
recipes must write to ignored preview outputs rather than directly replacing a
curated release artifact root. Use paths like
`artifacts/lr_ace_flagship_suite_v1/preview_local` with `--overwrite` for
repeatable regeneration checks. The output guard rejects source-tree paths
outside `artifacts/` and the top-level curated `artifacts/` root before creating
or replacing outputs. It also rejects output paths with existing symlink
components before overwrite deletion can follow the link. Relative
`run.output_dir` values are owned by the config workspace; standalone external
configs write outputs beside the config file instead of silently targeting the
QCchem checkout.

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
python -m pytest tests -q -W error::scipy.sparse._base.SparseEfficiencyWarning
```

`pyproject.toml` excludes tests marked `slow` or `stress` from the default
gate. The default release/CI gate treats SciPy sparse efficiency warnings as
failures so circuit/statevector regressions do not return as noisy test output.
Keep the CI `Run tests` command listed in the
`configs/release/trust_first_audit.yaml` `acceptance_commands` list; release
audit fails when the two drift.
CI must also keep the `Write release diagnostics manifest` step after the
release status and release acceptance freshness gates, and keep the
`Upload release diagnostics` step after that manifest step. The upload step uses
`if: always()` so failed runs preserve `artifacts/workbench_smoke.json`,
`artifacts/release_audit/release_readiness.*`,
`artifacts/release_audit/release_handoff.*`,
`artifacts/release_audit/release_status.json`,
`artifacts/release_audit/release_diagnostics_manifest.json`, and the release
sidecar freshness JSON as downloadable GitHub Actions artifacts. The manifest
records uploaded-path size and SHA-256 summaries, omitting only its own
self-referential digest. The job-level
`QCCHEM_RELEASE_DIAGNOSTIC_ARTIFACT_NAME` environment variable must match the
uploaded artifact name so `release_handoff.json` records the exact artifact
entrypoint for the current run. `qcchem release audit` prints that handoff path,
artifact name, artifact listing API URL, and diagnostics manifest path in CI
logs.
After downloading CI artifacts with `gh run download`, run
`qcchem release verify-artifacts --artifact-dir <download-dir>` before treating
the downloaded diagnostics as release evidence. The verifier is read-only: it
checks the downloaded release status summaries, release acceptance freshness
JSON, diagnostics manifest counts, and each uploaded file's recorded size and
SHA-256 digest without rerunning the audit or calling GitHub.
Name retained verifier outputs `release_artifact_verification.json` when they
live under an artifact root. The normalized artifact index and Workbench startup
inventory classify those reports as `release_artifact_verification`, exposing
their pass/fail status, failure count, and matrix artifact counts without
turning the downloaded diagnostics into tracked source files. Keep the Workbench
Overview release-verification block wired to the same indexed report so the
startup inventory and visible evidence console agree.
Slow tests are bounded opt-in checks for expensive or exploratory paths:

```bash
python -m pytest -m slow -q
```

Long exploratory stress cases remain available, but they are not part of the
bounded slow gate:

```bash
python -m pytest -m stress -q
```

The Trust-First release manifest advertises the bounded LR-ACE slow smoke as an
acceptance recipe. Do not add `stress` recipes to
`configs/release/trust_first_audit.yaml`: current LR-ACE stress configs are
exploratory long-run checks with per-config wall-time budgets up to 1200 seconds
and should be scheduled deliberately, one target at a time, when deeper method
evidence is needed.

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

SciPy `SparseEfficiencyWarning` is not filtered; the default release gate runs
with that warning category promoted to an error.

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
set -euo pipefail
python -m compileall -q qcchem
python -m pytest tests -q -W error::scipy.sparse._base.SparseEfficiencyWarning
rm -rf /tmp/qcchem-wheel-check
python -m pip wheel . --no-deps -w /tmp/qcchem-wheel-check
wheel="$(find /tmp/qcchem-wheel-check -maxdepth 1 -type f -name '*.whl' | head -n 1)"
test -n "$wheel"
python -m pip install --dry-run --ignore-installed "${wheel}[dev,ui,runtime]" >/tmp/qcchem-wheel-dependency-plan.txt
python - <<'PY'
from pathlib import Path

plan = Path("/tmp/qcchem-wheel-dependency-plan.txt").read_text(encoding="utf-8")
required = ("QCchem-0.1.0a1", "dash-", "qiskit-aer", "qiskit-ibm-runtime")
missing = [item for item in required if item not in plan]
if missing:
    raise SystemExit(f"Wheel dependency dry-run missed expected packages: {missing}")
print("Wheel dependency dry-run includes dev/ui/runtime extras.")
PY
python - <<'PY'
from email.parser import Parser
from pathlib import Path
from zipfile import ZipFile

wheel = next(Path("/tmp/qcchem-wheel-check").glob("*.whl"))
with ZipFile(wheel) as zf:
    names = set(zf.namelist())
    required = {
        "qcchem/workbench/assets/theme.css",
        "qcchem/workbench/assets/3dmol-bridge.js",
        "qcchem/workbench/assets/assistant-window.js",
        "qcchem/workbench/assets/qcchem-logo.png",
        "qcchem/workbench/assets/favicon.ico",
        "qcchem/workbench/assets/favicon.png",
    }
    missing = sorted(required - names)
    if missing:
        raise SystemExit(f"Wheel is missing release assets: {missing}")
    entry_points_name = next((name for name in names if name.endswith(".dist-info/entry_points.txt")), None)
    if entry_points_name is None:
        raise SystemExit("Wheel is missing entry_points.txt")
    entry_points = zf.read(entry_points_name).decode()
    for script in ("qcchem =", "qcchem-workbench ="):
        if script not in entry_points:
            raise SystemExit(f"Wheel is missing console script: {script}")
    metadata_name = next((name for name in names if name.endswith(".dist-info/METADATA")), None)
    if metadata_name is None:
        raise SystemExit("Wheel is missing METADATA")
    metadata = Parser().parsestr(zf.read(metadata_name).decode())
    extras = set(metadata.get_all("Provides-Extra", []))
    requires = metadata.get_all("Requires-Dist", []) or []
    if "ai" not in extras:
        raise SystemExit("Wheel metadata is missing ai extra")
    if not any(req.startswith("openai") and 'extra == "ai"' in req for req in requires):
        raise SystemExit("Wheel metadata is missing openai requirement for ai extra")
PY
repo_root="$(pwd)"
rm -rf /tmp/qcchem-wheel-target /tmp/qcchem-wheel-smoke.json /tmp/qcchem-wheel-release-audit
python -m pip install --no-deps --target /tmp/qcchem-wheel-target "$wheel"
(cd /tmp && PYTHONPATH=/tmp/qcchem-wheel-target python - <<'PY'
from importlib import resources
from pathlib import Path

import qcchem

target = Path("/tmp/qcchem-wheel-target").resolve()
package_file = Path(qcchem.__file__).resolve()
if not package_file.is_relative_to(target):
    raise SystemExit(f"qcchem imported from checkout instead of wheel target: {package_file}")

for asset in (
    "theme.css",
    "3dmol-bridge.js",
    "assistant-window.js",
    "qcchem-logo.png",
    "favicon.ico",
    "favicon.png",
):
    path = resources.files("qcchem.workbench").joinpath("assets", asset)
    if not path.is_file():
        raise SystemExit(f"Installed wheel is missing Workbench asset: {asset}")
PY
)
test -x /tmp/qcchem-wheel-target/bin/qcchem
test -x /tmp/qcchem-wheel-target/bin/qcchem-workbench
(cd /tmp && PYTHONPATH=/tmp/qcchem-wheel-target /tmp/qcchem-wheel-target/bin/qcchem --help >/dev/null)
(cd /tmp && PYTHONPATH=/tmp/qcchem-wheel-target /tmp/qcchem-wheel-target/bin/qcchem-workbench --help >/dev/null)
(cd /tmp && REPO_ROOT="$repo_root" PYTHONPATH=/tmp/qcchem-wheel-target python - <<'PY'
import os
from pathlib import Path

from qcchem.workbench.data import WORKBENCH_ARTIFACT_ROOT_ENV
from qcchem.workbench.server import prepare_workbench

artifact_root = Path(os.environ["REPO_ROOT"]) / "artifacts"
_app, summary = prepare_workbench(
    host="127.0.0.1",
    port=8050,
    debug=False,
    artifact_root=artifact_root,
)
if Path(summary["artifact_root"]) != artifact_root.resolve():
    raise SystemExit(f"Workbench used unexpected artifact root: {summary['artifact_root']}")
inventory = summary["artifact_inventory"]
if inventory["run_result_roots"] < 1 or inventory["benchmark_suites"] < 1:
    raise SystemExit(f"Installed Workbench did not index release artifacts: {inventory}")
if os.environ.get(WORKBENCH_ARTIFACT_ROOT_ENV) != str(artifact_root.resolve()):
    raise SystemExit("Workbench artifact-root environment was not set for page layouts")
PY
)
(cd /tmp && PYTHONPATH=/tmp/qcchem-wheel-target /tmp/qcchem-wheel-target/bin/qcchem workbench smoke --docs "$repo_root/docs/workbench.md" --artifact-root "$repo_root/artifacts" -o /tmp/qcchem-wheel-smoke.json)
(cd /tmp && PYTHONPATH=/tmp/qcchem-wheel-target /tmp/qcchem-wheel-target/bin/qcchem release audit --repo-root "$repo_root" -c configs/release/trust_first_audit.yaml -o /tmp/qcchem-wheel-release-audit)
REPO_ROOT="$repo_root" python - <<'PY'
import json
import os
from pathlib import Path

readiness = Path("/tmp/qcchem-wheel-release-audit/release_readiness.json")
summary = json.loads(readiness.read_text(encoding="utf-8"))
if summary.get("status") != "passed":
    raise SystemExit(f"Installed wheel release audit did not pass: {summary.get('status')}")
if summary.get("required_fail_count") != 0:
    raise SystemExit(f"Installed wheel release audit had required failures: {summary.get('required_fail_count')}")
schema_features = set(summary.get("schema_features", []))
for feature in (
    "evidence_matrix_core_fields",
    "evidence_matrix_review_warnings",
    "warning_policy",
    "acceptance_commands",
    "ci_acceptance_command_alignment",
    "ci_acceptance_status_gate",
    "acceptance_summary_source",
    "ci_release_diagnostics_manifest",
    "acceptance_schema_version",
    "acceptance_artifact_sha256",
    "acceptance_release_audit_check_id",
    "acceptance_runtime_evidence_status",
    "acceptance_recommended_action",
    "acceptance_contract_failure_count",
    "audit_provenance",
):
    if feature not in schema_features:
        raise SystemExit(f"Installed wheel release audit missing schema feature: {feature}")
expected_repo_root = str(Path(os.environ["REPO_ROOT"]).resolve())
actual_repo_root = summary.get("audit_provenance", {}).get("repo_root")
if actual_repo_root != expected_repo_root:
    raise SystemExit(f"Installed wheel release audit used unexpected repo root: {actual_repo_root}")
PY
git diff --check
test -z "$(git ls-files -ci --exclude-standard)"
test -z "$(git ls-files '*__pycache__*' '*.pyc' '*.pyo' '.DS_Store' '*/.DS_Store' 'build/**' 'dist/**' '*.egg-info' '*.egg-info/**' '**/*.egg-info' '**/*.egg-info/**')"
git diff --name-only -- .github artifacts README.md docs configs qcchem tests pyproject.toml
git status --short --untracked-files=all -- .github artifacts README.md docs configs qcchem tests pyproject.toml
```

For a publication-facing release check, also verify a fresh editable install in
a temporary environment so the `qcchem` console script cannot accidentally point
at an older worktree:

```bash
python -m venv /tmp/qcchem-release-venv
/tmp/qcchem-release-venv/bin/python -m pip install --upgrade pip setuptools wheel
/tmp/qcchem-release-venv/bin/python -m pip install -e ".[dev,ui,ai,runtime]"
/tmp/qcchem-release-venv/bin/python -m pip check
repo_root="$(pwd)"
/tmp/qcchem-release-venv/bin/python - <<'PY'
from pathlib import Path

import qcchem

repo_root = Path.cwd().resolve()
package_file = Path(qcchem.__file__).resolve()
print(f"qcchem_file={package_file}")
if not package_file.is_relative_to(repo_root):
    raise SystemExit(f"qcchem imported from unexpected checkout: {package_file}")
PY
(cd /tmp && /tmp/qcchem-release-venv/bin/qcchem workbench smoke --docs "$repo_root/docs/workbench.md" --artifact-root "$repo_root/artifacts" -o /tmp/qcchem-release-venv/workbench_smoke.json)
(cd /tmp && /tmp/qcchem-release-venv/bin/qcchem release audit --repo-root "$repo_root" -c configs/release/trust_first_audit.yaml -o /tmp/qcchem-release-venv/release_audit)
```

The two console-script checks run from `/tmp` so the current working directory
cannot accidentally satisfy imports that the installed script would otherwise
miss.

Then inspect:

- `artifacts/release_audit/release_readiness.md`
- `docs/verified_scope.md`
- `docs/release_showcase.md`
- `README.md`

For the visual release gate, also run the Workbench browser smoke checklist in
`docs/workbench.md`. The required direct routes are `/overview`,
`/result-confidence`, `/benchmarks`, `/hardware-campaign`, `/ai-workspace`, and
`/workflow-studio`; each route must show its own shell `Active route` label and
a clean browser console. The CI command
`qcchem workbench smoke --docs docs/workbench.md` verifies the same route table
at component-tree level; it does not replace the real browser console check.
