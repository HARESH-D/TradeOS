# Testing

## Current Coverage

- Password hashing and verification
- JWT creation and decoding
- Broker-secret encryption round trip
- Deterministic mock broker snapshot
- TypeScript production compilation
- Runtime smoke checks for login, manual sync, dashboard and filtered analysis APIs
- Angel One tradebook parsing with malformed worksheet dimensions, split-order fills and strict workbook validation
- FIFO partial-fill matching, unmatched sell reporting, repeat-upload idempotency and incremental cumulative imports
- Desktop and mobile visual checks for all current screens
- Gemini response parsing, query deduplication, citation deduplication and unsafe citation rejection
- Successful and failed agent-run persistence plus cross-user history isolation
- AI Agent provider-unavailable API smoke checks and responsive persisted-result rendering
- Ollama model discovery, structured-output parsing and invalid/offline provider boundaries
- Deterministic local analysis context, mode persistence and cross-user trade exclusion

## Commands

```bash
backend/.venv/bin/pip install -r backend/requirements-dev.txt
./scripts/quality-gate.sh
```

Every pull request also runs CodeQL, Gitleaks, dependency review, Python static analysis, dependency audits, Docker Compose validation, and production image builds. See [25_CHANGE_AND_PR_SAFETY.md](25_CHANGE_AND_PR_SAFETY.md) for blocking behavior and review policy.

Automated browser regression tests and broader API integration tests should be added as the first slice evolves. Sanitized golden workbooks should be added whenever another Angel One tradebook layout is encountered.
