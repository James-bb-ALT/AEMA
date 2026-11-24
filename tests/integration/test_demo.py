from __future__ import annotations

import json
from pathlib import Path

from aema.cli import main
from aema.dataset import load_dataset


def test_offline_demo_exports_and_reimports_fixture(
    fixture_dir: Path, tmp_path: Path, capsys
) -> None:
    assert (
        main(
            [
                "demo",
                "--fixtures",
                str(fixture_dir),
                "--output-root",
                str(tmp_path),
            ]
        )
        == 0
    )
    summary = json.loads(capsys.readouterr().out)
    assert summary["scientific_validation"] is False
    assert summary["canonical_records"] == 88
    assert summary["package_uid_relations"] == 3
    records, relations, manifest = load_dataset(summary["output_directory"])
    assert len(records) == 88 and len(relations) == 3
    assert manifest["canonical_schema_version"] == summary["canonical_schema_version"]


def test_demo_reports_missing_fixture_without_output(tmp_path: Path, capsys) -> None:
    output = tmp_path / "output"
    assert (
        main(
            [
                "demo",
                "--fixtures",
                str(tmp_path / "missing"),
                "--output-root",
                str(output),
            ]
        )
        == 2
    )
    assert "does not exist" in capsys.readouterr().err
    assert not output.exists()
