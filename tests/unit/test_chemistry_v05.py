from __future__ import annotations

from pathlib import Path

import yaml

from qcchem.io.config import load_run_spec


def test_load_run_spec_parses_active_space_compression_and_embedding(tmp_path: Path) -> None:
    config = {
        "molecule": {
            "name": "LiH-chem-v05",
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
            "remove_orbitals": [4],
            "active_space": {
                "selection_mode": "auto",
                "num_spatial_orbitals": 2,
                "auto": {
                    "enabled": True,
                    "strategy": "frontier_orbitals",
                    "num_occupied": 1,
                    "num_virtual": 1,
                },
            },
            "compression": {
                "enabled": True,
                "method": "modified_cholesky",
                "threshold": 1.0e-8,
                "max_rank": 8,
            },
            "embedding": {
                "enabled": True,
                "method": "dmet_skeleton",
                "bath_threshold": 0.05,
                "fragments": [
                    {"name": "Li_frag", "atom_indices": [0]},
                    {"name": "H_frag", "atom_indices": [1]},
                ],
            },
        },
        "mapping": {"kind": "jordan_wigner"},
        "backend": {"kind": "statevector"},
        "solver": {"kind": "exact"},
        "tasks": {
            "perturbative_correction": {
                "enabled": True,
                "method": "nevpt2",
                "plugin": "pyscf",
                "root": 0,
            }
        },
        "run": {"seed": 7, "output_dir": str(tmp_path / "artifacts"), "overwrite": True},
    }
    path = tmp_path / "chem_v05.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    spec = load_run_spec(path)

    assert spec.problem.freeze_core is True
    assert spec.problem.remove_orbitals == [4]
    assert spec.problem.active_space is not None
    assert spec.problem.active_space.selection_mode == "auto"
    assert spec.problem.active_space.auto.enabled is True
    assert spec.problem.compression.enabled is True
    assert spec.problem.compression.method == "modified_cholesky"
    assert spec.problem.embedding.enabled is True
    assert len(spec.problem.embedding.fragments) == 2
    assert spec.tasks.perturbative_correction.enabled is True
    assert spec.tasks.perturbative_correction.method == "nevpt2"

