"""Workflow runner entrypoints."""

from __future__ import annotations

import logging
import platform
import shutil
import subprocess
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np
import pyscf
import scipy
import yaml
from qiskit import __version__ as qiskit_version
from qiskit_nature import __version__ as qiskit_nature_version

from qcchem.backends import (
    attempt_runtime_submission,
    build_backend,
    build_measurement_plan,
    build_noise_model_summary,
    build_runtime_options_summary,
    describe_backend_capabilities,
    resolve_policy,
    resolve_execution_policy,
)
from qcchem.chem import build_electronic_structure_context, build_reduction_plan
from qcchem.chem.compression import build_compressed_fermionic_hamiltonian, build_compression_result
from qcchem.chem.plugins import build_embedding_result, run_nevpt2_correction
from qcchem.core.chemical_accuracy import check_chemical_accuracy
from qcchem.core import (
    ArtifactPaths,
    BackendSummary,
    BenchmarkSummary,
    CalibrationSummary,
    CompressedExecutionComparisonSummary,
    EnergyResult,
    ExactBaselineSummary,
    LogSummary,
    ProvenanceSummary,
    RunResult,
    RuntimeSubmissionSummary,
    SampledResultSummary,
    VariationalResultSummary,
)
from qcchem.io.config import load_run_spec
from qcchem.io.exports import workspace_fingerprint, write_hdf5_result, write_qcschema_json
from qcchem.io.serialization import to_primitive
from qcchem.mapping import MappedHamiltonian, map_fermionic_hamiltonian
from qcchem.mitigation import build_mitigation_summary
from qcchem.reporting import write_calibration_report, write_markdown_report, write_result_json
from qcchem.exploratory.solvers.registry import build_exploratory_solver
from qcchem.solvers import ExactDiagonalizationSolver, build_solver
from qcchem.solvers.spectrum import ExactSpectrum, compute_exact_spectrum
from qcchem.workflow.tasks import (
    build_excited_state_result,
    build_property_result,
    required_exact_states,
)
from qcchem.workflow.calibration import build_calibration_summary

