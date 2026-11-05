from decimal import Decimal
from datetime import datetime, timedelta, timezone

from app.services.risk_governor import (
    AccountRiskState, ContractRiskSpec, OpenPositionRisk, RiskGovernor,
)
from app.strategies.base import SignalCandidate


def candidate(**overrides):
    now = datetime.now(timezone.utc)
    values = dict(
        candidate_id="candidate-0001", strategy_id="ema200_trend", strategy_version="1.0",
        instrument_id="mt5:EURUSD", symbol="EURUSD", timeframe="1h", direction="long",
        created_at=now, signal_bar_close_time=now, expires_at=now + timedelta(hours=1),
        entry_price=1.1, stop_loss=1.09, take_profit=1.12, data_quality_valid=True,
    )
    values.update(overrides)
    return SignalCandidate(**values)


def account(**overrides):
    values = dict(equity=Decimal("100000"), high_water_mark=Decimal("100000"))
    values.update(overrides)
    return AccountRiskState(**values)


def contract(**overrides):
    values = dict(tick_size=Decimal("0.0001"), tick_value_per_lot=Decimal("10"),
                  volume_step=Decimal("0.01"), min_volume=Decimal("0.01"), max_volume=Decimal("100"))
    values.update(overrides)
    return ContractRiskSpec(**values)


def test_risk_sizes_trade_to_250_usd_budget():
    result = RiskGovernor().evaluate(candidate(), account(), contract(), spread=Decimal("0.0001"))
    assert result.status == "APPROVED"
    assert result.risk_amount == Decimal("250.00")
    assert result.volume_lots == Decimal("2.50")


def test_daily_loss_limit_fails_closed():
    result = RiskGovernor().evaluate(candidate(), account(daily_pnl=Decimal("-1000")), contract(),
                                     spread=Decimal("0.0001"))
    assert result.status == "REJECTED"
    assert "daily_loss_limit_breached" in result.reason_codes


def test_open_risk_is_aggregated_portfolio_wide():
    existing = OpenPositionRisk("GBPUSD", Decimal("600"), ("GBP", "USD"))
    result = RiskGovernor().evaluate(candidate(), account(positions=(existing,)), contract(),
                                     spread=Decimal("0.0001"))
    assert result.status == "REJECTED"
    assert "risk_budget_below_minimum_volume" not in result.reason_codes
    assert result.projected_open_risk <= Decimal("750")


def test_kill_switch_and_live_mode_are_rejected():
    assert RiskGovernor().evaluate(candidate(), account(kill_switch_active=True), contract(),
                                   spread=Decimal("0.0001")).status == "REJECTED"
    assert RiskGovernor().evaluate(candidate(), account(live_enabled=True), contract(),
                                   spread=Decimal("0.0001")).status == "REJECTED"


def test_missing_spread_or_contract_is_rejected():
    assert RiskGovernor().evaluate(candidate(), account(), contract(), spread=None).status == "REJECTED"
    assert RiskGovernor().evaluate(candidate(), account(), None, spread=Decimal("0.0001")).status == "REJECTED"
