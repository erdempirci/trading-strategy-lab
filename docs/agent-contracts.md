# Agent Contracts and Authority Boundaries

## Core rule
AI agents are analysis and research components, not execution authorities. They cannot access broker credentials, call order endpoints, alter risk policy, or execute generated code.

## Agent responsibilities
| Agent | Inputs | Allowed output |
|---|---|---|
| Market Regime | Validated OHLCV, instrument/session metadata | Regime label, volatility state, evidence |
| Technical Analyst | Closed bars, indicator features | Technical observations, candidate annotations |
| News Context | Timestamped news feed snippets | Event summary, source references, uncertainty |
| Strategy Research | Strategy DSL, validation reports | Proposed DSL parameters/variants |
| Candidate Explainer | SignalCandidate and score breakdown | Concise rationale and caveats |
| Post-Trade Review | Immutable trade/event record | Classification and review notes |

## Typed candidate contract (conceptual)
A candidate should contain:
- candidate_id, strategy_id, strategy_version
- venue, instrument_id, timeframe, direction
- created_at, signal_bar_close_time, expires_at
- entry_type, optional entry reference, stop and target proposal
- evidence and feature snapshot references
- backtest_validation_id
- estimated_costs, expected_value_after_costs
- regime_tags and data_quality_status

Prices and quantities must be decimal-safe and instrument-aware. A candidate is not an order.

## Candidate selection
1. Reject stale, malformed, expired or unvalidated candidates.
2. Check instrument session and venue availability.
3. Compare validation evidence and expected value after costs.
4. Consider correlation, currency factors, existing positions and remaining risk budget.
5. Choose the best eligible candidate or emit NO_TRADE.

The ranking score is a research prioritization mechanism, not a calibrated probability of profit.

## Risk governor authority
The risk governor is deterministic and fail-closed. It alone can approve or reject a candidate for paper execution. It validates account and venue health, data freshness and contract metadata, current/projected portfolio exposure, per-trade/daily/weekly/high-water-mark drawdown limits, margin and position limits, trading calendar, instrument constraints and kill-switch state.

The AI cannot override a rejection.

## Execution authority
Only the execution service accepts a risk-approved order intent. It must enforce unique idempotency keys, persist intent before submission, manage order lifecycle and partial fills, reconcile against paper broker state, record every transition and fail closed when state is ambiguous.

Live execution is disabled by design in this project phase.
