from __future__ import annotations

from pathlib import Path

from aema.adapters import adapt_pipeline
from aema.catalog import (
    CATALOG,
    CATALOG_BY_FIELD,
    CATALOG_VERSION,
    assert_catalog_covers,
)
from aema.models import PipelineInputs
from aema.pipeline import run_pipeline
from aema.schemas import MISC_FIELDS, NETWORK_FIELDS, PROCESS_FIELDS


def test_catalog_covers_all_current_export_columns() -> None:
    root = Path("tests/fixtures")
    result = run_pipeline(
        PipelineInputs(root / "checkin_v9.csv", root / "battery_report.txt", root / "packages.txt")
    )
    assert CATALOG_VERSION == "1.1"
    assert len(CATALOG) == len({(entry.source, entry.field) for entry in CATALOG})
    assert len(CATALOG) == 145
    assert_catalog_covers(result.frames())


def test_catalog_covers_schema_and_optional_fields() -> None:
    checkin = {entry.field for entry in CATALOG if entry.source == "checkin"}
    assert set(PROCESS_FIELDS) | set(NETWORK_FIELDS) | set(MISC_FIELDS) <= checkin
    assert {"partial_time_ms", "window_total_duration_ms", "cpu_estimated_charge_mah"} <= {
        entry.field for entry in CATALOG
    }


def test_catalog_metadata_semantics() -> None:
    by_field = {key: value for key, value in CATALOG_BY_FIELD.items()}
    assert by_field[("checkin", "mobile_wakeup_count")].unit == "count"
    assert by_field[("power", "battery_capacity_mah")].measurement_kind == "reported_capacity"
    assert by_field[("power", "actual_drain_min_mah")].measurement_kind == "reported_drain_range"
    assert (
        by_field[("power", "total_estimated_charge_mah")].measurement_kind
        == "uid_attributed_charge_estimate"
    )
    assert (
        by_field[("power", "cpu_estimated_charge_mah")].measurement_kind
        == "estimated_or_attributed_charge"
    )
    assert all(entry.method for entry in CATALOG if entry.classification == "numeric_metric")
    assert {
        entry.evidence_class for entry in CATALOG if entry.classification == "numeric_metric"
    } == {"estimated", "proxy"}
    assert not any(entry.evidence_class == "measured" for entry in CATALOG)
    for entry in CATALOG:
        if entry.classification == "numeric_metric":
            assert entry.metric and entry.measurement_kind
            assert entry.unit is not None
        else:
            assert entry.metric is None and entry.measurement_kind is None


def test_catalog_rejects_new_column() -> None:
    root = Path("tests/fixtures")
    result = run_pipeline(
        PipelineInputs(root / "checkin_v9.csv", root / "battery_report.txt", root / "packages.txt")
    )
    frames = result.frames()
    frames["package_uid_parsed.csv"]["new_field"] = 1
    try:
        assert_catalog_covers(frames)
    except AssertionError as exc:
        assert "new_field" in str(exc)
    else:
        raise AssertionError("catalog accepted an uncatalogued column")


def test_catalog_covers_extended_public_capture(fixture_dir: Path) -> None:
    result = run_pipeline(
        PipelineInputs(
            fixture_dir / "checkin_v9.csv",
            fixture_dir / "battery_report_extended.txt",
            fixture_dir / "packages.txt",
        )
    )
    assert_catalog_covers(result.frames())
    canonical = adapt_pipeline(result)
    assert canonical.diagnostics.unknown_numeric_fields == ()
    assert {record.method for record in canonical.records} == {
        "batterystats_checkin",
        "batterystats_power_report",
    }
    assert any(record.metric == "cpu_apps_estimated_charge_mah" for record in canonical.records)
    assert any(record.metric == "bluetooth_estimated_charge_mah" for record in canonical.records)
