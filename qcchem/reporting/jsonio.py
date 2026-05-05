"""JSON artifact writer for QCchem results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qcchem.io.serialization import to_primitive


def write_result_json(result: Any, path: Path) -> None:
    """Write a QCchem result object to JSON."""
    path.write_text(
        json.dumps(to_primitive(result), indent=2, sort_keys=True),
        encoding="utf-8",
    )
