from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card
from qcchem.workbench.pages.overview import build_sample_view_model


def _compression_figure() -> go.Figure:
    figure = go.Figure()
    figure.add_bar(
        x=["Original terms", "Post factorization", "Effective rank"],
        y=[128, 44, 11],
        marker_color=["#20334a", "#9a6b3f", "#93a18a"],
    )
    figure.update_layout(
        title={"text": "Compression posture from Hamiltonian assembly to deployable operator", "x": 0.04},
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 40},
        yaxis_title="Count",
        font={"color": "#2d2216"},
    )
    return figure


def build_active_space_compression_page(model: dict[str, object]) -> html.Div:
    view = model
    compression = view["compression"]
    reduction = view["reduction"]
    return html.Div(
        className="qcchem-page qcchem-page--active-space",
        style={"display": "grid", "gap": "1rem"},
        children=[
            html.Section(
                className="qcchem-card",
                children=[
                    html.P("Model Reduction", className="qcchem-card-eyebrow"),
                    html.H2("Active Space and Compression", className="qcchem-card-title", style={"fontSize": "2.1rem"}),
                    html.P(
                        "A compact view of what we kept, what we compressed away, and how that decision shifts the practical Hamiltonian.",
                        className="qcchem-card-note",
                    ),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))", "gap": "0.9rem", "marginTop": "1rem"},
                        children=[
                            metric_card("Selection mode", reduction.get("selection_mode", "auto"), "Reduction audit"),
                            metric_card("Compression method", compression.get("method", "n/a"), "Low-rank operator form"),
                            metric_card("Effective rank", str(compression.get("rank", "n/a")), "Post-factorization"),
                        ],
                    ),
                ],
            ),
            html.Section(className="qcchem-card", children=[dcc.Graph(figure=_compression_figure(), config={"displayModeBar": False})]),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(260px, 1fr))", "gap": "1rem"},
                children=[
                    detail_card(
                        "Reduction audit",
                        [
                            ("Chosen orbitals", str(reduction.get("selected_active_orbitals_original", []))),
                            ("Compression class", compression.get("method", "double_factorization")),
                            ("Pre-term count", str(compression.get("pre_term_count", 128))),
                            ("Post-term count", str(compression.get("post_term_count", 44))),
                        ],
                    ),
                    callout_card(
                        "Scientific readout",
                        "The page emphasizes whether compression is acting like an informed approximation layer rather than a blind resource cut. The retained rank is shown alongside orbital selection so the reader can connect chemistry and operator structure.",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_active_space_compression_page(build_sample_view_model())
