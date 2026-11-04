# Data adapters

Adapters must return normalized UTC OHLCV columns:
`timestamp, open, high, low, close, volume`.

## Binance / CCXT
Planned: implement an async/sync CCXT adapter with symbol mapping, pagination,
rate-limit handling, retries, and explicit exchange/source metadata.

## MetaTrader 5
Run the MetaTrader 5 terminal and its Python package on Windows. Export broker
bars to CSV or push them to a secured ingestion endpoint. The Mac/Docker MVP
does not embed the Windows-only terminal integration.
