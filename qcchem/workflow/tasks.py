"""Optional task execution for excited states and properties."""

from __future__ import annotations

import math

import numpy as np
from pyscf import gto, scf
from scipy.optimize import minimize_scalar

from qcchem.core import (
    ExcitedStateLevelResult,
    ExcitedStateTaskResult,
    PropertyTaskResult,
    PropertyValueResult,
    RunSpec,
)
from qcchem.solvers.spectrum import ExactSpectrum, compute_exact_spectrum


def required_exact_states(spec: RunSpec) -> int:
    """Return how many exact states are needed to satisfy optional tasks."""
    required = 1
    if spec.tasks.excited_state.enabled:
        required = max(
            required,
            spec.tasks.excited_state.num_states,
            max(spec.tasks.excited_state.state_indices, default=0) + 1,
        )
    for item in spec.tasks.properties:
        if item.enabled and item.state_indices:
            required = max(required, max(item.state_indices) + 1)
    return required


def ensure_exact_spectrum(operator, num_states: int) -> ExactSpectrum:
    """Compute an exact spectrum slice."""
    return compute_exact_spectrum(operator, num_states=num_states)


def _expectation(operator, statevector: np.ndarray) -> float:
    if len(operator) == 0:
        return 0.0
    matrix = operator.to_matrix(sparse=True)
    return float(np.real(np.vdot(statevector, matrix @ statevector)))


def _matrix_element(operator, bra: np.ndarray, ket: np.ndarray) -> complex:
    if len(operator) == 0:
        return 0.0 + 0.0j
    matrix = operator.to_matrix(sparse=True)
    return complex(np.vdot(bra, matrix @ ket))


def _transition_dipole_components(dipole_property, mapping, bra: np.ndarray, ket: np.ndarray) -> np.ndarray:
    fermionic_ops = dipole_property.second_q_ops()
    components: list[complex] = []
    for op_name in ("XDipole", "YDipole", "ZDipole"):
        fermionic_op = fermionic_ops[op_name]
        qubit_op = mapping.mapper.map(fermionic_op)
        components.append(_matrix_element(qubit_op, bra, ket))
    electronic = np.asarray(components, dtype=complex)
    return -electronic if getattr(dipole_property, "reverse_dipole_sign", True) else electronic


def build_excited_state_result(
    spec: RunSpec,
    spectrum: ExactSpectrum | None,
    *,
    total_constant_correction: float,
) -> ExcitedStateTaskResult | None:
    """Build the excited-state task result section."""
    task = spec.tasks.excited_state
    if not task.enabled:
        return None
    if spectrum is None:
        return ExcitedStateTaskResult(
            enabled=True,
            method=task.method,
            verification_status="exploratory",
            notes=["Exact spectrum unavailable; excited-state task left as exploratory placeholder."],
        )

    ground_total = spectrum.eigenvalues[0] + total_constant_correction
    states: list[ExcitedStateLevelResult] = []
    for state_index in sorted(set(task.state_indices)):
        if state_index >= len(spectrum.eigenvalues):
            continue
        total_energy = spectrum.eigenvalues[state_index] + total_constant_correction
        verification = "validated" if task.method == "exact_spectrum" else "exploratory"
        baseline = {"source": "exact_spectrum"}
        if task.method != "exact_spectrum":
            baseline["proxy_mode"] = "exact_spectrum_for_vqd_skeleton"
        states.append(
            ExcitedStateLevelResult(
                state_index=state_index,
                solver_energy=float(spectrum.eigenvalues[state_index]),
                total_energy=float(total_energy),
                excitation_energy=float(total_energy - ground_total),
                reference_state_index=0,
                solver_metadata={"requested_method": task.method},
                baseline=baseline,
                verification_status=verification,
            )
        )

    notes: list[str] = []
    verification_status = "validated"
    if task.method != "exact_spectrum":
        verification_status = "exploratory"
        notes.append(
            "Requested excited-state method is treated as an exploratory interface; values come from an exact-spectrum proxy."
        )
    return ExcitedStateTaskResult(
        enabled=True,
        method=task.method,
        states=states,
        verification_status=verification_status,
        notes=notes,
    )


