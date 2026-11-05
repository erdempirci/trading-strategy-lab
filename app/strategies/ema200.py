"""EMA200 trend strategy. Emits a candidate only; it never submits orders."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pandas as pd

from app.strategies.base import SignalCandidate, Strategy, infer_currency_exposures


class EMA200TrendStrategy(Strategy):
    strategy_id = "ema200_trend"
    version = "1.0.0"

    def __init__(self, atr_period: int = 14, reward_risk: float = 2.0):
        if atr_period < 2 or reward_risk <= 0:
            raise ValueError("atr_period must be >= 2 and reward_risk must be positive")
        self.atr_period = atr_period
        self.reward_risk = reward_risk

    def generate(self, instrument_id: str, symbol: str, timeframe: str, bars) -> list[SignalCandidate]:
        required = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required.issubset(bars.columns):
            raise ValueError(f"Missing columns: {sorted(required - set(bars.columns))}")
        data = bars.sort_values("timestamp").reset_index(drop=True)
        if len(data) < max(201, self.atr_period + 2):
            return []
        if data["timestamp"].duplicated().any():
            raise ValueError("Duplicate timestamps are not allowed")
        if "is_closed" in data.columns and not bool(data.iloc[-1]["is_closed"]):
            return []
        close = pd.to_numeric(data["close"], errors="coerce")
        high = pd.to_numeric(data["high"], errors="coerce")
        low = pd.to_numeric(data["low"], errors="coerce")
        if close.isna().any() or high.isna().any() or low.isna().any():
            raise ValueError("OHLC data must be numeric and complete")
        ema = close.ewm(span=200, adjust=False).mean()
        previous_close, last_close = float(close.iloc[-2]), float(close.iloc[-1])
        previous_ema, last_ema = float(ema.iloc[-2]), float(ema.iloc[-1])
        true_range = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ], axis=1).max(axis=1)
        atr = float(true_range.rolling(self.atr_period).mean().iloc[-1])
        if not pd.notna(atr) or atr <= 0:
            return []
        direction = "long" if previous_close <= previous_ema and last_close > last_ema else (
            "short" if previous_close >= previous_ema and last_close < last_ema else None
        )
        if direction is None:
            return []
        entry = last_close
        stop = entry - atr if direction == "long" else entry + atr
        target = entry + atr * self.reward_risk if direction == "long" else entry - atr * self.reward_risk
        stamp = pd.Timestamp(data.iloc[-1]["timestamp"]).to_pydatetime()
        if stamp.tzinfo is None:
            raise ValueError("bar timestamps must be timezone-aware")
        stamp = stamp.astimezone(timezone.utc)
        return [SignalCandidate(
            candidate_id=str(uuid4()), strategy_id=self.strategy_id, strategy_version=self.version,
            instrument_id=instrument_id, symbol=symbol, timeframe=timeframe, direction=direction,
            created_at=datetime.now(timezone.utc), signal_bar_close_time=stamp,
            expires_at=max(stamp + timedelta(hours=4), datetime.now(timezone.utc) + timedelta(hours=4)), entry_price=entry, stop_loss=stop,
            take_profit=target, regime_fit=0.0, signal_quality=0.0,
            data_quality_valid=False, evidence=["EMA200 close crossover", "ATR stop distance"],\n            currency_exposures=infer_currency_exposures(symbol),
        )]
