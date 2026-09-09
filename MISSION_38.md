# ZYRA AI — Mission 38
## Secure Session Activation

Mission 38 adds short-lived authenticated device sessions after pairing.

### Flow
Android pairs with the PC -> enrollment establishes the device identity -> a short-lived session is issued -> Android signs requests with the device secret -> PC verifies the session -> expiry requires re-activation.

### Security
- Sessions are short-lived by default.
- A session is bound to a device identity.
- HMAC-SHA256 authenticates the session proof.
- Expired sessions are rejected.
- A wrong device secret is rejected.
- Session IDs contain no secret material.
- Session state should be stored server-side and revocable.
- Production remote transport remains TLS/mTLS protected.
