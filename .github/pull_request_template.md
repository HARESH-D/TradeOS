## What changed

<!-- Describe the user-visible and technical changes. -->

## Why

<!-- Link the issue or explain the problem and expected outcome. -->

## Risk and rollback

<!-- Name the failure modes, affected data or APIs, and the rollback path. -->

## Verification

- [ ] `./scripts/quality-gate.sh` passes locally
- [ ] New or changed behavior has focused tests
- [ ] Dashboard, broker sync, and analysis behavior was smoke-tested when affected
- [ ] Desktop and mobile UI were checked when the interface changed
- [ ] Database changes are backward compatible or include a migration and rollback plan

## Security and privacy

- [ ] No credentials, broker tokens, TOTP values, PINs, private keys, or production `.env` files are committed
- [ ] Authentication and user-scoped authorization were reviewed when routes or queries changed
- [ ] Logs and error responses do not expose secrets or personal trading data
- [ ] New dependencies are necessary, pinned, licensed appropriately, and pass dependency review
- [ ] Broker operations remain read-only unless order execution is explicitly approved in a separate design

## Deployment

- [ ] Environment variable and deployment documentation changes are included
- [ ] The change is compatible with Vercel frontend and Oracle VM backend deployment
- [ ] Post-deploy health checks and rollback steps are clear

## Evidence

<!-- Add screenshots, API examples, or test output where they help the reviewer. -->
