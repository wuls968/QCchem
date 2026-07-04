from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Any


@dataclass(frozen=True)
class WorkbenchSmokeRoute:
    route: str
    active_label: str
    expected_text: str


def _walk_components(component: object) -> Iterable[object]:
    if isinstance(component, (list, tuple)):
        for child in component:
            yield from _walk_components(child)
        return
    yield component
    children = getattr(component, "children", None)
    if children is None:
        return
    if isinstance(children, (list, tuple)):
        for child in children:
            yield from _walk_components(child)
    else:
        yield from _walk_components(children)


def _collect_text(component: object) -> str:
    parts: list[str] = []
    for item in _walk_components(component):
        if isinstance(item, str):
            parts.append(item)
    return " ".join(parts)


def _normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def _text_excerpt(value: object, *, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def parse_workbench_smoke_routes(docs_path: Path) -> list[WorkbenchSmokeRoute]:
    docs = docs_path.read_text(encoding="utf-8")
    section_match = re.search(r"## Browser Smoke Checklist\n\n(?P<body>.*?)(?=\n## |\Z)", docs, flags=re.S)
    if section_match is None:
        raise ValueError(f"{docs_path} does not contain a Browser Smoke Checklist section.")

    routes: list[WorkbenchSmokeRoute] = []
    seen_routes: set[str] = set()
    for line in section_match.group("body").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        normalized_row = re.sub(r"\s+", " ", stripped).casefold()
        separator_row = re.match(r"^\|\s*:?-{3,}:?\s*\|\s*:?-{3,}:?\s*\|\s*:?-{3,}:?\s*\|$", stripped)
        if normalized_row == "| route | active route label | route-specific text to confirm |" or separator_row:
            continue
        match = re.match(
            r"^\|\s*`(?P<route>/[^`]+)`\s*\|\s*(?P<label>[^|]+?)\s*\|\s*(?P<text>[^|]+?)\s*\|$",
            line,
        )
        if match is None:
            raise ValueError(f"{docs_path} Browser Smoke Checklist has a malformed route row: {stripped}")
        route = match.group("route").strip()
        active_label = match.group("label").strip()
        expected_text = match.group("text").strip()
        if not route or not active_label or not expected_text:
            raise ValueError(f"{docs_path} Browser Smoke Checklist route rows must not contain empty cells: {stripped}")
        if route in seen_routes:
            raise ValueError(f"{docs_path} Browser Smoke Checklist contains duplicate route: {route}")
        seen_routes.add(route)
        routes.append(
            WorkbenchSmokeRoute(
                route=route,
                active_label=active_label,
                expected_text=expected_text,
            )
        )

    if not routes:
        raise ValueError(f"{docs_path} Browser Smoke Checklist does not list any routes.")
    return routes


def _render_page_text(page: dict[str, Any]) -> str:
    layout = page.get("layout")
    component = layout() if callable(layout) else layout
    return _collect_text(component)


def _render_page_text_or_error(page: dict[str, Any]) -> tuple[str, str | None]:
    try:
        return _render_page_text(page), None
    except Exception as exc:
        return "", f"{type(exc).__name__}: {exc}"


def _registered_pages(page_registry: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        [page for page in page_registry.values() if page.get("path")],
        key=lambda page: (int(page.get("order") or 0), str(page.get("path") or ""), str(page.get("name") or "")),
    )


def _failed_check_names(checks: dict[str, bool]) -> list[str]:
    return [name for name, passed in checks.items() if not passed]


def _failed_check_ids(kind: str, items: list[dict[str, object]], subject_key: str) -> list[str]:
    failures: list[str] = []
    for item in items:
        failed_checks = item.get("failed_checks")
        if not isinstance(failed_checks, list):
            continue
        subject = str(item.get(subject_key) or "")
        for check in failed_checks:
            failures.append(f"{kind}:{subject}:{check}")
    return failures


def _page_registry_result(page: dict[str, Any]) -> dict[str, object]:
    from qcchem.workbench.components.layout import page_focus

    path = str(page.get("path"))
    page_text, render_error = _render_page_text_or_error(page)
    normalized_page_text = _normalize_text(page_text)
    focus = page_focus(path)
    title = str(page.get("title") or page.get("name") or path)
    checks = {
        "rendered": render_error is None,
        "nonblank": bool(normalized_page_text),
        "not_placeholder": "placeholder page" not in normalized_page_text,
        "active_label": bool(str(focus.get("route_label") or "").strip()),
        "title_text": _normalize_text(title) in normalized_page_text,
    }
    failed_checks = _failed_check_names(checks)
    return {
        "path": path,
        "name": page.get("name"),
        "title": page.get("title"),
        "route_label": focus.get("route_label"),
        "text_excerpt": _text_excerpt(page_text),
        "render_error": render_error,
        "checks": checks,
        "failed_checks": failed_checks,
        "status": "passed" if not failed_checks else "failed",
    }


def run_workbench_smoke(routes: list[WorkbenchSmokeRoute], *, artifact_root: Path | None = None) -> dict[str, object]:
    import dash

    from qcchem.workbench.app import create_app
    from qcchem.workbench.components.layout import page_focus
    from qcchem.workbench.data import WORKBENCH_ARTIFACT_ROOT_ENV, resolve_workbench_artifact_root

    resolved_artifact_root = resolve_workbench_artifact_root(artifact_root)
    os.environ[WORKBENCH_ARTIFACT_ROOT_ENV] = str(resolved_artifact_root)
    app = create_app()
    page_registry = getattr(app, "page_registry", dash.page_registry)
    registered_pages = _registered_pages(page_registry)
    pages_by_path = {str(page.get("path")): page for page in registered_pages}
    registered_routes = sorted(pages_by_path)

    route_results: list[dict[str, object]] = []
    for route in routes:
        page = pages_by_path.get(route.route)
        focus = page_focus(route.route)
        route_label = str(focus.get("route_label") or "")
        if page is None:
            page_text = ""
            render_error = None
        else:
            page_text, render_error = _render_page_text_or_error(page)
        normalized_page_text = _normalize_text(page_text)
        expected_text = _normalize_text(route.expected_text)
        checks = {
            "registered": page is not None,
            "rendered": page is None or render_error is None,
            "active_label": route_label == route.active_label,
            "nonblank": bool(normalized_page_text),
            "expected_text": expected_text in normalized_page_text,
            "not_placeholder": "placeholder page" not in normalized_page_text,
        }
        failed_checks = _failed_check_names(checks)
        route_results.append(
            {
                "route": route.route,
                "page_name": page.get("name") if page is not None else None,
                "page_title": page.get("title") if page is not None else None,
                "expected_active_label": route.active_label,
                "actual_active_label": route_label,
                "expected_text": route.expected_text,
                "text_excerpt": _text_excerpt(page_text),
                "render_error": render_error,
                "checks": checks,
                "failed_checks": failed_checks,
                "status": "passed" if not failed_checks else "failed",
            }
        )

    failed_routes = [item for item in route_results if item["status"] != "passed"]
    page_results = [_page_registry_result(page) for page in registered_pages]
    failed_pages = [item for item in page_results if item["status"] != "passed"]
    failed_checks = _failed_check_ids("route", route_results, "route") + _failed_check_ids("page", page_results, "path")
    return {
        "schema_version": "qcchem.workbench_smoke.v0.1-alpha",
        "status": "passed" if not failed_routes and not failed_pages else "failed",
        "failed_checks": failed_checks,
        "scope": "component_tree",
        "artifact_root": str(resolved_artifact_root),
        "notes": [
            "Validates the documented showcase routes and all registered pages without starting a server or browser.",
            "Run the real browser checklist separately before release candidates.",
        ],
        "registered_routes": registered_routes,
        "route_count": len(route_results),
        "passed_routes": len(route_results) - len(failed_routes),
        "failed_routes": len(failed_routes),
        "routes": route_results,
        "page_count": len(page_results),
        "passed_pages": len(page_results) - len(failed_pages),
        "failed_pages": len(failed_pages),
        "pages": page_results,
    }


def run_workbench_smoke_from_docs(docs_path: Path, *, artifact_root: Path | None = None) -> dict[str, object]:
    routes = parse_workbench_smoke_routes(docs_path)
    summary = run_workbench_smoke(routes, artifact_root=artifact_root)
    summary["docs_path"] = str(docs_path)
    return summary
