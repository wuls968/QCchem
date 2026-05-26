from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit

from qcchem.backends.runtime_batch import attempt_runtime_batch_submission
from qcchem.core import AtomSpec, BackendSpec, LatticeQEDSpec, MoleculeSpec
from qcchem.qft.dynamics import build_lattice_qed_dynamics, build_trotter_circuit
from qcchem.qft.lattice_qed import build_lattice_qed_context
from qcchem.qft.observables import build_qft_observable_matrices


def _h2_molecule() -> MoleculeSpec:
    return MoleculeSpec(
        name="H2-lattice-qed-dynamics",
        geometry=[
            AtomSpec("H", (0.0, 0.0, 0.0)),
            AtomSpec("H", (0.0, 0.0, 0.74)),
        ],
    )


def _h2_spec() -> LatticeQEDSpec:
    spec = LatticeQEDSpec(enabled=True)
    spec.dimensions = 1
    spec.grid.shape = [2]
    spec.grid.spacing = [0.75]
    spec.grid.softening = 0.35
    spec.matter.spin_components = 2
    spec.matter.target_electrons = "auto"
    spec.gauge.electric_cutoff = 1
    spec.gauge.coupling = 1.0
    spec.constraints.enforce_physical_sector = True
    spec.constraints.target_charge_sector = "neutral"
    spec.constraints.gauss_law_tolerance = 1.0e-8
    spec.constraints.max_sector_enumeration_qubits = 8
    spec.dynamics.enabled = True
    spec.dynamics.initial_state.kind = "local_hopping_pulse"
    spec.dynamics.initial_state.base = "physical_reference"
    spec.dynamics.initial_state.link_index = 0
    spec.dynamics.initial_state.pulse_time = 0.05
    spec.dynamics.time_grid.start = 0.0
    spec.dynamics.time_grid.stop = 2.0
    spec.dynamics.time_grid.num_points = 41
    spec.dynamics.evolution.exact_enabled = True
    spec.dynamics.evolution.exact_qubit_limit = 12
    spec.dynamics.evolution.trotter_enabled = True
    spec.dynamics.evolution.trotter_step = 0.05
    spec.dynamics.runtime.enabled = True
    return spec


def _plaquette_spec() -> LatticeQEDSpec:
    spec = _h2_spec()
    spec.dimensions = 2
    spec.grid.shape = [2, 2]
    spec.grid.spacing = [0.75, 0.75]
    spec.grid.axes = "cartesian"
    spec.matter.spin_components = 1
    spec.constraints.max_sector_enumeration_qubits = 12
    spec.dynamics.evolution.exact_enabled = False
    spec.dynamics.evolution.exact_qubit_limit = 12
    spec.dynamics.evolution.trotter_enabled = False
    return spec


def _dense(matrix):
    return matrix.toarray() if hasattr(matrix, "toarray") else np.asarray(matrix)


def test_local_hopping_pulse_dynamics_preserves_gauss_sector_and_records_41_points() -> None:
    context = build_lattice_qed_context(_h2_molecule(), _h2_spec(), mapping_kind="jordan_wigner")

    dynamics = build_lattice_qed_dynamics(context, _h2_spec(), backend_spec=BackendSpec())

    assert dynamics["enabled"] is True
    assert dynamics["quench"]["kind"] == "local_hopping_pulse"
    assert dynamics["time_grid"]["num_points"] == 41
    assert len(dynamics["exact"]["time_points"]) == 41
    assert max(abs(value - 1.0) for value in dynamics["exact"]["state_norms"]) <= 1.0e-8
    assert max(dynamics["exact"]["observables"]["total_gauss_violation"]) <= 1.0e-8
    assert dynamics["trotter"]["circuit_resources"]["time_point_count"] == 41
    assert dynamics["trotter"]["propagation_mode"] == "incremental_monotonic"
    assert dynamics["trotter_error_summary"]["max_loschmidt_abs_error"] is not None


