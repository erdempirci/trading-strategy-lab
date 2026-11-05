"""Shared strategy contract and immutable signal candidate model."""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SignalCandidate(BaseModel):
    """A research signal, never an executable broker order."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str = Field(min_length=8, max_length=128)
    strategy_id: str = Field(min_length=2, max_length=64)
    strategy_version: str = Field(min_length=1, max_length=32)
    instrument_id: str = Field(min_length=2, max_length=64)
    symbol: str = Field(min_length=2, max_length=40)
    timeframe: str = Field(min_length=2, max_length=5)
    direction: Literal["long", "short"]
    created_at: datetime
    signal_bar_close_time: datetime
    expires_at: datetime
    entry_price: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)
    expected_value_r: float | None = None
    out_of_sample_trades: int = Field(default=0, ge=0)
    out_of_sample_expectancy_r: float | None = None
    out_of_sample_profit_factor: float | None = Field(default=None, ge=0)
    out_of_sample_max_drawdown_pct: float | None = Field(default=None, ge=0)
    regime_fit: float = Field(default=0, ge=0, le=1)
    signal_quality: float = Field(default=0, ge=0, le=1)
    estimated_cost_r: float = Field(default=0, ge=0)
    data_quality_valid: bool = False
    validation_id: str | None = None
    currency_exposures: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)

    @field_validator("created_at", "signal_bar_close_time", "expires_at")
    @classmethod
    def require_aware_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("candidate timestamps must be timezone-aware")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validate_trade_geometry(self):
        if not self.created_at <= self.signal_bar_close_time <= self.expires_at:
            raise ValueError("candidate timestamps are inconsistent")
        if self.direction == "long" and not self.stop_loss < self.entry_price < self.take_profit:
            raise ValueError("long candidate requires stop < entry < target")
        if self.direction == "short" and not self.take_profit < self.entry_price < self.stop_loss:
            raise ValueError("short candidate requires target < entry < stop")
        return self


class Strategy(ABC):
    strategy_id: str
    version: str

    @abstractmethod
    def generate(self, instrument_id: str, symbol: str, timeframe: str, bars) -> list[SignalCandidate]:
        """Generate candidates from validated, closed bars only."""
        raise NotImplementedError
