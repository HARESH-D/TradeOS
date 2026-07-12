# TradeOS

TradeOS is a decision-support workspace for Indian swing traders. It combines broker sync, portfolio visibility and performance analytics without acting as a price predictor or order-execution bot.

## First Product Slice

The current application includes:

- Email/password authentication with a seeded demo account
- Responsive trading dashboard with KPIs, equity curve, daily P&L and profit calendar
- Manual broker sync with demo and Angel One SmartAPI connection modes
- Manual Angel One P&L statement import from XLSX when live broker sync is unavailable
- Spreadsheet-style trade analysis with per-column filters, sorting, pagination and CSV export
- AI Agent workspace shell for the clean-room research and trade-analysis milestone
- Persistent SQLite development data and PostgreSQL-backed Docker deployment
- Encrypted broker API keys and session tokens; broker PIN and TOTP are never stored

## Run Locally

Start the API:

```bash
cd backend
python3 -m virtualenv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

Start the web application in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` and use:

```text
Email: demo@tradeos.app
Password: tradeos123
```

For a containerized environment, run `docker compose up --build` and open `http://localhost:8080`.

## Verification

```bash
backend/.venv/bin/pip install -r backend/requirements-dev.txt
./scripts/quality-gate.sh
```

The product direction and future phases remain documented in [docs/00_MASTER_SPEC.md](docs/00_MASTER_SPEC.md) and [docs/16_DEVELOPMENT_ROADMAP.md](docs/16_DEVELOPMENT_ROADMAP.md).

For an interview-ready explanation of the architecture, begin with [docs/20_SYSTEM_DESIGN_GUIDE.md](docs/20_SYSTEM_DESIGN_GUIDE.md), then use the linked HLD, LLD, and architecture improvement plan for deeper discussion.

The zero-cost POC deployment using Vercel and managed PostgreSQL is documented in [docs/26_VERCEL_POC_DEPLOYMENT.md](docs/26_VERCEL_POC_DEPLOYMENT.md). It does not provide a fixed broker-facing IP. The production topology with a reserved IP remains documented in [docs/24_ORACLE_VERCEL_DEPLOYMENT.md](docs/24_ORACLE_VERCEL_DEPLOYMENT.md).

Commit, pull request, automated review, and rollback rules are documented in [docs/25_CHANGE_AND_PR_SAFETY.md](docs/25_CHANGE_AND_PR_SAFETY.md). Security vulnerabilities should be reported using [SECURITY.md](SECURITY.md).