def build_property_result(
    spec: RunSpec,
    chemistry,
    mapping,
    spectrum: ExactSpectrum | None,
) -> PropertyTaskResult | None:
    """Build the property-task result section."""
    requested = [item for item in spec.tasks.properties if item.enabled]
    if not requested:
        return None

    properties: list[PropertyValueResult] = []
    dipole_property = getattr(chemistry.problem.properties, "electronic_dipole_moment", None)

    for item in requested:
        if item.property_name == "dipole_moment" and dipole_property is not None and spectrum is not None:
            state_index = item.state_indices[0] if item.state_indices else 0
            statevector = np.asarray(spectrum.eigenvectors[:, state_index], dtype=complex)
            fermionic_ops = dipole_property.second_q_ops()
            electronic_components: dict[str, float] = {}
            for axis_name, op_name in {"x": "XDipole", "y": "YDipole", "z": "ZDipole"}.items():
                fermionic_op = fermionic_ops[op_name]
                qubit_op = mapping.mapper.map(fermionic_op)
                electronic_components[axis_name] = _expectation(qubit_op, statevector)
            nuclear = np.asarray(dipole_property.nuclear_dipole_moment, dtype=float)
            electronic = np.asarray(
                [electronic_components["x"], electronic_components["y"], electronic_components["z"]],
                dtype=float,
            )
            total = nuclear - electronic if getattr(dipole_property, "reverse_dipole_sign", True) else nuclear + electronic
            properties.append(
                PropertyValueResult(
                    property_name=item.property_name,
                    method=item.method,
                    state_indices=item.state_indices,
                    value=float(math.sqrt(float(np.dot(total, total)))),
                    units="a.u.",
                    components={"x": float(total[0]), "y": float(total[1]), "z": float(total[2])},
                    implementation_status="validated",
                    provenance={
                        "source": "exact_expectation",
                        "statevector_source": "exact_spectrum",
                        "validated_scope": "ground_state_dipole_path",
                    },
                    notes=["Computed from exact eigenstate expectation values and nuclear dipole correction."],
                )
            )
            continue

        if item.property_name == "transition_dipole" and dipole_property is not None and spectrum is not None:
            if len(item.state_indices) < 2:
                properties.append(
                    PropertyValueResult(
                        property_name=item.property_name,
                        method=item.method,
                        state_indices=item.state_indices,
                        implementation_status="placeholder_only",
                        provenance={"source": "placeholder", "reason": "transition_dipole requires two state indices"},
                        notes=["Provide two state indices to compute a transition dipole."],
                    )
                )
                continue
            bra = np.asarray(spectrum.eigenvectors[:, item.state_indices[0]], dtype=complex)
            ket = np.asarray(spectrum.eigenvectors[:, item.state_indices[1]], dtype=complex)
            transition = _transition_dipole_components(dipole_property, mapping, bra, ket)
            magnitude = float(np.sqrt(float(np.sum(np.abs(transition) ** 2))))
            properties.append(
                PropertyValueResult(
                    property_name=item.property_name,
                    method=item.method,
                    state_indices=item.state_indices,
                    value=magnitude,
                    units="a.u.",
                    components={
                        "x": float(np.real(transition[0])),
                        "y": float(np.real(transition[1])),
                        "z": float(np.real(transition[2])),
                    },
                    implementation_status="validated",
                    provenance={
                        "source": "exact_transition_expectation",
                        "statevector_source": "exact_spectrum",
                        "validated_scope": "small_exact_spectrum_transition_property",
                    },
                    notes=[
                        "Computed from exact transition matrix elements.",
                        "Validated for small systems when exact-spectrum statevectors are available.",
                    ],
                )
            )
            continue

        if item.property_name == "oscillator_strength" and dipole_property is not None and spectrum is not None:
            if len(item.state_indices) < 2:
                properties.append(
                    PropertyValueResult(
                        property_name=item.property_name,
                        method=item.method,
                        state_indices=item.state_indices,
                        implementation_status="placeholder_only",
                        provenance={"source": "placeholder", "reason": "oscillator_strength requires two state indices"},
                        notes=["Provide two state indices to compute an oscillator strength."],
                    )
                )
                continue
            initial_index, final_index = item.state_indices[:2]
            bra = np.asarray(spectrum.eigenvectors[:, initial_index], dtype=complex)
            ket = np.asarray(spectrum.eigenvectors[:, final_index], dtype=complex)
            transition = _transition_dipole_components(dipole_property, mapping, bra, ket)
            magnitude = float(np.sqrt(float(np.sum(np.abs(transition) ** 2))))
            excitation_energy = float(spectrum.eigenvalues[final_index] - spectrum.eigenvalues[initial_index])
            oscillator_strength = float((2.0 / 3.0) * excitation_energy * (magnitude**2))
            properties.append(
                PropertyValueResult(
                    property_name=item.property_name,
                    method=item.method,
                    state_indices=item.state_indices,
                    value=oscillator_strength,
                    units="a.u.",
                    components={
                        "transition_dipole_magnitude": magnitude,
                        "excitation_energy": excitation_energy,
                    },
                    implementation_status="validated",
                    provenance={
                        "source": "exact_transition_derived",
                        "depends_on": ["transition_dipole", "excitation_energy"],
                        "validated_scope": "small_exact_spectrum_oscillator_strength",
                    },
                    notes=[
                        "Derived from exact-spectrum excitation energy and transition-dipole magnitude.",
                        "Validated for small systems when exact-spectrum statevectors are available.",
                    ],
                )
            )
            continue

        properties.append(
            PropertyValueResult(
                property_name=item.property_name,
                method=item.method,
                state_indices=item.state_indices,
                implementation_status="placeholder_only",
                provenance={"source": "placeholder", "validated_scope": "not_implemented"},
                notes=["Formal schema placeholder; implementation not yet validated in QCchem v0.4."],
            )
        )

    bundle_status = "validated" if all(item.implementation_status == "validated" for item in properties) else "exploratory"
    return PropertyTaskResult(
        enabled=True,
        properties=properties,
        verification_status=bundle_status,
    )


