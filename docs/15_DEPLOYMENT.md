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
