# TradeOS Architecture Improvement Plan

## 1. Executive Assessment

The current TradeOS design is appropriate for an MVP and system design demonstration. It has real boundaries instead of a single undifferentiated application: frontend pages, HTTP routes, services, database entities, a broker protocol, mock and Angel One adapters, analytics, security helpers, and containerized deployment.

Its main limitation is not the modular monolith. The main limitation is that broker synchronization, normalization, persistence, and analytics refresh happen inside one API request. That couples user-facing API capacity to the latency and reliability of an external broker.

The strongest evolution path is:

1. Make financial data and schema changes correct and auditable.
2. Move synchronization to an idempotent worker pipeline.
3. Normalize broker executions and portfolio snapshots properly.
4. Precompute dashboard read models.
5. Add production security and observability.
6. Scale storage and services only when measured load requires it.

## 2. Architecture Maturity Matrix

| Capability | Current state | Near-term target | Scale target |
|---|---|---|---|
| Application structure | Modular monolith | Modular monolith with repositories and domain services | Same boundaries; selective service extraction |
| Broker sync | Inline HTTP request | Queued worker job | Broker-specific worker pools and quotas |
| Sync idempotency | Trade unique key | Request key, active-run constraint, idempotent upserts | Checkpoints and replayable imports |
| Financial model | Closed demo trades and live execution-like rows | Canonical executions plus derived trades | Versioned matching and corporate-action support |
| Numeric precision | Floating point | Decimal and PostgreSQL `NUMERIC` | Same |
| Analytics | Full trade scan per request | Daily aggregate read model | Cache, replica, optional warehouse |
| Authentication | Seven-day JWT in local storage | Secure HttpOnly access and rotating refresh sessions | Device/session management and anomaly controls |
| Broker secrets | Fernet using configured key | Envelope encryption with KMS | Rotation and per-tenant key policy |
| Raw data | JSON in hot database rows | Encrypted object storage | Lifecycle tiers and retention controls |
| Database lifecycle | `create_all` | Alembic migrations | Online migration process |
| Observability | Logs and health endpoint | Structured logs, metrics, traces, alerts | SLO-driven operations |
| Testing | Security and mock unit tests plus manual smoke checks | API, database, adapter, and browser automation | Load, failover, and chaos testing |
| Deployment | Docker Compose | CI/CD to managed runtime | Multi-AZ, autoscaling, canary or blue/green |

## 3. P0: Correctness And Security Before Live Users

These items should be completed before treating the application as a production financial record.

### 3.1 Use Decimal Financial Types

**Current issue:** prices and P&L are stored as floating point. Binary floating point can introduce small rounding errors that accumulate or appear in exports.

**Change:**

- Replace Python `float` with `Decimal` in domain and calculation code.
- Replace database `FLOAT` with `NUMERIC(20, 8)` or a precision appropriate to the instrument.
- Define rounding rules for display, brokerage, taxes, and final net P&L.
- Add golden test cases with known broker statements.

**Success criterion:** calculated net P&L reconciles to broker statements within an explicitly documented tolerance.

### 3.2 Introduce Versioned Database Migrations

**Current issue:** tables are created with SQLAlchemy `create_all`; schema changes are not versioned.

**Change:**

- Add Alembic.
- Create a baseline migration from current models.
- Require forward and rollback review for every schema change.
- Adopt expand-migrate-contract for zero-downtime changes.

**Success criterion:** a clean database and a production-like database both reach the same schema through migrations.

### 3.3 Normalize Time Correctly

**Current issue:** timestamps are mostly naive, and malformed broker timestamps can fall back to the current date.

**Change:**

- Use timezone-aware UTC timestamps throughout persistence.
- Parse Angel One timestamps using documented formats and `Asia/Kolkata` where required.
- Quarantine invalid rows instead of assigning today's date.
- Store user reporting timezone separately.

**Success criterion:** the same execution always maps to the same exchange trading date across environments.

### 3.4 Harden TradeOS Sessions

**Current issue:** the browser stores a seven-day bearer JWT in local storage. Any successful script injection could read it, and there is no server-side revocation.

