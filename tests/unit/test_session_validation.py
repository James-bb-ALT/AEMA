from __future__ import annotations

import copy
from pathlib import Path

import pytest

from aema.errors import AcquisitionError
from aema.files import sha256_file
from aema.session import CAPTURE_FILES, validate_capture_manifest


@pytest.fixture
def capture(tmp_path: Path) -> tuple[dict, Path]:
    for name in CAPTURE_FILES:
        (tmp_path / name).write_text("captured bytes", encoding="utf-8")
    return {
        "schema_version": "1.0",
        "session_id": "session",
        "status": "complete",
        "started_at_utc": "2026-01-01T00:00:00Z",
        "ended_at_utc": "2026-01-01T00:01:00Z",
        "device": {"serial": "device", "model": "model", "build_fingerprint": "build", "sdk": "35"},
        "commands": [
            {
                "argv": ["dumpsys", "battery"],
                "exit_code": 0,
                "stdout_sha256": "a" * 64,
                "started_at_utc": "2026-01-01T00:00:00Z",
                "ended_at_utc": "2026-01-01T00:01:00Z",
            }
        ],
        "file_sha256": {name: sha256_file(tmp_path / name) for name in CAPTURE_FILES},
        "battery_state_file": "battery_state.txt",
    }, tmp_path


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("schema_version", "2.0", "unsupported"),
        ("session_id", "", "incomplete"),
        ("status", "failed", "incomplete"),
        ("started_at_utc", "invalid", "invalid capture timestamp"),
        ("started_at_utc", None, "invalid capture timestamp"),
        ("started_at_utc", "2026-01-01T00:00:00", "must be UTC"),
        ("started_at_utc", "2026-01-01T00:00:00+01:00", "must be UTC"),
        ("ended_at_utc", "2025-01-01T00:00:00Z", "interval is invalid"),
        ("commands", [], "log is empty"),
        ("file_sha256", {}, "file set is incomplete"),
        ("battery_state_file", "other.txt", "provenance is missing"),
    ],
)
def test_rejects_incomplete_or_inconsistent_capture(capture, field, value, error) -> None:
    manifest, directory = capture
    manifest[field] = value
    with pytest.raises(AcquisitionError, match=error):
        validate_capture_manifest(manifest, directory)


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("argv", "dumpsys", "invalid capture command"),
        ("argv", [], "invalid capture command"),
        ("exit_code", 1, "did not succeed"),
        ("stdout_sha256", "", "did not succeed"),
        ("ended_at_utc", "2025-01-01T00:00:00Z", "invalid command interval"),
    ],
)
def test_rejects_bad_command_log(capture, field, value, error) -> None:
    manifest, directory = capture
    manifest["commands"][0][field] = value
    with pytest.raises(AcquisitionError, match=error):
        validate_capture_manifest(manifest, directory)


def test_requires_device_identity_and_all_files(capture) -> None:
    manifest, directory = capture
    invalid = copy.deepcopy(manifest)
    invalid["device"]["sdk"] = " "
    with pytest.raises(AcquisitionError, match="missing device sdk"):
        validate_capture_manifest(invalid, directory)
    (directory / "stats.csv").unlink()
    with pytest.raises(AcquisitionError, match="missing capture file"):
        validate_capture_manifest(manifest, directory)
