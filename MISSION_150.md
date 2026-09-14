# Mission 150 — Authenticated NodeMCU runtime path

## Objective

Connect the authoritative persistent session/capability authorization layer to the existing capability-aware NodeMCU bridge.

## Runtime path

```text
Android / Windows client
        ↓
Authenticated session
        ↓
PersistentAuthorizationGateway
        ↓
NodeMCUCommandBridge
        ↓
NodeMCUAdapter
        ↓
NodeMCU transport / firmware
```

## Implemented

- Added `AuthenticatedNodeMCUCommandExecutor`.
- NodeMCU action-to-capability mapping is selected by the backend.
- Persistent session and device authorization happens before bridge execution.
- The bridge receives capabilities from the trusted device record rather than client-supplied authority.
- Invalid/expired sessions and missing enrolled capabilities are rejected before transport.
- Added regression tests for successful status routing, invalid sessions, missing GPIO capability, and expired sessions.

## Security invariant

A client cannot elevate itself by declaring a capability in its request. The backend derives the required capability from the allowlisted NodeMCU action, validates the durable device/session relationship, then passes only the trusted device capabilities to the bridge. The NodeMCU transport and firmware remain independent enforcement layers.

## Beta 5 gate

This completes the software-level authenticated runtime-to-NodeMCU command path. It does not claim physical NodeMCU connectivity. Beta 5 hardware validation still requires a real enrolled board, firmware, network endpoint, device secret, and an end-to-end test on the user's hardware.
