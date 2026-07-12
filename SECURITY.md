# Security Policy

## Supported Code

Security fixes are applied to the `main` branch. TradeOS is still in its first product slice, so no older release branches are supported yet.

## Reporting a Vulnerability

Do not open a public issue containing credentials, broker tokens, personal trading data, or exploit details. Use GitHub's private vulnerability reporting flow under the repository's **Security** tab. Include:

- A concise description and affected component
- Reproduction steps or a minimal proof of concept
- Expected impact and any known prerequisites
- Suggested mitigation, if available

Rotate any credential immediately if it may have been exposed. Removing a secret from a later commit does not remove it from Git history.

## Security Boundaries

- TradeOS is currently read-only with respect to broker activity; it does not place orders.
- Broker PINs and TOTP values must never be persisted or logged.
- API keys and broker session tokens must be encrypted at rest.
- Every database query containing user data must be scoped to the authenticated user.
- Production secrets belong in deployment secret stores or untracked `.env` files, never in Git.

## Automated Controls

Pull requests run CodeQL, Gitleaks, Bandit, dependency review, Python and npm audits, tests, builds, and container configuration validation. Automation reduces risk but does not replace human review for authentication, broker integration, data access, or deployment changes.
