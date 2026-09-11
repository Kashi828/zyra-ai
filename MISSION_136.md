# MISSION 136 — Flutter Session Inventory Contract

## Scope

Connect the cross-platform Flutter client to the existing authenticated session inventory and per-session revocation API without introducing client-side secret storage or weakening the server authorization boundary.

## Delivered

- Added typed Flutter models for `/v1/session/list` responses, including device metadata, active/inactive summary counts, and session state.
- Added `ZyraSessionCredentials` for the existing `device_id` + `session_id` authenticated context.
- Added client methods for session inventory and per-session revocation.
- Preserved the existing server-side same-device authorization boundary; the client does not attempt to authorize foreign sessions.
- Added regression coverage for active/inactive parsing and verified session credentials do not serialize a device secret.

## Security

The Flutter client models contain session identifiers and expiry state only. Device secrets and refresh tokens are intentionally excluded from the session-inventory credential object. Server-side authentication and authorization remain authoritative.