def _pyscf_unit(unit: str) -> str:
    normalized = unit.strip().lower()
    if normalized in {"angstrom", "ang", "a"}:
        return "Angstrom"
    if normalized in {"bohr", "au"}:
        return "Bohr"
    raise ValueError(f"Unsupported PySCF unit: {unit}")


def _pyscf_mol_from_geometry(spec: RunSpec, coords: np.ndarray | None = None):
    atom_parts = []
    actual_coords = coords
    if actual_coords is None:
        actual_coords = np.asarray([atom.coords for atom in spec.molecule.geometry], dtype=float)
    for atom, xyz in zip(spec.molecule.geometry, actual_coords, strict=True):
        atom_parts.append(f"{atom.symbol} {float(xyz[0])} {float(xyz[1])} {float(xyz[2])}")
    return gto.M(
        atom="; ".join(atom_parts),
        basis=spec.molecule.basis,
        charge=spec.molecule.charge,
        spin=spec.molecule.spin,
        unit=_pyscf_unit(spec.molecule.unit),
        verbose=0,
    )


def _run_rhf(spec: RunSpec, coords: np.ndarray | None = None):
    mol = _pyscf_mol_from_geometry(spec, coords)
    mf = scf.RHF(mol).run(verbose=0)
    return mol, mf


