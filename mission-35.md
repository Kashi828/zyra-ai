# Mission 35 — Secure Pairing UX + Device Management

## Deliverables
- QR/deep-link pairing UX contract
- Explicit PC identity confirmation before enrollment
- Trusted-device list model
- Revocation/disconnect states
- No secrets embedded in pairing offers
- Android Keystore remains the storage boundary for private device material

## Product flow
PC creates offer -> Android scans -> Android shows PC identity/fingerprint -> user approves -> enrollment completes -> device appears in Trusted Devices -> user can revoke it later.
