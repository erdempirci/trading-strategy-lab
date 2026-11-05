# Trading Strategy Lab — Dashboard (Next.js)

Strategy parameters, metrics, candlestick chart with EMA lines and trade markers
(TradingView Lightweight Charts), equity + drawdown, monthly returns, trade list and an
in-session run comparison table.

In production the dashboard and API share one domain: `vercel.json` routes `/api/*`
to the FastAPI service. Locally, set `API_URL` so Next.js proxies `/api/*` to uvicorn.

## Local
```bash
uvicorn app.main:app --port 8000                       # repo root
cd web && npm install && API_URL=http://127.0.0.1:8000 npm run dev
```
