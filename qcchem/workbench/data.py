from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_artifact_bundle(root: Path) -> dict[str, Any]:
    result_path = root / "result.json"
    qcschema_path = root / "qcschema.json"
    hdf5_path = root / "result.h5"
    bundle = {
        "root": str(root),
        "result": json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else None,
        "qcschema": json.loads(qcschema_path.read_text(encoding="utf-8")) if qcschema_path.exists() else None,
        "hdf5_path": str(hdf5_path) if hdf5_path.exists() else None,
    }
    return bundle
