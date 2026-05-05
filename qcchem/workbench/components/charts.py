from __future__ import annotations

import plotly.graph_objects as go

from qcchem.workbench.theme import THEME


def apply_chart_theme(
    figure: go.Figure,
    *,
    title: str,
    xaxis_title: str | None = None,
    yaxis_title: str | None = None,
    xaxis2_title: str | None = None,
    yaxis2_title: str | None = None,
    height: int = 420,
    legend: bool = False,
) -> go.Figure:
    figure.update_layout(
        title={"text": title, "x": 0.02},
        paper_bgcolor=THEME["surface"]["card"],
        plot_bgcolor=THEME["surface"]["panel"],
        margin={"l": 44, "r": 24, "t": 74, "b": 52},
        font={"color": THEME["text"]["primary"], "family": THEME["type"]["body"]},
        title_font={"family": THEME["type"]["display"], "size": 18, "color": THEME["text"]["primary"]},
        hoverlabel={
            "bgcolor": THEME["surface"]["card"],
            "bordercolor": THEME["surface"]["line"],
            "font": {"color": THEME["text"]["primary"], "family": THEME["type"]["body"]},
        },
        showlegend=legend,
        legend={
            "orientation": "h",
            "x": 0,
            "y": 1.12,
            "bgcolor": THEME["surface"]["card"],
            "bordercolor": THEME["surface"]["line"],
            "borderwidth": 1,
            "font": {"size": 11, "color": THEME["text"]["secondary"]},
        },
        height=height,
    )
    figure.update_xaxes(
        title_text=xaxis_title,
        showgrid=False,
        linecolor=THEME["surface"]["line"],
        mirror=True,
        showline=True,
        ticks="outside",
        ticklen=4,
        tickfont={"color": THEME["text"]["secondary"], "size": 11},
        title_font={"color": THEME["text"]["secondary"], "size": 12},
        zeroline=False,
        automargin=True,
    )
    figure.update_yaxes(
        title_text=yaxis_title,
        gridcolor="rgba(82, 82, 82, 0.14)",
        griddash="dot",
        linecolor=THEME["surface"]["line"],
        mirror=True,
        showline=True,
        ticks="outside",
        ticklen=4,
        tickfont={"color": THEME["text"]["secondary"], "size": 11},
        title_font={"color": THEME["text"]["secondary"], "size": 12},
        zeroline=False,
        automargin=True,
    )
    if xaxis2_title:
        figure.update_layout(
            xaxis2={
                "title": {"text": xaxis2_title, "font": {"color": THEME["text"]["secondary"], "size": 12}},
                "showgrid": False,
                "linecolor": THEME["surface"]["line"],
                "mirror": True,
                "showline": True,
                "ticks": "outside",
                "ticklen": 4,
                "tickfont": {"color": THEME["text"]["secondary"], "size": 11},
                "zeroline": False,
            }
        )
    if yaxis2_title:
        figure.update_yaxes(
            title_text=yaxis2_title,
            gridcolor="rgba(82, 82, 82, 0.12)",
            griddash="dot",
            linecolor=THEME["surface"]["line"],
            mirror=True,
            showline=True,
            ticks="outside",
            ticklen=4,
            tickfont={"color": THEME["text"]["secondary"], "size": 11},
            title_font={"color": THEME["text"]["secondary"], "size": 12},
            zeroline=False,
            automargin=True,
            secondary_y=True,
        )
    return figure


def add_threshold_line(
    figure: go.Figure,
    *,
    value: float,
    label: str,
    color: str | None = None,
    row: int | None = None,
    col: int | None = None,
    secondary_y: bool | None = None,
) -> go.Figure:
    kwargs: dict[str, object] = {}
    if row is not None:
        kwargs["row"] = row
    if col is not None:
        kwargs["col"] = col
    if secondary_y is not None:
        kwargs["secondary_y"] = secondary_y
    figure.add_hline(
        y=value,
        line_dash="dash",
        line_color=color or THEME["accent"]["deep_blue"],
        annotation_text=label,
        annotation_position="top left",
        **kwargs,
    )
    return figure


def add_chart_note(
    figure: go.Figure,
    *,
    text: str,
    x: float = 0.99,
    y: float = 0.98,
    xanchor: str = "right",
    yanchor: str = "top",
) -> go.Figure:
    figure.add_annotation(
        xref="paper",
        yref="paper",
        x=x,
        y=y,
        xanchor=xanchor,
        yanchor=yanchor,
        showarrow=False,
        align="right",
        bgcolor="rgba(255, 255, 255, 0.92)",
        bordercolor=THEME["surface"]["line"],
        borderwidth=1,
        font={"size": 11, "color": THEME["text"]["secondary"], "family": THEME["type"]["body"]},
        text=text,
    )
    return figure


def case_label(name: object) -> str:
    raw = str(name or "case")
    cleaned = raw
    for prefix in (
        "h2_runtime_hardware_probe_",
        "lih_active_runtime_hardware_probe_",
        "lih_active_",
        "h2_",
        "lih_",
    ):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
            break
    tokens = [token for token in cleaned.split("_") if token]
    replacements = {
        "puccd": "PUCCD",
        "uccsd": "UCCSD",
        "ca": "CA",
        "dd": "DD",
        "vqe": "VQE",
        "runtime": "Runtime",
        "layout": "layout",
        "highshots": "high shots",
        "high": "high",
        "shots": "shots",
        "mitigated": "mitigated",
        "hardware": "hardware",
        "probe": "probe",
        "active": "active",
        "exact": "exact",
        "compressed": "compressed",
        "uncompressed": "uncompressed",
        "ready": "ready",
        "statevector": "statevector",
    }
    words = [replacements.get(token, token.replace("-", " ").title()) for token in tokens]
    label = " ".join(words).strip()
    return label or raw


def blank_figure(title: str, subtitle: str) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        title={"text": title, "x": 0.02},
        annotations=[
            {
                "text": subtitle,
                "xref": "paper",
                "yref": "paper",
                "x": 0.02,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 14, "color": THEME["text"]["secondary"], "family": THEME["type"]["body"]},
            }
        ],
        paper_bgcolor=THEME["surface"]["card"],
        plot_bgcolor=THEME["surface"]["panel"],
        font={"color": THEME["text"]["primary"], "family": THEME["type"]["body"]},
        title_font={"family": THEME["type"]["display"], "size": 18, "color": THEME["text"]["primary"]},
        margin={"l": 36, "r": 24, "t": 64, "b": 32},
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    return figure
