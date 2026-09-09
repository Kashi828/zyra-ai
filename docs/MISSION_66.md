# ZYRA AI — Mission 66
## Android Session + Transport Integration

Mission 66 makes the Android Keystore session implementation the default path
for the application-facing session manager.

### Runtime flow
App start
→ `SessionManager.restore()`
→ if necessary `ensureActive(deviceId)`
→ encrypted Keystore-backed credentials
→ rotating refresh when the access session expires
→ authenticated transport session
→ WebSocket reconnect can recover the session without re-pairing.

### Transport boundary
`AuthenticatedTransportSession` exposes only the active device ID, session ID,
and expiry to the transport layer. The secure refresh token remains inside the
session lifecycle/storage layer.

### Note
The repository currently contains Kotlin source scaffolding rather than a
verifiable Android Gradle build in this environment. Python regression tests
cover the integration contracts; Android compilation should be run in Android
Studio/Gradle on the target project.
