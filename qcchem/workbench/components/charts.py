from __future__ import annotations

import plotly.graph_objects as go

from qcchem.workbench.theme import THEME


def blank_figure(title: str, subtitle: str) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        title={"text": title, "x": 0.03},
        annotations=[
            {
                "text": subtitle,
                "xref": "paper",
                "yref": "paper",
                "x": 0.03,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 14, "color": THEME["text"]["secondary"]},
            }
        ],
        paper_bgcolor=THEME["surface"]["card"],
        plot_bgcolor=THEME["surface"]["card"],
        font={"color": THEME["text"]["primary"]},
        margin={"l": 32, "r": 24, "t": 72, "b": 32},
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    return figure

