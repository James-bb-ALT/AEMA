from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import aema.collector as collector
from aema.cli import main
from aema.errors import AcquisitionError
from aema.models import PipelineInputs
from aema.pipeline import run_pipeline
from aema.session import validate_capture_manifest


def fake_adb(fixture_dir: Path, *, failing: str | None = None):
    calls: list[list[str]] = []
    outputs = {
        ("get-state",): b"device\n",
        ("shell", "getprop", "ro.product.model"): b"Test device\n",
        ("shell", "getprop", "ro.build.fingerprint"): b"test/build\n",
        ("shell", "getprop", "ro.build.version.sdk"): b"35\n",
        ("shell", "dumpsys", "batterystats", "--checkin"): (
            fixture_dir / "checkin_v9.csv"
        ).read_bytes(),
        ("shell", "dumpsys", "batterystats"): (fixture_dir / "battery_report.txt").read_bytes(),
        ("shell", "pm", "list", "packages", "-U"): (fixture_dir / "packages.txt").read_bytes(),
        ("shell", "dumpsys", "battery"): b"level: 80\nstatus: 3\n",
    }

    def run(argv, **kwargs):
        calls.append(argv)
        command = tuple(argv[3:])
        assert kwargs["capture_output"] is True
        assert kwargs["timeout"] == 120
        if failing is not None and failing in command:
            return subprocess.CompletedProcess(argv, 1, b"", b"device error")
        return subprocess.CompletedProcess(argv, 0, outputs[command], b"")

    return run, calls


def test_capture_manifest_and_cli_are_complete_and_read_only(
    fixture_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    run, calls = fake_adb(fixture_dir)
    monkeypatch.setattr(collector.subprocess, "run", run)
    root = tmp_path / "captures"
    assert main(["collect", "--serial", "SERIAL", "--output-root", str(root)]) == 0
    directory = Path(json.loads(capsys.readouterr().out)["capture_directory"])
    manifest = json.loads((directory / "capture_manifest.json").read_text(encoding="utf-8"))
    validate_capture_manifest(manifest, directory)
    assert manifest["device"]["build_fingerprint"] == "test/build"
    assert manifest["file_sha256"].keys() == {
        "stats.csv",
        "stats.txt",
        "packageUID.txt",
        "battery_state.txt",
    }
    assert all(argv[:3] == ["adb", "-s", "SERIAL"] for argv in calls)
    assert not any("--reset" in argv for argv in calls)
    parsed = run_pipeline(
        PipelineInputs(
            directory / "stats.csv",
            directory / "stats.txt",
            directory / "packageUID.txt",
        )
    )
    assert parsed.checkin.diagnostics.parsed_records == 5


def test_capture_failure_publishes_nothing(
    fixture_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run, _ = fake_adb(fixture_dir, failing="batterystats")
    monkeypatch.setattr(collector.subprocess, "run", run)
    root = tmp_path / "captures"
    with pytest.raises(AcquisitionError, match="returned 1"):
        collector.collect_session(serial="SERIAL", output_root=root)
    assert list(root.iterdir()) == []


def test_manifest_rejects_missing_device_field_and_changed_bytes(
    fixture_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run, _ = fake_adb(fixture_dir)
    monkeypatch.setattr(collector.subprocess, "run", run)
    directory = collector.collect_session(serial="SERIAL", output_root=tmp_path)
    manifest = json.loads((directory / "capture_manifest.json").read_text(encoding="utf-8"))
    missing = json.loads(json.dumps(manifest))
    del missing["device"]["sdk"]
    with pytest.raises(AcquisitionError, match="missing or invalid field"):
        validate_capture_manifest(missing, directory)
    with (directory / "stats.csv").open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(AcquisitionError, match="hash mismatch"):
        validate_capture_manifest(manifest, directory)
