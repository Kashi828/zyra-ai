# ZYRA AI — Mission 41
## Real Windows Tool Registry + Remote Bridge

Remote commands now terminate at an explicit Windows tool registry.

Supported initial actions:
- open_app
- open_folder
- open_url

Each action has a named capability such as `pc.apps`, `pc.files`, or `pc.web`.
Remote execution requires a valid device session and the corresponding capability.

Arbitrary remote shell execution is intentionally not exposed through this bridge.
The Windows runtime implementations should only be enabled on actual Windows hosts.
