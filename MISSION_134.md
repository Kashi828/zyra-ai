# Mission 134 — Session/Device Management Visibility & Controlled Per-Session Revocation

## Goal
Make authenticated session state visible to the owning device and add a narrowly scoped per-session revocation operation without weakening session isolation.

## Delivered
- Enriched `/v1/session/list` with authenticated device metadata.
- Session inventory now marks the caller's session as `current` and reports whether each returned session is `active`.
- Added `/v1/session/revoke` for controlled revocation of a selected session.
- Revocation requires a currently valid session and only permits targets owned by the same authenticated device.
- Foreign-device targets are hidden behind `404` and cannot be revoked.
- Already inactive targets return `409` rather than silently succeeding.
- Existing `/v1/session/logout` remains self-only and retains its existing semantics.
- Added regression coverage for visibility, same-device revocation, foreign-device isolation, missing targets, and inactive targets.

## Security invariant
A valid session may manage only sessions belonging to its own `device_id`. No endpoint introduced by this mission accepts an arbitrary device credential as authority to revoke a different device's session.

## Verification
The Mission 134 test suite is `tests/test_mission134_session_management.py`. CI remains the source of truth for the full repository test suite.
