from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.workflow.benchmark import run_benchmark_suite_from_config
from qcchem.workflow.runner import run_from_config


@pytest.mark.integration
def test_compressed_exact_execution_persists_comparison_and_exports(tmp_path: Path) -> None:
    result = run_from_config(
        Path("configs/lih_active_exact_compressed_cholesky.yaml"),
        output_dir=tmp_path / "lih-compressed-exact",
    )

    assert result.compression_result is not None
    assert result.compression_result.execution_enabled is True
    assert result.compression_result.pre_term_count >= result.compression_result.post_term_count
    assert result.benchmark.compressed_vs_uncompressed is not None
    assert result.benchmark.compressed_vs_uncompressed.available is True
    assert result.benchmark.compressed_vs_uncompressed.absolute_error is not None
    assert result.artifacts.qcschema_json is not None and result.artifacts.qcschema_json.exists()
    assert result.artifacts.hdf5_file is not None and result.artifacts.hdf5_file.exists()


@pytest.mark.integration
def test_compression_benchmark_suite_reports_four_lih_cases(tmp_path: Path) -> None:
    result = run_benchmark_suite_from_config(
        Path("benchmarks/compression_suite_v1.yaml"),
        output_dir=tmp_path / "compression-suite",
    )

    case_names = {case.name for case in result.cases}
    assert case_names == {
        "lih_active_exact_uncompressed",
        "lih_active_exact_compressed",
        "lih_active_vqe_uncompressed",
        "lih_active_vqe_compressed",
    }
    assert all("compression_method" in case.metrics for case in result.cases)
    assert any(case.metrics.get("execution_enabled") is True for case in result.cases)


@pytest.mark.integration
def test_auto_active_space_compressed_nevpt2_workflow_tracks_split_energies(tmp_path: Path) -> None:
    result = run_from_config(
        Path("configs/lih_auto_compressed_nevpt2.yaml"),
        output_dir=tmp_path / "lih-auto-compressed-nevpt2",
    )

    assert result.compression_result is not None
    assert result.perturbative_correction_result is not None
    assert result.perturbative_correction_result.reduced_active_space_energy is not None
    assert result.perturbative_correction_result.compressed_active_space_energy is not None
    assert result.perturbative_correction_result.corrected_total_energy == pytest.approx(
        result.perturbative_correction_result.compressed_active_space_energy
        + result.perturbative_correction_result.perturbative_correction,
        abs=1e-8,
    )
    payload = json.loads(result.artifacts.result_json.read_text(encoding="utf-8"))
    assert payload["benchmark"]["compressed_vs_uncompressed"]["available"] is True
    assert payload["perturbative_correction_result"]["plugin"] == "pyscf"
