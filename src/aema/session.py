"""Validation of an immutable host-side capture session."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from aema.errors import AcquisitionError
from aema.files import sha256_file

CAPTURE_SCHEMA_VERSION = "1.0"
CAPTURE_FILES = ("stats.csv", "stats.txt", "packageUID.txt", "battery_state.txt")


def _utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise AcquisitionError("invalid capture timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise AcquisitionError("capture timestamps must be UTC")
    return parsed


def validate_capture_manifest(manifest: dict, directory: str | Path) -> None:
    """Require complete metadata and matching hashes for all captured files."""
    try:
        if manifest["schema_version"] != CAPTURE_SCHEMA_VERSION:
            raise AcquisitionError("unsupported capture schema version")
        if not manifest["session_id"] or manifest["status"] != "complete":
            raise AcquisitionError("capture session is incomplete")
        device = manifest["device"]
        for name in ("serial", "model", "build_fingerprint", "sdk"):
            if not isinstance(device[name], str) or not device[name].strip():
                raise AcquisitionError(f"missing device {name}")
        if _utc(manifest["started_at_utc"]) >= _utc(manifest["ended_at_utc"]):
            raise AcquisitionError("capture interval is invalid")
        commands = manifest["commands"]
        if not commands:
            raise AcquisitionError("capture command log is empty")
        for command in commands:
            if not command["argv"] or not isinstance(command["argv"], list):
                raise AcquisitionError("invalid capture command")
            if command["exit_code"] != 0 or not command["stdout_sha256"]:
                raise AcquisitionError("capture command did not succeed")
            if _utc(command["started_at_utc"]) > _utc(command["ended_at_utc"]):
                raise AcquisitionError("invalid command interval")
        hashes = manifest["file_sha256"]
        if set(hashes) != set(CAPTURE_FILES):
            raise AcquisitionError("capture file set is incomplete")
        for name in CAPTURE_FILES:
            if not (Path(directory) / name).is_file():
                raise AcquisitionError(f"missing capture file {name}")
            if sha256_file(Path(directory) / name) != hashes[name]:
                raise AcquisitionError(f"capture hash mismatch for {name}")
        if manifest["battery_state_file"] != "battery_state.txt":
            raise AcquisitionError("battery state provenance is missing")
    except (KeyError, TypeError) as exc:
        raise AcquisitionError(f"capture manifest missing or invalid field: {exc}") from exc
