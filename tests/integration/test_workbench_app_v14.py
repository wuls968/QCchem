from __future__ import annotations

from collections.abc import Iterable
import importlib
import json
from pathlib import Path
import subprocess
import textwrap
from types import SimpleNamespace

import dash
import pytest

from qcchem.workbench.theme import SHARED_THEME_FAMILIES, THEME, css_var_map

REPO_ROOT = Path(__file__).resolve().parents[2]
SCIENTIFIC_PAGE_MODULES = {
    "qcchem.workbench.pages.overview": ("/overview", "Campaign Overview", "build_overview_page"),
    "qcchem.workbench.pages.structure_orbitals": ("/structure-orbitals", "Structure and Orbitals", "build_structure_orbitals_page"),
    "qcchem.workbench.pages.active_space_compression": ("/active-space-compression", "Active Space and Compression", "build_active_space_compression_page"),
    "qcchem.workbench.pages.mapping_resources": ("/mapping-resources", "Mapping, Resources, and Circuit", "build_mapping_resources_page"),
    "qcchem.workbench.pages.runtime_monitoring": ("/runtime-monitoring", "Runtime Monitoring", "build_runtime_monitoring_page"),
    "qcchem.workbench.pages.result_confidence": ("/result-confidence", "Result Confidence Report", "build_result_confidence_page"),
}


def _walk_components(component: object) -> Iterable[object]:
    yield component
    children = getattr(component, "children", None)
    if children is None:
        return
    if isinstance(children, (list, tuple)):
        for child in children:
            yield from _walk_components(child)
    else:
        yield from _walk_components(children)


def _resolve_layout(layout: object) -> object:
    return layout() if callable(layout) else layout


def _collect_text(component: object) -> str:
    parts: list[str] = []
    for item in _walk_components(component):
        if isinstance(item, str):
            parts.append(item)
    return " ".join(parts)


@pytest.mark.integration
def test_create_app_registers_primary_pages() -> None:
    from qcchem.workbench.app import create_app

    app = create_app()
    validation_layout = _resolve_layout(app.validation_layout)

    page_paths = {
        child.id["path"]
        for child in validation_layout.children
        if isinstance(getattr(child, "id", None), dict) and child.id.get("type") == "qcchem-page-validation"
    }

    assert "/" in page_paths
    assert set(page_paths) >= {route for route, _title, _builder in SCIENTIFIC_PAGE_MODULES.values()}


@pytest.mark.integration
def test_scientific_page_modules_render_real_content() -> None:
    for module_name, (_route, title, _builder) in SCIENTIFIC_PAGE_MODULES.items():
        module = importlib.import_module(module_name)
        page = _resolve_layout(module.layout)
        page_text = _collect_text(page)

        assert title in page_text
        assert "Placeholder Page" not in page_text


