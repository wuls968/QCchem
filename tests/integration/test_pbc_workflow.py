from __future__ import annotations

from pathlib import Path

import pytest
from qiskit_nature.second_q.problems import ElectronicBasis, ElectronicStructureProblem

from qcchem.pbc.pyscf_adapter import GammaCellInput, run_gamma_cell_problem
from qcchem.workflow.runner import run_from_config


def test_gamma_only_pyscf_pbc_adapter_builds_electronic_structure_problem() -> None:
    result = run_gamma_cell_problem(
        GammaCellInput(
            atom="H 0 0 0; H 0 0 1.4",
            lattice_vectors=((8.0, 0.0, 0.0), (0.0, 8.0, 0.0), (0.0, 0.0, 8.0)),
            basis="sto-3g",
            unit="Bohr",
            kpoint_mesh=(1, 1, 1),
            method="rhf",
            density_fit=True,
            density_fitting="fftdf",
            mesh=(7, 7, 7),
            max_cycle=30,
        )
    )

    assert isinstance(result.problem, ElectronicStructureProblem)
    assert result.problem.basis == ElectronicBasis.MO
    assert result.problem.num_spatial_orbitals == 2
    assert result.problem.num_particles == (1, 1)
    assert result.problem.reference_energy == pytest.approx(result.mean_field.e_tot)
    assert result.problem.hamiltonian.constants["nuclear_repulsion_energy"] == pytest.approx(
        result.mean_field.energy_nuc()
    )
    assert len(result.problem.hamiltonian.second_q_op()) > 0
    assert result.metadata["scope"]["non_gamma_policy"] == "rejected"
    assert result.metadata["mapping"]["raw_integrals"] == "ElectronicEnergy.from_raw_integrals"
    assert result.metadata["scf"]["density_fitting"] == "fftdf"
    assert result.metadata["scf"]["mesh"] == [7, 7, 7]


def test_pyscf_pbc_adapter_rejects_non_gamma_kpoint_mesh() -> None:
    with pytest.raises(ValueError, match="Gamma-only"):
        run_gamma_cell_problem(
            GammaCellInput(
                atom="H 0 0 0; H 0 0 1.4",
                lattice_vectors=((8.0, 0.0, 0.0), (0.0, 8.0, 0.0), (0.0, 0.0, 8.0)),
                basis="sto-3g",
                unit="Bohr",
                kpoint_mesh=(2, 1, 1),
            )
        )


def test_pyscf_pbc_adapter_rejects_open_shell_mapping() -> None:
    with pytest.raises(ValueError, match="closed-shell RHF"):
        run_gamma_cell_problem(
            GammaCellInput(
                atom="H 0 0 0",
                lattice_vectors=((8.0, 0.0, 0.0), (0.0, 8.0, 0.0), (0.0, 0.0, 8.0)),
                basis="sto-3g",
                unit="Bohr",
                charge=0,
                spin=1,
                method="uhf",
            )
        )


def _write_pbc_config(path: Path, *, pbc: str, runtime: str = "") -> None:
    path.write_text(
        f"""
molecule:
  name: H2-pbc-guard
  geometry:
    - symbol: H
      coords: [0.0, 0.0, 0.0]
    - symbol: H
      coords: [0.0, 0.0, 0.735]
  charge: 0
  multiplicity: 1
  basis: sto3g
  unit: angstrom
  periodic:
    enabled: true
    cell:
      vectors:
        - [8.0, 0.0, 0.0]
        - [0.0, 8.0, 0.0]
        - [0.0, 0.0, 8.0]
      unit: angstrom
    pbc: {pbc}
problem:
  pbc:
    enabled: true
    kpoint_mesh: [1, 1, 1]
mapping:
  kind: jordan_wigner
backend:
  kind: statevector
{runtime}
solver:
  kind: exact
benchmark:
  enabled: false
        """.strip(),
        encoding="utf-8",
    )


def test_pbc_runner_rejects_mixed_pbc_flags(tmp_path: Path) -> None:
    config = tmp_path / "mixed_pbc.yaml"
    _write_pbc_config(config, pbc="[true, false, true]")

    with pytest.raises(ValueError, match="fully periodic"):
        run_from_config(config, output_dir=tmp_path / "run")


def test_pbc_runner_rejects_runtime_submission(tmp_path: Path) -> None:
    config = tmp_path / "runtime_pbc.yaml"
    _write_pbc_config(
        config,
        pbc="[true, true, true]",
        runtime="""
  runtime:
    enabled: true
""",
    )

    with pytest.raises(ValueError, match="PBC runtime submissions are not supported"):
        run_from_config(config, output_dir=tmp_path / "run")
