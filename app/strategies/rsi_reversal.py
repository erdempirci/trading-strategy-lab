"""RSI threshold reversal strategy; candidate generation only."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pandas as pd

from app.strategies.base import SignalCandidate, Strategy, infer_currency_exposures


class RSIReversalStrategy(Strategy):
    strategy_id = "rsi_reversal"
    version = "1.0.0"

    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70,
                 reward_risk: float = 2.0):
        if period < 2 or not 0 < oversold < overbought < 100 or reward_risk <= 0:
            raise ValueError("Invalid RSI strategy parameters")
        self.period, self.oversold, self.overbought = period, oversold, overbought
        self.reward_risk = reward_risk

    def generate(self, instrument_id: str, symbol: str, timeframe: str, bars) -> list[SignalCandidate]:
        if not {"timestamp", "high", "low", "close"}.issubset(bars.columns):
            raise ValueError("RSI strategy requires timestamp, high, low and close")
        data = bars.sort_values("timestamp").reset_index(drop=True)
        if len(data) < self.period + 2 or ("is_closed" in data and not bool(data.iloc[-1]["is_closed"])):
            return []
        close = pd.to_numeric(data["close"], errors="coerce")
        delta = close.diff()
        gain = delta.clip(lower=0).ewm(alpha=1 / self.period, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1 / self.period, adjust=False).mean()
        rs = gain / loss.replace(0, float("nan"))
        rsi = 100 - (100 / (1 + rs))
        previous, current = rsi.iloc[-2], rsi.iloc[-1]
        direction = "long" if previous < self.oversold <= current else (
            "short" if previous > self.overbought >= current else None
        )
        if direction is None or pd.isna(current):
            return []
        entry = float(close.iloc[-1])
        atr = float((pd.to_numeric(data["high"]) - pd.to_numeric(data["low"])).rolling(self.period).mean().iloc[-1])
        if not pd.notna(atr) or atr <= 0:
            return []
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
            evidence=[f"RSI({self.period}) threshold recross"],
            currency_exposures=infer_currency_exposures(symbol),
        )]
