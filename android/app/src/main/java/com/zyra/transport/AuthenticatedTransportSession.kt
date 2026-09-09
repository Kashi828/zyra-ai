package com.zyra.transport

import com.zyra.session.DeviceSession

/**
 * Transport-facing view of the currently authenticated ZYRA session.
 * A transport client should only use an active sessionId supplied here.
 */
data class AuthenticatedTransportSession(
    val deviceId: String,
    val sessionId: String,
    val expiresAtEpochSeconds: Long
) {
    companion object {
        fun from(session: DeviceSession): AuthenticatedTransportSession? {
            val id = session.sessionId ?: return null
            if (!session.active) return null
            return AuthenticatedTransportSession(
                deviceId = session.deviceId,
                sessionId = id,
                expiresAtEpochSeconds = session.expiresAtEpochSeconds
            )
        }
    }
}
