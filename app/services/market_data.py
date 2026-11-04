import hashlib
import numpy as np
import pandas as pd


def demo_ohlcv(symbol: str = "BTC/USDT", timeframe: str = "1h", bars: int = 1000) -> pd.DataFrame:
    """Return deterministic synthetic OHLCV data; not real market prices."""
    if bars < 2:
        raise ValueError("bars must be at least 2")
    digest = hashlib.sha256(f"{symbol}:{timeframe}".encode()).digest()
    seed = int.from_bytes(digest[:4], "big")
    rng = np.random.default_rng(seed)
    drift = 0.00008
    returns = rng.normal(drift, 0.008, size=bars)
    close = 100 * np.exp(np.cumsum(returns))
    open_ = np.concatenate(([close[0]], close[:-1]))
    spread = np.abs(rng.normal(0.002, 0.001, size=bars))
    high = np.maximum(open_, close) * (1 + spread)
    low = np.minimum(open_, close) * (1 - spread)
    volume = rng.lognormal(mean=7, sigma=0.5, size=bars)
    timestamps = pd.date_range(end=pd.Timestamp.now(tz="UTC").floor("h"), periods=bars, freq="h")
    return pd.DataFrame({
        "timestamp": timestamps,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })
