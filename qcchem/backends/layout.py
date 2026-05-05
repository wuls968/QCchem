"""Backend-aware physical layout recommendation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import inf
from typing import Iterable


@dataclass(slots=True)
class LayoutPlan:
    """Recommended physical layout for a small hardware execution."""

    strategy: str
    selected_layout: list[int]
    score: float
    readout_score: float
    entangling_score: float
    connected_edge_count: int


def _normalize_edge(edge: tuple[int, int]) -> tuple[int, int]:
    return (int(edge[0]), int(edge[1])) if edge[0] <= edge[1] else (int(edge[1]), int(edge[0]))


def _adjacency(edges: Iterable[tuple[int, int]]) -> dict[int, set[int]]:
    graph: dict[int, set[int]] = {}
    for raw_u, raw_v in edges:
        u, v = _normalize_edge((raw_u, raw_v))
        graph.setdefault(u, set()).add(v)
        graph.setdefault(v, set()).add(u)
    return graph


def _is_connected_subset(nodes: tuple[int, ...], graph: dict[int, set[int]]) -> bool:
    if not nodes:
        return False
    allowed = set(nodes)
    stack = [nodes[0]]
    seen = set()
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        for neighbour in graph.get(node, set()):
            if neighbour in allowed and neighbour not in seen:
                stack.append(neighbour)
    return seen == allowed


def _mst_for_subset(
    nodes: tuple[int, ...],
    graph: dict[int, set[int]],
    two_qubit_errors: dict[tuple[int, int], float],
) -> tuple[float, list[tuple[int, int]]]:
    allowed = set(nodes)
    candidate_edges: list[tuple[float, tuple[int, int]]] = []
    for u in allowed:
        for v in graph.get(u, set()):
            if v not in allowed or u >= v:
                continue
            edge = (u, v)
            candidate_edges.append((float(two_qubit_errors.get(edge, 1.0)), edge))
    candidate_edges.sort(key=lambda item: (item[0], item[1]))
    parent = {node: node for node in allowed}

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(a: int, b: int) -> bool:
        root_a = find(a)
        root_b = find(b)
        if root_a == root_b:
            return False
        parent[root_b] = root_a
        return True

    total = 0.0
    selected: list[tuple[int, int]] = []
    for weight, edge in candidate_edges:
        if union(*edge):
            selected.append(edge)
            total += weight
            if len(selected) == len(nodes) - 1:
                break
    if len(selected) != len(nodes) - 1:
        return inf, []
    return total, selected


def _layout_order(
    nodes: tuple[int, ...],
    mst_edges: list[tuple[int, int]],
    *,
    readout_errors: dict[int, float],
    two_qubit_errors: dict[tuple[int, int], float],
) -> list[int]:
    if not mst_edges:
        return list(nodes)
    tree = _adjacency(mst_edges)
    root = min(nodes, key=lambda node: (float(readout_errors.get(node, 0.0)), node))
    ordered: list[int] = []
    seen: set[int] = set()

    def visit(node: int, parent: int | None) -> None:
        seen.add(node)
        ordered.append(node)
        neighbours = [item for item in tree.get(node, set()) if item != parent]
        neighbours.sort(
            key=lambda item: (
                float(two_qubit_errors.get(_normalize_edge((node, item)), 1.0)),
                float(readout_errors.get(item, 0.0)),
                item,
            )
        )
        for neighbour in neighbours:
            if neighbour not in seen:
                visit(neighbour, node)

    visit(root, None)
    for node in sorted(nodes):
        if node not in seen:
            ordered.append(node)
    return ordered


def recommend_initial_layout_from_errors(
    *,
    num_qubits: int,
    coupling_edges: Iterable[tuple[int, int]],
    readout_errors: dict[int, float],
    two_qubit_errors: dict[tuple[int, int], float],
    strategy: str = "min_weighted_error",
) -> LayoutPlan | None:
    """Recommend a connected physical-qubit subset from backend error metadata."""
    normalized_strategy = str(strategy).strip().lower()
    if normalized_strategy != "min_weighted_error":
        raise ValueError(f"Unsupported layout strategy: {strategy}")

    normalized_edges = [_normalize_edge(edge) for edge in coupling_edges]
    graph = _adjacency(normalized_edges)
    physical_qubits = sorted({node for edge in normalized_edges for node in edge} | set(readout_errors))
    if len(physical_qubits) < num_qubits:
        return None

    best: LayoutPlan | None = None
    for subset in combinations(physical_qubits, num_qubits):
        if not _is_connected_subset(subset, graph):
            continue
        entangling_score, mst_edges = _mst_for_subset(subset, graph, two_qubit_errors)
        if entangling_score == inf:
            continue
        readout_score = float(sum(float(readout_errors.get(node, 0.0)) for node in subset))
        score = float(entangling_score + readout_score / max(num_qubits, 1))
        layout = _layout_order(
            subset,
            mst_edges,
            readout_errors=readout_errors,
            two_qubit_errors=two_qubit_errors,
        )
        candidate = LayoutPlan(
            strategy=normalized_strategy,
            selected_layout=layout,
            score=score,
            readout_score=readout_score,
            entangling_score=float(entangling_score),
            connected_edge_count=len(mst_edges),
        )
        if best is None or candidate.score < best.score - 1.0e-15:
            best = candidate
        elif best is not None and abs(candidate.score - best.score) <= 1.0e-15:
            if tuple(candidate.selected_layout) < tuple(best.selected_layout):
                best = candidate
    return best


def _backend_num_qubits(backend) -> int:
    if getattr(backend, "num_qubits", None) is not None:
        return int(backend.num_qubits)
    target = getattr(backend, "target", None)
    if target is not None and getattr(target, "num_qubits", None) is not None:
        return int(target.num_qubits)
    coupling_map = getattr(backend, "coupling_map", None)
    if coupling_map is not None:
        edges = list(coupling_map.get_edges())
        if edges:
            return max(max(edge) for edge in edges) + 1
    return 0


def _extract_readout_errors(backend) -> dict[int, float]:
    num_qubits = _backend_num_qubits(backend)
    readout_errors = {index: 0.0 for index in range(num_qubits)}
    properties = None
    try:
        if hasattr(backend, "properties"):
            properties = backend.properties()
    except Exception:
        properties = None
    if properties is not None:
        for index in range(num_qubits):
            try:
                error = properties.readout_error(index)
            except Exception:
                error = None
            if error is not None:
                readout_errors[index] = float(error)
    return readout_errors


def _extract_two_qubit_errors(backend, coupling_edges: Iterable[tuple[int, int]]) -> dict[tuple[int, int], float]:
    preferred_gates = ("cz", "ecr", "cx")
    normalized_edges = [_normalize_edge(edge) for edge in coupling_edges]
    edge_errors: dict[tuple[int, int], float] = {}
    properties = None
    try:
        if hasattr(backend, "properties"):
            properties = backend.properties()
    except Exception:
        properties = None
    if properties is not None:
        for edge in normalized_edges:
            u, v = edge
            for gate in preferred_gates:
                for directed in ((u, v), (v, u)):
                    try:
                        error = properties.gate_error(gate, list(directed))
                    except Exception:
                        error = None
                    if error is not None:
                        edge_errors[edge] = float(error)
                        break
                if edge in edge_errors:
                    break

    target = getattr(backend, "target", None)
    if target is not None:
        for gate in preferred_gates:
            if gate not in getattr(target, "operation_names", []):
                continue
            for qargs, instruction_properties in target[gate].items():
                if instruction_properties is None or getattr(instruction_properties, "error", None) is None:
                    continue
                edge = _normalize_edge(tuple(int(item) for item in qargs))
                edge_errors.setdefault(edge, float(instruction_properties.error))
    return edge_errors


def recommend_initial_layout(backend, num_qubits: int, *, strategy: str = "min_weighted_error") -> LayoutPlan | None:
    """Recommend an initial layout from a backend object."""
    coupling_map = getattr(backend, "coupling_map", None)
    if coupling_map is None:
        return None
    coupling_edges = list(coupling_map.get_edges())
    if not coupling_edges:
        return None
    return recommend_initial_layout_from_errors(
        num_qubits=num_qubits,
        coupling_edges=coupling_edges,
        readout_errors=_extract_readout_errors(backend),
        two_qubit_errors=_extract_two_qubit_errors(backend, coupling_edges),
        strategy=strategy,
    )
