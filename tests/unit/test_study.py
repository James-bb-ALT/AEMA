from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from aema.errors import ParseError
from aema.study import audit_study
from aema.study import main as study_main
from aema.validation import REQUIRED_COLUMNS


def inputs(tmp_path: Path) -> tuple[Path, Path]:
    protocol = tmp_path / "protocol.json"
    protocol.write_text(
        json.dumps(
            {
                "protocol_id": "study-1",
                "status": "frozen",
                "planned_trials": {"idle": ["t1", "t2", "t3"]},
                "allowed_exclusion_reasons": ["clock marker missing"],
            }
        ),
        encoding="utf-8",
    )
    trials = tmp_path / "trials.csv"
    row = {
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
    with trials.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        for trial_id, reason in (("t1", ""), ("t2", ""), ("t3", "clock marker missing")):
            writer.writerow(row | {"trial_id": trial_id, "exclusion_reason": reason})
    return protocol, trials


def test_audits_frozen_plan_before_analysis(tmp_path: Path) -> None:
    protocol, trials = inputs(tmp_path)
    report = audit_study(protocol, trials)
    assert report["planned_trial_count"] == 3
    assert report["exclusions"] == [{"trial_id": "t3", "reason": "clock marker missing"}]
    assert report["analysis"]["conditions"]["idle"]["n"] == 2
    assert len(report["protocol_sha256"]) == 64


def test_rejects_unplanned_trial_and_reason(tmp_path: Path) -> None:
    protocol, trials = inputs(tmp_path)
    data = json.loads(protocol.read_text(encoding="utf-8"))
    data["planned_trials"]["idle"].append("t4")
    protocol.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ParseError, match="differs from the frozen plan"):
        audit_study(protocol, trials)
    data["planned_trials"]["idle"].remove("t4")
    data["allowed_exclusion_reasons"] = []
    protocol.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ParseError, match="unplanned exclusion reason"):
        audit_study(protocol, trials)


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("status", "draft", "must be frozen"),
        ("protocol_id", "", "must be frozen"),
        ("planned_trials", [], "non-empty mapping"),
        ("allowed_exclusion_reasons", "bad", "list of strings"),
        ("allowed_exclusion_reasons", [1], "list of strings"),
        ("planned_trials", {"idle": []}, "needs planned trial IDs"),
        ("planned_trials", {"idle": ["t1", "t1"]}, "unique and non-empty"),
    ],
)
def test_rejects_invalid_study_protocol(tmp_path: Path, field, value, error) -> None:
    protocol, trials = inputs(tmp_path)
    data = json.loads(protocol.read_text())
    data[field] = value
    protocol.write_text(json.dumps(data))
    with pytest.raises(ParseError, match=error):
        audit_study(protocol, trials)


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        ("missing_columns", "missing audit columns"),
        ("truncated", "malformed trial ledger row"),
        ("duplicate", "missing or duplicate trial ID"),
        ("condition", "condition differs from plan"),
    ],
)
def test_rejects_invalid_trial_ledger(tmp_path: Path, mutation, error) -> None:
    protocol, trials = inputs(tmp_path)
    with trials.open(newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        rows = list(reader)
    if mutation == "missing_columns":
        trials.write_text("other\nvalue\n")
    elif mutation == "truncated":
        trials.write_text(",".join(fields) + "\nshort\n")
    else:
        if mutation == "duplicate":
            rows[1]["trial_id"] = "t1"
        else:
            rows[0]["condition"] = "other"
        with trials.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    with pytest.raises(ParseError, match=error):
        audit_study(protocol, trials)


def test_study_cli_success_and_missing_input(tmp_path: Path, capsys) -> None:
    protocol, trials = inputs(tmp_path)
    assert study_main([str(protocol), str(trials)]) == 0
    assert json.loads(capsys.readouterr().out)["planned_trial_count"] == 3
    protocol.unlink()
    assert study_main([str(protocol), str(trials)]) == 2
    assert "invalid study inputs" in capsys.readouterr().err
