# Trading Strategy Lab

AI-assisted, multi-market strategy research and backtesting workspace.

> Research MVP only. No live order execution. Backtest results are hypothetical and do not imply future performance.

## MVP capabilities
- FastAPI REST API
- Deterministic OHLCV demo dataset (synthetic — results are NOT real performance)
- Binance spot OHLCV (public data, closed candles only): `GET /market-data/binance`, `POST /backtests` with `"data_source": "binance"`
- MT5 CSV export parser (`app/data_adapters/mt5_csv.py`)
- EMA crossover strategy (long/flat) and configurable fees/slippage
- Trade list, monthly returns, equity + drawdown curve
- Metrics: net return, max drawdown, recovery factor, win rate, profit factor, expectancy, avg win/loss, max consecutive losses, exposure, Sharpe
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

## Deploying on Vercel (two projects, one repo)
The API and dashboard are separate Vercel projects from this same repository.

1. **API** — *Add New → Project →* import `trading-strategy-lab`.
   Root Directory: repository root. Framework: FastAPI (auto-detected).
   `vercel.json` pins the function to `fra1` (Frankfurt).
   Optional env: `BINANCE_BASE_URL`.
2. **Dashboard** — import the same repo again.
   Root Directory: `web`. Framework: Next.js (auto-detected).
   Env: `API_URL` = the API project's URL from step 1, e.g. `https://my-api.vercel.app`.

## Data architecture
- Normalize all market bars to UTC OHLCV: timestamp, open, high, low, close, volume.
- Binance: optional CCXT adapter (public market data; exchange limits apply).
- MT5: run MetaTrader 5 on a Windows machine/VPS and export CSV or push bars to the API. The official MetaTrader5 Python package requires a supported Windows terminal environment; it is not part of the macOS container.
- Store bulk historical bars as Parquet; use PostgreSQL for users, experiments, metadata, and results when persistence is added.

## Backtesting assumptions (engine 0.2.0)
Trade-based, long/flat engine (`app/services/backtester.py`):
- Signals are evaluated at bar close; orders fill at the **next bar's open** (no look-ahead).
- Slippage is applied adversely to the fill price; fees are a % of notional on entry and exit.
- 100% of equity per trade, compounded, no leverage. Equity is marked to market every bar.
- A position open on the final bar is closed at the last close and flagged `forced_exit`.
- Win rate, profit factor, expectancy and consecutive losses are computed **per round-trip trade**.
- Sharpe is annualized from the request timeframe on a 24/7 calendar (crypto).
- Every response reports `data_source`, `synthetic_data` and a `data_quality` report.

This is still not a broker execution simulator. Intrabar stop/target, funding, swaps, contract multipliers, dividends, futures rolls, and market-specific calendars are not yet modeled.

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
