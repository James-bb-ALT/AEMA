"""Chronological Ridge/MLP comparison on synthetic data, never a personal forecast.

Run from the repository root: python -m experiments.ultralight_validation --output dist/ultralight
Only NumPy and the existing project dependencies are required. No model downloads.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import time
from pathlib import Path

import numpy as np

from experiments.battery_validation import SEEDS, feature_row, fit_ridge, metrics, predict, series

EXPERIMENT_VERSION = "1.0.0"
FEATURES = [
    f"{lag}_{target}"
    for lag in ("previous_slot", "previous_day", "mean_last_8_slots")
    for target in ("screen", "cpu", "wifi", "mobile_radio", "uid_1", "uid_2", "uid_3")
] + ["slot_sine", "slot_cosine", "weekend"]
TARGETS = ["screen", "cpu", "wifi", "mobile_radio", "uid_1", "uid_2", "uid_3"]
# Declared before observing test results. Every candidate uses the same input and output axes.
MLP_GRID = (((16, 8), 0.001), ((16, 8), 0.01), ((32, 16), 0.001), ((32, 16), 0.01))
MAX_EPOCHS = 600


def windows(values):
    """Origin t predicts slot [t,t+1), with values through slot t-1 observable."""
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != 7 or len(values) < 281:
        raise ValueError("Expected at least 281 six-hour slots and seven nonnegative targets")
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Invalid synthetic target values")
    origins = np.arange(8, len(values))
    x = np.array([feature_row(values, int(t)) for t in origins])
    masks = (
        origins < 224,
        (origins >= 224) & (origins < 280),
        origins >= 280,
    )
    return origins, x, values[origins], masks


def make_series(seed, regime):
    values = series(seed, 112)
    if regime == "linear_routine_shift":
        return values
    if regime != "nonlinear_routine_shift":
        raise ValueError("Unknown regime")
    # A second, explicitly invented mechanism; not a fit to a real phone.
    # Nonlinear load is deterministic from the base process, without modifying its dates.
    load = np.maximum(values / np.array([280, 230, 140, 130, 180, 200, 140]), 0)
    return values + 35 * load**2 + 15 * np.maximum(load - 0.7, 0)


def normalize(a):
    mean, scale = a.mean(axis=0), a.std(axis=0)
    scale[scale < 1e-8] = 1
    return mean, scale


def forward(weights, x):
    activations = [x]
    for index, (w, b) in enumerate(weights):
        z = activations[-1] @ w + b
        activations.append(np.maximum(z, 0) if index < len(weights) - 1 else z)
    return activations


def mlp_predict(model, x):
    z = (x - model["x_mean"]) / model["x_scale"]
    output = forward(model["layers"], z)[-1]
    return np.maximum(0, output * model["y_scale"] + model["y_mean"])


def fit_mlp(x, y, hidden, l2, seed, epochs=MAX_EPOCHS, validation=None):
    """Full-batch Adam, train-only normalization, optional chronological early stopping.

    Epoch selection uses the supplied validation partition, never an internal random split.
    Final refits use the selected epoch count and do not access held-out test labels.
    """
    xm, xs = normalize(x)
    ym, ys = normalize(y)
    z, target = (x - xm) / xs, (y - ym) / ys
    rng = np.random.default_rng(seed)
    dims = (x.shape[1], *hidden, y.shape[1])
    layers = [
        [rng.normal(0, np.sqrt(2 / a), (a, b)), np.zeros(b)]
        for a, b in zip(dims[:-1], dims[1:], strict=True)
    ]
    parameters = [p for layer in layers for p in layer]
    first = [np.zeros_like(p) for p in parameters]
    second = [np.zeros_like(p) for p in parameters]
    model = dict(x_mean=xm, x_scale=xs, y_mean=ym, y_scale=ys, layers=layers)
    best, best_score, best_epoch, stale = None, float("inf"), 0, 0
    for epoch in range(1, epochs + 1):
        activations = forward(layers, z)
        gradient = 2 * (activations[-1] - target) / target.size
        gradients = []
        for index in reversed(range(len(layers))):
            w, _ = layers[index]
            dw = activations[index].T @ gradient + 2 * l2 * w / len(x)
            db = gradient.sum(axis=0)
            gradients[:0] = [dw, db]
            gradient = gradient @ w.T
            if index:
                gradient *= activations[index] > 0
        for p, grad, m, v in zip(parameters, gradients, first, second, strict=True):
            m *= 0.9
            m += 0.1 * grad
            v *= 0.999
            v += 0.001 * grad**2
            p -= 0.003 * (m / (1 - 0.9**epoch)) / (np.sqrt(v / (1 - 0.999**epoch)) + 1e-8)
        if not all(np.isfinite(p).all() for p in parameters):
            raise ValueError("Nonfinite training parameters")
        if validation is not None:
            score = float(np.abs(mlp_predict(model, validation[0]) - validation[1]).mean())
            if score < best_score:
                best_score, best_epoch, stale = score, epoch, 0
                best = [[p.copy() for p in layer] for layer in layers]
            else:
                stale += 1
            if stale >= 60:
                break
    if validation is not None:
        model["layers"] = best
    return model, dict(
        epochs=best_epoch if validation is not None else epochs,
        validation_mae=best_score if validation is not None else None,
    )


def portable_predict(document, row):
    """Scalar-list reference for exported dense/ReLU weights; no NumPy inference runtime.

    This is an export parity reference on the host, not a tested Android implementation.
    """
    current = [
        (v - m) / s for v, m, s in zip(row, document["x_mean"], document["x_scale"], strict=True)
    ]
    for index, layer in enumerate(document["layers"]):
        w, b = layer["weights"], layer["bias"]
        current = [
            sum(v * w[i][j] for i, v in enumerate(current)) + bias for j, bias in enumerate(b)
        ]
        if index < len(document["layers"]) - 1:
            current = [max(0, v) for v in current]
    return [
        max(0, v * s + m)
        for v, s, m in zip(current, document["y_scale"], document["y_mean"], strict=True)
    ]


def export_ridge(model, path):
    mean, scale, weights = model
    document = dict(
        schema_version="1.0",
        experiment_version=EXPERIMENT_VERSION,
        synthetic=True,
        deployment_status="research_only_not_installed",
        feature_names=FEATURES,
        target_names=TARGETS,
        x_mean=mean.astype(np.float32).tolist(),
        x_scale=scale.astype(np.float32).tolist(),
        weights=weights.astype(np.float32).tolist(),
    )
    path.write_text(json.dumps(document, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    return dict(
        file=path.name,
        parameters=weights.size,
        raw_fp32_weight_bytes=weights.size * 4,
        raw_fp32_preprocessing_bytes=(mean.size + scale.size) * 4,
        json_bytes=path.stat().st_size,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def portable_ridge(document, row):
    z = [1.0] + [
        (v - m) / s for v, m, s in zip(row, document["x_mean"], document["x_scale"], strict=True)
    ]
    return [
        max(0, sum(v * w[j] for v, w in zip(z, document["weights"], strict=True)))
        for j in range(len(document["target_names"]))
    ]


def export_mlp(model, path):
    # float32 values encoded in JSON: portable representation, not a binary float32 file.
    def array(a):
        return np.asarray(a, dtype=np.float32).tolist()

    document = dict(
        schema_version="1.0",
        experiment_version=EXPERIMENT_VERSION,
        synthetic=True,
        deployment_status="research_only_not_installed",
        feature_names=FEATURES,
        target_names=TARGETS,
        unit="estimated_mah_per_synthetic_6h_slot",
        activation="relu_hidden_linear_output_nonnegative_clamp",
        **{k: array(model[k]) for k in ("x_mean", "x_scale", "y_mean", "y_scale")},
        layers=[dict(weights=array(w), bias=array(b)) for w, b in model["layers"]],
    )
    path.write_text(json.dumps(document, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    parameters = sum(w.size + b.size for w, b in model["layers"])
    preprocessing = sum(model[k].size for k in ("x_mean", "x_scale", "y_mean", "y_scale"))
    return dict(
        parameters=parameters,
        raw_fp32_weight_bytes=parameters * 4,
        raw_fp32_preprocessing_bytes=preprocessing * 4,
        json_bytes=path.stat().st_size,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def benchmark(call, repetitions=500):
    for _ in range(20):
        call()
    timings = []
    for _ in range(repetitions):
        start = time.perf_counter_ns()
        call()
        timings.append((time.perf_counter_ns() - start) / 1e6)
    return dict(
        repetitions=repetitions,
        p50_ms=float(np.percentile(timings, 50)),
        p95_ms=float(np.percentile(timings, 95)),
        scope="host_warm_single_7_output_row",
    )


def run_case(seed, regime, output):
    values = make_series(seed, regime)
    origins, x, y, (train, valid, test) = windows(values)
    ridge_selection_start = time.perf_counter()
    ridge_scores = [
        (float(np.abs(predict(fit_ridge(x[train], y[train], a), x[valid]) - y[valid]).mean()), a)
        for a in (0.1, 1, 10, 100)
    ]
    ridge_score, alpha = min(ridge_scores)
    ridge_selection_seconds = time.perf_counter() - ridge_selection_start
    candidates = []
    start = time.perf_counter()
    for hidden, l2 in MLP_GRID:
        _, selection = fit_mlp(
            x[train], y[train], hidden, l2, seed, validation=(x[valid], y[valid])
        )
        candidates.append(dict(hidden=list(hidden), l2=l2, **selection))
    selected = min(candidates, key=lambda c: c["validation_mae"])
    before_test = train | valid
    model, _ = fit_mlp(
        x[before_test],
        y[before_test],
        selected["hidden"],
        selected["l2"],
        seed,
        epochs=selected["epochs"],
    )
    mlp_fit_seconds = time.perf_counter() - start
    ridge_start = time.perf_counter()
    ridge = fit_ridge(x[before_test], y[before_test], alpha)
    ridge_fit_seconds = time.perf_counter() - ridge_start
    predictions = dict(
        previous_day=values[origins[test] - 4],
        ridge=predict(ridge, x[test]),
        mlp=mlp_predict(model, x[test]),
    )
    by_slot = {s: y[before_test & (origins % 4 == s)].mean(axis=0) for s in range(4)}
    predictions["slot_mean"] = np.array([by_slot[int(t % 4)] for t in origins[test]])
    # Selection is frozen on validation. Test metrics do not choose a model.
    selected_model = "mlp" if selected["validation_mae"] < ridge_score else "ridge"
    predictions["validation_selected"] = predictions[selected_model]
    name = f"{regime}-{seed}.json"
    artifact = export_mlp(model, output / name)
    restored = json.loads((output / name).read_text(encoding="utf-8"))
    ridge_artifact = export_ridge(ridge, output / f"ridge-{name}")
    ridge_restored = json.loads((output / ridge_artifact["file"]).read_text(encoding="utf-8"))
    ridge_portable = np.array([portable_ridge(ridge_restored, row.tolist()) for row in x[test]])
    ridge_error = float(np.max(np.abs(ridge_portable - predictions["ridge"])))
    portable = np.array([portable_predict(restored, row.tolist()) for row in x[test]])
    error = float(np.max(np.abs(portable - predictions["mlp"])))
    if max(error, ridge_error) >= 0.001:
        raise AssertionError(f"FP32 export parity exceeded 0.001 mAh: {error}, {ridge_error}")
    # Corrupt future labels: attributes at the cutoff must remain unchanged.
    changed = values.copy()
    changed[280:] += 100000
    assert np.array_equal(feature_row(values, 280), feature_row(changed, 280))
    # Inputs to fitting/selection must remain identical when test labels are changed.
    _, changed_x, changed_y, _ = windows(changed)
    assert np.array_equal(x[train | valid], changed_x[train | valid])
    assert np.array_equal(y[train | valid], changed_y[train | valid])
    one = x[test][:1]
    scalar_row = one[0].tolist()
    return dict(
        seed=seed,
        regime=regime,
        windows=dict(train=int(train.sum()), validation=int(valid.sum()), test=int(test.sum())),
        feature_count=x.shape[1],
        target_count=y.shape[1],
        alpha=alpha,
        ridge_validation_mae=ridge_score,
        mlp_candidates=candidates,
        selected_mlp=selected,
        validation_selected_model=selected_model,
        metrics={n: metrics(y[test], p) for n, p in predictions.items()},
        artifact=dict(file=name, **artifact),
        ridge_artifact=ridge_artifact,
        export_max_abs_error_mah=error,
        ridge_export_max_abs_error_mah=ridge_error,
        timings=dict(
            mlp_grid_and_refit_seconds=mlp_fit_seconds,
            ridge_refit_seconds=ridge_fit_seconds,
            ridge_grid_and_refit_seconds=ridge_selection_seconds + ridge_fit_seconds,
            ridge_numpy=benchmark(lambda: predict(ridge, one)),
            mlp_numpy=benchmark(lambda: mlp_predict(model, one)),
            mlp_portable=benchmark(lambda: portable_predict(restored, scalar_row)),
            ridge_portable=benchmark(lambda: portable_ridge(ridge_restored, scalar_row)),
        ),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    for regime in ("linear_routine_shift", "nonlinear_routine_shift"):
        for seed in SEEDS:
            row = run_case(seed, regime, args.output)
            results.append(row)
            print(
                json.dumps(
                    dict(
                        seed=seed,
                        regime=regime,
                        selected=row["validation_selected_model"],
                        mae={n: m["total_mae_mah"] for n, m in row["metrics"].items()},
                    )
                ),
                flush=True,
            )
    summary = {}
    for regime in {r["regime"] for r in results}:
        rows = [r for r in results if r["regime"] == regime]
        summary[regime] = {
            name: {
                key: float(np.mean([r["metrics"][name][key] for r in rows]))
                for key in rows[0]["metrics"][name]
            }
            for name in rows[0]["metrics"]
        }
    report = dict(
        experiment="ridge-vs-tiny-mlp",
        experiment_version=EXPERIMENT_VERSION,
        synthetic=True,
        no_real_accuracy_claim=True,
        python=platform.python_version(),
        numpy=np.__version__,
        machine=platform.machine(),
        processor=platform.processor(),
        thread_environment={
            k: os.environ.get(k) for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS")
        },
        horizon_hours=6,
        features=FEATURES,
        targets=TARGETS,
        selection_metric="validation_mean_absolute_error_across_7_outputs",
        checks=dict(
            future_features="pass",
            train_validation_future_label_isolation="pass",
            float32_export="pass",
        ),
        results=results,
        summary=summary,
        limits=[
            "No real-phone labels",
            "No Android inference or energy measurement",
            "No int8 calibration",
            "Synthetic identities are not real applications",
            "Host timings exclude data collection and cold loading",
        ],
    )
    (args.output / "comparison.json").write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