**Change:**

- Use short-lived access sessions in `Secure`, `HttpOnly`, `SameSite=Lax` cookies.
- Add rotating refresh sessions stored hashed in the database.
- Add CSRF protection for state-changing requests.
- Revoke refresh families on reuse, password change, or account disable.
- Add login rate limiting and account lock policy.

**Success criterion:** browser JavaScript cannot read authentication credentials, and individual sessions can be revoked.

### 3.5 Move Broker Secrets To Managed Key Protection

**Current issue:** Fernet encryption is sound for local development, but its fallback derives the encryption key from the JWT secret. This combines unrelated trust domains and makes rotation difficult.

**Change:**

- Use envelope encryption with a managed KMS.
- Generate a data key per account or tenant.
- Store ciphertext, encrypted data key, and key version.
- Keep JWT signing and data encryption keys separate.
- Add automated redaction tests.

**Success criterion:** rotating the JWT key does not affect broker credential decryption, and KMS access is limited to the connection and worker roles.

### 3.6 Build The Canonical Financial Model

**Current issue:** the live broker trade book is normalized into execution-like rows with zero P&L because entry and exit pairing is not yet implemented.

**Change:**

- Create separate order, execution, holding snapshot, position snapshot, and funds snapshot tables.
- Preserve immutable broker executions.
- Derive logical trades using a versioned matching rule, initially FIFO for long-only equity.
- Calculate charges through a dated charge-rule engine.
- Reconcile calculated totals against broker reports.

**Success criterion:** dashboard win rate and profit factor are based on complete logical trades, not fills.

### 3.7 Validate Angel One With A Controlled Account

**Current issue:** the adapter follows the broker contract but has not been validated using a real account in this repository.

**Change:**

- Test login, token refresh, empty resources, paginated resources, rate limits, and expired sessions.
- Capture sanitized response fixtures.
- Confirm public/local IP and MAC header requirements in the deployed environment.
- Add a reconnect-required state.

**Success criterion:** a controlled live sync reconciles resource counts and can recover from an expired access token without exposing secrets.

## 4. P1: Decouple Synchronization From The API

This is the highest-value architecture change after financial correctness.

### 4.1 Introduce Sync Jobs

**Current issue:** `POST /api/broker/sync` waits for the broker and database work to finish.

**Change:**

- Return `202 Accepted` after creating a queued sync run.
- Publish through a transactional outbox.
- Process using a separate worker command from the same codebase.
- Poll `GET /sync-runs/{id}` or stream progress through server-sent events.

**Success criterion:** API response time remains stable during a broker slowdown.

### 4.2 Add Idempotency And Concurrency Protection

**Change:**

- Require `Idempotency-Key` for manual sync starts.
- Add a partial unique index for one queued/running sync per account.
- Acquire a Redis lease in the worker.
- Upsert by account plus broker record ID.
- Store pagination checkpoints.
- Make every state transition compare-and-set.

**Success criterion:** duplicate requests and queue redelivery do not create duplicate records or overlapping account imports.

### 4.3 Handle Partial Failure Explicitly

**Change:**

- Track every resource independently.
- Distinguish empty success, missing data, timeout, auth rejection, broker error, and internal validation failure.
- Retain the previous successful snapshot when a replacement resource fails.
- Mark the overall run `partial` when appropriate.
- Add targeted resource replay.

**Success criterion:** the UI can tell the user exactly what is fresh and what was retained from a previous sync.

### 4.4 Apply Broker-Aware Rate Limits

**Change:**

- Maintain global, broker, account, and endpoint concurrency limits.
- Respect `Retry-After` when present.
- Use exponential backoff with jitter.
- Add circuit breakers and broker-specific queues.

**Success criterion:** one broker outage or one very large account cannot exhaust all sync workers.

## 5. P1: Build Fast And Explainable Analytics

### 5.1 Add Daily Performance Read Models

**Current issue:** every dashboard request loads all user trades and recalculates every metric.

**Change:**

