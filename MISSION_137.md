# MISSION 137 — Live Device Session Management UI

## Scope

Turn the Flutter Devices tab into a real client for the authenticated session inventory and per-session revocation APIs delivered in Mission 136.

## Delivered

- Added a dedicated Devices screen backed by `ZyraService`.
- Added device ID and current session ID inputs without any device-secret or refresh-token field.
- Added active/inactive session inventory loading through `/v1/session/list`.
- Added total, active, and inactive session counters.
- Added current-session identification and read-only inactive-session presentation.
- Added explicit confirmation before per-session revocation through `/v1/session/revoke`.
- Prevented the UI from offering revocation for the current session.
- Added honest loading, empty, and API-error states instead of reporting a fabricated online state.

## Security

The UI accepts only the existing authenticated `device_id` + `session_id` context. It does not store or transmit device secrets, refresh tokens, or secret hashes. Authorization remains server-side and same-device restrictions are not bypassed by the client.
