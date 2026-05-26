from __future__ import annotations

import json
from pathlib import Path

from qcchem.cli.main import main


def test_objective_cli_init_and_plan(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "configs" / "h2.yaml"
    config.parent.mkdir()
    config.write_text("run: {}\n", encoding="utf-8")
    objective = tmp_path / "objective.yaml"

    assert main(["objective", "init", "--name", "h2_local_validation", "--claim", "H2 local validation", "-o", str(objective)]) == 0
    assert objective.exists()
    payload = capsys.readouterr().out
    assert "Objective template written" in payload

    text = objective.read_text(encoding="utf-8")
    text = text.replace("- configs/h2.yaml", f"- {config}")
    objective.write_text(text, encoding="utf-8")

    assert main(["objective", "plan", "-c", str(objective), "-o", str(tmp_path / "plan")]) == 0
    plan = json.loads((tmp_path / "plan" / "objective_plan.json").read_text(encoding="utf-8"))
    assert plan["schema_version"] == "qcchem.objective.v0.1-alpha"
    assert plan["objective_name"] == "h2_local_validation"
