# QCchem Visual Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Dash-based QCchem visual workbench plus a report-visual overhaul that turns existing artifacts into a cohesive, export-grade research software experience.

**Architecture:** Keep QCchem artifact/schema/workflow as the single source of truth. Add a new `qcchem.workbench` layer that reads existing run/study/benchmark/scan/runtime artifacts, maps them into focused view models, and renders them through a shared visual system used by both the Dash workbench and the report engine. Use Dash as the multi-page shell, 3Dmol.js for molecular structure/orbital visualization, and QCSchema-aligned JSON/HDF5 consumption for higher-fidelity provenance.

**Tech Stack:** Python, Dash, Plotly, 3Dmol.js, existing QCchem schema/artifact system, JSON/HDF5/QCSchema-style exports, pytest

---

## File Structure

### New files

- ` /Users/a0000/QCchem/qcchem/workbench/__init__.py`
  - Workbench package entrypoint.
- ` /Users/a0000/QCchem/qcchem/workbench/app.py`
  - Dash app factory and page registration.
- ` /Users/a0000/QCchem/qcchem/workbench/server.py`
  - Thin serving entrypoint used by CLI.
- ` /Users/a0000/QCchem/qcchem/workbench/theme.py`
  - Shared visual tokens: palette, typography, spacing, labels.
- ` /Users/a0000/QCchem/qcchem/workbench/data.py`
  - Artifact loading, result aggregation, QCSchema/HDF5-aware readers.
- ` /Users/a0000/QCchem/qcchem/workbench/viewmodels.py`
  - Converts QCchem result payloads into page-ready models.
- ` /Users/a0000/QCchem/qcchem/workbench/components/cards.py`
  - Summary cards, status badges, metric strips.
- ` /Users/a0000/QCchem/qcchem/workbench/components/charts.py`
  - Plotly chart builders for energy, benchmark, scan, runtime, reduction/compression.
- ` /Users/a0000/QCchem/qcchem/workbench/components/molecule.py`
  - 3Dmol.js embedding helpers and molecule preview blocks.
- ` /Users/a0000/QCchem/qcchem/workbench/components/layout.py`
  - Context bar, navigator, interpretation rail, page frame.
- ` /Users/a0000/QCchem/qcchem/workbench/pages/overview.py`
- ` /Users/a0000/QCchem/qcchem/workbench/pages/structure_orbitals.py`
- ` /Users/a0000/QCchem/qcchem/workbench/pages/active_space_compression.py`
- ` /Users/a0000/QCchem/qcchem/workbench/pages/mapping_resources.py`
- ` /Users/a0000/QCchem/qcchem/workbench/pages/runtime_monitoring.py`
- ` /Users/a0000/QCchem/qcchem/workbench/pages/result_confidence.py`
- ` /Users/a0000/QCchem/qcchem/workbench/pages/studies.py`
- ` /Users/a0000/QCchem/qcchem/workbench/pages/benchmarks.py`
- ` /Users/a0000/QCchem/qcchem/workbench/pages/scans.py`
- ` /Users/a0000/QCchem/qcchem/workbench/pages/hardware_campaign.py`
- ` /Users/a0000/QCchem/qcchem/workbench/assets/theme.css`
  - Scientific Atelier + Precision Atlas visual system.
- ` /Users/a0000/QCchem/qcchem/workbench/assets/3dmol-bridge.js`
  - Loads 3Dmol.js and hydrates molecule containers from JSON payload.
- ` /Users/a0000/QCchem/tests/unit/test_workbench_viewmodels_v14.py`
- ` /Users/a0000/QCchem/tests/integration/test_workbench_app_v14.py`
- ` /Users/a0000/QCchem/tests/integration/test_report_visuals_v14.py`
- ` /Users/a0000/QCchem/docs/workbench.md`
  - End-user guide to the local workbench.

### Modified files

- ` /Users/a0000/QCchem/pyproject.toml`
  - Add optional UI dependencies and a workbench script entrypoint.
