# ZYRA AI — Mission 94

## Unified runtime-ready contract

- Added a single runtime readiness service for the desktop shell.
- Added a workspace context service that exposes only non-secret configuration summary.
- Added `/v1/setup/runtime-ready`.
- Added `/v1/setup/workspace-context`.
- Renderer can subscribe to runtime-ready and workspace-context lifecycle events.
- Runtime remains blocked until setup is complete and a model endpoint is configured.
