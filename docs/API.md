# StockInsight API V0.1

Base path: `/api/v1`

## `GET /health`

服务健康检查。

## `GET /stocks/{symbol}/overview`

APK 首页聚合接口。一次返回价格、市场环境、技术状态、1/5/10/20 日模型结果、样本外准确率和关键价位。

关键原则：

- `up_probability` 是当前历史相似状态产生的概率。
- `backtest_accuracy` 是 walk-forward 样本外方向命中率。
- 两者必须同时展示。
- `confidence=low` 时 APK 不应渲染成强交易信号。

## `GET /stocks/{symbol}/candles?limit=120`

日线 OHLCV，20–1000 条。

## `GET /stocks/{symbol}/technical`

RSI、均线、成交量倍率、波动率与自动关键价位。

## `GET /stocks/{symbol}/market-context`

返回 QQQ / SMH / NVDA / AMD / SPY 同期市场表现，并计算 ARM 相对表现。

## `GET /stocks/{symbol}/prediction`

仅返回当前 1/5/10/20 日概率。应用端仍应同时请求/显示回测有效性。

## `GET /stocks/{symbol}/backtest`

Walk-forward 样本外验证：

- tests
- accuracy
- high_confidence_tests
- high_confidence_accuracy
- brier_score

## `GET /stocks/{symbol}/events`

事件时间线。数据库表已支持：

- event_type
- importance
- source
- affected_symbols
- 1d / 5d reaction
- sector-relative reaction

V0.2 扩展 5m / 30m / 1h / 10d / 20d。

## `GET /stocks/{symbol}/policy`

政策分类与近期事件。V0.1 建结构，V0.2 接真实政策源。