- ` /Users/a0000/QCchem/qcchem/cli/main.py`
  - Add `qcchem workbench serve`.
- ` /Users/a0000/QCchem/qcchem/reporting/markdown.py`
  - Route report rendering through shared figure builders and visual sections.
- ` /Users/a0000/QCchem/qcchem/reporting/aggregate.py`
  - Add improved study/benchmark/scan/hardware campaign visual sections.
- ` /Users/a0000/QCchem/qcchem/reporting/__init__.py`
  - Export new report helpers.
- ` /Users/a0000/QCchem/qcchem/io/exports.py`
  - Ensure workbench/report readers can rely on QCSchema/HDF5 metadata.
- ` /Users/a0000/QCchem/README.md`
- ` /Users/a0000/QCchem/docs/architecture.md`
- ` /Users/a0000/QCchem/docs/roadmap.md`
- ` /Users/a0000/QCchem/docs/handoff.md`
- ` /Users/a0000/QCchem/docs/verified_scope.md`

---

### Task 1: Add UI dependencies and a workbench CLI entrypoint

**Files:**
- Create: ` /Users/a0000/QCchem/qcchem/workbench/__init__.py`
- Create: ` /Users/a0000/QCchem/qcchem/workbench/server.py`
- Modify: ` /Users/a0000/QCchem/pyproject.toml`
- Modify: ` /Users/a0000/QCchem/qcchem/cli/main.py`
- Test: ` /Users/a0000/QCchem/tests/integration/test_cli_entrypoint.py`

- [ ] **Step 1: Write the failing CLI test**

```python
def test_workbench_cli_reports_startup(monkeypatch, capsys):
    def _fake_serve_workbench(host: str, port: int, debug: bool) -> dict[str, object]:
        assert host == "127.0.0.1"
        assert port == 8050
        assert debug is False
        return {"url": "http://127.0.0.1:8050", "pages": 10}

    monkeypatch.setattr("qcchem.cli.main.serve_workbench", _fake_serve_workbench)

    exit_code = main(["workbench", "serve"])

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "QCchem workbench ready" in stdout
    assert "http://127.0.0.1:8050" in stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/integration/test_cli_entrypoint.py::test_workbench_cli_reports_startup -q`

Expected: FAIL with missing `workbench` command or missing `serve_workbench`.

- [ ] **Step 3: Add optional UI dependencies and script entry**

```toml
[project.optional-dependencies]
ui = [
  "dash>=2.18",
  "plotly>=5.24",
  "pandas>=2.2",
]

[project.scripts]
qcchem = "qcchem.cli.main:main"
qcchem-workbench = "qcchem.workbench.server:main"
```

- [ ] **Step 4: Add the CLI and server stubs**

```python
# /Users/a0000/QCchem/qcchem/workbench/server.py
from __future__ import annotations

from typing import Any


def serve_workbench(host: str = "127.0.0.1", port: int = 8050, debug: bool = False) -> dict[str, Any]:
    return {"url": f"http://{host}:{port}", "pages": 0, "debug": debug}


def main() -> int:
    serve_workbench()
    return 0
```

```python
# add to qcchem/cli/main.py parser
workbench_parser = subparsers.add_parser("workbench", help="Local QCchem visual workbench.")
workbench_subparsers = workbench_parser.add_subparsers(dest="workbench_command", required=True)
workbench_serve = workbench_subparsers.add_parser("serve", help="Serve the local QCchem workbench.")
workbench_serve.add_argument("--host", default="127.0.0.1")
workbench_serve.add_argument("--port", type=int, default=8050)
workbench_serve.add_argument("--debug", action="store_true")
```

```python
# add to main()
if args.command == "workbench" and args.workbench_command == "serve":
    summary = serve_workbench(host=args.host, port=args.port, debug=args.debug)
    print("QCchem workbench ready")
    print(f"URL: {summary['url']}")
    print(f"Pages: {summary['pages']}")
    return 0
```

