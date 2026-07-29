from __future__ import annotations

from pathlib import Path

from qcchem.io.artifact_index import build_artifact_index_entry


def test_artifact_index_entry_uses_supplied_payload_before_result_is_written(tmp_path: Path) -> None:
    result_path = tmp_path / "in_memory_run" / "result.json"

    entry = build_artifact_index_entry(
        result_path,
        payload={
            "run_id": "in_memory_run",
            "status": "completed",
            "provenance": {"git_commit": "abc123"},
        },
    )

    assert entry["artifact_name"] == "in_memory_run"
    assert entry["verification_status"] == "completed"
    assert entry["provenance_complete"] is True
    assert isinstance(entry["mtime"], float)
