package com.zyra

import org.json.JSONObject

/**
 * Authenticated Windows connection probe used by the Android client.
 *
 * The caller supplies the already-issued device/session identifiers; this class
 * never handles or returns the device secret. A successful health probe only
 * establishes reachability. Session status is what upgrades the state to an
 * authenticated/ready connection.
 */
object WindowsConnectionChecker {
    fun fromHealthResponse(httpSuccessful: Boolean): WindowsConnectionStatus {
        return if (httpSuccessful) {
            WindowsConnectionStatus(
                state = WindowsConnectionState.REACHABLE,
                detail = "Windows agent is reachable."
            )
        } else {
            WindowsConnectionStatus(
                state = WindowsConnectionState.ERROR,
                detail = "Windows agent returned an unsuccessful health response."
            )
        }
    }

    fun fromAuthenticatedStatus(deviceId: String, sessionId: String, body: String): WindowsConnectionStatus {
        val parsed = WindowsConnectionStatus.fromSessionStatus(body)
        return parsed.copy(
            deviceId = parsed.deviceId ?: deviceId,
            sessionId = parsed.sessionId ?: sessionId,
        )
    }

    fun failure(state: WindowsConnectionState, detail: String): WindowsConnectionStatus =
        WindowsConnectionStatus(state = state, detail = detail)

    fun buildSessionStatusBody(deviceId: String, sessionId: String): JSONObject =
        JSONObject()
            .put("device_id", deviceId)
            .put("session_id", sessionId)
}
