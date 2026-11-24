"""Offline Android bridge. The Android app bundles this exact host-side package."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from aema import __version__
from aema.errors import AemaError
from aema.session import CAPTURE_FILES, validate_capture_manifest


def publish_capture(staging: str, output_root: str, metadata_json: str) -> str:
    """Publish a fresh ZIP, retaining raw inputs even when their format is unsupported.

    Collection and parsing have separate statuses. Snapshots are cumulative Android
    BatteryStats exports, not reset-based six-hour measurements.
    """
    directory = Path(staging)
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    metadata = json.loads(metadata_json)
    metadata["app_version"] = __version__
    metadata["snapshot_semantics"] = "cumulative_since_android_reset; not_a_6h_delta"
    metadata["file_sha256"] = {
        name: hashlib.sha256((directory / name).read_bytes()).hexdigest().upper()
        for name in CAPTURE_FILES
        if (directory / name).is_file()
    }
    metadata["parse_status"] = "not_attempted"
    if metadata.get("status") == "complete":
        try:
            from aema.exporters import export_canonical_result
            from aema.models import PipelineInputs
            from aema.pipeline import run_pipeline

            validate_capture_manifest(metadata, directory)
            result = run_pipeline(
                PipelineInputs(
                    directory / "stats.csv",
                    directory / "stats.txt",
                    directory / "packageUID.txt",
                )
            )
            parsed = export_canonical_result(result, directory / "parsed")
            metadata["parse_status"] = "complete"
            metadata["parsed_directory"] = parsed.relative_to(directory).as_posix()
        except AemaError as exc:
            metadata["parse_status"] = "unsupported_or_invalid"
            metadata["parse_error"] = str(exc)
    metadata["scientific_validation"] = False
    (directory / "capture_manifest.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    final = root / f"aema_{stamp}_{uuid4().hex[:12]}.zip"
    descriptor, temporary = tempfile.mkstemp(prefix=".pending-", dir=root)
    os.close(descriptor)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(directory.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(directory).as_posix())
        os.replace(temporary, final)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise
    shutil.rmtree(directory)
    return str(final)
