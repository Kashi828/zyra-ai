# Mission 34 — Secure Device Discovery & Pairing Offers

Mission 34 adds a local-first discovery/pairing primitive for the ZYRA ecosystem.

## Added
- Short-lived pairing offers with a unique offer ID and nonce.
- HMAC-SHA256 integrity signatures; device secrets are not embedded in the offer.
- Base64url transport encoding suitable for QR/deep-link or local-discovery handoff.
- Single-use consumption to prevent replay of a pairing offer.
- Strict TTL and payload-size limits.
- Windows/Android device kind validation.

## Security notes
The offer authenticates the pairing payload but is not a replacement for an authenticated TLS channel. Public network exposure still requires TLS, secure key storage, and server-side authorization.
