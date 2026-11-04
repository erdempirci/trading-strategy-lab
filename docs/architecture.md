# Architecture decisions

- Frontend and API are separate deployable services; MVP ships API only.
- Historical bars are normalized to UTC OHLCV.
- Bulk bars should live in Parquet/object storage; relational DB holds metadata and results.
- Strategies are versioned declarative specifications, not arbitrary model-generated code.
- Backtest jobs are isolated from API request workers as compute requirements grow.
- Every run records data source, data range, timeframe, parameters, costs, engine version, and assumptions.
- No live execution in the MVP.
