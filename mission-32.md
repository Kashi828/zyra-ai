# Mission 32 — Unified Realtime Command Routing

Mission 32 connects the authenticated API authorization boundary with the realtime device hub.

## Highlights
- `communication/unified_router.py` centralizes authenticated command dispatch.
- Every command is checked against the session/device gateway before execution.
- Source/target device and capability mismatches are rejected.
- Sensitive capabilities require explicit confirmation.
- Only explicitly registered capability executors can run.
- Offline targets are rejected instead of being silently executed elsewhere.
- No unrestricted remote shell surface is introduced.

## Production note
The realtime transport remains localhost-first unless hardened remote TLS/authentication is explicitly enabled. The Android app should use the same authenticated route rather than a separate privileged path.
