"""Import and verify a published canonical dataset."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from aema.catalog import CATALOG_1_2_NEW_METRICS, SUPPORTED_CATALOG_VERSIONS
from aema.errors import ParseError
from aema.exporters import MANIFEST_FORMAT_VERSION
from aema.models import CANONICAL_SCHEMA_VERSION, CanonicalRecord, PackageUidRelation, Source


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _record(row: dict[str, str]) -> CanonicalRecord:
    data: dict[str, Any] = dict(row)
    for name in ("value", "uid", "line_number", "payload"):
        data[name] = json.loads(row[name]) if row[name] else None
    for name in ("unit", "method", "package_name"):
        data[name] = row[name] or None
    return CanonicalRecord.from_dict(data)


def _relation(row: dict[str, str]) -> PackageUidRelation:
    data: dict[str, Any] = dict(row)
    data["uid"] = json.loads(row["uid"])
    data["line_number"] = json.loads(row["line_number"]) if row["line_number"] else None
    return PackageUidRelation.from_dict(data)


def load_dataset(
    directory: str | Path,
) -> tuple[list[CanonicalRecord], list[PackageUidRelation], dict]:
    """Read canonical CSV tables only after manifest and artifact integrity checks."""
    root = Path(directory)
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        if manifest["canonical_schema_version"] != CANONICAL_SCHEMA_VERSION:
            raise ParseError("unsupported canonical schema version")
        if manifest["manifest_format_version"] != MANIFEST_FORMAT_VERSION:
            raise ParseError("unsupported manifest format version")
        if manifest["catalog_version"] not in SUPPORTED_CATALOG_VERSIONS:
            raise ParseError("unsupported metric catalog version")
        hashes = manifest["artifact_sha256"]
        if set(manifest["files"]) != set(hashes):
            raise ParseError("manifest file list does not match artifact hashes")
        if not {"canonical_records.csv", "canonical_relations.csv"} <= set(hashes):
            raise ParseError("manifest must hash both canonical CSV tables")
        for name, expected in hashes.items():
            if not name or Path(name).name != name:
                raise ParseError(f"invalid artifact name: {name!r}")
            actual = hashlib.sha256((root / name).read_bytes()).hexdigest().upper()
            if actual != expected:
                raise ParseError(f"artifact hash mismatch: {name}")
        records = [_record(row) for row in _read_csv(root / "canonical_records.csv")]
        if manifest["catalog_version"] == "1.1" and any(
            row.source == Source.POWER and row.metric in CATALOG_1_2_NEW_METRICS for row in records
        ):
            raise ParseError("catalog 1.1 does not define GPU metrics")
        relations = [_relation(row) for row in _read_csv(root / "canonical_relations.csv")]
        counts = manifest["counts"]
        if (
            len(records) != counts["canonical_records"]
            or len(relations) != counts["package_uid_relations"]
        ):
            raise ParseError("canonical record counts do not match manifest")
        input_hashes = manifest["input_sha256"]
        expected_by_source = {
            Source.CHECKIN: input_hashes["checkin"],
            Source.POWER: input_hashes["battery_report"],
            Source.PACKAGES: input_hashes["packages"],
        }
        for item in (*records, *relations):
            provenance = item.provenance
            if provenance.input_sha256 != expected_by_source[provenance.source].lower():
                raise ParseError("record input hash does not match manifest")
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, csv.Error) as exc:
        raise ParseError(f"invalid canonical dataset: {exc}") from exc
    return records, relations, manifest
