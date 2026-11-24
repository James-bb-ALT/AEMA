"""Descriptive comparison of paired BatteryStats and external charge trials."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from aema.errors import AemaError, ParseError

REQUIRED_COLUMNS = frozenset(
    {
        "trial_id",
        "condition",
        "device_id",
        "build_id",
        "instrument_id",
        "calibration_id",
        "window_start_utc",
        "window_end_utc",
        "clock_offset_ms",
        "estimated_charge_mah",
        "reference_charge_mah",
        "reference_standard_uncertainty_mah",
        "battery_stats_sha256",
        "reference_sha256",
        "exclusion_reason",
    }
)


def _number(row: dict[str, str], name: str, line: int) -> float:
    try:
        value = float(row[name])
    except (KeyError, ValueError) as exc:
        raise ParseError(f"line {line}: invalid {name}") from exc
    if not math.isfinite(value):
        raise ParseError(f"line {line}: non-finite {name}")
    return value


def _timestamp(row: dict[str, str], name: str, line: int) -> datetime:
    try:
        value = datetime.fromisoformat(row[name].replace("Z", "+00:00"))
    except (KeyError, ValueError) as exc:
        raise ParseError(f"line {line}: invalid {name}") from exc
    if value.tzinfo is None or value.utcoffset().total_seconds() != 0:
        raise ParseError(f"line {line}: {name} must be UTC")
    return value


def _validate_row(row: dict[str, str], line: int) -> tuple[str, float, float, float]:
    for name in (
        "trial_id",
        "condition",
        "device_id",
        "build_id",
        "instrument_id",
        "calibration_id",
    ):
        if not row[name].strip():
            raise ParseError(f"line {line}: missing {name}")
    start = _timestamp(row, "window_start_utc", line)
    end = _timestamp(row, "window_end_utc", line)
    if end <= start:
        raise ParseError(f"line {line}: window_end_utc must follow window_start_utc")
    _number(row, "clock_offset_ms", line)
    estimate = _number(row, "estimated_charge_mah", line)
    reference = _number(row, "reference_charge_mah", line)
    uncertainty = _number(row, "reference_standard_uncertainty_mah", line)
    if estimate < 0 or reference <= 0 or uncertainty < 0:
        raise ParseError(f"line {line}: invalid charge or reference uncertainty")
    for name in ("battery_stats_sha256", "reference_sha256"):
        digest = row[name].strip()
        if len(digest) != 64 or any(char not in "0123456789abcdefABCDEF" for char in digest):
            raise ParseError(f"line {line}: invalid {name}")
    return row["condition"].strip(), estimate, reference, uncertainty


def analyze_trials(path: str | Path) -> dict:
    """Summarize signed error and repeatability, without claiming calibrated accuracy."""
    groups: dict[str, list[tuple[float, float, float]]] = defaultdict(list)
    excluded: dict[str, list[dict[str, str]]] = defaultdict(list)
    metadata: dict[str, tuple[str, str, str, str]] = {}
    seen: set[str] = set()
    try:
        with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None or not REQUIRED_COLUMNS <= set(reader.fieldnames):
                missing = sorted(REQUIRED_COLUMNS - set(reader.fieldnames or []))
                raise ParseError(f"missing trial columns: {', '.join(missing)}")
            for line, row in enumerate(reader, start=2):
                if None in row or any(value is None for value in row.values()):
                    raise ParseError(f"line {line}: malformed CSV row")
                trial_id = row["trial_id"].strip()
                if not trial_id or trial_id in seen:
                    raise ParseError(f"line {line}: missing or duplicate trial_id")
                seen.add(trial_id)
                condition, estimate, reference, uncertainty = _validate_row(row, line)
                context = tuple(
                    row[name].strip()
                    for name in ("device_id", "build_id", "instrument_id", "calibration_id")
                )
                if condition in metadata and metadata[condition] != context:
                    raise ParseError(f"line {line}: mixed device, build, instrument or calibration")
                metadata[condition] = context
                if row["exclusion_reason"].strip():
                    excluded[condition].append(
                        {"trial_id": trial_id, "reason": row["exclusion_reason"].strip()}
                    )
                    continue
                groups[condition].append((estimate - reference, reference, uncertainty))
    except (OSError, UnicodeError) as exc:
        raise ParseError(f"cannot read trial CSV {path}: {exc}") from exc
    if not groups and not excluded:
        raise ParseError("no valid paired trials")
    conditions = {}
    for condition in sorted(metadata):
        trials = groups[condition]
        if len(trials) < 2:
            raise ParseError(f"condition {condition!r} needs at least two valid trials")
        errors = [error for error, _, _ in trials]
        conditions[condition] = {
            "n": len(trials),
            "excluded": excluded[condition],
            "device_id": metadata[condition][0],
            "build_id": metadata[condition][1],
            "instrument_id": metadata[condition][2],
            "calibration_id": metadata[condition][3],
            "mean_signed_error_mah": statistics.mean(errors),
            "mean_absolute_error_mah": statistics.mean(abs(error) for error in errors),
            "sample_sd_error_mah": statistics.stdev(errors),
            "mean_relative_error_percent": statistics.mean(
                100 * error / reference for error, reference, _ in trials
            ),
            "reference_standard_uncertainty_mah": [item[2] for item in trials],
        }
    return {
        "analysis": "descriptive_paired_charge_comparison",
        "unit": "mAh",
        "conditions": conditions,
        "limitations": [
            "Trial windows and calibration must be independently verified from raw sources.",
            "Reference uncertainty is reported, not combined with repeatability.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze paired charge trials in mAh")
    parser.add_argument("trials_csv", type=Path)
    args = parser.parse_args(argv)
    try:
        report = analyze_trials(args.trials_csv)
    except AemaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
