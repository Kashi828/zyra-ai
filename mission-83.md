# Mission 83 — Windows Backend Process Supervision

## Added

- `desktop/backend_supervisor.py`
  - loopback-only uvicorn command construction
  - startup health polling
  - startup timeout
  - bounded restart policy
  - graceful terminate/wait with kill fallback
- Electron shell restart handling for unexpected backend exit
- Bounded automatic backend restarts (two attempts)
- Tests for process lifecycle and health behavior

## Security

The backend supervisor only binds the desktop API to `127.0.0.1`. Automatic
restarts are bounded to avoid restart loops. No public network listener is
introduced.

## Packaging status

The project still contains the Windows installer configuration from Mission 82.
An actual signed `.exe` is not claimed until a Windows build environment runs
the Electron Builder pipeline.

## Next

Mission 84 can add installer dependency checks, first-run environment setup,
and a single command that launches the backend + native voice bridge + shell
with health-aware startup.
