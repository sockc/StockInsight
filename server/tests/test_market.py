from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from app import market


def _sample(count=180):
    idx = pd.bdate_range("2024-01-01", periods=count)
    close = np.linspace(50, 75, count)
    return pd.DataFrame(
        {"Open": close, "High": close + 2, "Low": close - 2,
         "Close": close, "Volume": np.ones(count) * 1000},
        index=idx,
    )


def test_history_validation_drops_corrupt_rows_and_duplicate_days():
    raw = _sample()
    raw.iloc[2, raw.columns.get_loc("Close")] = -1
    raw.iloc[3, raw.columns.get_loc("Volume")] = -5
    raw = pd.concat([raw, raw.iloc[[10]]])
    cleaned = market._clean_history(raw)
    assert len(cleaned) == len(raw) - 3
    assert cleaned.index.is_unique
    assert (cleaned["Close"] > 0).all()


def test_provider_error_uses_verified_snapshot(monkeypatch):
    market._cache.clear()
    market._last_good.clear()
    snapshot = _sample()
    at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(market, "_load_snapshot", lambda symbol: (snapshot, at))
    def broken(*args, **kwargs):
        raise ConnectionError("provider down")
    monkeypatch.setattr(market.yf, "Ticker", broken)
    result, mode, fetched = market.history_with_meta("ARM")
    assert mode == "historical_cache"
    assert fetched == at
    pd.testing.assert_frame_equal(result, snapshot)


def test_provider_error_without_verified_snapshot_is_explicit(monkeypatch):
    market._cache.clear()
    market._last_good.clear()
    monkeypatch.setattr(market, "_load_snapshot", lambda symbol: None)
    monkeypatch.setattr(
        market.yf, "Ticker", lambda symbol: (_ for _ in ()).throw(ConnectionError())
    )
    with pytest.raises(RuntimeError, match="no verified cache"):
        market.history_with_meta("ARM")
