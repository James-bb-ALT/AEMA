"""Regression proof for the experimental learner and its chronological/export boundaries."""

import json

import numpy as np
import pytest

from experiments.battery_validation import fit_ridge, predict
from experiments.ultralight_validation import (
    FEATURES,
    export_mlp,
    export_ridge,
    fit_mlp,
    make_series,
    mlp_predict,
    portable_predict,
    portable_ridge,
    windows,
)


def test_future_labels_cannot_change_training_or_origin_features():
    values = make_series(17, "linear_routine_shift")
    origins, x, y, masks = windows(values)
    train, valid, test = masks
    assert (train.sum(), valid.sum(), test.sum()) == (216, 56, 168)
    assert len(FEATURES) == x.shape[1] == 24
    changed = values.copy()
    changed[280:] += 12345
    _, changed_x, changed_y, _ = windows(changed)
    np.testing.assert_array_equal(x[train | valid], changed_x[train | valid])
    np.testing.assert_array_equal(y[train | valid], changed_y[train | valid])
    np.testing.assert_array_equal(x[origins == 280], changed_x[origins == 280])
    assert not np.array_equal(y[test], changed_y[test])


def test_mlp_learns_heldout_signal_and_export_survives_serialization(tmp_path):
    rng = np.random.default_rng(456)
    x = rng.uniform(-1, 1, (220, 24))
    y = np.maximum(0, 50 + 20 * x[:, :7] + 5 * np.maximum(x[:, 7:14], 0))
    model, selection = fit_mlp(
        x[:140], y[:140], (16, 8), 0.001, 77, epochs=600, validation=(x[140:180], y[140:180])
    )
    prediction = mlp_predict(model, x[180:])
    baseline_error = np.abs(y[:140].mean(axis=0) - y[180:]).mean()
    assert np.abs(prediction - y[180:]).mean() < baseline_error * 0.75
    assert 1 <= selection["epochs"] <= 600
    assert selection["validation_mae"] == pytest.approx(
        np.abs(mlp_predict(model, x[140:180]) - y[140:180]).mean()
    )
    # Means/scales must be fitted on training only, including for chronological validation.
    np.testing.assert_allclose(model["x_mean"], x[:140].mean(axis=0))
    path = tmp_path / "model.json"
    meta = export_mlp(model, path)
    restored = json.loads(path.read_text())
    portable = [portable_predict(restored, row.tolist()) for row in x[180:]]
    np.testing.assert_allclose(portable, prediction, rtol=0, atol=0.001)
    assert restored["synthetic"] is True
    assert restored["deployment_status"] == "research_only_not_installed"
    assert meta["parameters"] == 599
    assert meta["raw_fp32_weight_bytes"] == 599 * 4


def test_ridge_export_preserves_all_seven_axes(tmp_path):
    _, x, y, (train, valid, test) = windows(make_series(42, "nonlinear_routine_shift"))
    model = fit_ridge(x[train | valid], y[train | valid], 10)
    path = tmp_path / "ridge.json"
    artifact = export_ridge(model, path)
    document = json.loads(path.read_text())
    portable = [portable_ridge(document, row.tolist()) for row in x[test]]
    np.testing.assert_allclose(portable, predict(model, x[test]), rtol=0, atol=0.001)
    assert artifact["parameters"] == 175
    assert artifact["raw_fp32_weight_bytes"] == 700


@pytest.mark.parametrize(
    "invalid",
    [np.zeros((200, 7)), np.full((300, 7), np.nan), np.full((300, 7), -1), np.zeros((300, 6))],
)
def test_invalid_windows_are_rejected(invalid):
    with pytest.raises(ValueError):
        windows(invalid)
