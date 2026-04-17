from __future__ import annotations

import argparse
from typing import Any

from qcchem.workbench.app import create_app


def serve_workbench(host: str = "127.0.0.1", port: int = 8050, debug: bool = False) -> dict[str, Any]:
    app = create_app()
    return {"url": f"http://{host}:{port}", "pages": len(app.page_registry), "debug": debug}


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
    summary = serve_workbench(host=args.host, port=args.port, debug=args.debug)
    print_workbench_startup(summary)
    return 0
