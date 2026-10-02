from __future__ import annotations

from copy import deepcopy

import pytest
import numpy as np
from qiskit.quantum_info import SparsePauliOp

from qcchem.backends import ShotEstimatorBackend, StatevectorBackend
from qcchem.core import AnsatzSpec, BackendSpec, OptimizerSpec, SolverSpec
from qcchem.io.checkpoint import read_checkpoint, write_checkpoint
from qcchem.solvers.vqe import VQESolver
from qcchem.solvers.vqe_checkpoint import SCHEMA


class CountingStatevector(StatevectorBackend):
    def __init__(self, spec):
        super().__init__(spec)
        self.calls = 0

    def evaluate(self, *args):
        self.calls += 1
        return super().evaluate(*args)


class CountingShots(ShotEstimatorBackend):
    def __init__(self, spec, *, interrupt_at=None):
        super().__init__(spec)
        self.calls = 0
        self.interrupt_at = interrupt_at

    def evaluate(self, *args):
        self.calls += 1
        if self.calls == self.interrupt_at:
            raise KeyboardInterrupt
        return super().evaluate(*args)


OPERATOR = SparsePauliOp.from_list([("Z", 1.0), ("X", 0.4)])


def solver_spec(method="COBYLA"):
    return SolverSpec(
        optimizer=OptimizerSpec(kind=method, maxiter=50),
        ansatz=AnsatzSpec(rotation_blocks=["ry"], reps=1, skip_final_rotation_layer=True),
        initial_point="random",
    )


@pytest.mark.parametrize("method", ["COBYLA", "SLSQP", "BFGS", "L-BFGS-B", "Nelder-Mead", "Powell", "CG", "COBYQA", "TNC", "trust-constr"])
def test_resume_reconstructs_optimizer_without_repeating_estimates(tmp_path, method):
    if method == "COBYQA":
        from scipy.optimize._minimize import MINIMIZE_METHODS

        if "cobyqa" not in MINIMIZE_METHODS:
            pytest.skip("This installed SciPy does not provide COBYQA (requires SciPy 1.14+).")
    spec = solver_spec(method)
    options = BackendSpec(seed=71)
    full_backend = CountingStatevector(options)
    full = VQESolver(spec, full_backend, 7).solve(OPERATOR)
    old = tmp_path / "old.json"
    partial_backend = CountingStatevector(options)

    def cancel():
        if partial_backend.calls >= 3:
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        VQESolver(spec, partial_backend, 7, checkpoint_path=old, control_check=cancel).solve(OPERATOR)
    original_bytes = old.read_bytes()
    resumed_backend = CountingStatevector(options)
    resumed = VQESolver(spec, resumed_backend, 7, checkpoint_path=tmp_path / "new.json", resume_checkpoint=old).solve(OPERATOR)
    assert resumed.metadata["evaluation_trajectory"] == full.metadata["evaluation_trajectory"]
    assert resumed.optimal_parameters == full.optimal_parameters
    assert resumed.total_energy == full.total_energy
    assert resumed.iterations == full.iterations
    assert resumed.evaluations == full.evaluations == partial_backend.calls + resumed_backend.calls
    assert old.read_bytes() == original_bytes
    assert resumed.metadata["initial_point_provenance"]["checkpoint_recovery"]["replayed_evaluations"] == 3


def test_legacy_cobyla_defers_callback_failure_without_extra_estimates(tmp_path, monkeypatch):
    import qcchem.solvers.vqe as module

    monkeypatch.setattr(module, "scipy_version", "1.13.1")
    backend = CountingStatevector(BackendSpec(seed=71))
    path = tmp_path / "interrupted.json"
    failure = KeyboardInterrupt("cooperative cancellation")

    def cancel():
        if backend.calls == 3:
            raise failure

    with pytest.raises(KeyboardInterrupt) as caught:
        VQESolver(solver_spec(), backend, 7, checkpoint_path=path, control_check=cancel).solve(OPERATOR)
    assert caught.value is failure
    assert backend.calls == 3
    state = read_checkpoint(path, schema=SCHEMA)
    assert state["status"] == "interrupted"
    assert len(state["evaluation_trajectory"]) == 3
    assert "outcome" not in state


@pytest.mark.parametrize("method", ["COBYLA", "SLSQP"])
def test_seeded_shot_resume_preserves_every_seed_and_estimate(tmp_path, method):
    options = BackendSpec(kind="shot_estimator", seed=81, shots=512)
    spec = solver_spec(method)
    full = VQESolver(spec, CountingShots(options), 7).solve(OPERATOR)
    old = tmp_path / "old.json"
    backend = CountingShots(options)

    def cancel():
        if backend.calls >= 3:
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        VQESolver(spec, backend, 7, checkpoint_path=old, control_check=cancel).solve(OPERATOR)
    new_backend = CountingShots(options)
    resumed = VQESolver(spec, new_backend, 7, checkpoint_path=tmp_path / "new.json", resume_checkpoint=old).solve(OPERATOR)
    assert resumed.metadata["evaluation_trajectory"] == full.metadata["evaluation_trajectory"]
    assert [item["seed"] for item in resumed.metadata["evaluation_trajectory"]] == list(range(81, 81 + full.evaluations))
    assert all(item["shots"] == 512 for item in resumed.metadata["evaluation_trajectory"])
    assert backend.calls + new_backend.calls == full.evaluations


