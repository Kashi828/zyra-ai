# ZYRA AI — Mission 53
## Desktop Runtime Integration

The desktop shell now has a functional API integration layer:
- submit an agent goal to `/v1/runtime/tasks`
- poll `/v1/runtime/state` for task/device state
- request an agent stop with `/v1/agent/stop`
- show device presence in the desktop status bar
- update the live activity panel from runtime state

The desktop uses the backend as the authority. UI state does not grant permissions
or bypass policy. The stop route is a control request; the existing runtime/security
layers remain responsible for enforcing the stop and action boundaries.
