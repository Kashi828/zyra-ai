# ZYRA AI — Mission 67
## Android HTTP + WebSocket Transport Adapters

Mission 67 connects the Android session lifecycle to concrete transport
contracts.

### HTTP
`ZyraHttpTransport` implements `SessionApi` for:
- `/v1/session/create`
- `/v1/session/refresh`
- `/v1/session/logout`

JSON body transport is used so refresh tokens are not placed in URLs.

### WebSocket
`ZyraWebSocketClient` is the socket abstraction and
`SessionBoundWebSocketController` obtains an active session from the session
manager before connecting or reconnecting.

Only the active session identifier/device identity crosses the transport
boundary. The refresh token remains inside session storage/lifecycle code.

### Build note
This environment does not contain a complete Android Gradle build, so Kotlin
compilation is not claimed here. Python regression tests verify the source
contracts and security boundaries.
