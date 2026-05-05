from __future__ import annotations

from pathlib import Path

import yaml

from qcchem.io.config import load_run_spec


def test_load_run_spec_parses_measurement_and_low_rank_runtime_policy(tmp_path: Path) -> None:
    config = {
        "molecule": {
            "name": "LiH-low-rank-runtime-v07",
            "geometry": [
                {"symbol": "Li", "coords": [0.0, 0.0, 0.0]},
                {"symbol": "H", "coords": [0.0, 0.0, 1.6]},
            ],
            "basis": "sto3g",
            "charge": 0,
            "multiplicity": 1,
        },
        "problem": {
            "freeze_core": True,
            "active_space": {
                "num_electrons": 2,
                "num_spatial_orbitals": 2,
            },
            "compression": {
                "enabled": True,
                "method": "modified_cholesky",
                "threshold": 1.0e-3,
                "max_rank": 2,
                "execution_enabled": True,
            },
            "measurement": {
                "strategy": "low_rank_commuting",
                "runtime_precision_target": 5.0e-3,
                "execution_mode": "runtime_estimator",
                "grouping_policy": "commuting_low_rank",
            },
        },
        "mapping": {"kind": "jordan_wigner"},
        "backend": {
            "kind": "shot_estimator",
            "shots": 4096,
            "runtime": {
                "enabled": True,
                "service": "runtime_placeholder",
                "runtime_ready": True,
                "session_ready": True,
                "batch_ready": True,
                "precision_target": 5.0e-3,
                "resilience_level": 1,
                "grouping_policy": "commuting_low_rank",
            },
        },
        "solver": {"kind": "vqe"},
        "run": {"output_dir": str(tmp_path / "artifacts"), "overwrite": True},
    }
    path = tmp_path / "low_rank_runtime.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    spec = load_run_spec(path)

    assert spec.problem.measurement.strategy == "low_rank_commuting"
    assert spec.problem.measurement.runtime_precision_target == 5.0e-3
    assert spec.problem.measurement.grouping_policy == "commuting_low_rank"
    assert spec.backend.runtime.precision_target == 5.0e-3
    assert spec.backend.runtime.resilience_level == 1
    assert spec.backend.runtime.grouping_policy == "commuting_low_rank"
