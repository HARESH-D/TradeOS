# Database

## Implemented Tables

- `users`: email accounts and password hashes
- `broker_accounts`: broker mode, connection state, encrypted tokens and latest raw snapshot
- `sync_runs`: manual import history, record counts and errors
- `trades`: normalized trade rows used by dashboard analytics and the analysis grid

SQLite is the zero-configuration local default. Docker Compose uses PostgreSQL 16.

## Planned Tables

- Holdings
- Orders
- Charges
- JournalEntries
- AIInsights
- Strategies
- Notifications
- DailySnapshots
