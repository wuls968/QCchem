from pathlib import Path

from qcchem.cli.main import main


def test_standard_run_rejects_exploratory_config(tmp_path: Path) -> None:
    config = tmp_path / "exploratory.yaml"
    config.write_text(
        """
        molecule:
          name: H2
          geometry:
            - {symbol: H, coords: [0.0, 0.0, 0.0]}
            - {symbol: H, coords: [0.0, 0.0, 0.74]}
        solver:
          kind: vqd
          experimental: true
        """,
        encoding="utf-8",
    )

    exit_code = main(["run", "-c", str(config)])
    assert exit_code == 2


def test_exploratory_command_accepts_experimental_solver() -> None:
    from qcchem.cli.main import _build_parser

    parser = _build_parser()
    args = parser.parse_args(["exploratory", "run", "-c", "dummy.yaml"])
    assert args.command == "exploratory"
