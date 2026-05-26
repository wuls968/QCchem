from pathlib import Path

from qcchem.backends.capabilities import describe_backend_capabilities
from qcchem.backends.policy import resolve_execution_policy
from qcchem.io.artifact_index import build_artifact_index
from qcchem.io.benchmark_config import load_benchmark_suite_spec
from qcchem.io.config import load_run_spec


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
