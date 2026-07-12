# API Spec

## Current Build APIs

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/broker`
- `POST /api/broker/connect`
- `POST /api/broker/sync`
- `POST /api/broker/statement/import`
- `GET /api/broker/sync/history`
- `GET /api/dashboard`
- `GET /api/analysis`
- `GET /health`

## Planned APIs

- `/portfolio`
- `/orders`
- `/trades`
- `/journal`
- `/rules`
- `/ai/review`
- `/reports`
- `/replay`

## Current Build Behavior

- Broker APIs are read-only.
- Manual sync is user-triggered.
- Statement import accepts an authenticated multipart upload named `file`. It supports Angel One equity P&L `.xlsx` files up to 4 MB.
- Re-importing a statement replaces the user's previous statement-derived trades, while preserving a sync-history entry for each import.
- P&L statements aggregate by symbol and omit individual execution dates. Imported rows therefore use the statement period end date and expose that choice as `date_basis: statement_period_end`.
- Dashboard APIs return summarized metrics and chart/calendar data.
- Analysis grid APIs return paginated, sortable, filterable trading records.
- Broker PIN/password and TOTP are accepted only during connect and must not be persisted or logged.

The current sync endpoint completes inline and returns `200`. The production target is `POST /api/v1/broker-accounts/{account_id}/sync-runs`, returning `202` with an asynchronous run ID and idempotency key behavior.

Detailed request, response, error, filtering, and pagination contracts are documented in [22_LOW_LEVEL_DESIGN.md](22_LOW_LEVEL_DESIGN.md).
