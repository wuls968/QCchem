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


def ensure_pages_registered() -> None:
    _register_page(
        "qcchem.workbench.pages.overview",
        path="/overview",
        name="Overview",
        title="Overview",
        summary="Landing page for run-level narratives, system context, and key metrics.",
        order=0,
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
