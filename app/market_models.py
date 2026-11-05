"""Canonical market-domain models shared by data and strategy services.

All timestamps are timezone-aware UTC. These models describe market metadata and
observations; they do not contain broker credentials or execution commands.
"""
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MarketSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weekday: int = Field(ge=0, le=6, description="Monday=0, Sunday=6")
    open_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    close_time: str = Field(pattern=r"^([01]\\d|2[0-3]):[0-5]\\d$")
    timezone: str = "UTC"


class ContractSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_size: float = Field(default=1.0, gt=0)
    tick_size: float = Field(gt=0)
    tick_value: float | None = Field(default=None, gt=0)
    quantity_step: float = Field(default=1.0, gt=0)
    min_quantity: float = Field(default=0.0, ge=0)
    max_quantity: float | None = Field(default=None, gt=0)
    min_notional: float | None = Field(default=None, gt=0)
    quote_currency: str = Field(min_length=2, max_length=12)
    base_currency: str = Field(min_length=2, max_length=12)
    maker_fee_rate: float = Field(default=0.0, ge=0, le=1)
    taker_fee_rate: float = Field(default=0.0, ge=0, le=1)
    swap_long: float | None = None
    swap_short: float | None = None
    profit_currency: str | None = Field(default=None, min_length=2, max_length=12)
    margin_currency: str | None = Field(default=None, min_length=2, max_length=12)
    digits: int | None = Field(default=None, ge=0, le=12)

    @model_validator(mode="after")
    def validate_quantity_bounds(self):
        if self.max_quantity is not None and self.max_quantity < self.min_quantity:
            raise ValueError("max_quantity must be greater than or equal to min_quantity")
        return self


class Instrument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instrument_id: str = Field(min_length=2, max_length=64)
    venue: str = Field(min_length=2, max_length=32)
    symbol: str = Field(min_length=2, max_length=40)
    asset_class: Literal["forex", "commodity", "index", "crypto"]
    market_type: Literal["spot", "perpetual", "futures", "cfd", "cash_index"]
    active: bool = True
    trading_timezone: str = "UTC"
    sessions: list[MarketSession] = Field(default_factory=list)
    contract: ContractSpec


class Quote(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instrument_id: str
    bid: float = Field(gt=0)
    ask: float = Field(gt=0)
    timestamp: datetime

    @field_validator("timestamp")
    @classmethod
    def timestamp_is_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must include timezone information")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def ask_not_below_bid(self):
        if self.ask < self.bid:
            raise ValueError("ask must be greater than or equal to bid")
        return self


class OHLCVBar(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instrument_id: str
    timeframe: str
    timestamp: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)
    is_closed: bool = True

    @field_validator("timestamp")
    @classmethod
    def timestamp_is_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must include timezone information")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def valid_ohlc_range(self):
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must be the greatest OHLC price")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be the lowest OHLC price")
        return self
