"""Benchmark VQE continuation strategies on small scan workflows."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from time import perf_counter
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qcchem.workflow.scan import run_scan_from_config

SYSTEMS = {
    "h2": {
        "base_config": "configs/h2.yaml",
        "values": [0.50, 0.65, 0.735, 0.85, 1.00],
    },
    "lih": {
        "base_config": "configs/lih_active_vqe_statevector.yaml",
        "values": [1.20, 1.40, 1.60, 1.80, 2.00],
    },
}

STRATEGIES = {
    "cold": {"enabled": False, "mode": "previous_optimal"},
    "previous_optimal": {"enabled": True, "mode": "previous_optimal"},
    "linear_predictor": {"enabled": True, "mode": "linear_predictor"},
}


def _selected_values(system: str, points: int) -> list[float]:
    values = list(SYSTEMS[system]["values"])
    if points < 2:
        raise ValueError("--points must be at least 2.")
    if points <= len(values):
        return values[:points]
    start = values[0]
    stop = values[-1]
    step = (stop - start) / float(points - 1)
    return [float(start + index * step) for index in range(points)]


def _write_scan_config(
    path: Path,
    *,
    name: str,
    base_config: str,
    values: list[float],
    enabled: bool,
    mode: str,
) -> None:
    path.write_text(
        "\n".join(
            [
                "scan:",
                f"  name: {name}",
                f"  base_config: {base_config}",
                "  continuity:",
                f"    enabled: {'true' if enabled else 'false'}",
                f"    mode: {mode}",
                "    on_parameter_mismatch: fallback",
                "  parameter:",
                "    name: bond_length",
                "    kind: bond_distance",
                "    atom_indices: [0, 1]",
                "    axis: [0.0, 0.0, 1.0]",
                "    values: [" + ", ".join(str(value) for value in values) + "]",
            ]
        ),
        encoding="utf-8",
    )


def _run_strategy(
    *,
    root: Path,
    system: str,
    strategy: str,
    points: int,
) -> dict[str, Any]:
    values = _selected_values(system, points)
    settings = STRATEGIES[strategy]
    name = f"{system}_{strategy}_{points}pt"
    config_path = root / f"{name}.yaml"
    output_dir = root / name
    _write_scan_config(
        config_path,
        name=name,
        base_config=str(SYSTEMS[system]["base_config"]),
        values=values,
        enabled=bool(settings["enabled"]),
        mode=str(settings["mode"]),
    )
    started = perf_counter()
    result = run_scan_from_config(config_path, output_dir=output_dir)
    elapsed = float(perf_counter() - started)
    payloads = [
        json.loads((point.run_artifact_root / "result.json").read_text(encoding="utf-8"))
        for point in result.points
    ]
    evaluations = [int(item["variational_result"]["evaluations"]) for item in payloads]
    energies = [float(item["energy"]["total_energy"]) for item in payloads]
    strategies = [
        str(item["variational_result"]["initial_point_strategy"]) for item in payloads
    ]
    return {
        "system": system,
        "strategy": strategy,
        "points": points,
        "scan_values": values,
        "elapsed_seconds": elapsed,
        "evaluations": evaluations,
        "evaluation_sum": int(sum(evaluations)),
        "total_energies": energies,
        "initial_point_strategies": strategies,
    }


def _summarize_system(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_strategy = {str(item["strategy"]): item for item in results}
    cold = by_strategy["cold"]
    linear = by_strategy["linear_predictor"]
    previous = by_strategy["previous_optimal"]
    cold_eval = int(cold["evaluation_sum"])
    linear_eval = int(linear["evaluation_sum"])
    previous_eval = int(previous["evaluation_sum"])
    linear_reduction = float((cold_eval - linear_eval) / max(cold_eval, 1))
    previous_reduction = float((cold_eval - previous_eval) / max(cold_eval, 1))
    linear_energy_delta = max(
        abs(float(a) - float(b))
        for a, b in zip(cold["total_energies"], linear["total_energies"])
    )
    previous_energy_delta = max(
        abs(float(a) - float(b))
        for a, b in zip(cold["total_energies"], previous["total_energies"])
    )
    return {
        "system": str(cold["system"]),
        "cold_evaluations": cold_eval,
        "previous_evaluations": previous_eval,
        "linear_evaluations": linear_eval,
        "previous_reduction_fraction": previous_reduction,
        "linear_reduction_fraction": linear_reduction,
        "max_previous_energy_delta_hartree": previous_energy_delta,
        "max_linear_energy_delta_hartree": linear_energy_delta,
        "linear_acceptance": {
            "min_reduction_fraction": 0.10,
            "max_energy_delta_hartree": 1.0e-4,
            "passed": bool(linear_reduction >= 0.10 and linear_energy_delta <= 1.0e-4),
        },
    }


def run_benchmark(*, systems: list[str], points: int, output: Path) -> dict[str, Any]:
    """Run all requested benchmark cases and write a JSON summary."""
    with tempfile.TemporaryDirectory(prefix="qcchem-vqe-continuity-") as tmp:
        root = Path(tmp)
        cases: list[dict[str, Any]] = []
        summaries: list[dict[str, Any]] = []
        for system in systems:
            system_cases = [
                _run_strategy(root=root, system=system, strategy=strategy, points=points)
                for strategy in ("cold", "previous_optimal", "linear_predictor")
            ]
            cases.extend(system_cases)
            summaries.append(_summarize_system(system_cases))
        payload = {
            "schema_version": "qcchem.vqe_continuity_benchmark.v1",
            "points": points,
            "systems": systems,
            "case_results": cases,
            "summaries": summaries,
            "accepted": all(item["linear_acceptance"]["passed"] for item in summaries),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--systems",
        default="h2,lih",
        help="Comma-separated subset of: h2,lih.",
    )
    parser.add_argument("--points", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    systems = [item.strip().lower() for item in args.systems.split(",") if item.strip()]
    unknown = sorted(set(systems) - set(SYSTEMS))
    if unknown:
        raise ValueError(f"Unknown systems: {unknown}")
    payload = run_benchmark(systems=systems, points=args.points, output=args.output)
    print(json.dumps({"accepted": payload["accepted"], "summaries": payload["summaries"]}, indent=2))
    return 0 if payload["accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
