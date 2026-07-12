# Database

## Implemented Tables

- `users`: email accounts and password hashes
- `broker_accounts`: broker mode, connection state, encrypted tokens and latest raw snapshot
- `sync_runs`: manual import history, record counts and errors
- `trades`: normalized trade rows used by dashboard analytics and the analysis grid
- `agent_runs`: user-scoped research prompts, provider/model, status, answers, source evidence, search queries and errors

SQLite is the zero-configuration local default. Docker Compose uses PostgreSQL 16.

## Planned Tables

- Holdings
- Orders
- Charges
- JournalEntries
- Agent messages, tool events, normalized evidence items and resumable checkpoints
- Strategies
- Notifications
- DailySnapshots
