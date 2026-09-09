# ZYRA AI — Mission 59
## Persistent Device Trust + Sessions

Trusted-device records and authenticated sessions now survive PC process restarts
through a SQLite security store.

### Persisted
- Device identity
- SHA-256 hash of the device enrollment secret
- Device capability set
- Device revocation state
- Session ID and device binding
- Session expiry/revocation

### Recovery
A fresh process instance can reopen the database and validate the same trusted
devices and unexpired sessions. Device revocation also invalidates its sessions.

### Security note
Raw enrollment secrets are not persisted by this store. On a hardened Windows
deployment, protect the database path with OS filesystem permissions and use
encryption-at-rest when threat requirements call for it.
