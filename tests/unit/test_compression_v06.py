from __future__ import annotations

from pathlib import Path

import yaml

from qcchem.chem.compression import _effective_max_rank
from qcchem.core import CompressionSpec
from qcchem.io.config import load_run_spec


def test_load_run_spec_parses_compression_execution_and_exports(tmp_path: Path) -> None:
    config = {
        "molecule": {
            "name": "LiH-compression-v06",
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
        },
        "mapping": {"kind": "jordan_wigner"},
        "backend": {"kind": "statevector"},
        "solver": {"kind": "exact"},
        "run": {
            "seed": 13,
            "output_dir": str(tmp_path / "artifacts"),
            "overwrite": True,
            "exports": {
                "qcschema_json": True,
                "hdf5": True,
            },
        },
    }
    path = tmp_path / "compression_v06.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    spec = load_run_spec(path)

    assert spec.problem.compression.enabled is True
    assert spec.problem.compression.execution_enabled is True
    assert spec.problem.compression.method == "modified_cholesky"
    assert spec.run.exports.qcschema_json is True
    assert spec.run.exports.hdf5 is True


def test_rank_schedule_raises_effective_compression_rank_for_adaptive_runs() -> None:
    spec = CompressionSpec(max_rank=4, rank_schedule=[4, 8, 12])

    assert _effective_max_rank(spec) == 12
