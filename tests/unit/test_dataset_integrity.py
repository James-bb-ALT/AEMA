from __future__ import annotations

import json
from pathlib import Path

import pytest

from aema.dataset import load_dataset
from aema.errors import ParseError
from aema.exporters import export_canonical_result
from aema.models import PipelineInputs
from aema.pipeline import run_pipeline


@pytest.mark.parametrize(
    "mutation",
    ["missing_hash", "unlisted_table", "traversal", "count", "schema", "catalog", "format"],
)
def test_dataset_rejects_unverifiable_manifest(
    fixture_dir: Path, tmp_path: Path, mutation: str
) -> None:
    result = run_pipeline(
        PipelineInputs(
            fixture_dir / "checkin_v9.csv",
            fixture_dir / "battery_report.txt",
            fixture_dir / "packages.txt",
        )
    )
    directory = export_canonical_result(result, tmp_path)
    path = directory / "manifest.json"
    manifest = json.loads(path.read_text())
    if mutation == "missing_hash":
        manifest["artifact_sha256"].pop("canonical_records.csv")
    elif mutation == "unlisted_table":
        manifest["artifact_sha256"].pop("canonical_records.csv")
        manifest["files"].remove("canonical_records.csv")
    elif mutation == "traversal":
        manifest["artifact_sha256"]["../outside"] = "A" * 64
        manifest["files"].append("../outside")
    elif mutation == "count":
        manifest["counts"]["canonical_records"] = 0
    else:
        manifest[
            {
                "schema": "canonical_schema_version",
                "catalog": "catalog_version",
                "format": "manifest_format_version",
            }[mutation]
        ] = "unknown"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ParseError):
        load_dataset(directory)
