"""Reproducible synthetic feasibility experiment; no product model is trained here."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import tempfile
import time
import zipfile
from pathlib import Path

import numpy as np

from aema.exporters import export_canonical_result
from aema.llm import prepare_analysis
from aema.models import PipelineInputs
from aema.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parents[1]
SEEDS = (17, 42, 103, 251, 907)
COMPONENTS = ("screen", "cpu", "wifi", "mobile_radio")


def make_report(values, app_values=(80, 30), uid=10001):
    total = sum(max(v, 0) for v in values)
    return (
        "Estimated power use (mAh):\n"
        f"  Capacity: 4700, Computed drain: {total}, actual drain: {total}-{total}\n"
        "  Global\n"
        + "".join(
            f"  {name}: {v:.6f} apps: 0\n" for name, v in zip(COMPONENTS, values, strict=True)
        )
        + f"UID {uid}: {app_values[0]:.6f}\nUID 1010042: {app_values[1]:.6f}\n"
    )


def capture_for_report(report: str, directory: Path) -> Path:
    """Exercise the real parser/export/import path, not hand-built canonical facts."""
    directory.mkdir(parents=True, exist_ok=True)
    power = directory / "power.txt"
    power.write_text(report, encoding="utf-8")
    inputs = PipelineInputs(
        ROOT / "tests/fixtures/checkin_v9.csv", power, ROOT / "tests/fixtures/packages.txt"
    )
    result = run_pipeline(inputs)
    parsed = Path(export_canonical_result(result, directory / "datasets"))
    path = directory / "capture.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "capture_manifest.json",
            json.dumps(
                dict(
                    schema_version="1.0",
                    status="complete",
                    parse_status="complete",
                    parsed_directory="parsed/data",
                    ended_at_utc="2026-01-01T00:00:00Z",
                    synthetic=True,
                )
            ),
        )
        for artifact in parsed.iterdir():
            archive.write(artifact, "parsed/data/" + artifact.name)
        for source, name in (
            (inputs.checkin, "stats.csv"),
            (inputs.battery_report, "stats.txt"),
            (inputs.packages, "packageUID.txt"),
        ):
            archive.write(source, name)
    return path


def scenario_definitions():
    return [
        dict(id="screen", values=[500, 20, 10, 5]),
        dict(id="cpu", values=[15, 450, 10, 5]),
        dict(id="wifi", values=[10, 20, 420, 5]),
        dict(id="mobile_radio", values=[10, 20, 5, 430]),
        dict(id="zero", values=[0, 0, 0, 0], apps=[0, 0]),
        dict(id="negative", values=[-500, 15, 6, 1], apps=[-30, 10]),
        dict(id="tie", values=[100, 100, 10, 5], apps=[80, 80]),
        dict(id="unresolved_uid", values=[5, 30, 10, 0], apps=[400, 10], uid=10088),
    ]


def build_llm_inputs(output: Path):
    definitions = scenario_definitions()
    cases = []
    for row in definitions:
        values = row["values"]
        positive = [max(0, v) for v in values]
        maximum = max(positive)
        row["expected_top_components"] = [
            c for c, v in zip(COMPONENTS, positive, strict=True) if maximum > 0 and v == maximum
        ]
        row["report"] = make_report(values, row.get("apps", (80, 30)), row.get("uid", 10001))
    (output / "llm-scenarios.json").write_text(json.dumps(definitions, indent=2), encoding="utf-8")
    # Train/validation/test have disjoint RNG streams and disjoint exact prompts.
    # Targets are reviewed deterministic selection rules, never measured energy labels.
    with tempfile.TemporaryDirectory() as temporary:
        for split, seed, count in (
            ("train", 8101, 96),
            ("validation", 8102, 16),
            ("test", 8103, 24),
        ):
            rng = np.random.default_rng(seed)
            for index in range(count):
                values = rng.integers(1, 650, 4).tolist()
                apps = rng.integers(1, 500, 2).tolist()
                if index % 8 == 0:
                    values, apps = [0] * 4, [0, 0]
                capture = capture_for_report(
                    make_report(values, apps), Path(temporary) / f"{split}-{index}"
                )
                prepared = json.loads(prepare_analysis(str(capture)))
                facts = prepared["facts"]
                focus = [
                    next(f["id"] for f in facts if f["axis"] == axis)
                    for axis in ("component", "uid")
                    if any(f["axis"] == axis and f["value_mah"] > 0 for f in facts)
                ]
                cases.append(
                    dict(
                        id=f"{split}-{index}",
                        split=split,
                        prepared=prepared,
                        target=json.dumps(dict(focus=focus), separators=(",", ":")),
                    )
                )
    prompt_sets = [
        {r["prepared"]["prompt"] for r in cases if r["split"] == s}
        for s in ("train", "validation", "test")
    ]
    # All-zero is a shared boundary scenario: remove it from held-out sets to prevent leakage.
    cases = [
        r
        for r in cases
        if r["split"] == "train" or any(f["value_mah"] > 0 for f in r["prepared"]["facts"])
    ]
    prompt_sets = [
        {r["prepared"]["prompt"] for r in cases if r["split"] == s}
        for s in ("train", "validation", "test")
    ]
    assert not (
        prompt_sets[0] & prompt_sets[1]
        or prompt_sets[0] & prompt_sets[2]
        or prompt_sets[1] & prompt_sets[2]
    )
    (output / "lora-cases.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")
    return dict(
        counts={s: sum(r["split"] == s for r in cases) for s in ("train", "validation", "test")},
        synthetic=True,
    )


def series(seed: int, days: int):
    """Synthetic four-slots/day process, with shared latent usage and a late routine shift."""
    rng = np.random.default_rng(seed)
    values = np.zeros((days * 4, 7))  # four components and three UIDs; axes overlap.
    previous = np.zeros(3)
    for t in range(len(values)):
        slot = t % 4
        weekend = (t // 4) % 7 >= 5
        routine = np.array(
            [[0.10, 0.08, 0.08], [0.6, 0.2, 0.35], [0.5, 0.6, 0.35], [0.35, 0.7, 0.15]]
        )[slot]
        if weekend:
            routine = routine * [0.7, 1.2, 1.2]
        if t >= 80 * 4:
            routine = routine + ([0.0, 0.5, -0.1] if slot == 2 else [0, 0, 0])
        usage = np.maximum(0, 0.7 * routine + 0.3 * previous + rng.normal(0, 0.08, 3))
        previous = usage
        components = (
            np.array([20, 18, 12, 10])
            + np.array([[220, 100, 60], [70, 220, 50], [30, 90, 100], [80, 30, 90]]) @ usage
        )
        apps = (
            np.array([15, 12, 8]) + np.array([[200, 20, 15], [20, 250, 30], [20, 10, 180]]) @ usage
        )
        values[t] = np.maximum(0, np.r_[components, apps] + rng.normal(0, 5, 7))
    return values


def feature_row(values, t):
    # Forecast origin is slot t; values[t] is the withheld next-six-hour label.
    angle = 2 * np.pi * (t % 4) / 4
    return np.r_[
        values[t - 1],
        values[t - 4],
        values[t - 8 : t].mean(axis=0),
        np.sin(angle),
        np.cos(angle),
        int((t // 4) % 7 >= 5),
    ]


def fit_ridge(x, y, alpha):
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale < 1e-8] = 1
    z = np.c_[np.ones(len(x)), (x - mean) / scale]
    penalty = np.eye(z.shape[1]) * alpha
    penalty[0, 0] = 0
    weights = np.linalg.solve(z.T @ z + penalty, z.T @ y)
    return mean, scale, weights


def predict(model, x):
    mean, scale, weights = model
    return np.maximum(0, np.c_[np.ones(len(x)), (x - mean) / scale] @ weights)


def metrics(y, prediction):
    error = prediction - y
    total, total_pred = y[:, :4].sum(axis=1), prediction[:, :4].sum(axis=1)
    return dict(
        component_mae_mah=float(np.abs(error[:, :4]).mean()),
        uid_mae_mah=float(np.abs(error[:, 4:]).mean()),
        total_mae_mah=float(np.abs(total_pred - total).mean()),
        total_rmse_mah=float(np.sqrt(np.square(total_pred - total).mean())),
        total_wape=float(np.abs(total_pred - total).sum() / total.sum()),
        top_component_accuracy=float(
            (y[:, :4].argmax(axis=1) == prediction[:, :4].argmax(axis=1)).mean()
        ),
        top_uid_accuracy=float(
            (y[:, 4:].argmax(axis=1) == prediction[:, 4:].argmax(axis=1)).mean()
        ),
    )


def numerical_experiment():
    results = []
    started = time.perf_counter()
    for seed in SEEDS:
        values = series(seed, 112)
        origins = np.arange(8, len(values))
        x = np.array([feature_row(values, int(t)) for t in origins])
        y = values[origins]
        # Train first56 days, choose alpha on next14; untouched test42 days.
        train, valid, test = (
            origins < 56 * 4,
            (origins >= 56 * 4) & (origins < 70 * 4),
            origins >= 70 * 4,
        )
        scores = [
            (np.abs(predict(fit_ridge(x[train], y[train], a), x[valid]) - y[valid]).mean(), a)
            for a in (0.1, 1, 10, 100)
        ]
        alpha = float(min(scores)[1])
        before_test = train | valid
        frozen = fit_ridge(x[before_test], y[before_test], alpha)
        predictions = {
            "persistence": values[origins[test] - 1],
            "previous_day": values[origins[test] - 4],
            "ridge_frozen": predict(frozen, x[test]),
        }
        # Seasonal mean is fit before test, not recalculated with hidden future observations.
        by_slot = {slot: y[before_test & (origins % 4 == slot)].mean(axis=0) for slot in range(4)}
        predictions["slot_mean"] = np.array([by_slot[int(t % 4)] for t in origins[test]])
        adapted = []
        for index in np.flatnonzero(test):
            # At origin t, only labels from slots <t are available (6h delayed labels).
            history = np.arange(max(0, index - 28 * 4), index)
            assert origins[history].max() < origins[index]
            adapted.append(
                predict(fit_ridge(x[history], y[history], alpha), x[index : index + 1])[0]
            )
        predictions["ridge_rolling_28d"] = np.array(adapted)
        # Deliberately corrupt the unseen future: historical attributes must stay identical.
        t = 340
        mutated = values.copy()
        mutated[t:] += 100_000
        assert np.array_equal(feature_row(values, t), feature_row(mutated, t))
        model = frozen
        z = np.array([1, *((x[test][0] - model[0]) / model[1])])
        reference = np.maximum(0, z @ model[2])
        mobile_style = np.array(
            [
                max(0, sum(float(z[i]) * float(model[2][i, j]) for i in range(len(z))))
                for j in range(y.shape[1])
            ]
        )
        export_error = float(np.abs(reference - mobile_style).max())
        assert export_error < 1e-9
        results.append(
            dict(
                seed=seed,
                windows=dict(
                    train=int(train.sum()), validation=int(valid.sum()), test=int(test.sum())
                ),
                alpha=alpha,
                metrics={name: metrics(y[test], pred) for name, pred in predictions.items()},
                export_max_abs_error_mah=export_error,
                exported_float64_bytes=sum(a.nbytes for a in frozen),
            )
        )
    summary = {
        name: {
            metric: dict(
                mean=float(np.mean([r["metrics"][name][metric] for r in results])),
                min=float(min(r["metrics"][name][metric] for r in results)),
                max=float(max(r["metrics"][name][metric] for r in results)),
            )
            for metric in results[0]["metrics"][name]
        }
        for name in results[0]["metrics"]
    }
    return dict(
        synthetic=True,
        no_real_accuracy_claim=True,
        horizon_hours=6,
        days=112,
        seeds=list(SEEDS),
        results=results,
        summary=summary,
        elapsed_seconds=time.perf_counter() - started,
        checks=dict(
            future_feature_mutation="pass",
            delayed_label_updates="pass",
            export_numeric_parity="pass",
        ),
    )


def audit_capture(path):
    # Public summary only: do not copy raw data, package names, serials or capture hashes.
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("capture_manifest.json"))
    result = dict(
        origin="emulator_capture_not_personal_phone",
        capture_count=1,
        status=manifest.get("status"),
        parse_status=manifest.get("parse_status"),
        independent_future_labels=0,
        trainable_six_hour_windows=0,
        reason="single cumulative snapshot; no paired future label or validated reset epoch",
    )
    if result["parse_status"] == "complete":
        prepared = json.loads(prepare_analysis(str(path)))
        result["usable_snapshot_facts"] = len(prepared["facts"])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--capture", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = dict(
        experiment="AEMA-validation-2026-11-24",
        software_version="2.0.1",
        python=platform.python_version(),
        numpy=np.__version__,
        numeric=numerical_experiment(),
        llm_data=build_llm_inputs(args.output),
    )
    if args.capture:
        result["available_capture_audit"] = audit_capture(args.capture)
    result["lora_cases_sha256"] = hashlib.sha256(
        (args.output / "lora-cases.json").read_bytes()
    ).hexdigest()
    (args.output / "simulation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "complete",
                "numeric_seconds": result["numeric"]["elapsed_seconds"],
                "llm_data": result["llm_data"],
            }
        )
    )


if __name__ == "__main__":
    main()
