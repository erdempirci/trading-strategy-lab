import pandas as pd
from app.services.backtester import run_ema_backtest
from app.services.market_data import demo_ohlcv


def test_demo_data_is_deterministic_except_timestamp():
    a = demo_ohlcv("BTC/USDT", "1h", 120)
    b = demo_ohlcv("BTC/USDT", "1h", 120)
    pd.testing.assert_series_equal(a["close"], b["close"])


def test_backtest_returns_core_metrics():
    frame = demo_ohlcv(bars=200)
    result = run_ema_backtest(frame)
    metrics = result["metrics"]
    assert "net_return_pct" in metrics
    assert "max_drawdown_pct" in metrics
    assert metrics["position_changes"] >= 0
    assert len(result["equity_curve"]) > 0
