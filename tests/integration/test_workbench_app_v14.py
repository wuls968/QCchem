from __future__ import annotations

from collections.abc import Iterable
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import textwrap
from types import SimpleNamespace

import dash
import pytest

from qcchem.workbench.theme import SHARED_THEME_FAMILIES, THEME, css_var_map

REPO_ROOT = Path(__file__).resolve().parents[2]


def _bounded_native_subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    for name in (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        env.setdefault(name, "1")
    env.setdefault("OMP_WAIT_POLICY", "PASSIVE")
    return env


SCIENTIFIC_PAGE_MODULES = {
    "qcchem.workbench.pages.overview": ("/overview", "Campaign Overview", "build_overview_page"),
    "qcchem.workbench.pages.structure_orbitals": ("/structure-orbitals", "Structure and Orbitals", "build_structure_orbitals_page"),
    "qcchem.workbench.pages.active_space_compression": ("/active-space-compression", "Active Space and Compression", "build_active_space_compression_page"),
    "qcchem.workbench.pages.mapping_resources": ("/mapping-resources", "Mapping, Resources, and Circuit", "build_mapping_resources_page"),
    "qcchem.workbench.pages.runtime_monitoring": ("/runtime-monitoring", "Runtime Monitoring", "build_runtime_monitoring_page"),
    "qcchem.workbench.pages.result_confidence": ("/result-confidence", "Result Confidence Report", "build_result_confidence_page"),
    "qcchem.workbench.pages.lr_ace_method": ("/lr-ace-method", "LR-ACE Method", "build_lr_ace_method_page"),
}
AGGREGATE_PAGE_MODULES = {
    "qcchem.workbench.pages.studies": ("/studies", "Studies", "build_studies_page"),
    "qcchem.workbench.pages.benchmarks": ("/benchmarks", "Benchmarks", "build_benchmarks_page"),
    "qcchem.workbench.pages.scans": ("/scans", "Scans", "build_scans_page"),
    "qcchem.workbench.pages.hardware_campaign": (
        "/hardware-campaign",
        "Hardware Campaign",
        "build_hardware_campaign_page",
    ),
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
    assert set(page_paths) >= {route for route, _title, _builder in AGGREGATE_PAGE_MODULES.values()}


@pytest.mark.integration
def test_scientific_page_modules_render_real_content() -> None:
    for module_name, (_route, title, _builder) in SCIENTIFIC_PAGE_MODULES.items():
        module = importlib.import_module(module_name)
        page = _resolve_layout(module.layout)
        page_text = _collect_text(page)

        assert title in page_text
        assert "Placeholder Page" not in page_text


@pytest.mark.integration
def test_aggregate_page_modules_render_real_content() -> None:
    for module_name, (_route, title, _builder) in AGGREGATE_PAGE_MODULES.items():
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
    model["confidence"]["chemical_accuracy"] = {
        "available": True,
        "meets_chemical_accuracy": False,
        "threshold_hartree": 0.0016,
    }
    model["confidence"]["runtime_chemical_accuracy"] = {
        "available": True,
        "meets_chemical_accuracy": False,
        "absolute_error_hartree": 0.0142,
        "threshold_hartree": 0.0016,
    }
    model["confidence"]["comparison_target"] = "probe-reference"
    model["confidence"]["boundary"]["comparison_target"] = "probe-reference"
    model["lr_ace"] = {
        "method_role": "flagship",
        "profile": "flagship_adaptive",
        "selected_factor_count": 3,
        "validation_gate": {
            "trust_label": "passed_exact_reference",
            "verification_status": "validated",
            "blocking_reason": None,
        },
        "local_accuracy_gate": {
            "passed": True,
            "absolute_error_hartree": 0.0004,
            "threshold_hartree": 0.0016,
        },
        "adaptive": {
            "enabled": True,
            "expansions": [
                {
                    "selected_count": 2,
                    "best_estimated_drop_hartree": 0.0123,
                }
            ],
        },
    }
    model["structure"]["active_space_metadata"] = {
        "num_active_orbitals": 6,
        "num_active_electrons": 8,
        "orbital_window": "Probe Window",
        "orbital_levels_ev": [-18.4, -11.2, -1.8, -0.6, 0.9],
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
        "qcchem.workbench.pages.lr_ace_method": "flagship_adaptive",
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
    assert "Evidence Capsule status" in confidence_text
    assert "Chemical accuracy False" in confidence_text
    assert "Runtime evidence available True" in confidence_text
    assert "Runtime chemical accuracy False" in confidence_text
    assert "Chemical accuracy threshold 0.0016 Ha" in confidence_text

    overview_module = importlib.import_module("qcchem.workbench.pages.overview")
    overview_page = overview_module.build_overview_page(model)
    overview_text = _collect_text(overview_page)
    assert "Research Objective" in overview_text
    assert "Claim compiler" in overview_text
    assert "Promotion gate" in overview_text
    overview_graph = next(component for component in _walk_components(overview_page) if component.__class__.__name__ == "Graph")
    assert len(overview_graph.figure.data) == 2
    assert tuple(overview_graph.figure.data[0].y) == pytest.approx((-9.8765,))
    assert tuple(overview_graph.figure.data[1].y) == pytest.approx((0.1234, 0.0142))
    assert overview_graph.figure.layout.yaxis.title.text == "Total energy (Hartree)"
    assert overview_graph.figure.layout.yaxis2.title.text == "Absolute error (Hartree)"
    assert "absolute-error evidence" in overview_graph.figure.layout.title.text.lower()

    compression_module = importlib.import_module("qcchem.workbench.pages.active_space_compression")
    compression_page = compression_module.build_active_space_compression_page(model)
    compression_graph = next(component for component in _walk_components(compression_page) if component.__class__.__name__ == "Graph")
    assert tuple(compression_graph.figure.data[0].y) == (300, 21, 5)

    runtime_module = importlib.import_module("qcchem.workbench.pages.runtime_monitoring")
    runtime_page = runtime_module.build_runtime_monitoring_page(model)
    runtime_text = _collect_text(runtime_page)
    runtime_graphs = [component for component in _walk_components(runtime_page) if component.__class__.__name__ == "Graph"]
    telemetry_graph = next(
        graph for graph in runtime_graphs if "Observed runtime and compilation telemetry" in graph.figure.layout.title.text
    )
    comparison_graph = next(
        graph for graph in runtime_graphs if "Simulator vs Hardware" in graph.figure.layout.title.text
    )
    comparison_values = tuple(comparison_graph.figure.data[0].y)

    assert "Simulator vs Hardware" in runtime_text
    assert "Comparison evidence" in runtime_text
    assert "Simulator reference" in runtime_text
    assert "Hardware backend" in runtime_text
    assert "Hardware verdict" in runtime_text
    telemetry_values = [
        value
        for trace in telemetry_graph.figure.data
        for value in (tuple(trace.y) if getattr(trace, "y", None) is not None else ())
    ]
    assert 8192 in telemetry_values
    assert 987 in telemetry_values
    assert comparison_graph.figure.data[0].x == ("Simulator", "Hardware")
    assert comparison_values == pytest.approx((0.0118, 0.0142))

    structure_module = importlib.import_module("qcchem.workbench.pages.structure_orbitals")
    structure_page = structure_module.build_structure_orbitals_page(model)
    structure_text = _collect_text(structure_page)
    assert "manual_probe" in structure_text
    assert "[0, 2]" in structure_text
    assert "[7, 8, 9]" in structure_text
    assert "orbital level" in structure_text.lower()
    structure_graph = next(component for component in _walk_components(structure_page) if component.__class__.__name__ == "Graph")
    assert tuple(structure_graph.figure.data[0].x) == (0, 1, 2, 3, 4)
    assert tuple(structure_graph.figure.data[0].y) == (-18.4, -11.2, -1.8, -0.6, 0.9)
    assert structure_graph.figure.layout.title.text == "Orbital energy ladder across the selected model window"


@pytest.mark.integration
def test_structure_orbitals_labels_original_indices_when_provided() -> None:
    from qcchem.workbench.pages.overview import build_sample_view_model
    from qcchem.workbench.pages.structure_orbitals import build_structure_orbitals_page

    model = build_sample_view_model()
    model["structure"]["active_space_metadata"] = {
        "num_active_orbitals": 5,
        "num_active_electrons": 2,
        "orbital_window": "Shifted window",
        "orbital_levels_ev": [-18.4, -11.2, -1.8, -0.6, 0.9],
        "orbital_indices_original": [5, 6, 7, 8, 9],
    }
    model["reduction"]["selected_active_orbitals_original"] = [7, 8, 9]
    model["reduction"]["selected_active_orbitals"] = [2, 3, 4]
    model["reduction"]["frozen_orbitals"] = [5]

    page = build_structure_orbitals_page(model)
    graph = next(component for component in _walk_components(page) if component.__class__.__name__ == "Graph")

    assert tuple(graph.figure.data[0].x) == (0, 1, 2, 3, 4)
    assert tuple(graph.figure.data[0].y) == (-18.4, -11.2, -1.8, -0.6, 0.9)
    assert tuple(graph.figure.data[0].marker.color) == ("#46607a", "#93a18a", "#9a6b3f", "#9a6b3f", "#9a6b3f")
    assert tuple(tuple(entry) for entry in graph.figure.data[0].customdata) == (
        (0, 5, "Frozen"),
        (1, 6, "Context"),
        (2, 7, "Active"),
        (3, 8, "Active"),
        (4, 9, "Active"),
    )
    assert tuple(graph.figure.layout.xaxis.ticktext) == (
        "pos 0 / orig 5",
        "pos 1 / orig 6",
        "pos 2 / orig 7",
        "pos 3 / orig 8",
        "pos 4 / orig 9",
    )


@pytest.mark.integration
def test_aggregate_pages_surface_real_content() -> None:
    from qcchem.workbench.pages.benchmarks import build_benchmarks_page, sample_benchmark_suite_model
    from qcchem.workbench.pages.hardware_campaign import (
        build_hardware_campaign_page,
        sample_hardware_campaign_model,
    )
    from qcchem.workbench.pages.scans import build_scans_page, sample_scan_model
    from qcchem.workbench.pages.studies import build_studies_page, sample_study_model

    study_page = build_studies_page(sample_study_model())
    study_text = _collect_text(study_page)
    assert "mini_comparison_study" in study_text
    assert "Run records" in study_text
    assert "backend.kind" in study_text

    benchmark_page = build_benchmarks_page(sample_benchmark_suite_model())
    benchmark_text = _collect_text(benchmark_page)
    assert "Validated" in benchmark_text
    assert "Exploratory" in benchmark_text
    assert "Unstable" in benchmark_text

    scan_page = build_scans_page(sample_scan_model())
    scan_text = _collect_text(scan_page)
    assert "bond_length" in scan_text
    assert "0.5" in scan_text
    assert "Scan points" in scan_text

    hardware_page = build_hardware_campaign_page(sample_hardware_campaign_model())
    hardware_text = _collect_text(hardware_page)
    assert "h2_runtime_hardware_probe_puccd_layout" in hardware_text
    assert "0.0137" in hardware_text
    assert "Runtime evidence status" in hardware_text


@pytest.mark.integration
def test_benchmark_page_uses_model_status_counts_in_chart() -> None:
    from qcchem.workbench.pages.benchmarks import build_benchmarks_page, sample_benchmark_suite_model

    model = sample_benchmark_suite_model()
    model["summary"]["status_counts"] = {"validated": 4, "exploratory": 2, "unstable": 1}

    page = build_benchmarks_page(model)
    graph = next(component for component in _walk_components(page) if component.__class__.__name__ == "Graph")

    assert tuple(graph.figure.data[0].x) == ("validated", "exploratory", "unstable")
    assert tuple(graph.figure.data[0].y) == (4, 2, 1)


@pytest.mark.integration
def test_study_page_uses_run_records_in_chart() -> None:
    from qcchem.workbench.pages.studies import build_studies_page, sample_study_model

    model = sample_study_model()
    model["run_records"] = [
        {
            "name": "exact_probe",
            "verification_status": "validated",
            "backend_kind": "statevector",
            "mapping_kind": "jordan_wigner",
            "policy_name": "benchmark",
            "total_energy": -1.23,
        },
        {
            "name": "runtime_probe",
            "verification_status": "exploratory",
            "backend_kind": "runtime",
            "mapping_kind": "parity",
            "policy_name": "hardware_ready",
            "total_energy": -1.11,
        },
    ]

    page = build_studies_page(model)
    graph = next(component for component in _walk_components(page) if component.__class__.__name__ == "Graph")

    assert tuple(graph.figure.data[0].x) == ("exact_probe", "runtime_probe")
    assert tuple(graph.figure.data[0].y) == pytest.approx((-1.23, -1.11))


@pytest.mark.integration
def test_scan_page_uses_points_in_curve() -> None:
    from qcchem.workbench.pages.scans import build_scans_page, sample_scan_model

    model = sample_scan_model()
    model["points"] = [
        {"point_label": "p0", "parameter_value": 0.4, "total_energy": -1.0, "verification_status": "validated"},
        {"point_label": "p1", "parameter_value": 0.8, "total_energy": -1.2, "verification_status": "validated"},
    ]

    page = build_scans_page(model)
    graph = next(component for component in _walk_components(page) if component.__class__.__name__ == "Graph")

    assert tuple(graph.figure.data[0].x) == pytest.approx((0.4, 0.8))
    assert tuple(graph.figure.data[0].y) == pytest.approx((-1.0, -1.2))
    assert tuple(graph.figure.data[0].customdata) == ("p0", "p1")


@pytest.mark.integration
def test_hardware_campaign_prefers_best_retrieved_case_over_submitted_case() -> None:
    from qcchem.reporting.hardware_campaign import build_hardware_campaign_summary
    from qcchem.workbench.pages.hardware_campaign import build_hardware_campaign_page

    model = build_hardware_campaign_summary(
        {
            "suite_name": "probe_suite",
            "summary": {"total_cases": 3, "runtime_evidence_status_counts": {"retrieved": 1, "submitted": 1, "failed": 1}},
            "cases": [
                {
                    "name": "submitted_low_error_case",
                    "achieved_error": 0.0021,
                    "runtime_evidence_status": "submitted",
                    "runtime_usage_seconds": 11.0,
                    "transpiled_depth": 100,
                    "backend_name": "ibm_probe",
                },
                {
                    "name": "retrieved_best_case",
                    "achieved_error": 0.0137,
                    "runtime_evidence_status": "retrieved_result",
                    "runtime_usage_seconds": 14.0,
                    "transpiled_depth": 120,
                    "backend_name": "ibm_probe",
                },
                {
                    "name": "failed_case",
                    "achieved_error": 0.0999,
                    "runtime_evidence_status": "failed",
                    "runtime_usage_seconds": 0.0,
                    "transpiled_depth": 140,
                    "backend_name": "ibm_probe",
                },
            ],
        }
    )

    page = build_hardware_campaign_page(model)
    detail_section = next(
        component
        for component in _walk_components(page)
        if getattr(component, "children", None)
        and component.__class__.__name__ == "Section"
        and "Best retrieved case" in _collect_text(component)
    )
    detail_text = _collect_text(detail_section)

    assert "retrieved_best_case" in detail_text
    assert "submitted_low_error_case" not in detail_text

    posture_section = next(
        component
        for component in _walk_components(page)
        if getattr(component, "children", None)
        and component.__class__.__name__ == "Section"
        and "Campaign posture" in _collect_text(component)
    )
    posture_text = _collect_text(posture_section)

    assert "0.0121 Ha" in posture_text


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
def test_result_confidence_treats_missing_primary_accuracy_as_unknown_not_success() -> None:
    from qcchem.workbench.pages.overview import build_sample_view_model
    from qcchem.workbench.pages.result_confidence import build_result_confidence_page

    model = build_sample_view_model()
    model["confidence"]["chemical_accuracy"] = {"available": True}

    page = build_result_confidence_page(model)
    text = _collect_text(page)

    assert "Chemical accuracy Unknown" in text
    assert "Chemical accuracy True" not in text


@pytest.mark.integration
def test_result_confidence_uses_benchmark_wording_without_chemical_accuracy_threshold() -> None:
    from qcchem.workbench.pages.overview import build_sample_view_model
    from qcchem.workbench.pages.result_confidence import build_result_confidence_page

    model = build_sample_view_model()
    model["confidence"]["chemical_accuracy"] = {"available": True, "meets_chemical_accuracy": False}

    page = build_result_confidence_page(model)
    text = _collect_text(page)
    graph = next(component for component in _walk_components(page) if component.__class__.__name__ == "Graph")

    assert "Benchmark threshold" in text
    assert "Chemical accuracy threshold" not in text
    assert "benchmark threshold" in graph.figure.layout.title.text.lower()


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
              failed: makeMount("failed", JSON.stringify({{ atoms: [{{ elem: "H", x: 0, y: 0, z: 0 }}] }})),
            }};
            let includeFailedInQuery = false;

            const createdViewers = [];
            let scriptPresent = false;
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
                    scriptPresent = true;
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
                  if (id === "qcchem-3dmol-script") return scriptPresent ? scriptNode : null;
                  return mounts[id] || null;
                }},
                querySelectorAll(selector) {{
                  if (selector === ".qcchem-molecule-viewer") {{
                    return includeFailedInQuery ? Object.values(mounts) : [mounts.invalid, mounts.refresh];
                  }}
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

              scriptNode.dataset = {{}};
              scriptPresent = false;
              includeFailedInQuery = true;
              context.$3Dmol = null;
              scriptNode.onerror = null;
              scriptNode.onload = null;
              context.document.head.appendChild = function(node) {{
                scriptPresent = true;
                scriptNode.src = node.src;
                scriptNode.onload = node.onload;
                scriptNode.onerror = node.onerror;
                if (typeof scriptNode.onerror === "function") scriptNode.onerror(new Error("load failure"));
              }};
              await context.QCChem3DMol.hydrate("failed");

              return {{
                invalidState,
                refreshFlag: mounts.refresh.dataset.qcchemBridgeHydrated,
                refreshHash: mounts.refresh.dataset.qcchemPayloadHash,
                viewersCreated: createdViewers.length,
                lastViewer: createdViewers[createdViewers.length - 1],
                failedText: mounts.failed._canvas.textContent,
              }};
            }}

            run()
              .then((payload) => {{
                process.stdout.write(JSON.stringify(payload));
              }})
              .catch((error) => {{
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
        env=_bounded_native_subprocess_env(),
    )
    payload = json.loads(result.stdout)

    assert payload["invalidState"]["flag"] == "invalid"
    assert payload["invalidState"]["text"] == "3Dmol viewer unavailable"
    assert payload["refreshFlag"] == "true"
    assert payload["viewersCreated"] >= 2
    assert payload["lastViewer"]["targetId"] == "refresh__canvas"
    assert payload["lastViewer"]["addedAtoms"] == [2]
    assert payload["failedText"] == "3Dmol viewer unavailable"


def test_theme_tokens_include_evidence_console_palette_and_css_parity() -> None:
    theme_css = (REPO_ROOT / "qcchem" / "workbench" / "assets" / "theme.css").read_text(encoding="utf-8")

    assert THEME["surface"]["paper"] == "#f2f4f8"
    assert THEME["surface"]["card"] == "#ffffff"
    assert THEME["accent"]["copper"] == "#0f62fe"
    assert THEME["accent"]["deep_blue"] == "#002d9c"
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
def test_shell_location_uses_spa_route_updates_for_direct_route_focus() -> None:
    from dash import dcc

    from qcchem.workbench.app import create_app
    from qcchem.workbench.components.layout import page_focus

    shell = _resolve_layout(create_app().layout)
    shell_location = next(
        component
        for component in _walk_components(shell)
        if isinstance(component, dcc.Location) and component.id == "qcchem-shell-location"
    )

    assert shell_location.refresh is False
    assert page_focus("/hardware-campaign")["route_label"] == "Hardware Campaign"
    assert page_focus("/ai-workspace")["route_label"] == "AI Workspace"
    assert page_focus("/workflow-studio")["route_label"] == "Workflow Studio"
    assert page_focus("/hardware-campaign")["route_label"] != page_focus("/overview")["route_label"]
    assert page_focus("/ai-workspace")["route_label"] != page_focus("/overview")["route_label"]
    assert page_focus("/workflow-studio")["route_label"] != page_focus("/overview")["route_label"]


@pytest.mark.integration
def test_shell_copy_uses_evidence_workbench_language() -> None:
    from qcchem.workbench.app import create_app

    shell = _resolve_layout(create_app().layout)
    shell_text = _collect_text(shell)

    assert "Evidence Workbench" in shell_text
    assert "Defended chemistry evidence" in shell_text
    assert "Scientific Atelier" not in shell_text


@pytest.mark.integration
def test_overview_page_leads_with_defended_claim_summary() -> None:
    from qcchem.workbench.pages.overview import build_overview_page, build_sample_view_model

    page = build_overview_page(build_sample_view_model())
    page_text = _collect_text(page)

    assert "Current defended claim" in page_text
    assert "Chemical accuracy target" in page_text
    assert "Runtime evidence status" in page_text


@pytest.mark.integration
def test_overview_page_surfaces_release_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from qcchem.workbench.data import WORKBENCH_ARTIFACT_ROOT_ENV
    from qcchem.workbench.pages.overview import build_overview_page, build_sample_view_model

    artifact_root = tmp_path / "artifacts"
    release_root = artifact_root / "release_evidence"
    release_root.mkdir(parents=True)
    verification_path = release_root / "release_artifact_verification.json"
    verification_path.write_text(
        json.dumps(
            {
                "schema_version": "qcchem.release_artifact_verification.v0.1-alpha",
                "status": "passed",
                "summary": {
                    "release_status_count": 6,
                    "diagnostics_manifest_count": 3,
                    "acceptance_status_count": 3,
                    "failure_count": 0,
                },
                "failures": [],
            }
        ),
        encoding="utf-8",
    )
    handoff_path = release_root / "release_evidence_handoff.md"
    (release_root / "release_evidence_summary.json").write_text(
        json.dumps(
            {
                "schema_version": "qcchem.release_evidence_collection.v0.1-alpha",
                "status": "passed",
                "recommended_action": "review_release_evidence",
                "first_failure": None,
                "release_artifact_verification": {
                    "matrix_artifacts": [
                        {"artifact_name": "qcchem-release-diagnostics-3.10", "status": "passed"},
                        {"artifact_name": "qcchem-release-diagnostics-3.11", "status": "passed"},
                    ]
                },
                "release_matrix_delta": {
                    "status": "changed",
                    "added": [],
                    "removed": [{"artifact_name": "qcchem-release-diagnostics-3.9"}],
                    "changed": [{"artifact_name": "qcchem-release-diagnostics-3.11"}],
                    "unchanged_count": 1,
                },
            }
        ),
        encoding="utf-8",
    )
    handoff_path.write_text("# QCchem Release Evidence Handoff\n", encoding="utf-8")
    monkeypatch.setenv(WORKBENCH_ARTIFACT_ROOT_ENV, str(artifact_root))

    page = build_overview_page(build_sample_view_model())
    page_text = _collect_text(page)

    assert "Release verification" in page_text
    assert "passed" in page_text
    assert "6 status bundles / 3 manifests / 3 sidecar reports; 0 failures" in page_text
    assert str(verification_path) in page_text
    assert "Release evidence handoff" in page_text
    assert "2 matrix artifacts / 0 failed" in page_text
    assert "delta=changed (1 changed, 0 added, 1 removed)" in page_text
    assert "review_release_evidence" in page_text
    assert "no first failure" in page_text
    assert str(handoff_path) in page_text


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
def test_prepare_workbench_reports_real_page_inventory_and_artifact_summary() -> None:
    from qcchem.workbench.server import prepare_workbench

    app, summary = prepare_workbench(host="127.0.0.1", port=8051, debug=False)

    assert app is not None
    assert summary["url"] == "http://127.0.0.1:8051"
    assert summary["default_route"] == "/overview"
    assert summary["page_count"] == len(summary["pages"])
    assert len(summary["pages"]) >= 10
    assert summary["pages"][0]["path"] == "/"
    assert summary["pages"][1]["path"] == "/overview"
    assert any(page["path"] == "/hardware-campaign" for page in summary["pages"])
    assert summary["artifact_root"].endswith("/artifacts")
    assert summary["artifact_inventory"]["run_result_roots"] >= 1
    assert summary["artifact_inventory"]["benchmark_suites"] >= 1
    assert summary["artifact_inventory"]["hardware_campaigns"] >= 1
    assert summary["artifact_inventory"]["featured_run"]
    assert summary["artifact_inventory"]["featured_hardware_campaign"]


@pytest.mark.integration
def test_workbench_artifact_root_defaults_to_current_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from qcchem.workbench.data import WORKBENCH_ARTIFACT_ROOT_ENV, resolve_workbench_artifact_root

    workspace = tmp_path / "workspace"
    artifact_root = workspace / "artifacts"
    artifact_root.mkdir(parents=True)
    monkeypatch.chdir(workspace)
    monkeypatch.delenv(WORKBENCH_ARTIFACT_ROOT_ENV, raising=False)

    assert resolve_workbench_artifact_root() == artifact_root.resolve()


@pytest.mark.integration
def test_workbench_artifact_root_rejects_missing_explicit_path(tmp_path: Path) -> None:
    from qcchem.workbench.data import resolve_workbench_artifact_root

    missing_root = tmp_path / "missing-artifacts"

    with pytest.raises(ValueError, match="artifact root does not exist"):
        resolve_workbench_artifact_root(missing_root)


@pytest.mark.integration
def test_prepare_workbench_accepts_explicit_artifact_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from qcchem.workbench.data import WORKBENCH_ARTIFACT_ROOT_ENV
    from qcchem.workbench.server import prepare_workbench

    artifact_root = tmp_path / "artifacts"
    run_root = artifact_root / "custom_run"
    run_root.mkdir(parents=True)
    (run_root / "result.json").write_text("{}", encoding="utf-8")
    (run_root / "report.md").write_text("# report\n", encoding="utf-8")
    release_root = artifact_root / "release_evidence"
    release_root.mkdir()
    (release_root / "release_artifact_verification.json").write_text(
        json.dumps(
            {
                "schema_version": "qcchem.release_artifact_verification.v0.1-alpha",
                "status": "passed",
                "summary": {
                    "release_status_count": 6,
                    "diagnostics_manifest_count": 3,
                    "acceptance_status_count": 3,
                    "failure_count": 0,
                },
                "failures": [],
            }
        ),
        encoding="utf-8",
    )
    (release_root / "release_evidence_summary.json").write_text(
        json.dumps(
            {
                "schema_version": "qcchem.release_evidence_collection.v0.1-alpha",
                "status": "passed",
                "recommended_action": "review_release_evidence",
                "first_failure": None,
            }
        ),
        encoding="utf-8",
    )
    (release_root / "release_evidence_handoff.md").write_text(
        "# QCchem Release Evidence Handoff\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(WORKBENCH_ARTIFACT_ROOT_ENV, "")

    _app, summary = prepare_workbench(
        host="127.0.0.1",
        port=8051,
        debug=False,
        artifact_root=artifact_root,
    )

    assert summary["artifact_root"] == str(artifact_root.resolve())
    assert summary["artifact_inventory"]["artifact_root_exists"] is True
    assert summary["artifact_inventory"]["indexed_artifacts"] == 3
    assert summary["artifact_inventory"]["run_result_roots"] == 1
    assert summary["artifact_inventory"]["release_artifact_verifications"] == 1
    assert summary["artifact_inventory"]["release_evidence_handoffs"] == 1
    assert summary["artifact_inventory"]["report_markdown_roots"] == 1
    assert summary["artifact_inventory"]["featured_release_artifact_verification"] == str(
        release_root / "release_artifact_verification.json"
    )
    assert summary["artifact_inventory"]["featured_release_evidence_handoff"] == str(
        release_root / "release_evidence_handoff.md"
    )
    assert os.environ[WORKBENCH_ARTIFACT_ROOT_ENV] == str(artifact_root.resolve())


@pytest.mark.integration
def test_prepare_workbench_skips_nested_preview_local_inventory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from qcchem.workbench.data import WORKBENCH_ARTIFACT_ROOT_ENV
    from qcchem.workbench.server import prepare_workbench

    artifact_root = tmp_path / "artifacts"
    curated = artifact_root / "curated_run"
    preview = curated / "preview_local"
    preview.mkdir(parents=True)
    (curated / "result.json").write_text("{}", encoding="utf-8")
    (curated / "report.md").write_text("# report\n", encoding="utf-8")
    (curated / "runtime_submission.json").write_text("{}", encoding="utf-8")
    (preview / "result.json").write_text("{}", encoding="utf-8")
    (preview / "report.md").write_text("# preview\n", encoding="utf-8")
    (preview / "runtime_submission.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv(WORKBENCH_ARTIFACT_ROOT_ENV, "")

    _app, summary = prepare_workbench(
        host="127.0.0.1",
        port=8051,
        debug=False,
        artifact_root=artifact_root,
    )
    inventory = summary["artifact_inventory"]

    assert inventory["artifact_root_exists"] is True
    assert inventory["artifact_root_is_dir"] is True
    assert inventory["inventory_error"] is None
    assert inventory["run_result_roots"] == 1
    assert inventory["report_markdown_roots"] == 1
    assert inventory["runtime_submission_sidecars"] == 1
    assert inventory["skipped_generated_artifacts"] == 1
    assert inventory["featured_run"] == str(curated / "result.json")


@pytest.mark.integration
def test_workbench_artifact_inventory_reports_file_root(tmp_path: Path) -> None:
    from qcchem.workbench import server

    artifact_root = tmp_path / "artifacts"
    artifact_root.write_text("not a directory", encoding="utf-8")

    inventory = server._artifact_inventory(artifact_root)

    assert inventory["artifact_root_exists"] is True
    assert inventory["artifact_root_is_dir"] is False
    assert inventory["inventory_error"] == "Artifact root is not a directory."
    assert inventory["run_result_roots"] == 0
    assert inventory["skipped_generated_artifacts"] == 0


@pytest.mark.integration
def test_workbench_docs_cover_registered_routes() -> None:
    from qcchem.workbench.server import prepare_workbench

    _app, summary = prepare_workbench(host="127.0.0.1", port=8051, debug=False)
    docs = (REPO_ROOT / "docs" / "workbench.md").read_text(encoding="utf-8")
    page_order_match = re.search(r"## Page Order\n\n(?P<body>.*?)(?=\n## )", docs, flags=re.S)

    assert page_order_match is not None

    documented_routes = re.findall(r"^\d+\. `([^`]+)`", page_order_match.group("body"), flags=re.M)
    registered_routes = [str(page["path"]) for page in summary["pages"] if page["path"] != "/"]

    assert documented_routes == registered_routes


@pytest.mark.integration
def test_workbench_smoke_checklist_matches_rendered_pages() -> None:
    from qcchem.workbench.smoke import run_workbench_smoke_from_docs

    summary = run_workbench_smoke_from_docs(REPO_ROOT / "docs" / "workbench.md")

    assert summary["status"] == "passed"
    assert summary["scope"] == "component_tree"
    assert summary["failed_checks"] == []
    assert summary["route_count"] == 6
    assert summary["failed_routes"] == 0
    assert summary["page_count"] == 14
    assert summary["failed_pages"] == 0
    assert "/overview" in summary["registered_routes"]
    assert [route["route"] for route in summary["routes"]] == [
        "/overview",
        "/result-confidence",
        "/benchmarks",
        "/hardware-campaign",
        "/ai-workspace",
        "/workflow-studio",
    ]
    assert all(route["checks"]["registered"] for route in summary["routes"])
    assert all(route["checks"]["active_label"] for route in summary["routes"])
    assert all(route["checks"]["expected_text"] for route in summary["routes"])
    assert all(route["page_title"] for route in summary["routes"])
    assert all(route["text_excerpt"] for route in summary["routes"])
    assert all(route["failed_checks"] == [] for route in summary["routes"])
    assert all(page["checks"]["nonblank"] for page in summary["pages"])
    assert all(page["checks"]["not_placeholder"] for page in summary["pages"])
    assert all(page["checks"]["active_label"] for page in summary["pages"])
    assert all(page["checks"]["title_text"] for page in summary["pages"])
    assert all(page["text_excerpt"] for page in summary["pages"])
    assert all(page["failed_checks"] == [] for page in summary["pages"])


@pytest.mark.integration
def test_workbench_smoke_summary_records_artifact_root() -> None:
    from qcchem.workbench.smoke import run_workbench_smoke_from_docs

    artifact_root = REPO_ROOT / "artifacts"
    summary = run_workbench_smoke_from_docs(
        REPO_ROOT / "docs" / "workbench.md",
        artifact_root=artifact_root,
    )

    assert summary["status"] == "passed"
    assert summary["artifact_root"] == str(artifact_root.resolve())
    assert summary["release_verification"]["status"] in {"missing", "passed", "failed"}


@pytest.mark.integration
def test_workbench_smoke_summary_records_release_verification(tmp_path: Path) -> None:
    from qcchem.workbench.smoke import run_workbench_smoke_from_docs

    artifact_root = tmp_path / "artifacts"
    release_root = artifact_root / "release_evidence"
    release_root.mkdir(parents=True)
    verification_path = release_root / "release_artifact_verification.json"
    verification_path.write_text(
        json.dumps(
            {
                "schema_version": "qcchem.release_artifact_verification.v0.1-alpha",
                "status": "passed",
                "summary": {
                    "release_status_count": 6,
                    "diagnostics_manifest_count": 3,
                    "acceptance_status_count": 3,
                    "failure_count": 0,
                },
                "failures": [],
            }
        ),
        encoding="utf-8",
    )

    summary = run_workbench_smoke_from_docs(
        REPO_ROOT / "docs" / "workbench.md",
        artifact_root=artifact_root,
    )

    release_verification = summary["release_verification"]
    assert summary["status"] == "passed"
    assert release_verification["available"] is True
    assert release_verification["status"] == "passed"
    assert release_verification["source_path"] == str(verification_path)
    assert release_verification["release_status_count"] == 6
    assert release_verification["diagnostics_manifest_count"] == 3
    assert release_verification["acceptance_status_count"] == 3
    assert release_verification["failure_count"] == 0
    assert release_verification["first_failure"] is None


@pytest.mark.integration
def test_workbench_smoke_restores_artifact_root_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from qcchem.workbench.data import WORKBENCH_ARTIFACT_ROOT_ENV
    from qcchem.workbench.smoke import run_workbench_smoke_from_docs

    original_root = tmp_path / "original"
    smoke_root = tmp_path / "smoke"
    original_root.mkdir()
    smoke_root.mkdir()
    monkeypatch.setenv(WORKBENCH_ARTIFACT_ROOT_ENV, str(original_root))

    summary = run_workbench_smoke_from_docs(REPO_ROOT / "docs" / "workbench.md", artifact_root=smoke_root)

    assert summary["status"] == "passed"
    assert summary["artifact_root"] == str(smoke_root.resolve())
    assert os.environ[WORKBENCH_ARTIFACT_ROOT_ENV] == str(original_root)


@pytest.mark.integration
def test_workbench_smoke_collects_text_from_top_level_component_lists() -> None:
    from dash import html

    from qcchem.workbench.smoke import _collect_text

    assert _collect_text([html.Div("Alpha"), html.Div(["Beta", html.Span("Gamma")])]) == "Alpha Beta Gamma"


@pytest.mark.integration
def test_workbench_smoke_reports_documented_text_drift(tmp_path: Path) -> None:
    from qcchem.workbench.smoke import run_workbench_smoke_from_docs

    docs = tmp_path / "workbench.md"
    docs.write_text(
        textwrap.dedent(
            """
            # Probe

            ## Browser Smoke Checklist

            | Route | Active route label | Route-specific text to confirm |
            | --- | --- | --- |
            | `/overview` | Overview | Text that should not exist |
            """
        ).strip(),
        encoding="utf-8",
    )

    summary = run_workbench_smoke_from_docs(docs)

    assert summary["status"] == "failed"
    assert summary["failed_checks"] == ["route:/overview:expected_text"]
    assert summary["failed_routes"] == 1
    assert summary["failed_pages"] == 0
    route = summary["routes"][0]
    assert route["route"] == "/overview"
    assert route["checks"]["registered"] is True
    assert route["checks"]["active_label"] is True
    assert route["checks"]["expected_text"] is False
    assert route["failed_checks"] == ["expected_text"]
    assert route["text_excerpt"]
    assert "Text that should not exist" not in route["text_excerpt"]


@pytest.mark.integration
def test_workbench_smoke_reports_missing_documented_route_with_registered_routes(tmp_path: Path) -> None:
    from qcchem.workbench.smoke import run_workbench_smoke_from_docs

    docs = tmp_path / "workbench.md"
    docs.write_text(
        textwrap.dedent(
            """
            # Probe

            ## Browser Smoke Checklist

            | Route | Active route label | Route-specific text to confirm |
            | --- | --- | --- |
            | `/missing-route` | Missing | Missing page text |
            """
        ).strip(),
        encoding="utf-8",
    )

    summary = run_workbench_smoke_from_docs(docs)
    route = summary["routes"][0]

    assert summary["status"] == "failed"
    assert "/overview" in summary["registered_routes"]
    assert route["route"] == "/missing-route"
    assert route["checks"]["registered"] is False
    assert "registered" in route["failed_checks"]
    assert route["page_title"] is None
    assert route["text_excerpt"] == ""


@pytest.mark.integration
def test_workbench_smoke_reports_layout_render_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from qcchem.cli.main import main
    from qcchem.workbench import app as workbench_app

    def broken_layout() -> object:
        raise RuntimeError("broken overview render")

    fake_app = SimpleNamespace(
        page_registry={
            "overview": {
                "path": "/overview",
                "name": "overview",
                "title": "Overview",
                "order": 0,
                "layout": broken_layout,
            }
        }
    )
    monkeypatch.setattr(workbench_app, "create_app", lambda: fake_app)
    docs = tmp_path / "workbench.md"
    output = tmp_path / "workbench_smoke.json"
    docs.write_text(
        textwrap.dedent(
            """
            # Probe

            ## Browser Smoke Checklist

            | Route | Active route label | Route-specific text to confirm |
            | --- | --- | --- |
            | `/overview` | Overview | Current defended claim |
            """
        ).strip(),
        encoding="utf-8",
    )

    exit_code = main(["workbench", "smoke", "--docs", str(docs), "-o", str(output)])

    assert exit_code == 2
    stdout = capsys.readouterr().out
    assert "Failed checks: route:/overview:rendered" in stdout
    assert "Failed route: /overview failed_checks=rendered,nonblank,expected_text" in stdout
    assert "render_error='RuntimeError: broken overview render'" in stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert "route:/overview:rendered" in payload["failed_checks"]
    assert "page:/overview:rendered" in payload["failed_checks"]
    route = payload["routes"][0]
    page = payload["pages"][0]
    assert route["checks"]["registered"] is True
    assert route["checks"]["rendered"] is False
    assert route["render_error"] == "RuntimeError: broken overview render"
    assert page["checks"]["rendered"] is False
    assert page["render_error"] == "RuntimeError: broken overview render"


@pytest.mark.integration
def test_workbench_smoke_rejects_malformed_checklist_route_row(tmp_path: Path) -> None:
    from qcchem.workbench.smoke import run_workbench_smoke_from_docs

    docs = tmp_path / "workbench.md"
    docs.write_text(
        textwrap.dedent(
            """
            # Probe

            ## Browser Smoke Checklist

            | Route | Active route label | Route-specific text to confirm |
            | --- | --- | --- |
            | /overview | Overview | Current defended claim |
            """
        ).strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="malformed route row"):
        run_workbench_smoke_from_docs(docs)


@pytest.mark.integration
def test_workbench_smoke_rejects_duplicate_documented_routes(tmp_path: Path) -> None:
    from qcchem.workbench.smoke import run_workbench_smoke_from_docs

    docs = tmp_path / "workbench.md"
    docs.write_text(
        textwrap.dedent(
            """
            # Probe

            ## Browser Smoke Checklist

            | Route | Active route label | Route-specific text to confirm |
            | --- | --- | --- |
            | `/overview` | Overview | Current defended claim |
            | `/overview` | Overview | Current defended claim |
            """
        ).strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate route: /overview"):
        run_workbench_smoke_from_docs(docs)


@pytest.mark.integration
def test_workbench_smoke_cli_uses_docs_checklist(capsys: pytest.CaptureFixture[str]) -> None:
    from qcchem.cli.main import main

    exit_code = main(["workbench", "smoke", "--docs", str(REPO_ROOT / "docs" / "workbench.md")])

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "Workbench smoke completed: passed" in stdout
    assert "Routes: 6 passed, 0 failed" in stdout
    assert "Registered pages: 14 passed, 0 failed" in stdout


@pytest.mark.integration
def test_workbench_smoke_cli_reports_failed_check_names(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from qcchem.cli.main import main

    docs = tmp_path / "workbench.md"
    docs.write_text(
        textwrap.dedent(
            """
            # Probe

            ## Browser Smoke Checklist

            | Route | Active route label | Route-specific text to confirm |
            | --- | --- | --- |
            | `/overview` | Overview | Text that should not exist |
            """
        ).strip(),
        encoding="utf-8",
    )

    exit_code = main(["workbench", "smoke", "--docs", str(docs)])

    assert exit_code == 2
    stdout = capsys.readouterr().out
    assert "Workbench smoke completed: failed" in stdout
    assert "Failed checks: route:/overview:expected_text" in stdout
    assert "Failed route: /overview failed_checks=expected_text" in stdout
    assert "text_excerpt=" in stdout


@pytest.mark.integration
def test_workbench_smoke_cli_rejects_missing_docs_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from qcchem.cli.main import main

    exit_code = main(["workbench", "smoke", "--docs", str(tmp_path / "missing_workbench.md")])

    assert exit_code == 2
    stdout = capsys.readouterr().out
    assert "QCchem workbench smoke rejected:" in stdout
    assert "missing_workbench.md" in stdout


@pytest.mark.integration
def test_workbench_smoke_cli_rejects_missing_artifact_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from qcchem.cli.main import main

    exit_code = main(
        [
            "workbench",
            "smoke",
            "--docs",
            str(REPO_ROOT / "docs" / "workbench.md"),
            "--artifact-root",
            str(tmp_path / "missing-artifacts"),
        ]
    )

    assert exit_code == 2
    stdout = capsys.readouterr().out
    assert "QCchem workbench smoke rejected:" in stdout
    assert "artifact root does not exist" in stdout


@pytest.mark.integration
def test_workbench_smoke_cli_can_write_json_summary(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from qcchem.cli.main import main

    output = tmp_path / "workbench_smoke.json"
    exit_code = main(
        [
            "workbench",
            "smoke",
            "--docs",
            str(REPO_ROOT / "docs" / "workbench.md"),
            "-o",
            str(output),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "passed"
    assert payload["schema_version"] == "qcchem.workbench_smoke.v0.1-alpha"
    assert payload["failed_checks"] == []
    assert payload["route_count"] == 6
    assert payload["failed_routes"] == 0
    assert payload["page_count"] == 14
    assert payload["failed_pages"] == 0
    assert "/overview" in payload["registered_routes"]
    assert payload["release_verification"]["status"] in {"missing", "passed", "failed"}
    assert payload["routes"][0]["text_excerpt"]
    assert payload["pages"][0]["text_excerpt"]
    assert "Workbench smoke summary written" in capsys.readouterr().out


@pytest.mark.integration
def test_workbench_smoke_cli_accepts_artifact_root(tmp_path: Path) -> None:
    from qcchem.cli.main import main

    output = tmp_path / "workbench_smoke.json"
    exit_code = main(
        [
            "workbench",
            "smoke",
            "--docs",
            str(REPO_ROOT / "docs" / "workbench.md"),
            "--artifact-root",
            str(REPO_ROOT / "artifacts"),
            "-o",
            str(output),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "passed"
    assert payload["artifact_root"] == str((REPO_ROOT / "artifacts").resolve())


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
def test_serve_workbench_reports_real_page_inventory(monkeypatch: pytest.MonkeyPatch) -> None:
    from qcchem.workbench import server

    monkeypatch.setattr(server, "launch_app", lambda app, *, host, port, debug: None)

    summary = server.serve_workbench(host="127.0.0.1", port=8051, debug=False)

    assert summary["page_count"] >= 10
    assert len(summary["pages"]) == summary["page_count"]
    assert summary["pages"][0]["path"] == "/"
    assert summary["pages"][1]["path"] == "/overview"
    assert summary["default_route"] == "/overview"
    assert Path(summary["artifact_root"]).name == "artifacts"
    assert summary["artifact_inventory"]["artifact_root_exists"] is True
    assert summary["artifact_inventory"]["run_result_roots"] >= 1
    assert summary["artifact_inventory"]["report_markdown_roots"] >= 1
    assert summary["artifact_inventory"]["runtime_submission_sidecars"] >= 1


@pytest.mark.integration
def test_workbench_server_main_prepares_prints_and_launches(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    from qcchem.workbench import server

    fake_app = object()
    events: list[tuple[str, object]] = []

    def _fake_prepare(
        host: str,
        port: int,
        debug: bool,
        artifact_root: Path | None = None,
    ) -> tuple[object, dict[str, object]]:
        events.append(("prepare", (host, port, debug, artifact_root)))
        return fake_app, {
            "url": "http://0.0.0.0:9011",
            "pages": 2,
            "default_route": "/overview",
            "artifact_root": "/tmp/qcchem-artifacts",
            "artifact_inventory": {
                "run_result_roots": 1,
                "benchmark_suites": 1,
                "study_results": 1,
                "scan_results": 1,
                "hardware_campaigns": 1,
            },
            "debug": True,
        }

    def _fake_launch(app: object, *, host: str, port: int, debug: bool) -> None:
        events.append(("launch", (app, host, port, debug)))

    monkeypatch.setattr(server, "prepare_workbench", _fake_prepare)
    monkeypatch.setattr(server, "launch_app", _fake_launch)

    exit_code = server.main(["--host", "0.0.0.0", "--port", "9011", "--debug"])

    assert exit_code == 0
    assert events == [
        ("prepare", ("0.0.0.0", 9011, True, None)),
        ("launch", (fake_app, "0.0.0.0", 9011, True)),
    ]
    stdout = capsys.readouterr().out
    assert "QCchem workbench ready" in stdout
    assert "http://0.0.0.0:9011" in stdout
    assert "/overview" in stdout
