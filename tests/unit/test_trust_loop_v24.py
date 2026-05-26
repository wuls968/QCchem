from __future__ import annotations

import json
from pathlib import Path

import yaml

from qcchem.io.artifact_index import build_artifact_index
from qcchem.io.benchmark_config import load_benchmark_suite_spec
from qcchem.io.campaign_config import load_campaign_spec
from qcchem.workflow.acceptance import build_benchmark_acceptance_summary
from qcchem.workflow.hardware_diagnostics import build_hardware_error_diagnostic


def test_hardware_error_diagnostic_classifies_runtime_gap() -> None:
    payload = {
        "benchmark": {"absolute_error": 1.0e-5, "absolute_error_threshold": 1.6e-3},
        "chemical_accuracy": {"absolute_error_hartree": 1.0e-5, "threshold_hartree": 1.6e-3},
        "runtime_chemical_accuracy": {"absolute_error_hartree": 0.05, "statistical_error": 0.001},
        "runtime_submission": {
            "submitted": True,
            "succeeded": True,
            "backend_name": "ibm_test",
            "job_id": "job-1",
            "transpiled_depth": 42,
            "transpiled_two_qubit_gate_count": 7,
            "returned_job_metadata": {"metadata": {"shots": 4096}},
        },
    }

    diagnostic = build_hardware_error_diagnostic(payload)

    assert diagnostic["diagnostic_label"] == "hardware_bias_or_layout"
    assert diagnostic["next_measurement"] == "compare_layout_mapping_and_backend_error_profile"
    assert diagnostic["shots"] == 4096


def test_benchmark_acceptance_rejects_status_mismatch_and_missing_evidence(tmp_path: Path) -> None:
    case_root = tmp_path / "case"
    case_root.mkdir()
    (case_root / "result.json").write_text(json.dumps({"verification_status": "exploratory"}), encoding="utf-8")
    payload = {
        "suite_name": "suite",
        "evidence_summary": {"trust_tier": "exploratory", "recommended_action": "review"},
        "cases": [
            {
                "name": "h2_case",
                "kind": "run",
                "status": "exploratory",
                "expected_status": "validated",
                "artifact_root": str(case_root),
            }
        ],
    }

    summary = build_benchmark_acceptance_summary(
        payload,
        benchmark_result_path=tmp_path / "benchmark_result.json",
        strict_exit_code=True,
    )

    assert summary["accepted"] is False
    assert summary["policy"]["strict_exit_code"] is True
    reasons = {failure["reason"] for failure in summary["blocking_failures"]}
    assert {"status_mismatch", "missing_evidence_summary"}.issubset(reasons)


def test_artifact_index_extracts_evidence_and_runtime_sidecar(tmp_path: Path) -> None:
    root = tmp_path / "artifacts" / "h2"
    root.mkdir(parents=True)
    (root / "result.json").write_text(
        json.dumps(
            {
                "run_id": "h2",
                "verification_status": "validated",
                "evidence_summary": {
                    "trust_tier": "validated",
                    "recommended_action": "promote_validated_result",
                    "runtime_evidence_status": "retrieved_result",
                },
                "pbc": {"enabled": True, "status": "metadata_only"},
                "pbc_qmmm": {"enabled": True, "status": "metadata_only"},
            }
        ),
        encoding="utf-8",
    )
    (root / "runtime_submission.json").write_text(
        json.dumps({"attempted": True, "submitted": True, "succeeded": True}),
        encoding="utf-8",
    )

    index = build_artifact_index(tmp_path / "artifacts")
    entry = index["artifacts"][0]

    assert entry["artifact_kind"] == "run"
    assert entry["trust_tier"] == "validated"
    assert entry["runtime_submission_status"] == "succeeded"
    assert entry["has_runtime_submission"] is True
    assert entry["has_pbc_metadata"] is True
    assert entry["has_pbc_qmmm_metadata"] is True


def test_campaign_config_loads_entries(tmp_path: Path) -> None:
    config = tmp_path / "campaign.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "campaign": {
                    "name": "mini_campaign",
                    "output_root": str(tmp_path / "out"),
                    "entries": [
                        {
                            "name": "existing_h2",
                            "kind": "artifact",
                            "artifact": "artifacts/h2",
                            "tags": ["smoke"],
                        }
                    ],
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    spec = load_campaign_spec(config)

    assert spec.name == "mini_campaign"
    assert spec.output_root == tmp_path / "out"
    assert spec.entries[0].kind == "artifact"
    assert spec.entries[0].tags == ["smoke"]


def test_benchmark_acceptance_yaml_parses_policy(tmp_path: Path) -> None:
    run_config = tmp_path / "run.yaml"
    run_config.write_text("molecule:\n  name: H2\n", encoding="utf-8")
    suite = tmp_path / "suite.yaml"
    suite.write_text(
        yaml.safe_dump(
            {
                "benchmark_suite": {
                    "name": "suite",
                    "acceptance": {
                        "required_files": ["result.json", "report.md"],
                        "strict_exit_code": False,
                    },
                    "cases": [
                        {
                            "name": "case",
                            "kind": "run",
                            "config": str(run_config),
                        }
                    ],
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    spec = load_benchmark_suite_spec(suite)

    assert spec.acceptance.required_files == ["result.json", "report.md"]
    assert spec.acceptance.strict_exit_code is False
