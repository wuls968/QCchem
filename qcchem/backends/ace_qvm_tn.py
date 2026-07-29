"""Tensor-network core for the exploratory ACE-QVM backend."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp


class ACEQVMCapacityError(RuntimeError):
    """Raised when ACE-QVM cannot execute within configured resource limits."""


_IDENTITY = np.eye(2, dtype=complex)
_PAULI = {
    "I": _IDENTITY,
    "X": np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=complex),
    "Y": np.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex),
    "Z": np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=complex),
}
_SWAP = np.asarray(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ],
    dtype=complex,
)
_CLIFFORD_GATES = {"id", "x", "y", "z", "h", "s", "sdg", "cx", "cy", "cz", "swap"}


@dataclass(slots=True)
class ACEQVMLedger:
    """Resource and approximation ledger for one ACE-QVM evaluation."""

    gate_counts: dict[str, int] = field(default_factory=dict)
    single_qubit_gate_count: int = 0
    two_qubit_gate_count: int = 0
    routed_swap_count: int = 0
    cross_block_gate_count: int = 0
    cut_gate_count: int = 0
    branch_prune_events: int = 0
    svd_truncation_events: int = 0
    total_discarded_svd_weight: float = 0.0
    total_pruned_branch_weight: float = 0.0
    max_observed_bond_dim: int = 1
    max_observed_branch_rank: int = 1
    max_observed_memory_bytes: int = 0
    capacity_status: str = "within_budget"
    notes: list[str] = field(default_factory=list)

    def record_gate(self, name: str, width: int) -> None:
        normalized = str(name).strip().lower()
        self.gate_counts[normalized] = int(self.gate_counts.get(normalized, 0)) + 1
        if width == 1:
            self.single_qubit_gate_count += 1
        elif width == 2:
            self.two_qubit_gate_count += 1

    def record_svd(
        self,
        singular_values: np.ndarray,
        kept: int,
        discarded_weight: float,
        *,
        over_error_budget: bool,
    ) -> None:
        kept_values = singular_values[:kept]
        observed = int(len(kept_values))
        self.max_observed_bond_dim = max(self.max_observed_bond_dim, observed)
        if discarded_weight > 0.0:
            self.svd_truncation_events += 1
            self.total_discarded_svd_weight += float(discarded_weight)
            if over_error_budget and self.capacity_status == "within_budget":
                self.capacity_status = "approximate_svd_truncated"

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_counts": dict(self.gate_counts),
            "single_qubit_gate_count": int(self.single_qubit_gate_count),
            "two_qubit_gate_count": int(self.two_qubit_gate_count),
            "routed_swap_count": int(self.routed_swap_count),
            "cross_block_gate_count": int(self.cross_block_gate_count),
            "cut_gate_count": int(self.cut_gate_count),
            "branch_prune_events": int(self.branch_prune_events),
            "svd_truncation_events": int(self.svd_truncation_events),
            "total_discarded_svd_weight": float(self.total_discarded_svd_weight),
            "total_pruned_branch_weight": float(self.total_pruned_branch_weight),
            "max_observed_bond_dim": int(self.max_observed_bond_dim),
            "max_observed_branch_rank": int(self.max_observed_branch_rank),
            "max_observed_memory_bytes": int(self.max_observed_memory_bytes),
            "capacity_status": self.capacity_status,
            "notes": list(self.notes),
        }


@dataclass(slots=True)
class ACEQVMSettings:
    """Normalized ACE-QVM execution settings."""

    memory_budget_gib: float = 4.0
    block_qubits: int = 8
    max_bond_dim: int = 64
    truncation_eps: float = 1.0e-8
    max_branch_rank: int = 16
    cross_block_policy: str = "auto"
    routing: str = "swap_network"
    observable_mode: str = "pauli_expectation"
    debug_dense_state_qubit_limit: int = 10

    @property
    def memory_budget_bytes(self) -> int:
        return int(float(self.memory_budget_gib) * (1024**3))

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_budget_gib": float(self.memory_budget_gib),
            "block_qubits": int(self.block_qubits),
            "max_bond_dim": int(self.max_bond_dim),
            "truncation_eps": float(self.truncation_eps),
            "max_branch_rank": int(self.max_branch_rank),
            "cross_block_policy": str(self.cross_block_policy),
            "routing": str(self.routing),
            "observable_mode": str(self.observable_mode),
            "debug_dense_state_qubit_limit": int(self.debug_dense_state_qubit_limit),
        }


class MPSState:
    """Small, deterministic open-boundary MPS state with logical-qubit routing."""

    def __init__(self, num_qubits: int) -> None:
        self.num_qubits = int(num_qubits)
        self.tensors = []
        for _ in range(self.num_qubits):
            tensor = np.zeros((1, 2, 1), dtype=complex)
            tensor[0, 0, 0] = 1.0
            self.tensors.append(tensor)
        self.qubit_at_site = list(range(self.num_qubits))
        self.site_for_qubit = {index: index for index in range(self.num_qubits)}
        self._memory_bytes = int(sum(tensor.nbytes for tensor in self.tensors))
        self._max_bond_dim = 1

    def copy(self) -> "MPSState":
        copied = MPSState(self.num_qubits)
        copied.tensors = [tensor.copy() for tensor in self.tensors]
        copied.qubit_at_site = list(self.qubit_at_site)
        copied.site_for_qubit = dict(self.site_for_qubit)
        copied._memory_bytes = int(self._memory_bytes)
        copied._max_bond_dim = int(self._max_bond_dim)
        return copied

    def memory_bytes(self) -> int:
        return int(self._memory_bytes)

    def max_bond_dim(self) -> int:
        return int(self._max_bond_dim)

    def _replace_tensor(self, site: int, tensor: np.ndarray) -> None:
        previous = self.tensors[site]
        self._memory_bytes += int(tensor.nbytes) - int(previous.nbytes)
        self._max_bond_dim = max(self._max_bond_dim, int(tensor.shape[0]), int(tensor.shape[2]))
        self.tensors[site] = tensor

    def apply_one_qubit(self, logical_qubit: int, matrix: np.ndarray) -> None:
        site = self.site_for_qubit[int(logical_qubit)]
        tensor = self.tensors[site]
        self._replace_tensor(site, np.einsum("op,lpr->lor", matrix, tensor, optimize=False))

    def _index_for_qargs(
        self,
        *,
        left_bit: int,
        right_bit: int,
        left_logical: int,
        right_logical: int,
        qargs: tuple[int, int],
    ) -> int:
        bits = {
            int(left_logical): int(left_bit),
            int(right_logical): int(right_bit),
        }
        return int(bits[int(qargs[0])] + 2 * bits[int(qargs[1])])

    def _apply_adjacent_matrix(
        self,
        *,
        left_site: int,
        matrix: np.ndarray,
        qargs: tuple[int, int],
        settings: ACEQVMSettings,
        ledger: ACEQVMLedger,
    ) -> None:
        right_site = int(left_site) + 1
        left_tensor = self.tensors[left_site]
        right_tensor = self.tensors[right_site]
        left_logical = self.qubit_at_site[left_site]
        right_logical = self.qubit_at_site[right_site]
        theta = np.tensordot(left_tensor, right_tensor, axes=(2, 0))
        updated = np.zeros_like(theta)
        for left_out in range(2):
            for right_out in range(2):
                out_index = self._index_for_qargs(
                    left_bit=left_out,
                    right_bit=right_out,
                    left_logical=left_logical,
                    right_logical=right_logical,
                    qargs=qargs,
                )
                for left_in in range(2):
                    for right_in in range(2):
                        in_index = self._index_for_qargs(
                            left_bit=left_in,
                            right_bit=right_in,
                            left_logical=left_logical,
                            right_logical=right_logical,
                            qargs=qargs,
                        )
                        updated[:, left_out, right_out, :] += (
                            matrix[out_index, in_index] * theta[:, left_in, right_in, :]
                        )
        left_dim, _, _, right_dim = updated.shape
        unfolded = updated.reshape(left_dim * 2, 2 * right_dim)
        u_matrix, singular_values, vh_matrix = np.linalg.svd(unfolded, full_matrices=False)
        max_keep = min(int(settings.max_bond_dim), len(singular_values))
        keep = max_keep
        if settings.truncation_eps > 0.0:
            for candidate in range(1, max_keep + 1):
                if float(np.sum(singular_values[candidate:] ** 2)) <= float(settings.truncation_eps):
                    keep = candidate
                    break
        keep = max(1, min(keep, max_keep))
        discarded_weight = float(np.sum(singular_values[keep:] ** 2))
        ledger.record_svd(
            singular_values,
            keep,
            discarded_weight,
            over_error_budget=discarded_weight > float(settings.truncation_eps),
        )
        kept_s = singular_values[:keep]
        self._replace_tensor(left_site, u_matrix[:, :keep].reshape(left_dim, 2, keep))
        self._replace_tensor(right_site, (np.diag(kept_s) @ vh_matrix[:keep, :]).reshape(keep, 2, right_dim))

    def _apply_swap_at(self, left_site: int, settings: ACEQVMSettings, ledger: ACEQVMLedger) -> None:
        qargs = (self.qubit_at_site[left_site], self.qubit_at_site[left_site + 1])
        self._apply_adjacent_matrix(
            left_site=left_site,
            matrix=_SWAP,
            qargs=qargs,
            settings=settings,
            ledger=ledger,
        )
        left_logical, right_logical = self.qubit_at_site[left_site], self.qubit_at_site[left_site + 1]
        self.qubit_at_site[left_site], self.qubit_at_site[left_site + 1] = right_logical, left_logical
        self.site_for_qubit[left_logical] = left_site + 1
        self.site_for_qubit[right_logical] = left_site
        ledger.routed_swap_count += 1

    def apply_two_qubit(
        self,
        qargs: tuple[int, int],
        matrix: np.ndarray,
        *,
        settings: ACEQVMSettings,
        ledger: ACEQVMLedger,
    ) -> None:
        first, second = int(qargs[0]), int(qargs[1])
        if first == second:
            raise ValueError("ACE-QVM received a two-qubit gate with duplicate qargs.")
        swaps: list[int] = []
        while abs(self.site_for_qubit[first] - self.site_for_qubit[second]) > 1:
            first_site = self.site_for_qubit[first]
            second_site = self.site_for_qubit[second]
            if first_site < second_site:
                swap_site = first_site
            else:
                swap_site = first_site - 1
            self._apply_swap_at(swap_site, settings, ledger)
            swaps.append(swap_site)
        left_site = min(self.site_for_qubit[first], self.site_for_qubit[second])
        self._apply_adjacent_matrix(
            left_site=left_site,
            matrix=matrix,
            qargs=(first, second),
            settings=settings,
            ledger=ledger,
        )
        for swap_site in reversed(swaps):
            self._apply_swap_at(swap_site, settings, ledger)

    def overlap_with(self, other: "MPSState", pauli_label: str | None = None) -> complex:
        if self.qubit_at_site != other.qubit_at_site:
            raise ValueError("ACE-QVM branch contraction requires matching logical-site order.")
        env = np.ones((1, 1), dtype=complex)
        reversed_label = str(pauli_label)[::-1] if pauli_label is not None else None
        for site, left_tensor in enumerate(self.tensors):
            right_tensor = other.tensors[site]
            logical_qubit = self.qubit_at_site[site]
            op = _IDENTITY if reversed_label is None else _PAULI[reversed_label[logical_qubit]]
            env = np.einsum(
                "ab,apr,pq,bqs->rs",
                env,
                left_tensor.conj(),
                op,
                right_tensor,
                optimize=False,
            )
        return complex(env[0, 0])

    def to_statevector(self) -> np.ndarray:
        tensor = self.tensors[0]
        dense = tensor[0, :, :]
        for site in range(1, self.num_qubits):
            dense = np.tensordot(dense, self.tensors[site], axes=(-1, 0))
        dense = np.squeeze(dense, axis=-1)
        state = np.zeros(2**self.num_qubits, dtype=complex)
        for site_bits in np.ndindex(*(2 for _ in range(self.num_qubits))):
            logical_index = 0
            for site, bit in enumerate(site_bits):
                logical_index |= int(bit) << int(self.qubit_at_site[site])
            state[logical_index] = dense[site_bits]
        return state


@dataclass(slots=True)
class _Branch:
    coefficient: complex
    state: MPSState


def build_interaction_graph(circuit: QuantumCircuit, operator: SparsePauliOp) -> dict[str, Any]:
    """Build a compact weighted graph from circuit gates and Pauli supports."""
    num_qubits = int(circuit.num_qubits)
    weights: dict[tuple[int, int], float] = {}
    gate_edges: dict[tuple[int, int], int] = {}
    non_clifford_edges: dict[tuple[int, int], int] = {}
    qubit_indices = {qubit: index for index, qubit in enumerate(circuit.qubits)}
    for instruction in circuit.data:
        qargs = [qubit_indices[qubit] for qubit in instruction.qubits]
        if len(qargs) != 2:
            continue
        edge = tuple(sorted((int(qargs[0]), int(qargs[1]))))
        gate_edges[edge] = int(gate_edges.get(edge, 0)) + 1
        weights[edge] = float(weights.get(edge, 0.0) + 1.0)
        if instruction.operation.name.lower() not in _CLIFFORD_GATES:
            non_clifford_edges[edge] = int(non_clifford_edges.get(edge, 0)) + 1
            weights[edge] = float(weights.get(edge, 0.0) + 0.25)
    for label, coeff in zip(operator.paulis.to_labels(), operator.coeffs, strict=True):
        support = [index for index, char in enumerate(label[::-1]) if char != "I"]
        for left_position, left in enumerate(support):
            for right in support[left_position + 1 :]:
                edge = tuple(sorted((int(left), int(right))))
                weights[edge] = float(weights.get(edge, 0.0) + abs(complex(coeff)))
    return {
        "num_qubits": num_qubits,
        "edges": [
            {
                "qubits": [int(left), int(right)],
                "weight": float(weight),
                "two_qubit_gate_count": int(gate_edges.get((left, right), 0)),
                "non_clifford_count": int(non_clifford_edges.get((left, right), 0)),
            }
            for (left, right), weight in sorted(weights.items())
        ],
    }


def memory_aware_partition(graph: dict[str, Any], settings: ACEQVMSettings) -> dict[str, Any]:
    """Greedy deterministic qubit partition used by the ACE-QVM ledger."""
    num_qubits = int(graph.get("num_qubits", 0))
    adjacency: dict[int, dict[int, float]] = {index: {} for index in range(num_qubits)}
    for edge in graph.get("edges", []):
        left, right = edge["qubits"]
        left = int(left)
        right = int(right)
        weight = float(edge["weight"])
        adjacency.setdefault(left, {})[right] = weight
        adjacency.setdefault(right, {})[left] = weight
    weighted_degree = {
        qubit: float(sum(neighbors.values()))
        for qubit, neighbors in adjacency.items()
    }
    unassigned = set(range(num_qubits))
    seed_order = sorted(range(num_qubits), key=lambda item: (-weighted_degree.get(item, 0.0), item))
    seed_cursor = 0
    blocks: list[list[int]] = []

    def take_seed() -> int | None:
        nonlocal seed_cursor
        while seed_cursor < len(seed_order) and seed_order[seed_cursor] not in unassigned:
            seed_cursor += 1
        if seed_cursor >= len(seed_order):
            return None
        selected = int(seed_order[seed_cursor])
        unassigned.remove(selected)
        seed_cursor += 1
        return selected

    while unassigned:
        seed = take_seed()
        if seed is None:
            break
        block = [seed]
        connection_scores: dict[int, float] = {}
        for neighbor, weight in adjacency.get(seed, {}).items():
            if neighbor in unassigned:
                connection_scores[neighbor] = connection_scores.get(neighbor, 0.0) + float(weight)
        while unassigned and len(block) < int(settings.block_qubits):
            connection_scores = {
                qubit: score
                for qubit, score in connection_scores.items()
                if qubit in unassigned and score > 0.0
            }
            if connection_scores:
                candidate = min(
                    connection_scores,
                    key=lambda item: (
                        -connection_scores.get(item, 0.0),
                        -weighted_degree.get(item, 0.0),
                        item,
                    ),
                )
                unassigned.remove(candidate)
            else:
                candidate = take_seed()
                if candidate is None:
                    break
            block.append(candidate)
            connection_scores.pop(candidate, None)
            for neighbor, weight in adjacency.get(candidate, {}).items():
                if neighbor in unassigned:
                    connection_scores[neighbor] = connection_scores.get(neighbor, 0.0) + float(weight)
        blocks.append(sorted(block))
    block_for_qubit = {
        int(qubit): int(block_index)
        for block_index, block in enumerate(blocks)
        for qubit in block
    }
    return {
        "blocks": blocks,
        "block_for_qubit": block_for_qubit,
        "block_qubits": int(settings.block_qubits),
        "partitioner": "greedy_weighted_degree",
    }


def _operator_schmidt_terms(matrix: np.ndarray, max_rank: int | None = None) -> list[tuple[complex, np.ndarray, np.ndarray]]:
    tensor = np.zeros((2, 2, 2, 2), dtype=complex)
    for out_a in range(2):
        for out_b in range(2):
            for in_a in range(2):
                for in_b in range(2):
                    tensor[out_a, out_b, in_a, in_b] = matrix[out_a + 2 * out_b, in_a + 2 * in_b]
    super_matrix = tensor.transpose(0, 2, 1, 3).reshape(4, 4)
    u_matrix, singular_values, vh_matrix = np.linalg.svd(super_matrix, full_matrices=False)
    terms: list[tuple[complex, np.ndarray, np.ndarray]] = []
    rank = len(singular_values) if max_rank is None else min(int(max_rank), len(singular_values))
    for index in range(rank):
        if singular_values[index] <= 1.0e-14:
            continue
        left = u_matrix[:, index].reshape(2, 2)
        right = vh_matrix[index, :].reshape(2, 2)
        terms.append((complex(singular_values[index]), left, right))
    return terms


class ACEQVMBranchEnsemble:
    """Branch-weighted MPS ensemble for ACE-QVM observable simulation."""

    def __init__(self, num_qubits: int, settings: ACEQVMSettings, partition: dict[str, Any]) -> None:
        self.num_qubits = int(num_qubits)
        self.settings = settings
        self.partition = partition
        self.ledger = ACEQVMLedger()
        self.branches = [_Branch(coefficient=1.0 + 0.0j, state=MPSState(num_qubits))]
        self._refresh_resource_ledger()

    def _same_block(self, first: int, second: int) -> bool:
        block_for_qubit = self.partition["block_for_qubit"]
        return block_for_qubit[int(first)] == block_for_qubit[int(second)]

    def _refresh_resource_ledger(self) -> None:
        branch_rank = len(self.branches)
        self.ledger.max_observed_branch_rank = max(self.ledger.max_observed_branch_rank, branch_rank)
        memory_bytes = sum(branch.state.memory_bytes() for branch in self.branches)
        memory_bytes += 16 * len(self.branches)
        self.ledger.max_observed_memory_bytes = max(self.ledger.max_observed_memory_bytes, int(memory_bytes))
        for branch in self.branches:
            self.ledger.max_observed_bond_dim = max(self.ledger.max_observed_bond_dim, branch.state.max_bond_dim())
        if memory_bytes > self.settings.memory_budget_bytes:
            raise ACEQVMCapacityError(
                "ace_qvm_capacity_exceeded: estimated tensor memory "
                f"{memory_bytes} bytes exceeds budget {self.settings.memory_budget_bytes} bytes."
            )

    def _prune_branches_if_needed(self) -> None:
        max_rank = int(self.settings.max_branch_rank)
        if len(self.branches) <= max_rank:
            return
        self.branches.sort(key=lambda branch: abs(branch.coefficient), reverse=True)
        dropped = self.branches[max_rank:]
        self.branches = self.branches[:max_rank]
        pruned_weight = float(sum(abs(branch.coefficient) ** 2 for branch in dropped))
        self.ledger.total_pruned_branch_weight += pruned_weight
        self.ledger.branch_prune_events += 1
        if self.ledger.capacity_status == "within_budget":
            self.ledger.capacity_status = "approximate_branch_truncated"
        self.ledger.notes.append(
            f"Pruned {len(dropped)} ACE-QVM branches to respect max_branch_rank={max_rank}."
        )

    def apply_one_qubit(self, qarg: int, matrix: np.ndarray, *, gate_name: str) -> None:
        self.ledger.record_gate(gate_name, 1)
        for branch in self.branches:
            branch.state.apply_one_qubit(int(qarg), matrix)

    def _apply_two_qubit_bond(self, qargs: tuple[int, int], matrix: np.ndarray, *, gate_name: str) -> None:
        self.ledger.record_gate(gate_name, 2)
        for branch in self.branches:
            branch.state.apply_two_qubit(
                qargs,
                matrix,
                settings=self.settings,
                ledger=self.ledger,
            )
        self._refresh_resource_ledger()

    def _apply_two_qubit_cut(self, qargs: tuple[int, int], matrix: np.ndarray, *, gate_name: str) -> None:
        terms = _operator_schmidt_terms(matrix)
        if not terms:
            return
        if len(self.branches) * len(terms) > int(self.settings.max_branch_rank):
            if self.settings.cross_block_policy == "fail":
                raise ACEQVMCapacityError(
                    "ace_qvm_capacity_exceeded: operator-Schmidt branch expansion would exceed "
                    f"max_branch_rank={self.settings.max_branch_rank}."
                )
        self.ledger.record_gate(gate_name, 2)
        self.ledger.cut_gate_count += 1
        expanded: list[_Branch] = []
        for branch in self.branches:
            for coefficient, left_op, right_op in terms:
                state = branch.state.copy()
                state.apply_one_qubit(int(qargs[0]), left_op)
                state.apply_one_qubit(int(qargs[1]), right_op)
                expanded.append(_Branch(coefficient=branch.coefficient * coefficient, state=state))
        self.branches = expanded
        self._prune_branches_if_needed()
        self._refresh_resource_ledger()

    def apply_two_qubit(self, qargs: tuple[int, int], matrix: np.ndarray, *, gate_name: str) -> None:
        first, second = int(qargs[0]), int(qargs[1])
        cross_block = not self._same_block(first, second)
        if cross_block:
            self.ledger.cross_block_gate_count += 1
        policy = str(self.settings.cross_block_policy)
        if cross_block and policy == "fail":
            raise ACEQVMCapacityError(
                f"ace_qvm_capacity_exceeded: cross-block gate {gate_name} on qubits {qargs} "
                "is not allowed by cross_block_policy=fail."
            )
        if cross_block and policy == "cut":
            self._apply_two_qubit_cut((first, second), matrix, gate_name=gate_name)
            return
        if cross_block and policy == "auto":
            schmidt_rank = len(_operator_schmidt_terms(matrix))
            if len(self.branches) * schmidt_rank <= int(self.settings.max_branch_rank):
                self._apply_two_qubit_cut((first, second), matrix, gate_name=gate_name)
                return
        self._apply_two_qubit_bond((first, second), matrix, gate_name=gate_name)

    def expectation(self, operator: SparsePauliOp) -> complex:
        numerator = 0.0 + 0.0j
        denominator = 0.0 + 0.0j
        for bra in self.branches:
            for ket in self.branches:
                weight = complex(bra.coefficient).conjugate() * complex(ket.coefficient)
                denominator += weight * bra.state.overlap_with(ket.state)
                term_value = 0.0 + 0.0j
                for label, coeff in zip(operator.paulis.to_labels(), operator.coeffs, strict=True):
                    term_value += complex(coeff) * bra.state.overlap_with(ket.state, label)
                numerator += weight * term_value
        if abs(denominator) <= 1.0e-14:
            raise ACEQVMCapacityError("ace_qvm_capacity_exceeded: branch ensemble norm collapsed to zero.")
        return numerator / denominator

    def debug_statevector(self) -> np.ndarray | None:
        if self.num_qubits > int(self.settings.debug_dense_state_qubit_limit):
            return None
        state = np.zeros(2**self.num_qubits, dtype=complex)
        for branch in self.branches:
            state += branch.coefficient * branch.state.to_statevector()
        norm = np.linalg.norm(state)
        return state if norm <= 1.0e-14 else state / norm


def simulate_circuit_expectation(
    *,
    circuit: QuantumCircuit,
    operator: SparsePauliOp,
    settings: ACEQVMSettings,
) -> tuple[float, dict[str, Any]]:
    """Simulate a prepared circuit with ACE-QVM and return an expectation value."""
    graph = build_interaction_graph(circuit, operator)
    partition = memory_aware_partition(graph, settings)
    ensemble = ACEQVMBranchEnsemble(circuit.num_qubits, settings, partition)
    qubit_indices = {qubit: index for index, qubit in enumerate(circuit.qubits)}
    for instruction in circuit.data:
        operation = instruction.operation
        qargs = tuple(qubit_indices[qubit] for qubit in instruction.qubits)
        name = operation.name.lower()
        if len(qargs) == 0:
            continue
        if len(qargs) == 1:
            ensemble.apply_one_qubit(qargs[0], np.asarray(operation.to_matrix(), dtype=complex), gate_name=name)
        elif len(qargs) == 2:
            ensemble.apply_two_qubit(
                (int(qargs[0]), int(qargs[1])),
                np.asarray(operation.to_matrix(), dtype=complex),
                gate_name=name,
            )
        else:
            raise ValueError(
                f"ACE-QVM supports only one- and two-qubit operations after decomposition; "
                f"operation '{name}' has {len(qargs)} qubits."
            )
    expectation = ensemble.expectation(operator)
    debug_state = ensemble.debug_statevector()
    ledger = ensemble.ledger.to_dict()
    max_memory_bytes = int(ledger.get("max_observed_memory_bytes", 0))
    memory_budget_bytes = int(settings.memory_budget_bytes)
    memory_report = {
        "memory_budget_bytes": memory_budget_bytes,
        "memory_budget_gib": float(settings.memory_budget_gib),
        "max_observed_memory_bytes": max_memory_bytes,
        "max_observed_memory_gib": float(max_memory_bytes / (1024**3)),
        "budget_usage_fraction": float(max_memory_bytes / memory_budget_bytes) if memory_budget_bytes > 0 else None,
        "within_memory_budget": bool(max_memory_bytes <= memory_budget_bytes),
        "debug_dense_state_qubit_limit": int(settings.debug_dense_state_qubit_limit),
        "dense_state_reconstruction_skipped": bool(debug_state is None),
    }
    metadata = {
        "algorithm_name": "ACE-QVM",
        "settings": settings.to_dict(),
        "interaction_graph": graph,
        "partition": partition,
        "ledger": ledger,
        "memory_report": memory_report,
        "debug_dense_state_available": debug_state is not None,
        "full_state_reconstruction": bool(debug_state is not None),
        "validated_observables_only": True,
        "hardware_verified": False,
    }
    return float(np.real_if_close(expectation).real), metadata
