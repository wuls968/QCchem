from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
import yaml
from qiskit.quantum_info import SparsePauliOp

from qcchem.core import WorkflowSpec, WorkflowStepSpec
from qcchem.io.config import load_run_spec
from qcchem.io.workflow_config import validate_workflow_spec
from qcchem.solvers.spectrum import compute_exact_spectrum
from qcchem.workflow.runner import run_spec
from qcchem.workflow.workflow_plugins import WorkflowExecutionContext


@pytest.mark.parametrize("count", [1, 14, 15, 16])
def test_complex_exact_near_full_dimension(count):
    operator = SparsePauliOp.from_list([("ZIII", 1), ("IZII", 2), ("IIZI", 3), ("IIIZ", 4)])
    spectrum = compute_exact_spectrum(operator, count)
    expected = np.linalg.eigvalsh(operator.to_matrix())[:count]
    assert spectrum.eigenvalues == pytest.approx(expected)
    assert spectrum.eigenvectors.shape == (16, count)


def test_exact_preflight_rejects_large_operator_before_matrix(monkeypatch):
    operator = SparsePauliOp.from_list([("Z" * 20, 1)])
    monkeypatch.setattr(SparsePauliOp, "to_matrix", lambda *args, **kwargs: pytest.fail("allocated matrix"))
    with pytest.raises(ValueError, match="limit=16"):
        compute_exact_spectrum(operator, 1)


@pytest.mark.parametrize("section,key,value", [
    ("mapping", "king", "jordan_wigner"), ("backend", "kind", "imaginary_backend"),
    ("backend", "shots", 0), ("backend", "precision", -0.1),
    ("benchmark", "absolute_error_threshold", float("nan")),
    ("run", "overwrite", "false"), ("solver", "kind", "imaginary_solver"),
    ("tasks", "properties", "dipole"),
    ("tasks", "properties", [{"state_indices": [-1]}]),
    ("tasks", "properties", [{"king": "dipole"}]),
])
def test_invalid_configuration_is_rejected_early(tmp_path, section, key, value):
    raw = yaml.safe_load(Path("configs/h2_exact.yaml").read_text())
    raw.setdefault(section, {})[key] = value
    config = tmp_path / "invalid.yaml"
    config.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValueError):
        load_run_spec(config)


@pytest.mark.parametrize("identifier", ["../escaped", "/tmp/escaped", "a/b", "a.b", "..", "a\\b"])
def test_direct_workflow_api_rejects_unsafe_step_ids(identifier):
    with pytest.raises(ValueError, match="step id"):
        validate_workflow_spec(WorkflowSpec(version="1", name="test", steps=[WorkflowStepSpec(id=identifier, kind="compare_artifacts")]))


def test_plugin_outputs_reject_traversal_and_symlinks(tmp_path):
    root = tmp_path / "workflow"
    step = root / "step_outputs" / "safe"
    step.mkdir(parents=True)
    external = tmp_path / "external"
    external.mkdir()
    context = WorkflowExecutionContext(WorkflowSpec(version="1", name="test"), root, step, tmp_path, {}, {})
    for name in ("../escaped.json", str(external / "escaped.json")):
        with pytest.raises(ValueError):
            context.output_path(name)
    (step / "linked").symlink_to(external, target_is_directory=True)
    with pytest.raises(FileExistsError, match="symlink"):
        context.output_path("linked/escaped.json")
    assert not list(external.iterdir())


def test_invalid_and_failed_overwrite_preserve_previous_bundle(tmp_path, monkeypatch):
    root = tmp_path / "existing"
    root.mkdir()
    marker = root / "checkpoint.bin"
    marker.write_bytes(b"valuable-checkpoint")
    spec = load_run_spec(Path("configs/h2_exact.yaml"))
    spec.run.overwrite = True
    invalid = deepcopy(spec)
    invalid.solver.kind = "imaginary_solver"
    with pytest.raises(ValueError):
        run_spec(invalid, source_config="invalid", output_dir=root)
    assert marker.read_bytes() == b"valuable-checkpoint"
    monkeypatch.setattr("qcchem.workflow.runner.build_electronic_structure_context", lambda *_: (_ for _ in ()).throw(RuntimeError("SCF failed")))
    with pytest.raises(RuntimeError, match="SCF failed"):
        run_spec(spec, source_config="failed", output_dir=root)
    assert marker.read_bytes() == b"valuable-checkpoint"
    assert list(tmp_path.glob(".existing.pending-*/run.log"))


