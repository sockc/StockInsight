from pydantic import BaseModel, Field


class PredictionHorizon(BaseModel):
    horizon: str
    up_probability: float
    expected_return_pct: float
    backtest_accuracy: float
    sample_size: int
    confidence: str = "low"


class MarketContextItem(BaseModel):
    symbol: str
    name: str
    change_pct: float
    relative_to_arm_pct: float | None = None
    note: str = ""


class TechnicalSummary(BaseModel):
    rsi14: float
    volume_ratio20: float
    volatility20_annualized_pct: float
    return5d_pct: float
    return20d_pct: float
    ma20: float
    ma50: float
    ma100: float
    ma200: float


class KeyLevels(BaseModel):
    resistance: list[float]
    support: list[float]


class OverviewResponse(BaseModel):
    symbol: str
    name: str
    currency: str = "USD"
    price: float
    change_pct: float
    as_of: str
    data_mode: str = "live"
    status_text: str
    predictions: list[PredictionHorizon]
    market_context: list[MarketContextItem]
    technicals: TechnicalSummary
    key_levels: KeyLevels
    notices: list[str] = Field(default_factory=list)


class EventItem(BaseModel):
    id: str
    time: str
    type: str
    title: str
    summary: str
    importance: str
    source: str | None = None
    affected_symbols: list[str] = Field(default_factory=list)
    reaction1d_pct: float | None = None
    reaction5d_pct: float | None = None
    sector_relative1d_pct: float | None = None


class EventsResponse(BaseModel):
    symbol: str
    items: list[EventItem]
    data_mode: str


class BacktestItem(BaseModel):
    horizon: str
    tests: int
    accuracy: float
    high_confidence_tests: int
    high_confidence_accuracy: float | None = None
    brier_score: float | None = None


class BacktestResponse(BaseModel):
    symbol: str
    items: list[BacktestItem]
    note: str
    data_mode: str


class PolicyCategory(BaseModel):
    key: str
    name: str
    status: str
    explanation: str


class PolicyResponse(BaseModel):
    symbol: str
    categories: list[PolicyCategory]
    recent_events: list[EventItem] = Field(default_factory=list)
    data_mode: str
    note: str
