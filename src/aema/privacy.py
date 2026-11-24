"""Allowlisted, pseudonymous study exports. Raw datasets never leave through this path."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import tempfile
from pathlib import Path

from aema.dataset import load_dataset
from aema.errors import ExportError


def export_pseudonymous_study(dataset: str | Path, output: str | Path, key: bytes) -> Path:
    """Export numeric metrics and shared-UID relations using study-scoped HMAC tokens.

    Keys must be retained separately by the study owner. Matching is possible by
    recomputing tokens from known identities; no identity map is written to the export.
    Payloads, diagnostics, input hashes, file paths and device identifiers are omitted.
    """
    if len(key) < 32:
        raise ExportError("pseudonymization requires a key of at least 32 bytes")
    records, relations, _ = load_dataset(dataset)

    def token(kind: str, value: object) -> str | None:
        if value is None:
            return None
        return hmac.new(key, f"{kind}:{value}".encode(), hashlib.sha256).hexdigest()

    report = {
        "schema_version": "aema-pseudonymous-study-1",
        "privacy": "pseudonymous; numeric patterns may still identify a participant",
        "records": [
            {
                "entity": record.entity,
                "metric": record.metric,
                "value": record.value,
                "unit": record.unit.value if record.unit else None,
                "measurement_kind": record.measurement_kind.value,
                "source": record.source.value,
                "method": record.method,
                "uid_token": token("uid", record.uid),
                "package_token": token("package", record.package_name),
            }
            for record in records
        ],
        "relations": [
            {
                "uid_token": token("uid", relation.uid),
                "package_token": token("package", relation.package_name),
            }
            for relation in relations
        ],
    }
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".study-", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
        # Exclusive creation: never replace another study export.
        os.link(temporary, target)
    except OSError as exc:
        raise ExportError(f"cannot publish pseudonymous study: {exc}") from exc
    finally:
        Path(temporary).unlink(missing_ok=True)
    return target
