package com.zyra.transport

import com.zyra.session.DeviceSession
import com.zyra.session.SessionManager

/**
 * Session-aware connection coordinator.
 * The caller owns scheduling; this class supplies refreshed sessions and a
 * bounded retry policy so reconnect work never blocks OkHttp callbacks.
 */
class SessionAwareWebSocket(
    private val sessionManager: SessionManager,
    private val reconnectPolicy: WebSocketReconnectPolicy = WebSocketReconnectPolicy()
) {
    fun authenticatedSession(deviceId: String): AuthenticatedTransportSession? {
        val active: DeviceSession = sessionManager.ensureActive(deviceId)
        return AuthenticatedTransportSession.from(active)
    }

    fun onTransportUnauthorized(deviceId: String): AuthenticatedTransportSession? =
        authenticatedSession(deviceId)

    fun reconnectAllowed(attempt: Int): Boolean =
        reconnectPolicy.shouldRetry(attempt)

    fun reconnectDelayMs(attempt: Int): Long =
        reconnectPolicy.delayMs(attempt)

    fun logout(): Boolean = sessionManager.logout()
}
