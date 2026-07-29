from qiskit.quantum_info import SparsePauliOp

from qcchem.backends.measurement import plan_measurement
from qcchem.core import MappingSummary, MeasurementSpec
from qcchem.mapping import MappedHamiltonian


def _toy_mapping() -> MappedHamiltonian:
    operator = SparsePauliOp.from_list(
        [
            ("ZZ", 1.0),
            ("ZX", 0.25),
            ("XZ", 0.25),
            ("XX", 0.125),
        ]
    )
    return MappedHamiltonian(
        fermionic_hamiltonian=object(),
        qubit_hamiltonian=operator,
        mapper=object(),
        summary=MappingSummary(
            kind="unit_test",
            num_qubits=2,
            fermionic_term_count=4,
            qubit_term_count=4,
        ),
        raw_qubit_hamiltonian=operator,
        base_mapper=object(),
    )


def test_shadow_lr_measurement_cost_uses_allocated_budgeted_shots() -> None:
    mapping = _toy_mapping()
    measurement = plan_measurement(
        measurement_spec=MeasurementSpec(
            planner="shadow_lr",
            total_shots=17,
            max_circuits=4,
            strategies=["low_rank_grouping", "locally_biased_shadows"],
        ),
        executed_mapping=mapping,
        uncompressed_mapping=mapping,
        compression_result=None,
        backend_precision=None,
        backend_shots=None,
    )

    allocated = sum(int(item["shots"]) for item in measurement.shot_allocation)
    assert allocated == 17
    assert measurement.estimated_shot_cost == 17.0
    assert measurement.uncompressed_estimated_shot_cost == 40000.0
    assert measurement.cost_reduction_ratio == 17.0 / 40000.0
    assert measurement.measurement_cost_model["budgeted_shots"] == 17
    assert measurement.measurement_cost_model["allocated_shots"] == 17
    assert measurement.measurement_cost_model["grouped_precision_baseline_shots"] == 40000.0
    assert measurement.measurement_cost_model["basis_l1_coverage_fraction"] == 1.0
    assert measurement.measurement_cost_model["unselected_basis_count"] == 0
    assert len(measurement.measurement_cost_model["plan_digest"]) == 64
    assert measurement.measurement_cost_model[
        "variance_inflation_vs_grouped_precision_proxy"
    ] == 40000.0 / 17.0
    assert all(int(item["shots"]) >= 1 for item in measurement.shot_allocation)


def test_shadow_lr_measurement_records_truncated_basis_audit() -> None:
    mapping = _toy_mapping()
    measurement = plan_measurement(
        measurement_spec=MeasurementSpec(
            planner="shadow_lr",
            total_shots=10,
            max_circuits=2,
            strategies=["low_rank_grouping", "locally_biased_shadows"],
        ),
        executed_mapping=mapping,
        uncompressed_mapping=mapping,
        compression_result=None,
        backend_precision=None,
        backend_shots=None,
    )

    assert len(measurement.shadow_bases) == 2
    assert [item["shots"] for item in measurement.shot_allocation] == [7, 3]
    assert measurement.measurement_cost_model["basis_count"] == 4
    assert measurement.measurement_cost_model["selected_basis_count"] == 2
    assert measurement.measurement_cost_model["unselected_basis_count"] == 2
    assert measurement.measurement_cost_model[
        "basis_l1_coverage_fraction"
    ] == 1.25 / 1.625
    assert measurement.measurement_cost_model["max_allocated_shot_fraction"] == 0.7
    assert 0.0 < measurement.measurement_cost_model["allocation_entropy"] < 1.0