@pytest.mark.integration
def test_page_modules_expose_model_driven_builders() -> None:
    from qcchem.workbench.pages.overview import build_sample_view_model

    model = build_sample_view_model()
    model["hero"]["molecule_name"] = "Spec Probe"
    model["hero"]["total_energy"] = -9.8765
    model["hero"]["absolute_error"] = 0.1234
    model["runtime"]["backend_name"] = "backend-probe"
    model["runtime"]["transpiled_depth"] = 987
    model["runtime"]["returned_job_metadata"] = {"metadata": {"shots": 8192}}
    model["runtime"]["result_provenance"] = {"attempt_stage": "queued"}
    model["compression"]["method"] = "tensor_hypercontraction"
    model["compression"]["pre_term_count"] = 300
    model["compression"]["post_term_count"] = 21
    model["compression"]["rank"] = 5
    model["mapping"]["kind"] = "parity"
    model["confidence"]["verification_status"] = "review-probe"
    model["confidence"]["chemical_accuracy"] = {"available": True, "meets_chemical_accuracy": False}
    model["confidence"]["runtime_chemical_accuracy"] = {"available": True, "meets_chemical_accuracy": False}
    model["confidence"]["comparison_target"] = "probe-reference"
    model["confidence"]["boundary"]["comparison_target"] = "probe-reference"
    model["structure"]["active_space_metadata"] = {
        "num_active_orbitals": 6,
        "num_active_electrons": 8,
        "orbital_window": "Probe Window",
    }
    model["reduction"]["selection_mode"] = "manual_probe"
    model["reduction"]["selected_active_orbitals_original"] = [7, 8, 9]
    model["reduction"]["frozen_orbitals"] = [0, 2]

    expected_strings = {
        "qcchem.workbench.pages.overview": "Spec Probe",
        "qcchem.workbench.pages.structure_orbitals": "Probe Window",
        "qcchem.workbench.pages.active_space_compression": "tensor_hypercontraction",
        "qcchem.workbench.pages.mapping_resources": "Parity",
        "qcchem.workbench.pages.runtime_monitoring": "backend-probe",
        "qcchem.workbench.pages.result_confidence": "probe-reference",
    }

    for module_name, (_route, title, builder_name) in SCIENTIFIC_PAGE_MODULES.items():
        module = importlib.import_module(module_name)
        builder = getattr(module, builder_name)
        page = builder(model)
        page_text = _collect_text(page)

        assert title in page_text
        assert expected_strings[module_name] in page_text

    confidence_page = importlib.import_module("qcchem.workbench.pages.result_confidence").build_result_confidence_page(model)
    confidence_text = _collect_text(confidence_page)
    assert "Chemical accuracy False" in confidence_text
    assert "Runtime evidence available True" in confidence_text
    assert "Runtime chemical accuracy False" in confidence_text

    overview_module = importlib.import_module("qcchem.workbench.pages.overview")
    overview_page = overview_module.build_overview_page(model)
    overview_graph = next(component for component in _walk_components(overview_page) if component.__class__.__name__ == "Graph")
    overview_y = tuple(overview_graph.figure.data[0].y)
    assert overview_y[1] == pytest.approx(-9.8765)

    compression_module = importlib.import_module("qcchem.workbench.pages.active_space_compression")
    compression_page = compression_module.build_active_space_compression_page(model)
    compression_graph = next(component for component in _walk_components(compression_page) if component.__class__.__name__ == "Graph")
    assert tuple(compression_graph.figure.data[0].y) == (300, 21, 5)

    runtime_module = importlib.import_module("qcchem.workbench.pages.runtime_monitoring")
    runtime_page = runtime_module.build_runtime_monitoring_page(model)
    runtime_graph = next(component for component in _walk_components(runtime_page) if component.__class__.__name__ == "Graph")
    assert runtime_graph.figure.data[0].y[-1] == 987

    structure_module = importlib.import_module("qcchem.workbench.pages.structure_orbitals")
    structure_page = structure_module.build_structure_orbitals_page(model)
    structure_text = _collect_text(structure_page)
    assert "manual_probe" in structure_text
    assert "[0, 2]" in structure_text
    structure_graph = next(component for component in _walk_components(structure_page) if component.__class__.__name__ == "Graph")
    assert tuple(structure_graph.figure.data[0].x) == (0, 2, 7, 8, 9, 6)


@pytest.mark.integration
def test_result_confidence_treats_missing_runtime_accuracy_as_unknown_not_success() -> None:
    from qcchem.workbench.pages.overview import build_sample_view_model
    from qcchem.workbench.pages.result_confidence import build_result_confidence_page

    model = build_sample_view_model()
    model["confidence"]["runtime_chemical_accuracy"] = {"available": True}

    page = build_result_confidence_page(model)
    text = _collect_text(page)

    assert "Runtime evidence available True" in text
    assert "Runtime chemical accuracy Unknown" in text
    assert "Runtime chemical accuracy True" not in text


