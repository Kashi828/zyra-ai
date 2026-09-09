# ZYRA AI — Mission 69
## Unified Realtime Event Stream

Mission 69 connects the authenticated Android WebSocket to one server-side
realtime event hub.

### Event envelope
The common event includes:
- event ID/type
- device ID
- optional task/command/transfer IDs
- status
- payload

### Server
`/v1/realtime/ws` requires the durable device-bound session. Authenticated
clients receive a connected event and subscribed events through a bounded
queue.

Remote command completion/failure is published into the same event stream.

### Android
The OkHttp client now parses JSON event envelopes and forwards them through
`RealtimeEventListener`, while presence is updated from socket state.

### Security
Only the active session ID is sent over the WebSocket. Refresh tokens remain
outside the socket. Queue size is bounded to prevent unbounded memory growth.
