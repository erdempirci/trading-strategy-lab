# Forex M1–M4 implementation notes

This branch adds the first Forex-oriented strategy and portfolio-control building blocks on top of the autonomous paper-trading architecture.

## Included

- Extended canonical contract metadata with profit currency, margin currency and price digits; corrected MarketSession time validation.
- Added an immutable SignalCandidate contract. Candidates are research outputs, not executable orders.
- Added deterministic EMA200 trend, RSI threshold-reversal and MACD crossover candidate generators. Each requires closed bars and emits stop/target references; candidates remain unvalidated until the separate data-quality and research gates approve them.
- Added evidence-gated opportunity ranking. It rejects stale/invalid, expired or insufficiently validated candidates and returns a ranking score that is explicitly not a win probability.
- Added a deterministic, fail-closed Risk Governor with paper-only enforcement, per-trade sizing, portfolio open-risk aggregation, daily/weekly loss, high-water-mark drawdown, spread, margin and kill-switch checks.
- Added chronological expanding walk-forward window generation to support out-of-sample research without shuffling time-series data.
- Added unit tests for candidate ranking, lot sizing, risk stops, signal generation and walk-forward windows.

## Forex sizing assumptions

ContractRiskSpec.tick_value_per_lot must be supplied in the account currency by a trusted broker/MT5 metadata adapter. The Risk Governor does not guess pip values or perform undocumented currency conversion. If tick value, spread, account state or contract metadata is missing, the candidate is rejected. Production integration must derive and reconcile contract values against the MT5 terminal before enabling demo execution.

## Not yet included / follow-up work

- Full multi-strategy portfolio selector wired to persisted strategy validation reports.
- RSI/MACD/EMA parameter walk-forward runner and Monte Carlo evaluation.
- Session-breakout, Bollinger, FVG and ATR-momentum strategies.
- Currency-factor exposure model using live portfolio conversion rates.
- Paper order lifecycle, durable event ledger and Windows MT5 gateway.
- End-to-end service/API wiring and live market data adapter for Forex.

## Safety

This branch does not add broker credentials or live order submission. AccountRiskState.live_enabled=True is rejected, and all new components are research/risk components only. The existing API continues to advertise live trading as disabled.
