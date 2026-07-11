# Security

## Implemented

- PBKDF2-SHA256 password hashing with a random per-password salt
- Signed JWT authentication
- Authenticated route dependency and user-scoped database filters
- Fernet encryption for broker API keys and session tokens
- Broker PIN and current TOTP are used during connection but never persisted
- Strict configured CORS origin list
- Read-only broker workflow with no order placement APIs

## Production Improvements

- Secure HttpOnly sessions with rotating refresh tokens and revocation
- Separate managed keys and KMS envelope encryption for broker secrets
- Login, broker-connect, sync, grid, and export rate limits
- Immutable audit events
- Structured secret redaction
- CSRF protection for cookie-authenticated writes
- WAF, security headers, dependency scanning, and container scanning
- Data retention, user export, and deletion workflows

See [21_HIGH_LEVEL_DESIGN.md](21_HIGH_LEVEL_DESIGN.md) for the threat controls and [23_ARCHITECTURE_IMPROVEMENT_PLAN.md](23_ARCHITECTURE_IMPROVEMENT_PLAN.md) for the prioritized hardening sequence.