- Add `daily_performance` per broker account and date.
- Update only dates affected by a sync.
- Recompute cumulative values from the earliest affected date.
- Store calculation version and source version.

**Success criterion:** dashboard query cost depends on requested days rather than total lifetime trades.

### 5.2 Define Metric Semantics

Document and test:

- Whether flat trades enter win-rate denominator
- Whether P&L is realized, unrealized, or combined
- Treatment of deposits and withdrawals in drawdown
- Charge allocation across partial fills
- Exchange timezone and trading date
- Multi-currency behavior
- Corporate actions and broker corrections

**Success criterion:** every displayed metric has a formula, population, timezone, and calculation version.

### 5.3 Add Cache With Data Versions

**Change:**

- Increment account data version after successful projection.
- Include data version in Redis keys.
- Cache common date ranges for short periods.
- Serve PostgreSQL directly when Redis is unavailable.

**Success criterion:** repeated dashboard reads avoid repeated database aggregation without serving stale data after sync.

### 5.4 Make The Analysis Grid Fully Server-Side

**Current issue:** server filters some top-level fields, then AG Grid filters only the fetched maximum of 500 rows. The visible filter semantics are therefore not global for large accounts.

**Change:**

- Translate an allowlisted AG Grid filter/sort model into query specifications.
- Use cursor pagination.
- Return filtered summary metrics from the server.
- Persist filters in the URL.
- Run large exports asynchronously from the same query specification.

**Success criterion:** a filter always applies to the complete account history, regardless of page size.

## 6. P1: Production Observability And Operations

### 6.1 Structured Telemetry

Add correlation IDs across API, outbox, queue, worker, and broker requests. Emit:

- API request count, errors, and latency
- Database pool saturation and slow queries
- Queue depth, oldest job age, and retries
- Sync duration and success by broker and resource
- Broker rate-limit and authentication errors
- Projection lag and cache hit ratio

### 6.2 Alerting

Page or notify on user-impacting symptoms:

- API error-budget burn
- Queue age above freshness target
- Broker auth failure spike
- Dead-letter queue growth
- Database disk, replication lag, or pool exhaustion
- Cross-tenant authorization test failure

### 6.3 Audit And Supportability

- Immutable security and financial-operation audit events
- Admin support tools that never reveal secret material
- Safe sync replay with reason and actor
- User-visible sync timeline and error codes

## 7. P1: Automated Quality Gates

### Continuous Integration

Every change should run:

1. Python lint, type checking, and unit tests.
2. TypeScript checking and production build.
3. PostgreSQL integration tests.
4. Broker adapter contract tests.
5. API schema compatibility checks.
6. Browser tests for login, sync, dashboard, grid, and responsive layouts.
7. Dependency, container, and secret scans.
8. Migration test from the previous release.

### Release Gates

- Error-free canary or staging smoke test
- Database backup verification
- Rollback plan
- Feature flag for new broker or calculation versions
- Reconciliation sample for analytics changes

## 8. P2: Scale The Runtime Based On Evidence

Do not split services merely to make the architecture diagram larger.

### Extract Broker Workers When

- Queue age requires independent autoscaling.
- Broker SDK dependencies conflict with the API runtime.
- Broker-specific release cadence or ownership emerges.

The worker can be a separate deployment from the same repository before it becomes a separate service or repository.

### Add Read Replicas When

- Read traffic saturates primary CPU or I/O.
- Dashboard and grid reads compete with sync writes.
- Replica lag remains within the stated freshness tolerance.

### Partition Trades And Executions When

- Indexes no longer fit practical memory budgets.
- Vacuum or maintenance time becomes material.
- Query plans degrade at hundreds of millions of rows.

Partition by account hash for even distribution or by time for retention management; choose based on measured query patterns.

### Add A Warehouse When

- Cross-user or cross-account reporting becomes a product requirement.
- Long-range analytical scans affect transactional performance.
- Data science and AI feature generation need reproducible historical datasets.

Use change data capture or outbox events to populate it. PostgreSQL remains the operational source of truth.

### Extract Authentication When

