# ZYRA AI — Mission 85

## First-run Windows setup + beta installer pipeline

Mission 85 turns the desktop shell into a safer first-run experience and prepares a reproducible Windows beta installer flow.

### Delivered

- Added `desktop/install_check.py` for non-destructive local environment checks.
- Added `GET /v1/system/setup-check` for the Electron setup screen.
- Added first-run setup UI with required vs optional components and explicit re-check/continue controls.
- Added Windows preparation script: `scripts/prepare_windows.ps1`.
- Added Windows installer build script: `scripts/build_windows.ps1`.
- Added npm aliases `prepare:win` and `build:win`.
- Fixed Electron Python executable selection precedence and centralized it in `pythonExecutable()`.
- Kept setup non-destructive: no automatic package installs, model downloads, or privileged operations.

### Release behavior

The repository now contains the configuration and scripts needed to produce `ZYRA-AI-Setup-<version>-x64.exe` on a Windows build machine with Node.js, npm, Python 3.11+, and the required Python environment available.

This Linux development environment does not produce or claim a Windows `.exe` artifact.

### Validation

- 226 pytest tests passed.
- Python source compilation passed.
- Electron `main.js` and `preload.js` syntax checks passed.
