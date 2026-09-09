# ZYRA AI — Mission 97

## Runtime health integration

- Bound runtime health to the persisted model endpoint configuration.
- Exposed the runtime health service through the FastAPI application.
- Added a desktop runtime-health client with automatic refresh.
- Corrected the desktop health client to use `/v1/runtime/health`.
- Runtime health reports API, model, voice, and overall runtime state without exposing credentials.
