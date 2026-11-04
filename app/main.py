from fastapi import FastAPI, HTTPException
from app.schemas import BacktestRequest
from app.services.market_data import demo_ohlcv
from app.services.backtester import run_ema_backtest

app = FastAPI(
    title="Trading Strategy Lab API",
    version="0.1.0",
    description="Research-only strategy backtesting API. Live trading is disabled.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "trading-strategy-lab"}


@app.get("/market-data/demo")
def get_demo_data(
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    bars: int = 500,
) -> dict:
    if bars < 50 or bars > 5000:
        raise HTTPException(status_code=400, detail="bars must be between 50 and 5000")
    frame = demo_ohlcv(symbol=symbol, timeframe=timeframe, bars=bars)
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "source": "deterministic_demo",
        "bars": len(frame),
        "data": frame.tail(10).to_dict(orient="records"),
    }


@app.post("/backtests")
def create_backtest(request: BacktestRequest) -> dict:
    if request.strategy != "ema_crossover":
        raise HTTPException(status_code=400, detail="Only ema_crossover is available in MVP")
    if request.fast_period >= request.slow_period:
        raise HTTPException(status_code=400, detail="fast_period must be less than slow_period")

    frame = demo_ohlcv(
        symbol=request.symbol,
        timeframe=request.timeframe,
        bars=request.bars,
    )
    try:
        result = run_ema_backtest(
            frame=frame,
            fast_period=request.fast_period,
            slow_period=request.slow_period,
            initial_capital=request.initial_capital,
            fee_bps=request.fee_bps,
            slippage_bps=request.slippage_bps,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "symbol": request.symbol,
        "timeframe": request.timeframe,
        "strategy": request.strategy,
        "data_source": "deterministic_demo",
        "assumptions": {
            "execution": "next_bar_close",
            "position": "long_or_flat",
            "fees": "charged on position changes",
            "slippage": "charged on position changes",
            "live_trading": False,
        },
        **result,
    }
