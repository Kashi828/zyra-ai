# Mission 36 — Actual Pairing Flow

Mission 36 connects the secure pairing protocol to a user-confirmed enrollment flow.

## Flow
1. Windows creates a short-lived signed offer.
2. ZYRA turns it into a `zyra://pair?offer=...` deep link suitable for a QR payload.
3. Android parses the deep link and shows the PC identity/endpoint preview.
4. The user explicitly confirms the PC pairing.
5. The Windows service enrolls the Android device and returns a one-time device secret.
6. The Android app stores that secret in its existing Keystore-backed secret store.

Pairing offers contain metadata, not the long-lived device secret. The offer is short-lived and single-use.
