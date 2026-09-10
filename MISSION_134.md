# Mission 134 — Session/Device Management Visibility & Controlled Per-Session Revocation

## Goal
Make authenticated session state visible to the owning device and add a narrowly scoped per-session revocation operation without weakening session isolation.

## Delivered
- Enriched `/v1/session/list` with authenticated device metadata.
- Session inventory marks the caller's session as `current` and reports whether returned sessions are `active`.
- Added `/v1/session/revoke` for controlled revocation of a selected session.
- Revocation requires a currently valid session and only permits targets owned by the same authenticated device.
- Foreign-device targets are hidden behind `404` and cannot be revoked.
- Already inactive targets return `409` rather than silently succeeding.
- Per-session revocation now invalidates both the session and every refresh credential associated with that session.
- Session creation, revocation, logout, and device revocation are recorded in the durable audit log without storing or exposing device secrets.
- Existing `/v1/session/logout` remains self-only.
- Regression coverage includes visibility, same-device revocation, cross-device isolation, missing/inactive targets, refresh-token invalidation, and audit safety.

## Security invariants
- No arbitrary shell execution is introduced.
- Device secrets remain hashed at rest and are never returned by session endpoints.
- Session authorization remains durable and bound to `device_id`.
- A valid session cannot manage another device's sessions.
- Revocation closes both access-session and refresh-token paths.
- Emergency-stop and existing authorization controls remain intact for protected device actions.
- Security lifecycle actions are auditable without recording credentials.

## Verification
The Mission 134 test suite is `tests/test_mission134_session_management.py`. CI remains the source of truth for the full repository test suite.
