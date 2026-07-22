# Deployment

## Docker Compose

The initial environment contains:

- `web`: React production bundle served by Nginx on port 8080
- `api`: FastAPI service on port 8000
- `db`: PostgreSQL 16 with a persistent volume

Run:

```bash
docker compose up --build
```

Set strong `JWT_SECRET` and `ENCRYPTION_KEY` values before any non-local deployment. The Oracle bundle prepares HTTPS and local database backups; managed secrets, versioned migrations, and off-machine automated backups remain production improvements.

## Oracle And Vercel

The prepared production topology uses Vercel for the Vite frontend and an Oracle Cloud VM for FastAPI, PostgreSQL, HTTPS termination, and the reserved outbound IPv4 required for broker allowlisting.

See [24_ORACLE_VERCEL_DEPLOYMENT.md](24_ORACLE_VERCEL_DEPLOYMENT.md) for the complete provisioning, deployment, verification, Angel One registration, backup, and recovery procedure.

## Vercel POC

For the current no-card POC, the frontend and FastAPI backend can run as separate Vercel projects with managed PostgreSQL. See [26_VERCEL_POC_DEPLOYMENT.md](26_VERCEL_POC_DEPLOYMENT.md).

This topology is suitable for authentication, dashboards, analysis and tradebook uploads. Vercel Hobby egress is dynamic, so its observed IP must not be represented as a reserved or stable Angel One allowlist address. Use tradebook upload for reliable data ingestion until the backend moves to infrastructure with a reserved outbound IP.

Grounded AI research additionally requires backend-only `GEMINI_API_KEY`. `GEMINI_MODEL` defaults to `gemini-2.5-flash`, selected because the current Gemini free tier includes a limited daily grounded-search allowance. Redeploy the API after changing either value. Never configure the key in the Vite frontend project.

## Local Llama

Local trade and portfolio analysis runs beside the development API:

```bash
ollama pull llama3.1:8b
ollama serve
cd backend
OLLAMA_ENABLED=true .venv/bin/uvicorn app.main:app --reload
```

The defaults are `OLLAMA_BASE_URL=http://127.0.0.1:11434`, `OLLAMA_MODEL=llama3.1:8b`, and a 4096-token context. Keep the endpoint on loopback. The Vercel API cannot call a laptop's localhost, so hosted local inference still requires the planned authenticated outbound companion runner.
