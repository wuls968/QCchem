"""Missing backend uncertainty must not become a fabricated error bar."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from qcchem.backends.base import BackendEstimate
from qcchem.backends.cudaq_adapter import _observe_std
from qcchem.io.serialization import to_primitive
from qcchem.workflow.runner import _build_sampled_result
from qcchem.solvers.vqe_checkpoint import SCHEMA, VQECheckpoint
from qcchem.io.checkpoint import read_checkpoint
from qiskit.quantum_info import SparsePauliOp


def _summary(values, stds):
    estimates = [BackendEstimate(value=value, reported_std=std, shots=4096)
                 for value, std in zip(values, stds, strict=True)]
    backend = SimpleNamespace(backend_kind="cudaq_sample", spec=SimpleNamespace(seed=7),
                              sample_repeated=lambda *args: estimates)
    outcome = SimpleNamespace(metadata={"ansatz_circuit": object()}, optimal_parameters=np.array([]))
    return _build_sampled_result(
        backend=backend, solver_kind="vqe", solver_outcome=outcome, operator=object(),
        constant_energy_correction=1.0, nuclear_repulsion_energy=2.0,
        external_point_charge_nuclear_interaction_energy=3.0, boundary_embedding_constant_energy=4.0,
    )


def test_cudaq_absent_uncertainty_depends_on_sampling_mode():
    assert _observe_std(object(), shots=4096) is None
    assert _observe_std(object(), shots=None) == 0.0


@pytest.mark.parametrize("name,value", [("standard_deviation", -1), ("std", np.nan),
                                       ("variance", -0.1), ("variance", np.inf)])
def test_cudaq_rejects_invalid_reported_uncertainty(name, value):
    with pytest.raises(ValueError, match="uncertainty"):
        _observe_std(SimpleNamespace(**{name: lambda: value}), shots=1024)


def test_cudaq_retains_explicit_backend_variance():
    assert _observe_std(SimpleNamespace(variance=lambda: 0.25), shots=1024) == 0.5


def test_one_unknown_sampling_uncertainty_has_no_confidence_interval():
    result = _summary([-5.0], [None])
    assert result.sampled_solver_energy_std is None
    assert result.standard_error is None
    assert result.confidence_interval_low is None
    assert result.confidence_interval_high is None
    assert to_primitive(result)["repeat_reported_stds"] == [None]
    assert result.sampled_total_energy_mean == 5.0


def test_repeated_samples_estimate_mean_error_without_backend_error_bars():
    result = _summary([-4.0, -6.0, -5.0], [None, None, None])
    assert result.sampled_solver_energy_mean == -5.0
    assert result.sampled_solver_energy_std == pytest.approx(1.0)
    assert result.standard_error == pytest.approx(1.0 / np.sqrt(3))
    assert result.confidence_interval_low == pytest.approx(-5.0 - 1.96 / np.sqrt(3))
    assert result.repeat_reported_stds == [None, None, None]
    assert result.sampled_total_energy_mean == 5.0


def test_one_backend_reported_error_is_preserved():
    result = _summary([-5.0], [0.125])
    assert result.sampled_solver_energy_std is None
    assert result.standard_error == 0.125
    assert result.confidence_interval_high == pytest.approx(-5.0 + 1.96 * 0.125)


def test_vqe_journal_retains_missing_uncertainty(tmp_path):
    path = tmp_path / "vqe_checkpoint.json"
    checkpoint = VQECheckpoint(path=path, source=None, signature="test", backend=object(),
                               operator=SparsePauliOp.from_list([("Z", 1.0)]),
                               initial_point=np.array([0.5]), provenance={}, control_check=None)
    assert checkpoint.evaluate(np.array([0.5]), lambda: BackendEstimate(value=-1.0, reported_std=None)) == -1.0
    state = read_checkpoint(path, schema=SCHEMA)
    assert state["evaluation_trajectory"][0]["reported_std"] is None
    checkpoint._validate(state, 1)
