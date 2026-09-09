# Mission 23 — Secure Remote Access Foundation

Mission 23 adds a remote-access security layer without opening ZYRA to the public internet by default.

## Added
- TLS 1.2+ server/client context builders.
- Optional mutual TLS via a configured CA and client certificate.
- Explicit remote-access policy (`enabled`, TLS requirement, device-auth requirement).
- Short-lived enrollment challenges and HMAC signatures.
- Replay protection and rate limiting for enrollment/message authorization.
- A remote-session authorizer that only decides whether an action may proceed; it does not execute OS actions.

## Production deployment requirements
1. Use certificates from a trusted private CA or a suitable public PKI for the actual hostname.
2. Store private keys outside the repository with OS-backed protection.
3. Keep `ZYRA_ALLOW_REMOTE_CONTROL=false` until a secure deployment is configured.
4. Do not expose the raw local agent port directly to the internet.
5. Place internet-facing access behind a hardened TLS terminator/relay and require device authentication.
6. Keep high-risk tool calls behind ZYRA's existing confirmation and policy engine.
