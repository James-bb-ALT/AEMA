"""User-facing descriptions of catalogued metrics."""

from __future__ import annotations

from aema.catalog import CATALOG
from aema.errors import AemaError

LIMITATIONS = {
    "estimated": "Android-attributed estimate; no calibrated per-component uncertainty is available.",
    "proxy": "Reported activity or capacity proxy; no calibrated electrical uncertainty is available.",
}


def inspect_metrics(*, metric: str | None = None, source: str | None = None) -> list[dict]:
    """Describe numeric metrics without implying direct measurement."""
    entries = [
        entry
        for entry in CATALOG
        if entry.metric is not None
        and (metric is None or entry.metric == metric)
        and (source is None or entry.source == source)
    ]
    if not entries:
        raise AemaError("no catalogued metric matches the query")
    return [
        {
            "metric": entry.metric,
            "source": entry.source,
            "unit": entry.unit,
            "method": entry.method,
            "measurement_kind": entry.measurement_kind,
            "evidence_class": entry.evidence_class,
            "calibrated_uncertainty": None,
            "limitation": LIMITATIONS[entry.evidence_class],
        }
        for entry in entries
    ]