def test_pending_local_evaluation_is_retried_with_original_seed(tmp_path):
    spec = solver_spec()
    options = BackendSpec(kind="shot_estimator", seed=12, shots=256)
    full = VQESolver(spec, CountingShots(options), 7).solve(OPERATOR)
    old = tmp_path / "old.json"
    with pytest.raises(KeyboardInterrupt):
        VQESolver(spec, CountingShots(options, interrupt_at=4), 7, checkpoint_path=old).solve(OPERATOR)
    state = read_checkpoint(old, schema=SCHEMA)
    assert len(state["evaluation_trajectory"]) == 3
    assert state["pending_evaluation"]["evaluation_index"] == 4
    resumed = VQESolver(spec, CountingShots(options), 7, checkpoint_path=tmp_path / "new.json", resume_checkpoint=old).solve(OPERATOR)
    assert resumed.metadata["evaluation_trajectory"] == full.metadata["evaluation_trajectory"]


@pytest.mark.parametrize("change", ["budget", "seed", "operator", "circuit", "corruption", "replay"])
def test_changed_checkpoint_is_rejected_before_new_estimates(tmp_path, change):
    old = tmp_path / "old.json"
    spec = solver_spec()
    options = BackendSpec(seed=71)
    backend = CountingStatevector(options)

    def cancel():
        if backend.calls >= 3:
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        VQESolver(spec, backend, 7, checkpoint_path=old, control_check=cancel).solve(OPERATOR)
    spec = deepcopy(spec)
    operator = OPERATOR
    seed = 7
    if change == "budget":
        spec.optimizer.maxiter += 1
    elif change == "seed":
        seed += 1
    elif change == "operator":
        operator = SparsePauliOp.from_list([("Z", 1.1)])
    elif change == "circuit":
        spec.ansatz.reps += 1
    elif change == "corruption":
        old.write_text(old.read_text().replace('"energy":', '"other_energy":'))
    else:
        state = read_checkpoint(old, schema=SCHEMA)
        state["evaluation_trajectory"][1]["parameters"][0] += 0.01
        write_checkpoint(old, state)
    new_backend = CountingStatevector(options)
    with pytest.raises(ValueError):
        VQESolver(spec, new_backend, seed, checkpoint_path=tmp_path / "new.json", resume_checkpoint=old).solve(operator)
    assert new_backend.calls == 0


def test_completed_optimizer_checkpoint_uses_no_backend_calls(tmp_path):
    old = tmp_path / "old.json"
    options = BackendSpec(seed=9)
    full = VQESolver(solver_spec(), CountingStatevector(options), 7, checkpoint_path=old).solve(OPERATOR)
    backend = CountingStatevector(options)
    result = VQESolver(solver_spec(), backend, 7, checkpoint_path=tmp_path / "new.json", resume_checkpoint=old).solve(OPERATOR)
    assert backend.calls == 0
    assert result.evaluations == full.evaluations
    assert result.total_energy == full.total_energy


def test_unseeded_shot_recovery_is_rejected(tmp_path):
    old = tmp_path / "old.json"
    options = BackendSpec(kind="shot_estimator", shots=128)
    VQESolver(solver_spec(), CountingShots(options), 7, checkpoint_path=old).solve(OPERATOR)
    with pytest.raises(ValueError, match="backend.seed"):
        VQESolver(solver_spec(), CountingShots(options), 7, checkpoint_path=tmp_path / "new.json", resume_checkpoint=old).solve(OPERATOR)


@pytest.mark.parametrize("difference", [2.0e-16, 1.0e-10])
def test_hamiltonian_roundoff_is_bounded_and_original_coefficients_reused(tmp_path, difference):
    old = tmp_path / "old.json"
    spec = solver_spec()
    options = BackendSpec(seed=7)
    full = VQESolver(spec, CountingStatevector(options), 7, checkpoint_path=old).solve(OPERATOR)
    changed = OPERATOR.copy()
    changed.coeffs[0] += difference
    backend = CountingStatevector(options)
    solver = VQESolver(spec, backend, 7, checkpoint_path=tmp_path / "new.json", resume_checkpoint=old)
    if difference > 1.0e-12:
        with pytest.raises(ValueError, match="roundoff bound"):
            solver.solve(changed)
    else:
        resumed = solver.solve(changed)
        assert resumed.total_energy == full.total_energy
        assert np.array_equal(resumed.metadata["checkpoint_operator"].coeffs, OPERATOR.coeffs)
        assert resumed.metadata["initial_point_provenance"]["checkpoint_recovery"]["hamiltonian_roundoff_l1_hartree"] <= 1e-12
    assert backend.calls == 0
