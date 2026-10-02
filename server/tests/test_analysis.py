import numpy as np
import pandas as pd
import pytest

from app.analysis import _rsi, _neighbor_prediction, _walk_forward, _confidence


def test_rsi_warmup_flat_up_and_down():
    flat = _rsi(pd.Series([100.0] * 40))
    assert flat.iloc[:14].isna().all()
    assert flat.iloc[-1] == pytest.approx(50.0)
    assert _rsi(pd.Series(np.arange(1.0, 41.0))).iloc[-1] == 100.0
    assert _rsi(pd.Series(np.arange(40.0, 0.0, -1.0))).iloc[-1] == 0.0


def test_model_does_not_use_unmatured_future_labels():
    idx = pd.bdate_range("2024-01-01", periods=230)
    close = pd.Series(np.linspace(20, 40, len(idx)), index=idx)
    features = pd.DataFrame({"feature": np.arange(len(idx), dtype=float)}, index=idx)
    i, h = 200, 20
    original = _neighbor_prediction(features, close, i, h, k=8)
    mutated = close.copy()
    mutated.iloc[i + 1:] = 100000
    after = _neighbor_prediction(features, mutated, i, h, k=8)
    assert original == after


def test_backtest_reports_past_only_baseline_and_nonoverlap():
    rng = np.random.default_rng(42)
    idx = pd.bdate_range("2023-01-01", periods=280)
    close = pd.Series(100 * np.exp(rng.normal(0.0003, 0.015, len(idx)).cumsum()), index=idx)
    features = pd.DataFrame({"r": close.pct_change().fillna(0)}, index=idx)
    result = _walk_forward(features, close, horizon=5)
    assert result.tests > 0
    assert result.baseline_accuracy is not None
    assert result.baseline_brier_score is not None
    assert result.non_overlapping_tests < result.tests
    assert 0 <= result.baseline_accuracy <= 100
    assert _confidence(100, 10000) == "low"
