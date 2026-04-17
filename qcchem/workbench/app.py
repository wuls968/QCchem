from __future__ import annotations

from pathlib import Path

import dash
from dash import Dash, dcc, html

from qcchem.workbench.components.layout import build_shell
from qcchem.workbench.pages._registry import ensure_pages_registered

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def create_app() -> Dash:
    app = Dash(
        __name__,
        use_pages=True,
        pages_folder="",
        assets_folder=str(ASSETS_DIR),
        suppress_callback_exceptions=True,
        title="QCchem Visual Workbench",
    )
    ensure_pages_registered()
    app.page_registry = dash.page_registry
    app.layout = build_shell()
    app.validation_layout = html.Div(
        [
            dcc.Location(id="qcchem-url"),
            build_shell(),
        ]
    )
    return app
