"""Non-destructive ADB capture of inputs already supported by the parser."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from aema.errors import AcquisitionError
from aema.files import sha256_file
from aema.session import CAPTURE_SCHEMA_VERSION, validate_capture_manifest


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def collect_session(*, serial: str, output_root: str | Path, adb: str = "adb") -> Path:
    """Capture read-only ADB outputs into one atomically published directory."""
    if not serial.strip():
        raise AcquisitionError("ADB serial is required")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=".aema-capture-", dir=root))
    started = _now()
    commands: list[dict] = []

    def run(*args: str) -> bytes:
        argv = [adb, "-s", serial, *args]
        command_started = _now()
        try:
            completed = subprocess.run(argv, capture_output=True, check=False, timeout=120)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AcquisitionError(f"ADB command failed: {argv}: {exc}") from exc
        commands.append(
            {
                "argv": argv,
                "started_at_utc": command_started,
                "ended_at_utc": _now(),
                "exit_code": completed.returncode,
                "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest().upper(),
                "stderr": completed.stderr.decode("utf-8", errors="replace"),
            }
        )
        if completed.returncode != 0:
            raise AcquisitionError(
                f"ADB command returned {completed.returncode}: {argv}: "
                f"{completed.stderr.decode('utf-8', errors='replace')}"
            )
        return completed.stdout

    try:
        if run("get-state").strip() != b"device":
            raise AcquisitionError("ADB target is not in device state")
        model = run("shell", "getprop", "ro.product.model").decode("utf-8").strip()
        build = run("shell", "getprop", "ro.build.fingerprint").decode("utf-8").strip()
        sdk = run("shell", "getprop", "ro.build.version.sdk").decode("utf-8").strip()
        outputs = {
            "stats.csv": ("shell", "dumpsys", "batterystats", "--checkin"),
            "stats.txt": ("shell", "dumpsys", "batterystats"),
            "packageUID.txt": ("shell", "pm", "list", "packages", "-U"),
            "battery_state.txt": ("shell", "dumpsys", "battery"),
        }
        for name, argv in outputs.items():
            content = run(*argv)
            if not content.strip():
                raise AcquisitionError(f"empty ADB output for {name}")
            (temp_dir / name).write_bytes(content)
        manifest = {
            "schema_version": CAPTURE_SCHEMA_VERSION,
            "session_id": uuid4().hex,
            "status": "complete",
            "started_at_utc": started,
            "ended_at_utc": _now(),
            "device": {
                "serial": serial,
                "model": model,
                "build_fingerprint": build,
                "sdk": sdk,
            },
            "commands": commands,
            "file_sha256": {name: sha256_file(temp_dir / name) for name in outputs},
            "battery_state_file": "battery_state.txt",
        }
        validate_capture_manifest(manifest, temp_dir)
        (temp_dir / "capture_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        final_dir = root / f"capture_{stamp}_{uuid4().hex[:8]}"
        os.replace(temp_dir, final_dir)
        return final_dir
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if isinstance(exc, AcquisitionError):
            raise
        raise AcquisitionError(f"capture failed: {exc}") from exc
