from __future__ import annotations

from pathlib import Path

import pytest

from qcchem.workflow.runner import run_from_config


def _h2_environment_problem(cache_dir: Path, *, compression: bool = False) -> str:
    compression_yaml = ""
    if compression:
        compression_yaml = """
  compression:
    enabled: true
    method: modified_cholesky
    threshold: 1.0e-10
    max_rank: 4
    apply_to_solver: true
    execution_enabled: true
"""
    return f"""
problem:
  environment_embedding:
    enabled: true
    point_charges:
      enabled: true
      unit: angstrom
      charges:
        - label: mm_probe
          coords: [0.0, 0.0, 2.0]
          charge: -0.5
      damping:
        kind: gaussian
        default_radius: 0.4
        radius_unit: angstrom
    cache:
      enabled: true
      directory: {cache_dir}
{compression_yaml}
"""


def _write_config(
    path: Path,
    *,
    solver_yaml: str,
    problem_yaml: str,
    extra_yaml: str = "",
) -> None:
    path.write_text(
        f"""
molecule:
  name: H2-qmmm-solver-surface
  geometry:
    - symbol: H
      coords: [0.0, 0.0, 0.0]
    - symbol: H
      coords: [0.0, 0.0, 0.735]
  charge: 0
  multiplicity: 1
  basis: sto3g
  unit: angstrom
{problem_yaml}
mapping:
  kind: jordan_wigner
backend:
  kind: statevector
{solver_yaml}
benchmark:
  enabled: true
  exact_baseline_qubit_limit: 12
  absolute_error_threshold: 1.0e-3
  relative_error_threshold: 1.0e-3
run:
  seed: 19
  output_dir: artifacts/h2_qmmm_solver_surface
  overwrite: true
{extra_yaml}
        """.strip(),
        encoding="utf-8",
    )


def _assert_environment_auto_z2_skip(result) -> None:
    notes = " ".join(result.mapping.symmetry_reduction_notes)
    assert result.mapping.raw_num_qubits == 4
    assert result.mapping.num_qubits == result.mapping.raw_num_qubits
    assert result.mapping.symmetry_tapered_qubits == 0
    assert result.mapping.symmetry_reduction_status == "disabled"
    assert "environment embedding in auto mode" in notes
    assert "stable QM/MM-like qubit accounting" in notes


@pytest.mark.integration
def test_qmmm_environment_embedding_vqe_surface_keeps_qubit_count_stable(tmp_path: Path) -> None:
    config = tmp_path / "h2_env_vqe.yaml"
    _write_config(
        config,
        problem_yaml=_h2_environment_problem(tmp_path / "cache-vqe"),
        solver_yaml="""
solver:
  kind: vqe
  optimizer:
    kind: COBYLA
    maxiter: 2
  ansatz:
    kind: twolocal
    reps: 1
""",
    )

    result = run_from_config(config, output_dir=tmp_path / "h2-env-vqe")

    assert result.environment_embedding is not None
    assert result.environment_embedding.active_space_projection["environment_qubit_growth"] == 0
    _assert_environment_auto_z2_skip(result)
    assert result.variational_result is not None


@pytest.mark.integration
def test_qmmm_environment_embedding_compressed_exact_surface(tmp_path: Path) -> None:
    config = tmp_path / "h2_env_compressed.yaml"
    _write_config(
        config,
        problem_yaml=_h2_environment_problem(tmp_path / "cache-compression", compression=True),
        solver_yaml="solver:\n  kind: exact\n",
    )

    result = run_from_config(config, output_dir=tmp_path / "h2-env-compressed")

    assert result.environment_embedding is not None
    assert result.environment_embedding.active_space_projection["environment_qubit_growth"] == 0
    assert result.compression_result is not None
    assert result.compression_result.execution_enabled is True
    assert result.benchmark.compressed_vs_uncompressed is not None


@pytest.mark.integration
def test_qmmm_environment_embedding_tc_qsci_surface(tmp_path: Path) -> None:
    config = tmp_path / "h2_env_tc_qsci.yaml"
    _write_config(
        config,
        problem_yaml=_h2_environment_problem(tmp_path / "cache-tc-qsci"),
        solver_yaml="solver:\n  kind: exact\n",
        extra_yaml="""
policy:
  allow_exploratory: true
exploratory:
  enabled: true
  modules: [tc_qsci]
tc_qsci:
  enabled: true
  cast_model:
    kind: identity
  initial_state:
    kind: hf
  kick:
    time: 0.05
    num_kicks: 1
    pauli_term_budget: 8
    shots: 128
  selection:
    max_determinants: 4
    min_count: 1
    symmetry_postselect: true
  resource_estimation:
    enabled: true
    target_precision: 1.0e-3
""",
    )

    result = run_from_config(
        config,
        output_dir=tmp_path / "h2-env-tc-qsci",
        exploratory_command=True,
    )

    assert result.environment_embedding is not None
    assert result.environment_embedding.active_space_projection["environment_qubit_growth"] == 0
    assert result.tc_qsci_result is not None
    assert result.determinant_selection is not None


@pytest.mark.integration
def test_qmmm_environment_embedding_lr_ace_surface(tmp_path: Path) -> None:
    config = tmp_path / "h2_env_lr_ace.yaml"
    _write_config(
        config,
        problem_yaml=_h2_environment_problem(tmp_path / "cache-lr-ace", compression=True),
        solver_yaml="""
solver:
  kind: lr_ace
  experimental: true
  optimizer:
    kind: COBYLA
    maxiter: 40
  ansatz:
    kind: lr_ace
    reps: 1
  initial_point: zeros
""",
        extra_yaml="""
policy:
  allow_exploratory: true
exploratory:
  enabled: true
  modules: [lr_ace]
""",
    )

    result = run_from_config(
        config,
        output_dir=tmp_path / "h2-env-lr-ace",
        exploratory_command=True,
    )

    assert result.environment_embedding is not None
    assert result.environment_embedding.active_space_projection["environment_qubit_growth"] == 0
    assert result.variational_result is not None
    assert result.compression_result is not None
