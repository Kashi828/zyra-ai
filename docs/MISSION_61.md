# ZYRA AI — Mission 61
## Production FastAPI Security Wiring

The persistent device/session/capability authorization layer is now attached
to the FastAPI application factory.

### Runtime path

FastAPI startup
→ persistent security store
→ persistent authorization gateway
→ remote command route
→ registered Windows tool
→ backend-derived capability
→ execution

The route does not accept a client-provided capability list as an authorization
source.

### Operational default
`data/zyra_security.sqlite3` is the default security database path. Remote
access is still subject to the existing local-first configuration and transport
controls; this mission only removes the possibility of accidentally omitting
the persistent authorization dependency when constructing the API app.
