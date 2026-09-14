# Mission 147 — NodeMCU transport contract validation

## Objective

Lock down the software-side command path from an enrolled ZYRA runtime to the bounded NodeMCU HTTP agent before Beta 5 hardware testing.

## Implemented

- Added transport-level tests for the existing `NodeMCUTransport`.
- Verified allowlisted `status` requests are sent as HTTP POST requests to `/v1/status`.
- Verified the configured `X-Zyra-Device-Secret` header is transmitted without persisting credentials in the transport.
- Verified `gpio.write` boolean values are normalized to the firmware's integer `0`/`1` contract.
- Verified invalid non-loopback HTTP endpoints are rejected when TLS is required.
- Verified non-allowlisted actions such as `shell` are rejected before any network request.
- Verified malformed `gpio.write` requests are rejected before network access.

## Existing firmware contract

The NodeMCU firmware exposes only `/v1/status`, `/v1/gpio.read`, and `/v1/gpio.write`, requires the device-secret header, bounds JSON request size, rejects unknown fields, and allowlists GPIO pins D1/D2. See `iot/nodemcu/zyra_nodemcu_firmware.ino`.

## Security invariant

Network reachability is not authorization. The ZYRA runtime must authorize the operation first, and the NodeMCU remains independently authenticated and allowlisted. No shell, arbitrary code, or arbitrary GPIO operation is introduced by this mission.

## Beta 5 acceptance gate

1. Python transport contract tests pass in CI.
2. Android and Windows client builds remain green.
3. Runtime-to-NodeMCU mapping is exercised with a fake transport before physical hardware is used.
4. Physical NodeMCU testing is performed only after the above software gates pass.

Physical hardware connectivity is **not claimed by this mission**; it requires the actual NodeMCU device and a configured network/secret.
