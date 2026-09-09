# ZYRA AI — Mission 39
## Android ↔ PC Session Activation

Mission 39 connects the enrolled-device identity to a short-lived authenticated session.

### Session flow
1. Android loads the enrolled PC/device identity.
2. Android requests session activation.
3. PC verifies device trust and issues a short-lived session proof.
4. Android keeps session state locally and uses it for authorized commands.
5. Expired/revoked sessions are rejected.
6. Android can sign out and re-activate a session without re-pairing.

### Security boundaries
- Session identity is bound to the enrolled device.
- Expired sessions cannot execute commands.
- Revoked sessions are terminal.
- Android private credential material remains in Keystore-backed storage.
- Remote transport remains TLS-protected in production.
