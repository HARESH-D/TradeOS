# Requirements

## Current Build Functional Scope

- Angel One broker connection
- Manual broker sync
- Fetch broker profile, holdings, orders, trades, positions, and RMS limits
- Trading dashboard with key metrics, charts, sync status, and calendar-style P&L
- Analysis page with an Excel-like data grid
- Column filtering, sorting, searching, and date range filtering on the analysis grid
- Read-only data views in the first build; no order placement or automation
- Monthly and daily P&L foundation after brokerage, STT, GST, exchange charges, SEBI charges, and stamp duty

## Future Functional Scope

- Trade journal
- Rule and risk validation
- Strategy validator
- AI trade review and coaching
- Reports
- Replay mode
- Multi-broker support
- Order automation with risk guardrails

## Non-functional
- Modular
- Dockerized
- Production-ready
- Clean, dense, trading-workspace UI inspired by modern trading journal dashboards
- Broker credentials and tokens handled securely
- AI must never predict stock prices; it should reason over the user's historical data
