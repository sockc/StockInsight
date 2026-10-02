from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from threading import Lock

import numpy as np
import pandas as pd
import yfinance as yf
from cachetools import TTLCache
from sqlalchemy import delete, select

from .db import MarketCandleRecord, MarketSnapshotRecord, SessionLocal

logger = logging.getLogger(__name__)

WATCHLIST = ["ARM", "QQQ", "SMH", "NVDA", "AMD", "SPY"]
NAMES = {
    "ARM": "Arm Holdings",
    "QQQ": "Nasdaq-100 ETF",
    "SMH": "VanEck Semiconductor ETF",
    "NVDA": "NVIDIA",
    "AMD": "AMD",
    "SPY": "S&P 500 ETF",
}

# Memory TTL avoids repeated downloads; verified Postgres snapshots survive restarts.
PROVIDER_REFRESH = timedelta(minutes=90)
_cache: TTLCache = TTLCache(maxsize=32, ttl=600)
_last_good: dict[tuple[str, str], tuple[pd.DataFrame, datetime]] = {}
_lock = Lock()


@dataclass(frozen=True)
class MarketBundle:
    histories: dict[str, pd.DataFrame]
    aligned_close: pd.DataFrame
    data_mode: str = "historical_delayed"
    fetched_at: datetime | None = None


def _clean_history(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        raise ValueError("empty market history")
    required = ["Open", "High", "Low", "Close", "Volume"]
    if any(col not in df.columns for col in required):
        raise ValueError("market history missing required OHLCV columns")

    out = df[required].copy()
    for col in required:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    idx = pd.to_datetime(out.index)
    if getattr(idx, "tz", None) is not None:
        idx = idx.tz_convert("America/New_York").tz_localize(None)
    out.index = idx.normalize()
    out = out[~out.index.duplicated(keep="last")].sort_index()
    values = out[required].to_numpy(dtype=float)
    finite = np.isfinite(values).all(axis=1)
    plausible = (
        (out["Open"] > 0) & (out["High"] > 0) &
        (out["Low"] > 0) & (out["Close"] > 0) &
        (out["Volume"] >= 0) &
        (out["High"] >= out["Low"]) &
        (out["High"] >= out[["Open", "Close"]].max(axis=1) * 0.999) &
        (out["Low"] <= out[["Open", "Close"]].min(axis=1) * 1.001)
    )
    out = out.loc[finite & plausible]
    if out.empty:
        raise ValueError("no valid OHLCV rows after validation")
    return out


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _load_snapshot(symbol: str) -> tuple[pd.DataFrame, datetime] | None:
    if SessionLocal is None:
        return None
    with SessionLocal() as session:
        meta = session.get(MarketSnapshotRecord, symbol)
        if meta is None:
            return None
        rows = session.scalars(
            select(MarketCandleRecord)
            .where(MarketCandleRecord.symbol == symbol)
            .order_by(MarketCandleRecord.day)
        ).all()
        if len(rows) < 160:
            return None
        df = pd.DataFrame(
            [{
                "Date": r.day, "Open": r.open, "High": r.high,
                "Low": r.low, "Close": r.close, "Volume": r.volume,
            } for r in rows]
        ).set_index("Date")
        df.index = pd.to_datetime(df.index)
        return _clean_history(df), _utc(meta.fetched_at)


def _save_snapshot(symbol: str, df: pd.DataFrame, fetched_at: datetime) -> None:
    if SessionLocal is None:
        return
    with SessionLocal.begin() as session:
        session.execute(delete(MarketCandleRecord).where(MarketCandleRecord.symbol == symbol))
        session.add_all([
            MarketCandleRecord(
                symbol=symbol, day=ts.date(),
                open=float(row.Open), high=float(row.High),
                low=float(row.Low), close=float(row.Close),
                volume=int(row.Volume),
            )
            for ts, row in df.iterrows()
        ])
        meta = session.get(MarketSnapshotRecord, symbol)
        if meta is None:
            session.add(MarketSnapshotRecord(
                symbol=symbol, fetched_at=fetched_at, source="yfinance"
            ))
        else:
            meta.fetched_at = fetched_at


def history_with_meta(symbol: str, period: str = "5y") -> tuple[pd.DataFrame, str, datetime]:
    symbol = symbol.upper()
    key = (symbol, period)
    with _lock:
        cached = _cache.get(key)
        if cached is not None:
            df, mode, fetched = cached
            return df.copy(), mode, fetched

    # Persistent snapshots are only valid for the same historical period (5y).
    snapshot = None
    if period == "5y":
        try:
            snapshot = _load_snapshot(symbol)
        except Exception:
            logger.exception("Cannot read historical market snapshot for %s", symbol)

    now = datetime.now(timezone.utc)
    if snapshot and now - snapshot[1] < PROVIDER_REFRESH:
        result = (snapshot[0], "historical_cache", snapshot[1])
    else:
        try:
            raw = yf.Ticker(symbol).history(
                period=period, interval="1d",
                auto_adjust=True, actions=False, repair=True,
            )
            cleaned = _clean_history(raw)
            if len(cleaned) < 160:
                raise ValueError("insufficient verified historical candles")
            fetched = datetime.now(timezone.utc)
            result = (cleaned, "historical_delayed", fetched)
            try:
                if period == "5y":
                    _save_snapshot(symbol, cleaned, fetched)
            except Exception:
                logger.exception("Could not persist verified market snapshot for %s", symbol)
        except Exception:
            logger.exception("Market provider unavailable for %s", symbol)
            with _lock:
                memory = _last_good.get(key)
            fallback = snapshot or memory
            if fallback is None:
                raise RuntimeError("market provider unavailable and no verified cache exists")
            result = (fallback[0], "historical_cache", fallback[1])

    with _lock:
        _cache[key] = result
        _last_good[key] = (result[0].copy(), result[2])
    return result[0].copy(), result[1], result[2]


def history(symbol: str, period: str = "5y") -> pd.DataFrame:
    return history_with_meta(symbol, period)[0]


def bundle(symbol: str = "ARM") -> MarketBundle:
    symbol = symbol.upper()
    symbols = [symbol] + [s for s in WATCHLIST if s != symbol]
    fetched = {s: history_with_meta(s) for s in symbols}
    histories = {s: item[0] for s, item in fetched.items()}
    close = pd.concat(
        {s: df["Close"] for s, df in histories.items()},
        axis=1, join="inner",
    ).dropna()
    close.columns = symbols
    if len(close) < 160:
        raise RuntimeError("not enough aligned verified market history")
    mode = (
        "historical_cache"
        if any(item[1] == "historical_cache" for item in fetched.values())
        else "historical_delayed"
    )
    oldest_fetch = min(item[2] for item in fetched.values())
    return MarketBundle(histories, close, mode, oldest_fetch)
