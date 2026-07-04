from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

import dash

from qcchem.workbench.app import create_app
from qcchem.workbench.data import WORKBENCH_ARTIFACT_ROOT_ENV, resolve_workbench_artifact_root

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT_ROOT = REPO_ROOT / "artifacts"
_GENERATED_ARTIFACT_DIR_NAMES = {"preview_local"}
_INVENTORY_RESULT_FILENAMES = {
    "result.json",
    "benchmark_result.json",
    "study_result.json",
    "scan_result.json",
    "hardware_calibration_summary.json",
}


def _find_first_existing(*paths: Path) -> str | None:
    for path in paths:
        if path.exists():
            return str(path)
    return None


def _is_nested_generated_artifact_file(path: Path, *, root: Path) -> bool:
    try:
        relative_parts = path.relative_to(root).parts
    except ValueError:
        relative_parts = path.parts
    parent_parts = relative_parts[:-1]
    return any(name in parent_parts for name in _GENERATED_ARTIFACT_DIR_NAMES)


def _artifact_files(root: Path, filename: str) -> list[Path]:
    return sorted(
        path
        for path in root.rglob(filename)
        if path.is_file() and not _is_nested_generated_artifact_file(path, root=root)
    )


def _empty_artifact_inventory(
    *,
    root_exists: bool,
    root_is_dir: bool,
    inventory_error: str | None = None,
) -> dict[str, Any]:
    return {
        "artifact_root_exists": root_exists,
        "artifact_root_is_dir": root_is_dir,
        "inventory_error": inventory_error,
        "run_result_roots": 0,
        "benchmark_suites": 0,
        "study_results": 0,
        "scan_results": 0,
        "hardware_campaigns": 0,
        "report_markdown_roots": 0,
        "runtime_submission_sidecars": 0,
        "skipped_generated_artifacts": 0,
        "featured_run": None,
        "featured_benchmark": None,
        "featured_study": None,
        "featured_scan": None,
        "featured_hardware_campaign": None,
    }


def _count_skipped_generated_artifacts(root: Path) -> int:
    return sum(
        1
        for path in root.rglob("*.json")
        if path.is_file()
        and path.name in _INVENTORY_RESULT_FILENAMES
        and _is_nested_generated_artifact_file(path, root=root)
    )


def _artifact_inventory(root: Path) -> dict[str, Any]:
    if not root.exists():
        return _empty_artifact_inventory(root_exists=False, root_is_dir=False)
    if not root.is_dir():
        return _empty_artifact_inventory(
            root_exists=True,
            root_is_dir=False,
            inventory_error="Artifact root is not a directory.",
        )

    run_results = _artifact_files(root, "result.json")
    benchmark_results = _artifact_files(root, "benchmark_result.json")
    study_results = _artifact_files(root, "study_result.json")
    scan_results = _artifact_files(root, "scan_result.json")
    hardware_campaigns = _artifact_files(root, "hardware_calibration_summary.json")
    report_markdowns = _artifact_files(root, "report.md")
    runtime_sidecars = _artifact_files(root, "runtime_submission.json")

    return {
        "artifact_root_exists": True,
        "artifact_root_is_dir": True,
        "inventory_error": None,
        "run_result_roots": len(run_results),
        "benchmark_suites": len(benchmark_results),
        "study_results": len(study_results),
        "scan_results": len(scan_results),
        "hardware_campaigns": len(hardware_campaigns),
        "report_markdown_roots": len(report_markdowns),
        "runtime_submission_sidecars": len(runtime_sidecars),
        "skipped_generated_artifacts": _count_skipped_generated_artifacts(root),
        "featured_run": _find_first_existing(
            root / "h2_runtime_hardware_probe_puccd_layout" / "result.json",
            root / "h2" / "result.json",
            *(path for path in run_results[:1]),
        ),
        "featured_benchmark": _find_first_existing(
            root / "hardware_calibration_suite_v1" / "benchmark_report.md",
            root / "benchmark_suite_v1" / "benchmark_result.json",
            *(path for path in benchmark_results[:1]),
        ),
        "featured_study": _find_first_existing(
            root / "mini_comparison_study" / "study_result.json",
            *(path for path in study_results[:1]),
        ),
        "featured_scan": _find_first_existing(
            root / "h2_short_scan" / "scan_result.json",
            *(path for path in scan_results[:1]),
        ),
        "featured_hardware_campaign": _find_first_existing(
            root / "hardware_calibration_suite_v1" / "hardware_calibration_summary.json",
            *(path for path in hardware_campaigns[:1]),
        ),
    }


