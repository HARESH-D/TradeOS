# Database

## Implemented Tables

- `users`: email accounts and password hashes
- `broker_accounts`: broker mode, connection state, encrypted tokens and latest raw snapshot
- `sync_runs`: manual import history, record counts and errors
- `trade_executions`: immutable Angel One fills deduplicated by account, exchange, segment, trade date and Trade ID
- `trades`: normalized trade rows used by dashboard analytics and the analysis grid
- `agent_runs`: user-scoped research prompts, provider/model, status, answers, source evidence, search queries and errors

SQLite is the zero-configuration local default. Docker Compose uses PostgreSQL 16.

Tradebook imports append only new `trade_executions`. The `trades` table is a rebuildable FIFO projection containing closed matched lots and one weighted open-position row per ISIN; the underlying unmatched buy lots remain immutable in `trade_executions`. Broker charges are not present in the tradebook and are currently stored as zero on those derived rows.

## Planned Tables

- Holdings
- Orders
- Charges
- JournalEntries
- Agent messages, tool events, normalized evidence items and resumable checkpoints
- Strategies
- Notifications
- DailySnapshots
