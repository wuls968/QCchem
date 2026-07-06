import json
import subprocess
from pathlib import Path

import pytest
import yaml

from qcchem.backends.capabilities import describe_backend_capabilities
from qcchem.backends.policy import resolve_execution_policy
from qcchem.core import BenchmarkCaseSpec
from qcchem.io.artifact_index import build_artifact_index
from qcchem.io.benchmark_config import load_benchmark_suite_spec
from qcchem.io.config import load_run_spec
from qcchem.io.release_audit_config import load_release_audit_spec
from qcchem.io.release_git_hygiene import (
    RELEASE_ARTIFACT_ACCEPTANCE_SCHEMA_VERSION,
    manifest_acceptance_sidecar_paths,
    orphan_release_acceptance_sidecars,
    release_generated_output_paths,
)
from qcchem.workflow.benchmark import _select_benchmark_cases
from qcchem.workflow.common import prepare_clean_output_root
from qcchem.workflow.runner import _prepare_artifact_paths

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_backend_capability_and_policy_resolution() -> None:
    spec = load_run_spec(Path("configs/h2_hardware_ready.yaml"))

    capabilities = describe_backend_capabilities(spec.backend)
    policy = resolve_execution_policy(spec.policy, spec.backend, spec.benchmark, spec.mitigation)

    assert policy.name == "hardware_ready"
    assert capabilities.runtime_ready is True
    assert capabilities.mitigation_ready is True
    assert capabilities.supports_confidence_metrics is True
    assert spec.backend.repetitions >= 5
    assert spec.mitigation.symmetry_check.enabled is True


def test_benchmark_registry_contains_suite_v1_cases() -> None:
    suite = load_benchmark_suite_spec(Path("benchmarks/benchmark_suite_v1.yaml"))
    case_names = {case.name for case in suite.cases}

    assert {
        "h2_exact_reference",
        "h2_statevector_vqe",
        "h2_shot_vqe",
        "h2_noisy_comparison",
        "lih_exact_reference",
        "lih_active_space_vqe",
        "h2o_active_space_exact",
        "jw_bk_consistency_h2",
        "h2_shot_scaling",
        "h2_optimizer_stability",
    }.issubset(case_names)


def test_artifact_indexer_discovers_result_artifacts(tmp_path: Path) -> None:
    first = tmp_path / "artifacts" / "h2_run"
    first.mkdir(parents=True)
    (first / "result.json").write_text("{}", encoding="utf-8")
    (first / "report.md").write_text("# report", encoding="utf-8")
    (first / "field_model_registry.json").write_text("{}", encoding="utf-8")
    (first / "field_hamiltonian.json").write_text("{}", encoding="utf-8")

    second = tmp_path / "artifacts" / "lih_run"
    second.mkdir(parents=True)
    (second / "result.json").write_text("{}", encoding="utf-8")

    index = build_artifact_index(tmp_path / "artifacts")

    assert index["total_artifacts"] == 2
    assert {item["artifact_root"] for item in index["artifacts"]} == {
        str(first),
        str(second),
    }
    assert index["artifacts"][0]["has_result_json"] is True
    indexed = {Path(str(item["artifact_root"])).name: item for item in index["artifacts"]}
    assert indexed["h2_run"]["has_field_evidence"] is True
    assert indexed["h2_run"]["field_sidecar_count"] == 2
    assert indexed["lih_run"]["has_field_evidence"] is False
    assert index["artifact_root_exists"] is True
    assert index["artifact_root_is_dir"] is True
    assert index["index_error"] is None
    assert index["skipped_generated_artifacts"] == 0


