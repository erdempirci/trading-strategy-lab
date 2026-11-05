"""MACD signal-line crossover strategy; candidate generation only."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pandas as pd

from app.strategies.base import SignalCandidate, Strategy, infer_currency_exposures


class MACDMomentumStrategy(Strategy):
    strategy_id = "macd_momentum"
    version = "1.0.0"

    def __init__(self, fast: int = 12, slow: int = 26, signal_period: int = 9,
                 atr_period: int = 14, reward_risk: float = 2.0):
        if fast < 2 or slow <= fast or signal_period < 2 or atr_period < 2 or reward_risk <= 0:
            raise ValueError("Invalid MACD strategy parameters")
        self.fast, self.slow, self.signal_period = fast, slow, signal_period
        self.atr_period, self.reward_risk = atr_period, reward_risk

    def generate(self, instrument_id: str, symbol: str, timeframe: str, bars) -> list[SignalCandidate]:
        required = {"timestamp", "high", "low", "close"}
        if not required.issubset(bars.columns):
            raise ValueError(f"Missing columns: {sorted(required - set(bars.columns))}")
        data = bars.sort_values("timestamp").reset_index(drop=True)
        if len(data) < self.slow + self.signal_period + 2:
            return []
        if "is_closed" in data and not bool(data.iloc[-1]["is_closed"]):
            return []
        close = pd.to_numeric(data["close"], errors="coerce")
        macd = close.ewm(span=self.fast, adjust=False).mean() - close.ewm(span=self.slow, adjust=False).mean()
        signal = macd.ewm(span=self.signal_period, adjust=False).mean()
        direction = "long" if macd.iloc[-2] <= signal.iloc[-2] and macd.iloc[-1] > signal.iloc[-1] else (
            "short" if macd.iloc[-2] >= signal.iloc[-2] and macd.iloc[-1] < signal.iloc[-1] else None
        )
        if direction is None or close.isna().any():
            return []
        high, low = pd.to_numeric(data["high"]), pd.to_numeric(data["low"])
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        atr = float(tr.rolling(self.atr_period).mean().iloc[-1])
        if not pd.notna(atr) or atr <= 0:
            return []
        entry = float(close.iloc[-1])
        stop = entry - atr if direction == "long" else entry + atr
        target = entry + atr * self.reward_risk if direction == "long" else entry - atr * self.reward_risk
        stamp = pd.Timestamp(data.iloc[-1]["timestamp"]).to_pydatetime()
        if stamp.tzinfo is None:
            raise ValueError("bar timestamps must be timezone-aware")
        stamp = stamp.astimezone(timezone.utc)
        now = datetime.now(timezone.utc)
        return [SignalCandidate(
            candidate_id=str(uuid4()), strategy_id=self.strategy_id, strategy_version=self.version,
            instrument_id=instrument_id, symbol=symbol, timeframe=timeframe, direction=direction,
            created_at=now, signal_bar_close_time=stamp,
            expires_at=max(stamp + timedelta(hours=4), now + timedelta(hours=4)),
            entry_price=entry, stop_loss=stop, take_profit=target,
            evidence=[f"MACD({self.fast},{self.slow},{self.signal_period}) crossover", "ATR stop distance"],
            currency_exposures=infer_currency_exposures(symbol),
        )]
