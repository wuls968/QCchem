from pathlib import Path

import yaml

from qcchem.io.config import load_run_spec


def test_run_spec_parses_exploratory_gate(tmp_path: Path) -> None:
    config = {
        "molecule": {
            "name": "H2",
            "geometry": [
                {"symbol": "H", "coords": [0.0, 0.0, 0.0]},
                {"symbol": "H", "coords": [0.0, 0.0, 0.74]},
            ],
        },
        "solver": {
            "kind": "vqd",
            "experimental": True,
        },
        "policy": {
            "name": "benchmark",
            "allow_exploratory": True,
        },
        "exploratory": {
            "enabled": True,
            "modules": ["solvers.vqd"],
            "notes": ["manual opt-in"],
        },
    }
    path = tmp_path / "exploratory.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")

    spec = load_run_spec(path)

    assert spec.solver.experimental is True
    assert spec.policy.allow_exploratory is True
    assert spec.exploratory.enabled is True
    assert spec.exploratory.modules == ["solvers.vqd"]


def test_run_result_defaults_keep_core_origin() -> None:
    from qcchem.core.results import RunResult

    assert "module_origin" in RunResult.__dataclass_fields__
    assert "capability_tier" in RunResult.__dataclass_fields__
