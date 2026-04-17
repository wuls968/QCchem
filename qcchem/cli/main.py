"""Command-line interface for QCchem."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qcchem.io.config import load_run_spec
from qcchem.io.serialization import to_primitive
from qcchem.reporting import write_aggregate_report, write_markdown_report
from qcchem.workflow.benchmark import run_benchmark_suite_from_config
from qcchem.workflow.runner import run_from_config
from qcchem.workflow.scan import run_scan_from_config
from qcchem.workflow.study import run_study_from_config


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qcchem", description="QCchem quantum chemistry workflow CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a QCchem calculation from YAML config.")
    run_parser.add_argument("-c", "--config", type=Path, required=True, help="Path to YAML config.")
    run_parser.add_argument("-o", "--output-dir", type=Path, help="Override artifact output directory.")

    report_parser = subparsers.add_parser("report", help="Regenerate a run Markdown report from result.json.")
    report_parser.add_argument("result_json", type=Path, help="Path to result.json.")
    report_parser.add_argument("-o", "--output", type=Path, help="Optional report output path.")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a config and print a summary.")
    inspect_parser.add_argument("-c", "--config", type=Path, required=True, help="Path to YAML config.")

    study_parser = subparsers.add_parser("study", help="Study workflow commands.")
    study_subparsers = study_parser.add_subparsers(dest="study_command", required=True)
    study_run = study_subparsers.add_parser("run", help="Run a study from YAML config.")
    study_run.add_argument("-c", "--config", type=Path, required=True)
    study_run.add_argument("-o", "--output-dir", type=Path)
    study_report = study_subparsers.add_parser("report", help="Regenerate a study report from JSON.")
    study_report.add_argument("result_json", type=Path)
    study_report.add_argument("-o", "--output", type=Path)

    benchmark_parser = subparsers.add_parser("benchmark", help="Benchmark workflow commands.")
    benchmark_subparsers = benchmark_parser.add_subparsers(dest="benchmark_command", required=True)
    benchmark_run = benchmark_subparsers.add_parser("run", help="Run a benchmark suite from YAML config.")
    benchmark_run.add_argument("-c", "--config", type=Path, required=True)
    benchmark_run.add_argument("-o", "--output-dir", type=Path)
    benchmark_report = benchmark_subparsers.add_parser("report", help="Regenerate a benchmark report from JSON.")
    benchmark_report.add_argument("result_json", type=Path)
    benchmark_report.add_argument("-o", "--output", type=Path)

    scan_parser = subparsers.add_parser("scan", help="Scan workflow commands.")
    scan_subparsers = scan_parser.add_subparsers(dest="scan_command", required=True)
    scan_run = scan_subparsers.add_parser("run", help="Run a scan from YAML config.")
    scan_run.add_argument("-c", "--config", type=Path, required=True)
    scan_run.add_argument("-o", "--output-dir", type=Path)
    scan_report = scan_subparsers.add_parser("report", help="Regenerate a scan report from JSON.")
    scan_report.add_argument("result_json", type=Path)
    scan_report.add_argument("-o", "--output", type=Path)

    exploratory_parser = subparsers.add_parser("exploratory", help="Exploratory workflow commands.")
    exploratory_subparsers = exploratory_parser.add_subparsers(dest="exploratory_command", required=True)
    exploratory_run = exploratory_subparsers.add_parser("run", help="Run an exploratory QCchem calculation.")
    exploratory_run.add_argument("-c", "--config", type=Path, required=True)
    exploratory_run.add_argument("-o", "--output-dir", type=Path)
    return parser


def _write_aggregate_from_json(result_json: Path, output: Path | None, *, kind: str) -> int:
    payload = json.loads(result_json.read_text(encoding="utf-8"))
    output_path = output or result_json.with_suffix(".md")
    write_aggregate_report(payload, output_path, kind=kind)
    print(f"{kind.capitalize()} report written to {output_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the QCchem CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        try:
            result = run_from_config(args.config, output_dir=args.output_dir)
        except ValueError as exc:
            print(f"QCchem run rejected: {exc}")
            return 2
        print(f"QCchem run completed: {result.problem.molecule_name}")
        print(f"Verification status: {result.verification_status}")
        print(f"Total energy: {result.energy.total_energy:.12f} {result.energy.energy_units}")
        if result.noise_model is not None:
            print(f"Noise model: {result.noise_model.profile} ({result.noise_model.model_kind})")
        if result.runtime_options is not None:
            print(
                "Runtime snapshot: "
                f"service={result.runtime_options.service}, "
                f"session_ready={result.runtime_options.session_ready}, "
                f"batch_ready={result.runtime_options.batch_ready}, "
                f"low_rank_workload={result.runtime_options.low_rank_workload}"
            )
        if result.measurement is not None:
            print(
                "Measurement plan: "
                f"strategy={result.measurement.strategy}, "
                f"groups={result.measurement.group_count}, "
                f"estimated_cost={result.measurement.estimated_shot_cost:.0f}"
            )
        if result.calibration is not None:
            print(
                "Calibration: "
                f"measured_wall_time={result.calibration.measured_wall_time_seconds:.3f}s, "
                f"measured_cost={result.calibration.measured_shot_usage}, "
                f"achieved_error={result.calibration.achieved_error}"
            )
        if result.reduction_audit is not None and result.reduction_audit.selection_mode != "none":
            print(
                "Reduction audit: "
                f"mode={result.reduction_audit.selection_mode}, "
                f"transformers={result.reduction_audit.transformers_applied}"
            )
        if result.compression_result is not None:
            print(
                "Compression audit: "
                f"method={result.compression_result.method}, "
                f"status={result.compression_result.verification_status}"
            )
        if result.benchmark.compressed_vs_uncompressed is not None:
            print(
                "Compressed comparison: "
                f"abs_error={result.benchmark.compressed_vs_uncompressed.absolute_error:.6e}, "
                f"terms={result.benchmark.compressed_vs_uncompressed.pre_term_count}"
                f"->{result.benchmark.compressed_vs_uncompressed.post_term_count}"
            )
        if result.perturbative_correction_result is not None:
            print(
                "Perturbative correction: "
                f"method={result.perturbative_correction_result.method}, "
                f"status={result.perturbative_correction_result.verification_status}"
            )
        if result.embedding_result is not None:
            print(
                "Embedding audit: "
                f"method={result.embedding_result.method}, "
                f"status={result.embedding_result.verification_status}"
            )
        if result.runtime_submission is not None:
            print(
                "Runtime submission: "
                f"attempted={result.runtime_submission.attempted}, "
                f"submitted={result.runtime_submission.submitted}, "
                f"failure={result.runtime_submission.failure_category}"
            )
        if result.excited_state_result is not None:
            print(f"Excited-state task: {result.excited_state_result.verification_status}")
        if result.property_result is not None:
            print(f"Property task: {result.property_result.verification_status}")
        if result.artifacts.qcschema_json is not None:
            print(f"QCSchema export: {result.artifacts.qcschema_json}")
        if result.artifacts.hdf5_file is not None:
            print(f"HDF5 export: {result.artifacts.hdf5_file}")
        print(f"Artifacts: {result.artifacts.root}")
        return 0

    if args.command == "report":
        payload = json.loads(args.result_json.read_text(encoding="utf-8"))
        output_path = args.output or args.result_json.with_name("report.md")
        write_markdown_report(payload, output_path)
        print(f"Report written to {output_path}")
        return 0

    if args.command == "inspect":
        spec = load_run_spec(args.config)
        print(json.dumps(to_primitive(spec), indent=2, sort_keys=True))
        return 0

    if args.command == "study":
        if args.study_command == "run":
            result = run_study_from_config(args.config, output_dir=args.output_dir)
            print(f"Study completed: {result.study_name}")
            print(f"Runs: {result.summary.total_runs}")
            print(f"Artifacts: {result.artifacts.root}")
            return 0
        if args.study_command == "report":
            return _write_aggregate_from_json(args.result_json, args.output, kind="study")

    if args.command == "benchmark":
        if args.benchmark_command == "run":
            result = run_benchmark_suite_from_config(args.config, output_dir=args.output_dir)
            if isinstance(result, dict):
                summary = result.get("summary", {})
                print(f"Benchmark suite completed: {result.get('suite_name')}")
                print(f"Cases: {summary.get('total_cases')}")
                print(
                    "Runtime evidence status counts: "
                    f"{summary.get('runtime_evidence_status_counts', {})}"
                )
                print(f"Artifacts: {result.get('artifact_root')}")
                return 0
            print(f"Benchmark suite completed: {result.suite_name}")
            print(f"Cases: {result.summary.total_cases}")
            print(f"Status counts: {result.summary.status_counts}")
            print(f"Artifacts: {result.artifacts.root}")
            return 0
        if args.benchmark_command == "report":
            return _write_aggregate_from_json(args.result_json, args.output, kind="benchmark")

    if args.command == "scan":
        if args.scan_command == "run":
            result = run_scan_from_config(args.config, output_dir=args.output_dir)
            print(f"Scan completed: {result.scan_name}")
            print(f"Points: {result.summary.total_runs}")
            print(f"Artifacts: {result.artifacts.root}")
            return 0
        if args.scan_command == "report":
            return _write_aggregate_from_json(args.result_json, args.output, kind="scan")

    if args.command == "exploratory":
        if args.exploratory_command == "run":
            result = run_from_config(
                args.config,
                output_dir=args.output_dir,
                exploratory_command=True,
            )
            print(f"QCchem exploratory run completed: {result.problem.molecule_name}")
            print(f"Verification status: {result.verification_status}")
            print(f"Module origin: {result.module_origin}")
            print(f"Capability tier: {result.capability_tier}")
            print(f"Artifacts: {result.artifacts.root}")
            return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