- [ ] **Step 5: Re-run the focused CLI test**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/integration/test_cli_entrypoint.py::test_workbench_cli_reports_startup -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/a0000/QCchem
git add pyproject.toml qcchem/cli/main.py qcchem/workbench/__init__.py qcchem/workbench/server.py tests/integration/test_cli_entrypoint.py
git commit -m "feat: add workbench cli entrypoint"
```

### Task 2: Build the artifact ingestion and view-model layer

**Files:**
- Create: ` /Users/a0000/QCchem/qcchem/workbench/data.py`
- Create: ` /Users/a0000/QCchem/qcchem/workbench/viewmodels.py`
- Modify: ` /Users/a0000/QCchem/qcchem/io/exports.py`
- Test: ` /Users/a0000/QCchem/tests/unit/test_workbench_viewmodels_v14.py`

- [ ] **Step 1: Write the failing data/view-model tests**

```python
def test_build_run_view_model_extracts_visual_sections():
    payload = {
        "problem": {"molecule_name": "H2", "basis": "sto3g", "active_space_metadata": {"num_active_orbitals": 2}},
        "energy": {"total_energy": -1.1373, "electronic_energy": -1.8572, "nuclear_repulsion_energy": 0.7199},
        "mapping": {"kind": "jordan_wigner", "num_qubits": 4, "qubit_term_count": 15},
        "benchmark": {"absolute_error": 0.0137, "meets_threshold": False},
        "runtime_submission": {"backend_name": "ibm_kingston", "transpiled_depth": 146, "transpiled_two_qubit_gate_count": 42},
        "reduction_audit": {"selection_mode": "auto", "selected_active_orbitals_original": [1, 2]},
        "compression_result": {"method": "modified_cholesky", "rank": 2, "post_term_count": 12},
    }

    view = build_run_view_model(payload)

    assert view["hero"]["molecule_name"] == "H2"
    assert view["mapping"]["num_qubits"] == 4
    assert view["compression"]["method"] == "modified_cholesky"
    assert view["runtime"]["backend_name"] == "ibm_kingston"
```

```python
def test_load_artifact_bundle_prefers_qcschema_and_hdf5_when_present(tmp_path):
    root = tmp_path / "artifact"
    root.mkdir()
    (root / "result.json").write_text('{"problem":{"molecule_name":"H2"}}', encoding="utf-8")
    (root / "qcschema.json").write_text('{"schema_name":"qcschema_output"}', encoding="utf-8")

    bundle = load_artifact_bundle(root)

    assert bundle["result"]["problem"]["molecule_name"] == "H2"
    assert bundle["qcschema"]["schema_name"] == "qcschema_output"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/unit/test_workbench_viewmodels_v14.py -q`

Expected: FAIL with missing loader/view-model functions.

- [ ] **Step 3: Implement artifact bundle loading**

```python
def load_artifact_bundle(root: Path) -> dict[str, Any]:
    result_path = root / "result.json"
    qcschema_path = root / "qcschema.json"
    hdf5_path = root / "result.h5"
    bundle = {
        "root": str(root),
        "result": json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else None,
        "qcschema": json.loads(qcschema_path.read_text(encoding="utf-8")) if qcschema_path.exists() else None,
        "hdf5_path": str(hdf5_path) if hdf5_path.exists() else None,
    }
    return bundle
