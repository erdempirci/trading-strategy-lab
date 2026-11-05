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
        currency_exposures=["EUR", "USD"],
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


def evaluate(candidate_value=None, account_value=None, contract_value=None, **kwargs):
    return RiskGovernor().evaluate(
        candidate_value or candidate(), account_value or account(), contract_value or contract(),
        spread=Decimal("0.0001"), margin_required_per_lot=Decimal("1000"), **kwargs,
    )


def test_risk_sizes_trade_to_250_usd_budget():
    result = evaluate()
    assert result.status == "APPROVED"
    assert result.risk_amount == Decimal("250.00")
    assert result.volume_lots == Decimal("0.25")


def test_daily_loss_limit_fails_closed():
    result = evaluate(account_value=account(daily_pnl=Decimal("-1000")))
    assert result.status == "REJECTED"
    assert "daily_loss_limit_breached" in result.reason_codes


def test_open_risk_and_currency_factor_are_aggregated():
    existing = OpenPositionRisk("GBPUSD", Decimal("300"), ("GBP", "USD"))
    result = evaluate(account_value=account(positions=(existing,)))
    assert result.status == "APPROVED"
    assert result.projected_open_risk == Decimal("500")
    assert result.risk_amount == Decimal("200.00")


def test_kill_switch_and_live_mode_are_rejected():
    assert evaluate(account_value=account(kill_switch_active=True)).status == "REJECTED"
    assert evaluate(account_value=account(live_enabled=True)).status == "REJECTED"


def test_missing_spread_contract_or_margin_is_rejected():
    assert RiskGovernor().evaluate(candidate(), account(), contract(), spread=None,
                                   margin_required_per_lot=Decimal("1000")).status == "REJECTED"
    assert RiskGovernor().evaluate(candidate(), account(), None, spread=Decimal("0.0001"),
                                   margin_required_per_lot=Decimal("1000")).status == "REJECTED"
    assert RiskGovernor().evaluate(candidate(), account(), contract(), spread=Decimal("0.0001"),
                                   margin_required_per_lot=None).status == "REJECTED"


def test_currency_factor_cap_rejects_excess_concentration():
    existing = OpenPositionRisk("GBPUSD", Decimal("500"), ("GBP", "USD"))
    result = evaluate(account_value=account(positions=(existing,)))
    assert result.status == "REJECTED"
    assert "currency_factor_risk_limit_reached" in result.reason_codes
