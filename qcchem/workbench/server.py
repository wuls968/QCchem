from __future__ import annotations

from typing import Any


def serve_workbench(host: str = "127.0.0.1", port: int = 8050, debug: bool = False) -> dict[str, Any]:
    return {"url": f"http://{host}:{port}", "pages": 0, "debug": debug}


def main() -> int:
    serve_workbench()
    return 0
