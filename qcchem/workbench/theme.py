from __future__ import annotations

from typing import Any

THEME: dict[str, dict[str, Any]] = {
    "surface": {
        "paper": "#f7f1e8",
        "card": "#fffaf3",
        "panel": "#fbf5ec",
        "canvas": "#efe5d6",
        "line": "#dfd0ba",
    },
    "text": {
        "primary": "#2d2216",
        "secondary": "#6d5a46",
        "muted": "#8a765f",
        "inverse": "#f8f3eb",
    },
    "accent": {
        "copper": "#9a6b3f",
        "deep_blue": "#20334a",
        "ice": "#d9ecf4",
        "sage": "#93a18a",
        "signal": "#c58742",
    },
    "status": {
        "validated": "#315f4a",
        "exploratory": "#8b6a3f",
        "unstable": "#91453f",
        "informational": "#46607a",
    },
    "spacing": {
        "xxs": "0.25rem",
        "xs": "0.5rem",
        "sm": "0.75rem",
        "md": "1rem",
        "lg": "1.5rem",
        "xl": "2rem",
        "xxl": "3rem",
    },
    "radius": {
        "sm": "12px",
        "md": "18px",
        "lg": "22px",
        "xl": "32px",
        "pill": "999px",
    },
    "shadow": {
        "card": "0 18px 48px rgba(84, 63, 36, 0.12)",
        "panel": "0 10px 24px rgba(32, 51, 74, 0.08)",
    },
    "type": {
        "display": "'Iowan Old Style', 'Palatino Linotype', serif",
        "body": "'Avenir Next', 'Helvetica Neue', sans-serif",
        "mono": "'SFMono-Regular', 'Menlo', monospace",
    },
}


def css_var_map() -> dict[str, str]:
    variables: dict[str, str] = {}
    for section, values in THEME.items():
        if isinstance(values, dict):
            for key, value in values.items():
                variables[f"--qcchem-{section}-{key.replace('_', '-')}"] = str(value)
    return variables

