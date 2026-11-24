from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from aema.cli import main


def test_cli_runs_complete_flow(fixture_dir: Path, tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            "--checkin",
            str(fixture_dir / "checkin_v9.csv"),
            "--battery-report",
            str(fixture_dir / "battery_report.txt"),
            "--packages",
            str(fixture_dir / "packages.txt"),
            "--output-root",
            str(tmp_path),
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["record_counts"] == {
        "battery_report": 3,
        "checkin": 5,
        "packages": 3,
    }
    assert Path(payload["output_directory"]).is_dir()
    output = Path(payload["output_directory"])
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["canonical_schema_version"] == "1.0"
    assert (output / "canonical_records.jsonl").is_file()
    assert (output / "canonical_relations.jsonl").is_file()
    assert (output / "canonical_diagnostics.json").is_file()
    canonical_diagnostics = json.loads(
        (output / "canonical_diagnostics.json").read_text(encoding="utf-8")
    )
    assert manifest["canonical_diagnostics"] == canonical_diagnostics
    assert canonical_diagnostics["sources"]["checkin"]["accepted_lines"] == [2, 3, 4, 5, 6]


def test_cli_inspects_metric_with_unit_method_and_limit(capsys) -> None:
    assert main(["inspect", "--source", "power", "--metric", "cpu_apps_estimated_charge_mah"]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert len(rows) == 1
    assert rows[0]["unit"] == "mAh"
    assert rows[0]["method"] == "batterystats_power_report"
    assert rows[0]["evidence_class"] == "estimated"
    assert rows[0]["calibrated_uncertainty"] is None
    assert "uncertainty" in rows[0]["limitation"]


def test_cli_inspect_rejects_unknown_metric(capsys) -> None:
    assert main(["inspect", "--metric", "unknown_metric"]) == 2
    assert "no catalogued metric" in capsys.readouterr().err


def test_cli_reports_required_input_failure(tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            "--checkin",
            str(tmp_path / "missing.csv"),
            "--battery-report",
            str(tmp_path / "missing.txt"),
            "--packages",
            str(tmp_path / "missing-packages.txt"),
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "does not exist" in captured.err


def _entrypoint(name: str) -> list[str]:
    if name == "module":
        return [sys.executable, "-m", "aema"]
    executable = Path(sys.executable).with_name("aema.exe" if os.name == "nt" else "aema")
    if not executable.exists():
        pytest.skip("installed aema entrypoint unavailable")
    return [str(executable)]


@pytest.mark.parametrize("entrypoint", ["console", "module"])
def test_installed_entrypoints_return_success_json(
    entrypoint: str, fixture_dir: Path, tmp_path: Path
) -> None:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(Path("src").resolve())
    completed = subprocess.run(
        _entrypoint(entrypoint)
        + [
            "--checkin",
            str(fixture_dir / "checkin_v9.csv"),
            "--battery-report",
            str(fixture_dir / "battery_report.txt"),
            "--packages",
            str(fixture_dir / "packages.txt"),
            "--output-root",
            str(tmp_path / entrypoint),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert completed.returncode == 0
    assert completed.stderr == ""
    assert json.loads(completed.stdout)["record_counts"]["checkin"] == 5


@pytest.mark.parametrize("entrypoint", ["console", "module"])
def test_installed_entrypoints_reject_missing_arguments(entrypoint: str) -> None:
    completed = subprocess.run(_entrypoint(entrypoint), check=False, capture_output=True, text=True)
    assert completed.returncode == 2
    assert "required" in completed.stderr
    assert completed.stdout == ""


def test_cli_lenient_recovers_record_error_and_fatal_error_publishes_nothing(
    fixture_dir: Path, tmp_path: Path, capsys
) -> None:
    checkin = tmp_path / "mixed.csv"
    checkin.write_text(
        "9,0,i,vers\n9,1,l,pr,broken\n9,1,l,pwi,cpu,1,0,0,0\n",
        encoding="utf-8",
    )
    output_root = tmp_path / "lenient-output"
    exit_code = main(
        [
            "--checkin",
            str(checkin),
            "--battery-report",
            str(fixture_dir / "battery_report.txt"),
            "--packages",
            str(fixture_dir / "packages.txt"),
            "--output-root",
            str(output_root),
            "--lenient",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    manifest = json.loads(
        (Path(payload["output_directory"]) / "manifest.json").read_text(encoding="utf-8")
    )
    assert exit_code == 0
    assert len(manifest["records"]["checkin"]["warnings"]) == 1
    diagnostics = json.loads(
        (Path(payload["output_directory"]) / "canonical_diagnostics.json").read_text(
            encoding="utf-8"
        )
    )
    assert diagnostics["sources"]["checkin"]["rejected_lines"] == [2]
    assert diagnostics["sources"]["checkin"]["accepted_lines"] == [3]
    assert manifest["canonical_diagnostics"] == diagnostics

    fatal = tmp_path / "fatal.csv"
    fatal.write_text("9,0,i,vers\n10,1,l,pwi,cpu,1,0,0,0\n", encoding="utf-8")
    fatal_root = tmp_path / "fatal-output"
    exit_code = main(
        [
            "--checkin",
            str(fatal),
            "--battery-report",
            str(fixture_dir / "battery_report.txt"),
            "--packages",
            str(fixture_dir / "packages.txt"),
            "--output-root",
            str(fatal_root),
            "--lenient",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "unsupported check-in version" in captured.err
    assert not fatal_root.exists()


@pytest.mark.parametrize(
    ("contents", "expected"),
    [
        (b"9,0,i,vers\n10,1,l,pwi,cpu,1,0,0,0\n", "unsupported check-in version"),
        (b"9,0,i,vers\n9,1,l,pr,broken\n", "data fields"),
        (b"", "missing version record"),
        (b"\xff\xfe\x00", "cannot decode"),
    ],
)
def test_cli_strict_input_errors_publish_nothing(
    contents: bytes, expected: str, fixture_dir: Path, tmp_path: Path, capsys
) -> None:
    checkin = tmp_path / "bad.csv"
    checkin.write_bytes(contents)
    output_root = tmp_path / "output"
    exit_code = main(
        [
            "--checkin",
            str(checkin),
            "--battery-report",
            str(fixture_dir / "battery_report.txt"),
            "--packages",
            str(fixture_dir / "packages.txt"),
            "--output-root",
            str(output_root),
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 2
    assert expected in captured.err
    assert not output_root.exists()
