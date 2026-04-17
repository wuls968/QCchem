from __future__ import annotations

import argparse
from typing import Any

import dash

from qcchem.workbench.app import create_app


def build_workbench_summary(app: Any, *, host: str, port: int, debug: bool) -> dict[str, Any]:
    pages = len(getattr(app, "page_registry", dash.page_registry))
    return {"url": f"http://{host}:{port}", "pages": pages, "debug": debug}


def prepare_workbench(host: str = "127.0.0.1", port: int = 8050, debug: bool = False) -> tuple[Any, dict[str, Any]]:
    app = create_app()
    return app, build_workbench_summary(app, host=host, port=port, debug=debug)


def launch_app(app: Any, *, host: str, port: int, debug: bool) -> None:
    app.run(host=host, port=port, debug=debug)


def serve_workbench(host: str = "127.0.0.1", port: int = 8050, debug: bool = False) -> dict[str, Any]:
    app, summary = prepare_workbench(host=host, port=port, debug=debug)
    launch_app(app, host=host, port=port, debug=debug)
    return summary


def print_workbench_startup(summary: dict[str, Any]) -> None:
    print("QCchem workbench ready")
    print(f"URL: {summary['url']}")
    print(f"Pages: {summary['pages']}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qcchem-workbench", description="Serve the QCchem workbench.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--debug", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    app, summary = prepare_workbench(host=args.host, port=args.port, debug=args.debug)
    print_workbench_startup(summary)
    launch_app(app, host=args.host, port=args.port, debug=args.debug)
    return 0
