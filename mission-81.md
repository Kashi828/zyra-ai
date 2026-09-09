# Mission 81 — Desktop Voice Bridge Integration

## Added

- Native stdio JSON bridge at `desktop/native_bridge.py`
- Bridge operations for ping, persistent voice session, auth headers, and logout
- Browser UI now prefers `window.zyraDesktopBridge`
- Desktop JavaScript no longer persists refresh tokens
- Existing loopback bootstrap remains as a development fallback
- Launcher exposes the native bridge entry point
- Security tests verify that refresh tokens are not returned to the browser bridge contract

## Security

The native bridge is intentionally narrow: it exposes session identity and
short-lived auth headers, not refresh tokens. Refresh-token storage and
rotation remain in the native runtime layer.

The browser fallback keeps only device/session IDs needed for the current local
session and does not persist the refresh token.

## Next

Mission 82 can add the actual packaged Windows shell host (Electron/Tauri or a
native WebView host), expose `window.zyraDesktopBridge`, and produce the first
repeatable Windows beta build pipeline.
