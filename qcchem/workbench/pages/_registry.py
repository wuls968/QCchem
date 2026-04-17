from __future__ import annotations

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
    dash.register_page(
        module,
        path=path,
        name=name,
        title=title,
        order=order,
        layout=_placeholder_layout(title, summary),
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
        "qcchem.workbench.pages.results",
        path="/results",
        name="Results",
        title="Results Atlas",
        summary="Reserved for scientific result slices once the page implementations arrive.",
        order=1,
    )

