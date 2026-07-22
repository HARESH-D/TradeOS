# Vercel POC Deployment

## Purpose

This runbook is the current zero-cost proof-of-concept topology:

```text
Browser -> Vercel Vite frontend -> Vercel FastAPI function -> managed PostgreSQL
```

It supports authentication, dashboard analytics, the analysis grid, demo sync and Angel One equity tradebook upload. It is not the final live-broker topology because Vercel Hobby does not provide a dedicated outbound IPv4.

## Projects

- Frontend root directory: `frontend`
- Backend root directory: `backend`
- Preferred backend region: Singapore (`sin1`)
- Database: Vercel-managed PostgreSQL integration

The backend uses `backend/index.py` as its FastAPI entrypoint. The database URL accepts both `postgres://` and `postgresql://` provider formats and is normalized to the psycopg 3 SQLAlchemy driver.

## Backend Environment

Configure these values in the backend Vercel project:

```text
DATABASE_URL=<managed PostgreSQL connection string>
JWT_SECRET=<random secret>
ENCRYPTION_KEY=<Fernet key>
CORS_ORIGINS=https://<frontend-host>
FRONTEND_URL=https://<frontend-host>
ALLOWED_HOSTS=<backend-host>
SEED_DEMO=false
GEMINI_API_KEY=<Google AI Studio key>
GEMINI_MODEL=gemini-2.5-flash
AGENT_REQUEST_TIMEOUT_SECONDS=90
```

Never commit these values. Broker PIN and TOTP remain ephemeral and must not be stored or logged.

`GEMINI_API_KEY` is optional for the trading dashboard but required for AI research. Configure it only on the backend project. The status API reveals whether it exists but never returns the key.

## Frontend Environment

Configure the production frontend project with:

```text
VITE_API_URL=https://<backend-host>/api
```

Redeploy the frontend after changing the value because Vite embeds it at build time.

## Verification

1. Confirm `GET https://<backend-host>/health` returns `status: ok`.
2. Register a new user from the frontend.
3. Open Broker and upload an Angel One equity tradebook `.xlsx` file.
4. Confirm the import summary and sync-history record appear.
5. Confirm dashboard and analysis rows use the execution entry and exit dates and contain only that user's imported data.
6. Upload the same tradebook again and confirm it reports zero new executions.
7. Upload a later cumulative tradebook and confirm only unseen Trade IDs are added.
8. When Gemini is configured, run a public research question and confirm the answer and source links persist after refresh.

## Tradebook Semantics

The Angel One tradebook contains individual fills with Trade IDs, Order IDs, quantities, prices and execution timestamps. TradeOS therefore:

- Stores each execution once using account, exchange, segment, trade date and Trade ID as its identity.
- Preserves previous executions when cumulative or date-sliced files are uploaded.
- Rebuilds derived long-equity trades using FIFO by ISIN after each successful import.
- Uses the sell date as the realized date and retains both entry and exit timestamps.
- Keeps remaining buys as immutable lots, presents them as weighted open positions, and reports sells that lack earlier buy history as unmatched.

The tradebook does not include broker charges. Current P&L is execution-derived before charges; exact net P&L requires a later contract-note or charge-reconciliation import.

## Broker IP Limitation

The user's home Wi-Fi public IP is not the outbound IP of a Vercel backend request. A Vercel function calls Angel One from Vercel infrastructure, and Hobby egress may change. Updating an Angel One allowlist weekly does not guarantee uninterrupted sync because the platform IP can change inside that interval.

For the POC, use tradebook upload as the dependable path and treat live sync as experimental. When fixed egress becomes necessary, move only the backend and database to the reserved-IP topology in [24_ORACLE_VERCEL_DEPLOYMENT.md](24_ORACLE_VERCEL_DEPLOYMENT.md); the API boundary and frontend can remain unchanged.
