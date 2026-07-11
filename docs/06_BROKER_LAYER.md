# Broker Layer

Implement adapter interface.

## Current Build

Initial real implementation: Angel One SmartAPI.

The first broker workflow is read-only:
- Connect broker
- Manual sync
- Fetch profile
- Fetch holdings
- Fetch orders
- Fetch trades
- Fetch positions
- Fetch RMS limits

No order placement, modification, cancellation, or automation in the first build.

## Adapter Contract

Each broker adapter should expose the same high-level operations:
- connect
- refresh_session
- get_profile
- get_holdings
- get_orders
- get_trades
- get_positions
- get_rms_limits

The app should also include a mock broker adapter for development and UI testing without live broker credentials.

## Security Direction

- Do not store broker PIN/password.
- Do not store TOTP secret in the first build.
- Store broker API key and session tokens only if encrypted.
- Do not log sensitive request fields.
