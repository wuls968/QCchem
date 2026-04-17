from __future__ import annotations

import json
from typing import Any

from dash import html


def build_molecule_viewer(
    molecule: dict[str, Any],
    *,
    viewer_id: str,
    title: str,
    caption: str | None = None,
    height: str = "320px",
) -> html.Section:
    payload = json.dumps(molecule, separators=(",", ":"))
    return html.Section(
        id=viewer_id,
        className="qcchem-card",
        children=[
            html.P("Molecular Scene", className="qcchem-card-eyebrow"),
            html.H3(title, className="qcchem-card-title"),
            html.Div(
                id=f"{viewer_id}__canvas",
                className="qcchem-molecule-viewer",
                **{
                    "data-molecule-json": payload,
                    "style": {
                        "height": height,
                        "borderRadius": "18px",
                        "background": "radial-gradient(circle at top, rgba(32, 51, 74, 0.18), rgba(32, 51, 74, 0.82))",
                        "boxShadow": "inset 0 0 0 1px rgba(255, 255, 255, 0.08)",
                        "overflow": "hidden",
                    },
                },
            ),
            html.P(
                caption or "Hydrated by the 3Dmol.js bridge with orbitals, labels, and style metadata from the page model.",
                className="qcchem-card-note",
                style={"marginTop": "0.85rem"},
            ),
        ],
    )
