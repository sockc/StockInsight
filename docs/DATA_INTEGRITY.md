# Data integrity and model validation (first hardening pass)

## Data source / fallback

- The server uses **adjusted daily bars** from yfinance, not real-time market quotes.
- Invalid OHLCV candles (non-finite, non-positive prices, negative volume or inconsistent ranges) are rejected.
- A successful 5-year download is stored in PostgreSQL, when DATABASE_URL is configured. A background task checks the watchlist on server start and every 90 minutes; normal requests reuse a verified snapshot for up to 90 minutes, with a 10-minute in-process API cache. Set MARKET_REFRESH_ENABLED=0 to disable background refresh (for example when running multiple workers).
- If the provider fails, the last verified PostgreSQL snapshot (or in-process last-good data within the current server process) is used with data_mode=historical_cache and a visible collection timestamp. If no verified data exist, the request fails with HTTP 502; **no fabricated price is returned**.
- Only app display data that were actually received from the API may be cached on the device. The built-in demonstration figures must not be substituted for failed real requests.

## Model output

- up_probability is retained for backward API compatibility, but currently represents the **weighted up-frequency of K similar historical observations**, not a statistically calibrated probability.
- The walk-forward loop uses only feature vectors available at prediction time and labels that have matured by that time.
- Historical up-frequency serves as a per-step baseline; accuracy and Brier score are reported for both.
- Non-overlapping evaluations are reported separately for multi-day windows. They have smaller samples and are not a substitute for a fully independent holdout.
- Confidence remains low until probability calibration has been validated on a separate held-out period. If no valid prediction can be computed, that horizon is omitted instead of returning an invented 50%.
- This release does **not** establish predictive edge. Data-source licensing, corporate-action revisions, exchange calendars and a held-out probability-calibration study remain future work.

Run locally: cd server && pip install -r requirements.txt && python -m pytest
