import json
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


def test_exploratory_capacity_benchmark_parser_accepts_sizes(tmp_path: Path) -> None:
    from qcchem.cli.main import _build_parser

    parser = _build_parser()
    args = parser.parse_args(
        [
            "exploratory",
            "capacity-benchmark",
            "-o",
            str(tmp_path / "ace-capacity"),
            "--sizes",
            "2,4",
            "--case",
            "product_x",
        ]
    )
    assert args.command == "exploratory"
    assert args.exploratory_command == "capacity-benchmark"
    assert args.sizes == "2,4"
    assert args.case == ["product_x"]
    assert args.overwrite is False


def test_exploratory_capacity_benchmark_writes_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "ace-capacity"

    exit_code = main(
        [
            "exploratory",
            "capacity-benchmark",
            "-o",
            str(output_dir),
            "--sizes",
            "2,4",
            "--case",
            "product_x",
            "--timeout-seconds",
            "30",
        ]
    )

    assert exit_code == 0
    payload = json.loads((output_dir / "benchmark.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == "qcchem.ace_qvm_capacity_benchmark.v0.1"
    assert payload["observed_capacity"]["product_x"]["max_ok_qubits"] == 4
    assert payload["observed_capacity"]["product_x"]["max_observed_bond_dim"] == 1
    assert (output_dir / "benchmark.md").exists()
