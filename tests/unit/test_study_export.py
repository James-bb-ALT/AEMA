from __future__ import annotations

import json
from pathlib import Path

from aema.cli import main
from aema.files import sha256_file


def test_study_summary_contains_only_total_and_nonidentifying_metadata(
    fixture_dir: Path, tmp_path: Path, capsys
) -> None:
    report = fixture_dir / "battery_report.txt"
    assert (
        main(
            [
                "study-summary",
                "--battery-report",
                str(report),
                "--output-root",
                str(tmp_path),
            ]
        )
        == 0
    )
    directory = Path(json.loads(capsys.readouterr().out)["study_directory"])
    content = (directory / "study_summary.json").read_text(encoding="utf-8")
    payload = json.loads(content)
    assert payload["metric"] == "computed_drain_mah"
    assert payload["value"] == 12
    assert payload["unit"] == "mAh"
    assert payload["source_sha256"] == sha256_file(report)
    assert payload["calibrated_uncertainty"] is None
    assert set(payload) == {
        "schema_version",
        "study_id",
        "metric",
        "value",
        "unit",
        "method",
        "evidence_class",
        "calibrated_uncertainty",
        "source_sha256",
        "limitation",
    }
    assert "u10a42" not in content
    assert "com.example" not in content
    assert str(report.resolve()) not in content


def test_study_summary_rejects_missing_report(tmp_path: Path, capsys) -> None:
    output = tmp_path / "output"
    assert (
        main(
            [
                "study-summary",
                "--battery-report",
                str(tmp_path / "missing.txt"),
                "--output-root",
                str(output),
            ]
        )
        == 2
    )
    assert "does not exist" in capsys.readouterr().err
    assert not output.exists()
