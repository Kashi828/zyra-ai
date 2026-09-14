# Mission 153 — Automated NodeMCU E2E CI Gate

## Objective
Make the Mission 152 simulated NodeMCU end-to-end harness an explicit, deterministic CI gate for the Beta development branch.

## Changes
- Added `beta` to the push trigger of `.github/workflows/zyra-beta-ci.yml` so beta commits receive direct CI validation.
- Added a dedicated `NodeMCU simulated E2E gate` step that runs `tests/test_mission_152_nodemcu_e2e_harness.py`.
- Kept the complete Python regression suite and compile checks intact.
- Android and Windows build jobs remain part of the same beta CI workflow.

## Validated software path
`AuthenticatedNodeMCUCommand → PersistentAuthorizationGateway → NodeMCUCommandBridge → NodeMCUAdapter → simulated NodeMCU transport`

The dedicated gate covers authenticated status delivery, GPIO write/read round-trip behavior, invalid-session rejection before transport, and unsupported-action rejection before transport.

## Security invariant
The simulated E2E gate validates the software authorization chain but does **not** replace physical hardware validation. Client reachability cannot authorize commands, caller capability cannot be self-declared, and NodeMCU transport/firmware enforcement remains an independent boundary.

## Beta 5 status
This mission establishes the automated software-side IoT CI gate. Physical NodeMCU testing has not been performed and is still required before claiming hardware-validated Beta 5 readiness.