SCHEMA_VERSION = "qcchem.result.v0.8-alpha"
ENERGY_UNITS = "Hartree"
ENERGY_FORMULA = (
    "total_energy = solver_energy + constant_energy_correction + nuclear_repulsion_energy; "
    "electronic_energy = solver_energy + constant_energy_correction"
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _prepare_artifact_paths(root: Path, overwrite: bool, *, qcschema_json: bool, hdf5: bool) -> ArtifactPaths:
    resolved_root = root.expanduser()
    if not resolved_root.is_absolute():
        resolved_root = (_project_root() / resolved_root).resolve()
    if resolved_root.exists() and overwrite:
        shutil.rmtree(resolved_root)
    if resolved_root.exists() and any(resolved_root.iterdir()) and not overwrite:
        raise FileExistsError(
            f"Artifact directory '{resolved_root}' already exists and is not empty. "
            "Set run.overwrite=true or use a new output directory."
        )
    resolved_root.mkdir(parents=True, exist_ok=True)
    return ArtifactPaths(
        root=resolved_root,
        resolved_config=resolved_root / "resolved_config.yaml",
        result_json=resolved_root / "result.json",
        exact_result_json=resolved_root / "exact_result.json",
        report_markdown=resolved_root / "report.md",
        log_file=resolved_root / "run.log",
        calibration_json=resolved_root / "calibration.json",
        calibration_report_markdown=resolved_root / "calibration_report.md",
        runtime_submission_json=resolved_root / "runtime_submission.json",
        qcschema_json=(resolved_root / "qcschema.json") if qcschema_json else None,
        hdf5_file=(resolved_root / "result.h5") if hdf5 else None,
    )


def _build_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger(f"qcchem.{log_path.parent.name}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger


def _record(logger: logging.Logger, events: list[str], message: str) -> None:
    logger.info(message)
    events.append(message)


def _git_commit(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None
    return result.stdout.strip() or None


def _git_describe(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "describe", "--always", "--dirty", "--tags"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None
    return result.stdout.strip() or None


def _git_branch(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None
    branch = result.stdout.strip()
    return branch or None


def _git_remote_origin(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None
    return result.stdout.strip() or None


def _workspace_status_porcelain(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return ""
    return result.stdout


def _workspace_dirty(root: Path) -> bool | None:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None
    return bool(result.stdout.strip())


def _git_status_summary(root: Path) -> dict[str, int]:
    porcelain = _workspace_status_porcelain(root).splitlines()
    summary = {"staged": 0, "unstaged": 0, "untracked": 0}
    for line in porcelain:
        if line.startswith("??"):
            summary["untracked"] += 1
            continue
        if line[:1].strip():
            summary["staged"] += 1
        if line[1:2].strip():
            summary["unstaged"] += 1
    return summary


def _dependency_versions() -> dict[str, str]:
    versions = {
        "python": platform.python_version(),
        "qiskit": qiskit_version,
        "qiskit_nature": qiskit_nature_version,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pyscf": pyscf.__version__,
    }
    try:
        import qiskit_aer

        versions["qiskit_aer"] = qiskit_aer.__version__
    except Exception:
        pass
    return versions


def _write_exact_artifact(artifacts: ArtifactPaths, exact_baseline: ExactBaselineSummary) -> None:
    payload = {"schema_version": SCHEMA_VERSION, **to_primitive(exact_baseline)}
    write_result_json(payload, artifacts.exact_result_json)


def _write_optional_artifacts(
    artifacts: ArtifactPaths,
    *,
    calibration,
    runtime_submission,
    result,
) -> None:
    if calibration is not None and artifacts.calibration_json is not None:
        payload = {"schema_version": SCHEMA_VERSION, **to_primitive(calibration)}
        write_result_json(payload, artifacts.calibration_json)
    if calibration is not None and artifacts.calibration_report_markdown is not None:
        write_calibration_report(result, artifacts.calibration_report_markdown)
    if runtime_submission is not None and artifacts.runtime_submission_json is not None:
        payload = {"schema_version": SCHEMA_VERSION, **to_primitive(runtime_submission)}
        write_result_json(payload, artifacts.runtime_submission_json)


def _solve_with_timing(solver, operator):
    started = perf_counter()
    outcome = solver.solve(operator)
    return outcome, float(perf_counter() - started)


def _with_simplified_mapping(mapping: MappedHamiltonian, *, atol: float) -> MappedHamiltonian:
    simplified = mapping.qubit_hamiltonian.simplify(atol=atol)
    return MappedHamiltonian(
        fermionic_hamiltonian=mapping.fermionic_hamiltonian,
        qubit_hamiltonian=simplified,
        mapper=mapping.mapper,
        summary=type(mapping.summary)(
            kind=mapping.summary.kind,
            num_qubits=int(simplified.num_qubits),
            fermionic_term_count=mapping.summary.fermionic_term_count,
            qubit_term_count=len(simplified),
        ),
    )


def _compression_post_term_limit(bundle, total_terms: int) -> int:
    if bundle is None or bundle.rank <= 0:
        return total_terms
    if bundle.method == "modified_cholesky":
        target = max(bundle.rank * 6, bundle.rank)
    else:
        secondary = bundle.secondary_rank or bundle.rank
        target = max(secondary * 4, bundle.rank * 4)
    return min(total_terms, target)


def _with_truncated_mapping(mapping: MappedHamiltonian, *, atol: float, max_terms: int | None) -> MappedHamiltonian:
    operator = mapping.qubit_hamiltonian
    if max_terms is not None and len(operator) > max_terms:
        coeffs = np.abs(operator.coeffs)
        keep = np.argsort(coeffs)[-max_terms:]
        operator = operator[keep]
    simplified = operator.simplify(atol=atol)
    return MappedHamiltonian(
        fermionic_hamiltonian=mapping.fermionic_hamiltonian,
        qubit_hamiltonian=simplified,
        mapper=mapping.mapper,
        summary=type(mapping.summary)(
            kind=mapping.summary.kind,
            num_qubits=int(simplified.num_qubits),
            fermionic_term_count=mapping.summary.fermionic_term_count,
            qubit_term_count=len(simplified),
        ),
    )


def _build_sampled_result(
    *,
    backend,
    solver_kind: str,
    solver_outcome,
    operator,
    constant_energy_correction: float,
    nuclear_repulsion_energy: float,
) -> SampledResultSummary | None:
    if backend is None or solver_kind != "vqe":
        return None
    if getattr(backend, "backend_kind", "") != "shot_estimator":
        return None
    ansatz = solver_outcome.metadata.get("ansatz_circuit")
    if ansatz is None:
        return None

    estimates = backend.sample_repeated(ansatz, operator, np.asarray(solver_outcome.optimal_parameters, dtype=float))
    raw_values = np.asarray([item.value for item in estimates], dtype=float)
    raw_stds = np.asarray([item.reported_std for item in estimates], dtype=float)
    mean = float(raw_values.mean())
    empirical_std = float(raw_values.std(ddof=1)) if len(raw_values) > 1 else 0.0
    if len(raw_values) > 1:
        standard_error = float(empirical_std / np.sqrt(len(raw_values)))
    else:
        standard_error = float(raw_stds[0]) if len(raw_stds) else 0.0
    ci_half_width = 1.96 * standard_error

    return SampledResultSummary(
        available=True,
        backend_kind=getattr(backend, "backend_kind", "unknown"),
        shots=estimates[0].shots if estimates else None,
        num_repeats=len(estimates),
        seed=getattr(backend, "spec", None).seed if hasattr(backend, "spec") else None,
        repeat_seeds=[item.seed for item in estimates],
        repeat_solver_energies=[float(value) for value in raw_values],
        repeat_reported_stds=[float(value) for value in raw_stds],
        repeat_metadata=[dict(item.metadata) for item in estimates],
        sampled_solver_energy_mean=mean,
        sampled_solver_energy_std=empirical_std,
        sampled_electronic_energy_mean=float(mean + constant_energy_correction),
        sampled_total_energy_mean=float(mean + constant_energy_correction + nuclear_repulsion_energy),
        standard_error=standard_error,
        confidence_interval_low=float(mean - ci_half_width),
        confidence_interval_high=float(mean + ci_half_width),
    )


def _classify_verification_status(
    benchmark: BenchmarkSummary,
    sampled_result: SampledResultSummary | None,
) -> str:
    if not benchmark.exact_available:
        return "exploratory"
    if benchmark.meets_threshold is False:
        return "failed"
    if sampled_result is not None and benchmark.within_uncertainty is False:
        return "unstable"
    if benchmark.meets_threshold:
        return "validated"
    return "exploratory"


def _compute_exact_spectrum_if_needed(spec, mapping, logger, events) -> ExactSpectrum | None:
    need_exact = spec.benchmark.enabled or spec.tasks.excited_state.enabled or bool(spec.tasks.properties)
    if not need_exact:
        return None
    required_states = required_exact_states(spec)
    if mapping.summary.num_qubits > spec.benchmark.exact_baseline_qubit_limit:
        _record(
            logger,
            events,
            "Skipping exact spectrum: qubit count exceeds configured exact-baseline limit.",
        )
        return None
    _record(logger, events, f"Computing exact spectrum for {required_states} states")
    return compute_exact_spectrum(mapping.qubit_hamiltonian, num_states=required_states)


def _ensure_exploratory_allowed(spec, *, exploratory_command: bool) -> None:
    requested = (
        spec.solver.experimental
        or spec.mitigation.experimental
        or spec.exploratory.enabled
        or bool(spec.exploratory.modules)
    )
    if requested and not (exploratory_command or spec.policy.allow_exploratory):
        raise ValueError(
            "Exploratory modules require `qcchem exploratory ...` or `policy.allow_exploratory=true`."
        )


def run_spec(spec, *, source_config: str, output_dir: Path | None = None) -> RunResult:
    """Run a QCchem calculation from an already-parsed RunSpec."""
    started_at = perf_counter()
    if output_dir is not None:
        spec.run.output_dir = Path(output_dir)

    artifacts = _prepare_artifact_paths(
        spec.run.output_dir,
        overwrite=spec.run.overwrite,
        qcschema_json=spec.run.exports.qcschema_json,
        hdf5=spec.run.exports.hdf5,
    )
    logger = _build_logger(artifacts.log_file)
    events: list[str] = []
    repo_root = _project_root()
    git_commit = _git_commit(repo_root)
    git_branch = _git_branch(repo_root)
    git_describe = _git_describe(repo_root)
    git_remote_origin = _git_remote_origin(repo_root)
    workspace_dirty = _workspace_dirty(repo_root)
    workspace_status = _workspace_status_porcelain(repo_root)
    git_status_summary = _git_status_summary(repo_root)
    dependency_versions = _dependency_versions()
    _record(logger, events, f"Loading config from {source_config}")
    artifacts.resolved_config.write_text(
        yaml.safe_dump(to_primitive(spec), sort_keys=False),
        encoding="utf-8",
    )

    capability = describe_backend_capabilities(spec.backend)
    policy_summary = resolve_execution_policy(spec.policy, spec.backend, spec.benchmark, spec.mitigation)
    policy_engine_result = resolve_policy(spec)
    noise_model = build_noise_model_summary(spec.backend.noise)

    _record(logger, events, "Building electronic structure problem")
    chemistry = build_electronic_structure_context(spec)

    _record(logger, events, f"Applying mapping: {spec.mapping.kind}")
    uncompressed_mapping = map_fermionic_hamiltonian(chemistry.fermionic_hamiltonian, spec.mapping.kind)
    compression_bundle = build_compressed_fermionic_hamiltonian(chemistry.problem, spec.problem.compression)
    compressed_mapping = None
    if compression_bundle is not None:
        compressed_mapping = map_fermionic_hamiltonian(compression_bundle.fermionic_hamiltonian, spec.mapping.kind)
        compressed_mapping = _with_truncated_mapping(
            compressed_mapping,
            atol=spec.problem.compression.threshold,
            max_terms=_compression_post_term_limit(compression_bundle, len(compressed_mapping.qubit_hamiltonian)),
        )
        _record(logger, events, f"Constructed compressed mapped Hamiltonian via {compression_bundle.method}")
    mapping = compressed_mapping if compressed_mapping is not None else uncompressed_mapping
    compression_result = build_compression_result(
        pre_mapping_summary=uncompressed_mapping.summary,
        spec=spec.problem.compression,
        execution_bundle=compression_bundle,
        post_mapping_summary=(mapping.summary if compressed_mapping is not None else None),
    )
    if compression_result is not None:
        _record(logger, events, f"Computed compression audit: {compression_result.method}")
    measurement = build_measurement_plan(
        measurement_spec=spec.problem.measurement,
        executed_mapping=mapping,
        uncompressed_mapping=uncompressed_mapping,
        compression_result=compression_result,
        backend_precision=spec.backend.precision,
        backend_shots=spec.backend.shots,
    )
    _record(
        logger,
        events,
        f"Prepared measurement plan: groups={measurement.group_count}, cost={measurement.estimated_shot_cost:.0f}",
    )
    runtime_options = build_runtime_options_summary(
        spec.backend,
        capability,
        measurement=measurement,
        compression=compression_result,
    )
    if runtime_options is not None:
        _record(logger, events, f"Prepared runtime policy snapshot for service={runtime_options.service}")

    solver_kind = spec.solver.kind.strip().lower()
    backend = None
    backend_required = solver_kind == "vqe" or (
        spec.solver.experimental and solver_kind in {"adapt_vqe", "vqd", "folded_spectrum"}
    )
    if backend_required:
        _record(logger, events, f"Preparing backend: {spec.backend.kind}")
        backend = build_backend(spec.backend)
    else:
        _record(logger, events, f"Skipping backend construction for solver: {spec.solver.kind}")

    _record(logger, events, f"Running solver: {spec.solver.kind}")
    if spec.solver.experimental:
        solver = build_exploratory_solver(
            spec.solver.kind,
            spec=spec.solver,
            backend=backend,
            seed=spec.run.seed,
            problem_summary=chemistry.summary,
            mapper=mapping.mapper,
        )
    else:
        solver = build_solver(
            spec.solver,
            backend=backend,
            seed=spec.run.seed,
            problem_summary=chemistry.summary,
            mapper=mapping.mapper,
        )
    solver_outcome, compressed_solve_wall_time = _solve_with_timing(solver, mapping.qubit_hamiltonian)

    spectrum = _compute_exact_spectrum_if_needed(spec, mapping, logger, events)
    exact_energy = float(spectrum.eigenvalues[0]) if spectrum is not None else None
    if exact_energy is None and spec.benchmark.enabled and solver_kind in {"exact", "reference"}:
        exact_energy = float(solver_outcome.total_energy)

    exact_baseline = ExactBaselineSummary(
        available=exact_energy is not None,
        solver_hamiltonian_energy=exact_energy,
        electronic_energy=(float(exact_energy + chemistry.electronic_constant_correction) if exact_energy is not None else None),
        total_energy=(float(exact_energy + chemistry.total_constant_correction) if exact_energy is not None else None),
        energy_units=ENERGY_UNITS,
    )
    _record(logger, events, f"Writing exact baseline artifact to {artifacts.exact_result_json}")
    _write_exact_artifact(artifacts, exact_baseline)

    sampled_result = _build_sampled_result(
        backend=backend,
        solver_kind=solver_kind,
        solver_outcome=solver_outcome,
        operator=mapping.qubit_hamiltonian,
        constant_energy_correction=chemistry.electronic_constant_correction,
        nuclear_repulsion_energy=chemistry.nuclear_repulsion_energy,
    )
    if sampled_result is not None:
        _record(logger, events, "Collected repeated shot-based sampling statistics")

    solver_energy = float(solver_outcome.total_energy)
    electronic_energy = float(solver_energy + chemistry.electronic_constant_correction)
    total_energy = float(solver_energy + chemistry.total_constant_correction)
    correlation_energy = None
    if chemistry.hf_reference_energy is not None:
        correlation_energy = float(total_energy - chemistry.hf_reference_energy)

    variational_result = None
    if solver_kind == "vqe":
        variational_result = VariationalResultSummary(
            available=True,
            solver_kind=spec.solver.kind,
            optimizer={
                "kind": spec.solver.optimizer.kind,
                "maxiter": spec.solver.optimizer.maxiter,
                "tol": spec.solver.optimizer.tol,
            },
            ansatz={
                "kind": spec.solver.ansatz.kind,
                "rotation_blocks": spec.solver.ansatz.rotation_blocks,
                "entanglement_blocks": spec.solver.ansatz.entanglement_blocks,
                "entanglement": spec.solver.ansatz.entanglement,
                "reps": spec.solver.ansatz.reps,
            },
            initial_point_strategy=spec.solver.initial_point if isinstance(spec.solver.initial_point, str) else "custom",
            parameter_count=int(solver_outcome.metadata.get("ansatz_num_parameters", 0)),
            converged=solver_outcome.converged,
            iterations=solver_outcome.iterations,
            evaluations=solver_outcome.evaluations,
            optimal_parameters=solver_outcome.optimal_parameters,
            final_objective_energy=solver_energy,
            optimizer_message=str(solver_outcome.metadata.get("optimizer_message")),
        )

    compressed_comparison = None
    if compression_result is not None and compression_result.execution_enabled:
        if solver_kind == "vqe":
            reference_backend = build_backend(spec.backend)
        else:
            reference_backend = None
        reference_solver = build_solver(
            spec.solver,
            backend=reference_backend,
            seed=spec.run.seed,
            problem_summary=chemistry.summary,
            mapper=uncompressed_mapping.mapper,
        )
        uncompressed_outcome, uncompressed_solve_wall_time = _solve_with_timing(
            reference_solver,
            uncompressed_mapping.qubit_hamiltonian,
        )
        uncompressed_solver_energy = float(uncompressed_outcome.total_energy)
        uncompressed_total_energy = float(uncompressed_solver_energy + chemistry.total_constant_correction)
        absolute_difference = float(abs(total_energy - uncompressed_total_energy))
        relative_difference = float(absolute_difference / max(abs(uncompressed_total_energy), 1.0e-12))
        compressed_comparison = CompressedExecutionComparisonSummary(
            available=True,
            method=compression_result.method,
            rank=compression_result.rank,
            threshold=compression_result.threshold,
            pre_term_count=compression_result.pre_term_count,
            post_term_count=compression_result.post_term_count,
            compressed_solver_energy=solver_energy,
            uncompressed_solver_energy=uncompressed_solver_energy,
            compressed_total_energy=total_energy,
            uncompressed_total_energy=uncompressed_total_energy,
            absolute_error=absolute_difference,
            relative_error=relative_difference,
            compressed_solve_wall_time_seconds=compressed_solve_wall_time,
            uncompressed_solve_wall_time_seconds=uncompressed_solve_wall_time,
        )
        _record(logger, events, "Computed compressed-vs-uncompressed execution comparison")

    comparison_target = "variational_result"
    compared_energy = solver_energy
    statistical_error = None
    if sampled_result is not None and sampled_result.sampled_solver_energy_mean is not None:
        comparison_target = "sampled_result"
        compared_energy = sampled_result.sampled_solver_energy_mean
        statistical_error = sampled_result.standard_error
    elif solver_kind in {"exact", "reference"}:
        comparison_target = "exact_baseline"

    compared_total_energy = total_energy
    if sampled_result is not None and sampled_result.sampled_total_energy_mean is not None:
        compared_total_energy = sampled_result.sampled_total_energy_mean

    absolute_error = None
    relative_error = None
    within_uncertainty = None
    meets_threshold = None
    if compressed_comparison is not None:
        comparison_target = "compressed_vs_uncompressed"
        absolute_error = compressed_comparison.absolute_error
        denominator = max(abs(compressed_comparison.uncompressed_total_energy), 1.0e-12)
        relative_error = float(absolute_error / denominator)
        if statistical_error is not None and sampled_result is not None:
            within_uncertainty = bool(absolute_error <= 1.96 * statistical_error)
        meets_threshold = (
            absolute_error <= spec.benchmark.absolute_error_threshold
            and relative_error <= spec.benchmark.relative_error_threshold
        )
    elif exact_energy is not None:
        absolute_error = float(abs(compared_energy - exact_energy))
        denominator = max(abs(float(exact_energy)), 1.0e-12)
        relative_error = float(absolute_error / denominator)
        if statistical_error is not None:
            within_uncertainty = bool(absolute_error <= 1.96 * statistical_error)
        meets_threshold = (
            absolute_error <= spec.benchmark.absolute_error_threshold
            and relative_error <= spec.benchmark.relative_error_threshold
        )

    benchmark = BenchmarkSummary(
        exact_available=(exact_energy is not None) or (compressed_comparison is not None),
        comparison_target=comparison_target,
        absolute_error=absolute_error,
        relative_error=relative_error,
        statistical_error=statistical_error,
        absolute_error_threshold=spec.benchmark.absolute_error_threshold,
        relative_error_threshold=spec.benchmark.relative_error_threshold,
        within_uncertainty=within_uncertainty,
        meets_threshold=meets_threshold,
        exact_electronic_energy=exact_baseline.electronic_energy,
        exact_total_energy=exact_baseline.total_energy,
        compressed_vs_uncompressed=compressed_comparison,
    )

    calibration = build_calibration_summary(
        measurement=measurement,
        sampled_result=sampled_result,
        benchmark=benchmark,
        measured_wall_time_seconds=compressed_solve_wall_time,
    )
    if calibration is not None:
        _record(
            logger,
            events,
            (
                "Computed empirical calibration: "
                f"wall_time={calibration.measured_wall_time_seconds:.3f}s, "
                f"measured_cost={calibration.measured_shot_usage}"
            ),
        )

    runtime_submission = None
    if (
        runtime_options is not None
        and runtime_options.enabled
        and solver_kind == "vqe"
        and variational_result is not None
        and solver_outcome.metadata.get("ansatz_circuit") is not None
        and measurement.execution_mode == "runtime_estimator"
    ):
        runtime_submission = attempt_runtime_submission(
            spec=spec.backend,
            circuit=solver_outcome.metadata["ansatz_circuit"],
            operator=mapping.qubit_hamiltonian,
            parameter_values=solver_outcome.optimal_parameters,
        )
        if runtime_submission is not None:
            status_text = "submitted" if runtime_submission.submitted else runtime_submission.failure_category
            _record(logger, events, f"Runtime submission attempt recorded: {status_text}")

    mitigation = build_mitigation_summary(spec.mitigation)
    excited_state_result = build_excited_state_result(
        spec,
        spectrum,
        total_constant_correction=chemistry.total_constant_correction,
    )
    property_result = build_property_result(spec, chemistry, mapping, spectrum)
    perturbative_correction_result = run_nevpt2_correction(
        spec.molecule,
        chemistry.reduction_audit,
        spec.tasks.perturbative_correction,
        reduced_active_space_energy=(
            compressed_comparison.uncompressed_total_energy if compressed_comparison is not None else total_energy
        ),
        compressed_active_space_energy=(total_energy if compression_result is not None and compression_result.execution_enabled else None),
    )
    if perturbative_correction_result is not None and perturbative_correction_result.enabled:
        _record(logger, events, f"Computed perturbative correction: {perturbative_correction_result.method}")
    embedding_result = build_embedding_result(spec.molecule, spec.problem.embedding)
    if embedding_result is not None and embedding_result.enabled:
        _record(logger, events, f"Computed embedding audit: {embedding_result.method}")

    reduction_plan = build_reduction_plan(spec, chemistry.reduction_audit)
    chemical_accuracy = check_chemical_accuracy(
        total_energy,
        exact_baseline.total_energy if exact_baseline.available else None,
        statistical_error=benchmark.statistical_error,
    )

    verification_status = _classify_verification_status(benchmark, sampled_result)
    if (
        compression_result is not None
        and compression_result.execution_enabled
        and compression_result.verification_status == "exploratory"
        and verification_status == "validated"
    ):
        verification_status = "exploratory"
    if (
        runtime_options is not None
        and runtime_options.enabled
        and runtime_options.runtime_ready
        and runtime_options.provenance.get("adapter") == "runtime_ready_placeholder"
        and verification_status == "validated"
    ):
        verification_status = "exploratory"
    if (
        runtime_submission is not None
        and runtime_submission.attempted
        and not runtime_submission.submitted
        and verification_status == "validated"
    ):
        verification_status = "exploratory"
    if spec.solver.experimental and verification_status == "validated":
        verification_status = "exploratory"

    run_id = artifacts.root.name
    module_origin = str(solver_outcome.metadata.get("module_origin", "core"))
    capability_tier = str(solver_outcome.metadata.get("capability_tier", verification_status))
    scientific_risk_notes = [
        str(item) for item in solver_outcome.metadata.get("scientific_risk_notes", [])
    ]
    verification_notes = [
        f"validation_scope={solver_outcome.metadata.get('validation_scope')}"
    ] if solver_outcome.metadata.get("validation_scope") else []
    hardware_verified = bool(
        runtime_submission is not None and runtime_submission.submitted and runtime_submission.succeeded
    )
    hardware_evidence_tier = None
    if runtime_submission is not None and runtime_submission.submitted and runtime_submission.succeeded:
        hardware_evidence_tier = "retrieved_result"
    elif runtime_submission is not None and runtime_submission.submitted:
        hardware_evidence_tier = "submitted"
    elif runtime_submission is not None and runtime_submission.attempted:
        hardware_evidence_tier = "runtime_attempt"
    result = RunResult(
        schema_version=SCHEMA_VERSION,
        run_id=run_id,
        verification_status=verification_status,
        energy=EnergyResult(
            solver_energy=solver_energy,
            constant_energy_correction=float(chemistry.electronic_constant_correction),
            electronic_energy=electronic_energy,
            nuclear_repulsion_energy=float(chemistry.nuclear_repulsion_energy),
            total_energy=total_energy,
            hf_reference_energy=chemistry.hf_reference_energy,
            exact_ground_energy=exact_energy,
            correlation_energy=correlation_energy,
            energy_units=ENERGY_UNITS,
            energy_formula=ENERGY_FORMULA,
        ),
        exact_baseline=exact_baseline,
        sampled_result=sampled_result,
        variational_result=variational_result,
        benchmark=benchmark,
        mitigation=mitigation,
        problem=chemistry.summary,
        mapping=mapping.summary,
        backend=BackendSummary(
            kind=spec.backend.kind,
            shots=spec.backend.shots,
            precision=spec.backend.precision,
            seed=spec.backend.seed,
            repetitions=spec.backend.repetitions,
            abelian_grouping=spec.backend.abelian_grouping,
            noise_enabled=spec.backend.noise.enabled,
            runtime_enabled=spec.backend.runtime.enabled,
        ),
        reduction_audit=chemistry.reduction_audit,
        noise_model=noise_model,
        measurement=measurement,
        chemical_accuracy=chemical_accuracy,
        reduction_plan=reduction_plan,
        policy_engine=policy_engine_result,
        calibration=calibration,
        runtime_options=runtime_options,
        runtime_submission=runtime_submission,
        compression_result=compression_result,
        backend_capability=capability,
        execution_policy=policy_summary,
        excited_state_result=excited_state_result,
        property_result=property_result,
        perturbative_correction_result=perturbative_correction_result,
        embedding_result=embedding_result,
        provenance=ProvenanceSummary(
            timestamp=datetime.now(timezone.utc).isoformat(),
            wall_time_seconds=0.0,
            source_config=str(source_config),
            seed=spec.run.seed,
            git_commit=git_commit,
            git_commit_short=((git_commit or "")[:12] or None),
            git_branch=git_branch,
            git_describe=git_describe,
            git_remote_origin=git_remote_origin,
            repo_root=str(repo_root),
            workspace_dirty=workspace_dirty,
            workspace_fingerprint=workspace_fingerprint(
                [
                    str(source_config),
                    yaml.safe_dump(to_primitive(spec), sort_keys=True),
                    json.dumps(dependency_versions, sort_keys=True),
                    workspace_status,
                ]
            ),
            git_status_summary=git_status_summary,
            dependency_versions=dependency_versions,
        ),
        log_summary=LogSummary(events=list(events)),
        artifacts=artifacts,
        module_origin=module_origin,
        capability_tier=capability_tier,
        hardware_verified=hardware_verified,
        hardware_evidence_tier=hardware_evidence_tier,
        verification_notes=verification_notes,
        scientific_risk_notes=scientific_risk_notes,
    )

    _record(logger, events, f"Writing JSON result to {artifacts.result_json}")
    result.log_summary.events = list(events)
    write_result_json(result, artifacts.result_json)

    _record(logger, events, f"Writing Markdown report to {artifacts.report_markdown}")
    result.log_summary.events = list(events)
    write_markdown_report(result, artifacts.report_markdown)

    _record(logger, events, "Run completed")
    result.log_summary.events = list(events)
    result.provenance.wall_time_seconds = float(perf_counter() - started_at)
    write_result_json(result, artifacts.result_json)
    write_markdown_report(result, artifacts.report_markdown)
    _write_optional_artifacts(
        artifacts,
        calibration=calibration,
        runtime_submission=runtime_submission,
        result=result,
    )
    if artifacts.qcschema_json is not None:
        write_qcschema_json(result, artifacts.qcschema_json)
    if artifacts.hdf5_file is not None:
        write_hdf5_result(result, artifacts.hdf5_file)
    return result


def run_from_config(
    config_path: Path,
    output_dir: Path | None = None,
    *,
    exploratory_command: bool = False,
) -> RunResult:
    """Run a QCchem calculation from a YAML configuration."""
    spec = load_run_spec(config_path)
    _ensure_exploratory_allowed(spec, exploratory_command=exploratory_command)
    return run_spec(spec, source_config=str(config_path), output_dir=output_dir)
