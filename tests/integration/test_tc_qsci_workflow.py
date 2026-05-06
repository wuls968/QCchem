from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.workflow.runner import run_from_config


def _write_h2_tc_qsci_config(path: Path, output_dir: Path, *, mapping: str = "jordan_wigner") -> None:
    path.write_text(
        f"""
molecule:
  name: H2-tc-qsci-test
  geometry:
    - {{symbol: H, coords: [0.0, 0.0, 0.0]}}
    - {{symbol: H, coords: [0.0, 0.0, 0.735]}}
  charge: 0
  multiplicity: 1
  basis: sto3g

problem:
  active_space: null

mapping:
  kind: {mapping}

backend:
  kind: statevector

solver:
  kind: exact

benchmark:
  enabled: true
  exact_baseline_qubit_limit: 12
  absolute_error_threshold: 1.0e-8
  relative_error_threshold: 1.0e-8

policy:
  allow_exploratory: true

exploratory:
  enabled: true
  modules: [tc_qsci]

tc_qsci:
  enabled: true
  cast_model:
    kind: identity
  initial_state:
    kind: hf
  kick:
    time: 0.05
    num_kicks: 1
    pauli_term_budget: 8
    shots: 256
  selection:
    max_determinants: 4
    min_count: 1
    symmetry_postselect: true
  resource_estimation:
    enabled: true
    target_precision: 1.0e-3

run:
  seed: 17
  output_dir: {output_dir}
  overwrite: true
""",
        encoding="utf-8",
    )


@pytest.mark.integration
def test_h2_tc_qsci_run_persists_exploratory_artifact_sections(tmp_path: Path) -> None:
    config = tmp_path / "h2_tc_qsci.yaml"
    _write_h2_tc_qsci_config(config, tmp_path / "h2-tc-qsci")

    result = run_from_config(config, exploratory_command=True)

    assert result.verification_status == "exploratory"
    assert result.module_origin == "exploratory"
    assert result.tc_qsci_result is not None
    assert result.determinant_selection is not None
    assert result.cast_hamiltonian is not None
    assert result.low_rank_resource_estimate is not None
    assert result.qpe_resource_estimate is not None
    assert result.error_budget is not None

    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert payload["tc_qsci_result"]["algorithm_name"] == "TC-kicked QSCI"
    assert payload["determinant_selection"]["selected_determinant_count"] > 0
    assert payload["symmetry_sector"]["particle_number_conserved"] is True
    assert payload["cast_hamiltonian"]["kind"] == "identity"
    assert payload["qpe_resource_estimate"]["estimator_scope"] == "coarse_fault_tolerant_resource_estimate_only"
    assert "## TC-Kicked QSCI" in result.artifacts.report_markdown.read_text(encoding="utf-8")


@pytest.mark.integration
def test_lih_active_tc_qsci_config_stays_exploratory(tmp_path: Path) -> None:
    result = run_from_config(
        Path("configs/exploratory/lih_active_tc_qsci.yaml"),
        output_dir=tmp_path / "lih-active-tc-qsci",
        exploratory_command=True,
    )

    assert result.tc_qsci_result is not None
    assert result.verification_status == "exploratory"
    assert result.capability_tier == "exploratory"


@pytest.mark.integration
def test_tc_qsci_rejects_non_jw_sampling_without_resource_only_mode(tmp_path: Path) -> None:
    config = tmp_path / "h2_tc_qsci_bk.yaml"
    _write_h2_tc_qsci_config(config, tmp_path / "h2-tc-qsci-bk", mapping="bravyi_kitaev")

    with pytest.raises(ValueError, match="TC-QSCI determinant sampling v1 requires jordan_wigner"):
        run_from_config(config, exploratory_command=True)
