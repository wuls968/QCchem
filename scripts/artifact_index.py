#!/usr/bin/env python
"""Generate a compact QCchem artifact index."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from qcchem.io.artifact_index import build_artifact_index


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts")
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else root / "artifact_index.json"
    index = build_artifact_index(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