@pytest.mark.integration
def test_molecule_viewer_exposes_simple_model_contract_for_bridge() -> None:
    from qcchem.workbench.components.molecule import build_molecule_viewer

    viewer = build_molecule_viewer(
        {
            "atoms": [
                {"elem": "H", "x": 0.0, "y": 0.0, "z": 0.0},
                {"elem": "H", "x": 0.0, "y": 0.0, "z": 0.74},
            ],
            "style": {"stick": {}},
        },
        viewer_id="probe-viewer",
    )
    props = viewer.to_plotly_json()["props"]
    canvas = props["children"][2].to_plotly_json()["props"]

    assert props["id"] == "probe-viewer"
    assert props["data-molecule-json"]
    assert '"atoms"' in props["data-molecule-json"]
    assert "qcchem-molecule-viewer" in props["className"]
    assert canvas["id"] == "probe-viewer__canvas"


def test_three_dmol_bridge_asset_reads_molecule_payload() -> None:
    bridge = (REPO_ROOT / "qcchem" / "workbench" / "assets" / "3dmol-bridge.js").read_text(encoding="utf-8")

    assert "data-molecule-json" in bridge
    assert "3Dmol" in bridge
    assert "qcchem-molecule-viewer" in bridge
    assert "QCChem3DMol" in bridge
    assert "hydrate(id)" in bridge or "hydrate: function" in bridge or "hydrate(id" in bridge
    assert "payload.atoms" in bridge
    assert 'getElementById(id)' in bridge
    assert "mountNode.dataset[BRIDGE_FLAG] = \"invalid\"" in bridge
    assert "element.dataset" not in bridge
    assert "dataset.qcchemPayloadHash" in bridge
    assert "script.dataset.qcchem3dmolReady" in bridge or "qcchem3dmolReady" in bridge
    assert "querySelector(CANVAS_SELECTOR)" in bridge


