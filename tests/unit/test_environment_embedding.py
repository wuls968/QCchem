from __future__ import annotations

from pathlib import Path

import pytest

from qcchem.chem.problem_builder import build_electronic_structure_context
from qcchem.io.config import load_run_spec


def _write_h2_embedding_config(
    path: Path,
    *,
    charge: float = -0.5,
    radius: float = 0.4,
    active_space: bool = False,
    boundary: bool = False,
) -> None:
    active_space_yaml = (
        "{num_electrons: 2, num_spatial_orbitals: 1}" if active_space else "null"
    )
    cut_bonds_yaml = (
        "[{label: H0-MM, qm_atom: 0, mm_atom: 5}]" if boundary else "[]"
    )
    path.write_text(
        f"""
molecule:
  name: H2-fingerprint
  geometry:
    - symbol: H
      coords: [0.0, 0.0, 0.0]
    - symbol: H
      coords: [0.0, 0.0, 0.735]
  basis: sto3g
problem:
  active_space: {active_space_yaml}
  environment_embedding:
    enabled: true
    point_charges:
      enabled: true
      charges:
        - label: mm
          coords: [0.0, 0.0, 2.0]
          charge: {charge}
      damping:
        kind: gaussian
        default_radius: {radius}
        radius_unit: angstrom
    boundary:
      enabled: {str(boundary).lower()}
      cut_bonds: {cut_bonds_yaml}
      leakage_threshold: 1.0
      strict: false
    cache:
      enabled: false
solver:
  kind: exact
        """.strip(),
        encoding="utf-8",
    )


def test_boundary_embedding_strict_mode_rejects_excessive_leakage(tmp_path: Path) -> None:
    config_path = tmp_path / "h2_boundary_strict.yaml"
    config_path.write_text(
        """
molecule:
  name: H2-boundary
  geometry:
    - symbol: H
      coords: [0.0, 0.0, 0.0]
    - symbol: H
      coords: [0.0, 0.0, 0.735]
  basis: sto3g
problem:
  environment_embedding:
    enabled: true
    point_charges:
      enabled: false
    boundary:
      enabled: true
      cut_bonds:
        - label: H0-MM
          qm_atom: 0
          mm_atom: 5
      leakage_threshold: 0.0
      strict: true
solver:
  kind: exact
        """.strip(),
        encoding="utf-8",
    )
    spec = load_run_spec(config_path)

    with pytest.raises(ValueError, match="Boundary orbital leakage exceeds threshold"):
        build_electronic_structure_context(spec)


def test_effective_hamiltonian_fingerprint_tracks_physics_inputs(tmp_path: Path) -> None:
    configs = {
        "base": {},
        "charge": {"charge": -0.25},
        "radius": {"radius": 0.55},
        "active_space": {"active_space": True},
        "boundary": {"boundary": True},
    }
    fingerprints = {}
    for name, kwargs in configs.items():
        path = tmp_path / f"{name}.yaml"
        _write_h2_embedding_config(path, **kwargs)
        context = build_electronic_structure_context(load_run_spec(path))
        assert context.environment_embedding is not None
        fingerprints[name] = context.environment_embedding.cache_fingerprint

    assert len(set(fingerprints.values())) == len(fingerprints)
