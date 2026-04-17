from __future__ import annotations

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
        "benchmark": {"absolute_error": 0.0137, "meets_threshold": False},
        "runtime_submission": {
            "backend_name": "ibm_kingston",
            "transpiled_depth": 146,
            "transpiled_two_qubit_gate_count": 42,
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


def test_load_artifact_bundle_prefers_qcschema_and_hdf5_when_present(tmp_path) -> None:
    root = tmp_path / "artifact"
    root.mkdir()
    (root / "result.json").write_text('{"problem":{"molecule_name":"H2"}}', encoding="utf-8")
    (root / "qcschema.json").write_text('{"schema_name":"qcschema_output"}', encoding="utf-8")
    (root / "result.h5").touch()

    bundle = load_artifact_bundle(root)

    assert bundle["result"]["problem"]["molecule_name"] == "H2"
    assert bundle["qcschema"]["schema_name"] == "qcschema_output"
    assert bundle["hdf5_path"] == str(root / "result.h5")
