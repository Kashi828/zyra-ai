# Mission 30 — Unified Authorization Gateway

Mission 30 adds a single authorization boundary for API and remote actions.

## What changed
- Session validation is required before action authorization.
- Device identity must match the authenticated session device.
- Device capability and trust policies are enforced centrally.
- Rate limiting is enforced before an action reaches an executor.
- Sensitive capabilities are marked as requiring confirmation.
- The gateway authorizes only; it never executes tools.

## Security boundary
`request -> session -> device identity -> capability/trust policy -> rate limit -> confirmation flag -> executor`

Remote access remains subject to the transport security and deployment requirements from previous missions.
