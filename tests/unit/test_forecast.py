from __future__ import annotations

import hashlib
import json
import zipfile

import numpy as np
import pytest

import aema.forecast as forecast
import aema.forecast_training as training
from experiments.forecast_simulation import BASE, UIDS, create_capture


def sample(index):
    return dict(
        end_ms=int(BASE.timestamp() * 1000) + index * forecast.SLOT_MS,
        elapsed_ms=120000 + index * forecast.SLOT_MS,
        device_key="a" * 64,
        epoch="epoch-1",
        boot="3",
        synthetic=False,
        values=[index * (i + 1) for i in range(6)],
        shared_uids=[10001],
    )


def model():
    return dict(
        schema_version="aema_ridge_6h/1.0",
        feature_contract=forecast.CONTRACT,
        horizon_hours=6,
        synthetic=False,
        device_key="a" * 64,
        targets=forecast.targets_for(UIDS),
        x_mean=[0.0] * 23,
        x_scale=[1.0] * 23,
        weights=[[0.0] * 6 for _ in range(24)],
    )


@pytest.fixture
def capture(tmp_path):
    return create_capture(tmp_path, 1, np.array([20, 30, 40, 50, 60, 70]))


def replace_member(path, name, data):
    with zipfile.ZipFile(path) as z:
        members = {n: z.read(n) for n in z.namelist()}
    members[name] = data
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n, value in members.items():
            z.writestr(n, value)


def test_real_parser_snapshot_provenance_and_shared_uid(capture):
    snap = forecast.read_snapshot(capture, forecast.targets_for(UIDS))
    assert snap["values"] == [20, 30, 40, 50, 60, 70]
    assert snap["shared_uids"] == [10001]
    assert snap["synthetic"] is True
    assert snap["epoch"] == "2026-01-05-00-00-00"


@pytest.mark.parametrize(
    "change",
    [
        {"forecast_boot_count": None},
        {"forecast_boot_count": "unknown"},
        {"ended_elapsed_realtime_ms": -1},
        {"started_at_utc": "2026-01-01T00:00:00Z"},
        {"started_at_utc": "2026-01-05T06:00:00Z"},
    ],
)
def test_bad_snapshot_metadata_rejected(capture, change):
    with zipfile.ZipFile(capture) as z:
        meta = json.loads(z.read("capture_manifest.json"))
    meta.update(change)
    replace_member(capture, "capture_manifest.json", json.dumps(meta).encode())
    with pytest.raises((ValueError, KeyError)):
        forecast.read_snapshot(capture, forecast.targets_for(UIDS))


@pytest.mark.parametrize(
    "battery,valid_hash",
    [(b"status: 2\n", True), (b"status: 5\n", True), (b"no state", True), (b"status: 3\n", False)],
)
def test_charging_unknown_state_and_hash_mismatch_rejected(capture, battery, valid_hash):
    with zipfile.ZipFile(capture) as z:
        meta = json.loads(z.read("capture_manifest.json"))
    meta["file_sha256"]["battery_state.txt"] = (
        hashlib.sha256(battery).hexdigest() if valid_hash else "bad"
    )
    replace_member(capture, "capture_manifest.json", json.dumps(meta).encode())
    replace_member(capture, "battery_state.txt", battery)
    with pytest.raises(ValueError):
        forecast.read_snapshot(capture, forecast.targets_for(UIDS))


def test_missing_target_never_becomes_zero(capture):
    with pytest.raises(ValueError, match="missing"):
        forecast.read_snapshot(capture, forecast.targets_for([99999]))


@pytest.mark.parametrize(
    "change",
    [
        dict(epoch="reset"),
        dict(boot="4"),
        dict(device_key="b" * 64),
        dict(end_ms=1),
        dict(elapsed_ms=1),
        dict(values=[-1] * 6),
    ],
)
def test_delta_rejects_resets_boots_clock_jumps_and_negative_counters(change):
    previous, current = sample(0), sample(1)
    current.update(change)
    with pytest.raises(ValueError):
        forecast.delta(previous, current)


def test_features_observe_only_history_with_utc_calendar():
    snapshots = [sample(i) for i in range(9)]
    rows = [forecast.delta(a, b) for a, b in zip(snapshots[:-1], snapshots[1:], strict=True)]
    origin = snapshots[-1]["end_ms"]
    values = forecast.features(rows, origin)
    assert values[:18] == [1, 2, 3, 4, 5, 6] * 3
    assert values[18:] == pytest.approx([0, 1, 0, 0, 48], abs=1e-12)
    with pytest.raises(ValueError):
        forecast.features(rows[:7], origin)
    rows[3]["start_ms"] -= 1
    with pytest.raises(ValueError):
        forecast.features(rows, origin)
    with pytest.raises(ValueError):
        forecast.timestamp("2026-01-01T00:00:00")


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", "bad"),
        ("feature_contract", "bad"),
        ("synthetic", "false"),
        ("horizon_hours", 12),
        ("device_key", "device-name"),
        ("targets", []),
        ("x_mean", []),
        ("x_scale", [0.0] * 23),
        ("x_mean", [float("nan")] * 23),
        ("weights", []),
        ("weights", [[0.0] * 5 for _ in range(24)]),
        ("weights", [[True] * 6 for _ in range(24)]),
    ],
)
def test_invalid_model_contract_is_rejected(field, value):
    data = model()
    data[field] = value
    with pytest.raises(ValueError):
        forecast.validate_model(data)


@pytest.mark.parametrize("ids", [[10001, 10001], [2147483648], [0]])
def test_invalid_target_identity_is_rejected(ids):
    data = model()
    data["targets"] = forecast.targets_for(ids)
    with pytest.raises(ValueError):
        forecast.validate_model(data)


