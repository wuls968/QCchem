from __future__ import annotations

from qiskit.quantum_info import SparsePauliOp

from qcchem.exploratory.solvers.lr_ace import build_low_rank_generator_plan


def test_lr_ace_turns_dominant_x_factor_into_real_mixing_generator() -> None:
    operator = SparsePauliOp.from_list(
        [
            ("II", -1.0),
            ("IZ", 0.4),
            ("ZI", -0.4),
            ("ZZ", -0.01),
            ("XX", 0.18),
        ]
    )

    plan = build_low_rank_generator_plan(operator, max_generators=2)

    assert plan["source_terms"][0]["pauli"] == "XX"
    assert plan["selected_generators"][0]["pauli"] == "YX"
    assert plan["selected_generators"][0]["source_pauli"] == "XX"
    assert plan["selected_factor_count"] == 1
    assert plan["low_rank_aware"] is True
