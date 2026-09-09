# ZYRA AI — Mission 64
## Android Session Lifecycle

Mission 64 adds the Android-side lifecycle around the real PC session API.

### App flow
- Restore a persisted session on app start.
- Use the existing session when still active.
- Refresh it through the one-time rotating refresh token when needed.
- If refresh fails, clear stale credentials and create a fresh session after
  the device is still enrolled/trusted.
- Logout calls the PC API and clears local session state.

### Credential storage
`SecureSessionStorage` is deliberately a storage contract. The production
Android implementation must be backed by Android Keystore-encrypted storage;
the included in-memory implementation is for tests/development only.

### Recovery
The session ID and rotating refresh token are persisted by the Android layer,
so normal app/process restarts do not require pairing again.
