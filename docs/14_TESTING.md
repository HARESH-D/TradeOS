# Testing

## Current Coverage

- Password hashing and verification
- JWT creation and decoding
- Broker-secret encryption round trip
- Deterministic mock broker snapshot
- TypeScript production compilation
- Runtime smoke checks for login, manual sync, dashboard and filtered analysis APIs
- Desktop and mobile visual checks for all current screens

## Commands

```bash
cd backend && .venv/bin/pytest -q
cd frontend && npm run build
cd frontend && npm audit --audit-level=moderate
```

API integration tests and automated browser regression tests should be added as the first slice evolves.
