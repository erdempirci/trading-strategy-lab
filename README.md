# Trading Strategy Lab

AI-assisted, multi-market strategy research and backtesting workspace.

> Research MVP only. No live order execution. Backtest results are hypothetical and do not imply future performance.

## MVP capabilities
- FastAPI REST API
- Deterministic OHLCV demo dataset
- EMA crossover strategy (long/flat) and configurable fees/slippage
- Backtest metrics: net return, win rate, profit factor, max drawdown, expectancy, Sharpe
- Docker Compose development environment
- Adapter interfaces for Binance (CCXT) and MT5 CSV export

## Quick start (Docker)
```bash
cp .env.example .env
docker compose up --build
```
Open http://localhost:8000/docs and run:
- `GET /health`
- `GET /market-data/demo?symbol=BTC/USDT&timeframe=1h&bars=500`
- `POST /backtests` with body:
```json
{
  "symbol": "BTC/USDT",
  "timeframe": "1h",
  "strategy": "ema_crossover",
  "fast_period": 12,
  "slow_period": 26,
  "initial_capital": 10000,
  "fee_bps": 5,
  "slippage_bps": 2
}
```

## Local development
Python 3.11+ recommended.
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Data architecture
- Normalize all market bars to UTC OHLCV: timestamp, open, high, low, close, volume.
- Binance: optional CCXT adapter (public market data; exchange limits apply).
- MT5: run MetaTrader 5 on a Windows machine/VPS and export CSV or push bars to the API. The official MetaTrader5 Python package requires a supported Windows terminal environment; it is not part of the macOS container.
- Store bulk historical bars as Parquet; use PostgreSQL for users, experiments, metadata, and results when persistence is added.

## Backtesting assumptions
The starter engine uses close-to-close signal execution with a one-bar delay to avoid look-ahead: signals computed at bar close are applied to the next bar's close. Fees and slippage are charged on position changes. This is a simplified MVP model, not a broker execution simulator. Intrabar stop/target, funding, swaps, contract multipliers, dividends, futures rolls, and market-specific calendars are not yet modeled.

## Roadmap
1. Data ingestion and validation
2. Long/short strategy interface and event-driven execution
3. Trade ledger, equity curve and downloadable reports
4. Walk-forward and out-of-sample evaluation
5. Parameter optimization and Monte Carlo
6. AI strategy specification generation (validated JSON DSL; no arbitrary code execution)
7. Supabase persistence and user accounts
8. Paper trading, then optional broker integration behind explicit controls

## Safety
Never place live trades based only on this research MVP. Verify data quality, transaction costs, execution assumptions, and out-of-sample performance independently.
