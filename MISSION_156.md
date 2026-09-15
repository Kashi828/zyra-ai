# Mission 156 — NodeMCU transport integration

## Objective

Align the enrolled NodeMCU adapter with the concrete HTTP transport contract so the runtime bridge can reach a real device without a signature mismatch.

## Change

`NodeMCUAdapter.execute()` now forwards `action` and `payload` using the transport's actual request contract. The enrolled endpoint remains part of the device binding and is validated when the adapter is created.

## Regression coverage

A dedicated integration test verifies that an allowlisted GPIO command crosses the adapter boundary with the expected action and payload.

## Security invariant

This is an interface correction, not an authorization bypass. The authenticated executor and capability bridge remain upstream of the adapter, and the transport retains its action allowlist, device-secret header, endpoint/TLS checks, and GPIO validation.

## Beta 5 status

Software integration is now structurally aligned for the real transport path. CI must still pass, and physical NodeMCU testing remains a separate validation step.
