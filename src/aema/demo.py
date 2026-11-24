"""Offline, reproducible demonstration of the parser pipeline."""

from __future__ import annotations

from pathlib import Path

from aema.dataset import load_dataset
from aema.errors import ParseError
from aema.exporters import export_canonical_result
from aema.models import PipelineInputs
from aema.pipeline import run_pipeline


def run_demo(fixtures: str | Path, output_root: str | Path) -> dict:
    """Parse bundled-style fixtures and verify a published round trip."""
    root = Path(fixtures)
    result = run_pipeline(
        PipelineInputs(
            root / "checkin_v9.csv",
            root / "battery_report.txt",
            root / "packages.txt",
        )
    )
    counts = {
        "checkin": result.checkin.diagnostics.parsed_records,
        "battery_report": result.battery_report.diagnostics.parsed_records,
        "packages": result.packages.diagnostics.parsed_records,
    }
    if counts != {"checkin": 5, "battery_report": 3, "packages": 3}:
        raise ParseError(f"fixture record counts differ from demo baseline: {counts}")
    directory = export_canonical_result(result, output_root)
    records, relations, manifest = load_dataset(directory)
    if len(records) != 88 or len(relations) != 3:
        raise ParseError("demo canonical counts differ from baseline")
    return {
        "purpose": "parser_fixture_demo",
        "scientific_validation": False,
        "output_directory": str(directory),
        "record_counts": counts,
        "canonical_records": len(records),
        "package_uid_relations": len(relations),
        "canonical_schema_version": manifest["canonical_schema_version"],
    }