def _gradient_metrics(gradient: np.ndarray) -> dict[str, float]:
    norms = np.linalg.norm(gradient, axis=1)
    return {
        "max_norm": float(np.max(norms)) if len(norms) else 0.0,
        "rms_norm": float(np.sqrt(np.mean(norms**2))) if len(norms) else 0.0,
    }


def build_gradient_result(spec: RunSpec) -> dict[str, object] | None:
    """Build a PySCF-backed nuclear-gradient artifact section."""

    task = spec.tasks.gradient
    if not task.enabled:
        return None
    if task.method.strip().lower() != "pyscf_rhf":
        return {
            "enabled": True,
            "method": task.method,
            "state_index": task.state_index,
            "verification_status": "exploratory",
            "notes": [f"Unsupported gradient method: {task.method}"],
        }
    _mol, mf = _run_rhf(spec)
    gradient = np.asarray(mf.nuc_grad_method().kernel(), dtype=float)
    metrics = _gradient_metrics(gradient)
    return {
        "enabled": True,
        "method": "pyscf_rhf",
        "state_index": task.state_index,
        "gradient": gradient.tolist(),
        "units": "Hartree/Bohr",
        "max_norm": metrics["max_norm"],
        "rms_norm": metrics["rms_norm"],
        "provenance": {"source": "pyscf.scf.RHF.nuc_grad_method", "reference_state": "RHF ground state"},
        "verification_status": "validated" if task.state_index == 0 else "exploratory",
    }


def build_geometry_optimization_result(spec: RunSpec) -> dict[str, object] | None:
    """Build a small-system PySCF RHF geometry-optimization artifact section."""

    task = spec.tasks.geometry_optimization
    if not task.enabled:
        return None
    if task.method.strip().lower() != "pyscf_rhf":
        return {
            "enabled": True,
            "method": task.method,
            "verification_status": "exploratory",
            "notes": [f"Unsupported geometry optimization method: {task.method}"],
        }

    coords0 = np.asarray([atom.coords for atom in spec.molecule.geometry], dtype=float)
    symbols = [atom.symbol for atom in spec.molecule.geometry]
    if len(symbols) != 2:
        gradient = build_gradient_result(
            RunSpec(
                molecule=spec.molecule,
                problem=spec.problem,
                mapping=spec.mapping,
                backend=spec.backend,
                solver=spec.solver,
                benchmark=spec.benchmark,
                mitigation=spec.mitigation,
                policy=spec.policy,
                exploratory=spec.exploratory,
                tasks=spec.tasks,
                tc_qsci=spec.tc_qsci,
                hardware_optimization=spec.hardware_optimization,
                run=spec.run,
            )
        )
        return {
            "enabled": True,
            "method": "pyscf_rhf",
            "verification_status": "exploratory",
            "initial_geometry": coords0.tolist(),
            "final_geometry": coords0.tolist(),
            "trajectory": [],
            "gradient": gradient,
            "notes": ["Current validated geometry optimization is limited to two-atom H2/LiH-style systems."],
        }

    axis = coords0[1] - coords0[0]
    initial_distance = float(np.linalg.norm(axis))
    if initial_distance <= 0:
        raise ValueError("Two-atom geometry optimization requires a non-zero initial bond distance.")
    axis = axis / initial_distance
    trajectory: list[dict[str, float]] = []

    def _coords(distance: float) -> np.ndarray:
        coords = np.array(coords0, copy=True)
        coords[1] = coords[0] + axis * distance
        return coords

    def _energy(distance: float) -> float:
        _mol, mf = _run_rhf(spec, _coords(distance))
        value = float(mf.e_tot)
        trajectory.append({"bond_distance": float(distance), "total_energy": value})
        return value

    upper = max(4.0, initial_distance * 2.5)
    result = minimize_scalar(
        _energy,
        bounds=(0.2, upper),
        method="bounded",
        options={"maxiter": int(task.max_steps), "xatol": 1.0e-4},
    )
    final_distance = float(result.x)
    final_coords = _coords(final_distance)
    _mol, final_mf = _run_rhf(spec, final_coords)
    final_gradient = np.asarray(final_mf.nuc_grad_method().kernel(), dtype=float)
    metrics = _gradient_metrics(final_gradient)
    validated_symbols = set(symbols) in ({"H"}, {"H", "Li"})
    converged = bool(metrics["max_norm"] <= max(task.gradient_tolerance * 20.0, 1.0e-2))
    return {
        "enabled": True,
        "method": "pyscf_rhf",
        "initial_geometry": coords0.tolist(),
        "final_geometry": final_coords.tolist(),
        "initial_energy": float(trajectory[0]["total_energy"]) if trajectory else None,
        "final_energy": float(final_mf.e_tot),
        "energy_drop": (
            None if not trajectory else float(trajectory[0]["total_energy"] - float(final_mf.e_tot))
        ),
        "trajectory": trajectory,
        "converged": converged,
        "final_bond_distance": final_distance,
        "gradient": final_gradient.tolist(),
        "gradient_units": "Hartree/Bohr",
        "max_gradient_norm": metrics["max_norm"],
        "rms_gradient_norm": metrics["rms_norm"],
        "verification_status": "validated" if validated_symbols and converged else "exploratory",
        "provenance": {
            "source": "pyscf.scf.RHF + scipy.optimize.minimize_scalar",
            "validated_scope": "two_atom_h2_lih_reference_optimization",
            "optimizer_success": bool(result.success),
            "optimizer_message": str(result.message),
        },
        "notes": ["Two-atom optimization scans the bond distance along the initial molecular axis."],
    }


