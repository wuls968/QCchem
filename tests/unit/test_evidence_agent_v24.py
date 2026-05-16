from __future__ import annotations

import json
from pathlib import Path

from qcchem.workflow.evidence_agent import (
    build_action_proposal,
    build_evidence_graph,
    load_evidence_source,
    review_claims,
    summarize_evidence_artifacts,
)


def _write_validated_run(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / "result.json"
    path.write_text(
        json.dumps(
            {
                "run_id": "h2_validated",
                "verification_status": "validated",
                "problem": {"molecule_name": "H2", "basis": "sto-3g"},
                "energy": {
                    "total_energy": -1.137,
                    "electronic_energy": -1.857,
                    "solver_energy": -1.857,
                    "constant_energy_correction": 0.0,
                    "nuclear_repulsion_energy": 0.72,
                    "energy_units": "Hartree",
                },
                "benchmark": {
                    "comparison_target": "exact diagonalization",
                    "absolute_error": 1.0e-4,
                    "absolute_error_threshold": 1.6e-3,
                },
                "backend": {"kind": "statevector"},
                "mapping": {"kind": "jordan_wigner"},
                "exact_baseline": {"available": True, "source": "exact_diagonalization"},
                "chemical_accuracy": {
                    "available": True,
                    "meets_chemical_accuracy": True,
                    "absolute_error_hartree": 1.0e-4,
                    "threshold_hartree": 1.6e-3,
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_hardware_campaign(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / "hardware_calibration_summary.json"
    path.write_text(
        json.dumps(
            {
                "suite_name": "h2_hardware_campaign",
                "summary": {
                    "total_cases": 1,
                    "runtime_evidence_status_counts": {"retrieved_result": 1},
                    "hardware_verified_cases": ["h2_runtime_probe"],
                },
                "cases": [
                    {
                        "name": "h2_runtime_probe",
                        "achieved_error": 0.012,
                        "meets_chemical_accuracy": False,
                        "runtime_evidence_status": "retrieved_result",
                        "hardware_verified": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_load_evidence_source_detects_run_result_and_hashes_payload(tmp_path: Path) -> None:
    result_path = _write_validated_run(tmp_path / "h2")

    source = load_evidence_source(result_path)

    assert source.artifact_kind == "run"
    assert source.trust_tier == "validated"
    assert source.chemical_accuracy_status == "met"
    assert source.payload_hash
    assert "result.json" in source.output_links


def test_evidence_graph_keeps_chemistry_and_runtime_best_evidence_separate(tmp_path: Path) -> None:
    run_path = _write_validated_run(tmp_path / "h2")
    hardware_path = _write_hardware_campaign(tmp_path / "hardware")

    graph = summarize_evidence_artifacts([str(run_path), str(hardware_path)])

    assert graph["trust_tier"] == "validated"
    assert graph["best_chemistry_evidence"]["artifact_kind"] == "run"
    assert graph["best_runtime_evidence"]["artifact_kind"] == "hardware_campaign"
    assert any("hardware_verified" in note for note in graph["boundary_notes"])


def test_review_claims_flags_hardware_verified_publication_overclaim(tmp_path: Path) -> None:
    hardware_path = _write_hardware_campaign(tmp_path / "hardware")

    review = review_claims(
        targets=[hardware_path],
        claim_text="This hardware_verified result is publication-grade and chemically accurate.",
    )

    assert review["status"] == "failed"
    assert any(finding["finding_id"].startswith("hardware-boundary") for finding in review["findings"])


def test_action_proposal_blocks_real_hardware_submit(tmp_path: Path) -> None:
    run_path = _write_validated_run(tmp_path / "h2")
    source = load_evidence_source(run_path)
    graph = build_evidence_graph([source]).to_record()

    action = build_action_proposal(
        task_type="execution",
        request_text="submit this to real hardware",
        linked_artifacts=[str(run_path)],
        evidence_graph=graph,
        action_kind="hardware_optimize_submit",
    )

    assert action.allowed is False
    assert "not allowed" in action.blocked_reason
