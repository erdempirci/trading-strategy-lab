from datetime import datetime, timedelta, timezone

from app.services.opportunity_ranker import rank_candidates, select_best_candidate
from app.strategies.base import SignalCandidate


def candidate(**overrides):
    now = datetime.now(timezone.utc)
    values = dict(
        candidate_id="candidate-0001", strategy_id="ema200_trend", strategy_version="1.0",
        instrument_id="mt5:EURUSD", symbol="EURUSD", timeframe="1h", direction="long",
        created_at=now, signal_bar_close_time=now, expires_at=now + timedelta(hours=1),
        entry_price=1.1, stop_loss=1.09, take_profit=1.12, out_of_sample_trades=100,
        out_of_sample_expectancy_r=0.2, out_of_sample_profit_factor=1.4,
        regime_fit=0.9, signal_quality=0.8, estimated_cost_r=0.1,
        data_quality_valid=True, validation_id="walkforward-001", currency_exposures=["EUR", "USD"],
    )
    values.update(overrides)
    return SignalCandidate(**values)


def test_ranker_selects_best_eligible_candidate():
    a = candidate(candidate_id="candidate-0001", regime_fit=0.7)
    b = candidate(candidate_id="candidate-0002", regime_fit=1.0)
    selected = select_best_candidate([a, b])
    assert selected is not None
    assert selected.candidate.candidate_id == "candidate-0002"


def test_ranker_rejects_missing_oos_validation_and_bad_data():
    result = rank_candidates([candidate(validation_id=None, data_quality_valid=False)])[0]
    assert result.eligible is False
    assert "invalid_or_unverified_data" in result.rejection_reasons
    assert "insufficient_out_of_sample_evidence" in result.rejection_reasons


def test_expired_candidate_is_ineligible():
    now = datetime.now(timezone.utc)
    item = candidate(expires_at=now - timedelta(seconds=1))
    assert rank_candidates([item], now=now)[0].eligible is False
