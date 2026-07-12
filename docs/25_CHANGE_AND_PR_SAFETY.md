# Change, Commit, and Pull Request Safety

## 1. Purpose

This document is the durable operating guide and change register for TradeOS commits and pull requests. Git remains the authoritative commit history and GitHub remains the authoritative PR history; this file records the intent, risk, and verification standard around meaningful releases.

The rule is simple: changes reach `main` through a reviewed pull request after required automated checks pass. Direct pushes to `main` should be disabled with a GitHub branch protection rule.

## 2. Safe Change Flow

1. Pull the latest `main` and create a short-lived branch such as `feature/manual-sync` or `fix/user-scope-filter`.
2. Keep each commit focused and use an imperative subject, for example `Add broker sync status endpoint`.
3. Never stage production `.env` files, credentials, database files, generated builds, or unrelated local edits.
4. Install developer checks with `backend/.venv/bin/pip install -r backend/requirements-dev.txt`.
5. Run `./scripts/quality-gate.sh` before pushing.
6. Open a draft PR early and complete the repository PR template.
7. Resolve every required check and review finding before marking the PR ready.
8. Squash-merge feature work when intermediate commits do not add useful history. Preserve separate commits when they represent independently reversible changes.
9. Verify `/health`, authentication, broker connection or sync, dashboard, and analysis after deployment when those surfaces are affected.
10. Revert the merge commit or redeploy the previous image if production validation fails; do not patch production manually.

## 3. Automated Review Gates

| Gate | Detects | Blocking behavior |
| --- | --- | --- |
| Backend tests and compile | Behavioral regressions and invalid Python | Any failure blocks merge |
| Ruff | Import errors, undefined names, common defects, and style drift | Any finding blocks merge |
| Bandit | Medium or high confidence Python security risks | Medium or high severity findings block merge |
| pip-audit and npm audit | Known dependency vulnerabilities | Python findings or moderate-and-higher npm findings block merge |
| Frontend type check and build | Type errors and production bundle failures | Any failure blocks merge |
| Docker checks | Invalid Compose files and broken image builds | Any failure blocks merge |
| CodeQL | Cross-file security and data-flow vulnerabilities | Findings appear in GitHub code scanning for review |
| Dependency review | Vulnerabilities introduced by a PR | Moderate-and-higher additions block merge |
| Gitleaks | Credentials and tokens in commits or history | Any detected secret blocks merge and requires rotation |
| CODEOWNERS | Sensitive changes without owner review | Enforced once branch protection requires code-owner review |

Automation cannot prove business correctness. Authentication, user scoping, broker credential handling, schema changes, financial calculations, and deployment configuration always require human review.

## 4. Required GitHub Settings

After the workflows land on `main`, protect the `main` branch with these settings:

- Require a pull request before merging
- Keep the approval count at zero while this is a solo-maintainer repository because an author cannot approve their own PR
- Require at least one approval and code-owner review as soon as a second maintainer is added
- Dismiss stale approvals when new commits are pushed
- Require all Quality Gate, CodeQL, Dependency Review, and Secret Scan checks
- Require branches to be up to date before merging
- Require conversation resolution
- Block force pushes and branch deletion
- Do not allow bypasses for routine work

Enable private vulnerability reporting, Dependabot alerts, Dependabot security updates, secret scanning, and push protection in the repository Security settings where available.

## 5. Review Priorities

Review in this order:

1. Security: secret exposure, authentication bypass, missing user scoping, unsafe broker calls, and sensitive logs.
2. Correctness: incorrect P&L calculations, duplicate sync data, timezone errors, partial transaction handling, and stale cache behavior.
3. Reliability: retries, idempotency, rollback, timeouts, external API failures, and migration safety.
4. Compatibility: API contracts, database schema, deployment environment, and responsive UI behavior.
5. Maintainability: unclear ownership, unnecessary complexity, duplicated logic, missing tests, and weak naming.

## 6. Change Register

Update this table in each release PR. Use the final PR number and merge commit after merge when available.

| Date | Commit or PR | Summary | Risk | Verification |
| --- | --- | --- | --- | --- |
| Initial | `737acdc` | Repository initialization | Low | Repository created |
| 2026-07-12 | PR `#1` / `5b5d390` | Trading dashboard, manual broker sync, analysis grid, documentation, and deployment bundle | High | Backend tests, frontend build and audit, Docker production smoke tests, browser smoke tests |
| 2026-07-12 | PR `#1` / `c077844` | Add PR governance, quality gates, security scans, dependency automation, and patched backend dependencies | Medium | Full local quality gate, image builds, workflow validation, and GitHub checks |
| 2026-07-12 | PR `#16` / `6223039` | Add Angel One statement import, statement-aware analytics, and Vercel POC backend support | High | Full quality gate, dependency audits, real-workbook parsing, and duplicate-safe HTTP import smoke test |

## 7. Incident Rule

If a secret is committed, stop normal development, revoke or rotate it first, then remove it from the branch and Git history as appropriate. A green Gitleaks rerun does not make the old credential safe. Record the response in a private security advisory without copying the secret into issues, PR comments, or logs.
