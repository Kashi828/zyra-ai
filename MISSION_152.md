# Mission 152 — Simulated NodeMCU end-to-end gate

## Objective

Provide a deterministic CI-side simulation of the Beta 5 IoT path before physical hardware is connected.

## End-to-end path

`AuthenticatedNodeMCUCommand` → `PersistentAuthorizationGateway` → `NodeMCUCommandBridge` → `NodeMCUAdapter` → simulated NodeMCU transport.

## Coverage

- authenticated telemetry reaches the simulated device;
- GPIO write/read round-trip preserves state;
- invalid sessions are rejected before transport;
- unsupported actions are rejected before transport.

The harness uses a loopback endpoint only as metadata; it does not open a network listener and does not represent physical hardware.

## Beta 5 invariant

A passing simulation proves the software routing and authorization contract only. It does not prove Wi-Fi connectivity, firmware behavior, electrical GPIO behavior, or physical NodeMCU operation.
