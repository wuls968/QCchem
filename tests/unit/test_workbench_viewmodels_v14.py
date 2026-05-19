from __future__ import annotations

import pytest

from qcchem.io.exports import build_qcschema_payload
from qcchem.workbench.data import load_artifact_bundle
from qcchem.workbench.viewmodels import build_run_view_model


def test_build_run_view_model_extracts_visual_sections() -> None:
    payload = {
        "problem": {
            "molecule_name": "H2",
            "basis": "sto3g",
            "active_space_metadata": {"num_active_orbitals": 2},
        },
        "energy": {
            "total_energy": -1.1373,
            "electronic_energy": -1.8572,
            "nuclear_repulsion_energy": 0.7199,
        },
        "mapping": {"kind": "jordan_wigner", "num_qubits": 4, "qubit_term_count": 15},
        "benchmark": {
            "absolute_error": 0.0137,
            "relative_error": 0.021,
            "meets_threshold": False,
            "within_uncertainty": True,
            "threshold": 0.02,
            "comparison_target": "exact",
            "compressed_vs_uncompressed": "compressed",
        },
        "runtime_submission": {
            "backend_name": "ibm_kingston",
            "backend_version": "1.4.0",
            "provider": "ibm",
            "job_id": "job-123",
            "attempted": True,
            "submitted": True,
            "succeeded": True,
            "runtime_kind": "runtime_estimator",
            "mode": "runtime",
            "service": "ibm_runtime",
            "failure_category": None,
            "failure_message": None,
            "options_snapshot": {"precision_target": 0.02},
            "result_provenance": {"attempt_stage": "result_retrieved"},
            "returned_job_metadata": {"metadata": {"shots": 4096}},
            "verification_status": "passed",
            "transpiled_depth": 146,
            "transpiled_two_qubit_gate_count": 42,
            "transpilation": {"optimization_level": 2},
        },
        "reduction_audit": {
            "selection_mode": "auto",
            "selected_active_orbitals_original": [1, 2],
        },
        "compression_result": {
            "method": "modified_cholesky",
            "rank": 2,
            "post_term_count": 12,
        },
    }

    view = build_run_view_model(payload)

    assert view["hero"]["molecule_name"] == "H2"
    assert view["mapping"]["num_qubits"] == 4
    assert view["compression"]["method"] == "modified_cholesky"
    assert view["runtime"]["backend_name"] == "ibm_kingston"
    assert view["runtime"]["failure_category"] is None
    assert view["runtime"]["mode"] == "runtime"
    assert view["runtime"]["options_snapshot"]["precision_target"] == 0.02
    assert view["runtime"]["result_provenance"]["attempt_stage"] == "result_retrieved"
    assert view["runtime"]["returned_job_metadata"]["metadata"]["shots"] == 4096
    assert view["benchmark"]["relative_error"] == 0.021
    assert view["benchmark"]["comparison_target"] == "exact"
    assert view["confidence"]["threshold"] == 0.02
    assert view["confidence"]["hardware_verified"] is None


def test_load_artifact_bundle_prefers_qcschema_and_hdf5_when_present(tmp_path) -> None:
    root = tmp_path / "artifact"
    root.mkdir()
    (root / "qcschema.json").write_text(
        """
        {
          "schema_name": "qcschema_output",
          "success": true,
          "molecule": {
            "name": "H2",
            "charge": 0,
            "multiplicity": 1
          },
          "properties": {
            "return_energy": -1.1373,
            "electronic_energy": -1.8572,
            "nuclear_repulsion_energy": 0.7199
          },
          "extras": {
            "verification_status": "exploratory",
            "hardware_verified": false,
            "mapping": {
              "kind": "jordan_wigner",
              "num_qubits": 4
            },
            "reduction_audit": {
              "active_space_metadata": {
                "num_active_orbitals": 2
              }
            },
            "runtime_submission": {
              "backend_name": "ibm_kingston"
            },
            "quantum_evidence": {
              "available": true,
              "sidecar_path": "/tmp/quantum_evidence.json",
              "hamiltonian": {
                "pauli_term_count": 15
              }
            }
          }
        }
        """,
        encoding="utf-8",
    )
    (root / "result.h5").touch()

    bundle = load_artifact_bundle(root)

    assert bundle["result"] is None
    assert bundle["qcschema"]["schema_name"] == "qcschema_output"
    assert bundle["hdf5_path"] == str(root / "result.h5")
    assert bundle["artifacts"]["result"]["present"] is False
    assert bundle["artifacts"]["qcschema"]["present"] is True
    assert bundle["artifacts"]["hdf5"]["present"] is True
    assert bundle["artifacts"]["hdf5"]["path"] == str(root / "result.h5")
    assert bundle["preferred_source"] == "qcschema"
    assert bundle["run"]["problem"]["molecule_name"] == "H2"
    assert bundle["run"]["verification_status"] == "exploratory"
    assert bundle["run"]["success"] is True
    assert bundle["run"]["problem"]["active_space_metadata"]["num_active_orbitals"] == 2
    assert bundle["run"]["mapping"]["num_qubits"] == 4
    assert bundle["run"]["quantum_evidence"]["available"] is True
    assert bundle["run"]["quantum_evidence"]["hamiltonian"]["pauli_term_count"] == 15


def test_build_qcschema_payload_rejects_incomplete_payload() -> None:
    with pytest.raises(ValueError, match="missing required sections"):
        build_qcschema_payload({"problem": {"molecule_name": "H2"}})


def test_build_qcschema_payload_marks_missing_verification_status_as_unsuccessful() -> None:
    payload = {
        "problem": {
            "molecule_name": "H2",
            "basis": "sto3g",
            "charge": 0,
            "multiplicity": 1,
        },
        "energy": {
            "total_energy": -1.1373,
            "electronic_energy": -1.8572,
            "nuclear_repulsion_energy": 0.7199,
        },
    }

    qcschema = build_qcschema_payload(payload)

    assert qcschema["extras"]["verification_status"] is None
    assert qcschema["success"] is False


def test_build_qcschema_payload_rejects_present_problem_without_molecule_name() -> None:
    payload = {
        "problem": {
            "basis": "sto3g",
            "charge": 0,
            "multiplicity": 1,
        },
        "energy": {
            "total_energy": -1.1373,
            "electronic_energy": -1.8572,
            "nuclear_repulsion_energy": 0.7199,
        },
    }

    with pytest.raises(ValueError, match="problem.molecule_name"):
        build_qcschema_payload(payload)


def test_build_qcschema_payload_rejects_present_energy_without_total_energy() -> None:
    payload = {
        "problem": {
            "molecule_name": "H2",
            "basis": "sto3g",
            "charge": 0,
            "multiplicity": 1,
        },
        "energy": {
            "electronic_energy": -1.8572,
            "nuclear_repulsion_energy": 0.7199,
        },
    }

    with pytest.raises(ValueError, match="energy.total_energy"):
        build_qcschema_payload(payload)
