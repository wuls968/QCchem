from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card
from qcchem.workbench.components.molecule import build_molecule_viewer
from qcchem.workbench.pages.overview import SAMPLE_MOLECULE_PAYLOAD, build_sample_view_model


def _orbital_figure() -> go.Figure:
    figure = go.Figure()
    figure.add_scatter(
        x=[-22, -14, -7, 4, 11, 18],
        y=[0.12, 0.24, 0.92, 0.85, 0.18, 0.08],
        mode="lines+markers",
        line={"color": "#20334a", "width": 3},
        marker={"size": 10, "color": "#9a6b3f"},
        fill="tozeroy",
        fillcolor="rgba(154, 107, 63, 0.15)",
    )
    figure.update_layout(
        title={"text": "Orbital importance across the selected active window", "x": 0.04},
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 40},
        xaxis_title="Orbital index offset",
        yaxis_title="Weighted participation",
        font={"color": "#2d2216"},
    )
    return figure


def layout() -> html.Div:
    view = build_sample_view_model()
    metadata = view["structure"]["active_space_metadata"] or {}
    return html.Div(
        className="qcchem-page qcchem-page--structure",
        style={"display": "grid", "gap": "1rem"},
        children=[
            html.Section(
                className="qcchem-card",
                children=[
                    html.P("Electronic Structure", className="qcchem-card-eyebrow"),
                    html.H2("Structure and Orbitals", className="qcchem-card-title", style={"fontSize": "2.1rem"}),
                    html.P(
                        "Geometry, orbital selection, and chemically meaningful symmetry cues for the current active-space model.",
                        className="qcchem-card-note",
                    ),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))", "gap": "0.9rem", "marginTop": "1rem"},
                        children=[
                            metric_card("Basis", view["hero"]["basis"], "Minimal basis for quick visual comparison"),
                            metric_card("Active orbitals", str(metadata.get("num_active_orbitals", "4")), "Window kept after reduction"),
                            metric_card("Fragment symmetry", "Sigma backbone", metadata.get("orbital_window", "Valence-focused window")),
                        ],
                    ),
                ],
            ),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "minmax(280px, 0.9fr) minmax(0, 1.1fr)", "gap": "1rem"},
                children=[
                    build_molecule_viewer(
                        SAMPLE_MOLECULE_PAYLOAD,
                        viewer_id="structure-molecule",
                        title="Geometry and label overlay",
                        caption="The bridge payload can also carry orbital surfaces later; for now it anchors the spatial discussion with reproducible JSON.",
                    ),
                    html.Section(className="qcchem-card", children=[dcc.Graph(figure=_orbital_figure(), config={"displayModeBar": False})]),
                ],
            ),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(260px, 1fr))", "gap": "1rem"},
                children=[
                    detail_card(
                        "Orbital curation",
                        [
                            ("Selection mode", "Automatic reduction audit"),
                            ("Frozen orbitals", "[0, 1]"),
                            ("Window label", metadata.get("orbital_window", "1 sigma to 3 sigma*")),
                            ("Interpretation", "Bonding-antibonding pair retained"),
                        ],
                    ),
                    callout_card(
                        "Why this page matters",
                        "The active-space and compression decisions later in the atlas are only believable if the orbital window still reads as a chemistry-first choice rather than a resource-only concession.",
                        accent="copper",
                    ),
                ],
            ),
        ],
    )