def _page_inventory(page_registry: dict[str, Any]) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    for page in sorted(
        page_registry.values(),
        key=lambda page: (int(page.get("order") or 0), str(page.get("path") or ""), str(page.get("name") or "")),
    ):
        path = page.get("path")
        if not path:
            continue
        pages.append(
            {
                "path": path,
                "name": page.get("name"),
                "title": page.get("title"),
                "order": page.get("order"),
                "description": page.get("description"),
            }
        )
    return pages


def build_workbench_summary(
    app: Any,
    *,
    host: str,
    port: int,
    debug: bool,
    artifact_root: Path | None = None,
) -> dict[str, Any]:
    page_registry = getattr(app, "page_registry", dash.page_registry)
    pages = _page_inventory(page_registry)
    page_paths = [page["path"] for page in pages]
    resolved_artifact_root = resolve_workbench_artifact_root(artifact_root)
    artifact_inventory = _artifact_inventory(resolved_artifact_root)
    return {
        "url": f"http://{host}:{port}",
        "pages": pages,
        "page_count": len(pages),
        "page_paths": page_paths,
        "default_route": "/overview",
        "artifact_root": str(resolved_artifact_root),
        "artifact_inventory": artifact_inventory,
        "debug": debug,
    }


def prepare_workbench(
    host: str = "127.0.0.1",
    port: int = 8050,
    debug: bool = False,
    artifact_root: Path | None = None,
) -> tuple[Any, dict[str, Any]]:
    resolved_artifact_root = resolve_workbench_artifact_root(artifact_root)
    os.environ[WORKBENCH_ARTIFACT_ROOT_ENV] = str(resolved_artifact_root)
    app = create_app()
    return app, build_workbench_summary(
        app,
        host=host,
        port=port,
        debug=debug,
        artifact_root=resolved_artifact_root,
    )


def launch_app(app: Any, *, host: str, port: int, debug: bool) -> None:
    app.run(host=host, port=port, debug=debug)


def serve_workbench(
    host: str = "127.0.0.1",
    port: int = 8050,
    debug: bool = False,
    artifact_root: Path | None = None,
) -> dict[str, Any]:
    app, summary = prepare_workbench(host=host, port=port, debug=debug, artifact_root=artifact_root)
    launch_app(app, host=host, port=port, debug=debug)
    return summary


def print_workbench_startup(summary: dict[str, Any]) -> None:
    page_count = summary.get("page_count")
    if page_count is None:
        pages = summary.get("pages", [])
        page_count = len(pages) if isinstance(pages, list) else pages
    default_route = summary.get("default_route", "/overview")
    artifact_root = summary.get("artifact_root", "n/a")
    inventory = summary.get("artifact_inventory") or {}
    print("QCchem workbench ready")
    print(f"URL: {summary['url']}")
    print(f"Pages: {page_count}")
    print(f"Default route: {default_route}")
    print(f"Artifact root: {artifact_root}")
    print(
        "Artifact inventory: "
        f"runs={inventory.get('run_result_roots')} "
        f"benchmarks={inventory.get('benchmark_suites')} "
        f"studies={inventory.get('study_results')} "
        f"scans={inventory.get('scan_results')} "
        f"hardware={inventory.get('hardware_campaigns')} "
        f"reports={inventory.get('report_markdown_roots')} "
        f"runtime_sidecars={inventory.get('runtime_submission_sidecars')}"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qcchem-workbench", description="Serve the QCchem workbench.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "--artifact-root",
        type=Path,
        help="Artifact root to index; defaults to ./artifacts when present.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        app, summary = prepare_workbench(
            host=args.host,
            port=args.port,
            debug=args.debug,
            artifact_root=args.artifact_root,
        )
    except (OSError, ValueError) as exc:
        print(f"QCchem workbench rejected: {exc}")
        return 2
    print_workbench_startup(summary)
    launch_app(app, host=args.host, port=args.port, debug=args.debug)
    return 0
