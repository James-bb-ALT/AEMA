from __future__ import annotations

import json
from pathlib import Path

import pytest

from aema.dataset import load_dataset
from aema.errors import ParseError
from aema.exporters import export_canonical_result
from aema.models import PipelineInputs
from aema.pipeline import run_pipeline


@pytest.mark.parametrize("gpu", [False, True])
def test_catalog_1_1_import_remains_compatible_but_cannot_claim_gpu_metrics(
    fixture_dir: Path, tmp_path: Path, gpu: bool
) -> None:
    result = run_pipeline(
        PipelineInputs(
            fixture_dir / "checkin_v9.csv",
            fixture_dir / ("battery_report_gpu.txt" if gpu else "battery_report.txt"),
            fixture_dir / "packages.txt",
        )
    )
    directory = export_canonical_result(result, tmp_path)
    assert load_dataset(directory)[2]["catalog_version"] == "1.2"
    path = directory / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["catalog_version"] = "1.1"
    path.write_text(json.dumps(manifest))
    if gpu:
        with pytest.raises(ParseError, match="GPU"):
            load_dataset(directory)
    else:
        records, _, verified = load_dataset(directory)
        assert len(records) == 88 and verified["catalog_version"] == "1.1"


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
