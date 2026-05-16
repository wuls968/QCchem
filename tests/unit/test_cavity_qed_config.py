from __future__ import annotations

from pathlib import Path

import pytest

from qcchem.io.config import load_run_spec


def _write_cavity_config(path: Path, *, coupling: float = 0.05, max_occupation: int = 1) -> None:
    path.write_text(
        f"""
molecule:
  name: H2-cavity-config
  geometry:
    - symbol: H
      coords: [0.0, 0.0, 0.0]
    - symbol: H
      coords: [0.0, 0.0, 0.74]

policy:
  name: benchmark
  allow_exploratory: true

exploratory:
  enabled: true
  modules: [cavity_qed]

problem:
  cavity_qed:
    enabled: true
    model: pauli_fierz_cavity_qed
    photon_encoding: linear
    include_dipole_self_energy: true
    photon_physical_subspace_penalty: 25.0
    modes:
      - frequency: 0.4
        coupling_strength: {coupling}
        polarization: [0.0, 0.0, 1.0]
        max_occupation: {max_occupation}

mapping:
  kind: jordan_wigner

backend:
  kind: statevector

solver:
  kind: exact

benchmark:
  enabled: true

run:
  output_dir: artifacts/test_h2_cavity_config
  overwrite: true
        """.strip(),
        encoding="utf-8",
    )


def test_load_run_spec_parses_cavity_qed_config(tmp_path: Path) -> None:
    config = tmp_path / "cavity.yaml"
    _write_cavity_config(config, coupling=0.07, max_occupation=2)

    spec = load_run_spec(config)

    assert spec.problem.cavity_qed.enabled is True
    assert spec.problem.cavity_qed.model == "pauli_fierz_cavity_qed"
    assert spec.problem.cavity_qed.photon_encoding == "linear"
    assert spec.problem.cavity_qed.include_dipole_self_energy is True
    assert spec.problem.cavity_qed.photon_physical_subspace_penalty == pytest.approx(25.0)
    assert len(spec.problem.cavity_qed.modes) == 1
    mode = spec.problem.cavity_qed.modes[0]
    assert mode.frequency == pytest.approx(0.4)
    assert mode.coupling_strength == pytest.approx(0.07)
    assert mode.polarization == [0.0, 0.0, 1.0]
    assert mode.max_occupation == 2


def test_cavity_qed_rejects_invalid_polarization(tmp_path: Path) -> None:
    config = tmp_path / "bad_cavity.yaml"
    _write_cavity_config(config)
    text = config.read_text(encoding="utf-8").replace(
        "polarization: [0.0, 0.0, 1.0]",
        "polarization: [0.0, 0.0, 0.0]",
    )
    config.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match="problem.cavity_qed.modes.0.polarization"):
        load_run_spec(config)


def test_cavity_qed_rejects_negative_photon_cutoff(tmp_path: Path) -> None:
    config = tmp_path / "bad_cutoff.yaml"
    _write_cavity_config(config, max_occupation=-1)

    with pytest.raises(ValueError, match="problem.cavity_qed.modes.0.max_occupation"):
        load_run_spec(config)
