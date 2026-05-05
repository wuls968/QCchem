from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card, status_card
from qcchem.workbench.components.charts import apply_chart_theme
from qcchem.workbench.components.molecule import build_molecule_viewer
from qcchem.workbench.pages.overview import SAMPLE_MOLECULE_PAYLOAD, build_sample_view_model
from qcchem.workbench.theme import THEME


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
    for position, energy in zip(orbital_indices, orbital_levels, strict=True):
        figure.add_shape(
            type="line",
            x0=position,
            x1=position,
            y0=min(orbital_levels) - 0.8 if orbital_levels else -1,
            y1=energy,
            line={"color": "rgba(82, 82, 82, 0.18)", "width": 2},
        )
    figure.add_scatter(
        x=orbital_indices,
        y=orbital_levels,
        mode="markers",
        marker={
            "size": 16,
            "color": colors,
            "line": {"color": THEME["surface"]["paper"], "width": 1.5},
        },
        customdata=[(position, original, label) for position, original, label in zip(orbital_indices, original_labels, labels, strict=True)],
        hovertemplate=(
            "Current position %{customdata[0]}<br>"
            "Original orbital %{customdata[1]}<br>"
            "Energy %{y:.2f} eV<br>"
            "%{customdata[2]}<extra></extra>"
        ),
    )
    if active_positions:
        active_energies = [orbital_levels[index] for index in active_positions if index < len(orbital_levels)]
        if active_energies:
            figure.add_hrect(
                y0=min(active_energies) - 0.35,
                y1=max(active_energies) + 0.35,
                fillcolor="rgba(15, 98, 254, 0.08)",
                line_width=0,
            )
            figure.add_annotation(
                xref="paper",
                y=max(active_energies) + 0.28,
                x=0.98,
                showarrow=False,
                xanchor="right",
                bgcolor="rgba(255, 255, 255, 0.88)",
                bordercolor=THEME["surface"]["line"],
                borderwidth=1,
                font={"size": 11, "color": THEME["text"]["secondary"]},
                text="Active-space window",
            )
    apply_chart_theme(
        figure,
        title="Orbital energy ladder across the selected model window",
        xaxis_title="Orbital position / original index",
        yaxis_title="Orbital energy (eV)",
        height=460,
    )
    figure.update_xaxes(tickmode="array", tickvals=orbital_indices, ticktext=ticktext)
    figure.update_layout(
        annotations=[
            *tuple(figure.layout.annotations or ()),
            {
                "xref": "paper",
                "yref": "paper",
                "x": 0.02,
                "y": 1.15,
                "showarrow": False,
                "align": "left",
                "font": {"size": 11, "color": THEME["text"]["secondary"]},
                "text": (
                    f"Frozen {len(frozen_positions)} · "
                    f"Active {len(active_positions)} · "
                    f"Context {max(len(orbital_indices) - len(frozen_positions) - len(active_positions), 0)}"
                ),
            },
        ]
    )
    return figure


def build_structure_orbitals_page(model: dict[str, object]) -> html.Div:
    view = model
    metadata = view["structure"]["active_space_metadata"] or {}
    reduction = view.get("reduction") or {}
    molecule_model = view.get("molecule_viewer") or SAMPLE_MOLECULE_PAYLOAD
    original_labels = _resolve_orbital_labels(metadata, reduction, len(metadata.get("orbital_levels_ev", [])))
    active_count = len(_normalize_indices(reduction.get("selected_active_orbitals_original"))) or int(metadata.get("num_active_orbitals", 0) or 0)
    frozen_count = len(_normalize_indices(reduction.get("frozen_orbitals")))
    return html.Div(
        className="qcchem-page qcchem-page--structure",
        children=[
            html.Section(
                className="qcchem-card qcchem-structure__hero",
                children=[
                    html.P("Electronic structure", className="qcchem-card-eyebrow"),
                    html.H1("Structure and Orbitals", className="qcchem-card-title qcchem-page__hero-title"),
                    html.P(
                        "This page should defend the chemistry window itself. Geometry, orbital ordering, and frozen-versus-active boundaries need to read like a chemically coherent choice before later compression or runtime tradeoffs are credible.",
                        className="qcchem-card-note qcchem-page__hero-body",
                    ),
                    html.Div(
                        className="qcchem-page__summary-grid",
                        children=[
                            metric_card("Basis", view["hero"]["basis"], "Model basis for orbital interpretation"),
                            metric_card("Active orbitals", str(metadata.get("num_active_orbitals", "4")), "Window carried into reduction"),
                            metric_card("Selection mode", str(reduction.get("selection_mode", "auto")), metadata.get("orbital_window", "Valence-focused window")),
                            status_card(
                                "Orbital partition",
                                f"{active_count} active / {frozen_count} frozen",
                                f"original labels: {original_labels}",
                                tone="validated" if active_count else "informational",
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="qcchem-page__analysis-grid",
                children=[
                    build_molecule_viewer(
                        molecule_model,
                        viewer_id="structure-molecule",
                        title="Geometry reference",
                        caption="Anchor geometry used to judge whether the chosen active window still reads as chemistry-first.",
                    ),
                    html.Section(
                        className="qcchem-card qcchem-structure__ladder",
                        children=[
                            html.P("Orbital evidence", className="qcchem-card-eyebrow"),
                            html.H2("Active-space ladder", className="qcchem-card-title"),
                            html.P(
                                "Read the ladder before reading operator compression. If the active orbitals and frozen orbitals do not look sensible here, later efficiency gains are not yet persuasive.",
                                className="qcchem-card-note",
                            ),
                            dcc.Graph(figure=_orbital_selection_figure(metadata, reduction), config={"displayModeBar": False}),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="qcchem-page__detail-grid",
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
                    detail_card(
                        "Why this window matters",
                        [
                            ("Active electrons", str(metadata.get("num_active_electrons", "n/a"))),
                            ("Active orbitals", str(metadata.get("num_active_orbitals", "n/a"))),
                            ("Original labels", str(original_labels)),
                            ("Interpretation", "Frozen, context, and active levels should remain legible before compression is introduced."),
                        ],
                        eyebrow="Selection story",
                    ),
                    callout_card(
                        "Interpretation rule",
                        "Ask two questions in order: do the retained orbitals still match a chemistry story, and does the frozen/context split feel like a principled simplification rather than a resource-only concession?",
                        accent="copper",
                        eyebrow="Review protocol",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_structure_orbitals_page(build_sample_view_model())