def test_artifact_indexer_reports_file_root_without_scanning(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    root.write_text("not a directory", encoding="utf-8")

    index = build_artifact_index(root)

    assert index["artifact_root_exists"] is True
    assert index["artifact_root_is_dir"] is False
    assert index["index_error"] == "Artifact root is not a directory."
    assert index["total_artifacts"] == 0
    assert index["artifacts"] == []


def test_artifact_indexer_skips_nested_preview_local_outputs(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    curated = artifact_root / "h2_run"
    curated.mkdir(parents=True)
    (curated / "result.json").write_text("{}", encoding="utf-8")

    preview = curated / "preview_local"
    preview.mkdir()
    preview_result = preview / "result.json"
    preview_result.write_text("{}", encoding="utf-8")

    index = build_artifact_index(artifact_root)

    assert index["total_artifacts"] == 1
    assert [item["artifact_root"] for item in index["artifacts"]] == [str(curated)]
    assert index["skipped_generated_artifacts"] == 1
    assert index["skipped_generated_result_paths"] == [str(preview_result)]
    assert index["skipped_generated_result_paths_truncated"] is False


def test_artifact_indexer_indexes_explicit_preview_root(tmp_path: Path) -> None:
    preview = tmp_path / "artifacts" / "h2_run" / "preview_local"
    preview.mkdir(parents=True)
    (preview / "result.json").write_text("{}", encoding="utf-8")

    index = build_artifact_index(preview)

    assert index["total_artifacts"] == 1
    assert index["skipped_generated_artifacts"] == 0


def test_artifact_indexer_reads_acceptance_summary_sidecar(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts" / "accepted_run"
    artifact_root.mkdir(parents=True)
    (artifact_root / "result.json").write_text("{}", encoding="utf-8")
    (artifact_root / "acceptance_summary.json").write_text(
        """
{
  "accepted": true,
  "recommended_action": "accept_release_artifact_with_declared_boundary"
}
""",
        encoding="utf-8",
    )

    index = build_artifact_index(tmp_path / "artifacts")
    entry = index["artifacts"][0]

    assert entry["has_acceptance_summary"] is True
    assert entry["acceptance_summary_source"] == "sidecar"
    assert entry["acceptance_summary_readable"] is True
    assert entry["acceptance_summary_error"] is None
    assert entry["recommended_action"] == "accept_release_artifact_with_declared_boundary"


def test_artifact_indexer_prefers_sidecar_acceptance_over_embedded_summary(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts" / "accepted_run"
    artifact_root.mkdir(parents=True)
    (artifact_root / "result.json").write_text(
        """
{
  "acceptance_summary": {
    "accepted": false,
    "recommended_action": "resolve_embedded_acceptance"
  }
}
""",
        encoding="utf-8",
    )
    (artifact_root / "acceptance_summary.json").write_text(
        """
{
  "accepted": true,
  "recommended_action": "accept_release_artifact_with_declared_boundary"
}
""",
        encoding="utf-8",
    )

    index = build_artifact_index(tmp_path / "artifacts")
    entry = index["artifacts"][0]

    assert entry["has_acceptance_summary"] is True
    assert entry["acceptance_summary_source"] == "sidecar"
    assert entry["acceptance_summary_readable"] is True
    assert entry["acceptance_summary_error"] is None
    assert entry["recommended_action"] == "accept_release_artifact_with_declared_boundary"


def test_artifact_indexer_surfaces_unreadable_acceptance_summary_sidecar(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts" / "bad_acceptance_run"
    artifact_root.mkdir(parents=True)
    (artifact_root / "result.json").write_text("{}", encoding="utf-8")
    (artifact_root / "acceptance_summary.json").write_text("{not-json", encoding="utf-8")

    index = build_artifact_index(tmp_path / "artifacts")
    entry = index["artifacts"][0]

    assert entry["has_acceptance_summary"] is True
    assert entry["acceptance_summary_path"] == str(artifact_root / "acceptance_summary.json")
    assert entry["acceptance_summary_source"] is None
    assert entry["acceptance_summary_readable"] is False
    assert "JSONDecodeError" in str(entry["acceptance_summary_error"])


def test_artifact_indexer_marks_empty_acceptance_sidecar_readable(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts" / "empty_acceptance_run"
    artifact_root.mkdir(parents=True)
    (artifact_root / "result.json").write_text("{}", encoding="utf-8")
    (artifact_root / "acceptance_summary.json").write_text("{}", encoding="utf-8")

    index = build_artifact_index(tmp_path / "artifacts")
    entry = index["artifacts"][0]

    assert entry["has_acceptance_summary"] is True
    assert entry["acceptance_summary_path"] == str(artifact_root / "acceptance_summary.json")
    assert entry["acceptance_summary_source"] == "sidecar"
    assert entry["acceptance_summary_readable"] is True
    assert entry["acceptance_summary_error"] is None
    assert entry["recommended_action"] is None


def test_prepare_clean_output_root_rejects_non_empty_directory_without_overwrite(tmp_path: Path) -> None:
    root = tmp_path / "aggregate"
    root.mkdir()
    sentinel = root / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists and is not empty"):
        prepare_clean_output_root(root, workflow_name="Benchmark suite", overwrite=False)

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_prepare_clean_output_root_overwrite_replaces_existing_directory(tmp_path: Path) -> None:
    root = tmp_path / "aggregate"
    root.mkdir()
    sentinel = root / "old.txt"
    sentinel.write_text("old", encoding="utf-8")

    resolved = prepare_clean_output_root(root, workflow_name="Benchmark suite", overwrite=True)

    assert resolved == root
    assert root.exists()
    assert not sentinel.exists()


def test_prepare_clean_output_root_rejects_symlink_output_target(tmp_path: Path) -> None:
    target = tmp_path / "real-output"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    link = tmp_path / "linked-output"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is unavailable on this filesystem")

    with pytest.raises(FileExistsError, match="symlink component"):
        prepare_clean_output_root(link, workflow_name="Benchmark suite", overwrite=True)

    assert link.is_symlink()
    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_prepare_clean_output_root_rejects_existing_file_path(tmp_path: Path) -> None:
    root = tmp_path / "aggregate"
    root.write_text("not a directory", encoding="utf-8")

    with pytest.raises(FileExistsError, match="not a directory"):
        prepare_clean_output_root(root, workflow_name="Benchmark suite", overwrite=False)


@pytest.mark.parametrize("root", [Path(Path.cwd().anchor), Path.home(), REPO_ROOT, Path("artifacts")])
def test_prepare_clean_output_root_rejects_broad_overwrite_targets(root: Path) -> None:
    with pytest.raises(FileExistsError, match="too broad for workflow output"):
        prepare_clean_output_root(root, workflow_name="Benchmark suite", overwrite=True)


@pytest.mark.parametrize("root", [REPO_ROOT / ".git", REPO_ROOT / "qcchem", REPO_ROOT / "tests"])
def test_prepare_clean_output_root_rejects_source_tree_overwrite_targets(root: Path) -> None:
    with pytest.raises(FileExistsError, match="source tree outside artifacts"):
        prepare_clean_output_root(root, workflow_name="Benchmark suite", overwrite=True)


def test_prepare_clean_output_root_rejects_new_source_tree_output_target() -> None:
    root = REPO_ROOT / "qcchem" / "new-aggregate-output"

    with pytest.raises(FileExistsError, match="source tree outside artifacts"):
        prepare_clean_output_root(root, workflow_name="Benchmark suite", overwrite=False)

    assert not root.exists()


def test_run_artifact_paths_rejects_existing_file_path(tmp_path: Path) -> None:
    root = tmp_path / "artifact-file"
    root.write_text("not a directory", encoding="utf-8")

    with pytest.raises(FileExistsError, match="not a directory"):
        _prepare_artifact_paths(root, overwrite=True, qcschema_json=False, hdf5=False)

    assert root.read_text(encoding="utf-8") == "not a directory"


def test_run_artifact_paths_rejects_symlink_output_target(tmp_path: Path) -> None:
    target = tmp_path / "real-run-output"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    link = tmp_path / "linked-run-output"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is unavailable on this filesystem")

    with pytest.raises(FileExistsError, match="symlink component"):
        _prepare_artifact_paths(link, overwrite=True, qcschema_json=False, hdf5=False)

    assert link.is_symlink()
    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_run_artifact_paths_rejects_new_source_tree_output_target() -> None:
    root = REPO_ROOT / "docs" / "run-output"

    with pytest.raises(FileExistsError, match="source tree outside artifacts"):
        _prepare_artifact_paths(root, overwrite=False, qcschema_json=False, hdf5=False)

    assert not root.exists()


def test_run_artifact_paths_guards_before_overwrite(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "run-output"
    root.mkdir()
    sentinel = root / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    calls: dict[str, object] = {}

    def _fake_guard(resolved_root: Path, *, workflow_name: str) -> None:
        calls["resolved_root"] = resolved_root
        calls["workflow_name"] = workflow_name
        raise FileExistsError("blocked by overwrite guard")

    monkeypatch.setattr("qcchem.workflow.runner.guard_output_target", _fake_guard)

    with pytest.raises(FileExistsError, match="blocked by overwrite guard"):
        _prepare_artifact_paths(root, overwrite=True, qcschema_json=False, hdf5=False)

    assert calls == {"resolved_root": root, "workflow_name": "Run"}
    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_release_git_hygiene_keeps_outputs_ignored_and_sidecars_tracked() -> None:
    git_probe = _run_git(["rev-parse", "--is-inside-work-tree"])
    if git_probe.returncode != 0:
        pytest.skip("release git hygiene checks require a git checkout")

    for path in release_generated_output_paths():
        ignored = _run_git(["check-ignore", "--no-index", "-q", path])
        assert ignored.returncode == 0, f"{path} should stay ignored as local generated output"

    tracked_ignored = _run_git(["ls-files", "-ci", "--exclude-standard"])
    assert tracked_ignored.returncode == 0
    assert tracked_ignored.stdout.strip() == "", (
        "ignored generated files must not stay tracked:\n" + tracked_ignored.stdout
    )

    spec = load_release_audit_spec(REPO_ROOT / "configs" / "release" / "trust_first_audit.yaml")
    release_sidecars = manifest_acceptance_sidecar_paths(spec)

    assert release_sidecars
    for sidecar in sorted(release_sidecars, key=str):
        path = sidecar.as_posix()
        ignored = _run_git(["check-ignore", "--no-index", "-q", path])
        assert ignored.returncode == 1, f"{path} must not match .gitignore"
        tracked = _run_git(["ls-files", "--error-unmatch", path])
        assert tracked.returncode == 0, f"{path} must be tracked as release evidence"

    assert orphan_release_acceptance_sidecars(REPO_ROOT, release_sidecars) == []


def test_ci_runs_release_acceptance_sidecar_freshness_gate() -> None:
    workflow = yaml.safe_load((REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["test"]["steps"]
    matches = [
        step
        for step in steps
        if isinstance(step, dict)
        and step.get("name") == "Run release acceptance sidecar freshness"
    ]

    assert len(matches) == 1
    command = matches[0]["run"]
    assert isinstance(command, str)
    assert [line.strip() for line in command.splitlines() if line.strip()] == [
        "set -euo pipefail",
        "python -m qcchem.cli.main release acceptance-status \\",
        "-c configs/release/trust_first_audit.yaml \\",
        "--strict \\",
        "--repair-plan \\",
        "-o /tmp/qcchem-release-acceptance-status.json",
    ]


def test_ci_validates_release_acceptance_status_artifact_contract() -> None:
    workflow = yaml.safe_load((REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["test"]["steps"]
    matches = [
        step
        for step in steps
        if isinstance(step, dict)
        and step.get("name") == "Validate release acceptance status artifact"
    ]

    assert len(matches) == 1
    command = matches[0]["run"]
    assert isinstance(command, str)
    assert "set -euo pipefail" in command
    assert "/tmp/qcchem-release-acceptance-status.json" in command
    assert "RELEASE_ACCEPTANCE_STATUS_SCHEMA_FEATURES" in command
    assert "release_acceptance_status_contract_failures" in command


def test_ci_validates_release_status_artifacts_with_shared_api() -> None:
    workflow = yaml.safe_load((REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["test"]["steps"]
    matches = [
        step
        for step in steps
        if isinstance(step, dict)
        and step.get("name") == "Validate release status artifacts"
    ]

    assert len(matches) == 1
    command = matches[0]["run"]
    assert isinstance(command, str)
    assert "set -euo pipefail" in command
    assert "from qcchem.workflow.release_status import build_release_status_summary" in command
    assert 'Path("artifacts/release_audit")' in command
    assert 'Path("/tmp/qcchem-wheel-release-audit")' in command
    assert "contract_mismatches" in command


def test_manifest_release_acceptance_sidecars_share_handoff_contract() -> None:
    spec = load_release_audit_spec(REPO_ROOT / "configs" / "release" / "trust_first_audit.yaml")
    release_sidecars = manifest_acceptance_sidecar_paths(spec)
    required_keys = {
        "schema_version",
        "artifact_name",
        "artifact_path",
        "artifact_sha256",
        "accepted",
        "acceptance_scope",
        "trust_tier",
        "runtime_evidence_status",
        "release_audit_check_id",
        "blocking_failures",
        "warnings",
        "release_boundaries",
        "recommended_action",
    }

    assert release_sidecars
    for sidecar in sorted(release_sidecars, key=str):
        payload = json.loads((REPO_ROOT / sidecar).read_text(encoding="utf-8"))
        missing = sorted(required_keys - set(payload))
        assert missing == [], f"{sidecar} is missing release handoff fields: {missing}"
        assert payload["schema_version"] == RELEASE_ARTIFACT_ACCEPTANCE_SCHEMA_VERSION
        assert payload["recommended_action"] == "accept_release_artifact_with_declared_boundary"
        assert isinstance(payload["release_boundaries"], list)
        assert payload["release_boundaries"]


def test_release_manifest_advertises_bounded_lr_ace_slow_smoke_not_stress() -> None:
    spec = load_release_audit_spec(REPO_ROOT / "configs" / "release" / "trust_first_audit.yaml")

    assert "python -m pytest -m slow tests/integration/test_lr_ace_workflow_v19.py -q" in spec.acceptance_commands
    assert (
        "python -m pytest tests -q -W error::scipy.sparse._base.SparseEfficiencyWarning"
        in spec.acceptance_commands
    )
    assert not any("-m stress" in command for command in spec.acceptance_commands)


def test_release_git_hygiene_detects_orphan_release_artifact_sidecars(tmp_path: Path) -> None:
    manifest_sidecar = Path("artifacts") / "manifest_bound" / "acceptance_summary.json"
    orphan_release_sidecar = tmp_path / "artifacts" / "orphan_release" / "acceptance_summary.json"
    legacy_sidecar = tmp_path / "artifacts" / "legacy_benchmark" / "acceptance_summary.json"
    manifest_bound_sidecar = tmp_path / manifest_sidecar
    for path in (orphan_release_sidecar, legacy_sidecar, manifest_bound_sidecar):
        path.parent.mkdir(parents=True)
    orphan_release_sidecar.write_text(
        (
            '{"schema_version": "'
            + RELEASE_ARTIFACT_ACCEPTANCE_SCHEMA_VERSION
            + '", "accepted": true, "blocking_failures": [], "warnings": [], '
            '"recommended_action": "accept_release_artifact"}'
        ),
        encoding="utf-8",
    )
    manifest_bound_sidecar.write_text(orphan_release_sidecar.read_text(encoding="utf-8"), encoding="utf-8")
    legacy_sidecar.write_text(
        (
            '{"schema_version": "qcchem.benchmark_acceptance.v0.1-alpha", '
            '"accepted": true, "blocking_failures": [], "warnings": [], '
            '"recommended_action": "promote_accepted_benchmark"}'
        ),
        encoding="utf-8",
    )

    assert orphan_release_acceptance_sidecars(tmp_path, {manifest_sidecar}) == [
        Path("artifacts") / "orphan_release" / "acceptance_summary.json"
    ]


def test_artifact_indexer_discovers_workflow_artifacts(tmp_path: Path) -> None:
    workflow_root = tmp_path / "artifacts" / "workflows" / "h2_flow"
    workflow_root.mkdir(parents=True)
    (workflow_root / "workflow_result.json").write_text(
        """
{
  "schema_version": "qcchem.workflow_run.v0.1-alpha",
  "workflow_name": "h2_flow",
  "status": "completed",
  "summary": {
    "completed_steps": 3,
    "failed_steps": 0,
    "generated_steps": 1
  },
  "acceptance_summary": {
    "accepted": true,
    "recommended_action": "promote_workflow_outputs"
  }
}
""",
        encoding="utf-8",
    )
    (workflow_root / "workflow_report.md").write_text("# Workflow\n", encoding="utf-8")
    (workflow_root / "workflow_graph.json").write_text("{}", encoding="utf-8")
    (workflow_root / "provenance.jsonl").write_text("{}\n", encoding="utf-8")
    (workflow_root / "registry.json").write_text("{}", encoding="utf-8")

    index = build_artifact_index(tmp_path / "artifacts")
    entry = index["artifacts"][0]

    assert entry["artifact_kind"] == "workflow"
    assert entry["artifact_name"] == "h2_flow"
    assert entry["workflow_status"] == "completed"
    assert entry["workflow_accepted"] is True
    assert entry["workflow_completed_steps"] == 3
    assert entry["workflow_failed_steps"] == 0
    assert entry["workflow_generated_steps"] == 1
    assert entry["has_acceptance_summary"] is True
    assert entry["has_report_markdown"] is True
    assert entry["has_workflow_graph"] is True
    assert entry["has_workflow_provenance"] is True
    assert entry["has_workflow_registry"] is True


def test_benchmark_tag_filter_selects_fast_and_records_skipped_cases() -> None:
    cases = [
        BenchmarkCaseSpec(name="fast_h2", kind="run", tags=["fast", "h2"]),
        BenchmarkCaseSpec(name="slow_h2o", kind="run", tags=["slow", "h2o"]),
        BenchmarkCaseSpec(name="fast_lih", kind="run", tags=["fast", "lih"]),
    ]

    selected, summary = _select_benchmark_cases(cases, include_tags="fast", exclude_tags=["h2"])

    assert [case.name for case in selected] == ["fast_lih"]
    assert summary["include_tags"] == ["fast"]
    assert summary["exclude_tags"] == ["h2"]
    assert summary["selected_cases"] == ["fast_lih"]
    assert {item["name"] for item in summary["skipped_cases"]} == {"fast_h2", "slow_h2o"}
