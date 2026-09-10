# Mission 134 — Session/Device Management Visibility & Controlled Per-Session Revocation

## Goal
Make authenticated session state visible to the owning device and add narrowly scoped per-session revocation without weakening session isolation.

## Delivered
- Enriched `/v1/session/list` with authenticated device metadata.
- Session inventory marks the caller's session as `current` and reports `active` state.
- Added `/v1/session/revoke` for controlled revocation of a selected session.
- Revocation only permits targets owned by the same authenticated device.
- Foreign-device targets return `404`; inactive targets return `409`.
- Per-session revocation invalidates both the access session and associated refresh credentials.
- Session creation, revocation, logout, device revocation, and command completion are auditable without credentials.

## Security invariants
- No arbitrary shell execution is introduced.
- Device secrets remain hashed and are never returned by session endpoints.
- Session authorization remains durable and bound to `device_id`.
- A valid session cannot manage another device's sessions.
- Emergency stop remains fail-closed for protected actions.
- Audit logging does not record secrets or refresh tokens.
