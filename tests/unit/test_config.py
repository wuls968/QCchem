from pathlib import Path

from qcchem.io.config import load_run_spec


def test_load_run_spec_from_yaml() -> None:
    spec = load_run_spec(Path("configs/h2.yaml"))

    assert spec.molecule.name == "H2"
    assert spec.molecule.basis == "sto3g"
    assert spec.molecule.multiplicity == 1
    assert spec.mapping.kind == "jordan_wigner"
    assert spec.backend.kind == "statevector"
    assert spec.solver.kind == "vqe"
    assert spec.benchmark.enabled is True
    assert spec.benchmark.exact_baseline_qubit_limit == 12
    assert spec.run.seed == 7


def test_load_shot_backend_and_mitigation_config() -> None:
    spec = load_run_spec(Path("configs/h2_shot.yaml"))

    assert spec.backend.kind == "shot_estimator"
    assert spec.backend.shots == 4096
    assert spec.backend.seed == 101
    assert spec.backend.repetitions == 5
    assert spec.backend.abelian_grouping is False
    assert spec.mitigation.symmetry_check.enabled is True
    assert spec.mitigation.readout.enabled is False


def test_load_noisy_runtime_and_property_configs() -> None:
    noisy = load_run_spec(Path("configs/h2_noisy.yaml"))
    property_spec = load_run_spec(Path("configs/h2_property_validation.yaml"))

    assert noisy.backend.noise.enabled is True
    assert noisy.backend.noise.profile == "depolarizing_readout"
    assert noisy.backend.runtime.session_ready is True
    assert noisy.backend.runtime.batch_ready is True
    assert property_spec.tasks.excited_state.enabled is True
    assert [item.property_name for item in property_spec.tasks.properties] == [
        "dipole_moment",
        "transition_dipole",
        "oscillator_strength",
    ]


def test_load_runtime_budget_controls_from_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "runtime_budget.yaml"
    config_path.write_text(
        """
molecule:
  name: H2-budget
  geometry:
    - symbol: H
      coords: [0.0, 0.0, 0.0]
    - symbol: H
      coords: [0.0, 0.0, 0.74]

backend:
  kind: shot_estimator
  runtime:
    enabled: true
    service: ibm_quantum_platform
    runtime_ready: true
    precision_target: 0.04
    max_budgeted_shots: 2048
    max_execution_seconds: 240
    calibration_strategy: shot_budget
    options:
      submit_real_job: false

solver:
  kind: vqe

run:
  seed: 9
        """.strip(),
        encoding="utf-8",
    )

    spec = load_run_spec(config_path)

    assert spec.backend.runtime.enabled is True
    assert spec.backend.runtime.precision_target == 0.04
    assert spec.backend.runtime.max_budgeted_shots == 2048
    assert spec.backend.runtime.max_execution_seconds == 240
    assert spec.backend.runtime.calibration_strategy == "shot_budget"


def test_load_h2_chemical_accuracy_push_config() -> None:
    spec = load_run_spec(Path("configs/h2_runtime_hardware_probe_ca.yaml"))

    assert spec.backend.runtime.service == "ibm_quantum_platform"
    assert spec.backend.runtime.max_budgeted_shots == 4096
    assert spec.backend.runtime.max_execution_seconds == 300
    assert spec.backend.runtime.calibration_strategy == "chemical_accuracy_push"
    assert spec.backend.runtime.resilience_level == 2
    assert spec.backend.runtime.options["backend_name"] == "ibm_kingston"
    assert spec.backend.runtime.options["optimization_level"] == 3


def test_load_h2_puccd_hardware_probe_config() -> None:
    spec = load_run_spec(Path("configs/h2_runtime_hardware_probe_puccd.yaml"))

    assert spec.solver.ansatz.kind == "puccd"
    assert spec.backend.runtime.service == "ibm_quantum_platform"
    assert spec.backend.runtime.max_budgeted_shots == 4096
    assert spec.backend.runtime.calibration_strategy == "chemical_accuracy_push"
    assert spec.backend.runtime.options["backend_name"] == "ibm_kingston"


def test_load_h2_puccd_layout_hardware_probe_config() -> None:
    spec = load_run_spec(Path("configs/h2_runtime_hardware_probe_puccd_layout.yaml"))

    assert spec.solver.ansatz.kind == "puccd"
    assert spec.backend.runtime.options["layout_strategy"] == "min_weighted_error"
    assert spec.backend.runtime.options["layout_method"] == "sabre"
    assert spec.backend.runtime.options["routing_method"] == "sabre"
    assert spec.backend.runtime.options["seed_transpiler"] == 727


def test_load_h2_uccsd_layout_hardware_probe_config() -> None:
    spec = load_run_spec(Path("configs/h2_runtime_hardware_probe_ca_layout.yaml"))

    assert spec.solver.ansatz.kind == "uccsd"
    assert spec.backend.runtime.options["layout_strategy"] == "min_weighted_error"
    assert spec.backend.runtime.options["layout_method"] == "sabre"
    assert spec.backend.runtime.options["routing_method"] == "sabre"
    assert spec.backend.runtime.options["seed_transpiler"] == 737


def test_load_h2_puccd_layout_mitigated_hardware_probe_config() -> None:
    spec = load_run_spec(Path("configs/h2_runtime_hardware_probe_puccd_layout_mitigated.yaml"))

    assert spec.solver.ansatz.kind == "puccd"
    assert spec.backend.runtime.max_budgeted_shots == 8192
    assert spec.backend.runtime.options["layout_strategy"] == "min_weighted_error"
    estimator_options = spec.backend.runtime.options["estimator_options"]
    assert estimator_options["dynamical_decoupling"]["enable"] is True
    assert estimator_options["twirling"]["num_randomizations"] == 32
    assert estimator_options["resilience"]["measure_mitigation"] is True


def test_load_h2_puccd_layout_highshots_hardware_probe_config() -> None:
    spec = load_run_spec(Path("configs/h2_runtime_hardware_probe_puccd_layout_highshots.yaml"))

    assert spec.solver.ansatz.kind == "puccd"
    assert spec.backend.runtime.max_budgeted_shots == 8192
    assert spec.backend.runtime.precision_target == 0.01
    assert spec.backend.runtime.resilience_level == 2
    assert spec.backend.runtime.options["layout_strategy"] == "min_weighted_error"
    assert "estimator_options" not in spec.backend.runtime.options


def test_load_h2_runtime_micro_probe_v2_config() -> None:
    spec = load_run_spec(Path("configs/h2_runtime_micro_probe_v2.yaml"))

    assert spec.molecule.name == "H2-runtime-micro-probe-v2"
    assert spec.solver.ansatz.kind == "puccd"
    assert spec.backend.runtime.enabled is True
    assert spec.backend.runtime.service == "ibm_quantum_platform"
    assert spec.backend.runtime.max_budgeted_shots is not None
    assert spec.backend.runtime.max_budgeted_shots <= 1024
    assert spec.backend.runtime.precision_target is not None
    assert spec.backend.runtime.precision_target >= 0.05
    assert spec.backend.runtime.options["submit_real_job"] is True
    assert spec.backend.runtime.options["wait_for_result"] is False
    assert spec.backend.runtime.options["requires_action_time_confirmation"] is True
    assert spec.run.output_dir == Path("artifacts/h2_runtime_micro_probe_v2")
    assert spec.exploratory.enabled is True
    assert "runtime_micro_probe" in spec.exploratory.modules
