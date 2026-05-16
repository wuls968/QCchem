from __future__ import annotations

import pytest

from qcchem.field_models.registry import get_field_model_adapter


def test_field_model_registry_dispatches_lattice_qed_and_cavity_qed() -> None:
    lattice = get_field_model_adapter("lattice_qed")
    cavity = get_field_model_adapter("pauli_fierz_cavity_qed")

    assert lattice.model_kind == "lattice_qed"
    assert cavity.model_kind == "pauli_fierz_cavity_qed"
    assert lattice.capability_tier == "exploratory"
    assert cavity.capability_tier == "exploratory"
    assert "gauss_law" in lattice.observables
    assert "photon_occupation" in cavity.observables


def test_field_model_registry_rejects_unknown_model() -> None:
    with pytest.raises(ValueError, match="Unsupported field model"):
        get_field_model_adapter("not_a_field_model")
