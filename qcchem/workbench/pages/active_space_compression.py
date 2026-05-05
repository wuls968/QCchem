from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from qcchem.workbench.components.cards import callout_card, detail_card, metric_card, status_card
from qcchem.workbench.components.charts import apply_chart_theme
from qcchem.workbench.pages.overview import build_sample_view_model
from qcchem.workbench.theme import THEME


def _compression_figure(compression: dict[str, object]) -> go.Figure:
    pre_term_count = int(compression.get("pre_term_count") or compression.get("post_term_count") or 0)
    post_term_count = int(compression.get("post_term_count") or 0)
    rank = int(compression.get("rank") or 0)
    compression_ratio = (post_term_count / pre_term_count) if pre_term_count else 0.0
    rank_ratio = (rank / pre_term_count) if pre_term_count else 0.0
    figure = make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_bar(
        x=["Original terms", "Post factorization", "Effective rank"],
        y=[pre_term_count, post_term_count, rank],
        marker={
            "color": [THEME["accent"]["deep_blue"], THEME["accent"]["copper"], THEME["accent"]["sage"]],
            "line": {"color": THEME["surface"]["paper"], "width": 1.4},
        },
        text=[str(pre_term_count), str(post_term_count), str(rank)],
        textposition="outside",
        hovertemplate="%{x}: %{y}<extra></extra>",
        name="Operator scale",
        secondary_y=False,
    )
    figure.add_scatter(
        x=["Post factorization", "Effective rank"],
        y=[compression_ratio, rank_ratio],
        mode="lines+markers",
        line={"color": THEME["status"]["informational"], "width": 2.4},
        marker={"size": 8, "color": THEME["status"]["informational"]},
        hovertemplate="%{x}: %{y:.2%} of original term scale<extra></extra>",
        name="Relative scale",
        secondary_y=True,
    )
    apply_chart_theme(
        figure,
        title="Compression posture from Hamiltonian assembly to deployable operator",
        yaxis_title="Count",
        yaxis2_title="Relative to original terms",
        height=430,
        legend=True,
    )
    figure.update_layout(legend={"orientation": "h", "x": 0, "y": 1.18})
    return figure


def build_active_space_compression_page(model: dict[str, object]) -> html.Div:
    view = model
    compression = view["compression"]
    reduction = view["reduction"]
    reduction_ratio = (
        (int(compression.get("post_term_count") or 0) / int(compression.get("pre_term_count") or 1))
        if int(compression.get("pre_term_count") or 0)
        else 0.0
    )
    return html.Div(
        className="qcchem-page qcchem-page--active-space",
        children=[
            html.Section(
                className="qcchem-card qcchem-active-space__hero",
                children=[
                    html.P("Model reduction", className="qcchem-card-eyebrow"),
                    html.H1("Active Space and Compression", className="qcchem-card-title qcchem-page__hero-title"),
                    html.P(
                        "QCchem should feel most distinctive here: what orbitals were kept, how compression changed the operator, and whether the approximation still looks like a chemistry decision rather than a brute-force resource cut.",
                        className="qcchem-card-note qcchem-page__hero-body",
                    ),
                    html.Div(
                        className="qcchem-page__summary-grid",
                        children=[
                            metric_card("Selection mode", reduction.get("selection_mode", "auto"), "Reduction audit"),
                            metric_card("Compression method", compression.get("method", "n/a"), "Low-rank operator form"),
                            metric_card("Effective rank", str(compression.get("rank", "n/a")), "Post-factorization"),
                            status_card(
                                "Operator contraction",
                                f"{(1 - reduction_ratio):.1%}",
                                "From original operator to compressed execution footprint",
                                tone="validated" if reduction_ratio < 0.5 else "exploratory",
                            ),
                        ],
                    ),
                ],
            ),
            html.Section(
                className="qcchem-card qcchem-active-space__chart",
                children=[
                    html.P("Operator evidence", className="qcchem-card-eyebrow"),
                    html.H2("Compression posture", className="qcchem-card-title"),
                    html.P(
                        "The chart should let you see both absolute scale and relative contraction so the reduced operator reads as an intentional bridge from chemistry to execution.",
                        className="qcchem-card-note",
                    ),
                    dcc.Graph(figure=_compression_figure(compression), config={"displayModeBar": False}),
                ],
            ),
            html.Div(
                className="qcchem-page__detail-grid",
                children=[
                    detail_card(
                        "Reduction audit",
                        [
                            ("Chosen orbitals", str(reduction.get("selected_active_orbitals_original", []))),
                            ("Compression class", compression.get("method", "double_factorization")),
                            ("Pre-term count", str(compression.get("pre_term_count", 128))),
                            ("Post-term count", str(compression.get("post_term_count", 44))),
                            (
                                "Reduction ratio",
                                (
                                    f"{(int(compression.get('post_term_count', 44)) / int(compression.get('pre_term_count', 128))):.2%}"
                                    if int(compression.get("pre_term_count", 128))
                                    else "n/a"
                                ),
                            ),
                        ],
                    ),
                    detail_card(
                        "Compression story",
                        [
                            ("Active orbitals", str(reduction.get("selected_active_orbitals_original", []))),
                            ("Frozen orbitals", str(reduction.get("frozen_orbitals", []))),
                            ("Execution posture", "Compression-aware execution is using the reduced operator, not just auditing it."),
                            ("Interpretation", "Rank is shown as a chemistry-and-cost bridge rather than a bare algebraic number."),
                        ],
                        eyebrow="QCchem Differentiator",
                    ),
                    callout_card(
                        "Interpretation rule",
                        "Judge this page in two steps: first ask whether the active orbitals still make chemistry sense, then ask whether the contraction ratio and effective rank look like a disciplined approximation rather than arbitrary shrinking.",
                        eyebrow="Review protocol",
                    ),
                ],
            ),
        ],
    )


def layout() -> html.Div:
    return build_active_space_compression_page(build_sample_view_model())
