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
            "verification_status": "passed",
            "mapping": {
              "kind": "jordan_wigner",
              "num_qubits": 4
            },
            "runtime_submission": {
              "backend_name": "ibm_kingston"
            }
          }
        }
        """,
        encoding="utf-8",
    )
    (root / "result.h5").touch()

    bundle = load_artifact_bundle(root)

    assert bundle["artifacts"]["result"]["present"] is False
    assert bundle["artifacts"]["qcschema"]["present"] is True
    assert bundle["artifacts"]["hdf5"]["present"] is True
    assert bundle["artifacts"]["hdf5"]["path"] == str(root / "result.h5")
    assert bundle["preferred_source"] == "qcschema"
    assert bundle["run"]["problem"]["molecule_name"] == "H2"
    assert bundle["run"]["verification_status"] == "passed"
    assert bundle["run"]["mapping"]["num_qubits"] == 4


def test_build_qcschema_payload_rejects_incomplete_payload() -> None:
    with pytest.raises(ValueError, match="missing required sections"):
        build_qcschema_payload({"problem": {"molecule_name": "H2"}})
