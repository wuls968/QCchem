from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from qcchem.io.release_audit_config import load_release_audit_spec
from qcchem.workflow.release_audit import run_release_audit


def test_release_audit_datetime_utc_usage_is_python310_compatible() -> None:
    source = Path("qcchem/workflow/release_audit.py").read_text(encoding="utf-8")

    assert "from datetime import UTC" not in source
    assert "datetime.now(UTC)" not in source
    assert "timezone.utc" in source


def _write_release_fixture(root: Path) -> None:
    (root / "pyproject.toml").write_text('[project]\nversion = "0.1.0a1"\n', encoding="utf-8")
    (root / "README.md").write_text(
        "QFT LR-ACE TC-QSCI finite-cutoff exploratory boundary release audit",
        encoding="utf-8",
    )
    docs = root / "docs"
    docs.mkdir()
    for name in ("verified_scope.md", "release_showcase.md"):
        (docs / name).write_text(
            "QFT LR-ACE TC-QSCI finite-cutoff exploratory boundary release audit",
            encoding="utf-8",
        )
    configs = root / "configs" / "exploratory"
    configs.mkdir(parents=True)
    (configs / "h2_4site_lattice_qed_sparse_exact.yaml").write_text(
        "problem:\n  qft:\n    enabled: true\nsolver:\n  kind: lattice_qed_sparse_exact\n",
        encoding="utf-8",
    )
    (configs / "h2_lr_ace.yaml").write_text("solver:\n  kind: lr_ace\n", encoding="utf-8")
    (configs / "h2_tc_qsci.yaml").write_text(
        "exploratory:\n  modules: [tc_qsci]\ntc_qsci:\n  enabled: true\n",
        encoding="utf-8",
    )
    tests = root / "tests" / "unit"
    tests.mkdir(parents=True)
    (tests / "test_release_audit_v23.py").write_text("# release audit fixture target\n", encoding="utf-8")


