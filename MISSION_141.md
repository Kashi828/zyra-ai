# Mission 141 — Platform-Aware Windows Connection Contract

## Goal
Define the next Beta 5 integration boundary for connecting the modern Flutter client to the Windows ZYRA runtime without weakening backend authorization.

## Scope
- Android and Windows clients use the existing ZYRA service/session architecture.
- Connection discovery and probing remain platform-aware.
- A successful network probe must not be treated as authentication.
- Protected commands continue to require the current authenticated device/session context.
- UI connection state must distinguish API reachability, Windows reachability, and authenticated readiness.

## Beta 5 acceptance criteria
- Flutter client can represent Windows connection states explicitly.
- Failed discovery/probe produces actionable UI feedback without exposing credentials.
- Authenticated remote commands remain blocked when session credentials are absent or invalid.
- Android and Windows builds remain green in CI.
- NodeMCU integration is tested only through the authorized runtime path.

## Security invariants
- Backend authorization remains authoritative.
- LAN reachability never grants command authorization.
- Device secrets and refresh tokens are not persisted by the Flutter session context.
- Only allowlisted remote actions may be dispatched by the current client surface.
