from qcchem.exploratory.solvers.registry import get_exploratory_solver


def test_vqd_solver_is_registered_as_exploratory() -> None:
    solver_cls, metadata = get_exploratory_solver("vqd")
    assert solver_cls is not None
    assert metadata["module_origin"] == "exploratory"
    assert metadata["capability_tier"] == "exploratory"


def test_exploratory_solver_metadata_contains_scientific_risk_notes() -> None:
    _, metadata = get_exploratory_solver("qse")
    assert metadata["scientific_risk_notes"]
