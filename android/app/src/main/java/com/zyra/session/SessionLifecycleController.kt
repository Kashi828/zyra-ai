package com.zyra.session

import kotlin.math.max

interface SessionApi {
    fun create(deviceId: String): CreateSessionResponse
    fun refresh(deviceId: String, refreshToken: String): RefreshSessionResponse
    fun logout(deviceId: String, sessionId: String): Boolean
}

class SessionLifecycleController(
    private val api: SessionApi,
    private val storage: SecureSessionStorage,
    private val nowSeconds: () -> Long = { System.currentTimeMillis() / 1000L }
) {
    fun restore(): DeviceSession? {
        val state = storage.load() ?: return null
        if (state.deviceId.isBlank() || state.sessionId.isBlank() || state.refreshToken.isBlank()) {
            storage.clear()
            return null
        }
        return DeviceSession(
            deviceId = state.deviceId,
            sessionId = state.sessionId,
            expiresAtEpochSeconds = state.expiresAtEpochSeconds,
            active = state.expiresAtEpochSeconds > nowSeconds()
        )
    }

    fun ensureActive(deviceId: String): DeviceSession {
        val restored = restore()
        if (restored != null && restored.deviceId == deviceId && restored.active) {
            return restored
        }

        val current = storage.load()
        if (current != null &&
            current.deviceId == deviceId &&
            current.refreshToken.isNotBlank() &&
            current.refreshExpiresAtEpochSeconds > nowSeconds()) {
            try {
                val refreshed = api.refresh(deviceId, current.refreshToken)
                val next = PersistedSessionState(
                    deviceId = deviceId,
                    sessionId = refreshed.sessionId,
                    refreshToken = refreshed.refreshToken,
                    expiresAtEpochSeconds = refreshed.expiresAt,
                    refreshExpiresAtEpochSeconds = max(refreshed.expiresAt, current.refreshExpiresAtEpochSeconds)
                )
                storage.save(next)
                return DeviceSession(deviceId, refreshed.sessionId, refreshed.expiresAt, true)
            } catch (_: Exception) {
                storage.clear()
            }
        }

        val created = api.create(deviceId)
        storage.save(
            PersistedSessionState(
                deviceId = deviceId,
                sessionId = created.sessionId,
                refreshToken = created.refreshToken,
                expiresAtEpochSeconds = created.expiresAt,
                refreshExpiresAtEpochSeconds = created.expiresAt
            )
        )
        return DeviceSession(deviceId, created.sessionId, created.expiresAt, true)
    }

    fun logout(): Boolean {
        val state = storage.load() ?: return true
        return try {
            api.logout(state.deviceId, state.sessionId)
            storage.clear()
            true
        } catch (_: Exception) {
            false
        }
    }
}