def _write_artifact(path: Path, *, algorithm: str = "core", trust_tier: str = "exploratory") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "verification_status": trust_tier,
        "module_origin": "exploratory" if trust_tier == "exploratory" else "core",
        "hardware_verified": False,
        "scientific_risk_notes": ["finite-cutoff exploratory boundary"],
        "evidence_summary": {
            "primary_scientific_claim": f"{algorithm} artifact is release-readable within its declared trust boundary.",
            "trust_tier": trust_tier,
            "chemical_accuracy_status": "met" if trust_tier == "validated" else "unavailable",
            "runtime_evidence_status": "none",
            "recommended_action": "collect_stronger_baseline",
            "primary_baseline": {
                "baseline_kind": "exact",
                "baseline_source": "exact_diagonalization",
                "baseline_scope": "single_run",
                "baseline_strength": "strong",
            },
            "primary_error_metric": {"metric_kind": "absolute_error_hartree", "value": 0.0},
        },
    }
    if algorithm == "qft":
        payload["qft_model"] = {"model": "lattice_qed_minimal_coupling", "engine": {"actual_representation": "sparse_projected"}}
    elif algorithm == "tc_qsci":
        payload["tc_qsci_result"] = {"algorithm_name": "TC-kicked QSCI"}
    elif algorithm == "lr_ace":
        payload["variational_result"] = {"ansatz": {"lr_ace": {"algorithm_name": "LR-ACE"}}}
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_hardware_campaign_artifact(
    path: Path,
    *,
    runtime_evidence_status: str = "retrieved_result",
    include_evidence_summary: bool = False,
    hardware_verified_cases: list[str] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    verified_cases = ["h2_runtime_probe"] if hardware_verified_cases is None else hardware_verified_cases
    payload: dict[str, Any] = {
        "suite_name": "hardware_calibration_suite_v1",
        "summary": {
            "total_cases": 1,
            "runtime_evidence_status_counts": {runtime_evidence_status: 1},
            "hardware_verified_cases": verified_cases,
        },
        "cases": [
            {
                "name": "h2_runtime_probe",
                "achieved_error": 0.0137,
                "meets_chemical_accuracy": False,
                "runtime_evidence_status": runtime_evidence_status,
                "runtime_submission_status": "succeeded" if runtime_evidence_status == "retrieved_result" else "submitted",
                "hardware_verified": runtime_evidence_status == "retrieved_result",
            }
        ],
    }
    if include_evidence_summary:
        payload["evidence_summary"] = {
            "result_identity": {"artifact_kind": "hardware_campaign", "artifact_name": "hardware_calibration_suite_v1"},
            "primary_scientific_claim": "Hardware campaign carries retrieved runtime plumbing evidence for release review.",
            "trust_tier": "hardware_verified",
            "chemical_accuracy_status": "not_met",
            "runtime_evidence_status": runtime_evidence_status,
            "primary_baseline": {
                "baseline_kind": "hardware_probe_reference",
                "baseline_source": "h2_runtime_probe",
                "baseline_scope": "hardware_campaign",
                "baseline_strength": "medium",
            },
            "primary_error_metric": {
                "metric_kind": "achieved_error_hartree",
                "value": 0.0137,
                "units": "Hartree",
            },
            "recommended_action": "worth_one_more_controlled_attempt",
            "execution_evidence": {"hardware_verified_cases": verified_cases},
        }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_config(
    root: Path,
    *,
    artifact: Path,
    algorithm: str = "qft",
    artifact_required: bool = True,
    include_exploratory_artifact: bool = True,
    warning_policy: str = "",
) -> Path:
    required_value = str(artifact_required).lower()
    exploratory_artifact = f"\n      artifact: {artifact.relative_to(root)}" if include_exploratory_artifact else ""
    config = root / "release_audit.yaml"
    config.write_text(
        f"""
release_audit:
  profile: trust_first
  release_version: 0.1.0a1
{warning_policy}
  curated_artifacts:
    - name: core_anchor
      path: {artifact.relative_to(root)}
      required: {required_value}
  exploratory_assets:
    - name: {algorithm}_asset
      kind: {algorithm}
      config: configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml
{exploratory_artifact}
      required: {required_value}
  required_docs:
    - path: README.md
      terms: [QFT, LR-ACE, TC-QSCI, finite-cutoff, exploratory boundary, release audit]
    - path: docs/verified_scope.md
      terms: [QFT, LR-ACE, TC-QSCI, finite-cutoff, exploratory boundary, release audit]
    - path: docs/release_showcase.md
      terms: [QFT, LR-ACE, TC-QSCI, finite-cutoff, exploratory boundary, release audit]
  acceptance_commands:
    - python -m pytest tests/unit/test_release_audit_v23.py -q
""",
        encoding="utf-8",
    )
    return config


def _write_acceptance_sidecar(
    artifact: Path,
    *,
    accepted: Any = True,
    blocking_failures: list[Any] | None = None,
    warnings: list[Any] | None = None,
    trust_tier: str = "exploratory",
    runtime_evidence_status: str = "none",
    recommended_action: str = "accept_release_artifact",
    artifact_path: str = "artifacts/qft/result.json",
    release_audit_check_id: str = "curated_artifact:core_anchor:acceptance_summary",
    artifact_sha256: str | None = None,
) -> None:
    artifact_digest = artifact_sha256 or hashlib.sha256(artifact.read_bytes()).hexdigest()
    (artifact.parent / "acceptance_summary.json").write_text(
        json.dumps(
            {
                "schema_version": "qcchem.release_artifact_acceptance.v0.1-alpha",
                "artifact_path": artifact_path,
                "artifact_sha256": artifact_digest,
                "release_audit_check_id": release_audit_check_id,
                "trust_tier": trust_tier,
                "runtime_evidence_status": runtime_evidence_status,
                "accepted": accepted,
                "blocking_failures": blocking_failures or [],
                "warnings": warnings or [],
                "recommended_action": recommended_action,
            }
        ),
        encoding="utf-8",
    )


def test_release_audit_config_parses_defaults_and_paths(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    config = _write_config(tmp_path, artifact=artifact)

    spec = load_release_audit_spec(config)

    assert spec.profile == "trust_first"
    assert spec.release_version == "0.1.0a1"
    assert spec.curated_artifacts[0].name == "core_anchor"
    assert spec.exploratory_assets[0].kind == "qft"
    assert spec.required_docs[0].terms[-1] == "release audit"
    assert spec.source_path == config


def test_release_audit_config_parses_warning_policy(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    config = _write_config(
        tmp_path,
        artifact=artifact,
        warning_policy=(
            "  warning_policy:\n"
            "    max_count: 1\n"
            "    allowed_ids:\n"
            "      - curated_artifact:core_anchor:acceptance_summary\n"
        ),
    )

    spec = load_release_audit_spec(config)

    assert spec.warning_policy is not None
    assert spec.warning_policy.max_count == 1
    assert spec.warning_policy.allowed_ids == ["curated_artifact:core_anchor:acceptance_summary"]


@pytest.mark.parametrize(
    ("body", "field_path"),
    [
        (
            """
  curated_artifacts:
    - name: core_anchor
      path: artifacts/qft/result.json
      required: "false"
""",
            "release_audit.curated_artifacts.required",
        ),
        (
            """
  curated_artifacts:
    - name: core_anchor
      path: artifacts/qft/result.json
      acceptance_required: "true"
""",
            "release_audit.curated_artifacts.acceptance_required",
        ),
        (
            """
  exploratory_assets:
    - name: qft_asset
      kind: qft
      config: configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml
      required: "false"
""",
            "release_audit.exploratory_assets.required",
        ),
        (
            """
  required_docs:
    - path: README.md
      required: "false"
""",
            "release_audit.required_docs.required",
        ),
    ],
)
def test_release_audit_config_rejects_string_booleans(tmp_path: Path, body: str, field_path: str) -> None:
    config = tmp_path / "bad_boolean_release_audit.yaml"
    config.write_text(
        f"""
release_audit:
  profile: trust_first
  release_version: 0.1.0a1
{body}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=f"{field_path} must be a boolean"):
        load_release_audit_spec(config)


@pytest.mark.parametrize(
    ("body", "field_path"),
    [
        (
            """
  required_docs:
    - path: README.md
      terms: [release audit, 123]
""",
            "release_audit.required_docs.terms",
        ),
        (
            """
  warning_policy:
    max_count: 1
    allowed_ids:
      - curated_artifact:core_anchor:acceptance_summary
      - 42
""",
            "release_audit.warning_policy.allowed_ids",
        ),
        (
            """
  acceptance_commands:
    - python -m pytest tests/unit/test_release_audit_v23.py -q
    - 42
""",
            "release_audit.acceptance_commands",
        ),
        (
            """
  acceptance_commands:
    - ""
""",
            "release_audit.acceptance_commands",
        ),
    ],
)
def test_release_audit_config_rejects_non_string_list_items(tmp_path: Path, body: str, field_path: str) -> None:
    config = tmp_path / "bad_list_items_release_audit.yaml"
    config.write_text(
        f"""
release_audit:
  profile: trust_first
  release_version: 0.1.0a1
{body}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=field_path):
        load_release_audit_spec(config)


@pytest.mark.parametrize(
    ("body", "field_path"),
    [
        (
            """
  profile: 42
""",
            "release_audit.profile",
        ),
        (
            """
  curated_artifacts:
    - name: 42
      path: artifacts/qft/result.json
""",
            "release_audit.curated_artifacts.name",
        ),
        (
            """
  curated_artifacts:
    - name: core_anchor
      path: 42
""",
            "release_audit.curated_artifacts.path",
        ),
        (
            """
  exploratory_assets:
    - name: 42
      kind: qft
      config: configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml
""",
            "release_audit.exploratory_assets.name",
        ),
        (
            """
  exploratory_assets:
    - name: qft_asset
      kind: 42
      config: configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml
""",
            "release_audit.exploratory_assets.kind",
        ),
        (
            """
  exploratory_assets:
    - name: qft_asset
      kind: qft
      config: 42
""",
            "release_audit.exploratory_assets.config",
        ),
        (
            """
  exploratory_assets:
    - name: qft_asset
      kind: qft
      config: configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml
      artifact: 42
""",
            "release_audit.exploratory_assets.artifact",
        ),
        (
            """
  exploratory_assets:
    - name: qft_asset
      kind: qft
      config: configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml
      artifact: ""
""",
            "release_audit.exploratory_assets.artifact",
        ),
        (
            """
  required_docs:
    - path: 42
      terms: [release audit]
""",
            "release_audit.required_docs.path",
        ),
        (
            """
  release_version: 42
""",
            "release_audit.release_version",
        ),
    ],
)
def test_release_audit_config_rejects_non_string_scalar_fields(
    tmp_path: Path,
    body: str,
    field_path: str,
) -> None:
    config = tmp_path / "bad_scalar_release_audit.yaml"
    config.write_text(
        f"""
release_audit:
  profile: trust_first
  release_version: 0.1.0a1
{body}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=field_path):
        load_release_audit_spec(config)


@pytest.mark.parametrize(
    ("body", "field_path"),
    [
        (
            """
  curated_artifacts:
    - name: core_anchor
      path: /tmp/qcchem-outside/result.json
""",
            "release_audit.curated_artifacts.path",
        ),
        (
            """
  curated_artifacts:
    - name: core_anchor
      path: ../outside/result.json
""",
            "release_audit.curated_artifacts.path",
        ),
        (
            """
  exploratory_assets:
    - name: qft_asset
      kind: qft
      config: /tmp/qcchem-outside/config.yaml
""",
            "release_audit.exploratory_assets.config",
        ),
        (
            """
  exploratory_assets:
    - name: qft_asset
      kind: qft
      config: configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml
      artifact: ../outside/result.json
""",
            "release_audit.exploratory_assets.artifact",
        ),
        (
            """
  required_docs:
    - path: ~/qcchem-release-notes.md
      terms: [release audit]
""",
            "release_audit.required_docs.path",
        ),
    ],
)
def test_release_audit_config_rejects_non_repo_relative_path_fields(
    tmp_path: Path,
    body: str,
    field_path: str,
) -> None:
    config = tmp_path / "bad_path_release_audit.yaml"
    config.write_text(
        f"""
release_audit:
  profile: trust_first
  release_version: 0.1.0a1
{body}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=field_path):
        load_release_audit_spec(config)


@pytest.mark.parametrize(
    ("body", "field_path"),
    [
        (
            """
  curated_artifacts:
    - name: duplicate_anchor
      path: artifacts/qft/result.json
    - name: duplicate_anchor
      path: artifacts/other/result.json
""",
            "release_audit.curated_artifacts.name",
        ),
        (
            """
  exploratory_assets:
    - name: duplicate_asset
      kind: qft
      config: configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml
    - name: duplicate_asset
      kind: lr_ace
      config: configs/exploratory/h2_lr_ace.yaml
""",
            "release_audit.exploratory_assets.name",
        ),
        (
            """
  required_docs:
    - path: README.md
      terms: [release audit]
    - path: README.md
      terms: [QFT]
""",
            "release_audit.required_docs.path",
        ),
    ],
)
def test_release_audit_config_rejects_duplicate_check_id_sources(
    tmp_path: Path,
    body: str,
    field_path: str,
) -> None:
    config = tmp_path / "duplicate_release_audit.yaml"
    config.write_text(
        f"""
release_audit:
  profile: trust_first
  release_version: 0.1.0a1
{body}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=field_path):
        load_release_audit_spec(config)


@pytest.mark.parametrize(
    ("body", "field_path"),
    [
        (
            """
  warning_policy:
    max_count: 1
    allowed_ids:
      - curated_artifact:core_anchor:acceptance_summary
      - " curated_artifact:core_anchor:acceptance_summary "
""",
            "release_audit.warning_policy.allowed_ids",
        ),
        (
            """
  acceptance_commands:
    - python -m pytest tests/unit/test_release_audit_v23.py -q
    - " python -m pytest tests/unit/test_release_audit_v23.py -q "
""",
            "release_audit.acceptance_commands",
        ),
    ],
)
def test_release_audit_config_rejects_duplicate_policy_and_acceptance_lists(
    tmp_path: Path,
    body: str,
    field_path: str,
) -> None:
    config = tmp_path / "duplicate_policy_release_audit.yaml"
    config.write_text(
        f"""
release_audit:
  profile: trust_first
  release_version: 0.1.0a1
{body}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=field_path):
        load_release_audit_spec(config)


def test_release_audit_config_rejects_invalid_profile_and_version(tmp_path: Path) -> None:
    config = tmp_path / "bad_release_audit.yaml"
    config.write_text(
        """
release_audit:
  profile: anything_goes
  release_version: 1.0.0
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="release_audit.profile"):
        load_release_audit_spec(config)

    config.write_text(
        """
release_audit:
  profile: trust_first
  release_version: 1.0.0
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="release_audit.release_version"):
        load_release_audit_spec(config)


def test_release_audit_fails_missing_evidence_fields(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "bad" / "result.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        json.dumps({"verification_status": "exploratory", "evidence_summary": {"trust_tier": "exploratory"}}),
        encoding="utf-8",
    )
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    assert summary["status"] == "failed"
    failed_ids = {check["id"] for check in summary["checks"] if check["status"] == "failed"}
    assert "curated_artifact:core_anchor:evidence_summary" in failed_ids
    evidence_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:evidence_summary")
    assert evidence_check["details"]["missing_fields"] == [
        "primary_scientific_claim",
        "primary_baseline",
        "primary_error_metric",
        "chemical_accuracy_status",
        "runtime_evidence_status",
        "recommended_action",
    ]
    assert summary["required_fail_count"] > 0
    assert (tmp_path / "out" / "release_readiness.json").exists()
    assert (tmp_path / "out" / "release_readiness.md").exists()


@pytest.mark.parametrize(
    ("command", "reason"),
    [
        ("python -m pytest tests/unit/missing_release_gate.py -q", "missing_pytest_targets"),
        ("qcchem benchmark run -c benchmarks/missing_suite.yaml -o artifacts/missing_suite", "missing_benchmark_configs"),
        (
            "qcchem benchmark run -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml",
            "missing_benchmark_output_option",
        ),
        (
            "qcchem benchmark run -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml "
            "--config=configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml "
            "-o artifacts/qft_benchmark",
            "multiple_benchmark_config_options",
        ),
        (
            "qcchem benchmark run --config= -o artifacts/qft_benchmark",
            "empty_benchmark_configs",
        ),
        (
            "qcchem benchmark run -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml "
            "-o artifacts/qft_benchmark --output-dir=artifacts/qft_benchmark_alt",
            "multiple_benchmark_output_options",
        ),
        (
            "qcchem benchmark run -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml -o /tmp/out",
            "absolute_benchmark_outputs",
        ),
        (
            "qcchem benchmark run -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml -o ~/out",
            "home_directory_benchmark_outputs",
        ),
        (
            "qcchem benchmark run -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml -o ../out",
            "outside_repo_benchmark_outputs",
        ),
        (
            "qcchem benchmark run -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml -o artifacts/../artifacts/out",
            "parent_directory_benchmark_outputs",
        ),
        (
            "qcchem benchmark run -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml -o scratch/out",
            "non_artifacts_benchmark_outputs",
        ),
        (
            "qcchem benchmark run -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml -o artifacts",
            "non_artifacts_benchmark_outputs",
        ),
        (
            "qcchem benchmark run -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml --output-dir=",
            "empty_benchmark_outputs",
        ),
        (
            "qcchem benchmark run -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml --output=artifacts/qft_benchmark",
            "unsupported_benchmark_output_options",
        ),
        ("python -m pytest tests/../tests/unit/test_release_audit_v23.py -q", "parent_directory_pytest_targets"),
        ("python -m pytest tests/../tests -q", "parent_directory_pytest_targets"),
        (
            "qcchem benchmark run -c configs/../configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml",
            "parent_directory_benchmark_configs",
        ),
        ("python -m pytest ~/release_gate.py -q", "home_directory_pytest_targets"),
        ("qcchem benchmark run -c ~/release_suite.yaml", "home_directory_benchmark_configs"),
        ("python -m pytest tests/unit/test_release_audit_v23.py -q && echo done", "shell_control_tokens"),
        ("python -m pytest tests/unit/test_release_audit_v23.py -q; echo done", "shell_control_tokens"),
        ("python -m pytest tests/unit/test_release_audit_v23.py -q | tee out.log", "shell_control_tokens"),
        (
            "qcchem benchmark run -c benchmarks/lr_ace_flagship_suite_v1.yaml -o artifacts/lr && echo done",
            "shell_control_tokens",
        ),
        ("python -m pytest $(echo tests/unit/test_release_audit_v23.py) -q", "shell_expansion_tokens"),
        ("python -m pytest `echo tests/unit/test_release_audit_v23.py` -q", "shell_expansion_tokens"),
        ("python -m pytest ${RELEASE_TEST_TARGET} -q", "shell_expansion_tokens"),
        ('python -m pytest tests/unit/test_release_audit_v23.py -k "$MARKER" -q', "shell_expansion_tokens"),
        ("python -m pytest tests/unit/test_release_audit_*.py -q", "shell_expansion_tokens"),
        ("qcchem benchmark run -c ${BENCHMARK_CONFIG} -o artifacts/out", "shell_expansion_tokens"),
        ("qcchem benchmark run -c benchmarks/*.yaml -o artifacts/out", "shell_expansion_tokens"),
        ("python -m pytest tests/unit/test_release_audit_v23.py --basetemp=/tmp/qcchem -q", "unsafe_pytest_option_paths"),
        ("python -m pytest tests/unit/test_release_audit_v23.py --basetemp /tmp/qcchem -q", "unsafe_pytest_option_paths"),
        ("python -m pytest tests/unit/test_release_audit_v23.py --basetemp= -q", "unsafe_pytest_option_paths"),
        ("python -m pytest tests/unit/test_release_audit_v23.py --basetemp -q", "unsafe_pytest_option_paths"),
        ("python -m pytest --basetemp tests -q", "missing_pytest_targets"),
        ("python -m pytest --junitxml tests/unit/test_release_audit_v23.py -q", "missing_pytest_targets"),
        ("python -m pytest -m tests -q", "missing_pytest_targets"),
        ('python -m pytest "tests/unit/test_release_audit_v23.py -q', "parse_error"),
        ("/usr/bin/python3 -m pytest tests/unit/test_release_audit_v23.py -q", "nonportable_python_executable"),
        (".venv/bin/python -m pytest tests/unit/test_release_audit_v23.py -q", "nonportable_python_executable"),
        ("python -m pytest -q", "missing_pytest_targets"),
        ("python3 -m pytest -q", "missing_pytest_targets"),
        ("pytest -q", "missing_pytest_targets"),
        ("echo release-ready", "unsupported_command"),
    ],
)
def test_release_audit_validates_acceptance_command_targets(
    tmp_path: Path,
    command: str,
    reason: str,
) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    config = _write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False)
    payload = config.read_text(encoding="utf-8")
    payload = payload.replace(
        "    - python -m pytest tests/unit/test_release_audit_v23.py -q",
        f"    - {command}",
    )
    config.write_text(payload, encoding="utf-8")
    spec = load_release_audit_spec(config)

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    command_check = next(check for check in summary["checks"] if check["id"] == "release_acceptance_commands:static_targets")
    failure = command_check["details"]["failures"][0]
    assert summary["status"] == "failed"
    assert command_check["required"] is True
    assert command_check["status"] == "failed"
    assert failure["reason"] == reason
    assert failure["remediation"]
    assert not failure["remediation"].startswith("Inspect this acceptance command")
    assert (tmp_path / "out" / "release_readiness.json").exists()
    assert (tmp_path / "out" / "release_readiness.md").exists()
    report = (tmp_path / "out" / "release_readiness.md").read_text(encoding="utf-8")
    assert "## Acceptance Command Repairs" in report
    assert command in report
    assert f"  - reason: `{reason}`" in report
    assert f"  - remediation: {failure['remediation']}" in report


def test_release_audit_accepts_pytest_directory_acceptance_target(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    config = _write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False)
    payload = config.read_text(encoding="utf-8")
    payload = payload.replace(
        "    - python -m pytest tests/unit/test_release_audit_v23.py -q",
        "    - python -m pytest tests -q",
    )
    config.write_text(payload, encoding="utf-8")
    spec = load_release_audit_spec(config)

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    command_check = next(check for check in summary["checks"] if check["id"] == "release_acceptance_commands:static_targets")
    assert summary["status"] == "passed"
    assert command_check["status"] == "passed"
    assert command_check["details"]["failures"] == []


def test_release_audit_accepts_python3_pytest_acceptance_command(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    config = _write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False)
    payload = config.read_text(encoding="utf-8")
    payload = payload.replace(
        "    - python -m pytest tests/unit/test_release_audit_v23.py -q",
        "    - python3 -m pytest tests/unit/test_release_audit_v23.py -q",
    )
    config.write_text(payload, encoding="utf-8")
    spec = load_release_audit_spec(config)

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    command_check = next(check for check in summary["checks"] if check["id"] == "release_acceptance_commands:static_targets")
    assert summary["status"] == "passed"
    assert command_check["status"] == "passed"
    assert command_check["details"]["failures"] == []


def test_release_audit_accepts_pytest_marker_with_explicit_target(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    config = _write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False)
    payload = config.read_text(encoding="utf-8")
    payload = payload.replace(
        "    - python -m pytest tests/unit/test_release_audit_v23.py -q",
        "    - python -m pytest -m slow tests/unit/test_release_audit_v23.py -q",
    )
    config.write_text(payload, encoding="utf-8")
    spec = load_release_audit_spec(config)

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    command_check = next(check for check in summary["checks"] if check["id"] == "release_acceptance_commands:static_targets")
    assert summary["status"] == "passed"
    assert command_check["status"] == "passed"
    assert command_check["details"]["failures"] == []


def test_release_audit_accepts_pytest_flag_before_explicit_target(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    config = _write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False)
    payload = config.read_text(encoding="utf-8")
    payload = payload.replace(
        "    - python -m pytest tests/unit/test_release_audit_v23.py -q",
        "    - python -m pytest --cache-clear tests/unit/test_release_audit_v23.py -q",
    )
    config.write_text(payload, encoding="utf-8")
    spec = load_release_audit_spec(config)

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    command_check = next(check for check in summary["checks"] if check["id"] == "release_acceptance_commands:static_targets")
    assert summary["status"] == "passed"
    assert command_check["status"] == "passed"
    assert command_check["details"]["failures"] == []


def test_release_audit_accepts_quoted_pytest_expression_with_control_characters(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    config = _write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False)
    payload = config.read_text(encoding="utf-8")
    payload = payload.replace(
        "    - python -m pytest tests/unit/test_release_audit_v23.py -q",
        '    - python -m pytest tests/unit/test_release_audit_v23.py -k "alpha|beta" -q',
    )
    config.write_text(payload, encoding="utf-8")
    spec = load_release_audit_spec(config)

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    command_check = next(check for check in summary["checks"] if check["id"] == "release_acceptance_commands:static_targets")
    assert summary["status"] == "passed"
    assert command_check["status"] == "passed"
    assert command_check["details"]["failures"] == []


def test_release_audit_accepts_non_path_pytest_options_with_equals(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    config = _write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False)
    payload = config.read_text(encoding="utf-8")
    payload = payload.replace(
        "    - python -m pytest tests/unit/test_release_audit_v23.py -q",
        "    - python -m pytest tests/unit/test_release_audit_v23.py --maxfail=1 --tb=short -q",
    )
    config.write_text(payload, encoding="utf-8")
    spec = load_release_audit_spec(config)

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    command_check = next(check for check in summary["checks"] if check["id"] == "release_acceptance_commands:static_targets")
    assert summary["status"] == "passed"
    assert command_check["status"] == "passed"
    assert command_check["details"]["failures"] == []


def test_release_audit_accepts_pytest_warning_filter_with_explicit_target(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    config = _write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False)
    payload = config.read_text(encoding="utf-8")
    payload = payload.replace(
        "    - python -m pytest tests/unit/test_release_audit_v23.py -q",
        "    - python -m pytest tests -q -W error::scipy.sparse._base.SparseEfficiencyWarning",
    )
    config.write_text(payload, encoding="utf-8")
    spec = load_release_audit_spec(config)

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    command_check = next(check for check in summary["checks"] if check["id"] == "release_acceptance_commands:static_targets")
    assert summary["status"] == "passed"
    assert command_check["status"] == "passed"
    assert command_check["details"]["failures"] == []


def test_release_audit_accepts_benchmark_acceptance_output_under_artifacts(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    config = _write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False)
    payload = config.read_text(encoding="utf-8")
    payload = payload.replace(
        "    - python -m pytest tests/unit/test_release_audit_v23.py -q",
        "    - qcchem benchmark run -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml --output-dir=artifacts/qft_benchmark",
    )
    config.write_text(payload, encoding="utf-8")
    spec = load_release_audit_spec(config)

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    command_check = next(check for check in summary["checks"] if check["id"] == "release_acceptance_commands:static_targets")
    assert summary["status"] == "passed"
    assert command_check["status"] == "passed"
    assert command_check["details"]["failures"] == []


def test_release_audit_accepts_benchmark_acceptance_preview_output_under_curated_artifact(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    config = _write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False)
    payload = config.read_text(encoding="utf-8")
    payload = payload.replace(
        "    - python -m pytest tests/unit/test_release_audit_v23.py -q",
        (
            "    - qcchem benchmark run "
            "-c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml "
            "-o artifacts/qft/preview_local --overwrite"
        ),
    )
    config.write_text(payload, encoding="utf-8")
    spec = load_release_audit_spec(config)

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    command_check = next(check for check in summary["checks"] if check["id"] == "release_acceptance_commands:static_targets")
    assert summary["status"] == "passed"
    assert command_check["status"] == "passed"
    assert command_check["details"]["failures"] == []


def test_release_audit_rejects_benchmark_acceptance_output_on_curated_artifact_root(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    config = _write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False)
    payload = config.read_text(encoding="utf-8")
    payload = payload.replace(
        "    - python -m pytest tests/unit/test_release_audit_v23.py -q",
        (
            "    - qcchem benchmark run "
            "-c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml "
            "-o artifacts/qft"
        ),
    )
    config.write_text(payload, encoding="utf-8")
    spec = load_release_audit_spec(config)

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    command_check = next(check for check in summary["checks"] if check["id"] == "release_acceptance_commands:static_targets")
    failure = command_check["details"]["failures"][0]
    assert summary["status"] == "failed"
    assert command_check["status"] == "failed"
    assert failure["reason"] == "protected_release_artifact_outputs"
    assert failure["protected_outputs"][0]["protected_root"] == "artifacts/qft"
    assert failure["protected_outputs"][0]["allowed_preview_root"] == "artifacts/qft/preview_local"


def test_release_audit_rejects_benchmark_acceptance_output_on_exploratory_artifact_root(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    curated_artifact = tmp_path / "artifacts" / "core" / "result.json"
    exploratory_artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(curated_artifact, algorithm="core", trust_tier="validated")
    _write_artifact(exploratory_artifact, algorithm="qft", trust_tier="exploratory")
    _write_acceptance_sidecar(
        curated_artifact,
        trust_tier="validated",
        artifact_path="artifacts/core/result.json",
    )
    _write_acceptance_sidecar(
        exploratory_artifact,
        artifact_path="artifacts/qft/result.json",
        release_audit_check_id="exploratory_asset:qft_asset:acceptance_summary",
    )
    config = tmp_path / "release_audit.yaml"
    config.write_text(
        """
release_audit:
  profile: trust_first
  release_version: 0.1.0a1
  curated_artifacts:
    - name: core_anchor
      path: artifacts/core/result.json
      required: true
  exploratory_assets:
    - name: qft_asset
      kind: qft
      config: configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml
      artifact: artifacts/qft/result.json
      required: true
  required_docs:
    - path: README.md
      terms: [QFT, LR-ACE, TC-QSCI, finite-cutoff, exploratory boundary, release audit]
    - path: docs/verified_scope.md
      terms: [QFT, LR-ACE, TC-QSCI, finite-cutoff, exploratory boundary, release audit]
    - path: docs/release_showcase.md
      terms: [QFT, LR-ACE, TC-QSCI, finite-cutoff, exploratory boundary, release audit]
  acceptance_commands:
    - qcchem benchmark run -c configs/exploratory/h2_4site_lattice_qed_sparse_exact.yaml -o artifacts/qft
""",
        encoding="utf-8",
    )
    spec = load_release_audit_spec(config)

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    command_check = next(check for check in summary["checks"] if check["id"] == "release_acceptance_commands:static_targets")
    failure = command_check["details"]["failures"][0]
    assert summary["status"] == "failed"
    assert command_check["status"] == "failed"
    assert failure["reason"] == "protected_release_artifact_outputs"
    assert failure["protected_outputs"][0]["protected_root"] == "artifacts/qft"
    assert failure["protected_outputs"][0]["allowed_preview_root"] == "artifacts/qft/preview_local"


def test_release_audit_rejects_benchmark_acceptance_config_directory(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    (tmp_path / "benchmarks").mkdir()
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    config = _write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False)
    payload = config.read_text(encoding="utf-8")
    payload = payload.replace(
        "    - python -m pytest tests/unit/test_release_audit_v23.py -q",
        "    - qcchem benchmark run -c benchmarks -o artifacts/out",
    )
    config.write_text(payload, encoding="utf-8")
    spec = load_release_audit_spec(config)

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    command_check = next(check for check in summary["checks"] if check["id"] == "release_acceptance_commands:static_targets")
    failure = command_check["details"]["failures"][0]
    assert summary["status"] == "failed"
    assert command_check["status"] == "failed"
    assert failure["reason"] == "non_file_benchmark_configs"
    assert failure["non_file_configs"][0]["reason"] == "not_file"


@pytest.mark.parametrize(
    ("command", "reason", "details_key"),
    [
        (
            "python -m pytest ../outside_release_gate.py -q",
            "outside_repo_pytest_targets",
            "outside_targets",
        ),
        (
            "qcchem benchmark run -c ../outside_suite.yaml -o artifacts/outside_suite",
            "outside_repo_benchmark_configs",
            "outside_configs",
        ),
    ],
)
def test_release_audit_rejects_acceptance_commands_outside_repo(
    tmp_path: Path,
    command: str,
    reason: str,
    details_key: str,
) -> None:
    _write_release_fixture(tmp_path)
    outside_file = tmp_path.parent / (
        "outside_release_gate.py" if "pytest" in command else "outside_suite.yaml"
    )
    outside_file.write_text("# outside release target\n", encoding="utf-8")
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    config = _write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False)
    payload = config.read_text(encoding="utf-8")
    payload = payload.replace(
        "    - python -m pytest tests/unit/test_release_audit_v23.py -q",
        f"    - {command}",
    )
    config.write_text(payload, encoding="utf-8")
    spec = load_release_audit_spec(config)

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    command_check = next(check for check in summary["checks"] if check["id"] == "release_acceptance_commands:static_targets")
    failure = command_check["details"]["failures"][0]
    assert summary["status"] == "failed"
    assert command_check["status"] == "failed"
    assert failure["reason"] == reason
    assert failure[details_key][0]["reason"] == "outside_repo"
    assert str(tmp_path) not in failure[details_key][0]["resolved"]


@pytest.mark.parametrize(
    ("command_template", "reason", "details_key", "target_relative_path"),
    [
        (
            "python -m pytest {target} -q",
            "absolute_pytest_targets",
            "absolute_targets",
            Path("tests") / "unit" / "test_release_audit_v23.py",
        ),
        (
            "qcchem benchmark run -c {target} -o artifacts/absolute_suite",
            "absolute_benchmark_configs",
            "absolute_configs",
            Path("benchmarks") / "absolute_suite.yaml",
        ),
    ],
)
def test_release_audit_rejects_absolute_acceptance_command_targets(
    tmp_path: Path,
    command_template: str,
    reason: str,
    details_key: str,
    target_relative_path: Path,
) -> None:
    _write_release_fixture(tmp_path)
    target = tmp_path / target_relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# absolute release target\n", encoding="utf-8")
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    config = _write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False)
    payload = config.read_text(encoding="utf-8")
    payload = payload.replace(
        "    - python -m pytest tests/unit/test_release_audit_v23.py -q",
        f"    - {command_template.format(target=target)}",
    )
    config.write_text(payload, encoding="utf-8")
    spec = load_release_audit_spec(config)

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    command_check = next(check for check in summary["checks"] if check["id"] == "release_acceptance_commands:static_targets")
    failure = command_check["details"]["failures"][0]
    assert summary["status"] == "failed"
    assert command_check["status"] == "failed"
    assert failure["reason"] == reason
    assert failure[details_key][0]["reason"] == "absolute_path"
    assert failure[details_key][0]["resolved"] == str(target.resolve())


@pytest.mark.parametrize(
    ("artifact_text", "error_fragment"),
    [
        ("{not-json", "JSONDecodeError"),
        ("[]", "must contain a JSON object"),
    ],
)
def test_release_audit_fails_unreadable_artifact_without_crashing(
    tmp_path: Path,
    artifact_text: str,
    error_fragment: str,
) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "bad" / "result.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(artifact_text, encoding="utf-8")
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    readable_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:readable")
    assert summary["status"] == "failed"
    assert readable_check["required"] is True
    assert readable_check["status"] == "failed"
    assert readable_check["details"]["path"].endswith("result.json")
    assert error_fragment in readable_check["details"]["error"]
    assert (tmp_path / "out" / "release_readiness.json").exists()
    assert (tmp_path / "out" / "release_readiness.md").exists()
    report = (tmp_path / "out" / "release_readiness.md").read_text(encoding="utf-8")
    assert "curated_artifact:core_anchor:readable" in report


def test_release_audit_reports_unreadable_exploratory_config_without_crashing(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    config_path = tmp_path / "configs" / "exploratory" / "h2_4site_lattice_qed_sparse_exact.yaml"
    config_path.write_text("problem: [not-closed", encoding="utf-8")
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    config_check = next(check for check in summary["checks"] if check["id"] == "exploratory_asset:qft_asset:config")
    assert summary["status"] == "failed"
    assert config_check["required"] is True
    assert config_check["status"] == "failed"
    assert config_check["summary"] == "classified=unreadable, expected=qft"
    assert config_check["details"]["config"].endswith("h2_4site_lattice_qed_sparse_exact.yaml")
    assert config_check["details"]["error"]
    assert "Error" in config_check["details"]["error"]
    assert (tmp_path / "out" / "release_readiness.json").exists()
    assert (tmp_path / "out" / "release_readiness.md").exists()
    report = (tmp_path / "out" / "release_readiness.md").read_text(encoding="utf-8")
    assert "exploratory_asset:qft_asset:config" in report


def test_release_audit_warning_policy_fails_unlisted_warnings(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    spec = load_release_audit_spec(
        _write_config(
            tmp_path,
            artifact=artifact,
            artifact_required=False,
            warning_policy=(
                "  warning_policy:\n"
                "    max_count: 0\n"
                "    allowed_ids: []\n"
            ),
        )
    )

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    policy_check = next(check for check in summary["checks"] if check["id"] == "release_warning_policy")
    assert summary["status"] == "failed"
    assert summary["warning_count"] > 0
    assert policy_check["status"] == "failed"
    assert "curated_artifact:core_anchor:acceptance_summary" in policy_check["details"]["unexpected_ids"]
    report = (tmp_path / "out" / "release_readiness.md").read_text(encoding="utf-8")
    assert "- warning_policy_allowed_ids: `[]`" in report
    assert "- warning_policy_unexpected_count: `2`" in report
    assert "curated_artifact:core_anchor:acceptance_summary" in report
    assert "exploratory_asset:qft_asset:acceptance_summary" in report


def test_release_audit_requires_acceptance_summary_for_required_artifact(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    acceptance_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:acceptance_summary")
    assert summary["status"] == "failed"
    assert acceptance_check["required"] is True
    assert acceptance_check["status"] == "failed"


def test_release_audit_matrix_reads_sidecar_acceptance_status(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    spec = load_release_audit_spec(
        _write_config(
            tmp_path,
            artifact=artifact,
            include_exploratory_artifact=False,
            warning_policy=(
                "  warning_policy:\n"
                "    max_count: 0\n"
                "    allowed_ids: []\n"
            ),
        )
    )

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    assert summary["status"] == "passed"
    assert summary["schema_version"] == "1.1"
    assert {
        "failed_checks",
        "required_failed_checks",
        "warning_checks",
        "evidence_matrix_core_fields",
        "evidence_matrix_review_warnings",
        "warning_policy",
        "acceptance_commands",
        "acceptance_command_remediation",
        "acceptance_summary_source",
        "acceptance_schema_version",
        "acceptance_artifact_path",
        "acceptance_artifact_sha256",
        "acceptance_release_audit_check_id",
        "acceptance_trust_tier",
        "acceptance_runtime_evidence_status",
        "acceptance_status",
        "acceptance_recommended_action",
        "acceptance_blocking_failure_count",
        "acceptance_warning_count",
        "acceptance_contract_failure_count",
        "audit_provenance",
    }.issubset(set(summary["schema_features"]))
    assert summary["audit_provenance"]["generated_at_utc"].endswith("Z")
    assert summary["audit_provenance"]["repo_root"] == str(tmp_path.resolve())
    assert summary["audit_provenance"]["manifest_path"] == "release_audit.yaml"
    assert summary["audit_provenance"]["output_dir"] == "out"
    assert summary["acceptance_commands"] == ["python -m pytest tests/unit/test_release_audit_v23.py -q"]
    assert summary["warning_count"] == 0
    assert summary["required_failed_checks"] == []
    assert summary["warning_checks"] == []
    assert summary["evidence_matrix"][0]["primary_scientific_claim"].endswith(
        "release-readable within its declared trust boundary."
    )
    assert summary["evidence_matrix"][0]["primary_baseline"]["baseline_kind"] == "exact"
    assert summary["evidence_matrix"][0]["primary_error_metric"]["metric_kind"] == "absolute_error_hartree"
    assert summary["evidence_matrix"][0]["chemical_accuracy_status"] == "unavailable"
    assert summary["evidence_matrix"][0]["review_warning_count"] == 0
    assert summary["evidence_matrix"][0]["review_warnings"] == []
    assert summary["evidence_matrix"][0]["acceptance_status"] is True
    assert summary["evidence_matrix"][0]["acceptance_trust_tier"] == "exploratory"
    assert summary["evidence_matrix"][0]["acceptance_runtime_evidence_status"] == "none"
    assert summary["evidence_matrix"][0]["acceptance_recommended_action"] == "accept_release_artifact"
    report = (tmp_path / "out" / "release_readiness.md").read_text(encoding="utf-8")
    assert "- schema_version: `1.1`" in report
    assert "- schema_features: `" in report
    assert "acceptance_commands" in report
    assert "- generated_at_utc: `" in report
    assert f"- repo_root: `{tmp_path.resolve()}`" in report
    assert "- manifest_path: `release_audit.yaml`" in report
    assert "- output_dir: `out`" in report
    assert "- primary_scientific_claim: `qft artifact is release-readable within its declared trust boundary.`" in report
    assert '- primary_baseline: `{"baseline_kind": "exact"' in report
    assert '- primary_error_metric: `{"metric_kind": "absolute_error_hartree", "value": 0.0}`' in report
    assert "- chemical_accuracy_status: `unavailable`" in report
    assert "- review_warning_count: `0`" in report
    assert "- review_warnings: `[]`" in report
    assert "- acceptance_status: `True`" in report
    assert "- acceptance_artifact_sha256: `" in report
    assert "- acceptance_trust_tier: `exploratory`" in report
    assert "- acceptance_runtime_evidence_status: `none`" in report
    assert "- acceptance_recommended_action: `accept_release_artifact`" in report
    assert "- acceptance_blocking_failure_count: `0`" in report
    assert "- acceptance_warning_count: `0`" in report
    assert "- acceptance_contract_failure_count: `0`" in report


def test_release_audit_matrix_surfaces_review_warnings_without_warning_policy_failure(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["evidence_summary"]["primary_scientific_claim"] = "QFT result None requires manual release review."
    payload["evidence_summary"]["primary_baseline"] = {
        "baseline_kind": "none",
        "baseline_source": "unavailable",
        "baseline_scope": "single_run",
        "baseline_strength": "weak",
    }
    payload["evidence_summary"]["primary_error_metric"] = {
        "metric_kind": "absolute_error_hartree",
        "value": None,
    }
    artifact.write_text(json.dumps(payload), encoding="utf-8")
    _write_acceptance_sidecar(artifact)
    spec = load_release_audit_spec(
        _write_config(
            tmp_path,
            artifact=artifact,
            include_exploratory_artifact=False,
            warning_policy=(
                "  warning_policy:\n"
                "    max_count: 0\n"
                "    allowed_ids: []\n"
            ),
        )
    )

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    entry = summary["evidence_matrix"][0]
    assert summary["status"] == "passed"
    assert summary["warning_count"] == 0
    assert summary["warning_checks"] == []
    assert summary["warning_policy"]["status"] == "passed"
    assert entry["review_warning_count"] == 3
    assert [warning["reason"] for warning in entry["review_warnings"]] == [
        "weak_or_missing_baseline",
        "missing_error_metric_value",
        "claim_contains_null_placeholder",
    ]
    report = (tmp_path / "out" / "release_readiness.md").read_text(encoding="utf-8")
    assert "- review_warning_count: `3`" in report
    assert "weak_or_missing_baseline" in report
    assert "missing_error_metric_value" in report
    assert "claim_contains_null_placeholder" in report


def test_release_audit_fails_rejected_sidecar_for_required_artifact(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(
        artifact,
        accepted=False,
        blocking_failures=[{"check": "probe", "reason": "rejected"}],
        recommended_action="repair_release_artifact",
    )
    spec = load_release_audit_spec(
        _write_config(
            tmp_path,
            artifact=artifact,
            include_exploratory_artifact=False,
            warning_policy=(
                "  warning_policy:\n"
                "    max_count: 0\n"
                "    allowed_ids: []\n"
            ),
        )
    )

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    acceptance_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:acceptance_summary")
    assert summary["status"] == "failed"
    assert acceptance_check["required"] is True
    assert acceptance_check["status"] == "failed"
    assert summary["failed_checks"]
    assert summary["required_failed_checks"][0]["id"] == "curated_artifact:core_anchor:acceptance_summary"
    report = (tmp_path / "out" / "release_readiness.md").read_text(encoding="utf-8")
    assert "## Required Failed Checks" in report
    assert "curated_artifact:core_anchor:acceptance_summary" in report
    assert summary["evidence_matrix"][0]["acceptance_status"] is False


def test_release_audit_fails_accepted_sidecar_with_blocking_failures(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(
        artifact,
        blocking_failures=[{"check": "probe", "reason": "still_blocked"}],
        recommended_action="repair_release_artifact",
    )
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    acceptance_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:acceptance_summary")
    assert summary["status"] == "failed"
    assert acceptance_check["status"] == "failed"
    assert acceptance_check["details"]["accepted"] is True
    assert acceptance_check["details"]["blocking_failure_count"] == 1
    assert summary["evidence_matrix"][0]["acceptance_blocking_failure_count"] == 1


def test_release_audit_requires_literal_true_acceptance_status(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact, accepted="true")
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    acceptance_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:acceptance_summary")
    assert summary["status"] == "failed"
    assert acceptance_check["status"] == "failed"
    assert acceptance_check["details"]["accepted"] == "true"
    failed_ids = {check["id"] for check in summary["required_failed_checks"]}
    assert "curated_artifact:core_anchor:acceptance_summary" in failed_ids
    assert summary["required_failed_checks"][0]["details"]


def test_release_audit_warning_policy_fails_sidecar_warnings(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(
        artifact,
        warnings=[{"reason": "manual_review_required"}],
        recommended_action="review_acceptance_warnings",
    )
    spec = load_release_audit_spec(
        _write_config(
            tmp_path,
            artifact=artifact,
            include_exploratory_artifact=False,
            warning_policy=(
                "  warning_policy:\n"
                "    max_count: 0\n"
                "    allowed_ids: []\n"
            ),
        )
    )

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    acceptance_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:acceptance_summary")
    warning_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:acceptance_warnings")
    policy_check = next(check for check in summary["checks"] if check["id"] == "release_warning_policy")
    assert summary["status"] == "failed"
    assert acceptance_check["status"] == "passed"
    assert warning_check["status"] == "warning"
    assert policy_check["status"] == "failed"
    assert "curated_artifact:core_anchor:acceptance_warnings" in policy_check["details"]["unexpected_ids"]
    assert summary["evidence_matrix"][0]["acceptance_warning_count"] == 1
    assert summary["warning_checks"][0]["id"] == "curated_artifact:core_anchor:acceptance_warnings"
    assert summary["warning_checks"][0]["details"]["warnings"] == [{"reason": "manual_review_required"}]
    report = (tmp_path / "out" / "release_readiness.md").read_text(encoding="utf-8")
    assert "## Warning Checks" in report
    assert "curated_artifact:core_anchor:acceptance_warnings" in report


def test_release_audit_fails_sidecar_with_wrong_check_binding(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(
        artifact,
        release_audit_check_id="curated_artifact:other_anchor:acceptance_summary",
    )
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    acceptance_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:acceptance_summary")
    assert summary["status"] == "failed"
    assert acceptance_check["status"] == "failed"
    assert acceptance_check["details"]["contract_failure_count"] == 1
    assert acceptance_check["details"]["contract_failures"][0]["field"] == "release_audit_check_id"
    assert summary["evidence_matrix"][0]["acceptance_contract_failure_count"] == 1


def test_release_audit_fails_sidecar_with_wrong_artifact_binding(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact, artifact_path="artifacts/other/result.json")
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    acceptance_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:acceptance_summary")
    assert summary["status"] == "failed"
    assert acceptance_check["status"] == "failed"
    assert acceptance_check["details"]["contract_failure_count"] == 1
    assert acceptance_check["details"]["contract_failures"][0]["field"] == "artifact_path"
    assert summary["evidence_matrix"][0]["acceptance_contract_failure_count"] == 1


def test_release_audit_fails_sidecar_with_stale_artifact_digest(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact, artifact_sha256="0" * 64)
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    acceptance_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:acceptance_summary")
    assert summary["status"] == "failed"
    assert acceptance_check["status"] == "failed"
    assert acceptance_check["details"]["contract_failure_count"] == 1
    failure = acceptance_check["details"]["contract_failures"][0]
    assert failure["field"] == "artifact_sha256"
    assert failure["actual"] == "0" * 64
    assert len(failure["expected"]) == 64
    assert summary["evidence_matrix"][0]["acceptance_artifact_sha256"] == "0" * 64
    assert summary["evidence_matrix"][0]["acceptance_contract_failure_count"] == 1


@pytest.mark.parametrize(
    ("artifact_path", "reason"),
    [
        (None, "absolute_path"),
        ("artifacts/qft/../qft/result.json", "parent_directory_path"),
    ],
)
def test_release_audit_fails_sidecar_with_non_repo_relative_artifact_binding(
    tmp_path: Path,
    artifact_path: str | None,
    reason: str,
) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(
        artifact,
        artifact_path=str(artifact.resolve()) if artifact_path is None else artifact_path,
    )
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    acceptance_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:acceptance_summary")
    assert summary["status"] == "failed"
    assert acceptance_check["status"] == "failed"
    assert acceptance_check["details"]["contract_failure_count"] == 1
    assert acceptance_check["details"]["contract_failures"][0]["field"] == "artifact_path"
    assert acceptance_check["details"]["contract_failures"][0]["reason"] == reason


def test_release_audit_fails_sidecar_with_wrong_trust_tier_binding(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact, trust_tier="validated")
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    acceptance_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:acceptance_summary")
    assert summary["status"] == "failed"
    assert acceptance_check["status"] == "failed"
    assert acceptance_check["details"]["contract_failure_count"] == 1
    assert acceptance_check["details"]["contract_failures"][0]["field"] == "trust_tier"
    assert summary["evidence_matrix"][0]["acceptance_trust_tier"] == "validated"


def test_release_audit_fails_sidecar_with_wrong_runtime_evidence_binding(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact, runtime_evidence_status="retrieved_result")
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    acceptance_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:acceptance_summary")
    assert summary["status"] == "failed"
    assert acceptance_check["status"] == "failed"
    assert acceptance_check["details"]["contract_failure_count"] == 1
    assert acceptance_check["details"]["contract_failures"][0]["field"] == "runtime_evidence_status"
    assert summary["evidence_matrix"][0]["acceptance_runtime_evidence_status"] == "retrieved_result"


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("blocking_failures", {"reason": "not-a-list"}, "list"),
        ("warnings", {"reason": "not-a-list"}, "list"),
        ("recommended_action", "", "non_empty_string"),
        ("recommended_action", None, "non_empty_string"),
    ],
)
def test_release_audit_fails_release_sidecar_with_malformed_review_contract(
    tmp_path: Path,
    field: str,
    value: Any,
    expected: str,
) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    sidecar = artifact.parent / "acceptance_summary.json"
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    if value is None:
        payload.pop(field)
    else:
        payload[field] = value
    sidecar.write_text(json.dumps(payload), encoding="utf-8")
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    acceptance_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:acceptance_summary")
    assert summary["status"] == "failed"
    assert acceptance_check["status"] == "failed"
    assert acceptance_check["details"]["contract_failure_count"] == 1
    assert acceptance_check["details"]["contract_failures"][0]["field"] == field
    assert acceptance_check["details"]["contract_failures"][0]["expected"] == expected
    assert summary["evidence_matrix"][0]["acceptance_contract_failure_count"] == 1


@pytest.mark.parametrize("schema_version", ["qcchem.release_artifact_acceptance.v0.1-typo", None])
def test_release_audit_fails_unrecognized_acceptance_schema(tmp_path: Path, schema_version: str | None) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    sidecar = artifact.parent / "acceptance_summary.json"
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    if schema_version is None:
        payload.pop("schema_version")
    else:
        payload["schema_version"] = schema_version
    sidecar.write_text(json.dumps(payload), encoding="utf-8")
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    acceptance_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:acceptance_summary")
    assert summary["status"] == "failed"
    assert acceptance_check["status"] == "failed"
    assert acceptance_check["details"]["contract_failure_count"] == 1
    assert acceptance_check["details"]["contract_failures"][0]["field"] == "schema_version"
    assert summary["evidence_matrix"][0]["acceptance_contract_failure_count"] == 1


def test_release_audit_still_accepts_legacy_benchmark_acceptance_schema(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    (artifact.parent / "acceptance_summary.json").write_text(
        json.dumps(
            {
                "schema_version": "qcchem.benchmark_acceptance.v0.1-alpha",
                "suite_name": "legacy_suite",
                "accepted": True,
                "blocking_failures": [],
                "warnings": [],
                "recommended_action": "promote_accepted_benchmark",
            }
        ),
        encoding="utf-8",
    )
    spec = load_release_audit_spec(
        _write_config(
            tmp_path,
            artifact=artifact,
            include_exploratory_artifact=False,
            warning_policy=(
                "  warning_policy:\n"
                "    max_count: 0\n"
                "    allowed_ids: []\n"
            ),
        )
    )

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    acceptance_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:acceptance_summary")
    assert summary["status"] == "passed"
    assert acceptance_check["status"] == "passed"
    assert acceptance_check["details"]["schema_version"] == "qcchem.benchmark_acceptance.v0.1-alpha"
    assert acceptance_check["details"]["contract_failure_count"] == 0


def test_release_audit_prefers_bound_sidecar_over_embedded_legacy_acceptance(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["acceptance_summary"] = {
        "schema_version": "qcchem.benchmark_acceptance.v0.1-alpha",
        "accepted": False,
        "blocking_failures": [{"reason": "embedded_legacy_not_release_binding"}],
        "warnings": [],
        "recommended_action": "resolve_benchmark_acceptance_failures",
    }
    artifact.write_text(json.dumps(payload), encoding="utf-8")
    _write_acceptance_sidecar(artifact)
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    acceptance_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:acceptance_summary")
    assert summary["status"] == "passed"
    assert acceptance_check["status"] == "passed"
    assert acceptance_check["details"]["source"] == "sidecar"
    assert acceptance_check["details"]["schema_version"] == "qcchem.release_artifact_acceptance.v0.1-alpha"
    assert summary["evidence_matrix"][0]["acceptance_summary_source"] == "sidecar"
    assert summary["evidence_matrix"][0]["acceptance_schema_version"] == "qcchem.release_artifact_acceptance.v0.1-alpha"


def test_release_audit_fails_unreadable_acceptance_sidecar_without_crashing(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    (artifact.parent / "acceptance_summary.json").write_text("{not-json", encoding="utf-8")
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    acceptance_check = next(check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:acceptance_summary")
    assert summary["status"] == "failed"
    assert acceptance_check["status"] == "failed"
    assert acceptance_check["details"]["path"].endswith("acceptance_summary.json")
    assert "JSONDecodeError" in acceptance_check["details"]["error"]
    assert (tmp_path / "out" / "release_readiness.md").exists()


def test_release_audit_matrix_surfaces_hardware_campaign_runtime_evidence(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "hardware" / "hardware_calibration_summary.json"
    _write_hardware_campaign_artifact(artifact)
    _write_acceptance_sidecar(
        artifact,
        artifact_path="artifacts/hardware/hardware_calibration_summary.json",
        trust_tier="hardware_verified",
        runtime_evidence_status="retrieved_result",
    )
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    assert summary["status"] == "passed"
    entry = summary["evidence_matrix"][0]
    assert entry["runtime_evidence_status"] == "retrieved_result"
    assert entry["hardware_verified_case_count"] == 1
    report = (tmp_path / "out" / "release_readiness.md").read_text(encoding="utf-8")
    assert "- runtime_evidence_status: `retrieved_result`" in report
    assert "- hardware_verified_case_count: `1`" in report


def test_release_audit_fails_hardware_verified_trust_without_runtime_result(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "hardware" / "hardware_calibration_summary.json"
    _write_hardware_campaign_artifact(
        artifact,
        runtime_evidence_status="submitted",
        include_evidence_summary=True,
        hardware_verified_cases=[],
    )
    _write_acceptance_sidecar(
        artifact,
        artifact_path="artifacts/hardware/hardware_calibration_summary.json",
        trust_tier="hardware_verified",
        runtime_evidence_status="submitted",
    )
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    boundary_check = next(
        check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:runtime_evidence_boundary"
    )
    assert summary["status"] == "failed"
    assert boundary_check["status"] == "failed"
    assert boundary_check["details"]["failure"] == "hardware_verified_trust_without_retrieved_runtime_evidence"


def test_release_audit_fails_hardware_verified_run_without_top_level_runtime_evidence(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "runtime_claim" / "result.json"
    _write_artifact(artifact, algorithm="qft", trust_tier="hardware_verified")
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["evidence_summary"]["runtime_evidence_status"] = "retrieved_result"
    payload["evidence_summary"]["result_identity"] = {"artifact_kind": "run", "artifact_name": "runtime_claim"}
    artifact.write_text(json.dumps(payload), encoding="utf-8")
    _write_acceptance_sidecar(
        artifact,
        artifact_path="artifacts/runtime_claim/result.json",
        trust_tier="hardware_verified",
        runtime_evidence_status="retrieved_result",
    )
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    boundary_check = next(
        check for check in summary["checks"] if check["id"] == "curated_artifact:core_anchor:runtime_evidence_boundary"
    )
    assert summary["status"] == "failed"
    assert boundary_check["status"] == "failed"
    assert boundary_check["details"]["failure"] == "hardware_verified_trust_without_top_level_runtime_marker"


@pytest.mark.parametrize("algorithm", ["qft", "lr_ace", "tc_qsci"])
def test_release_audit_rejects_exploratory_assets_marked_validated(tmp_path: Path, algorithm: str) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / algorithm / "result.json"
    _write_artifact(artifact, algorithm=algorithm, trust_tier="validated")
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact, algorithm=algorithm))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    failed_ids = {check["id"] for check in summary["checks"] if check["status"] == "failed"}
    assert f"exploratory_asset:{algorithm}_asset:boundary" in failed_ids


def test_release_audit_rejects_runtime_preview_marked_hardware_verified(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "runtime_preview" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["hardware_verified"] = True
    payload["runtime_submission"] = {"attempted": True, "submitted": False, "failure_category": "runtime_submission_disabled"}
    artifact.write_text(json.dumps(payload), encoding="utf-8")
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    failed_ids = {check["id"] for check in summary["checks"] if check["status"] == "failed"}
    assert "curated_artifact:core_anchor:runtime_boundary" in failed_ids


def test_release_audit_reports_missing_doc_terms(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    (tmp_path / "README.md").write_text("QFT only", encoding="utf-8")
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    spec = load_release_audit_spec(_write_config(tmp_path, artifact=artifact))

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    readme_check = next(check for check in summary["checks"] if check["id"] == "doc:README.md:terms")
    assert readme_check["status"] == "failed"
    assert "TC-QSCI" in readme_check["details"]["missing_terms"]


def test_release_audit_reports_unreadable_doc_without_crashing(tmp_path: Path) -> None:
    _write_release_fixture(tmp_path)
    artifact = tmp_path / "artifacts" / "qft" / "result.json"
    _write_artifact(artifact, algorithm="qft")
    _write_acceptance_sidecar(artifact)
    config = _write_config(tmp_path, artifact=artifact, include_exploratory_artifact=False)
    payload = config.read_text(encoding="utf-8")
    payload = payload.replace("    - path: README.md", "    - path: docs", 1)
    config.write_text(payload, encoding="utf-8")
    spec = load_release_audit_spec(config)

    summary = run_release_audit(spec, repo_root=tmp_path, output_dir=tmp_path / "out")

    doc_check = next(check for check in summary["checks"] if check["id"] == "doc:docs:readable")
    assert summary["status"] == "failed"
    assert doc_check["required"] is True
    assert doc_check["status"] == "failed"
    assert doc_check["details"]["path"].endswith("docs")
    assert "IsADirectoryError" in doc_check["details"]["error"]
    assert (tmp_path / "out" / "release_readiness.json").exists()
    report = (tmp_path / "out" / "release_readiness.md").read_text(encoding="utf-8")
    assert "doc:docs:readable" in report
