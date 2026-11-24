from __future__ import annotations

import csv
import math
from pathlib import Path

import pytest

from aema.errors import ParseError
from aema.validation import REQUIRED_COLUMNS, analyze_trials, main


def trial(**changes: str) -> dict[str, str]:
    row = {
        "trial_id": "t1",
        "condition": "idle",
        "device_id": "device-a",
        "build_id": "build-a",
        "instrument_id": "instrument-a",
        "calibration_id": "cal-a",
        "window_start_utc": "2026-01-01T00:00:00Z",
        "window_end_utc": "2026-01-01T00:10:00Z",
        "clock_offset_ms": "0",
        "estimated_charge_mah": "11",
        "reference_charge_mah": "10",
        "reference_standard_uncertainty_mah": "0.2",
        "battery_stats_sha256": "a" * 64,
        "reference_sha256": "b" * 64,
        "exclusion_reason": "",
    }
    row.update(changes)
    return row


def write_trials(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)


def test_analyzes_paired_charge_and_exclusions(tmp_path: Path, capsys) -> None:
    path = tmp_path / "trials.csv"
    write_trials(
        path,
        [
            trial(),
            trial(trial_id="t2", estimated_charge_mah="12"),
            trial(trial_id="t3", exclusion_reason="clock marker missing"),
        ],
    )
    report = analyze_trials(path)
    idle = report["conditions"]["idle"]
    assert idle["n"] == 2
    assert idle["excluded"] == [{"trial_id": "t3", "reason": "clock marker missing"}]
    assert idle["mean_signed_error_mah"] == 1.5
    assert idle["mean_absolute_error_mah"] == 1.5
    assert idle["sample_sd_error_mah"] == pytest.approx(math.sqrt(0.5))
    assert idle["mean_relative_error_percent"] == 15
    assert idle["reference_standard_uncertainty_mah"] == [0.2, 0.2]
    assert main([str(path)]) == 0
    assert '"mean_signed_error_mah": 1.5' in capsys.readouterr().out


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"trial_id": "t1"}, "duplicate trial_id"),
        ({"window_end_utc": "2025-12-31T23:00:00Z"}, "window_end_utc"),
        ({"window_start_utc": "2026-01-01T00:00:00"}, "must be UTC"),
        ({"reference_charge_mah": "0"}, "invalid charge"),
        ({"estimated_charge_mah": "nan"}, "non-finite"),
        ({"reference_sha256": "bad"}, "invalid reference_sha256"),
        ({"calibration_id": "cal-b"}, "mixed device, build, instrument or calibration"),
    ],
)
def test_rejects_invalid_pair(tmp_path: Path, changes: dict[str, str], message: str) -> None:
    path = tmp_path / "bad.csv"
    write_trials(path, [trial(), trial(**({"trial_id": "t2"} | changes))])
    with pytest.raises(ParseError, match=message):
        analyze_trials(path)


def test_rejects_single_pair_and_empty_input(tmp_path: Path, capsys) -> None:
    path = tmp_path / "single.csv"
    write_trials(path, [trial()])
    assert main([str(path)]) == 2
    assert "at least two" in capsys.readouterr().err
    path.write_text("", encoding="utf-8")
    with pytest.raises(ParseError, match="missing trial columns"):
        analyze_trials(path)


def test_rejects_condition_with_only_exclusions(tmp_path: Path) -> None:
    path = tmp_path / "excluded.csv"
    write_trials(path, [trial(exclusion_reason="window mismatch")])
    with pytest.raises(ParseError, match="at least two valid trials"):
        analyze_trials(path)
