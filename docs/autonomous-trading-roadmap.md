# Autonomous Trading Roadmap & Engineering Backlog

## Locked product decisions
- Multi-strategy selection: evaluate candidates from multiple strategies and select the best eligible risk-adjusted opportunity at portfolio level.
- Starting simulated equity: USD 100,000.
- Monitoring: continuous scanning subject to each instrument's actual market calendar; no forced trades.
- Markets: Forex, gold/commodities, indices, crypto.
- Initial development: Mac Mini M4; later VPS. MT5 terminal gateway runs on Windows.
- AI providers: Claude and OpenAI through provider-neutral adapters.
- Initial operating mode: research + paper trading only. Live order execution is out of scope until a separate approval gate.

## Operating principles
- No-trade is a first-class decision; do not force a minimum number of trades.
- Strategy signals are deterministic and independently testable.
- AI provides bounded analysis and strategy-spec proposals; it does not generate executable code or submit orders.
- Candidate ranking is subordinate to hard portfolio risk checks.
- Risk is aggregated across strategies, symbols, accounts and venues.
- Every decision, rejection, order, fill and position update is auditable and replayable.
- No promotion based solely on in-sample returns.

## Initial paper portfolio policy
| Parameter | Initial value | Notes |
|---|---:|---|
| Starting equity | $100,000 | Simulated USD account |
| Risk per trade | 0.25% | $250 at initial equity |
| Daily loss stop | 1.0% | $1,000 at initial equity |
| Weekly loss stop | 2.5% | $2,500 at initial equity |
| Portfolio drawdown stop | 5.0% | From high-water mark |
| Live trading | Disabled | Separate future approval required |

These are provisional simulation defaults. Include realized and unrealized P&L, fees, spread, slippage, swaps/funding, and currency conversion. Limits must be enforced centrally, not separately per strategy.

## Delivery milestones

### M0 — Repository and quality baseline
- [ ] Verify current default branch, CI, tests, deployment configuration and dashboard/API split.
- [ ] Record exact current API endpoints and supported data sources.
- [ ] Add structured logging, correlation IDs and configuration validation.

### M1 — Multi-market instrument and data foundation
- [ ] Define canonical Instrument, Venue, MarketSession, ContractSpec, Quote, and OHLCVBar schemas.
- [ ] Normalize timestamps to UTC and reject duplicates, gaps beyond policy, invalid OHLC, negative volume and stale bars.
- [ ] Add instrument metadata adapters: tick size/value, contract multiplier, lot/quantity step, min/max quantity, min notional, fees, sessions and currency.
- [ ] Extend Binance adapter with pagination, rate-limit handling, retry/backoff, closed-candle policy and spot/derivatives capability flags.
- [ ] Harden MT5 CSV import with symbol metadata sidecar and validation.
- [ ] Design Windows MT5 gateway contract; do not run MetaTrader5 terminal integration in Mac/Linux containers.
- [ ] Add data freshness and provider health endpoints.

### M2 — Strategy framework and candidate generation
- [ ] Define versioned declarative strategy DSL and typed SignalCandidate.
- [ ] Define common strategy interface: warmup, required timeframes, instruments, parameters, signal generation and risk hints.
- [ ] Port EMA crossover into the interface; add EMA200 trend, RSI reversal, MACD, Bollinger breakout, session breakout and ATR momentum as independently tested strategies.
- [ ] Add long/short/flat support only after execution accounting is correct.
- [ ] Add multi-timeframe and market-regime tags.
- [ ] Prevent look-ahead bias and enforce closed-bar signals by default.

### M3 — Research-grade backtest and validation
- [ ] Add instrument-aware sizing and contract-aware P&L.
- [ ] Model spread, commissions, slippage, swaps, funding, tick/lot precision and trading sessions.
- [ ] Add intrabar stop/target simulation with explicit ambiguity policy and configurable fill model.
- [ ] Add portfolio-level simultaneous positions and shared cash/margin.
- [ ] Add out-of-sample split, walk-forward, parameter stability and Monte Carlo.
- [ ] Add benchmark comparisons and reproducibility reports.
- [ ] Persist data fingerprint, strategy version, engine version, assumptions and costs for every run.

