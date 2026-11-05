from fastapi import FastAPI, HTTPException

from app.data_adapters.binance import BinanceDataError, fetch_binance_ohlcv
from app.data_adapters.normalize import quality_report
from app.schemas import BacktestRequest
from app.services.backtester import run_ema_backtest
from app.services.market_data import demo_ohlcv

ENGINE_VERSION = "0.2.0"

app = FastAPI(
    title="Trading Strategy Lab API",
    version=ENGINE_VERSION,
    description="Research-only strategy backtesting API. Live trading is disabled.",
)


def _load_frame(source: str, symbol: str, timeframe: str, bars: int):
    try:
        if source == "binance":
            return fetch_binance_ohlcv(symbol, timeframe, bars), "binance_spot"
        return demo_ohlcv(symbol=symbol, timeframe=timeframe, bars=bars), "deterministic_demo"
    except BinanceDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "Trading Strategy Lab",
        "status": "running",
        "message": "API is online. Open /docs to use the API.",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "trading-strategy-lab", "engine_version": ENGINE_VERSION}


@app.get("/market-data/demo")
def get_demo_data(symbol: str = "BTC/USDT", timeframe: str = "1h", bars: int = 500) -> dict:
    if bars < 50 or bars > 5000:
        raise HTTPException(status_code=400, detail="bars must be between 50 and 5000")
    frame, source = _load_frame("demo", symbol, timeframe, bars)
    return {"symbol": symbol, "timeframe": timeframe, "source": source, "bars": len(frame),
            "data": frame.tail(10).to_dict(orient="records")}


@app.get("/market-data/binance")
def get_binance_data(symbol: str = "BTC/USDT", timeframe: str = "1h", bars: int = 500) -> dict:
    if bars < 1 or bars > 5000:
        raise HTTPException(status_code=400, detail="bars must be between 1 and 5000")
    frame, source = _load_frame("binance", symbol, timeframe, bars)
    return {"symbol": symbol, "timeframe": timeframe, "source": source,
            "quality": quality_report(frame, timeframe),
            "data": frame.tail(10).to_dict(orient="records")}


@app.post("/backtests")
def create_backtest(request: BacktestRequest) -> dict:
    if request.strategy != "ema_crossover":
        raise HTTPException(status_code=400, detail="Only ema_crossover is available in MVP")

    frame, source = _load_frame(request.data_source, request.symbol, request.timeframe,
                                request.bars)
    try:
        result = run_ema_backtest(
            frame=frame,
            fast_period=request.fast_period,
            slow_period=request.slow_period,
            initial_capital=request.initial_capital,
            fee_bps=request.fee_bps,
            slippage_bps=request.slippage_bps,
            timeframe=request.timeframe,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not request.include_trades:
        result.pop("trades")

    return {
        "symbol": request.symbol,
        "timeframe": request.timeframe,
        "strategy": request.strategy,
        "parameters": {"fast_period": request.fast_period, "slow_period": request.slow_period},
        "data_source": source,
        "synthetic_data": source == "deterministic_demo",
        "data_quality": quality_report(frame, request.timeframe),
        "engine_version": ENGINE_VERSION,
        "assumptions": {
            "signal": "evaluated at bar close",
            "execution": "next_bar_open",
            "position": "long_or_flat, 100% equity, no leverage",
            "fees": "fee_bps of notional on entry and exit",
            "slippage": "slippage_bps adverse to fill price",
            "open_position_at_end": "closed at last close, flagged forced_exit",
            "sharpe_annualization": "24/7 market calendar",
            "live_trading": False,
        },
        **result,
    }
