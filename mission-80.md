# Mission 80 — Windows Desktop Runtime Bridge

## Added

- Native-host desktop session store under the user's local application/state directory
- Persistent desktop voice session lifecycle
- Automatic refresh of near-expiry session credentials
- Logout that invalidates the server session and clears local state
- Loopback-only native API client
- Windows desktop launcher entry point
- Explicit native-host separation so refresh tokens do not need to live in the web UI

## Security

The desktop launcher binds the ZYRA API to `127.0.0.1` when it launches the
backend. The runtime bridge communicates through loopback and keeps the refresh
token outside the browser-facing JavaScript state.

The existing authorization, approval, and command controls remain unchanged.

## Packaging note

This mission adds the native runtime bridge and launcher, but it is not yet a
signed Windows `.exe` installer. Packaging/signing will be handled after the
runtime API surface is complete.

## Next

Mission 81 can make the voice UI consume the native bridge lifecycle and begin
the Windows beta packaging path.
