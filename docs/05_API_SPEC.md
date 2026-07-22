# API Spec

## Current Build APIs

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/broker`
- `POST /api/broker/connect`
- `POST /api/broker/sync`
- `POST /api/broker/tradebook/import`
- `GET /api/broker/sync/history`
- `GET /api/dashboard`
- `GET /api/analysis`
- `GET /api/agent/status`
- `GET /api/agent/runs`
- `POST /api/agent/runs`
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
- Tradebook import accepts an authenticated multipart upload named `file`. It supports Angel One equity tradebook `.xlsx` files up to 4 MB, including exports with incorrect worksheet dimension metadata.
- Executions are immutable and deduplicated by broker account plus `exchange:segment:trade_date:trade_id`. Order ID is not a deduplication key because one order can contain multiple fills.
- Re-importing the same cumulative tradebook adds zero executions. A later cumulative or date-sliced upload preserves history and adds only unseen execution identities.
- Long equity executions are matched FIFO by ISIN. A sell date becomes the realized date; entry and exit timestamps are retained. Remaining buy lots are aggregated into weighted open positions for analysis, while sells without earlier buys remain flagged as unmatched rather than receiving an invented cost basis.
- Tradebook-derived gross and net P&L currently exclude broker charges because the export does not provide them.
- Dashboard APIs return summarized metrics and chart/calendar data.
- Analysis grid APIs return paginated, sortable, filterable trading records.
- Broker PIN/password and TOTP are accepted only during connect and must not be persisted or logged.
- Agent status reports provider readiness without exposing keys.
- Agent run history is authenticated and scoped to the current user.
- `POST /api/agent/runs` accepts Gemini for public research and local Llama for trade review or portfolio analysis.
- Llama analysis receives a compact, user-scoped context calculated by TradeOS. It does not receive broker credentials and does not perform financial arithmetic.
- Gemini cannot receive trade or portfolio modes, and Llama cannot receive research mode; unsupported pairs return `409`.
- Missing Gemini configuration returns `503`; provider and quota failures return `502`. Failed attempts remain visible in run history for audit.
- An offline or missing local Ollama model returns `503`. Invalid or incomplete structured model output returns `502` and remains auditable.
- Completed runs return the answer and model. Research additionally returns search queries and HTTPS citation records.

The current sync endpoint completes inline and returns `200`. The production target is `POST /api/v1/broker-accounts/{account_id}/sync-runs`, returning `202` with an asynchronous run ID and idempotency key behavior.

Detailed request, response, error, filtering, and pagination contracts are documented in [22_LOW_LEVEL_DESIGN.md](22_LOW_LEVEL_DESIGN.md).
