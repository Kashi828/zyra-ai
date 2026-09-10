# Mission 135 — Session Inventory Lifecycle Visibility

## Scope
Complete the session-management visibility work started in Mission 134 by allowing an authenticated device to request its own inactive session history, while keeping the default inventory limited to active sessions.

## Delivered
- `/v1/session/list` accepts an optional `include_inactive` boolean.
- The default remains `false`, preserving the existing active-session inventory behavior.
- When enabled, revoked or expired sessions belonging to the authenticated device are returned with their existing lifecycle state.
- The response includes `summary.total`, `summary.active`, and `summary.inactive` counts.
- The caller's session remains marked as `current` when it is active.
- Invalid non-boolean `include_inactive` values return `400` rather than being silently coerced.
- Session inventory remains strictly device-scoped; another device's sessions are never exposed.
- Session inventory does not expose device secrets, refresh tokens, secret hashes, or other credential material.

## Security invariants
- No arbitrary shell execution is introduced.
- Session authorization remains durable and bound to `device_id`.
- Only the authenticated device can enumerate its session inventory.
- Historical visibility does not grant authority to revive or modify inactive sessions.
- Per-session revocation continues to invalidate both access and refresh credentials.
- Emergency-stop and existing protected-action authorization controls remain untouched.
- Audit logging remains credential-safe.

## Verification
The Mission 135 regression suite is `tests/test_mission135_session_inventory.py`. CI remains the source of truth for the full repository test suite.
