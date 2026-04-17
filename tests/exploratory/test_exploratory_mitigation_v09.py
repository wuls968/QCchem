from qcchem.exploratory.benchmarks.suite_definitions import EXPLORATORY_SUITES


def test_exploratory_benchmark_suites_are_not_validated() -> None:
    assert EXPLORATORY_SUITES["spectroscopy_v1"]["scope"] == "exploratory"
    assert EXPLORATORY_SUITES["strong_correlation_v1"]["scope"] == "exploratory"


def test_exploratory_mitigation_metadata_declares_risk() -> None:
    from qcchem.exploratory.mitigation.readout import READOUT_EXPLORATORY_METADATA

    assert READOUT_EXPLORATORY_METADATA["module_origin"] == "exploratory"
    assert READOUT_EXPLORATORY_METADATA["scientific_risk_notes"]
