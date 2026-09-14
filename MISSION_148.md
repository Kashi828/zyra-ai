# Mission 148 — NodeMCU runtime command bridge

## Objective

Connect the existing enrolled NodeMCU adapter to a capability-aware runtime-facing command bridge without introducing arbitrary code execution.

## Implemented

- Added `core/nodemcu_command_bridge.py`.
- Mapped `status` and `gpio.read` to `iot.telemetry`.
- Mapped `gpio.write` to `iot.gpio`.
- Unknown actions are rejected before transport access.
- Missing capabilities are rejected before transport access.
- Successful calls remain routed through the existing enrolled `NodeMCUAdapter`.
- Added fake-transport tests covering telemetry, GPIO authorization, unknown-action rejection, and successful GPIO routing.

## Security boundary

The bridge is not an authentication replacement. Session authorization remains upstream at the authenticated command/runtime boundary, while the capability check prevents a caller from using a NodeMCU transport without the corresponding enrolled capability. The NodeMCU firmware independently authenticates its device secret and enforces its own hardware allowlist.

## Beta 5 gate

This mission establishes the software-side runtime-to-NodeMCU mapping needed before physical hardware testing. It does not claim that a physical NodeMCU has been connected or flashed successfully.
