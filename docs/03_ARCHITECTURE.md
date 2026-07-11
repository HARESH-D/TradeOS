# Architecture

## Current Runtime

- Frontend: React + TypeScript
- Backend: FastAPI modular monolith
- Database: SQLite for local development, PostgreSQL in Docker
- Reverse proxy: Nginx in Docker
- Broker adapters: deterministic mock and Angel One SmartAPI

Redis, background workers, a job queue, managed secrets, and AI providers are target components rather than current runtime dependencies.

## Core Pattern

TradeOS should use a modular service architecture:
- API routes expose product workflows
- Services own business logic
- Repositories own persistence
- Broker adapters isolate broker-specific APIs
- Analysis services normalize synced broker data into dashboard and grid-ready shapes

## Broker Adapter Direction

Broker Interface
-> Mock Broker
-> Angel One SmartAPI
-> Upstox/Zerodha/Dhan/Groww in future

The first real broker is Angel One SmartAPI. A mock broker should remain available so the dashboard and analysis pages can run without live credentials.

## Current Build Data Flow

User connects Angel One
-> Manual sync starts
-> Broker adapter fetches profile, holdings, orders, trades, positions, RMS
-> Backend stores normalized records and raw broker payloads
-> Dashboard reads summarized metrics
-> Analysis grid reads detailed rows with filters

The current manual sync runs inside the API request. The production target accepts the request quickly and performs broker work through an idempotent background job.

See [20_SYSTEM_DESIGN_GUIDE.md](20_SYSTEM_DESIGN_GUIDE.md) for the interview walkthrough and [21_HIGH_LEVEL_DESIGN.md](21_HIGH_LEVEL_DESIGN.md) for current and target diagrams.
