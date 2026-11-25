"""Verified six-hour estimate windows and Ridge feature contract, without an LLM.

This module prepares data only. Android evaluates Ridge with its native Java engine.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from aema.errors import AemaError
from aema.files import sha256_file
from aema.llm import _read, _verified_capture

CONTRACT = "valid_lag1_lag4_mean8_calendar_age_utc_v1"
SLOT_MS = 6 * 3600 * 1000
COMPONENTS = ("screen", "cpu", "wifi", "mobile_radio")
MAX_MODEL_BYTES = 256 * 1024


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("UTC timestamp required")
    return int(parsed.timestamp() * 1000)


def targets_for(uids):
    return [dict(id=f"component:{c}", axis="component") for c in COMPONENTS] + [
        dict(id=f"uid:{uid}", axis="uid") for uid in uids
    ]


def validate_model(model):
    """Match the bounded native contract; a hash provides integrity, not authenticity."""
    if (
        model.get("schema_version") != "aema_ridge_6h/1.0"
        or model.get("feature_contract") != CONTRACT
    ):
        raise ValueError("Unsupported forecast model")
    if type(model.get("synthetic")) is not bool or model.get("horizon_hours") != 6:
        raise ValueError("Missing model provenance or horizon")
    if not isinstance(model.get("device_key"), str) or not re.fullmatch(
        r"[a-f0-9]{64}", model["device_key"]
    ):
        raise ValueError("Missing device binding")
    targets = model["targets"]
    if not isinstance(targets, list) or not 5 <= len(targets) <= 16:
        raise ValueError("Expected four components and 1-12 UIDs")
    if targets[:4] != targets_for([]):
        raise ValueError("Unsupported component order")
    ids = [t["id"] for t in targets]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate target")
    for target in targets[4:]:
        if target.get("axis") != "uid" or not re.fullmatch(r"uid:[1-9][0-9]{0,9}", target["id"]):
            raise ValueError("Invalid UID target")
        if int(target["id"][4:]) > 2147483647:
            raise ValueError("UID exceeds contract")
    width = len(targets) * 3 + 5
    for key in ("x_mean", "x_scale"):
        if len(model[key]) != width:
            raise ValueError("Invalid normalizer dimensions")
        for value in model[key]:
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError("Nonfinite normalizer")
            if key == "x_scale" and value <= 0:
                raise ValueError("Scale must be positive")
    if len(model["weights"]) != width + 1:
        raise ValueError("Invalid Ridge dimensions")
    for row in model["weights"]:
        if len(row) != len(targets) or any(
            type(v) not in (float, int) or not math.isfinite(v) for v in row
        ):
            raise ValueError("Invalid Ridge weights")
    return model


def read_snapshot(path, targets):
    """Reject snapshots without independently observable reset/boot/time provenance."""
    metadata, records, relations = _verified_capture(Path(path))
    if type(metadata.get("synthetic", False)) is not bool:
        raise ValueError("Invalid capture provenance flag")
    with zipfile.ZipFile(path) as archive:
        text = archive.read("stats.txt").decode("utf-8")
        battery = _read(archive, "battery_state.txt", 256 * 1024)
    if (
        hashlib.sha256(battery).hexdigest().lower()
        != metadata["file_sha256"]["battery_state.txt"].lower()
    ):
        raise ValueError("Battery state hash mismatch")
    epoch = re.findall(r"^\s*Start clock time:\s*(\d{4}-\d\d-\d\d-\d\d-\d\d-\d\d)\s*$", text, re.M)
    if len(epoch) != 1:
        raise ValueError("BatteryStats reset epoch unavailable")
    # Require the new, explicitly collected boot counter; older captures remain readable elsewhere.
    boot = metadata["forecast_boot_count"]
    if not isinstance(boot, str) or not re.fullmatch(r"[0-9]+", boot):
        raise ValueError("Boot counter unavailable")
    device = metadata["device"]
    device_key = hashlib.sha256(
        (device["serial"] + "\n" + device["build_fingerprint"]).encode()
    ).hexdigest()
    end = timestamp(metadata["ended_at_utc"])
    start = timestamp(metadata["started_at_utc"])
    elapsed = metadata["ended_elapsed_realtime_ms"]
    if type(elapsed) is not int or not 0 < end - start <= 120000 or elapsed <= 0:
        raise ValueError("Capture timing unavailable or capture exceeds two minutes")
    # Endpoint charging state is a screen, not proof that no charging occurred inside the interval.
    statuses = re.findall(rb"^\s*status:\s*([0-9]+)\s*$", battery, re.M)
    if len(statuses) != 1 or statuses[0] not in (b"3", b"4"):
        raise ValueError("Capture endpoint is charging, full or unknown")
    estimates = {}
    for record in records:
        if record.source.value != "power" or record.unit.value != "mAh":
            continue
        name = None
        if record.uid is None:
            for c in COMPONENTS:
                if record.metric == f"{c}_estimated_charge_mah":
                    name = f"component:{c}"
        elif record.metric == "total_estimated_charge_mah":
            name = f"uid:{record.uid}"
        if name in {t["id"] for t in targets}:
            if name in estimates or not math.isfinite(record.value) or record.value < 0:
                raise ValueError("Duplicate or negative cumulative estimate")
            estimates[name] = record.value
    if set(estimates) != {t["id"] for t in targets}:
        raise ValueError("Modeled component/UID missing; absence is not zero")
    packages = {}
    for relation in relations:
        packages.setdefault(relation.uid, set()).add(relation.package_name)
    return dict(
        end_ms=end,
        elapsed_ms=elapsed,
        device_key=device_key,
        epoch=epoch[0],
        boot=boot,
        synthetic=metadata.get("synthetic", False),
        values=[estimates[t["id"]] for t in targets],
        shared_uids=[uid for uid, names in packages.items() if len(names) > 1],
    )


def delta(previous, current):
    duration = current["end_ms"] - previous["end_ms"]
    monotonic = current["elapsed_ms"] - previous["elapsed_ms"]
    if any(previous[k] != current[k] for k in ("device_key", "epoch", "boot")):
        raise ValueError("Device, reset epoch or boot changed")
    if not SLOT_MS * 0.95 <= duration <= SLOT_MS * 1.05 or abs(duration - monotonic) > 30000:
        raise ValueError("Six-hour cadence or clock continuity invalid")
    values = [b - a for a, b in zip(previous["values"], current["values"], strict=True)]
    if any(v < 0 or not math.isfinite(v) for v in values):
        raise ValueError("Cumulative counter decreased")
    return dict(
        start_ms=previous["end_ms"],
        end_ms=current["end_ms"],
        values=[v * SLOT_MS / duration for v in values],
    )


def features(rows, origin_ms):
    if len(rows) != 8:
        raise ValueError("Eight valid six-hour windows required")
    if (
        any(rows[i]["end_ms"] > rows[i + 1]["start_ms"] for i in range(7))
        or rows[-1]["end_ms"] > origin_ms
        or origin_ms - rows[0]["start_ms"] > 14 * 86400000
    ):
        raise ValueError("Discontinuous window history")
    when = datetime.fromtimestamp(origin_ms / 1000, timezone.utc)
    phase = 2 * math.pi * (when.hour * 3600 + when.minute * 60 + when.second) / 86400
    n = len(rows[-1]["values"])
    return (
        rows[-1]["values"]
        + rows[-4]["values"]
        + [sum(row["values"][i] for row in rows) / 8 for i in range(n)]
        + [
            math.sin(phase),
            math.cos(phase),
            int(when.weekday() >= 5),
            (origin_ms - rows[-1]["end_ms"]) / 3600000,
            (origin_ms - rows[0]["start_ms"]) / 3600000,
        ]
    )


def prepare_forecast(captures_root, model_json, now_ms):
    """Bridge returns a feature vector or an explicit abstention; no weights are executed here."""
    try:
        if len(model_json.encode()) > MAX_MODEL_BYTES:
            raise ValueError("Model exceeds size limit")
        model = validate_model(json.loads(model_json))
        if model["synthetic"]:
            raise ValueError("Synthetic models cannot read personal captures")
        paths = sorted(Path(captures_root).glob("*.zip"))[-64:]
        if len(paths) < 9:
            return json.dumps(dict(status="abstained", reason="NEED_VALID_HISTORY"))
        snapshots = []
        for path in paths:
            try:
                snapshot = read_snapshot(path, model["targets"])
                if snapshot["synthetic"]:
                    raise ValueError("Synthetic captures cannot produce a personal forecast")
                snapshots.append(snapshot)
            except (
                OSError,
                ValueError,
                KeyError,
                TypeError,
                AemaError,
                zipfile.BadZipFile,
                UnicodeError,
            ):
                snapshots.append(None)
        if snapshots[-1] is None or snapshots[-2] is None:
            raise ValueError("Latest capture interval is invalid")
        if snapshots[-1]["device_key"] != model["device_key"]:
            return json.dumps(dict(status="abstained", reason="DEVICE_MISMATCH"))
        origin = snapshots[-1]["end_ms"]
        if not 0 <= now_ms - origin <= 30 * 60 * 1000:
            return json.dumps(dict(status="abstained", reason="CAPTURE_STALE_OR_CLOCK_CHANGED"))
        # Each delta must be valid on its own. Never span a failed capture/reset.
        # Old valid windows may remain useful after a rejected interval; ages are explicit features.
        delta(snapshots[-2], snapshots[-1])
        rows, used = [], set()
        for index in reversed(range(1, len(snapshots))):
            a, b = snapshots[index - 1], snapshots[index]
            try:
                row = delta(a, b)
                if (
                    b["device_key"] != model["device_key"]
                    or origin - row["start_ms"] > 14 * 86400000
                ):
                    continue
                rows.append(row)
                used.update((index - 1, index))
                if len(rows) == 8:
                    break
            except (TypeError, ValueError):
                continue
        if len(rows) < 8:
            return json.dumps(dict(status="abstained", reason="NEED_VALID_HISTORY"))
        rows.reverse()
        return json.dumps(
            dict(
                status="ready",
                origin_ms=origin,
                features=features(rows, origin),
                shared_uids=snapshots[-1]["shared_uids"],
                history_sha256=[sha256_file(paths[i]).lower() for i in sorted(used)],
                history_span_hours=(origin - rows[0]["start_ms"]) / 3600000,
            ),
            allow_nan=False,
        )
    except (OSError, ValueError, KeyError, TypeError, AemaError, zipfile.BadZipFile, UnicodeError):
        return json.dumps(dict(status="abstained", reason="HISTORY_INVALID_OR_UNSUPPORTED"))
