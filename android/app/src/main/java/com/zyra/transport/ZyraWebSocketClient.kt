package com.zyra.transport

/**
 * Transport-neutral WebSocket client contract.
 *
 * Implement with the existing OkHttp WebSocket dependency in the Android app.
 * The session ID should be attached according to the server's authenticated
 * WebSocket protocol; the refresh token must never be sent over the socket.
 */
interface ZyraWebSocketClient {
    fun connect(session: AuthenticatedTransportSession)
    fun disconnect()
    fun sendText(message: String): Boolean
}

class SessionBoundWebSocketController(
    private val sessionAware: SessionAwareWebSocket,
    private val socket: ZyraWebSocketClient
) {
    fun connect(deviceId: String): AuthenticatedTransportSession {
        val session = sessionAware.authenticatedSession(deviceId)
            ?: throw IllegalStateException("no active ZYRA session")
        socket.connect(session)
        return session
    }

    fun reconnectAfterUnauthorized(deviceId: String): AuthenticatedTransportSession {
        socket.disconnect()
        val session = sessionAware.onTransportUnauthorized(deviceId)
            ?: throw IllegalStateException("unable to restore ZYRA session")
        socket.connect(session)
        return session
    }

    fun send(message: String): Boolean = socket.sendText(message)

    fun disconnect() = socket.disconnect()
}
