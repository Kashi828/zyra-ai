# Mission 82 — Windows Packaged Shell Foundation

## Added

- Electron Windows shell scaffold
- Hardened `BrowserWindow` configuration:
  - context isolation
  - sandbox
  - no renderer Node.js integration
- Narrow preload bridge exposed as `window.zyraDesktopBridge`
- Native bridge calls for voice session, auth headers, logout, and health
- Local backend startup on `127.0.0.1`
- NSIS x64 packaging configuration with Electron Builder
- Renderer now prefers the native bridge for voice auth

## Packaging

The source tree now has a repeatable Electron/Electron Builder configuration,
but this mission does **not** claim that an `.exe` was built in this environment.
The next packaging step should install the pinned npm dependencies and produce
a Windows installer on a Windows build runner.

## Security

The renderer cannot directly access Node APIs. Native capabilities are exposed
through a small allowlisted preload API. The Windows shell is configured to
request only microphone permission from Electron's permission callback, and the
local backend binds to loopback.

## Next

Mission 83 can add a proper local backend process supervisor with health checks,
graceful shutdown, port selection, and installer-time dependency handling.
