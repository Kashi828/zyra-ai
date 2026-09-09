# ZYRA AI — Mission 68
## Concrete OkHttp WebSocket + Presence

Mission 68 adds a concrete Android WebSocket implementation around the existing
session-aware transport contracts.

### Transport
`OkHttpZyraWebSocketClient`:
- uses OkHttp WebSocket
- attaches the active session ID as a Bearer credential
- attaches the device identity
- sends no refresh token to the socket
- uses a 20-second WebSocket ping interval
- exposes explicit connection states
- forwards server messages to the app layer

### Recovery
`WebSocketReconnectPolicy` provides bounded exponential backoff:
1s, 2s, 4s, ... up to 30s, with a maximum retry count.

`SessionAwareWebSocket` obtains/refreshes the authenticated session before
reconnect, keeping credential refresh outside the socket callback itself.

### Presence
`PresenceHeartbeat` maps the socket lifecycle to an online/offline device
presence sink for the Android UI/runtime.

### Build note
This environment does not contain a complete Android Gradle project, so Kotlin
compilation is not claimed here. Source-contract regression tests were run
against the cumulative repository.
