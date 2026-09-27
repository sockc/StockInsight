from __future__ import annotations

from dataclasses import dataclass
from threading import Lock

import pandas as pd
import yfinance as yf
from cachetools import TTLCache


WATCHLIST = ["ARM", "QQQ", "SMH", "NVDA", "AMD", "SPY"]
NAMES = {
    "ARM": "Arm Holdings",
    "QQQ": "Nasdaq-100 ETF",
    "SMH": "VanEck Semiconductor ETF",
    "NVDA": "NVIDIA",
    "AMD": "AMD",
    "SPY": "S&P 500 ETF",
}


@dataclass(frozen=True)
class MarketBundle:
    histories: dict[str, pd.DataFrame]
    aligned_close: pd.DataFrame


_cache: TTLCache = TTLCache(maxsize=32, ttl=600)
_lock = Lock()


def _clean_history(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        raise RuntimeError("empty market history")
    out = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    out = out.dropna(subset=["Close"])
    idx = pd.to_datetime(out.index)
    if getattr(idx, "tz", None) is not None:
        idx = idx.tz_convert("America/New_York").tz_localize(None)
    out.index = idx.normalize()
    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out


def history(symbol: str, period: str = "5y") -> pd.DataFrame:
    symbol = symbol.upper()
    key = (symbol, period)
    with _lock:
        cached = _cache.get(key)
        if cached is not None:
            return cached.copy()

    raw = yf.Ticker(symbol).history(
        period=period,
        interval="1d",
        auto_adjust=True,
        actions=False,
        repair=True,
    )
    cleaned = _clean_history(raw)
    with _lock:
        _cache[key] = cleaned
    return cleaned.copy()


def bundle(symbol: str = "ARM") -> MarketBundle:
    symbol = symbol.upper()
    symbols = [symbol] + [s for s in WATCHLIST if s != symbol]
    histories = {s: history(s) for s in symbols}
    close = pd.concat({s: df["Close"] for s, df in histories.items()}, axis=1, join="inner").dropna()
    close.columns = symbols
    if len(close) < 160:
        raise RuntimeError("not enough aligned market history")
    return MarketBundle(histories=histories, aligned_close=close)
