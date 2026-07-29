"""Capacity benchmark helpers for the exploratory ACE-QVM backend."""

from __future__ import annotations

import json
import math
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from qcchem.workflow.common import prepare_clean_output_root


SCHEMA_VERSION = "qcchem.ace_qvm_capacity_benchmark.v0.1"
DEFAULT_CASES = ("product_x", "cluster_chain")
DEFAULT_SIZES = (128, 512, 2048, 8192, 32768)
CASE_DESCRIPTIONS = {
    "product_x": "H on every qubit, observable X_0; bond dimension should stay 1.",
    "cluster_chain": (
        "H on every qubit plus nearest-neighbor CZ chain, observable X_0 Z_1; "
        "1D graph-state MPS should stay low bond."
    ),
}

_CHILD_CODE = r'''
from __future__ import annotations
import json
import platform
import resource
import sys
import time

from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp

from qcchem.backends.ace_qvm_tn import ACEQVMCapacityError, ACEQVMSettings, simulate_circuit_expectation

case = sys.argv[1]
n = int(sys.argv[2])
memory_budget_gib = float(sys.argv[3])
block_qubits = int(sys.argv[4])
max_bond_dim = int(sys.argv[5])
max_branch_rank = int(sys.argv[6])
settings = ACEQVMSettings(
    memory_budget_gib=memory_budget_gib,
    block_qubits=block_qubits,
    max_bond_dim=max_bond_dim,
    truncation_eps=1.0e-12,
    max_branch_rank=max_branch_rank,
    cross_block_policy="bond",
    routing="swap_network",
    observable_mode="pauli_expectation",
    debug_dense_state_qubit_limit=0,
)

def maxrss_bytes() -> int:
    rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return rss if platform.system() == "Darwin" else rss * 1024

def emit(payload):
    payload["python_maxrss_bytes"] = maxrss_bytes()
    print(json.dumps(payload, sort_keys=True))

if case == "baseline_import":
    emit({"status": "ok", "case": case, "num_qubits": n})
    raise SystemExit(0)

start = time.perf_counter()
try:
    qc = QuantumCircuit(n)
    if case == "product_x":
        for qubit in range(n):
            qc.h(qubit)
        label = "I" * (n - 1) + "X"
        expected = 1.0
    elif case == "cluster_chain":
        for qubit in range(n):
            qc.h(qubit)
        for qubit in range(n - 1):
            qc.cz(qubit, qubit + 1)
        label = "X" if n == 1 else "I" * (n - 2) + "ZX"
        expected = 1.0
    else:
        raise ValueError(f"unknown case: {case}")
    operator = SparsePauliOp.from_list([(label, 1.0)])
    build_seconds = time.perf_counter() - start
    sim_start = time.perf_counter()
    value, metadata = simulate_circuit_expectation(circuit=qc, operator=operator, settings=settings)
    sim_seconds = time.perf_counter() - sim_start
    ledger = metadata["ledger"]
    emit({
        "status": "ok",
        "case": case,
        "num_qubits": n,
        "expected": expected,
        "value": value,
        "abs_error": abs(float(value) - expected),
        "build_seconds": build_seconds,
        "simulate_seconds": sim_seconds,
        "wall_seconds": time.perf_counter() - start,
        "ledger": ledger,
        "partition_blocks": len(metadata["partition"].get("blocks", [])),
        "debug_dense_state_available": metadata.get("debug_dense_state_available"),
    })
except ACEQVMCapacityError as exc:
    emit({
        "status": "capacity_error",
        "case": case,
        "num_qubits": n,
        "message": str(exc),
        "wall_seconds": time.perf_counter() - start,
    })
except Exception as exc:
    emit({
        "status": "error",
        "case": case,
        "num_qubits": n,
        "error_type": type(exc).__name__,
        "message": str(exc),
        "wall_seconds": time.perf_counter() - start,
    })
'''


def parse_size_list(raw: str | None) -> list[int]:
    """Parse a comma-separated positive integer size list."""
    if raw is None or not str(raw).strip():
        return list(DEFAULT_SIZES)
    sizes: list[int] = []
    for item in str(raw).split(","):
        stripped = item.strip()
        if not stripped:
            continue
        value = int(stripped)
        if value <= 0:
            raise ValueError("ACE-QVM capacity benchmark sizes must be positive integers.")
        sizes.append(value)
    if not sizes:
        raise ValueError("ACE-QVM capacity benchmark requires at least one qubit size.")
    return sizes


def _memory_snapshot() -> dict[str, Any]:
    try:
        import psutil  # type: ignore[import-not-found]
    except Exception:
        return {
            "source": "unavailable",
            "total_bytes": None,
            "available_bytes_at_start": None,
            "total_gib": None,
            "available_gib_at_start": None,
        }
    vm = psutil.virtual_memory()
    return {
        "source": "psutil",
        "total_bytes": int(vm.total),
        "available_bytes_at_start": int(vm.available),
        "total_gib": float(vm.total / (1024**3)),
        "available_gib_at_start": float(vm.available / (1024**3)),
    }


