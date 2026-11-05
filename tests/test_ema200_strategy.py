import pandas as pd

from app.strategies.ema200 import EMA200TrendStrategy


def make_bars(closed=True):
    closes = [1.0] * 205 + [1.01, 1.02]
    return pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=len(closes), freq="1h", tz="UTC"),
        "open": closes, "high": [x + 0.002 for x in closes],
        "low": [x - 0.002 for x in closes], "close": closes,
        "volume": [100.0] * len(closes), "is_closed": [True] * (len(closes) - 1) + [closed],
    })


def test_ema200_emits_research_candidate_after_closed_bar_cross():
    candidates = EMA200TrendStrategy().generate("mt5:EURUSD", "EURUSD", "1h", make_bars())
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.direction == "long"
    assert candidate.stop_loss < candidate.entry_price < candidate.take_profit
    assert candidate.data_quality_valid is False  # must pass separate quality gate


def test_ema200_ignores_forming_bar():
    assert EMA200TrendStrategy().generate("mt5:EURUSD", "EURUSD", "1h", make_bars(False)) == []


def test_ema200_requires_warmup_history():
    assert EMA200TrendStrategy().generate(
        "mt5:EURUSD", "EURUSD", "1h", make_bars().head(100)
    ) == []