### M4 — Candidate ranking and portfolio risk governor
- [ ] Define candidate score from out-of-sample expectancy, drawdown, stability, regime fit, cost sensitivity, freshness and diversification.
- [ ] Calibrate score weights only using validation data; score is not a probability of profit.
- [ ] Add portfolio exposure/correlation and currency-factor aggregation (especially USD exposure across FX, gold, indices and crypto).
- [ ] Implement central sizing: 0.25% initial risk budget per trade, subject to remaining portfolio limits.
- [ ] Enforce 1% daily, 2.5% weekly and 5% high-water-mark portfolio drawdown stops.
- [ ] Add max open risk, max instrument exposure, margin utilization and concurrent position limits.
- [ ] Fail closed on stale data, missing contract specs, broker state uncertainty or risk service failure.
- [ ] Return explicit APPROVED, REJECTED or NO_TRADE with reason codes.

### M5 — AI agent layer
- [ ] Define provider-neutral Claude/OpenAI adapters with timeouts, retries, token budgets and cost telemetry.
- [ ] Define bounded agent contracts: Market Regime, News Context, Strategy Research, Candidate Explanation and Post-Trade Review.
- [ ] Require strict JSON schema outputs and persist prompts/model/version/output for audit.
- [ ] Treat news/social content and model outputs as untrusted input; defend against prompt injection.
- [ ] AI may propose strategy DSL revisions but cannot execute code, change risk limits or send orders.
- [ ] Add deterministic fallback when AI is unavailable; system may continue approved deterministic strategies or abstain.

### M6 — Paper trading and execution simulation
- [ ] Build deterministic paper broker with lifecycle: intent, submitted, accepted, partially filled, filled, cancelled, rejected.
- [ ] Add idempotency keys, retry policy, reconciliation and duplicate-order prevention.
- [ ] Simulate spread, slippage, partial fills, latency, rejected orders and market closures.
- [ ] Add portfolio ledger for cash, positions, realized/unrealized P&L, fees and equity.
- [ ] Run 24/7 scheduler respecting each instrument's trading calendar and service health.
- [ ] Add global/per-venue kill switch and restart reconciliation.
- [ ] Start with $100,000 USD virtual equity and the risk defaults above.

### M7 — Dashboard and operations
- [ ] Command Center: equity, drawdown, exposure, agent/service status and market coverage.
- [ ] Market Scanner: instruments, timeframe, regime, freshness and candidate status.
- [ ] Strategy Lab: versions, tests, validation and ranking.
- [ ] AI Agents: bounded task logs, rationale and model cost.
- [ ] Positions/Orders: paper order lifecycle and trade journal.
- [ ] Risk Monitor: remaining daily/weekly/drawdown budgets and kill switches.
- [ ] Alerts for stale data, worker failures, risk stops and order reconciliation mismatches.
- [ ] Authentication, role-based access, secrets management, backups and audit log.

### M8 — Operational readiness review (not automatic live activation)
- [ ] Complete sustained paper-trading evaluation across different market regimes.
- [ ] Verify costs and fill assumptions against venue/broker observations.
- [ ] Review sample size, out-of-sample stability, tail loss, drawdown and operational incidents.
- [ ] Complete security review, disaster recovery, kill-switch drills and reconciliation tests.
- [ ] Require explicit human approval and separate deployment/configuration change before any live trading capability is enabled.

## First implementation sprint
1. Add canonical instrument and market data schemas.
2. Add market-data quality/freshness service.
3. Wrap existing EMA crossover in a strategy interface.
4. Add SignalCandidate and NO_TRADE response models.
5. Add paper account and portfolio ledger with $100,000 initial equity.
6. Implement central risk governor and unit tests for every hard limit.
7. Add end-to-end test: Binance historical bars -> EMA candidate -> portfolio selector -> risk approval/rejection -> paper fill -> ledger update.

## Definition of done for first autonomous paper loop
- Scans supported markets without assuming every instrument is always open.
- Never uses incomplete candles unless explicitly configured.
- Produces candidates with reproducible inputs and strategy version.
- Selects only eligible candidates and may choose NO_TRADE.
- Enforces portfolio-wide limits before any paper order.
- Prevents duplicate orders and reconciles order/position state.
- Records all events and can replay a complete decision.
- Starts with $100,000 virtual equity; no real funds or live orders are used.
