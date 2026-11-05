from datetime import datetime, timezone

import pandas as pd
import pytest
from pydantic import ValidationError

from app.market_models import ContractSpec, Instrument, OHLCVBar, Quote
from app.services.data_quality import assess_ohlcv_quality


def sample_contract():
    return ContractSpec(
        tick_size=0.01,
        quote_currency="USDT",
        base_currency="BTC",
        quantity_step=0.001,
        min_quantity=0.001,
    )


def test_instrument_contract_schema():
    instrument = Instrument(
        instrument_id="binance:spot:BTCUSDT",
        venue="binance",
        symbol="BTC/USDT",
        asset_class="crypto",
        market_type="spot",
        contract=sample_contract(),
    )
    assert instrument.contract.tick_size == 0.01
    with pytest.raises(ValidationError):
        ContractSpec(
            tick_size=0.01, quote_currency="USDT", base_currency="BTC",
            min_quantity=2, max_quantity=1,
        )


def test_quote_normalizes_timezone_and_rejects_crossed_market():
    quote = Quote(
        instrument_id="binance:spot:BTCUSDT",
        bid=100, ask=101,
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    assert quote.timestamp.tzinfo == timezone.utc
    with pytest.raises(ValidationError):
        Quote(
            instrument_id="x", bid=101, ask=100,
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )


def test_bar_rejects_invalid_ohlc_and_naive_timestamp():
    with pytest.raises(ValidationError):
        OHLCVBar(
            instrument_id="x", timeframe="1h",
            timestamp=datetime(2026, 1, 1),
            open=100, high=99, low=98, close=99, volume=1,
        )


def test_quality_gate_detects_stale_and_invalid_data():
    now = datetime(2026, 1, 1, 3, tzinfo=timezone.utc)
    frame = pd.DataFrame([
        {"timestamp": "2026-01-01T00:00:00Z", "open": 100, "high": 102,
         "low": 99, "close": 101, "volume": 10},
        {"timestamp": "2026-01-01T01:00:00Z", "open": 101, "high": 100,
         "low": 98, "close": 99, "volume": -1},
    ])
    result = assess_ohlcv_quality(frame, "1h", now=now, max_age_bars=1)
    assert result["valid"] is False
    assert result["invalid_ohlc_bars"] == 1
    assert result["negative_volume_bars"] == 1
    assert result["stale"] is False


def test_quality_gate_rejects_empty_dataset():
    result = assess_ohlcv_quality(
        pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"]),
        "1h",
    )
    assert result["valid"] is False
    assert result["reason"] == "empty_dataset"
