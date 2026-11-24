from __future__ import annotations

import json
from pathlib import Path

import pytest

from aema.cli import main
from aema.errors import ExportError
from aema.exporters import export_canonical_result
from aema.models import PipelineInputs
from aema.pipeline import run_pipeline
from aema.privacy import export_pseudonymous_study


def dataset(fixture_dir: Path, tmp_path: Path) -> Path:
    result = run_pipeline(
        PipelineInputs(
            fixture_dir / "checkin_v9.csv",
            fixture_dir / "battery_report.txt",
            fixture_dir / "packages.txt",
        )
    )
    return export_canonical_result(result, tmp_path / "datasets")


def test_export_has_no_raw_identifiers_and_preserves_shared_uid(
    fixture_dir: Path, tmp_path: Path
) -> None:
    source = dataset(fixture_dir, tmp_path)
    output = export_pseudonymous_study(source, tmp_path / "study.json", b"a" * 32)
    text = output.read_text(encoding="utf-8")
    report = json.loads(text)
    assert len(report["records"]) == 88
    relations = report["relations"]
    assert relations[0]["uid_token"] == relations[1]["uid_token"]
    assert relations[0]["package_token"] != relations[1]["package_token"]
    for forbidden in (
        "app.one",
        "app.two",
        "package_name",
        "input_sha256",
        "payload",
        "input_paths",
        str(tmp_path),
    ):
        assert forbidden not in text
    another = export_pseudonymous_study(source, tmp_path / "other.json", b"b" * 32)
    assert json.loads(another.read_text())["relations"][0] != relations[0]
    same = export_pseudonymous_study(source, tmp_path / "same.json", b"a" * 32)
    assert same.read_bytes() == output.read_bytes()
    with pytest.raises(ExportError, match="cannot publish"):
        export_pseudonymous_study(source, output, b"a" * 32)
    assert output.read_text() == text


def test_privacy_cli_and_key_errors(fixture_dir: Path, tmp_path: Path, capsys) -> None:
    source = dataset(fixture_dir, tmp_path)
    key = tmp_path / "study.key"
    key.write_bytes(b"a" * 32)
    args = [
        "pseudonymize",
        "--dataset",
        str(source),
        "--key-file",
        str(key),
        "--output",
        str(tmp_path / "export.json"),
    ]
    assert main(args) == 0
    assert "study_file" in capsys.readouterr().out
    key.write_bytes(b"short")
    assert main(args) == 2
    assert "at least 32" in capsys.readouterr().err
    key.unlink()
    assert main(args) == 2
