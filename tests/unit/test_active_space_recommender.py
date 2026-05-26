from __future__ import annotations

import pytest

from qcchem.chem.active_space_recommender import (
    OrbitalDiagnostics,
    recommend_trusted_active_space,
)
from qcchem.core import AutoActiveSpaceSpec


def test_trusted_recommender_prefers_fractional_natural_occupations() -> None:
    diagnostics = OrbitalDiagnostics(
        orbital_energies=[-1.1, -0.45, -0.03, 0.02, 0.5, 0.9],
        scf_occupations=[2.0, 2.0, 2.0, 0.0, 0.0, 0.0],
        natural_occupations=[1.999, 1.96, 1.30, 0.70, 0.04, 0.001],
        natural_occupation_source="mp2",
        fallback_reasons=[],
    )
    auto = AutoActiveSpaceSpec(
        enabled=True,
        strategy="trusted_orbital_score",
        min_spatial_orbitals=2,
        max_spatial_orbitals=4,
        max_qubits=8,
        energy_window_hartree=0.12,
        occupation_tolerance=0.08,
        max_candidates=6,
    )

    result = recommend_trusted_active_space(
        diagnostics,
        auto,
        num_particles=(3, 3),
        available_original=[0, 1, 2, 3, 4, 5],
    )

    assert result.selected_current == [2, 3]
    assert result.selected_original == [2, 3]
    assert result.num_electrons == (1, 1)
    assert result.recommendation["strategy"] == "trusted_orbital_score"
    assert result.recommendation["confidence"] >= 0.65
    assert result.recommendation["selected"]["active_orbitals_original"] == [2, 3]
    assert result.recommendation["candidates"][0]["active_orbitals_original"] == [2, 3]


def test_trusted_recommender_records_resource_rejections() -> None:
    diagnostics = OrbitalDiagnostics(
        orbital_energies=[-1.0, -0.2, -0.01, 0.01, 0.02, 0.03],
        scf_occupations=[2.0, 2.0, 2.0, 0.0, 0.0, 0.0],
        natural_occupations=None,
        natural_occupation_source="none",
        fallback_reasons=["natural occupations disabled"],
    )
    auto = AutoActiveSpaceSpec(
        enabled=True,
        strategy="trusted_orbital_score",
        min_spatial_orbitals=2,
        max_spatial_orbitals=5,
        max_qubits=4,
        energy_window_hartree=0.05,
        max_candidates=5,
    )

    result = recommend_trusted_active_space(
        diagnostics,
        auto,
        num_particles=(3, 3),
        available_original=[0, 1, 2, 3, 4, 5],
    )

    assert result.selected_current == [2, 3]
    assert result.recommendation["selected"]["num_qubits"] == 4
    assert any(
        rejected["reason"] == "exceeds_max_qubits"
        for rejected in result.recommendation["rejected_candidates"]
    )
    assert "natural occupations disabled" in result.recommendation["warnings"]


def test_trusted_recommender_rejects_impossible_qubit_budget() -> None:
    diagnostics = OrbitalDiagnostics(
        orbital_energies=[-0.5, 0.1],
        scf_occupations=[2.0, 0.0],
        natural_occupations=None,
        natural_occupation_source="none",
        fallback_reasons=[],
    )
    auto = AutoActiveSpaceSpec(
        enabled=True,
        strategy="trusted_orbital_score",
        min_spatial_orbitals=2,
        max_spatial_orbitals=2,
        max_qubits=2,
    )

    with pytest.raises(ValueError, match="max_qubits"):
        recommend_trusted_active_space(
            diagnostics,
            auto,
            num_particles=(1, 1),
            available_original=[0, 1],
        )
