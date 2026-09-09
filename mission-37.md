# Mission 37 — Persistent Android Enrollment

Mission 37 replaces ephemeral pairing state with a durable Android enrollment record.

## Included
- Enrolled PC metadata persisted locally.
- Device secret stored through Android Keystore-backed `SecretStore`.
- Revocation persisted and treated as terminal until a new enrollment.
- Endpoint validation allows WSS for remote transport and loopback WS for local development.
- Missing/undecryptable secrets make the enrollment unavailable rather than falling back to plaintext.

## Security model
The metadata store does not write the device secret into SharedPreferences. The secret is encrypted using the Keystore-backed storage abstraction already present in the app. A future hardened release should also use `EncryptedSharedPreferences`/Jetpack Security or an equivalent platform-supported encrypted store for non-secret metadata where appropriate.
