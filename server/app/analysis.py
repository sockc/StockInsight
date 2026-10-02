from __future__ import annotations

import math
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from .market import NAMES, WATCHLIST, MarketBundle, bundle
from .schemas import (
    BacktestItem,
    BacktestResponse,
    KeyLevels,
    MarketContextItem,
    OverviewResponse,
    PredictionHorizon,
    TechnicalSummary,
)

HORIZONS = (1, 5, 10, 20)
K_NEIGHBORS = 30


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    # Preserve warm-up NaN. Flat prices are neutral, not overbought.
    value = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
    value = value.mask((loss == 0) & (gain > 0), 100.0)
    value = value.mask((gain == 0) & (loss > 0), 0.0)
    value = value.mask((gain == 0) & (loss == 0), 50.0)
    return value.clip(0, 100)


def _feature_frame(m: MarketBundle, symbol: str) -> pd.DataFrame:
    close = m.aligned_close
    arm = close[symbol]
    primary = m.histories[symbol].reindex(close.index)
    f = pd.DataFrame(index=close.index)

    for p in (1, 5, 10, 20, 60):
        f[f"arm_r{p}"] = arm.pct_change(p)
    for p in (5, 20, 50, 100):
        f[f"arm_ma{p}_dist"] = arm / arm.rolling(p).mean() - 1

    f["arm_rsi14"] = _rsi(arm) / 100.0
    logret = np.log(arm / arm.shift(1))
    f["arm_vol20"] = logret.rolling(20).std(ddof=0) * math.sqrt(252)
    f["arm_volume_ratio20"] = primary["Volume"] / primary["Volume"].rolling(20).mean() - 1

    for peer in [s for s in WATCHLIST if s != symbol and s in close.columns]:
        for p in (1, 5, 20):
            f[f"{peer.lower()}_r{p}"] = close[peer].pct_change(p)
    return f.replace([np.inf, -np.inf], np.nan)


def _standardized_distance(candidates: pd.DataFrame, current: pd.Series) -> pd.Series:
    mean = candidates.mean(axis=0)
    std = candidates.std(axis=0, ddof=0).replace(0, 1.0).fillna(1.0)
    z = (candidates - current) / std
    return np.sqrt((z * z).sum(axis=1))


def _neighbor_prediction(
    features: pd.DataFrame,
    close: pd.Series,
    current_idx: int,
    horizon: int,
    k: int = K_NEIGHBORS,
) -> tuple[float, float, int] | None:
    current_time = features.index[current_idx]
    current = features.loc[current_time]
    if current.isna().any():
        return None

    # At prediction time i, a training observation j can be used only when its
    # forward-horizon label is already known: j + horizon <= i.
    max_train_pos = current_idx - horizon
    if max_train_pos <= 110:
        return None

    candidates = features.iloc[100 : max_train_pos + 1].dropna()
    if len(candidates) < k:
        return None
    distances = _standardized_distance(candidates, current).sort_values()
    nearest = distances.head(k)

    returns: list[float] = []
    weights: list[float] = []
    for ts, dist in nearest.items():
        pos = close.index.get_loc(ts)
        if isinstance(pos, slice) or pos + horizon >= len(close):
            continue
        r = float(close.iloc[pos + horizon] / close.iloc[pos] - 1.0)
        returns.append(r)
        weights.append(1.0 / (float(dist) + 0.20))
    if not returns:
        return None

    w = np.asarray(weights, dtype=float)
    r = np.asarray(returns, dtype=float)
    up_probability = float(np.average((r > 0).astype(float), weights=w))
    expected_return = float(np.average(r, weights=w))
    return up_probability, expected_return, len(returns)


