from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from qcchem.cli.main import main
from qcchem.workbench.server import main as workbench_main

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_python_module_cli_entrypoint_runs_and_writes_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "cli-h2"
    command = [
        sys.executable,
        "-m",
        "qcchem.cli.main",
        "run",
        "-c",
        str(REPO_ROOT / "configs" / "h2.yaml"),
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


@pytest.mark.integration
def test_run_cli_resolves_relative_output_dir_against_external_config_workspace(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = tmp_path / "external_h2.yaml"
    artifact_name = f"external_h2_{tmp_path.name}"
    config.write_text(
        f"""
molecule:
  name: H2-external-output
  geometry:
    - symbol: H
      coords: [0.0, 0.0, 0.0]
    - symbol: H
      coords: [0.0, 0.0, 0.735]
  basis: sto3g
solver:
  kind: exact
run:
  output_dir: artifacts/{artifact_name}
""".strip(),
        encoding="utf-8",
    )

    assert main(["run", "-c", str(config)]) == 0

    stdout = capsys.readouterr().out
    assert "QCchem run completed: H2-external-output" in stdout
    assert (tmp_path / "artifacts" / artifact_name / "result.json").exists()
    assert not (REPO_ROOT / "artifacts" / artifact_name).exists()


def test_run_cli_reports_output_guard_rejections(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    def _reject_output(*args, **kwargs):
        raise FileExistsError("output path is inside the QCchem source tree outside artifacts")

    monkeypatch.setattr("qcchem.cli.main.run_from_config", _reject_output)

    assert main(["run", "-c", str(tmp_path / "config.yaml"), "-o", "qcchem/tmp-output"]) == 2

    stdout = capsys.readouterr().out
    assert "QCchem run rejected:" in stdout
    assert "source tree outside artifacts" in stdout


def test_exploratory_run_cli_reports_output_guard_rejections(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    def _reject_output(*args, **kwargs):
        raise FileExistsError("output path is inside the QCchem source tree outside artifacts")

    monkeypatch.setattr("qcchem.cli.main.run_from_config", _reject_output)

    assert main(["exploratory", "run", "-c", str(tmp_path / "config.yaml"), "-o", "qcchem/tmp-output"]) == 2

    stdout = capsys.readouterr().out
    assert "QCchem exploratory run rejected:" in stdout
    assert "source tree outside artifacts" in stdout


def test_runtime_collect_cli_reports_polled_status(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    def _fake_collect_runtime_artifact(artifact_root: Path) -> dict[str, object]:
        assert artifact_root == tmp_path
        return {
            "artifact_root": str(artifact_root),
            "job_id": "job-collect",
            "status": "QUEUED",
            "result_updated": False,
        }

    monkeypatch.setattr("qcchem.cli.main.collect_runtime_artifact", _fake_collect_runtime_artifact)

    exit_code = main(["runtime", "collect", str(tmp_path)])

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "Runtime collect completed" in stdout
    assert "job-collect" in stdout
    assert "QUEUED" in stdout


def test_active_space_recommend_cli_writes_json_and_yaml_patch(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    output = tmp_path / "recommendation.json"

    def _fake_recommend_active_space_from_config(config: Path) -> dict[str, object]:
        assert config == tmp_path / "config.yaml"
        return {
            "strategy": "trusted_orbital_score",
            "selected": {
                "num_electrons": [1, 1],
                "num_spatial_orbitals": 2,
                "active_orbitals_original": [1, 2],
            },
            "candidates": [{"score": 0.91}],
            "yaml_patch": {
                "problem": {
                    "active_space": {
                        "selection_mode": "auto",
                        "num_electrons": [1, 1],
                        "num_spatial_orbitals": 2,
                        "active_orbitals": [1, 2],
                        "auto": {"enabled": True, "strategy": "trusted_orbital_score"},
                    }
                }
            },
        }

    monkeypatch.setattr(
        "qcchem.cli.main.recommend_active_space_from_config",
        _fake_recommend_active_space_from_config,
    )

    exit_code = main(
        [
            "active-space",
            "recommend",
            "-c",
            str(tmp_path / "config.yaml"),
            "-o",
            str(output),
            "--emit-yaml-patch",
        ]
    )

    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["strategy"] == "trusted_orbital_score"
    stdout = capsys.readouterr().out
    assert "Active-space recommendation written" in stdout
    assert "active_space:" in stdout
    assert "trusted_orbital_score" in stdout


def test_benchmark_accept_and_artifact_index_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    case_root = tmp_path / "case"
    case_root.mkdir()
    (case_root / "result.json").write_text(
        json.dumps(
            {
                "verification_status": "validated",
                "evidence_summary": {
                    "trust_tier": "validated",
                    "recommended_action": "promote_validated_result",
                },
            }
        ),
        encoding="utf-8",
    )
    benchmark_result = tmp_path / "benchmark_result.json"
    benchmark_result.write_text(
        json.dumps(
            {
                "suite_name": "mini",
                "evidence_summary": {"trust_tier": "validated", "recommended_action": "promote_validated_result"},
                "cases": [
                    {
                        "name": "case",
                        "kind": "run",
                        "status": "validated",
                        "expected_status": "validated",
                        "artifact_root": str(case_root),
                        "evidence_summary": {"trust_tier": "validated"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert main(["benchmark", "accept", str(benchmark_result)]) == 0
    assert (tmp_path / "acceptance_summary.json").exists()
    assert main(["artifacts", "index", str(tmp_path), "-o", str(tmp_path / "index.json")]) == 0
    stdout = capsys.readouterr().out
    assert "Benchmark acceptance: accepted" in stdout
    assert "Artifact index written" in stdout


def test_benchmark_run_honors_strict_acceptance_exit_code(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    result = SimpleNamespace(
        suite_name="strict_suite",
        summary=SimpleNamespace(total_cases=1, status_counts={"exploratory": 1}),
        evidence_summary=None,
        artifacts=SimpleNamespace(root=tmp_path),
        acceptance_summary={
            "accepted": False,
            "blocking_failures": [{"reason": "status_mismatch"}],
            "policy": {"strict_exit_code": True},
        },
    )
    monkeypatch.setattr("qcchem.cli.main.run_benchmark_suite_from_config", lambda *args, **kwargs: result)

    assert main(["benchmark", "run", "-c", str(tmp_path / "suite.yaml")]) == 2


def test_release_audit_cli_prints_nested_failure_reason(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.1.0a1"\n', encoding="utf-8")
    test_target = tmp_path / "tests" / "unit" / "test_release_audit_v23.py"
    test_target.parent.mkdir(parents=True)
    test_target.write_text("# release audit fixture target\n", encoding="utf-8")
    workflow = tmp_path / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        """
name: CI

on:
  push:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Run tests
        run: python -m pytest tests/unit/test_release_audit_v23.py -q
""",
        encoding="utf-8",
    )
    config = tmp_path / "configs" / "release" / "trust_first_audit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(
        """
release_audit:
  profile: trust_first
  release_version: 0.1.0a1
  curated_artifacts: []
  required_docs: []
  acceptance_commands:
    - python -m pytest tests/unit/test_release_audit_v23.py -q
""".lstrip(),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "release",
            "audit",
            "-c",
            str(config),
            "--repo-root",
            str(tmp_path),
            "-o",
            str(tmp_path / "audit"),
        ]
    )

    stdout = capsys.readouterr().out
    assert exit_code == 2
    assert "Release audit completed: failed" in stdout
    assert (
        "- release_acceptance_sidecars:ci_freshness_gate: "
        "CI is missing or misconfigures the release acceptance sidecar freshness gate. "
        "(failure_reason=missing_ci_acceptance_status_step "
        "workflow=.github/workflows/ci.yml "
        "step_name=Run release acceptance sidecar freshness)"
    ) in stdout.splitlines()


def test_release_accept_artifact_cli_writes_bound_sidecar(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.1.0a1"\n', encoding="utf-8")
    artifact = tmp_path / "artifacts" / "h2" / "result.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        json.dumps(
            {
                "schema_version": "qcchem.result.v0.1-alpha",
                "run_id": "h2-local",
                "problem": {"molecule_name": "H2", "basis": "sto3g"},
                "energy": {"total_energy": -1.137, "energy_units": "Hartree"},
                "backend": {"kind": "statevector"},
                "benchmark": {"absolute_error": 0.0, "exact_available": True},
                "chemical_accuracy": {"available": True, "meets_chemical_accuracy": True},
                "verification_status": "validated",
            }
        ),
        encoding="utf-8",
    )
    config = tmp_path / "configs" / "release" / "trust_first_audit.yaml"
    config.parent.mkdir(parents=True)
    config.write_text(
        """
release_audit:
  profile: trust_first
  release_version: 0.1.0a1
  curated_artifacts:
    - name: h2_anchor
      path: artifacts/h2/result.json
      required: true
  required_docs: []
  acceptance_commands: []
""".lstrip(),
        encoding="utf-8",
    )

    assert (
        main(
            [
                "release",
                "acceptance-status",
                "-c",
                str(config),
                "--repo-root",
                str(tmp_path),
                "--strict",
                "--repair-plan",
            ]
        )
        == 2
    )
    stdout = capsys.readouterr().out
    assert "Release acceptance sidecars: needs_update" in stdout
    assert (
        "Sidecar issue: h2_anchor status=missing changed_fields=none "
        "sidecar=artifacts/h2/acceptance_summary.json (reason=sidecar_missing)"
    ) in stdout
    assert "Release acceptance repair plan:" in stdout
    assert "- h2_anchor status=missing issue=sidecar_missing sidecar=artifacts/h2/acceptance_summary.json" in stdout
    assert "preview: qcchem release accept-artifact" in stdout
    assert "--dry-run" in stdout
    assert "repair: qcchem release accept-artifact" in stdout
    assert "--overwrite" not in stdout

    assert (
        main(
            [
                "release",
                "accept-artifact",
                "-c",
                str(config),
                "--name",
                "h2_anchor",
                "--repo-root",
                str(tmp_path),
            ]
        )
        == 0
    )
    sidecar = artifact.parent / "acceptance_summary.json"
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    stdout = capsys.readouterr().out

    assert "Release acceptance sidecar written" in stdout
    assert payload["schema_version"] == "qcchem.release_artifact_acceptance.v0.1-alpha"
    assert payload["artifact_path"] == "artifacts/h2/result.json"
    assert payload["release_audit_check_id"] == "curated_artifact:h2_anchor:acceptance_summary"

    status_output = tmp_path / "acceptance_status.json"
    assert (
        main(
            [
                "release",
                "acceptance-status",
                "-c",
                str(config),
                "--repo-root",
                str(tmp_path),
                "--strict",
                "-o",
                str(status_output),
            ]
        )
        == 0
    )
    status = json.loads(status_output.read_text(encoding="utf-8"))
    assert status["status"] == "fresh"
    assert status["fresh_count"] == 1
    assert "Release acceptance sidecars: fresh" in capsys.readouterr().out

    artifact_payload = json.loads(artifact.read_text(encoding="utf-8"))
    artifact_payload["energy"]["total_energy"] = -1.138
    artifact.write_text(json.dumps(artifact_payload), encoding="utf-8")
    assert (
        main(
            [
                "release",
                "acceptance-status",
                "-c",
                str(config),
                "--repo-root",
                str(tmp_path),
                "--strict",
                "--repair-plan",
            ]
        )
        == 2
    )
    stdout = capsys.readouterr().out
    assert "Release acceptance sidecars: needs_update" in stdout
    assert "Sidecar issue: h2_anchor status=stale changed_fields=artifact_sha256" in stdout
    assert "(contract_failure_field=artifact_sha256" in stdout
    assert "- h2_anchor status=stale issue=contract_failure:artifact_sha256" in stdout
    assert "--dry-run" in stdout
    assert "--overwrite" in stdout

    stale_sidecar_text = sidecar.read_text(encoding="utf-8")
    assert (
        main(
            [
                "release",
                "accept-artifact",
                "-c",
                str(config),
                "--name",
                "h2_anchor",
                "--repo-root",
                str(tmp_path),
                "--dry-run",
            ]
        )
        == 0
    )
    stdout = capsys.readouterr().out
    assert "Release acceptance sidecar dry run:" in stdout
    assert "Current sidecar status: stale" in stdout
    assert "Changed fields: artifact_sha256" in stdout
    assert "Current sidecar detail: contract_failure_field=artifact_sha256" in stdout
    assert "Release acceptance sidecar written" not in stdout
    assert sidecar.read_text(encoding="utf-8") == stale_sidecar_text

    assert (
        main(
            [
                "release",
                "accept-artifact",
                "-c",
                str(config),
                "--name",
                "h2_anchor",
                "--repo-root",
                str(tmp_path),
            ]
        )
        == 2
    )
    assert "Release acceptance rejected" in capsys.readouterr().out


def test_release_acceptance_status_cli_rejects_report_contract_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = tmp_path / "trust_first_audit.yaml"
    config.write_text("release_audit:\n  profile: trust_first\n", encoding="utf-8")
    output = tmp_path / "acceptance_status.json"

    def _bad_report_from_config(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "schema_version": "qcchem.release_artifact_acceptance_status.v0.1-alpha",
            "status": "fresh",
        }

    monkeypatch.setattr(
        "qcchem.cli.main.release_acceptance_status_report_from_config",
        _bad_report_from_config,
    )

    exit_code = main(
        [
            "release",
            "acceptance-status",
            "-c",
            str(config),
            "-o",
            str(output),
        ]
    )

    stdout = capsys.readouterr().out
    assert exit_code == 2
    assert "Release acceptance status rejected:" in stdout
    assert "contract mismatch" in stdout
    assert "total_sidecars" in stdout
    assert not output.exists()


def test_aggregate_workflow_cli_passes_overwrite_flags(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, bool] = {}

    def _fake_study(config: Path, output_dir: Path | None = None, *, overwrite: bool = False):
        captured["study"] = overwrite
        return SimpleNamespace(
            study_name="study",
            summary=SimpleNamespace(total_runs=1),
            evidence_summary=None,
            artifacts=SimpleNamespace(root=output_dir or tmp_path / "study"),
        )

    def _fake_benchmark(config: Path, output_dir: Path | None = None, **kwargs):
        captured["benchmark"] = bool(kwargs.get("overwrite"))
        return SimpleNamespace(
            suite_name="suite",
            summary=SimpleNamespace(total_cases=1, status_counts={"validated": 1}),
            evidence_summary=None,
            artifacts=SimpleNamespace(root=output_dir or tmp_path / "benchmark"),
            acceptance_summary={"accepted": True, "blocking_failures": []},
        )

    def _fake_scan(config: Path, output_dir: Path | None = None, *, overwrite: bool = False):
        captured["scan"] = overwrite
        return SimpleNamespace(
            scan_name="scan",
            summary=SimpleNamespace(total_runs=1),
            evidence_summary=None,
            artifacts=SimpleNamespace(root=output_dir or tmp_path / "scan"),
        )

    def _fake_campaign(config: Path, output_dir: Path | None = None, *, overwrite: bool = False):
        captured["campaign"] = overwrite
        return {
            "campaign_name": "campaign",
            "status": "accepted",
            "artifact_root": str(output_dir or tmp_path / "campaign"),
            "acceptance_summary": {"accepted": True},
        }

    def _fake_workflow(config: Path, output_dir: Path | None = None, *, overwrite: bool = False):
        captured["workflow"] = overwrite
        return SimpleNamespace(
            workflow_name="workflow",
            status="completed",
            artifact_root=output_dir or tmp_path / "workflow",
            outputs={"workflow_report_markdown": str(tmp_path / "workflow" / "workflow_report.md")},
        )

    monkeypatch.setattr("qcchem.cli.main.run_study_from_config", _fake_study)
    monkeypatch.setattr("qcchem.cli.main.run_benchmark_suite_from_config", _fake_benchmark)
    monkeypatch.setattr("qcchem.cli.main.run_scan_from_config", _fake_scan)
    monkeypatch.setattr("qcchem.cli.main.run_campaign_from_config", _fake_campaign)
    monkeypatch.setattr("qcchem.cli.main.run_custom_workflow_from_config", _fake_workflow)

    assert main(["study", "run", "-c", str(tmp_path / "study.yaml"), "--overwrite"]) == 0
    assert main(["benchmark", "run", "-c", str(tmp_path / "suite.yaml"), "--overwrite"]) == 0
    assert main(["scan", "run", "-c", str(tmp_path / "scan.yaml"), "--overwrite"]) == 0
    assert main(["campaign", "run", "-c", str(tmp_path / "campaign.yaml"), "--overwrite"]) == 0
    assert main(["workflow", "run", "-c", str(tmp_path / "workflow.yaml"), "--overwrite"]) == 0
    assert captured == {
        "study": True,
        "benchmark": True,
        "scan": True,
        "campaign": True,
        "workflow": True,
    }


def test_aggregate_workflow_cli_reports_existing_output_rejections(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def _raise_existing_output(*args, **kwargs):
        assert kwargs.get("overwrite") is False
        raise FileExistsError("output directory already exists and is not empty")

    monkeypatch.setattr("qcchem.cli.main.run_study_from_config", _raise_existing_output)
    monkeypatch.setattr("qcchem.cli.main.run_benchmark_suite_from_config", _raise_existing_output)
    monkeypatch.setattr("qcchem.cli.main.run_scan_from_config", _raise_existing_output)
    monkeypatch.setattr("qcchem.cli.main.run_campaign_from_config", _raise_existing_output)
    monkeypatch.setattr("qcchem.cli.main.run_custom_workflow_from_config", _raise_existing_output)

    assert main(["study", "run", "-c", str(tmp_path / "study.yaml")]) == 2
    assert main(["benchmark", "run", "-c", str(tmp_path / "suite.yaml")]) == 2
    assert main(["scan", "run", "-c", str(tmp_path / "scan.yaml")]) == 2
    assert main(["campaign", "run", "-c", str(tmp_path / "campaign.yaml")]) == 2
    assert main(["workflow", "run", "-c", str(tmp_path / "workflow.yaml")]) == 2

    stdout = capsys.readouterr().out
    assert "Study rejected: output directory already exists and is not empty" in stdout
    assert "Benchmark suite rejected: output directory already exists and is not empty" in stdout
    assert "Scan rejected: output directory already exists and is not empty" in stdout
    assert "Campaign rejected: output directory already exists and is not empty" in stdout
    assert "Workflow run rejected: output directory already exists and is not empty" in stdout


def test_campaign_artifact_only_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    artifact_root = tmp_path / "artifacts" / "h2"
    artifact_root.mkdir(parents=True)
    (artifact_root / "result.json").write_text(
        json.dumps(
            {
                "run_id": "h2",
                "verification_status": "validated",
                "evidence_summary": {
                    "trust_tier": "validated",
                    "recommended_action": "promote_validated_result",
                },
            }
        ),
        encoding="utf-8",
    )
    config = tmp_path / "campaign.yaml"
    config.write_text(
        f"""
campaign:
  name: mini_campaign
  output_root: {tmp_path / "campaign_out"}
  entries:
    - name: existing_h2
      kind: artifact
      artifact: {artifact_root}
""",
        encoding="utf-8",
    )

    result_path = tmp_path / "campaign_out" / "campaign_result.json"
    assert main(["campaign", "run", "-c", str(config)]) == 0
    assert result_path.exists()
    assert main(["campaign", "report", str(result_path)]) == 0
    assert main(["campaign", "accept", str(result_path)]) == 0
    sentinel = tmp_path / "campaign_out" / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    assert main(["campaign", "run", "-c", str(config)]) == 2
    assert sentinel.read_text(encoding="utf-8") == "keep"
    assert main(["campaign", "run", "-c", str(config), "--overwrite"]) == 0
    assert not sentinel.exists()
    stdout = capsys.readouterr().out
    assert "Campaign completed: mini_campaign" in stdout
    assert "Campaign acceptance: accepted" in stdout
    assert "Campaign rejected:" in stdout


def test_workbench_cli_reports_startup(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_app = object()
    events: list[tuple[str, object]] = []

    def _fake_prepare_workbench(
        host: str,
        port: int,
        debug: bool,
        artifact_root: Path | None = None,
    ) -> tuple[object, dict[str, object]]:
        assert host == "127.0.0.1"
        assert port == 8050
        assert debug is False
        assert artifact_root is None
        events.append(("prepare", (host, port, debug, artifact_root)))
        return fake_app, {"url": "http://127.0.0.1:8050", "pages": 10}

    def _fake_launch_app(app: object, *, host: str, port: int, debug: bool) -> None:
        assert app is fake_app
        events.append(("launch", (host, port, debug)))

    def _fake_print_workbench_startup(summary: dict[str, object]) -> None:
        events.append(("print", summary["url"]))
        print("QCchem workbench ready")
        print(f"URL: {summary['url']}")
        print(f"Pages: {summary['pages']}")

    def _unexpected_serve_workbench(
        host: str,
        port: int,
        debug: bool,
        artifact_root: Path | None = None,
    ) -> dict[str, object]:
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
        ("prepare", ("127.0.0.1", 8050, False, None)),
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


def test_workbench_cli_passes_artifact_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_app = object()
    captured: dict[str, object] = {}

    def _fake_prepare_workbench(
        host: str,
        port: int,
        debug: bool,
        artifact_root: Path | None = None,
    ) -> tuple[object, dict[str, object]]:
        captured["artifact_root"] = artifact_root
        return fake_app, {"url": f"http://{host}:{port}", "pages": 1}

    def _fake_launch_app(app: object, *, host: str, port: int, debug: bool) -> None:
        assert app is fake_app

    monkeypatch.setattr(
        "qcchem.cli.main.importlib.import_module",
        lambda name: SimpleNamespace(
            prepare_workbench=_fake_prepare_workbench,
            launch_app=_fake_launch_app,
            print_workbench_startup=lambda summary: None,
        ),
    )

    exit_code = main(["workbench", "serve", "--artifact-root", str(tmp_path / "artifacts")])

    assert exit_code == 0
    assert captured["artifact_root"] == tmp_path / "artifacts"


def test_workbench_cli_rejects_missing_artifact_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["workbench", "serve", "--artifact-root", str(tmp_path / "missing-artifacts")])

    assert exit_code == 2
    stdout = capsys.readouterr().out
    assert "QCchem workbench rejected:" in stdout
    assert "artifact root does not exist" in stdout


def test_workbench_script_reports_startup(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_app = object()

    def _fake_prepare_workbench(
        host: str,
        port: int,
        debug: bool,
        artifact_root: Path | None = None,
    ) -> tuple[object, dict[str, object]]:
        assert host == "0.0.0.0"
        assert port == 9001
        assert debug is True
        assert artifact_root is None
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


def test_workbench_script_passes_artifact_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_app = object()
    captured: dict[str, object] = {}

    def _fake_prepare_workbench(
        host: str,
        port: int,
        debug: bool,
        artifact_root: Path | None = None,
    ) -> tuple[object, dict[str, object]]:
        captured["artifact_root"] = artifact_root
        return fake_app, {"url": f"http://{host}:{port}", "pages": 10}

    def _fake_launch_app(app: object, *, host: str, port: int, debug: bool) -> None:
        assert app is fake_app

    monkeypatch.setattr("qcchem.workbench.server.prepare_workbench", _fake_prepare_workbench)
    monkeypatch.setattr("qcchem.workbench.server.launch_app", _fake_launch_app)

    exit_code = workbench_main(["--artifact-root", str(tmp_path / "artifacts")])

    assert exit_code == 0
    assert captured["artifact_root"] == tmp_path / "artifacts"


def test_workbench_script_rejects_missing_artifact_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = workbench_main(["--artifact-root", str(tmp_path / "missing-artifacts")])

    assert exit_code == 2
    stdout = capsys.readouterr().out
    assert "QCchem workbench rejected:" in stdout
    assert "artifact root does not exist" in stdout
