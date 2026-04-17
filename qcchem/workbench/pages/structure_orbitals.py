from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card
from qcchem.workbench.components.molecule import build_molecule_viewer
from qcchem.workbench.pages.overview import SAMPLE_MOLECULE_PAYLOAD, build_sample_view_model


def _normalize_indices(values: object) -> list[int]:
    if not values:
        return []
    return [int(value) for value in values]


def _resolve_orbital_labels(metadata: dict[str, object], reduction: dict[str, object], count: int) -> list[int]:
    label_candidates = (
        metadata.get("orbital_indices_original"),
        metadata.get("orbital_labels_original"),
        reduction.get("orbital_indices_original"),
        reduction.get("orbital_labels_original"),
        reduction.get("selected_active_orbitals_original"),
        reduction.get("selected_active_orbitals"),
    )
    for candidate in label_candidates:
        labels = _normalize_indices(candidate)
        if len(labels) == count:
            return labels
    return list(range(count))


def _orbital_selection_figure(metadata: dict[str, object], reduction: dict[str, object]) -> go.Figure:
    orbital_levels = tuple(float(value) for value in metadata.get("orbital_levels_ev", []))
    orbital_indices = tuple(range(len(orbital_levels)))
    original_labels = _resolve_orbital_labels(metadata, reduction, len(orbital_levels))
    active_original_orbitals = set(_normalize_indices(reduction.get("selected_active_orbitals_original")))
    active_current_orbitals = set(_normalize_indices(reduction.get("selected_active_orbitals")))
    active_original_orbitals.update(_normalize_indices(reduction.get("active_orbitals_original")))
    active_current_orbitals.update(_normalize_indices(reduction.get("active_orbitals")))
    frozen_original_orbitals = set(_normalize_indices(reduction.get("frozen_orbitals")))
    frozen_original_orbitals.update(_normalize_indices(reduction.get("frozen_core_orbitals")))
    frozen_current_orbitals = set(_normalize_indices(reduction.get("frozen_orbitals_current")))

    active_positions = {
        position
        for position, original in enumerate(original_labels)
        if position in active_current_orbitals or original in active_original_orbitals
    }
    frozen_positions = {
        position
        for position, original in enumerate(original_labels)
        if position in frozen_current_orbitals or original in frozen_original_orbitals
    }
    colors = [
        "#9a6b3f" if index in active_positions else "#46607a" if index in frozen_positions else "#93a18a"
        for index in orbital_indices
    ]
    labels = [
        "Active" if index in active_positions else "Frozen" if index in frozen_positions else "Context"
        for index in orbital_indices
    ]
    ticktext = [
        f"pos {position}" if original == position else f"pos {position} / orig {original}"
        for position, original in enumerate(original_labels)
    ]

    figure = go.Figure()
    figure.add_scatter(
        x=orbital_indices,
        y=orbital_levels,
        mode="markers",
        marker={"size": 14, "color": colors},
        customdata=[(position, original, label) for position, original, label in zip(orbital_indices, original_labels, labels, strict=True)],
        hovertemplate=(
            "Current position %{customdata[0]}<br>"
            "Original orbital %{customdata[1]}<br>"
            "Energy %{y:.2f} eV<br>"
            "%{customdata[2]}<extra></extra>"
        ),
    )
    figure.update_layout(
        title={"text": "Orbital energy ladder across the selected model window", "x": 0.04},
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 40},
        xaxis_title="Orbital position / original index",
        yaxis_title="Orbital energy (eV)",
        font={"color": "#2d2216"},
    )
    figure.update_xaxes(tickmode="array", tickvals=orbital_indices, ticktext=ticktext)
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
                        "Geometry context plus a model-driven orbital energy ladder showing which levels are frozen, active, or retained as surrounding context.",
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
                        title="Geometry reference",
                        caption="A simple atom-based geometry reference for the current orbital selection narrative.",
                    ),
                    html.Section(
                        className="qcchem-card",
                        children=[dcc.Graph(figure=_orbital_selection_figure(metadata, reduction), config={"displayModeBar": False})],
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
                            ("Orbital levels (eV)", str(metadata.get("orbital_levels_ev", []))),
                            ("Selected active orbitals", str(reduction.get("selected_active_orbitals_original", []))),
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
