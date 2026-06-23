from __future__ import annotations

import importlib

import dash
from dash import html


def _placeholder_layout(title: str, summary: str) -> html.Div:
    return html.Div(
        className="qcchem-page-placeholder",
        children=[
            html.P("Placeholder Page", className="qcchem-panel__eyebrow"),
            html.H2(title, className="qcchem-page-placeholder__title"),
            html.P(summary, className="qcchem-page-placeholder__body"),
        ],
    )


def _register_page(module: str, *, path: str, name: str, title: str, summary: str, order: int) -> None:
    if module in dash.page_registry:
        return
    module_object = importlib.import_module(module)
    dash.register_page(
        module,
        path=path,
        name=name,
        title=title,
        order=order,
        description=summary,
        layout=getattr(module_object, "layout", _placeholder_layout(title, summary)),
    )


def _register_alias_page(
    module: str,
    *,
    layout_module: str,
    path: str,
    name: str,
    title: str,
    summary: str,
    order: int,
) -> None:
    if module in dash.page_registry:
        return
    module_object = importlib.import_module(layout_module)
    dash.register_page(
        module,
        path=path,
        name=name,
        title=title,
        order=order,
        description=summary,
        layout=getattr(module_object, "layout", _placeholder_layout(title, summary)),
    )


def ensure_pages_registered() -> None:
    _register_alias_page(
        "qcchem.workbench.pages.home",
        layout_module="qcchem.workbench.pages.overview",
        path="/",
        name="Home",
        title="Overview",
        summary="Landing page for run-level narratives, system context, and key metrics.",
        order=0,
    )
    _register_page(
        "qcchem.workbench.pages.overview",
        path="/overview",
        name="Overview",
        title="Overview",
        summary="Landing page for run-level narratives, system context, and key metrics.",
        order=1,
    )
    _register_page(
        "qcchem.workbench.pages.structure_orbitals",
        path="/structure-orbitals",
        name="Structure",
        title="Structure and Orbitals",
        summary="Geometry context, orbital windows, and structure-driven interpretation.",
        order=1,
    )
    _register_page(
        "qcchem.workbench.pages.active_space_compression",
        path="/active-space-compression",
        name="Active Space",
        title="Active Space and Compression",
        summary="Reduction audits, active-space boundaries, and low-rank operator posture.",
        order=2,
    )
    _register_page(
        "qcchem.workbench.pages.mapping_resources",
        path="/mapping-resources",
        name="Mapping",
        title="Mapping, Resources, and Circuit",
        summary="Mapping choice, tapering savings, and compiled-circuit burden.",
        order=3,
    )
    _register_page(
        "qcchem.workbench.pages.runtime_monitoring",
        path="/runtime-monitoring",
        name="Runtime",
        title="Runtime Monitoring",
        summary="Runtime submission evidence, operational telemetry, and compile posture.",
        order=4,
    )
    _register_page(
        "qcchem.workbench.pages.result_confidence",
        path="/result-confidence",
        name="Confidence",
        title="Result Confidence Report",
        summary="Accuracy boundary, verification status, and report-grade scientific confidence.",
        order=5,
    )
    _register_page(
        "qcchem.workbench.pages.lr_ace_method",
        path="/lr-ace-method",
        name="LR-ACE",
        title="LR-ACE Method",
        summary="Flagship LR-ACE generator plan, adaptive provenance, and trust-first validation gate.",
        order=6,
    )
    _register_page(
        "qcchem.workbench.pages.studies",
        path="/studies",
        name="Studies",
        title="Studies",
        summary="Aggregate study comparisons across defended runs, exploratory probes, and campaign axes.",
        order=7,
    )
    _register_page(
        "qcchem.workbench.pages.benchmarks",
        path="/benchmarks",
        name="Benchmarks",
        title="Benchmarks",
        summary="Benchmark suite control surface with status bands, defended scope, and exploratory separation.",
        order=8,
    )
    _register_page(
        "qcchem.workbench.pages.scans",
        path="/scans",
        name="Scans",
        title="Scans",
        summary="Aggregate parameter-scan view across validated-like and exploratory sweep points.",
        order=9,
    )
    _register_page(
        "qcchem.workbench.pages.hardware_campaign",
        path="/hardware-campaign",
        name="Hardware Campaign",
        title="Hardware Campaign",
        summary="Hardware runtime campaign ranking, best-case evidence, and runtime status posture.",
        order=10,
    )
    _register_page(
        "qcchem.workbench.pages.ai_workspace",
        path="/ai-workspace",
        name="AI Workspace",
        title="AI Workspace",
        summary="Task-centric AI ticket surface for drafting, review lanes, and provider shell controls.",
        order=11,
    )
    _register_page(
        "qcchem.workbench.pages.workflow_studio",
        path="/workflow-studio",
        name="Workflow Studio",
        title="Workflow Studio",
        summary="Split Studio for YAML-first custom workflows, plugin palette, derived graph, and run artifacts.",
        order=12,
    )


def build_validation_pages() -> list[html.Div]:
    validation_pages: list[html.Div] = []
    for page in dash.page_registry.values():
        path = page.get("path")
        if not path:
            continue
        validation_pages.append(
            html.Div(
                id={"type": "qcchem-page-validation", "path": path},
                children=page.get("name", path),
            )
        )
    return validation_pages
