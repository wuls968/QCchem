from __future__ import annotations

import hashlib
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
    cache_enabled: bool = False,
    cache_directory: Path | None = None,
    source_file: Path | None = None,
) -> None:
    active_space_yaml = (
        "{num_electrons: 2, num_spatial_orbitals: 1}" if active_space else "null"
    )
    cut_bonds_yaml = (
        "[{label: H0-MM, qm_atom: 0, mm_atom: 5}]" if boundary else "[]"
    )
    charge_source_yaml = (
        f"      source_file: {source_file}\n"
        if source_file is not None
        else f"""      charges:
        - label: mm
          coords: [0.0, 0.0, 2.0]
          charge: {charge}
"""
    )
    cache_directory_yaml = (
        f"\n      directory: {cache_directory}" if cache_directory is not None else ""
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
{charge_source_yaml.rstrip()}
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
      enabled: {str(cache_enabled).lower()}{cache_directory_yaml}
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
        fingerprints[name] = context.environment_embedding.physics_fingerprint
        assert context.environment_embedding.cache_fingerprint == fingerprints[name]

    assert len(set(fingerprints.values())) == len(fingerprints)


def test_effective_hamiltonian_physics_fingerprint_ignores_cache_directory(
    tmp_path: Path,
) -> None:
    fingerprints = []
    for name in ("cache_a", "cache_b"):
        path = tmp_path / f"{name}.yaml"
        _write_h2_embedding_config(
            path,
            cache_enabled=True,
            cache_directory=tmp_path / name,
        )
        context = build_electronic_structure_context(load_run_spec(path))
        assert context.environment_embedding is not None
        fingerprints.append(context.environment_embedding.physics_fingerprint)
        assert (
            context.environment_embedding.cache_fingerprint
            == context.environment_embedding.physics_fingerprint
        )
        assert context.environment_embedding.provenance["source_file_digests"] == {}
        assert context.environment_embedding.storage_policy["enabled"] is True
        assert context.environment_embedding.storage_policy["cache_directory"] == str(
            tmp_path / name
        )
        assert context.environment_embedding.storage_policy["refresh"] is False
        assert context.environment_embedding.storage_policy["read_through"] is False
        assert context.environment_embedding.storage_policy["skips_recomputation"] is False
        repeat = build_electronic_structure_context(load_run_spec(path))
        assert repeat.environment_embedding is not None
        assert repeat.environment_embedding.cache_hit is True
        assert repeat.environment_embedding.cache_validation["validated"] is True
        assert repeat.environment_embedding.cache_validation["reload_matrix_error"] <= 1.0e-12
        assert (
            repeat.environment_embedding.cache_validation["boundary_reload_matrix_error"]
            <= 1.0e-12
        )

    assert fingerprints[0] == fingerprints[1]


def test_environment_embedding_records_source_file_digest(tmp_path: Path) -> None:
    source_file = tmp_path / "environment.xyzq"
    source_text = "mm 0.0 0.0 2.0 -0.5\n"
    source_file.write_text(source_text, encoding="utf-8")
    config_path = tmp_path / "h2_source_file.yaml"
    _write_h2_embedding_config(config_path, source_file=source_file)

    context = build_electronic_structure_context(load_run_spec(config_path))

    assert context.environment_embedding is not None
    expected_digest = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    source_key = str(source_file)
    assert context.environment_embedding.provenance["source_file_digests"] == {
        source_key: expected_digest
    }
    assert context.external_point_charges is not None
    assert context.external_point_charges.source_file_digests == {
        source_key: expected_digest
    }
    assert context.external_point_charges.provenance["source_file_digests"] == {
        source_key: expected_digest
    }


def test_corrupted_environment_cache_npz_fails_on_second_run(tmp_path: Path) -> None:
    config_path = tmp_path / "h2_cache.yaml"
    _write_h2_embedding_config(
        config_path,
        cache_enabled=True,
        cache_directory=tmp_path / "cache",
    )
    context = build_electronic_structure_context(load_run_spec(config_path))
    assert context.environment_embedding is not None
    matrix_path = Path(context.environment_embedding.cache_paths["matrices_npz"])
    matrix_path.write_bytes(b"not a valid npz")

    with pytest.raises(ValueError, match="cache validation failed"):
        build_electronic_structure_context(load_run_spec(config_path))
