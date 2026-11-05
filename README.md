# Trading Strategy Lab

AI-assisted, multi-market strategy research and autonomous paper-trading workspace.

> Current implementation is a research MVP. Autonomous live trading is not implemented or enabled. Backtest and paper results are hypothetical and do not imply future performance.

## Product target
- Markets: Forex, gold/commodities, indices, crypto.
- Selection: evaluate multiple strategy candidates and select the best eligible risk-adjusted opportunity at portfolio level.
- Monitoring: continuous scanning subject to each instrument's actual market calendar; no forced trades.
- Initial paper account: USD 100,000.
- AI providers: Claude and OpenAI behind provider-neutral adapters.
- Development: Mac Mini M4; long-running workers later on VPS. MT5 terminal gateway requires Windows.

## Current MVP capabilities
- FastAPI REST API
- Deterministic synthetic OHLCV demo dataset (not real market performance)
- Binance spot OHLCV public data
- MT5 CSV export parser
- EMA crossover backtesting with fees/slippage, trade list and performance metrics
- Docker Compose development environment
- Separate dashboard deployment path under web

See docs/architecture.md, docs/autonomous-trading-roadmap.md, docs/agent-contracts.md, and docs/forex-m1-m4-implementation.md.

## Quick start (Docker)
```bash
cp .env.example .env
docker compose up --build
```
Open http://localhost:8000/docs.

## Local development
Python 3.11+:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Current backtest limitations
The current engine is not yet a full multi-market broker simulator. Contract multipliers, instrument-specific sizing, full spread/session/swap/funding models, intrabar stop/target execution, portfolio margin, and paper order lifecycle are planned. Do not interpret synthetic demo data or simple backtests as evidence of a profitable live strategy.

## Safety
The current project has no live order execution. AI agents will not have direct order authority. A deterministic portfolio-wide risk governor must approve every paper order. Live trading requires a separate future security, reliability, validation and human approval gate.
