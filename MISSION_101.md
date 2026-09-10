# Mission 101 — Self-contained Windows Beta Runtime

## Goal
Make the Windows beta installer carry its own Python backend and native bridge instead of requiring Python to be installed on the end-user machine.

## Implementation
- Added `scripts/bundle_windows_runtime.py`.
- PyInstaller builds separate onedir bundles for `zyra-backend` and `zyra-native-bridge`.
- Electron packaged builds prefer the bundled executables.
- Development builds retain the existing Python fallback.
- Electron Builder includes `runtime/**/*` in the installer payload.
- CI installs PyInstaller and builds the bundled runtime before creating the NSIS installer.

## Security boundary
The bundled runtime remains local to the Windows machine. Electron continues to use context isolation, disabled Node integration, sandboxed renderer content, and loopback-only backend binding.

## Beta limitation
The Android artifact remains a debug APK in this beta. Production signing/AAB publication is a separate release-hardening step.
