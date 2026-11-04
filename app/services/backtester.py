import numpy as np
import pandas as pd


def _max_drawdown(equity: pd.Series) -> float:
    peaks = equity.cummax()
    drawdown = equity / peaks - 1.0
    return float(drawdown.min())


def run_ema_backtest(
    frame: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    initial_capital: float = 10_000,
    fee_bps: float = 5,
    slippage_bps: float = 2,
) -> dict:
    required = {"timestamp", "close"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Missing columns: {sorted(required - set(frame.columns))}")
    if fast_period >= slow_period:
        raise ValueError("fast_period must be less than slow_period")
    if initial_capital <= 0:
        raise ValueError("initial_capital must be positive")

    data = frame.copy().sort_values("timestamp").reset_index(drop=True)
    if data["close"].isna().any() or (data["close"] <= 0).any():
        raise ValueError("close prices must be positive and non-null")

    data["ema_fast"] = data["close"].ewm(span=fast_period, adjust=False).mean()
    data["ema_slow"] = data["close"].ewm(span=slow_period, adjust=False).mean()
    # A signal known at bar close is applied from the following bar onward.
    target_position = (data["ema_fast"] > data["ema_slow"]).astype(float).shift(1).fillna(0.0)
    market_returns = data["close"].pct_change().fillna(0.0)
    turnover = target_position.diff().abs().fillna(target_position.abs())
    cost_rate = (fee_bps + slippage_bps) / 10_000
    strategy_returns = target_position * market_returns - turnover * cost_rate
    equity = initial_capital * (1 + strategy_returns).cumprod()

    trade_mask = turnover > 0
    trade_returns = strategy_returns[trade_mask]
    gross_profit = float(trade_returns[trade_returns > 0].sum())
    gross_loss = float(-trade_returns[trade_returns < 0].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)
    std = float(strategy_returns.std(ddof=1))
    sharpe = float(np.sqrt(24 * 365) * strategy_returns.mean() / std) if std > 0 else 0.0

    return {
        "metrics": {
            "initial_capital": round(float(initial_capital), 2),
            "final_equity": round(float(equity.iloc[-1]), 2),
            "net_profit": round(float(equity.iloc[-1] - initial_capital), 2),
            "net_return_pct": round(float((equity.iloc[-1] / initial_capital - 1) * 100), 4),
            "max_drawdown_pct": round(_max_drawdown(equity) * 100, 4),
            "win_rate_pct": round(float((trade_returns > 0).mean() * 100), 2) if len(trade_returns) else 0.0,
            "profit_factor": round(float(profit_factor), 4) if np.isfinite(profit_factor) else None,
            "expectancy_per_position_change_pct": round(float(trade_returns.mean() * 100), 4) if len(trade_returns) else 0.0,
            "position_changes": int(trade_mask.sum()),
            "sharpe_annualized_24x365": round(sharpe, 4),
        },
        "equity_curve": [
            {"timestamp": ts.isoformat(), "equity": round(float(value), 2)}
            for ts, value in zip(data["timestamp"].iloc[::max(1, len(data)//100)], equity.iloc[::max(1, len(data)//100)])
        ],
    }
