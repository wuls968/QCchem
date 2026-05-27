from __future__ import annotations

import copy
from pathlib import Path

import numpy as np

from qcchem.io.config import load_run_spec
from qcchem.qft.lattice_qed import build_lattice_qed_context

REPO_ROOT = Path(__file__).resolve().parents[2]


def _contexts(config_name: str):
    spec = load_run_spec(REPO_ROOT / "configs" / "exploratory" / config_name)
    sector_first = copy.deepcopy(spec.problem.qft)
    sector_first.engine.projected_builder = "sector_first"
    legacy = copy.deepcopy(spec.problem.qft)
    legacy.engine.projected_builder = "legacy_full_project"
    return (
        build_lattice_qed_context(
            spec.molecule,
            sector_first,
            mapping_kind=spec.mapping.kind,
            materialize_pauli=False,
        ),
        build_lattice_qed_context(
            spec.molecule,
            legacy,
            mapping_kind=spec.mapping.kind,
            materialize_pauli=False,
        ),
    )


def test_sector_first_projected_builder_matches_legacy_four_site_oracle() -> None:
    sector_first, legacy = _contexts("h2_4site_lattice_qed_sparse_exact.yaml")

    assert sector_first.summary.engine["build_mode"] == "sector_first_projected"
    assert legacy.summary.engine["build_mode"] == "legacy_full_project"
    assert sector_first.summary.physical_sector["basis_hash"] == legacy.summary.physical_sector["basis_hash"]
    assert sector_first.summary.engine["projected_dimension"] == legacy.summary.engine["projected_dimension"]
    assert sector_first.summary.engine["peak_matrix_dimension"] < legacy.summary.engine["peak_matrix_dimension"]

    left = sector_first.sparse_bundle.projected_hamiltonian.toarray()
    right = legacy.sparse_bundle.projected_hamiltonian.toarray()
    assert np.allclose(left, right, atol=1.0e-10)


def test_sector_first_projected_builder_matches_legacy_plaquette_oracle() -> None:
    sector_first, legacy = _contexts("h2_2d_lattice_qed_projected_exact.yaml")

    assert sector_first.summary.engine["build_mode"] == "sector_first_projected"
    assert sector_first.summary.plaquette_count > 0
    assert sector_first.summary.physical_sector["basis_hash"] == legacy.summary.physical_sector["basis_hash"]

    left = sector_first.sparse_bundle.projected_hamiltonian.toarray()
    right = legacy.sparse_bundle.projected_hamiltonian.toarray()
    assert np.allclose(left, right, atol=1.0e-10)
