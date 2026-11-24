"""Minimal public-facing export for the total-charge study."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from aema.catalog import CATALOG_BY_FIELD
from aema.errors import ExportError
from aema.files import sha256_file
from aema.parsers.battery_report import BatteryReportParser

STUDY_SUMMARY_VERSION = "1.0"


def export_total_charge_summary(report: str | Path, output_root: str | Path) -> Path:
    """Publish one attributed total without package, UID, or local path metadata."""
    path = Path(report)
    parsed = BatteryReportParser(path).parse_result()
    summaries = [record for record in parsed.records if record.get("record_type") == "summary"]
    if len(summaries) != 1:
        raise ExportError("battery report must contain one summary")
    entry = CATALOG_BY_FIELD[("power", "computed_drain_mah")]
    payload = {
        "schema_version": STUDY_SUMMARY_VERSION,
        "study_id": uuid4().hex,
        "metric": "computed_drain_mah",
        "value": summaries[0]["computed_drain_mah"],
        "unit": entry.unit,
        "method": entry.method,
        "evidence_class": entry.evidence_class,
        "calibrated_uncertainty": None,
        "source_sha256": sha256_file(path),
        "limitation": "BatteryStats estimate; not validated against an external reference.",
    }
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=".aema-study-", dir=root))
    try:
        (temp_dir / "study_summary.json").write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        final_dir = root / f"study_{stamp}_{uuid4().hex[:8]}"
        os.replace(temp_dir, final_dir)
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise ExportError(f"cannot publish study summary: {exc}") from exc
    return final_dir
