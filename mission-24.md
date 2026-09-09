# Mission 24 — Device Identity & Trust

Mission 24 adds persistent identity and trust management for authorized ZYRA devices.

## Features
- Persistent Windows/Android device identities in SQLite.
- Per-device random secret, stored only as a PBKDF2-HMAC-SHA256 verifier.
- Session expiry and revocation.
- Explicit capability allowlists.
- Trust levels: untrusted, standard, trusted.
- Sensitive remote capabilities require trusted devices.
- Authorization updates `last_seen` for activity tracking.

## Security notes
- Device secrets are not stored in plaintext by the identity store.
- Revocation immediately invalidates authorization.
- Capability checks happen before a sensitive action is accepted.
- This is an identity/policy layer, not a replacement for TLS. Remote transport should remain protected by TLS/mTLS in deployments that leave the local machine.