@pytest.mark.integration
def test_three_dmol_bridge_node_smoke_handles_invalid_and_refresh(tmp_path: Path) -> None:
    bridge_path = REPO_ROOT / "qcchem" / "workbench" / "assets" / "3dmol-bridge.js"
    script_path = tmp_path / "bridge-smoke.js"
    script_path.write_text(
        textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");

            const bridgeCode = fs.readFileSync({json.dumps(str(bridge_path))}, "utf8");

            function makeMount(id, payload) {{
              const canvas = {{
                id: id + "__canvas",
                className: "qcchem-molecule-viewer__canvas",
                textContent: "",
                children: [],
                replaceChildren() {{ this.children = []; this.textContent = ""; }},
              }};
              return {{
                id,
                className: "qcchem-molecule-viewer",
                dataset: {{}},
                textContent: "",
                _payload: payload,
                getAttribute(name) {{
                  if (name === "data-molecule-json") return this._payload;
                  return null;
                }},
                setAttribute(name, value) {{
                  if (name === "data-molecule-json") this._payload = value;
                }},
                querySelector(selector) {{
                  if (selector === ".qcchem-molecule-viewer__canvas") return canvas;
                  return null;
                }},
                _canvas: canvas,
              }};
            }}

            const mounts = {{
              invalid: makeMount("invalid", "{{bad json"),
              refresh: makeMount("refresh", JSON.stringify({{ atoms: [{{ elem: "H", x: 0, y: 0, z: 0 }}] }})),
            }};

            const createdViewers = [];
            const scriptNode = {{
              id: "qcchem-3dmol-script",
              dataset: {{}},
              async: true,
              onload: null,
              onerror: null,
            }};

            const context = {{
              console,
              Promise,
              setTimeout,
              clearTimeout,
              window: {{}},
              document: {{
                readyState: "complete",
                head: {{
                  appendChild(node) {{
                    scriptNode.src = node.src;
                    scriptNode.onload = node.onload;
                    scriptNode.onerror = node.onerror;
                    if (typeof scriptNode.onload === "function") scriptNode.onload();
                  }},
                }},
                createElement() {{
                  return {{
                    id: "",
                    dataset: {{}},
                    async: true,
                    onload: null,
                    onerror: null,
                    src: "",
                  }};
                }},
                getElementById(id) {{
                  if (id === "qcchem-3dmol-script") return scriptNode;
                  return mounts[id] || null;
                }},
                querySelectorAll(selector) {{
                  if (selector === ".qcchem-molecule-viewer") return Object.values(mounts);
                  return [];
                }},
                addEventListener() {{}},
              }},
            }};

            context.window = context;
            context.$3Dmol = {{
              createViewer(target) {{
                const record = {{ targetId: target.id, addedAtoms: [], renderCount: 0 }};
                createdViewers.push(record);
                return {{
                  addModel() {{
                    return {{
                      addAtoms(atoms) {{
                        record.addedAtoms.push(atoms.length);
                      }},
                    }};
                  }},
                  setStyle() {{}},
                  addLabel() {{}},
                  zoomTo() {{}},
                  render() {{
                    record.renderCount += 1;
                  }},
                }};
              }},
            }};

            vm.createContext(context);
            vm.runInContext(bridgeCode, context);

            async function run() {{
              await context.QCChem3DMol.hydrate("invalid");
              const invalidState = {{
                flag: mounts.invalid.dataset.qcchemBridgeHydrated,
                text: mounts.invalid._canvas.textContent,
              }};

              await context.QCChem3DMol.hydrate("refresh");
              mounts.refresh.setAttribute("data-molecule-json", JSON.stringify({{ atoms: [{{ elem: "H", x: 0, y: 0, z: 0 }}, {{ elem: "H", x: 0, y: 0, z: 0.7 }}] }}));
              await context.QCChem3DMol.hydrate("refresh");

              process.stdout.write(JSON.stringify({{
                invalidState,
                refreshFlag: mounts.refresh.dataset.qcchemBridgeHydrated,
                refreshHash: mounts.refresh.dataset.qcchemPayloadHash,
                viewersCreated: createdViewers.length,
                lastViewer: createdViewers[createdViewers.length - 1],
              }}));
            }}

            run().catch((error) => {{
              console.error(error);
              process.exit(1);
            }});
            """
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        ["node", str(script_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["invalidState"]["flag"] == "invalid"
    assert payload["invalidState"]["text"] == "3Dmol viewer unavailable"
    assert payload["refreshFlag"] == "true"
    assert payload["viewersCreated"] >= 2
    assert payload["lastViewer"]["targetId"] == "refresh__canvas"
    assert payload["lastViewer"]["addedAtoms"] == [2]


def test_theme_tokens_include_scientific_atelier_palette_and_css_parity() -> None:
    theme_css = (REPO_ROOT / "qcchem" / "workbench" / "assets" / "theme.css").read_text(encoding="utf-8")

    assert THEME["surface"]["paper"] == "#f7f1e8"
    assert THEME["surface"]["card"] == "#fffaf3"
    assert THEME["accent"]["copper"] == "#9a6b3f"
    assert THEME["accent"]["deep_blue"] == "#20334a"
    for css_name, css_value in css_var_map(families=SHARED_THEME_FAMILIES).items():
        assert f"{css_name}: {css_value};" in theme_css
    assert "font-family: var(--qcchem-type-body);" in theme_css
    assert "font-family: var(--qcchem-type-display);" in theme_css


@pytest.mark.integration
def test_shell_layout_exposes_core_regions() -> None:
    from dash import dcc, html

    from qcchem.workbench.app import create_app

    app = create_app()
    shell = _resolve_layout(app.layout)
    validation_layout = _resolve_layout(app.validation_layout)

    assert isinstance(shell, html.Div)
    assert shell.className == "qcchem-shell"

    child_classes = {
        getattr(child, "className", None)
        for child in shell.children
        if getattr(child, "className", None) is not None
    }
    assert "qcchem-context-bar" in child_classes

    main_grid = next(child for child in shell.children if getattr(child, "className", "") == "qcchem-main-grid")
    main_grid_classes = [getattr(child, "className", None) for child in main_grid.children]

    assert "qcchem-research-navigator" in main_grid_classes
    assert "qcchem-interpretation-rail" in main_grid_classes
    assert any(isinstance(child, dcc.Location) for child in validation_layout.children)


@pytest.mark.integration
def test_validation_markers_do_not_call_parameterized_layout() -> None:
    from qcchem.workbench.pages._registry import build_validation_pages

    module = "tests.integration._parameterized_page_probe"

    def _layout(**_: object) -> None:
        raise AssertionError("validation markers should not execute page layouts")

    dash.page_registry.pop(module, None)
    dash.register_page(module, path="/parameterized-probe", name="Parameterized Probe", layout=_layout)
    try:
        markers = build_validation_pages()
    finally:
        dash.page_registry.pop(module, None)

    marker_paths = {
        marker.id["path"]
        for marker in markers
        if isinstance(getattr(marker, "id", None), dict) and marker.id.get("type") == "qcchem-page-validation"
    }
    assert "/parameterized-probe" in marker_paths


@pytest.mark.integration
def test_validation_layout_uses_current_page_registry_for_markers() -> None:
    from dash import html as dash_html

    from qcchem.workbench.app import create_app

    module = "tests.integration._late_validation_probe"
    dash.page_registry.pop(module, None)
    app = create_app()
    dash.register_page(module, path="/late-validation", name="Late Validation", layout=dash_html.Div("Late Validation"))
    try:
        validation_layout = _resolve_layout(app.validation_layout)
    finally:
        dash.page_registry.pop(module, None)

    marker_paths = {
        child.id["path"]
        for child in validation_layout.children
        if isinstance(getattr(child, "id", None), dict) and child.id.get("type") == "qcchem-page-validation"
    }
    assert "/late-validation" in marker_paths


@pytest.mark.integration
def test_shell_layout_uses_current_page_registry_for_navigation() -> None:
    from dash import dcc
    from dash import html as dash_html

    from qcchem.workbench.app import create_app

    module = "tests.integration._late_navigation_probe"
    dash.page_registry.pop(module, None)
    app = create_app()
    dash.register_page(module, path="/late-probe", name="Late Probe", layout=dash_html.Div("Late Probe"))
    try:
        shell = app.layout()
    finally:
        dash.page_registry.pop(module, None)

    hrefs = [component.href for component in _walk_components(shell) if isinstance(component, dcc.Link)]
    assert "/late-probe" in hrefs


@pytest.mark.integration
def test_serve_workbench_launches_app(monkeypatch: pytest.MonkeyPatch) -> None:
    from qcchem.workbench import server

    fake_app = SimpleNamespace()
    launched: dict[str, object] = {}

    monkeypatch.setattr(server, "create_app", lambda: fake_app)

    def _fake_launch(app: object, *, host: str, port: int, debug: bool) -> None:
        launched["app"] = app
        launched["host"] = host
        launched["port"] = port
        launched["debug"] = debug

    monkeypatch.setattr(server, "launch_app", _fake_launch)

    summary = server.serve_workbench(host="0.0.0.0", port=9010, debug=True)

    assert launched == {"app": fake_app, "host": "0.0.0.0", "port": 9010, "debug": True}
    assert summary["url"] == "http://0.0.0.0:9010"


@pytest.mark.integration
def test_workbench_server_main_prepares_prints_and_launches(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    from qcchem.workbench import server

    fake_app = object()
    events: list[tuple[str, object]] = []

    def _fake_prepare(host: str, port: int, debug: bool) -> tuple[object, dict[str, object]]:
        events.append(("prepare", (host, port, debug)))
        return fake_app, {"url": "http://0.0.0.0:9011", "pages": 2, "debug": True}

    def _fake_launch(app: object, *, host: str, port: int, debug: bool) -> None:
        events.append(("launch", (app, host, port, debug)))

    monkeypatch.setattr(server, "prepare_workbench", _fake_prepare)
    monkeypatch.setattr(server, "launch_app", _fake_launch)

    exit_code = server.main(["--host", "0.0.0.0", "--port", "9011", "--debug"])

    assert exit_code == 0
    assert events == [
        ("prepare", ("0.0.0.0", 9011, True)),
        ("launch", (fake_app, "0.0.0.0", 9011, True)),
    ]
    stdout = capsys.readouterr().out
    assert "QCchem workbench ready" in stdout
    assert "http://0.0.0.0:9011" in stdout
