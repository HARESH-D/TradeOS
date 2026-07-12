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
backend/.venv/bin/pip install -r backend/requirements-dev.txt
./scripts/quality-gate.sh
```

Every pull request also runs CodeQL, Gitleaks, dependency review, Python static analysis, dependency audits, Docker Compose validation, and production image builds. See [25_CHANGE_AND_PR_SAFETY.md](25_CHANGE_AND_PR_SAFETY.md) for blocking behavior and review policy.

API integration tests and automated browser regression tests should be added as the first slice evolves.
