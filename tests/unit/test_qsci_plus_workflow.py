from types import SimpleNamespace

import numpy as np
import pytest
from qiskit.quantum_info import Operator, SparsePauliOp

from qcchem.exploratory.qsci.workflow import run_qsci_plus


def test_qsci_plus_reports_embedded_ritz_variance_and_residuals() -> None:
    operator = SparsePauliOp.from_list(
        [
            ("IIII", -0.2),
            ("ZIII", 0.3),
            ("IZII", -0.1),
            ("IIZI", 0.2),
            ("IIIZ", -0.4),
        ]
    )
    matrix = np.asarray(operator.to_matrix(), dtype=complex)
    exact_energy = float(np.linalg.eigvalsh(matrix)[0])
    spec = SimpleNamespace(
        mapping=SimpleNamespace(kind="jordan_wigner"),
        run=SimpleNamespace(seed=11),
        qsci=SimpleNamespace(
            enabled=True,
            sampler="local_energy_proxy",
            shots=512,
            max_determinants=4,
            min_probability=0.0,
            excited_roots=1,
            determinant_repair=SimpleNamespace(
                enforce_particle_number=True,
                enforce_spin_sector=True,
                hamming_expansion=1,
            ),
            classical_diagonalizer=SimpleNamespace(
                method="dense_exact",
                max_subspace_size=4,
            ),
        ),
    )
    chemistry = SimpleNamespace(
        summary=SimpleNamespace(
            num_spatial_orbitals=2,
            num_particles=(1, 1),
        )
    )
    physical_mapping = SimpleNamespace(qubit_hamiltonian=operator)

    payload = run_qsci_plus(
        spec=spec,
        chemistry=chemistry,
        physical_mapping=physical_mapping,
        exact_solver_energy=exact_energy,
    )

    assert payload is not None
    audit = payload["subspace_audit"]
    assert payload["selected_subspace_size"] == 4
    assert audit["variance_method"] == "embedded_ritz_vector_sparse_hamiltonian"
    assert audit["selected_sector_coverage_fraction"] == pytest.approx(1.0)
    assert payload["variance_estimate"] == pytest.approx(audit["ground_state_variance"])
    assert audit["ground_state_residual_norm"] == pytest.approx(0.0, abs=1.0e-12)
    assert audit["ground_state_external_coupling_residual_norm"] == pytest.approx(0.0, abs=1.0e-12)
    assert audit["variational_upper_bound_passed"] is True
    assert payload["variational_upper_bound"] is True
    assert audit["root_residuals"]
    selection_audit = payload["selection_bias_audit"]
    assert selection_audit["selected_origin_counts"] == {"sampled": 4}
    assert selection_audit["selected_multi_origin_counts"]["sampled"] == 4
    assert selection_audit["selected_multi_origin_counts"]["sector_repaired"] == 4
    assert selection_audit["hartree_fock_selected"] is True
    assert all("selection_origins" in item for item in payload["repaired_determinants"])


def test_qsci_plus_tracks_hartree_fock_and_hamming_repair_origins() -> None:
    operator = SparsePauliOp.from_list(
        [
            ("IIII", -0.2),
            ("ZIII", 0.3),
            ("IZII", -0.1),
            ("IIZI", 0.2),
            ("IIIZ", -0.4),
        ]
    )
    matrix = np.asarray(operator.to_matrix(), dtype=complex)
    exact_energy = float(np.linalg.eigvalsh(matrix)[0])
    spec = SimpleNamespace(
        mapping=SimpleNamespace(kind="jordan_wigner"),
        run=SimpleNamespace(seed=1),
        qsci=SimpleNamespace(
            enabled=True,
            sampler="local_energy_proxy",
            shots=1,
            max_determinants=4,
            min_probability=0.0,
            excited_roots=1,
            determinant_repair=SimpleNamespace(
                enforce_particle_number=True,
                enforce_spin_sector=True,
                hamming_expansion=2,
            ),
            classical_diagonalizer=SimpleNamespace(
                method="dense_exact",
                max_subspace_size=4,
            ),
        ),
    )
    chemistry = SimpleNamespace(
        summary=SimpleNamespace(
            num_spatial_orbitals=2,
            num_particles=(1, 1),
        )
    )
    physical_mapping = SimpleNamespace(qubit_hamiltonian=operator)

    payload = run_qsci_plus(
        spec=spec,
        chemistry=chemistry,
        physical_mapping=physical_mapping,
        exact_solver_energy=exact_energy,
    )

    assert payload is not None
    selection_audit = payload["selection_bias_audit"]
    assert selection_audit["selected_origin_counts"] == {
        "hamming_expanded": 2,
        "hartree_fock_reference": 1,
        "sampled": 1,
    }
    assert selection_audit["selected_multi_origin_counts"]["hamming_expanded"] == 2
    assert selection_audit["hartree_fock_selected"] is True
    origin_by_bitstring = {
        item["bitstring"]: item["selection_origins"]
        for item in payload["repaired_determinants"]
    }
    assert origin_by_bitstring["0101"] == ["hartree_fock_reference"]
    assert origin_by_bitstring["0110"] == ["hamming_expanded"]
    assert origin_by_bitstring["1001"] == ["hamming_expanded"]


