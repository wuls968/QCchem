from __future__ import annotations

import json
from pathlib import Path

from qcchem.cli.main import main
from tests.unit.test_promotion_gate import _write_lr_ace


def test_promote_exploratory_cli_blocks_direct_validated(tmp_path: Path) -> None:
    artifact = _write_lr_ace(tmp_path / "h2_lr_ace")

    assert main(
        [
            "promote",
            "exploratory",
            "--artifact",
            str(artifact),
            "--target",
            "validated_algorithm_candidate",
            "-o",
            str(tmp_path / "promotion"),
        ]
    ) == 2

    payload = json.loads((tmp_path / "promotion" / "promotion_review.json").read_text(encoding="utf-8"))
    assert payload["status"] == "blocked"
    assert (tmp_path / "promotion" / "promotion_review.md").exists()
