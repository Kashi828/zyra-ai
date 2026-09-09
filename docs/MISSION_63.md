# ZYRA AI — Mission 63
## Session Refresh, Rotation + Logout

ZYRA now supports durable short-lived sessions with one-time refresh token
rotation.

### Flow
Create session → short-lived access session + refresh token
→ refresh → old token consumed → new session + replacement token

### Security
- Refresh tokens are stored only as SHA-256 hashes.
- Tokens are bound to device identity.
- Refresh tokens are single-use.
- Reuse is rejected instead of creating another live session.
- Logout revokes the session and its refresh token.
- Device logout revokes the device and its sessions.
- State persists in the existing SQLite security database.
