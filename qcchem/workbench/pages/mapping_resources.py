from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card, status_card
from qcchem.workbench.components.charts import apply_chart_theme
from qcchem.workbench.pages.overview import build_sample_view_model
from qcchem.workbench.theme import THEME


def _resource_figure(view: dict[str, object]) -> go.Figure:
    mapping = view["mapping"]
    runtime = view["runtime"]
    logical_qubits = float(mapping.get("num_qubits", 0) or 0)
    tapered_qubits = float(mapping.get("symmetry_tapered_qubits", 0) or 0)
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_bar(
        x=["Logical qubits", "Pauli terms", "Depth", "2Q gates"],
        y=[
            logical_qubits,
            float(mapping.get("qubit_term_count", 0) or 0),
            float(runtime.get("transpiled_depth", 0) or 0),
            float(runtime.get("transpiled_two_qubit_gate_count", 0) or 0),
        ],
        marker={
            "color": [
                THEME["accent"]["deep_blue"],
                THEME["status"]["informational"],
                THEME["accent"]["copper"],
                THEME["accent"]["signal"],
            ],
            "line": {"color": THEME["surface"]["paper"], "width": 1.4},
        },
        text=[
            str(int(logical_qubits)),
            str(int(mapping.get("qubit_term_count", 0) or 0)),
            str(int(runtime.get("transpiled_depth", 0) or 0)),
            str(int(runtime.get("transpiled_two_qubit_gate_count", 0) or 0)),
        ],
        textposition="outside",
        hovertemplate="%{x}: %{y}<extra></extra>",
        name="Resource burden",
        secondary_y=False,
    )
    figure.add_scatter(
        x=["Logical qubits", "Taper savings"],
        y=[logical_qubits, (tapered_qubits / logical_qubits) if logical_qubits else 0.0],
        mode="lines+markers",
        line={"color": THEME["accent"]["sage"], "width": 2.5},
        marker={"size": 8, "color": THEME["accent"]["sage"]},
        hovertemplate="%{x}: %{y:.2f}<extra></extra>",
        name="Taper posture",
        secondary_y=True,
    )
    apply_chart_theme(
        figure,
        title="Mapping, tapering, and compiled circuit burden",
        yaxis_title="Count",
        yaxis2_title="Qubit / savings ratio",
        height=420,
        legend=True,
    )
    figure.update_layout(legend={"orientation": "h", "x": 0, "y": 1.18})
    return figure


def build_mapping_resources_page(model: dict[str, object]) -> html.Div:
    view = model
    mapping = view["mapping"]
    runtime = view["runtime"]
    logical_qubits = int(mapping.get("num_qubits", 0) or 0)
    tapered = int(mapping.get("symmetry_tapered_qubits", 0) or 0)
    taper_ratio = (tapered / logical_qubits) if logical_qubits else 0.0
    return html.Div(
        className="qcchem-page qcchem-page--mapping",
        children=[
            html.Section(
                className="qcchem-card qcchem-mapping__hero",
                children=[
                    html.P("Compilation story", className="qcchem-card-eyebrow"),
                    html.H1("Mapping, Resources, and Circuit", className="qcchem-card-title qcchem-page__hero-title"),
                    html.P(
                        "This page should answer the practical question early: does an elegant mapping survive contact with tapering, layout, depth, and two-qubit-gate pressure once the backend sees the compiled circuit?",
                        className="qcchem-card-note qcchem-page__hero-body",
                    ),
                    html.Div(
                        className="qcchem-page__summary-grid",
                        children=[
                            metric_card("Mapping", str(mapping.get("kind", "n/a")).replace("_", " ").title(), "Operator transform"),
                            metric_card("Layout", str(runtime.get("transpilation", {}).get("layout", "sabre")), "Compilation strategy"),
                            metric_card("Backend", str(runtime.get("backend_name", "n/a")), f"depth {runtime.get('transpiled_depth', 'n/a')}"),
                            status_card(
                                "Taper savings",
                                f"{tapered} qubits",
                                f"{taper_ratio:.1%} of logical register removed",
                                tone="validated" if tapered else "informational",
                            ),
                        ],
                    ),
                ],
            ),
            html.Section(
                className="qcchem-card qcchem-mapping__chart",
                children=[
                    html.P("Resource burden", className="qcchem-card-eyebrow"),
                    html.H2("Compiled resource posture", className="qcchem-card-title"),
                    html.P(
                        "Use this chart to connect mapping elegance to compiled burden. The important question is not just how many qubits were saved, but what depth and entangling pressure remained after compilation.",
                        className="qcchem-card-note",
                    ),
                    dcc.Graph(figure=_resource_figure(view), config={"displayModeBar": False}),
                ],
            ),
            html.Div(
                className="qcchem-page__detail-grid",
                children=[
                    detail_card(
                        "Circuit budget",
                        [
                            ("Logical qubits", str(mapping.get("num_qubits", 0))),
                            ("Pauli terms", str(mapping.get("qubit_term_count", 0))),
                            ("Transpiled depth", str(runtime.get("transpiled_depth", 0))),
                            ("Two-qubit gates", str(runtime.get("transpiled_two_qubit_gate_count", 0))),
                            ("Backend", str(runtime.get("backend_name", "n/a"))),
                        ],
                    ),
                    detail_card(
                        "Interpretation posture",
                        [
                            ("Mapping kind", str(mapping.get("kind", "n/a"))),
                            ("Tapered qubits", str(mapping.get("symmetry_tapered_qubits", 0))),
                            ("Layout strategy", str(runtime.get("transpilation", {}).get("layout", "n/a"))),
                            ("Question", "Did tapering materially reduce burden, or did compilation push complexity back into depth and 2Q gates?"),
                        ],
                        eyebrow="Review lens",
                    ),
                    callout_card(
                        "Interpretation rule",
                        "Read mapping pages in two stages: first count qubit and Pauli savings, then inspect whether compiled depth and two-qubit gates preserved or erased those savings on the target backend.",
                        accent="copper",
                        eyebrow="Review protocol",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_mapping_resources_page(build_sample_view_model())
