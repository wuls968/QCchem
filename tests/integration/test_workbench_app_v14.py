from __future__ import annotations

from pathlib import Path

import pytest

from qcchem.workbench.theme import THEME

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_create_app_registers_primary_pages() -> None:
    from qcchem.workbench.app import create_app

    app = create_app()

    page_paths = {
        child.id["path"]
        for child in app.validation_layout.children
        if isinstance(getattr(child, "id", None), dict) and child.id.get("type") == "qcchem-page-validation"
    }

    assert "/overview" in page_paths
    assert "/results" in page_paths


def test_theme_tokens_include_scientific_atelier_palette() -> None:
    assert THEME["surface"]["paper"] == "#f7f1e8"
    assert THEME["surface"]["card"] == "#fffaf3"
    assert THEME["accent"]["copper"] == "#9a6b3f"
    assert THEME["accent"]["deep_blue"] == "#20334a"


@pytest.mark.integration
def test_shell_layout_exposes_core_regions() -> None:
    from dash import dcc, html

    from qcchem.workbench.app import create_app

    app = create_app()
    shell = app.layout

    assert isinstance(shell, html.Div)
    assert shell.className == "qcchem-shell"

    child_classes = {
        getattr(child, "className", None)
        for child in shell.children
        if getattr(child, "className", None) is not None
    }
    assert "qcchem-context-bar" in child_classes

    main_grid = next(child for child in shell.children if getattr(child, "className", "") == "qcchem-main-grid")
    main_grid_classes = [getattr(child, "className", None) for child in main_grid.children]

    assert "qcchem-research-navigator" in main_grid_classes
    assert "qcchem-interpretation-rail" in main_grid_classes
    assert any(isinstance(child, dcc.Location) for child in app.validation_layout.children)
