from __future__ import annotations

from collections.abc import Iterable
import importlib
from pathlib import Path
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
    model["runtime"]["backend_name"] = "backend-probe"
    model["compression"]["method"] = "tensor_hypercontraction"
    model["mapping"]["kind"] = "parity"
    model["confidence"]["verification_status"] = "review-probe"
    model["structure"]["active_space_metadata"] = {
        "num_active_orbitals": 6,
        "orbital_window": "Probe Window",
    }

    expected_strings = {
        "qcchem.workbench.pages.overview": "Spec Probe",
        "qcchem.workbench.pages.structure_orbitals": "Probe Window",
        "qcchem.workbench.pages.active_space_compression": "tensor_hypercontraction",
        "qcchem.workbench.pages.mapping_resources": "Parity",
        "qcchem.workbench.pages.runtime_monitoring": "backend-probe",
        "qcchem.workbench.pages.result_confidence": "review-probe",
    }

    for module_name, (_route, title, builder_name) in SCIENTIFIC_PAGE_MODULES.items():
        module = importlib.import_module(module_name)
        builder = getattr(module, builder_name)
        page = builder(model)
        page_text = _collect_text(page)

        assert title in page_text
        assert expected_strings[module_name] in page_text


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
    assert canvas["data-molecule-json"]
    assert '"atoms"' in canvas["data-molecule-json"]
    assert "qcchem-molecule-viewer" in canvas["className"]


def test_three_dmol_bridge_asset_reads_molecule_payload() -> None:
    bridge = (REPO_ROOT / "qcchem" / "workbench" / "assets" / "3dmol-bridge.js").read_text(encoding="utf-8")

    assert "data-molecule-json" in bridge
    assert "3Dmol" in bridge
    assert "qcchem-molecule-viewer" in bridge
    assert "QCChem3DMol" in bridge
    assert "hydrate(id)" in bridge or "hydrate: function" in bridge or "hydrate(id" in bridge
    assert "payload.atoms" in bridge


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
