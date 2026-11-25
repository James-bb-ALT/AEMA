"""Host-only training/export of device-bound Ridge forecasts from verified capture ZIPs."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import zipfile
from pathlib import Path

import numpy as np

from aema.errors import AemaError
from aema.forecast import CONTRACT, delta, features, read_snapshot, targets_for, validate_model


def fit(x, y, alpha):
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale < 1e-8] = 1
    z = np.c_[np.ones(len(x)), (x - mean) / scale]
    penalty = np.eye(z.shape[1]) * alpha
    penalty[0, 0] = 0
    return mean, scale, np.linalg.solve(z.T @ z + penalty, z.T @ y)


def predict(model, x):
    mean, scale, weights = model
    return np.maximum(0, np.c_[np.ones(len(x)), (x - mean) / scale] @ weights)


def train(captures, uids):
    targets = targets_for(uids)
    # Validate identifiers before doing I/O. Numbers are validated again at final export.
    if (
        not 1 <= len(uids) <= 12
        or len(set(uids)) != len(uids)
        or any(not 0 < u < 2147483648 for u in uids)
    ):
        raise ValueError("Choose 1-12 distinct positive UIDs")
    paths = sorted(Path(captures).glob("*.zip"))
    if len(paths) > 1024:
        raise ValueError("Limit training input to 1024 captures")
    snapshots, rejected = [], 0
    for path in paths:
        try:
            snapshots.append(read_snapshot(path, targets))
        except (
            OSError,
            ValueError,
            KeyError,
            TypeError,
            AemaError,
            zipfile.BadZipFile,
            UnicodeError,
        ):
            rejected += 1
            snapshots.append(None)  # Never bridge an invalid/missing intermediate capture.
    devices = {s["device_key"] for s in snapshots if s}
    if len(devices) != 1:
        raise ValueError("Expected verified captures from exactly one installation/build")
    history, samples = [], []
    for a, b in zip(snapshots[:-1], snapshots[1:], strict=True):
        try:
            row = delta(a, b)
        except (TypeError, ValueError):
            continue
        if len(history) >= 8:
            try:
                samples.append((features(history[-8:], row["start_ms"]), row["values"]))
            except ValueError:
                pass  # History older than 14 days cannot label this example.
        history.append(row)
    if len(samples) < 64:
        raise ValueError(f"Need at least 64 labeled examples after lags; found {len(samples)}")
    x = np.array([s[0] for s in samples])
    y = np.array([s[1] for s in samples])
    n = len(x)
    validation_start, test_start = n - 32, n - 16
    candidates = [
        (
            float(
                np.abs(
                    predict(
                        fit(x[:validation_start], y[:validation_start], a),
                        x[validation_start:test_start],
                    )
                    - y[validation_start:test_start]
                ).mean()
            ),
            a,
        )
        for a in (0.1, 1, 10, 100)
    ]
    score, alpha = min(candidates)
    # Withheld test is evaluated once; exported model does not fit its labels.
    trained = fit(x[:test_start], y[:test_start], alpha)
    test_prediction = predict(trained, x[test_start:])
    baseline = x[test_start:, len(targets) : 2 * len(targets)]
    report = dict(
        examples=n,
        rejected_captures=rejected,
        train=validation_start,
        validation=16,
        test=16,
        alpha=alpha,
        validation_mae=score,
        test_mae=float(np.abs(test_prediction - y[test_start:]).mean()),
        fourth_valid_window_test_mae=float(np.abs(baseline - y[test_start:]).mean()),
        scientific_validation=False,
        online_learning=False,
        target_semantics="future_BatteryStats_estimate_not_physical_ground_truth",
    )
    mean, scale, weights = trained
    model = dict(
        schema_version="aema_ridge_6h/1.0",
        model_version="1.0.0",
        feature_contract=CONTRACT,
        horizon_hours=6,
        synthetic=any(s["synthetic"] for s in snapshots if s),
        device_key=next(iter(devices)),
        targets=targets,
        x_mean=mean.astype(np.float32).tolist(),
        x_scale=scale.astype(np.float32).tolist(),
        weights=weights.astype(np.float32).tolist(),
        training=report,
    )
    validate_model(model)
    return model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captures", type=Path, required=True)
    parser.add_argument("--uids", type=int, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    model = train(args.captures, args.uids)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".forecast-", dir=args.output.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(model, stream, allow_nan=False, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, args.output)
    finally:
        Path(name).unlink(missing_ok=True)
    print(json.dumps(model["training"], indent=2))


if __name__ == "__main__":
    main()
