"""Deterministic fail-closed portfolio risk gate for paper trading only."""
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_DOWN
from typing import Literal

from app.strategies.base import SignalCandidate


@dataclass(frozen=True)
class RiskPolicy:
    risk_per_trade_pct: Decimal = Decimal("0.0025")
    max_open_risk_pct: Decimal = Decimal("0.0075")
    daily_loss_limit_pct: Decimal = Decimal("0.01")
    weekly_loss_limit_pct: Decimal = Decimal("0.025")
    max_drawdown_pct: Decimal = Decimal("0.05")
    max_margin_utilization_pct: Decimal = Decimal("0.50")
    max_open_positions: int = 3
    max_spread_to_stop_ratio: Decimal = Decimal("0.10")


@dataclass(frozen=True)
class OpenPositionRisk:
    symbol: str
    risk_amount: Decimal
    currency_exposures: tuple[str, ...] = ()


@dataclass(frozen=True)
class AccountRiskState:
    equity: Decimal
    high_water_mark: Decimal
    daily_pnl: Decimal = Decimal("0")
    weekly_pnl: Decimal = Decimal("0")
    used_margin: Decimal = Decimal("0")
    positions: tuple[OpenPositionRisk, ...] = ()
    connected: bool = True
    account_state_known: bool = True
    kill_switch_active: bool = False
    live_enabled: bool = False


@dataclass(frozen=True)
class ContractRiskSpec:
    tick_size: Decimal
    tick_value_per_lot: Decimal
    volume_step: Decimal
    min_volume: Decimal
    max_volume: Decimal


@dataclass(frozen=True)
class RiskDecision:
    status: Literal["APPROVED", "REJECTED", "NO_TRADE"]
    reason_codes: tuple[str, ...]
    risk_amount: Decimal = Decimal("0")
    volume_lots: Decimal = Decimal("0")
    projected_open_risk: Decimal = Decimal("0")


class RiskGovernor:
    def __init__(self, policy: RiskPolicy | None = None):
        self.policy = policy or RiskPolicy()

    def evaluate(self, candidate: SignalCandidate | None, account: AccountRiskState | None,
                 contract: ContractRiskSpec | None, *, spread: Decimal | None = None,
                 margin_required_per_lot: Decimal | None = None) -> RiskDecision:
        if candidate is None:
            return RiskDecision("NO_TRADE", ("no_candidate",))
        if account is None or contract is None:
            return RiskDecision("REJECTED", ("unknown_account_or_contract_state",))
        reasons = []
        if not account.connected or not account.account_state_known:
            reasons.append("account_or_broker_state_unknown")
        if account.kill_switch_active:
            reasons.append("kill_switch_active")
        if account.live_enabled:
            reasons.append("live_execution_forbidden_in_this_release")
        if not candidate.data_quality_valid:
            reasons.append("market_data_not_validated")
        if account.equity <= 0 or account.high_water_mark <= 0:
            reasons.append("invalid_equity_state")
        if contract.tick_size <= 0 or contract.tick_value_per_lot <= 0 or contract.volume_step <= 0:
            reasons.append("invalid_contract_spec")
        if reasons:
            return RiskDecision("REJECTED", tuple(reasons))

        equity = account.equity
        if account.daily_pnl <= -(equity * self.policy.daily_loss_limit_pct):
            reasons.append("daily_loss_limit_breached")
        if account.weekly_pnl <= -(equity * self.policy.weekly_loss_limit_pct):
            reasons.append("weekly_loss_limit_breached")
        if equity <= account.high_water_mark * (1 - self.policy.max_drawdown_pct):
            reasons.append("portfolio_drawdown_limit_breached")
        if len(account.positions) >= self.policy.max_open_positions:
            reasons.append("max_open_positions_reached")
        if account.used_margin >= equity * self.policy.max_margin_utilization_pct:
            reasons.append("margin_utilization_limit_reached")
        if reasons:
            return RiskDecision("REJECTED", tuple(reasons))

        stop_distance = abs(Decimal(str(candidate.entry_price)) - Decimal(str(candidate.stop_loss)))
        if stop_distance <= 0:
            return RiskDecision("REJECTED", ("invalid_stop_distance",))
        if spread is None or spread < 0:
            return RiskDecision("REJECTED", ("spread_unknown_or_invalid",))
        if spread / stop_distance > self.policy.max_spread_to_stop_ratio:
            return RiskDecision("REJECTED", ("spread_too_large_relative_to_stop",))

        risk_budget = equity * self.policy.risk_per_trade_pct
        existing_risk = sum((p.risk_amount for p in account.positions), Decimal("0"))
        max_open_risk = equity * self.policy.max_open_risk_pct
        remaining_open_risk = max_open_risk - existing_risk
        if remaining_open_risk <= 0:
            return RiskDecision("REJECTED", ("portfolio_open_risk_limit_reached",))
        risk_budget = min(risk_budget, remaining_open_risk)
        ticks = stop_distance / contract.tick_size
        loss_per_lot = ticks * contract.tick_value_per_lot
        if loss_per_lot <= 0:
            return RiskDecision("REJECTED", ("invalid_loss_per_lot",))
        raw_volume = risk_budget / loss_per_lot
        volume = (raw_volume / contract.volume_step).to_integral_value(rounding=ROUND_DOWN) * contract.volume_step
        if volume < contract.min_volume:
            return RiskDecision("REJECTED", ("risk_budget_below_minimum_volume",))
        if volume > contract.max_volume:
            volume = (contract.max_volume / contract.volume_step).to_integral_value(rounding=ROUND_DOWN) * contract.volume_step
        actual_risk = volume * loss_per_lot
        if actual_risk > risk_budget:
            return RiskDecision("REJECTED", ("rounded_volume_exceeds_risk_budget",))
        if margin_required_per_lot is not None:
            projected_margin = account.used_margin + volume * margin_required_per_lot
            if projected_margin > equity * self.policy.max_margin_utilization_pct:
                return RiskDecision("REJECTED", ("projected_margin_limit_exceeded",))
        projected_open_risk = existing_risk + actual_risk
        return RiskDecision("APPROVED", (), actual_risk, volume, projected_open_risk)
