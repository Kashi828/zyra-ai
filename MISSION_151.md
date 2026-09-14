# Mission 151 — Beta 5 NodeMCU hardware gate

## Objective

Define the final software-side contract that must pass before physical NodeMCU testing is treated as a Beta 5 validation result.

## Required software checks

1. The NodeMCU adapter accepts only `status`, `gpio.read`, and `gpio.write`.
2. The transport sends the enrolled device secret using `X-Zyra-Device-Secret`.
3. The bridge checks both caller capability and the enrolled NodeMCU capability.
4. The authenticated runtime path validates the device/session before dispatching IoT work.
5. GPIO requests are constrained by the existing transport/firmware contract.

## Physical Beta 5 procedure

After the software gate is green, connect an actual NodeMCU to the test network and verify:

- the device receives a stable enrolled endpoint;
- `/v1/status` returns valid device telemetry;
- `/v1/gpio.read` returns the expected pin state;
- an allowlisted `gpio.write` changes the selected test output;
- a wrong device secret is rejected;
- a non-allowlisted action is rejected;
- an unauthorized capability never reaches the device.

Use a low-risk test output such as an LED/resistor or another isolated indicator. Do not connect the first test to mains or hazardous loads.

## Evidence required for Beta 5 hardware sign-off

Record the firmware revision, NodeMCU model, enrolled device ID, endpoint, test results, and timestamps. Software CI success alone is not physical hardware validation.

## Security invariant

Physical connectivity must never bypass ZYRA session authentication, capability authorization, device-secret authentication, or the NodeMCU action allowlist.

## Current status

The software contract is implemented and testable. **Physical NodeMCU validation has not been performed or claimed by this mission.**
