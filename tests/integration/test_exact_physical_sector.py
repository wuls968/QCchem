"""Independent chemistry checks against PySCF FCI, not a shared QCchem baseline."""
from pathlib import Path

import numpy as np
import pytest
from pyscf import fci, gto, scf

from qcchem.chem.problem_builder import build_electronic_structure_context
from qcchem.io.config import load_run_spec
from qcchem.mapping.mapper import map_fermionic_hamiltonian
from qcchem.solvers.sector import molecular_sector
from qcchem.solvers.spectrum import compute_exact_spectrum
from qcchem.workflow.runner import run_spec


@pytest.mark.parametrize("charge,multiplicity", [(1, 2), (0, 1), (0, 3)])
@pytest.mark.parametrize("kind,taper", [
    ("jordan_wigner", "disabled"), ("bravyi_kitaev", "disabled"),
    ("parity_two_qubit_reduction", "disabled"), ("jordan_wigner", "auto"),
])
def test_exact_sector_matches_independent_fci(charge, multiplicity, kind, taper):
    spec = load_run_spec(Path("configs/h2_exact.yaml"))
    spec.molecule.charge = charge
    spec.molecule.multiplicity = multiplicity
    context = build_electronic_structure_context(spec)
    mapping = map_fermionic_hamiltonian(
        context.fermionic_hamiltonian, kind, num_particles=context.summary.num_particles,
        problem=context.problem, symmetry_reduction={"z2": taper, "strict": True},
    )
    sector = molecular_sector(context.summary, mapping.mapper)
    spectrum = compute_exact_spectrum(mapping.qubit_hamiltonian, 3, sector=sector)
    mol = gto.M(atom=spec.molecule.geometry_string(), basis=spec.molecule.basis,
                charge=charge, spin=multiplicity - 1, unit=spec.molecule.unit, verbose=0)
    mean_field = scf.RHF(mol) if multiplicity == 1 else scf.UHF(mol)
    mean_field.kernel()
    independent_total, _ = fci.FCI(mean_field).kernel()
    assert spectrum.eigenvalues[0] + context.total_constant_correction == pytest.approx(independent_total, abs=1e-8)
    assert spectrum.sector["num_particles"] == list(context.summary.num_particles)
    for column in spectrum.eigenvectors.T:
        for number_op, particles in zip(sector.number_operators, sector.num_particles):
            assert np.vdot(column, number_op.to_matrix() @ column).real == pytest.approx(particles, abs=1e-8)
        spin = (multiplicity - 1) / 2
        assert np.vdot(column, sector.spin_squared.to_matrix() @ column).real == pytest.approx(spin * (spin + 1), abs=1e-8)


def test_charged_pipeline_cannot_validate_neutral_energy(tmp_path):
    spec = load_run_spec(Path("configs/h2_exact.yaml"))
    spec.molecule.charge, spec.molecule.multiplicity = 1, 2
    result = run_spec(spec, source_config="charged-sector-regression", output_dir=tmp_path / "h2plus")
    assert result.energy.total_energy == pytest.approx(-0.536370078554, abs=1e-8)
    assert result.exact_baseline.sector["num_particles"] == [1, 0]
    assert result.exact_baseline.sector["multiplicity"] == 2
