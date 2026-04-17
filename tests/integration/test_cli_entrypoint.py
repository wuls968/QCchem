from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from qcchem.cli.main import main


@pytest.mark.integration
def test_python_module_cli_entrypoint_runs_and_writes_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "cli-h2"
    command = [
        sys.executable,
        "-m",
        "qcchem.cli.main",
        "run",
        "-c",
        str(Path("/Users/a0000/QCchem/configs/h2.yaml")),
        "-o",
        str(output_dir),
    ]

    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "QCchem run completed: H2" in completed.stdout
    assert (output_dir / "result.json").exists()
    assert (output_dir / "report.md").exists()


def test_workbench_cli_reports_startup(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def _fake_serve_workbench(host: str, port: int, debug: bool) -> dict[str, object]:
        assert host == "127.0.0.1"
        assert port == 8050
        assert debug is False
        return {"url": "http://127.0.0.1:8050", "pages": 10}

    monkeypatch.setattr("qcchem.cli.main.serve_workbench", _fake_serve_workbench)

    exit_code = main(["workbench", "serve"])

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "QCchem workbench ready" in stdout
    assert "http://127.0.0.1:8050" in stdout
