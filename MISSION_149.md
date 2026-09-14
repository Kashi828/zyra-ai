# Mission 149 — Enrolled NodeMCU capability boundary

## Objective

Strengthen the runtime-facing NodeMCU bridge so a caller cannot exercise a capability that is not also enrolled on the target NodeMCU device.

## Implemented

- `NodeMCUCommandBridge` now checks the caller capability set.
- The bridge also checks the enrolled device capability set before transport access.
- Unknown NodeMCU actions remain rejected before transport access.
- Existing routing through `NodeMCUAdapter` is unchanged.
- Added a regression test proving an un-enrolled `iot.gpio` capability cannot reach transport even when the caller presents that capability.

## Security boundary

The bridge is a secondary capability boundary, not an authentication replacement. Upstream authenticated session validation remains authoritative. The enrolled NodeMCU device capabilities provide an additional device-side authorization constraint, and the NodeMCU transport/firmware still independently enforces device-secret authentication and hardware action allowlists.

## Beta 5 gate

This mission improves the software authorization path required for Beta 5 NodeMCU testing. It does not claim physical hardware connectivity, flashing, or end-to-end hardware success.
