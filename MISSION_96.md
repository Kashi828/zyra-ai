# ZYRA AI — Mission 96

## Runtime health integration

- Added runtime health checks for API, model endpoint, and voice capability.
- Wired `RuntimeHealthService` into the FastAPI app factory.
- Exposed `/v1/runtime/health` through the existing runtime health route module.
- Added regression tests for configured/offline/degraded states.
- No installation, privilege escalation, or credential handling was added.