def _dense_limit(bytes_available: int | None, working_copies: int) -> int | None:
    if bytes_available is None:
        return None
    usable = max(1, int(bytes_available) // (16 * int(working_copies)))
    return int(math.floor(math.log2(usable)))


def _default_memory_budget_gib(memory: dict[str, Any]) -> float:
    available = memory.get("available_gib_at_start")
    if isinstance(available, int | float) and available > 0.75:
        return float(max(0.5, min(float(available) * 0.75, float(available) - 0.25)))
    return 1.0


def _run_child(
    *,
    case: str,
    num_qubits: int,
    memory_budget_gib: float,
    block_qubits: int,
    max_bond_dim: int,
    max_branch_rank: int,
    timeout_seconds: float,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                _CHILD_CODE,
                case,
                str(num_qubits),
                f"{memory_budget_gib:.12g}",
                str(block_qubits),
                str(max_bond_dim),
                str(max_branch_rank),
            ],
            text=True,
            capture_output=True,
            timeout=float(timeout_seconds),
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "case": case,
            "num_qubits": int(num_qubits),
            "timeout_seconds": float(exc.timeout or timeout_seconds),
            "parent_elapsed_seconds": time.perf_counter() - started,
        }
    if proc.returncode != 0:
        return {
            "status": "process_error",
            "case": case,
            "num_qubits": int(num_qubits),
            "returncode": int(proc.returncode),
            "stdout_tail": proc.stdout[-2000:],
            "stderr_tail": proc.stderr[-4000:],
            "parent_elapsed_seconds": time.perf_counter() - started,
        }
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    payload = json.loads(lines[-1]) if lines else {
        "status": "missing_output",
        "case": case,
        "num_qubits": int(num_qubits),
    }
    payload["parent_elapsed_seconds"] = time.perf_counter() - started
    if proc.stderr.strip():
        payload["stderr_tail"] = proc.stderr[-2000:]
    return payload


def _capacity_summary(results: list[dict[str, Any]], *, dense_four_copy_qubits: int | None) -> dict[str, Any]:
    by_case: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        if result.get("status") == "ok" and result.get("case") in DEFAULT_CASES:
            by_case.setdefault(str(result["case"]), []).append(result)
    observed = {
        case: {
            "max_ok_qubits": max(int(item["num_qubits"]) for item in rows),
            "max_ok_wall_seconds": max(float(item.get("wall_seconds") or 0.0) for item in rows),
            "max_ok_python_maxrss_bytes": max(int(item.get("python_maxrss_bytes") or 0) for item in rows),
            "max_ok_ledger_memory_bytes": max(
                int((item.get("ledger") or {}).get("max_observed_memory_bytes") or 0)
                for item in rows
            ),
            "max_observed_bond_dim": max(
                int((item.get("ledger") or {}).get("max_observed_bond_dim") or 0)
                for item in rows
            ),
            "max_observed_branch_rank": max(
                int((item.get("ledger") or {}).get("max_observed_branch_rank") or 0)
                for item in rows
            ),
        }
        for case, rows in by_case.items()
    }
    max_any = max((item["max_ok_qubits"] for item in observed.values()), default=0)
    comparison: dict[str, Any] = {"max_ace_qvm_qubits_tested": max_any}
    if dense_four_copy_qubits:
        comparison["vs_conservative_dense_four_copy_qubits"] = float(max_any / dense_four_copy_qubits)
        comparison["absolute_qubit_increase_vs_conservative_dense"] = int(max_any - dense_four_copy_qubits)
    else:
        comparison["vs_conservative_dense_four_copy_qubits"] = None
        comparison["absolute_qubit_increase_vs_conservative_dense"] = None
    observed["comparison_to_dense"] = comparison
    return observed


