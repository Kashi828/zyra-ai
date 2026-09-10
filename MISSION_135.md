# Mission 135 — Session Inventory Lifecycle Visibility

## Scope
Allow an authenticated device to inspect its own inactive session history while keeping the default inventory limited to active sessions.

## Delivered
- `/v1/session/list` accepts optional boolean `include_inactive`.
- Default remains `false`.
- Revoked and expired sessions are returned only for the authenticated device when requested.
- Response includes `summary.total`, `summary.active`, and `summary.inactive`.
- Invalid non-boolean history flags return `400`.
- Session inventory exposes no device secrets, refresh tokens, or secret hashes.

## Security invariants
- Historical visibility grants no ability to revive or modify inactive sessions.
- Device/session binding remains enforced.
- Per-session revocation invalidates both access and refresh paths.
- Emergency-stop and existing protected-action controls remain intact.
