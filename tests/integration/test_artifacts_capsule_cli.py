from __future__ import annotations

import json
from pathlib import Path

from qcchem.cli.main import main
from tests.unit.test_evidence_capsule import _write_run


def test_artifacts_capsule_cli_writes_json_and_markdown(tmp_path: Path, capsys) -> None:
    _write_run(tmp_path / "h2")

    assert main(["artifacts", "capsule", str(tmp_path / "h2"), "-o", str(tmp_path / "capsule")]) == 0

    payload = json.loads((tmp_path / "capsule" / "evidence_capsule.json").read_text(encoding="utf-8"))
    assert payload["capsule_status"] == "complete"
    assert (tmp_path / "capsule" / "evidence_capsule.md").exists()
    assert "Evidence capsule written" in capsys.readouterr().out