def test_qft_observable_matrices_are_hermitian_and_plaquette_observables_exist() -> None:
    h2_context = build_lattice_qed_context(_h2_molecule(), _h2_spec(), mapping_kind="jordan_wigner")
    observables = build_qft_observable_matrices(h2_context)

    for name in ("particle_number", "total_electric_energy", "total_gauss_violation"):
        matrix = observables.aggregate[name]
        assert matrix.shape == h2_context.hamiltonian_matrix.shape
        dense = _dense(matrix)
        assert np.allclose(dense, dense.conj().T)

    plaquette_context = build_lattice_qed_context(
        _h2_molecule(),
        _plaquette_spec(),
        mapping_kind="jordan_wigner",
        materialize_pauli=False,
    )
    plaquette_observables = build_qft_observable_matrices(plaquette_context)
    assert plaquette_observables.plaquette_wilson
    assert plaquette_observables.aggregate["total_wilson"].shape == (
        plaquette_context.summary.engine["projected_dimension"],
        plaquette_context.summary.engine["projected_dimension"],
    )


def test_trotter_circuit_exists_for_time_point_and_runtime_batch_disabled_records_preview() -> None:
    context = build_lattice_qed_context(_h2_molecule(), _h2_spec(), mapping_kind="jordan_wigner")
    circuit = build_trotter_circuit(context, _h2_spec(), time=0.2)

    assert isinstance(circuit, QuantumCircuit)
    assert circuit.num_qubits == context.summary.total_qubits
    assert circuit.depth() is not None and circuit.depth() > 0

    backend = BackendSpec()
    backend.runtime.enabled = True
    backend.runtime.options["submit_real_job"] = False
    preview = attempt_runtime_batch_submission(
        spec=backend,
        pubs=[
            {
                "time": 0.0,
                "observable": "particle_number",
                "circuit": circuit,
                "operator": context.qubit_hamiltonian,
                "parameter_values": [],
            }
        ],
    )

    assert preview["attempted"] is True
    assert preview["submitted"] is False
    assert preview["pub_count"] == 1
    assert preview["failure_category"] == "runtime_submission_disabled"


def test_qft_runtime_micro_limits_filter_time_points_and_observables() -> None:
    spec = _h2_spec()
    spec.dynamics.runtime.time_point_indices = [0, 10]
    spec.dynamics.runtime.observable_names = ["particle_number", "total_gauss_violation"]
    spec.dynamics.runtime.max_pub_count = 4
    spec.dynamics.runtime.max_total_pub_shots = 2048
    spec.dynamics.runtime.max_logical_depth = 200
    backend = BackendSpec()
    backend.runtime.enabled = True
    backend.runtime.max_budgeted_shots = 512
    backend.runtime.options["submit_real_job"] = False
    context = build_lattice_qed_context(_h2_molecule(), spec, mapping_kind="jordan_wigner")

    dynamics = build_lattice_qed_dynamics(context, spec, backend_spec=backend)

    runtime_batch = dynamics["runtime_batch"]
    assert runtime_batch["pub_count"] == 4
    assert runtime_batch["failure_category"] == "runtime_submission_disabled"
    assert {item["observable"] for item in runtime_batch["pubs_preview"]} == {
        "particle_number",
        "total_gauss_violation",
    }
    assert [item["time"] for item in runtime_batch["pubs_preview"][::2]] == [0.0, 0.5]


def test_qft_runtime_budget_gate_rejects_too_many_pubs_before_submission() -> None:
    spec = _h2_spec()
    spec.dynamics.runtime.time_point_indices = [0, 10]
    spec.dynamics.runtime.observable_names = ["particle_number", "total_gauss_violation"]
    spec.dynamics.runtime.max_pub_count = 3
    backend = BackendSpec()
    backend.runtime.enabled = True
    backend.runtime.options["submit_real_job"] = True
    backend.runtime.options["runtime_budget_confirmation"] = "I understand IBM Runtime budget"
    context = build_lattice_qed_context(_h2_molecule(), spec, mapping_kind="jordan_wigner")

    dynamics = build_lattice_qed_dynamics(context, spec, backend_spec=backend)

    runtime_batch = dynamics["runtime_batch"]
    assert runtime_batch["submitted"] is False
    assert runtime_batch["failure_category"] == "runtime_budget_exceeded"
    assert runtime_batch["result_provenance"]["attempt_stage"] == "budget_gate"
