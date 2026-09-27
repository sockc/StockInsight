from __future__ import annotations

from contextlib import asynccontextmanager
from threading import Lock

from cachetools import TTLCache
from fastapi import FastAPI, HTTPException, Query

from .analysis import analyze, candles
from .db import init_db
from .events import event_response
from .policy import policy_response
from .schemas import BacktestResponse, EventsResponse, OverviewResponse, PolicyResponse


_analysis_cache: TTLCache = TTLCache(maxsize=16, ttl=600)
_analysis_lock = Lock()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="StockInsight Analysis Server",
    version="0.1.0",
    description="ARM-first market context, walk-forward backtest, event and policy analysis API.",
    lifespan=lifespan,
)


def _analysis(symbol: str) -> tuple[OverviewResponse, BacktestResponse]:
    symbol = symbol.upper()
    with _analysis_lock:
        cached = _analysis_cache.get(symbol)
    if cached is not None:
        return cached
    try:
        result = analyze(symbol)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"market data / analysis failed: {exc}") from exc
    with _analysis_lock:
        _analysis_cache[symbol] = result
    return result


@app.get("/")
def root() -> dict:
    return {
        "name": "StockInsight Analysis Server",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/api/v1/health")
def health() -> dict:
    return {"ok": True, "version": "0.1.0"}


@app.get("/api/v1/stocks/{symbol}/overview", response_model=OverviewResponse)
def overview(symbol: str) -> OverviewResponse:
    return _analysis(symbol)[0]


@app.get("/api/v1/stocks/{symbol}/backtest", response_model=BacktestResponse)
def backtest(symbol: str) -> BacktestResponse:
    return _analysis(symbol)[1]


@app.get("/api/v1/stocks/{symbol}/prediction")
def prediction(symbol: str) -> dict:
    o = _analysis(symbol)[0]
    return {
        "symbol": o.symbol,
        "as_of": o.as_of,
        "predictions": [x.model_dump() for x in o.predictions],
        "notice": "概率必须与样本外回测准确率一起解释。",
    }


@app.get("/api/v1/stocks/{symbol}/technical")
def technical(symbol: str) -> dict:
    o = _analysis(symbol)[0]
    return {
        "symbol": o.symbol,
        "as_of": o.as_of,
        "technicals": o.technicals.model_dump(),
        "key_levels": o.key_levels.model_dump(),
    }


@app.get("/api/v1/stocks/{symbol}/market-context")
def market_context(symbol: str) -> dict:
    o = _analysis(symbol)[0]
    return {
        "symbol": o.symbol,
        "as_of": o.as_of,
        "items": [x.model_dump() for x in o.market_context],
    }


@app.get("/api/v1/stocks/{symbol}/candles")
def candle_history(symbol: str, limit: int = Query(default=120, ge=20, le=1000)) -> dict:
    try:
        items = candles(symbol.upper(), limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"market data failed: {exc}") from exc
    return {"symbol": symbol.upper(), "items": items}


@app.get("/api/v1/stocks/{symbol}/events", response_model=EventsResponse)
def events(symbol: str, limit: int = Query(default=50, ge=1, le=100)) -> EventsResponse:
    return event_response(symbol, limit)


@app.get("/api/v1/stocks/{symbol}/policy", response_model=PolicyResponse)
def policy(symbol: str) -> PolicyResponse:
    return policy_response(symbol)