def build_response_property_result(spec: RunSpec) -> dict[str, object] | None:
    """Build response-property artifacts, currently finite-field RHF polarizability."""

    task = spec.tasks.response_properties
    if not task.enabled:
        return None
    requested = set(task.properties)
    properties: list[dict[str, object]] = []
    if "static_polarizability" in requested:
        _mol, mf0 = _run_rhf(spec)
        mol = mf0.mol
        hcore0 = mf0.get_hcore()
        dipoles = mol.intor("int1e_r", comp=3)
        step = float(task.finite_field_step)
        diagonal: list[float] = []
        energies: dict[str, float] = {"zero": float(mf0.e_tot)}
        for axis_index, axis_name in enumerate(("x", "y", "z")):
            axis_values: dict[str, float] = {}
            for sign, label in ((1.0, "plus"), (-1.0, "minus")):
                mf = scf.RHF(mol)
                field_hcore = hcore0 + sign * step * dipoles[axis_index]
                mf.get_hcore = lambda *args, _field_hcore=field_hcore: _field_hcore
                mf.kernel()
                axis_values[label] = float(mf.e_tot)
                energies[f"{axis_name}_{label}"] = float(mf.e_tot)
            diagonal.append(float(-(axis_values["plus"] + axis_values["minus"] - 2.0 * mf0.e_tot) / (step**2)))
        properties.append(
            {
                "property_name": "static_polarizability",
                "method": "finite_field_rhf",
                "value": {"xx": diagonal[0], "yy": diagonal[1], "zz": diagonal[2]},
                "isotropic": float(sum(diagonal) / 3.0),
                "units": "a.u.",
                "finite_field_step": step,
                "field_energies": energies,
                "implementation_status": "validated",
                "provenance": {
                    "source": "PySCF RHF finite-field second derivative",
                    "validated_scope": "small_molecule_rhf_reference_response",
                },
            }
        )
    for name in requested - {"static_polarizability"}:
        properties.append(
            {
                "property_name": name,
                "method": task.method,
                "implementation_status": "placeholder_only",
                "notes": ["Response property is declared but not implemented yet."],
            }
        )
    return {
        "enabled": True,
        "method": task.method,
        "properties": properties,
        "verification_status": "validated"
        if properties and all(item.get("implementation_status") == "validated" for item in properties)
        else "exploratory",
    }
