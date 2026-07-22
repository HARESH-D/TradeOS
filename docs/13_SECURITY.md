# Security

## Implemented

- PBKDF2-SHA256 password hashing with a random per-password salt
- Signed JWT authentication
- Authenticated route dependency and user-scoped database filters
- Fernet encryption for broker API keys and session tokens
- Broker PIN and current TOTP are used during connection but never persisted
- Strict configured CORS origin list
- Read-only broker workflow with no order placement APIs
- Pull-request CodeQL, Gitleaks, Bandit, dependency review, and dependency audit automation
- Pinned GitHub Action revisions with restricted workflow permissions
- CODEOWNERS coverage for broker, core security, deployment, and workflow changes
- Gemini key remains a backend-only environment secret and provider readiness exposes only a boolean
- Agent prompts are length-bounded and every run is scoped to the authenticated user
- Citation URLs are accepted only as valid HTTPS links; stored answers, titles and excerpts are size-bounded
- Gemini errors are sanitized before persistence and API responses
- AI research has no broker credentials, trading writes or order-execution tools
- Local Llama receives only user-scoped read-only analytics context; portfolio rows use an explicit field allowlist and never include broker credentials
- Ollama is disabled by default and its documented local endpoint binds to loopback; it must not be exposed directly to the public internet

The Gemini free tier may use submitted content to improve Google products under its current terms. The first research slice must therefore be used for public research prompts only. Private portfolio context will not be sent to a cloud model until an explicit provider-data policy and user consent control are implemented.

## Production Improvements

- Secure HttpOnly sessions with rotating refresh tokens and revocation
- Separate managed keys and KMS envelope encryption for broker secrets
- Login, broker-connect, sync, grid, and export rate limits
- Immutable audit events
- Structured secret redaction
- CSRF protection for cookie-authenticated writes
- WAF, security headers, dependency scanning, and container scanning
- Data retention, user export, and deletion workflows
- Agent rate limits, per-run tool/token budgets, prompt-injection evaluations and provider data-consent controls

See [21_HIGH_LEVEL_DESIGN.md](21_HIGH_LEVEL_DESIGN.md) for the threat controls and [23_ARCHITECTURE_IMPROVEMENT_PLAN.md](23_ARCHITECTURE_IMPROVEMENT_PLAN.md) for the prioritized hardening sequence.

Repository reporting instructions are in [../SECURITY.md](../SECURITY.md), and merge safeguards are in [25_CHANGE_AND_PR_SAFETY.md](25_CHANGE_AND_PR_SAFETY.md).
