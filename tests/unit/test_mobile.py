from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

import aema.mobile as mobile
from aema.dataset import load_dataset
from aema.files import sha256_file


def test_failure_bridge_starts_without_loading_numeric_libraries() -> None:
    completed = subprocess.run(
        [sys.executable, "-c", "import aema.mobile, sys; assert 'pandas' not in sys.modules"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    import aema
    from aema.models import PipelineInputs, PipelineResult
    from aema.pipeline import run_pipeline

    assert aema.PipelineInputs is PipelineInputs
    assert aema.PipelineResult is PipelineResult
    assert aema.parse_inputs is run_pipeline
    with pytest.raises(AttributeError):
        _ = aema.missing_public_symbol


def staged(fixture_dir: Path, tmp_path: Path) -> tuple[Path, dict]:
    directory = tmp_path / "stage"
    directory.mkdir()
    for origin, name in (
        ("checkin_v9.csv", "stats.csv"),
        ("battery_report.txt", "stats.txt"),
        ("packages.txt", "packageUID.txt"),
    ):
        shutil.copy(fixture_dir / origin, directory / name)
    (directory / "battery_state.txt").write_text("level: 80\n", encoding="utf-8")
    return directory, {
        "schema_version": "1.0",
        "session_id": "s1",
        "status": "complete",
        "device": {
            "serial": "install-id",
            "model": "model",
            "build_fingerprint": "build",
            "sdk": "35",
        },
        "started_at_utc": "2026-01-01T00:00:00Z",
        "ended_at_utc": "2026-01-01T00:01:00Z",
        "battery_state_file": "battery_state.txt",
        "commands": [
            {
                "argv": ["dumpsys", "battery"],
                "exit_code": 0,
                "stdout_sha256": sha256_file(directory / "battery_state.txt"),
                "started_at_utc": "2026-01-01T00:00:00Z",
                "ended_at_utc": "2026-01-01T00:01:00Z",
            }
        ],
    }


def test_mobile_zip_contains_verifiable_host_dataset(fixture_dir: Path, tmp_path: Path) -> None:
    stage, metadata = staged(fixture_dir, tmp_path)
    path = Path(
        mobile.publish_capture(str(stage), str(tmp_path / "captures"), json.dumps(metadata))
    )
    with zipfile.ZipFile(path) as archive:
        archive.extractall(tmp_path / "unpacked")
    manifest = json.loads((tmp_path / "unpacked/capture_manifest.json").read_text())
    assert manifest["parse_status"] == "complete"
    records, relations, _ = load_dataset(tmp_path / "unpacked" / manifest["parsed_directory"])
    assert len(records) == 88 and len(relations) == 3
    assert manifest["scientific_validation"] is False
    assert not stage.exists()


@pytest.mark.parametrize("state", ["failed", "unsupported"])
def test_mobile_retains_raw_when_collection_or_parser_fails(
    state: str, fixture_dir: Path, tmp_path: Path
) -> None:
    stage, metadata = staged(fixture_dir, tmp_path)
    if state == "failed":
        metadata["status"] = "failed"
        (stage / "stats.csv").unlink()
    else:
        (stage / "stats.csv").write_text("10,0,l,m,unsupported\n", encoding="utf-8")
    path = mobile.publish_capture(str(stage), str(tmp_path / "captures"), json.dumps(metadata))
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("capture_manifest.json"))
        assert archive.read("stats.txt") == (fixture_dir / "battery_report.txt").read_bytes()
    assert manifest["parse_status"] == (
        "not_attempted" if state == "failed" else "unsupported_or_invalid"
    )


def test_archive_failure_keeps_staging_and_removes_partial_zip(
    fixture_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stage, metadata = staged(fixture_dir, tmp_path)

    def fail(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(mobile.zipfile.ZipFile, "write", fail)
    with pytest.raises(OSError, match="disk full"):
        mobile.publish_capture(str(stage), str(tmp_path / "captures"), json.dumps(metadata))
    assert stage.is_dir()
    assert list((tmp_path / "captures").iterdir()) == []
