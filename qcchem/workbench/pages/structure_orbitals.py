from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card
from qcchem.workbench.components.molecule import build_molecule_viewer
from qcchem.workbench.pages.overview import SAMPLE_MOLECULE_PAYLOAD, build_sample_view_model


def _orbital_figure(metadata: dict[str, object], reduction: dict[str, object]) -> go.Figure:
    frozen_orbitals = [int(value) for value in reduction.get("frozen_orbitals", [])]
    active_orbitals = [int(value) for value in reduction.get("selected_active_orbitals_original", [])]
    active_count = int(metadata.get("num_active_orbitals") or len(active_orbitals) or 0)
    orbital_trace = tuple(frozen_orbitals + active_orbitals + [active_count])
    participation = []
    for index, orbital in enumerate(orbital_trace):
        if index < len(frozen_orbitals):
            participation.append(0.1)
        elif index < len(frozen_orbitals) + len(active_orbitals):
            participation.append(0.9 - (0.08 * (index - len(frozen_orbitals))))
        else:
            participation.append(max(0.2, active_count / 10.0))

    figure = go.Figure()
    figure.add_scatter(
        x=orbital_trace,
        y=tuple(participation),
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


def build_structure_orbitals_page(model: dict[str, object]) -> html.Div:
    view = model
    metadata = view["structure"]["active_space_metadata"] or {}
    reduction = view.get("reduction") or {}
    molecule_model = view.get("molecule_viewer") or SAMPLE_MOLECULE_PAYLOAD
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
                            metric_card(
                                "Selection mode",
                                str(reduction.get("selection_mode", "auto")),
                                metadata.get("orbital_window", "Valence-focused window"),
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "minmax(280px, 0.9fr) minmax(0, 1.1fr)", "gap": "1rem"},
                children=[
                    build_molecule_viewer(
                        molecule_model,
                        viewer_id="structure-molecule",
                        title="Geometry and label overlay",
                        caption="The bridge payload can also carry orbital surfaces later; for now it anchors the spatial discussion with reproducible JSON.",
                    ),
                    html.Section(
                        className="qcchem-card",
                        children=[dcc.Graph(figure=_orbital_figure(metadata, reduction), config={"displayModeBar": False})],
                    ),
                ],
            ),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(260px, 1fr))", "gap": "1rem"},
                children=[
                    detail_card(
                        "Orbital curation",
                        [
                            ("Selection mode", str(reduction.get("selection_mode", "Automatic reduction audit"))),
                            ("Frozen orbitals", str(reduction.get("frozen_orbitals", []))),
                            ("Window label", metadata.get("orbital_window", "1 sigma to 3 sigma*")),
                            ("Interpretation", str(reduction.get("selected_active_orbitals_original", []))),
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


def layout() -> html.Div:
    return build_structure_orbitals_page(build_sample_view_model())
