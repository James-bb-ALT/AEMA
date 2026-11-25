"""Create synthetic capture ZIPs, train the real host path and export native app fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from aema.forecast import SLOT_MS, delta, features, read_snapshot, targets_for
from aema.forecast_training import predict, train
from experiments.battery_validation import capture_for_report, make_report, series

BASE = datetime(
    2026, 1, 5, tzinfo=timezone.utc
)  # Monday, matching the original synthetic calendar.
UIDS = [10001, 1010042]


def create_capture(root, index, cumulative):
    report = "Start clock time: 2026-01-05-00-00-00\n" + make_report(cumulative[:4], cumulative[4:])
    path = capture_for_report(report, root / f"stage-{index:04}")
    with zipfile.ZipFile(path) as z:
        members = {name: z.read(name) for name in z.namelist()}
    battery = b"Current Battery Service state:\n  status: 3\n"
    end = BASE + timedelta(hours=6 * index)
    meta = json.loads(members["capture_manifest.json"])
    meta.update(
        synthetic=True,
        started_at_utc=(end - timedelta(seconds=2)).isoformat(),
        ended_at_utc=end.isoformat(),
        ended_elapsed_realtime_ms=120000 + index * SLOT_MS,
        forecast_boot_count="3",
        device=dict(serial="synthetic-fixture", build_fingerprint="fixture-build"),
        file_sha256={"battery_state.txt": hashlib.sha256(battery).hexdigest()},
    )
    members["capture_manifest.json"] = json.dumps(meta).encode()
    members["battery_state.txt"] = battery
    target = root / "captures" / f"aema_{index:04}.zip"
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in members.items():
            z.writestr(name, data)
    return target


def simulate(output):
    output.mkdir(parents=True, exist_ok=True)
    values = series(17, 112)[:, [0, 1, 2, 3, 4, 5]]
    cumulative = np.zeros(6)
    for index in range(96):
        create_capture(output, index, cumulative)
        cumulative += values[index]
    model = train(output / "captures", UIDS)
    assert model["synthetic"] is True
    (output / "synthetic-model.json").write_text(json.dumps(model, indent=2), encoding="utf-8")
    snapshots = [
        read_snapshot(p, targets_for(UIDS)) for p in sorted((output / "captures").glob("*.zip"))
    ]
    rows = [delta(a, b) for a, b in zip(snapshots[:-1], snapshots[1:], strict=True)]
    cases = []
    for index in range(79, 95):  # Exactly the 16 withheld target slots of this training run.
        origin = rows[index]["start_ms"]
        inputs = features(rows[index - 8 : index], origin)
        trained = tuple(np.array(model[k]) for k in ("x_mean", "x_scale", "weights"))
        expected = predict(trained, np.array([inputs]))[0].tolist()
        cases.append(
            dict(origin_ms=origin, features=inputs, shared_uids=[10001], expected=expected)
        )
    fixture = dict(synthetic=True, model=model, input=cases[0])
    (output / "forecast-demo.json").write_text(
        json.dumps(fixture, separators=(",", ":")), encoding="utf-8"
    )
    (output / "forecast-native-cases.json").write_text(
        json.dumps(dict(model=model, cases=cases)), encoding="utf-8"
    )
    result = dict(
        synthetic=True,
        capture_count=96,
        training=model["training"],
        native_cases=len(cases),
        model_bytes=(output / "synthetic-model.json").stat().st_size,
        weights_fp32_bytes=(3 * len(model["targets"]) + 6) * len(model["targets"]) * 4,
        scientific_validation=False,
        deployed_personal_model=False,
    )
    (output / "simulation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(simulate(args.output), indent=2))


if __name__ == "__main__":
    main()