def render_capacity_report(payload: dict[str, Any]) -> str:
    """Render a compact Markdown capacity report."""
    memory = payload["memory"]
    dense = payload["dense_statevector_estimate"]
    observed = payload["observed_capacity"]
    lines = [
        "# ACE-QVM Capacity Benchmark",
        "",
        "## System Memory",
        f"- Total memory: `{memory.get('total_gib')}` GiB",
        f"- Available memory at start: `{memory.get('available_gib_at_start')}` GiB",
        f"- ACE-QVM ledger budget: `{memory.get('ace_qvm_ledger_budget_gib')}` GiB",
        "",
        "## Dense Statevector Estimate",
        f"- Single complex128 statevector theoretical limit: `{dense.get('single_vector_theoretical_qubits_at_available_memory')}` qubits",
        f"- Two working copies estimate: `{dense.get('two_working_copies_qubits_at_available_memory')}` qubits",
        f"- Four working copies conservative estimate: `{dense.get('four_working_copies_conservative_qubits_at_available_memory')}` qubits",
        "",
        "## Observed ACE-QVM Capacity",
    ]
    for case in DEFAULT_CASES:
        capacity = observed.get(case)
        if not isinstance(capacity, dict):
            continue
        lines.extend(
            [
                f"### {case}",
                f"- Max OK qubits tested: `{capacity['max_ok_qubits']}`",
                f"- Max OK wall time: `{capacity['max_ok_wall_seconds']}` s",
                f"- Max child RSS bytes: `{capacity['max_ok_python_maxrss_bytes']}`",
                f"- Max ledger tensor memory bytes: `{capacity['max_ok_ledger_memory_bytes']}`",
                f"- Max bond dimension: `{capacity['max_observed_bond_dim']}`",
                f"- Max branch rank: `{capacity['max_observed_branch_rank']}`",
                "",
            ]
        )
    comparison = observed.get("comparison_to_dense") or {}
    lines.extend(
        [
            "## Lift vs Dense Estimate",
            f"- Max ACE-QVM qubits tested: `{comparison.get('max_ace_qvm_qubits_tested')}`",
            f"- Increase vs conservative dense estimate: `{comparison.get('absolute_qubit_increase_vs_conservative_dense')}` qubits",
            f"- Ratio vs conservative dense estimate: `{comparison.get('vs_conservative_dense_four_copy_qubits')}`x",
            "",
            "## Boundary",
            "- This benchmark is a low-entanglement observable workload, not a volume-law arbitrary-circuit claim.",
            "- Dense statevector limits are formula estimates only; no near-OOM dense allocation is attempted.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_ace_qvm_capacity_benchmark(
    *,
    output_dir: Path,
    sizes: list[int] | tuple[int, ...] | None = None,
    cases: list[str] | tuple[str, ...] | None = None,
    memory_budget_gib: float | None = None,
    block_qubits: int = 64,
    max_bond_dim: int = 64,
    max_branch_rank: int = 64,
    timeout_seconds: float = 120.0,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Run ACE-QVM low-entanglement capacity probes and write JSON/Markdown artifacts."""
    selected_sizes = list(DEFAULT_SIZES if sizes is None else sizes)
    selected_cases = list(DEFAULT_CASES if cases is None else cases)
    if not selected_sizes or any(int(size) <= 0 for size in selected_sizes):
        raise ValueError("ACE-QVM capacity benchmark sizes must be positive integers.")
    unknown_cases = [case for case in selected_cases if case not in DEFAULT_CASES]
    if unknown_cases:
        raise ValueError(f"Unsupported ACE-QVM capacity benchmark case(s): {unknown_cases}")
    if block_qubits <= 0 or max_bond_dim <= 0 or max_branch_rank <= 0:
        raise ValueError("ACE-QVM capacity benchmark resource limits must be positive.")
    if timeout_seconds <= 0:
        raise ValueError("ACE-QVM capacity benchmark timeout must be positive.")

    artifact_root = prepare_clean_output_root(output_dir, workflow_name="ACE-QVM capacity benchmark", overwrite=overwrite)
    memory = _memory_snapshot()
    budget = float(memory_budget_gib) if memory_budget_gib is not None else _default_memory_budget_gib(memory)
    if budget <= 0.0:
        raise ValueError("ACE-QVM capacity benchmark memory budget must be positive.")

    results = [
        _run_child(
            case="baseline_import",
            num_qubits=0,
            memory_budget_gib=budget,
            block_qubits=block_qubits,
            max_bond_dim=max_bond_dim,
            max_branch_rank=max_branch_rank,
            timeout_seconds=timeout_seconds,
        )
    ]
    for case in selected_cases:
        for size in selected_sizes:
            result = _run_child(
                case=case,
                num_qubits=int(size),
                memory_budget_gib=budget,
                block_qubits=block_qubits,
                max_bond_dim=max_bond_dim,
                max_branch_rank=max_branch_rank,
                timeout_seconds=timeout_seconds,
            )
            results.append(result)
            if result.get("status") != "ok":
                break

    available_bytes = memory.get("available_bytes_at_start")
    dense = {
        "complex128_bytes_per_amplitude": 16,
        "single_vector_theoretical_qubits_at_available_memory": _dense_limit(available_bytes, 1),
        "two_working_copies_qubits_at_available_memory": _dense_limit(available_bytes, 2),
        "four_working_copies_conservative_qubits_at_available_memory": _dense_limit(available_bytes, 4),
        "note": "Formula only; no large dense state allocation was attempted.",
    }
    memory["ace_qvm_ledger_budget_gib"] = budget
    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "artifact_root": str(artifact_root),
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python": sys.version.split()[0],
        },
        "memory": memory,
        "dense_statevector_estimate": dense,
        "settings": {
            "block_qubits": int(block_qubits),
            "max_bond_dim": int(max_bond_dim),
            "max_branch_rank": int(max_branch_rank),
            "cross_block_policy": "bond",
            "debug_dense_state_qubit_limit": 0,
        },
        "cases": {case: CASE_DESCRIPTIONS[case] for case in selected_cases},
        "results": results,
    }
    payload["observed_capacity"] = _capacity_summary(
        results,
        dense_four_copy_qubits=dense["four_working_copies_conservative_qubits_at_available_memory"],
    )
    outputs = {
        "benchmark_json": str(artifact_root / "benchmark.json"),
        "benchmark_markdown": str(artifact_root / "benchmark.md"),
    }
    payload["outputs"] = outputs
    (artifact_root / "benchmark.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (artifact_root / "benchmark.md").write_text(render_capacity_report(payload), encoding="utf-8")
    return payload
