"""Reusable OHLCV data-quality and freshness gate."""
from datetime import datetime, timedelta, timezone

import pandas as pd

from app.services.timeframes import timeframe_minutes


def assess_ohlcv_quality(
    frame: pd.DataFrame,
    timeframe: str,
    *,
    now: datetime | None = None,
    max_age_bars: int = 2,
) -> dict:
    """Return a fail-closed quality assessment for normalized OHLCV data.

    A forming candle must be removed by the provider adapter before this check.
    Freshness is measured from the latest candle open time plus one timeframe.
    """
    if max_age_bars < 0:
        raise ValueError("max_age_bars cannot be negative")
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")

    step = timedelta(minutes=timeframe_minutes(timeframe))
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    current = current.astimezone(timezone.utc)

    if frame.empty:
        return {
            "valid": False,
            "reason": "empty_dataset",
            "bars": 0,
            "stale": True,
            "age_seconds": None,
            "invalid_ohlc_bars": 0,
            "negative_volume_bars": 0,
            "duplicate_timestamps": 0,
        }

    data = frame.copy()
    timestamps = pd.to_datetime(data["timestamp"], utc=True)
    prices = data[["open", "high", "low", "close"]].apply(pd.to_numeric, errors="coerce")
    volume = pd.to_numeric(data["volume"], errors="coerce")
    invalid_ohlc = (
        prices.isna().any(axis=1)
        | (prices <= 0).any(axis=1)
        | (prices["high"] < prices[["open", "close", "low"]].max(axis=1))
        | (prices["low"] > prices[["open", "close", "high"]].min(axis=1))
    )
    negative_volume = volume.isna() | (volume < 0)
    duplicate_count = int(timestamps.duplicated().sum())
    latest_close_time = timestamps.max().to_pydatetime() + step
    age_seconds = max(0.0, (current - latest_close_time).total_seconds())
    stale = current - latest_close_time > step * max_age_bars

    problems = []
    if int(invalid_ohlc.sum()):
        problems.append("invalid_ohlc")
    if int(negative_volume.sum()):
        problems.append("negative_or_invalid_volume")
    if duplicate_count:
        problems.append("duplicate_timestamps")
    if stale:
        problems.append("stale_data")

    return {
        "valid": not problems,
        "reason": ",".join(problems) if problems else None,
        "bars": len(data),
        "stale": stale,
        "age_seconds": round(age_seconds, 3),
        "latest_bar_close": latest_close_time.isoformat(),
        "invalid_ohlc_bars": int(invalid_ohlc.sum()),
        "negative_volume_bars": int(negative_volume.sum()),
        "duplicate_timestamps": duplicate_count,
    }
