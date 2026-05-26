from __future__ import annotations

from pathlib import Path

import pytest

from qcchem.io.config import load_run_spec


def _write_qft_config(path: Path, *, shape: str = "[2]", spacing: str = "[0.75]") -> None:
    path.write_text(
        f"""
molecule:
  name: H2-lattice-qed-config
  geometry:
    - symbol: H
      coords: [0.0, 0.0, 0.0]
    - symbol: H
      coords: [0.0, 0.0, 0.74]

policy:
  name: benchmark
  allow_exploratory: true

exploratory:
  enabled: true
  modules:
    - lattice_qed

problem:
  qft:
    enabled: true
    model: lattice_qed_minimal_coupling
    dimensions: 1
    grid:
      shape: {shape}
      spacing: {spacing}
      origin: molecule_center
      axes: principal
      boundary: open
      softening: 0.35
    matter:
      spin_components: 2
      target_electrons: auto
      include_soft_coulomb_density: false
    gauge:
      group: u1
      electric_cutoff: 1
      coupling: 1.0
      include_magnetic_plaquettes: true
    constraints:
      gauss_law_penalty: 10.0
      particle_number_penalty: 10.0
      padding_penalty: 50.0
      enforce_physical_sector: true
      target_charge_sector: neutral
      gauss_law_tolerance: 1.0e-8
      max_sector_enumeration_qubits: 8
    ansatz:
      generator_policy: gauge_invariant_hopping
    dynamics:
      enabled: true
      method: real_time_quench
      initial_state:
        kind: local_hopping_pulse
        base: physical_reference
        link_index: 0
        pulse_time: 0.05
        pulse_strength: 1.0
      time_grid:
        start: 0.0
        stop: 2.0
        num_points: 41
      evolution:
        exact_enabled: true
        exact_qubit_limit: 12
        trotter_enabled: true
        trotter_step: 0.05
        trotter_order: 1
      runtime:
        enabled: true
        runtime_observables: aggregate_gauge

mapping:
  kind: jordan_wigner

backend:
  kind: statevector

solver:
  kind: exact

run:
  output_dir: artifacts/test_lattice_qed_config
  overwrite: true
        """.strip(),
        encoding="utf-8",
    )


def test_load_run_spec_parses_lattice_qed_defaults(tmp_path: Path) -> None:
    config = tmp_path / "qft.yaml"
    _write_qft_config(config)

    spec = load_run_spec(config)

    assert spec.problem.qft.enabled is True
    assert spec.problem.qft.model == "lattice_qed_minimal_coupling"
    assert spec.problem.qft.dimensions == 1
    assert spec.problem.qft.grid.shape == [2]
    assert spec.problem.qft.grid.spacing == [0.75]
    assert spec.problem.qft.grid.origin == "molecule_center"
    assert spec.problem.qft.grid.axes == "principal"
    assert spec.problem.qft.matter.target_electrons == "auto"
    assert spec.problem.qft.gauge.electric_cutoff == 1
    assert spec.problem.qft.constraints.gauss_law_penalty == 10.0
    assert spec.problem.qft.constraints.enforce_physical_sector is True
    assert spec.problem.qft.constraints.target_charge_sector == "neutral"
    assert spec.problem.qft.constraints.gauss_law_tolerance == pytest.approx(1.0e-8)
    assert spec.problem.qft.constraints.max_sector_enumeration_qubits == 8
    assert spec.problem.qft.ansatz.generator_policy == "gauge_invariant_hopping"
    assert spec.problem.qft.engine.representation == "auto"
    assert spec.problem.qft.engine.auto_project_physical_sector is True
    assert spec.problem.qft.engine.projected_builder == "auto"
    assert spec.problem.qft.engine.max_projected_dimension == 4096
    assert spec.problem.qft.engine.max_full_qubits_for_dense == 10
    assert spec.problem.qft.engine.materialize_pauli == "auto"
    assert spec.problem.qft.engine.store_basis_indices == "preview"
    assert spec.problem.qft.engine.projector_tolerance == pytest.approx(1.0e-8)
    assert spec.problem.qft.dynamics.enabled is True
    assert spec.problem.qft.dynamics.method == "real_time_quench"
    assert spec.problem.qft.dynamics.initial_state.kind == "local_hopping_pulse"
    assert spec.problem.qft.dynamics.initial_state.base == "physical_reference"
    assert spec.problem.qft.dynamics.initial_state.link_index == 0
    assert spec.problem.qft.dynamics.initial_state.pulse_time == pytest.approx(0.05)
    assert spec.problem.qft.dynamics.time_grid.num_points == 41
    assert spec.problem.qft.dynamics.evolution.trotter_step == pytest.approx(0.05)
    assert spec.problem.qft.dynamics.runtime.enabled is True
    assert spec.problem.qft.dynamics.runtime.runtime_observables == "aggregate_gauge"
    assert spec.problem.qft.dynamics.runtime.time_point_indices is None
    assert spec.problem.qft.dynamics.runtime.observable_names is None