- Multiple TradeOS products share identity.
- Enterprise SSO, MFA, and policy requirements expand substantially.
- A managed identity provider offers a better security and operational tradeoff.

## 9. P2: Future Product Modules Without Destabilizing Core Data

### Portfolio Engine

Build on canonical executions and snapshots. Do not recalculate portfolio state from UI-specific trade rows.

### Journal And Rule Engine

Journal entries reference immutable trade IDs and store user-authored context separately. Rule results include rule version and source data version so historical decisions remain explainable.

### AI Coach

AI reads curated, permission-checked features and journal entries. It does not receive broker tokens. Store prompt version, model, inputs by reference, output, and user feedback. AI generates retrospective explanations, not price predictions.

### Order Execution

Treat this as a separate risk domain. It requires:

- Explicit user confirmation and strong authentication
- Pre-trade risk checks
- Idempotent order command IDs
- State-machine reconciliation with broker order status
- Kill switch, limits, and circuit breakers
- Stronger audit, compliance, and operational controls

Do not place it inside the read-only sync worker path.

## 10. Recommended Delivery Sequence

### Milestone A: Production Data Foundation

1. Add migrations.
2. Convert money to Decimal/NUMERIC.
3. Normalize timezone handling.
4. Add execution, order, holding, position, and funds tables.
5. Add sanitized broker fixtures and live Angel One validation.
6. Reconcile data and P&L with broker statements.

### Milestone B: Reliable Synchronization

1. Add sync API version 1 and idempotency key.
2. Add sync state machine and resource results.
3. Add outbox and queue.
4. Run a separate worker deployment.
5. Add Redis lock, retries, checkpoints, and dead-letter handling.
6. Add progress UI and reconnect state.

### Milestone C: Analytics Read Models

1. Build logical trade matching.
2. Build charge engine.
3. Add daily aggregates and calculation versions.
4. Add Redis dashboard cache.
5. Convert analysis to server-side query model and cursor pagination.
6. Add asynchronous export.

### Milestone D: Security And Operations

1. Move web auth to secure sessions.
2. Move broker secrets to KMS envelope encryption.
3. Add rate limits and audit events.
4. Add structured telemetry and SLO dashboards.
5. Add automated integration, browser, load, and resilience tests.
6. Deploy managed PostgreSQL with backups and recovery drills.

### Milestone E: Product Expansion

1. Portfolio and charges views.
2. Journal and rule engine.
3. AI retrospective coach.
4. Additional broker adapters.
5. Guarded order workflow only after a separate risk and compliance review.

## 11. Design Review Checklist

Use this checklist before approving a new feature:

### Data

- What is the source of truth?
- Is the operation idempotent?
- Are money and time represented correctly?
- Is the calculation versioned and explainable?
- What is the retention and deletion policy?

### Security

- How is tenant ownership enforced?
- Does the path handle credentials or regulated data?
- Could logs or traces expose secrets?
- What rate limit and audit event are required?

### Reliability

- What happens on timeout, duplicate delivery, partial failure, and retry?
- Can a stale worker overwrite newer state?
- Is there a recovery or replay path?

### Performance

- What is the expected cardinality and query pattern?
- Which index supports it?
- Does the request perform external I/O?
- Is caching safe and how is it invalidated?

### Operations

- Which metrics and alerts show failure?
- How is the change rolled back?
- Does it require a migration or backfill?
- How will support diagnose a user-visible issue?

## 12. The Best Improvement Story For An Interview

Use this concise answer when asked what you would improve first:

> The MVP's boundaries are sound, but synchronization is still synchronous and live broker executions are not yet modeled as full round-trip trades. I would first make money and time exact, add migrations, and validate the broker contract. Then I would accept sync requests asynchronously through an idempotent job and transactional outbox, normalize immutable executions, derive trades, and update daily aggregate read models. That removes external broker latency from the API, makes retries safe, and gives the dashboard predictable performance. After that I would harden browser sessions, move secret encryption to KMS, and add observability before scaling into separate services.

This answer demonstrates prioritization: correctness first, then reliability, performance, security, and only then organizational scale.

