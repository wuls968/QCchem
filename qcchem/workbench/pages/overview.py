from __future__ import annotations

from typing import Any

from dash import dcc, html
import plotly.graph_objects as go

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card
from qcchem.workbench.components.molecule import build_molecule_viewer
from qcchem.workbench.viewmodels import build_run_view_model

SAMPLE_MOLECULE_PAYLOAD: dict[str, Any] = {
    "format": "xyz",
    "coordinates": "3\nLiH fragment\nLi 0.0 0.0 0.0\nH 0.0 0.0 1.62\nX 0.0 0.0 0.81\n",
    "style": {"stick": {"radius": 0.18}, "sphere": {"scale": 0.28}},
    "labels": [
        {"text": "Li", "position": {"x": 0.0, "y": 0.0, "z": 0.0}},
        {"text": "H", "position": {"x": 0.0, "y": 0.0, "z": 1.62}},
    ],
}

SAMPLE_RUN_PAYLOAD: dict[str, Any] = {
    "problem": {
        "molecule_name": "LiH Active Fragment",
        "basis": "sto-3g",
        "charge": 0,
        "multiplicity": 1,
        "active_space_metadata": {
            "num_active_orbitals": 4,
            "num_active_electrons": 2,
            "orbital_window": "1 sigma to 3 sigma*",
        },
    },
    "energy": {
        "total_energy": -7.8823,
        "electronic_energy": -8.8761,
        "nuclear_repulsion_energy": 0.9938,
    },
    "mapping": {
        "kind": "bravyi_kitaev",
        "num_qubits": 8,
        "qubit_term_count": 128,
        "symmetry_tapered_qubits": 2,
    },
    "benchmark": {
        "absolute_error": 0.0118,
        "relative_error": 0.0015,
        "meets_threshold": True,
        "within_uncertainty": True,
        "threshold": 0.02,
        "comparison_target": "exact diagonalization",
        "compressed_vs_uncompressed": "compressed",
    },
    "runtime_submission": {
        "backend_name": "ibm_kyiv",
        "backend_version": "1.7.2",
        "provider": "ibm",
        "job_id": "job-lih-2048",
        "attempted": True,
        "submitted": True,
        "succeeded": True,
        "runtime_kind": "runtime_estimator",
        "mode": "runtime",
        "service": "ibm_runtime",
        "failure_category": None,
        "failure_message": None,
        "options_snapshot": {"shots": 4096, "resilience_level": 1, "precision_target": 0.015},
        "result_provenance": {"attempt_stage": "result_retrieved", "queue_hours": 0.4},
        "returned_job_metadata": {"metadata": {"shots": 4096, "usage_seconds": 132}},
        "verification_status": "passed",
        "transpiled_depth": 312,
        "transpiled_two_qubit_gate_count": 74,
        "transpilation": {"optimization_level": 2, "layout": "sabre"},
    },
    "reduction_audit": {
        "selection_mode": "auto",
        "selected_active_orbitals_original": [2, 3, 4, 5],
        "frozen_orbitals": [0, 1],
    },
    "compression_result": {
        "method": "double_factorization",
        "rank": 11,
        "post_term_count": 44,
        "pre_term_count": 128,
    },
    "verification_status": "validated",
    "hardware_verified": True,
    "chemical_accuracy": {"available": True, "meets_chemical_accuracy": True, "absolute_error_hartree": 0.0118},
    "runtime_chemical_accuracy": {"available": True, "meets_chemical_accuracy": True, "absolute_error_hartree": 0.0142},
}


def build_sample_view_model() -> dict[str, Any]:
    return build_run_view_model(SAMPLE_RUN_PAYLOAD)


def _overview_figure(view: dict[str, Any]) -> go.Figure:
    figure = go.Figure()
    figure.add_bar(
        x=["Reference", "Compressed VQE", "Hardware Result"],
        y=[-7.8941, view["hero"]["total_energy"], -7.8801],
        marker_color=["#20334a", "#9a6b3f", "#93a18a"],
    )
    figure.update_layout(
        title={"text": "Energy alignment across the current evidence stack", "x": 0.04},
        paper_bgcolor="#fffaf3",
        plot_bgcolor="#fffaf3",
        margin={"l": 36, "r": 20, "t": 72, "b": 40},
        font={"color": "#2d2216"},
        yaxis_title="Energy (Hartree)",
    )
    return figure


def layout() -> html.Div:
    view = build_sample_view_model()
    return html.Div(
        className="qcchem-page qcchem-page--overview",
        style={"display": "grid", "gap": "1.25rem"},
        children=[
            html.Section(
                className="qcchem-card",
                style={"padding": "1.75rem", "background": "linear-gradient(135deg, rgba(255,250,243,0.96), rgba(217,236,244,0.62))"},
                children=[
                    html.P("Run Atlas", className="qcchem-card-eyebrow"),
                    html.H2("Campaign Overview", className="qcchem-card-title", style={"fontSize": "2.3rem", "marginBottom": "0.6rem"}),
                    html.P(
                        "A scientific landing page for the current LiH active-space campaign: structure context, compression posture, hardware execution readiness, and the error envelope we can currently defend.",
                        className="qcchem-card-note",
                        style={"maxWidth": "48rem", "lineHeight": "1.7"},
                    ),
                    html.Div(
                        style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(170px, 1fr))", "gap": "0.9rem", "marginTop": "1.25rem"},
                        children=[
                            metric_card("Molecule", view["hero"]["molecule_name"], view["hero"]["basis"]),
                            metric_card("Total energy", f'{view["hero"]["total_energy"]:.4f} Ha', "Compressed VQE estimate"),
                            metric_card("Absolute error", f'{view["hero"]["absolute_error"]:.4f} Ha', "Against exact diagonalization"),
                            metric_card("Hardware backend", view["runtime"]["backend_name"], view["runtime"]["job_id"]),
                        ],
                    ),
                ],
            ),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "minmax(0, 1.2fr) minmax(280px, 0.8fr)", "gap": "1rem"},
                children=[
                    html.Section(className="qcchem-card", children=[dcc.Graph(figure=_overview_figure(view), config={"displayModeBar": False})]),
                    build_molecule_viewer(
                        SAMPLE_MOLECULE_PAYLOAD,
                        viewer_id="overview-molecule",
                        title="LiH active fragment",
                        caption="Representative fragment and anchor labels used throughout the workbench while full artifact-driven selection lands in Task 7.",
                    ),
                ],
            ),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(240px, 1fr))", "gap": "1rem"},
                children=[
                    detail_card(
                        "Scientific framing",
                        [
                            ("Active space", "2 electrons / 4 orbitals"),
                            ("Compression", "Double factorization rank 11"),
                            ("Mapping", "Bravyi-Kitaev with 2 tapered qubits"),
                            ("Confidence state", "Validated against threshold"),
                        ],
                    ),
                    callout_card(
                        "Interpretation cue",
                        "This overview is intentionally opinionated: the next pages explain why the orbital window was chosen, how compression changed the Hamiltonian footprint, and whether runtime evidence strengthens the claim.",
                        accent="copper",
                    ),
                ],
            ),
        ],
    )