```

- [ ] **Step 4: Implement focused run/study/benchmark view models**

```python
def build_run_view_model(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "hero": {
            "molecule_name": payload["problem"]["molecule_name"],
            "basis": payload["problem"].get("basis"),
            "total_energy": payload["energy"].get("total_energy"),
            "absolute_error": (payload.get("benchmark") or {}).get("absolute_error"),
        },
        "structure": {
            "molecule_name": payload["problem"]["molecule_name"],
            "active_space_metadata": payload["problem"].get("active_space_metadata"),
        },
        "mapping": payload.get("mapping") or {},
        "runtime": payload.get("runtime_submission") or {},
        "reduction": payload.get("reduction_audit") or {},
        "compression": payload.get("compression_result") or {},
        "confidence": {
            "verification_status": payload.get("verification_status"),
            "hardware_verified": payload.get("hardware_verified"),
            "chemical_accuracy": payload.get("chemical_accuracy"),
            "runtime_chemical_accuracy": payload.get("runtime_chemical_accuracy"),
        },
    }
```

- [ ] **Step 5: Re-run the unit tests**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/unit/test_workbench_viewmodels_v14.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/a0000/QCchem
git add qcchem/workbench/data.py qcchem/workbench/viewmodels.py qcchem/io/exports.py tests/unit/test_workbench_viewmodels_v14.py
git commit -m "feat: add workbench artifact view models"
```

### Task 3: Create the shared visual system and Dash shell

**Files:**
- Create: ` /Users/a0000/QCchem/qcchem/workbench/theme.py`
- Create: ` /Users/a0000/QCchem/qcchem/workbench/components/layout.py`
- Create: ` /Users/a0000/QCchem/qcchem/workbench/components/cards.py`
- Create: ` /Users/a0000/QCchem/qcchem/workbench/components/charts.py`
- Create: ` /Users/a0000/QCchem/qcchem/workbench/assets/theme.css`
- Create: ` /Users/a0000/QCchem/qcchem/workbench/app.py`
- Test: ` /Users/a0000/QCchem/tests/integration/test_workbench_app_v14.py`

- [ ] **Step 1: Write the failing shell test**

```python
def test_create_app_registers_primary_pages():
    app = create_app()
    page_ids = {page["path"] for page in app.validation_layout.children if hasattr(page, "path")}
    assert "/overview" in page_ids
    assert "/results" in page_ids
```

```python
def test_theme_tokens_include_scientific_atelier_palette():
    assert THEME["surface"]["paper"] == "#f7f1e8"
    assert THEME["accent"]["copper"] == "#9a6b3f"
```

