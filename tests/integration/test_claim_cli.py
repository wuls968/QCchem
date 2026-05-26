from __future__ import annotations

import json
from pathlib import Path

from qcchem.cli.main import main
from tests.unit.test_claim_compiler import _write_hardware_artifact


def test_claim_check_cli_reads_claim_file_and_writes_review(tmp_path: Path) -> None:
    target = _write_hardware_artifact(tmp_path / "hardware")
    claim_file = tmp_path / "claim.txt"
    claim_file.write_text("hardware_verified proves publication-grade chemical accuracy", encoding="utf-8")

    assert main(["claim", "check", "--claim-file", str(claim_file), "--target", str(target), "-o", str(tmp_path / "review")]) == 2

    payload = json.loads((tmp_path / "review" / "claim_review.json").read_text(encoding="utf-8"))
    assert payload["support_level"] == "overclaimed"
    assert (tmp_path / "review" / "claim_review.md").exists()
