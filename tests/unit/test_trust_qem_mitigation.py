from __future__ import annotations

import json
from pathlib import Path

import pytest

from qcchem.core import MitigationSpec, PECSpec
from qcchem.mitigation import build_mitigation_summary


def test_trust_qem_pec_records_executable_calibration_model(tmp_path: Path) -> None:
    model = tmp_path / "pec_model.json"
    model.write_text(
        json.dumps(
            {
                "schema": "qcchem.pec_calibration_model.v1",
                "executable": True,
                "calibrated_operations": [
                    {
                        "operation": "x",
                        "qubits": [0],
                        "quasi_probabilities": [
                            {"operation": "x", "coefficient": 1.01},
                            {"operation": "identity", "coefficient": -0.01},
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    summary = build_mitigation_summary(
        MitigationSpec(
            pec=PECSpec(
                enabled=True,
                method="local_pec",
                calibration_model=str(model),
                max_overhead=9.0,
            )
        )
    )

    assert summary.applied_methods == ["pec"]
    assert summary.claim_allowed_methods == ["pec"]
    assert summary.claim_status == "claim_limited"
    assert summary.energy_replaces_primary is False
    assert summary.pec["status"] == "executable_calibration_model_recorded"
    assert summary.pec["allowed_for_claim"] is True
    assert summary.pec["energy_replaces_primary"] is False
    audit = summary.pec["calibration_model_audit"]
    assert audit["executable"] is True
    assert audit["schema"] == "qcchem.pec_calibration_model.v1"
    assert audit["calibrated_operation_count"] == 1
    assert audit["quasi_probability_entry_count"] == 2
    assert audit["max_operation_l1_overhead"] == pytest.approx(1.02)
