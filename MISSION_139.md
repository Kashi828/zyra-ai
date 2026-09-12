# Mission 139 — Flutter Service Contract Verification

## Goal
Make the authenticated Flutter command bridge regression-testable before every Android and Windows beta build.

## Delivered
- Added a loopback HTTP integration test for `ZyraService.executeRemoteCommand`.
- Verifies the protected `/v1/remote/commands` path and authenticated `device_id` / `session_id` fields.
- Verifies the allowlisted action and structured payload are transmitted unchanged.
- Verifies command IDs are propagated.
- Verifies successful command responses are parsed into `ZyraCommandResult`.
- Verifies protected API errors preserve the HTTP status and server detail through `ZyraApiException`.
- CI now runs `flutter test` after `flutter analyze` and before producing Android/Windows beta artifacts.

## Security invariants
- Tests use only synthetic device/session identifiers.
- No device secret or refresh token is introduced.
- The test server is loopback-only and exists only for the test process.
- The client test does not grant or bypass backend authorization; it verifies that authorization context is transmitted correctly.
