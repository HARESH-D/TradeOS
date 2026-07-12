# Vercel POC Deployment

## Purpose

This runbook is the current zero-cost proof-of-concept topology:

```text
Browser -> Vercel Vite frontend -> Vercel FastAPI function -> managed PostgreSQL
```

It supports authentication, dashboard analytics, the analysis grid, demo sync and Angel One P&L statement upload. It is not the final live-broker topology because Vercel Hobby does not provide a dedicated outbound IPv4.

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
3. Open Broker and upload an Angel One equity P&L `.xlsx` statement.
4. Confirm the import summary and sync-history record appear.
5. Confirm dashboard and analysis rows contain only that user's imported data.
6. Upload the same statement again and confirm trades are replaced rather than duplicated.
7. When Gemini is configured, run a public research question and confirm the answer and source links persist after refresh.

## Statement Semantics

The P&L statement contains symbol-level aggregates, open positions, charges and ledger adjustments. It does not contain individual execution timestamps. TradeOS therefore:

- Allocates statement costs across realized symbols by turnover.
- Stores the source rows, statement summary, charges and adjustments in the account snapshot.
- Marks open quantities as open positions and realized quantities as closed aggregates.
- Uses the report period end as the normalized trade date.
- Replaces the prior statement-derived dataset on each successful upload.

Import the Angel One tradebook in a later phase to obtain true entry, exit and holding-period analysis.

## Broker IP Limitation

The user's home Wi-Fi public IP is not the outbound IP of a Vercel backend request. A Vercel function calls Angel One from Vercel infrastructure, and Hobby egress may change. Updating an Angel One allowlist weekly does not guarantee uninterrupted sync because the platform IP can change inside that interval.

For the POC, use statement upload as the dependable path and treat live sync as experimental. When fixed egress becomes necessary, move only the backend and database to the reserved-IP topology in [24_ORACLE_VERCEL_DEPLOYMENT.md](24_ORACLE_VERCEL_DEPLOYMENT.md); the API boundary and frontend can remain unchanged.
