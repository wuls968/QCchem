from __future__ import annotations

from collections.abc import Sequence

from dash import dcc, html, page_container, page_registry

from qcchem.workbench.components.cards import callout_card, metric_card


def build_context_bar() -> html.Header:
    return html.Header(
        className="qcchem-context-bar",
        children=[
            html.Div(
                className="qcchem-context-bar__identity",
                children=[
                    html.P("QCchem Visual Workbench", className="qcchem-context-bar__eyebrow"),
                    html.H1("Scientific Atelier", className="qcchem-context-bar__title"),
                    html.P(
                        "Precision Atlas shell for interpreting runs, studies, and runtime evidence.",
                        className="qcchem-context-bar__subtitle",
                    ),
                ],
            ),
            html.Div(
                className="qcchem-context-bar__metrics",
                children=[
                    metric_card("Mode", "Workbench v14", "Shared visual system", tone="compact"),
                    metric_card("Focus", "Task 3", "Shell and theme only", tone="compact"),
                ],
            ),
        ],
    )


def build_research_navigator() -> html.Aside:
    nav_links = [
        dcc.Link(
            page["name"],
            href=page["path"],
            className="qcchem-research-navigator__link",
        )
        for page in page_registry.values()
    ]
    return html.Aside(
        className="qcchem-research-navigator",
        children=[
            html.Div(
                className="qcchem-panel",
                children=[
                    html.P("Research Navigator", className="qcchem-panel__eyebrow"),
                    html.H2("Atlas routes", className="qcchem-panel__title"),
                    html.Nav(children=nav_links, className="qcchem-research-navigator__links"),
                ],
            ),
        ],
    )


def build_interpretation_rail() -> html.Aside:
    return html.Aside(
        className="qcchem-interpretation-rail",
        children=[
            html.Div(
                className="qcchem-panel",
                children=[
                    html.P("Interpretation Rail", className="qcchem-panel__eyebrow"),
                    html.H2("Reading guide", className="qcchem-panel__title"),
                    callout_card(
                        "Narrative-ready shell",
                        "This rail is reserved for experiment confidence, curation notes, and export cues in later tasks.",
                    ),
                ],
            ),
        ],
    )


def build_page_frame(children: Sequence[html.Component] | html.Component) -> html.Main:
    return html.Main(className="qcchem-page-frame", children=children)


def build_shell() -> html.Div:
    content = build_page_frame(page_container)
    return html.Div(
        className="qcchem-shell",
        children=[
            build_context_bar(),
            html.Div(
                className="qcchem-main-grid",
                children=[
                    build_research_navigator(),
                    content,
                    build_interpretation_rail(),
                ],
            ),
        ],
    )
