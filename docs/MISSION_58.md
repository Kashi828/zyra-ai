# ZYRA AI — Mission 58
## Enrollment → Authenticated Session Activation

Mission 58 closes the gap between pairing/enrollment and the authenticated
runtime session.

### Flow
1. Android completes one-time device enrollment.
2. The PC stores the enrollment secret in the device trust layer.
3. Android creates a short-lived nonce/timestamp proof.
4. The PC verifies the device-bound HMAC proof and replay guard.
5. The existing session infrastructure issues a short-lived session.
6. Subsequent commands can use the authenticated session instead of relying
   on the original pairing state.

### Security
- Session activation is device-bound.
- Proofs expire quickly and include a nonce.
- Reusing a nonce is rejected.
- The raw enrollment secret is not returned by the activation route.
- Production transport should remain TLS/mTLS protected when remote access is enabled.
