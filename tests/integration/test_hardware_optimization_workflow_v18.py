from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.cli.main import main
from qcchem.chem import build_electronic_structure_context
from qcchem.core import RuntimeSubmissionSummary
from qcchem.io.config import load_run_spec
from qcchem.mapping import map_fermionic_hamiltonian
from qcchem.solvers.exact import ExactDiagonalizationSolver

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_parity_two_qubit_reduction_preserves_h2_exact_energy() -> None:
    spec = load_run_spec(REPO_ROOT / "configs" / "h2_runtime_hardware_probe_puccd_layout.yaml")
    chemistry = build_electronic_structure_context(spec)

    jw = map_fermionic_hamiltonian(chemistry.fermionic_hamiltonian, "jordan_wigner")
    parity = map_fermionic_hamiltonian(
        chemistry.fermionic_hamiltonian,
        "parity_two_qubit_reduction",
        num_particles=chemistry.summary.num_particles,
    )

    jw_energy = ExactDiagonalizationSolver().solve(jw.qubit_hamiltonian).total_energy
    parity_energy = ExactDiagonalizationSolver().solve(parity.qubit_hamiltonian).total_energy

    assert jw.summary.num_qubits == 4
    assert parity.summary.num_qubits == 2
    assert jw.summary.qubit_term_count == 15
    assert parity.summary.qubit_term_count == 5
    assert parity_energy == pytest.approx(jw_energy, abs=1.0e-8)


@pytest.mark.integration
def test_h2_hardware_precision_push_config_parses_budget_controls() -> None:
    spec = load_run_spec(REPO_ROOT / "configs" / "h2_hardware_precision_push.yaml")

    assert spec.hardware_optimization.enabled is True
    assert spec.hardware_optimization.profile == "h2_precision_push"
    assert spec.hardware_optimization.max_real_jobs == 3
    assert spec.hardware_optimization.stop_if_error_below == pytest.approx(1.6e-3)
    assert "parity_puccd_layout" in spec.hardware_optimization.candidate_strategies
    assert spec.backend.runtime.options["wait_for_result"] is False
    assert spec.backend.runtime.options["submit_real_job"] is False


@pytest.mark.integration
def test_hardware_optimize_preview_writes_ranked_plan(tmp_path: Path) -> None:
    exit_code = main(
        [
            "hardware",
            "optimize",
            "-c",
            str(REPO_ROOT / "configs" / "h2_hardware_precision_push.yaml"),
            "--preview",
            "-o",
            str(tmp_path / "h2-precision-preview"),
        ]
    )

    assert exit_code == 0
    plan_path = tmp_path / "h2-precision-preview" / "hardware_optimization_plan.json"
    report_path = tmp_path / "h2-precision-preview" / "hardware_optimization_report.md"
    assert plan_path.exists()
    assert report_path.exists()

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    ranked_ids = [candidate["candidate_id"] for candidate in plan["ranked_candidates"]]
    assert ranked_ids[0].startswith("parity_")
    assert plan["runtime_budget_ledger"]["can_submit_more"] is True
    assert plan["stop_reason"] == "preview_only"
    assert "Optimization Trial" in report_path.read_text(encoding="utf-8")


@pytest.mark.integration
def test_hardware_optimize_submit_requires_confirmation(tmp_path: Path) -> None:
    exit_code = main(
        [
            "hardware",
            "optimize",
            "-c",
            str(REPO_ROOT / "configs" / "h2_hardware_precision_push.yaml"),
            "--submit",
            "-o",
            str(tmp_path / "h2-precision-submit"),
        ]
    )

    assert exit_code == 2
    assert not (tmp_path / "h2-precision-submit" / "runtime_submission.json").exists()
    assert not (tmp_path / "h2-precision-submit" / "candidates").exists()


@pytest.mark.integration
def test_hardware_optimize_submit_with_fake_runtime_writes_sidecar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_attempt_runtime_submission(*, spec, circuit, operator, parameter_values, submission_callback=None):
        summary = RuntimeSubmissionSummary(
            attempted=True,
            submitted=True,
            succeeded=False,
            service=spec.runtime.service,
            mode="backend",
            session_requested=spec.runtime.session_ready,
            batch_requested=spec.runtime.batch_ready,
            options_snapshot={
                "max_budgeted_shots": spec.runtime.max_budgeted_shots,
                "precision_target": spec.runtime.precision_target,
            },
            job_id="fake-h2-hardware-optimization",
            backend_name="fake_backend",
            verification_status="exploratory",
        )
        if submission_callback is not None:
            submission_callback(summary)
        return summary

    monkeypatch.setattr("qcchem.workflow.runner.attempt_runtime_submission", _fake_attempt_runtime_submission)

    exit_code = main(
        [
            "hardware",
            "optimize",
            "-c",
            str(REPO_ROOT / "configs" / "h2_hardware_precision_push.yaml"),
            "--submit",
            "--confirm-runtime-budget",
            "I understand IBM Runtime budget",
            "-o",
            str(tmp_path / "h2-precision-submit"),
        ]
    )

    assert exit_code == 0
    sidecars = list((tmp_path / "h2-precision-submit" / "runtime_jobs").glob("*/runtime_submission.json"))
    assert len(sidecars) == 1
    sidecar = json.loads(sidecars[0].read_text(encoding="utf-8"))
    assert sidecar["job_id"] == "fake-h2-hardware-optimization"
    assert sidecar["submitted"] is True
    assert sidecar["options_snapshot"]["max_budgeted_shots"] == 8192
    plan = json.loads((tmp_path / "h2-precision-submit" / "hardware_optimization_plan.json").read_text(encoding="utf-8"))
    assert plan["runtime_budget_ledger"]["real_jobs_submitted"] == 1
    assert plan["submitted_attempts"][0]["candidate_id"] == "parity_puccd_layout"


@pytest.mark.integration
def test_hardware_campaign_page_surfaces_optimization_trial() -> None:
    from qcchem.workbench.pages.hardware_campaign import build_hardware_campaign_page

    model = {
        "suite_name": "hardware_precision_push_v1",
        "summary": {"total_cases": 1, "runtime_evidence_status_counts": {"retrieved_result": 1}},
        "cases": [
            {
                "name": "parity_puccd_layout",
                "achieved_error": 0.004,
                "meets_chemical_accuracy": False,
                "backend_name": "ibm_kingston",
                "runtime_evidence_status": "retrieved_result",
                "runtime_usage_seconds": 40.0,
                "transpiled_depth": 34,
                "transpiled_two_qubit_gate_count": 8,
                "layout_strategy": "min_weighted_error",
                "hardware_verified": True,
            }
        ],
        "hardware_optimization": {
            "candidate_id": "parity_puccd_layout",
            "selection_score": [0, 2, 8, 34, 0.02],
            "local_accuracy_pass": True,
            "transpiled_depth": 34,
            "transpiled_two_qubit_gate_count": 8,
            "runtime_budget_ledger": {
                "real_jobs_submitted": 1,
                "max_real_jobs": 3,
                "total_budgeted_shots": 8192,
                "max_total_budgeted_shots": 40960,
            },
            "stop_reason": "continue_collecting_runtime_evidence",
        },
    }

    page_text = str(build_hardware_campaign_page(model))

    assert "Optimization Trial" in page_text
    assert "parity_puccd_layout" in page_text
    assert "8192" in page_text
