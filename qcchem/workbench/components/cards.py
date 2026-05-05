from __future__ import annotations

from dash import html


def metric_card(title: str, value: str, note: str | None = None, *, tone: str = "default") -> html.Section:
    children: list[html.Component] = [
        html.P(title, className="qcchem-card-eyebrow"),
        html.H3(value, className="qcchem-card-value"),
    ]
    if note:
        children.append(html.P(note, className="qcchem-card-note qcchem-card-note--compact"))
    return html.Section(children=children, className=f"qcchem-card qcchem-card--metric qcchem-card--{tone}")


def status_card(title: str, value: str, body: str, *, tone: str = "informational") -> html.Section:
    badge_text = {
        "validated": "Defended",
        "exploratory": "Watch",
        "unstable": "Risk",
        "informational": "Info",
    }.get(tone, tone.replace("_", " ").title())
    return html.Section(
        className=f"qcchem-card qcchem-card--status qcchem-card--status-{tone}",
        children=[
            html.Div(
                className="qcchem-card__header",
                children=[
                    html.P(title, className="qcchem-card-eyebrow"),
                    html.Span(badge_text, className=f"qcchem-badge qcchem-badge--{tone}"),
                ],
            ),
            html.H3(value, className="qcchem-card-title qcchem-card-title--dense"),
            html.P(body, className="qcchem-card-note"),
        ],
    )


def callout_card(title: str, body: str, *, accent: str = "copper", eyebrow: str = "Review note") -> html.Section:
    return html.Section(
        className=f"qcchem-card qcchem-card--callout qcchem-card--accent-{accent}",
        children=[
            html.P(eyebrow, className="qcchem-card-eyebrow"),
            html.H3(title, className="qcchem-card-title"),
            html.P(body, className="qcchem-card-note"),
        ],
    )


def detail_card(title: str, details: list[tuple[str, str]], *, eyebrow: str = "Scientific Detail") -> html.Section:
    rows = [
        html.Div(
            className="qcchem-detail-card__row",
            children=[
                html.Span(label, className="qcchem-detail-card__label"),
                html.Strong(value, className="qcchem-detail-card__value"),
            ],
        )
        for label, value in details
    ]
    return html.Section(
        className="qcchem-card",
        children=[
            html.P(eyebrow, className="qcchem-card-eyebrow"),
            html.H3(title, className="qcchem-card-title"),
            html.Div(rows, className="qcchem-detail-card__grid"),
        ],
    )
