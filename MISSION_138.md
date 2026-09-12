# Mission 138 — Authenticated Flutter Remote Action Bridge

## Goal
Connect the Flutter Home surface to the production authenticated Windows command bridge without introducing arbitrary command execution or client-side secret storage.

## Delivered
- Added `ZyraService.executeRemoteCommand(...)` for `POST /v1/remote/commands`.
- Requests carry only `device_id`, `session_id`, action, payload, and an optional command ID.
- Added platform-aware local API defaults: Android emulator uses `10.0.2.2:8000`; desktop uses `127.0.0.1:8000`.
- Added `ZYRA_API_URL` build-time override for non-local deployments.
- Added connection timeouts and readable API/network errors.
- Updated the Home quick actions to use the authenticated bridge for `open_app`, `open_folder`, and `open_url`.
- Folder and URL values are collected explicitly; the server remains authoritative for validation and capability checks.
- Free-form Home text is not translated into shell commands. Until an intent router exists, only the explicit allowlisted actions can execute remotely.
- Home displays the latest protected action result and API connection state.

## Security invariants
- No device secret or refresh token is accepted or stored by the Flutter session context.
- The backend remains authoritative for device/session authorization and capability enforcement.
- Windows execution remains restricted to the existing `WindowsCommandRegistry`; arbitrary shell execution is not exposed.
- Unsupported actions are rejected by the server.
