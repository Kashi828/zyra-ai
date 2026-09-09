# ZYRA AI — Mission 95

## Runtime health aggregation

- Added a read-only runtime health service for API, model, voice, and overall runtime state.
- Local model endpoints are probed with a short timeout; non-local endpoints are treated as configured rather than probed.
- Added `/v1/setup/runtime-health` and a renderer health event helper.
- Added regression coverage for health response shape and local-only probing.
- No credentials or remote-control privileges are exposed by the health layer.