def test_successful_overwrite_keeps_backup_and_final_paths(tmp_path):
    root = tmp_path / "existing"
    root.mkdir()
    (root / "checkpoint.bin").write_bytes(b"previous")
    spec = load_run_spec(Path("configs/h2_exact.yaml"))
    spec.run.overwrite = True
    result = run_spec(spec, source_config="overwrite", output_dir=root)
    assert result.artifacts.root == root
    assert result.run_id == "existing"
    assert len(list(tmp_path.glob("existing.backup-*/checkpoint.bin"))) == 1
    assert ".pending-" not in (root / "result.json").read_text()


def test_sector_eigenvector_columns_are_valid_qiskit_inputs():
    from qiskit.quantum_info import Statevector
    from qcchem.chem.problem_builder import build_electronic_structure_context
    from qcchem.mapping.mapper import map_fermionic_hamiltonian
    from qcchem.solvers.sector import molecular_sector

    context = build_electronic_structure_context(load_run_spec(Path('configs/h2_exact.yaml')))
    mapping = map_fermionic_hamiltonian(context.fermionic_hamiltonian, 'jordan_wigner')
    spectrum = compute_exact_spectrum(mapping.qubit_hamiltonian, 3, sector=molecular_sector(context.summary, mapping.mapper))
    for column in spectrum.eigenvectors.T:
        assert column.flags.c_contiguous
        assert Statevector(column).expectation_value(SparsePauliOp('IIII')).real == pytest.approx(1)


def test_missing_hardware_data_stays_unavailable():
    from qcchem.workbench.pages.overview import SAMPLE_RUN_PAYLOAD, _overview_figure
    from qcchem.workbench.viewmodels import build_run_view_model, build_runtime_comparison_model

    payload = deepcopy(SAMPLE_RUN_PAYLOAD)
    payload['runtime_submission'] = None
    payload['runtime_chemical_accuracy'] = None
    model = build_run_view_model(payload)
    comparison = build_runtime_comparison_model(model)
    assert comparison['hardware_error_hartree'] is None
    assert comparison['error_gap_hartree'] is None
    figure = _overview_figure(model)
    assert figure.data[1].y[1] is None
    assert figure.data[0].x == ('Reported calculation',)


def test_real_geometry_and_bohr_conversion_do_not_use_demo_atoms():
    from qcchem.workbench.pages.overview import SAMPLE_RUN_PAYLOAD
    from qcchem.workbench.viewmodels import build_run_view_model

    payload = deepcopy(SAMPLE_RUN_PAYLOAD)
    payload['problem'].update(molecule_name='H2', geometry=[{'symbol': 'H', 'coords': [0, 0, 1]}], geometry_unit='bohr')
    model = build_run_view_model(payload)
    assert model['molecule_viewer']['atoms'] == [{'elem': 'H', 'x': 0.0, 'y': 0.0, 'z': pytest.approx(0.529177210903)}]
    assert model['is_demo'] is False


def test_doctor_reports_interpreter_and_outdated_versions(monkeypatch):
    from importlib import metadata
    from qcchem.diagnostics import environment_diagnostics

    original = metadata.version
    monkeypatch.setattr(metadata, 'version', lambda name: '0.36.1' if name == 'qiskit-ibm-runtime' else original(name))
    report = environment_diagnostics()
    assert report['optional_features']['runtime'] is False
    assert report['dependencies']['qiskit-ibm-runtime']['minimum_version'] == '0.46.0'
    assert report['python']['executable']
    assert report['conda']['interpreter_environment']


def test_doctor_does_not_require_an_undeclared_packaging_dependency(monkeypatch):
    import builtins
    from qcchem.diagnostics import environment_diagnostics

    original = builtins.__import__

    def without_packaging(name, *args, **kwargs):
        if name == 'packaging.version':
            raise ModuleNotFoundError('packaging is unavailable')
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', without_packaging)
    report = environment_diagnostics()
    assert report['dependencies']['qiskit']['compatible'] is True
    assert report['status'] == 'ready'
