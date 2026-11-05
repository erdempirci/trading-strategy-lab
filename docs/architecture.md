# Architecture decisions

## Product direction
Trading Strategy Lab is evolving from a research/backtesting MVP into a multi-market autonomous trading research and paper-trading platform.

Locked user decisions:
- Strategy selection: run multiple independent strategies and let a portfolio-level selector choose the best eligible risk-adjusted opportunity.
- Initial simulated portfolio: USD 100,000.
- Monitoring: continuous 24/7 market monitoring subject to each instrument's actual market calendar; no forced trades.
- Markets: Forex, gold/commodities, indices, crypto.
- Initial integrations: Binance public market data and MT5 CSV; later MT5 Windows gateway and broker/exchange paper execution.
- AI providers: Claude and OpenAI through provider adapters.

## High-level architecture
1. **Market data plane**: provider adapters ingest bars/ticks, normalize timestamps to UTC, validate quality, track freshness, and expose instrument metadata. Crypto uses Binance/CCXT. MT5 data arrives through CSV initially; a Windows gateway is a later milestone.
2. **Strategy plane**: versioned deterministic strategy implementations consume normalized market data and emit typed signal candidates. Strategies do not submit orders.
3. **Research and selection plane**: candidate evaluator scores signals using out-of-sample strategy evidence, regime fit, expected value after costs, signal freshness, and portfolio diversification. The selector ranks candidates but cannot override hard risk rules.
4. **AI agent plane**: AI agents summarize market context, classify regimes, explain candidate signals, and propose strategy specifications using a validated JSON DSL. AI output is advisory and schema-validated; no arbitrary generated code execution.
5. **Risk governor**: deterministic, independent pre-trade and portfolio-level gate. It enforces account limits, instrument limits, correlated exposure, leverage/margin constraints, trading sessions, data freshness, and kill-switch state. Risk rules are not editable by agents.
6. **Execution plane**: paper broker first; later venue-specific adapters. Order intents are idempotent, stateful, auditable, and reconciled against broker/exchange state.
7. **Observability and learning**: immutable signal/decision/order/trade events, metrics, alerts, replay, and post-trade analysis. Learning proposes candidate versions; promotion requires independent validation and policy gates.

## Decision and execution flow
Market data -> normalization/quality gate -> strategy signals -> candidate scoring/ranking -> portfolio risk simulation -> risk approval/rejection -> paper execution -> order reconciliation -> trade journal/performance.

A NO_TRADE outcome is valid and expected. The system must not trade merely to remain active.

## Initial paper portfolio and risk policy
Initial paper equity: USD 100,000.

Provisional conservative defaults for simulation only:
- Risk per trade: 0.25% of current equity (USD 250 at initial equity).
- Daily loss stop: 1.0% (USD 1,000 at initial equity).
- Weekly loss stop: 2.5% (USD 2,500 at initial equity).
- Portfolio drawdown hard stop: 5.0% from configured high-water mark (USD 5,000 at initial equity).
- Risk limits aggregate across all strategies and venues; correlated exposures are not independent.
- Include open/unrealized P&L, commissions, spread, slippage, swaps/funding and currency conversion.
- Stop opening positions on stale/invalid data, uncertain order state, broker disconnect, breached limits, or active kill switch.
These are engineering defaults for paper testing, not return targets or a live-trading recommendation.

## Market-specific constraints
- **Forex / gold / indices**: MT5/broker symbol metadata is authoritative for contract size, tick size/value, volume step, min/max volume, sessions, margin, swaps, and execution mode. MT5 Python terminal integration runs on a supported Windows host, not inside the Mac/Linux API container.
- **Crypto**: Binance/CCXT adapter must distinguish spot vs derivatives. Do not enable derivatives, leverage, margin, or withdrawals by default. Respect exchange precision, min notional, rate limits, fees, funding and maintenance windows.
- Never assume all symbols share a common pip, lot, contract multiplier, session calendar, or fee model.

## Service boundaries
- API: control plane and read APIs; not a long-running trading loop.
- Market-data workers: ingestion, normalization and freshness monitoring.
- Strategy workers: deterministic signal generation and replay.
- Research workers: backtests, optimization, walk-forward and Monte Carlo.
- Agent workers: bounded AI calls with typed inputs/outputs, budgets and timeouts.
- Risk service: deterministic gate; fail closed.
- Execution service: paper execution first; later venue adapters.
- Database: PostgreSQL for metadata, state and event ledger; Parquet/DuckDB for historical analytics.
- Frontend: dashboard/control plane; dangerous controls authenticated and audited.

## Deployment
- Mac Mini M4 is the initial development workstation.
- Vercel may host the Next.js dashboard and lightweight API/control endpoints.
- Long-running workers, streaming connections, schedulers and future MT5 gateway belong on a VPS or dedicated host.
- MT5 terminal gateway must run on Windows.
- Docker Compose is the local orchestration baseline.

## Safety and reliability invariants
1. Research/backtest code cannot place orders.
2. AI agents cannot call broker/exchange order APIs directly.
3. Only execution service can submit an approved, risk-signed order intent.
4. Risk governor fails closed if data, account state, limits, or order state are unknown.
5. Every order intent has a unique idempotency key and complete audit trail.
6. Live execution remains disabled until separate explicit enablement, extensive paper evidence, operational controls and human approval.
7. No strategy is promoted based on in-sample performance alone.
8. A strategy cannot change its own risk budget or global risk limits.
9. Global and per-venue kill switches plus restart reconciliation are mandatory.

## Current repository reality
Existing MVP includes FastAPI, deterministic demo data, Binance public OHLCV, MT5 CSV parsing, EMA crossover backtesting, trade/curve metrics, tests, Docker, and a separate web dashboard deployment path. These are retained. Autonomous agents, portfolio selection, paper execution, persistent event ledger, MT5 gateway, and live execution are planned work, not implemented features.
