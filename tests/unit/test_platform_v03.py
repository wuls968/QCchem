from pathlib import Path

from qcchem.backends.capabilities import describe_backend_capabilities
from qcchem.backends.policy import resolve_execution_policy
from qcchem.core import BenchmarkCaseSpec
from qcchem.io.artifact_index import build_artifact_index
from qcchem.io.benchmark_config import load_benchmark_suite_spec
from qcchem.io.config import load_run_spec
from qcchem.workflow.benchmark import _select_benchmark_cases


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
