from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card
from qcchem.workbench.pages.overview import build_sample_view_model


def _resource_figure(view: dict[str, object]) -> go.Figure:
    mapping = view["mapping"]
    runtime = view["runtime"]
    figure = go.Figure()
    figure.add_bar(
        x=["Logical qubits", "Pauli terms", "Depth", "2Q gates"],
        y=[
            mapping.get("num_qubits", 0),
            mapping.get("qubit_term_count", 0),
            runtime.get("transpiled_depth", 0),
            runtime.get("transpiled_two_qubit_gate_count", 0),
        ],
        marker_color=["#20334a", "#46607a", "#9a6b3f", "#c58742"],
    )
    figure.update_layout(
        title={"text": "Mapping, tapering, and compiled circuit burden", "x": 0.04},
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 40},
        yaxis_title="Count",
        font={"color": "#2d2216"},
    )
    return figure


def build_mapping_resources_page(model: dict[str, object]) -> html.Div:
    view = model
    mapping = view["mapping"]
    runtime = view["runtime"]
    return html.Div(
        className="qcchem-page qcchem-page--mapping",
        style={"display": "grid", "gap": "1rem"},
        children=[
            html.Section(
                className="qcchem-card",
                children=[
                    html.P("Compilation Story", className="qcchem-card-eyebrow"),
                    html.H2("Mapping, Resources, and Circuit", className="qcchem-card-title", style={"fontSize": "2.1rem"}),
                    html.P(
                        "A route for connecting the fermionic representation to the compiled circuit burden that the chosen backend will actually see.",
                        className="qcchem-card-note",
                    ),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))", "gap": "0.9rem", "marginTop": "1rem"},
                        children=[
                            metric_card("Mapping", str(mapping.get("kind", "n/a")).replace("_", " ").title(), "Operator transform"),
                            metric_card("Tapered qubits", str(mapping.get("symmetry_tapered_qubits", 0)), "Symmetry savings"),
                            metric_card("Layout", str(runtime.get("transpilation", {}).get("layout", "sabre")), "Compilation strategy"),
                        ],
                    ),
                ],
            ),
            html.Section(className="qcchem-card", children=[dcc.Graph(figure=_resource_figure(view), config={"displayModeBar": False})]),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(260px, 1fr))", "gap": "1rem"},
                children=[
                    detail_card(
                        "Circuit budget",
                        [
                            ("Logical qubits", str(mapping.get("num_qubits", 0))),
                            ("Pauli terms", str(mapping.get("qubit_term_count", 0))),
                            ("Transpiled depth", str(runtime.get("transpiled_depth", 0))),
                            ("Two-qubit gates", str(runtime.get("transpiled_two_qubit_gate_count", 0))),
                        ],
                    ),
                    callout_card(
                        "Resource lens",
                        "This page keeps mapping and compiled burden together so a reader can judge whether an elegant transform still survives contact with layout and entangling-gate pressure.",
                        accent="copper",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_mapping_resources_page(build_sample_view_model())
