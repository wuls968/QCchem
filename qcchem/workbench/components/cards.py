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


def detail_card(title: str, details: list[tuple[str, str]], *, eyebrow: str = "Scientific Detail") -> html.Section:
    rows = [
        html.Div(
            className="qcchem-detail-card__row",
            style={
                "display": "grid",
                "gridTemplateColumns": "minmax(0, 1fr) auto",
                "gap": "0.75rem",
                "padding": "0.5rem 0",
                "borderBottom": "1px solid rgba(32, 51, 74, 0.08)",
            },
            children=[
                html.Span(label, style={"color": "var(--qcchem-text-secondary)"}),
                html.Strong(value, style={"color": "var(--qcchem-accent-deep-blue)"}),
            ],
        )
        for label, value in details
    ]
    return html.Section(
        className="qcchem-card",
        children=[
            html.P(eyebrow, className="qcchem-card-eyebrow"),
            html.H3(title, className="qcchem-card-title"),
            html.Div(rows),
        ],
    )