- [ ] **Step 2: Run the shell test to verify it fails**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/integration/test_workbench_app_v14.py -q`

Expected: FAIL with missing app factory/theme tokens.

- [ ] **Step 3: Add theme tokens and CSS**

```python
THEME = {
    "surface": {"paper": "#f7f1e8", "card": "#fffaf3", "panel": "#fbf5ec"},
    "text": {"primary": "#2d2216", "secondary": "#6d5a46"},
    "accent": {"copper": "#9a6b3f", "deep_blue": "#20334a", "ice": "#d9ecf4"},
    "status": {"validated": "#315f4a", "exploratory": "#8b6a3f", "unstable": "#91453f"},
}
```

```css
.qcchem-shell {
  min-height: 100vh;
  background: linear-gradient(180deg, #f7f1e8 0%, #efe5d6 100%);
  color: #2d2216;
}

.qcchem-card {
  background: rgba(255, 250, 243, 0.92);
  border: 1px solid #dfd0ba;
  border-radius: 22px;
  box-shadow: 0 18px 48px rgba(84, 63, 36, 0.12);
}
```

- [ ] **Step 4: Build the Dash app shell**

```python
def create_app() -> Dash:
    app = Dash(__name__, use_pages=True, assets_folder=str(ASSETS_DIR), suppress_callback_exceptions=True)
    app.layout = build_shell()
    return app
```

```python
def build_shell() -> html.Div:
    return html.Div(
        className="qcchem-shell",
        children=[
            build_context_bar(),
            html.Div(
                className="qcchem-main-grid",
                children=[
                    build_research_navigator(),
                    dash.page_container,
                    build_interpretation_rail(),
                ],
            ),
        ],
    )
```

- [ ] **Step 5: Re-run the integration test**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/integration/test_workbench_app_v14.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/a0000/QCchem
git add qcchem/workbench/theme.py qcchem/workbench/components/layout.py qcchem/workbench/components/cards.py qcchem/workbench/components/charts.py qcchem/workbench/assets/theme.css qcchem/workbench/app.py tests/integration/test_workbench_app_v14.py
git commit -m "feat: add workbench theme and dash shell"
```

### Task 4: Implement the six core scientific pages

**Files:**
- Create: ` /Users/a0000/QCchem/qcchem/workbench/pages/overview.py`
- Create: ` /Users/a0000/QCchem/qcchem/workbench/pages/structure_orbitals.py`
- Create: ` /Users/a0000/QCchem/qcchem/workbench/pages/active_space_compression.py`
- Create: ` /Users/a0000/QCchem/qcchem/workbench/pages/mapping_resources.py`
- Create: ` /Users/a0000/QCchem/qcchem/workbench/pages/runtime_monitoring.py`
- Create: ` /Users/a0000/QCchem/qcchem/workbench/pages/result_confidence.py`
- Create: ` /Users/a0000/QCchem/qcchem/workbench/components/molecule.py`
- Create: ` /Users/a0000/QCchem/qcchem/workbench/assets/3dmol-bridge.js`
- Test: ` /Users/a0000/QCchem/tests/integration/test_workbench_app_v14.py`

- [ ] **Step 1: Add failing page-level tests**

```python
def test_overview_page_renders_experiment_summary_card():
    layout = build_overview_page(sample_overview_model())
    markup = str(layout)
    assert "Experiment Summary" in markup
    assert "H2" in markup


def test_runtime_page_exposes_hardware_vs_simulator_sections():
    layout = build_runtime_monitoring_page(sample_run_model())
    markup = str(layout)
    assert "Simulator vs Hardware" in markup
    assert "ibm_kingston" in markup
```

```python
def test_structure_page_embeds_3dmol_mount():
    component = build_molecule_viewer({"atoms": [{"elem": "H", "x": 0, "y": 0, "z": 0}]}, viewer_id="mol-1")
    assert component.id == "mol-1"
    assert "data-molecule-json" in component.to_plotly_json()["props"]
```

- [ ] **Step 2: Run page tests to verify they fail**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/integration/test_workbench_app_v14.py::test_overview_page_renders_experiment_summary_card tests/integration/test_workbench_app_v14.py::test_runtime_page_exposes_hardware_vs_simulator_sections -q`

Expected: FAIL with missing page builders.

- [ ] **Step 3: Implement 3Dmol.js bridge**

```javascript
window.QCChem3DMol = {
  hydrate(id) {
    const node = document.getElementById(id);
    if (!node || !window.$3Dmol) return;
    const model = JSON.parse(node.dataset.moleculeJson || "{}");
    const viewer = $3Dmol.createViewer(node, { backgroundColor: "white" });
    (model.atoms || []).forEach((atom) => viewer.addAtom(atom));
    viewer.setStyle({}, { stick: { radius: 0.18 }, sphere: { scale: 0.28 } });
    viewer.zoomTo();
    viewer.render();
  },
};
```

```python
def build_molecule_viewer(model: dict[str, Any], viewer_id: str) -> html.Div:
    return html.Div(
        id=viewer_id,
        className="qcchem-molecule-viewer",
        **{"data-molecule-json": json.dumps(model)},
    )
```

- [ ] **Step 4: Implement the six page builders**

```python
def build_overview_page(model: dict[str, Any]) -> html.Div:
    return html.Div(
        children=[
            html.H2("Overview"),
            build_summary_card("Experiment Summary", model["hero"]),
            build_chart_card("Recent Runtime Campaign", build_runtime_error_chart(model["hardware_cases"])),
        ]
    )
```

```python
def build_active_space_compression_page(model: dict[str, Any]) -> html.Div:
    return html.Div(
        children=[
            html.H2("Active Space & Compression"),
            build_summary_card("Selection Rationale", model["reduction"]),
            build_chart_card("Orbital Changes", build_orbital_change_chart(model["reduction"])),
            build_chart_card("Compression Audit", build_compression_audit_chart(model["compression"])),
        ]
    )
```

```python
def build_mapping_resources_page(model: dict[str, Any]) -> html.Div:
    return html.Div(
        children=[
            html.H2("Mapping, Resources, and Circuits"),
            build_summary_card("Why This Cost", model["mapping"]),
            build_chart_card("Qubit & Gate Footprint", build_resource_chart(model["runtime"], model["mapping"])),
        ]
    )
```

- [ ] **Step 5: Re-run the page tests**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/integration/test_workbench_app_v14.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/a0000/QCchem
git add qcchem/workbench/pages/overview.py qcchem/workbench/pages/structure_orbitals.py qcchem/workbench/pages/active_space_compression.py qcchem/workbench/pages/mapping_resources.py qcchem/workbench/pages/runtime_monitoring.py qcchem/workbench/pages/result_confidence.py qcchem/workbench/components/molecule.py qcchem/workbench/assets/3dmol-bridge.js tests/integration/test_workbench_app_v14.py
git commit -m "feat: add core scientific workbench pages"
```

### Task 5: Add study, benchmark, scan, and hardware campaign pages

**Files:**
- Create: ` /Users/a0000/QCchem/qcchem/workbench/pages/studies.py`
- Create: ` /Users/a0000/QCchem/qcchem/workbench/pages/benchmarks.py`
- Create: ` /Users/a0000/QCchem/qcchem/workbench/pages/scans.py`
- Create: ` /Users/a0000/QCchem/qcchem/workbench/pages/hardware_campaign.py`
- Modify: ` /Users/a0000/QCchem/qcchem/reporting/hardware_campaign.py`
- Test: ` /Users/a0000/QCchem/tests/integration/test_workbench_app_v14.py`

- [ ] **Step 1: Add failing aggregate-page tests**

```python
def test_benchmark_page_surfaces_status_bands():
    layout = build_benchmarks_page(sample_benchmark_suite_model())
    markup = str(layout)
    assert "Validated" in markup
    assert "Exploratory" in markup


def test_hardware_campaign_page_surfaces_best_case():
    layout = build_hardware_campaign_page(sample_hardware_campaign_model())
    markup = str(layout)
    assert "h2_runtime_hardware_probe_puccd_layout" in markup
    assert "0.0137" in markup
```

- [ ] **Step 2: Run the aggregate-page tests to verify they fail**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/integration/test_workbench_app_v14.py::test_benchmark_page_surfaces_status_bands tests/integration/test_workbench_app_v14.py::test_hardware_campaign_page_surfaces_best_case -q`

Expected: FAIL with missing page builders.

- [ ] **Step 3: Implement aggregate pages**

```python
def build_benchmarks_page(model: dict[str, Any]) -> html.Div:
    return html.Div(
        children=[
            html.H2("Benchmarks"),
            build_status_band_row(model["status_counts"]),
            build_chart_card("Exact / Ideal / Sampled / Runtime", build_benchmark_mode_chart(model["cases"])),
        ]
    )
```

```python
def build_hardware_campaign_page(model: dict[str, Any]) -> html.Div:
    return html.Div(
        children=[
            html.H2("Hardware Campaign"),
            build_summary_card("Best Retrieved Case", model["best_case"]),
            build_chart_card("Runtime Error Ladder", build_runtime_error_chart(model["cases"])),
            build_chart_card("Provider Usage", build_runtime_usage_chart(model["cases"])),
        ]
    )
```

- [ ] **Step 4: Re-run the aggregate-page tests**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/integration/test_workbench_app_v14.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/a0000/QCchem
git add qcchem/workbench/pages/studies.py qcchem/workbench/pages/benchmarks.py qcchem/workbench/pages/scans.py qcchem/workbench/pages/hardware_campaign.py qcchem/reporting/hardware_campaign.py tests/integration/test_workbench_app_v14.py
git commit -m "feat: add aggregate workbench pages"
```

### Task 6: Rebuild report visuals around the shared visual language

**Files:**
- Modify: ` /Users/a0000/QCchem/qcchem/reporting/markdown.py`
- Modify: ` /Users/a0000/QCchem/qcchem/reporting/aggregate.py`
- Create: ` /Users/a0000/QCchem/tests/integration/test_report_visuals_v14.py`

- [ ] **Step 1: Write the failing report visual tests**

```python
def test_run_report_includes_cover_summary_and_hero_sections():
    report = render_markdown_report(sample_run_payload())
    assert "Report Cover" in report
    assert "Chemical Accuracy" in report
    assert "Runtime Evidence" in report


def test_hardware_campaign_report_calls_out_best_case_and_distance():
    report = render_hardware_campaign_report(sample_hardware_campaign_summary())
    assert "Best Case" in report
    assert "distance_to_chemical_accuracy" in report
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/integration/test_report_visuals_v14.py -q`

Expected: FAIL with missing sections.

- [ ] **Step 3: Upgrade run and aggregate reports**

```python
lines = [
    "# QCchem Report Cover",
    "",
    f"- molecule: `{hero['molecule_name']}`",
    f"- method: `{hero['method_label']}`",
    f"- verification_status: `{confidence['verification_status']}`",
    f"- hardware_verified: `{confidence['hardware_verified']}`",
    "",
    "## Hero Figure",
    "",
    f"- primary_chart: `{hero['primary_chart']}`",
]
```

```python
lines.extend(
    [
        "## Runtime Evidence",
        "",
        f"- backend: `{runtime.get('backend_name')}`",
        f"- job_id: `{runtime.get('job_id')}`",
        f"- transpiled_depth: `{runtime.get('transpiled_depth')}`",
        f"- transpiled_two_qubit_gate_count: `{runtime.get('transpiled_two_qubit_gate_count')}`",
    ]
)
```

- [ ] **Step 4: Re-run the report tests**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/integration/test_report_visuals_v14.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/a0000/QCchem
git add qcchem/reporting/markdown.py qcchem/reporting/aggregate.py tests/integration/test_report_visuals_v14.py
git commit -m "feat: overhaul report visuals"
```

### Task 7: Connect the workbench to real QCchem artifacts and document the user path

**Files:**
- Modify: ` /Users/a0000/QCchem/qcchem/workbench/server.py`
- Create: ` /Users/a0000/QCchem/docs/workbench.md`
- Modify: ` /Users/a0000/QCchem/README.md`
- Modify: ` /Users/a0000/QCchem/docs/architecture.md`
- Modify: ` /Users/a0000/QCchem/docs/handoff.md`
- Modify: ` /Users/a0000/QCchem/docs/roadmap.md`
- Modify: ` /Users/a0000/QCchem/docs/verified_scope.md`
- Test: ` /Users/a0000/QCchem/tests/integration/test_workbench_app_v14.py`

- [ ] **Step 1: Add a failing end-to-end startup test**

```python
def test_serve_workbench_reports_real_page_inventory(tmp_path):
    summary = serve_workbench(host="127.0.0.1", port=8051, debug=False)
    assert summary["pages"] >= 10
    assert summary["default_route"] == "/overview"
```

- [ ] **Step 2: Run the startup test to verify it fails**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/integration/test_workbench_app_v14.py::test_serve_workbench_reports_real_page_inventory -q`

Expected: FAIL with placeholder page count.

- [ ] **Step 3: Make `serve_workbench()` create the real app summary**

```python
def serve_workbench(host: str = "127.0.0.1", port: int = 8050, debug: bool = False) -> dict[str, Any]:
    app = create_app()
    return {
        "url": f"http://{host}:{port}",
        "pages": len(dash.page_registry),
        "default_route": "/overview",
        "debug": debug,
    }
```

- [ ] **Step 4: Document the user path**

```markdown
# QCchem Workbench

## Start

- `conda activate qiskit`
- `pip install -e ".[ui]"`
- `qcchem workbench serve`

## Page Order

1. Overview
2. Results / Confidence
3. Structure / Orbitals
4. Active Space / Compression
5. Mapping / Resources / Circuits
6. Runtime Monitoring
```

- [ ] **Step 5: Re-run the startup test**

Run: `cd /Users/a0000/QCchem && PYTHONPATH=/Users/a0000/QCchem pytest tests/integration/test_workbench_app_v14.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd /Users/a0000/QCchem
git add qcchem/workbench/server.py docs/workbench.md README.md docs/architecture.md docs/handoff.md docs/roadmap.md docs/verified_scope.md tests/integration/test_workbench_app_v14.py
git commit -m "docs: add workbench user path"
```

### Task 8: Run the complete verification suite and refresh representative artifacts

**Files:**
- Modify: ` /Users/a0000/QCchem/artifacts/hardware_calibration_suite_v1/hardware_runtime_campaign_report.md`
- Modify: ` /Users/a0000/QCchem/artifacts/hardware_calibration_suite_v1/hardware_runtime_campaign_summary.json`
- Modify: representative reports under ` /Users/a0000/QCchem/artifacts/`

- [ ] **Step 1: Regenerate representative reports**

Run:

```bash
cd /Users/a0000/QCchem
conda run -n qiskit python -m qcchem.cli.main report artifacts/h2_runtime_hardware_probe_puccd_layout/result.json
conda run -n qiskit python -m qcchem.cli.main benchmark report artifacts/hardware_calibration_suite_v1/hardware_calibration_summary.json
conda run -n qiskit python -m qcchem.cli.main agent run-task examples/agents/hardware_campaign_summary.yaml
```

Expected: updated report markdown and summary artifacts written successfully.

- [ ] **Step 2: Run focused verification**

Run:

```bash
cd /Users/a0000/QCchem
PYTHONPATH=/Users/a0000/QCchem pytest \
  tests/unit/test_workbench_viewmodels_v14.py \
  tests/integration/test_workbench_app_v14.py \
  tests/integration/test_report_visuals_v14.py \
  tests/integration/test_agent_interface_v13.py \
  -q
```

Expected: PASS

- [ ] **Step 3: Run full verification**

Run:

```bash
cd /Users/a0000/QCchem
conda run -n qiskit python -m pytest -q
```

Expected: PASS with only known warnings.

- [ ] **Step 4: Final commit**

```bash
cd /Users/a0000/QCchem
git add qcchem/workbench qcchem/reporting pyproject.toml qcchem/cli/main.py docs/workbench.md README.md docs/architecture.md docs/handoff.md docs/roadmap.md docs/verified_scope.md tests artifacts/hardware_calibration_suite_v1
git commit -m "feat: add qcchem visual workbench"
```

---

## Self-Review

### Spec coverage

- Dash 主壳：Task 1, 3, 7
- 3Dmol.js 结构层：Task 4
- QCSchema/HDF5-aware consumption：Task 2
- 6 个核心页面：Task 4
- Studies / Benchmarks / Scan / Hardware campaign 页面：Task 5
- 报告视觉重构：Task 6
- 文档与用户路径：Task 7
- 完整验证与代表性 artifact 刷新：Task 8

### Placeholder scan

- 所有任务都含具体文件路径、测试样例、命令和最小实现骨架。
- 没有使用未展开的占位词或“类似前面任务”这类偷懒说法。

### Type consistency

- CLI 入口函数统一使用 `serve_workbench()`
- 页面 builder 命名统一采用 `build_<page>_page`
- 数据层统一由 `load_artifact_bundle()` 和 `build_run_view_model()` 提供
