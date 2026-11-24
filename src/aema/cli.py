"""Command-line entry point for AEMA parsing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aema.collector import collect_session
from aema.demo import run_demo
from aema.errors import AemaError
from aema.exporters import export_canonical_result
from aema.models import PipelineInputs
from aema.pipeline import run_pipeline
from aema.presentation import inspect_metrics
from aema.privacy import export_pseudonymous_study
from aema.study_export import export_total_charge_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aema", description="Parse Android batterystats and package UID files."
    )
    parser.add_argument("--checkin", type=Path, required=True, help="batterystats check-in CSV")
    parser.add_argument(
        "--battery-report", type=Path, required=True, help="human-readable batterystats report"
    )
    parser.add_argument("--packages", type=Path, required=True, help="package UID mapping")
    parser.add_argument(
        "--output-root", type=Path, default=Path("outputs"), help="parent for a new output dir"
    )
    parser.add_argument(
        "--lenient", action="store_true", help="skip malformed records and report warnings"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if arguments and arguments[0] == "pseudonymize":
        privacy_parser = argparse.ArgumentParser(prog="aema pseudonymize")
        privacy_parser.add_argument("--dataset", type=Path, required=True)
        privacy_parser.add_argument("--key-file", type=Path, required=True)
        privacy_parser.add_argument("--output", type=Path, required=True)
        args = privacy_parser.parse_args(arguments[1:])
        try:
            output = export_pseudonymous_study(
                args.dataset, args.output, args.key_file.read_bytes()
            )
        except (AemaError, OSError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(json.dumps({"study_file": str(output)}, indent=2, sort_keys=True))
        return 0
    if arguments and arguments[0] == "collect":
        collect_parser = argparse.ArgumentParser(prog="aema collect")
        collect_parser.add_argument("--serial", required=True)
        collect_parser.add_argument("--output-root", type=Path, default=Path("captures"))
        collect_parser.add_argument("--adb", default="adb")
        args = collect_parser.parse_args(arguments[1:])
        try:
            directory = collect_session(
                serial=args.serial, output_root=args.output_root, adb=args.adb
            )
        except AemaError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(json.dumps({"capture_directory": str(directory)}, indent=2, sort_keys=True))
        return 0
    if arguments and arguments[0] == "demo":
        demo_parser = argparse.ArgumentParser(prog="aema demo")
        demo_parser.add_argument("--fixtures", type=Path, required=True)
        demo_parser.add_argument("--output-root", type=Path, default=Path("demo-output"))
        args = demo_parser.parse_args(arguments[1:])
        try:
            summary = run_demo(args.fixtures, args.output_root)
        except AemaError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    if arguments and arguments[0] == "study-summary":
        summary_parser = argparse.ArgumentParser(prog="aema study-summary")
        summary_parser.add_argument("--battery-report", type=Path, required=True)
        summary_parser.add_argument("--output-root", type=Path, default=Path("study-outputs"))
        args = summary_parser.parse_args(arguments[1:])
        try:
            directory = export_total_charge_summary(args.battery_report, args.output_root)
        except AemaError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(json.dumps({"study_directory": str(directory)}, indent=2, sort_keys=True))
        return 0
    if arguments and arguments[0] == "inspect":
        inspect_parser = argparse.ArgumentParser(prog="aema inspect")
        inspect_parser.add_argument("--metric")
        inspect_parser.add_argument("--source", choices=("checkin", "power"))
        args = inspect_parser.parse_args(arguments[1:])
        try:
            metrics = inspect_metrics(metric=args.metric, source=args.source)
        except AemaError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(metrics, indent=2, sort_keys=True))
        return 0
    args = build_parser().parse_args(arguments)
    try:
        result = run_pipeline(
            PipelineInputs(args.checkin, args.battery_report, args.packages),
            strict=not args.lenient,
        )
        output_dir = export_canonical_result(result, args.output_root)
    except AemaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    summary = {
        "output_directory": str(output_dir),
        "record_counts": {
            "checkin": result.checkin.diagnostics.parsed_records,
            "battery_report": result.battery_report.diagnostics.parsed_records,
            "packages": result.packages.diagnostics.parsed_records,
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