def _walk_forward(features: pd.DataFrame, close: pd.Series, horizon: int) -> BacktestItem:
    start = max(180, int(len(features) * 0.46))
    # At step i the baseline may only use labels that mature on or before i.
    predictions: list[tuple[float, int, float]] = []
    for i in range(start, len(features) - horizon):
        pred = _neighbor_prediction(features, close, i, horizon)
        if pred is None:
            continue
        p, _, _ = pred
        actual = int(close.iloc[i + horizon] > close.iloc[i])
        matured = close.iloc[100 + horizon : i + 1].to_numpy() > close.iloc[100 : i - horizon + 1].to_numpy()
        if len(matured) == 0:
            continue
        baseline = float(matured.mean())
        predictions.append((p, actual, baseline))

    if not predictions:
        return BacktestItem(
            horizon=f"{horizon}D", tests=0, accuracy=0.0,
            high_confidence_tests=0, high_confidence_accuracy=None,
            brier_score=None, baseline_accuracy=None, baseline_brier_score=None,
            non_overlapping_tests=0, non_overlapping_accuracy=None,
        )

    correct = sum((p >= 0.5) == bool(y) for p, y, _ in predictions)
    brier = sum((p - y) ** 2 for p, y, _ in predictions) / len(predictions)
    baseline_correct = sum((b >= 0.5) == bool(y) for _, y, b in predictions)
    baseline_brier = sum((b - y) ** 2 for _, y, b in predictions) / len(predictions)
    high = [(p, y) for p, y, _ in predictions if p >= 0.60 or p <= 0.40]
    non_overlap = predictions[::horizon]
    non_overlap_correct = sum((p >= 0.5) == bool(y) for p, y, _ in non_overlap)

    return BacktestItem(
        horizon=f"{horizon}D", tests=len(predictions),
        accuracy=round(correct / len(predictions) * 100, 1),
        high_confidence_tests=len(high),
        high_confidence_accuracy=(
            round(sum((p >= 0.5) == bool(y) for p, y in high) / len(high) * 100, 1)
            if high else None
        ),
        brier_score=round(brier, 3),
        baseline_accuracy=round(baseline_correct / len(predictions) * 100, 1),
        baseline_brier_score=round(baseline_brier, 3),
        non_overlapping_tests=len(non_overlap),
        non_overlapping_accuracy=round(non_overlap_correct / len(non_overlap) * 100, 1),
    )


def _confidence(backtest_accuracy: float, tests: int) -> str:
    # A high apparent accuracy is not calibrated probability. Until a
    # held-out calibration study exists, do not advertise high confidence.
    return "low"


def _key_levels(primary: pd.DataFrame, price: float) -> KeyLevels:
    recent = primary.tail(252)
    resist_candidates = [
        float(primary.tail(5)["High"].max()),
        float(primary.tail(20)["High"].max()),
        float(primary.tail(60)["High"].max()),
        float(recent["High"].max()),
    ]
    support_candidates = [
        float(primary.tail(5)["Low"].min()),
        float(primary.tail(20)["Low"].min()),
        float(primary.tail(60)["Low"].min()),
        float(primary["Close"].tail(20).mean()),
        float(primary["Close"].tail(50).mean()),
        float(primary["Close"].tail(100).mean()),
    ]

    resistance = sorted({round(x, 2) for x in resist_candidates if x >= price * 0.995})[:3]
    support = sorted({round(x, 2) for x in support_candidates if x <= price * 1.005}, reverse=True)[:4]
    return KeyLevels(resistance=resistance, support=support)


def _technical(primary: pd.DataFrame) -> TechnicalSummary:
    close = primary["Close"]
    volume = primary["Volume"]
    logret = np.log(close / close.shift(1))
    return TechnicalSummary(
        rsi14=round(float(_rsi(close).iloc[-1]), 1),
        volume_ratio20=round(float(volume.iloc[-1] / volume.tail(20).mean()), 2),
        volatility20_annualized_pct=round(float(logret.tail(20).std(ddof=0) * math.sqrt(252) * 100), 1),
        return5d_pct=round(float((close.iloc[-1] / close.iloc[-6] - 1) * 100), 2),
        return20d_pct=round(float((close.iloc[-1] / close.iloc[-21] - 1) * 100), 2),
        ma20=round(float(close.tail(20).mean()), 2),
        ma50=round(float(close.tail(50).mean()), 2),
        ma100=round(float(close.tail(100).mean()), 2),
        ma200=round(float(close.tail(200).mean()), 2),
    )


