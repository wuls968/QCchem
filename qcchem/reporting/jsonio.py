"""JSON artifact writer for QCchem results."""

from __future__ import annotations

import json
import os
from tempfile import NamedTemporaryFile
from pathlib import Path
from typing import Any

from qcchem.io.serialization import to_primitive


def write_result_json(result: Any, path: Path) -> None:
    """Write a QCchem result object to JSON."""
    content = json.dumps(to_primitive(result), indent=2, sort_keys=True)
    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                prefix=f".{path.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
