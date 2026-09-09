# Mission 84 — Windows Bootstrap and Health Diagnostics

## Added

- Environment dependency checker with required and optional voice dependencies
- `/health` endpoint for local desktop readiness
- `/v1/system/diagnostics` endpoint
- Non-installing bootstrap diagnostic script
- Electron startup waits for backend health before opening the shell
- npm diagnostics command
- Required dependency checks for Python, FastAPI, and Uvicorn
- Optional voice checks for sounddevice, faster-whisper, and pyttsx3

## Behavior

Diagnostics report missing dependencies but never install packages or download
models automatically. This avoids an unexpected network/model download during
first launch.

The desktop shell continues to use loopback-only backend communication.

## Next

Mission 85 can add installer-friendly Python runtime detection and first-run
setup UI, then start the Windows beta packaging validation cycle.