def test_prepare_requires_bound_model_valid_recent_real_history(tmp_path, monkeypatch):
    text = json.dumps(model())
    assert (
        json.loads(forecast.prepare_forecast(tmp_path, text, 0))["reason"] == "NEED_VALID_HISTORY"
    )
    for i in range(9):
        (tmp_path / f"aema_{i:04}.zip").write_bytes(b"fixture-only mock input")
    snapshots = {f"aema_{i:04}.zip": sample(i) for i in range(9)}
    monkeypatch.setattr(forecast, "read_snapshot", lambda path, _: snapshots[path.name])
    now = sample(8)["end_ms"]
    ready = json.loads(forecast.prepare_forecast(tmp_path, text, now))
    assert ready["status"] == "ready"
    assert len(ready["features"]) == 23
    assert ready["shared_uids"] == [10001]
    assert (
        json.loads(forecast.prepare_forecast(tmp_path, text, now + 31 * 60000))["reason"]
        == "CAPTURE_STALE_OR_CLOCK_CHANGED"
    )
    altered = model()
    altered["device_key"] = "b" * 64
    assert (
        json.loads(forecast.prepare_forecast(tmp_path, json.dumps(altered), now))["reason"]
        == "DEVICE_MISMATCH"
    )
    altered = model()
    altered["synthetic"] = True
    assert (
        json.loads(forecast.prepare_forecast(tmp_path, json.dumps(altered), now))["status"]
        == "abstained"
    )
    snapshots["aema_0008.zip"]["synthetic"] = True
    assert json.loads(forecast.prepare_forecast(tmp_path, text, now))["status"] == "abstained"
    assert (
        json.loads(forecast.prepare_forecast(tmp_path, "x" * (forecast.MAX_MODEL_BYTES + 1), now))[
            "status"
        ]
        == "abstained"
    )


def training_paths(tmp_path, monkeypatch, count=83):
    for i in range(count):
        (tmp_path / f"aema_{i:04}.zip").touch()
    snapshots = {f"aema_{i:04}.zip": sample(i) for i in range(count)}

    def reader(path, _):
        item = snapshots[path.name]
        if item is None:
            raise ValueError("Fixture models a rejected capture")
        return item

    monkeypatch.setattr(training, "read_snapshot", reader)
    return snapshots


def test_host_training_cannot_fit_heldout_future_and_preserves_device_binding(
    tmp_path, monkeypatch
):
    snapshots = training_paths(tmp_path, monkeypatch)
    first = training.train(tmp_path, UIDS)
    assert first["training"]["examples"] == 74
    assert first["training"]["train"] == 42
    assert first["training"]["test"] == first["training"]["validation"] == 16
    assert first["device_key"] == "a" * 64
    for i in range(67, 83):
        snapshots[f"aema_{i:04}.zip"]["values"] = [
            v + 10000 * (i - 66) for v in sample(i)["values"]
        ]
    mutated = training.train(tmp_path, UIDS)
    for key in ("x_mean", "x_scale", "weights"):
        assert first[key] == mutated[key]
    assert first["training"]["test_mae"] != mutated["training"]["test_mae"]


def test_training_skips_invalid_pairs_preserves_history_and_requires_enough_labels(
    tmp_path, monkeypatch
):
    snapshots = training_paths(tmp_path, monkeypatch)
    snapshots["aema_0040.zip"] = None
    interrupted = training.train(tmp_path, UIDS)
    assert interrupted["training"]["examples"] == 72
    assert interrupted["training"]["rejected_captures"] == 1
    for i in range(41, 56):
        snapshots[f"aema_{i:04}.zip"] = None
    with pytest.raises(ValueError, match="at least 64"):
        training.train(tmp_path, UIDS)
    with pytest.raises(ValueError):
        training.train(tmp_path, [0])


def test_training_cli_writes_atomic_valid_model(tmp_path, monkeypatch, capsys):
    captures = tmp_path / "captures"
    captures.mkdir()
    training_paths(captures, monkeypatch)
    output = tmp_path / "model.json"
    monkeypatch.setattr(
        "sys.argv",
        ["train", "--captures", str(captures), "--uids", *map(str, UIDS), "--output", str(output)],
    )
    training.main()
    forecast.validate_model(json.loads(output.read_text()))
    assert "scientific_validation" in capsys.readouterr().out
    assert not list(tmp_path.glob(".forecast-*"))


def test_history_allows_gaps_with_explicit_ages_but_never_future_or_old_history():
    rows = [forecast.delta(sample(i), sample(i + 1)) for i in (0, 1, 2, 5, 6, 7, 8, 9)]
    origin = sample(11)["end_ms"]
    values = forecast.features(rows, origin)
    assert values[-2:] == [6, 66]
    with pytest.raises(ValueError):
        forecast.features(rows, sample(9)["end_ms"])
    with pytest.raises(ValueError):
        forecast.features(rows, sample(57)["end_ms"])


def test_prepare_recovers_valid_windows_after_reset_without_bridging(tmp_path, monkeypatch):
    snapshots = {}
    for i in range(12):
        name = f"aema_{i:04}.zip"
        (tmp_path / name).write_bytes(name.encode())
        snapshots[name] = sample(i)
        if i >= 5:
            snapshots[name]["epoch"] = "after-reset"
    monkeypatch.setattr(forecast, "read_snapshot", lambda path, _: snapshots[path.name])
    ready = json.loads(
        forecast.prepare_forecast(tmp_path, json.dumps(model()), sample(11)["end_ms"])
    )
    assert ready["status"] == "ready"
    assert ready["history_span_hours"] == 54
    assert ready["features"][:6] == [1, 2, 3, 4, 5, 6]
    assert len(ready["history_sha256"]) == 10
