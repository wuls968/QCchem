from __future__ import annotations

from typing import Any

SHARED_THEME_FAMILIES: tuple[str, ...] = (
    "surface",
    "text",
    "accent",
    "status",
    "spacing",
    "radius",
    "shadow",
    "type",
)

THEME: dict[str, dict[str, Any]] = {
    "surface": {
        "paper": "#f2f4f8",
        "card": "#ffffff",
        "panel": "#f8fafc",
        "canvas": "#dde1e6",
        "line": "#c1c7cd",
    },
    "text": {
        "primary": "#161616",
        "secondary": "#525252",
        "muted": "#6f6f6f",
        "inverse": "#f4f4f4",
    },
    "accent": {
        "copper": "#0f62fe",
        "deep_blue": "#002d9c",
        "ice": "#edf5ff",
        "sage": "#a6c8ff",
        "signal": "#4589ff",
    },
    "status": {
        "validated": "#198038",
        "exploratory": "#8a6d1f",
        "unstable": "#da1e28",
        "informational": "#0043ce",
    },
    "spacing": {
        "xxs": "0.125rem",
        "xs": "0.375rem",
        "sm": "0.75rem",
        "md": "1rem",
        "lg": "1.5rem",
        "xl": "2rem",
        "xxl": "2.75rem",
    },
    "radius": {
        "sm": "6px",
        "md": "10px",
        "lg": "14px",
        "xl": "20px",
        "pill": "999px",
    },
    "shadow": {
        "card": "0 1px 2px rgba(22, 22, 22, 0.08), 0 8px 24px rgba(22, 22, 22, 0.06)",
        "panel": "0 1px 2px rgba(22, 22, 22, 0.08), 0 16px 40px rgba(22, 22, 22, 0.08)",
    },
    "type": {
        "display": "'IBM Plex Sans', 'Helvetica Neue', sans-serif",
        "body": "'IBM Plex Sans', 'Helvetica Neue', sans-serif",
        "mono": "'IBM Plex Mono', 'SFMono-Regular', 'Menlo', monospace",
    },
}


def css_var_map(*, families: tuple[str, ...] | None = None) -> dict[str, str]:
    variables: dict[str, str] = {}
    included = families or tuple(THEME.keys())
    for section in included:
        values = THEME[section]
        if isinstance(values, dict):
            for key, value in values.items():
                variables[f"--qcchem-{section}-{key.replace('_', '-')}"] = str(value)
    return variables


def css_var_lines(*, families: tuple[str, ...] | None = None) -> list[str]:
    return [f"  {name}: {value};" for name, value in css_var_map(families=families).items()]
