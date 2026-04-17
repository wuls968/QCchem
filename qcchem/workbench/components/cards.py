from __future__ import annotations

from dash import html


def metric_card(title: str, value: str, note: str | None = None, *, tone: str = "default") -> html.Section:
    children: list[html.Component] = [
        html.P(title, className="qcchem-card-eyebrow"),
        html.H3(value, className="qcchem-card-value"),
    ]
    if note:
        children.append(html.P(note, className="qcchem-card-note"))
    return html.Section(children=children, className=f"qcchem-card qcchem-card--{tone}")


def callout_card(title: str, body: str, *, accent: str = "copper") -> html.Section:
    return html.Section(
        className=f"qcchem-card qcchem-card--callout qcchem-card--accent-{accent}",
        children=[
            html.P("Workbench", className="qcchem-card-eyebrow"),
            html.H3(title, className="qcchem-card-title"),
            html.P(body, className="qcchem-card-note"),
        ],
    )

