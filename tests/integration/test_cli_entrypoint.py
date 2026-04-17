from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from qcchem.cli.main import main
from qcchem.workbench.server import main as workbench_main


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
    fake_app = object()
    events: list[tuple[str, object]] = []

    def _fake_prepare_workbench(host: str, port: int, debug: bool) -> tuple[object, dict[str, object]]:
        assert host == "127.0.0.1"
        assert port == 8050
        assert debug is False
        events.append(("prepare", (host, port, debug)))
        return fake_app, {"url": "http://127.0.0.1:8050", "pages": 10}

    def _fake_launch_app(app: object, *, host: str, port: int, debug: bool) -> None:
        assert app is fake_app
        events.append(("launch", (host, port, debug)))

    def _fake_print_workbench_startup(summary: dict[str, object]) -> None:
        events.append(("print", summary["url"]))
        print("QCchem workbench ready")
        print(f"URL: {summary['url']}")
        print(f"Pages: {summary['pages']}")

    def _unexpected_serve_workbench(host: str, port: int, debug: bool) -> dict[str, object]:
        raise AssertionError("CLI startup should use prepare_workbench and launch_app sequencing")

    monkeypatch.setattr(
        "qcchem.cli.main.importlib.import_module",
        lambda name: SimpleNamespace(
            prepare_workbench=_fake_prepare_workbench,
            launch_app=_fake_launch_app,
            serve_workbench=_unexpected_serve_workbench,
            print_workbench_startup=_fake_print_workbench_startup,
        ),
    )

    exit_code = main(["workbench", "serve"])

    assert exit_code == 0
    assert events == [
        ("prepare", ("127.0.0.1", 8050, False)),
        ("print", "http://127.0.0.1:8050"),
        ("launch", ("127.0.0.1", 8050, False)),
    ]
    stdout = capsys.readouterr().out
    assert "QCchem workbench ready" in stdout
    assert "http://127.0.0.1:8050" in stdout


def test_workbench_cli_reports_missing_optional_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def _raise_module_not_found(name: str) -> object:
        raise ModuleNotFoundError("dash is not installed", name="dash")

    monkeypatch.setattr("qcchem.cli.main.importlib.import_module", _raise_module_not_found)

    exit_code = main(["workbench", "serve"])

    assert exit_code == 2
    stdout = capsys.readouterr().out
    assert "QCchem workbench requires optional UI dependencies" in stdout
    assert 'pip install -e ".[ui]"' in stdout


def test_workbench_script_reports_startup(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_app = object()

    def _fake_prepare_workbench(host: str, port: int, debug: bool) -> tuple[object, dict[str, object]]:
        assert host == "0.0.0.0"
        assert port == 9001
        assert debug is True
        return fake_app, {"url": "http://0.0.0.0:9001", "pages": 10}

    def _fake_launch_app(app: object, *, host: str, port: int, debug: bool) -> None:
        assert app is fake_app
        assert host == "0.0.0.0"
        assert port == 9001
        assert debug is True

    monkeypatch.setattr("qcchem.workbench.server.prepare_workbench", _fake_prepare_workbench)
    monkeypatch.setattr("qcchem.workbench.server.launch_app", _fake_launch_app)

    exit_code = workbench_main(["--host", "0.0.0.0", "--port", "9001", "--debug"])

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "QCchem workbench ready" in stdout
    assert "http://0.0.0.0:9001" in stdout
