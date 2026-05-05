from __future__ import annotations

import pytest

from qcchem.backends.layout import recommend_initial_layout_from_errors


def test_recommend_initial_layout_prefers_lower_error_connected_subset() -> None:
    plan = recommend_initial_layout_from_errors(
        num_qubits=4,
        coupling_edges=[
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 4),
            (4, 5),
        ],
        readout_errors={
            0: 0.03,
            1: 0.03,
            2: 0.02,
            3: 0.005,
            4: 0.004,
            5: 0.006,
        },
        two_qubit_errors={
            (0, 1): 0.04,
            (1, 2): 0.04,
            (2, 3): 0.015,
            (3, 4): 0.012,
            (4, 5): 0.014,
        },
    )

    assert plan is not None
    assert set(plan.selected_layout) == {2, 3, 4, 5}
    assert plan.strategy == "min_weighted_error"
    assert plan.connected_edge_count == 3
    assert plan.score < 0.08


def test_recommend_initial_layout_returns_none_when_backend_graph_cannot_fit_qubits() -> None:
    plan = recommend_initial_layout_from_errors(
        num_qubits=4,
        coupling_edges=[(0, 1), (2, 3)],
        readout_errors={0: 0.01, 1: 0.01, 2: 0.01, 3: 0.01},
        two_qubit_errors={(0, 1): 0.02, (2, 3): 0.02},
    )

    assert plan is None


def test_recommend_initial_layout_rejects_unknown_strategy() -> None:
    with pytest.raises(ValueError, match="Unsupported layout strategy"):
        recommend_initial_layout_from_errors(
            num_qubits=2,
            coupling_edges=[(0, 1)],
            readout_errors={0: 0.01, 1: 0.01},
            two_qubit_errors={(0, 1): 0.02},
            strategy="mystery_mode",
        )
