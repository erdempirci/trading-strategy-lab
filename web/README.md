# Trading Strategy Lab — Dashboard (Next.js)

Strategy parameters, metrics, candlestick chart with EMA lines and trade markers
(TradingView Lightweight Charts), equity + drawdown, monthly returns, trade list and an
in-session run comparison table.

The browser only talks to this app. `/api/*` is proxied server-side to the FastAPI
service (see `next.config.ts`), so no CORS setup is needed.

| Env var   | Default                                         | Purpose                     |
|-----------|-------------------------------------------------|-----------------------------|
| `API_URL` | `https://trading-strategy-lab-omega.vercel.app` | FastAPI base URL (no slash) |

`API_URL` is read at build time — redeploy after changing it.

## Local
```bash
cd web
npm install
API_URL=http://127.0.0.1:8000 npm run dev   # API: uvicorn app.main:app --port 8000
```