def _market_context(m: MarketBundle, symbol: str) -> list[MarketContextItem]:
    arm = m.aligned_close[symbol]
    arm_change = float((arm.iloc[-1] / arm.iloc[-2] - 1) * 100)
    result: list[MarketContextItem] = []
    for peer in [s for s in WATCHLIST if s != symbol and s in m.aligned_close.columns]:
        s = m.aligned_close[peer]
        change = float((s.iloc[-1] / s.iloc[-2] - 1) * 100)
        result.append(
            MarketContextItem(
                symbol=peer,
                name=NAMES.get(peer, peer),
                change_pct=round(change, 2),
                relative_to_arm_pct=round(arm_change - change, 2),
                note="ARM涨跌减去该标的同期涨跌",
            )
        )
    return result


def analyze(symbol: str = "ARM") -> tuple[OverviewResponse, BacktestResponse]:
    symbol = symbol.upper()
    m = bundle(symbol)
    primary = m.histories[symbol].loc[: m.aligned_close.index[-1]].copy()
    features = _feature_frame(m, symbol)
    close = m.aligned_close[symbol]

    backtests = [_walk_forward(features, close, h) for h in HORIZONS]
    backtest_map = {int(x.horizon[:-1]): x for x in backtests}

    predictions: list[PredictionHorizon] = []
    for horizon in HORIZONS:
        pred = _neighbor_prediction(features, close, len(features) - 1, horizon)
        bt = backtest_map[horizon]
        if pred is None:
            # Do not invent 50% or a zero return when observations are insufficient.
            continue
        p, expected, n = pred
        predictions.append(
            PredictionHorizon(
                horizon=f"{horizon}D",
                up_probability=round(p * 100, 1),
                expected_return_pct=round(expected * 100, 2),
                backtest_accuracy=bt.accuracy,
                sample_size=n,
                confidence=_confidence(bt.accuracy, bt.tests),
            )
        )

    price = float(close.iloc[-1])
    daily_change = float((close.iloc[-1] / close.iloc[-2] - 1) * 100)
    as_of = close.index[-1].strftime("%Y-%m-%d")

    oldest_fetch = m.fetched_at.isoformat() if m.fetched_at else "unknown"
    calendar_age = (
        (datetime.now(timezone.utc).date() - close.index[-1].date()).days
    )
    stale_label = " · 行情可能过期" if calendar_age > 5 else ""
    mode_label = "已验证历史缓存" if m.data_mode == "historical_cache" else "历史日线（非实时）"

    overview = OverviewResponse(
        symbol=symbol,
        name=NAMES.get(symbol, symbol),
        currency="USD",
        price=round(price, 2),
        change_pct=round(daily_change, 2),
        as_of=as_of,
        data_mode=m.data_mode,
        status_text=f"{mode_label} · 行情截至 {as_of} · 最近采集 {oldest_fetch}{stale_label}",
        predictions=predictions,
        market_context=_market_context(m, symbol),
        technicals=_technical(primary),
        key_levels=_key_levels(primary, price),
        notices=[
            "显示的是历史相似样本上涨比例，未经概率校准，不是未来上涨的可靠概率。",
            "回测同时提供历史上涨频率基准；多日预测窗口重叠，独立样本数量更少。",
            "yfinance 为原型日线数据源，不是实时授权行情。",
        ],
    )
    backtest = BacktestResponse(
        symbol=symbol,
        items=backtests,
        note="逐日扩展回测仅使用当时已成熟的标签；对比同期历史上涨频率基准，并单列不重叠评估。相似样本比例未经校准，样本仍可能相关。",
        data_mode="computed",
    )
    return overview, backtest


def candles(symbol: str = "ARM", limit: int = 120) -> list[dict]:
    m = bundle(symbol)
    df = m.histories[symbol].tail(max(20, min(limit, 1000)))
    return [
        {
            "date": idx.strftime("%Y-%m-%d"),
            "open": round(float(row.Open), 4),
            "high": round(float(row.High), 4),
            "low": round(float(row.Low), 4),
            "close": round(float(row.Close), 4),
            "volume": int(row.Volume),
        }
        for idx, row in df.iterrows()
    ]