def test_qsci_plus_residual_expansion_adds_externally_coupled_determinants() -> None:
    matrix = np.eye(16, dtype=complex) * 5.0
    for determinant, energy in {5: -1.0, 6: -0.85, 9: -0.75, 10: -0.65}.items():
        matrix[determinant, determinant] = energy
    matrix[5, 6] = matrix[6, 5] = -0.2
    matrix[6, 9] = matrix[9, 6] = -0.1
    operator = SparsePauliOp.from_operator(Operator(matrix)).simplify(atol=1.0e-12)
    exact_energy = float(np.linalg.eigvalsh(matrix)[0])
    chemistry = SimpleNamespace(
        summary=SimpleNamespace(
            num_spatial_orbitals=2,
            num_particles=(1, 1),
        )
    )
    physical_mapping = SimpleNamespace(qubit_hamiltonian=operator)

    def _spec(*, residual_expansion) -> SimpleNamespace:
        return SimpleNamespace(
            mapping=SimpleNamespace(kind="jordan_wigner"),
            run=SimpleNamespace(seed=7),
            qsci=SimpleNamespace(
                enabled=True,
                sampler="local_energy_proxy",
                shots=1024,
                max_determinants=1,
                min_probability=0.0,
                excited_roots=0,
                determinant_repair=SimpleNamespace(
                    enforce_particle_number=True,
                    enforce_spin_sector=True,
                    hamming_expansion=0,
                ),
                classical_diagonalizer=SimpleNamespace(
                    method="dense_exact",
                    max_subspace_size=4,
                ),
                residual_expansion=residual_expansion,
            ),
        )

    baseline = run_qsci_plus(
        spec=_spec(residual_expansion=SimpleNamespace(enabled=False)),
        chemistry=chemistry,
        physical_mapping=physical_mapping,
        exact_solver_energy=exact_energy,
    )
    expanded = run_qsci_plus(
        spec=_spec(
            residual_expansion=SimpleNamespace(
                enabled=True,
                scorer="external_residual_coupling",
                max_iterations=2,
                batch_size=1,
                max_additional_determinants=2,
                target_residual_norm=1.0e-12,
            )
        ),
        chemistry=chemistry,
        physical_mapping=physical_mapping,
        exact_solver_energy=exact_energy,
    )

    assert baseline is not None
    assert expanded is not None
    baseline_residual = baseline["subspace_audit"]["ground_state_external_coupling_residual_norm"]
    expanded_residual = expanded["subspace_audit"]["ground_state_external_coupling_residual_norm"]
    baseline_error = abs(baseline["subspace_audit"]["variational_upper_bound_margin_hartree"])
    expanded_error = abs(expanded["subspace_audit"]["variational_upper_bound_margin_hartree"])

    assert expanded["selected_subspace_size"] > baseline["selected_subspace_size"]
    assert expanded_residual < baseline_residual
    assert expanded_error < baseline_error
    selection_audit = expanded["selection_bias_audit"]
    residual_audit = selection_audit["residual_expansion"]
    assert residual_audit["enabled"] is True
    assert residual_audit["added_determinant_count"] >= 1
    assert selection_audit["selected_multi_origin_counts"]["residual_expanded"] >= 1
