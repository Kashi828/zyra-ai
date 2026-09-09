# ZYRA AI — Mission 60
## Persistent Authorization Enforcement

Mission 60 makes the durable security store authoritative for remote Windows
command authorization while preserving the Mission 41 bridge interface for
existing consumers.

### Authoritative path

`device_id + session_id + registered action`
→ resolve backend tool capability
→ persistent device lookup
→ persistent session validation
→ revocation check
→ capability check
→ Windows tool execution

A client cannot supply its own capability set when the persistent gateway is
configured. The backend derives the required capability from the registered
tool.

### Compatibility
The older in-memory bridge mode remains available for existing callers and
tests. Production runtime wiring should use `auth_gateway=PersistentAuthorizationGateway(...)`.

### Security
Revoked devices and invalid/expired sessions are denied before the Windows
runner is reached. Public remote access remains disabled by default.