def test_lattice_qed_grid_shape_must_match_dimensions(tmp_path: Path) -> None:
    config = tmp_path / "bad_qft.yaml"
    _write_qft_config(config, shape="[2, 2]", spacing="[0.75]")

    with pytest.raises(ValueError, match="problem.qft.grid.shape"):
        load_run_spec(config)


def test_lattice_qed_engine_parses_sparse_projected_options(tmp_path: Path) -> None:
    config = tmp_path / "qft_engine.yaml"
    _write_qft_config(config)
    text = config.read_text(encoding="utf-8")
    text = text.replace(
        "    dynamics:\n",
        """    engine:
      representation: sparse_projected
      auto_project_physical_sector: true
      projected_builder: sector_first
      max_projected_dimension: 128
      max_full_qubits_for_dense: 6
      materialize_pauli: never
      store_basis_indices: hash_only
      projector_tolerance: 1.0e-9
    dynamics:\n""",
    )
    config.write_text(text, encoding="utf-8")

    spec = load_run_spec(config)

    assert spec.problem.qft.engine.representation == "sparse_projected"
    assert spec.problem.qft.engine.projected_builder == "sector_first"
    assert spec.problem.qft.engine.max_projected_dimension == 128
    assert spec.problem.qft.engine.max_full_qubits_for_dense == 6
    assert spec.problem.qft.engine.materialize_pauli == "never"
    assert spec.problem.qft.engine.store_basis_indices == "hash_only"
    assert spec.problem.qft.engine.projector_tolerance == pytest.approx(1.0e-9)


def test_lattice_qed_runtime_parses_micro_batch_limits(tmp_path: Path) -> None:
    config = tmp_path / "qft_runtime_limits.yaml"
    _write_qft_config(config)
    text = config.read_text(encoding="utf-8")
    text = text.replace(
        "        runtime_observables: aggregate_gauge\n",
        """        runtime_observables: aggregate_gauge
        time_point_indices: [0, 10]
        observable_names: [particle_number, total_gauss_violation]
        max_pub_count: 4
        max_total_pub_shots: 2048
        max_logical_depth: 200
""",
    )
    config.write_text(text, encoding="utf-8")

    spec = load_run_spec(config)

    runtime = spec.problem.qft.dynamics.runtime
    assert runtime.time_point_indices == [0, 10]
    assert runtime.observable_names == ["particle_number", "total_gauss_violation"]
    assert runtime.max_pub_count == 4
    assert runtime.max_total_pub_shots == 2048
    assert runtime.max_logical_depth == 200


def test_lattice_qed_engine_rejects_invalid_materialization_policy(tmp_path: Path) -> None:
    config = tmp_path / "bad_qft_engine.yaml"
    _write_qft_config(config)
    text = config.read_text(encoding="utf-8")
    text = text.replace(
        "    dynamics:\n",
        """    engine:
      representation: sparse_projected
      materialize_pauli: sometimes
    dynamics:\n""",
    )
    config.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match="problem.qft.engine.materialize_pauli"):
        load_run_spec(config)
